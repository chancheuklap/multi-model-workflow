---
name: orchestrate-plan-writing
description: "已有 reviewed source design 和 to-issues 产出的 vertical large issues / small issues 时主动使用。覆盖完整流程：前置条件确认 → 计划文档写作方法论 → 派发 plan-writer agent → Plan Entry Gate → Plan Review（单次 Codex 集成审查 + 修复）→ Git Checkpoint → 过渡到 orchestrate-execution。纯 Coordinator 线性流程：主线程按本技能逐步执行调度、review 接收、修复路由和进度追踪；plan-writer agent 通过 skills 字段自动加载本技能获取写作方法论。"
---

# Orchestrate Plan Writing

覆盖从设计文档到计划文档通过审查的完整流程。Coordinator 按本技能逐步执行——不由 Worker 或 Reviewer 消费。

**核心原则**：Source design + issue hierarchy → plan-writer 产出 vertical-slice plan → 单次 Codex 集成审查 → Coordinator 验证 + 修复 → Git Checkpoint → 进入 Execution。

**plan-writer agent 消费说明**：plan-writer 通过 `skills: ["orchestrate-plan-writing"]` 自动加载本技能。Agent 启动后读取 `references/plan-writing-methodology.md` 获取写作方法论（Steps 3-8）+ 修订流程 + Git 纪律 + 任务范围。

---

# 第一部分：前置条件确认

## Step 0：Re-entry 检测

检查是否存在已通过 Plan Review 的 plan 文档（来自上次执行 plan-writing 或跨会话恢复）。

| 条件 | 模式 | 下一步 |
| --- | --- | --- |
| 无已有 plan | **新建模式** | Step 1（正常流程） |
| 已有 plan + workflow 附带 `NEEDS_PLAN_REVISION` context（execution 打回） | **修订模式** | Step 0a |
| 已有 plan + 无修订 context | **新建模式**（忽略旧 plan，可能 scope 已变） | Step 1 |

### Step 0a：Plan 修订模式

Execution 返回 `NEEDS_PLAN_REVISION` 时，workflow 附带具体的 plan 问题描述。

1. 读取已有 plan 文档
2. 读取 workflow 附带的修订 context（哪些 pack 有问题、具体 findings）
3. 判断修订范围：

| 修订范围 | 路径 |
| --- | --- |
| 只需修改 plan header / coverage map / scope check / 发布风险表 | Coordinator 直接修 → 跳到 Step 11（Plan Entry Gate 重检） |
| 需修改 Task Pack 内容（implementation tasks / owned files / verification） | SendMessage 原 plan-writer（agentId 从 workflow context 获取）或新建 plan-writer，prompt 附带具体 findings + 现有 plan path → plan-writer 定向修订 → Step 11 |
| 修订揭示 design gap / issue mismatch | 返回 `NEEDS_DISCOVERY` / `NEEDS_ISSUES`（upstream backflow） |

4. 修订后重跑 Plan Entry Gate（Step 11）+ Task Pack Inventory Gate（Step 12）
5. 如果 pack_count 变化 → 更新 budget file（Step 12a）
6. 重跑 Plan Review（Step 13-18），scope 缩小到修改的部分（targeted re-review 优先）

## Step 1：验证输入完备性

派发前必须验证：
- source design / SPEC / PRD / bug brief 存在且已通过 Design Review（或等价 review）
- `to-issues` 产出的 vertical large issues 和 vertical small issues 已就绪

缺件时路由：

| 缺件 | 返回 | 路由 |
| --- | --- | --- |
| 无 source design | `NEEDS_DISCOVERY` | orchestrate-discovery |
| design 未 review | `NEEDS_DESIGN_REVIEW` | Design Review |
| 缺 large/small issue | `NEEDS_ISSUES` | to-issues |
| issue ready state 不清 | `NEEDS_TRIAGE` | triage |
| 业务术语或验收不清 | `NEEDS_DISCOVERY` | orchestrate-discovery |
| bug 缺复现或 hypothesis | `NEEDS_DIAGNOSIS` | diagnose |
| 需要方案比较 | `NEEDS_DECISION` | user / prototype |
| 架构摩擦反复阻塞 | `NEEDS_ARCHITECTURE` | improve-codebase-architecture |
| 模块地图不足 | `NEEDS_CONTEXT` | zoom-out / code-explorer |

