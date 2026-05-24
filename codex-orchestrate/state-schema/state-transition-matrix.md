# State Transition Matrix

所有 `state.sh transition` 调用必须匹配以下矩阵中的一行，否则 exit 2。
`*` 表示通配符（匹配任意值）。

| Actor | From | To | 触发描述 |
| --- | --- | --- | --- |
| Coordinator | pending | dispatched | Worker 首次派发 |
| Coordinator | dispatched | returned | Worker 返回（Coordinator 手动路由） |
| Coordinator | returned | committed | Git Checkpoint 完成 |
| Coordinator | review_pending | pass | Review 通过 |
| Coordinator | review_pending | needs_repair | Review 需要修复 |
| Coordinator | * | blocked | 任意状态 → 阻塞 |
| Coordinator | returned | repairing | 进入修复流程（需 disposition_refs） |
| Coordinator | repairing | returned | 修复完成返回 |
| Coordinator | workflow | dispatched | Workflow 初始派发 |
| Coordinator | workflow | discovery | 进入 Discovery phase |
| Coordinator | workflow | plan-writing | 进入 Plan Writing phase |
| Coordinator | workflow | execution | 进入 Execution phase |
| Coordinator | workflow | final-review | 进入 Final Review phase |
| Coordinator | discovery | plan-writing | Discovery → Plan Writing 阶段推进 |
| Coordinator | plan-writing | execution | Plan Writing → Execution 阶段推进 |
| Coordinator | execution | final-review | Execution → Final Review 阶段推进 |
| Coordinator | final-review | closed | Final Review → 关闭 |
| Coordinator | * | execution_done | Execution 完成 |
| Coordinator | * | closed | 工作流关闭 |
| agent-return-handler | dispatched | returned | PostToolUse hook 自动标记 Worker 返回 |
| track-execution-state | returned | committed | PostToolUse hook 自动标记 commit 完成 |

## 设计约束

- `actor` 是硬性身份标识，不可伪造——由调用方（hook/Coordinator）传入
- `repairing` 转换必须附带 `--disposition-refs`，且所有引用的 finding 必须在 `review_dispositions` 中状态为 `accepted` 且有 `evidence`
- `--from` 必须匹配当前 `cursor.phase`，除非传入 `--force`
