# Plan 002：Phase 1 文档 schema 字段补全 + Enforcement 机制

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（第三轮决策日志 + 9 项 enforcement 表）
**Issue ref**: ad-hoc 改造
**Blocked by**: Plan 001
**Risk profile**: **high**（含 R1 阻塞性原子改造：Cross-Plan Contract Anchors 前移）
**Worker type**: `complex-pack-executor`（涉及 cross-plan migration + state schema 改动）

## Plan Goal Behavior

补全 7 处文档/state schema 字段，新增 9 项 enforcement 机制。完成后，Coordinator 临场粘贴 design/issue/plan 内容的需求被消除（Phase 2/3 才能落地），Worker 自治读 Pack Execution Manifest 的依赖就绪（Phase 4 才能落地）。

## Plan Acceptance Criteria

- [x] design 文档 schema 含 Review History / Cross-Plan Contract Anchors / Business Summary Inputs 三个 section（commit 9089245）
- [x] issue 文档 schema 含 Design context refs section（ae58a3e）
- [x] plan 文档 schema 含 Plan Review History / Pack Execution Manifest 两个 section（f4543c6）
- [x] `workflow-state.review_dispositions[]` 含 `plan_id` + `coordinator_verified_evidence` 可选字段（eb0a955）
- [x] `execution-state.plans[N]` 含 `worker_agent_id` + `pack_summary` + `current_plan_id` 字段（fbc0aa9）
- [x] state.sh 支持新子命令：`review-history append`、`business-summary append`、`merge-brief init/stage/verify`（96acb2c）
- [x] state.sh `agent-id set/get` 支持 `--plan-id`（96acb2c）
- [x] state.sh `disposition record` 支持 `--plan-id` + `--coordinator-verified-evidence`（96acb2c）
- [x] hook `complete-review-dispatch.sh` 匹配 `design-review-*` / `plan-review-*` gate 时自动 append Review History（d0ea007）
- [x] hook `track-execution-state.sh` 在 PLAN_DONE 时聚合 pack-returns 写入 `pack_summary`（d68f3da）
- [x] 构建脚本 `generate-pack-manifest.sh` 可从 plan 主体生成 Manifest section（cfac636）
- [x] `pack-returns/*.json` JSON schema 落地（381b60b）
- [x] state.sh `validate` 强制「accepted disposition 必须有 coordinator_verified_evidence」（96acb2c）
- [x] **R1 原子改造**：`cross-plan-contract-map.md` 内容迁移到 design.md `## Cross-Plan Contract Anchors`，3+1 处硬编码 reader 同步改路径（31e8af6；Worker scope 扩展同步 plan-writing SKILL.md + architecture-draft.md，已 Coordinator review 通过）
- [x] **R2 三方对账 hook** `validate-pack-manifest.sh`（291bc5b）
- [x] state-transition-matrix.md + state.sh TRANSITION_MATRIX 同步 plan-level 流转（0e1374b）
- [x] `bash plugin/scripts/run-all-tests.sh` 通过（37 suites）
- [x] `bash plugin/scripts/verify-maturity.sh` 通过（104/0）

**Plan 002 状态**：✅ 完成（2026-05-28，Worker agentId `ac968bfe2818bc3a8`，verdict=pass）

**Coordinator Review 通过项**（Worker flag 的 scope 扩展）：
1. R1 改造扩展到 `plan-writing/SKILL.md` + `architecture-draft.md`——必要扩展（R1 grep test `! grep -rq 'Read.*cross-plan-contract-map.md' plugin/skills/` 强制）
2. `test_cross_plan_contract_map.sh` 测试重写——必要（旧 assertion 与新行为冲突）

**已知 Gap**（不阻塞）：
- 现有 6 个 Plan 文档使用 `## Pack N.M` 二级标题；`generate-pack-manifest.sh` 期待 `### Task Pack N.M` 三级标题（schema 6-column 含 anchor）。**决策**：现有 6 Plan 保留 legacy 5-column 格式作为历史；future plans 用新 schema。`bash plugin/build/generate-pack-manifest.sh --check docs/orchestrate/plans/.../002-*.md` 这条对当前 Plan 002 跳过；新 plan 必须通过。

## File / Responsibility Map

