# Environment Detection + Infrastructure Setup

> **流程位置**：`orchestrate-workflow` Steps 0-2 · 完成后按 Route 进入对应 phase
>
> Step 1（Entry Gate）在 SKILL.md 中，不在此 reference。本文档覆盖 Step 0（环境检测 + 断点续传）和 Step 2（基础设施搭建）。

## Step 0：Environment Detection + Resume

启动时检测当前环境，决定是断点续传还是全新任务。

### 0a：检测是否在工作树中

```bash
[ -f "$(git rev-parse --show-toplevel)/.git" ] && echo "IN_WORKTREE" || echo "MAIN_REPO"
```

工作树内 `.git` 是文件（指向主仓库的 `.git/worktrees/`）；主仓库的 `.git` 是目录。

| 状态 | 动作 |
| --- | --- |
| `IN_WORKTREE` + `.codex/multi-model-workflow/active-run-id` 存在 | 进入 0b（断点续传） |
| `IN_WORKTREE` + 无 `active-run-id` | 提示 "没有找到活跃的 workflow 状态文件，将作为全新任务处理" → Step 1（Entry Gate） |
| `MAIN_REPO` | Step 1（Entry Gate） |

### 0b：断点续传

用户已在工作树中启动 Claude，直接读取本地状态文件恢复。

```bash
RUN_ID=$(cat .codex/multi-model-workflow/active-run-id)
SLUG=$(grep -A1 '^## Feature slug' ".codex/multi-model-workflow/scope-${RUN_ID}.md" | tail -1 | xargs)
```

**Source Stability 检查**：Budget file 记录 `last_gate_phase` 和 `last_gate_timestamp`。检查 source artifacts 自上次 gate 通过后是否被修改：

```bash
git log --oneline --since="<last_gate_timestamp>" -- \
  "docs/orchestrate/design/${SLUG}.md" \
  "docs/orchestrate/plans/${SLUG}/" \
  "docs/orchestrate/issues/${SLUG}/"
```

| 条件 | 从哪里继续 |
| --- | --- |
| Design doc 存在但无 Design Review 通过记录 | orchestrate-discovery（Design Review 阶段） |
| Design doc 在 Design Review 后被修改 | 重新进入 Design Review |
| Plan 存在 + Design Review 通过 + design 未变 | orchestrate-plan-writing（Plan Review 阶段） |
| Plan 在 Plan Review 后被修改 | 重新进入 Plan Review |
| Packs 部分完成 + plan 未变 | orchestrate-execution（读 execution-state file 确定从哪个 Plan/Pack 继续） |
| 所有 Plans 通过 Plan Implementation Review + 代码未变 | orchestrate-final-review |
| Final Review 通过 | Closing（Step 21） |

**Scope Contract 和 Budget File 已存在** → 读取并验证。`pack_count` 或 `editable artifacts` 与当前 plan 不一致 → 更新。

验证通过后，按上表路由到对应 phase。**不再执行 Steps 1-2**。

---

## docs/orchestrate/ 路径约定

所有 orchestrate 产出文档统一存放在项目的 `docs/orchestrate/` 下，按类型分子文件夹，同一功能用相同的 feature slug（`YYYY-MM-DD-<feature>`）贯穿四个子文件夹：

```
docs/orchestrate/
├── design/          # 设计文档（orchestrate-discovery 产出）
│   └── YYYY-MM-DD-<feature>.md
├── plans/           # 实施计划（plan-writer 产出，每个大 issue 一份 plan）
│   └── YYYY-MM-DD-<feature>/
│       ├── 001-<issue-slug>.md          # 与 issues/ 下同编号文件一一对应
│       ├── 002-<issue-slug>.md
│       └── ...
├── issues/          # issue hierarchy（大 issue: Coordinator 产出；小 issue: plan-writer 补全）
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
- Plans: `docs/orchestrate/plans/<slug>/`（目录，每个大 issue 一份 plan 文件）
- Issues: `docs/orchestrate/issues/<slug>/`
- Mockups: `docs/orchestrate/mockups/<slug>/`

---

## Step 2：Infrastructure Setup

Entry Gate（Step 1）完成后执行。创建工作树、写入状态文件。

### Step 2a：Git Checkpoint（工作树创建）

**禁止在主仓库直接切分支**（`git checkout -b`）。所有工作在独立工作树中进行。

| 状态 | 动作 |
| --- | --- |
| 在主仓库中（非工作树） | 创建工作树（见下方） |
| 已在工作树中 | 继续（不重复创建） |
| 有 dirty files 属于当前 scope | 暂不 stage |
| 有 dirty files 不属于当前 scope | 不 stage、不动、不 stash |

**检测是否在工作树中**：

```bash
[ -f "$(git rev-parse --show-toplevel)/.git" ] && echo "IN_WORKTREE" || echo "MAIN_REPO"
```

**创建工作树**（仅 MAIN_REPO 时执行）：

1. 创建并进入工作树：
   ```
   EnterWorktree({ name: "<short-scope>" })
   ```
2. 确认分支名：`git branch --show-current`

工作树创建后，后续所有状态文件（Scope Contract、workflow-state、execution-state、pack-returns）写在工作树的 `.codex/multi-model-workflow/` 中。工作树删除时，状态文件随之清除。

### Step 2b：Write Scope Contract

从用户提供的功能描述提取 kebab-case 核心词，加上当天日期组成 feature slug（`YYYY-MM-DD-<feature>`）；不确定时一次性问用户确认。然后创建 `.codex/multi-model-workflow/scope-<run_id>.md`：

```markdown
# Scope Contract: <run_id>

