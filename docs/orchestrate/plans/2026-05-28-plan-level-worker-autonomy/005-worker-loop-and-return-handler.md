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

## Plan Acceptance Criteria

- [ ] `pack-executor.md` + `complex-pack-executor.md` 加 Worker Loop 段（template 注入）
- [ ] Worker 在 Plan 边界写 3 个 artifact（plan-return.json / doc-patch.diff / open-items.json）至 `plan-returns/<run_id>/<plan_id>/`
- [ ] `validate-pack-dispatch.sh` 改为 `validate-plan-dispatch.sh`（校验 envelope.plan_id 存在 + plan.md 存在 + Pack Execution Manifest 就绪）
- [ ] `agent-return-handler.sh` 重写：解析 artifact → apply doc-patch → 触发 Plan-level review dispatch（不再 per-Pack）
- [ ] `track-execution-state.sh` 改为聚合 pack_summary（每 Pack 完成 transition 触发后台累加，Plan 完成后写 execution-state.plans[N].pack_summary）
- [ ] `enforce-pack-commit.sh` 改为 enforce-plan-commit（Plan 完成前 git checkpoint 至少 N 次，N = pack 数）
- [ ] `guard-doc-edit.sh` 保留（Worker 仍不能动 docs/；Worker 改 plan.md 勾选通过 doc-patch.diff 由 Coordinator apply）
- [ ] `track-effort-budget.sh` 改为 Plan-level 计费（一个 Plan 算一次 Worker dispatch + 一次 Review dispatch）
- [ ] `state.sh` 新增/改写 5 个子命令：`agent-id --plan-id`、`disposition --plan-id`、`agent-context-check`、`pack-progress` (Worker 内部用)、`plan-complete`
- [ ] `dispatch-envelope-v1.json` 加 `plan_id` 字段
- [ ] Worker Loop 7 步全部测试覆盖
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
- [ ] `bash plugin/scripts/verify-maturity.sh` 通过

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

---

## Pack 5.1：worker-loop template + resolver 新增

### Goal behavior

新增 `plugin/build/templates/worker-loop.md.tmpl`（Worker Loop 7 步 + Context 自监控段）和 `plugin/build/resolvers/worker-loop.sh`（注入 pack-executor.md 和 complex-pack-executor.md）。template 内容由设计文档 Worker Loop 合同段定义。

### Implementation tasks

1. Read `plugin/build/templates/`（参考现有 template 结构）
2. Read `plugin/build/resolvers/`（参考现有 resolver）
3. 创建 `plugin/build/templates/worker-loop.md.tmpl`，内容包含：
   - `## Worker Loop（7 步）` 段
     1. Read DISPATCH_ENVELOPE → 取 plan_id、run_id、plan_path
     2. Read plan.md（含 Pack Execution Manifest）
     3. Read execution-worker-dispatch.md（执行手册）
     4. 进入 Pack 循环：对每个 manifest pack
        - Pack TDD（red → green → refactor）
        - Run verification commands
        - `state.sh pack-progress --pack-id <id> --status complete`
        - git commit（按 enforce-plan-commit 规则）
        - 调用 `state.sh agent-context-check`，若返回 `need-fresh-worker` → break 进入 5
     5. Plan 完成 / Context 触发 → 写 3 个 artifact 到 `plan-returns/<run_id>/<plan_id>/`：
        - `plan-return.json`（verdict + pack 完成状态 + open_items_path + doc_patch_path）
        - `doc-patch.diff`（plan.md / design.md 勾选 patch）
        - `open-items.json`（未完成 Pack / 阻塞项 / repair 建议）
     6. `state.sh plan-complete --plan-id <plan_id> --verdict <verdict>`
     7. exit（让 SubagentStop hook 触发 agent-return-handler.sh）
   - `## Context 自监控` 段（pack-count heuristic, threshold=5）
4. 创建 `plugin/build/resolvers/worker-loop.sh`：
   - 读 template
   - 替换变量
   - 注入到 `pack-executor.md` 和 `complex-pack-executor.md` 的 `<!-- BEGIN: worker-loop -->` / `<!-- END: worker-loop -->` 锚点