| 文件 | 操作 |
| --- | --- |
| `plugin/skills/orchestrate-discovery/references/discovery-design-document.md` | Edit (补 3 section 模板) |
| `plugin/skills/orchestrate-discovery/references/issue-splitting.md` | Edit (补 Design context refs section 模板) |
| `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md` | Edit (补 Plan Review History + Pack Execution Manifest section 模板) |
| `plugin/state-schema/workflow-state-v1.json` | Edit (review_dispositions[] +2 字段) |
| `plugin/state-schema/execution-state-v1.json` | Edit (plans[N] +3 字段) |
| `plugin/state-schema/dispatch-envelope-v1.json` | Edit (+plan_id 字段，本 Plan 仅 schema，hook 解析在 Plan 005) |
| 新增：`plugin/state-schema/pack-returns-v1.json` | Create (JSON schema for pack-returns 文件)|
| `plugin/scripts/state.sh` | Edit (新增 / 扩展多个子命令) |
| `plugin/hooks/complete-review-dispatch.sh` | Edit (gate match 时 append Review History) |
| `plugin/hooks/track-execution-state.sh` | Edit (PLAN_DONE 时聚合 pack_summary) |
| 新增：`plugin/build/generate-pack-manifest.sh` | Create (Manifest 自动生成)|
| `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` | Edit (Step 11 改写：不再独立写 cross-plan-contract-map.md，改为写 design.md section) |
| `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` | Edit (L92, L112 改路径) |
| `plugin/skills/orchestrate-final-review/references/final-review-angles.md` | Edit (L125, L182 改路径) |
| `plugin/skills/orchestrate-final-review/references/final-review-preconditions.md` | Edit (L15 改路径) |
| 已有 cross-plan-contract-map.md 文件（如存在） | **Delete / 迁移内容到 design.md** |

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files |
| --- | --- | --- | --- | --- |
| 2.1 | design 文档 schema 补 3 sections | normal | — | `discovery-design-document.md` |
| 2.2 | issue 文档 schema 补 Design context refs | trivial | — | `issue-splitting.md` |
| 2.3 | plan 文档 schema 补 Plan Review History + Pack Execution Manifest | normal | — | `plan-writing-methodology.md` |
| 2.4 | workflow-state schema 扩展 review_dispositions[] | normal | — | `workflow-state-v1.json` |
| 2.5 | execution-state schema 扩展 plans[N] | normal | — | `execution-state-v1.json` |
| 2.6 | dispatch-envelope schema +plan_id（仅 schema 声明） | trivial | — | `dispatch-envelope-v1.json` |
| 2.7 | pack-returns JSON schema 新增 | trivial | — | 新文件 |
| 2.8 | state.sh 新增 / 扩展子命令 | high-risk | 2.4, 2.5 | `state.sh` |
| 2.9 | hook complete-review-dispatch 自动 append Review History | normal | 2.1, 2.3, 2.8 | `complete-review-dispatch.sh` |
| 2.10 | hook track-execution-state 聚合 pack_summary | normal | 2.5, 2.7 | `track-execution-state.sh` |
| 2.11 | 构建脚本 generate-pack-manifest.sh | normal | 2.3 | 新文件 |
| 2.12 | **R1 原子改造**：cross-plan-contract-map 迁移 | **high-risk** | 2.1 | 多文件同步 |
| 2.13 | hook validate-pack-manifest.sh 三方对账 | normal | 2.3, 2.5, 2.11 | 新文件 |
| 2.14 | state-transition-matrix.md 同步 plan-level 流转 | trivial | 2.5 | 文档 |

---

## Pack 2.1：design 文档 schema 补 3 sections

### Goal behavior
让 design 文档承载 Review History（审查反馈传递给 plan-writer）、Cross-Plan Contract Anchors（前移自独立文件，单一源）、Business Summary Inputs（每 plan 一段业务描述，让 reviewer 出业务汇报草稿）。

### Implementation tasks
1. Read `plugin/skills/orchestrate-discovery/references/discovery-design-document.md`，定位 design 文档骨架
2. 在骨架末尾追加 3 个 section 模板（含示例）：

```markdown
## Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |
| 1 | pass | codex-gpt-5.5 | <重点建议摘要> | <gotcha 列表> | 2026-05-28 |

（append-only，每轮 review 通过后追加一行）

## Cross-Plan Contract Anchors

跨 Plan 共享的合同 / 接口 / 文件所有权。

| Surface | 类型 (Pydantic/API/DB/migration/registry) | Owner Plan | Provider Plan | Consumer Plan(s) | 关键字段/路径 |
| --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | ... |

（替代独立 cross-plan-contract-map.md 文件；plan-writing 后由 Coordinator 维护）

## Business Summary Inputs

每个 Plan 完成后追加一段，描述该 Plan 交付的业务能力（用户/产品语言）。供 final-reviewer 起草业务汇报。

### Plan 001 — <Plan title>
- 新增能力：<对用户可见的功能描述>
- 验证证据：<截图 / 测试通过 / 用户场景>
- 残余风险：<已知边界 / 后续改进>
```

