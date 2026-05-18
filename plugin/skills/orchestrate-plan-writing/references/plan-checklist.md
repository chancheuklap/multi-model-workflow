# Plan Checklist

保存 plan 前自检。分为过度设计检查和设计不足检查。

## 过度设计信号（删减）

- [ ] 为一个 small issue 新增多个长期对象 / registry / migration / UI surface，但 source issue 只要求一个可验证行为。
- [ ] 提前塞入未来消息中心 / 历史页 / dashboard / 跨设备恢复 / 复杂权限 / 运营后台。
- [ ] 因多个 pack 触碰同一文件就抽 shared helper，但没有当前重复复杂度证据。
- [ ] 细 task 写大量生产代码，超过 plan 所需的接口 shape 和断言。
- [ ] 预设未验证的 fixture / class / schema 字段要求 worker 照做。
- [ ] verification 变成大而全矩阵，pack-local 行为没 focused command。
- [ ] Scope Check 写 yes split 但仍硬塞多个大 issue。

修正：当前 issue 没要求的能力移到 out of scope；没有 path reality 的细节改成"先 `rg` 验真再落实"；新抽象绑定至少两个真实 consumer。

## 设计不足信号（补齐）

- [ ] pack 只写"实现功能"，无行为 / 结果 / failure state。
- [ ] 只写路径和文件，无 owner / provider / consumer / contract anchors。
- [ ] UI 工作无 states / viewport / interaction / visual verification。
- [ ] billing / permission / runtime 无 Contract anchors。
- [ ] issue acceptance 没进 pack acceptance。
- [ ] blocked-by 没进 dependencies，或真串行写成并行。
- [ ] pack 改 shared contract 却无 consumer 同步和 migration gate。
- [ ] production-risk 只在 risk flags，没进"发布风险和人工门禁"。
- [ ] 只列最终大套测试，无 pack-local verification。
- [ ] worker 仍需自行决定术语 / 文案 / UI target / issue hierarchy。
- [ ] RED / GREEN expected result 不清楚。

修正：术语不清 → `NEEDS_DISCOVERY`；需方案比较 → `NEEDS_DECISION`；issue 太大 → `NEEDS_ISSUES`；架构卡住 → `NEEDS_ARCHITECTURE`。

## Coverage 检查

- [ ] 每条 source design intent 映射到 large issue section 或 Task Pack。
- [ ] 每个 small issue 映射到一个 Task Pack。
- [ ] Source Coverage Map 非空泛。
- [ ] File / Responsibility Map 每个路径被 Task Pack 消费。
- [ ] 发布风险覆盖所有 production-risk pack。
- [ ] 后文引用 type / field / fixture / command 与前文一致。
- [ ] Execution owner = Orchestrate Workflow，无额外 handoff。
- [ ] 缺 small issue 时不生成正式 pack。

## 质量结论

```text
Plan quality: pass / needs repair / route required
Overdesign checked:
Underdesign checked:
Largest remaining risk:
Route if not pass:
```
