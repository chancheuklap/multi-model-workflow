# codex/hooks/ agents.overrides.md

## 目录职责

`codex/hooks/` 是 user-level Codex hooks 的 source。安装脚本复制 hook shell，并把 `hooks.json` 中的 repo-relative command 改写成 user-level runtime path 后同步到：

- `/Users/cheuklapchan/.codex/hooks/multi-model-workflow/`
- `/Users/cheuklapchan/.codex/hooks.json`

## 编辑规则

- `session-start.sh` 注入 Plugin V2 等价的短规则：entry routing、skill namespace、hard gates、compaction recovery；只在 Codex 必要字段上做映射。
- `SessionStart` matcher 覆盖 `startup|resume|clear|compact`；`compact` 来自 Plugin V2，`resume` 是 Codex 会话恢复等价入口。
- `guard-premature-push.sh` 负责阻止 Orchestrate scope 未关闭时过早 publish，并在允许 `git push` / `gh pr create` / `gh pr edit` 前自动调用 cleanup。
- `track-review-budget.sh` 负责 review budget / dispatch ledger，不写 phase-specific review logic；external reviewer runner 成功返回后直接调用它。
- `cleanup-run-state.sh` 是 publish 前自动清理 helper，也可作为手动 fallback；只删 `.codex/multi-model-workflow/`，不删正式 design / plan / issue / report / code artifacts。
- `hooks.json` 是 hook manifest source；新增或删除 hook 时必须先改这里，再改安装脚本的脚本清单。
- Hook 中不得写旧 Claude runtime 路径；统一使用 `.codex/multi-model-workflow/`。
- Claude cross-model review 默认使用 `codex/reviewers/claude-subscription-review.sh`，固定 `claude-opus-4-7` + `--effort high`；不得在 hook 中引导 `claude -p`，除非用户明确授权 Agent SDK credits / Extra Usage。
- 修改本目录后运行 `bash codex/hooks/install-hooks.sh --apply`，并对比 user-level hook runtime。
