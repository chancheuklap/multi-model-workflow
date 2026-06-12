# build override

- `build.sh` is the single resolver entrypoint. Do not restore external resolver scripts unless a real build contract requires it.
- Template anchors must render deterministic output. After editing templates, run `bash codex-orchestrate-new/build/build.sh --apply --plugin-dir codex-orchestrate-new` and then `--check`.
- Shared templates must use Codex-native tool names, state paths and agent_type names.
- `worker-loop.codex.md.tmpl` is the only worker-loop template in this source tree.
- Tests under `build/tests/` should verify generated contracts and resolver behavior, not isolated wording unless that wording is a runtime anchor.
