# 修复分流 + Targeted Re-Review + 截断

> **流程位置**：`orchestrate-execution` Steps 10-12 · 仅 needs repair 时进入

## Step 10：修复路由

所有 repair prompt 只携带 accepted findings。Repair 返回后默认只做 targeted re-review；只有 source baseline 改变时才 full phase review rerun。

- **路径 A**（≤ 2 文件、不碰合同边界、意图明确）：Coordinator 直接修 → 跑验证 → Step 11
- **路径 B**（多文件、根因已知）：SendMessage 给原 worker（或新建同类 agent） → Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
Agent({
  subagent_type: "complex-code-explorer",
  description: "Investigate unknown root cause: Pack N.M finding",
  prompt: "
    ## Scope
    只读调查。Reviewer 报告了症状但无法确定根因。找到根因，不写代码。

    ## 症状描述
    <paste accepted finding — severity / locator / evidence / impact>

    ## 已知上下文
    - Pack: <pack number + title>
    - Worker 修复尝试: <前轮修复内容及失败原因，如有>
    - 相关文件: <affected files>
    - Git diff scope: <paste>

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

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex-pack-executor）。

## Step 11：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 8（读取 `execution-review-dispatch.md`），但：
- gate 名使用 `pack-review-N.M-repair-<round>`（`<round>` = 当前修复轮次 1/2/3），不覆盖 baseline 结果
- scope 缩小到：changed files（修复涉及的文件）/ accepted findings（原 finding 是否解决）/ 受影响 angle

## Step 12：修复截断

每个 pack 最多 **2 Worker repair round + 1 root-cause-analyst round = 3 repair round**。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → 截断 Worker 循环，新建 `root-cause-analyst`（见下方模板） |

### Root-Cause-Analyst 截断 Dispatch

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Investigate repair failure: Pack N.M",
  prompt: "
    ## 调度场景
    Repair Truncation（Execution Pack Review）。Worker 修了两轮，reviewer 仍报 needs repair。

    ## 前两轮上下文
    - Round 1 accepted findings: <paste>
    - Round 1 worker 修复内容: <paste>
    - Round 2 accepted findings: <paste>
    - Round 2 worker 修复内容: <paste>
    - Git diff scope: <paste>
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
| `fixed` | Targeted Re-Review（消耗 Round 3） |
| `root cause found, not fixed` | 用 analyst findings 重新 dispatch worker（消耗 Round 3） |
| `root cause in design/plan` | 写回 design doc / plan → 回到 orchestrate-discovery 或 orchestrate-plan-writing |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

Round 3 Targeted Re-Review 仍 needs repair → BLOCKED，报告用户。

---
> **下一步**：修复通过 → 回到 Steps 4-9 per-pack 循环继续（`execution-pack-review-cycle.md`），或全部 pack 完成 → Step 13（`execution-completion.md`）。BLOCKED → 返回 verdict。