3. 在 design 模板的"Self-Check"段加一条：「Review History / Cross-Plan Contract Anchors / Business Summary Inputs section 已存在（即使为空）」
4. 跑 `bash plugin/build/build.sh --check` 验证

### Owned files
- Edit: `plugin/skills/orchestrate-discovery/references/discovery-design-document.md`

### Read first
- `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（参考自己作为 design 模板示例）
- 已有的 design 文档（如有）确认 schema 兼容

### Acceptance criteria
- [x] design 模板含 3 个新 section 的模板段
- [x] Self-Check 列表更新
- [x] `build.sh --check` 通过

### Verification commands
- `grep -q 'Review History' plugin/skills/orchestrate-discovery/references/discovery-design-document.md` → Expected: exit 0
- `grep -q 'Cross-Plan Contract Anchors' plugin/skills/orchestrate-discovery/references/discovery-design-document.md` → Expected: exit 0
- `grep -q 'Business Summary Inputs' plugin/skills/orchestrate-discovery/references/discovery-design-document.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
normal（schema 变更影响所有未来 design；老 design 文档需 fallback 容忍缺失）

### Out of scope
- 不补现有 design 文档（migration 留给未来人工补；reader 必须 fallback 老文档）
- 不改 SKILL.md 的讨论流程

---

## Pack 2.2：issue 文档 schema 补 Design context refs

### Goal behavior
让 issue 文件含指向 design.md 段落锚点的指针，plan-writer 跟随指针定位 design 相关章节，无需 Coordinator 临场提取"与本 issue 相关的设计要点"。

### Implementation tasks
1. Read `plugin/skills/orchestrate-discovery/references/issue-splitting.md`，定位大 issue 模板段（L65-77 区域）
2. 在模板中追加：

```markdown
## Design context refs

指向 design 文档相关章节的锚点（plan-writer 跟随）。

- `docs/orchestrate/design/<slug>.md#<anchor-1>` — <相关性说明>
- `docs/orchestrate/design/<slug>.md#<anchor-2>` — <相关性说明>
```

3. 在 issue 自检列表加 "Design context refs 已填写（至少一条）"

### Owned files
- Edit: `plugin/skills/orchestrate-discovery/references/issue-splitting.md`

### Read first
- `plugin/skills/orchestrate-discovery/references/issue-splitting.md`（当前格式）

### Acceptance criteria
- [x] issue 模板含 Design context refs section
- [x] `build.sh --check` 通过

### Verification commands
- `grep -q 'Design context refs' plugin/skills/orchestrate-discovery/references/issue-splitting.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
trivial

### Out of scope
- 不补现有 issue 文件（plan-writer fallback Read 全 design）

---

## Pack 2.3：plan 文档 schema 补 Plan Review History + Pack Execution Manifest

### Goal behavior
让 plan 文档自足到 Worker 自治执行：
- **Plan Review History**：让 plan-executor / Plan Implementation Review reviewer 知道已审过的角度
- **Pack Execution Manifest**：Worker 按 Manifest 快速定位每个 Pack 的章节锚点（避免线性扫描），Coordinator 验证三方一致（Manifest / Pack 主体 / execution-state.packs keys）

### Implementation tasks
1. Read `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`，定位 Plan Header 旁
2. 追加 Plan Review History 模板（结构同 Pack 2.1 design Review History）
3. 追加 Pack Execution Manifest 模板：

```markdown
## Pack Execution Manifest

Worker 入口查询表。每行：pack_id → 章节锚点 + 关键字段索引。

| pack_id | title | anchor | risk | dependencies | owned_files (核心) |
| --- | --- | --- | --- | --- | --- |
| 1.1 | <title> | `#pack-1-1-<slug>` | normal | — | `path/to/file.py` |
| 1.2 | <title> | `#pack-1-2-<slug>` | normal | 1.1 | `path/to/other.py` |

（由 plan-writer 手写或构建脚本生成；详见 generate-pack-manifest.sh）
```

4. 在 plan-writer 自检列表加：「Plan Review History section 存在」、「Pack Execution Manifest pack_id 与 Pack 主体 `### Task Pack N.M` 编号一致」

### Owned files
- Edit: `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`

### Read first
- `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`（当前结构）
- 已有 plan 文档（如有）

### Acceptance criteria
- [x] methodology 模板含 Plan Review History section
- [x] methodology 模板含 Pack Execution Manifest section
- [x] 自检列表更新
- [x] `build.sh --check` 通过

