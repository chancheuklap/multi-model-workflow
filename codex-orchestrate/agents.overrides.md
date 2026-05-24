# codex-orchestrate override

- `codex-orchestrate/` starts as a byte-for-byte copy of `plugin/`; every later change must be traceable as a host migration from the copied Claude plugin baseline.
- Do not invent new workflow behavior here. Preserve the copied phase, gate, state, review, worker, and closing contracts unless the change is required to make the same contract work in Codex.
- Remove Claude-only runtime terms from executable paths and current instructions as each layer is migrated. Do not leave compatibility fallbacks or dual Claude/Codex entrypoints.
- Keep source, installed plugin cache, custom agent runtime, and user config parity verifiable before declaring the plugin usable.
- Ad-hoc review skills must dispatch the native `codex_reviewer` subagent with `spawn_agent` and `wait_agent`; do not add external review runners.