## Step 2：验证 Scope Contract + Budget File

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）。验证 editable artifacts 包含 plan 保存路径和 source design path。

**Budget File**：读取 `.claude/multi-model-workflow/active-run-id` 找到 budget file，记录当前 `budget_used`。Plan-writing 阶段会消耗 Plan Review dispatch（1-2 次，含修复后的 targeted re-review）。

---

# 第二部分：计划文档写作方法论

**详细内容见 `references/plan-writing-methodology.md`**（Steps 3-8 + 自检 + 修订流程 + Git 纪律 + 任务范围）。

Coordinator 按该文件内容构造 plan-writer dispatch prompt；plan-writer agent 启动后读取该文件执行写作。

核心流程概要：Step 3（读 design + issues + 代码库）→ Step 4（文件结构）→ Step 5（Plan Header）→ Step 6（Task Pack）→ Step 7（Implementation Tasks）→ Step 8（自检：过度设计 / 设计不足 / Coverage）。

---

# 第三部分：Plan-writer 派发协议

## Step 9：构造 Plan-writer Dispatch Brief

Dispatch prompt 必须自足——plan-writer 通过 skills 自动加载读取第二部分方法论，但 Coordinator 仍需在 prompt 中写清所有输入 artifact 路径和上下文。

```
Agent({
  subagent_type: "plan-writer",
  description: "Write implementation plan: <feature>",
  prompt: "
    ## Goal
    从 source design + issue hierarchy 写出 implementation plan。

    ## Source artifacts
    - Source design: <path>（已通过 Design Review）
    - Issue hierarchy:
      - Large issues: <path(s) + titles>
      - Small issues: <listed in large issue docs, or separate paths>
    - Scope Contract: <path>
    - CLAUDE.md: <project root>/CLAUDE.md

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/YYYY-MM-DD-<feature>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    - Design Review 中 reviewer 的重点建议: <paste if any>
    - 用户偏好 / 架构决策: <paste if any>
    - 已知 gotcha / 路径变更: <paste if any>

    ## Out of scope
    - <explicitly list what NOT to include>
    - 不自创 issue——只消费 to-issues 产出的 issue hierarchy

    ## Return contract
    ### Verdict
    PLAN_CREATED / NEEDS_DISCOVERY / NEEDS_ISSUES / NEEDS_TRIAGE /
    NEEDS_DIAGNOSIS / NEEDS_DECISION / NEEDS_ARCHITECTURE / NEEDS_CONTEXT / BLOCKED
    ### Plan path
    ### Issue mapping
    ### Quality gate
    ### Open items
  "
})
```

**记录返回的 agentId**——后续修复可能需要 SendMessage 继续该 plan-writer（保有 design + issue 上下文）。

## Step 10：处理 Plan-writer 返回

Plan-writer 返回以下状态：

| Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `PLAN_CREATED` | plan 写完，自检通过 | 进入 Step 11（Plan Entry Gate） |
| `NEEDS_DISCOVERY` | 业务意图/术语不清 | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 缺 issue / issue 粒度不足 / scope 过大 | 调用 to-issues |
| `NEEDS_TRIAGE` | issue ready state 不清 | 调用 triage |
| `NEEDS_DIAGNOSIS` | bug 缺复现或 hypothesis | 调用 diagnose |
| `NEEDS_DECISION` | 需要产品/业务决策 | 询问用户（一次只问一个问题） |
| `NEEDS_ARCHITECTURE` | 架构假设与代码现实不符 | 调用 improve-codebase-architecture |
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 code-explorer / 调用 zoom-out，补充后 SendMessage 给原 plan-writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan-writer 的阻塞原因 |

