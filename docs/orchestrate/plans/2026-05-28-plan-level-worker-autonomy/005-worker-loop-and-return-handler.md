# Plan 005：Phase 4 Worker Loop 自治 + agent-return-handler 重写

**Design source**: `docs/orchestrate/design/2026-05-28-plan-level-worker-autonomy.md`（核心改造章节 + Worker Loop 合同 + 第三轮调研追加）
**调研依据**: 调研 A 「Worker 类型差异」、调研 D 「Hook 改造方案」、调研 E 「Plan 文档 schema」
**Blocked by**: Plan 002（schema 字段就绪）+ Plan 004（dispatch reference 反转完成）
**Risk profile**: high（状态机 / hook / 数据流多点联动）
**Worker type**: `complex-pack-executor`

## Plan Goal Behavior

落地 Plan-level Worker 自治。Worker 接到 Plan 后按 Pack Execution Manifest 自治执行全部 Pack（每 Pack TDD → verify → commit → state.sh transition → checkpoint），完成后写 3 个 plan-return artifact（plan-return.json + doc-patch.diff + open-items.json）。Coordinator 端 SubagentStop hook（agent-return-handler.sh）解析 artifact → apply doc-patch → 调度 Plan-level Codex Review → 路由 verdict。

**Worker 类型分工**：
- `pack-executor`：normal/trivial Plan，pack 串行
- `complex-pack-executor`：high-risk Plan（含 migration / billing / auth / cross-module），Pack 串行但每 Pack 后多一轮自检

**Context 自监控**：Worker 每完成 Pack 调用 `state.sh agent-context-check`，若 `packs_in_session ≥ 5` 且剩余 Pack ≥ 2，返回 verdict=`need-fresh-worker`，Coordinator 起新 Agent 续做。

## 决策记录（与设计文档第三轮拍板对齐）

| # | 设计决策 | 本 Plan 落实 |
| --- | --- | --- |
| 决策 2 | **保留 `pack-executor.md` / `complex-pack-executor.md` 名字**（不改名为 plan-executor）| Pack 5.2 直接在原文件加锚点 |
| 决策 3 | `plan-returns/` 落地路径 = **`.claude/multi-model-workflow/plan-returns/<run_id>/<plan_id>/`**（与 pack-returns 同 level，不触发 guard-doc-edit）| Pack 5.1/5.3/5.9 全部用此绝对路径 |
| 决策 4 | Context 阈值 = **5 packs in session**；剩余 ≥ 2 时触发 need-fresh-worker | Pack 5.4 实现 |
| 决策 5 | Effort budget 权重 = **实际 Pack 数**（不再固定 1）；need-fresh-worker 续派计 0.5 | Pack 5.12 改写 |
| 决策 6 | doc-patch apply 时机 = **Plan Implementation Review 通过后**（避免回滚）| Pack 5.9 verdict 路由：complete → 触发 Review → Review pass → apply doc-patch + commit |
| 决策 7 | per-pack 三次失败封顶；**per-plan 不额外封顶**——Worker 走 partial-pass 返回，Coordinator 决定续修或拍 BLOCKED | Pack 5.1 Worker Loop template 写明 |
| Repair Mode | envelope `repair_round >= 1` + `disposition_refs` 非空 → **SendMessage 同 worker**（不新派 Agent）+ 每个 finding 独立 commit `Pack N.M: <title> — repair: <summary>` | Pack 5.1 Worker Loop template 加 Repair Mode 段；Plan 001 Pack 1.3 已取消 sendmessage 写文件 |

## Plan Acceptance Criteria

**Plan 005 状态**：✅ 完成（2026-05-28，Worker agentId `a1721d257b5c1d257`，verdict=pass）

19/19 Pack 全部 committed：5.1 worker-loop template + resolver / 5.2 pack-executor + complex-pack-executor 锚点 / 5.3 plan-return + open-items schema / 5.4-5.7 state.sh 4 子命令（含 execution-plan complete / plan-returns ingest 命名对齐设计）/ 5.8 validate-plan-dispatch.sh / 5.9 agent-return-handler.sh 重写（决策 6: 不 apply doc-patch）/ 5.10 track-execution-state.sh + NEXT 抑制 / 5.11 enforce-plan-commit.sh / 5.12 effort budget 按实际 Pack 数（决策 5）/ 5.13 parse-envelope.sh + plan_id 消费 / 5.14 hooks.json 集中重命名 + 注册 / 5.15 lib/plan-return-parser.sh + lib/doc-patch-apply.sh / 5.16 e2e fixture 14 assertions / 5.17 continuation 21 invariants（additive per_pack merge + effort 5.5）/ 5.18 guard-plan-doc-patch.sh + 5.19 detect-worker-scope-drift.sh 兜底。

Plan-level 验证：run-all-tests **53 suites pass** + verify-maturity **104/0** + build.sh --check 通过 + e2e + continuation 测试全绿。

- [x] `pack-executor.md` + `complex-pack-executor.md` 加 Worker Loop 段（template 注入；保留原文件名按决策 2）
- [x] Worker Loop template **含设计文档 §Worker Loop（L579-606）完整 5 步启动序列 + Pack 循环主体 + Repair Mode + Context 自监控**
- [x] Worker 在 Plan 边界写 3 个 artifact 至 **`${STATE_DIR}/plan-returns/<run_id>/<plan_id>/`**（决策 3 钉死路径）
- [x] `validate-pack-dispatch.sh` 改为 `validate-plan-dispatch.sh`
- [x] `agent-return-handler.sh` 重写：解析 artifact → **Review 通过后才 apply doc-patch**（决策 6）→ 路由 4 路 verdict
- [x] `track-execution-state.sh` 改为聚合 pack_summary
- [x] `enforce-pack-commit.sh` 改为 enforce-plan-commit
- [x] `guard-doc-edit.sh` 保留 + 加白名单允许 Worker 写 `${STATE_DIR}/plan-returns/`
- [x] `track-effort-budget.sh` 计费 = **实际 Pack 数**（决策 5）；need-fresh-worker 续派计 0.5
- [x] `state.sh` 新增/改写：`agent-id --plan-id`、`disposition --plan-id`、`agent-context-check`、`pack-progress`、**`execution-plan complete`** + **`plan-returns ingest`**（与设计 9 项 enforcement #5 命名对齐）
- [x] `dispatch-envelope-v1.json` 加 `plan_id` 字段（Plan 002 Pack 2.6 完成）
- [x] Worker Loop 启动 5 步 + Pack 循环 + Repair Mode + need-fresh-worker 全部测试覆盖
- [x] `track-execution-state.sh` NEXT 消息修正：worker_agent_id 非空时抑制「Dispatch Plan Implementation Review」（避免误导，调研 D 漏项 #10）
- [x] **可选** hook `guard-plan-doc-patch.sh`（校验 doc-patch 只动 plan checkbox 行）
- [x] **可选** hook `detect-worker-scope-drift.sh`（PostToolUse Edit 兜底）
- [x] `bash plugin/scripts/run-all-tests.sh` 通过
- [x] `bash plugin/scripts/verify-maturity.sh` 通过

