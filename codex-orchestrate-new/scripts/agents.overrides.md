# scripts override

- Runtime state belongs under `.codex/multi-model-workflow`.
- Script changes must preserve the copied workflow contracts while replacing host-specific mechanisms with Codex-native command and state handling.
- Script comments and user-facing messages must describe Codex shell, file, hook and subagent actions directly.
- Do not add compatibility fallbacks to old state paths, old plugin search paths, or old companion scripts.
- `validate-plugin-contract.sh` is the Codex-aware source manifest gate. It accepts `.codex-plugin/plugin.json` `hooks` and validates the referenced hook manifest directly.
- `verify-runtime-parity.sh` is the source/runtime parity gate. It checks plugin cache parity, user-level agent TOML parity, agent registration, and persisted plugin hook trust records.
- Dispatch validation that needs the full prompt/message must live in explicit scripts called by Skills before `spawn_agent` or `send_input`.
- Review dispatch bookkeeping belongs in explicit scripts: `dispatch-review.sh` validates and records reviewer agents, `complete-review-dispatch.sh` records durable results and increments review budget exactly once, and `record-review-disposition.sh` marks disposition progress.
- Review Budget is a hard stop by default. Only explicit user authorization may use `--allow-over-budget --override-reason "<reason>"`, and the same override must be carried through review validation and completion bookkeeping.
- `verify-maturity.sh` must include manifest, build, schema, agent, dispatch, hook and residue checks for the current source root.
