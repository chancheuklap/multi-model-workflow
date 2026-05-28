# Issue 002 — 合同与状态机层清理（Contracts & State）

## What to build

把 plugin 的"合同 + 状态机 + Worker Loop 机制"层做系统级清理，覆盖本轮影响最大的几个删除 + 合同重写：

- **删除 Path A 自修分叉**（决策 3）：移除 Path A 概念；所有修复一律走 Path B SendMessage；删除 `state.sh path-a-escalation` 子命令。
- **删除 doc-patch 系统 + Coordinator checkbox toggle 权威规则**（决策 4 / Alignment Review C3 闭合）：
  - 删除 `guard-plan-doc-patch.sh` + `scripts/lib/doc-patch-apply.sh` + `plan-return-v1.json` 的 `doc_patch_path` 字段
  - 修改 `agent-return-handler.sh`：不再暂存 doc-patch.diff，输出 NEXT 指令"Coordinator 须 Edit per_pack[*].status=committed 的 Pack checkbox"
  - 删除 worker-loop.md.tmpl 的"写 doc-patch.diff"步骤
  - **新增权威规则**：Coordinator Edit 的 source-of-truth = `plan-return.per_pack[*]` where `status == committed`；在 `orchestrate-execution/SKILL.md` Step 14 + `plan-review-resolution.md` 写入此规则
- **删除 bug-seed-file 中间文档**（决策 5）：RCA findings 直接进 Discovery；移除 scope contract 中 `bug_seed_path` 可选字段。
- **删除 state.sh agent-context-check + worker-loop segment 5 双路径重写**（决策 6 / Alignment Review C4 闭合）：
  - 删除 `state.sh agent-context-check` 子命令 + 18 处 Worker Loop 内调用
  - worker-loop.md.tmpl segment 5 必须包含两条路径：(a) 正常路径 `packs_in_session += 1`；(b) 启动 / Compaction recovery 路径 从 `execution-state.plans[plan_id].packs[*].status=="committed"` 计数作为初值
- **state.sh 死命令 + scripts/lib 清理**（决策 7 / Alignment Review C2 修正后）：
  - state.sh 删除 `business-summary` / `plans` / `path-a-escalation` 子命令；**保留** `idempotency check/append`
  - 删除 `scripts/lib/review-effectiveness.sh`；合并 `learnings-jsonl.sh` + `learnings-poison-detector.sh`
  - **review_effectiveness 真实 7 处 consumer 清理**：workflow-state-v1.json L10/L83 / state.sh L170/L347 / 2 个 hook test fixtures / test_review_effectiveness.sh 整文件 / learnings-confidence-audit.md L44 / verify-maturity.sh L73 / architecture-draft.md 相关章节
- **删除 Targeted Re-review 机制（全局，本轮 token 经济最大单项）**（决策 13）：
  - 删除 dispatch-envelope-v1.json 的 `review_intent` enum 中 `targeted-re-review` 值
  - 删除 review-dispatch.md.tmpl 的 `[variant=targeted-re-review]` 子模板（**必须在 D1 canonical 抽取之前完成**——执行顺序见决策 1）
  - 删除 plan-gates.md / SKILL.md 中所有 targeted-re-review 描述
  - **review budget 公式 `3P + 12` → `2P + 6`**：`2P` = 每 Plan 2 次（Plan Review + Plan Impl Review）；`+6` = Design Review 2 + Final Review 2 + Release Gate 1 + Multi-PR Integration Review 1
  - 修复后处置改为 Coordinator 自验闭合（grep + Read 验证修复点已落地），不再 reviewer 闭合复审
  - 极端失败走 `root-cause-analyst` 路径

完成本 issue 后：plugin 的合同基线（schema / state / Worker Loop 机制 / review 闭合方式）符合 token economy 目标；下游 Issue 003 才能在已清理的合同上做 phase 级压缩。

## Small issues

### 1. D13a — 删除 .tmpl 中 targeted-re-review 子模板（cross-issue priority）
**Type:** AFK
**What to build:** 在 `plugin/build/templates/review-dispatch.md.tmpl` 中删除 `[variant=targeted-re-review]` 子模板及对应 resolver 入参。此 Pack **必须在 Issue 001 D1 canonical 抽取之前执行**——否则 5 处 targeted-re-review 残留会进入 `_shared/`。
**Acceptance criteria:**
- [ ] `review-dispatch.md.tmpl` 不含 `variant=targeted-re-review` 子模板
- [ ] `build/resolvers/` 对应 resolver 不再处理 targeted-re-review variant
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [ ] 全树 `grep -r "variant=targeted-re-review" plugin/build/templates/` 无结果
**Blocked by:** None（**此小 issue 优先于 Issue 001 全部 Pack 执行**）