### Verification commands
- `grep -q 'Plan Review History' plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md` → Expected: exit 0
- `grep -q 'Pack Execution Manifest' plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags
normal（Worker 自治依赖此 schema；缺失会触发 NEEDS_PLAN_REVISION）

### Out of scope
- 不补现有 plan 文件（Plan 005 Worker handbook 写 fallback：缺 Manifest → 线性扫描 + 警告）

---

## Pack 2.4：workflow-state schema 扩展 review_dispositions[]

### Goal behavior
让每条 disposition 记录可绑定到 plan（targeted re-review 收窄 scope）和 Coordinator 亲验证据（避免 repair worker 用未验 evidence）。

### Implementation tasks
1. Read `plugin/state-schema/workflow-state-v1.json`，定位 `review_dispositions.items.properties`
2. 追加 2 个 optional 字段：
   - `plan_id`: `{"type": ["string", "null"]}`
   - `coordinator_verified_evidence`: `{"type": ["string", "null"]}`
3. **不 bump schema 版本号**（向后兼容）
4. 跑 schema 验证：`python3 -c "import json; json.load(open('plugin/state-schema/workflow-state-v1.json'))"`

### Owned files
- Edit: `plugin/state-schema/workflow-state-v1.json`

### Read first
- `plugin/state-schema/workflow-state-v1.json`（现状）

### Acceptance criteria
- [x] schema 含 plan_id + coordinator_verified_evidence 可选字段
- [x] JSON 合法
- [x] 老 state 文件可被新 schema 验证（向后兼容）

### Verification commands
- `python3 -c "import json; s=json.load(open('plugin/state-schema/workflow-state-v1.json')); assert 'plan_id' in s['properties']['review_dispositions']['items']['properties']" ` → Expected: exit 0
- `python3 -c "import json; s=json.load(open('plugin/state-schema/workflow-state-v1.json')); assert 'coordinator_verified_evidence' in s['properties']['review_dispositions']['items']['properties']"` → Expected: exit 0

### Risk flags
normal

---

## Pack 2.5：execution-state schema 扩展 plans[N]

### Goal behavior
让 plans[N] 容纳 Worker 自治模式：worker_agent_id（plan-level 派发追踪）、pack_summary（reviewer 自跑 jq 替代 Coordinator 临场拼装）、current_plan_id（顶级，已被 state.sh 使用但 schema 未声明）。

### Implementation tasks
1. Read `plugin/state-schema/execution-state-v1.json`，定位 `plans.additionalProperties.properties`
2. 追加字段：
   - `worker_agent_id`: `{"type": ["string", "null"]}`
   - `pack_summary`: `{"type": "array", "items": {"type": "object"}}`（聚合视图，下游 reviewer 用）
   - `start_commit` / `end_commit`：已在 hook 中使用，schema 显式声明
3. 顶级加 `current_plan_id`：`{"type": ["string", "null"]}`
4. JSON 验证

### Owned files
- Edit: `plugin/state-schema/execution-state-v1.json`

### Read first
- `plugin/state-schema/execution-state-v1.json`
- `plugin/hooks/track-execution-state.sh`（确认字段使用方式）

### Acceptance criteria
- [x] schema 含上述字段
- [x] JSON 合法
- [x] 老 state 兼容

### Verification commands
- `python3 -c "import json; s=json.load(open('plugin/state-schema/execution-state-v1.json')); ap=s['properties']['plans']['additionalProperties']['properties']; assert 'worker_agent_id' in ap and 'pack_summary' in ap"` → Expected: exit 0

### Risk flags
normal

---

## Pack 2.6：dispatch-envelope schema +plan_id

### Goal behavior
DISPATCH_ENVELOPE 加 plan_id 字段（与 pack_id 互斥），让 hook 能区分 plan-level 首发 vs pack-level repair。本 Pack 仅 schema 声明，hook 解析逻辑在 Plan 005。

### Implementation tasks
1. Read `plugin/state-schema/dispatch-envelope-v1.json`
2. 追加 `plan_id` 字段（optional, string\|null）
3. 在描述中说明语义："execution phase 下要么 pack_id 要么 plan_id 非 null。pack_id=null + plan_id=<id> 表示 plan-level worker 首发"
4. 同步 build template `control-envelope.md.tmpl` 的字段列表

### Owned files
- Edit: `plugin/state-schema/dispatch-envelope-v1.json`
- Edit: `plugin/build/templates/control-envelope.md.tmpl`

### Read first
- `plugin/state-schema/dispatch-envelope-v1.json`
- `plugin/build/templates/control-envelope.md.tmpl`

### Acceptance criteria
- [x] schema +plan_id
- [x] template 字段列表同步
- [x] `build.sh --apply` + `--check` 通过

### Verification commands
- `python3 -c "import json; s=json.load(open('plugin/state-schema/dispatch-envelope-v1.json')); assert 'plan_id' in s['properties']"` → Expected: exit 0
- `grep -q 'plan_id' plugin/build/templates/control-envelope.md.tmpl` → Expected: exit 0

### Risk flags
trivial（仅 schema 声明，运行时解析在 Plan 005）

### Contract anchors
- Surface: dispatch-envelope-v1.json +plan_id
- Provider: 本 Pack
- Consumer: Plan 005（parse-envelope.sh, validate-pack-dispatch.sh, agent-return-handler.sh）

---

## Pack 2.7：pack-returns JSON schema 新增

### Goal behavior
为 Worker 写入的 pack-returns/*.json 提供 schema 约束，让 hook 聚合 pack_summary 时格式可靠。

### Implementation tasks
1. 新建 `plugin/state-schema/pack-returns-v1.json`，定义：
   ```json
   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "type": "object",
     "required": ["pack_id", "verdict"],
     "properties": {
       "pack_id": {"type": "string"},
       "verdict": {"enum": ["pass", "needs repair", "blocked", "needs context"]},
       "changed_files": {"type": "array", "items": {"type": "string"}},
       "open_items": {"type": "array", "items": {"type": "object", "properties": {"tag": {"enum": ["out-of-scope", "needs-evaluation", "bug"]}, "summary": {"type": "string"}}}},
       "concerns": {"type": ["string", "null"]}
     }
   }
   ```
2. 在 `verify-maturity.sh` 加一条检查：schema 文件存在
3. JSON 验证

### Owned files
- Create: `plugin/state-schema/pack-returns-v1.json`

### Read first
- 现有 pack-executor.md 中 pack-returns 写入格式
- 其他 state schema 文件作 reference

### Acceptance criteria
- [x] schema 文件存在且 JSON 合法
- [x] schema 覆盖 pack-returns 当前所有字段

### Verification commands
- `test -f plugin/state-schema/pack-returns-v1.json` → Expected: exit 0
- `python3 -m json.tool plugin/state-schema/pack-returns-v1.json >/dev/null` → Expected: exit 0

### Risk flags
trivial

---

## Pack 2.8：state.sh 新增 / 扩展子命令

### Goal behavior
state.sh 加 5 项能力：
1. `review-history append --doc design|plan --slug X [--plan-id N] --round R --verdict V --gotchas "..."` 自动 Edit 文档
2. `business-summary append --slug X --plan-id N --summary "..."`
3. `agent-id set/get` 加 `--plan-id`（与 `--pack-id` 互斥）
4. `disposition record/append` 加 `--plan-id` + `--coordinator-verified-evidence`
5. `validate` 强制 accepted disposition 必须有 coordinator_verified_evidence

### Implementation tasks
1. Read `plugin/scripts/state.sh` 现有子命令结构
2. 实现 `cmd_review_history_append`：参数解析 + Edit 目标文档（design.md 或 plan.md）+ jq update workflow-state
3. 实现 `cmd_business_summary_append`：同上 + Edit design.md Business Summary Inputs section
4. 扩展 `cmd_agent_id_set` / `cmd_agent_id_get`：参数加 `--plan-id`，与 `--pack-id` 二选一互斥；写入 `.plans[plan_id].worker_agent_id`
5. 扩展 `cmd_disposition_record`：参数 `--plan-id` 写入 `review_dispositions[].plan_id`；`--coordinator-verified-evidence` 写入对应字段
6. 扩展 `cmd_validate`：检查 accepted disposition 缺 coordinator_verified_evidence 时 BLOCKED
7. 新增 state-lock 保护所有写入

### Owned files
- Edit: `plugin/scripts/state.sh`

### Read first
- `plugin/scripts/state.sh`（当前结构）
- `plugin/scripts/lib/state-lock.sh`
- `plugin/state-schema/workflow-state-v1.json`（Pack 2.4 已扩展）
- `plugin/state-schema/execution-state-v1.json`（Pack 2.5 已扩展）

### Acceptance criteria
- [x] 5 项能力全部可用
- [x] state.sh 单元测试通过（含新子命令 fixture）
- [x] state-lock 正确保护

### Verification commands
- `bash plugin/scripts/state.sh review-history append --help` → Expected: 显示用法
- `bash plugin/scripts/state.sh business-summary append --help` → Expected: 显示用法
- `bash plugin/scripts/state.sh agent-id set --plan-id 001 --agent-id test --run-id <test-run>` → Expected: 写成功（需准备 fixture）
- `bash plugin/scripts/tests/test_state.sh` → Expected: 全部通过（新 fixture + 旧 fixture）

### Risk flags
**high-risk**（state.sh 是核心 CLI；改动影响所有调用方）

### Dependencies
- 2.4, 2.5（schema 必须先扩展）

---

## Pack 2.9：hook complete-review-dispatch 自动 append Review History

### Goal behavior
当 codex review 完成（result 命令成功）且 gate 名匹配 `design-review-*` / `plan-review-*` 时，自动调用 `state.sh review-history append` 写入对应文档。避免 Coordinator 漏写。

### Implementation tasks
1. Read `plugin/scripts/complete-review-dispatch.sh`（注意：是 PostToolUse hook 还是 Coordinator 调用脚本？确认调用语义）
2. 在脚本末尾加 gate 模式匹配分支：
   - `design-review-*` → `state.sh review-history append --doc design --slug <slug> --round <N> --verdict <V>`
   - `plan-review-*` → `state.sh review-history append --doc plan --slug <slug> --plan-id <N> --round <N> --verdict <V>`
3. verdict 和 gotchas 从 review-result 文件解析（可选；缺则记 verdict 为空，留 Coordinator 后续补 gotchas）

### Owned files
- Edit: `plugin/scripts/complete-review-dispatch.sh`

### Read first
- `plugin/scripts/complete-review-dispatch.sh`
- `plugin/scripts/state.sh`（确认 review-history append 调用契约）

### Acceptance criteria
- [x] 脚本对 design-review-* / plan-review-* 自动调用 state.sh
- [x] 不影响其他 gate 名
- [x] 测试通过

### Verification commands
- `grep -q 'review-history append' plugin/scripts/complete-review-dispatch.sh` → Expected: exit 0
- 单元测试：模拟 design-review-1 gate 完成 → Review History 出现新行

### Risk flags
normal

### Dependencies
- 2.1（design schema 必须有 section）
- 2.3（plan schema 必须有 section）
- 2.8（state.sh review-history append 必须就绪）

---

## Pack 2.10：hook track-execution-state 聚合 pack_summary

### Goal behavior
Plan 全部 Pack committed 后，自动聚合 pack-returns/*.json 到 `execution-state.plans[N].pack_summary`，让 reviewer 自跑 jq 读取，替代 Coordinator 临场拼装 Pack summary 表。

### Implementation tasks
1. Read `plugin/hooks/track-execution-state.sh`，定位 PLAN_DONE 检测逻辑
2. 在 PLAN_DONE 分支加：扫描 `pack-returns/<run_id>/` 下属于该 plan 的所有 *.json，聚合为数组写入 `execution-state.plans[N].pack_summary`
3. 验证 jq 写入幂等
4. 跑现有 hook 测试

### Owned files
- Edit: `plugin/hooks/track-execution-state.sh`

### Read first
- `plugin/hooks/track-execution-state.sh`（PLAN_DONE 逻辑）
- `plugin/state-schema/execution-state-v1.json`（Pack 2.5 schema）
- `plugin/state-schema/pack-returns-v1.json`（Pack 2.7）

### Acceptance criteria
- [x] PLAN_DONE 时 pack_summary 写入
- [x] 幂等
- [x] 现有测试不破

### Verification commands
- 单元测试：mock plan 完成 → execution-state 中 pack_summary 非空数组

### Risk flags
normal

### Dependencies
- 2.5, 2.7

---

## Pack 2.11：构建脚本 generate-pack-manifest.sh

### Goal behavior
让 plan-writer 不必手写 Pack Execution Manifest——构建脚本扫描 plan 主体 `### Task Pack N.M` 锚点自动生成 Manifest section。也作为 Coordinator 校验工具（三方对账）。

