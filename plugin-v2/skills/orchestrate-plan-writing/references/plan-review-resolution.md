# Plan Review — Disposition + 修复 + 截断

> **流程位置**：`orchestrate-plan-writing` Steps 15-18 · Disposition + 修复 + 截断 · 通过后 → Step 19 回到 SKILL.md（Git Checkpoint）

## Step 15：接收 Review Findings

**Coordinator 不是传话筒**——必须主动验证 finding 的正确性：

1. **读 plan + 代码**：检查 reviewer 说的是否与 plan 内容和代码事实一致
2. **对照 source artifacts**：reviewer 说 coverage 缺失 → 对照 source design 和 issue hierarchy 确认
3. **跑 grep/find**：reviewer 说路径不存在 → 自己验真
4. **用自己的判断力质疑和确认**：不因为 reviewer 说了就当真

逐条 disposition：

| Disposition | 动作 |
| --- | --- |
| `accepted — plan repair` | Coordinator 直接修 plan 框架性内容（header、coverage map、scope check、发布风险表），或 SendMessage plan-writer 修 Task Pack 内容 |
| `accepted — design gap` | 回到 orchestrate-discovery → Design Review → 写回后 re-review plan |
| `accepted — issue-plan mismatch` | 调用 to-issues → 写回后 re-review plan |
| `accepted — architecture friction` | 调用 improve-codebase-architecture → 写回后 re-review |
| `rejected` | 记录反证；不 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 `code-explorer` / `complex-code-explorer` 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding / issue / commit；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计/计划/发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Plan Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ Step 19（Git Checkpoint）。

**Plan Review needs repair** → Step 16。

## Step 16：修复路由

所有 repair prompt 只携带 accepted findings，不夹带 rejected / out-of-scope / low-confidence observations。

### 路径 A：Coordinator 直接修复

**条件**：Plan header、coverage map、scope check、发布风险表、dependency chain 等框架性内容。

1. Coordinator 读 finding、对照 source artifacts
2. 直接修改 plan 文档
3. 验证修改与 source design / issues 一致
4. 进入 Step 17（Targeted Re-Review）

### 路径 B：SendMessage 给 plan-writer agent

**条件**：Task Pack 内容、implementation tasks、verification commands、owned files、contract anchors 等写作细节。

1. 检查 SendMessage 是否可用（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）
2. 可用 → SendMessage 给 saved agentId，附 accepted findings + 修复方向
3. 不可用 → 新建 `plan-writer` agent，prompt 含 accepted findings + plan path + source design path + issue paths
4. Plan-writer 修复后返回 → 重跑 Plan Entry Gate + Task Pack Inventory Gate → 进入 Step 17

### 路径 C：Upstream Backflow

**条件**：finding 揭示的不是 plan 问题，而是 source artifact 问题。

| Finding 类型 | Upstream | 写回目标 | 回到 |
| --- | --- | --- | --- |
| design gap / 需求不清 | orchestrate-discovery | design document | Plan Review re-review |
| issue-plan mismatch | to-issues | issue hierarchy | Plan-writing re-run |
| architecture friction | improve-codebase-architecture | design doc / plan anchors | Plan Review re-review |
| domain 术语冲突 | grill-with-docs | CONTEXT.md + design document | Plan Review re-review |

### 修复归属快速判定

| 信号 | 路径 |
| --- | --- |
| "coverage map 缺 intent X" / "发布风险表遗漏 pack Y" | A（Coordinator 直接修） |
| "Task Pack 3.1 的 verification command 不存在" / "owned files 遗漏 migration" | B（SendMessage plan-writer） |
| "source design 没定义这个行为" / "issue acceptance 与 design intent 矛盾" | C（Upstream backflow） |
| accepted finding 涉及 migration / billing / permission / shared contract | B（用 plan-writer 修） |

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
| 项目规则 / 代码现实 mismatch | 调用 improve-codebase-architecture 或 zoom-out 补充上下文后 re-run |
