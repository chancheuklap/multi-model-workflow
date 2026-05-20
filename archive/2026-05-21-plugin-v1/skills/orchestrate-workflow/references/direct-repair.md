# Direct Repair

Entry Gate 选择 Direct Repair 时加载。条件：已有批准 design / plan / mockup / acceptance / failing test，目标行为清楚。

## Brief

用 Pack Brief 字段（见 `dispatch-primitives.md`），做以下适配：

- `Pack` 写 `Targeted repair`。
- `Issue` 写 accepted reviewer finding、failing test、批准 design / plan / mockup / acceptance 的 locator，或用户明确 repair brief。
- `Implementation tasks` 只写修复 accepted finding 或 failing behavior 所需步骤；不临场扩展 issue hierarchy。
- 缺目标行为、合同边界、UI target 或验收口径时，返回 Discovery / user decision，不让 worker 自行决定。

## Review 分级

Worker 返回后，按改动风险决定 review 方式：

| 条件 | review 方式 |
| --- | --- |
| 不触碰合同边界、不改 shared contract / migration / permission / billing / runtime、不改 public API、变更 ≤ 3 个文件且全部是 UI / copy / config / style / test fix | coordinator 自检：读 diff、跑 verification、确认 acceptance → 不派 reviewer |
| 上述条件任一不满足 | targeted Pack Review（派 `codex-reviewer` via `codex:codex-rescue --model gpt-5.4`） |
| 触碰 migration / billing / permission / runtime / release boundary | targeted Pack Review + 检查是否触发 early release gate |

Coordinator 自检必须实际读 diff 和跑验证命令，不能只看 worker self-report。自检不通过时仍派 reviewer。

## Reception

- pass → 完成。
- needs repair → 按 `dispatch-primitives.md` 修复归属判断。
- release gate 触发 → 读 `review-budget.md` Release Gate 条件。
