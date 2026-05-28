# Plan 004：Phase 3 Dispatch Reference 反转（让 sub-agent 自读）

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（Document-as-Context 原则 + 推荐改造顺序 Phase 3）
**调研依据**: 调研 C 「Dispatch Reference 改造方案」
**Blocked by**: Plan 003（SKILL 已 lean，dispatch reference 成为唯一执行手册）
**Risk profile**: normal（语义改写，但不动状态机和数据流）
**Worker type**: `pack-executor`

## Plan Goal Behavior

把所有 `*-dispatch.md` reference 从「Coordinator 必须粘贴的内容片段」**反转**为「sub-agent 自读的执行手册」。Coordinator 端的 prompt 缩为 envelope + 文档路径 + handbook 路径指针；详细执行指南、QA 模板、verdict 体例由 sub-agent 第一步 `Read handbook` 自己拿。

**反转后命名**：含「dispatch」语义保留（向后兼容），但内部段落改写为「Sub-agent 自读手册」视角——主语从「Coordinator 必须 …」改为「Sub-agent（你）必须 …」。

## 决策注记（不新增中介文档）

按用户 USER #8 + 决策 9「不要新增更多东西」原则：本 Plan 反转 `bug-investigation-route.md` 与 `workflow-direct-repair.md` 时**不创建** `bug-seed-<run_id>.md` 与 `repair-brief-<run_id>.md` 中介文档模板。Coordinator 把用户原话 / 错误日志 / 偏差描述作为「运行时变量」inline 写到 dispatch envelope（类比 DISPATCH_ENVELOPE 字段），sub-agent 自读 envelope 即获取。这保留了 Document-as-Context 原则（不让 Coordinator 现场创作业务内容），同时避免新增模板文件。

## Plan Acceptance Criteria

- [x] **12 个** reference 文件完成视角反转（execution-worker-dispatch / execution-review-dispatch / plan-writer-dispatch / plan-review-dispatch / bug-investigation-route / workflow-direct-repair / design-review-angles / final-review-angles + 4 merge-* reference）
- [x] 每个 reference 顶部加 `## Self-Read Protocol` 段
- [x] 删除「Coordinator 必须把以下内容粘贴到 prompt」类指引
- [x] 删除与 SKILL.md 重复的流程概述
- [x] Coordinator 端 dispatch 调用 prompt 缩为 envelope + 路径
- [x] 每个 reference 末尾保留「Coordinator 端最小职责」段
- [x] design-review-angles / final-review-angles / merge-* 中所有 `<paste …>` 段已删
- [x] bug-investigation envelope 加 `bug_context` inline 字段语义说明 / direct-repair envelope 加 `repair_context` inline 字段
- [x] `bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [x] `bash plugin/scripts/run-all-tests.sh` 通过（37/37 suites）

**Plan 004 状态**：✅ 完成（2026-05-28，Worker agentId `ae6d29f73b4383903`，verdict=pass）

**Plan 文档校正**：Pack 4.5 (discovery-dispatch.md) + Pack 4.6 (final-review-dispatch.md) — 这两个文件不存在于 codebase（discovery 与 final-review skill 的 dispatch 行为在 SKILL.md 中，已由 Plan 003 瘦身处理；角色规范在 -angles.md / -preconditions.md / 等独立文件，Pack 4.9 已覆盖）。Pack 4.5 / 4.6 视为 plan-writer 估算误差，正式 drop（实际反转工作全部由其他 Pack 覆盖）。

## File / Responsibility Map

| 文件 | 当前角色 | 反转后角色 | 主要工作 |
| --- | --- | --- | --- |
| `orchestrate-execution/references/execution-worker-dispatch.md` | Coordinator 派发指南 | Worker 自读执行手册 | 改写视角 + 加 Self-Read Protocol |
| `orchestrate-execution/references/execution-review-dispatch.md` | Coordinator 派发 review prompt | Codex Reviewer 自读手册 | 删粘贴段，留 envelope 字段说明 |
| `orchestrate-plan-writing/references/plan-writer-dispatch.md` | Coordinator 派发 Plan Writer | Plan Writer 自读手册 | 视角反转 |
| `orchestrate-plan-writing/references/plan-review-dispatch.md` | Coordinator 派发 Plan Reviewer | Plan Reviewer 自读手册 | 视角反转 |
| `orchestrate-discovery/references/discovery-dispatch.md` | Coordinator 派发 Discovery | Discovery agent 自读手册 | 视角反转 |
| `orchestrate-final-review/references/final-review-dispatch.md` | Coordinator 派发 Final Reviewer | Final Reviewer 自读手册 | 视角反转 |

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files |
| --- | --- | --- | --- | --- |
| 4.1 | execution-worker-dispatch.md 反转 | normal | Plan 003 完成 | `execution-worker-dispatch.md` |
| 4.2 | execution-review-dispatch.md 反转 | normal | — | `execution-review-dispatch.md` |
| 4.3 | plan-writer-dispatch.md 反转 | normal | — | `plan-writer-dispatch.md` |
| 4.4 | plan-review-dispatch.md 反转 | normal | — | `plan-review-dispatch.md` |
| 4.5 | discovery-dispatch.md 反转 | trivial | — | `discovery-dispatch.md` |
| 4.6 | final-review-dispatch.md 反转 | trivial | — | `final-review-dispatch.md` |
| 4.7 | bug-investigation-route.md 反转 | normal | — | `bug-investigation-route.md` |
| 4.8 | workflow-direct-repair.md 反转 | normal | — | `workflow-direct-repair.md` |
| 4.9 | design-review-angles.md / final-review-angles.md / merge-conflict-* 删除 paste 段 | normal | Plan 002 (schema 字段就绪) | 多文件 |

---

## Pack 4.1：execution-worker-dispatch.md 反转

### Goal behavior

把当前以「Coordinator 必须 …」为主语的派发指南，反转为以「Worker（你）必须 …」为主语的执行手册。顶部加 `## Self-Read Protocol` 段：Worker 第一步 Read envelope → Read plan.md → Read 本文件 → 进入 Worker Loop。删除 Coordinator 端粘贴模板（执行步骤、QA 模板、verdict 体例）的副本，因为现在 Worker 自己来读。