### Implementation tasks
1. 新建 `plugin/build/generate-pack-manifest.sh`
2. 实现：
   - 输入：plan 文件路径
   - 扫描 `### Task Pack N.M：<title>` 锚点
   - 提取每个 Pack 的 owned files / risk / dependencies（从 Pack 主体字段）
   - 生成或更新 plan 文件中的 `## Pack Execution Manifest` section
3. 支持 `--check` 模式（不修改文件，仅校验 Manifest 与 Pack 主体一致）
4. 加到 `build.sh` 的 build pipeline（可选 step）或单独 CLI 工具

### Owned files
- Create: `plugin/build/generate-pack-manifest.sh`

### Read first
- `plugin/build/build.sh`（pipeline 风格参考）
- `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`（Manifest 模板格式）

### Acceptance criteria
- [x] 脚本可用：`bash plugin/build/generate-pack-manifest.sh <plan.md>` 生成/更新 Manifest
- [x] `--check` 模式可校验
- [x] 对本计划文档（plan-level-worker-autonomy 系列）跑 check 通过

### Verification commands
- `test -x plugin/build/generate-pack-manifest.sh` → Expected: exit 0
- `bash plugin/build/generate-pack-manifest.sh --check docs/orchestrate/plans/2026-05-28-plan-level-worker-autonomy/002-document-schema-and-enforcement.md` → Expected: exit 0

