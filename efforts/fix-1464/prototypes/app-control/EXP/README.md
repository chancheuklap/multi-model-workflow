# Codex App control experiment

This experiment checks the first prerequisite of the approved six-step App runner plan. An adapter needs to operate sessions in the desktop App, including stopping work and delivering a wake after its sending process exits.

The public app-server protocol can read saved history from a different process. History visibility does not establish control of the running session.

## Run the isolated comparison

```sh
python3 efforts/fix-1464/prototypes/app-control/EXP/probe.py --fixtures
```

`--binary` selects the CLI executable. The experiment uses both the installed CLI and the executable bundled with the running desktop App.

The default public-control probe reads the App process transport and attempts the public control socket. It calls `thread/loaded/list` only when the socket exists. A pass requires the current `CODEX_THREAD_ID` in that runtime's loaded-session list. `--socket` selects an existing public control socket. The probe does not start a daemon or change a listener.

`--fixtures` creates a throwaway HOME, CODEX_HOME, working directory, and local HTTP provider. It creates one session in a consumer app-server, persists a failed initial turn, and uses another app-server to enqueue a message through `thread/queue/add`. The producer exits before the consumer starts the queued turn. A third process then attempts `turn/interrupt`; the consumer also attempts interruption of its own turn. The local provider returns failure and never contacts a model service. Cleanup closes the owned servers and removes the temporary home.

The generated `results.json` and `index.html` are under `.scratch/fix-1464/app-control/evidence/public-control/`. `--output` changes that location.

## Observed on 2026-10-31

CLI 0.165.0 and the desktop App's CLI 0.165.0-alpha.1.2 both showed:

| Operation | Observation |
| --- | --- |
| Start with an exact working directory, model, and approval policy | The response retained the supplied values |
| Read the session's history from the producer | Succeeded while the session was not loaded there |
| Enqueue through a producer that subsequently exits | Acknowledged |
| Consumer receives the external queued message | A new turn started and contacted the local fixture provider |
| Interrupt from the third process | Failed with `thread not found` |
| Interrupt in the consumer runtime | Confirmed by `turn/completed` with status `interrupted` |

The actual desktop App's child app-server used `stdio://`, exposed no named Unix socket, and had no default public control socket. The isolated results therefore do not establish control of the desktop runtime. They establish that cross-process queue delivery works and that sharing history does not confer interruption capability.

The `shell_environment_policy.set` override was submitted at thread start. This experiment does not execute a command to verify its environment. It does not prove a real App session's startup environment, hooks, restart recovery, or worker and reviewer lifecycle.

## Self-wake check in the real App

`--enqueue-self` sends one clearly identified continuation to the current `CODEX_THREAD_ID`, through the public app-server queue API. It creates no new chat and gives no implementation work to another agent. Its sending process exits after the queue acknowledges the message. This option changes the current chat's queue and is opt-in.

A queue acknowledgment is not a completed wake check. A subsequent App turn must receive the exact marker recorded under `--output`, after the original turn ends and the sender exits. The continuation then records that observation before resuming the original six-step task.

The real desktop chat received marker `mmw-app-wake-f7c1af16-abd0-4c83-a156-3aaeca0f0593` in a new turn after the preceding assistant final. The sender had exited with code 0 before that final. The observation was recorded at 2026-10-31T04:39:47Z under `.scratch/fix-1464/app-control/evidence/self-wake/observed.json`, separately from the original queue acknowledgment. This establishes a real App wake after turn completion. It does not establish restart recovery or control of another chat.

## Public MCP discovery

```sh
python3 efforts/fix-1464/prototypes/app-control/EXP/probe.py --mcp-discovery --binary /Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex --output .scratch/fix-1464/app-control/evidence/mcp-public
```

This read-only probe uses the documented `mcpServerStatus/list` endpoint and the existing first-party App plugin. Its enabled override applies only to the temporary app-server process. It inherits the App binding without printing it and does not alter signing, process ancestry, caller identities, or persistent configuration.

Discovery returned zero tools and `MCP startup failed: Mcp error: -32603: Codex app tools pipe closed`. The App log at 2026-10-31T04:40:52.699Z records `dynamic_app_tools_peer_rejected`, reason `missing-code-signing-identity`. The rejected identity remains unknown. This route therefore did not establish a script-accessible App control API. No write tool or model turn was attempted through it.

## Reusable parts and limits

`Rpc` is a small standard-library client for the public JSONL protocol. `public_control` checks that a discovered socket serves the intended running session. `fixture` distinguishes persisted history, queue delivery, and live interruption. `enqueue_self` tests a real App wake without dispatching another agent. `mcp_discovery` checks the App plugin through the documented protocol.

These are experimental assets. No MMW runner, installed skill, live model configuration, relay, or watchdog consumes them. The App adapter remains unimplemented until the complete control requirement is proved.

## Native App control verified

The owner requested a direct native-tool test on 2026-10-31. Opening the existing checkout with `codex app /Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow` registered that exact directory as an App project. `list_projects` returned project `f481e100-95fb-4e80-99ee-d7b33aff7478` for the exact path. `create_thread` then started a fresh local chat in that project without creating a worktree or changing the branch.

Independent chat `01a1904d-896b-7813-8c21-4b67cfbd48f5`, titled `MMW 独立会话启动验证`, ran its first commands in that exact directory. Both `pwd -P` and `git rev-parse --show-toplevel` matched the requested path. The branch was `fix-1464`, HEAD was `942c588bd300d47ebb2b53432e915e76ce4a5ef2`, and the worktree was clean. The raw command records show that no `cd` or workspace rebinding preceded the observation. The chat had its own `CODEX_THREAD_ID` and contained the verification brief rather than the parent's conversation.

`send_message_to_thread` started a second read-only turn. `wait_threads` and `read_thread` reported it as active and in progress. The test's Python sleep process was observed as PID 3873, owned by the actual desktop app-server PID 2520. `set_thread_archived` then returned success. A subsequent native read reported that turn as `interrupted`, the chat as `notLoaded`, and the sleep process was confirmed absent. The chat remains archived after the test. No product file was modified by the verification chat.

This directly proves native App creation in an exact existing checkout, independent context, follow-up dispatch, live state inspection, and active-turn interruption through archival for this case. The earlier script-launch/MCP failure does not establish a limitation of these native tools. The implementation must connect MMW's preparation and registration to the verified native operations, and use the separately verified public queue for background delivery. Model/effort overrides, startup environment and permission delivery, hook compatibility, restart recovery, and complete MMW ticket lifecycle acceptance remain unverified.

Protocol reference: [Codex App Server](https://learn.chatgpt.com/docs/app-server). Command reference: [Developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
