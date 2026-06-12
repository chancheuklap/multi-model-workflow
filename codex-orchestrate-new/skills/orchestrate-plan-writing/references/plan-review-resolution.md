# Plan Review — Disposition + 修复 + 截断

> **流程位置**：`orchestrate-plan-writing` Steps 15-18 · Disposition + 修复 + 截断 · 通过后 → Step 19 回到 SKILL.md（Git Checkpoint）

## Step 15：接收 + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/disposition-table.md` 并按其 disposition 选项处理 findings（含 `needs evidence` 补证的 explorer 选型 + prompt + 返回契约）。

Plan Review 的 `accepted` 细分为 5 种路由：

| `accepted` 子类型 | 动作 |
| --- | --- |
| `plan repair` | Coordinator 直接修框架性内容，或 send_input plan_writer 修 Task Pack 内容 |
| `design gap` | 回到 orchestrate-discovery → Design Review → 写回后 re-review plan |
| `issue-plan mismatch` | 判断：大 issue 级问题 → 返回 Coordinator 走大 issue 拆分；小 issue 级问题 → send_input plan_writer 重新执行 Step 3c 拆分 → re-review plan |
| `issue quality` | 小 issue 拆分质量问题（覆盖度/粒度/验收标准/依赖）→ send_input plan_writer 重新执行 Step 3c 修正小 issue → re-review plan |
| `architecture friction` | `加载 skill `improve-codebase-architecture`` → 写回后 re-review |

**通过** → Step 19（Git Checkpoint）。**Needs repair** → Step 16。

## Step 16：修复路由

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

Plan Review 三条路径：

- **路径 A**（框架性内容：header / coverage map / scope check / 发布风险表）：Coordinator 直接修 → Step 17
- **路径 B**（Task Pack 内容：implementation tasks / verification / owned files / contract anchors）：

<!-- BEGIN: send-input-resume [variant=plan_writer] -->
**Plan-Writer send_input Resume 步骤**（plan_writer 修复）：

1. `state.sh read --run-id <run_id> --field '.plan_writer_agent_id'` 读取 workflow-state 中的 plan_writer_agent_id
2. 若返回 null/empty -> 立即标记 BLOCKED 给用户 + `state.sh transition --actor Coordinator --to blocked`（不允许创建新 agent）
3. 恢复并发送：
   ```
   resume_agent({ id: "<plan_writer_agent_id>" })
   send_input({
     target: "<plan_writer_agent_id>",
     message: "<DISPATCH_ENVELOPE>\n\n修复任务：包含 accepted findings、Coordinator 亲验证据、需要修改的 plan/issue sections、verification commands 和 Return Contract。"
   })
   ```
   send_input inline 发送完整修复 prompt，直接写入 `message` 字段，不先写到文件再引用。
4. `wait_agent({targets:["<plan_writer_agent_id>"], timeout_ms:600000})` 等待 final message；如 agent 仍需继续修，重复 resume + send_input，不新建 plan_writer
5. 解析返回结果 → `state.sh transition --actor Coordinator --to returned`
5b. 验证 plan 文件格式 + pack count validator
6. 回到 Plan Review 重审

Compaction recovery: 从 `workflow-state.cursor` + plan/design 文档重建 repair context；dispatch prompt 不需要 durable copy。
<!-- END: send-input-resume -->

→ 重跑 Gate → Step 17
- **路径 C**（source artifact 问题）：Upstream backflow → 写回后 re-review

路径 C 路由表：

| Finding 类型 | Upstream | 写回目标 |
| --- | --- | --- |
| design gap / 需求不清 | orchestrate-discovery | design document |
| issue-plan mismatch | 大 issue 级：Coordinator 走大 issue 拆分；小 issue 级：send_input plan_writer Step 3c | issue hierarchy |
| issue quality | send_input plan_writer 重新执行 Step 3c | issue hierarchy（小 issue 章节） |
| architecture friction | `加载 skill `improve-codebase-architecture`` | design doc / plan anchors |
| domain 术语冲突 | `加载 skill `grill-with-docs`` | CONTEXT.md（或 CONTEXT-MAP.md 对应子 context 文件） + design document |

## Coordinator checkbox toggle 权威规则（D4 source-of-truth）

Plan Implementation Review pass 后，Coordinator Edit plan 文档勾选 checkbox 的 source-of-truth 是 `plan-return.per_pack[*]` where `status == committed`：
1. Read `.codex/multi-model-workflow/plan-returns/<run_id>/<plan_id>/plan-return.json`
2. 对每个 `per_pack[i].status == "committed"` 的 Pack，按 Pack ID 精确匹配 `docs/orchestrate/plans/<slug>/<plan-file>.md` 中该 Pack body 首行的 `- [ ] **Pack N.M**` 完成 checkbox（不是 `## Pack Execution Manifest` 表行——表行是 Worker 入口查询表，无 checkbox），Edit toggle 为 `- [x] **Pack N.M**`。脚本 `state.sh checkbox toggle` 已实现此精确匹配
3. `status` 不是 `committed`（pending / in_progress / blocked / skipped）的 Pack 不勾选

## Step 17：Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 14（读取 `plan-review-dispatch.md`），但：
- gate 名使用 `plan-review-repair-<round>`（`<round>` = 当前修复轮次 1/2），不覆盖 baseline 结果
- scope 缩小到：changed sections（修复涉及的 plan 章节）/ accepted findings（原 finding 是否解决）/ 受影响 angle

## Step 18：修复截断

Plan Review repair 轮次上限由 `routes-v1.json` 的 `repair_policy.max_repair_rounds`（plan-review phase）持有，`enforce-repair-round-cap.sh` hook 机器强制——超限 Re-Review 派发被 exit 2 拦截。当前值：`max_repair_rounds=2, escalate_to_rca=false`（等价于旧散文的"最多 2 个 repair round"）。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2（截断） | 仍 needs repair → **截断**。判定原因 |

**截断路由**：

| 判定 | 下一步 |
| --- | --- |
| Plan 层面问题（结构、coverage、task quality） | BLOCKED，报告用户附 2 轮 findings 汇总 |
| Source artifact 问题（design gap / issue mismatch） | 强制 upstream backflow（路径 C） |
| 项目规则 / 代码现实 mismatch | `加载 skill `improve-codebase-architecture`` 补充上下文后 re-run |

---
> **下一步**：通过 → Step 19 回到 SKILL.md（Git Checkpoint）。BLOCKED → 返回 verdict。upstream backflow → 返回对应 phase。