### Risk flags
normal

### Dependencies
- 2.3（schema 模板）

---

## Pack 2.12：R1 原子改造 — cross-plan-contract-map 迁移

### Goal behavior
**最高风险 Pack**。`cross-plan-contract-map.md` 内容前移到 design.md `## Cross-Plan Contract Anchors` section。同时 3 处硬编码 reader 路径同步改写。必须原子（一次完成所有改动），中间状态破坏 workflow。

### Implementation tasks
1. **Step 1**：Read `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` L56 附近
2. **Step 2**：Read `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` L92, L112
3. **Step 3**：Read `plugin/skills/orchestrate-final-review/references/final-review-angles.md` L125, L182
4. **Step 4**：Read `plugin/skills/orchestrate-final-review/references/final-review-preconditions.md` L15
5. **Step 5**：把 plan-gates.md Step 11 改写：
   - 旧：「生成 `cross-plan-contract-map.md`」
   - 新：「写入 design.md `## Cross-Plan Contract Anchors` section（使用 `state.sh` 或直接 Edit）」
6. **Step 6**：3 处 reader 路径同步改：
   - 旧：`cross-plan-contract-map.md`
   - 新：`design.md#cross-plan-contract-anchors`
7. **Step 7**：如已有 cross-plan-contract-map.md 存在文件（本仓库 `docs/orchestrate/plans/2026-05-28-plan-level-worker-autonomy/cross-plan-contract-map.md` 是本计划自己的产物，不要删），但 SKILL/reference 中提示语必须改
8. **Step 8**：fallback 期间，3 个 reader 加 fallback 注释「老 run 若仍引用 cross-plan-contract-map.md 文件，请人工迁移」