upstream skill 结论必须写回 design document / issue hierarchy，再 SendMessage 给原 plan-writer 继续。

---

# 第四部分：Plan Entry Gate + Task Pack Inventory Gate

## Step 11：Plan Entry Gate

Plan 必须包含以下字段，缺失则 needs repair（SendMessage plan-writer 修复）：
- Source design（path + 已 reviewed 确认）
- Source issues（paths）
- Execution owner: Orchestrate Workflow
- Plan unit 定义
- Completion gate
- Source Coverage Map（每条 source intent 有对应 Task Pack）
- File / Responsibility Map
- 发布风险和人工门禁表

声称 issue-backed 但缺 issues → `NEEDS_ISSUES` → to-issues。
多余 handoff owner / 非 Orchestrate Workflow 的 execution owner → needs repair。

## Step 12：Task Pack Inventory Gate

每个 pack 必须满足：

| 必须有 | 不能进 Execution 的 pack |
| --- | --- |
| 对应 confirmed small issue | 横切 pack（不是 vertical slice） |
| vertical slice 可独立验证 | 前后端分层不能单独验证 |
| owned files + 每文件职责 | UI 只写"实现 mockup"无状态/交互 |
| acceptance criteria（从 issue 映射） | 缺目标行为需 worker 猜 |
| verification commands（pack-local） | 多 worker 写同一文件 |
| contract anchors（触碰合同时） | 只写 helper 无 public behavior |
| mockup anchors（UI 时） | 需人工决策却标 AFK |
| commit boundary | — |
| risk flags | — |
| dependencies + parallel safety | — |

不通过的 pack → SendMessage 给 plan-writer 修复 → 重新检查。

## Step 12a：更新 Budget File

Task Pack Inventory Gate 通过后，pack_count 已确认。立即更新 budget file：

```json
{
  "pack_count": N,
  "budget_total": "2N + 12"
}
```

公式推导：`(Discovery baseline: 2 + Plan-writing baseline: 1 + Pack Reviews: N + Final Review: 2) × 2 + Release gate max: 2 = 2N + 12`。

**这是 budget_total 的首次有效赋值**——workflow entry gate 创建时写 0（pack_count 未知），此处确认。Workflow 在 plan-writing 返回后做确认性写入。

---

# 第五部分：Plan Review

## Step 13：Budget Check

派发前读 budget file，确认 `budget_used + 1 ≤ budget_total`。达到 80% 时触发 Direction Check（重述 current phase / 剩余工作 / 累计 findings / 是否继续）。超过预算时停止并报告用户。

## Step 14：派发 Codex Reviewer

读取 `references/plan-review-dispatch.md` 构建 dispatch prompt。通过 `codex:codex-rescue --model gpt-5.4` 派发 1 个 baseline reviewer，整合 Coverage & Task Quality / Compliance & Verification / Cross-Verification 三个角度。

Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction。

---

# 第六部分：Coordinator 验证 + Disposition

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

**Plan Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ 跳到 Step 19（Git Checkpoint）。

**Plan Review needs repair**（有 accepted finding）→ 进入 Step 16。

---

# 第七部分：修复分流

## Step 16：修复路由

所有 repair prompt 只携带 accepted findings，不夹带 rejected / out-of-scope / low-confidence observations。

### 路径 A：Coordinator 直接修复

**条件**：Plan header、coverage map、scope check、发布风险表、dependency chain 等框架性内容。

1. Coordinator 读 finding、对照 source artifacts
2. 直接修改 plan 文档
3. 验证修改与 source design / issues 一致
4. 进入 Step 17（Targeted Re-Review）

### 路径 B：SendMessage 给 plan-writer agent

