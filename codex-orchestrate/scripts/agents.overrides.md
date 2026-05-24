# scripts override

- Runtime state belongs under `.codex/multi-model-workflow`.
- Script changes must preserve the copied workflow contracts while replacing host-specific mechanisms with Codex-native command and state handling.
- Script comments and user-facing messages must not refer to old-host tool names; describe Codex shell, file, hook, and subagent actions directly.
- Do not add compatibility fallbacks to old state paths, old plugin search paths, or old companion scripts.
- Verification scripts must validate the root `codex-orchestrate/hooks.json` manifest and Codex-native hook contracts; do not check for removed old-host review command hooks.
- Dispatch validation that needs the full prompt/message must live in explicit scripts called by Skills before `spawn_agent` or `send_input`; do not move it back into `SubagentStart` hooks.
