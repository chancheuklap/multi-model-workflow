# Repair Grading

Worker 返回后，按改动风险决定 review 方式：

| 条件 | review 方式 |
| --- | --- |
| 不触碰合同边界、不改 shared contract / migration / permission / billing / runtime、不改 public API、变更 ≤ 3 个文件且全部是 UI / copy / config / style / test fix | coordinator 自检：读 diff、跑 verification、确认 acceptance → 不派 reviewer |
| 上述条件任一不满足 | targeted Pack Review（派 `codex-reviewer` via `codex:codex-rescue --model gpt-5.4`） |
| 触碰 migration / billing / permission / runtime / release boundary | targeted Pack Review + 检查是否触发 early release gate |

## Coordinator 自检

Coordinator 自检必须实际读 diff 和跑验证命令，不能只看 worker self-report。自检不通过时仍派 reviewer。

步骤：
1. `git diff` 读变更。
2. 跑 verification commands。
3. 对照 acceptance criteria 确认。
4. 通过 → 完成。不通过 → 派 codex-reviewer。
