## Answer

The independent researcher chat is confirmed as `01a190c9-9815-7fd3-92e4-487cc35fd440`, and the App reports its requested working directory as `/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow`. The adapter confirms stop only after the App acknowledges archival of the requested chat and a subsequent read shows `notLoaded` without an `inProgress` turn. This read-only investigation confirms identity and directory live, but does not demonstrate a successful stop or prove that every operating-system descendant has terminated.

## Evidence scope

Source paths below are relative to `/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow`. Both adapter source files compared byte-for-byte equal to their frozen counterparts under `/private/tmp/mmw-app-final-20261031/runtime/mmw-v4/skills/dispatch/scripts/runners/`. No candidate code was run to control this investigation.

## Independent identity and directory

- `mmw-v4/skills/dispatch/scripts/runners/codex_app.py:213-235` resolves the directory strictly, calls public `thread/start` with `ephemeral: false`, and rejects a returned directory mismatch. When approval skipping is requested, it also checks the returned approval policy and sandbox. This establishes the preparation receipt's directory, rather than assuming a requested argument was retained.
- `mmw-v4/skills/dispatch/scripts/runners/codex-app-tools.js:20-43` calls that preparation helper, sends the initial prompt to the prepared ID, and rejects a send receipt identifying another chat. It does not fork the coordinating chat in this path. The startup return copies `args.cwd`; startup does not itself reread App metadata after sending.
- `mmw-v4/skills/dispatch/scripts/runners/codex_app.py:137-164` correlates native request and receipt IDs, requires a valid session identity, and rejects a different session on operations other than start. Lines 387-393 record the returned startup session and requested directory.
- The dispatch record `/tmp/mmw-app-final-20261031/home/state/chancheuklap__multi-model-workflow/briefs/20261031-070807-aa6d/2/started.json:1` identifies this researcher session. Its ID differs from the coordinator `01a18fb6-564f-7bc2-897e-9d87893e1ec9`, recorded in `/tmp/mmw-app-final-20261031/home/state/chancheuklap__multi-model-workflow/codex-app/01a18fb6-564f-7bc2-897e-9d87893e1ec9.json:1`.
- A live `mcp__codex_app__read_thread` response is preserved verbatim as formatted JSON in `efforts/fix-1464/research/1470-app-role-acceptance/brief-2/read-thread.json`. Lines 4-13 confirm the researcher ID, researcher title, brief-bearing initial preview, active status, and requested directory. Lines 25-29 show its current turn is in progress. Lines 39-46 also show a real command executing in that directory. The session's `CODEX_THREAD_ID` and shell `pwd` independently matched those values during this investigation, but their stdout was not saved as a separate artifact.

## Confirmed stop boundary

`mmw-v4/skills/dispatch/scripts/runners/codex-app-tools.js:53-61` implements a two-stage stop. The archive receipt must contain the requested ID and `archived: true`. The following `read_thread` must return `notLoaded`, and its returned turn must not be `inProgress`. The inspection uses the returned thread ID and current turn at lines 11-17. Python then checks the session identity and requires `stopped: true` before persisting a stopped observation at `mmw-v4/skills/dispatch/scripts/runners/codex_app.py:401-406`.

This is an App-confirmed chat stop boundary. It is not a process-group kill or a check of every spawned command. No stop was requested here because the assignment is read-only, and interrupting another running session is outside its scope. The saved live response shows this researcher still active at the time of observation, not stopped.

## What remains unproved

- This investigation supplies no real successful archive-and-inspect stop receipt. Source inspection establishes what the adapter requires, not that the App has satisfied that requirement in this acceptance run.
- The stop inspection requests only one turn at `codex-app-tools.js:12-17`. A missing returned turn passes the optional-turn check if the thread is `notLoaded`. The code does not enumerate older turns or operating-system descendants.
- Persisted `stopped` observations are cached. `codex_app.py:112-123` returns a stopped record before checking process identity, and lines 401-406 skip a fresh native stop when that record already says stopped. A later foreground active or idle inspection can overwrite it at lines 408-413. Therefore a cached stopped result alone does not prove the App was just inspected or that the chat cannot later resume.
- Recorded process identity is the shared App runtime ancestor, found at `codex_app.py:53-71`, not a unique worker process. The coordinator and researcher observation files cited above both record PID 2520. Distinct chat IDs prove distinct chats, not operating-system process isolation.
- The directory evidence establishes App metadata and observed command location at the sampled time. It does not prove that a session cannot later change directory. This source review makes no broader claim about restart recovery, installed hooks, or every role.

## Problems

None