### Implementation tasks

1. Read `plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md`
2. 重写顶部章节：
   - 加 `## Self-Read Protocol`（5 步：envelope / plan.md / Pack Execution Manifest / 本手册 / Worker Loop 入口）
   - 加 `## 你是谁` 段：说明你是 pack-executor 或 complex-pack-executor，按 Plan 接到全部 Pack
3. 改写所有以「Coordinator 必须粘贴 / 必须写明 / 必须包含」开头的段：
   - 改主语为「你（Worker）」
   - 把「以下内容必须出现在 prompt」改为「你执行时按以下顺序」
4. 删除与 SKILL.md / Worker Loop 锚点重复的流程概述
5. 在文件末尾加 `## Coordinator 端最小职责`（≤ 10 行）：
   - 写 envelope（含 plan_id）
   - state.sh agent-id --plan-id 记录
   - 等待 SubagentStop hook 触发 agent-return-handler.sh
6. `bash plugin/build/build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md`

### Read first

- 当前 `execution-worker-dispatch.md`
- `plugin/agents/pack-executor.md`（Worker Loop 锚点位置）
- 调研 C 给出的逐段反转标注

### Acceptance criteria

- [ ] 文件顶部含 `## Self-Read Protocol` 段（5 步）
- [ ] 无「Coordinator 必须粘贴」类指引
- [ ] 主语统一为「你（Worker）」
- [ ] 末尾含 `## Coordinator 端最小职责` 段
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md` → Expected: exit 0
- `! grep -q 'Coordinator 必须粘贴' plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md` → Expected: exit 0
- `grep -q 'Coordinator 端最小职责' plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal（语义反转，但本 Pack 不改 Worker 实际行为；Worker Loop 真正落地在 Plan 005）

### Out of scope

- 不实现 Worker Loop 本身（Plan 005 Pack 5.1）
- 不动 agent-return-handler.sh（Plan 005 Pack 5.9）

---

## Pack 4.2：execution-review-dispatch.md 反转

