# Merge Brief 写作模板

> **使用说明**：本模板用于 multi-pr-merge agent 在 Step 2 创建 merge-brief 时参考。
> 创建命令：`bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" merge-brief init --run-id <run_id> --slug <slug>`
> 文件路径：`.claude/multi-model-workflow/merge-brief-<run_id>.md`
> 
> **边界**：merge-brief 是跨 PR 的合成视角。不复制单 PR 的 design/plan 内容，只写跨 PR 的交互、合同、顺序、冲突。

---

<!-- MERGE_BRIEF_META
{
  "schema_version": "1",
  "run_id": "<run_id>",
  "slug": "<feature-slug>",
  "created_at": "<ISO-8601>",
  "last_updated_at": "<ISO-8601>",
  "current_stage": "init",
  "integration_review_gate": null
}
-->

# Merge Brief: <run_id>

## 1. Meta

- **run_id**: `<run_id>`
- **slug**: `<feature-slug>`
- **route**: `multi-pr-merge`
- **created_at**: `<ISO-8601>`
- **current_stage**: `init` → 由 `state.sh merge-brief stage` 推进
- **关联 workflow-state 路径**: `.claude/multi-model-workflow/workflow-state-<run_id>.json`

> 写什么：run 的基础标识信息，与 workflow-state 对齐。
> 不写什么：具体的设计决策、实现细节——那些在各 PR 的 design.md 里。
> 与 workflow-state 的边界：workflow-state 是状态机锚（phase/budget/cursor）；merge-brief 是合成模型的 narrative。

---

## 2. 参与 PR（Big Picture）

> 写什么：所有参与本次合并的 PR 基本信息 + 各自的关键文档路径 + Final Review 结果。
> 数据来源：`gh pr view --json` + 各 PR 的 docs/orchestrate/ 树。
> 不写什么：PR 内容细节——用路径指向，不内联粘贴。

| PR | Branch | 大设计 path | 大计划 path | 单 PR design path | 单 PR plan path | Final-review verdict | 核心行为 (≤2 句) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #NNN | `feature/xxx` | `docs/orchestrate/design/YYYY-MM-DD-xxx.md` | `docs/orchestrate/plans/YYYY-MM-DD-xxx/` | — | — | pass | 该 PR 的核心行为一句话描述 |

---

## 3. 合并后正确状态模型（Step 2 强制产出）

> 写什么：所有 PR 合并后系统应具备的跨 PR 行为、合同面、文件交叉、合并顺序、风险热点。
> 不写什么：单个 PR 内部行为——那在各 PR 的 design.md §Goal Behavior。
> 与 plan.md 的边界：plan 写 Pack 执行路线图（已执行完）；merge-brief §3 写合并后的语义视角。

### 3.1 行为清单

来自大设计文档，逐条列出合并后系统应展示的行为。每条标注由哪些 PR 共同支撑。

- [ ] 行为 A（由 #NNN + #MMM 共同支撑）
- [ ] 行为 B（由 #NNN 单独支撑，但 #MMM 的变更是前提条件）

### 3.2 合同地图（Cross-PR Contract Surfaces）

> 重点：跨 PR 的接口、协议、数据结构的变更方向。

| Surface | 类型 | Provider PR | Consumer PR(s) | 修改方向摘要 |
| --- | --- | --- | --- | --- |
| `UserSchema` | Pydantic | #NNN | #MMM | #NNN 新增 phone 字段，#MMM 消费 |

### 3.3 文件交叉矩阵

> 并改 = 两个 PR 都改了同一文件；单改一方依赖 = 只有一方改，另一方依赖其产物。

| 文件 | 涉及 PR | 交叉类型 |
| --- | --- | --- |
| `app/models/user.py` | #NNN, #MMM | 并改 |

### 3.4 合并顺序（依赖驱动）

1. **#NNN** — 理由：Provider PR，#MMM 消费其 UserSchema 变更
2. **#MMM** — 理由：Consumer PR，依赖 #NNN 的 phone 字段

### 3.5 风险热点

| 热点 | 严重度 | 说明 |
| --- | --- | --- |
| `UserSchema.phone` 字段跨 PR | high | #NNN 添加，#MMM 消费，合并顺序错误会导致 runtime error |

---

## 4. Conflict Findings（Steps 5-7 持续追加）

> 写什么：Explorer 返回后由 Coordinator 追加每个 conflict；classification 由 Coordinator 在 Step 7 填写。
> 不写什么：修复方案——那在 §6 Resolution Log。
> conflict_id per-run（C-001 起编，跨 run 不重用）。

### Conflict C-001

