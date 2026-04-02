# Server implementation

The server in `artifacts/server.py` runs a single local session over websockets. It starts the quiz as soon as the second player joins, rejects late joins after the game has started, opens one question at a time, and awards the point through an `asyncio.Lock` plus a `current_question_open` guard so only one answer can win each round.

# Client implementation

The client in `artifacts/client.py` is a minimal terminal client. It connects with a player name, prints server events, and reads answers from stdin with `asyncio.to_thread(input, ...)` so a human can play without blocking the receive loop.

# State model

The session uses an explicit `GamePhase` enum with `WAITING_FOR_PLAYERS`, `QUESTION_OPEN`, and `GAME_OVER`. Question progression also keeps `current_question_index`, `current_answer`, and `current_question_open` as explicit session state instead of inferring everything from incidental variables.

# Edge cases handled

- Simultaneous correct answers are serialized by `answer_lock`; once one answer wins, `current_question_open` flips false and later in-flight answers are ignored.
- If no one answers correctly within 10 seconds, the question expires and the server advances.
- A player disconnect during the game removes that player from the active map. If fewer than two players remain, the server ends the session cleanly instead of hanging.
- Late join attempts after the game has started are rejected instead of mutating live state.
- Not handled: reconnect with score restoration or session resume. That needs durable player identity and is out of scope for this minimal single-session build.
