# Execution Dispatch Templates

## Pack Brief Template

Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。Coordinator 从 plan 中提取并在 prompt 中写全以下所有字段：

```text
Pack: <pack number + title>
Issue: <issue reference>
Scope: <editable artifacts for this pack>
Goal behavior: <end-to-end behavior description>
Implementation tasks:
  <paste ALL tasks with full text — don't让 worker 读 plan 文件>
Owned files:
  - Create: <path — responsibility>
  - Modify: <path — responsibility>
  - Test: <path — behavior covered>
Read first:
  - <source docs, ADRs, project rules, mockups>
Contract anchors:
  - boundary type / owner / provider / consumer / verifier
  - Pydantic model / schema_version / compatibility
  - registry / migration / catalog
  - repository / read model
  - tests / release gate
  - forbidden shortcuts
Mockup anchors:
  - path / viewport / states / interaction / visual verification
Acceptance criteria:
  - [ ] <each criterion>
Verification commands:
  - <command> → Expected: <result>
Commit boundary: <one atomic commit scope>
Risk flags: <normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL>
发布风险: <risk surface / N/A>
AFK / HITL: <manual gate requirements>
Dependencies: <pack dependencies>
Parallel safety: <can parallel with which packs / why>
Out of scope: <what NOT to touch>
Return contract:
  ### Verdict
  pass / blocked / needs repair / needs context
  ### Evidence
  ### Result
  - Changed files
  - Completed behavior (each with verification evidence)
  - Known gaps
  - Needs review
  ### Verification
  ### Open Items
```

**关键规则**：
- Pack Brief 必须来自已通过 Plan Review 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。
- 所有 task 完整文本直接贴在 prompt 中——不让 worker 读 plan 文件（节省 worker 上下文，确保 worker 拿到的是完整信息）。
- Coordinator 提供场景上下文（where this fits, dependencies, architectural context），让 worker 理解这个 pack 在整体中的位置。

---

## Pack Review Codex Dispatch Template

Worker 返回 `pass` 或处理完 `needs repair` concerns 后，派发 **1 个** baseline Codex reviewer：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Pack Review: Task Pack N.M",
  prompt: "
    --model gpt-5.4

    ## Scope
    Review the implementation of Task Pack N.M: <title>

    ## Source artifacts
    - Plan: <path>
    - Source design: <path>
    - Pack acceptance criteria: <paste>
    - Verification commands: <paste>

    ## Changed files
    <list from worker return>

    ## Contract anchors
    <paste if this pack touches contract boundaries>

    ## Mockup anchors
    <paste if this pack has UI work>

    ## Review angles (single integrated review)

    ### Spec Compliance
    验 worker 是否实现了 pack 要求的一切（不多不少）：
    - 每条 acceptance criteria 是否满足
    - 是否有 missing requirements
    - 是否有 extra/unneeded work（YAGNI）
    - goal behavior 是否可从代码中确认

    ### Code Quality
    验实现是否正确、可维护：
    - TDD 纪律：测试测的是 public behavior，不是 mock behavior
    - 合同纪律：跨边界数据用正式 Pydantic contract，不是 bare dict
    - 不 mock 仓库内部业务模块
    - 文件职责清晰、接口定义好
    - 遵循项目既有模式

    ### Contract & Risk
    验高风险面是否正确处理：
    - Contract anchors 闭合（owner / provider / consumer / verification）
    - Migration / registry / catalog 完整
    - 发布风险标注准确
    - rollback / compatibility 考虑

    ## Calibration
    只标记会导致实际问题的 issue。实现者做出错误的东西或卡住——这是 issue。
    措辞、风格偏好、nice-to-have 建议——不是。
    除非有严重缺口（spec 不符、合同破损、测试不覆盖核心行为、引入安全风险），否则 approve。

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    Pack Review 结果：
    Spec compliance:
    Code quality:
    Contract & risk:
    Critical:
    Important:
    低置信度观察:
    Disposition required:
    ### Verification
    ### Open Items
  "
})
```

---

## Root-Cause-Analyst 截断 Dispatch Template

Worker 修了两轮，reviewer 仍报 needs repair 时使用：

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
