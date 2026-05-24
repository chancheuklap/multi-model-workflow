# scripts override

- Runtime state belongs under `.codex/multi-model-workflow`.
- Script changes must preserve the copied workflow contracts while replacing host-specific mechanisms with Codex-native command and state handling.
- Do not add compatibility fallbacks to old state paths, old plugin search paths, or old companion scripts.