**条件**：Task Pack 内容、implementation tasks、verification commands、owned files、contract anchors 等写作细节——plan-writer 保有 design + issue 上下文。

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

upstream skill 结论写回后，根据影响范围决定是 re-review plan 还是 re-run plan-writing。

### 修复归属快速判定

| 信号 | 路径 |
| --- | --- |
| "coverage map 缺 intent X" / "发布风险表遗漏 pack Y" | A（Coordinator 直接修） |
| "Task Pack 3.1 的 verification command 不存在" / "owned files 遗漏 migration" | B（SendMessage plan-writer） |
| "source design 没定义这个行为" / "issue acceptance 与 design intent 矛盾" | C（Upstream backflow） |
| accepted finding 涉及 migration / billing / permission / shared contract | B（用 plan-writer 修，因为涉及 pack 写作细节） |

---

# 第八部分：Targeted Re-Review + 修复截断

## Step 17：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 14，但 scope 缩小到：
- changed sections（修复涉及的 plan 章节）
- accepted findings（原 finding 是否解决）
- 受影响 angle（coverage / compliance / cross-verification 中与修复相关的）

## Step 18：修复预算 + 截断

**修复预算**：Plan Review 最多 **2 个 repair round**（含 Coordinator 直接修和 plan-writer 修复）。这是 per-phase 上限；全局 review budget 优先——Direction Check 在 80% 时触发，可能在 plan 用满 2 轮之前就要求停下来评估方向。

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

2 轮修复后仍 needs repair 通常意味着 plan 的基础输入（design / issues）有问题，继续在 plan 层修补无意义。

---

# 第九部分：Git Checkpoint

## Step 19：提交 Plan 文档

Plan Review 通过后（+ 所有 Gate 通过）：

1. `git add <plan doc path>`——stage plan 文档
2. `git commit -m "Plan: <feature> — reviewed implementation plan"`
3. Commit boundary = 回退边界：如果后续 execution 阶段需要回到 plan，可以 revert 到这个 commit

**规则**：
- Plan-writer 不 commit；Coordinator 在 Plan Review 通过后统一 commit
- 不 stage 不属于当前 scope 的 dirty files
- Design doc repair（如有）和 plan doc 分别提交——不混在一个 commit 里

---

# 第十部分：过渡到 Execution + 返回格式

## Step 20：Plan Review 通过

Plan Review 通过 + Git Checkpoint 完成后，返回 verdict。orchestrate-workflow 将路由到 orchestrate-execution。

## 上游 Route Payload

需要交回 `to-issues` 时：

```text
Upstream route: to-issues
Source design:
Parent large issue:
Issue recording target:
Why current issue boundary is insufficient:
Suggested vertical slices:
这些 slices 只是建议；必须等 to-issues 运行并写回后，才能成为正式 issue / Task Pack。
```

## 返回格式

```text
### Verdict
PLAN_CREATED | NEEDS_DISCOVERY | NEEDS_DESIGN_REVIEW | NEEDS_ISSUES | NEEDS_TRIAGE | NEEDS_DIAGNOSIS | NEEDS_DECISION | NEEDS_ARCHITECTURE | NEEDS_CONTEXT | BLOCKED

### Plan path
- <保存路径>

### Plan Review
- Review dispatched: <count>
- Findings dispositioned: <count>
- Repairs applied: <count>
- Repair rounds used: <N> / 2

### Issue mapping
- Large issues: <count and titles>
- Task Packs: <count>
- Dependencies: <dependency chain summary>

### Quality gate
- Overdesign checked: yes + findings or clean
- Underdesign checked: yes + findings or clean
- Coverage checked: yes + findings or clean
- Type consistency checked: yes + findings or clean
- Largest remaining risk:

### Git state
- Commits: <plan commit hash>
- Branch: <current branch>
- Clean: yes / no

### Open items
- Blockers / HITL:
- Needs context: <具体缺什么>

### Next route
- orchestrate-execution / upstream route / user decision / blocked
```
