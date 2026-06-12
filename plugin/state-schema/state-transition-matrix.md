# State Transition Matrix（人读说明）

> **机器以 `routes-v1.json` 为准。** 本文件是给人读的转换语义说明，不再是 `state.sh` 的数据源。
> `state.sh transition` 的合法跳转由 `routes-v1.json` 决定：候选集 =
> `global_transitions`（route 无关的 work-item 状态机）∪ `routes[route].phase_transitions`
> （route 相关的 phase 推进）。匹配不到即 `exit 2`。`*` 表示通配符（匹配任意值）。

## work-item 状态机（route 无关 → `global_transitions`）

| Actor | From | To | 触发描述 |
| --- | --- | --- | --- |
| Coordinator | pending | dispatched | Worker 首次派发 |
| Coordinator | pending | in_progress | plan-level Worker 首次派发（Worker 自治模式）|
| Coordinator | dispatched | returned | Worker 返回（Coordinator 手动路由） |
| Coordinator | returned | review_pending | plan-level Worker 返回后进入 Plan Implementation Review（Worker 自治模式）|
| Coordinator | returned | committed | Git Checkpoint 完成 |
| agent-return-handler | in_progress | returned | plan-level Worker 自治 PostToolUse hook 自动标记 |
| Coordinator | review_pending | pass | Review 通过 |
| Coordinator | review_pending | needs_repair | Review 需要修复 |
| Coordinator | * | blocked | 任意状态 → 阻塞 |
| Coordinator | returned | repairing | 进入修复流程（需 disposition_refs） |
| Coordinator | repairing | returned | 修复完成返回 |
| Coordinator | workflow | dispatched | Workflow 初始派发 |
| Coordinator | * | closed | 工作流关闭 |
| agent-return-handler | dispatched | returned | PostToolUse hook 自动标记 Worker 返回 |
| track-execution-state | returned | committed | PostToolUse hook 自动标记 commit 完成 |

## phase 推进（route 相关 → `routes[route].phase_transitions`）

下表是 `formal` route 的完整 phase 推进序列。轻档（`light`）等子形态的合法 phase 推进
**不同**——例如 `light` 没有 `workflow:discovery`，机器据此拒绝轻档误入 Discovery。
各 route 的实际 phase 推进以 `routes-v1.json` 的对应记录为准。

| Actor | From | To | 触发描述（formal）|
| --- | --- | --- | --- |
| Coordinator | workflow | discovery | 进入 Discovery phase |
| Coordinator | workflow | plan-writing | 进入 Plan Writing phase |
| Coordinator | workflow | execution | 进入 Execution phase |
| Coordinator | workflow | final-review | 进入 Final Review phase |
| Coordinator | discovery | plan-writing | Discovery → Plan Writing 阶段推进 |
| Coordinator | plan-writing | execution | Plan Writing → Execution 阶段推进 |
| Coordinator | execution | final-review | Execution → Final Review 阶段推进 |
| Coordinator | final-review | closed | Final Review → 关闭 |

## 设计约束

- `actor` 是硬性身份标识，不可伪造——由调用方（hook/Coordinator）传入
- `repairing` 转换必须附带 `--disposition-refs`，且所有引用的 finding 必须在 `review_dispositions` 中状态为 `accepted` 且有 `evidence`
- `--from` 必须匹配当前 `cursor.phase`，除非传入 `--force`
- `returned → committed`（track-execution-state 自动）保持 per-pack 含义；plan-level 不直接复用此 transition
- 读 `routes-v1.json` 失败或 route 缺失时，`state.sh transition_allowed` 回退到内置全量矩阵（fail-open，绝不更严）
