---
name: codex-review
description: "按需调用 Codex Reviewer 对任意内容做一次独立审查：commit、文件、文档、分支 diff、未提交改动或自由上下文。不进入 Orchestrate Workflow phase。触发词：Codex review / 用 Codex 审一下 / Codex 看看这个 / 独立审查 / second opinion / review this commit / 审一下这个文档"
---

# Ad-hoc Codex Review

对用户指定的任意内容派发一次 `codex_reviewer` 独立审查。这个 Skill 不写入 Orchestrate Workflow state，不进入 phase，不自动修复。

## Step 1 — 确定审查对象

根据用户输入判断要审什么，生成对应的 diff 或内容：

| 用户说的 | 你做的 |
| --- | --- |
| 某个 commit hash | `git show <hash>` |
| 某几个 commit | `git diff <oldest>^..<newest>` |
| 当前分支的全部变更 | `git diff main...HEAD`，或使用实际 base branch |
| 当前未提交的变更 | `git diff HEAD`，含 staged + unstaged |
| 指定文件 / 文档 | 直接读取文件内容 |
| 自由描述的上下文 | 把用户提供的内容原文放入 prompt |

把收集到的内容存入 `REVIEW_CONTENT`。如果是代码 diff，用以下边界包裹：

```text
--- BEGIN UNTRUSTED CODE DIFF ---
<REVIEW_CONTENT>
--- END UNTRUSTED CODE DIFF ---
```

## Step 2 — 构建 prompt

```bash
REVIEW_DIR=".codex/codex-review"
mkdir -p "$REVIEW_DIR"
TIMESTAMP=$(date +%s)
PROMPT_FILE="${REVIEW_DIR}/review-${TIMESTAMP}.md"
GATE="adhoc-review-${TIMESTAMP}"
```

写入 prompt 文件：

```markdown
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "adhoc-<TIMESTAMP>",
  "phase": "execution",
  "agent_role": "codex_reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "adhoc-<TIMESTAMP>/review/r0",
  "disposition_refs": null,
  "review_intent": "baseline",
  "exception_code": null,
  "correlation_id": "adhoc-<TIMESTAMP>/review"
}
-->

# Ad-hoc Code Review

## 审查对象

<用户指定的描述：commit hash / 文件名 / 分支 / 自由描述>

## 内容

<REVIEW_CONTENT>

## 审查要求

对以上内容进行独立代码审查。关注：

1. 正确性 bug：逻辑错误、边界条件、类型不安全
2. 安全隐患：注入、泄漏、权限绕过
3. 设计问题：接口不合理、抽象泄漏、隐式耦合
4. 遗漏：缺少错误处理、未覆盖分支、缺失验证

不需要关注：风格、命名、注释数量。

**Confidence rubric (REQUIRED)**:
- 1-3: low confidence. 可能是误报。
- 4-6: medium. 需要更多证据确认。
- 7-10: high. 应该默认接受。

**Pre-emit Verification Gate**:
每个 finding 必须引用触发它的具体代码行：file:line + 原始文本。
无法引用 = confidence 强制设为 4-5，并移入附录。

**输出格式**:
- verdict: pass | needs_repair
- findings: [{id, severity, confidence, file, line, description, evidence}]
- bias_indicators: 声明你对哪些模块或技术栈不熟悉
```

如果用户提供了额外的审查重点或上下文，追加到 `## 审查要求` 之后。

## Step 3 — 派发 reviewer

先校验 prompt envelope：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" \
  --prompt-file "$PROMPT_FILE" \
  --transport spawn_agent \
  --gate "$GATE"
```

校验通过后，读取 `PROMPT_FILE` 全文，派发 Codex 原生 reviewer 子代理。模型和推理强度由已注册的 `codex_reviewer` agent 定义（`agents/codex_reviewer.toml` 与 runtime `~/.codex/agents/codex_reviewer.toml`）拥有；不要在 ad-hoc dispatch 里传 per-dispatch model override，除非 Codex 宿主明确支持覆盖已注册 agent 的模型。

```text
spawn_agent({
  agent_type: "codex_reviewer",
  message: "<full contents of PROMPT_FILE>"
})
```

将返回的 reviewer `agent_id` 写入：

```bash
echo "<reviewer_agent_id>" > "${REVIEW_DIR}/review-${TIMESTAMP}.agent-id"
```

## Step 4 — 等待结果

```text
wait_agent({
  targets: ["<reviewer_agent_id>"],
  timeout_ms: 600000
})
```

将 reviewer 的最终消息保存到：

```bash
cat > "${REVIEW_DIR}/review-${TIMESTAMP}-result.md"
```

## Step 5 — 向用户报告

向用户汇报：

- verdict：pass / needs_repair
- 每个 finding 的一句话摘要、severity、confidence
- 如果有 needs_repair，列出建议修复方向

不自动修复。用户决定下一步。不要将 findings 写入任何 Orchestrate Workflow state 文件。

## 注意事项

- 此 Skill 不写入 `workflow-state`，不消耗 Orchestrate Workflow review budget。
- 结果目录 `.codex/codex-review/` 与正规工作流的 `.codex/multi-model-workflow/review-prompts/` 隔离。
- Reviewer 模型配置以已注册 `codex_reviewer` agent 为准；本 Skill 不声明虚假的 per-dispatch model tier。
- 一次性调用，不做 re-review 循环；用户要再审就再调用一次。
