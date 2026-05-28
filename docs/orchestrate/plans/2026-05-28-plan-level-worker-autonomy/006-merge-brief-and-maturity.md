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

- [ ] `merge-brief-v1.json` schema 定义（9 段：scope_summary / pr_inventory / contract_conflicts / state_divergence / shared_files / merge_strategy / verification_plan / rollback_plan / decision_log）
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

---

## Pack 6.1：merge-brief-v1.json schema 定义

### Goal behavior

定义 merge-brief 的 9 段 JSON schema。

### Implementation tasks

1. Read `plugin/state-schema/`（参考样式）
2. 创建 `plugin/state-schema/merge-brief-v1.json`，含 9 段：
   - `scope_summary`: 合并目标范围
   - `pr_inventory[]`: PR 列表 {pr_url, branch, design_path, plan_paths[]}
   - `contract_conflicts[]`: 跨 PR 合同冲突 {surface, prs, conflict_type, resolution}
   - `state_divergence[]`: 状态机差异 {state_file, prs, divergence, resolution}
   - `shared_files[]`: 多 PR 同改文件 {path, prs, merge_strategy}
   - `merge_strategy`: 整体策略 {order[], rebase|merge, conflict_handling}
   - `verification_plan[]`: 合并后验证步骤
   - `rollback_plan`: 回滚预案
   - `decision_log[]`: 关键决策 {at, decision, rationale}
3. schema_version = "1"
4. 加 README 索引

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