- **type**: `code` | `function` | `intent` | `contract` | `implicit-dep` | `migration-order`
- **involved_prs**: [#NNN, #MMM]
- **files**: [`app/models/user.py:45`, `app/api/users.py:120`]
- **description**: PR #NNN 修改了 `UserSchema` 添加 phone 字段，PR #MMM 直接使用了旧的字段列表导致在合并后运行时缺少 phone 字段。
- **severity**: `low` | `medium` | `high` | `blocker`
- **classification**: `simple` | `complex-clear` | `systemic`（Step 7 填）
- **route**: `coordinator-fix` | `worker-fix` | `analyst-then-worker`（Step 7 填）
- **status**: `open`
- **discovered_by**: `explorer-<agent_id>` 或 `Coordinator`
- **discovered_at**: `<ISO-8601>`

---

## 5. Root Cause Analysis（Step 10 追加；仅 systemic conflict）

> 写什么：Analyst 返回后由 Coordinator 从 analyst result 中提炼并追加。
> 不写什么：修复代码、具体 diff——那在 §6 + worker result。
> 与 §4 的关系：§5 解释"为什么发生"；§4 描述"发生了什么"。

### RCA for C-001

- **analyst_agent_id**: `<id>`
- **resolution**: `root_cause_identified` | `design_conflict` | `implementation_deviation` | `unable_to_determine`
- **root_cause_type**: 设计遗漏 / 实现偏离 / 缺失协调 / 隐式耦合 / 合同版本冲突 / 迁移顺序冲突
- **root_cause_detail**: `<analyst 详述>`
- **fix_direction**: `<修复方向，不写代码>`
- **target_pr**: `#NNN`
- **related_conflicts**: [`C-002`]
- **design_impact**: 大设计需更新 / 无
- **regression_risk**: `<风险评估>`

---

## 6. Resolution Log（Steps 13-15 追加）

> 写什么：Coordinator 验证修复后，从 worker result 中提炼并追加。
> 不写什么：Coordinator 未亲验的结果——必须 coordinator_verified=true 才落盘。
> 与 worker-results/ 的关系：worker-result 是原文；§6 是 Coordinator 验证摘要。

### Resolution for C-001

- **owner**: `coordinator-path-a` | `worker:<agent_id>`
- **repair_round**: 1
- **changed_files**: [`app/models/user.py`]
- **summary**: 在 #MMM 的 API handler 中补充了 phone 字段引用，对齐 #NNN 的 UserSchema。
- **verification**:
  - commands run: `python3 -m pytest tests/test_users.py -v`
  - tests: `pass`
  - coordinator_verified: `true`（evidence: `pytest passed 12/12`）
- **status_after**: `resolved` | `escalated-to-systemic` | `new-conflict-spawned (→ C-002)`
- **resolved_at**: `<ISO-8601>`

---

## 7. Integration Review Pointers（Step 16 前补写）

> 写什么：喂给 Codex 集成审查的指针；不粘贴内容，只给路径和锚点。
> 不写什么：审查结论——那在 review-results/ 里。

- **base_diff_range**: `git diff $(git merge-base main HEAD)..HEAD`
- **contract_surfaces_to_audit**: `[见 §3.2 表，重点：UserSchema, migration/0042_add_phone]`
- **resolved_conflicts_summary**: `[C-001, C-003]`（仅 resolved 的）
- **per_pr_final_review_verdict_refs**:
  - `[.claude/multi-model-workflow/review-results/final-review-<pr1>.md]`
  - `[.claude/multi-model-workflow/review-results/final-review-<pr2>.md]`
- **regression_focus_files**: `[app/models/user.py, tests/test_users.py]`（§3.5 已被 §6 触及的文件）
- **integration_review_gate_name**: `multi-pr-integration-review`

---

## 8. Open Items / Out-of-scope

> 写什么：合并过程累积的非阻塞项、范围外冲突的 GitHub issue refs、待用户决策清单。
> 不写什么：已经 resolved 的冲突——那在 §6。

- [ ] **Out-of-scope**: PR #MMM 中的 deprecated API 清理 → GitHub issue #456（已创建，不阻塞合并）
- [ ] **User decision needed**: `<需要用户拍板的事项>`

---

## 9. Verdict（Step 22 写入）

> 写什么：最终 verdict + 关键证据指针。写完后更新 META current_stage=complete。
> 默认不归档：merge-brief 随 worktree 删除。仅在 verdict=MERGE_COMPLETE 时，Coordinator 可选 cp 到 docs/orchestrate/merge-briefs/<slug>-<run_id>.md。

- **verdict**: `MERGE_COMPLETE` | `NEEDS_DISCOVERY` | `NEEDS_USER_DECISION` | `BLOCKED`
- **evidence_pointers**:
  - per-PR merge commit: `git log --oneline main..HEAD`
  - 集成审查 verdict: `.claude/multi-model-workflow/review-results/multi-pr-integration-review.md`
  - 全量测试结果: `bash plugin/scripts/run-all-tests.sh → 全 pass`
- **decided_at**: `<ISO-8601>`

---

## 示例：迷你 merge-brief（3 PR 合并）

> 以下为最简化示例，展示真实使用时各段的密度。

<!-- MERGE_BRIEF_META
{
  "schema_version": "1",
  "run_id": "example-run-001",
  "slug": "user-phone-feature",
  "created_at": "2026-05-28T10:00:00Z",
  "last_updated_at": "2026-05-28T18:30:00Z",
  "current_stage": "complete",
  "integration_review_gate": "multi-pr-integration-review"
}
-->

### §2 PR 表（示例）

| PR | Branch | 大设计 path | Final-review | 核心行为 |
| --- | --- | --- | --- | --- |
| #101 | `feat/user-schema` | `docs/orchestrate/design/2026-05-01-user-phone.md` | pass | 添加 phone 字段到 UserSchema + migration |
| #102 | `feat/user-api` | 同上（共享大设计） | pass | 新增 GET /users/{id}/phone 端点 |
| #103 | `feat/user-frontend` | 同上 | needs_repair | 前端 UserCard 展示 phone |

### §4 Conflict（示例）

**C-001**: #102 的 API handler 使用旧 UserSchema（无 phone），在 #101 合入后运行时报错。severity=high / classification=simple / status=resolved

### §6 Resolution（示例）

**C-001**: Coordinator 直接在 #102 的 `api/users.py:78` 补充 `phone=user.phone`。tests pass。status_after=resolved。

### §9 Verdict（示例）

**MERGE_COMPLETE**。所有冲突 resolved。集成审查 pass。3 PR 顺序合入：#101 → #102 → #103。
