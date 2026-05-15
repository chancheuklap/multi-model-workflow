# External Engineering Methods Adopted

这些方法来自外部 engineering skills 的调研，用于校准本 workflow。这里记录的是已吸收的具体行为，不是方法名称清单。

## Diagnose

用于 unknown root cause。

- 修复前先建立 feedback loop。
- 反馈闭环优先级：failing test、HTTP/API script、CLI invocation、headless browser flow、trace/log replay、throwaway harness、property/fuzz loop、bisect/differential loop、HITL checklist。
- 把 loop 当成产品打磨：让它更快、更尖锐、更确定。30 秒 flaky loop 价值很低，2 秒 deterministic loop 才能支撑修复。
- 非确定性问题的目标是提高复现率；可以循环 100 次、并行触发、施加压力、固定随机种子、冻结时间、缩小时序窗口。
- feedback loop 必须复现用户描述的同一个问题。
- 无法建立 loop 时停止，报告缺少的环境、日志、样本或人工步骤。
- 提出 3-5 个可证伪 hypotheses，每个写出可观察预测。
- 一次只验证一个 hypothesis 和一个变量。
- debug instrumentation 必须能区分 hypotheses；临时日志用唯一 `[DEBUG-...]` 前缀，收尾清理。
- 回归测试必须落在 correct seam；如果没有 correct seam，这本身就是 architecture finding。
- 修复后先重跑原始 loop，再跑 focused regression，最后清理 throwaway harness / temporary instrumentation。

## TDD

用于 worker 实现和 review。

- 测试 public behavior，不测试 private helper 或内部调用顺序。
- 每个行为是一条 tracer bullet：失败检查 -> 最小实现 -> focused verification。
- 禁止 horizontal slicing：不要先写全部 tests / schema / endpoint shell，再最后补行为。
- 好测试像 specification：描述系统做什么，不描述内部怎么做。
- mock 只用于外部边界，例如第三方 API、时间、随机数、文件系统、不可控进程。默认不 mock 当前仓库内部模块或要验证的业务规则。
- 设计可测试 interface：依赖从外部注入，不在函数内部创建；优先返回结果，少做隐藏副作用；interface surface 越小越好。
- 找不到 public behavior seam 时，不强行测 internal detail；报告 missing seam。
- refactor 只能在 GREEN 后做；refactor 后重跑对应 behavior tests。
- refactor 候选包括 duplication、long method、shallow module、feature envy、primitive obsession，以及新代码暴露出的旧设计问题。

## Grill With Docs

用于 Phase 0 design / plan review。

- domain language 必须对齐项目正式文档。
- AgentFlow 权威入口是 `AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、SPEC、ADR、GUIDE。
- 模糊词必须落到系统、状态、字段、事件或用户可见结果。
- 对每个新对象、新状态、新流程、新合同，追问 owner / writer / reader / verifier / cleanup responsibility。
- 至少用两个场景挑战设计，其中一个必须是失败、空状态、权限、重复提交、并发或回滚。
- 只有 hard-to-reverse、without context surprising、real trade-off 同时成立时才要求 ADR。
- 如果用户或文档提出的说法能被代码验证，先查代码；如果代码与设计说法矛盾，作为 finding。

## To-Issues

用于 Task Pack 设计。

- Task Pack 必须是 vertical slice。
- 完成后必须 demoable 或 independently verifiable。
- pack brief 必须包含 current behavior、desired behavior、key interfaces、acceptance criteria、out of scope。
- 标明 AFK / HITL。
- 依赖只写真实阻塞关系，不制造伪依赖。
- 长期 brief 优先写行为和接口，不写易漂移的 line number。文件路径只在立即执行 pack 中作为 owned files 使用。
- issue publishing、triage labels 和 issue tracker state machine 不进入本 workflow；这里只吸收 vertical slice 和 durable brief 方法。

## Improve Codebase Architecture

用于 review finding 分类。

- 用 deletion test、seam、adapter、interface depth、leverage、locality 判断架构摩擦。
- 单 adapter seam 通常是假 seam；多个 adapter、明确生产/测试边界或多个变化方向才可能是真 seam。
- dependency category 影响设计建议：
  - in-process：可直接 deepen，通过新 interface 测试；
  - local-substitutable：有本地替身时可 deepen，例如 test DB / in-memory filesystem；
  - remote but owned：定义 port，生产 adapter + test adapter；
  - true external：第三方服务用 injected port 和 mock adapter。
- interface 是测试表面。新测试应穿过 deep module interface；旧 shallow module unit tests 如果只测实现细节，应在新 seam 稳定后删除。
- 架构问题不默认阻塞交付。只有造成生产风险、数据风险、权限风险、账务风险、无法回滚或验收不成立时，才升级为 blocker。

## Prototype Gate

不作为默认路径，只在 Phase 0 发现 design 无法靠文档审查回答时使用。

- 先写清 prototype 要回答的问题。
- 逻辑 / 状态模型问题：做一个可运行 terminal / CLI prototype，展示每步状态。
- UI 方向问题：做多个差异明显的 UI variants，并能一条命令启动。
- prototype 从第一天就是 throwaway：不默认持久化，不碰生产数据，不写成正式架构。
- 完成后只保留答案：吸收到 design / ADR / plan；prototype 要删除或明确吸收进正式代码。

## 不纳入 Runtime 的外部内容

- 不安装整套外部 skills。
- 不引入 `CONTEXT.md`、`docs/agents/domain.md`、triage labels 或 issue tracker state machine。
- 不让外部 skill 替代 Claude plugin 原始 workflow；只把其中经过筛选的方法融合进 review / worker / explorer / Task Pack 合同。
