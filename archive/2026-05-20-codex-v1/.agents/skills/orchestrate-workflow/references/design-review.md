# Design Review (Phase 0a)

审 design document，确认能被 issue 拆分、plan、Task Pack 和实现承接。不做文字润色、不派 worker、不写 plan。

## 输入

- Scope + design document + 相关 mockup + project docs + Contract anchors（触碰合同边界时）。

## Pass 条件

两个 baseline review 通过 + 无 Critical finding。最多 2 个 repair rounds。

## Dispatch：2 个 baseline `code_reviewer`（可并行，不合并）

### Baseline 1: Design Content Review

审设计自身是否完整、可测试、可执行。Prompt 包含 Scope / Read first / Project baseline / Contract anchors。

检查：业务术语一致性 / 用户旅程覆盖 / 每条行为可验证 / UI 有 mockup 转化 / 合同有 Contract anchors / 失败场景覆盖 / 无未来需求混入。

Critical：核心意图不可测 / 目标行为含混导致 plan 必须猜 / UI 有 mockup 但没转成验收状态 / 合同缺 anchors / 文档内部矛盾 / 关键场景缺失 / 新对象缺 owner。

### Baseline 2: Project Alignment Review

审设计是否符合项目事实和约束。Prompt 包含 Scope / Read first / Project baseline（北极星、不变量、数据权威、contract wall）/ Contract anchors。

检查：项目术语 / 数据权威和模块边界 / 不变量 / 新端口注册 / migration tree / helper placement / 基础设施依赖 / ADR 条件。

Critical：违反北极星或不变量 / 依赖不存在的基础设施 / 跨服务合同缺 producer-consumer / 绕过 Pydantic/registry/migration / 未设计生产风险。

## Release Gate

只在 release strategy / migration-deploy order / rollback / manual gate 必须提前判定时追加 `release_reviewer`。普通 production-risk 由 baseline 转成 risk flags。

## Result Payload

`### Result` 下使用：

```text
Review: 设计文档 - <Design Content Review / Project Alignment Review>
Phase summary: 通过 / 阻塞
Critical:
Important:
低置信度观察:
Disposition required:
```

Design finding 默认 route 给 `parent` 或 `docs_worker` 做 document repair；domain / UX / ownership / target-state ambiguity route 给 `orchestrate-discovery`；产品承诺、业务规则、UX、发布策略、架构 trade-off 无法从 source artifacts 判定时 route 给 `user decision` 或 `orchestrate-discovery`。

## Reception

- accepted document repair → coordinator / docs_worker 修 design。
- accepted domain / UX / ownership ambiguity → orchestrate-discovery。
- accepted issue gap → Phase 0a 通过后 route to-issues。
- rejected / out of scope / duplicate → 记录，不 repair。

修复后 targeted re-review changed sections + 受影响 angle。
