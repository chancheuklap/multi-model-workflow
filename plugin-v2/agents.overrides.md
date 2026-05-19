# plugin-v2/ agents.overrides.md

## 目录职责

Claude Code plugin v2 (v0.8.1)。6 个内部 Skill + 7 个 Sub-Agent + ~25 个 skill-specific reference（无共享 reference 文件夹）。所有代码审查通过 `codex:codex-rescue` 跨模型派发。Worker agent（pack-executor / complex-pack-executor / plan-writer）无 maxTurns 限制——三次失败协议是内置熔断器。

## 架构约束

- **渐进式加载**：SKILL.md 是骨架；reference 到达步骤时才读取
- **Sub-agent 隔离**：dispatch prompt 自足；sub-agent 不读 SKILL.md / references
- **Agent 定义 = 行为权威**：TDD、自检、scope 边界等通用规则写 agent 定义，dispatch template 只写场景信息
- **Reviewer 独立验证**：所有 Calibration 包含"不信任上游报告"
- **合并策略铁律**：只用 `git merge --no-ff`，绝对禁止 squash merge（`--squash`）和 rebase（`--rebase`），完整保留 commit 历史
- **Review 预算**：`2N + 12`（N = pack 数）

## 内部 Skill

| Skill | 职责 |
|-------|------|
| orchestrate-workflow | 主入口。Entry Gate + Infrastructure + Phase 路由 + Closing |
| orchestrate-discovery | Discovery + Design Review + to-issues 过渡 |
| orchestrate-plan-writing | Plan Writing + Plan Review |
| orchestrate-execution | Pack 执行循环 |
| orchestrate-final-review | Final Review + 遗留清扫 + Release Gate + 业务汇报 |
| orchestrate-multi-pr-merge | 跨 PR 冲突发现 + 修复 + 集成审查 + 合并 |

## Sub-Agent

| Agent | Model | 职责 |
|-------|-------|------|
| plan-writer | Opus 4.7 1M | 从 design + issues 撰写 plan（不 autoload SKILL.md，直接 Read methodology） |
| pack-executor | Sonnet | 常规 Task Pack 实现 |
| complex-pack-executor | Opus 4.7 | 高风险 Task Pack（migration / billing / auth / shared contracts） |
| code-explorer | Sonnet | 只读窄域代码探索 |
| complex-code-explorer | Opus 4.7 | 只读多模块深度调查 |
| root-cause-analyst | Opus 4.7 1M | Bug 调查 / Repair 截断 / Multi-PR 冲突根因 |
| docs-worker | Sonnet | 低风险文档清理 |

## 信息密度规则

- **Disposition 表**：每个 phase 的 disposition 文件自足内联完整 6 行 Disposition 定义 + Reception Rules + needs-evidence 补证说明。**新增**：每个 disposition 文件前置"整体 Verdict 前置检查"处理 `needs context` 整体 verdict
- **修复路由**：每个 phase 的 repair 文件自足内联路径 A/B/C + 截断规则
- **Direction Check**：简化为仅"达到预算 80%"触发（execution-pack-review-cycle.md 和 final-review-preconditions.md）
- **Forbidden Shortcuts**：内联在 execution-review-dispatch.md（Code Quality）和 final-review-angles.md（Baseline 2）
- **Upstream Skill 允许输出**：内联在 session-start.sh hook（始终加载）
- **Durable Handoff Brief**：内联在 workflow-infrastructure.md
- **Agent 行为规则**（TDD、自检、Git 纪律、三次失败协议）：写在 agent 定义中，dispatch template 不重复。**TDD 例外**：`risk_flags: trivial` 的 pack 不强制红-绿循环
- **Return Contract / Calibration**：在 Codex dispatch template 中保持 inline（sub-agent 隔离规则要求自足）
- **NEEDS_EXECUTION 回流上限**：最多 1 次（final-review-repair.md + final-review-completion.md + workflow-formal-orchestrate.md）

## 架构变更记录

- **plan-writer 不再 autoload 完整 SKILL.md**：移除了 `skills: ["orchestrate-plan-writing"]`，改为 Read tool 读取 `references/plan-writing-methodology.md`
- **Budget file 新增字段**：`starting_commit`（Git Checkpoint 时记录）、`discovery_used`（Discovery phase 本地计数）
- **Release Gate 预算说明修正**：不再称"独立预算"，改为"已包含在全局 `2N+12` 预算中"
- **Design Review per-phase allowance**：改用 `discovery_used` 字段做本地计数，不依赖全局 `budget_used`
- **Worker maxTurns 移除**：pack-executor / complex-pack-executor / plan-writer 无 maxTurns 限制（三次失败协议是熔断器）
- **Pack Brief 精简**：必需字段 10 个 + 条件字段 5 个（仅在相关时包含）。移除了 Commit boundary / Parallel safety / Issue / Scope 等 Worker 不需要的字段
- **Review 预算**：`2N + 12`（N = pack 数）。Design Review 2 dispatches + Plan Review 1 + Pack Review N + Final Review 2 + Release Gate 2 + 修复余量 N+5

## Hooks

| Hook | 事件 | 脚本 | 职责 |
|------|------|------|------|
| SessionStart | `startup\|clear\|compact` | `session-start.sh` | 注入行为规则（routing / hard gates / agent roles） |
| PreToolUse/Bash | 所有 Bash 调用 | `scripts/guard-premature-push.sh` | ① 拦截 `--squash` 和 `rebase`（合并策略铁律） ② 有未完成 task 时拦截 `git push` 和 `gh pr create` |
| SubagentStop/coding | `pack-executor\|complex-pack-executor` | inline | 提醒 Coordinator 派发 Codex review |
| SubagentStop/codex | `codex:codex-rescue` | `track-review-budget.sh` | 递增 budget_used，80% 触发 Direction Check 警告，100% 报 EXHAUSTED |

**注意**：PreToolUse/Bash hook 对 sub-agent 同样生效（Claude Code hook 全局拦截），因此 worker agent 执行 `git merge --squash` 也会被拦截。`git merge --no-ff`（无 `--squash`）不受影响——执行阶段 Coordinator 合并 worktree 和 Multi-PR 合并都正常放行。

## 编辑注意

- 改 dispatch template 时检查 agent 定义的模式检测表和输入期望是否对齐
- 改 verdict 值时 `rg` 验证所有 producer 和 consumer 同步
- 改 disposition 表时同步所有 4 个 phase 文件（execution-pack-review-cycle / final-review-disposition / plan-review-resolution / merge-integration-review）
- 改 agent 定义的通用规则时检查所有相关 agent 是否需要同步
- dispatch template 中不放 agent 定义已有的行为规则（自检、TDD、Git 纪律等）
- 改 Forbidden Shortcuts 时同步 execution-review-dispatch.md 和 final-review-angles.md
- 改 NEEDS_EXECUTION 上限时同步 final-review-repair.md、final-review-completion.md、workflow-formal-orchestrate.md
- 改 disposition 的 `needs context` 前置检查时同步所有 5 个 disposition 文件（含 merge-integration-review.md）
- 改 Analyst ↔ Explorer 循环上限时同步 merge-rca-investigation.md
