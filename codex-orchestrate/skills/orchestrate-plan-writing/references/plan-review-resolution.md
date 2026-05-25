# Plan Review — Disposition + 修复 + 截断

> **流程位置**：`orchestrate-plan-writing` Steps 15-18 · Disposition + 修复 + 截断 · 通过后 → Step 19 回到 SKILL.md（Git Checkpoint）

## Step 15：接收 + Disposition

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

<!-- BEGIN: disposition-table -->
**Coordinator 亲验纪律** (disposition 之前的必经步骤):

收到 reviewer findings 后**禁止直接转发给 worker**。逐条执行：
1. 亲验：用 Read / grep / 对照设计文档验证 finding 的事实主张
2. Disposition：accepted / rejected / needs evidence / out of scope（调用 state.sh disposition append）
3. 修复指令：只把 accepted findings 翻译为具体修复指令传给 worker。Reviewer 原始输出不传

没有 disposition 的 finding 不能进入 repair。过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

**Confidence 校准** (Codex 返回 confidence 1-10):

| Confidence | Coordinator 默认动作 | 覆写条件 |
| --- | --- | --- |
| 8-10 (high) | 直接亲验，通常 accept 或 reject | Coordinator 找到反向证据 |
| 5-7 (medium) | 亲验 + 派 code_explorer 补证 -> 再定 disposition | -- |
| 1-4 (low) | 默认 suppress -> 记录为 "suppressed: low confidence" | Coordinator 手动升级并附证据 |

**Disposition 审计写入** (每条 finding 决定后立即调用):

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" disposition append \
  --run-id "<run_id>" --review-round <r> --finding-id <id> \
  --disposition <accepted|rejected|suppress|path-a|path-b> \
  --confidence <1-10> --severity <H|M|L> \
  --evidence "<一行理由>" --path "<file:line>"
```

`--evidence` 对 `--disposition accepted` 必填且非空。

**Disposition 表**:

| disposition | Coordinator 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 补证据（窄范围用 `code_explorer`，多模块用 `complex_code_explorer`）；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；**立即**开 GitHub issue（Durable Handoff Brief 格式，先查重） |
| `needs evaluation` | 不在当前 pack 可修范围但需独立评估；**立即**开 GitHub issue，标明评估要点 |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Path A re-review 规则** (仅 confidence >= 7 的 accepted findings):
- Coordinator Path A 直接修复 -> 强制 targeted Codex re-review
- Codex 返回 `needs_repair` -> 必须升级 Path B 派 worker
- 用 `state.sh path-a-escalation start/update/clear` 追踪
<!-- END: disposition-table -->

**`needs evidence` 补证**：派 `code_explorer`（窄范围单文件/单调用链）或 `complex_code_explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

Plan Review 的 `accepted` 细分为 5 种路由：

| `accepted` 子类型 | 动作 |
| --- | --- |
| `plan repair` | Coordinator 直接修框架性内容，或 send_input plan_writer 修 Task Pack 内容 |
| `design gap` | 回到 orchestrate-discovery → Design Review → 写回后 re-review plan |
| `issue-plan mismatch` | 判断：大 issue 级问题 → 返回 Coordinator 走大 issue 拆分；小 issue 级问题 → send_input plan_writer 重新执行 Step 3c 拆分 → re-review plan |
| `issue quality` | 小 issue 拆分质量问题（覆盖度/粒度/验收标准/依赖）→ send_input plan_writer 重新执行 Step 3c 修正小 issue → re-review plan |
| `architecture friction` | `Skill({ skill: "improve-codebase-architecture" })` → 写回后 re-review |

**通过** → Step 19（Git Checkpoint）。**Needs repair** → Step 16。

## Step 16：修复路由

<!-- BEGIN: repair-routing -->
**Finding-to-owner 修复分流 (REQUIRED)**：

