# Multi-PR 系统性冲突 — Root-Cause-Analyst 调查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 9-11 · 仅系统性冲突时进入

这是 Multi-PR Merge 独特的调查场景。与 Bug Investigation（从零查 bug）和 Repair Truncation（worker 修两轮不过）不同，PR 冲突调查的对象是"两个各自正确的 PR 合在一起为什么出问题"。

## Step 9：构造 Analyst Dispatch

```
spawn_agent({
  agent_type: "root_cause_analyst",
  description: "Multi-PR conflict investigation: <conflict cluster summary>",
  prompt: "
    ## 调度场景
    Multi-PR Merge 冲突调查。这不是 bug，不是 repair 截断——这是多个并行 PR
    合并时发现的系统性冲突。每个 PR 各自正确（已通过 Final Review），但它们的
    交互产生了冲突。

    ## 大设计文档
    <path>（整体目标 + 架构方案 + 模块划分）

    ## 参与合并的 PR
    | PR | Branch | 核心行为 | 对应 Issue |
    | --- | --- | --- | --- |
    <paste>

    ## Explorer 发现的冲突
    <paste conflict list from explorer — type / PRs / files / description / severity>

    ## Coordinator 的正确状态理解
    <paste from Step 2 — 合并后系统应该是什么样子>

    ## 合同地图
    <paste cross-PR contract surfaces>

    ## Methodology
    启动后立即 Read 以下文件，按其中 5 步方法论执行调查：
    ${MMW_PLUGIN_ROOT}/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md

    ## 你的任务

    使用 Multi-PR Conflict Investigation 方法论（模式 3）。
    从"交互"而非"错误"的视角出发——不是某段代码错了，而是两段各自正确的
    代码合在一起产生了矛盾。

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context

    ### Evidence
    - 实际检查过的 PRs / files / diffs / docs

    ### Result
    - Resolution: root_cause_identified / design_conflict / implementation_deviation / unable_to_determine
    - 冲突分析：
      | # | 冲突 | 根因类型 | 涉及 PR | 根因详述 | 修复方向 | 需改哪个 PR | 关联冲突 |
    - 设计影响：<大设计是否需要更新 / 无>
    - 建议修复顺序：<如果多个冲突有关联>
    - 排除的假设：<with evidence>
    - 回归风险：<修复后可能影响的区域>

    ### Verification

    ### Open Items
  "
})
```

## Step 10：接收 Analyst 返回

Coordinator 审阅 analyst findings，不是盲目接受——主动验证：

1. **对照设计文档**：analyst 的根因判断是否与设计意图一致
2. **对照 PR diff**：analyst 说的文件/代码/行为是否与实际代码一致
3. **评估修复方向**：analyst 建议的修复方向是否合理、是否有更简单的路径

## Step 11：Analyst Resolution 路由

| Analyst Resolution | Coordinator 动作 |
| --- | --- |
| `root_cause_identified` | 逐个冲突审阅修复方向 → 按修复顺序逐个 dispatch worker（Step 12） |
| `design_conflict` | 冲突在设计层面——两个 PR 的目标本身矛盾。两条路：(1) 回 orchestrate-discovery 让用户重新对齐设计 → 返回 `NEEDS_DISCOVERY`；(2) 当场询问用户做决策 → 拿到决策后继续 |
| `implementation_deviation` | 某个 PR 偏离了设计——定位到具体偏离，dispatch worker 修复偏离（Step 12） |
| `unable_to_determine` | 派 complex_code_explorer 补充信息后重新 dispatch analyst；或 BLOCKED 报告用户 |

**`unable_to_determine` Explorer Dispatch**：

```
spawn_agent({
  agent_type: "complex_code_explorer",
  description: "Supplement PR conflict investigation: <conflict cluster>",
  prompt: "
    ## Scope
    只读调查。Root-cause-analyst 无法确定 PR 间冲突的根因，需要更多信息。

    ## Analyst 已排除的假设
    <paste from analyst return — excluded hypotheses with evidence>

    ## 待澄清的冲突
    <paste unresolved conflicts from analyst return>

    ## PRs involved
    | PR | Branch | 核心行为 |
    <paste>

    ## 大设计文档
    <path>

    ## 调查方向
    <Coordinator 根据 analyst 排除路径判断的下一步方向——
     隐式依赖 / 运行时行为耦合 / 配置传播 / 时序依赖等>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 PRs / files / diffs / docs
    ### Result
    - Facts: confirmed facts with locators
    - Inferences: hypotheses, clearly marked
    - Excluded paths: hypotheses checked and ruled out with evidence
    - Recommended next probe: <for analyst re-dispatch>
    ### Verification
    ### Open Items
  "
})
```

Explorer 返回后：用 explorer findings 补充 analyst prompt，重新 dispatch `root_cause_analyst`（Step 9）。**Analyst ↔ Explorer 循环最多 1 次**（analyst → explorer → analyst）。第 2 轮 analyst 仍返回 `unable_to_determine` → BLOCKED，报告用户。

---
> **下一步**：root_cause_identified / implementation_deviation → Step 12（`merge-conflict-repair.md`）。design_conflict → 返回 verdict。unable_to_determine → 派 explorer 补信息或 BLOCKED。
