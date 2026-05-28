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
REVIEW_DIR=".claude/codex-review"
mkdir -p "$REVIEW_DIR"
TIMESTAMP=$(date +%s)
PROMPT_FILE="${REVIEW_DIR}/review-${TIMESTAMP}.md"
```

写入 prompt 文件，格式：

```markdown
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "adhoc-<TIMESTAMP>",
  "phase": "execution",
  "agent_role": "codex-reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "adhoc-<TIMESTAMP>/review/r0",
  "disposition_refs": null,
  "review_intent": "ad-hoc",
  "exception_code": null,
  "correlation_id": "adhoc-<TIMESTAMP>/review"
}
-->

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

**Confidence rubric (REQUIRED)**:
- 1-3: low confidence. 可能是误报。
- 4-6: medium. 需要更多证据确认。
- 7-10: high. 应该默认接受。

**Pre-emit Verification Gate**：
每个 finding 必须引用触发它的具体代码行（file:line + 原始文本）。
无法引用 = confidence 强制设为 4-5，移入附录。

**证据表 (REQUIRED)**：
Reviewer 必须在 `### Evidence` 下填写半结构化证据表：

| 字段 | 必填内容 |
| --- | --- |
| 已读设计 / mockup / plan 来源 | 实际读过的文档、计划、mockup 或用户上下文。 |
| 已检查代码或产物路径 | 已检查的源码、生成产物、state schema、hooks、templates 或文档路径。 |
| 已运行命令或验证 | 实际执行的命令、脚本、测试、build check 或人工验证。 |
| Finding 证据 | 支撑 finding 的路径、行号、diff、命令输出或可复现行为。 |
| 假设 | 影响 verdict 的前提和未被源码直接证明的判断。 |
| 未验证项 | 相关但未能验证的内容，以及原因。 |

**输出格式**：
- verdict: pass | needs_repair
- findings: [{id, severity, confidence, file, line, description, evidence}]
- bias_indicators: 声明你对哪些模块/技术栈不熟悉

```

如果用户提供了额外的审查重点或上下文，追加到 `## 审查要求` 之后。

## Step 3 — 派发 Codex

```bash
CODEX_SCRIPT="$(find ~/.claude/plugins -path '*/codex/scripts/codex-companion.mjs' -type f 2>/dev/null | head -1)"

node "$CODEX_SCRIPT" task --background \
  --prompt-file "$PROMPT_FILE" \
  --model gpt-5.4 --effort xhigh
```

记录 job ID：
```bash
# codex-companion 输出中包含 job ID，提取并保存
echo "<JOB_ID>" > "${REVIEW_DIR}/review-${TIMESTAMP}.job-id"
```

## Step 4 — 等待结果

```bash
node "$CODEX_SCRIPT" status "$(cat ${REVIEW_DIR}/review-${TIMESTAMP}.job-id)" \
  --wait --timeout-ms 600000
```

用 `run_in_background: true` 执行此命令。

## Step 5 — 收集并报告

```bash
node "$CODEX_SCRIPT" result "$(cat ${REVIEW_DIR}/review-${TIMESTAMP}.job-id)"
```

将结果保存到 `${REVIEW_DIR}/review-${TIMESTAMP}-result.md`。

向用户汇报：
- verdict（pass / needs_repair）
- 每个 finding 的一句话摘要 + confidence
- 如果有 needs_repair，列出建议的修复方向

不自动修复——用户决定下一步。不要将 findings 写入任何 orchestrate workflow 的 state 文件。

## 注意事项

- 此 skill 不写入 `workflow-state`，不消耗 Orchestrate Workflow 的 review budget
- 结果目录 `.claude/codex-review/` 与正规工作流的 `review-prompts/` 隔离
- 默认用 `gpt-5.4 --effort xhigh`；用户要求时可切换模型
- 一次性调用，不做 re-review 循环——用户要再审就再调用一次
