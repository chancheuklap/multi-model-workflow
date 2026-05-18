# Infrastructure Setup + Cross-Conversation Resume

## Step 3：Cross-Conversation Resume

新对话接手上一个 session 的工作。检查 artifact 状态决定从哪里继续。

### 3a：检测活跃运行

```bash
cat .claude/multi-model-workflow/active-run-id 2>/dev/null
find .claude/multi-model-workflow/budget-*.json -mmin -60 2>/dev/null
```

- **无活跃运行** → 从 Entry Gate（Step 1）开始
- **有活跃运行且 stale（> 1h 无更新）** → 清理旧文件，从 Entry Gate 开始
- **有活跃运行且 fresh** → 进入 3b

### 3b：Source Stability 检查

Budget file 记录 `last_gate_phase` 和 `last_gate_timestamp`。检查 source artifacts 自上次 gate 通过后是否被修改：

```bash
git log --oneline --since="<last_gate_timestamp>" -- <design_path> <plan_path> <issue_paths>
```

| 条件 | 从哪里继续 |
| --- | --- |
| Design doc 存在但无 Design Review 通过记录 | orchestrate-discovery（Design Review 阶段） |
| Design doc 在 Design Review 后被修改 | 重新进入 Design Review |
| Plan 存在 + Design Review 通过 + design 未变 | orchestrate-plan-writing（Plan Review 阶段） |
| Plan 在 Plan Review 后被修改 | 重新进入 Plan Review |
| Packs 部分完成 + plan 未变 | orchestrate-execution（从上次完成的 pack 继续） |
| 所有 packs 完成 + 代码未变 | orchestrate-final-review |
| Final Review 通过 | Closing（Step 21） |

### 3c：恢复 Infrastructure

Scope Contract 和 Budget File 已存在 → 读取并验证。`pack_count` 或 `editable artifacts` 与当前 plan 不一致 → 更新。

---

## Step 4：Write Scope Contract

创建 `.claude/multi-model-workflow/scope-<run_id>.md`：

```markdown
# Scope Contract: <run_id>

## Source artifacts
- <用户明确提供的文档 / tracker refs / diff>

## Editable artifacts
- <source artifacts 或当前 phase 明确要求产出的 design / plan / pack / report>

## Read-only context
- <相关 issue、ADR、代码或 runbook——sub-agent 只能用来判断，不得变成交付范围>

## Out of scope
- <明确列出容易被误纳入的相关 issue、ADR、未来能力>

## Issue recording target
- <small issue hierarchy 写回哪里>
```

**规则**：Source artifacts 只包含用户明确提供的内容。Editable artifacts 只能是 source 或 phase 产出。Out of scope 阻止 sub-agent 和 reviewer 扩大范围。

## Step 5：Git Checkpoint

| 状态 | 动作 |
| --- | --- |
| 在 main / master / release branch 上 | 创建 `work/<short-scope>` 分支 |
| 已在 work branch 上 | 继续 |
| 有 dirty files 属于当前 scope | 暂不 stage |
| 有 dirty files 不属于当前 scope | 不 stage、不动、不 stash |

## Step 6：Budget File（仅 Formal Orchestrate）

创建 `.claude/multi-model-workflow/budget-<run_id>.json` 和 `active-run-id`：

```json
{
  "run_id": "formal-<YYYYMMDD>-<HHMMSS>",
  "budget_total": 0,
  "budget_used": 0,
  "pack_count": 0,
  "last_gate_phase": "entry",
  "last_gate_timestamp": "<ISO 8601>",
  "dispatches": []
}
```

`budget_total` 在 plan-writing Step 12a 按 `2N + 12` 更新。Bug / Multi-PR route 不创建 budget file。
