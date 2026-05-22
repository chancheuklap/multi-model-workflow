---
name: orchestrate-plan-writing
description: "已有 reviewed design + issue hierarchy 时使用。派 plan-writer → Plan Entry Gate → Plan Review → Git Checkpoint。产出：reviewed plan + Task Pack inventory + budget_total。"
---

# Orchestrate Plan Writing

Source design + issue hierarchy → **逐个 issue 派发 plan-writer** → 全部 plan 写完后 Plan Review → Git Checkpoint → 进入 Execution。

**每个大 issue 对应一份 plan 文件**。Coordinator 读取 `issues/<slug>/` 目录，逐个 issue 派发 plan-writer，每个 plan-writer 只写一份 plan。Plan 文件编号与 issue 文件编号一一对应。

**Only stop for：**
- Plan-writer 返回 upstream verdict 需要用户决策
- BLOCKED

**Never stop for：**
- Issue 之间的切换（连续逐 issue 派发 plan-writer）
- Plan Review findings（按修复分流处理）

---

**Pre-plan-writing（进入前快速验证）：**
- [ ] Design Review 通过
- [ ] Issue hierarchy 已就绪（docs/orchestrate/issues/<slug>/）
- [ ] Scope Contract 和 Budget file 存在
- [ ] Budget 状态锚写入：`current_phase = plan-writing`

**Dispatch 协议**：所有 plan-writer Agent 调用必须使用 `run_in_background: true`，以确保 Coordinator 能获取 agentId 用于后续 SendMessage 修复路径。

---

## Step 0：Re-entry 检测

| 条件 | 下一步 |
| --- | --- |
| 无已有 plan | Step 1 |
| 已有部分 plan + `NEEDS_PLAN_REVISION` context | 读取 `references/plan-preconditions.md` 修订模式 → Step 11 |
| 已有全部 plan + 无修订 context | Step 1（忽略旧 plan） |

## Steps 1-2：前置条件

验证 source design 已 reviewed + issue hierarchy 已就绪 + Scope Contract + Budget File 存在。缺件时 **Read** `references/plan-preconditions.md` 路由。读完进入 Steps 3-8 方法论。

## Steps 3-8：写作方法论

**Read** `references/plan-writing-methodology.md`（plan-writer 消费；Coordinator 按此理解 plan 结构，为 dispatch brief 构造做准备）。Coordinator 理解后进入 Steps 9-10 派发。

<!-- BEGIN: control-envelope -->
## DISPATCH_ENVELOPE (required prefix for every Agent dispatch)

Every `Agent({...})` dispatch and every `SendMessage({...})` repair MUST begin its `prompt` with:

```
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "<run_id>",
  "phase": "<plan-writing|execution|final-review|discovery>",
  "agent_role": "<pack-executor|complex-pack-executor|plan-writer|codex-reviewer>",
  "agent_id": "<existing agent_id or null for first dispatch>",
  "pack_id": "<N.M or null>",
  "repair_round": 0,
  "idempotency_key": "<run_id>/<pack_id>/r<repair_round>",
  "disposition_refs": null,
  "review_intent": null,
  "exception_code": null
}
-->
```

For repair (repair_round >= 1): set `disposition_refs` to array of accepted finding IDs.
For codex-reviewer dispatches: set `review_intent` and `exception_code` for targeted-re-review.

Hooks parse this block. Missing/malformed envelope = dispatch BLOCKED.
<!-- END: control-envelope -->

## Steps 9-10：逐 issue 派发 plan-writer + 处理返回

**Read** `references/plan-writer-dispatch.md` 并严格执行。派发后进入 Steps 11-12a gate。

Coordinator 列出 `docs/orchestrate/issues/<slug>/` 目录下的所有大 issue 文件（`001-*.md, 002-*.md, ...`），然后**逐个 issue 派发 plan-writer**：

1. 按 issue 编号顺序遍历
2. 每次派发一个 plan-writer，传入设计文档 + 当前这个 issue 文件
3. plan-writer 写出 `docs/orchestrate/plans/<slug>/00N-<issue-slug>.md`（编号与 issue 文件对应）
4. 处理 plan-writer 返回（verdict 路由见 dispatch 文档）
5. 下一个 issue，直到全部完成

