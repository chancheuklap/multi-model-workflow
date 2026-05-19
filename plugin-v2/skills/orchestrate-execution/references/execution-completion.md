# Git Checkpoint + 并行合并 + Backflow + 进度

> **流程位置**：`orchestrate-execution` Steps 13-16 · Release Gate 条件触发时先读取 `execution-release-gate.md`

## Step 13：Early Release Gate（条件触发）

Pack Review 通过后，检查该 pack 是否触碰发布风险面（migration / deploy order / rollback / manual production gate / billing / permission / runtime）。

- **触发** → 读取 `execution-release-gate.md` 执行 Release Gate 流程
- **不触发** → 继续 Step 14

## Step 14：Git Checkpoint

1. `git add <owned files + test files + plan doc>`
2. `git commit -m "<Pack N.M: title — summary of behavior>"`
3. Commit boundary = 回退边界

**规则**：Worker 不 commit；Coordinator 统一提交。不 stage 非当前 scope 文件。Design/plan repair、Task Pack、finding repair 分别提交。

## Step 15：合并并行 Pack 的 Worktree

并行 pack 各自通过 Pack Review 后，按依赖顺序逐个合并：

1. 确定合并顺序（按 plan 中的 dependencies）
2. `git merge <worktree-branch> --no-ff`
3. 冲突处理：简单 → Coordinator 直接解决；复杂 → 新建 targeted-repair agent
4. 每次 merge 后跑完整测试
5. 全部 merge 完后再跑一次确认集成正确

**合并策略铁律**：只用 `git merge --no-ff`，**绝对禁止 squash merge（`--squash`）和 rebase（`--rebase`）**。完整保留每个 worktree 分支的 commit 历史。

**不并行合并**——串行避免 merge conflict 级联。

## Backflow + Upstream Skill 路由

| 问题类型 | Upstream Skill | 写回目标 |
| --- | --- | --- |
| design / domain gap | `Skill({ skill: "multi-model-workflow:orchestrate-discovery" })` | design document |
| architecture friction | `Skill({ skill: "improve-codebase-architecture" })` | design doc / plan anchors |
| 术语 / domain 冲突 | `Skill({ skill: "grill-with-docs" })` | domain docs + design document |
| module map / call chain | `Skill({ skill: "zoom-out" })` | plan anchors / explorer brief |
| bug reproduction / hypothesis | `Skill({ skill: "diagnose" })` | bug brief / design document |

**影响范围判定**：只影响当前 pack → 写回继续 / 改变 plan anchors → 回到 orchestrate-plan-writing / 暴露 design 缺口 → 回到 orchestrate-discovery。

## Plan Checkbox 维护

每个 pack 通过后勾选 plan 中的 implementation tasks + 更新 Coverage Map。Coordinator 验证 checkbox state 与 git diff 一致。

## 进度汇报

每完成 2-3 个 pack 后一行 FYI。不做长篇汇报。

## Re-Entry from Final Review

Final Review 打回时：按修复分流三条路径（读取 `execution-repair-truncation.md`）处理 → targeted re-review → Git Checkpoint → 返回 Final Review。不重新执行所有 pack。

## 不存在"非阻塞项"

**铁律。** 所有东西要么当场修复，要么立刻开 GitHub issue。Worker 说"先跳过"→ 不接受。Reviewer 说"Minor, not blocking" → Coordinator 仍需 disposition。

---
> **下一步**：所有 pack 完成且无阻塞 → 回到 SKILL.md 返回区确定 verdict 并返回给 orchestrate-workflow。
