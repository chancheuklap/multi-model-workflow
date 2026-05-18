# Contract Boundary

任意 design / plan / Task Pack / review / repair 触碰跨边界改动时读取。

## Boundary Types

- API request / response（HTTP、FastAPI route、local agent API、UI action endpoint）
- Pydantic protocol（模块内正式 contract 或 shared contracts）
- DB entity / read model（表、列、repository、projection）
- JSON payload（JSONB、Local SQLite JSON、runtime state JSON）
- Task / sync payload（durable task、sync outbox、scheduler event）
- Business catalog（port、command、chargeable action、capability、permission）
- External adapter（第三方 API、浏览器、支付、文件系统）
- UI form action（表单输入、页面 action、状态更新）

## Contract Anchors

dispatch prompt / plan pack / review finding 使用：

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

不存在的项写清"本 pack 新增"或"本任务不触碰"。

## Forbidden Shortcuts

以下默认是 finding；影响当前验收 / 数据 / 权限 / 账务 / runtime / 发布时是 Critical：

- 用 bare dict 作为跨模块长期合同。
- route / host / page 内临时拼 nested dict 绕过正式 contract。
- 新增 route-local schema / 一次性 helper 而不放到 domain service / shared contract。
- public API 返回 `dict[str, Any]`。
- silent unknown-field drop / `extra=allow` 无版本策略。
- 直接写 JSONB/SQLite JSON 不注册不走 validator。
- 新 DB 字段没有 migration / repository / read model / 回归测试。
- 新 port / command / chargeable action / capability 没进 registry / catalog。
- 测试 mock 当前仓库内部业务模块。
- helper 只为绕过边界而存在。

允许原始 dict 只在 external transport adapter 私有层。
