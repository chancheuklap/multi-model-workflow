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

## 2. Executability

- 已验证 existing paths、commands、tests、fixtures、endpoints、mockup paths。
- plan 已包含 Scope Check 和 File / Responsibility Map。
- 新文件标记为 `Create`。
- 每个 Task Pack 都有 owned files / responsibilities。
- 每个 Task Pack 都有 verification commands 或 HITL / manual gate。
- 细 task 适合短反馈循环。
- 改代码或测试的 step 有足够完整的代码 / 测试 shape、命令和 expected result。
- 后续 task 使用的类型、函数、方法、字段、fixture 与前文定义或 existing code 一致。
- 没有 task 要求 worker 自行决定产品行为、领域术语、UI 目标状态、permission meaning、billing meaning、架构方向、issue hierarchy 或 schema ownership。

## 3. Pack Quality

- pack 是 vertical slice，可以 demo 或 independently verify。
- shared contract、migration、billing、permission、runtime、browser takeover、release gate 工作串行或同 pack。
- 并行 pack 不触碰同一文件或 contract surface。
- UI / UX pack 有 mockup anchors、viewport、states、interaction 和 visual verification。
- contract pack 有 owner、provider、consumer、model、schema_version 或 migration / catalog / registry，以及 verification。

## 4. Red Flags

这些内容出现时必须修正：

- 任何非 Orchestrate Workflow 的 execution owner 或额外 execution handoff；
- horizontal packs：all backend、all frontend、all tests、all schema、all templates；
- placeholder：TBD、TODO、later、appropriate、similar；
- `write tests`、`add validation`、`handle edge cases`、`implement logic` 这类没有具体内容的 step；
- 代码片段使用省略号、伪变量或未定义名称；
- 未验证路径或命令被写成现有事实；
- 用 “Task Pack Planning later” 推迟本轮已知 pack 边界。
- 在缺少小 issue 时生成正式 Task Pack。
- plan 没有经过 `to-issues` issue hierarchy，却声称 issue-backed。

无法从当前上下文修正时，返回对应 route：`NEEDS_CONTEXT`、`NEEDS_ISSUES`、`NEEDS_TRIAGE`、`NEEDS_DIAGNOSIS`、`NEEDS_DECISION` 或 `NEEDS_ARCHITECTURE`，说明缺少的 artifact、issue、decision 或 feedback loop。
