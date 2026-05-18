# Coordinator Dispatch

## 前置条件

派发前验证：

- source design / SPEC / PRD / bug brief 存在且已通过 Phase 0a 或等价 review
- `to-issues` 产出的 vertical large issues 和 vertical small issues 已就绪

缺件时按 `${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md` Handoff Status 中 plan-writing 行对应的 verdict 路由。

## 派发 plan-writer

按 `${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md` Dispatch Checklist 执行。plan-writer 特有的 dispatch prompt 输入：

```
Agent({
  subagent_type: "plan-writer",
  description: "Write implementation plan: <feature>",
  prompt: "
    ## Goal
    从 source design + issue hierarchy 写出 implementation plan。

    ## 输入
    - Source design: <path>（已通过 Phase 0a review）
    - Issue hierarchy:
      - Large issues: <path(s)>
      - Small issues: <listed in large issue docs, or separate paths>
    - Plan 保存路径: docs/orchestrate/plans/YYYY-MM-DD-<feature>.md

    ## 补充上下文（如有）
    <coordinator 在 Phase 0a 中积累的重要决策、reviewer 的重点建议、用户偏好>

    ## Return contract
    pass / blocked / needs context
  "
})
```

## 处理返回

plan-writer verdict → skill verdict 映射和下一步路由见 `${CLAUDE_PLUGIN_ROOT}/references/coordinator-tools.md` Handoff Status（plan-writing 行）。

## Plan review 后修订

Phase 0b 返回 accepted findings 时，按 `${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md` SendMessage vs 新建 agent 规则，优先 SendMessage 复用同一 plan-writer agent。Dispatch prompt 附加 accepted findings + 修订要求。