5. `bash plugin/build/build.sh --apply --plugin-dir plugin` 验证 resolver 正常工作

### Owned files

- Create: `plugin/build/templates/worker-loop.md.tmpl`
- Create: `plugin/build/resolvers/worker-loop.sh`

### Read first

- 设计文档「Worker Loop 合同」段
- 现有 template / resolver 样例（如 `review-dispatch`）

### Acceptance criteria

- [ ] worker-loop.md.tmpl 存在且含 7 步 + Context 自监控段
- [ ] worker-loop.sh resolver 可执行
- [ ] `build.sh --apply` 能注入到 pack-executor.md（验证 Pack 5.2）
- [ ] 模板含 plan-return.json schema 引用

### Verification commands

- `test -f plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `test -x plugin/build/resolvers/worker-loop.sh` → Expected: exit 0
- `grep -q 'Worker Loop' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0
- `grep -q 'agent-context-check' plugin/build/templates/worker-loop.md.tmpl` → Expected: exit 0

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

- [ ] 两个 agent 文件含 `BEGIN: worker-loop` 锚点
- [ ] `build.sh --apply` + `--check` 通过
- [ ] complex-pack-executor 含高风险自检 checklist

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

定义 `plan-return.json` 和 `open-items.json` 的 JSON schema，存放至 `plugin/state-schema/`。这是 Worker → Coordinator 的合同。

### Implementation tasks

1. Read `plugin/state-schema/`（参考现有 schema 风格）
2. 创建 `plugin/state-schema/plan-return-v1.json`：
   - schema_version, run_id, plan_id, started_at, finished_at
   - verdict: `complete` | `partial` | `blocked` | `need-fresh-worker`
   - pack_results: array of {pack_id, status: `done|skipped|blocked`, commits[], verification_passed: bool}
   - doc_patch_path: relative path to doc-patch.diff
   - open_items_path: relative path to open-items.json
   - context_snapshot: {packs_in_session, agent_context_check_result}
3. 创建 `plugin/state-schema/open-items-v1.json`：
   - schema_version, plan_id
   - items: array of {kind: `repair|defer|blocked`, pack_id, finding, suggested_action}
4. Pack 002 Pack 2.7 已定义 pack-returns 目录结构；本 Pack 是 plan-returns（Plan-level 粒度）。
5. README 更新 schema 索引

### Owned files

- Create: `plugin/state-schema/plan-return-v1.json`
- Create: `plugin/state-schema/open-items-v1.json`
- Edit: `plugin/state-schema/README.md`（如有）

### Read first

- 现有 schema 文件
- 设计文档 Worker Loop artifact 段

### Acceptance criteria

- [ ] 2 个 schema 文件存在且 JSON 合法
- [ ] verdict 枚举完整（`complete|partial|blocked|need-fresh-worker`）
- [ ] schema_version = "1"

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

- [ ] state.sh agent-context-check 子命令存在
- [ ] mock 测试：packs_in_session=5, remaining=2 → need-fresh-worker
- [ ] mock 测试：packs_in_session=3, remaining=5 → ok

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

- [ ] state.sh agent-id --plan-id <id> 可正确写入
- [ ] 无 --plan-id 时保持向后兼容（旧行为）
- [ ] lock 保护正常

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

- [ ] disposition 写入含 plan_id 字段
- [ ] 无 --plan-id 时保持向后兼容
- [ ] 单测通过

### Verification commands

- `bash plugin/scripts/state.sh disposition --plan-id p1 --gate plan-review --verdict pass --reviewer codex` → Expected: exit 0
- 验证 workflow-state.json review_dispositions 末尾含 plan_id

### Risk flags

normal

### Dependencies

- Plan 002 Pack 2.4 + 2.6

---

## Pack 5.7：state.sh pack-progress + plan-complete 子命令

### Goal behavior

Worker 内部用：`pack-progress` 标记单 Pack 完成（触发 track-execution-state 聚合）；`plan-complete` 标记整 Plan 完成（关闭 plan-returns 目录，触发 SubagentStop 后 handler 读取）。

### Implementation tasks

