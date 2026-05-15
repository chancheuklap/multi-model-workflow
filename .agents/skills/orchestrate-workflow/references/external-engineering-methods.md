# External Engineering Methods

把外部方法压成七条硬习惯。只在对应 phase 需要时读取本文件；不要把方法名写进 dispatch 代替具体要求。

| 习惯 | 触发 | 执行动作 |
| --- | --- | --- |
| Feedback loop first | bug、flaky、unknown root cause | 先构造 failing test、HTTP/API script、CLI、headless browser、trace/log replay、throwaway harness、property/fuzz、bisect/differential loop；HITL 最后使用并写成清单。 |
| Falsifiable hypotheses | loop 建立后 | 提 3-5 个 hypothesis，每个写预测和证伪条件；一次只验证一个变量；无证据连续失败后停止扩大搜索。 |
| Vertical slice TDD | implementation pack | 每轮只做一个 public behavior：失败检查 -> 最小实现 -> focused verification -> 必要 refactor。禁止先铺 tests/schema/shell 再最后补行为。 |
| Public behavior tests | 测试和 review | 测 HTTP/API、CLI、UI state、DB-visible effect、public interface 或 documented workflow；mock 只用于第三方、时间、随机数、文件系统、不可控进程等外部边界。 |
| Grill with docs | design / plan review | 术语对齐正式文档；新对象/状态/流程/合同必须有 owner、writer、reader、verifier、cleanup；至少挑战 happy path + 一个失败/权限/重复/并发/回滚场景。 |
| Durable Task Pack | task split / handoff | pack 必须 demoable 或 independently verifiable，写 current behavior、desired behavior、key interfaces、acceptance criteria、out of scope、AFK/HITL 和真实依赖。 |
| Architecture friction, not noise | review / final review | 用 deletion test、seam、adapter、interface depth、leverage、locality 判断；只有造成生产、数据、权限、账务、回滚或当前验收风险时才升级 blocker。 |

## Prototype Gate

只在 Phase 0 无法靠文档判断状态机、UI 方向或接口形状时使用：

- 先写清 prototype 要回答的问题。
- 逻辑 / 状态模型：做可运行 terminal / CLI prototype，展示每步状态。
- UI 方向：做多个差异明显的 variants，并能一条命令启动。
- prototype 默认 throwaway，不碰生产数据，不写成正式架构。
- 完成后只保留答案：吸收到 design / ADR / plan；prototype 删除或明确转为正式代码。
