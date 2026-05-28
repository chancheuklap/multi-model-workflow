# 合同与状态机层清理（Contracts & State）Implementation Plan

**Goal:** 把 plugin 的合同 + 状态机 + Worker Loop 机制层做系统级清理——删 Path A 自修分叉 / 删 doc-patch 系统 + 落地 Coordinator checkbox toggle 权威规则 / 删 bug-seed-file 中间文档 / 删 state.sh agent-context-check 并重写 worker-loop segment 5 双路径 / 清理 state.sh 死命令 + scripts/lib + review_effectiveness 8 处真实 consumer / 全局删除 Targeted Re-review 机制并落地 budget 公式 `3P+12 → 2P+6`。

**Source design:** docs/orchestrate/design/2026-05-28-workflow-token-economy.md
**Source issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md
**Execution owner:** Orchestrate Workflow
**Blocked by:** 001 (Infrastructure) — 但 **Pack 2.1 必须优先于 Issue 001 全部 Pack 执行**（cross-issue priority；执行顺序见 Pack 2.1 Dependencies）；Pack 2.2-2.8 在 Issue 001 完成后执行。
**Architecture:** 删除自挖坑机制 → 收敛合同表面 → 删 11 处实际调用点（亲验 grep 结果：worker-loop.md.tmpl L55+L100 / pack-executor L114+L159 / complex-pack-executor L112+L157+L187 / architecture-draft L215+L355+L739+L1240；设计文档 D6 描述的 "18 处" 含 architecture-draft 文中重复提及和流程图节点） + 8 处 consumer + 5 处 hook test fixture + 5 处 SKILL/reference 描述。**不动**：Worker Loop 6 段合同 semantics / Document-as-Context 主线 / Codex Review 5 步派发协议 / guard-doc-edit.sh / track-execution-state.sh / track-effort-budget.sh / per_pack 必填字段。
**Tech stack:** bash / jq / Python（hook 解析）/ JSON Schema / Markdown templates / build.sh resolver。
**Quality gate:** 进入 Plan Review 前必须通过过度设计 / 设计不足自审。

## File / Responsibility Map

**Create:** （本 plan 不创建新文件——所有改动为删除或修改）

**Modify (state schemas):**
- `plugin/state-schema/workflow-state-v1.json` — 删除 `path_a_escalation` / `blocked_for_self_fix` / `bug_seed_path` / `review_effectiveness`（D3 + D5 + D7a）
- `plugin/state-schema/dispatch-envelope-v1.json` — `review_intent` enum 收敛为 `baseline` 单值（D13b + D3 cascade）
- `plugin/state-schema/plan-return-v1.json` — 删除 `doc_patch_path` 字段 + description 中 doc-patch.diff 提及（D4）

**Modify (hooks):**
- `plugin/hooks/gate-codex-review.sh` — 删除 `targeted-re-review` / `path-a-re-review` / `--resume` 强制检查分支（D3 + D13b）
- `plugin/hooks/lib/parse-envelope.sh` — 删除 review_intent enum 校验 + targeted-re-review exception_code 校验（D13b）
- `plugin/hooks/agent-return-handler.sh` — 删除 5 处 doc-patch.diff 暂存提示，verdict=pass/partial-pass 时输出新 NEXT "Coordinator: Edit per_pack[*].status=committed 的 checkbox"（D4）
- `plugin/hooks/validate-plan-dispatch.sh` — 删除 Step 8 Path A 检查（D3）
- `plugin/hooks/guard-doc-edit.sh` — 顶部注释更新（不再提及 doc-patch.diff control-plane）（D4）
- `plugin/hooks/hooks.json` — 删除 `guard-plan-doc-patch.sh` 条目（D4）

**Delete (hooks):**
- `plugin/hooks/guard-plan-doc-patch.sh`（D4）

**Modify (state.sh + scripts):**
- `plugin/scripts/state.sh` — 删除 4 个子命令（`business-summary` / `plans` / `path-a-escalation` / `agent-context-check`）+ 删除 init 的 `review_effectiveness` 字段 + required_fields 校验列表清理（D3 + D6 + D7a + D7b）
- `plugin/scripts/learnings-jsonl.sh` — 内联 poison-detector 为 function（D7b）
- `plugin/scripts/lib/state-lock.sh` — 顶部注释更新（不再提及 review-effectiveness.sh）（D7a）
- `plugin/scripts/verify-maturity.sh` — 删除 L73 review-effectiveness 检查（D7a）

**Delete (scripts/lib):**
- `plugin/scripts/lib/review-effectiveness.sh`（D7a）
- `plugin/scripts/lib/learnings-poison-detector.sh`（D7b — 合并入 learnings-jsonl.sh）
- `plugin/scripts/lib/doc-patch-apply.sh`（D4）

**Modify (templates):**
- `plugin/build/templates/review-dispatch.md.tmpl` — 删除 `[variant=targeted-re-review]` 子模板（D13a）
- `plugin/build/templates/worker-loop.md.tmpl` — 删除"写 doc-patch.diff"步骤；重写 segment 5 双路径（packs_in_session += 1 + execution-state 重建 counter）；删除 2 处 `state.sh agent-context-check` 调用（D4 + D6）
- `plugin/build/templates/disposition-table.md.tmpl` — 删除 `path-a` 选项（disposition enum 10→9）（D3）
- `plugin/build/resolvers/`（对应 review-dispatch resolver）— 删除 targeted-re-review variant 处理（D13a）

**Modify (agents):**
- `plugin/agents/pack-executor.md` — 删除 doc-patch.diff 写出指令（L114-L184 共 5 处）+ 删除 2 处 `state.sh agent-context-check` 调用（L114/L159）（D4 + D6）
- `plugin/agents/complex-pack-executor.md` — 删除 doc-patch.diff 写出指令（L112-L187 共 8 处）+ 删除 3 处 `state.sh agent-context-check` 调用（L112/L157/L187）（D4 + D6）

**Modify (SKILL.md):**
- `plugin/skills/orchestrate-execution/SKILL.md` — Step 14 写入 Coordinator checkbox toggle 权威规则（D4）；删除 L428 `state.sh path-a-escalation` 描述（D3）
- `plugin/skills/orchestrate-plan-writing/SKILL.md` — L172 budget 公式 `3P + 12` → `2P + 6`（D13b）；L235 删除 `state.sh path-a-escalation` 描述（D3）
- `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` — 删除 targeted-re-review 描述（D13b cascade in this issue scope，仅删除合同表面提及；Issue 003 处理具体 reference 内容压缩）
- `plugin/skills/orchestrate-final-review/SKILL.md` — 同上（仅删除 targeted-re-review 提及）

