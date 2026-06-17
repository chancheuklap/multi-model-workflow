> **使用场景**：派发 Codex review 时按本文件格式构造 prompt + 调用 `dispatch-review.sh validate/record` · **完成后回到** 调用方 phase skill 的对应 step

# Codex Review Dispatch

Codex 版 review 是原生 subagent 工作流，不调用外部 companion 或 job runner。

职责拆分：

- Coordinator 写 review prompt，并以 `DISPATCH_ENVELOPE` 开头。
- `dispatch-review.sh validate` 校验 envelope、gate、budget、repair round 和 plan implementation 前置条件。
- Coordinator 调用 `spawn_agent(agent_type="codex_reviewer")`。
- `dispatch-review.sh record` 保存 reviewer agent id、registry entry 和 prompt 内容摘要；record 成功后该 prompt 冻结。
- Coordinator 用 `wait_agent` 等 final message，把结果写入 `review-results/<gate>.md`。
- `complete-review-dispatch.sh` 核对 prompt 未被改写后标记 durable result，并 exactly-once 递增 review budget。
- durable complete 成功后再 `close_agent` 释放容量；closed reviewer 仍可用 registry 里的 agent id `resume_agent`，但 workflow 默认从 durable result 继续 disposition，不重新派同一 review。
- Coordinator 完成 finding disposition 后用 `record-review-disposition.sh` 标记 started / completed。

## 流程

### Baseline review

1. 写 prompt 到 `.codex/multi-model-workflow/review-prompts/<gate>.md`，首段必须是 `DISPATCH_ENVELOPE`，并设置 `agent_role: "codex_reviewer"`。

2. Code diff 必须用不可信边界包裹：

   ```text
   --- BEGIN UNTRUSTED CODE DIFF ---
   <diff>
   --- END UNTRUSTED CODE DIFF ---
   ```

3. 按 phase 选择 reviewer 模型：

   - `discovery, plan-writing`：`spawn_agent` 可显式指定 `model: "gpt-5.5"`、`reasoning_effort: "xhigh"`。
   - `execution, final-review, bug-investigation, direct-repair, multi-pr-merge`：默认 `codex_reviewer` 配置（`gpt-5.4` / `xhigh`）即可，除非风险要求升级。

4. validate：

   ```bash
   bash "${MMW_PLUGIN_ROOT}/scripts/dispatch-review.sh" validate \
     --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" \
     --gate "<gate>"
	   ```

   对 `plan-impl-review-N`，validate 会确认该 Plan 的 worker 已经经过 `SubagentStop` return-handler durable handling（execution-state 里有 `return_handler_completed_at`，或该 Plan 没有 worker owner）。不要在 worker 仍在 session 中时用 worktree commit / plan-return 文件抢先派审。

   如果 Review Budget 已耗尽，且用户明确授权继续 review，validate 和 complete 两步都必须传：

   ```bash
   --allow-over-budget --override-reason "<brief user authorization>"
   ```

5. 派发 reviewer：

   ```text
   spawn_agent({
     agent_type: "codex_reviewer",
     message: "Read this review prompt file and return the requested review: <absolute prompt path>"
   })
   ```

   保存返回的 agent id。

6. record：

   ```bash
   bash "${MMW_PLUGIN_ROOT}/scripts/dispatch-review.sh" record \
     --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" \
     --gate "<gate>" \
     --agent-id "<AGENT_ID>"
   ```

   从这一步开始，`review-prompts/<gate>.md` 是 reviewer 正在审的冻结合同。目标 commit、scope 或 gate 变化时，写新的 prompt 并重新派发 reviewer；不要修改已 record 的 prompt 后继续用旧 agent result 收口。

7. 等结果：

   ```text
   wait_agent({targets:["<AGENT_ID>"], timeout_ms:600000})
   ```

   把 final message 原文保存到 `.codex/multi-model-workflow/review-results/<gate>.md`。

8. durable complete：

   ```bash
   bash "${MMW_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" \
     --run-id "<run_id>" \
     --gate "<gate>" \
     --agent-id "<AGENT_ID>" \
     --result-file ".codex/multi-model-workflow/review-results/<gate>.md"
   ```

9. 释放 reviewer 容量：

   ```text
   close_agent({target:"<AGENT_ID>"})
   ```

10. disposition recovery anchor：

   ```bash
   bash "${MMW_PLUGIN_ROOT}/scripts/record-review-disposition.sh" --run-id "<run_id>" --gate "<gate>" --status started
   # Coordinator 处理 findings 并写 disposition
   bash "${MMW_PLUGIN_ROOT}/scripts/record-review-disposition.sh" --run-id "<run_id>" --gate "<gate>" --status completed
   ```

## Compaction Recovery

- 有 `review-registry/<gate>.json` 且 status 为 `dispatched`：读取其中的 `agent_id`，先 `wait_agent`；如果 agent 已关闭但无 result file，先 `resume_agent` 再 `wait_agent`。仍不可取时报告 BLOCKED，不重新派同一 review。
- status 为 `completed` 或 `disposition_started` 且 result file 存在：直接读该 result file 继续 disposition。
- disposition 未 completed 前，不进入 repair。

> **幻觉抑制四件套**（Confidence rubric / Pre-emit Verification Gate / 证据表 / Bias indicators）由 `dispatch-review.sh validate` 自动追加到 prompt 文件，单源是 `_shared/review-prompt-quartet.md`。
