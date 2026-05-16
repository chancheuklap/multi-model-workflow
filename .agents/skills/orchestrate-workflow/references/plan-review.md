# Plan Review Contract

Phase 0b 审 issue-backed implementation plan。目标是确认计划覆盖 source design / requirements 和 `to-issues` 产出的 source issues，且 plan 中的 Task Pack inventory 可以直接进入 Orchestrate dispatch。Plan Review 必须同时读取 source design / requirements、source issues 和 plan；如果只有 plan，没有 source intent 或 issue source，返回 `NEEDS_CONTEXT`，或由主线程补齐 source intent 后再审。

## Plan Intake Requirements

进入 review 前，主线程必须确认 plan 包含：

- `Source design`；
- `Source issues`；
- `Execution owner: Orchestrate Workflow`；
- `Plan unit`；
- `Completion gate`；
- large issue -> Task Pack mapping；
- source issues 来自 `to-issues` 或等价垂直 issue workflow；
- 每个 Task Pack 的 issue source、goal behavior、owned files / responsibilities、read first、Contract anchors、Mockup anchors、acceptance criteria、verification commands、risk flags、AFK / HITL、dependencies、parallel safety、out of scope。

如果 plan 声明非 Orchestrate Workflow 的 execution owner，或添加额外 execution handoff，返回 `needs repair`，由主线程修 plan，不进入 Phase A。

如果 plan 声称 issue-backed，但缺少 vertical large issues 或 vertical small issues，返回 `needs context`，routing 指向 upstream `to-issues`。

## Dispatch 1: Coverage And Task Quality

派 `code_reviewer`。

Prompt 必须包含：

- Read first：source design / requirements、source issues、plan、相关 UI / UX mockup、根 `AGENTS.md`、相关 `PROJECT.md` / `ENGINEERING-RULES.md` / SPEC / ADR / GUIDE。
- Project baseline：本计划必须承接的 design intent、issue acceptance、项目不变量、模块边界和验收门槛。
- Contract anchors：如果计划触碰 API / Pydantic / DB / JSON / sync / task payload / UI action / helper 边界，列出 owner、provider、consumer、model、schema_version、registry / migration / catalog、repository / read model 和验证方式。

检查：

- 逐条提取 source design / requirements 的 intent，确认每条 intent 至少有一个 large issue section 或 Task Pack 覆盖。
- 逐条提取 source issue acceptance criteria，确认每条 criteria 进入 Task Pack acceptance criteria，或有明确 out of scope 依据。
- large issue section 是否对应 vertical large issue；Task Pack 是否对应 vertical small issue。候选 small issue 不能进入 Phase A。
- 如果有 UI / UX mockup，逐条提取可见页面状态、关键交互、viewport 和组件状态，确认每项至少有 Task Pack 和验收证据覆盖。
- 如果 source design / requirements 对 desired behavior、业务术语、UI target state、role、视觉层级、交互意图或验收口径含混，route 给 upstream `grill-with-docs`；不要把含混点包装成 worker task。
- 找出计划做了但 design 或 issue 没要求的 scope creep。
- 每个 Task Pack 是否足够具体：改什么、在哪改、测试什么、预期什么结果。
- pack 内细 task 是否能在短反馈循环内完成；过大的 task 要拆。
- 依赖关系是否真实、是否有循环依赖。
- large issue / Task Pack 分组是否符合 source issue 边界、shared files、shared contracts、dependency order。
- API / Pydantic / DB / JSON / helper 任务是否按正式合同边界切分，而不是把 schema、tests、implementation 横切。
- 是否为每个高风险区域标出验证方式和人工 gate。

Critical：

- design intent 或 issue acceptance 无 Task Pack 覆盖。
- source intent / UI target state / business context 不清，却计划直接进入实现。
- Task Pack 描述无法执行，worker 必须自行决定目标行为。
- 依赖顺序错误会导致实现失败。
- plan 缺少 Task Pack inventory 或核心验证方式。
- plan 缺少 `to-issues` 产出的 small issue，却生成正式 Task Pack。
- UI / UX mockup 没有被转成 Task Pack、viewport 检查或 visual / DOM 验收。
- 合同边界任务没有 Contract anchors，worker 必须自创 dict / helper 才能执行。

