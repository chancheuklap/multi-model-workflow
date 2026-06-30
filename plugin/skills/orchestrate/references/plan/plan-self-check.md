# Plan 自检 + Pack 就绪门（写完 / 保存前读全文）

作者保存前自己过的闸。②计划审由 flow 触发(plan handoff pass 后,独立 Codex 审),本阶段 不自派、不复制审题。

## 自检（保存前）

- **spec 覆盖**：逐条扫 source design / issue 需求，每条能指到一个实现它的 Task；缺口补上。
- **类型一致**：后续 task 用的类型 / 签名 / 字段名与前文定义一致（Task 3 `clearLayers()` 但 Task 7 `clearFullLayers()` 就是 bug）。
- **过度设计（删减）**：为一个 small issue 新增多个长期对象但只要一个可验证行为 / 提前塞未来功能 / 无重复证据就抽 shared helper / 全大套矩阵无 pack-local focused command。
- **设计不足（补齐）**：pack 只写"实现功能"无行为/结果/failure state / 只写路径无 owner/provider/consumer/anchors / UI 无视觉规格 / issue 验收没进 pack / blocked-by 没进 dependencies 或真串行写成并行 / 改 shared contract 无 consumer 同步和 migration gate / RED-GREEN expected 不清 / 改既有行为无 Verified current state / 触碰数据无 Rollback / 验收用主观语言。
- **覆盖**：每条 design intent 映射到 Pack / 每个 small issue 映射到一个 Pack / File-Responsibility Map 每路径被 Pack 消费 / 后文引用与前文一致 / 发布风险覆盖所有 production-risk pack。
- **反模式**：见 `plan-rigor.md`，命中即修。

## Pack 就绪门（写完逐 pack 过一遍）

能进落地：对应 confirmed small issue / vertical slice 可独立验证 / owned files + 职责 / Interfaces（Consumes·Produces）/ acceptance（可 pass/fail）/ verification commands（pack-local）/ 触合同有 anchors / mockup 存在有具体视觉规格 / commit boundary / risk flags / dependencies / Complexity / 改既有行为有 Verified current state + Rollback。
不能进：横切 pack（分层不能单独验证）/ UI 只写"实现 mockup"无状态交互 / 缺目标行为需猜 / 多人写同一文件 / 只写 helper 无 public behavior / 需人工决策却标 AFK / 抽不出独立 brief（依赖"看上一个 pack"）。

## 重大 / 碰红线

自检 + Pack 就绪门逐条过后 handoff,**②计划审由 flow 触发**(独立 Codex 审,见编排的审核 loop)——本阶段 不自派审、不自己跳阶段。触碰不变量 / 合同 / 数据权威 / 发布风险时尤其确保上面每条都过。审回的 findings 自己亲验再改,外部模型是劳动力不是事实源。
