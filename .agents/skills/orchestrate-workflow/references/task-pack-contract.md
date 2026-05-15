# Task Pack Contract

Task Pack 是 Codex subagent 的执行单位，不是 plan section 的机械复制。

## 合格标准

一个 pack 必须同时满足：

- 是 vertical slice，完成后能 demo 或 independently verify。
- 有用户可见行为、公开接口行为或可检查系统效果。
- 有 owned files / responsibilities。
- 涉及 API / Pydantic / DB / JSON / sync / task payload / UI action / helper 时，有 Contract anchors：owner、provider、consumer、Pydantic model、schema_version、registry / migration / catalog、repository / read model、verification。
- UI / UX pack 有 mockup anchors：路径、页面区域、viewport、states、interaction。
- 有 acceptance criteria。
- 有 verification commands 或复现检查。
- 有 risk flags：普通、高风险、生产风险、HITL。
- 依赖关系是真阻塞，不是“可能有关”。

## 不合格 Pack

以下 pack 不应派发：

- 只按技术层横切：“先写全部 tests / schema / templates / endpoint shell，再写 implementation”。
- 只按前端 / 后端 / 测试分层，但完成后不能单独验证。
- UI / UX 工作只写“实现 mockup”但没有拆出可验收的页面状态、交互、viewport 或视觉证据。
- 没有 owned files。
- 没有验证命令。
- 多个 worker 会同时写同一文件、同一 migration、同一 shared contract。
- 需要同一个 Pydantic model、DB column、JSON registry、capability、chargeable action、port / command catalog，却被拆给多个 worker 并行。
- 只写“新增 helper / dict shape / schema”但没有 owner、consumer、正式 contract 和 public behavior 验证。
- 需要产品、账号、真实环境、人工验收或权限决策，却标成 AFK。

## 分包规则

- 触碰同一文件或同一合同的 tasks 放同一 pack。
- 同一 API / Pydantic contract / DB migration / repository / JSON registry / capability / chargeable action / runtime boundary 放同一 pack 或串行 pack。
- migration、billing、auth、permissions、runtime、browser takeover、shared contract 默认串行。
- 独立 pack 才并行。
- 如果一个 pack 太大，按可验证行为拆，不按文件层拆。
- UI / UX pack 按用户可见状态拆，例如 empty / loading / success / error / permission / responsive viewport；不要按 CSS / JS / template 横切。
- 如果一个 task 太小但共享上下文，和相邻 task 合并。

## Pack Brief 模板

```text
Pack:
Goal behavior:
Tasks:
Owned files / responsibilities:
Read first:
Contract anchors:
Mockup anchors:
Acceptance criteria:
Verification commands:
Risk flags:
AFK / HITL:
Dependencies:
Parallel safety:
Out of scope:
```

这个 brief 进入 worker dispatch prompt。不要只发 task 标题。

## Durable Handoff Brief

当 pack 要跨会话交接、导出为 issue、或留给以后 agent 处理时，用 durable brief，不要只保存当前文件行号。

```text
Current behavior:
Desired behavior:
Key interfaces:
Acceptance criteria:
Out of scope:
Risk flags:
AFK / HITL:
```

原则：

- 写行为合同，不写“去某文件第 N 行改 X”。
- 可以命名稳定类型、函数签名、配置 shape 或业务对象，但不要把临时路径当成唯一入口。
- acceptance criteria 必须逐条可验证。
- UI / UX durable brief 必须保留 mockup path、目标 viewport、关键 states 和允许偏差。
- out of scope 必须明确，避免 agent 顺手扩大范围。
- 如果需要文件范围用于立即执行，把它放在 Pack Brief 的 owned files 中，不放进 durable contract 的核心语义。
