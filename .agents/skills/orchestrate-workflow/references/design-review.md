# Design Review Contract

Phase 0a 审 design doc。目标不是润色文字，而是判断设计能否被计划、实现和最终验证承接。

## Dispatch 1: Design Content Review

派 `code_reviewer`。让 reviewer 专注设计自身，不审代码实现。

检查：

- 完整性：是否有 TODO / TBD / 空节；用户旅程是否覆盖起点、操作、结果、异常路径。
- 可测试性：每条“用户应该能 X / 系统应该 Y”能否写出命令、API、UI 操作或手工验收步骤。
- 场景挑战：至少一个 happy path，加一个失败、空状态、权限不足、重复提交、并发或回滚场景。
- 内部一致性：术语、状态、数据流、责任边界是否前后一致。
- 范围纪律：是否把未来假想需求混进本阶段，或遗漏本阶段必须承诺的能力。

Critical：

- 核心意图不可测试。
- 文档内部矛盾会导致 plan 写错。
- 关键业务场景缺失。
- 新对象、新状态、新合同缺 owner / writer / reader / verifier / cleanup responsibility，并且影响验收。

输出：

```text
### 设计文档 - 内容与逻辑审查
结论: 通过 / 阻塞
Critical:
Important:
低置信度观察:
```

每条 finding 必须有 design doc section、证据、为什么会影响下游、具体修正建议、confidence。

## Dispatch 2: Project Alignment Review

派 `code_reviewer`；如果设计涉及 production-risk，派 `release_reviewer`。

先读项目规则：`AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、相关 SPEC / ADR / GUIDE。

检查：

- domain language 是否使用项目正式术语。
- 数据权威源是否正确，例如 Gateway / Collection / Local Agent 的 owner 是否混乱。
- 模块边界和依赖方向是否正确。
- contract wall、LINEAGE、billing four-state、local-first / cloud-authority 等不变量是否被破坏。
- 新端口、命令、收费动作、迁移、JSONB 字段、后台任务是否写明注册位置和消费方。
- 设计是否依赖项目中不存在的基础设施、外部 API 或运行环境。
- hard-to-reverse、without context surprising、real trade-off 三者同时成立时，是否需要 ADR / SPEC / GUIDE 更新。

Critical：

- 违反项目北极星、不变量、权威源或模块边界。
- 设计依赖不存在的基础设施。
- 跨服务合同缺 producer / consumer / verification。
- 生产数据、权限、账务、迁移或回滚风险未设计。

输出：

```text
### 设计文档 - 项目对齐审查
结论: 通过 / 阻塞
Critical:
Important:
低置信度观察:
```

Phase 0 finding 返回 coordinator。主线程修文档；不派 worker 写代码。
