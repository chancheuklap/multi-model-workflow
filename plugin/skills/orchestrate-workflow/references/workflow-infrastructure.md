# Infrastructure Setup + Cross-Conversation Resume

> **流程位置**：`orchestrate-workflow` Steps 3-6 · 含 Cross-Conversation Resume · 完成后按 Route 进入对应 phase

## Step 3：Cross-Conversation Resume

新对话接手上一个 session 的工作。先检测活跃工作树，再检查 artifact 状态决定从哪里继续。

### 3-pre：检测并进入活跃工作树

主仓库中检查是否有活跃工作树的 breadcrumb：

```bash
cat .claude/multi-model-workflow/active-worktree 2>/dev/null
```

| 状态 | 动作 |
| --- | --- |
| 有 `active-worktree` 文件且路径有效（`git worktree list` 包含该路径） | `EnterWorktree({ path: "<路径>" })` 进入已有工作树 → 继续 3a |
| 有 `active-worktree` 文件但路径无效（工作树已被手动删除） | 删除 breadcrumb 文件 → 继续 3a（当作首次运行） |
| 无 `active-worktree` 文件 | 继续 3a（首次运行或已清理） |

### 3a：检测活跃运行

```bash
cat .claude/multi-model-workflow/active-run-id 2>/dev/null
find .claude/multi-model-workflow/workflow-state-*.json -mmin -60 2>/dev/null
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

### 3c：恢复 Infrastructure

Scope Contract 和 Budget File 已存在 → 读取并验证。`pack_count` 或 `editable artifacts` 与当前 plan 不一致 → 更新。

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
- Plans: `docs/orchestrate/plans/<slug>/`（目录，每个大 issue 一份 plan 文件）
- Issues: `docs/orchestrate/issues/<slug>/`
- Mockups: `docs/orchestrate/mockups/<slug>/`

---

## Step 4：Git Checkpoint（工作树创建）

**禁止在主仓库直接切分支**（`git checkout -b`）。所有工作在独立工作树中进行。

| 状态 | 动作 |
| --- | --- |
| 在主仓库中（非工作树） | 创建工作树（见下方） |
| 已在工作树中 | 继续 |
| 有 dirty files 属于当前 scope | 暂不 stage |
| 有 dirty files 不属于当前 scope | 不 stage、不动、不 stash |

**检测是否在工作树中**：

```bash
[ -f "$(git rev-parse --show-toplevel)/.git" ] && echo "IN_WORKTREE" || echo "MAIN_REPO"
```

工作树内 `.git` 是文件（指向主仓库的 `.git/worktrees/`）；主仓库的 `.git` 是目录。

**创建工作树**（仅 MAIN_REPO 时执行）：

1. 准备 breadcrumb 目录（在主仓库中，进入工作树前执行）：
   ```bash
   mkdir -p .claude/multi-model-workflow
   ```
2. 创建并进入工作树：
   ```
   EnterWorktree({ name: "<short-scope>" })
   ```
3. 确认分支名：`git branch --show-current`
4. 写入跨会话恢复 breadcrumb（用 `git worktree list` 获取主仓库路径）：
   ```bash
   MAIN_REPO=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')
   echo "$(pwd)" > "${MAIN_REPO}/.claude/multi-model-workflow/active-worktree"
   ```

工作树创建后，后续所有状态文件（Scope Contract、workflow-state、execution-state、pack-returns）写在工作树的 `.claude/multi-model-workflow/` 中。工作树删除时，状态文件随之清除。

## Step 5：Write Scope Contract

从用户提供的功能描述提取 kebab-case 核心词，加上当天日期组成 feature slug（`YYYY-MM-DD-<feature>`）；不确定时一次性问用户确认。然后创建 `.claude/multi-model-workflow/scope-<run_id>.md`：

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

## Step 6：Workflow State File（仅 Formal Orchestrate）

创建 `.claude/multi-model-workflow/workflow-state-<run_id>.json` via `state.sh init`：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" init --run-id "<run_id>" --slug "<slug>" --route formal
echo "<run_id>" > .claude/multi-model-workflow/active-run-id
```

Budget 在 plan count 确认后初始化（plan-writing Step 12a）：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" budget initialize --run-id "<run_id>" --plan-count <N>
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

**与 `last_gate_phase` 的区别**：`last_gate_phase` 记录最近通过的 gate（粗粒度，phase 级，用于 cross-conversation resume），`cursor.*` 记录当前精确位置（reference + step 级，用于 compaction recovery）。两者共存。

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