### 2. D13b — 全局删除 Targeted Re-review 机制（schema + hooks + budget + SKILL 描述）
**Type:** AFK
**What to build:** 完整落地决策 13——`dispatch-envelope-v1.json` `review_intent` enum 收敛为 `baseline` 单值；`parse-envelope.sh` 删除 enum 校验 + targeted-re-review exception_code 校验；`gate-codex-review.sh` 删除 targeted-re-review 分支 + `--resume` 强制检查（决策 9 关于"保持 exit 2"被本决策推翻）；budget 公式 `3P+12` → `2P+6` 落到 `plan-gates.md` L46 + `orchestrate-plan-writing/SKILL.md` L172；所有 SKILL.md / reference 中 targeted re-review 描述清除；`workflow-state-v1.json` 删除 `self_verifications.exception_code` 相关字段（保留 `disposition_refs`）。
**Acceptance criteria:**
- [ ] `dispatch-envelope-v1.json` `review_intent` enum 仅含 `baseline`（或字段删除）
- [ ] `parse-envelope.sh` 删除 `targeted-re-review` 分支 + exception_code 必填校验
- [ ] `gate-codex-review.sh` 不含 `targeted-re-review` / `--resume` 强制检查代码
- [ ] `plan-gates.md` L46 含 `2P + 6`；`orchestrate-plan-writing/SKILL.md` L172 含 `2P + 6`
- [ ] 全树 grep `targeted-re-review` / `targeted re-review` 仅在 git history / decision rationale 中残留
- [ ] `plugin/hooks/tests/test_envelope_parse.sh` / `test_gate_codex_review.sh` 通过（含新增 baseline-only 用例）
**Blocked by:** 1（必须先删 .tmpl 子模板以免新增 grep 残留）

### 3. D7a — review_effectiveness 删除（lib + schema + 8 处 consumer + 测试）
**Type:** AFK
**What to build:** 删除 `plugin/scripts/lib/review-effectiveness.sh`；清理 8 处真实 consumer：`workflow-state-v1.json` L10/L83 / `state.sh` L170/L347 / `test_agent_id_hook_guard.sh` L59 / `test_effort_budget_weighting.sh` L46 / `test_review_effectiveness.sh` 整文件 / `learnings-confidence-audit.md` L44 / `verify-maturity.sh` L73 / `architecture-draft.md` L703/L756/L940 / `state-lock.sh` L3 注释 / `build/tests/test_review_effectiveness_optional.sh` 整文件（**设计文档 7 处 + 实际探查 +1 处 build/tests，共 8 处 consumer**）。
**Acceptance criteria:**
- [ ] `plugin/scripts/lib/review-effectiveness.sh` 不存在
- [ ] `plugin/scripts/tests/test_review_effectiveness.sh` 不存在
- [ ] `plugin/build/tests/test_review_effectiveness_optional.sh` 不存在
- [ ] `workflow-state-v1.json` `required` 数组 + properties 段均不含 `review_effectiveness`
- [ ] `state.sh` init + required_fields 校验列表不含 `review_effectiveness`
- [ ] `verify-maturity.sh` 不含 `review-effectiveness optional diagnostic` 检查
- [ ] `architecture-draft.md` L703 / L756 / L940 三段对应内容清除
- [ ] `learnings-confidence-audit.md` L44 引用段清除
- [ ] 2 个 hook test fixture 中 `review_effectiveness` 字段移除
- [ ] `state-lock.sh` 顶部注释更新（不再提及 review-effectiveness.sh）
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
**Blocked by:** None（独立于其他 small issue）