1. Read state.sh
2. 加 `pack-progress`：
   - 入参 `--plan-id <id> --pack-id <id> --status complete|skipped|blocked --commit-sha <sha>`
   - 写 execution-state.plans[N].pack_summary.packs[]
3. 加 `plan-complete`：
   - 入参 `--plan-id <id> --verdict <v>`
   - 写 execution-state.plans[N].finished_at + verdict
4. 单测

### Owned files

- Edit: `plugin/scripts/state.sh`

### Acceptance criteria

- [ ] 两个子命令存在且正确写状态
- [ ] 写入受 lock 保护
- [ ] 单测通过

### Verification commands

- `bash plugin/scripts/state.sh pack-progress --plan-id p1 --pack-id 5.1 --status complete --commit-sha abc1234` → Expected: exit 0
- `bash plugin/scripts/state.sh plan-complete --plan-id p1 --verdict complete` → Expected: exit 0

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

- [ ] validate-plan-dispatch.sh 存在且可执行
- [ ] envelope 缺 plan_id → deny
- [ ] plan.md 缺 Pack Execution Manifest → deny
- [ ] 正常 envelope → allow
- [ ] 旧 validate-pack-dispatch.sh 已删除

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

Worker SubagentStop 触发，handler 现在按 **Plan 边界**处理：
1. 解析 SubagentStop payload 取 agent_id + run_id
2. 查 execution-state.plans 找到该 worker_agent_id 对应的 plan_id
3. Read `plan-returns/<run_id>/<plan_id>/plan-return.json`
4. 按 verdict 路由：
   - `complete`：apply doc-patch.diff（用 lib/doc-patch-apply.sh）→ 触发 Plan-level review dispatch（写 trigger marker）→ state.sh plan-complete --verdict complete
   - `partial`：apply doc-patch.diff（仅完成 Pack 部分）→ open-items 转 review dispatch 评估
   - `blocked`：不 apply doc-patch → 触发 BLOCKED 路由（与现状一致）
   - `need-fresh-worker`：apply doc-patch（部分） → 触发 Coordinator 新 Agent dispatch（写新 envelope 含 resume_from_pack_id）

### Implementation tasks

1. Read `plugin/hooks/agent-return-handler.sh`（现状）
2. 结构性重写：
   - 调用 `lib/plan-return-parser.sh` 解析 artifact（Pack 5.15 提供）
   - 调用 `lib/doc-patch-apply.sh` apply patch（Pack 5.15 提供）
   - 按 verdict 路由 4 路
   - 每路由都要写 disposition / progress marker
3. 失败保护：parse 失败 / 缺 artifact → 写 BLOCKED + 通知 Coordinator
4. 测试 fixture 覆盖 4 路 verdict

### Owned files

- Rewrite: `plugin/hooks/agent-return-handler.sh`
- Create: `tests/hooks/agent-return-handler.bats`（Pack 5.16 补全 fixture）

### Read first

- 当前 agent-return-handler.sh
- 设计文档 verdict 路由表
- Pack 5.3 schema

### Acceptance criteria

- [ ] 4 路 verdict 均有显式分支
- [ ] apply doc-patch 在 `complete|partial|need-fresh-worker` 三路触发
- [ ] `blocked` 路径不 apply patch
- [ ] 缺 artifact → BLOCKED 输出
- [ ] need-fresh-worker → 写新 envelope marker 含 resume_from_pack_id

### Verification commands

- `test -x plugin/hooks/agent-return-handler.sh` → Expected: exit 0
- `shellcheck plugin/hooks/agent-return-handler.sh` → Expected: exit 0
- Pack 5.16 端到端测试

### Risk flags

high（结构性重写，多路状态写入）

### Dependencies

- Pack 5.3, 5.5, 5.6, 5.7, 5.15

---

## Pack 5.10：track-execution-state.sh 重写为 pack_summary 聚合

### Goal behavior

旧 hook 每 PostToolUse / Stop 写一次 execution-state.current_pack。新 hook 改为：监听 `state.sh pack-progress` 调用 → 追加 execution-state.plans[N].pack_summary.packs[]；Plan 完成时（state.sh plan-complete）聚合 pack_summary.total / completed / failed / commits[]。

