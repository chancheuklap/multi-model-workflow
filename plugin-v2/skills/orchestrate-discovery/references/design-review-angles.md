# Design Review Angles + Dispatch Details

> **流程位置**：`orchestrate-discovery` Steps 10-11 · Design Review 派发 + 修复 · 通过后回到 SKILL.md Step 12

## Codex Dispatch 公共部分

两个 review angle 通过 `codex:codex-rescue --model gpt-5.4 --wait` 派发。每次 review 是全新 Codex task，可并行不可合并。`--wait` 强制前台执行——review 必须等 Codex 线程完成后再返回 verdict。

**Budget check**：Discovery Design Review 使用固定 per-phase allowance（2 baseline + 2 repair headroom = 4 dispatches）。此阶段 budget_total 尚未确认（pack_count 未知），不依赖 budget_total 做检查。检查 budget file 的 `discovery_used + 2 ≤ 4`。每次 dispatch 后 Coordinator 递增 `discovery_used`。

Prompt 中要求 reviewer 使用 Return Contract：

```text
### Verdict
pass / blocked / needs repair / needs context

### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots

### Result
（使用下方 Result Payload 格式）

### Verification
- 已运行的 commands 和结果

### Open Items
- parent 必须处理的问题
```

每条 finding 使用 Finding Shape：`severity / confidence / locator / evidence / impact / remediation`。

## Baseline 1: Design Content Review

审设计自身是否完整、可测试、可执行。Prompt 包含 Scope / Read first / Project baseline / Contract anchors。

检查：业务术语一致性 / 用户旅程覆盖 / 每条行为可验证 / UI 有 mockup 转化 / 合同有 Contract anchors / 失败场景覆盖 / 无未来需求混入。

Critical：核心意图不可测 / 目标行为含混导致 plan 必须猜 / UI 有 mockup 但没转成验收状态 / 合同缺 anchors / 文档内部矛盾 / 关键场景缺失 / 新对象缺 owner。

## Baseline 2: Project Alignment Review

审设计是否符合项目事实和约束。Prompt 包含 Scope / Read first / Project baseline（北极星、不变量、数据权威、contract wall）/ Contract anchors。

检查：项目术语 / 数据权威和模块边界 / 不变量 / 新端口注册 / migration tree / helper placement / 基础设施依赖 / ADR 条件。

Critical：违反北极星或不变量 / 依赖不存在的基础设施 / 跨服务合同缺 producer-consumer / 绕过 Pydantic/registry/migration / 未设计生产风险。

## Calibration

只标记会导致实际问题的 issue。核心意图不可测、内部矛盾、关键场景缺失——这些是 issue。措辞改进、风格偏好、"某些 section 不够详细"——不是。除非有严重缺口会导致有缺陷的 plan，否则 approve。

## Result Payload

```text
Review: 设计文档 - <Design Content Review / Project Alignment Review>
Phase summary: 通过 / 阻塞
Critical:
Important:
低置信度观察:
Disposition required:
```