### 4. D7b — state.sh 死命令 + scripts/lib poison-detector 合并
**Type:** AFK
**What to build:** 删除 `state.sh` 的 `business-summary` / `plans` 子命令（保留 `idempotency check/append`）+ 对应 test_state.sh 用例；合并 `scripts/lib/learnings-poison-detector.sh` 入 `learnings-jsonl.sh`（poison-detector 改为 function 嵌入）。
**Acceptance criteria:**
- [ ] `bash plugin/scripts/state.sh business-summary --help` exit ≠ 0（命令不存在）
- [ ] `bash plugin/scripts/state.sh plans add --help` exit ≠ 0
- [ ] `bash plugin/scripts/state.sh idempotency check --run-id foo --key bar` 仍可执行（保留）
- [ ] `plugin/scripts/lib/learnings-poison-detector.sh` 不存在；`learnings-jsonl.sh` 内含 poison-detector 函数
- [ ] `plugin/scripts/tests/test_learnings_poison_detection.sh` 调用方式更新且通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
**Blocked by:** None

### 5. D3 — Path A 完全删除（state.sh + schema + hooks + disposition + reference + tests）
**Type:** AFK
**What to build:** 删除 `state.sh path-a-escalation` 子命令；删除 `workflow-state-v1.json` `path_a_escalation` / `blocked_for_self_fix` 字段；`gate-codex-review.sh` 删除 `path-a-re-review` 分支；`dispatch-envelope-v1.json` `review_intent` enum 删除 `path-a-re-review`（D13b 已部分处理，本 Pack 确认收敛）；`validate-plan-dispatch.sh` Step 8 Path A 检查删除；`disposition-table.md.tmpl` 删除 `path-a` 选项（disposition enum 10→9）；删除 `path-a-re-review.md` reference + `test_path_a_re_review.sh` + 5 处 SKILL/reference 中 `state.sh path-a-escalation` 描述 + 3 处 hook test fixture 中 `path_a_escalation: []`。
**Acceptance criteria:**
- [ ] `bash plugin/scripts/state.sh path-a-escalation start --help` exit ≠ 0
- [ ] `workflow-state-v1.json` 不含 `path_a_escalation` / `blocked_for_self_fix`
- [ ] `gate-codex-review.sh` 不含 `path-a-re-review` 分支
- [ ] `dispatch-envelope-v1.json` enum 不含 `path-a-re-review`
- [ ] `disposition-table.md.tmpl` 不含 `path-a` 选项
- [ ] `plugin/skills/orchestrate-execution/references/path-a-re-review.md` 不存在
- [ ] `plugin/scripts/tests/test_path_a_re_review.sh` 不存在
- [ ] 3 hook test fixture（test_need_fresh_worker_continuation / test_worker_loop_e2e / test_validate_plan_dispatch）不含 `path_a_escalation: []`
- [ ] `validate-plan-dispatch.sh` 不含 Step 8 Path A 检查代码
- [ ] 全树 grep `path-a` / `path_a` 在 plan / SKILL.md / reference 中仅在 git history / decision rationale 中残留
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
**Blocked by:** 2（D13b 已处理 `gate-codex-review.sh` 部分清理；本 Pack 完成 path-a-re-review 分支删除）

### 6. D5 — bug-seed-file 删除（中间文档移除）
**Type:** AFK
**What to build:** 删除 `bug-investigation-route.md` 中 "写入 Bug Seed 文件" 步骤 + Scope Contract `bug_seed_path` 字段；`architecture-draft.md` §17 + 任何 SKILL.md 提及 `bug-seed-<run_id>.md` 全清；RCA findings 直接作为 Discovery Source artifact。
**Acceptance criteria:**
- [ ] `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` 不含 "bug-seed-<run_id>.md" / "写入 Bug Seed" 步骤
- [ ] `architecture-draft.md` §17（Bug Seed File）章节删除
- [ ] 全树 grep `bug-seed-path` / `bug_seed_path` / `bug-seed-file` 无残留（git history / decision rationale 除外）
- [ ] `bug-investigation-route.md` 改为 RCA findings 直接进 Scope Contract 的 Source artifacts
**Blocked by:** None

