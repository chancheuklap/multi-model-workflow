# Pack Dispatch

## Worker 选择

| 条件 | Agent | Model |
| --- | --- | --- |
| 普通 pack（无 risk flags） | pack-executor | sonnet |
| 高风险 pack（migration / billing / auth / permission / runtime / shared contract） | complex-pack-executor | opus |

## Prompt 构成

Pack Brief 完整字段：

```text
Pack / Issue / Scope / Goal behavior / Implementation tasks（所有 task 完整文本）/
Owned files / Read first / Contract anchors / Mockup anchors /
Acceptance criteria / Verification commands / Risk flags /
发布风险 / Commit boundary / AFK-HITL / Dependencies /
Parallel safety / Out of scope / Return contract
```

Pack Brief 必须来自已通过 Phase 0b 的 plan。不在 dispatch prompt 里临场重切。

## Contract Boundary

触碰合同边界时，dispatch prompt 额外包含 `${CLAUDE_PLUGIN_ROOT}/references/contract-boundary.md` 中的 Contract Anchors 模板，由 coordinator 填写当前 pack 的具体 anchors。

## Worker 返回处理

| Worker Verdict | Coordinator 动作 |
| --- | --- |
| pass | 进入 Pack Review |
| needs repair | 检查正确性问题 → 先处理；观察性意见 → 记下继续 |
| needs context | SendMessage 补上下文（fallback: 新建同类 worker） |
| blocked | 技术阻塞：拆 pack / 进入 repair 循环。业务阻塞：问用户 |
