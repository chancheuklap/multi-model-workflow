# Codex Review Dispatch Protocol

> **Lookup**：任意 phase 准备派发 baseline review 或 release review 前读取。

所有 review 通过 Codex `codex-companion.mjs` 四步协议派发。不使用 Claude CLI、不使用 `claude -p`。

## 四步协议

```bash
# Step 0 — 定位脚本（每个 session 只做一次）
CODEX_SCRIPT="$(find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" -type f 2>/dev/null | head -1)"
```

### Step 1 — Submit + 持久化 job-id

Coordinator 写好 review prompt 到 `.codex/multi-model-workflow/review-prompts/<gate>.md` 后：

```bash
node "$CODEX_SCRIPT" task --background \
  --prompt-file .codex/multi-model-workflow/review-prompts/<gate>.md \
  --json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['jobId'])" \
  > .codex/multi-model-workflow/review-prompts/<gate>.job-id
```

**关键**：`--json` + `python3` 提取确保 job-id 完整持久化到文件，不经过终端渲染截断。

### Step 2 — Wait（后台等待）

```bash
node "$CODEX_SCRIPT" status \
  "$(cat .codex/multi-model-workflow/review-prompts/<gate>.job-id)" \
  --wait --timeout-ms 600000
```

用 `run_in_background: true` 执行。Coordinator 可以继续其他工作。

### Step 3 — Verify + Result

后台 wait 完成后（收到 exit 通知），**必须**先验证 job 状态再取结果：

```bash
JOB_STATUS=$(node "$CODEX_SCRIPT" status \
  "$(cat .codex/multi-model-workflow/review-prompts/<gate>.job-id)" \
  --json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job',d).get('status','unknown'))")
```

- `completed` / `failed` / `cancelled` → 继续取结果
- `queued` / `running` → wait 超时了，重新执行 Step 2
- 取不到 → 报错，检查 job-id 文件内容

取结果：

```bash
node "$CODEX_SCRIPT" result \
  "$(cat .codex/multi-model-workflow/review-prompts/<gate>.job-id)" \
  > .codex/multi-model-workflow/review-results/<gate>.md
```

### Step 4 — Budget 记账

取到结果后 Coordinator 立即运行：

```bash
MULTI_MODEL_WORKFLOW_REVIEW_LANE=codex \
MULTI_MODEL_WORKFLOW_REVIEW_NAME=<gate> \
  bash codex/hooks/track-review-budget.sh
```

## Compaction 恢复

有 `.job-id` 文件但无对应 `review-results/` → 从 Step 2 继续。

## Reporting

每个 review gate 汇报：

- Job ID
- Reviewer result path
- Budget status（track-review-budget.sh 输出）
