# Final Review 修复分流 + 截断

> **流程位置**：`orchestrate-final-review` Steps 9-12 · 仅 needs repair 时进入

## Step 9：修复路由

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 自验收（verification commands + acceptance criteria 对照）即闭合，不再派发 targeted Codex re-review；自验仍有疑虑 → 升级 RCA 或 BLOCKED 报告用户。

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

Worker 修复后返回 → 进入 Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
spawn_agent({
  agent_type: "complex_code_explorer",
  message: "
    <DISPATCH_ENVELOPE>

    ## Scope
    只读调查。Final Review 报告了症状但无法确定根因。找到根因，不写代码。

    ## 症状描述
    <paste accepted finding — severity / locator / evidence / impact>

    ## 已知上下文
    - Source design: <path>
    - Plan: <path>
    - Affected packs: <list>
    - 相关文件: <affected files>
    - Git diff scope: git diff <implementation_base_commit>..HEAD（base 从 execution-state 最早 start_commit 取得）

    ## 调查方向
    <Coordinator 初步判断——跨 pack 交互 / 时序 / 隐式依赖 / 合同闭合 / 状态污染等>

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

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex_pack_executor）；涉及多个 pack 的系统性问题 → Step 10（判定 Plan 维度）。

---

## Step 10：Implementation Gap 回 Execution 的判定

如果 accepted findings 涉及多个 pack 的系统性问题（不是单点修复），Coordinator 先判断 **Plan 维度**，再决定路由：

### Step 10a：Plan 维度判定

| 情况 | 路由 |
| --- | --- |
| 所有 affected packs 属于**同一 Plan** | **留在 Final Review**——按 Path B 修复 + Step 11 Coordinator 自验闭合。不回 Execution |
| Affected packs **跨越多个 Plan** 且系统性（shared contract / migration 顺序 / cross-plan state） | → Step 10b（回 Execution 判定） |

### Step 10b：回 Execution 的条件（任一成立）

- 跨 Plan 的系统性问题（shared contract 不一致、migration 顺序错误、cross-plan state 竞争）
- 需要重新执行某个完整 pack
- plan 的 Source Coverage Map 有未覆盖的 intent 需要新 pack 实现
- 修复影响其它 Plan 的 dependencies 或 contract surface

**留在 Final Review 修复的条件**（即使跨 Plan）：
- 涉及 1-2 个 pack 的少量文件
- 修复范围明确、不影响其它 pack
- 不需要新 pack

回 Execution → 读 budget file `execution_reflux_count`：0 → 可回流，返回 `NEEDS_EXECUTION` verdict，附 accepted findings 和 affected packs 及所属 Plan；≥1 → BLOCKED 报告用户。

---

## Step 11：Coordinator 自验闭合

修复返回后，Coordinator 必须直接对 accepted findings 做闭合验证：

1. 对照每条 finding 的 evidence、affected packs 和 acceptance criteria 检查修复 diff。
2. 运行相关 verification commands；涉及全局行为时运行 Final Review 前置检查中的 diff / grep / test 命令。
3. 用 `state.sh disposition append` 记录 resolved evidence。自验仍有疑虑时进入 Step 12 RCA escalation 或 BLOCKED，不派发 targeted re-review。

---

## Step 12：修复截断（repair-once + RCA escalation）

Worker repair 轮次上限由 `routes-v1.json` 的 `repair_policy.max_repair_rounds`（final-review phase）持有，`enforce-repair-round-cap.sh` hook 机器强制。当前值：`max_repair_rounds=1, escalate_to_rca=true`（等价于旧散文的"每个 gap 最多 1 个 repair round + 1 个 RCA escalation"）。

| 阶段 | 动作 |
| --- | --- |
| Round 1 | 路径 B（send_input Worker）修复 → Coordinator 自验（grep / Read + verification commands 对照 acceptance criteria） |
| RCA escalation | Coordinator 自验仍 needs repair → 新建 `root_cause_analyst` 调度（见下方 dispatch 模板） |
| BLOCKED | Analyst Resolution 仍 `unable to determine` / `root cause in design/plan` 已写回上游 → 报告用户 |

**Root-Cause-Analyst 截断调度**：

```
spawn_agent({
  agent_type: "root_cause_analyst",
  message: "
    <DISPATCH_ENVELOPE>

    ## 调度场景
    Repair Truncation（Final Review）。Final Review 修复一轮后，Coordinator 自验仍无法闭合。

    ## Round 1 上下文
    - Round 1 accepted findings: <paste>
    - Round 1 修复内容: <paste>
    - Git diff scope: <paste>

    ## Source context
    - Source design: <path>
    - Plan: <path>
    - Affected packs: <list>

    ## 你的任务
    不要重复 Round 1 的修复方法。从不同维度切入——时序、状态污染、隐式依赖、配置漂移、跨 pack 交互。

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
| `fixed` | Coordinator 自验闭合（不再派 Targeted Re-Review）|
| `root cause found, not fixed` | 用 analyst findings dispatch worker → Coordinator 自验 |
| `root cause in design/plan` | 写回 design doc / plan → 返回对应 upstream verdict |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

RCA escalation 产出的不是 Codex review 派发，不消耗 review budget。Analyst 路径仍失败 → BLOCKED，报告用户附完整排查记录。

**Phase 内部 review dispatch 软上限**：3（2 baseline + 0 targeted + 最多 1 release gate）。

---
> **下一步**：修复通过 → Step 13（`final-review-completion.md`）。BLOCKED → 返回 verdict。
