# codex-orchestrate override

- `codex-orchestrate/` is the Codex-native source for this workflow. Preserve the copied phase, gate, state, review, worker, and closing contracts unless a change is required for Codex execution.
- Do not invent new workflow behavior here. Keep changes traceable to host migration or contract preservation.
- Runtime instructions must use Codex-native executable paths, state paths, agent fields, and review dispatch. Do not leave compatibility fallbacks or dual host entrypoints.
- Keep source, installed plugin cache, custom agent runtime, and user config parity verifiable before declaring the plugin usable.
- Ad-hoc review skills must dispatch the native `codex_reviewer` subagent with `spawn_agent` and `wait_agent`; do not add external review runners.
- Orchestrated review references must use `.codex/multi-model-workflow/review-*`, reviewer `.agent-id` files, `spawn_agent`, `send_input`, and `wait_agent`; do not describe job-id polling.
- Current workflow state paths are `.codex/multi-model-workflow/*`. Do not write new runtime instructions against old-host state paths.
