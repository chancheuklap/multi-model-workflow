# Plan 006：Phase 5 merge-brief 中介文档 + Phase 6 测试/maturity 同步

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（merge-brief schema + maturity 校验段）
**调研依据**: 调研 F 「multi-pr-merge skill 改造」、设计文档 merge-brief 9 段 schema
**Blocked by**: Plan 005（Worker Loop / hook 全部就绪后才能整体校验）
**Risk profile**: normal（merge-brief 是新文档但单一职责；maturity 校验是聚合）
**Worker type**: `pack-executor`

## Plan Goal Behavior

1. **Phase 5**：在 `orchestrate-multi-pr-merge/` 引入 merge-brief 中介文档（唯一新增的合成视角文档），含 9 段固定 schema，作为多 PR 合并时的"合成模型"载体。
2. **Phase 6**：把所有新 schema 字段 / 新 hook / 新 state.sh 子命令 / 新 reference 反转 纳入 `verify-maturity.sh` 校验；新增 schema 索引文档；run-all-tests 全面跑过。

## Plan Acceptance Criteria

- [ ] `merge-brief-v1.json` schema 定义（9 段，严格对齐设计 §merge-brief Schema：Meta / 参与 PR / 正确状态模型 / Conflict Findings / RCA / Resolution Log / Integration Review Pointers / Open Items / Verdict）
- [ ] 决策 8 写入 schema 注释（per-run conflict_id / 追加 PR 视为新 run / 默认不归档）
- [ ] `state.sh merge-brief init/stage/verify` 3 helper（设计 9 项 enforcement #6）
- [ ] `validate-multi-pr-dispatch.sh` 新 hook（强制 dispatch prompt 引用 merge-brief 路径）
- [ ] `review-dispatch.md.tmpl` 追加 targeted re-review scope 收窄段（设计 Phase 6 通用收尾）
- [ ] 3 个 multi-pr handbook（explorer / worker / integration-review）
- [ ] `orchestrate-multi-pr-merge/references/merge-brief-template.md` 模板文件
- [ ] `orchestrate-multi-pr-merge/SKILL.md` 加 merge-brief 写作指针 + workflow-state.cursor.reference 写入指引
- [ ] workflow-state.cursor.reference 接受 merge-brief 路径（schema 已 Plan 002 加，本 Plan 校验消费）
- [ ] `verify-maturity.sh` 校验新增 schema 字段全部就绪（Plan 002 加的 4 条 + Plan 005 加的 2 条）
- [ ] `verify-maturity.sh` 校验新 hook 全部就位 + 旧 hook 全部清除
- [ ] `verify-maturity.sh` 校验所有 dispatch reference 含 Self-Read Protocol
- [ ] `verify-maturity.sh` 校验所有 SKILL.md 行数符合 Plan 003 目标
- [ ] `run-all-tests.sh` 通过
- [ ] 新增端到端测试：Discovery → Plan Writing → Execution → Final Review 全链路 mock fixture
- [ ] 文档：plugin/architecture-draft.md 更新 Plan-level Worker 段
- [ ] 版本号 bump：plugin.json + marketplace.json 同步

## File / Responsibility Map

| 文件 | 改动类型 |
| --- | --- |
| `plugin/state-schema/merge-brief-v1.json` | 新增 |
| `plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md` | 新增 |
| `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` | 加 merge-brief 写作段 |
| `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-merge-dispatch.md` | 加 merge-brief 读写指引（Plan 004 反转过的视角） |
| `plugin/scripts/verify-maturity.sh` | 扩 6 类校验 |
| `tests/integration/full-workflow-e2e.bats` | 新增 |
| `plugin/architecture-draft.md` | 更新 Plan-level Worker 段 |
| `plugin/.claude-plugin/plugin.json` | bump 版本 |
| `.claude-plugin/marketplace.json` | bump 版本 |

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files |
| --- | --- | --- | --- | --- |
| 6.1 | merge-brief-v1.json schema 定义 | normal | — | `merge-brief-v1.json` |
| 6.2 | merge-brief-template.md 写作模板 | normal | 6.1 | `merge-brief-template.md` |
| 6.3 | orchestrate-multi-pr-merge SKILL.md / dispatch 接入 merge-brief | normal | 6.1, 6.2 | 2 个文件 |
| 6.4 | workflow-state.cursor.reference 接收 merge-brief 路径消费校验 | normal | Plan 002 cursor 字段已加 | `state.sh cursor`, hook |
| 6.5 | verify-maturity.sh 扩 6 类校验 | normal | Plan 002-005 全完成 | `verify-maturity.sh` |
| 6.6 | full-workflow-e2e 集成测试 | normal | 6.5 | `tests/integration/full-workflow-e2e.bats` |
| 6.7 | architecture-draft.md 更新 + 版本号 bump | trivial | 6.1-6.6 | 3 个文件 |
| 6.8 | state.sh merge-brief init/stage/verify 3 helper | normal | 6.1 | `state.sh` |
| 6.9 | validate-multi-pr-dispatch.sh 新 hook | normal | 6.1, 6.3 | 新文件 |
| 6.10 | review-dispatch.md.tmpl 追加 targeted re-review 收窄 scope 段 | trivial | — | template |
| 6.11 | 3 个 multi-pr handbook 新增（explorer / worker / integration-review）| normal | 6.1 | 新文件 ×3 |