### Goal behavior

Codex Reviewer 自读视角。删除 Coordinator 端「必须粘贴 review prompt 全文」的指引；改为 Reviewer 自读 envelope + plan-return.json + 本手册（含 confidence rubric / pre-emit gate / 证据表 / verdict 体例）。

### Implementation tasks

1. Read `plugin/skills/orchestrate-execution/references/execution-review-dispatch.md`
2. 顶部加 `## Self-Read Protocol`（envelope → plan-return.json → doc-patch.diff → open-items.json → 本手册 review rubric）
3. 改主语为「你（Reviewer）」
4. 保留 confidence rubric / pre-emit gate / evidence schema 段（这些是 Reviewer 实际要遵守的）
5. 末尾加 `## Coordinator 端最小职责`（≤ 10 行）：
   - 计算需要 review 的 plan 列表
   - 写 envelope（含 plan_id, plan_return_path）
   - 收 verdict 后调度 state.sh disposition --plan-id
6. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-execution/references/execution-review-dispatch.md`

### Read first

- 当前 `execution-review-dispatch.md`
- `plugin/build/templates/review-dispatch.md.tmpl`（确认 confidence rubric 等仍由 template 注入）

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol` 段
- [ ] 主语统一为「你（Reviewer）」
- [ ] confidence rubric / pre-emit gate / evidence schema 保留
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-execution/references/execution-review-dispatch.md` → Expected: exit 0
- `grep -q 'confidence' plugin/skills/orchestrate-execution/references/execution-review-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal

---

## Pack 4.3：plan-writer-dispatch.md 反转

### Goal behavior

Plan Writer 自读视角。Coordinator 端 prompt 缩为：envelope + design.md 路径 + issue.md 路径 + Plan Writer 手册路径。Plan Writer 第一步 Read design.md（含 Cross-Plan Contract Anchors / Business Summary Inputs / Review History）+ Read issue.md（含 Design context refs）+ Read 本手册。

### Implementation tasks

1. Read `plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md`
2. 顶部加 `## Self-Read Protocol`：envelope → design.md → issue.md → 本手册 → 进入 Plan 写作循环
3. 主语反转
4. 删除与 SKILL.md 重复的 Pack 写作模板（Plan Writer 自读手册即可）
5. 保留：plan.md schema、Pack 数量上限、worker_type 选择规则、budget_total 计算公式
6. 末尾加 `## Coordinator 端最小职责`
7. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md`

### Read first

- 当前 `plan-writer-dispatch.md`
- `plugin/skills/orchestrate-plan-writing/SKILL.md`（确认无重复）

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol`
- [ ] 含 `## Coordinator 端最小职责`
- [ ] plan.md schema + Pack 上限 + worker_type 选择规则 + budget 公式 保留
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal

---

## Pack 4.4：plan-review-dispatch.md 反转

### Goal behavior

Plan Reviewer 自读视角。Coordinator 端 prompt 缩为：envelope + plan.md 路径 + design.md 路径 + 本手册。Reviewer 自读时按手册逐条核 Pack 数量、worker_type、verification commands、Pack Execution Manifest 字段完整性。

### Implementation tasks

1. Read `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
2. 顶部加 `## Self-Read Protocol`
3. 主语反转
4. 保留 Plan Review rubric / verdict 体例 / Cross-Plan Contract Anchors 校验项
5. 末尾加 `## Coordinator 端最小职责`：收 verdict 后写 Plan Review History
6. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`

### Read first

- 当前 `plan-review-dispatch.md`

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol` + `## Coordinator 端最小职责`
- [ ] Plan Review rubric 保留
- [ ] Cross-Plan Contract Anchors 校验项保留（Plan 002 Pack 2.11 已迁到 design.md）
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` → Expected: exit 0
- `grep -q 'Cross-Plan Contract Anchors' plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal

---

## Pack 4.5：discovery-dispatch.md 反转

### Goal behavior

Discovery agent 自读视角。Coordinator 端 prompt 缩为 envelope + bug brief / 需求 brief 路径 + 本手册。

### Implementation tasks

