from __future__ import annotations

import argparse
import asyncio
import json

import websockets
from websockets.exceptions import ConnectionClosed


async def receive_messages(
    websocket: websockets.WebSocketClientProtocol, stop_event: asyncio.Event
) -> None:
    try:
        async for raw_message in websocket:
            payload = json.loads(raw_message)
            message = payload.get("message")
            if message:
                print(message)
            elif payload.get("type") == "question":
                print(f"Q{payload['index']}: {payload['prompt']}")
            else:
                print(payload)

            if payload.get("type") in {"game_over", "shutdown"}:
                stop_event.set()
                return
    except ConnectionClosed:
        stop_event.set()


async def send_answers(
    websocket: websockets.WebSocketClientProtocol, stop_event: asyncio.Event
) -> None:
    while not stop_event.is_set():
        answer = await asyncio.to_thread(input, "> ")
        if stop_event.is_set():
            return
        if not answer.strip():
            continue
        await websocket.send(json.dumps({"type": "answer", "answer": answer}))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal buzzer quiz client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    uri = f"ws://{args.host}:{args.port}"
    stop_event = asyncio.Event()

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"type": "join", "name": args.name}))
        receiver = asyncio.create_task(receive_messages(websocket, stop_event))
        sender = asyncio.create_task(send_answers(websocket, stop_event))

        done, pending = await asyncio.wait(
            {receiver, sender},
            return_when=asyncio.FIRST_COMPLETED,
        )
        stop_event.set()
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        await asyncio.gather(*done, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
