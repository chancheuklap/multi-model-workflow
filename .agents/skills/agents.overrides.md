# .agents/skills/ agents.overrides.md

## 目录职责

旧 repo-local Orchestrate phase skills 已从这里移除，避免 Codex 继续加载过时流程。

新的 Codex 原子复刻入口是 `codex-orchestrate/` 插件包：

- skills source: `codex-orchestrate/skills/`
- custom agents: `codex-orchestrate/agents/`
- hooks: `codex-orchestrate/hooks/`
- review lane: `codex-orchestrate/scripts/review/review-lane.sh`
- worktree execution: `codex-orchestrate/scripts/dispatch/`

## 编辑规则

- 不要在 `.agents/skills/orchestrate-*` 下重建旧 runtime。
- 修改 Orchestrate 行为时改 `codex-orchestrate/`，并保持对应子目录的 `agents.overrides.md` 同步。
- 安装或验证 runtime 走 `codex-orchestrate/installers/`。