1. Read `plugin/skills/orchestrate-discovery/references/discovery-dispatch.md`
2. 顶部加 `## Self-Read Protocol`
3. 主语反转
4. 保留 Discovery 输出 schema（design.md / issue hierarchy / bug brief）
5. 末尾加 `## Coordinator 端最小职责`
6. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-discovery/references/discovery-dispatch.md`

### Read first

- 当前 `discovery-dispatch.md`

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol` + `## Coordinator 端最小职责`
- [ ] Discovery 输出 schema 保留
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-discovery/references/discovery-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

trivial

---

## Pack 4.6：final-review-dispatch.md 反转

### Goal behavior

Final Reviewer 自读视角。Coordinator 端 prompt 缩为 envelope + design.md 路径 + 所有 plan.md 路径 + workflow-state.json 路径 + final-review-angles.md 路径。

### Implementation tasks

1. Read `plugin/skills/orchestrate-final-review/references/final-review-dispatch.md`
2. 顶部加 `## Self-Read Protocol`：envelope → design.md（含 Cross-Plan Contract Anchors）→ plans index → workflow-state → final-review-angles → 本手册
3. 主语反转
4. 保留 Final Review angles 引用、verdict 体例
5. 末尾加 `## Coordinator 端最小职责`
6. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-final-review/references/final-review-dispatch.md`

### Read first

- 当前 `final-review-dispatch.md`
- `plugin/skills/orchestrate-final-review/references/final-review-angles.md`（确认 angles 不重复）

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol` + `## Coordinator 端最小职责`
- [ ] Final Review angles 引用保留
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-final-review/references/final-review-dispatch.md` → Expected: exit 0
- `grep -q 'final-review-angles' plugin/skills/orchestrate-final-review/references/final-review-dispatch.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

trivial

---

## Pack 4.7：bug-investigation-route.md 反转

### Goal behavior

把 `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` 中 L16/L19/L22/L25 四处 `<paste user's bug description>` / `<paste error log>` / `<paste file paths>` / `<paste previous attempts>` 粘贴段反转。按本 Plan 决策注记：不新建 bug-seed.md 模板，而是把这些用户输入作为 dispatch envelope 的 inline 字段（envelope 扩展加 `bug_context` object），analyst agent 自读 envelope.bug_context 即获取。

### Implementation tasks

1. Read `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
2. 顶部加 `## Self-Read Protocol`（envelope → envelope.bug_context → 本手册 → 进入 RCA 流程）
3. 删除 4 处 `<paste …>` 段
4. 改写为：「Coordinator 在 dispatch envelope 中以 inline 字段 `bug_context: {description, error_log, file_paths[], previous_attempts}` 传入。Analyst（你）从 envelope 提取即可。」
5. 末尾加 `## Coordinator 端最小职责`：把用户原话/错误日志组装到 envelope.bug_context 字段，不写文件
6. 在 Plan 005 Pack 5.13 已扩展 envelope schema 的基础上 piggyback（envelope 扩展加 `bug_context` 字段，本 Pack 仅在 reference 中声明用法，schema 加字段建议挂到 Plan 002 Pack 2.6 envelope 扩展中）
7. `bash plugin/build/build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`

### Read first

- 当前 `bug-investigation-route.md`
- `plugin/state-schema/dispatch-envelope-v1.json`（Plan 002 已加字段）

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol` + `## Coordinator 端最小职责`
- [ ] 4 处 paste 段已删
- [ ] reference 中明确 `envelope.bug_context` 字段语义
- [ ] `build.sh --check` 通过

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` → Expected: exit 0
- `! grep -q 'paste user' plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` → Expected: exit 0
- `grep -q 'bug_context' plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` → Expected: exit 0

### Risk flags

normal

### Out of scope

- 不创建 bug-seed.md 模板文件（决策：不新增中介文档）

---

## Pack 4.8：workflow-direct-repair.md 反转

### Goal behavior

同 Pack 4.7 思路：把 `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md` L13 区域 worker dispatch 段中粘贴的 deviation 描述 / Source design / Fix scope / Acceptance 反转。Coordinator 把这些信息组装到 envelope inline 字段 `repair_context: {deviation, source_design_path, fix_scope, acceptance}`，worker 自读。

### Implementation tasks

1. Read `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md`
2. 顶部加 `## Self-Read Protocol`
3. 删除 worker dispatch 段中粘贴指令
4. 改写为 envelope inline 模式
5. 末尾加 `## Coordinator 端最小职责`
6. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md`

### Read first

- 当前 `workflow-direct-repair.md`

### Acceptance criteria

- [ ] 含 `## Self-Read Protocol` + `## Coordinator 端最小职责`
- [ ] 粘贴段已删
- [ ] envelope.repair_context 字段语义明确

