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
- `"pending"` → 阻止新 Worker dispatch（codex-reviewer 除外）
- `"acknowledged"` 或 null → 放行

### Step 3: User Confirm
Coordinator 向用户展示当前消耗情况，**一次只问一个决策问题**：

> Budget 消耗已达 80%（{used}/{total}）。
> - 已完成 Plan: {completed_plans}/{total_plans}
> - 当前 repair round: {current_round}
> 
> 选择：
> 1. **继续** — 消耗完剩余 budget
> 2. **停止** — 标记当前 scope 为 BLOCKED，报告已完成部分
> 3. **调整** — 修改 scope 或策略后继续

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
- codex-reviewer dispatch 不受 Direction Check 阻塞（review 本身是消耗 budget 的行为，不能阻止）
- Direction Check 是纯用户交互，不自动决策
