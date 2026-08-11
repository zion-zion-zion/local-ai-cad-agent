# 01 — Keep Stop available for the full Run

**What to build:** Make the existing Stop action reliably available from the moment a Run starts until it reaches a terminal state. A user can stop streamed model output or an active CAD/terminal operation, see an immediate stopping state, and keep the latest successful CAD Revision.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Stop remains visible while a Run is starting, streaming model content or reasoning, and executing a CAD or terminal operation.
- [x] Streaming events can hide or replace the thinking indicator without hiding Stop while the Run remains active.
- [x] Clicking Stop immediately disables Stop and new message submission and presents a clear stopping state.
- [x] The existing project-scoped stop request prevents deliberate later model rounds, stops the active CAD or terminal subprocess through the existing mechanism, and eventually reports a terminal stopped state.
- [x] The client returns to idle controls only after a terminal server event; an incomplete streamed assistant response is visibly marked as stopped rather than complete.
- [x] Stopping a Run does not remove or roll back the latest successful CAD Revision.
- [x] Stop remains manual: no browser-disconnect, progress heuristic, time, or token policy triggers it automatically.
- [x] Existing server-side Stop behavior is covered through the Flask application seam, including preservation of an already successful CAD Revision.
- [x] Client Run-state behavior is covered with the existing Node test runner, including running, streaming, stopping, and stopped transitions.

## Comments

- Implemented in commit `87d028f` (`Keep Stop available throughout agent runs`).
- Verification: `node --test tests/test_run_state.mjs` (4 passed); the focused AgentRunner cancellation test (1 passed); the focused Flask Stop/Revision-preservation test (1 passed).
- `tests/test_benchmark.py` was intentionally deleted and was not restored.
