# Direction Check

> **流程位置**：budget 消耗达阈值时触发 · 双模式（attended/afk）决定何时停顿

## 触发条件

双模式（P4 D3）：**attendance_mode** 决定 80% 时的行为。

| 进度 | attended（在场） | afk（无人值守，默认） |
| --- | --- | --- |
| < 80% | 仪表：每次计数后 additionalContext 报「E/T」 | 同左 |
| ≥ 80%（过半段） | 写 `pending_direction_check`，`validate-plan-dispatch.sh` 拦非 reviewer 派发 → 用户做业务决策 | **软提醒并继续**：只写 additionalContext「⚠ 已用 E/T（≥80%），继续中。到顶将停。」**不写 DC，不阻断** |
| ≥ 100%（到顶） | 同 AFK：escape hatch 硬停 | **escape hatch 硬停**：写 `pending_direction_check`（threshold_type=`review`, threshold_percent=100）→ 拦派发一次 |

- **有效用量（effective_used）= review_used − review_credit**（credit 记录合理回流归还的额度，不破坏 review_used 历史真相）
- `track-review-budget.sh` 读 `attendance_mode`，按上表分叉 80%/100% 行为
- `validate-plan-dispatch.sh:66-72` 不变，仍是 DC 的 `exit 2` 执行点

### 触发命令
```bash
state.sh direction-check trigger --run-id <run_id> --type <review> --threshold-percent <80|100>
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

## 流程

### Step 1: Trigger
Hook 检测到阈值 → 调用 `state.sh direction-check trigger`。

### Step 2: Block
`validate-plan-dispatch.sh` 检查 `pending_direction_check.ack_status`：
- `"pending"` → 阻止新 Worker dispatch（codex-reviewer 除外）
- `"acknowledged"` 或 null → 放行

### Step 3: User Confirm
Coordinator 向用户展示当前消耗情况，**一次只问一个决策问题**。使用以下信息化展示格式：

> **进度**：完成 {completed_packs}/{total_packs} 个 Task Pack，当前在 Plan {current_plan} 的修复循环。
> **Review 预算**：已用（有效）{effective_used}/{review_total} 次 Codex review（累计 {review_used}，credit 归还 {review_credit}）。
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

## Escape Hatch（100% 到顶）

到顶的 `exit 2` 不是"永久卡死"，而是"停一次让 Coordinator 决策"。Coordinator 用以下命令放行后清 DC，自主跑可续：

```bash
state.sh budget check --allow-over-budget --override-reason "<reason>"
state.sh direction-check ack --run-id <run_id> --action continue
```

**Override cap**：`override_count` 超过 2 次后，`budget check --allow-over-budget` 被拒（exit 2），必须报告用户。

## 约束

- 同一阈值只触发一次（hook 检查 `pending_direction_check` 是否已存在）
- codex-reviewer dispatch 不受 Direction Check 阻塞（review 本身是消耗 budget 的行为，不能阻止）
- AFK 模式下 80% 不写 DC，只软提醒——Coordinator 在自主循环的下一跳看到软信号后可自行调整策略
- AFK 模式 Coordinator 可在 escape hatch 按预设策略自动决策，但受 100% 触发保证——不会无限烧

---
> **下一步**：用户确认继续 → 回到触发 Direction Check 的步骤继续执行。用户选择停止 → BLOCKED。