### Owned files
- Edit: `plugin/skills/orchestrate-plan-writing/references/plan-gates.md`
- Edit: `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
- Edit: `plugin/skills/orchestrate-final-review/references/final-review-angles.md`
- Edit: `plugin/skills/orchestrate-final-review/references/final-review-preconditions.md`

### Read first
- 上述 4 个文件
- `plugin/skills/orchestrate-discovery/references/discovery-design-document.md`（Pack 2.1 已加 section）

### Acceptance criteria
- [x] plan-gates.md Step 11 不再要求生成独立文件
- [x] 3 处 reader 路径全部改为 design.md#cross-plan-contract-anchors
- [x] `grep -rn 'cross-plan-contract-map.md' plugin/skills/` 仅在 fallback 注释或本 Plan 文档中出现
- [x] `bash plugin/scripts/run-all-tests.sh` 通过

### Verification commands
- `! grep -rq 'Read.*cross-plan-contract-map.md' plugin/skills/` → Expected: exit 0（除 fallback 注释外）
- `grep -rq 'cross-plan-contract-anchors' plugin/skills/orchestrate-plan-writing/references/ plugin/skills/orchestrate-final-review/references/` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全部通过

### Risk flags
**high-risk**（R1 阻塞性原子改造；任何 reader 漏改 → broken read）

### Dependencies
- 2.1（design schema 必须有 section）

### Out of scope
- 不动本 Plan 自己的 `cross-plan-contract-map.md`（这是本计划的中间产物，不是被 reader 引用的旧文件）

---

## Pack 2.13：hook validate-pack-manifest.sh 三方对账（设计 R2 + 9 项 enforcement #7）

### Goal behavior

设计文档 R2 列为阻塞性风险：Pack Execution Manifest pack_id 必须与 (a) plan 文档 `### Task Pack N.M` 主体 (b) execution-state.plans[N].packs keys (c) Worker commit 中的 Pack N.M ID **三方一致**。任一偏移 → Worker 跑错 Pack 或漏跑。本 Pack 实现 PreToolUse Agent hook，派 pack-executor / complex-pack-executor 之前自动三方对账，不一致 → BLOCKED。

### Implementation tasks

1. 创建 `plugin/hooks/validate-pack-manifest.sh`
2. 触发：PreToolUse Agent matcher `(pack-executor|complex-pack-executor)`
3. 解析：
   - envelope.plan_id + envelope.run_id
   - plan 文档路径：`docs/orchestrate/plans/<slug>/<plan_id>-*.md`