### Verification commands

- `grep -q 'Self-Read Protocol' plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md` → Expected: exit 0
- `grep -q 'repair_context' plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md` → Expected: exit 0

### Risk flags

normal

---

## Pack 4.9：design-review-angles + final-review-angles + merge-conflict-* 删除 paste 段

### Goal behavior

调研 B 列出额外的 paste 段反转：
- `design-review-angles.md` L100/L107/L182-184 三处 `<paste project docs>` / `<paste contract anchors>` → 删除，reviewer 自读 CLAUDE.md + design.md `## Cross-Plan Contract Anchors`（Plan 002 已迁）
- `final-review-angles.md` L122/L132/L137/L140-148/L156/L158 多处 paste → 改为 reviewer 自跑 `ls docs/orchestrate/plans/`、jq 读 execution-state.plans[N].pack_summary（Plan 002 Pack 2.10 已聚合）、git diff 自跑、读 design/plan
- `merge-conflict-discovery.md` / `merge-conflict-repair.md` / `merge-rca-investigation.md` / `merge-integration-review.md` 中粘贴段全部改为「Read `.claude/multi-model-workflow/merge-brief-<run_id>.md` 中对应段」

### Implementation tasks

1. Read 5 个 reference 文件
2. 按调研 B 标注逐一删除 `<paste …>` 段
3. 改为指针引用（design.md / plan.md / execution-state / merge-brief）
4. 各文件顶部已有的 Self-Read Protocol（Pack 4.6/4.x 已加）补充新指针
5. `build.sh --apply` + `--check`

### Owned files

- Edit: `plugin/skills/orchestrate-discovery/references/design-review-angles.md`
- Edit: `plugin/skills/orchestrate-final-review/references/final-review-angles.md`
- Edit: `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-discovery.md`
- Edit: `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- Edit: `plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md`
- Edit: `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`

### Read first

- 上述 6 个文件
- 调研 B 报告中各文件的 paste 段位置标注
- Plan 002 Pack 2.10 (pack_summary 聚合) + Plan 006 (merge-brief schema)

### Acceptance criteria

- [ ] `grep -rn '<paste' plugin/skills/orchestrate-discovery/references/design-review-angles.md plugin/skills/orchestrate-final-review/references/final-review-angles.md plugin/skills/orchestrate-multi-pr-merge/references/` 无匹配
- [ ] merge-* reference 全部含 merge-brief 路径引用
- [ ] `build.sh --check` 通过

### Verification commands

- `! grep -rq '<paste' plugin/skills/orchestrate-discovery/references/design-review-angles.md plugin/skills/orchestrate-final-review/references/final-review-angles.md plugin/skills/orchestrate-multi-pr-merge/references/` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Plan 002 Pack 2.1/2.10/2.12（design schema + pack_summary + cross-plan migration）
- Plan 006 Pack 6.1/6.2（merge-brief schema 必须先存在）

---

## Plan-level 验证

```bash
bash plugin/build/build.sh --apply --plugin-dir plugin
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/run-all-tests.sh
bash plugin/scripts/verify-maturity.sh

# 视角反转完整性
for f in plugin/skills/*/references/*-dispatch.md; do
  grep -q 'Self-Read Protocol' "$f" || echo "MISSING Self-Read Protocol: $f"
  grep -q 'Coordinator 端最小职责' "$f" || echo "MISSING Coordinator section: $f"
done
```

全部通过 → Plan 004 完成。

## Plan Review History

（待 Plan Implementation Review 后追加）