---

## Pack 6.1：merge-brief-v1.json schema 定义

### Goal behavior

定义 merge-brief 的 9 段 JSON schema。

### Implementation tasks

1. Read `plugin/state-schema/`（参考样式）
2. 创建 `plugin/state-schema/merge-brief-v1.json`，**严格对齐设计文档 §merge-brief Schema（L608-621）的 9 段**：
   - **§1 Meta** META JSON 头：`schema_version, run_id, slug, created_at, last_updated_at, current_stage (enum: init|conflict_discovery|rca|repair|integration_review|merging|complete), integration_review_gate`
   - **§2 参与 PR 表** `pr_inventory[]`: `{pr, branch, big_design_path, big_plan_path, single_pr_design_path, single_pr_plan_path, final_review_verdict, core_behavior}`
   - **§3 合并后正确状态模型**：`behaviors[]`, `contract_surfaces[]` (surface, type, provider_pr, consumer_prs, modification_direction), `file_cross_matrix[][]`, `merge_order[]`, `risk_hotspots[]`
   - **§4 Conflict Findings**: per-conflict 块 `{conflict_id: "C-001", type: enum, involved_prs[], files[], description, severity, classification: simple|complex-clear|systemic, route: coordinator-fix|worker-fix|analyst-then-worker, status: open|rca-in-progress|repair-in-progress|resolved|escalated, discovered_by, discovered_at}`
   - **§5 Root Cause Analysis**: per-systemic-conflict `{analyst_agent_id, resolution, root_cause_type, root_cause_detail, fix_direction, target_pr, related_conflicts[], design_impact, regression_risk}`
   - **§6 Resolution Log**: `{owner, repair_round, changed_files, summary, verification: {commands, tests, coordinator_verified, evidence}, status_after, resolved_at}`
   - **§7 Integration Review Pointers**: `{base_diff_range, contract_surfaces_to_audit[], resolved_conflicts_summary[], per_pr_final_review_verdict_refs[], regression_focus_files[], integration_review_gate_name}`
   - **§8 Open Items / Out-of-scope**
   - **§9 Verdict**: enum `MERGE_COMPLETE|NEEDS_DISCOVERY|NEEDS_USER_DECISION|BLOCKED` + 证据指针
3. **决策 8 写入 schema 注释**：
   - `conflict_id` per-run（C-001 起编，跨 run 不重用）
   - 追加 PR 视为新 run，不在同 brief 增量
   - 默认不归档到 `docs/orchestrate/merge-briefs/`，随 worktree 清理一起删
4. schema_version = "1"
5. 加 README 索引

### Owned files

- Create: `plugin/state-schema/merge-brief-v1.json`
- Edit: `plugin/state-schema/README.md`

### Acceptance criteria

- [ ] schema JSON 合法
- [ ] 含 9 段字段
- [ ] schema_version = "1"

### Verification commands

- `python3 -m json.tool plugin/state-schema/merge-brief-v1.json > /dev/null` → Expected: exit 0
- `jq -r '.properties | keys | length' plugin/state-schema/merge-brief-v1.json` → Expected: ≥ 10 (含 schema_version)

### Risk flags

normal

---

