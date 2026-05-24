# codex-orchestrate override

- `codex-orchestrate/` is the Codex-native source for this workflow. Preserve the copied phase, gate, state, review, worker, and closing contracts unless a change is required for Codex execution.
- Do not invent new workflow behavior here. Keep changes traceable to host migration or contract preservation.
- Runtime instructions must use Codex-native executable paths, state paths, agent fields, and review dispatch. Do not leave compatibility fallbacks or dual host entrypoints.
- Codex source text must not describe old-host tool-name labels; express the required Codex action directly.
- `.codex-plugin/plugin.json` must declare bundled hooks with `"hooks": "./hooks.json"` so runtime installation loads the hook manifest.
- Keep source, installed plugin cache, custom agent runtime, and user config parity verifiable before declaring the plugin usable.
- Ad-hoc review skills must dispatch the native `codex_reviewer` subagent with `spawn_agent` and `wait_agent`; do not add external review runners.
- Orchestrated review references must use `.codex/multi-model-workflow/review-*`, reviewer `.agent-id` files, `spawn_agent`, `send_input`, and `wait_agent`; do not describe job-id polling.
- Dispatch validation belongs in explicit Coordinator scripts before `spawn_agent` / `send_input`; those scripts may gate the prompt envelope, but must not run reviews or replace subagents.
- Current workflow state paths are `.codex/multi-model-workflow/*`. Do not write new runtime instructions against old-host state paths.
- Worktree instructions must delegate filesystem placement to Codex runtime / Codex App. Do not describe pseudo tools, custom `git worktree add` paths, or invented worktree roots; the expected native shape is `${CODEX_HOME:-$HOME/.codex}/worktrees/<codex-assigned-id>/<repo-name>`.
- `architecture-draft.md` is the Codex source architecture authority. Keep it in Chinese and keep it detailed enough to audit workflow routes, state files, document artifacts, subagents, hooks, scripts, tests, and Codex-specific runtime rulings.
