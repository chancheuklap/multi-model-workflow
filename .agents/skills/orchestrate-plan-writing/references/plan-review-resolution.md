# Plan Review — Disposition + 修复 + 截断

> **流程位置**：`orchestrate-plan-writing` Steps 15-18 · Disposition + 修复 + 截断 · 通过后 → Step 19 回到 SKILL.md（Git Checkpoint）

## Step 15：接收 + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch（budget 消耗 +1），不进入 per-finding disposition。

收到 finding 后，Coordinator 不是传话筒——必须亲验每条 finding 的正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 按下方 4 种子类型路由 |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 补证据（窄范围用 `code-explorer`，多模块用 `complex-code-explorer`）；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；**立即**开 GitHub issue（Durable Handoff Brief 格式，先查重） |
| `needs evaluation` | 不在当前 pack 可修范围但需独立评估；**立即**开 GitHub issue，标明评估要点 |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**`needs evidence` 补证**：派 `code-explorer`（窄范围单文件/单调用链）或 `complex-code-explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

Plan Review 的 `accepted` 细分为 4 种路由：

| `accepted` 子类型 | 动作 |
| --- | --- |
| `plan repair` | Coordinator 直接修框架性内容，或 SendMessage plan-writer 修 Task Pack 内容 |
| `design gap` | 回到 orchestrate-discovery → Design Review → 写回后 re-review plan |
| `issue-plan mismatch` | `Skill({ skill: "to-issues" })` → 写回后 re-review plan |
| `architecture friction` | `Skill({ skill: "improve-codebase-architecture" })` → 写回后 re-review |

**通过** → Step 19（Git Checkpoint）。**Needs repair** → Step 16。

## Step 16：修复路由

Plan Review 三条路径：

- **路径 A**（框架性内容：header / coverage map / scope check / 发布风险表）：Coordinator 直接修 → Step 17
- **路径 B**（Task Pack 内容：implementation tasks / verification / owned files / contract anchors）：SendMessage plan-writer（或新建）→ 重跑 Gate → Step 17
- **路径 C**（source artifact 问题）：Upstream backflow → 写回后 re-review

路径 C 路由表：

| Finding 类型 | Upstream | 写回目标 |
| --- | --- | --- |
| design gap / 需求不清 | orchestrate-discovery | design document |
| issue-plan mismatch | `Skill({ skill: "to-issues" })` | issue hierarchy |
| architecture friction | `Skill({ skill: "improve-codebase-architecture" })` | design doc / plan anchors |
| domain 术语冲突 | `Skill({ skill: "grill-with-docs" })` | CONTEXT.md + design document |

## Step 17：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 14（读取 `plan-review-dispatch.md`），但 scope 缩小到：
- changed sections（修复涉及的 plan 章节）
- accepted findings（原 finding 是否解决）
- 受影响 angle（coverage / compliance / cross-verification 中与修复相关的）

## Step 18：修复预算 + 截断

**修复预算**：Plan Review 最多 **2 个 repair round**。全局 review budget 优先——Direction Check 在 80% 时触发。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2（截断） | 仍 needs repair → **截断**。判定原因 |

**截断路由**：

| 判定 | 下一步 |
| --- | --- |
| Plan 层面问题（结构、coverage、task quality） | BLOCKED，报告用户附 2 轮 findings 汇总 |
| Source artifact 问题（design gap / issue mismatch） | 强制 upstream backflow（路径 C） |
| 项目规则 / 代码现实 mismatch | `Skill({ skill: "improve-codebase-architecture" })` 或 `Skill({ skill: "zoom-out" })`补充上下文后 re-run |