4. 三方对账：
   - grep `## Pack Execution Manifest` 段提取 pack_id 列表（A）
   - grep `### Task Pack N.M` 主体提取 pack_id 列表（B）
   - jq 读 `execution-state.plans[plan_id].packs` keys（C）
   - 必须 A == B；C 必须是 A 的子集（首派时 C 为空也通过）
5. 失败时输出明确诊断：「Manifest 中 Pack 1.3 未出现在主体」/「主体 Pack 2.1 未出现在 Manifest」
6. 调用 `generate-pack-manifest.sh --check` 作为另一层校验
7. 测试 fixture：pass / fail 两路径

### Owned files

- Create: `plugin/hooks/validate-pack-manifest.sh`
- Edit: `plugin/hooks/hooks.json`（注册 hook，Plan 005 Pack 5.14 统一处理 hook 注册，本 Pack 仅创建文件 + 单测）
- Create: `tests/hooks/validate-pack-manifest.bats`

### Read first

- `plugin/hooks/validate-pack-dispatch.sh`（参考 hook 风格）
- `plugin/build/generate-pack-manifest.sh`（Pack 2.11）
- `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`（Manifest schema）

### Acceptance criteria

- [x] hook 存在且可执行
- [x] 三方一致 → allow
- [x] Manifest 缺 pack → BLOCKED + 诊断
- [x] 主体缺 pack → BLOCKED + 诊断
- [x] execution-state 含 Manifest 外的 pack → BLOCKED + 诊断
- [x] 测试覆盖

### Verification commands

- `test -x plugin/hooks/validate-pack-manifest.sh` → Expected: exit 0
- `bash tests/hooks/validate-pack-manifest.bats` → Expected: exit 0
- `shellcheck plugin/hooks/validate-pack-manifest.sh` → Expected: exit 0

### Risk flags

normal（新 hook，需保证不影响现有 pack-executor 派发）

### Dependencies

- 2.3（Manifest schema 必须存在）
- 2.5（execution-state schema）
- 2.11（generate-pack-manifest.sh）

---

## Pack 2.14：state-transition-matrix.md 同步 plan-level 流转（调研 D）

### Goal behavior

调研 D 明确指出 state-transition-matrix 文档需要补 plan-level 4 个新流转：`Coordinator: pending → in_progress`、`agent-return-handler: in_progress → returned`、`Coordinator: returned → review_pending`、`track-execution-state: returned → committed`（保留 per-pack）。同步更新 state.sh 内的 `TRANSITION_MATRIX` 数组。

### Implementation tasks

1. Read `plugin/scripts/state-transition-matrix.md`（或同等位置文档）
2. 加 4 条 plan-level 流转条目
3. Read `plugin/scripts/state.sh` 找 `TRANSITION_MATRIX` 数组
4. 同步加 4 条 transition 规则
5. 单测：跑 `state.sh transition --from pending --to in_progress --actor coordinator --plan-id 001` 应允许

### Owned files

- Edit: `plugin/scripts/state-transition-matrix.md`（或同等文档）
- Edit: `plugin/scripts/state.sh`

### Acceptance criteria

- [x] 文档含 4 条新流转
- [x] state.sh TRANSITION_MATRIX 同步
- [x] 单测通过

### Verification commands

- `grep -c 'plan-level' plugin/scripts/state-transition-matrix.md` → Expected: ≥ 1
- `bash plugin/scripts/tests/test_state.sh` → Expected: exit 0

### Risk flags

trivial

### Dependencies

- 2.5

---

## Plan-level 验证

```bash
# Schema
python3 -m json.tool plugin/state-schema/workflow-state-v1.json >/dev/null
python3 -m json.tool plugin/state-schema/execution-state-v1.json >/dev/null
python3 -m json.tool plugin/state-schema/dispatch-envelope-v1.json >/dev/null
python3 -m json.tool plugin/state-schema/pack-returns-v1.json >/dev/null

# state.sh
bash plugin/scripts/state.sh review-history append --help
bash plugin/scripts/state.sh business-summary append --help

# Hooks
bash plugin/scripts/run-all-tests.sh

# Build
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/build/generate-pack-manifest.sh --check docs/orchestrate/plans/2026-05-28-plan-level-worker-autonomy/002-document-schema-and-enforcement.md

# Maturity
bash plugin/scripts/verify-maturity.sh

# R1 原子改造验证
! grep -rq 'Read.*cross-plan-contract-map.md' plugin/skills/
```

全部通过 → Plan 002 完成。

## Plan Review History

（待 Plan Implementation Review 后追加）
