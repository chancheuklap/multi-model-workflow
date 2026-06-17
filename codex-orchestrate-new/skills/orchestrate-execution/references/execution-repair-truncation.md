# 修复分流 + 自验闭合 + 截断

> **流程位置**：`orchestrate-execution` Steps 10-12 · 仅 needs repair 时进入

## Step 10：修复路由

Coordinator 收到 Plan Implementation Review findings → 逐条 disposition（与 Step 9 完全一致）。

Accepted findings 按 `Affected packs` 字段分组 → 每组复用现有三路分流：

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 默认自验收（verification commands + acceptance criteria 对照）。如果修复改变了 Plan baseline、用户明确要求独立复核，或 RCA 根因修复风险高到无法靠 Coordinator 自验闭合，则重新派发一次 baseline Codex review，走 `_shared/review-dispatch.md` 的 `spawn_agent` / `wait_agent` / durable result / `close_agent` 流程；不续用旧 reviewer session 或旧 job id 概念。

- **路径 A**（≤ 2 文件、不碰合同边界、意图明确）：Coordinator 直接修 → 跑验证 → Step 11
- **路径 B**（多文件、根因已知）：

<!-- BEGIN: send-input-resume [variant=worker] -->
**Worker send_input Resume 步骤**（pack_executor / complex_pack_executor 修复）：

修复 resume 的是 **plan-level 自治 Worker**（一个 Worker 拥有整个 Plan）。Findings 按 `[Pack N.M]` 归属分组传给同一个 Worker，由它在原 context 中逐个修复。

1. `state.sh agent-id get --run-id <run_id> --plan-id <plan_id>` 读取 execution-state 中的 plan worker_agent_id（`plans[<plan_id>].worker_agent_id`）
2. 若返回 null/empty -> 立即标记 BLOCKED 给用户 + `state.sh transition --actor Coordinator --to blocked`（不允许创建新 agent）
3. 恢复并发送：
   ```
   resume_agent({ id: "<agent_id>" })
   send_input({
     target: "<agent_id>",
     message: "<DISPATCH_ENVELOPE>\n\n修复任务：包含 accepted findings、Coordinator 亲验证据、repair scope、verification commands 和 Return Contract。"
   })
   ```
   send_input inline 发送完整修复 prompt，直接写入 `message` 字段，不先写到文件再引用。
4. `wait_agent({targets:["<agent_id>"], timeout_ms:600000})` 等待 final message；如 agent 仍需继续修，重复 resume + send_input，不新建同类 worker
5. 解析返回结果 → `state.sh transition --actor Coordinator --to returned`
5b. 修复完成后运行 verification commands + 对照 acceptance criteria + grep 确认变更
6. 写 `state.sh disposition append` 或 `state.sh update --field plans[N].packs[M].repair_round`

Compaction recovery: 从 `workflow-state.cursor` + plan/design 文档重建 repair context；dispatch prompt 不需要 durable copy。
<!-- END: send-input-resume -->

→ Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
spawn_agent({
  agent_type: "complex_code_explorer",
  message: "
    <DISPATCH_ENVELOPE>

    ## Scope
    只读调查。Reviewer 报告了症状但无法确定根因。找到根因，不写代码。

    ## 症状描述
    <paste accepted finding — severity / locator / evidence / impact>

    ## 已知上下文
    - Plan: <plan number + title>
    - Affected packs: <N.M, N.K>
    - Worker 修复尝试: <前轮修复内容及失败原因，如有>
    - 相关文件: <affected files>
    - Git diff scope: <plan-start-commit>..<plan-end-commit>

    ## 调查方向
    <Coordinator 初步判断——时序 / 隐式依赖 / 状态污染 / 配置漂移等>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 files / tests / logs / commands
    ### Result
    - Facts: confirmed facts with locators
    - Root cause assessment: <root cause + evidence, if found>
    - Recommended fix direction: <路径 A（Coordinator 直接修）/ 路径 B（Worker 修）+ 理由>
    - Excluded paths: hypotheses checked and ruled out with evidence
    - Recommended next probe: <if root cause not found>
    ### Verification
    ### Open Items
  "
})
```

Explorer 返回后路由：

| Explorer Result | 动作 |
| --- | --- |
| Root cause found + 推荐路径 A | Coordinator 直接修复 → Step 11 |
| Root cause found + 推荐路径 B | 派 Worker 修复 → Step 11 |
| Root cause not found | 报告用户，附 explorer 已排除路径 |

**涉及多个 Pack 交互的 finding**：Coordinator 判断是否合并修复（用 complex_pack_executor）或拆分到各 Pack worker。

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex_pack_executor）。

**Coordinator 写入 execution state**：`plans[N].repair_round += 1`、`plans[N].status = repairing`。

## Step 11：修复后闭合

修复完成后，默认由 Coordinator 自验闭合，不另建缩小范围审查。

只有 source baseline 改变、用户明确要求，或 RCA 根因修复风险高到必须独立复核时，重新派发 baseline Codex review：
- 按 Step 8 读取 `execution-review-dispatch.md` 和 `_shared/review-dispatch.md`
- 新 gate 使用 `plan-impl-review-N-baseline-rerun-<round>`，不覆盖原 baseline result
- scope 写明 changed files、accepted findings、受影响 angle 和重新 review 的原因

## Step 12：修复截断

Worker repair 轮次上限由 `routes-v1.json` 的 `repair_policy.max_repair_rounds`（execution phase）持有，`dispatch-review.sh validate` 和 repair flow 共同强制；超限后不再续修，进入 RCA 或 BLOCKED。当前值：`max_repair_rounds=2, escalate_to_rca=true`（等价于旧散文的"2 Worker round + 1 RCA round"）。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Coordinator 自验；必要时 baseline rerun |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Coordinator 自验；必要时 baseline rerun |
| Round 3（截断） | 仍 needs repair → 截断 Worker 循环，新建 `root_cause_analyst`（见下方模板） |

### Root-Cause-Analyst 截断 Dispatch

```
spawn_agent({
  agent_type: "root_cause_analyst",
  message: "
    <DISPATCH_ENVELOPE>

    ## 调度场景
    Repair Truncation（Plan Implementation Review）。Worker 修了两轮，reviewer 仍报 needs repair。

    ## 前两轮上下文
    - Round 1 accepted findings: <paste>
    - Round 1 worker 修复内容: <paste>
    - Round 2 accepted findings: <paste>
    - Round 2 worker 修复内容: <paste>
    - Git diff scope: <plan-start-commit>..<plan-end-commit>
    - Affected packs: <N.M, N.K>
    - 原 Pack Brief: <paste relevant subset>

    ## 你的任务
    不要重复 worker 的方法。从不同维度切入——时序、状态污染、隐式依赖、配置漂移。

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed / root cause in design/plan / unable to reproduce / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    - Regression risk: <what could break>
    ### Verification
    ### Open Items
  "
})
```

**Analyst Resolution 路由**：

| Resolution | 下一步 |
| --- | --- |
| `fixed` | Coordinator 自验闭合；必要时 baseline rerun |
| `root cause found, not fixed` | 用 analyst findings 重新 dispatch worker（消耗 Round 3） |
| `root cause in design/plan` | 写回 design doc / plan → 回到 orchestrate-discovery 或 orchestrate-plan-writing |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

Round 3 自验或 baseline rerun 仍 needs repair → BLOCKED，报告用户。

---
> **下一步**：修复通过 → SKILL.md Step 13（Release Gate，条件触发）→ Step 14（completion）。BLOCKED → 返回 verdict。