## Feature slug
<YYYY-MM-DD-feature>

## Source artifacts
- <用户明确提供的文档 / tracker refs / diff>

## Editable artifacts
- Design: docs/orchestrate/design/<slug>.md
- Plans: docs/orchestrate/plans/<slug>/
- Issues: docs/orchestrate/issues/<slug>/
- Mockups: docs/orchestrate/mockups/<slug>/（UI/UX 时）

## Read-only context
- <相关 issue、ADR、代码或 runbook——sub-agent 只能用来判断，不得变成交付范围>

## Out of scope
- <明确列出容易被误纳入的相关 issue、ADR、未来能力>
```

**规则**：Source artifacts 只包含用户明确提供的内容。Editable artifacts 只能是 source 或 phase 产出。Out of scope 阻止 sub-agent 和 reviewer 扩大范围。Feature slug 一旦确定不可中途修改。

### Step 2c：Workflow State File（仅 Formal Orchestrate）

创建 `.codex/multi-model-workflow/workflow-state-<run_id>.json` via `state.sh init`：

```bash
mkdir -p .codex/multi-model-workflow
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" init --run-id "<run_id>" --slug "<slug>" --route formal
echo "<run_id>" > .codex/multi-model-workflow/active-run-id
```

Budget 在 plan count 确认后初始化（plan-writing Step 12a）：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" budget initialize --run-id "<run_id>" --plan-count <N>
```

Budget 一旦初始化（`budget_status = initialized`），`review_total` 和 `effort_total` **不可变**——执行阶段、Final Review 阶段均不得修改。如果执行阶段发现 pack 数与 plan 不一致，返回 `NEEDS_PLAN_REVISION`，不得静默更新。Bug / Multi-PR route 使用 `--route hotfix` 等，budget 自动设为 `unlimited`。

### 状态锚字段（Compaction Recovery）

| 字段 | 类型 | 更新时机 | 用途 |
|------|------|---------|------|
| `cursor.phase` | string | 进入/退出 phase skill 时（`state.sh transition` 自动更新） | Compaction 后知道在哪个 phase |
| `cursor.reference` | string \| null | Read reference 前写入，执行完写 null | Compaction 后知道在哪个 reference 里 |
| `cursor.step` | integer \| null | 进入 phase / reference 时（记录起始步骤号） | Compaction 后知道从哪个步骤继续 |

**更新规则**：
- 进入 phase skill → `state.sh transition` 更新 `cursor.phase`，手动清空 `cursor.reference` 和 `cursor.step`
- Read reference 前 → 写 `cursor.reference`
- 执行完 reference 回到 SKILL.md → `cursor.reference` 设为 null
- 进入 phase / reference 时 → 写 `cursor.step`（记录起始步骤号）

```bash
# 示例：进入 reference 前更新 cursor
state.sh update --run-id <run_id> --field '.cursor.reference' --value '"discovery-discussion.md"'
state.sh update --run-id <run_id> --field '.cursor.step' --value '3'

# 执行完 reference 后清空
state.sh update --run-id <run_id> --field '.cursor.reference' --value 'null'
```

**恢复规则**（compaction 后）：
1. 读 workflow-state 的 `cursor.phase` / `cursor.reference` / `cursor.step`
2. 如果 `cursor.reference` 不为 null → 重新 Read 该 reference，从 `cursor.step` 位置继续
3. 如果 `cursor.reference` 为 null → 在 SKILL.md 的 `cursor.step` 位置继续

**与 `last_gate_phase` 的区别**：`last_gate_phase` 记录最近通过的 gate（粗粒度，phase 级，用于断点续传），`cursor.*` 记录当前精确位置（reference + step 级，用于 compaction recovery）。两者共存。

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

---
> **下一步**：Route 1 → SKILL.md Steps 7-14（Formal Orchestrate phase dispatch）。Route 2 → SKILL.md Steps 15-18（bug-investigation-route.md）。Route 3 → SKILL.md Steps 19-20（Multi-PR Merge）。
