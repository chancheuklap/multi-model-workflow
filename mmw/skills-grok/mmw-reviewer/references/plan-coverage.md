# 覆盖质量审

**谁读**：任务名是「覆盖质量审」的审查者。

一张 ticket 对应一份 plan 和一个 `worker`。按整份 plan 判断它是否给出了可执行路线。

plan 按批次写：task 只给本批次的 plan，不在本批次的 ticket 没有 plan 是常态，不是 finding。

## 往哪里看

- **目标覆盖**：本批次每张 ticket 都有 plan；ticket 的每条验收都映射到 `## Acceptance` 的证明方式。
- **覆盖扫描**（task 注明首批次时执行）：沿 spec 的 `## Implementation Decisions` 与 `## User Stories` 逐条走，指认承接它的 ticket；指认不出承接方的条目报 finding。
- **实施路线**：步骤顺序成立，覆盖从当前状态到目标状态的必要改动。`worker` 不需要猜业务决定，但可以在已确认边界内选择局部实现。
- **prototype 决定**：存在 prototype 时，plan 引用了用户选中版本和对应逐轮记录；每条被采用的决定都落进实施步骤或验收。
- **research 事实**：ticket 使用 research 时，plan 引用了 research 索引和精确文件；适用的范围快照与未查清项进入实施步骤或验收。
- **验证**：每条验收都有测试、产物或人工结果。界面任务把自动验证与浏览器审批分开。
- **范围**：plan 没有漏掉 ticket 必需的迁移、登记、文档或回滚，也没有加入 ticket 之外的功能。

## 这几种一定要报

ticket 验收没有证明方式；步骤执行完仍达不到目标；关键顺序或依赖缺失；未决业务决定被塞给 `worker`；用户确认的 prototype 决定没有进入路线；需要真实凭证、生产操作或人工决定却没有关卡。

唯一判据：`worker` 读完整份 plan 后，能否在不重开产品决定的前提下完成这张 ticket。
