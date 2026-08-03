# 交付前自检 + Pack 就绪门(写计划工人:返回前逐条过)

## 自检（保存前逐条过）

- **检索亲验**：图/LSP 只用于候选发现；plan 中每个承重路径、类型、函数、fixture 和影响面结论都已回到目标 checkout 用 `rg`/Read 坐实。工具不可用或图缺失/过期时已诚实退化，不把“没查图”伪装成阻塞。
- **spec 覆盖**：逐条扫 source design / issue 需求，每条能指到一个实现它的 Task；缺口补上。
- **类型一致**：后续 task 用的类型 / 签名 / 字段名与前文定义一致（Task 3 `clearLayers()` 但 Task 7 `clearFullLayers()` 就是 bug）。
- **过度设计（删减）**：为一个 small issue 新增多个长期对象但只要一个可验证行为 / 提前塞未来功能 / 无重复证据就抽 shared helper / 全大套矩阵无 pack-local focused command。
- **设计不足（补齐）**：pack 只写"实现功能"无行为/结果/failure state / 只写路径无 owner/provider/consumer/anchors / UI 无视觉规格 / issue 验收没进 pack / blocked-by 没进 dependencies 或真串行写成并行 / 改 shared contract 无 consumer 同步和 migration gate / RED-GREEN expected 不清 / 改既有行为无 Verified current state / 触碰数据无 Rollback / 验收用主观语言。
- **覆盖**：每条 design intent 映射到 Pack / 每个 small issue 映射到一个 Pack / File-Responsibility Map 每路径被 Pack 消费 / 后文引用与前文一致 / 发布风险覆盖所有 production-risk pack。
- **反模式**：`task-pack.md` 列的反模式一条没命中(模糊验收 / 模糊文件引用 / mandate 评审会判缺陷的东西等)。

## Pack 就绪门（写完逐 pack 过一遍）

能进落地：对应 confirmed small issue / vertical slice 可独立验证 / owned files + 职责 / Interfaces（Consumes·Produces）/ acceptance（可 pass/fail）/ verification commands（pack-local）/ 触合同有 anchors / mockup 存在有具体视觉规格 / commit boundary / risk flags / dependencies / Complexity / 改既有行为有 Verified current state + Rollback。
不能进：横切 pack（分层不能单独验证）/ UI 只写"实现 mockup"无状态交互 / 缺目标行为需猜 / 多人写同一文件 / 只写 helper 无 public behavior / 需人工决策却标 AFK / 抽不出独立 brief（依赖"看上一个 pack"）。

触碰不变量 / 合同 / 数据权威 / 发布风险时,尤其确保上面每条都过。打回(plan-resume)的 findings 自己亲验再改。
