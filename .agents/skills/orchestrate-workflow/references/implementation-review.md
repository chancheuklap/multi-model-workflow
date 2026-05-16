# Implementation Review 合同

Phase A 审 Task Pack 的实现。独立确认 worker 是否真实完成 pack；不接受 worker 自报作为通过证据。

每个 pack 最多 3 轮修复。每轮 repair 必须说明上一轮为什么不够，并改变方法、证据或边界；不能重复同一种修补。

## 派发：Pack Review

派 `code_reviewer`。生产风险 pack 追加 `release_reviewer`。

必须提供：

- Read first：plan、pack 相关 design / SPEC / ADR / GUIDE、相关 UI / UX mockup、根 `AGENTS.md`、相关 `PROJECT.md` / `ENGINEERING-RULES.md`、changed files 涉及目录的 `AGENTS.override.md` / `agents.overrides.md`；
- Project baseline：本 pack 必须遵守的数据权威、模块边界、contract wall、测试路由、日志规则和风险约束；
- Contract anchors：本 pack 涉及的 API、Pydantic、DB、JSON、task、sync、catalog、capability、helper 边界；
- Mockup anchors：UI / UX pack 的目标页面、viewport、states、interaction 和允许偏差；
- plan path；
- pack brief；
- worker report；
- base SHA 或 diff scope；
- verification commands；
- changed files；
- risk flags。

## 必做独立验证

Reviewer 不信任 worker self-report：

1. 读取 `git diff <base>..HEAD` 或当前 diff。
2. 读取变更文件。
3. 跑相关 focused verification，或说明为什么无法运行。
4. UI / UX pack 必须打开实现或检查截图 / DOM / CSS，和 mockup anchors 对照。
5. 涉及合同边界时，按 `contract-boundary.md` 对照 diff 检查正式 contract、registry、migration、repository、read model、catalog 和 producer / consumer。
6. 对照 pack brief 逐 task 审查。

## Phase 1：Spec Compliance

先审 spec compliance。有 Critical 时停止，不进入 code quality。

检查：

- task 要求的功能是否已实现。
- UI / UX task 是否按 mockup 实现了对应页面状态、信息架构、布局、组件状态和交互。
- UI / UX finding 是否有明确目标。如果目标来自已批准 mockup / design / acceptance criteria，按 implementation divergence 审；如果目标来自主观反馈且 role、state、hierarchy、copy、interaction 或 verification 不清，route 给 upstream `grill-with-docs`，不要要求 worker 自行改。
- 是否做错了行为。
- 是否漏掉错误路径、权限、空状态、重复提交、并发、回滚。
- API / Pydantic / DB / JSON / helper 边界是否按 Contract anchors 实现，没有让 worker 自创临时结构。
- 是否做了未要求的 scope creep。
- pack 内多个 task 是否互相兼容。
- 安全问题无论 spec 是否要求，默认 Critical。

Critical：

- 功能缺失或做错。
- mockup 中关键 UI / UX 状态未落地，或实现与 mockup 的信息架构、交互、视觉层级明显不一致。
- UI / UX 目标含混却已被 worker 自行落成新行为，导致验收标准不可追溯。
- 安全漏洞、权限绕过、敏感数据泄漏。
- 新 API / DB / JSON / task / sync payload 绕过 Pydantic contract、JSON registry、migration tree、catalog 或 consumer 同步。
- 违反项目不变量或跨服务合同。

## Phase 2：Code Quality

仅 spec compliance 通过后执行。

检查：

- 逻辑错误、空值处理、类型不匹配、资源泄漏、竞态条件。
- 项目规则：logger、contract wall、模块边界、单一权威源、registry、`AGENTS.override.md`。
- 合同质量：`schema_version`、`extra=forbid`、typed public return、unknown-field handling、producer / consumer 同步、DB migration / repository / read model 闭合。
- helper placement：新增 helper 是否属于 domain service、repository、adapter 或 shared contract；route / host / page action 中的一次性 helper 默认可疑。
- 测试质量：public behavior、真实边界、no internal mocks、正确 seam。测试应描述系统做什么，不断言 private helper、内部调用次数、内部调用顺序或临时数据结构。
- UI / UX 证据：browser screenshot、DOM key scan、responsive viewport check、manual checklist 或视觉回归检查是否覆盖 mockup 关键状态。
- Mock 边界：第三方 API、系统时间、随机数、文件系统、不可控进程可以 mock；当前仓库内部模块、业务规则、要验证的 collaborator 默认不 mock。
- Interface testability：如果实现为了可测性暴露 private seam、引入 single-adapter interface、或让 caller 学会过多 implementation detail，记录 architecture finding。
- Architecture routing：bad seam、single-adapter interface、repeated repair loop、隐藏 coupling 或测试只能断言内部细节时，route 给 upstream `improve-codebase-architecture`；只有影响当前 correctness、data、permission、billing、runtime、rollback 或 release safety 时阻塞本 pack。
- 文件健康：不必要重复、过早抽象、临时 instrumentation、死代码。

Refactor 只在 GREEN 后允许。reviewer 可以建议 refactor，但不能用普通整洁偏好阻塞 pack；只有影响 correctness、test seam、项目规则或当前验收时才升级。

## Routing

```text
needs coding_worker
needs complex_coding_worker
needs complex_code_explorer
needs release_reviewer
needs user decision
```

判断：

- 能说清楚改哪里改什么：worker。
- 问题存在但根因不明：`complex_code_explorer`。
- desired behavior、UI target、business term 或 object ownership 不清：upstream `grill-with-docs`。
- bad seam、repeated repair、single-adapter interface 或 weak test surface：upstream `improve-codebase-architecture`。
- 涉及生产风险：`release_reviewer`。
- 改变产品范围或业务规则：用户决策。

## Result Payload

```text
Spec Compliance:
Phase summary: 通过 / 阻塞
Critical:
Important:

Code Quality:
Phase summary: 通过 / 阻塞 / 未执行
Critical:
Important:

Verification summary:
命令:
结果:

Routing summary:
```

Coordinator 派发必须包含标准顶层 return headings。本 payload 放在 `### Result` 下。顶层 `### Verdict` 只使用 `pass / blocked / needs repair / needs context`；“通过 / 阻塞 / 未执行”只作为 spec compliance 和 code quality 的 phase summary。每条 finding 必须使用统一 shape：severity、confidence、locator、evidence、impact、remediation、routing。Review result 不能只返回自由文本结论。
