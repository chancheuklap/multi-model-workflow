# codex/reviewers/ agents.overrides.md

## 目录职责

`codex/reviewers/` 存放 Codex 调用或交接外部 reviewer 的脚本。目前维护：

- `claude-subscription-review.sh`：Codex → external Claude Code reviewer，使用普通 `claude` stdin，不使用 `claude -p`。
- `claude-review.sh`：Codex → `claude -p` non-interactive reviewer，属于 Agent SDK / Extra Usage 路径。

## 使用规则

- 默认 external Claude reviewer lane 是 `claude-subscription-review.sh`。
- 所有 Claude reviewer lane 必须使用 `claude-opus-4-7` 和 `--effort high`，不得降级成 Sonnet 或 medium effort。
- `claude-subscription-review.sh` 禁止使用 `-p`，只允许 read-only tools：默认 `Read,Grep,Glob`。
- `claude-review.sh` 必须要求 `--allow-extra-usage` 或 `CLAUDE_REVIEW_ALLOW_EXTRA_USAGE=1`，避免误烧 Extra Usage。
- reviewer runner 成功返回后必须调用 `codex/hooks/track-review-budget.sh`，写入 `budget_used` 和 dispatch ledger。
- Parent prompt 必须自足，不能只写“按 Orchestrate review”。
- 如果 external Claude runner 失败，Codex 可以回落到内部 `code_reviewer` / `release_reviewer`，但汇报必须说明未执行 cross-model review。
- 不在 bridge 中写 phase-specific review logic；phase-specific prompt 仍由 `.agents/skills/orchestrate-*/references/*.md` 负责。