**Modify (references):**
- `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` — L46 budget 公式 `3P + 12` → `2P + 6`（D13b）
- `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md` — L56 删除 `state.sh path-a-escalation` 描述（D3）；写入 Coordinator checkbox toggle 权威规则（D4）
- `plugin/skills/orchestrate-discovery/references/design-review-angles.md` — L306 删除 `state.sh path-a-escalation` 描述（D3）
- `plugin/skills/orchestrate-final-review/references/final-review-disposition.md` — L56 删除 `state.sh path-a-escalation` 描述（D3）
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` — L228 删除 `state.sh path-a-escalation` 描述（D3）
- `plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md` — L44 删除 review-effectiveness.sh 引用段（D7a）
- `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` — 删除"写入 Bug Seed 文件" Step + Scope Contract `bug_seed_path` 字段（D5）

**Delete (references):**
- `plugin/skills/orchestrate-execution/references/path-a-re-review.md`（D3）

**Modify (architecture-draft.md):**
- `plugin/architecture-draft.md` — 删除多处：L215 / L355 / L739 / L1240（agent-context-check）+ §17（Bug Seed File）（D5）+ §7.5 / Decision 6 段（D4）+ L703 / L756 / L940 review_effectiveness（D7a）+ §11.4 + §13 review intent 表 targeted-re-review 相关行（D13b）+ Path A 相关段（L901 / L904）（D3）

**Delete (tests — 与子命令/lib 删除同步):**
- `plugin/scripts/tests/test_review_effectiveness.sh`（D7a）
- `plugin/build/tests/test_review_effectiveness_optional.sh`（D7a — 设计文档遗漏的第 8 处 consumer，已亲验存在）
- `plugin/scripts/tests/test_path_a_re_review.sh`（D3）
- `plugin/scripts/tests/test_state_agent_context_check.sh`（D6）
- `plugin/scripts/tests/test_doc_patch_apply.sh`（D4）
- `plugin/hooks/tests/test_guard_plan_doc_patch.sh`（D4）

**Modify (test fixtures):**
- `plugin/hooks/tests/test_agent_id_hook_guard.sh` — L59 删除 `review_effectiveness` + L61 `path_a_escalation` 字段（D3 + D7a）
- `plugin/hooks/tests/test_effort_budget_weighting.sh` — L46 删除 `review_effectiveness` + L48 `path_a_escalation` 字段（D3 + D7a）
- `plugin/hooks/tests/test_need_fresh_worker_continuation.sh` — L43 删除 `path_a_escalation: []`（D3）
- `plugin/hooks/tests/test_worker_loop_e2e.sh` — L43 删除 `path_a_escalation: []`（D3）
- `plugin/hooks/tests/test_validate_plan_dispatch.sh` — L18 删除 `path_a_escalation: []`（D3）
- `plugin/hooks/tests/test_envelope_parse.sh` — 新增 baseline-only 用例 + 删除 targeted-re-review exception_code 用例（D13b）
- `plugin/hooks/tests/test_gate_codex_review.sh` — 删除 targeted-re-review 分支 + --resume 用例（D13b）

**Test (new behavior covered):**
- 现有 57 个 hook test suite 全过（fixture 已同步）
- 新增 baseline-only review_intent 用例（test_envelope_parse.sh + test_gate_codex_review.sh）

**Docs / rules / registry / migration / release gate:**
- `plugin/scripts/verify-maturity.sh` — 加 grep 检查 6 项：(a) workflow-state 不含 `path_a_escalation` / `blocked_for_self_fix` / `bug_seed_path` / `review_effectiveness`；(b) `gate-codex-review.sh` 不含 `targeted-re-review` / `--resume` 关键字；(c) `state.sh` 不支持 4 个删除的子命令；(d) review_effectiveness 8 处 consumer 全清；(e) `worker-loop.md.tmpl` segment 5 含两条路径关键字串；(f) D4 Coordinator checkbox toggle 规则在 3 处落地（SKILL.md Step 14 + plan-review-resolution.md + agent-return-handler.sh NEXT 输出）
- 无 migration（state.sh validate 对未知字段 graceful ignore，旧 run 不需要迁移）
- 无 release gate（plugin 内部重构，无用户可感知功能变化）

## 发布风险和人工门禁

| 风险面 | Task Pack | Risk flag | 提前 review | Manual gate owner |
| --- | --- | --- | --- | --- |
| Build template 删除 targeted-re-review variant 影响 build resolver | Pack 2.1 | normal | build.sh --check 验证 | 自动 |
| Schema 字段删除影响旧 workflow-state JSON 兼容 | Pack 2.2 / 2.5 / 2.7 | normal | state.sh validate 对未知字段 graceful ignore | 自动 |
| Hook 删除（guard-plan-doc-patch.sh）影响 doc-patch 流程 | Pack 2.7 | normal | hooks.json 同步更新；agent-return-handler 改 NEXT 指令 | 自动 |
| Worker Loop segment 5 双路径写错（漏 recovery path）→ long-running worker context 溢出 | Pack 2.8 | high-risk | verify-maturity grep 两条路径关键字串 | 自动 |
| Coordinator checkbox toggle 权威规则未落地 → Coordinator 不知如何 Edit plan | Pack 2.7 | high-risk | grep `per_pack[*].status == committed` 3 处落地 | 自动 |
| budget 公式 `3P+12 → 2P+6` 未同步 → effort budget 计算错乱 | Pack 2.2 | normal | grep `2P + 6` 在 plan-gates.md / SKILL.md L172 | 自动 |

---

### Task Pack 2.1: D13a — 删除 .tmpl 中 targeted-re-review 子模板（cross-issue priority）

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 1

**Goal behavior:** `review-dispatch.md.tmpl` 中 `[variant=targeted-re-review]` 子模板及其 resolver 入参完全删除；build.sh --check 通过；此 Pack 在 Issue 001 D1 canonical 抽取之前完成，避免 5 处 targeted-re-review 残留进入 `plugin/skills/_shared/`。

**Owned files / responsibilities:**
- Modify: `plugin/build/templates/review-dispatch.md.tmpl` — 删除 `[variant=targeted-re-review]` 子模板段
- Modify: `plugin/build/resolvers/`（具体 resolver 文件由 Worker grep 定位，预计 `resolve-review-dispatch.sh` 或类似）— 删除 targeted-re-review variant 处理逻辑
- Test: 无新增 test；通过 `bash plugin/build/build.sh --check --plugin-dir plugin` 验证

**Read first:**
- `plugin/build/templates/review-dispatch.md.tmpl`（理解当前 variant 结构）
- `plugin/build/README.md`（理解 resolver 工作流）
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 13 + §4.2 决策 1 中"与决策 13 的执行顺序"段

**Contract anchors:**
- Owner: build template system
- Producer: `build/resolvers/*.sh`
- Consumer: 所有含 `<!-- BEGIN: review-dispatch -->` 锚点的 SKILL.md / reference.md（11 处）
- Verification: build.sh --check 不报错 + grep `variant=targeted-re-review` 在 `plugin/build/templates/` 无结果

**Acceptance criteria:**
- [ ] `plugin/build/templates/review-dispatch.md.tmpl` 不含 `variant=targeted-re-review` 子模板段
- [ ] `plugin/build/resolvers/` 中 review-dispatch 相关 resolver 不再处理 `targeted-re-review` variant
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` 退出码 0
- [ ] `grep -rn "variant=targeted-re-review" plugin/build/templates/` 无结果

**Verification commands:**
- `grep -rn "variant=targeted-re-review" plugin/build/templates/` → Expected: 无输出
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: 通过（exit 0）

**Commit boundary:** 一个 atomic commit：删除 targeted-re-review variant 子模板 + resolver 处理代码
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None（**cross-issue priority**：必须先于 Issue 001 全部 Pack 执行）
**Out of scope:** 不动 `review-dispatch.content-only` variant（codex-review skill 范围，§10 第 15 条）；不抽取 canonical reference（Issue 001 D1 处理）

#### Implementation tasks

- [ ] Step 1: Read 当前 review-dispatch.md.tmpl 结构 + 定位 targeted-re-review variant 段
  - 文件: `plugin/build/templates/review-dispatch.md.tmpl`
  - Behavior: grep `variant=targeted-re-review` 找到子模板起止行
  - Run: `grep -n "variant=targeted-re-review\|END.*targeted-re-review" plugin/build/templates/review-dispatch.md.tmpl` → Expected: 找到起止行号

- [ ] Step 2: 定位对应 resolver 文件
  - Run: `grep -rln "variant=targeted-re-review\|targeted-re-review" plugin/build/resolvers/` → Expected: 1-2 个 resolver 文件
  - Behavior: 阅读 resolver 内 handling logic，标记需删除的代码段

- [ ] Step 3: 写失败的 build check（Red）
  - Run: 先 `bash plugin/build/build.sh --apply --plugin-dir plugin` 重建一次 baseline；记录当前 inject 位置数
  - Expected: 当前 build 通过；记录 11 个 .md 文件含 `<!-- BEGIN: review-dispatch -->` 锚点

- [ ] Step 4: 删除 .tmpl 中 targeted-re-review variant 子模板
  - 文件: `plugin/build/templates/review-dispatch.md.tmpl`
  - 动作: Edit 删除 `variant=targeted-re-review` 起止段（用 Step 1 找到的行号定位）

- [ ] Step 5: 删除 resolver 中 targeted-re-review variant 处理
  - 文件: Step 2 定位的 resolver
  - 动作: Edit 删除 targeted-re-review 分支代码

- [ ] Step 6: 跑 build check 验证
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
  - Run: `bash plugin/build/build.sh --apply --plugin-dir plugin` → Expected: 11 个目标文件中 targeted-re-review 段被移除

- [ ] Step 7: 全树验证无残留
  - Run: `grep -rn "variant=targeted-re-review" plugin/build/templates/` → Expected: 无输出

- [ ] Step 8: Suggested commit boundary
  - Message: `feat(build): D13a 删除 review-dispatch targeted-re-review variant 子模板（cross-issue priority for Issue 001 D1）`

---

### Task Pack 2.2: D13b — 全局删除 Targeted Re-review 机制（schema + hooks + budget + 描述）

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 2

**Goal behavior:** `dispatch-envelope-v1.json` `review_intent` enum 收敛为 `baseline` 单值（保留 `path-a-re-review` 由 Pack 2.5 删除）；`parse-envelope.sh` + `gate-codex-review.sh` 删除 targeted-re-review 处理（含 `--resume` 强制检查——决策 9 关于"保持 exit 2"被本决策推翻）；budget 公式 `3P + 12` → `2P + 6` 落到 plan-gates.md L46 + orchestrate-plan-writing/SKILL.md L172；所有 SKILL.md / reference 中 targeted re-review 描述清除；workflow-state-v1.json `self_verifications.exception_code` 相关字段清理。

**Owned files / responsibilities:**
- Modify: `plugin/state-schema/dispatch-envelope-v1.json` — `review_intent` enum 改为 `["baseline"]`（path-a-re-review 留给 Pack 2.5）
- Modify: `plugin/hooks/lib/parse-envelope.sh` — 删除 targeted-re-review 分支 + exception_code 必填校验
- Modify: `plugin/hooks/gate-codex-review.sh` — 删除 `targeted-re-review` case + `--resume` 强制检查（约 20 行）
- Modify: `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` — L46 `3P + 12` → `2P + 6`（含 effort_total `(2P + 6) * 2`）
- Modify: `plugin/skills/orchestrate-plan-writing/SKILL.md` — L172 `3P + 12` → `2P + 6`
- Modify: `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` / `orchestrate-final-review/SKILL.md` / `orchestrate-execution/SKILL.md` — grep 删除所有 targeted-re-review 描述
- Modify: `plugin/architecture-draft.md` — 删除 §11.4 + §13 review intent 表中 targeted-re-review 行
- Modify: `plugin/hooks/tests/test_envelope_parse.sh` + `test_gate_codex_review.sh` — 更新用例（新增 baseline-only + 删除 targeted-re-review exception_code 用例）

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 13 + §5.1 + §5.6 + §5.2
- `plugin/state-schema/dispatch-envelope-v1.json`（理解当前 enum 结构）
- `plugin/hooks/lib/parse-envelope.sh`（理解当前校验逻辑）
- `plugin/hooks/gate-codex-review.sh`（理解当前分支结构）

**Contract anchors:**
- Owner: D13 全局删除 Targeted Re-review
- Producer: dispatch-envelope schema 是所有 review dispatch 的合同源
- Consumer: parse-envelope.sh / gate-codex-review.sh / 所有 SKILL.md 中 review dispatch 描述
- Model: `dispatch-envelope-v1.json` `review_intent` 字段
- Verification: grep 全树 `targeted-re-review` 仅在 git history / decision rationale 中残留；2 个 hook test pass

**Acceptance criteria:**
- [ ] `dispatch-envelope-v1.json` `review_intent` enum 仅含 `["baseline"]`（不含 `targeted-re-review`；`path-a-re-review` 由 Pack 2.5 删）
- [ ] `parse-envelope.sh` 不含 `targeted-re-review` 分支 + 不含 exception_code 必填校验
- [ ] `gate-codex-review.sh` 不含 `targeted-re-review` case + 不含 `--resume` 强制检查代码
- [ ] `plan-gates.md` L46 含 `budget.review_total = 2P + 6` + `budget.effort_total = (2P + 6) * 2`
- [ ] `orchestrate-plan-writing/SKILL.md` L172 含 `budget_total = 2P + 6`
- [ ] 全树 `grep -rn "targeted-re-review\|targeted re-review" plugin/` 在 .sh / .json / SKILL.md / reference.md 中无残留（git history / decision rationale 除外）
- [ ] `plugin/hooks/tests/test_envelope_parse.sh` 通过（含新增 baseline-only 用例）
- [ ] `plugin/hooks/tests/test_gate_codex_review.sh` 通过（删除 targeted-re-review + --resume 用例）
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

**Verification commands:**
- `jq -r '.properties.review_intent.oneOf[0].enum' plugin/state-schema/dispatch-envelope-v1.json` → Expected: `["baseline"]`（或仅含 baseline + path-a-re-review，path-a 由 Pack 2.5 删）
- `grep -n "targeted-re-review" plugin/hooks/gate-codex-review.sh plugin/hooks/lib/parse-envelope.sh` → Expected: 无输出
- `grep -n "2P + 6" plugin/skills/orchestrate-plan-writing/references/plan-gates.md plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: 两文件均含
- `grep -rn "targeted-re-review\|targeted re-review" plugin/skills/ plugin/architecture-draft.md` → Expected: 无残留
- `bash plugin/hooks/tests/test_envelope_parse.sh` → Expected: pass
- `bash plugin/hooks/tests/test_gate_codex_review.sh` → Expected: pass

**Commit boundary:** 一个 atomic commit：dispatch-envelope schema + parse-envelope + gate-codex-review + budget 公式 + SKILL/reference 描述清除 + 2 hook test 同步
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** Pack 2.1（先删 .tmpl 子模板以免新增 grep 残留）
**Out of scope:** Path A 相关 review_intent enum 值（Pack 2.5 处理）；review-dispatch.md.tmpl 子模板（已 Pack 2.1）

#### Implementation tasks

- [ ] Step 1: 写失败测试（Red）— 新增 baseline-only 用例
  - 文件: `plugin/hooks/tests/test_envelope_parse.sh`
  - Behavior: 新增 case "valid baseline envelope（不含 exception_code）" → 期望 exit 0；"含 review_intent=targeted-re-review" → 当前 exit 0（旧行为），修复后应 exit ≠ 0（enum 不允许）
  - Run: `bash plugin/hooks/tests/test_envelope_parse.sh` → Expected: FAIL（新 case 因 schema 未改而失败）

- [ ] Step 2: 修改 dispatch-envelope-v1.json
  - 文件: `plugin/state-schema/dispatch-envelope-v1.json` L27
  - 动作: 把 `"enum": ["baseline", "targeted-re-review", "path-a-re-review"]` 改为 `"enum": ["baseline", "path-a-re-review"]`（path-a-re-review 留给 Pack 2.5）
  - 同时检查 `exception_code` 字段——若仅服务 targeted-re-review，标注待删除（具体删除由后续 step 处理）

- [ ] Step 3: 修改 parse-envelope.sh
  - 文件: `plugin/hooks/lib/parse-envelope.sh` L49-L80
  - 动作: 删除 `baseline|targeted-re-review` 行的 `|targeted-re-review` 部分；删除 L74-78 `if [[ "$REVIEW_INTENT" == "targeted-re-review" ]]; then ... exception_code 必填` 整段
  - Run: `bash plugin/hooks/tests/test_envelope_parse.sh` → Expected: 新 case PASS（schema 已改）；旧 targeted-re-review case 仍存在则 FAIL → 删除该 case

- [ ] Step 4: 修改 gate-codex-review.sh
  - 文件: `plugin/hooks/gate-codex-review.sh`
  - 定位: `grep -n "targeted-re-review\|--resume" plugin/hooks/gate-codex-review.sh`
  - 动作: 删除 `targeted-re-review)` case 整段（含 `--resume` 强制检查 + 任何 exception_code 处理）
  - 注意: 保留 `baseline)` case + `uncommitted packs` 检查（决策 9 这两项不动）+ `path-a-re-review)` case（Pack 2.5 删）

- [ ] Step 5: 跑 hook test 验证
  - Run: `bash plugin/hooks/tests/test_gate_codex_review.sh` → Expected: PASS（删除 targeted-re-review + --resume 用例后）
  - 若失败：检查测试 fixture 是否仍含 targeted-re-review 用例 → 一并删除

- [ ] Step 6: 修改 plan-gates.md budget 公式
  - 文件: `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` L46
  - 当前内容（Read 验证）: `此命令写入 budget.review_total = 3P + 12、budget.effort_total = (3P + 12) * 2`
  - 改为: `此命令写入 budget.review_total = 2P + 6、budget.effort_total = (2P + 6) * 2`
  - 公式分配（追加说明段）:
    > `2P` = 每 Plan 2 次 review（Plan Review + Plan Implementation Review）；`+6` 固定分配：Design Review 2 + Final Review 2 + Release Gate 1 + Multi-PR Integration Review 1。

- [ ] Step 7: 修改 orchestrate-plan-writing/SKILL.md
  - 文件: `plugin/skills/orchestrate-plan-writing/SKILL.md` L172
  - 当前内容: `budget_total = 3P + 12`
  - 改为: `budget_total = 2P + 6`

- [ ] Step 8: 清除 SKILL.md / reference 中 targeted-re-review 描述
  - 定位: `grep -rln "targeted-re-review\|targeted re-review" plugin/skills/`
  - 动作: 逐文件 Edit 删除 targeted-re-review 描述行（保留 baseline review 描述）。**仅本 Pack scope**：删除合同表面提及；具体 reference 内容压缩（如 final-review-repair.md Step 11/12 重写）由 Issue 003 处理

- [ ] Step 9: 修改 architecture-draft.md
  - 文件: `plugin/architecture-draft.md`
  - 定位: `grep -n "targeted-re-review\|targeted re-review" plugin/architecture-draft.md`
  - 动作: 删除 §11.4 targeted re-review 章节 + §13 review intent 表中 targeted-re-review 行；保留 baseline review 描述

- [ ] Step 10: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS（review_effectiveness 检查仍在，由 Pack 2.3 处理）

- [ ] Step 11: Suggested commit boundary
  - Message: `feat(plugin): D13b 全局删除 Targeted Re-review 机制（schema + hooks + budget 2P+6 + 描述清除）`

---

### Task Pack 2.3: D7a — review_effectiveness 删除（lib + schema + 8 处 consumer）

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 3

**Goal behavior:** `plugin/scripts/lib/review-effectiveness.sh` 删除；8 处真实 consumer 全清——`workflow-state-v1.json` L10/L83 / `state.sh` L170/L347 / `test_agent_id_hook_guard.sh` L59 / `test_effort_budget_weighting.sh` L46 / `test_review_effectiveness.sh` 整文件 / `learnings-confidence-audit.md` L44 / `verify-maturity.sh` L73 / `architecture-draft.md` L703/L756/L940 / `state-lock.sh` L3 注释 / `build/tests/test_review_effectiveness_optional.sh` 整文件（设计文档 7 处 + 实际探查 +1 处 build/tests 共 8 处）。

**Owned files / responsibilities:**
- Delete: `plugin/scripts/lib/review-effectiveness.sh`
- Delete: `plugin/scripts/tests/test_review_effectiveness.sh`
- Delete: `plugin/build/tests/test_review_effectiveness_optional.sh`（设计文档遗漏的第 8 处 consumer）
- Modify: `plugin/state-schema/workflow-state-v1.json` L10 + L83
- Modify: `plugin/scripts/state.sh` L170（init 字段）+ L347（required_fields 校验列表）
- Modify: `plugin/hooks/tests/test_agent_id_hook_guard.sh` L59
- Modify: `plugin/hooks/tests/test_effort_budget_weighting.sh` L46
- Modify: `plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md` L44
- Modify: `plugin/scripts/verify-maturity.sh` L73
- Modify: `plugin/architecture-draft.md` L703 / L756 / L940
- Modify: `plugin/scripts/lib/state-lock.sh` L3 注释
- Test: 现有测试套件继续通过（fixture 已同步）

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 7 + Decision §11 D3 用户决策（删除 lib + 字段）
- `plugin/scripts/lib/review-effectiveness.sh`（理解当前 lib 接口）
- `plugin/state-schema/workflow-state-v1.json`（理解当前 schema 结构）

**Contract anchors:**
- Owner: D7 review_effectiveness 字段 + lib 删除
- Producer: 无（lib 删除后无生产者）
- Consumer: 8 处真实 consumer（设计文档已纠正）
- Model: `workflow-state-v1.json` `review_effectiveness` object
- Verification: grep 全树无 `review_effectiveness` / `review-effectiveness` 残留（git history / decision rationale 除外）

**Acceptance criteria:**
- [ ] `plugin/scripts/lib/review-effectiveness.sh` 不存在
- [ ] `plugin/scripts/tests/test_review_effectiveness.sh` 不存在
- [ ] `plugin/build/tests/test_review_effectiveness_optional.sh` 不存在
- [ ] `workflow-state-v1.json` `required` 数组不含 `review_effectiveness`；properties 段不含 `review_effectiveness`
- [ ] `state.sh` init 不再初始化 `review_effectiveness` 字段
- [ ] `state.sh` L347 required_fields 校验列表不含 `review_effectiveness`
- [ ] `verify-maturity.sh` 不含 `review-effectiveness optional diagnostic script exists` 检查
- [ ] `architecture-draft.md` L703 / L756 / L940 三段对应内容清除（L703 删除 review_effectiveness 字段提及；L756 删除 review-effectiveness.sh 表行；L940 整段删除）
- [ ] `learnings-confidence-audit.md` L44 引用段清除
- [ ] `test_agent_id_hook_guard.sh` L59 + `test_effort_budget_weighting.sh` L46 不含 `review_effectiveness` 字段
- [ ] `state-lock.sh` L3 注释更新（不再提及 review-effectiveness.sh）
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
- [ ] `bash plugin/scripts/verify-maturity.sh` 通过（删除 review-effectiveness 检查后）

**Verification commands:**
- `test ! -e plugin/scripts/lib/review-effectiveness.sh` → Expected: exit 0
- `test ! -e plugin/scripts/tests/test_review_effectiveness.sh` → Expected: exit 0
- `test ! -e plugin/build/tests/test_review_effectiveness_optional.sh` → Expected: exit 0
- `jq '.required | index("review_effectiveness")' plugin/state-schema/workflow-state-v1.json` → Expected: null
- `jq '.properties.review_effectiveness' plugin/state-schema/workflow-state-v1.json` → Expected: null
- `grep -n "review_effectiveness\|review-effectiveness" plugin/scripts/state.sh` → Expected: 无输出
- `grep -n "review-effectiveness" plugin/scripts/verify-maturity.sh` → Expected: 无输出
- `grep -rn "review_effectiveness\|review-effectiveness" plugin/skills/ plugin/architecture-draft.md plugin/scripts/lib/state-lock.sh` → Expected: 无输出（git history 除外）
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 一个 atomic commit：lib 删除 + 8 处 consumer 全清 + 2 个 test 文件删除 + verify-maturity 同步
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None（独立于其他 Pack）
**Out of scope:** review_dispositions 字段（保留，不删）；plugin/reviews/ 下的历史审查文档（git history 不动）

#### Implementation tasks

- [ ] Step 1: 写失败测试（Red）— 验证 state.sh init 不再含 review_effectiveness
  - 文件: `plugin/scripts/tests/test_state.sh`（如存在 init 测试）— 新增 case "init 后的 workflow-state 不含 review_effectiveness"
  - 或临时 inline: `bash plugin/scripts/state.sh init --run-id test-r0 --slug test --route formal && jq '.review_effectiveness' .claude/multi-model-workflow/workflow-state-test-r0.json`
  - Expected: 当前 = object（FAIL）；修复后 = null（PASS）

- [ ] Step 2: 删除 lib + tests
  - Run: `rm plugin/scripts/lib/review-effectiveness.sh plugin/scripts/tests/test_review_effectiveness.sh plugin/build/tests/test_review_effectiveness_optional.sh`
  - Verify: `test ! -e plugin/scripts/lib/review-effectiveness.sh` → exit 0

- [ ] Step 3: 修改 workflow-state-v1.json schema
  - 文件: `plugin/state-schema/workflow-state-v1.json` L10 + L83
  - L10: required 数组中删除 `"review_effectiveness"`
  - L83: properties 段删除整个 `"review_effectiveness": {...}` block

- [ ] Step 4: 修改 state.sh init + required_fields
  - 文件: `plugin/scripts/state.sh` L170 + L347
  - L170: 删除 init 时的 `"review_effectiveness": {...}` 初始化段
  - L347: required_fields 校验列表中删除 `"review_effectiveness"`

- [ ] Step 5: 修改 2 个 hook test fixture
  - 文件: `plugin/hooks/tests/test_agent_id_hook_guard.sh` L59 + `plugin/hooks/tests/test_effort_budget_weighting.sh` L46
  - 动作: 删除 `"review_effectiveness": {"reject_count":0,...},` 整行（保留其他字段 + 行末逗号合法）

- [ ] Step 6: 修改 verify-maturity.sh
  - 文件: `plugin/scripts/verify-maturity.sh` L73
  - 动作: 删除 `check "review-effectiveness optional diagnostic script exists" test -x ...` 整行

- [ ] Step 7: 修改 architecture-draft.md（3 处）
  - 文件: `plugin/architecture-draft.md`
  - L703: 该行是 workflow-state JSON 结构说明，删除 `review_effectiveness` 字段提及
  - L756: lib 文件表中删除 `scripts/lib/review-effectiveness.sh` 行
  - L940: 整段（"`scripts/lib/review-effectiveness.sh` 从 disposition 聚合统计..."）删除

- [ ] Step 8: 修改 learnings-confidence-audit.md
  - 文件: `plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md` L44
  - 动作: 删除 `- review-effectiveness.sh 聚合统计（reject_count, suppress_count, path_a/b_count）` 行

- [ ] Step 9: 修改 state-lock.sh 注释
  - 文件: `plugin/scripts/lib/state-lock.sh` L3
  - 当前: `# Extracted from state.sh for reuse by review-effectiveness.sh and other scripts.`
  - 改为: `# Extracted from state.sh for reuse by other scripts.`

- [ ] Step 10: 跑全量测试 + verify-maturity
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
  - Run: `grep -rn "review_effectiveness\|review-effectiveness" plugin/` | grep -v ".git\|/reviews/" → Expected: 无输出

- [ ] Step 11: Suggested commit boundary
  - Message: `feat(plugin): D7a 删除 review_effectiveness 字段 + lib + 8 处 consumer 清理`

---

### Task Pack 2.4: D7b — state.sh 死命令 + scripts/lib poison-detector 合并

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 4

**Goal behavior:** `state.sh` 删除 2 个 0 生产调用的子命令 `business-summary` / `plans`（**保留** `idempotency check/append`——4 处生产调用，调研误判已纠正）+ 对应 test 用例；`scripts/lib/learnings-poison-detector.sh` 合并入 `learnings-jsonl.sh`（poison-detector 改为 function 嵌入 + 删除独立脚本）。`path-a-escalation` 和 `agent-context-check` 由 Pack 2.5 / 2.8 删除，不在本 Pack。

**Owned files / responsibilities:**
- Modify: `plugin/scripts/state.sh` — 删除 `business-summary` 子命令（L1611 附近的 cmd_business_summary 函数 + dispatcher case）；删除 `plans` 子命令对应函数 + dispatcher case
- Modify: `plugin/scripts/learnings-jsonl.sh` — 内联 poison-detector 为 function
- Delete: `plugin/scripts/lib/learnings-poison-detector.sh`
- Modify: `plugin/scripts/tests/test_state.sh` — 删除 business-summary / plans 用例
- Modify: `plugin/scripts/tests/test_learnings_poison_detection.sh` — 调用方式更新（改为 source learnings-jsonl.sh 后调用 function）

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 7 + §5.7
- `plugin/scripts/state.sh`（理解当前子命令 dispatcher 结构）
- `plugin/scripts/lib/learnings-poison-detector.sh`（理解当前接口）

**Contract anchors:**
- Owner: D7 state.sh 死命令清理
- Producer: state.sh dispatcher
- Consumer: 任何调用 state.sh business-summary / plans 的方（已亲验 0 生产调用）
- Verification: state.sh subcommand 数从 20 → 18（path-a-escalation / agent-context-check 由 Pack 2.5 / 2.8 删，本 Pack 后达 18，最终 16）

**Acceptance criteria:**
- [ ] `bash plugin/scripts/state.sh business-summary append --help` exit ≠ 0（命令不存在）
- [ ] `bash plugin/scripts/state.sh plans add --help` exit ≠ 0
- [ ] `bash plugin/scripts/state.sh idempotency check --run-id foo --key bar 2>&1` 仍可执行（保留——4 处生产调用）
- [ ] `plugin/scripts/lib/learnings-poison-detector.sh` 不存在
- [ ] `plugin/scripts/learnings-jsonl.sh` 内含 poison-detector 函数（grep `poison_detector\|poison-detector` 在该文件内有定义）
- [ ] `plugin/scripts/tests/test_state.sh` 不含 business-summary / plans 用例
- [ ] `plugin/scripts/tests/test_learnings_poison_detection.sh` 调用方式更新（source learnings-jsonl.sh）且通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

**Verification commands:**
- `bash plugin/scripts/state.sh business-summary 2>&1 | grep -i "unknown\|invalid\|not found"` → Expected: 命中（命令不存在）
- `bash plugin/scripts/state.sh plans 2>&1 | grep -i "unknown\|invalid\|not found"` → Expected: 命中
- `bash plugin/scripts/state.sh idempotency check --help 2>&1` → Expected: 显示 usage（保留）
- `test ! -e plugin/scripts/lib/learnings-poison-detector.sh` → Expected: exit 0
- `grep -n "poison" plugin/scripts/learnings-jsonl.sh` → Expected: 包含函数定义
- `bash plugin/scripts/tests/test_learnings_poison_detection.sh` → Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 一个 atomic commit：state.sh 死命令删除 + poison-detector 合并 + 测试同步
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** `path-a-escalation` 子命令（Pack 2.5）；`agent-context-check` 子命令（Pack 2.8）；`idempotency check/append`（保留不删）

#### Implementation tasks

- [ ] Step 1: 写失败测试（Red）— 子命令不存在
  - Run: `bash plugin/scripts/state.sh business-summary 2>&1; echo "exit=$?"` → Expected (now): exit 0 + 输出 usage；Expected (after): exit ≠ 0
  - Run: `bash plugin/scripts/state.sh plans 2>&1; echo "exit=$?"` → Expected (now): exit 0 + 输出 usage；Expected (after): exit ≠ 0

- [ ] Step 2: 定位 state.sh 中子命令函数 + dispatcher
  - Run: `grep -n "cmd_business_summary\|cmd_plans\|business-summary)\|plans)" plugin/scripts/state.sh`
  - 记录: function 定义行 + dispatcher case 行

- [ ] Step 3: 删除 state.sh business-summary
  - 文件: `plugin/scripts/state.sh`
  - 动作: Edit 删除 `cmd_business_summary` 函数完整段（L1611 附近）+ dispatcher 中 `business-summary)` case 整行
  - 验证: `grep -n "business-summary\|business_summary" plugin/scripts/state.sh` → 无输出

- [ ] Step 4: 删除 state.sh plans 子命令
  - 文件: `plugin/scripts/state.sh`
  - 动作: Edit 删除 `cmd_plans` 函数 + dispatcher 中 `plans)` case
  - 注意: 不删除 hook 错误消息字符串中的 `state.sh plans add` 提示（已是 deprecated 提示）；改为统一提示"plans 子命令已移除"——或一并清理（同 Pack 内）
  - 定位错误提示: `grep -n "state.sh plans add" plugin/hooks/`
  - 动作: 把 hook 中 `state.sh plans add` 错误提示文本删除或替换（不再引用已删命令）

- [ ] Step 5: 删除 state.sh 测试用例
  - 文件: `plugin/scripts/tests/test_state.sh`
  - 定位: `grep -n "business-summary\|cmd_plans\|state.sh plans" plugin/scripts/tests/test_state.sh`
  - 动作: 删除对应测试用例段（保留其他子命令测试）

- [ ] Step 6: 跑 state.sh 子命令测试验证
  - Run: `bash plugin/scripts/tests/test_state.sh` → Expected: PASS（剩余用例全过）
  - Run: `bash plugin/scripts/state.sh business-summary 2>&1; echo "exit=$?"` → Expected: exit ≠ 0
  - Run: `bash plugin/scripts/state.sh idempotency check --run-id foo --key bar 2>&1; echo "exit=$?"` → Expected: 仍可执行（保留）

- [ ] Step 7: 合并 poison-detector 入 learnings-jsonl.sh
  - 文件 source: `plugin/scripts/lib/learnings-poison-detector.sh`
  - 文件 target: `plugin/scripts/learnings-jsonl.sh`
  - 动作: Read poison-detector.sh 整文件 → 将主逻辑包装为 shell function（如 `detect_learning_poison() { ... }`）→ Edit append 到 learnings-jsonl.sh 底部
  - 注意: 保留 shebang + 原有 license/comment

- [ ] Step 8: 删除 learnings-poison-detector.sh
  - Run: `rm plugin/scripts/lib/learnings-poison-detector.sh`
  - Verify: `test ! -e plugin/scripts/lib/learnings-poison-detector.sh` → exit 0

- [ ] Step 9: 更新 test_learnings_poison_detection.sh
  - 文件: `plugin/scripts/tests/test_learnings_poison_detection.sh`
  - 当前: 调用 `bash plugin/scripts/lib/learnings-poison-detector.sh ...`
  - 改为: `source plugin/scripts/lib/learnings-jsonl.sh; detect_learning_poison ...`（具体调用按 Step 7 实际 function 接口）
  - Run: `bash plugin/scripts/tests/test_learnings_poison_detection.sh` → Expected: PASS

- [ ] Step 10: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

- [ ] Step 11: Suggested commit boundary
  - Message: `feat(plugin): D7b 删除 state.sh business-summary/plans 子命令 + 合并 poison-detector 入 learnings-jsonl`

---

### Task Pack 2.5: D3 — Path A 完全删除（state.sh + schema + hooks + disposition + reference + tests）

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 5

**Goal behavior:** Path A 自修分叉完全删除——`state.sh path-a-escalation` 子命令 + `workflow-state-v1.json` `path_a_escalation` / `blocked_for_self_fix` 字段 + `gate-codex-review.sh` `path-a-re-review` 分支 + `dispatch-envelope-v1.json` enum 中 `path-a-re-review` 值 + `validate-plan-dispatch.sh` Step 8 Path A 检查 + `disposition-table.md.tmpl` `path-a` 选项及 "Path A re-review 规则" 整段（已亲验：disposition CLI enum 5 值 `accepted|rejected|suppress|path-a|path-b` → 删 `path-a` 后 4 值；"Path A re-review 规则" 段在 L44-47） + `path-a-re-review.md` reference + `test_path_a_re_review.sh` + 6 处 SKILL/reference 中 `state.sh path-a-escalation` 描述 + **5 处 hook test fixture 中 `path_a_escalation: []`**（亲验 grep 结果：test_need_fresh_worker_continuation L43 / test_worker_loop_e2e L43 / test_validate_plan_dispatch L18 / test_agent_id_hook_guard L61 / test_effort_budget_weighting L48；后 2 处的 review_effectiveness 字段已由 Pack 2.3 处理，本 Pack 处理 path_a_escalation 字段）。

**Owned files / responsibilities:**
- Modify: `plugin/scripts/state.sh` — 删除 `path-a-escalation` 子命令函数 + dispatcher case
- Modify: `plugin/state-schema/workflow-state-v1.json` — required 数组 + properties 段删除 `path_a_escalation`；删除 `blocked_for_self_fix`（如存在）
- Modify: `plugin/state-schema/dispatch-envelope-v1.json` — `review_intent` enum 删除 `path-a-re-review`（Pack 2.2 已删 targeted-re-review；本 Pack 完成 enum 收敛为 `["baseline"]`）
- Modify: `plugin/hooks/gate-codex-review.sh` — 删除 `path-a-re-review)` case（约 10 行）
- Modify: `plugin/hooks/validate-plan-dispatch.sh` — 删除 Step 8 Path A 检查代码段
- Modify: `plugin/build/templates/disposition-table.md.tmpl` — 删除 `path-a` 选项 + 删除 L44-47 "Path A re-review 规则" 整段（4 行）（亲验：CLI disposition enum L23 当前 5 值 `accepted|rejected|suppress|path-a|path-b`，删除 `path-a` 后 4 值；设计文档 §4.2 D3 "disposition 枚举 10→9" 表述含其他 SKILL/reference 中 disposition 枚举累计，本 Pack 仅处理 .tmpl 中实际存在的 path-a 引用）
- Modify: `plugin/skills/_shared/disposition-table.md` — 删除 `path-a` 选项（Issue 001 Pack 9 canonical 抽取时保留了 path-a，本 Pack 在 live canonical 中同步清理）
- Modify: 5 处 SKILL/reference 中 `state.sh path-a-escalation` 描述：
  - `plugin/skills/orchestrate-discovery/references/design-review-angles.md` L306
  - `plugin/skills/orchestrate-plan-writing/SKILL.md` L235
  - `plugin/skills/orchestrate-final-review/references/final-review-disposition.md` L56
  - `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` L228
  - `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md` L56
  - `plugin/skills/orchestrate-execution/SKILL.md` L428
- Modify: `plugin/architecture-draft.md` L901 + L904 + 其他 Path A 提及（grep 定位）
- Delete: `plugin/skills/orchestrate-execution/references/path-a-re-review.md`
- Delete: `plugin/scripts/tests/test_path_a_re_review.sh`
- Modify (test fixtures): **5 hook test fixture 删除 `path_a_escalation: []`**：
  - `plugin/hooks/tests/test_need_fresh_worker_continuation.sh` L43
  - `plugin/hooks/tests/test_worker_loop_e2e.sh` L43
  - `plugin/hooks/tests/test_validate_plan_dispatch.sh` L18
  - `plugin/hooks/tests/test_agent_id_hook_guard.sh` L61（review_effectiveness 字段已由 Pack 2.3 处理，本 Pack 删 path_a_escalation 字段）
  - `plugin/hooks/tests/test_effort_budget_weighting.sh` L48（review_effectiveness 字段已由 Pack 2.3 处理，本 Pack 删 path_a_escalation 字段）

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 3 + Decision §11 D1 用户决策（完全删除）
- `plugin/scripts/state.sh`（找 cmd_path_a_escalation 函数）
- `plugin/hooks/gate-codex-review.sh` L54-L63（path-a-re-review case）

**Contract anchors:**
- Owner: D3 Path A 完全删除
- Producer: 无（Path A 概念删除后无生产者）
- Consumer: gate-codex-review.sh / state.sh / 5 处 SKILL/reference / 3 处 hook test fixture
- Model: workflow-state `path_a_escalation` 字段 / dispatch-envelope `review_intent` enum
- Verification: grep 全树 `path-a` / `path_a` 在 .sh / .json / .md 中无残留（git history / decision rationale 除外）

**Acceptance criteria:**
- [ ] `bash plugin/scripts/state.sh path-a-escalation start --help` exit ≠ 0
- [ ] `workflow-state-v1.json` 不含 `path_a_escalation` / `blocked_for_self_fix`
- [ ] `gate-codex-review.sh` 不含 `path-a-re-review` case 代码
- [ ] `dispatch-envelope-v1.json` `review_intent` enum 收敛为 `["baseline"]`
- [ ] `disposition-table.md.tmpl` 不含 `path-a` 字符串（CLI enum 从 5 值降至 4 值，且 L44-47 "Path A re-review 规则" 整段删除）
- [ ] `plugin/skills/orchestrate-execution/references/path-a-re-review.md` 不存在
- [ ] `plugin/scripts/tests/test_path_a_re_review.sh` 不存在
- [ ] **5 hook test fixture** 不含 `path_a_escalation: []`（test_need_fresh_worker_continuation / test_worker_loop_e2e / test_validate_plan_dispatch / test_agent_id_hook_guard / test_effort_budget_weighting）
- [ ] 6 处 SKILL/reference 中 `state.sh path-a-escalation` 描述清除
- [ ] `validate-plan-dispatch.sh` 不含 Step 8 Path A 检查代码
- [ ] `architecture-draft.md` L901/L904 Path A 段删除
- [ ] 全树 `grep -rn "path-a\|path_a" plugin/` 在 .sh / .json / .md 中无残留（git history / decision rationale 除外）
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

**Verification commands:**
- `bash plugin/scripts/state.sh path-a-escalation 2>&1; echo "exit=$?"` → Expected: exit ≠ 0
- `jq '.required | index("path_a_escalation")' plugin/state-schema/workflow-state-v1.json` → Expected: null
- `jq -r '.properties.review_intent.oneOf[0].enum' plugin/state-schema/dispatch-envelope-v1.json` → Expected: `["baseline"]`
- `grep -n "path-a-re-review" plugin/hooks/gate-codex-review.sh` → Expected: 无输出
- `grep -n "path-a" plugin/build/templates/disposition-table.md.tmpl` → Expected: 无输出
- `grep -n "path-a" plugin/skills/_shared/disposition-table.md` → Expected: 无输出
- `test ! -e plugin/skills/orchestrate-execution/references/path-a-re-review.md` → Expected: exit 0
- `test ! -e plugin/scripts/tests/test_path_a_re_review.sh` → Expected: exit 0
- `grep -n "path_a_escalation" plugin/hooks/tests/` → Expected: 无输出
- `grep -rn "state.sh path-a-escalation" plugin/skills/` → Expected: 无输出
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 一个 atomic commit：state.sh + 2 schema + 2 hook + template + 6 SKILL/reference + reference 删除 + 测试删除 + 3 fixture 同步
**Risk flags:** normal
**发布风险:** 旧 workflow-state JSON 含 `path_a_escalation` 字段——靠 state.sh validate 对未知字段 graceful ignore 兼容（设计文档 §9.1 场景 3 已说明）
**AFK / HITL:** AFK
**Dependencies:** Pack 2.2（已删 gate-codex-review.sh 中 targeted-re-review 分支 + parse-envelope 中 enum 校验；本 Pack 完成 path-a-re-review 分支的删除）
**Out of scope:** doc-patch（Pack 2.7）；agent-context-check（Pack 2.8）

#### Implementation tasks

- [ ] Step 1: 写失败测试（Red）— Path A 子命令不存在 + schema 不含字段
  - Run: `bash plugin/scripts/state.sh path-a-escalation 2>&1; echo "exit=$?"` → Expected (now): exit 0；Expected (after): exit ≠ 0
  - Run: `jq '.properties.path_a_escalation' plugin/state-schema/workflow-state-v1.json` → Expected (now): {...}；Expected (after): null

- [ ] Step 2: 删除 state.sh path-a-escalation 子命令
  - 文件: `plugin/scripts/state.sh`
  - 定位: `grep -n "cmd_path_a_escalation\|path-a-escalation)" plugin/scripts/state.sh`
  - 动作: Edit 删除 function 段 + dispatcher case

- [ ] Step 3: 修改 workflow-state-v1.json schema
  - 文件: `plugin/state-schema/workflow-state-v1.json`
  - L11: required 数组中删除 `"path_a_escalation"`
  - L101: properties 段删除 `"path_a_escalation": { "type": "array" }`
  - 检查 + 删除 `blocked_for_self_fix`（grep 定位）

- [ ] Step 4: 修改 state.sh init（删除 path_a_escalation 字段初始化）
  - 文件: `plugin/scripts/state.sh`
  - 定位: `grep -n "path_a_escalation" plugin/scripts/state.sh`
  - 动作: 删除 init 中 `"path_a_escalation": []` 行 + required_fields 校验列表中的 `"path_a_escalation"`

- [ ] Step 5: 修改 dispatch-envelope-v1.json
  - 文件: `plugin/state-schema/dispatch-envelope-v1.json` L27
  - 当前（Pack 2.2 后）: `"enum": ["baseline", "path-a-re-review"]`
  - 改为: `"enum": ["baseline"]`

- [ ] Step 6: 修改 gate-codex-review.sh
  - 文件: `plugin/hooks/gate-codex-review.sh` L54-L63
  - 动作: 删除 `path-a-re-review)` case 整段（约 10 行）

- [ ] Step 7: 修改 validate-plan-dispatch.sh
  - 文件: `plugin/hooks/validate-plan-dispatch.sh`
  - 定位: `grep -n "path_a\|Path A\|path-a" plugin/hooks/validate-plan-dispatch.sh`
  - 动作: 删除 Step 8 Path A 检查代码段（按设计文档 §4.2 决策 9）

- [ ] Step 8: 修改 disposition-table.md.tmpl
  - 文件: `plugin/build/templates/disposition-table.md.tmpl`
  - 动作 a: L23 CLI enum `--disposition <accepted|rejected|suppress|path-a|path-b>` 改为 `--disposition <accepted|rejected|suppress|path-b>`（CLI 5 值降至 4 值）
  - 动作 b: 删除 L44-47 "Path A re-review 规则" 整段（4 行）
  - 验证: `grep -n "path-a" plugin/build/templates/disposition-table.md.tmpl` → 无输出
  - 注意: disposition 主表 L32-40 不变（7 个 markdown table row：accepted / rejected / needs evidence / duplicate / out of scope / needs evaluation / user decision——不含 path-a 行，无需改动）

- [ ] Step 8b: 修改 canonical disposition-table.md（live 文件）
  - 文件: `plugin/skills/_shared/disposition-table.md`（Issue 001 Pack 9 抽取时保留了 path-a，本步在 live canonical 中同步清理）
  - 动作: 与 Step 8 同模式——删除 CLI enum 中 `path-a` + 删除 "Path A re-review 规则" 整段
  - 验证: `grep -n "path-a" plugin/skills/_shared/disposition-table.md` → 无输出

- [ ] Step 9: 删除 path-a-re-review.md reference + test_path_a_re_review.sh
  - Run: `rm plugin/skills/orchestrate-execution/references/path-a-re-review.md plugin/scripts/tests/test_path_a_re_review.sh`

- [ ] Step 10: 修改 6 处 SKILL/reference 中 path-a-escalation 描述
  - 文件 1: `plugin/skills/orchestrate-discovery/references/design-review-angles.md` L306 — 删除 `- 用 state.sh path-a-escalation start/update/clear 追踪` 行
  - 文件 2: `plugin/skills/orchestrate-plan-writing/SKILL.md` L235 — 同上
  - 文件 3: `plugin/skills/orchestrate-final-review/references/final-review-disposition.md` L56 — 同上
  - 文件 4: `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` L228 — 同上
  - 文件 5: `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md` L56 — 同上
  - 文件 6: `plugin/skills/orchestrate-execution/SKILL.md` L428 — 同上

- [ ] Step 11: 修改 architecture-draft.md
  - 文件: `plugin/architecture-draft.md`
  - 定位: `grep -n "path-a\|path_a\|Path A" plugin/architecture-draft.md`
  - 动作: 删除 L901 / L904 + 其他 Path A 段（含 disposition table 中 path-a 行 + workflow-state 字段列表中 path_a_escalation）

- [ ] Step 12: 修改 **5 hook test fixture**
  - 文件 1: `plugin/hooks/tests/test_need_fresh_worker_continuation.sh` L43
  - 文件 2: `plugin/hooks/tests/test_worker_loop_e2e.sh` L43
  - 文件 3: `plugin/hooks/tests/test_validate_plan_dispatch.sh` L18
  - 文件 4: `plugin/hooks/tests/test_agent_id_hook_guard.sh` L61（Pack 2.3 已删 L59 review_effectiveness；本步删 L61 `"path_a_escalation": [],`）
  - 文件 5: `plugin/hooks/tests/test_effort_budget_weighting.sh` L48（Pack 2.3 已删 L46 review_effectiveness；本步删 L48 `"path_a_escalation": [],`）
  - 动作: 在 fixture JSON 中删除 `"path_a_escalation":[],` 或 `"path_a_escalation": [],` 段（保留其他字段，确保 JSON 合法 + 行末逗号处理正确）
  - 验证（每个文件单独跑）: `python3 -c "import json; json.load(open('/tmp/fixture.json'))"` 或在 test 内 `jq .` 验证 JSON 合法

- [ ] Step 13: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
  - Run: `grep -rn "path-a\|path_a" plugin/scripts plugin/hooks plugin/skills plugin/state-schema plugin/build/templates | grep -v ".git\|/reviews/"` → Expected: 无输出
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: PASS（disposition-table.md.tmpl 改动后 build check 不变）

- [ ] Step 14: Suggested commit boundary
  - Message: `feat(plugin): D3 完全删除 Path A 自修分叉（state.sh + schema + hooks + disposition + reference + 3 fixture）`

---

### Task Pack 2.6: D5 — bug-seed-file 删除（中间文档移除）

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 6

**Goal behavior:** RCA findings 直接作为 Discovery Source artifact，不再先建 `bug-seed-<run_id>.md` 中间文档。`bug-investigation-route.md` 中"写入 Bug Seed 文件" Step 删除 + Scope Contract `bug_seed_path` 字段删除；`architecture-draft.md` §17 + 任何 SKILL.md 提及 `bug-seed-<run_id>.md` 全清。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` — 删除"写入 Bug Seed 文件" Step；改为 RCA findings 直接进 Scope Contract Source artifacts
- Modify: `plugin/architecture-draft.md` — 删除 §17（Bug Seed File）章节 + 其他 bug-seed 提及
- Modify: 任何 SKILL.md / reference 中 `bug-seed-<run_id>.md` 提及（grep 定位）

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 5
- `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`（当前 RCA → Discovery 流程）

**Contract anchors:**
- Owner: D5 bug-seed-file 删除
- Producer: 无（中间文档删除后无生产者）
- Consumer: bug-investigation route 流程
- Verification: 全树 grep `bug-seed-path` / `bug_seed_path` / `bug-seed-file` 无残留

**Acceptance criteria:**
- [ ] `bug-investigation-route.md` 不含 "bug-seed-<run_id>.md" / "写入 Bug Seed" 步骤
- [ ] `architecture-draft.md` §17（Bug Seed File）章节删除
- [ ] 全树 `grep -rn "bug-seed-path\|bug_seed_path\|bug-seed-file\|bug-seed-" plugin/` 无残留（git history / decision rationale 除外）
- [ ] `bug-investigation-route.md` 改为 "RCA findings 直接进 Scope Contract 的 Source artifacts"
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

**Verification commands:**
- `grep -n "bug-seed\|bug_seed" plugin/skills/orchestrate-workflow/references/bug-investigation-route.md` → Expected: 无输出
- `grep -n "Bug Seed" plugin/architecture-draft.md` → Expected: 无输出
- `grep -rn "bug-seed\|bug_seed" plugin/` | grep -v ".git\|/reviews/" → Expected: 无残留
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 一个 atomic commit：bug-investigation-route.md + architecture-draft.md §17 删除
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** Bug Investigation Route 整体流程不动（只删 bug-seed-file 中间文档）；其他 RCA 路径不动

#### Implementation tasks

- [ ] Step 1: 写失败 grep（Red）
  - Run: `grep -rn "bug-seed\|bug_seed" plugin/ | grep -v ".git\|/reviews/"` → Expected (now): 多条；Expected (after): 无残留

- [ ] Step 2: 修改 bug-investigation-route.md
  - 文件: `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
  - 定位: `grep -n "bug-seed\|Bug Seed" plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
  - 当前 L63 / L79-80（设计文档 D5 已亲验）
  - 动作: 
    - 删除 L63 "Coordinator 整理 analyst report 写入 `.claude/multi-model-workflow/bug-seed-<run_id>.md`" 段
    - 删除 L79 "写入 Bug Seed 文件" Step
    - 修改 L80 "更新 Scope Contract" 段——从 "加入 bug-seed-<run_id>.md" 改为 "加入 RCA analyst findings 报告路径作为 Source artifact"

- [ ] Step 3: 修改 architecture-draft.md
  - 文件: `plugin/architecture-draft.md`
  - 定位: `grep -n "Bug Seed\|bug-seed\|bug_seed" plugin/architecture-draft.md`
  - 动作: 删除 §17（Bug Seed File）章节整段 + 其他 bug-seed 提及（流程图 / 状态字段表）

- [ ] Step 4: 全树清扫
  - Run: `grep -rn "bug-seed\|bug_seed" plugin/ | grep -v ".git\|/reviews/"`
  - 动作: 逐一处理剩余命中（应为零）

- [ ] Step 5: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

- [ ] Step 6: Suggested commit boundary
  - Message: `feat(plugin): D5 删除 bug-seed-file 中间文档（RCA findings 直接进 Discovery Source artifacts）`

---

### Task Pack 2.7: D4 — doc-patch 系统完全删除 + Coordinator checkbox toggle 权威规则

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 7

**Goal behavior:** doc-patch 系统完全删除——`guard-plan-doc-patch.sh` hook + `doc-patch-apply.sh` lib + `plan-return-v1.json` `doc_patch_path` 字段 + Worker Loop "写 doc-patch.diff" 步骤 + pack-executor/complex-pack-executor 的 doc-patch 写出指令 + `architecture-draft.md` §7.5 / Decision 6 段。**新增权威规则**：Coordinator Edit 的 source-of-truth = `plan-return.per_pack[*]` where `status == committed`——写入 3 处：`orchestrate-execution/SKILL.md` Step 14 + `orchestrate-plan-writing/references/plan-review-resolution.md` + `agent-return-handler.sh` NEXT 指令输出。

**Owned files / responsibilities:**
- Delete: `plugin/hooks/guard-plan-doc-patch.sh`
- Delete: `plugin/scripts/lib/doc-patch-apply.sh`
- Delete: `plugin/scripts/tests/test_doc_patch_apply.sh`
- Delete: `plugin/hooks/tests/test_guard_plan_doc_patch.sh`
- Modify: `plugin/hooks/hooks.json` — 删除 `guard-plan-doc-patch.sh` 条目
- Modify: `plugin/state-schema/plan-return-v1.json` — 删除 `doc_patch_path` 字段 + L4 description 中 "doc-patch.diff" 提及全部重写
- Modify: `plugin/hooks/agent-return-handler.sh` — 删除 5 处 doc-patch.diff 暂存提示（L13/L94/L108/L111/L114/L124/L127）；verdict=pass/partial-pass 时输出新 NEXT "Coordinator: Plan Implementation Review pass 后 Edit per_pack[*].status=committed 的 checkbox（按 Pack ID 精确匹配 plan 文档中 `- [ ] **Pack N.M**` 行）"
- Modify: `plugin/build/templates/worker-loop.md.tmpl` — 删除"写 doc-patch.diff"步骤（具体行由 Worker grep `doc-patch` 定位）
- Modify: `plugin/agents/pack-executor.md` — 删除 doc-patch.diff 写出指令（L119/L120/L124/L182/L184 共 5 处）
- Modify: `plugin/agents/complex-pack-executor.md` — 删除 doc-patch.diff 写出指令（L117/L118/L122/L180/L182 共 8 处）
- Modify: `plugin/hooks/guard-doc-edit.sh` — 顶部注释 L14-L16 更新（不再提及 doc-patch.diff control-plane）
- Modify: `plugin/architecture-draft.md` — 删除 §7.5（doc-patch 章节）+ Decision 6 + 多处 doc-patch.diff / guard-plan-doc-patch / doc-patch-apply.sh 提及（grep 定位）
- Modify: `plugin/skills/orchestrate-execution/SKILL.md` Step 14（L447 附近）— 写入 Coordinator checkbox toggle 权威规则
- Modify: `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md` — 写入 Coordinator checkbox toggle 权威规则

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 4（含 Coordinator checkbox toggle 权威规则四步骤）
- `plugin/hooks/agent-return-handler.sh`（理解 NEXT 输出格式）
- `plugin/skills/orchestrate-execution/SKILL.md` L447 Step 14（理解 Plan 推进当前流程）

**Contract anchors:**
- Owner: D4 doc-patch 系统删除 + Coordinator checkbox toggle 权威规则
- Producer: 删除 guard-plan-doc-patch.sh / doc-patch-apply.sh
- Consumer: agent-return-handler.sh / worker-loop.md.tmpl / 2 个 agent 定义 / 2 个 SKILL/reference
- Model: plan-return-v1.json `per_pack[*].status == "committed"` 是新 source-of-truth
- Verification: grep 全树 `doc-patch` / `doc_patch` 无残留；3 处 Coordinator checkbox toggle 规则落地（含 `per_pack[*].status == committed` 字串）

**Acceptance criteria:**
- [ ] `plugin/hooks/guard-plan-doc-patch.sh` 不存在
- [ ] `plugin/scripts/lib/doc-patch-apply.sh` 不存在
- [ ] `plugin/scripts/tests/test_doc_patch_apply.sh` + `plugin/hooks/tests/test_guard_plan_doc_patch.sh` 不存在
- [ ] `plugin/hooks/hooks.json` 不含 `guard-plan-doc-patch.sh` 条目
- [ ] `plan-return-v1.json` 不含 `doc_patch_path` 字段；L4 description 不含 "doc-patch.diff" 字符串
- [ ] `agent-return-handler.sh` 不含 "doc-patch.diff" 字符串；含 "per_pack" 和 "status=committed" 输出
- [ ] `worker-loop.md.tmpl` 不含 "doc-patch.diff" 字符串
- [ ] `pack-executor.md` + `complex-pack-executor.md` 不含 "doc-patch" 字符串
- [ ] `architecture-draft.md` §7.5（doc-patch）+ Decision 6 段删除
- [ ] `orchestrate-execution/SKILL.md` Step 14 含 `per_pack[*].status == committed` 表述
- [ ] `plan-review-resolution.md` 含 Coordinator checkbox toggle 权威规则
- [ ] `guard-doc-edit.sh` 顶部注释不再提及 doc-patch.diff
- [ ] 全树 `grep -rn "doc-patch\|doc_patch" plugin/` 在 .sh / .json / .md 中无残留（git history / decision rationale 除外）
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
- [ ] `bash plugin/build/build.sh --apply --plugin-dir plugin && bash plugin/build/build.sh --check --plugin-dir plugin` 通过

**Verification commands:**
- `test ! -e plugin/hooks/guard-plan-doc-patch.sh` → Expected: exit 0
- `test ! -e plugin/scripts/lib/doc-patch-apply.sh` → Expected: exit 0
- `test ! -e plugin/scripts/tests/test_doc_patch_apply.sh` → Expected: exit 0
- `test ! -e plugin/hooks/tests/test_guard_plan_doc_patch.sh` → Expected: exit 0
- `grep -n "guard-plan-doc-patch" plugin/hooks/hooks.json` → Expected: 无输出
- `jq '.properties.doc_patch_path' plugin/state-schema/plan-return-v1.json` → Expected: null
- `grep -n "doc-patch" plugin/state-schema/plan-return-v1.json` → Expected: 无输出
- `grep -n "doc-patch" plugin/hooks/agent-return-handler.sh` → Expected: 无输出
- `grep -n "per_pack\[\*\]\.status == committed\|per_pack\[\*\].status==committed\|per_pack\[\*\].status = committed" plugin/skills/orchestrate-execution/SKILL.md` → Expected: 命中（Step 14）
- `grep -n "per_pack" plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md` → Expected: 命中
- `grep -rn "doc-patch\|doc_patch" plugin/` | grep -v ".git\|/reviews/" → Expected: 无残留
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 一个 atomic commit：hook 删除 + lib 删除 + 2 test 删除 + schema 删除 + agent-return-handler 改写 + worker-loop.md.tmpl + 2 agent + guard-doc-edit 注释 + 3 处 Coordinator 规则落地 + architecture-draft.md
**Risk flags:** high-risk（Coordinator checkbox toggle 权威规则若漏写一处，Coordinator 不知如何 Edit plan 文档，导致整个 Execution flow 卡住）
**发布风险:** Coordinator 漏勾 checkbox（设计文档 §6.1 风险 4）— `guard-premature-push.sh` 已有兜底（plan 未勾完不能 push）
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** Worker Loop segment 5 重写（Pack 2.8）；segment 6 artifact schema 中 per_pack 必填结构不动（仅删 doc_patch_path 可选字段）

#### Implementation tasks

- [ ] Step 1: 写失败测试（Red）— Coordinator checkbox toggle 规则在 3 处落地
  - Run: `grep -n "per_pack\[\*\]\.status" plugin/skills/orchestrate-execution/SKILL.md plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md plugin/hooks/agent-return-handler.sh` → Expected (now): 无命中；Expected (after): 3 文件各至少 1 处命中

- [ ] Step 2: 删除 guard-plan-doc-patch.sh + 2 个 doc-patch 测试
  - Run: `rm plugin/hooks/guard-plan-doc-patch.sh plugin/hooks/tests/test_guard_plan_doc_patch.sh plugin/scripts/lib/doc-patch-apply.sh plugin/scripts/tests/test_doc_patch_apply.sh`
  - Verify: 4 个文件均不存在

- [ ] Step 3: 修改 hooks.json
  - 文件: `plugin/hooks/hooks.json`
  - 定位: `grep -n "guard-plan-doc-patch" plugin/hooks/hooks.json`（L82 附近）
  - 动作: 删除该 hook 条目整段（PreToolUse + Write matcher + command）
  - 验证: `python3 -m json.tool plugin/hooks/hooks.json >/dev/null` → exit 0

- [ ] Step 4: 修改 plan-return-v1.json schema
  - 文件: `plugin/state-schema/plan-return-v1.json`
  - L4: description 文本中删除所有 "doc-patch.diff" / "doc_patch_path" / "Decision 6" 提及 — 重写 description 段，反映 per_pack 是 Plan-level envelope 唯一权威，Coordinator 在 Plan Implementation Review pass 后用 Edit 工具直接 toggle plan 文档 checkbox（按 per_pack[*].status == committed 决定）
  - properties: 删除 `doc_patch_path` 字段段
  - L39: description 中 "doc-patch NOT yet applied" 类提及全部删除

- [ ] Step 5: 修改 agent-return-handler.sh
  - 文件: `plugin/hooks/agent-return-handler.sh`
  - 定位: `grep -n "doc-patch\|doc_patch" plugin/hooks/agent-return-handler.sh`（L13/L94/L108/L111/L114/L124/L127）
  - 动作 a: 删除 L13 / L94 注释中 "doc-patch NOT applied here" 等
  - 动作 b: 改写 L108（verdict=pass）输出为:
    > `[multi-model-workflow] NEXT: Plan ${PLAN_ID} Worker returned verdict=pass. Dispatch Plan Implementation Review (Codex). After review pass, Coordinator MUST Edit plan doc: toggle checkbox '- [ ]' → '- [x]' for each Pack where per_pack[*].status == committed (read plan-return.json at ${BUDGET_DIR}/plan-returns/${RUN_ID}/${PLAN_ID}/plan-return.json).`
  - 动作 c: 改写 L111（verdict=partial-pass）类似格式
  - 动作 d: 改写 L114（verdict=blocked）— 删除 doc-patch 提及，保留 per_pack[].reason + open-items.json 引用
  - 动作 e: 改写 L124 / L127 — 同上格式（删除 "doc-patch.diff NOT applied" 句）

- [ ] Step 6: 修改 worker-loop.md.tmpl
  - 文件: `plugin/build/templates/worker-loop.md.tmpl`
  - 定位: `grep -n "doc-patch" plugin/build/templates/worker-loop.md.tmpl`
  - 动作: 删除所有 "写 doc-patch.diff" / "doc-patch.diff" 提及（包括步骤段、artifact list 段）

- [ ] Step 7: 修改 pack-executor.md + complex-pack-executor.md
  - 文件 1: `plugin/agents/pack-executor.md`
  - 定位: `grep -n "doc-patch\|doc_patch" plugin/agents/pack-executor.md`（L119/L120/L124/L182/L184）
  - 动作: 删除 doc-patch.diff 写出指令 + 引用段（每处删整行或整段）
  - 文件 2: `plugin/agents/complex-pack-executor.md`
  - 定位: 同上（L117/L118/L122/L180/L182）
  - 动作: 同上

- [ ] Step 8: 修改 guard-doc-edit.sh 注释
  - 文件: `plugin/hooks/guard-doc-edit.sh` L14-L16
  - 当前:
    ```
    # (plan-return.json, doc-patch.diff, open-items.json) are control-plane data,
    # not source-of-truth design docs; guard-plan-doc-patch.sh validates the
    # doc-patch.diff content separately to ensure it only touches plan-doc
    ```
  - 改为:
    ```
    # (plan-return.json, open-items.json) are control-plane data,
    # not source-of-truth design docs. Coordinator owns plan-doc checkbox
    # toggling per per_pack[*].status==committed (read from plan-return.json).
    ```

- [ ] Step 9: 修改 architecture-draft.md
  - 文件: `plugin/architecture-draft.md`
  - 定位: `grep -n "doc-patch\|guard-plan-doc-patch\|doc-patch-apply\|Decision 6" plugin/architecture-draft.md`（多处：L58/L178/L195/L222/L357/L379/L408/L461-462/L470/L518/L559/L579-585/L654/L687/L759/L1242/L1288/L1328/L1329/L1351/L1371）
  - 动作: 
    - 删除 §7.5（"doc-patch（plan checkbox 勾选）"章节，约 10-15 行）
    - 删除 Decision 6 表行 + 文中提及（L1242 / L1288）
    - 删除 guard-plan-doc-patch.sh hook 条目（L408 / L461-462 / L518）
    - 删除 doc-patch-apply.sh lib 条目（L759）
    - 删除 plan-return.json description 中 doc-patch 提及（L559）
    - 删除流程图中 doc-patch 节点（L178 / L195 / L357 / L379 / L654 / L687）
    - 删除测试统计中 guard-plan-doc-patch / doc-patch apply 行（L1328 / L1329）
    - 更新 L1351 / L1371（移除 doc-patch apply 触发同步规则）

- [ ] Step 10: 写入 Coordinator checkbox toggle 权威规则（3 处）
  - 文件 1: `plugin/skills/orchestrate-execution/SKILL.md` Step 14 段（L447）
  - 在 Step 14 起始处 + Plan Implementation Review pass 后的 Edit 动作前，新增段:
    ```markdown
    **Coordinator checkbox toggle 权威规则**（D4 source-of-truth）：
    Plan Implementation Review pass 后，Coordinator Edit plan 文档勾选 checkbox 的 source-of-truth 是 `plan-return.per_pack[*]` where `status == committed`：
    1. Read `.claude/multi-model-workflow/plan-returns/<plan_id>/plan-return.json`
    2. 对每个 `per_pack[i].status == "committed"` 的 Pack，按 Pack ID 精确匹配 `docs/orchestrate/plans/<slug>/<plan-file>.md` 中 `- [ ] **Pack N.M**` 行，Edit toggle 为 `- [x] **Pack N.M**`
    3. `status` 不是 `committed`（pending / in_progress / blocked / skipped）的 Pack 不勾选
    ```
  - 文件 2: `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md`
  - 在合适段落写入同规则（4 步骤完整列出，按设计文档 §4.2 决策 4）

- [ ] Step 11: 跑 build + 全量测试
  - Run: `bash plugin/build/build.sh --apply --plugin-dir plugin` → Expected: 通过
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: 通过
  - Run: `python3 -m json.tool plugin/hooks/hooks.json >/dev/null` → exit 0
  - Run: `python3 -m json.tool plugin/state-schema/plan-return-v1.json >/dev/null` → exit 0
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

- [ ] Step 12: 全树清扫验证
  - Run: `grep -rn "doc-patch\|doc_patch" plugin/` | grep -v ".git\|/reviews/" → Expected: 无残留

- [ ] Step 13: Suggested commit boundary
  - Message: `feat(plugin): D4 删除 doc-patch 系统 + 落地 Coordinator checkbox toggle 权威规则（per_pack[*].status==committed）`

---

### Task Pack 2.8: D6 — agent-context-check 删除 + worker-loop segment 5 双路径

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/002-contracts-and-state-cleanup.md Small issue 8

**Goal behavior:** `state.sh agent-context-check` 子命令删除 + 测试文件删除 + 11 处实际调用点（亲验 grep 结果：worker-loop.md.tmpl L55+L100 / pack-executor L114+L159 / complex-pack-executor L112+L157+L187 / architecture-draft L215+L355+L739+L1240；设计文档 D6 描述的 "18 处" 含 architecture-draft 文中重复提及和流程图节点）删除；**重写 `worker-loop.md.tmpl` segment 5** 必须包含两条路径（main flow 内）：(a) 正常路径 `packs_in_session += 1`；(b) 启动 / Compaction recovery 路径 从 `execution-state.plans[plan_id].packs[*].status == "committed"` 计数作为初值。Worker 启动步骤 3 增加 recovery 逻辑。

**Owned files / responsibilities:**
- Modify: `plugin/scripts/state.sh` — 删除 `agent-context-check` 子命令（L982-L1030 函数 cmd_agent_context_check + L2124 dispatcher case）
- Delete: `plugin/scripts/tests/test_state_agent_context_check.sh`
- Modify: `plugin/build/templates/worker-loop.md.tmpl` — 删除 L55 + L100 `state.sh agent-context-check` 调用；**重写 segment 5（Context 自监控）** main flow 含两条路径
- Modify: `plugin/agents/pack-executor.md` — 删除 L114 + L159 `state.sh agent-context-check` 调用
- Modify: `plugin/agents/complex-pack-executor.md` — 删除 L112 + L157 + L187 `state.sh agent-context-check` 调用 + 高风险自检 checklist 引用
- Modify: `plugin/architecture-draft.md` — 更新 L215 / L355 / L739 / L1240 4 处提及（删除 agent-context-check 表行 / 流程图节点 / 测试统计行）

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 6（含 worker-loop.md.tmpl segment 5 双路径重写规则）+ §9.1 场景 5（recovery 路径）
- `plugin/build/templates/worker-loop.md.tmpl`（理解当前 segment 5 结构）
- `plugin/state-schema/execution-state-v1.json`（理解 plans[plan_id].packs[*].status 字段）

**Contract anchors:**
- Owner: D6 agent-context-check 删除 + Worker Loop segment 5 双路径
- Producer: Worker Loop 模板（worker-loop.md.tmpl）注入到 worker-prompts/<pack-id>.md
- Consumer: pack-executor / complex-pack-executor / Worker runtime
- Model: execution-state-v1.json `plans[plan_id].packs[*].status == "committed"` 是 packs_in_session 重建源
- Verification: grep `agent-context-check` 全树无残留；worker-loop.md.tmpl segment 5 同时含两条路径关键字串

**Acceptance criteria:**
- [ ] `bash plugin/scripts/state.sh agent-context-check --help` exit ≠ 0
- [ ] `plugin/scripts/tests/test_state_agent_context_check.sh` 不存在
- [ ] `worker-loop.md.tmpl` segment 5 同时含:
  - 正常路径关键字串: `packs_in_session += 1` （或 `packs_in_session += 1` 同义中文表述）
  - 启动/recovery 关键字串: `execution-state.plans` + `status == "committed"`（或 `status==committed`）或同义"从 execution-state 重建 counter"表述
- [ ] `pack-executor.md` + `complex-pack-executor.md` 不含 `state.sh agent-context-check` 字符串
- [ ] `architecture-draft.md` L215/L355/L739/L1240 对应内容更新或删除
- [ ] 全树 `grep -rn "agent-context-check" plugin/` 在 .sh / .md 中无残留（git history / decision rationale 除外）
- [ ] `bash plugin/build/build.sh --apply --plugin-dir plugin && bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

**Verification commands:**
- `bash plugin/scripts/state.sh agent-context-check 2>&1; echo "exit=$?"` → Expected: exit ≠ 0
- `test ! -e plugin/scripts/tests/test_state_agent_context_check.sh` → Expected: exit 0
- `grep -c "packs_in_session" plugin/build/templates/worker-loop.md.tmpl` → Expected: ≥ 1
- `grep -c "execution-state.plans\|从 execution-state 重建" plugin/build/templates/worker-loop.md.tmpl` → Expected: ≥ 1
- `grep -n "agent-context-check" plugin/agents/pack-executor.md plugin/agents/complex-pack-executor.md` → Expected: 无输出
- `grep -rn "agent-context-check" plugin/` | grep -v ".git\|/reviews/" → Expected: 无残留
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 一个 atomic commit：state.sh 子命令删除 + 测试删除 + worker-loop segment 5 双路径重写 + 2 agent + 4 处 architecture-draft 更新
**Risk flags:** high-risk（segment 5 漏写 recovery path → long-running worker context 溢出；按 §6.1 风险 segment 5 双路径 + verify-maturity grep 两条路径关键字串兜底）
**发布风险:** Worker Loop segment 5 重写——若漏 recovery path，启动后 counter 始终从 0 开始，5+2 阈值会被推迟，导致 long-running worker context 溢出
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** Worker Loop 其他 5 段（启动 / 循环 / verdict / repair / artifact）semantics 不动；只改 segment 5 mechanism（设计文档 §10 第 1 条已说明）

#### Implementation tasks

- [ ] Step 1: 写失败测试（Red）— worker-loop.md.tmpl segment 5 含双路径
  - Run: `grep -c "packs_in_session" plugin/build/templates/worker-loop.md.tmpl` → Expected (now): 0 或不含双路径；Expected (after): ≥ 1
  - Run: `grep -c "execution-state.plans\|从 execution-state 重建" plugin/build/templates/worker-loop.md.tmpl` → Expected (after): ≥ 1

- [ ] Step 2: 删除 state.sh agent-context-check 子命令
  - 文件: `plugin/scripts/state.sh`
  - 定位 L982-L1030（cmd_agent_context_check 函数）+ L2124（dispatcher case `agent-context-check)`）
  - 动作: Edit 删除 function 段 + dispatcher case
  - 验证: `grep -n "agent_context_check\|agent-context-check" plugin/scripts/state.sh` → 无输出

- [ ] Step 3: 删除 test_state_agent_context_check.sh
  - Run: `rm plugin/scripts/tests/test_state_agent_context_check.sh`
  - Verify: `test ! -e plugin/scripts/tests/test_state_agent_context_check.sh` → exit 0

- [ ] Step 4: 修改 worker-loop.md.tmpl — 删除 agent-context-check 调用 + 重写 segment 5
  - 文件: `plugin/build/templates/worker-loop.md.tmpl`
  - 定位: `grep -n "agent-context-check\|segment 5\|Context 自监控" plugin/build/templates/worker-loop.md.tmpl`（L55 / L100 + segment 5 标题）
  - 动作 a: 删除 L55 + L100 `state.sh agent-context-check` 调用代码
  - 动作 b: 重写 segment 5（Context 自监控）main flow 段。**完整内容**（写出来，按设计文档 §4.2 D6 段，必须主流程文本中明示双路径）:
    ```markdown
    ## Segment 5: Context 自监控

    Worker 维护本地 in-memory counter `packs_in_session`，用于判断是否需要 fresh worker。

    **正常路径**（每完成 1 个 Pack）:
    ```
    packs_in_session += 1
    if packs_in_session >= 5 and remaining_packs >= 2:
        verdict = "need-fresh-worker"
        break
    ```

    **启动 / Compaction recovery 路径**（Worker 启动 Step 3 必须执行，用于 in-memory counter 丢失场景）:
    ```
    # 从 execution-state.plans[plan_id].packs[*].status == "committed" 计数作为 packs_in_session 初值
    packs_in_session = count(execution-state.plans[plan_id].packs[*] where status == "committed")
    ```

    `execution-state` 由 `track-execution-state.sh` 自动维护，是单一真相源。Compaction 后内存丢失时，启动 recovery 路径精确反映已完成 Pack 数，无需"猜"。
    ```

- [ ] Step 5: 修改 pack-executor.md
  - 文件: `plugin/agents/pack-executor.md` L114 + L159
  - 定位: `grep -n "agent-context-check\|need-fresh-worker" plugin/agents/pack-executor.md`
  - 动作: 删除 `ctx=$(bash state.sh agent-context-check ...)` 行（L114）+ 删除 `bash state.sh agent-context-check ...` 行（L159）
  - 注意: 保留 need-fresh-worker 判断逻辑（改为 in-memory counter 判断——按 Step 4 segment 5 模板）

- [ ] Step 6: 修改 complex-pack-executor.md
  - 文件: `plugin/agents/complex-pack-executor.md` L112 + L157 + L187
  - 动作: 同 pack-executor.md（删除 3 处 state.sh agent-context-check 调用）
  - 注意: L187 是"高风险自检 checklist"段——删除 "在 state.sh agent-context-check 之前先做一轮高风险自检" 中 "state.sh agent-context-check" 字符串；保留"高风险自检 checklist" 行为本身（改为 "在 verdict 判断之前先做一轮高风险自检"）

- [ ] Step 7: 修改 architecture-draft.md
  - 文件: `plugin/architecture-draft.md`
  - 定位:
    - L215: `state.sh agent-context-check` 表行 — 删除整行
    - L355: 流程图中 `state.sh agent-context-check → 若 need-fresh-worker → break` — 改为 `Worker 本地 counter 判断 → 若 need-fresh-worker → break`
    - L739: 子命令表中 `agent-context-check` 行 — 删除整行
    - L1240: 测试统计中"`state.sh agent-context-check` + worker-loop.md.tmpl 段 6"提及 — 改为 "Worker in-memory counter + execution-state 重建 + worker-loop.md.tmpl segment 5 双路径"
  - 如果整体 §17 / Decision 4 / 其他段含 agent-context-check 提及 → 一并更新

- [ ] Step 8: 跑 build + 全量测试
  - Run: `bash plugin/build/build.sh --apply --plugin-dir plugin` → Expected: 通过（worker-loop.md.tmpl 锚点重新注入到 pack-executor.md + complex-pack-executor.md）
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: 通过
  - Run: `grep -c "packs_in_session" plugin/build/templates/worker-loop.md.tmpl` → Expected: ≥ 1
  - Run: `grep -c "execution-state.plans\|从 execution-state 重建" plugin/build/templates/worker-loop.md.tmpl` → Expected: ≥ 1
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

- [ ] Step 9: 全树清扫验证
  - Run: `grep -rn "agent-context-check" plugin/` | grep -v ".git\|/reviews/" → Expected: 无残留

- [ ] Step 10: Suggested commit boundary
  - Message: `feat(plugin): D6 删除 state.sh agent-context-check + 重写 worker-loop segment 5 双路径（normal + recovery from execution-state）`

---

## Cross-Plan Contract Anchors

> 本节由 plan-writing Step 12b 在所有 plan 完成后统一回填到 source design.md `## Cross-Plan Contract Anchors` section。

本 Plan 触碰的合同表面（供其他 Plan 同步对照）:
- `plugin/state-schema/dispatch-envelope-v1.json` `review_intent` enum: 3 值 → 1 值（baseline）— Pack 2.2 + 2.5
- `plugin/state-schema/workflow-state-v1.json`: 删除 `path_a_escalation` / `blocked_for_self_fix` / `bug_seed_path` / `review_effectiveness` — Pack 2.3 + 2.5 + 2.6
- `plugin/state-schema/plan-return-v1.json`: 删除 `doc_patch_path` 字段 — Pack 2.7
- `plugin/scripts/state.sh`: 删除 4 子命令（`business-summary` / `plans` / `path-a-escalation` / `agent-context-check`）— Pack 2.4 + 2.5 + 2.8
- `plugin/build/templates/disposition-table.md.tmpl`: disposition enum 10 → 9 — Pack 2.5
- `plugin/build/templates/review-dispatch.md.tmpl`: 删除 `variant=targeted-re-review` — Pack 2.1
- `plugin/build/templates/worker-loop.md.tmpl`: segment 5 重写 + 删除 doc-patch.diff 步骤 — Pack 2.7 + 2.8
- `plugin/hooks/`: 删除 `guard-plan-doc-patch.sh`（Pack 2.7）+ `gate-codex-review.sh` 简化（Pack 2.2 + 2.5）+ `agent-return-handler.sh` NEXT 改写（Pack 2.7）+ `validate-plan-dispatch.sh` Step 8 删除（Pack 2.5）
- `plugin/scripts/lib/`: 删除 `doc-patch-apply.sh` / `review-effectiveness.sh` / `learnings-poison-detector.sh`（合并入 learnings-jsonl.sh）— Pack 2.3 + 2.4 + 2.7
- **新增权威规则**：Coordinator Edit 的 source-of-truth = `plan-return.per_pack[*].status == committed`（落地 3 处：`orchestrate-execution/SKILL.md` Step 14 + `plan-review-resolution.md` + `agent-return-handler.sh` NEXT 指令）— Pack 2.7
- **Budget 公式更新**：`budget_total = 3P + 12` → `2P + 6`（落地 plan-gates.md L46 + orchestrate-plan-writing/SKILL.md L172）— Pack 2.2

下游 Plan（特别是 Issue 001 / Issue 003）需要同步对照本合同变化：
- Issue 001 D1（canonical reference 抽取）在 Pack 2.1 之后执行——本 Plan 已通过 cross-issue priority 保证执行顺序
- Issue 003 处理的 SKILL.md / reference 压缩需基于本 Plan 删除后的合同表面进行

---

## 执行顺序与依赖图

```
Pack 2.1 (D13a .tmpl)      ← cross-issue priority: 必须先于 Issue 001 全部 Pack 执行
   ↓
[Issue 001 全部 Pack]      ← 由 Coordinator 安排 Issue 001 plan 执行
   ↓
Pack 2.2 (D13b 全局)       ← 依赖 Pack 2.1
   ↓
Pack 2.3 (D7a review_effectiveness)  独立     Pack 2.4 (D7b state.sh 死命令)  独立
Pack 2.5 (D3 Path A)       ← 依赖 Pack 2.2     Pack 2.6 (D5 bug-seed)  独立
Pack 2.7 (D4 doc-patch)    独立                Pack 2.8 (D6 agent-context-check)  独立
```

**注**：本 Plan 内 Pack 严格串行执行（按 Dependencies 字段排序）。Pack 2.3 / 2.4 / 2.6 / 2.7 / 2.8 在 Pack 2.2 完成后可任意顺序串行；Pack 2.5 必须在 Pack 2.2 之后。