## Dispatch 2: Compliance And Verification

派 `code_reviewer`；涉及 production-risk 时追加 `release_reviewer`。

`release_reviewer` 只补充审 migration order、deploy order、compatibility、rollback、manual production gate 和跨服务生产风险；不能替代 Coverage、Task Quality、Compliance 或 Reference Verification。

Prompt 必须包含：

- Read first：source design / requirements、source issues、plan、相关 UI / UX mockup、根 `AGENTS.md`、相关 `PROJECT.md` / `ENGINEERING-RULES.md` / SPEC / ADR / GUIDE、计划涉及目录的 `AGENTS.override.md` / `agents.overrides.md`。
- Project baseline：本计划涉及的项目规则、数据权威、contract wall、测试路由、迁移 / 发布 / 回滚约束。
- Contract anchors：本计划涉及的 API、Pydantic、DB、JSON、task、sync、catalog、capability、helper 边界。

逐条验真：

- 已有文件路径是否存在。
- mockup / screenshot / HTML prototype 路径是否存在，且计划引用的是当前版本。
- 已有函数、类、fixture、配置项、环境变量是否存在。
- 命令和脚本入口是否存在。
- 新建文件是否被明确标注为新建，不要误报不存在。
- 涉及目录如有 `AGENTS.override.md` / `agents.overrides.md`，是否安排同步更新。
- 数据库变更是否说明 migration tree。
- 新端口 / 命令 / 收费动作 / 合同字段 / capability 是否安排注册位置。
- Pydantic contract 是否安排 `schema_version`、`extra=forbid`、兼容策略和 consumer 同步。
- JSONB / SQLite JSON 是否安排 registry、validator 和 unknown-field 测试。
- 数据库字段是否安排 migration、repository 写入、read model、API / contract 同步和回归测试。
- public API / client / service 是否计划返回 typed contract，而不是把 `dict[str, Any]` 传给上游。
- helper 是否落到 domain service、repository、adapter 或 shared contract，而不是 route / host / page 临时层。

Critical：

- 引用不存在的路径、函数、类、fixture 或命令。
- 引用不存在或版本不明的 UI / UX mockup，却把它当作实现标准。
- 违反项目规则、不变量、权威源、模块边界。
- 计划允许 bare dict、route-local schema、临时 helper、silent unknown-field drop 或错误 migration tree 进入实现。
- 高风险变更没有迁移、兼容、回滚或人工验证任务。

## Dispatch 3: Independent Second Opinion

派独立 `code_reviewer`，不要给它前两份 review 的结论。目的不是重复检查，而是用新 framing 找遗漏。

Prompt 必须包含同一组 Read first 和 Project baseline，也就是 source design / requirements、source issues 与 plan，但不要包含前两份 review 的 finding。

检查：

- 是否有任务互相矛盾。
- 是否有隐含依赖没有标出。
- 是否有两个 Task Pack 会改同一文件或同一 contract surface，却被计划并行。
- 是否有 risky assumption，例如假设 API / data shape / fixture 存在。
- 是否有 risky assumption，例如假设 Pydantic contract、DB 字段、JSON registry、catalog、capability 或 helper 已存在。
- 是否有 “Task Pack Planning later 再决定边界” 或 “最后统一验证” 的水平切片风险。
- 是否有把 UI / UX 主观反馈、业务含混点或 architecture seam 问题伪装成普通实现 task 的风险；前者 route 给 `grill-with-docs`，后者 route 给 `improve-codebase-architecture`。

## Result Payload

```text
Review: 计划文档审查
Phase summary: 可执行 / 需修正
设计与 issue 覆盖:
Grep / rg 验真:
Task Pack inventory:
Critical:
Important:
低置信度观察:
```

Coordinator dispatch must include the standard top-level return headings. This payload belongs under `### Result`。顶层 `### Verdict` 只使用 `pass / blocked / needs repair / needs context`；“可执行 / 需修正”只作为 phase summary。每条 finding 必须使用统一 shape：severity、confidence、locator、evidence、impact、remediation、routing。Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction；context ambiguity route 给 upstream `grill-with-docs`，architecture friction route 给 upstream `improve-codebase-architecture`。

Phase 0 plan findings 返回 coordinator。主线程修 plan，不派 worker 写代码。
