# Codex 跨 PR 集成审查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 16-18 · 所有冲突解决后（或 explorer 未发现冲突）进入 · 通过后 → Steps 19-22（`merge-completion.md`）

## Self-Read Protocol

你是 codex-reviewer（执行 Multi-PR 集成审查）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`gate`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`，获取大设计文档路径、PR 列表、合同地图、冲突解决记录。
3. 读大设计文档（来自 merge-brief）理解整体目标。
4. 自行运行 `git diff` 获取所有 PR 合并后的 combined diff。
5. 读本文件（你正在读的这份手册），理解 Review Angles 与 Return Contract 格式。
6. 按 7 个 Review Angles 独立验证，遵守 Pre-emit Verification Gate，输出 findings。

这不是 Plan Implementation Review（审查单个 Plan 的全部 pack），不是 Final Review（审查 design intent coverage）——这是**跨 PR 集成审查**，验证多个 PR 合在一起后系统是否正确。

## Step 16：构造 Codex Dispatch

**Read** `plugin/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/multi-pr-integration-review.md`：

```markdown
## Scope
跨 PR 集成审查。多个并行 PR 来自同一大设计，各自已通过 Final Review。
本次审查验证它们合在一起后是否正确。

## Merge context
读 `.claude/multi-model-workflow/merge-brief-<run_id>.md` 获取：
- 大设计文档路径（你自读该文档）
- PRs included（PR / Branch / 核心行为 / Final Review verdict）
- 冲突解决记录（resolved conflicts + how they were fixed；或 'Explorer 确认无 PR 间冲突'）
- 合同地图（all cross-PR contract surfaces）

## Combined diff
自行运行 `git diff <base-branch>..HEAD`（或对每个 PR branch 分别 diff 后合并）。

## Review angles

### 1. 组合行为正确性
所有 PR 合在一起是否产出大设计描述的正确行为。
每个 PR 各自正确不代表组合正确——关注交互、顺序、依赖。

### 2. 合同一致性
跨 PR 的 Pydantic model / API / DB schema / JSON payload / registry 是否一致。
一个 PR 提供的合同是否被另一个 PR 正确消费。

### 3. 迁移完整性
多个 PR 的 migration 合并后：
- 顺序是否正确
- 是否有遗漏的 migration（PR A 改了 model，PR B 没有对应 migration）
- 回滚是否安全

### 4. 状态一致性
跨 PR 的 shared state 假设是否一致。
并发访问 shared state 是否安全。

### 5. Import / 依赖
合并后是否有循环 import。
依赖版本是否一致。

### 6. 回归
合并所有 PR 后，既有功能是否完好。
跑完整测试套件并报告结果。

### 7. 冲突修复质量（如有）
之前解决的冲突的修复是否正确、完整。
修复是否引入了新问题。

## Calibration
**不要信任各 PR 的 Final Review 结论——独立验证组合行为。** 每个 PR 各自正确不代表组合正确。你的审查必须基于合并后的代码事实，不是各 PR 独立 review 的结论。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
单个 PR 内部的代码质量——已在各自 Final Review 中覆盖，不再重复。
措辞、命名、风格——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
组合行为:
合同一致性:
迁移完整性:
状态一致性:
Import / 依赖:
回归:
冲突修复质量:
Critical:
Important:
Disposition required:
### Verification
### Open Items
```

## Step 17：接收 + Disposition

**整体 Verdict 前置检查**：reviewer 返回整体 `needs context` 时，Coordinator 补充上下文后重新 dispatch，不进入 per-finding disposition。

**Read** `plugin/skills/_shared/disposition-table.md` 并按其 disposition 选项处理 findings。

Multi-PR 增加验证维度：对照大设计文档确认 spec 判断 + 对照冲突解决记录确认修复判断。

**`needs evidence` 补证**：派 `code-explorer`（窄范围单文件/单调用链）或 `complex-code-explorer`（多模块/跨边界）做只读调查。Prompt 包含：finding 待验证、reviewer 主张、Coordinator 存疑点、相关文件。Explorer 返回 confirmed / refuted / partially confirmed 后再给最终 disposition。

**Review 通过** → Step 19（`merge-completion.md`）。

**有 accepted findings** → Step 18。

## Step 18：集成审查修复

修复路由同冲突解决阶段：

**Read** `plugin/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

- 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
- 复杂修复 → 派 worker

修复后做 **Repair Re-Review**。按以下步骤派发 Codex review（复用已有 `CODEX_SCRIPT`）：
1. 写 prompt → `review-prompts/<gate>.md`，并以前缀 `DISPATCH_ENVELOPE` 声明 `agent_role: "codex-reviewer"`、`review_intent: "baseline"` 和非空 `disposition_refs`。
2. 按 Step 16 的共享 `review-dispatch` 执行。
3. 等待和读取结果也按 Step 16 的共享 `review-dispatch` 执行，结果写入 `review-results/<gate>.md`。

Compaction 恢复：有 `.job-id` 无对应 `review-results/` → 从 Step 3 继续。

gate 名使用 `multi-pr-repair-<round>`（`<round>` = 当前修复轮次 1/2），不覆盖 baseline 结果。

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/multi-pr-repair-<round>.md`。下例以第 1 轮为例；第 2 轮时同步替换 `repair_round` 和 `idempotency_key`：

```markdown
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "<run_id>",
  "phase": "multi-pr-merge",
  "agent_role": "codex-reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 1,
  "idempotency_key": "<run_id>/multi-pr-repair-1",
  "disposition_refs": ["<accepted finding ids>"],
  "review_intent": "baseline",
  "exception_code": null
}
-->

## Scope
Repair re-review for Multi-PR integration repair.
Only review the changes made to address the listed findings.

## Original findings
读 `DISPATCH_ENVELOPE.disposition_refs` 对应的 accepted findings（由 Coordinator 在 repair dispatch 时填入）。

## Repair diff
<git diff of repair changes>

## Review focus
- Each accepted finding has been addressed
- Repair does not introduce new issues

## Calibration
只验证修复是否解决了原始 finding。不做全面重审。

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
Per-finding status:
### Verification
### Open Items
```

最多 2 轮修复。超过 → BLOCKED。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `merge-brief-<run_id>.md`（若已写则复用），确保包含 PR 列表、设计文档路径、合同地图、冲突解决记录。
2. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`gate`（`multi-pr-integration-review`）、`review_intent: "baseline"`。
3. 写 review-prompts 文件，运行 validate/record 脚本，触发 Codex job。
4. 等待 job 完成后运行 result/complete 脚本，进入 Steps 17-18 disposition 流程。

---
> **下一步**：通过 → Steps 19-22（`merge-completion.md`）。BLOCKED → 返回 verdict。