## Pack 6.2：merge-brief-template.md 写作模板

### Goal behavior

提供 multi-pr-merge agent 写 merge-brief 时使用的 Markdown 模板，9 段对应 schema。

### Implementation tasks

1. 创建 `plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md`
2. 9 段 Markdown 占位符 + 写作指引（每段写什么 / 不写什么 / 与 design.md / plan.md 边界）
3. 顶部加 frontmatter 区指引：`run_id`, `created_at`, `prs[]`
4. 模板末尾示例段（mock 一个迷你 merge-brief）

### Owned files

- Create: `plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md`

### Read first

- 设计文档 merge-brief 段
- cross-plan-contract-map.md 中 merge-brief 与现有文档的边界表

### Acceptance criteria

- [ ] 模板含 9 段
- [ ] 每段含写作指引 + 边界说明
- [ ] 末尾含示例

### Verification commands

- `grep -c '^## ' plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md` → Expected: ≥ 9

### Risk flags

normal

### Dependencies

- 6.1

---

## Pack 6.3：orchestrate-multi-pr-merge SKILL.md / dispatch 接入 merge-brief

### Goal behavior

SKILL.md 加 merge-brief 写作流程段：合并开始时 multi-pr-merge agent 自读 PR 清单 → 用 merge-brief-template.md 起草 → 写入 `.claude/multi-model-workflow/merge-brief-<run_id>.md` → workflow-state.cursor.reference 指向该路径 → 后续 review-prompts 等引用 merge-brief 路径。

dispatch reference（Plan 004 已反转视角）需加段：merge agent 自读时第一步起草 merge-brief。

### Implementation tasks

1. Read `plugin/skills/orchestrate-multi-pr-merge/SKILL.md`
2. 加段「## merge-brief 写作流程」（指针 + workflow-state 写入指引）
3. Read `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-merge-dispatch.md`
4. 在 dispatch reference 顶部 Self-Read Protocol 加一步：起草 merge-brief
5. `bash plugin/build/build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-multi-pr-merge/SKILL.md`
- Edit: `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-merge-dispatch.md`

### Acceptance criteria

- [ ] SKILL.md 含 merge-brief 写作流程段
- [ ] dispatch reference Self-Read Protocol 含 merge-brief 起草步骤
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'merge-brief' plugin/skills/orchestrate-multi-pr-merge/SKILL.md` → Expected: exit 0
- `grep -q 'merge-brief' plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-merge-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal

### Dependencies

- 6.1, 6.2

---

## Pack 6.4：workflow-state.cursor.reference 接收 merge-brief 路径消费校验

### Goal behavior

Plan 002 已加 workflow-state.cursor.reference 字段。本 Pack 校验 state.sh cursor 子命令和相关 hook 能正确写入 / 读出 merge-brief 路径。

### Implementation tasks

1. Read `plugin/scripts/state.sh` cursor 子命令
2. 确认 `state.sh cursor --reference <path>` 可写
3. 加单测：写入 `.claude/multi-model-workflow/merge-brief-<run_id>.md` → 读回一致
4. Hook（如 review-prompts 生成）确认能解析 cursor.reference 并 include 到 review prompt

### Owned files

- Edit/单测: `plugin/scripts/state.sh`
- Create: `tests/state/cursor-reference.bats`

### Acceptance criteria

- [ ] state.sh cursor --reference 接收路径
- [ ] 单测覆盖写入 + 读回
- [ ] hook 消费链路正常

### Verification commands

