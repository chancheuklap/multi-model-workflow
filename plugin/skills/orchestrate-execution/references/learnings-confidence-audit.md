# Learnings Confidence Audit

> **流程位置**：review finding disposition 阶段 · Coordinator 逐条处理 finding 时参考

## Low-Confidence Finding 处理规则

Codex review 返回的每条 finding 带有 confidence 1-10。Coordinator 不盲目接受所有 finding，按 confidence 级别分层处理。

### Confidence 1-3 (Low)

**默认动作**：suppress — 记录为 `"suppressed: low confidence"`。

```bash
state.sh disposition append --run-id <run_id> --finding-id <id> \
  --disposition suppress --confidence <1-3> --severity L \
  --evidence "suppressed: low confidence (reviewer confidence=$confidence)"
```

**覆写条件**：Coordinator 手动升级需附证据：
- Coordinator 独立验证了 finding 的事实主张
- 即使 confidence 低，finding 指向已知的真实问题
- 覆写时必须在 evidence 中写明独立验证的方法和结果

### Confidence 4-6 (Medium)

**默认动作**：亲验 + 补证 — 不直接 accept 或 reject。

1. Coordinator 先用 Read/grep 验证 finding 的事实主张
2. 如果无法确认 → 派 `code-explorer` 或 `complex-code-explorer` 补证
3. Explorer 返回 confirmed → accept；refuted → reject；partially confirmed → 细化 scope 再补证

### Confidence 7-10 (High)

**默认动作**：亲验后 accept 或 reject。

1. Coordinator 用 Read/grep 验证 finding 的事实主张
2. 验证通过 → accept（大多数情况）
3. 验证失败（Coordinator 找到反向证据）→ reject，evidence 中写明反向证据

## 审计追踪

所有 disposition 决定都写入 workflow-state：
- `state.sh disposition append` 记录每条 finding 的 disposition + confidence + evidence
- `review-effectiveness.sh` 聚合统计（reject_count, suppress_count, path_a/b_count）
- 统计用于 Direction Check 和 Final Review 的 review effectiveness 报告

---

## Calibration Learning 触发规则

| 条件 | 动作 | Learning 类型 |
|------|------|-------------|
| Finding confidence < 7 但 Coordinator 亲验后 accept | 写入 calibration learning："reviewer under-confidence on this pattern" | review-calibration |
| Finding confidence ≥ 8 但 Coordinator reject | 写入 over-confidence learning："reviewer confident but wrong on [category]" | review-calibration |
| 同一 category 累计近 5 次 run 中 3 条 reject | 写入 reviewer-drift learning："reviewer consistently wrong on [category]" | reviewer-drift |
| Worker 返回 needs repair（首次 dispatch 未通过） | 写入 repair-pattern learning | repair-pattern |
| Worker 修改了 owned files 之外的文件 | 写入 scope-drift learning | scope-drift |

---
> **下一步**：回到当前 disposition 处理流程继续下一条 finding。
