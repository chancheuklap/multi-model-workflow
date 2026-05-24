# Direction Check

> **流程位置**：budget 消耗达 80% 时触发 · 需要用户确认才能继续

## 触发条件

当 review budget 或 effort budget 消耗达 80% 时自动触发：
- `track-review-budget.sh`：review_used >= review_total * 80%
- `track-effort-budget.sh`：effort_used >= effort_total * 80%
- `state.sh direction-check trigger` 写入 `pending_direction_check`

## 流程

### Step 1: Trigger
Hook 检测到 80% 阈值 → 调用：
```bash
state.sh direction-check trigger --run-id <run_id> --type <review|effort> --threshold-percent 80
```

workflow-state 写入：
```json
{
  "pending_direction_check": {
    "triggered_at": "<ISO 8601>",
    "threshold_type": "review",
    "threshold_percent": 80,
    "ack_status": "pending"
  }
}
```

### Step 2: Block
`validate-pack-dispatch.sh` 检查 `pending_direction_check.ack_status`：
- `"pending"` → 阻止新 Worker dispatch（reviewer 除外）
- `"acknowledged"` 或 null → 放行

### Step 3: User Confirm
Coordinator 向用户展示当前消耗情况，**一次只问一个决策问题**。使用以下信息化展示格式：

> **进度**：完成 {completed_packs}/{total_packs} 个 Task Pack，当前在 Plan {current_plan} 的修复循环。
> **Review 预算**：已用 {review_used}/{review_total} 次 Codex review。
> **Finding 趋势**：Plan 1 有 {p1_findings} 个 findings（{p1_accepted} accepted），Plan 2 目前 {p2_findings} 个 findings（{p2_accepted} accepted）——密度在{下降/上升}。
> **预计剩余**：{remaining_packs} 个 Pack + Final Review，预计还需 {estimated_reviews} 次 review。
>
> 选择：
> 1. **继续** — 消耗完剩余 budget
> 2. **停止** — 标记当前 scope 为 BLOCKED，报告已完成部分
> 3. **调整** — 修改 scope 或策略后继续

Coordinator 从 workflow-state 和 execution-state 中读取实际数据填充上述模板。Finding 趋势通过对比各 Plan 的 findings 密度（findings / pack 数）判断上升或下降。预计剩余 review 次数 = 剩余 Pack 数 * 当前平均 review 轮次 + 1（Final Review）。

### Step 4: Acknowledge
用户确认后：

```bash
# continue
state.sh direction-check ack --run-id <run_id> --action continue

# stop
state.sh direction-check ack --run-id <run_id> --action stop

# adjust (clears the check, allows re-trigger later)
state.sh direction-check ack --run-id <run_id> --action adjust
```

| 用户选择 | 动作 |
| --- | --- |
| continue | `ack_status = "acknowledged"`, 继续执行，direction_check_count += 1 |
| stop | `ack_status = "stopped"`, 返回 BLOCKED |
| adjust | `pending_direction_check = null`, Coordinator 调整 scope 后继续 |

## 约束

- 同一阈值只触发一次（hook 检查 `pending_direction_check` 是否已存在）
- reviewer dispatch 不受 Direction Check 阻塞（review 本身是消耗 budget 的行为，不能阻止）
- Direction Check 是纯用户交互，不自动决策

---
> **下一步**：用户确认继续 → 回到触发 Direction Check 的步骤继续执行。用户选择停止 → BLOCKED。
