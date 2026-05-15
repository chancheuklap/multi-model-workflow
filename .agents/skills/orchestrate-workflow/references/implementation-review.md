# Implementation Review Contract

Phase A 审 Task Pack 的实现。目标是确认 worker 的代码真的完成 pack，而不是相信 worker 自报。

## Dispatch: Pack Review

派 `code_reviewer`。生产风险 pack 追加 `release_reviewer`。

必须提供：

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
4. 对照 pack brief 逐 task 审查。

## Phase 1: Spec Compliance

先审 spec compliance。有 Critical 时停止，不进入 code quality。

检查：

- task 要求的功能是否已实现。
- 是否做错了行为。
- 是否漏掉错误路径、权限、空状态、重复提交、并发、回滚。
- 是否做了未要求的 scope creep。
- pack 内多个 task 是否互相兼容。
- 安全问题无论 spec 是否要求，默认 Critical。

Critical：

- 功能缺失或做错。
- 安全漏洞、权限绕过、敏感数据泄漏。
- 违反项目不变量或跨服务合同。

## Phase 2: Code Quality

仅 spec compliance 通过后执行。

检查：

- 逻辑错误、空值处理、类型不匹配、资源泄漏、竞态条件。
- 项目规则：logger、contract wall、模块边界、单一权威源、registry、`AGENTS.override.md`。
- 测试质量：public behavior、真实边界、no internal mocks、正确 seam。
- 文件健康：不必要重复、过早抽象、临时 instrumentation、死代码。

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
- 涉及生产风险：`release_reviewer`。
- 改变产品范围或业务规则：用户决策。

## 输出格式

```text
### Spec Compliance
结论: 通过 / 阻塞
Critical:
Important:

### Code Quality
结论: 通过 / 阻塞 / 未执行
Critical:
Important:

### Verification
命令:
结果:

### Routing
```

每条 finding 必须有 severity、confidence、file/line、evidence、why it matters、remediation、routing。
