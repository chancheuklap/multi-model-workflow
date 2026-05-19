# codex/hooks/ agents.overrides.md

## 目录职责

`codex/hooks/` 是 user-level Codex hooks 的 source。安装脚本把这里的 hook shell 和 `hooks.json` 同步到：

- `/Users/cheuklapchan/.codex/hooks/multi-model-workflow/`
- `/Users/cheuklapchan/.codex/hooks.json`

## 编辑规则

- `session-start.sh` 只写会改变 Codex 会话行为的短规则提醒。
- `guard-premature-push.sh` 负责阻止 Orchestrate scope 未关闭时过早 push。
- `track-review-budget.sh` 负责 review budget / dispatch ledger，不写 phase-specific review logic；external reviewer runner 成功返回后直接调用它。
- Hook 中不得写旧 Claude runtime 路径；统一使用 `.codex/multi-model-workflow/`。
- Claude cross-model review 默认使用 `codex/reviewers/claude-subscription-review.sh`，固定 `claude-opus-4-7` + `--effort high`；不得在 hook 中引导 `claude -p`，除非用户明确授权 Agent SDK credits / Extra Usage。
- 修改本目录后运行 `bash codex/hooks/install-hooks.sh --apply`，并对比 user-level hook runtime。
