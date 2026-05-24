# archived codex/ overrides

## 目录职责

This directory is the archived pre-atomic Codex implementation. It is retained
only for audit and historical comparison.

Current Codex Orchestrate behavior is owned by `codex-orchestrate/` and the
installed plugin cache under:

```text
~/.codex/plugins/cache/multi-model-workflow/codex-orchestrate/0.1.0/
```

## 编辑规则

- Do not restore this directory to repository root.
- Do not copy these agent, skill, or hook contracts into active runtime without
  checking `plugin/` and implementing a Codex-native replacement.
- Active changes belong in `codex-orchestrate/`, not this archive.
