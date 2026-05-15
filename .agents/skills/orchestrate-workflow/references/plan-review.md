# Plan Review Contract

Phase 0b 审 plan。目标是确认计划可以真实执行，不会把虚构路径、横切任务或缺失验收传给 worker。

## Dispatch 1: Coverage And Task Quality

派 `code_reviewer`。

Prompt 必须包含：

- Read first：plan、design doc、相关 UI / UX mockup、根 `AGENTS.md`、相关 `PROJECT.md` / `ENGINEERING-RULES.md` / SPEC / ADR / GUIDE。
- Project baseline：本计划必须承接的 design intent、项目不变量、模块边界和验收门槛。
- Contract anchors：如果计划触碰 API / Pydantic / DB / JSON / sync / task payload / UI action / helper 边界，列出 owner、provider、consumer、model、schema_version、registry / migration / catalog、repository / read model 和验证方式。

检查：

- 如果有 design doc，逐条提取 design intent，确认每条 intent 至少有一个 task 覆盖。
- 如果有 UI / UX mockup，逐条提取可见页面状态、关键交互、viewport 和组件状态，确认每项至少有 task 和验收证据覆盖。
- 找出计划做了但 design 没要求的 scope creep。
- 每个 task 是否足够具体：改什么、在哪改、测试什么、预期什么结果。
- task 是否能在一个短反馈循环内完成；过大的 task 要拆。
- 依赖关系是否真实、是否有循环依赖。
- section / pack 分组是否符合 shared files、shared contracts、dependency order。
- API / Pydantic / DB / JSON / helper 任务是否按正式合同边界切分，而不是把 schema、tests、implementation 横切。
- 是否为每个高风险区域标出验证方式和人工 gate。

Critical：

- design intent 无 task 覆盖。
- task 描述无法执行，worker 必须猜。
- 依赖顺序错误会导致实现失败。
- plan 缺少核心验证方式。
- UI / UX mockup 没有被转成 implementation task、viewport 检查或 visual / DOM 验收。
- 合同边界任务没有 Contract anchors，worker 必须自创 dict / helper 才能执行。

## Dispatch 2: Compliance And Verification

派 `code_reviewer`；涉及 production-risk 时追加 `release_reviewer`。

`release_reviewer` 只补充审 migration order、deploy order、compatibility、rollback、manual production gate 和跨服务生产风险；不能替代 Coverage、Task Quality、Compliance 或 Reference Verification。

Prompt 必须包含：

- Read first：plan、design doc、相关 UI / UX mockup、根 `AGENTS.md`、相关 `PROJECT.md` / `ENGINEERING-RULES.md` / SPEC / ADR / GUIDE、计划涉及目录的 `AGENTS.override.md` / `agents.overrides.md`。
- Project baseline：本计划涉及的项目规则、数据权威、contract wall、测试路由、迁移 / 发布 / 回滚约束。
- Contract anchors：本计划涉及的 API、Pydantic、DB、JSON、task、sync、catalog、capability、helper 边界。

逐条验真：

- 已有文件路径是否存在。
- mockup / screenshot / HTML prototype 路径是否存在，且计划引用的是当前版本。
- 已有函数、类、fixture、配置项、环境变量是否存在。
- 命令和脚本入口是否存在。
- 新建文件是否被明确标注为新建，不要误报不存在。
- 涉及目录如有 `AGENTS.override.md`，是否安排同步更新。
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

Prompt 必须包含同一组 Read first 和 Project baseline，但不要包含前两份 review 的 finding。

检查：

- 是否有任务互相矛盾。
- 是否有隐含依赖没有标出。
- 是否有两个 pack 会改同一文件却被计划并行。
- 是否有 risky assumption，例如假设 API / data shape / fixture 存在。
- 是否有 risky assumption，例如假设 Pydantic contract、DB 字段、JSON registry、catalog、capability 或 helper 已存在。
- 是否有“最后统一验证”的水平切片风险。

## 输出格式

```text
### 计划文档审查
结论: 可执行 / 需修正
设计覆盖:
Grep / rg 验真:
Critical:
Important:
低置信度观察:
```

每条 finding 必须有 plan section / task、证据、为什么会导致执行出错、具体修正建议、confidence。

Phase 0 plan findings 返回 coordinator。主线程修 plan，不派 worker 写代码。
