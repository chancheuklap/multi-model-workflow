# Contract Boundary Contract

用于 API、Pydantic、数据库字段、JSONB / SQLite JSON、sync outbox、local task payload、billing、permission、runtime、capability、UI form action、external adapter 和跨模块 helper。

目标是防止 subagent 用 bare dict、临时 helper、route-local schema 或 mock 内部业务规则绕过系统合同。

## Boundary Classification

设计、计划、pack 和 review 先判断触碰哪种边界：

- API request / response：HTTP、FastAPI route、local agent API、browser / UI action endpoint。
- Pydantic protocol：`src/shared/contracts/*.py` 或模块内正式 contract。
- DB entity / read model：表、列、repository、projection、read model。
- JSON payload：Gateway / Collection JSONB，Local SQLite JSON，runtime state JSON。
- Task / sync payload：durable task、sync outbox、scheduler event、worker handoff。
- Business catalog：port、command、chargeable action、capability、permission。
- External adapter：第三方 API、浏览器、支付、文件系统、CLI、网络。
- UI form action：表单输入、页面 action、状态更新、错误返回。

## AgentFlow Anchors

AgentFlow 任务优先核这些权威位置：

- Cross-boundary protocol：`src/shared/contracts/*.py`，默认 `extra=forbid`，有版本演进时写 `schema_version`。
- JSONB / SQLite JSON：`JSONB_COLUMN_REGISTRY` / `LOCAL_JSON_COLUMN_REGISTRY`，写入走 `validate_*_payload()`。
- Database authority：Gateway 数据走 `migrations/gateway/versions`；Collection 数据走 `migrations/collection/versions`；`runtime.*` schema 只属于 Collection。
- Migration rule：两棵 Alembic tree 都是手写迁移，`target_metadata=None`，禁止 autogenerate 依赖。
- Ports / commands：新 port 写 `src/shared/ports.py`；新命令写 `scripts/dev/common/command_contract.py`。
- Billing catalog：chargeable action / settlement / wallet 走正式 shared contract 和 catalog。
- Capability / permission：新增页面、API 或 action 必须接入 capability catalog 和 capability decision。
- Local Agent public client / service boundary：public method 返回 Pydantic response contract；私有 transport `_request()` 才能保留原始 dict，并且必须在边界立刻 `model_validate`。
- Compass / Console 类边界：业务能力放 service / domain facade，不塞进 `console_host.py` 这类 host helper。
- 目录规则：变更目录存在 `AGENTS.override.md` 或 `agents.overrides.md` 时同步核对。

## Contract Anchors

dispatch prompt 和 review finding 使用这组字段：

```text
Contract anchors:
- boundary type:
- owner:
- provider:
- consumer:
- verifier:
- Pydantic model:
- schema_version / compatibility:
- registry / migration / catalog:
- repository / read model:
- tests / release gate:
- forbidden shortcuts:
```

如果某项不存在，必须写清“本 pack 新增”或“本任务不触碰”。不能留空让 worker 猜。

## Forbidden Shortcuts

以下情况默认是 finding；影响当前验收、数据、权限、账务、runtime 或发布时是 Critical：

- 用 bare dict 作为跨模块、API、task、sync、DB JSON 的长期合同。
- 在 route、page action、host、worker 内部临时拼 nested dict，绕过正式 Pydantic contract。
- 新增 route-local schema、一次性 helper 或兼容 helper，而不是放到现有 domain service、repository、shared contract、catalog 或 adapter。
- public API / client / service 返回 `dict[str, Any]`，或让上游 caller 自己理解 provider 原始 shape。
- silent unknown-field drop、`extra=allow`、兼容字段吞掉错误，却没有版本策略和 consumer 同步。
- 直接写 JSONB / SQLite JSON，不注册 column model，不走 validator。
- 新数据库字段没有 migration、repository 写入、read model、contract / API 同步和回归测试。
- 把 `runtime.*` schema 放进 Gateway migration。
- 新 port、command、chargeable action、capability 没有进入对应 registry / catalog。
- 测试 mock 当前仓库内部业务模块，导致只验证 mock 交互，不验证 public behavior。
- helper 只为绕过边界而存在，删除后不会让 caller 复杂度上升。

允许的原始 dict 只存在于 external transport adapter 的私有层。离开 adapter 前必须转换成正式 contract。

## Phase Requirements

### Design Review

设计必须写清：

- 数据或请求从哪个系统进入，由谁拥有、读取、确认、结算、展示、清理。
- API / DB / JSON / sync / task payload 的 producer、consumer、verifier。
- Pydantic model、schema version、error code、idempotency、retry、compatibility 和删除期限。
- 数据库字段归属、migration tree、repository / read model、rollback 或 backfill。
- 哪些外部 adapter 可以返回原始 shape，正式边界在哪里完成 `model_validate`。

### Plan Review

计划必须验真：

- 引用的 contract、repository、migration tree、registry、catalog、helper、fixture、命令真实存在；新建项明确标为新建。
- 每个 producer / consumer 都有对应修改或明确不受影响的证据。
- 测试覆盖 public behavior、contract validation、unknown field、error path、migration / repository / read model。
- 高风险合同改动有 deploy order、compatibility、manual gate 和 rollback。

### Task Pack

pack 必须按合同边界切分：

- 同一 shared contract、migration、repository、capability、chargeable action、runtime boundary 放同一 pack 或串行 pack。
- 不把 schema / tests / implementation 横切成不能单独证明价值的 pack。
- Contract anchors 进入 worker prompt。

### Implementation Review

reviewer 必须检查 diff：

- 是否新增或修改正式 Pydantic contract，而不是长期 bare dict。
- `schema_version`、`extra=forbid`、consumer 同步是否合理。
- JSON registry、migration tree、repository、read model、catalog、capability 是否闭合。
- public API / client / service 是否返回 typed contract。
- helper 是否落在正确 domain / service / adapter 层，而不是 host / route / page 临时层。
- 测试是否穿过 public behavior seam，没有 mock 掉当前仓库业务规则。

### Final Review

final review 必须确认：

- producer / consumer / verifier 全部同步。
- contract tests、repository / read model tests、API tests、UI action tests 或 release gate 已运行或明确不能运行的原因。
- deploy order、rollback、manual production verification 已闭合。
- 没有残留 ad-hoc helper、bare dict、未注册 JSON、错误 migration tree 或未同步 consumer。
