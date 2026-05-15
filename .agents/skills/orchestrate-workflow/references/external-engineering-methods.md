# External Engineering Methods Adopted

这些方法来自外部 engineering skills 的调研，用于校准本 workflow。这里记录的是已吸收的具体行为，不是方法名称清单。

## Diagnose

用于 unknown root cause。

- 修复前先建立 feedback loop。
- 反馈闭环优先级：failing test、HTTP/API script、CLI invocation、headless browser flow、trace/log replay、throwaway harness、property/fuzz loop、bisect/differential loop、HITL checklist。
- feedback loop 必须复现用户描述的同一个问题。
- 无法建立 loop 时停止，报告缺少的环境、日志、样本或人工步骤。
- 提出 3-5 个可证伪 hypotheses，每个写出可观察预测。
- 一次只验证一个 hypothesis 和一个变量。
- debug instrumentation 必须能区分 hypotheses；临时日志用唯一 `[DEBUG-...]` 前缀，收尾清理。
- 修复后先重跑原始 loop，再跑 focused regression。

## TDD

用于 worker 实现和 review。

- 测试 public behavior，不测试 private helper 或内部调用顺序。
- 每个行为是一条 tracer bullet：失败检查 -> 最小实现 -> focused verification。
- 禁止 horizontal slicing：不要先写全部 tests / schema / endpoint shell，再最后补行为。
- mock 只用于外部边界。默认不 mock 当前仓库内部模块或要验证的业务规则。
- 找不到 public behavior seam 时，不强行测 internal detail；报告 missing seam。

## Grill With Docs

用于 Phase 0 design / plan review。

- domain language 必须对齐项目正式文档。
- AgentFlow 权威入口是 `AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、SPEC、ADR、GUIDE。
- 模糊词必须落到系统、状态、字段、事件或用户可见结果。
- 对每个新对象、新状态、新流程、新合同，追问 owner / writer / reader / verifier / cleanup responsibility。
- 至少用两个场景挑战设计，其中一个必须是失败、空状态、权限、重复提交、并发或回滚。
- 只有 hard-to-reverse、without context surprising、real trade-off 同时成立时才要求 ADR。

## To-Issues

用于 Task Pack 设计。

- Task Pack 必须是 vertical slice。
- 完成后必须 demoable 或 independently verifiable。
- pack brief 必须包含 current behavior、desired behavior、key interfaces、acceptance criteria、out of scope。
- 标明 AFK / HITL。
- 依赖只写真实阻塞关系，不制造伪依赖。

## Improve Codebase Architecture

用于 review finding 分类。

- 用 deletion test、seam、adapter、interface depth、leverage、locality 判断架构摩擦。
- 单 adapter seam 通常是假 seam；多个 adapter、明确生产/测试边界或多个变化方向才可能是真 seam。
- 架构问题不默认阻塞交付。只有造成生产风险、数据风险、权限风险、账务风险、无法回滚或验收不成立时，才升级为 blocker。

## 不纳入 Runtime 的外部内容

- 不安装整套外部 skills。
- 不引入 `CONTEXT.md`、`docs/agents/domain.md`、triage labels 或 issue tracker state machine。
- 不把 prototype 作为默认路径；只有设计不确定性必须先回答时才走单独 prototype 任务。