### 7. D4 — doc-patch 系统完全删除 + Coordinator checkbox toggle 权威规则
**Type:** AFK
**What to build:** 删除 `plugin/hooks/guard-plan-doc-patch.sh` + `hooks.json` 中对应条目；删除 `plugin/scripts/lib/doc-patch-apply.sh` + `plugin/scripts/tests/test_doc_patch_apply.sh` + `plugin/hooks/tests/test_guard_plan_doc_patch.sh`；`plan-return-v1.json` 删除 `doc_patch_path` 字段 + description 文本中 "doc-patch.diff" 提及全部重写；`agent-return-handler.sh` 删除 5 处 doc-patch.diff 暂存提示，verdict=pass/partial-pass 时输出新 NEXT 指令"Coordinator: Plan Implementation Review pass 后 Edit per_pack[*].status=committed 的 checkbox"；`worker-loop.md.tmpl` 删除"写 doc-patch.diff"步骤；`pack-executor.md` / `complex-pack-executor.md` 删除 doc-patch.diff 写出指令；`guard-doc-edit.sh` 顶部注释更新（不再提及 doc-patch.diff control-plane）；`architecture-draft.md` 全清 doc-patch / Decision 6 段；**新增权威规则**写入 3 处：`orchestrate-execution/SKILL.md` Step 14 + `orchestrate-plan-writing/references/plan-review-resolution.md` + `agent-return-handler.sh` NEXT 指令——Coordinator Edit 的 source-of-truth = `plan-return.per_pack[*]` where `status == committed`。
**Acceptance criteria:**
- [ ] `plugin/hooks/guard-plan-doc-patch.sh` 不存在
- [ ] `plugin/scripts/lib/doc-patch-apply.sh` 不存在
- [ ] `plugin/scripts/tests/test_doc_patch_apply.sh` + `plugin/hooks/tests/test_guard_plan_doc_patch.sh` 不存在
- [ ] `plugin/hooks/hooks.json` 不含 `guard-plan-doc-patch.sh` 条目
- [ ] `plan-return-v1.json` 不含 `doc_patch_path` 字段 + description 文本不含 "doc-patch.diff"
- [ ] `agent-return-handler.sh` 不含 "doc-patch.diff" 字符串；含 "per_pack[*].status=committed" 输出
- [ ] `worker-loop.md.tmpl` 不含 "doc-patch.diff" 字符串
- [ ] `pack-executor.md` + `complex-pack-executor.md` 不含 "doc-patch" 字符串
- [ ] `architecture-draft.md` §7.5 / Decision 6 段删除
- [ ] `orchestrate-execution/SKILL.md` Step 14 含 "per_pack[*].status == committed" 表述
- [ ] `plan-review-resolution.md` 含 Coordinator checkbox toggle 权威规则
- [ ] 全树 grep `doc-patch` / `doc_patch` 无残留（git history / decision rationale 除外）
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
**Blocked by:** None

### 8. D6 — agent-context-check 删除 + worker-loop segment 5 双路径
**Type:** AFK
**What to build:** 删除 `state.sh agent-context-check` 子命令（L982-1030 函数 + L2124 dispatcher case） + `test_state_agent_context_check.sh` 整文件；删除 11 处实际调用点（亲验 grep 结果）：`worker-loop.md.tmpl` L55/L100 / `pack-executor.md` L114/L159 / `complex-pack-executor.md` L112/L157/L187 / `architecture-draft.md` L215/L355/L739/L1240；**重写 `worker-loop.md.tmpl` segment 5** 必须包含两条路径（main flow 内）：(a) 正常路径 `packs_in_session += 1`；(b) 启动 / Compaction recovery 路径 从 `execution-state.plans[plan_id].packs[*].status=="committed"` 计数作为初值。
**Acceptance criteria:**
- [ ] `bash plugin/scripts/state.sh agent-context-check --help` exit ≠ 0
- [ ] `plugin/scripts/tests/test_state_agent_context_check.sh` 不存在
- [ ] `worker-loop.md.tmpl` segment 5 同时含 `packs_in_session += 1`（正常路径）和 `execution-state.plans[*].packs[*].status` 或同义"从 execution-state 重建 counter"表述（启动 / recovery 路径）
- [ ] `pack-executor.md` / `complex-pack-executor.md` 不含 `state.sh agent-context-check` 字符串
- [ ] `architecture-draft.md` L215/L355/L739/L1240 对应内容更新或删除
- [ ] 全树 grep `agent-context-check` 在 .sh / .md 中无残留（git history / decision rationale 除外）
- [ ] `bash plugin/build/build.sh --apply --plugin-dir plugin && bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
**Blocked by:** None

## Blocked by

- **001 (Infrastructure)** — D13 删 Targeted Re-review 必须先于 D1 canonical 抽取完成（决策 1 与决策 13 执行顺序声明），且 D7 review_effectiveness 删除需要 D1 完成后的 canonical reference 引用基线。**例外**：本 issue 的 Small issue 1 (D13a — 删除 .tmpl 中 targeted-re-review 子模板) **必须先于 Issue 001 全部 Pack 执行**，其他 Small issues 2-8 在 Issue 001 完成后执行。