全部 plan-writer 返回 `PLAN_CREATED` 后，进入 Step 11。任一 plan-writer 返回 upstream verdict → 按 verdict 路由处理后重新进入。

## Steps 11-12a：Plan Entry Gate + Task Pack Inventory Gate + Budget 赋值

**Read** `references/plan-gates.md`（对 `plans/<slug>/` 下所有 plan 文件做 gate 检查 + budget_total 首次赋值 `3P + 12`，P = plan 文件总数）。通过后进入 Steps 13-14 review。

## Steps 13-14：Plan Review

**Read** `references/plan-review-dispatch.md`，按其中的 Codex review 派发步骤提交。派发后进入 Steps 15-18 disposition。

<!-- BEGIN: disposition-table -->
**Coordinator 亲验纪律** (disposition 之前的必经步骤):

收到 reviewer findings 后**禁止直接转发给 worker**。逐条执行：
1. 亲验：用 Read / grep / 对照设计文档验证 finding 的事实主张
2. Disposition：accepted / rejected / needs evidence / out of scope（调用 state.sh disposition append）
3. 修复指令：只把 accepted findings 翻译为具体修复指令传给 worker。Reviewer 原始输出不传

**Confidence 校准** (Codex 返回 confidence 1-10):

| Confidence | Coordinator 默认动作 | 覆写条件 |
| --- | --- | --- |
| 8-10 (high) | 直接亲验，通常 accept 或 reject | Coordinator 找到反向证据 |
| 5-7 (medium) | 亲验 + 派 code-explorer 补证 -> 再定 disposition | -- |
| 1-4 (low) | 默认 suppress -> 记录为 "suppressed: low confidence" | Coordinator 手动升级并附证据 |

**Disposition 审计写入** (每条 finding 决定后立即调用):

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" disposition append \
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
| `rejected` | 记录反证；不派 repair |
| `needs evidence` | 派 explorer 补证据 |
| `duplicate / already covered` | 链到已有 finding |
| `out of scope` | 开 GitHub issue（Durable Handoff Brief） |
| `needs evaluation` | 开 GitHub issue |
| `user decision` | 停止执行，一次只问一个决策问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Path A re-review 规则** (仅 confidence >= 7 的 accepted findings):
- Coordinator Path A 直接修复 -> 强制 targeted Codex re-review
- Codex 返回 `needs_repair` -> 必须升级 Path B 派 worker
- 用 `state.sh path-a-escalation start/update/clear` 追踪
<!-- END: disposition-table -->

## Steps 15-18：Disposition + 修复 + 截断

**Read** `references/plan-review-resolution.md`（Coordinator 亲验 → disposition → 修复路由 A/B/C → 最多 2 轮 → 截断路由）。通过后回到 Step 19 Git Checkpoint。

## Step 19：Git Checkpoint

`git add` + `git commit`。Plan-writer 不 commit；Coordinator 统一提交。Design doc repair 和 plan doc 分别提交。

---

**Required before returning（返回前验证）：**
- [ ] 所有 issue 的 plan 文件已写完
- [ ] Plan Entry Gate + Task Pack Inventory Gate 通过
- [ ] budget_total 已赋值（3P + 12）
- [ ] Plan Review 通过
- [ ] Git Checkpoint 完成
- [ ] Budget 状态锚更新：`current_phase = plan-writing_done`

## Step 20：返回

```text
### Verdict
PLAN_CREATED | NEEDS_DISCOVERY | NEEDS_DESIGN_REVIEW | NEEDS_ISSUES |
NEEDS_TRIAGE | NEEDS_DIAGNOSIS | NEEDS_DECISION | NEEDS_ARCHITECTURE |
NEEDS_CONTEXT | BLOCKED

### Plan directory + file count
### Plan Review
- Review dispatched / Findings dispositioned / Repairs applied / Rounds used
### Issue mapping
- Large issues / Task Packs / Dependencies
### Quality gate
- Overdesign / Underdesign / Coverage / Type consistency / Largest risk
### Git state
### Open items
### Next route
- orchestrate-execution / upstream route / user decision / blocked
```
