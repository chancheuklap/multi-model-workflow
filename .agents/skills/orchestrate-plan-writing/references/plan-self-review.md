# Plan Self Review

生成或保存 issue-backed plan 前必须自检。

## 1. Coverage

- 每条 source design intent 都映射到大 issue section 或 Task Pack。
- 每个大 issue 都出现在 plan 一级章节。
- 每个大 issue 都已经通过 `to-issues` 拆出小 issue。缺少小 issue 时不能生成正式 plan，必须返回 `NEEDS_ISSUES`。
- 每个小 issue 都映射到一个 Task Pack。
- 每条 issue acceptance criterion 都进入 Task Pack acceptance criteria，或有 source evidence 支持 out of scope。
- 每个 blocked-by 都进入 Task Pack dependencies。
- plan 包含 Source Coverage Map，并且 coverage evidence 不是空泛描述。
- 如果 Scope Check 判断应拆成多份 plan，当前文件没有继续把多个 subsystem 硬塞在一起。

## 2. Executability

- 已验证 existing paths、commands、tests、fixtures、endpoints、mockup paths。
- plan 已包含 Scope Check 和 File / Responsibility Map。
- plan 已包含 quality gate 结论，说明 overdesign / underdesign 是否已检查。
- 新文件标记为 `Create`。
- 每个 Task Pack 都有 owned files / responsibilities。
- 每个 Task Pack 都有 verification commands 或 HITL / manual gate。
- production-risk / billing / permission / migration / runtime / manual gate pack 都引用对应发布风险面。
- 细 task 适合短反馈循环。
- 改代码或测试的 step 有足够完整的 behavior、关键断言、合同面、命令和 expected result。
- 后续 task 使用的类型、函数、方法、字段、fixture 与前文定义或 existing code 一致。
- File / Responsibility Map 中的路径都被 Task Pack 消费；Task Pack 中的路径都能回到 map。
- RED / GREEN 命令有明确 expected result，且不是只依赖最终大套测试。
- 没有 task 要求 worker 自行决定产品行为、领域术语、UI 目标状态、permission meaning、billing meaning、架构方向、issue hierarchy 或 schema ownership。

## 3. Pack Quality

- pack 是 vertical slice，可以 demo 或 independently verify。
- shared contract、migration、billing、permission、runtime、browser takeover、release gate 工作串行或同 pack。
- 并行 pack 不触碰同一文件或 contract surface。
- UI / UX pack 有 mockup anchors、viewport、states、interaction 和 visual verification。
- contract pack 有 owner、provider、consumer、model、schema_version 或 migration / catalog / registry，以及 verification。
- “发布风险和人工门禁”覆盖所有 production-risk / billing / permission / runtime / migration / manual gate pack，且能被 Phase B final release gate 消费。

## 4. Red Flags

这些内容出现时必须修正：

- 任何非 Orchestrate Workflow 的 execution owner 或额外 execution handoff；
- horizontal packs：all backend、all frontend、all tests、all schema、all templates；
- placeholder：TBD、TODO、later、appropriate、similar；
- `write tests`、`add validation`、`handle edge cases`、`implement logic` 这类没有具体内容的 step；
- `similar to previous`、`defer`、`later` 或把关键行为留给后续补齐；
- 代码片段使用省略号、伪变量或未定义名称；
- 大段生产代码出现在 plan 中，且不是 source design、prototype、ADR 或 existing contract 固定的精确 shape；
- 未验证路径或命令被写成现有事实；
- 用 “之后再切 Task Pack” 推迟本轮已知 pack 边界。
- 在缺少小 issue 时生成正式 Task Pack。
- plan 没有经过 `to-issues` issue hierarchy，却声称 issue-backed。
- 为当前 issue 没要求的未来能力预建 registry、migration、消息中心、历史页、全局 dashboard 或复杂抽象。
- Task Pack 缺少 failure state、contract anchors、mockup states、pack-local verification 或 dependency truth。
- production-risk 只写在 risk flags 里，没有进入“发布风险和人工门禁”。

无法从当前上下文修正时，返回对应 route：`NEEDS_DISCOVERY`、`NEEDS_CONTEXT`、`NEEDS_ISSUES`、`NEEDS_TRIAGE`、`NEEDS_DIAGNOSIS`、`NEEDS_DECISION` 或 `NEEDS_ARCHITECTURE`，说明缺少的 design、artifact、issue、decision 或 feedback loop。
