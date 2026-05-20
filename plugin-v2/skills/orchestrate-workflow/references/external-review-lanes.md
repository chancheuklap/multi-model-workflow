# External Review Lanes（Plugin V2）

> **Lookup**：任意 phase 准备派发 review 前读取。

## Review Lane

跨模型 review 通过 Codex（GPT）提供独立意见。**不使用 `codex:codex-rescue`**——它只能调 `task`、不能调 `review`，且会自动选 background 导致结果丢失。

### 调用方式

所有 review 统一用以下模式：

**Step 1：写 review prompt 到文件**

```
Write({
  file_path: ".claude/multi-model-workflow/review-prompts/<gate>.md",
  content: "<完整 review prompt，从对应的 review dispatch 模板构造>"
})
```

**Step 2：提交 Codex 后台任务**

```
Bash({
  command: 'JOB_ID=$(node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task --background "$(cat .claude/multi-model-workflow/review-prompts/<gate>.md)" 2>/dev/null | grep -oE "codex-[a-zA-Z0-9]+" | head -1) && echo "JOB_ID=$JOB_ID"',
  description: "Submit Codex review task"
})
```

记录返回的 JOB_ID。

**Step 3：轮询等待完成**

```
Bash({
  command: 'node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" status <JOB_ID> --wait --timeout-ms 600000',
  run_in_background: true,
  description: "Wait for Codex review completion"
})
```

`run_in_background: true` 避免 Bash 超时限制。完成后 Claude Code 自动通知 Coordinator。

**Step 4：获取结果**

```
Bash({
  command: 'node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" result <JOB_ID>',
  description: "Fetch Codex review result"
})
```

将结果保存到 `.claude/multi-model-workflow/review-results/<gate>.md` 备查。

### 关键规则

- **不用 `codex:codex-rescue` 做 review**——它被明确禁止调用 `review`/`status`/`result`
- **不在 prompt 中写 `--wait` 或 `--model`**——这些不是 Codex task 的有效 flag
- Review prompt 必须自足——包含 review scope、source artifacts、review angles、calibration、return contract
- Coordinator 拿到结果后按当前 phase 的 disposition rules 亲验每条 finding
- 每次 review dispatch 消耗 budget_used + 1

### Budget 记录

每次 review 完成后，Coordinator 更新 budget file 的 `budget_used` 和 `dispatches` 数组。
