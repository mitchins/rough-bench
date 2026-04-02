from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum

import websockets
from websockets.exceptions import ConnectionClosed


HOST = "127.0.0.1"
PORT = 8765
MIN_PLAYERS = 2
MAX_PLAYERS = 4
POINTS_TO_WIN = 5
QUESTION_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class Question:
    prompt: str
    answer: str


class GamePhase(Enum):
    WAITING_FOR_PLAYERS = "waiting_for_players"
    QUESTION_OPEN = "question_open"
    GAME_OVER = "game_over"


class QuizServer:
    def __init__(self) -> None:
        self.questions = [
            Question("Capital of France?", "paris"),
            Question("2 + 2?", "4"),
            Question("Largest ocean on Earth?", "pacific"),
            Question("Planet known as the red planet?", "mars"),
            Question("Author of Hamlet?", "shakespeare"),
            Question("Chemical symbol for gold?", "au"),
            Question("Fastest land animal?", "cheetah"),
            Question("Square root of 81?", "9"),
            Question("Continent containing Kenya?", "africa"),
            Question("Language primarily spoken in Brazil?", "portuguese"),
        ]
        self.phase = GamePhase.WAITING_FOR_PLAYERS
        self.players: dict[str, websockets.WebSocketServerProtocol] = {}
        self.scores: dict[str, int] = {}
        self.current_question_index = -1
        self.current_answer = ""
        self.current_question_open = False
        self.answer_lock = asyncio.Lock()
        self.timeout_task: asyncio.Task[None] | None = None
        self.shutdown_event = asyncio.Event()

    async def run(self, host: str = HOST, port: int = PORT) -> None:
        async with websockets.serve(self.handle_connection, host, port) as server:
            print(f"Quiz server listening on ws://{host}:{port}")
            await self.shutdown_event.wait()
            server.close()
            await server.wait_closed()

    async def handle_connection(
        self, websocket: websockets.WebSocketServerProtocol
    ) -> None:
        player_name: str | None = None
        try:
            join_raw = await websocket.recv()
            payload = json.loads(join_raw)
            player_name = str(payload.get("name", "")).strip()
            if payload.get("type") != "join" or not player_name:
                await websocket.send(
                    json.dumps({"type": "error", "message": "First message must be join"})
                )
                await websocket.close()
                await websocket.wait_closed()
                return

            if self.phase != GamePhase.WAITING_FOR_PLAYERS:
                await websocket.send(
                    json.dumps({"type": "error", "message": "Game already started"})
                )
                await websocket.close()
                await websocket.wait_closed()
                return

            if len(self.players) >= MAX_PLAYERS or player_name in self.players:
                await websocket.send(
                    json.dumps({"type": "error", "message": "Name unavailable"})
                )
                await websocket.close()
                await websocket.wait_closed()
                return

            self.players[player_name] = websocket
            self.scores[player_name] = 0
            await self.broadcast(
                {
                    "type": "status",
                    "message": f"{player_name} joined ({len(self.players)}/{MAX_PLAYERS})",
                    "scores": self.scores,
                }
            )

            if len(self.players) >= MIN_PLAYERS and self.phase == GamePhase.WAITING_FOR_PLAYERS:
                await self.start_next_question()

            async for raw_message in websocket:
                message = json.loads(raw_message)
                if message.get("type") == "answer":
                    await self.handle_answer(player_name, str(message.get("answer", "")))
        except ConnectionClosed:
            pass
        finally:
            if player_name is not None:
                await self.unregister_player(player_name)

    async def handle_answer(self, player_name: str, answer: str) -> None:
        normalized_answer = answer.strip().casefold()
        if not normalized_answer:
            return

        async with self.answer_lock:
            if self.phase != GamePhase.QUESTION_OPEN or not self.current_question_open:
                return
            if normalized_answer != self.current_answer:
                await self.send_to(
                    player_name,
                    {"type": "status", "message": f"Incorrect: {answer.strip()}"},
                )
                return

            self.current_question_open = False
            if self.timeout_task is not None:
                self.timeout_task.cancel()
                self.timeout_task = None

            self.scores[player_name] += 1
            await self.broadcast(
                {
                    "type": "correct",
                    "message": f"{player_name} answered correctly",
                    "scores": self.scores,
                }
            )

            if self.scores[player_name] >= POINTS_TO_WIN:
                await self.end_game(winner=player_name)
                return

        await self.start_next_question()

    async def start_next_question(self) -> None:
        if self.phase == GamePhase.GAME_OVER:
            return
        if len(self.players) < MIN_PLAYERS:
            await self.shutdown("Not enough players to continue")
            return

        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            winner = max(self.scores, key=self.scores.get, default=None)
            await self.end_game(winner=winner)
            return

        question = self.questions[self.current_question_index]
        self.current_answer = question.answer.casefold()
        self.current_question_open = True
        self.phase = GamePhase.QUESTION_OPEN

        await self.broadcast(
            {
                "type": "question",
                "index": self.current_question_index + 1,
                "prompt": question.prompt,
                "timeout_seconds": QUESTION_TIMEOUT_SECONDS,
                "scores": self.scores,
            }
        )
        self.timeout_task = asyncio.create_task(
            self.expire_question(self.current_question_index)
        )

    async def expire_question(self, question_index: int) -> None:
        try:
            await asyncio.sleep(QUESTION_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            return

        async with self.answer_lock:
            if (
                self.phase != GamePhase.QUESTION_OPEN
                or not self.current_question_open
                or question_index != self.current_question_index
            ):
                return
            self.current_question_open = False
            await self.broadcast(
                {
                    "type": "expired",
                    "message": f"Question {question_index + 1} expired",
                    "scores": self.scores,
                }
            )

        await self.start_next_question()

    async def unregister_player(self, player_name: str) -> None:
        websocket = self.players.pop(player_name, None)
        self.scores.pop(player_name, None)
        if websocket is not None and not websocket.closed:
            await websocket.close()
            await websocket.wait_closed()

        if self.phase == GamePhase.GAME_OVER:
            return

        if player_name:
            await self.broadcast(
                {
                    "type": "status",
                    "message": f"{player_name} disconnected",
                    "scores": self.scores,
                }
            )

        if self.phase != GamePhase.WAITING_FOR_PLAYERS and len(self.players) < MIN_PLAYERS:
            await self.shutdown("Not enough players remain")

    async def send_to(self, player_name: str, payload: dict[str, object]) -> None:
        websocket = self.players.get(player_name)
        if websocket is None:
            return
        await websocket.send(json.dumps(payload))

    async def broadcast(self, payload: dict[str, object]) -> None:
        message = json.dumps(payload)
        stale_players: list[str] = []
        for name, websocket in list(self.players.items()):
            try:
                await websocket.send(message)
            except ConnectionClosed:
                stale_players.append(name)
        for name in stale_players:
            await self.unregister_player(name)

    async def end_game(self, winner: str | None) -> None:
        if winner is None:
            await self.shutdown("Game over with no winner")
            return
        await self.broadcast(
            {
                "type": "game_over",
                "message": f"{winner} wins",
                "winner": winner,
                "scores": self.scores,
            }
        )
        await self.shutdown(f"Winner: {winner}")

    async def shutdown(self, reason: str) -> None:
        if self.phase == GamePhase.GAME_OVER:
            return

        self.phase = GamePhase.GAME_OVER
        self.current_question_open = False
        if self.timeout_task is not None:
            self.timeout_task.cancel()
            self.timeout_task = None

        message = json.dumps({"type": "shutdown", "message": reason})
        for websocket in list(self.players.values()):
            try:
                await websocket.send(message)
                await websocket.close()
                await websocket.wait_closed()
            except ConnectionClosed:
                pass

        self.players.clear()
        self.shutdown_event.set()


async def main() -> None:
    server = QuizServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
