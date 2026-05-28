# Plan 004：Phase 3 Dispatch Reference 反转（让 sub-agent 自读）

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（Document-as-Context 原则 + 推荐改造顺序 Phase 3）
**调研依据**: 调研 C 「Dispatch Reference 改造方案」
**Blocked by**: Plan 003（SKILL 已 lean，dispatch reference 成为唯一执行手册）
**Risk profile**: normal（语义改写，但不动状态机和数据流）
**Worker type**: `pack-executor`

## Plan Goal Behavior

把所有 `*-dispatch.md` reference 从「Coordinator 必须粘贴的内容片段」**反转**为「sub-agent 自读的执行手册」。Coordinator 端的 prompt 缩为 envelope + 文档路径 + handbook 路径指针；详细执行指南、QA 模板、verdict 体例由 sub-agent 第一步 `Read handbook` 自己拿。

**反转后命名**：含「dispatch」语义保留（向后兼容），但内部段落改写为「Sub-agent 自读手册」视角——主语从「Coordinator 必须 …」改为「Sub-agent（你）必须 …」。

## Plan Acceptance Criteria

- [ ] 6 个 dispatch reference 文件完成视角反转
- [ ] 每个 reference 顶部加 `## Self-Read Protocol` 段（sub-agent 启动时必读 5 步）
- [ ] 删除「Coordinator 必须把以下内容粘贴到 prompt」类指引
- [ ] 删除与 SKILL.md 重复的流程概述
- [ ] Coordinator 端 dispatch 调用 prompt 缩为 envelope + 路径（验收信号：dispatch 调用代码不超过 12 行）
- [ ] 每个 reference 末尾保留「Coordinator 端最小职责」段（≤ 10 行，仅列状态写入 / hook 触发义务）
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

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