- `bash plugin/scripts/state.sh cursor --reference .claude/multi-model-workflow/merge-brief-test.md` → Expected: exit 0
- `bash tests/state/cursor-reference.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Plan 002 cursor 字段

---

## Pack 6.5：verify-maturity.sh 扩 6 类校验

### Goal behavior

把所有 Plan 002-005 的产物纳入 `verify-maturity.sh`：
1. **Schema 字段就绪**：dispatch-envelope.plan_id / workflow-state.review_dispositions[].plan_id 等 6 字段
2. **新 hook 存在 + 旧 hook 已删**：validate-plan-dispatch / enforce-plan-commit 存在；validate-pack-dispatch / enforce-pack-commit 不存在
3. **state.sh 子命令存在**：agent-context-check / pack-progress / plan-complete / agent-id --plan-id / disposition --plan-id
4. **dispatch reference 视角反转**：6 个 reference 全含 Self-Read Protocol + Coordinator 端最小职责
5. **SKILL.md 瘦身完成**：orchestrate-execution ≤ 260 行 / plan-writing ≤ 220 / workflow ≤ 220
6. **worker-loop 锚点**：pack-executor.md + complex-pack-executor.md 含 BEGIN: worker-loop

### Implementation tasks

1. Read 当前 `plugin/scripts/verify-maturity.sh`
2. 在末尾新增 6 段校验函数
3. 每段失败时输出明确诊断 + 修复指引
4. 测试：跑通现状 → 应该全 pass

### Owned files

- Edit: `plugin/scripts/verify-maturity.sh`

### Read first

- 当前 verify-maturity.sh
- 所有 Plan 002-005 产物

### Acceptance criteria

- [ ] 新增 6 段校验
- [ ] 每段失败诊断清晰
- [ ] 在 Plan 002-005 全完成的前提下，verify-maturity.sh 全 pass

### Verification commands

- `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Plan 002, 003, 004, 005 全完成

---

## Pack 6.6：full-workflow-e2e 集成测试

### Goal behavior

构造一个 mock fixture，覆盖 Discovery → Plan Writing → Execution → Final Review → Multi-PR Merge 的全链路。每 phase 用 fixture state file 模拟前一 phase 输出，验证：
- 状态机转换正确
- 文档 schema 字段被正确写入 / 读出
- hook 链路触发正确
- Plan-level Worker dispatch / return / review 路由正确

### Implementation tasks

1. 创建 `tests/integration/full-workflow-e2e.bats`
2. fixture 目录 `tests/fixtures/full-workflow/`：
   - mock design.md（含 Cross-Plan Contract Anchors + Review History + Business Summary Inputs）
   - mock issue.md × 2
   - mock plan.md × 2（含 Pack Execution Manifest）
   - mock workflow-state.json
   - mock plan-return.json × 2
3. 顺序模拟：
   - Discovery 输出 → workflow-state.cursor 推进
   - Plan Writing 输出 → review_dispositions 加 Plan Review pass
   - Execution Plan 1 Worker dispatch → 模拟 SubagentStop → handler 处理 → review pass
   - Execution Plan 2 同上
   - Final Review pass
4. 每 phase 后断言 state schema 合法 + 关键字段写入

### Owned files

- Create: `tests/integration/full-workflow-e2e.bats`
- Create: `tests/fixtures/full-workflow/*`

### Acceptance criteria

- [ ] 全链路 e2e 跑通
- [ ] 每 phase 状态字段断言通过
- [ ] schema 校验通过

### Verification commands

- `bash tests/integration/full-workflow-e2e.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- 6.5

---

## Pack 6.7：architecture-draft.md 更新 + 版本号 bump

### Goal behavior

更新架构文档反映 Plan-level Worker 改造；同步 plugin.json + marketplace.json 版本号。

### Implementation tasks

1. Read `plugin/architecture-draft.md`
2. 更新「执行阶段调度粒度」段：由 Pack-level 改为 Plan-level Worker 自治
3. 更新「Worker Loop 合同」段（新增）
4. 更新「merge-brief 中介文档」段（新增）
5. 更新「Hook 链路」段：替换 validate-plan-dispatch / enforce-plan-commit
6. Read `plugin/.claude-plugin/plugin.json` 当前版本号
7. minor bump（如 1.2.0 → 1.3.0；本次是重大架构改造）
8. 同步更新 `.claude-plugin/marketplace.json`
9. `diff` 验证一致

### Owned files

- Edit: `plugin/architecture-draft.md`
- Edit: `plugin/.claude-plugin/plugin.json`
- Edit: `.claude-plugin/marketplace.json`

### Read first

- 当前 architecture-draft.md
- 当前 plugin.json + marketplace.json

### Acceptance criteria

- [ ] architecture-draft.md 反映 Plan-level Worker
- [ ] 两处版本号一致
- [ ] verify-maturity.sh 通过

### Verification commands

- `diff <(jq -r .version plugin/.claude-plugin/plugin.json) <(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)` → Expected: empty output
- `grep -q 'Plan-level Worker' plugin/architecture-draft.md` → Expected: exit 0
- `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0

