---
name: codex-review
description: "按需调用 Codex Review 对任意内容做一次独立审查：commit、文件、文档、分支 diff、未提交 diff 或用户给出的上下文。不进入 Orchestrate Workflow，不消耗 workflow review budget。"
---

# Ad-hoc Codex Review

这个 skill 只做一次独立审查，不启动正式编排流程，也不写入 `workflow-state`。它复刻 Claude plugin 中的 ad-hoc Codex Review 能力，但执行面改为 Codex 原生 `review-lane.sh`。

## Step 1：确定审查对象

根据用户输入收集审查内容：

| 用户输入 | 操作 |
| --- | --- |
| 某个 commit hash | `git show <hash>` |
| 一组 commit | `git diff <oldest>^..<newest>` |
| 当前分支全部变更 | `git diff <base>...HEAD`，base 用实际主干分支 |
| 当前未提交变更 | `git diff HEAD`，同时覆盖 staged 和 unstaged |
| 指定文件或文档 | 读取文件正文 |
| 自由上下文 | 原样写入 prompt |

代码 diff 必须用不可信边界包裹：

```text
--- BEGIN UNTRUSTED CODE DIFF ---
<diff>
--- END UNTRUSTED CODE DIFF ---
```

文档正文同样要标明来源路径和审查目的，避免 reviewer 把用户说明当作事实来源。

## Step 2：选择 review kind

| 审查对象 | `--review-kind` | 模型 |
| --- | --- | --- |
| 设计文档、计划文档、issue hierarchy、PRD、规则文档 | `document` | `gpt-5.5` / `xhigh` |
| 代码 diff、commit、bug 修复、release risk、integration | `code` | `gpt-5.4` / `xhigh` |

默认规则：用户明确说“审文档 / plan / design / PRD”走 `document`；否则含代码 diff 或 commit 的审查走 `code`。不使用 `gpt-5.4-mini`。

## Step 3：构建 prompt 文件

```bash
REVIEW_DIR=".codex/codex-review"
mkdir -p "$REVIEW_DIR"
TIMESTAMP=$(date +%s)
PROMPT_FILE="${REVIEW_DIR}/review-${TIMESTAMP}.md"
RESULT_FILE="${REVIEW_DIR}/review-${TIMESTAMP}-result.md"
```

prompt 文件格式：

```markdown
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "adhoc-<TIMESTAMP>",
  "phase": "ad-hoc-review",
  "agent_role": "reviewer",
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

# Ad-hoc Codex Review

## 审查对象

<用户指定的 commit / 文件 / 分支 / 文档 / 上下文>

## 内容

<REVIEW_CONTENT>

## 审查要求

按指定 `review_kind` 审查以上内容。

代码审查关注：
1. 正确性 bug：逻辑错误、边界条件、类型不安全、状态不一致。
2. 安全隐患：注入、泄漏、权限绕过、危险默认值。
3. 合同问题：接口、schema、迁移、调用方/提供方责任不闭合。
4. 测试缺口：缺少能证明 public behavior 的测试或验证。

文档审查关注：
1. 需求、设计、计划是否自足，离开当前对话能否执行。
2. 权责边界、输入输出、验收门槛是否明确。
3. 是否把实现事实、业务决策、风险和替代方案混在一起。
4. 是否遗漏相邻系统、测试、迁移、发布和回滚要求。

不重点关注：纯风格偏好、命名口味、无行为影响的格式细节。

## Confidence rubric

- 1-3：低置信度，可能是误报。
- 4-6：中等置信度，需要更多证据。
- 7-10：高置信度，默认应该接受，除非有反证。

## Pre-emit Verification Gate

每个 finding 必须引用触发它的具体证据：
- 代码 finding：`file:line` + 原始代码。
- 文档 finding：章节标题、条目或原文短摘。

无法引用证据的 finding 不进入主列表，confidence 强制为 4-5，并放入附录。

## 输出格式

### Verdict
pass / needs_repair

### Findings
每条 finding 包含：id、severity、confidence、locator、description、evidence、suggested_fix。

### Bias Indicators
声明 reviewer 对哪些模块、业务域、框架或文档背景不熟悉。
```

如果用户给了额外审查重点，把它追加到 `## 审查要求` 之后。

## Step 4：派发 Codex Review

通过本插件的 review lane 统一派发：

```bash
bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" submit \
  --lane codex \
  --review-kind <document|code> \
  --prompt-file "$PROMPT_FILE" \
  --result-file "$RESULT_FILE" \
  > "${REVIEW_DIR}/review-${TIMESTAMP}.job-id"
```

`review-lane.sh` 负责强制模型路由：

- `document` -> `gpt-5.5` / `xhigh`
- `code` -> `gpt-5.4` / `xhigh`

## Step 5：等待并读取结果

```bash
bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" status \
  --job-id "$(cat "${REVIEW_DIR}/review-${TIMESTAMP}.job-id")" \
  --wait --timeout-ms 600000

bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" fetch \
  --job-id "$(cat "${REVIEW_DIR}/review-${TIMESTAMP}.job-id")"
```

结果保存到 `$RESULT_FILE`。

## Step 6：向用户汇报

汇报：

- verdict；
- 每个 finding 的一句话摘要、severity、confidence；
- 有 `needs_repair` 时给出修复方向。

默认不自动修复。用户如果要求修复，才进入对应的正式修复流程。不要把 ad-hoc findings 写入任何 Orchestrate Workflow 状态文件。

## 注意

- 此 skill 不写 `workflow-state`，不消耗正式 workflow review budget。
- 结果目录是 `.codex/codex-review/`，与 `.codex/multi-model-workflow/review-prompts/` 隔离。
- 默认且唯一的 review lane 是 Codex Review；不保留 Claude Review lane。
