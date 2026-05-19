# Infrastructure Setup + Cross-Conversation Resume

> **流程位置**：`orchestrate-workflow` Steps 3-6 · 含 Cross-Conversation Resume · 完成后按 Route 进入对应 phase

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

Budget file 记录 `last_gate_phase` 和 `last_gate_timestamp`。从活跃运行的 Scope Contract 读取 feature slug，用约定路径检查 source artifacts 自上次 gate 通过后是否被修改：

```bash
RUN_ID=$(cat .claude/multi-model-workflow/active-run-id)
SLUG=$(grep -A1 '^## Feature slug' ".claude/multi-model-workflow/scope-${RUN_ID}.md" | tail -1 | xargs)
git log --oneline --since="<last_gate_timestamp>" -- \
  "docs/orchestrate/design/${SLUG}.md" \
  "docs/orchestrate/plans/${SLUG}.md" \
  "docs/orchestrate/issues/${SLUG}/"
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

## docs/orchestrate/ 路径约定

所有 orchestrate 产出文档统一存放在项目的 `docs/orchestrate/` 下，按类型分子文件夹，同一功能用相同的 feature slug（`YYYY-MM-DD-<feature>`）贯穿四个子文件夹：

```
docs/orchestrate/
├── design/          # 设计文档（orchestrate-discovery 产出）
│   └── YYYY-MM-DD-<feature>.md
├── plans/           # 实施计划（plan-writer 产出）
│   └── YYYY-MM-DD-<feature>.md
├── issues/          # issue hierarchy（to-issues 产出）
│   └── YYYY-MM-DD-<feature>/
│       ├── 001-<large-issue-slug>.md   # 大 issue 文档（内含小 issue 拆分）
│       ├── 002-<large-issue-slug>.md
│       └── ...
└── mockups/         # prototype / frontend-design 产出
    └── YYYY-MM-DD-<feature>/
        ├── *.html / *.png / *.svg
        └── README.md                   # mockup 索引（页面 × viewport × states）
```

**命名规则**：
- `<feature>` 用 kebab-case，取功能核心词（如 `compass-ui`、`billing-gate`、`auth-middleware`）
- 日期取 run 创建日（与 `run_id` 中日期一致）
- Coordinator 在 Infrastructure Setup 确定 feature slug 后，所有 phase 使用同一个 slug

**路径推导**：给定 feature slug `<slug>`，各文档路径为：
- Design: `docs/orchestrate/design/<slug>.md`
- Plan: `docs/orchestrate/plans/<slug>.md`
- Issues: `docs/orchestrate/issues/<slug>/`
- Mockups: `docs/orchestrate/mockups/<slug>/`

---

## Step 4：Write Scope Contract

从用户提供的功能描述提取 kebab-case 核心词，加上当天日期组成 feature slug（`YYYY-MM-DD-<feature>`）；不确定时一次性问用户确认。然后创建 `.claude/multi-model-workflow/scope-<run_id>.md`：

```markdown
# Scope Contract: <run_id>

## Feature slug
<YYYY-MM-DD-feature>

## Source artifacts
- <用户明确提供的文档 / tracker refs / diff>

## Editable artifacts
- Design: docs/orchestrate/design/<slug>.md
- Plan: docs/orchestrate/plans/<slug>.md
- Issues: docs/orchestrate/issues/<slug>/
- Mockups: docs/orchestrate/mockups/<slug>/（UI/UX 时）

## Read-only context
- <相关 issue、ADR、代码或 runbook——sub-agent 只能用来判断，不得变成交付范围>

## Out of scope
- <明确列出容易被误纳入的相关 issue、ADR、未来能力>
```

**规则**：Source artifacts 只包含用户明确提供的内容。Editable artifacts 只能是 source 或 phase 产出。Out of scope 阻止 sub-agent 和 reviewer 扩大范围。Feature slug 一旦确定不可中途修改。

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
  "starting_commit": "<git rev-parse HEAD after Git Checkpoint>",
  "discovery_used": 0,
  "last_gate_phase": "entry",
  "last_gate_timestamp": "<ISO 8601>",
  "dispatches": []
}
```

`budget_total` 在 plan-writing Step 12a 按 `2N + 12` 更新。Bug / Multi-PR route 不创建 budget file。

---

## Durable Handoff Brief

跨会话交接、导出为 issue、或留给以后 agent 处理时，用 durable brief，不要只保存当前文件行号。

```text
Current behavior:
Desired behavior:
Key interfaces:
Acceptance criteria:
Out of scope:
Risk flags:
AFK / HITL:
```

写行为合同，不写"去某文件第 N 行改 X"。UI / UX durable brief 必须保留 mockup 目录路径（`docs/orchestrate/mockups/<slug>/`）、目标 viewport、关键 states 和允许偏差。如果 durable brief 来自 Discovery domain alignment、prototype 或 architecture review，写明 resolved context、prototype verdict 或 architecture finding。
