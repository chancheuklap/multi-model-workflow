# Review Budget

## 全局预算

一个 Formal Orchestrate 的 review dispatch 总数有预算。超出预算时强制 Direction Check（见 `coordinator-tools.md`），由 coordinator 判断是继续、简化还是停止。

| 组成部分 | 预算 |
| --- | --- |
| Phase 0a baseline | 2 |
| Phase 0b baseline | 3 |
| Phase A Pack Review | 每个 pack 1 |
| Phase B Final Review | 2 |
| Release gate | 最多 2（early + final 合并同发布风险面） |
| Repair headroom | baseline 总数 × 1.0 |

**公式**：预算 = 2 + 3 + N + 2 + 2 + (7 + N) = 2N + 16

示例：4 个 pack → 预算 = 13 + 11 = 24。实际 happy path 用 13，留 11 给 repair。

**刹车机制**：累计 review dispatch 达到预算的 80% 时，coordinator 必须做 Direction Check（见 `coordinator-tools.md`），重述当前 phase / 剩余工作 / 累计 findings / 是否继续。超过预算时停止并报告用户。

## Budget File Lifecycle

- **Created**: 由 `orchestrate-workflow` entry gate 在选择 Formal Orchestrate 时创建 `.claude/multi-model-workflow/budget-<run_id>.json`，同时写 `.claude/multi-model-workflow/active-run-id`。
- **Updated**: 由 `track-review-budget.sh`（SubagentStop on `codex:codex-rescue`）递增 `budget_used` 并追加 dispatch 记录；由 `orchestrate-plan-review` 在确认 pack count 后更新 `budget_total` 和 `pack_count`。
- **Read**: 每个 review skill 通过 `active-run-id` 找到 budget file，检查 budget。
- **Deleted**: 由 `orchestrate-final-review` Phase C finishing（成功路径）删除 budget file、`active-run-id` 和 `scope-<run_id>.md`。用户显式 abort 时 coordinator 清理。>1h 无更新的 stale file 由下次 entry gate 清理。
- **Concurrency**: 单活跃运行 + stale 检测。不支持并行 Formal Orchestrate。

**Budget file schema**:
```json
{
  "run_id": "formal-20260518-143022",
  "budget_total": 24,
  "budget_used": 0,
  "pack_count": 4,
  "dispatches": []
}
```

**Stale detection**: Entry gate 检查 `active-run-id` 指向的 budget file 是否在过去 1 小时内更新过。Stale → 覆写。Fresh → 警告用户并确认后覆写。

## Per-phase 规则

- `codex-reviewer`（via `codex:codex-rescue --model gpt-5.4`）是 baseline reviewer；每个 phase 指定的 baseline angles 可并行不可合并。
- `codex:codex-rescue --model gpt-5.5`（via `codex:codex-rescue --model gpt-5.5`）只审 release-risk，不审普通代码质量、设计完整性或 plan coverage。
- `production-risk` risk flag 先进入 plan 的"发布风险和人工门禁"；真正 dispatch trigger 是 early release gate 或 final release gate。
- Repair 后默认 targeted re-review；只有 source design / plan / scope / shared contract / migration / permission / billing / runtime baseline 改变时才 full phase review rerun。
- 追加 reviewer 只允许：evidence conflict / 连续 repair 后同类风险仍复现 / release gate / 用户要求。
- 多个相邻 high-risk packs 属于同一发布风险面时合并一次 release-risk review。
- release blocker 修复后只做 targeted release re-review；不重跑 baseline review，除非修复改变 source design / plan / shared contract / migration / permission / billing / runtime baseline。
- 每次 spawn reviewer 前先数清本 phase 已经派过的 baseline reviews、targeted re-reviews 和 release gates；如果下一次 spawn 不属于这三类，先做方向检查（见 `coordinator-tools.md` Direction Check），不用 review 填补不确定感。

## Release Gate

**Early release gate**（Phase A 中触发）：

- 迁移 / deploy order / rollback / manual production gate 必须在实现前决定。
- baseline finding 暴露的问题必须先判定 release strategy 才能修。
- 等待 Phase B 才审会造成不可逆数据、权限、账务或 runtime 风险。
- 用户明确要求。

**Final release gate**（Phase B 后触发）：Final Intent Review 没有 implementation / design / context / plan blocker 后，如果最终 diff 触碰 migration、billing、permission、runtime、cross-service contract、deploy order、rollback 或 manual production dependency，才派 `codex:codex-rescue --model gpt-5.5`。
