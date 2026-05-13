# Final Intent Review — 调度 prompt template

Phase B：仅当 design doc 存在时。调度 workflow-auditor 端到端验证功能是否符合设计意图。

## 发送给 workflow-auditor 的 prompt

所有 pack 的 spec + quality review 已通过。你的任务：实际运行功能，验证它做到了 design doc 承诺的用户体验。

**Design doc**: [DESIGN_FILE_PATH]
**Plan**: [PLAN_FILE_PATH]
**起始 commit**: [STARTING_COMMIT_SHA]

---

### 步骤

1. 从 design 提取每条意图。模糊意图标 Suggestion。
2. 用 Bash 端到端运行功能。
3. 逐条比对：通过 / GAP。
4. 每个 GAP 判断类型：
   - **Implementation gap**：代码没做到但设计合理。描述 acceptance test 应做什么（你不写测试，只描述）。
   - **Design gap**：设计文档本身有缺陷——承诺了不可实现的东西、遗漏了关键约束、与项目工程规则冲突。标注 `needs user decision` 并说明"设计需修正"。
5. 代码级全量 review：`git diff [STARTING_COMMIT_SHA]..HEAD` 的交叉问题。

### 报告

意图验证：通过数/总数 + Gap 列表（区分 implementation gap 和 design gap）。代码级 findings（confidence ≥ 80）+ routing。

结论："功能符合设计意图" 或 "阻塞：N gaps（其中 M 个需要设计修正）+ K Critical"。低于 80 置信度的观察列在"低置信度观察"段落供参考。
