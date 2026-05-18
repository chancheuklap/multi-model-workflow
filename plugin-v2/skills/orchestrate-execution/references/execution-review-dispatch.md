# Pack Review Codex Dispatch Template

> **流程位置**：`orchestrate-execution` Step 8 · Worker 返回后派发 Reviewer 时读取

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