### Risk flags

trivial

### Dependencies

- 6.1-6.6

---

## Pack 6.8：state.sh merge-brief init / stage / verify 3 helper

### Goal behavior

设计文档 §merge-brief Schema 末段 + 9 项 enforcement #6 明确：不做"全 schema CLI"避免回到模板填空反模式；只提供 3 个轻量 helper 管 META 结构化字段，内容由 multi-pr-merge agent 直接 Edit。

### Implementation tasks

1. Read `plugin/scripts/state.sh`
2. 加 `merge-brief init --run-id X --slug Y`：
   - 仅当 `${STATE_DIR}/merge-brief-<run_id>.md` 不存在时，按 merge-brief-template.md（Pack 6.2）写入文件
   - 文件 META 段填 schema_version=1, run_id, slug, created_at, current_stage=init
3. 加 `merge-brief stage --run-id X --stage S`：
   - 更新 META.current_stage（enum 校验）
   - 更新 META.last_updated_at
4. 加 `merge-brief verify --run-id X`：
   - 解析 META 完整性
   - 校验 §4 中所有 conflict status 自洽（resolved 必须有 §6 对应记录；rca-in-progress 必须有 §5 anaylst_agent_id 或挂起标记）
   - 不深度 lint 全部段（深度校验放 verify-maturity.sh C5）
5. 单测

### Owned files

- Edit: `plugin/scripts/state.sh`
- Create: `tests/state/merge-brief.bats`

### Read first

- 设计文档 §merge-brief Schema
- Plan 006 Pack 6.1 schema + Pack 6.2 template

### Acceptance criteria

- [ ] 3 个子命令存在
- [ ] init 幂等（已存在则保留不覆盖）
- [ ] stage 校验 enum
- [ ] verify 检测 META 缺失 / status 不自洽 → BLOCKED
- [ ] 不引入 conflict/rca/resolution CLI 操作（避免回到模板填空）

### Verification commands

- `bash plugin/scripts/state.sh merge-brief init --run-id test-r1 --slug test` → Expected: exit 0
- `bash plugin/scripts/state.sh merge-brief stage --run-id test-r1 --stage rca` → Expected: exit 0
- `bash plugin/scripts/state.sh merge-brief verify --run-id test-r1` → Expected: exit 0
- `bash tests/state/merge-brief.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- 6.1（schema 必须存在）

---

## Pack 6.9：validate-multi-pr-dispatch.sh 新 hook

### Goal behavior

调研 E §6.1：dispatch envelope 中 `phase=multi-pr-merge` 时强制校验 `${STATE_DIR}/merge-brief-<run_id>.md` 已存在 + META 与 envelope `repair_round` / `conflict_id` 一致。防止 dispatch 携带 paste 段反模式。

### Implementation tasks

1. 创建 `plugin/hooks/validate-multi-pr-dispatch.sh`
2. 触发：PreToolUse Agent matcher when envelope.phase == multi-pr-merge
3. 校验：
   - `${STATE_DIR}/merge-brief-<run_id>.md` 存在
   - META 可解析、`current_stage` 与 envelope `repair_round` 一致性（如 round=1 时 stage 不能是 init）
   - 若 envelope 含 `conflict_id`：§4 中存在该 id 且 status ≠ resolved
   - dispatch prompt body **强制包含字符串 `merge-brief-<run_id>.md`**（防 paste 反模式）
4. 失败 → BLOCKED + actionable error
5. hooks.json 注册
6. 测试 fixture

### Owned files

- Create: `plugin/hooks/validate-multi-pr-dispatch.sh`
- Edit: `plugin/hooks/hooks.json`
- Create: `tests/hooks/validate-multi-pr-dispatch.bats`

### Acceptance criteria

- [ ] hook 存在
- [ ] 4 个校验项全部实现
- [ ] grep 检查强制引用 merge-brief 路径
- [ ] 测试覆盖 pass / 4 类 fail 路径

### Verification commands

- `test -x plugin/hooks/validate-multi-pr-dispatch.sh` → Expected: exit 0
- `bash tests/hooks/validate-multi-pr-dispatch.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- 6.1, 6.3

---

## Pack 6.10：review-dispatch.md.tmpl 追加 targeted re-review 收窄 scope 段