### Implementation tasks

1. Read 当前 `track-execution-state.sh`
2. 重写聚合逻辑：
   - 监听 state.sh pack-progress 调用（hook input 含 subcommand 参数）
   - 追加 packs[]（保留每 Pack 状态 / commit_sha / verified_at）
   - 监听 state.sh plan-complete → 聚合 total / completed / failed / commits
3. lock 保护
4. 测试 fixture

### Owned files

- Rewrite: `plugin/hooks/track-execution-state.sh`
- Create/Edit: `tests/hooks/track-execution-state.bats`

### Read first

- 当前 track-execution-state.sh
- Plan 002 Pack 2.5 execution-state schema（plans[N].pack_summary）

### Acceptance criteria

- [ ] hook 监听 state.sh pack-progress → 追加 packs[]
- [ ] hook 监听 state.sh plan-complete → 聚合 summary
- [ ] lock 保护，并发写无丢失
- [ ] 测试覆盖 Pack→Plan 整链路

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

- [ ] 重命名完成
- [ ] commit 缺失 → deny
- [ ] commit 数 < 完成 Pack 数 → deny
- [ ] 测试覆盖 pass / fail

### Verification commands

- `bash tests/hooks/enforce-plan-commit.bats` → Expected: exit 0

### Risk flags

normal

---

## Pack 5.12：track-effort-budget.sh Plan-level 计费

### Goal behavior

旧 hook 每 Pack dispatch + 每 Pack review 各算一次。新 hook 改为：
- 一个 Plan 的 Worker dispatch 算 1 次（不论 Worker 用了几个 Pack）
- 一个 Plan 的 Codex Review 算 1 次
- need-fresh-worker continuation 算 0.5 次（合理近似）

### Implementation tasks

1. Read `track-effort-budget.sh`
2. 改写计费规则：监听 envelope.plan_id 去重
3. need-fresh-worker resume：检查 envelope 是否含 `resume_from_pack_id`，若有 → 计 0.5
4. 输出 budget marker 到 effort-state.json
5. 测试

### Owned files

- Edit: `plugin/hooks/track-effort-budget.sh`
- Edit: `tests/hooks/track-effort-budget.bats`

### Acceptance criteria

- [ ] Plan-level 去重计费正常
- [ ] need-fresh-worker 计 0.5
- [ ] 测试通过

### Verification commands

- `bash tests/hooks/track-effort-budget.bats` → Expected: exit 0

### Risk flags

normal

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

- [ ] parse-envelope.sh 输出 PLAN_ID
- [ ] 5 个 hook 统一调用 lib
- [ ] envelope 无 plan_id → 5 个 hook 均能给出明确错误

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

- [ ] hooks.json JSON 合法
- [ ] 所有旧 hook 名替换完成
- [ ] run-all-tests 通过

### Verification commands

- `python3 -m json.tool plugin/hooks/hooks.json > /dev/null` → Expected: exit 0
- `! grep -q 'validate-pack-dispatch' plugin/hooks/hooks.json` → Expected: exit 0
- `! grep -q 'enforce-pack-commit' plugin/hooks/hooks.json` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: exit 0

### Risk flags

high（hook 触发链路总入口，错一行整个 plugin 失效）

### Dependencies

- Pack 5.8, 5.9, 5.10, 5.11

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

- [ ] 2 个 lib 文件可 source
- [ ] parser 输出变量正确
- [ ] doc-patch-apply 冲突时不污染 working tree
- [ ] 单测覆盖

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

- [ ] 4 路 verdict 端到端测试全部通过
- [ ] doc-patch apply 后 git working tree 干净 + 文件已修改
- [ ] state 写入符合 schema

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

- [ ] need-fresh-worker 路径完整跑通
- [ ] 接续后 pack_summary 累积正确
- [ ] budget 计费 = 1.5
- [ ] 边界条件（剩余 < 2）不触发

### Verification commands

- `bash tests/integration/need-fresh-worker.bats` → Expected: exit 0

### Risk flags

normal

### Dependencies

- Pack 5.16

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
