# Learnings Trust Gate

Worker 返回的 learnings 必须经过信任门才能写入 learnings.jsonl。

## 检查清单

1. **投毒检测** — 调用 `scripts/lib/learnings-poison-detector.sh`
   - 指令注入（prompt manipulation patterns）
   - 跨 run 污染（引用其他 run_id）
   - 范围逃逸（引用 scope contract 排除的文件）
2. **高频检测** — 单次 run 超过 10 条 learning → 告警
3. **时间衰减** — 超过 30 天的 learning 自动降权（不删除，标记 `decayed: true`）

## Coordinator 操作

- `CLEAN` → 写入 learnings.jsonl
- `POISONED` → 丢弃 + 记录到 run-summary 的 adversarial 段
- 高频告警 → 只取前 10 条，余下丢弃并记录