### Goal behavior

设计文档 Phase 6 通用收尾 (L520-521) + 调研 C §6 第 3 段草稿（~160 字）：追加规则——当 envelope `review_intent=targeted-re-review` 且 `disposition_refs` 非空时，reviewer 只审 disposition_refs 中 finding 关联的 [Pack N.M] 对应 owned files；不重审全 Plan diff。新增问题超出 disposition scope → 列入 `Out of scope observations` 而非 finding。

### Implementation tasks

1. Read `plugin/build/templates/review-dispatch.md.tmpl`
2. 在末尾追加段（按调研 C §6 第 3 段草稿 ~160 字）：
   ```
   **Targeted re-review scope 收窄**：
   当 envelope `review_intent=targeted-re-review` 且 `disposition_refs` 非空时，reviewer 只审 disposition_refs 中 finding 关联的 [Pack N.M] 对应 owned files；
   不重审全 Plan diff。新增问题超出 disposition scope → 列入 `Out of scope observations` 而非 finding。
   ```
3. `build.sh --apply --plugin-dir plugin` 让 template 注入到 11 个 review skill 文件
4. `build.sh --check` 验证

### Owned files

- Edit: `plugin/build/templates/review-dispatch.md.tmpl`

### Acceptance criteria

- [ ] template 含 "Targeted re-review scope 收窄" 段
- [ ] `build.sh --apply` 后 11 个 review 锚点全部含该段
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Targeted re-review scope 收窄' plugin/build/templates/review-dispatch.md.tmpl` → Expected: exit 0
- `grep -rq 'Targeted re-review scope 收窄' plugin/skills/orchestrate-final-review/SKILL.md plugin/skills/orchestrate-execution/SKILL.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

trivial

---

## Pack 6.11：3 个 multi-pr handbook 新增

### Goal behavior

调研 E §8.2 明确：dispatch reference 反转后（Plan 004 Pack 4.9）explorer / worker / integration-reviewer 在 multi-pr-merge route 的角色规范需要落到独立 handbook 让 sub-agent 自读。

### Implementation tasks

1. 创建 `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md`：5 维冲突分析 + 严重程度 + 输出规范
2. 创建 `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md`：Scope / Acceptance 通用 + commit 规范 + verification
3. 创建 `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md`：7 review angles + calibration + return contract
4. 每个 handbook 顶部加 `## Self-Read Protocol`（envelope → merge-brief → 本 handbook → 执行）
5. Plan 004 Pack 4.9 中 dispatch reference 反转时引用这 3 个 handbook 路径

### Owned files

- Create: 3 个 handbook 文件

### Read first

- 现有 merge-conflict-discovery / merge-conflict-repair / merge-integration-review reference（提取角色规范）

### Acceptance criteria

- [ ] 3 个 handbook 文件存在
- [ ] 每个含 Self-Read Protocol
- [ ] 内容来自现有 merge-* reference 反转后剩余的角色规范

### Verification commands

- `test -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md` → Expected: exit 0
- `test -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md` → Expected: exit 0
- `test -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md` → Expected: exit 0
- `grep -l 'Self-Read Protocol' plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-*-handbook.md | wc -l` → Expected: 3

### Risk flags

normal

### Dependencies

- 6.1（merge-brief 路径出现在 Self-Read Protocol）

### 重要说明

这 3 个 handbook 是 **multi-pr-merge skill 的 reference 内部沉淀**，**不算用户拍板"不新增"原则违反**——它们是把现有 dispatch reference 中的角色规范段"搬家"到独立 handbook（与 Plan 003 SKILL.md 瘦身把内嵌段抽到 reference 是同类操作）。

---

## Plan-level 验证

```bash
bash plugin/build/build.sh --apply --plugin-dir plugin
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/run-all-tests.sh
bash plugin/scripts/verify-maturity.sh

# merge-brief 就绪
test -f plugin/state-schema/merge-brief-v1.json
test -f plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md

# 端到端
bash tests/integration/full-workflow-e2e.bats

# 版本号一致
diff <(jq -r .version plugin/.claude-plugin/plugin.json) <(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)
```

全部通过 → Plan 006 完成 → 整个 6-Plan 改造收口。

## Plan Review History

（待 Plan Implementation Review 后追加）