## File / Responsibility Map

| 文件 | 改动类型 |
| --- | --- |
| `plugin/agents/pack-executor.md` | +Worker Loop 段 +Context 自监控段 |
| `plugin/agents/complex-pack-executor.md` | +Worker Loop 段 +Context 自监控段 + 风险自检段 |
| `plugin/build/templates/worker-loop.md.tmpl` | 新增 template（Worker Loop 内容） |
| `plugin/build/resolvers/worker-loop.sh` | 新增 resolver（注入 pack-executor 和 complex-pack-executor） |
| `plugin/hooks/validate-pack-dispatch.sh` | 重命名 + 重写 → `validate-plan-dispatch.sh` |
| `plugin/hooks/agent-return-handler.sh` | 结构性重写 |
| `plugin/hooks/track-execution-state.sh` | 重写为 pack_summary 聚合 |
| `plugin/hooks/enforce-pack-commit.sh` | 改写为 enforce-plan-commit |
| `plugin/hooks/track-effort-budget.sh` | Plan-level 计费 |
| `plugin/hooks/hooks.json` | 同步重命名 + 触发事件调整 |
| `plugin/scripts/state.sh` | +5 子命令 |
| `plugin/state-schema/dispatch-envelope-v1.json` | +plan_id（Plan 002 Pack 2.10 已加，本 Plan 校验消费侧） |
| `plugin/scripts/lib/plan-return-parser.sh` | 新增 lib（parse plan-return.json） |
| `plugin/scripts/lib/doc-patch-apply.sh` | 新增 lib（apply doc-patch.diff） |
| `tests/hooks/agent-return-handler.bats` | 新增测试 fixture |

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files |
| --- | --- | --- | --- | --- |
| 5.1 | worker-loop template + resolver 新增 | normal | — | `worker-loop.md.tmpl`, `worker-loop.sh` |
| 5.2 | pack-executor / complex-pack-executor 接入 worker-loop 锚点 | normal | 5.1 | `pack-executor.md`, `complex-pack-executor.md` |
| 5.3 | Worker plan-return artifact schema 定义 | normal | — | `plan-return-v1.json`, `open-items-v1.json` |
| 5.4 | state.sh agent-context-check 子命令 | normal | — | `state.sh` |
| 5.5 | state.sh agent-id --plan-id 子命令 | normal | Plan 002 Pack 2.6 | `state.sh` |
| 5.6 | state.sh disposition --plan-id 子命令 | normal | Plan 002 Pack 2.6 | `state.sh` |
| 5.7 | state.sh pack-progress + plan-complete 子命令 | normal | 5.5 | `state.sh` |
| 5.8 | validate-pack-dispatch.sh → validate-plan-dispatch.sh 重写 | high | 5.5 | `validate-plan-dispatch.sh`, `hooks.json` |
| 5.9 | agent-return-handler.sh 结构性重写 | high | 5.3, 5.5, 5.6 | `agent-return-handler.sh`, lib/* |
| 5.10 | track-execution-state.sh 重写为 pack_summary 聚合 | high | 5.7 | `track-execution-state.sh` |
| 5.11 | enforce-pack-commit.sh → enforce-plan-commit | normal | — | `enforce-plan-commit.sh` |
| 5.12 | track-effort-budget.sh Plan-level 计费 | normal | — | `track-effort-budget.sh` |
| 5.13 | dispatch-envelope plan_id 消费校验 | normal | Plan 002 Pack 2.10 | parse-envelope.sh, 所有读 envelope 的 hook |
| 5.14 | hooks.json 重命名 + 触发事件调整 | high | 5.8, 5.9, 5.10, 5.11 | `hooks.json` |
| 5.15 | lib/plan-return-parser.sh + lib/doc-patch-apply.sh 新增 | normal | 5.3 | lib/* |
| 5.16 | Worker Loop 端到端测试 fixture | normal | 5.1-5.15 全完成 | `tests/hooks/*.bats` |
| 5.17 | Worker need-fresh-worker continuation 测试 | normal | 5.16 | `tests/hooks/*.bats` |
| 5.18 | guard-doc-edit.sh 加白名单 + 新增 guard-plan-doc-patch.sh | normal | 5.9 | `guard-doc-edit.sh`, 新文件 |
| 5.19 | detect-worker-scope-drift.sh PostToolUse Edit 兜底 | normal | — | 新文件 |

---

## Pack 5.1：worker-loop template + resolver 新增

### Goal behavior

新增 `plugin/build/templates/worker-loop.md.tmpl`（Worker Loop 7 步 + Context 自监控段）和 `plugin/build/resolvers/worker-loop.sh`（注入 pack-executor.md 和 complex-pack-executor.md）。template 内容由设计文档 Worker Loop 合同段定义。

### Implementation tasks

1. Read `plugin/build/templates/`（参考现有 template 结构）
2. Read `plugin/build/resolvers/`（参考现有 resolver）
3. Read 设计文档 L577-606（Worker Loop 完整行为契约：5 步启动 + Pack 循环主体 + Repair Mode）
4. 创建 `plugin/build/templates/worker-loop.md.tmpl`，内容必须**严格对齐设计文档**：

   **段 A：`## Worker Loop — 5 步严格启动序列`**
   1. Read plan 文档全文，验证 5 必备字段（Pack Manifest、Dependencies、Acceptance、Verification commands、owned files）；缺则立即返回 `NEEDS_PLAN_REVISION`
   2. Read `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-handbook.md`（固定行为规范）
   3. Read `${STATE_DIR}/execution-state-<run_id>.json`，提取 `plans[plan_id].packs` 当前 status 字典——区分首派 vs 续派（partial-fail recovery，跳过 `status=committed` 的 pack）
   4. Read `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/open-items.json`（若存在）—— 继承前任 worker 累积的 Open Items
   5. Read 项目 CLAUDE.md + 链入规则

   **段 B：`## Pack 循环主体`**
   ```
   sorted_packs = topo_sort(plan.packs, by="Dependencies")
   # 无 Dependencies 字段 → 按编号顺序；环 → 立即返回 NEEDS_PLAN_REVISION
   for pack in sorted_packs:
     if execution_state.packs[pack.id].status == "committed": continue   # partial-fail recovery
     TDD: write_failing_test → confirm_red → write_minimal_code → confirm_green  # trivial 例外
     run verification_commands → 失败走 on_pack_fail (三次失败协议：每次换方法)
     scope_drift_check(changed_files ⊆ pack.owned_files; 同 Plan 内其它 pack → 记录; 跨 Plan → revert)
     write ${STATE_DIR}/pack-returns/<run_id>/<pack_id>.json (commit 前)
     git commit "Pack N.M: <title> — <summary>"  # enforce-plan-commit hook 校验
     append open_items to ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/open-items.json
     call state.sh pack-progress --plan-id <id> --pack-id <id> --status complete --commit-sha <sha>
     call state.sh agent-context-check; if "need-fresh-worker" → break (Context 阈值=5 packs)
   # 全部 Pack 完成 / context 触发：
   write doc-patch.diff to ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/doc-patch.diff
   write plan-return.json to ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json
   call state.sh execution-plan complete --plan-id <id> --verdict <verdict>
   return  # SubagentStop 触发 agent-return-handler.sh
   ```

   **段 C：`## Verdict 枚举`** `pass | partial-pass | blocked | need-fresh-worker | needs-context | needs-plan-revision`

   **段 D：`## Repair Mode`**（envelope `repair_round >= 1` + `disposition_refs` 非空时）
   - 不重新读 plan 全文（worker 已有上下文，通过 SendMessage 续派来的）
   - 读 disposition_refs 中每个 finding 的 `[Pack N.M]` 归属标记
   - 按 Pack 独立 commit：`Pack N.M: <title> — repair: <summary>`（每 finding 独立 commit，不批量）
   - track-execution-state.sh 会把 status 再次置 `committed`（幂等）

   **段 E：`## Context 自监控`**
   - 每完成一个 Pack commit 后立即 `state.sh agent-context-check`
   - 阈值：`packs_in_session ≥ 5` 且 `remaining_packs ≥ 2` → 返回 `verdict=need-fresh-worker`
   - 报告位置：plan-return.json `verdict` 字段（不是单独 field）
   - 续派机制：Coordinator 派**新 Agent**（不 SendMessage——同 session 不解决累积）；新 worker Step 3 读 execution-state 自动跳过 `status=committed` 的 pack

   **段 F：`## 失败次数协议`**（决策 7）
   - per-pack TDD 内三次失败协议（沿用现有规则）
   - per-plan **不额外封顶**——Worker 走 `partial-pass` 返回 + 标记 failed_pack_id，由 Coordinator 决定 SendMessage 续修 / 拍 BLOCKED

5. 创建 `plugin/build/resolvers/worker-loop.sh`：注入到 `pack-executor.md` 和 `complex-pack-executor.md` 的 `<!-- BEGIN: worker-loop -->` / `<!-- END: worker-loop -->` 锚点
6. `bash plugin/build/build.sh --apply --plugin-dir plugin` 验证 resolver

### Owned files

- Create: `plugin/build/templates/worker-loop.md.tmpl`
- Create: `plugin/build/resolvers/worker-loop.sh`

### Read first

- 设计文档「Worker Loop 合同」段
- 现有 template / resolver 样例（如 `review-dispatch`）

### Acceptance criteria

- [x] worker-loop.md.tmpl 存在且含 6 段（A 启动 / B 循环 / C verdict / D Repair Mode / E Context / F 失败次数）
- [x] worker-loop.sh resolver 可执行
- [x] `build.sh --apply` 能注入到 pack-executor.md（验证 Pack 5.2）
- [x] 模板含 plan-return.json schema 引用
- [x] 模板路径全部用 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/`（决策 3）
- [x] 模板含 Repair Mode 段 + `repair:` commit message 规范

### Verification commands

- `test -f plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `test -x plugin/build/resolvers/worker-loop.sh` → Expected: exit 0
- `grep -q 'Worker Loop' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `grep -q 'agent-context-check' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `grep -q 'Repair Mode' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `grep -q '${STATE_DIR}/plan-returns' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `grep -q 'execution-plan complete' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0

### Risk flags

normal（纯新增 template）

---

## Pack 5.2：pack-executor / complex-pack-executor 接入 worker-loop 锚点

### Goal behavior

在 `pack-executor.md` 和 `complex-pack-executor.md` 加 `<!-- BEGIN: worker-loop -->` / `<!-- END: worker-loop -->` 锚点对，`build.sh --apply` 注入 Worker Loop。complex-pack-executor 额外加风险自检段。

### Implementation tasks

1. Read `plugin/agents/pack-executor.md` + `plugin/agents/complex-pack-executor.md`
2. 找合适位置插入 `<!-- BEGIN: worker-loop -->` / `<!-- END: worker-loop -->`（在「You are pack-executor」描述段之后、tool 列表之前）
3. complex-pack-executor 多加一段「每 Pack 完成后 + 高风险自检 checklist」（migration / contract / cross-module 三项）
4. `bash plugin/build/build.sh --apply` 注入
5. `bash plugin/build/build.sh --check` 验证

### Owned files

- Edit: `plugin/agents/pack-executor.md`
- Edit: `plugin/agents/complex-pack-executor.md`

### Read first

- 当前两个 agent 文件
- Pack 5.1 创建的 worker-loop.md.tmpl

### Acceptance criteria

- [x] 两个 agent 文件含 `BEGIN: worker-loop` 锚点
- [x] `build.sh --apply` + `--check` 通过
- [x] complex-pack-executor 含高风险自检 checklist

### Verification commands

- `grep -q 'BEGIN: worker-loop' plugin/agents/pack-executor.md` → Expected: exit 0
- `grep -q 'BEGIN: worker-loop' plugin/agents/complex-pack-executor.md` → Expected: exit 0
- `grep -q '高风险自检' plugin/agents/complex-pack-executor.md` → Expected: exit 0
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Pack 5.1

---

## Pack 5.3：Worker plan-return artifact schema 定义

### Goal behavior

定义 `plan-return.json` 和 `open-items.json` 的 JSON schema，存放至 `plugin/state-schema/`。这是 Worker → Coordinator 的合同。**所有 artifact 路径钉死在 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/`（决策 3）——不在 `docs/` 下，绕过 `guard-doc-edit.sh`**。

### Implementation tasks

1. Read `plugin/state-schema/`（参考现有 schema 风格）
2. 创建 `plugin/state-schema/plan-return-v1.json`，**与设计 §Worker Loop（L141-154）的 JSON 模板严格对齐**：
   - schema_version, run_id, plan_id, started_at, finished_at
   - verdict 枚举：`pass | partial-pass | blocked | need-fresh-worker | needs-context | needs-plan-revision`
   - per_pack: object of `{pack_id: {status: "committed|blocked|skipped", commit_sha, verdict, reason?, attempts?}}`
   - open_items_path: 相对路径 `plan-returns/<run_id>/<plan_id>/open-items.json`
   - doc_patch_path: 相对路径 `plan-returns/<run_id>/<plan_id>/doc-patch.diff`
   - context_pressure: `{completed_packs: int, triggered: bool}`
3. 创建 `plugin/state-schema/open-items-v1.json`：
   - schema_version, plan_id
   - items: array of `{tag: "out-of-scope|needs-evaluation|bug", pack_id, finding, suggested_action}`（标签与现有 pack-returns 的 open_items 三标签对齐）
4. **pack-returns 的 schema 由 Plan 002 Pack 2.7 创建**（pack-returns-v1.json）；本 Pack 不重复
5. README 更新 schema 索引：列出 plan-returns 文件路径协议为 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/{plan-return.json, doc-patch.diff, open-items.json}`

### Owned files

- Create: `plugin/state-schema/plan-return-v1.json`
- Create: `plugin/state-schema/open-items-v1.json`
- Edit: `plugin/state-schema/README.md`（如有）

### Read first

- 现有 schema 文件
- 设计文档 Worker Loop artifact 段

### Acceptance criteria

- [x] 2 个 schema 文件存在且 JSON 合法
- [x] verdict 枚举完整（`complete|partial|blocked|need-fresh-worker`）
- [x] schema_version = "1"

### Verification commands

- `python3 -m json.tool plugin/state-schema/plan-return-v1.json > /dev/null` → Expected: exit 0
- `python3 -m json.tool plugin/state-schema/open-items-v1.json > /dev/null` → Expected: exit 0
- `grep -q 'need-fresh-worker' plugin/state-schema/plan-return-v1.json` → Expected: exit 0

### Risk flags

normal

---

## Pack 5.4：state.sh agent-context-check 子命令

### Goal behavior

Worker 在 Pack 循环中调用 `state.sh agent-context-check`，根据 execution-state.plans[current_plan].packs_in_session（由 Pack 5.10 聚合写入）+ 剩余 Pack 数 → 返回 `ok` 或 `need-fresh-worker`。阈值 packs_in_session ≥ 5 且剩余 ≥ 2。

### Implementation tasks

1. Read `plugin/scripts/state.sh`
2. 加 subcommand `agent-context-check`：
   - 入参：`--plan-id <id>` `--run-id <id>`
   - 读 execution-state.json
   - 计算 packs_in_session（由 track-execution-state 聚合）+ remaining_packs（manifest 总 - 已完成）
   - 输出 JSON: `{"verdict":"ok|need-fresh-worker","reason":"..."}`
3. 加单测（用 mock state file）

### Owned files

- Edit: `plugin/scripts/state.sh`
- Edit/Create: `plugin/scripts/tests/state-agent-context-check.bats`

### Read first

- 当前 state.sh
- execution-state-v1.json schema

### Acceptance criteria

- [x] state.sh agent-context-check 子命令存在
- [x] mock 测试：packs_in_session=5, remaining=2 → need-fresh-worker
- [x] mock 测试：packs_in_session=3, remaining=5 → ok

### Verification commands

- `bash plugin/scripts/state.sh agent-context-check --help` → Expected: exit 0
- `bash plugin/scripts/tests/state-agent-context-check.bats` → Expected: exit 0

### Risk flags

normal

---

## Pack 5.5：state.sh agent-id --plan-id 子命令

### Goal behavior

扩展 `state.sh agent-id` 接收 `--plan-id` 入参，写入 execution-state.plans[N].worker_agent_id（Plan 002 Pack 2.5 已加字段）。

### Implementation tasks

1. Read `state.sh` agent-id 子命令现状
2. 加 `--plan-id <id>` 参数解析
3. 写 execution-state.plans[匹配 plan_id].worker_agent_id = <new-id>
4. 加 lock（避免并发写）
5. 单测

### Owned files

- Edit: `plugin/scripts/state.sh`

### Read first

- 当前 state.sh agent-id 子命令
- execution-state-v1.json

### Acceptance criteria

- [x] state.sh agent-id --plan-id <id> 可正确写入
- [x] 无 --plan-id 时保持向后兼容（旧行为）
- [x] lock 保护正常

### Verification commands

- `bash plugin/scripts/state.sh agent-id --plan-id test-plan-001 --agent-id worker-X` → Expected: exit 0 + 写入 state

### Risk flags

normal

### Dependencies

- Plan 002 Pack 2.5 (schema 字段)
- Plan 002 Pack 2.6 (state.sh 多子命令重构基础)

---

## Pack 5.6：state.sh disposition --plan-id 子命令

### Goal behavior

扩展 `state.sh disposition` 接收 `--plan-id`，写 workflow-state.review_dispositions[] 时携带 plan_id（Plan 002 Pack 2.4 已加 schema 字段）。

### Implementation tasks

1. Read state.sh disposition 子命令
2. 加 `--plan-id <id>` 参数
3. append review_dispositions[].plan_id
4. 单测

### Owned files

- Edit: `plugin/scripts/state.sh`

### Acceptance criteria

- [x] disposition 写入含 plan_id 字段
- [x] 无 --plan-id 时保持向后兼容
- [x] 单测通过

### Verification commands

- `bash plugin/scripts/state.sh disposition --plan-id p1 --gate plan-review --verdict pass --reviewer codex` → Expected: exit 0
- 验证 workflow-state.json review_dispositions 末尾含 plan_id

### Risk flags

normal

### Dependencies

- Plan 002 Pack 2.4 + 2.6

---

## Pack 5.7：state.sh pack-progress + execution-plan complete + plan-returns ingest 子命令

### Goal behavior

按设计 9 项 enforcement #5 命名规范，本 Pack 实现 3 个子命令：
- `pack-progress`：Worker 内部用，标记单 Pack 完成（触发 track-execution-state 聚合）
- **`execution-plan complete`**：Worker 内部用，标记整 Plan 完成（写 finished_at + verdict）
- **`plan-returns ingest`**：agent-return-handler.sh 用，读 plan-return.json → 验证 schema → 写 execution-state.plans[N].pack_summary + worker_verdict

### Implementation tasks

1. Read state.sh
2. 加 `pack-progress`：
   - 入参 `--plan-id <id> --pack-id <id> --status committed|skipped|blocked --commit-sha <sha>`
   - 写 execution-state.plans[N].pack_summary.packs[]（追加）
3. 加 `execution-plan complete`：
   - 入参 `--plan-id <id> --verdict <v>`
   - 写 execution-state.plans[N].finished_at + verdict
4. 加 `plan-returns ingest`：
   - 入参 `--run-id <id> --plan-id <id>`
   - 读 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json`
   - 用 plan-return-v1.json schema 验证
   - 把 per_pack 状态展开到 execution-state.plans[N].packs
   - 把 verdict 写到 execution-state.plans[N].worker_verdict
5. 全部子命令 lock 保护
6. 单测

### Owned files

- Edit: `plugin/scripts/state.sh`

### Acceptance criteria

- [x] 3 个子命令存在且正确写状态
- [x] 写入受 lock 保护
- [x] 命名与设计文档 9 项 enforcement #5 一致（`execution-plan complete` / `plan-returns ingest`）
- [x] 单测通过

### Verification commands

- `bash plugin/scripts/state.sh pack-progress --plan-id p1 --pack-id 5.1 --status committed --commit-sha abc1234` → Expected: exit 0
- `bash plugin/scripts/state.sh execution-plan complete --plan-id p1 --verdict pass` → Expected: exit 0
- `bash plugin/scripts/state.sh plan-returns ingest --run-id r1 --plan-id p1` → Expected: exit 0（需 fixture）

### Risk flags

normal

### Dependencies

- Pack 5.5

---

## Pack 5.8：validate-pack-dispatch.sh → validate-plan-dispatch.sh 重写

### Goal behavior

重命名 + 重写：原 hook 在每次 Pack dispatch 前校验 envelope，新 hook 在 Plan dispatch 前校验：
- envelope.plan_id 存在且非空
- envelope.plan_path 存在文件
- plan.md 含 `## Pack Execution Manifest` 段且非空
- envelope.run_id 与当前 workflow-state 一致

### Implementation tasks

1. Read `plugin/hooks/validate-pack-dispatch.sh`
2. 创建 `plugin/hooks/validate-plan-dispatch.sh`（重写）
3. 删除旧 `validate-pack-dispatch.sh`（或保留 deprecation shim 一段时间——本 Plan 决定直接删，避免双路径）
4. 新 hook 校验项：
   - envelope.plan_id 非空
   - plan_path file exists
   - plan.md 含 Pack Execution Manifest（grep -q）
   - run_id 与 workflow-state 当前一致
5. 失败时 deny 派发，输出明确原因
6. 测试 fixture（pass / fail 两路径）

### Owned files

- Create: `plugin/hooks/validate-plan-dispatch.sh`
- Delete: `plugin/hooks/validate-pack-dispatch.sh`
- Edit: `plugin/hooks/hooks.json`（Pack 5.14 统一处理，本 Pack 仅创建文件 + 单测）
- Create: `tests/hooks/validate-plan-dispatch.bats`

### Read first

- 当前 validate-pack-dispatch.sh
- dispatch-envelope-v1.json（Plan 002 Pack 2.10 加 plan_id）

### Acceptance criteria

- [x] validate-plan-dispatch.sh 存在且可执行
- [x] envelope 缺 plan_id → deny
- [x] plan.md 缺 Pack Execution Manifest → deny
- [x] 正常 envelope → allow
- [x] 旧 validate-pack-dispatch.sh 已删除

### Verification commands

- `test -x plugin/hooks/validate-plan-dispatch.sh` → Expected: exit 0
- `! test -e plugin/hooks/validate-pack-dispatch.sh` → Expected: exit 0
- `bash tests/hooks/validate-plan-dispatch.bats` → Expected: exit 0

### Risk flags

high（删除老 hook，必须确保 hooks.json 同步更新——Pack 5.14）

### Dependencies

- Pack 5.5（state.sh 配套）
- Plan 002 Pack 2.10（envelope schema）

---

## Pack 5.9：agent-return-handler.sh 结构性重写

### Goal behavior

Worker SubagentStop 触发，handler 按 **Plan 边界**处理：
1. 解析 SubagentStop payload 取 agent_id + run_id
2. 查 execution-state.plans 找到该 worker_agent_id 对应的 plan_id
3. Read `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json`
4. 调用 `state.sh plan-returns ingest` → 把 per_pack 状态写入 execution-state.plans[N]
5. 按 verdict 路由 **(决策 6: doc-patch apply 时机 = Review 通过后，不在本 handler 立即 apply)**：
   - `pass`：**不 apply doc-patch** → 输出 NEXT「派 Plan Implementation Review」（doc-patch.diff 留在 plan-returns 等 Review pass）→ Coordinator 派 review → review pass 后由 Coordinator 端流程（execution SKILL.md Step 14）apply doc-patch + commit
   - `partial-pass`：同 `pass` 流程（部分完成 Pack 也进 review；open-items 反映未完成 Pack）
   - `blocked`：**不 apply doc-patch** → 触发 BLOCKED 路由（与现状一致）
   - `need-fresh-worker`：**不 apply doc-patch** → 输出 NEXT「Coordinator 派**新 Agent** 续做 Plan，envelope 含 resume_from_pack_id」（同 session 不解决累积，不用 SendMessage）
   - `needs-plan-revision`：触发 NEEDS_PLAN_REVISION 路由（plan-writing repair）

### Implementation tasks

1. Read `plugin/hooks/agent-return-handler.sh`（现状）
2. 结构性重写：
   - 调用 `lib/plan-return-parser.sh` 解析 artifact（Pack 5.15 提供）
   - 调用 `state.sh plan-returns ingest` 写入 execution-state
   - **不调用** `lib/doc-patch-apply.sh`——doc-patch apply 由 Coordinator 在 Review pass 后执行（决策 6）
   - 按 verdict 路由 5 路
   - 每路由都要写 disposition / progress marker
   - **track-execution-state NEXT 消息修正**：因为 agent-return-handler 已经处理了 plan-level 返回，旧的「per-pack committed → 派 Plan Implementation Review」NEXT 文案需要在 track-execution-state 中抑制（worker_agent_id 非空时不 emit；详见 Pack 5.10）
3. 失败保护：parse 失败 / 缺 artifact → 写 BLOCKED + 通知 Coordinator
4. 测试 fixture 覆盖 5 路 verdict

### Owned files

- Rewrite: `plugin/hooks/agent-return-handler.sh`
- Create: `tests/hooks/agent-return-handler.bats`（Pack 5.16 补全 fixture）

### Read first

- 当前 agent-return-handler.sh
- 设计文档第三轮决策 6（doc-patch apply 时机）
- 设计文档 §Worker Loop Verdict 枚举
- Pack 5.3 plan-return-v1.json schema

### Acceptance criteria

- [x] 5 路 verdict 均有显式分支
- [x] **doc-patch.diff 在 handler 中绝不 apply**（决策 6：留到 Review pass 后 Coordinator 流程 apply）
- [x] handler 输出明确 NEXT 指令引导 Coordinator 下一步
- [x] need-fresh-worker → 输出"派新 Agent 含 resume_from_pack_id"指令
- [x] 缺 artifact → BLOCKED 输出
- [x] 调用 `state.sh plan-returns ingest` 写状态

### Verification commands

- `test -x plugin/hooks/agent-return-handler.sh` → Expected: exit 0
- `shellcheck plugin/hooks/agent-return-handler.sh` → Expected: exit 0
- Pack 5.16 端到端测试

### Risk flags

high（结构性重写，多路状态写入）

### Dependencies

- Pack 5.3, 5.5, 5.6, 5.7, 5.15

---

## Pack 5.10：track-execution-state.sh 重写为 pack_summary 聚合 + NEXT 消息修正

### Goal behavior

旧 hook 每 PostToolUse / Stop 写一次 execution-state.current_pack。新 hook 改为：监听 `state.sh pack-progress` → 追加 execution-state.plans[N].pack_summary.packs[]；Plan 完成时（state.sh execution-plan complete）聚合 pack_summary.total / completed / failed / commits[]。

**NEXT 消息修正（调研 D 漏项 #10）**：旧 hook 在「all-packs-committed」时 emit「Dispatch Plan Implementation Review」NEXT 消息。Worker 自治模式下 Worker 单 session 内会连续 commit 5 个 Pack，触发 hook 5 次但 Worker 还没返回——此时 emit Review NEXT 是错的。新 hook 必须**检查 worker_agent_id**：非空（Worker 还在跑）→ 抑制 NEXT；为空（Worker 已返回，agent-return-handler 已处理）→ emit「Dispatch Plan Implementation Review」NEXT。

### Implementation tasks

1. Read 当前 `track-execution-state.sh`
2. 重写聚合逻辑：
   - 监听 state.sh pack-progress 调用（hook input 含 subcommand 参数）
   - 追加 packs[]（保留每 Pack 状态 / commit_sha / verified_at）
   - 监听 state.sh execution-plan complete → 聚合 total / completed / failed / commits
3. **NEXT 消息分支修正**：
   - 在「all-packs-committed」检测后增加 worker_agent_id 检查
   - `worker_agent_id != null` → NEXT 改为「等 Worker session 返回，不要派 Review」
   - `worker_agent_id == null` → emit「Dispatch Plan Implementation Review」（原行为）
4. lock 保护
5. 测试 fixture（含 NEXT 抑制 / NEXT 触发两路）

### Owned files

- Rewrite: `plugin/hooks/track-execution-state.sh`
- Create/Edit: `tests/hooks/track-execution-state.bats`

### Read first

- 当前 track-execution-state.sh
- Plan 002 Pack 2.5 execution-state schema（plans[N].pack_summary）

### Acceptance criteria

- [x] hook 监听 state.sh pack-progress → 追加 packs[]
- [x] hook 监听 state.sh plan-complete → 聚合 summary
- [x] lock 保护，并发写无丢失
- [x] 测试覆盖 Pack→Plan 整链路

### Verification commands

- `bash tests/hooks/track-execution-state.bats` → Expected: exit 0

### Risk flags

high（多 hook + state 多写入并发风险）

### Dependencies

- Pack 5.7

---

## Pack 5.11：enforce-pack-commit.sh → enforce-plan-commit

### Goal behavior

旧 hook 每 Pack 后强制 commit。新 hook 改为：
- 每次 Worker 调用 `state.sh pack-progress` 时校验本次 commit_sha 是否存在
- Plan 完成时校验 commit 总数 ≥ Pack 数 - 跳过 / 阻塞数

### Implementation tasks

1. Read `enforce-pack-commit.sh`
2. 重命名为 `enforce-plan-commit.sh` 并重写
3. 监听 pack-progress：commit_sha 必须可解析（git cat-file -e）
4. 监听 plan-complete：commit 数 ≥ 实际完成 Pack 数（参考 pack_summary）
5. 失败时 deny + 输出修复建议

### Owned files

- Create: `plugin/hooks/enforce-plan-commit.sh`
- Delete: `plugin/hooks/enforce-pack-commit.sh`
- Edit: hooks.json（Pack 5.14 统一处理）
- Create: `tests/hooks/enforce-plan-commit.bats`

### Read first

- 当前 enforce-pack-commit.sh

### Acceptance criteria

- [x] 重命名完成
- [x] commit 缺失 → deny
- [x] commit 数 < 完成 Pack 数 → deny
- [x] 测试覆盖 pass / fail

### Verification commands

- `bash tests/hooks/enforce-plan-commit.bats` → Expected: exit 0

### Risk flags

normal

---

## Pack 5.12：track-effort-budget.sh Plan-level 计费（决策 5：权重 = 实际 Pack 数）

### Goal behavior

设计文档**决策 5**：Plan-level Worker dispatch 实际上跑了 N 个 Pack（典型 5 个），如果按固定 1 计费会严重失真（effort_total 跑空过早）。新规则：
- 一个 Plan 的 Worker dispatch 权重 = **实际完成的 Pack 数**（从 plan-return.json `per_pack` 中 status=committed 的条数累加）
- 一个 Plan 的 Codex Review 权重 = 1（不变）
- need-fresh-worker continuation 权重 = 0.5（合理近似 + 鼓励减少 churn）

### Implementation tasks

1. Read `track-effort-budget.sh` 现有计费逻辑
2. 改写：
   - 监听 PostToolUse Agent 触发：用 envelope.plan_id 去重（一个 plan_id 多 hook 触发只计 1 次基础）
   - **权重计算**：监听 SubagentStop 后 / agent-return-handler 处理完时，读 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json`，提取 `per_pack` 中 `status == "committed"` 计数 N → effort += N
   - need-fresh-worker resume（envelope 含 `resume_from_pack_id`）→ 基础 +0.5（额外续派开销）
3. 兼容老 envelope（无 plan_id）：fallback 计 1
4. 输出 budget marker 到 effort-state.json
5. 测试覆盖 3 类计费场景

### Owned files

- Edit: `plugin/hooks/track-effort-budget.sh`
- Edit: `tests/hooks/track-effort-budget.bats`

### Acceptance criteria

- [x] Plan dispatch effort = 实际 Pack 数（决策 5）
- [x] need-fresh-worker 续派 +0.5
- [x] Codex review 仍计 1
- [x] 老 envelope fallback 计 1
- [x] 测试覆盖：5-pack plan → effort +5；need-fresh-worker 续派后 → effort +0.5

### Verification commands

- `bash tests/hooks/track-effort-budget.bats` → Expected: exit 0

### Risk flags

normal（计费失真会让 budget guardian 误判，但不会破坏 workflow）

---

## Pack 5.13：dispatch-envelope plan_id 消费校验

### Goal behavior

Plan 002 Pack 2.10 已加 schema 字段，本 Pack 校验所有消费侧 hook / parser 正确解析 plan_id。修改 `parse-envelope.sh`（或同等 lib）输出 PLAN_ID 变量，所有 hook（validate-plan-dispatch、agent-return-handler、track-execution-state、enforce-plan-commit、track-effort-budget）都通过该变量消费。

### Implementation tasks

1. Read `plugin/scripts/lib/parse-envelope.sh`（如存在）；如不存在，新建
2. 加 `PLAN_ID=$(jq -r '.plan_id // empty' <<< "$envelope_json")` 输出
3. 在 5 个消费侧 hook 中替换硬编码 `jq -r .plan_id` 为统一 lib 调用
4. 单测

### Owned files

- Edit/Create: `plugin/scripts/lib/parse-envelope.sh`
- Edit: 5 个 hook 文件（替换解析方式）

### Read first

- 现状 envelope 解析散点
- dispatch-envelope-v1.json

### Acceptance criteria

- [x] parse-envelope.sh 输出 PLAN_ID
- [x] 5 个 hook 统一调用 lib
- [x] envelope 无 plan_id → 5 个 hook 均能给出明确错误

### Verification commands

- `grep -l 'PLAN_ID' plugin/hooks/*.sh | wc -l` → Expected: ≥ 5
- 单测覆盖 missing plan_id 场景

### Risk flags

normal

### Dependencies

- Plan 002 Pack 2.10

---

## Pack 5.14：hooks.json 重命名 + 触发事件调整

### Goal behavior

更新 `plugin/hooks/hooks.json`：
- `validate-pack-dispatch.sh` → `validate-plan-dispatch.sh`
- `enforce-pack-commit.sh` → `enforce-plan-commit.sh`
- agent-return-handler.sh 触发事件保持 SubagentStop
- track-execution-state 触发事件可能调整（按 5.10 实现）

### Implementation tasks

1. Read 当前 `plugin/hooks/hooks.json`
2. 替换 hook 文件名 + 同步事件
3. `python3 -m json.tool plugin/hooks/hooks.json` 验证格式
4. 测试 `bash plugin/scripts/run-all-tests.sh`

### Owned files

- Edit: `plugin/hooks/hooks.json`

### Read first

- 当前 hooks.json
- Pack 5.8, 5.9, 5.10, 5.11 输出

### Acceptance criteria

- [x] hooks.json JSON 合法
- [x] 所有旧 hook 名替换完成
- [x] run-all-tests 通过

### Verification commands

- `python3 -m json.tool plugin/hooks/hooks.json > /dev/null` → Expected: exit 0
- `! grep -q 'validate-pack-dispatch' plugin/hooks/hooks.json` → Expected: exit 0
- `! grep -q 'enforce-pack-commit' plugin/hooks/hooks.json` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: exit 0

### Risk flags

high（hook 触发链路总入口，错一行整个 plugin 失效）

### Dependencies

- Pack 5.8, 5.9, 5.10, 5.11, 5.18, 5.19 + Plan 002 Pack 2.13 (validate-pack-manifest.sh)

### 额外 hooks.json 注册

除了重命名旧 hook，本 Pack 还需注册以下新 hook：
- `validate-pack-manifest.sh`（Plan 002 Pack 2.13）→ PreToolUse Agent matcher `(pack-executor|complex-pack-executor)`
- `guard-plan-doc-patch.sh`（本 Plan Pack 5.18）→ PreToolUse Write matcher `*doc-patch.diff`
- `detect-worker-scope-drift.sh`（本 Plan Pack 5.19）→ PostToolUse Edit matcher（worker-active marker 存在时）

---

## Pack 5.15：lib/plan-return-parser.sh + lib/doc-patch-apply.sh 新增

### Goal behavior

抽出公共 lib 供 agent-return-handler.sh 调用：
- `plan-return-parser.sh`：parse plan-return.json + open-items.json，输出 bash 变量（VERDICT, PLAN_ID, DOC_PATCH_PATH, OPEN_ITEMS_PATH 等）
- `doc-patch-apply.sh`：apply doc-patch.diff（git apply --check 先验证 → git apply）

### Implementation tasks

1. 创建 `plugin/scripts/lib/plan-return-parser.sh`
2. 创建 `plugin/scripts/lib/doc-patch-apply.sh`
3. doc-patch-apply 必须：
   - git apply --check 先验证（cleanly apply）
   - 失败时输出 conflict 内容
   - 成功时执行 git add（不 commit，由 Coordinator 控制）
4. 单测覆盖 happy path + 冲突 path

### Owned files

- Create: `plugin/scripts/lib/plan-return-parser.sh`
- Create: `plugin/scripts/lib/doc-patch-apply.sh`
- Create: `tests/lib/plan-return-parser.bats`
- Create: `tests/lib/doc-patch-apply.bats`

### Read first

- Pack 5.3 schema
- 现有 plugin/scripts/lib/ 风格

### Acceptance criteria

- [x] 2 个 lib 文件可 source
- [x] parser 输出变量正确
- [x] doc-patch-apply 冲突时不污染 working tree
- [x] 单测覆盖

### Verification commands

- `bash -c 'source plugin/scripts/lib/plan-return-parser.sh && type parse_plan_return'` → Expected: exit 0
- `bash tests/lib/plan-return-parser.bats` → Expected: exit 0
- `bash tests/lib/doc-patch-apply.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Pack 5.3

---

## Pack 5.16：Worker Loop 端到端测试 fixture

### Goal behavior

构造端到端 fixture：模拟一个完整 Plan（3 Pack）的 Worker 执行 → SubagentStop → agent-return-handler 全链路。

### Implementation tasks

1. 创建 `tests/integration/worker-loop-e2e.bats`
2. fixture 包含：
   - mock plan.md（3 Pack）
   - mock plan-return.json (verdict=complete, 3 packs done)
   - mock doc-patch.diff
   - mock workflow-state.json + execution-state.json
3. 模拟 SubagentStop → 验证：
   - doc-patch 已 apply
   - execution-state.plans[N].finished_at 写入
   - workflow-state.review_dispositions 待写入
4. 覆盖 4 路 verdict

### Owned files

- Create: `tests/integration/worker-loop-e2e.bats`
- Create: `tests/fixtures/worker-loop/*`

### Acceptance criteria

- [x] 4 路 verdict 端到端测试全部通过
- [x] doc-patch apply 后 git working tree 干净 + 文件已修改
- [x] state 写入符合 schema

### Verification commands

- `bash tests/integration/worker-loop-e2e.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Pack 5.1-5.15 全完成

---

## Pack 5.17：Worker need-fresh-worker continuation 测试

### Goal behavior

专门覆盖 need-fresh-worker 路径：Worker 完成 3/5 Pack 后 context-check 返回 need-fresh-worker → 写部分 plan-return → handler 路由 → Coordinator 新 Agent dispatch 含 resume_from_pack_id → 新 Worker 接续完成剩余 2 Pack。

### Implementation tasks

1. 创建 `tests/integration/need-fresh-worker.bats`
2. 模拟两轮 Worker dispatch
3. 验证：
   - 第一轮 plan-return verdict=need-fresh-worker
   - handler 写 envelope marker 含 resume_from_pack_id=4
   - track-effort-budget 计 1.5（1 + 0.5）
   - 第二轮 Worker 接续后 verdict=complete
   - execution-state.plans[N].pack_summary.packs[] 累积 5 条
4. 边界：context-check 触发但剩余 Pack < 2 → 不触发 need-fresh-worker

### Owned files

- Create: `tests/integration/need-fresh-worker.bats`

### Acceptance criteria

- [x] need-fresh-worker 路径完整跑通
- [x] 接续后 pack_summary 累积正确
- [x] budget 计费 = 1.5
- [x] 边界条件（剩余 < 2）不触发

### Verification commands

- `bash tests/integration/need-fresh-worker.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Pack 5.16

---

## Pack 5.18：guard-doc-edit.sh 加白名单 + 新增 guard-plan-doc-patch.sh

### Goal behavior

两件事：
1. **更新 `guard-doc-edit.sh`**：白名单允许 Worker 写 `${STATE_DIR}/plan-returns/<run_id>/<plan_id>/{plan-return.json, doc-patch.diff, open-items.json}`（路径不在 `docs/` 下本就不触发，本 Pack 做防御性显式声明 + 注释）
2. **新增 `guard-plan-doc-patch.sh`**（调研 D 漏项 #4）：PreToolUse Write matcher on `*.diff`，校验 Worker 写的 `doc-patch.diff` 只触及 `docs/orchestrate/plans/<slug>/<plan_id>-*.md` 的 checkbox 行（`^- \[[ x]\]`）。防 Worker 借 doc-patch 越权改设计文档或其他内容。

### Implementation tasks

1. Read `plugin/hooks/guard-doc-edit.sh`
2. 加注释段说明：「Worker 写 `${STATE_DIR}/plan-returns/...` 是合法的——该路径不在 `docs/` 下，本 hook 不拦截」
3. 创建 `plugin/hooks/guard-plan-doc-patch.sh`：
   - PreToolUse Write，路径匹配 `*doc-patch.diff`
   - 解析 diff 内容：所有 `+/-` 行必须满足 (a) 目标文件是 plan 文档 (b) 只动 checkbox `- [x]` ↔ `- [x]`
   - 失败 → BLOCKED + 输出违规行
4. hooks.json 注册（在 Pack 5.14 统一处理）
5. 测试 fixture：合法 patch / 违规 patch

### Owned files

- Edit: `plugin/hooks/guard-doc-edit.sh`
- Create: `plugin/hooks/guard-plan-doc-patch.sh`
- Create: `tests/hooks/guard-plan-doc-patch.bats`

### Acceptance criteria

- [x] guard-doc-edit.sh 含 plan-returns 路径说明注释
- [x] guard-plan-doc-patch.sh 存在 + 校验逻辑正确
- [x] 合法 patch（只动 checkbox）→ allow
- [x] 违规 patch（动设计文档 / 动非 checkbox 行）→ BLOCKED
- [x] 测试通过

### Verification commands

- `test -x plugin/hooks/guard-plan-doc-patch.sh` → Expected: exit 0
- `bash tests/hooks/guard-plan-doc-patch.bats` → Expected: exit 0

### Risk flags

normal（兜底保险；缺失会让 Worker 通过 doc-patch 越权写文档的风险存在但概率低）

### Dependencies

- 5.9（agent-return-handler 已经定义 doc-patch.diff 写入路径）

---

## Pack 5.19：detect-worker-scope-drift.sh PostToolUse Edit 兜底

### Goal behavior

Worker 自治后 Coordinator 失去中途介入点。Worker 单 session 内连续 commit 5 个 Pack 期间，scope drift 只能靠 hook 兜底。本 Pack 新增 PostToolUse Edit hook，每次 Worker Edit 后比对 changed file 是否在当前 plan 的 owned_files 集合内（从 plan.md 提取）。

### Implementation tasks

1. 创建 `plugin/hooks/detect-worker-scope-drift.sh`
2. PostToolUse Edit matcher（worker-active marker 存在时触发，避免误拦 Coordinator）
3. 从 envelope 取 plan_id + plan_path
4. 解析 plan.md 中所有 `## Pack N.M` 的 `### Owned files` 段，并集为 plan-level owned_files
5. 比对 hook input 中的 file_path：
   - 在 owned_files 内 → allow
   - 在同 plan 其他 pack 的 owned_files → 记录 drift_note，allow（Worker 可能在做交叉 fix）
   - 跨 plan / 完全脱离 → WARN + 记录到 execution-state.plans[N].drift_warnings[]
6. 不直接 BLOCKED（避免打断 Worker session），只记录给 Coordinator 在 Plan 边界审视

### Owned files

- Create: `plugin/hooks/detect-worker-scope-drift.sh`
- Create: `tests/hooks/detect-worker-scope-drift.bats`

### Acceptance criteria

- [x] hook 存在且可执行
- [x] 在 owned_files 内 → 静默通过
- [x] 跨 plan → WARN + 写入 drift_warnings
- [x] 不 BLOCKED（避免打断 Worker）
- [x] 测试覆盖 3 种场景

### Verification commands

- `test -x plugin/hooks/detect-worker-scope-drift.sh` → Expected: exit 0
- `bash tests/hooks/detect-worker-scope-drift.bats` → Expected: exit 0

### Risk flags

normal（不阻断，只兜底；可选 Pack，但用户多次反馈"Worker 自治失去中途介入点"风险，本 Pack 是核心缓解）

---

## Plan-level 验证

```bash
bash plugin/build/build.sh --apply --plugin-dir plugin
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/run-all-tests.sh
bash plugin/scripts/verify-maturity.sh

# Worker Loop 锚点
grep -q 'BEGIN: worker-loop' plugin/agents/pack-executor.md
grep -q 'BEGIN: worker-loop' plugin/agents/complex-pack-executor.md

# 旧 hook 已清除
! test -e plugin/hooks/validate-pack-dispatch.sh
! test -e plugin/hooks/enforce-pack-commit.sh

# 新 hook 存在
test -x plugin/hooks/validate-plan-dispatch.sh
test -x plugin/hooks/enforce-plan-commit.sh

# 端到端
bash tests/integration/worker-loop-e2e.bats
bash tests/integration/need-fresh-worker.bats
```

全部通过 → Plan 005 完成。

## Plan Review History

（待 Plan Implementation Review 后追加）