这套规则在 reviewer 已经产出 finding、Coordinator 完成 disposition 之后使用。它不对 review 内容预先分风险等级，只根据 finding 的风险面、根因清晰度和修复形态选择 owner。

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 可自修；修完必须验证，Path A targeted re-review 失败时升级 Path B。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 使用 `send_input` resume 原 `pack_executor`；已有 agent_id 时不得新建同类 worker。 |
| 高风险或跨边界修复：跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板 | 使用 `send_input` resume 原 `complex_pack_executor`；若不是既有 pack 的 review finding，按首次定向修复派 `complex_pack_executor`。 |
| 根因不清，只知道症状 | 先派 `code_explorer` 或 `complex_code_explorer` 做只读补证；确认根因前不 patch。 |
| 系统性 bug、重复修复失败、未知 regression | 派 `root_cause_analyst`，要求列可证伪假设、排除证据和回归验证。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，附 affected plans / packs / 连接面 / producer-consumer 断点，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing；不得用代码 patch 代替 source artifact 修复。 |
| Release blocker | 简单且不碰合同边界可 Path A；涉及 migration / deploy order / rollback / permission / billing / runtime 时派 `complex_pack_executor`。 |
| Multi-PR 合并冲突 | 简单冲突可 Coordinator 修；跨 PR 合同、迁移、状态或依赖冲突派 `complex_pack_executor`；系统性冲突派 `root_cause_analyst`。 |

调度纪律：
- Targeted repair 必须优先 `send_input` 到原 agent；只有没有活跃原 agent 且不是已有 Pack review finding 的首次定向修复，才允许 `spawn_agent`。
- `Path A` 只适用于真正小范围修复；失败或 targeted re-review 返回 `needs repair` 时必须升级，不重复同一修法。
- `needs evidence` finding 先补证再决定 owner。
- 所有 repair prompt 只携带 accepted findings 和 Coordinator 亲验后的修复指令，不转发 reviewer 原始输出。
<!-- END: repair-routing -->

Plan Review 三条路径：

- **路径 A**（框架性内容：header / coverage map / scope check / 发布风险表）：Coordinator 直接修 → Step 17
- **路径 B**（Task Pack 内容：implementation tasks / verification / owned files / contract anchors）：

<!-- BEGIN: sendmessage-resume [variant=plan_writer] -->
**Plan-Writer send_input Resume 步骤**（plan_writer 修复）：

1. `state.sh read --run-id <run_id> --field '.plan_writer_agent_id'` 读取 workflow-state 中的 plan_writer_agent_id
2. 若返回 null/empty -> 立即标记 BLOCKED 给用户 + `state.sh transition --actor Coordinator --to blocked`（不允许创建新 agent）
3. 调用：
   ```
   send_input({
     target: "<plan_writer_agent_id>",
     message: "<含 DISPATCH_ENVELOPE 的修复 prompt，repair_round >= 1>"
   })
   ```
4. 等待原 agent 返回：`wait_agent({ targets: ["<plan_writer_agent_id>"], timeout_ms: 600000 })`
5. 解析返回结果 → `state.sh transition --actor Coordinator --to returned`
5b. 验证 plan 文件格式 + pack count validator
5c. `state.sh self-verify append --run-id <run_id> --repair-round <N> --verification-passed <yes|no>`
6. 回到 Plan Review 重审
<!-- END: sendmessage-resume -->

→ 重跑 Gate → Step 17
- **路径 C**（source artifact 问题）：Upstream backflow → 写回后 re-review

路径 C 路由表：

| Finding 类型 | Upstream | 写回目标 |
| --- | --- | --- |
| design gap / 需求不清 | orchestrate-discovery | design document |
| issue-plan mismatch | 大 issue 级：Coordinator 走大 issue 拆分；小 issue 级：send_input plan_writer Step 3c | issue hierarchy |
| issue quality | send_input plan_writer 重新执行 Step 3c | issue hierarchy（小 issue 章节） |
| architecture friction | `Skill({ skill: "improve-codebase-architecture" })` | design doc / plan anchors |
| domain 术语冲突 | `Skill({ skill: "grill-with-docs" })` | CONTEXT.md + design document |

## Step 17：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 14（读取 `plan-review-dispatch.md`），但：
- gate 名使用 `plan-review-repair-<round>`（`<round>` = 当前修复轮次 1/2），不覆盖 baseline 结果
- scope 缩小到：changed sections（修复涉及的 plan 章节）/ accepted findings（原 finding 是否解决）/ 受影响 angle

## Step 18：修复截断

Plan Review 最多 **2 个 repair round**。

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

---
> **下一步**：通过 → Step 19 回到 SKILL.md（Git Checkpoint）。BLOCKED → 返回 verdict。upstream backflow → 返回对应 phase。
