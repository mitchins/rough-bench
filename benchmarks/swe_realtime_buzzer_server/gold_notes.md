# Gold Notes

This task is a small artifact-first SWE build, not a design memo.

The important distinction is between a server that works once in a happy-path demo
and one that has at least closed the obvious doors:

- contested answers cannot both score for the same question
- a question cannot stay open forever
- disconnects do not leave the game stuck in a dead state
- game over actually shuts the session down

The required self-audit matters. A strong answer does not claim completeness. It
ships a bounded single-session implementation and says clearly what it did not
handle, such as reconnect with persistent identity or joining after the match has
already started.

The strongest cheap isolation check in review is the point-award path. Read the
code and ask:

1. Is there a single-winner guard, such as a lock plus a `question_open` flag?
2. After a correct answer, can a second in-flight answer still score?
3. If a player disconnects mid-game, does the server remove them and either
   continue deterministically or terminate cleanly?

A polished prose note without runnable server and client artifacts should still
score badly.
