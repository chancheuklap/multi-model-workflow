# Phase C Business Report + Finishing

Phase B 通过后进入。

## 汇报内容

向用户汇报：

1. **新增能力**：用业务语言描述用户或系统现在能做什么。
2. **验证证据**：每项能力的测试通过、UI 验证、contract 验证证据。
3. **残余风险**：未解决的 manual gate、已知 edge case、deploy 注意事项。
4. **发布检查**：migration / rollback / deploy order / manual production gate 状态。

## 未通过时

Phase B 未通过时：只汇报当前状态和 blocker，不声称完成。

## 收尾工作

- 清理 budget file（`.claude/multi-model-workflow/budget-<run_id>.json`）。
- 清理 `active-run-id`。
- 清理 `scope-<run_id>.md`。
- design / plan repair、通过 Pack Review 的 Task Pack、accepted finding repair、runtime sync 分别提交；按可回退边界划分 commit。
- **只有用户明确要求才 merge / PR / push / 删分支或丢弃改动。**
- 收尾工作直接在 Phase C 内完成，不交给外部流程。

## 禁止

- 没有验证证据声称完成。
- 用技术术语向用户汇报（用业务语言）。
- 未经用户指令 merge / push / PR。
