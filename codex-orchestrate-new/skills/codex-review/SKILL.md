---
name: codex-review
description: "按需调用 Codex Reviewer 对任意内容做一次独立审查——commit、文件、文档、分支 diff、任意上下文。不走 Orchestrate Workflow，无 phase 仪式。触发词：Codex review / 用 Codex 审一下 / Codex 看看这个 / 独立审查 / second opinion / review this commit / 审一下这个文档"
---

# Ad-hoc Codex Review

对用户指定的任意内容派发一次 Codex 独立审查，不经过 Orchestrate Workflow。

## Step 1 — 确定审查对象

根据用户输入判断要审什么，生成对应的 diff 或内容：

| 用户说的 | 你做的 |
|---------|--------|
| 某个 commit（hash） | `git show <hash>` |
| 某几个 commit | `git diff <oldest>^..<newest>` |
| 当前分支的全部变更 | `git diff main...HEAD`（或实际 base branch） |
| 当前未提交的变更 | `git diff HEAD`（含 staged + unstaged） |
| 指定文件 / 文档 | 直接读取文件内容 |
| 自由描述的上下文 | 把用户提供的内容原文放入 prompt |

把收集到的内容存入变量 `REVIEW_CONTENT`。如果是 code diff，用 `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---` 包裹。

## Step 2 — 构建 prompt 文件

```bash
REVIEW_DIR=".codex/multi-model-workflow/codex-review"
mkdir -p "$REVIEW_DIR"
TIMESTAMP=$(date +%s)
PROMPT_FILE="${REVIEW_DIR}/review-${TIMESTAMP}.md"
```

先用同一套生成器构造 ad-hoc envelope：

```bash
STATE_SH="${MMW_PLUGIN_ROOT:-}/scripts/state.sh"
[ -f "$STATE_SH" ] || STATE_SH="$(find ~/.codex/plugins -path '*/scripts/state.sh' -type f 2>/dev/null | head -1)"
ENVELOPE="$(bash "$STATE_SH" envelope build \
  --run-id "adhoc-${TIMESTAMP}" \
  --phase execution \
  --agent-role codex_reviewer \
  --review-intent ad-hoc)"
```

写入 prompt 文件，格式：

```markdown
<ENVELOPE>

# Ad-hoc Code Review

## 审查对象

<用户指定的描述——commit hash / 文件名 / 分支 / 自由描述>

## 内容

<REVIEW_CONTENT>

## 审查要求

对以上内容进行独立代码审查。关注：
1. 正确性 bug（逻辑错误、边界条件、类型不安全）
2. 安全隐患（注入、泄漏、权限绕过）
3. 设计问题（接口不合理、抽象泄漏、隐式耦合）
4. 遗漏（缺少的错误处理、未覆盖的分支、缺失的测试）

不需要关注：风格、命名、注释数量。

（防幻觉四件套——Confidence rubric / Pre-emit Gate / 证据表 / Bias indicators——在 Step 2 末尾由脚本统一追加，见下。）

**输出格式**：
- verdict: pass | needs_repair
- findings: [{id, severity, confidence, file, line, description, evidence}]
- bias_indicators: 声明你对哪些模块/技术栈不熟悉

```

如果用户提供了额外的审查重点或上下文，追加到 `## 审查要求` 之后。

**追加防幻觉四件套**（单源，与主流程 `dispatch-review.sh` 注入的同一份 `review-prompt-quartet.md`）：派发前把它追加到 prompt 文件末尾：

```bash
QUARTET="${MMW_PLUGIN_ROOT:-}/skills/_shared/review-prompt-quartet.md"
[ -f "$QUARTET" ] || QUARTET="$(find ~/.codex/plugins -path '*/skills/_shared/review-prompt-quartet.md' -type f 2>/dev/null | head -1)"
[ -f "$QUARTET" ] && cat "$QUARTET" >> "$PROMPT_FILE"
```

## Step 3 — 派发 Codex reviewer

使用 Codex multi-agent 工具派发：

```text
spawn_agent({
  agent_type: "codex_reviewer",
  message: "Read the review prompt file and return the requested review: <PROMPT_FILE>"
})
```

把返回的 agent id 保存到：

```bash
echo "<AGENT_ID>" > "${REVIEW_DIR}/review-${TIMESTAMP}.agent-id"
```

## Step 4 — 等待结果并关闭 agent

使用 `wait_agent({targets:["<AGENT_ID>"], timeout_ms:600000})` 等待 reviewer final message。拿到 final message 后保存到：

```bash
RESULT_FILE="${REVIEW_DIR}/review-${TIMESTAMP}-result.md"
```

保存完成后立即 `close_agent({target:"<AGENT_ID>"})` 释放并发容量。

## Step 5 — 收集并报告

向用户汇报：
- verdict（pass / needs_repair）
- 每个 finding 的一句话摘要 + confidence
- 如果有 needs_repair，列出建议的修复方向

不自动修复——用户决定下一步。不要将 findings 写入任何 orchestrate workflow 的 state 文件。

## 注意事项

- 此 skill 不写入 `workflow-state`，不消耗 Orchestrate Workflow 的 review budget
- 结果目录 `.codex/multi-model-workflow/codex-review/` 与正规工作流的 `review-prompts/` 隔离
- 默认使用 `codex_reviewer` agent 配置；用户要求时可在 `spawn_agent` 中显式指定模型
- 一次性调用，不做 re-review 循环——用户要再审就再调用一次
