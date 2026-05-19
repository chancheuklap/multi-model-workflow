# .agents/skills/ agents.overrides.md

## 目录职责

`.agents/skills/` 是 Codex Orchestrate phase skills 的 repo-local source。当前系统按 Plugin V2 的六 phase 拆分：

| Skill | 职责 |
| --- | --- |
| `orchestrate-workflow` | Entry Gate、Infrastructure、route、Closing |
| `orchestrate-discovery` | design document、domain alignment、Design Review |
| `orchestrate-plan-writing` | plan_writer dispatch、Plan Review、plan gates |
| `orchestrate-execution` | Task Pack execution、Pack Review、repair loop、early release gate |
| `orchestrate-final-review` | final intent review、tail sweep、final release gate、business report |
| `orchestrate-multi-pr-merge` | PR 交互冲突发现、修复、集成审查、合并 |

## 编辑规则

- `SKILL.md` 只写 phase skeleton、step order、return contract 和 reference map。
- 深水区行为写在该 skill 的 `references/*.md`，按到达步骤渐进读取。
- Reference 中的 dispatch prompt 必须自足，不假设 custom agent 读过本 skill。
- Codex 运行目录使用 `.codex/multi-model-workflow/`，不要写旧 Claude 运行目录。
- Review dispatch 使用 `code_reviewer`；release gate 使用 `release_reviewer`。
- 需要 Claude cross-model review 时先读 `orchestrate-workflow/references/external-review-lanes.md`；默认使用 `codex/reviewers/claude-subscription-review.sh` 自动调用普通 `claude` stdin，不走 `claude -p`，并固定 `claude-opus-4-7` + `--effort high`。
- Worker dispatch 使用 `coding_worker` 或 `complex_coding_worker`；未知根因使用 `root_cause_analyst`。
- 改 verdict、disposition、repair truncation、budget 或 release gate 时，用 `rg` 检查 producer/consumer 是否同步。
