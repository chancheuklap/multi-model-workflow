# 基础设施层重构（Template & Reference & Routes）Implementation Plan

**Goal:** 把 plugin 的"广义基础设施层"（模板系统 / 死孤儿文件 / 脚本 / hook / route enum / agent frontmatter / reference 路标）做一次系统级清理与去重，让下游 Issue 002（合同 & 状态机）和 Issue 003（phase skill 优化）在干净的基线上展开。

**Source design:** docs/orchestrate/design/2026-05-28-workflow-token-economy.md
**Source issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/001-infrastructure-consolidation.md
**Execution owner:** Orchestrate Workflow
**Blocked by:** None — 可立即启动
**Architecture:** plugin 内部重构（Build template 系统去重 / Reference 文件清扫 / Hook 行为降级 / Route enum 折叠 / Agent frontmatter 瘦身 / 脚本合并 + shim 期），不动 Worker Loop 6 段合同语义、Document-as-Context 主线、Codex Review 5 步派发协议。
**Tech stack:** Bash 4+（hooks / scripts / build.sh）、`jq` JSON 操作、Python3 `json.tool` 校验、Claude Code Plugin Anchor System、`plugin/state-schema/*.json` schema、`verify-maturity.sh` 整体回归测试套件、`run-all-tests.sh`。
**Quality gate:** 进入 Plan Review 前必须通过过度设计 / 设计不足自审。

## Scope notes（plan-writer 对设计文本的执行级澄清）

1. **D1 ↔ D13 cycle 解法（advisor approach，design "或等价做法" 授权）**：Pack 9 抽取 canonical reference 时，**抽取过程本身排除 `[variant=targeted-re-review]` 子模块**——canonical 文件从第一天就干净。Issue 002 D13 之后会删 `.tmpl` 中该 variant（对 canonical 消费者是 no-op，因为 inject 已停）。这不是预执行 D13，而是抽取时归一化（normalize on extraction）。
2. **D11 narrowed**：本 Issue 仅做 agent frontmatter 瘦身（Pack 1：docs-worker + plan-writer 移除 `skills:` 字段）。设计 D11 中提到的 Discovery SKILL.md Steps 3-6 显式 `Skill({ skill: "grill-with-docs" })` 调用 + discovery-discussion.md L80 改写——defer 到 Issue 003（避免与 D15 grill-with-docs Step 0 提升重复触碰同一文件）。
3. **Path A 处理边界**：Issue 001 仅删除 `path-a-re-review.md` 孤儿文件（Pack 5）+ `gate-codex-review.sh` 中 `path-a-re-review` 分支（Pack 7）。**不动** `state.sh path-a-escalation` 子命令、`workflow-state.path_a_escalation` 字段、SKILL.md 中 `path-a-escalation` 使用引用——这些归属 Issue 002（D3 完全删除 Path A）。Pack 7 删除 hook 检查后到 Issue 002 落地前的过渡期：hook 不再阻断、SKILL.md 仍有 stale 引用，可接受（hook 检查删除不会破坏任何 happy path）。
4. **execution-worker-handbook 路径 bug**：本 Issue 仅清理 architecture-draft.md L286 / L299 两处提及"execution-worker-handbook（Worker 自读）"的描述（这两处描述了不存在的文件，是 stale 文档），其余 6 处引用（SKILL.md L202 / agent 文件 / worker-loop.md.tmpl L12 critical runtime bug / architecture-draft L53 + L338）归属 Issue 003 D21（C1 完整版）。
5. **Shim 期持续到 Issue 003 之后**：Pack 8 完成后保留 4 个旧脚本作为 shim，所有 producer 在本 Pack 内迁移完成。设计 §5.8 规定"所有 producer 完成迁移 + 一轮 Plan Implementation Review 通过后再删除 shim"——本 Pack 触发的 PIR 不算最终删除信号，因为 Issue 002 / 003 仍可能新增对脚本的引用。Shim 删除归入 Issue 003 后的清理阶段（Open Item）。

## Cross-Plan Contract Anchors

**输出给 Issue 002（依赖本 Plan 完成）**：
- `plugin/skills/_shared/{review-dispatch,repair-routing,disposition-table}.md` 已存在（canonical 已干净，不含 targeted-re-review 残留）——Issue 002 D13 只需在 `.tmpl` 源中删除该 variant，无需碰 canonical
- `plugin/scripts/dispatch-review.sh` + `dispatch-route-worker.sh` 已可用——Issue 002 可在新合并脚本上做 review_intent enum 收敛
- `workflow-state-v1.json` route enum 已为 4 值，`phase_skip` / `commit_format_override` 已就位——Issue 002 删除 `path_a_escalation` / `blocked_for_self_fix` 字段时不会与 route 字段冲突
- `gate-codex-review.sh` 中 path-a-re-review 和 targeted-re-review 分支已删——Issue 002 删除 review_intent enum 时无 hook 残留检查
- 4 个旧 dispatch 脚本仍以 shim 形式存在——Issue 002 新增引用直接指向 `dispatch-<x>.sh <subcommand>` 形式

**输出给 Issue 003（依赖本 Plan 完成）**：
- Agent frontmatter 已瘦身（docs-worker + plan-writer 无 `skills:`）——Issue 003 D11 / D18 在 agent description 加 "Coordinator must verify" 时无 frontmatter 字段冲突
- 4 个死模板（forbidden-shortcuts / state-write / trust-boundary）已删——Issue 003 phase SKILL.md 压缩时不会碰到锚点
- 3 个 multi-pr handbook 已删 + verify-maturity §6.11 已重写——Issue 003 D23 cascade 落地时无 handbook 引用残留
- Reference 路标 100% 覆盖（除 `_shared/`）+ verify-maturity 已加 signpost 检查——Issue 003 新增 reference 自动受检
- route-extensions/ 目录已删（execution + workflow 两侧）——Issue 003 不会触碰 dead reference

**Open Item 给 Final Review**：
- Hook 数：design §2.1 目标 ≤ 10，Issue 001 完成后实际 = 12（13 - 1 from guard-plan-doc-patch）。Issue 002 / 003 无额外 hook 删除。该目标在本轮 plan 范围内不可达——flag 给 Final Review 重新评估（不应在本 Issue 内强行多删）。[needs-evaluation]
- Shim 删除 deferred 到 Issue 003 关闭后的清理阶段。

## File / Responsibility Map

**Create:**
- `plugin/skills/_shared/review-dispatch.md` — canonical（baseline 路径，排除 targeted-re-review variant）
- `plugin/skills/_shared/repair-routing.md` — canonical
- `plugin/skills/_shared/disposition-table.md` — canonical
- `plugin/scripts/dispatch-review.sh` — 合并 record + validate review-dispatch
- `plugin/scripts/dispatch-route-worker.sh` — 合并 record + validate route-worker-dispatch
- `plugin/scripts/tests/test_dispatch_review_shim.sh` — 验证旧脚本 shim 转发到新脚本

**Modify:**
- `plugin/agents/docs-worker.md` — 移除 `skills:` frontmatter（Pack 1）
- `plugin/agents/plan-writer.md` — 移除 `skills:` frontmatter（Pack 1）
- `plugin/skills/orchestrate-final-review/SKILL.md` — 内联 forbidden-shortcuts（Pack 2）
- `plugin/skills/orchestrate-execution/SKILL.md` — 内联 forbidden-shortcuts / state-write / trust-boundary（Pack 2/3/4），折回 learnings-confidence-audit + learnings-trust-gate 内容（Pack 5），canonical Read 替换（Pack 9）
- `plugin/skills/orchestrate-workflow/SKILL.md` — Step 1 表 Route 4-7 删 + Route 1 Variant Table 新增（Pack 6）
- `plugin/state-schema/workflow-state-v1.json` — route enum 8→4 + phase_skip + commit_format_override（Pack 6）
- `plugin/scripts/state.sh` — init 初始化 phase_skip / commit_format_override（Pack 6）
- `plugin/hooks/hooks.json` — 移除 guard-plan-doc-patch entry（Pack 7）
- `plugin/hooks/validate-plan-dispatch.sh` — Step 6 改 WARN / Step 8 删（Pack 7）
- `plugin/hooks/gate-codex-review.sh` — 删 path-a-re-review + targeted-re-review 分支（Pack 7）
- `plugin/scripts/record-review-dispatch.sh` / `validate-review-dispatch.sh` / `record-route-worker-dispatch.sh` / `validate-route-worker-dispatch.sh` — 改为 shim（Pack 8）
- `plugin/build/build.sh` — 跳过 review-dispatch / repair-routing / disposition-table 三个 resolver（Pack 9）
- `plugin/build/tests/test_review_evidence_table.sh` — 改扫 canonical reference（Pack 9）
- `plugin/scripts/verify-maturity.sh` — §6.11 重写（Pack 5）+ L58-59 改 canonical 检查（Pack 9）+ signpost 完整性检查（Pack 10）
- `plugin/architecture-draft.md` — 删 execution-worker-handbook L286/L299 行（Pack 5）+ build template anchor 表更新（Pack 9）
- 12 处 SKILL.md / reference 中 `<!-- BEGIN: review-dispatch -->` 锚点位置（Pack 9）
- 9 处 reference 中 `<!-- BEGIN: repair-routing -->` 锚点位置（Pack 9）
- 6 处 reference 中 `<!-- BEGIN: disposition-table -->` 锚点位置（Pack 9）
- 4 个 reference 顶部补路标 blockquote（Pack 10）
- `plugin/skills/orchestrate-execution/references/execution-completion.md` — 跳跃精简（Pack 10）
- `plugin/skills/orchestrate-final-review/references/final-review-completion.md` — 跳跃精简（Pack 10）
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md` — 折回 rca-pr-conflict-methodology 正文（Pack 10）

**Delete:**
- `plugin/build/templates/forbidden-shortcuts.md.tmpl` + `plugin/build/resolvers/forbidden-shortcuts.sh`（Pack 2）
- `plugin/build/templates/state-write.md.tmpl` + `plugin/build/resolvers/state-write.sh`（Pack 3）
- `plugin/build/templates/trust-boundary.md.tmpl` + `plugin/build/resolvers/trust-boundary.sh`（Pack 4）
- `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md`（Pack 5）
- `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md`（Pack 5）
- `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md`（Pack 5）
- `plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md`（Pack 5，内容折回 SKILL.md）
- `plugin/skills/orchestrate-execution/references/learnings-trust-gate.md`（Pack 5，内容折回 SKILL.md）
- `plugin/skills/orchestrate-execution/references/path-a-re-review.md`（Pack 5）
- `plugin/skills/orchestrate-execution/references/route-extensions/`（4 个 DEPRECATED 副本，Pack 5）
- `plugin/skills/orchestrate-workflow/references/route-extensions/`（4 个 hotfix/quickfix/spike/maintenance，Pack 6）
- `plugin/hooks/guard-plan-doc-patch.sh`（Pack 7）
- `plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`（Pack 10，折回 merge-rca-investigation.md）

**Test:**
- 既有 `plugin/hooks/tests/*.sh`（57 suites baseline）+ `plugin/scripts/tests/*.sh` — 每个 Pack 后 `bash plugin/scripts/run-all-tests.sh` 全绿
- 新增 `plugin/scripts/tests/test_dispatch_review_shim.sh` — 验证 shim 转发等价（Pack 8）

**Docs / rules / registry / migration / release gate:**
- `plugin/architecture-draft.md` 章节同步（Pack 5 + Pack 9）— 因 D2/D9/D10 改动多触碰，建议在最后一个 Pack（Pack 10）末尾一次性补全 architecture-draft.md 中所有相关章节更新（含 build template 表 / hook 表 / route enum 表 / reference 拓扑），避免每个 Pack 都改一次

## 发布风险和人工门禁

| 风险面 | Task Pack | Risk flag | 提前 review | Manual gate owner |
| --- | --- | --- | --- | --- |
| build template 系统去重导致 canonical 引用漏跨 SKILL.md（CR1） | Pack 9 (D1 canonical) | high-risk | 是 — Plan Review + Plan Impl Review 双重抓 | Coordinator 亲跑一次完整 Codex review 派发验证 SKILL.md → canonical 链路 |
| Route enum 收敛破坏 hotfix 实际路径（CR2） | Pack 6 (D10) | high-risk | 是 | 用户 — hotfix 在 Route 1 + flags 下能否完整跑通需人工确认（在 Plan Implementation Review 时） |
| Hook 删除 / 降级导致 production guardrail 失效 | Pack 7 (D9) | production-risk | 是 | Plan Implementation Review 检查 hook test 套件 + grep 验证保留 hook 行为不变 |
| Scripts 合并 shim 期 producer 漏迁移 | Pack 8 (D8) | runtime | 是 | Plan Implementation Review grep `validate-/record-(review\|route-worker)-dispatch.sh` 直接调用 |
| workflow-state schema 改动影响旧 run | Pack 6 (D10) | migration | 是 — 设计文档明示 graceful ignore 策略 | Plan Implementation Review |
| verify-maturity 检查变化误判通过/不通过 | Pack 5 / 9 / 10 | normal | — | Pack 内部自验：每个 Pack 跑一次 verify-maturity 整体 |

**Release Gate**：design §6.3 明示本轮不涉及用户能感知的功能变化（plugin 自身重构），Release Gate **不触发**。

---

### Task Pack 1: Agent frontmatter 瘦身（D11 局部）

**Issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/001-infrastructure-consolidation.md Small Issue 1
**Goal behavior:** `docs-worker` 和 `plan-writer` sub-agent 不再在 frontmatter `skills:` 字段中固定加载外部 skill；body 按需 `Skill({ skill: "..." })` 调用的引导文字保留。Coordinator 派发 docs-worker 处理纯机械整理时不再背 grill-with-docs；Coordinator 派发 plan-writer 写不涉及架构的 plan 时不再背 improve-codebase-architecture。

**Owned files / responsibilities:**
- Modify: `plugin/agents/docs-worker.md`（删除 frontmatter `skills:` 字段及其值列表行）
- Modify: `plugin/agents/plan-writer.md`（同上）

**Read first:**
- 设计文档 §4.2 决策 11（Sub-agent frontmatter 瘦身）
- `plugin/agents/docs-worker.md` 当前 frontmatter L20-21（`skills:\n  - grill-with-docs`）
- `plugin/agents/plan-writer.md` 当前 frontmatter L20-21（`skills:\n  - improve-codebase-architecture`）
- `plugin/agents/pack-executor.md` / `complex-pack-executor.md` / `root-cause-analyst.md` — 这三个**保持不变**

**Contract anchors:**
- Owner: Issue 001
- Provider: `plugin/agents/{docs-worker,plan-writer}.md` frontmatter
- Consumer: Claude Code agent loading（runtime 不再 preload 这两个 skill）
- Verification: agent frontmatter 解析在 Claude Code 启动时进行；本 Pack 完成后 docs-worker / plan-writer 派发不会自动加载 skill，但 body 中 Skill() 调用仍可用

**Acceptance criteria:**
- [ ] `plugin/agents/docs-worker.md` 顶部 frontmatter（`---` 之间）不含 `skills:` key
- [ ] `plugin/agents/plan-writer.md` 顶部 frontmatter 不含 `skills:` key
- [ ] `plugin/agents/pack-executor.md` 仍含 `skills:\n  - tdd`
- [ ] `plugin/agents/complex-pack-executor.md` 仍含 `skills:\n  - tdd`
- [ ] `plugin/agents/root-cause-analyst.md` 仍含 `skills:\n  - diagnose\n  - tdd`
- [ ] body 文字（说明何时按需调用 Skill）保留
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `awk '/^---$/{c++; next} c==1' plugin/agents/docs-worker.md | grep -c '^skills:'` → Expected: 0
- `awk '/^---$/{c++; next} c==1' plugin/agents/plan-writer.md | grep -c '^skills:'` → Expected: 0
- `awk '/^---$/{c++; next} c==1' plugin/agents/pack-executor.md | grep -c '^skills:'` → Expected: 1
- `awk '/^---$/{c++; next} c==1' plugin/agents/complex-pack-executor.md | grep -c '^skills:'` → Expected: 1
- `awk '/^---$/{c++; next} c==1' plugin/agents/root-cause-analyst.md | grep -c '^skills:'` → Expected: 1
- `bash plugin/scripts/run-all-tests.sh` → Expected: all suites pass

**Commit boundary:** 单 atomic commit，scope = "feat(agents): slim docs-worker + plan-writer frontmatter skills"
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None（独立 Pack）
**Out of scope:** Discovery SKILL.md / discovery-discussion.md 中 grill-with-docs Step 0 提升（Issue 003 D15）

#### Implementation tasks
- [ ] Step 1: 写 verification 命令做 baseline 检查（现在 docs-worker.md / plan-writer.md 应该都返回 `1`，pack-executor 等返回 `1`）
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/docs-worker.md | grep -c '^skills:'` → Expected: 1（改前）
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/plan-writer.md | grep -c '^skills:'` → Expected: 1（改前）
- [ ] Step 2: Edit `plugin/agents/docs-worker.md` — 删除 L20-21 两行（`skills:` 和下一行 `  - grill-with-docs`）；保留下方 `memory: project` / `maxTurns: 20` / `color: blue` 等字段
  - 文件 / Behavior / Key assertions：frontmatter 仍以 `---` 开头结尾；其他字段顺序不变
- [ ] Step 3: Edit `plugin/agents/plan-writer.md` — 删除 L20-21 两行（`skills:` 和 `  - improve-codebase-architecture`）；保留下方 `memory: project` / `color: cyan` 等字段
- [ ] Step 4: 运行 verification 命令确认 frontmatter 已修改
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/docs-worker.md | grep -c '^skills:'` → Expected: 0
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/plan-writer.md | grep -c '^skills:'` → Expected: 0
- [ ] Step 5: 确认其他 3 个 agent 不动
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/pack-executor.md | grep -c '^skills:'` → Expected: 1
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/complex-pack-executor.md | grep -c '^skills:'` → Expected: 1
  - Run: `awk '/^---$/{c++; next} c==1' plugin/agents/root-cause-analyst.md | grep -c '^skills:'` → Expected: 1
- [ ] Step 6: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS（all suites）
- [ ] Step 7: Suggested commit boundary — `feat(agents): slim docs-worker and plan-writer frontmatter skills (D11)`

---

### Task Pack 2: 死模板 `forbidden-shortcuts` 内联并删除（D2 part a）

**Issue:** Small Issue 2
**Goal behavior:** `<!-- BEGIN: forbidden-shortcuts -->` 锚点从 2 个 active 目标文件（orchestrate-final-review/SKILL.md L155 + orchestrate-execution/SKILL.md L480）中消除，原内容以非锚点形式保留；模板源 + resolver 删除。Build system 不再处理该模板。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-final-review/SKILL.md`（L155 附近 inline content 替换锚点）
- Modify: `plugin/skills/orchestrate-execution/SKILL.md`（L480 附近 inline content 替换锚点）
- Delete: `plugin/build/templates/forbidden-shortcuts.md.tmpl`
- Delete: `plugin/build/resolvers/forbidden-shortcuts.sh`

**Read first:**
- 设计文档 §4.2 决策 2（模板清理）+ §5.4 Build template anchor 合同变化
- `plugin/build/templates/forbidden-shortcuts.md.tmpl` 当前内容（这是要 inline 的源）
- `plugin/build/resolvers/forbidden-shortcuts.sh` 当前逻辑（用于理解 variant 处理）
- `plugin/skills/orchestrate-final-review/SKILL.md` L150-180（锚点上下文）
- `plugin/skills/orchestrate-execution/SKILL.md` L475-490（锚点上下文）

**Contract anchors:**
- Owner: Issue 001
- Provider: 2 个 SKILL.md（content 直接 inline）
- Consumer: Coordinator reading SKILL.md
- Verification: build.sh --check 不再有 `forbidden-shortcuts` 处理路径

**Acceptance criteria:**
- [ ] `grep -rn 'BEGIN: forbidden-shortcuts' plugin/` 返回空
- [ ] `grep -rn 'END: forbidden-shortcuts' plugin/` 返回空
- [ ] `test ! -f plugin/build/templates/forbidden-shortcuts.md.tmpl`
- [ ] `test ! -f plugin/build/resolvers/forbidden-shortcuts.sh`
- [ ] orchestrate-final-review/SKILL.md L150-180 含原 forbidden-shortcuts 内容（grep 关键字符串，如 "禁止快捷方式" 或同义中文/英文标志）
- [ ] orchestrate-execution/SKILL.md L475-490 同上
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `grep -rn 'BEGIN: forbidden-shortcuts\|END: forbidden-shortcuts' plugin/` → Expected: empty
- `test ! -f plugin/build/templates/forbidden-shortcuts.md.tmpl && echo OK` → Expected: OK
- `test ! -f plugin/build/resolvers/forbidden-shortcuts.sh && echo OK` → Expected: OK
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(build): inline forbidden-shortcuts and remove template (D2)"
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** state-write / trust-boundary（独立 Pack）

#### Implementation tasks
- [ ] Step 1: Read 当前模板和 resolver
  - Run: `cat plugin/build/templates/forbidden-shortcuts.md.tmpl` → 记下完整内容
  - Run: `cat plugin/build/resolvers/forbidden-shortcuts.sh` → 确认 resolver 是否处理 variant；如有 variant，需要对每个 active site 调用 resolver 还原 expanded 内容
- [ ] Step 2: 跑当前 build 确认基线
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0（baseline）
- [ ] Step 3: Read `plugin/skills/orchestrate-final-review/SKILL.md` L140-180 拿到完整锚点块；记录 BEGIN 行号和 END 行号
- [ ] Step 4: Edit orchestrate-final-review/SKILL.md — 把整个 `<!-- BEGIN: forbidden-shortcuts ... -->` 行 + 内容 + `<!-- END: forbidden-shortcuts -->` 替换为纯内容（无 BEGIN/END 注释）。内容应为 resolver 展开后的最终文本
- [ ] Step 5: Read orchestrate-execution/SKILL.md L470-495 同样处理；记录 BEGIN/END 行号；Edit 替换
- [ ] Step 6: 删除模板源
  - Run: `rm plugin/build/templates/forbidden-shortcuts.md.tmpl`
  - Run: `rm plugin/build/resolvers/forbidden-shortcuts.sh`
- [ ] Step 7: 跑 build --check 确认无 active anchor 残留
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- [ ] Step 8: grep 验证 anchor 清零
  - Run: `grep -rn 'BEGIN: forbidden-shortcuts\|END: forbidden-shortcuts' plugin/` → Expected: empty
- [ ] Step 9: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 10: Suggested commit boundary — `refactor(build): inline forbidden-shortcuts and remove template (D2)`

---

### Task Pack 3: 死模板 `state-write` 内联并删除（D2 part b）

**Issue:** Small Issue 3
**Goal behavior:** `<!-- BEGIN: state-write -->` 锚点从 orchestrate-execution/SKILL.md L211 单一 active site 中消除；模板源 + resolver 删除。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-execution/SKILL.md`（L211 附近）
- Delete: `plugin/build/templates/state-write.md.tmpl`
- Delete: `plugin/build/resolvers/state-write.sh`

**Read first:**
- 设计文档 §4.2 决策 2 + §5.4
- `plugin/build/templates/state-write.md.tmpl`
- `plugin/build/resolvers/state-write.sh`
- `plugin/skills/orchestrate-execution/SKILL.md` L205-220

**Contract anchors:**
- Owner: Issue 001
- Provider: orchestrate-execution/SKILL.md（content inline）
- Consumer: Coordinator reading SKILL.md
- Verification: build --check 不再触及 state-write

**Acceptance criteria:**
- [ ] `grep -rn 'BEGIN: state-write\|END: state-write' plugin/` 返回空
- [ ] `test ! -f plugin/build/templates/state-write.md.tmpl`
- [ ] `test ! -f plugin/build/resolvers/state-write.sh`
- [ ] orchestrate-execution/SKILL.md L205-220 含原 state-write 内容（grep 关键字符串验证）
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `grep -rn 'BEGIN: state-write\|END: state-write' plugin/` → Expected: empty
- `test ! -f plugin/build/templates/state-write.md.tmpl && echo OK` → Expected: OK
- `test ! -f plugin/build/resolvers/state-write.sh && echo OK` → Expected: OK
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(build): inline state-write and remove template (D2)"
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** forbidden-shortcuts / trust-boundary（独立 Pack）

#### Implementation tasks
- [ ] Step 1: Read 模板和 resolver
  - Run: `cat plugin/build/templates/state-write.md.tmpl` → 记录内容
  - Run: `cat plugin/build/resolvers/state-write.sh` → 确认 variant 处理
- [ ] Step 2: Baseline build check
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- [ ] Step 3: Read orchestrate-execution/SKILL.md L205-225 拿到完整锚点块
- [ ] Step 4: Edit 替换 BEGIN-END 整段为纯内容
- [ ] Step 5: 删除源
  - Run: `rm plugin/build/templates/state-write.md.tmpl plugin/build/resolvers/state-write.sh`
- [ ] Step 6: 验证清零
  - Run: `grep -rn 'BEGIN: state-write\|END: state-write' plugin/` → Expected: empty
- [ ] Step 7: build check + 全量测试
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 8: Commit `refactor(build): inline state-write and remove template (D2)`

---

### Task Pack 4: 死模板 `trust-boundary` 内联并删除（D2 part c）

**Issue:** Small Issue 4
**Goal behavior:** `<!-- BEGIN: trust-boundary [variant=worker] -->` 锚点从 orchestrate-execution/SKILL.md L187 单一 active site 中消除；模板源 + resolver 删除。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-execution/SKILL.md`（L187 附近）
- Delete: `plugin/build/templates/trust-boundary.md.tmpl`
- Delete: `plugin/build/resolvers/trust-boundary.sh`

**Read first:**
- 设计文档 §4.2 决策 2 + §5.4
- `plugin/build/templates/trust-boundary.md.tmpl`（注意 variant=worker 是唯一使用的变体）
- `plugin/build/resolvers/trust-boundary.sh`
- `plugin/skills/orchestrate-execution/SKILL.md` L180-200

**Contract anchors:**
- Owner: Issue 001
- Provider: orchestrate-execution/SKILL.md（content inline）
- Consumer: Coordinator
- Verification: build --check 不触及 trust-boundary

**Acceptance criteria:**
- [ ] `grep -rn 'BEGIN: trust-boundary\|END: trust-boundary' plugin/` 返回空
- [ ] `test ! -f plugin/build/templates/trust-boundary.md.tmpl`
- [ ] `test ! -f plugin/build/resolvers/trust-boundary.sh`
- [ ] orchestrate-execution/SKILL.md L180-200 含原 trust-boundary [variant=worker] 展开后内容
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `grep -rn 'BEGIN: trust-boundary\|END: trust-boundary' plugin/` → Expected: empty
- `test ! -f plugin/build/templates/trust-boundary.md.tmpl && echo OK` → Expected: OK
- `test ! -f plugin/build/resolvers/trust-boundary.sh && echo OK` → Expected: OK
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(build): inline trust-boundary worker variant and remove template (D2)"
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** forbidden-shortcuts / state-write（独立 Pack）

#### Implementation tasks
- [ ] Step 1: Read 模板 + resolver
  - Run: `cat plugin/build/templates/trust-boundary.md.tmpl`
  - Run: `cat plugin/build/resolvers/trust-boundary.sh` → 关键：确认 `[variant=worker]` 展开后的具体文本
- [ ] Step 2: Baseline build check
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- [ ] Step 3: Read orchestrate-execution/SKILL.md L180-205 拿到完整锚点块
- [ ] Step 4: Edit 替换 BEGIN-END 整段为 worker variant 展开后的纯内容
- [ ] Step 5: 删除源
  - Run: `rm plugin/build/templates/trust-boundary.md.tmpl plugin/build/resolvers/trust-boundary.sh`
- [ ] Step 6: 验证清零
  - Run: `grep -rn 'BEGIN: trust-boundary\|END: trust-boundary' plugin/` → Expected: empty
- [ ] Step 7: build check + 全量测试
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 8: Commit `refactor(build): inline trust-boundary worker variant and remove template (D2)`

---

### Task Pack 5: 孤儿 + 副本 reference 与 verify-maturity §6.11 清扫（D2 part d）

**Issue:** Small Issue 5
**Goal behavior:** 删除 3 个 multi-pr handbook 孤儿 + 2 个 learnings reference（内容折回 execution/SKILL.md）+ path-a-re-review.md + execution 一侧 route-extensions/ 副本目录；同步重写 verify-maturity.sh §6.11 6 行检查；清理 architecture-draft.md 中两处 execution-worker-handbook 描述。

**Owned files / responsibilities:**
- Delete: `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md`
- Delete: `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md`
- Delete: `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md`
- Delete: `plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md`（内容折回 SKILL.md）
- Delete: `plugin/skills/orchestrate-execution/references/learnings-trust-gate.md`（内容折回 SKILL.md）
- Delete: `plugin/skills/orchestrate-execution/references/path-a-re-review.md`
- Delete: `plugin/skills/orchestrate-execution/references/route-extensions/` 整个目录（4 个文件）
- Modify: `plugin/skills/orchestrate-execution/SKILL.md`（在 Worker 返回处理段附加原 learnings-confidence-audit + learnings-trust-gate 的合并子章节，标题为 `## Learnings 信任门` 或同义）
- Modify: `plugin/scripts/verify-maturity.sh` L379-394（删除 6 行 handbook 检查，替换为新检查：merge-brief-template.md 存在 + 4 个 merge-* reference 含 Self-Read Protocol）
- Modify: `plugin/architecture-draft.md` L286 / L299（删除 "execution-worker-handbook（Worker 自读）" 裸提及；保留 L53 / L338 等待 Issue 003 修）

**Read first:**
- 设计文档 §4.2 决策 2（孤儿 reference 文件清理）
- 设计文档 Alignment Review I5（verify-maturity §6.11 6 行清理）
- `plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md` 全文（确认它已被 merge-brief 覆盖）
- `plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md`（60 行待折回）
- `plugin/skills/orchestrate-execution/references/learnings-trust-gate.md`（21 行待折回）
- `plugin/scripts/verify-maturity.sh` L379-394 全段（要替换的 6 行检查）
- `plugin/architecture-draft.md` L280-310（L286/L299 上下文）

**Contract anchors:**
- Owner: Issue 001
- Provider: orchestrate-execution/SKILL.md（接收 learnings 内容）+ verify-maturity.sh（新检查）
- Consumer: multi-pr-merge 角色不再 Read 这 3 个 handbook（merge-brief 是唯一权威源，design D23 cascade 已明示）
- Verification: 文件物理消失 + grep 在 plugin/skills/ 内无孤儿引用

**Acceptance criteria:**
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md`
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md`
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md`
- [ ] `test ! -f plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md`
- [ ] `test ! -f plugin/skills/orchestrate-execution/references/learnings-trust-gate.md`
- [ ] `test ! -f plugin/skills/orchestrate-execution/references/path-a-re-review.md`
- [ ] `test ! -d plugin/skills/orchestrate-execution/references/route-extensions/`
- [ ] orchestrate-execution/SKILL.md 含 `## Learnings 信任门` 或同义子章节（grep 关键短语：`Confidence 分层处理` 或 `投毒检测` 等原内容代表性短语）
- [ ] `plugin/scripts/verify-maturity.sh` 不再含三处 `multi-pr-explorer-handbook.md` / `multi-pr-conflict-worker-handbook.md` / `multi-pr-integration-review-handbook.md` 字符串
- [ ] `plugin/scripts/verify-maturity.sh` 新含 `merge-brief-template.md` 存在性 + 4 个 merge-* reference 内容检查（grep 验证）
- [ ] `plugin/architecture-draft.md` L286 / L299 不再含 `execution-worker-handbook（Worker 自读）` 短语（其他位置允许残留，归 Issue 003）
- [ ] `bash plugin/scripts/verify-maturity.sh` 整体 pass
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `ls plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-*.md 2>/dev/null | wc -l` → Expected: 0
- `ls plugin/skills/orchestrate-execution/references/learnings-*.md 2>/dev/null | wc -l` → Expected: 0
- `test ! -f plugin/skills/orchestrate-execution/references/path-a-re-review.md && echo OK` → Expected: OK
- `test ! -d plugin/skills/orchestrate-execution/references/route-extensions/ && echo OK` → Expected: OK
- `grep -c 'multi-pr-explorer-handbook\|multi-pr-conflict-worker-handbook\|multi-pr-integration-review-handbook' plugin/scripts/verify-maturity.sh` → Expected: 0
- `grep -c 'execution-worker-handbook（Worker 自读）' plugin/architecture-draft.md` → Expected: 0
- `grep -c 'Confidence 分层处理\|投毒检测\|信任门' plugin/skills/orchestrate-execution/SKILL.md` → Expected: ≥ 1
- `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(skills): delete orphan handbooks + fold learnings into SKILL + clean verify-maturity §6.11 (D2)"
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** None
**Out of scope:** 
- D9 hooks（Pack 7）
- D10 workflow 一侧的 route-extensions/（Pack 6）
- execution-worker-handbook 其余 6 处引用修正（Issue 003 D21）

#### Implementation tasks
- [ ] Step 1: Read 5 个将删 reference 全文，记录关键内容
  - Run: `cat plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md` → 记录 60 行
  - Run: `cat plugin/skills/orchestrate-execution/references/learnings-trust-gate.md` → 记录 21 行
  - Run: `head plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md` → 确认内容已被 merge-brief 覆盖
- [ ] Step 2: Read orchestrate-execution/SKILL.md 找 Worker 返回处理段（grep `Worker 返回\|Plan Implementation Review\|Step 9`）
  - Run: `grep -n 'Worker 返回\|Plan Implementation Review' plugin/skills/orchestrate-execution/SKILL.md` → 记录行号
- [ ] Step 3: Edit orchestrate-execution/SKILL.md 在 Worker 返回处理段后插入 `## Learnings 信任门` 子章节，合并 learnings-confidence-audit + learnings-trust-gate 内容（保留所有原段落 + 表格 + 列表）
- [ ] Step 4: 删除 5 个 reference 文件 + execution route-extensions 目录
  - Run: `rm plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md`
  - Run: `rm plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md`
  - Run: `rm plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md`
  - Run: `rm plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md`
  - Run: `rm plugin/skills/orchestrate-execution/references/learnings-trust-gate.md`
  - Run: `rm plugin/skills/orchestrate-execution/references/path-a-re-review.md`
  - Run: `rm -r plugin/skills/orchestrate-execution/references/route-extensions/`
- [ ] Step 5: Edit verify-maturity.sh L379-394 — 删除 6 行 multi-pr handbook 检查；新增 4 行检查：
  - `check "6.11: merge-brief-template exists" test -f "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md"`
  - `check "6.11: merge-preparation has Self-Read Protocol" grep -q 'Self-Read Protocol' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-preparation.md"`
  - `check "6.11: merge-conflict-discovery has Self-Read Protocol" grep -q 'Self-Read Protocol' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-conflict-discovery.md"`
  - `check "6.11: merge-integration-review has Self-Read Protocol" grep -q 'Self-Read Protocol' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md"`
- [ ] Step 6: Read architecture-draft.md L280-310
  - Run: `sed -n '280,310p' plugin/architecture-draft.md` 实际用 Read tool 读
- [ ] Step 7: Edit architecture-draft.md L286 — 在 `execution-completion / execution-release-gate / execution-repair-truncation / path-a-re-review / learnings-confidence-audit / learnings-trust-gate / route-extensions/` 这串列表中删除已删的 4 项：`path-a-re-review` + `learnings-confidence-audit` + `learnings-trust-gate` + `route-extensions/`；删除 `execution-worker-handbook（Worker 自读） / `（含尾部斜杠分隔）
- [ ] Step 8: Edit architecture-draft.md L299 — 删除 `execution-worker-handbook.md` 提及（在 `execution-worker-dispatch.md / execution-review-dispatch.md / execution-worker-handbook.md` 这种串列表中删除该项）
- [ ] Step 9: 跑 verify-maturity 确认新检查 pass
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- [ ] Step 10: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 11: Commit `refactor(skills): delete orphan handbooks + fold learnings into SKILL + clean verify-maturity §6.11 (D2)`

---

### Task Pack 6: Route 4-7 折叠为 Route 1 + flags（D10）

**Issue:** Small Issue 6
**Goal behavior:** workflow-state route enum 从 8 值收敛为 4 值；新增 phase_skip + commit_format_override 字段；orchestrate-workflow/SKILL.md Step 1 表删除 Route 4-7 行，改为统一 Route 1 + Variant Table；删除 workflow 一侧 route-extensions/ 目录。Entry Gate 仍能识别 hotfix/quickfix/spike/maintenance 关键词，但路由到 Route 1 + 对应 flags。

**Owned files / responsibilities:**
- Modify: `plugin/state-schema/workflow-state-v1.json`（`route` enum 缩 + 新增 `phase_skip` / `commit_format_override`）
- Modify: `plugin/scripts/state.sh`（init 子命令初始化新字段）
- Modify: `plugin/skills/orchestrate-workflow/SKILL.md`（Step 1 表 Route 4-7 删除 + 新增 "Route 1 Variant Table" 段）
- Delete: `plugin/skills/orchestrate-workflow/references/route-extensions/` 整个目录（4 个文件）

**Read first:**
- 设计文档 §4.2 决策 10
- 设计文档 §5.2 workflow-state-v1.json schema 变化
- `plugin/state-schema/workflow-state-v1.json` 当前 enum 值（L18）
- `plugin/skills/orchestrate-workflow/SKILL.md` Step 1 表（L58-66）
- `plugin/skills/orchestrate-workflow/references/route-extensions/route-4-hotfix.md` 全文
- `plugin/skills/orchestrate-workflow/references/route-extensions/route-5-quickfix.md` 全文
- `plugin/skills/orchestrate-workflow/references/route-extensions/route-6-spike.md` 全文
- `plugin/skills/orchestrate-workflow/references/route-extensions/route-7-maintenance.md` 全文
- `plugin/scripts/state.sh` init 子命令实现（grep `init()` 找）

**Contract anchors:**
- Owner: Issue 001
- Provider: workflow-state-v1.json schema + state.sh init + orchestrate-workflow/SKILL.md
- Consumer: 所有 grep `route` 的 hook 和 SKILL.md（决策 10 中提到 `direct-repair` / `formal` / `bug-investigation` / `multi-pr-merge` 字符串保留——其他都删）
- Verification: schema enum 长度 = 4 + state.sh init 生成的 JSON 含新字段 + workflow/SKILL.md 不含 Route 4-7

**Acceptance criteria:**
- [ ] `jq '.properties.route.enum | length' plugin/state-schema/workflow-state-v1.json` = 4
- [ ] `jq -r '.properties.route.enum | sort | join(",")' plugin/state-schema/workflow-state-v1.json` 输出 `bug-investigation,direct-repair,formal,multi-pr-merge`
- [ ] `jq '.properties.phase_skip.type' plugin/state-schema/workflow-state-v1.json` 输出 `"array"`
- [ ] `jq -r '.properties.commit_format_override.type | if type == "array" then join("|") else . end' plugin/state-schema/workflow-state-v1.json` 含 `string` 和 `null`（schema 允许 nullable）
- [ ] `test ! -d plugin/skills/orchestrate-workflow/references/route-extensions/`
- [ ] orchestrate-workflow/SKILL.md 含 "Route 1 Variant Table" 字符串（grep）
- [ ] `grep -cE '^\| \*\*Route [4-7]:' plugin/skills/orchestrate-workflow/SKILL.md` = 0
- [ ] `grep -c 'route-extensions/route-' plugin/skills/orchestrate-workflow/SKILL.md` = 0
- [ ] orchestrate-workflow/SKILL.md Step 1 仍含 hotfix/quickfix/spike/maintenance 关键词，路由到 Route 1（grep 验证）
- [ ] `bash plugin/scripts/state.sh init --run-id pack6-test --slug test --route formal` 成功生成 workflow-state JSON 且含 `phase_skip: []`, `commit_format_override: null`
- [ ] state-schema JSON validity: `python3 -m json.tool plugin/state-schema/workflow-state-v1.json >/dev/null`
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `jq '.properties.route.enum' plugin/state-schema/workflow-state-v1.json` → Expected: 4 values, no hotfix/quickfix/spike/maintenance
- `jq '.properties.phase_skip' plugin/state-schema/workflow-state-v1.json` → Expected: array type defined
- `jq '.properties.commit_format_override' plugin/state-schema/workflow-state-v1.json` → Expected: nullable string
- `test ! -d plugin/skills/orchestrate-workflow/references/route-extensions/ && echo OK` → Expected: OK
- `grep -c '^\| \*\*Route [4-7]:' plugin/skills/orchestrate-workflow/SKILL.md` → Expected: 0
- `grep -c 'Route 1 Variant Table' plugin/skills/orchestrate-workflow/SKILL.md` → Expected: ≥ 1
- `bash plugin/scripts/state.sh init --run-id pack6-test --slug pack6-test --route formal && jq '.phase_skip,.commit_format_override' .claude/multi-model-workflow/workflow-state-pack6-test.json` → Expected: `[]` and `null`
- `python3 -m json.tool plugin/state-schema/workflow-state-v1.json >/dev/null` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(routes): collapse routes 4-7 into Route 1 + phase_skip flags (D10)"
**Risk flags:** high-risk + migration
**发布风险:** Route 折叠破坏 hotfix 实际路径（design §6.1 风险 2）—— 缓解：折叠前并行对照原 4 个 route-extensions 文件全文，把每个"特殊行为"逐项归入 SKILL.md Route 1 Variant Table
**AFK / HITL:** AFK（实现）+ HITL（Plan Impl Review 时用户确认 hotfix 在 Route 1 + flags 下能完整跑通）
**Dependencies:** None（与 Pack 2/3/4/5/7/8 独立；与 Pack 9 独立——Pack 9 不动 workflow SKILL.md 的 Route 表，只动 SKILL.md 中的 review-dispatch 锚点）
**Out of scope:** orchestrate-execution/references/route-extensions/（已由 Pack 5 删除）

#### Implementation tasks
- [ ] Step 1: Read 4 个 route-extensions 文件全文，提取每个 route 的特殊行为列表
  - Run: `wc -l plugin/skills/orchestrate-workflow/references/route-extensions/*.md`
  - 实际 Read 每个文件
  - 输出：4 个 route × 各特殊行为（如 hotfix: phase_skip=[discovery,plan-writing,final-review] + budget_status=unlimited + commit_format_override="hotfix-unreviewed" + pending_post_push_reviews 保留）
- [ ] Step 2: Read state-schema/workflow-state-v1.json 完整内容（确认 properties 段结构 + required 段）
- [ ] Step 3: Edit `plugin/state-schema/workflow-state-v1.json`
  - 修改 L18 `route` enum：从 8 值 `["formal","direct-repair","multi-pr-merge","bug-investigation","hotfix","quickfix","spike","maintenance"]` 改为 4 值 `["formal","direct-repair","multi-pr-merge","bug-investigation"]`
  - 在 properties 段新增 `phase_skip`：`{ "type": "array", "items": { "type": "string", "enum": ["discovery","plan-writing","execution","final-review","closed","bug-investigation","direct-repair","multi-pr-merge"] }, "default": [] }`（phase enum 与现有 cursor.phase 保持一致——先 Read 确认 cursor.phase 当前枚举值）
  - 在 properties 段新增 `commit_format_override`：`{ "type": ["string","null"], "default": null }`
  - required 段不动（这两个字段都是可选 + 有 default）
- [ ] Step 4: 验证 schema 合法性
  - Run: `python3 -m json.tool plugin/state-schema/workflow-state-v1.json >/dev/null` → Expected: exit 0
- [ ] Step 5: Read `plugin/scripts/state.sh` 中 init 子命令实现（grep `cmd_init\|case.*init` 找入口）
  - Run: `grep -n 'cmd_init\|"phase_skip"\|"commit_format_override"' plugin/scripts/state.sh`
- [ ] Step 6: Edit state.sh init 子命令 — 在生成 workflow-state JSON 的 jq pipeline 中加入 `phase_skip: []` 和 `commit_format_override: null` 字段
- [ ] Step 7: 手动验 state.sh init
  - Run: `bash plugin/scripts/state.sh init --run-id pack6-init-test --slug pack6 --route formal`
  - Run: `jq '.phase_skip,.commit_format_override' .claude/multi-model-workflow/workflow-state-pack6-init-test.json` → Expected: `[]` `null`
  - Run: `rm -f .claude/multi-model-workflow/workflow-state-pack6-init-test.json`（清理）
- [ ] Step 8: 验证 state.sh 不接受已删 route 值
  - Run: `bash plugin/scripts/state.sh init --run-id pack6-bad --slug pack6 --route hotfix 2>&1 || echo "Correctly rejected"` → Expected: 接受或拒绝看 state.sh 是否做 enum 校验。如做了校验，应输出 "Correctly rejected"；如未做（依赖 schema 校验），允许通过但 schema validation 应报错
- [ ] Step 9: Edit `plugin/skills/orchestrate-workflow/SKILL.md` L58-66 表
  - 删除 L63-66 四行（Route 4/5/6/7）
  - 在 Step 1 表后或 Step 2 后插入新段 "## Route 1 Variant Table"（≈80-120 行）
  - 表头：`| Variant 关键词 | phase_skip | budget_status | commit_format_override | 备注 |`
  - 4 行：hotfix / quickfix / spike / maintenance，每行填具体 flag 值（值来源于 Step 1 提取的列表）
  - 在表后写一段说明文字：Entry Gate 识别这 4 个关键词 → Route 1 + 对应 flags；保留 pending_post_push_reviews 机制不动
- [ ] Step 10: 删除 workflow 一侧 route-extensions 目录
  - Run: `rm -r plugin/skills/orchestrate-workflow/references/route-extensions/`
- [ ] Step 11: 验证 grep 清扫
  - Run: `grep -rn 'route-extensions/route-' plugin/` → Expected: 仅设计文档 / 审计 / git history（不在 plugin/skills/ 或 plugin/build/ 或 plugin/hooks/ 内）
- [ ] Step 12: 跑 verify-maturity + 全量测试
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS（如有 route-extensions 引用检查需同步更新）
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 13: Commit `refactor(routes): collapse routes 4-7 into Route 1 + phase_skip flags (D10)`

---

### Task Pack 7: Hook 降级 / 删除（D9）

**Issue:** Small Issue 7
**Goal behavior:** 删除 guard-plan-doc-patch.sh + hooks.json 对应 entry；validate-plan-dispatch.sh Step 6 Manifest 缺失从 exit 2 改为 WARN，Step 8 Path A 检查整段删除；gate-codex-review.sh 删除 path-a-re-review + targeted-re-review 两个分支；保留 validate-multi-pr-dispatch.sh (b)(d) exit 2 不动。

**Owned files / responsibilities:**
- Delete: `plugin/hooks/guard-plan-doc-patch.sh`
- Modify: `plugin/hooks/hooks.json`（删除 L80-83 PreToolUse/Write 中 guard-plan-doc-patch entry）
- Modify: `plugin/hooks/validate-plan-dispatch.sh`（Step 6 改 WARN + Step 8 整段删）
- Modify: `plugin/hooks/gate-codex-review.sh`（删 path-a-re-review L54-65 + targeted-re-review L66-75 两个 case 分支）

**Read first:**
- 设计文档 §4.2 决策 9
- 设计文档 §5.6 Hook 行为契约变化
- 设计文档 Alignment Review C5（保持 (b)(d) exit 2）
- `plugin/hooks/guard-plan-doc-patch.sh` 当前全文（122 行）
- `plugin/hooks/hooks.json` L73-85（Write matcher）
- `plugin/hooks/validate-plan-dispatch.sh` Step 6（L74-103）+ Step 8（L124-130）
- `plugin/hooks/gate-codex-review.sh` 当前全文（91 行）

**Contract anchors:**
- Owner: Issue 001
- Provider: 3 个 hook 脚本 + hooks.json
- Consumer: Claude Code hook 触发系统（PreToolUse/Write + PreToolUse/Bash for codex-companion）
- Verification: Hook 数 = 12（13-1）+ hooks.json JSON 合法 + 各 hook 改后行为符合契约表

**Acceptance criteria:**
- [ ] `test ! -f plugin/hooks/guard-plan-doc-patch.sh`
- [ ] `grep -c 'guard-plan-doc-patch' plugin/hooks/hooks.json` = 0
- [ ] `python3 -m json.tool plugin/hooks/hooks.json >/dev/null` 成功
- [ ] `plugin/hooks/validate-plan-dispatch.sh` Step 6 Manifest 缺失输出含 `WARN` 字符串
- [ ] `plugin/hooks/validate-plan-dispatch.sh` Step 6 Manifest 缺失退出码非 2（应是 0）
- [ ] `plugin/hooks/validate-plan-dispatch.sh` 不再含 `# Step 8: Path A escalation` 注释段
- [ ] `grep -c 'path-a-re-review\|targeted-re-review' plugin/hooks/gate-codex-review.sh` = 0
- [ ] `grep -c 'baseline\|review_intent' plugin/hooks/gate-codex-review.sh` ≥ 1（确认 baseline review 仍可用）
- [ ] `grep -c 'exit 2' plugin/hooks/validate-multi-pr-dispatch.sh` ≥ 4（(a)(b)(c)(d) 共 4 处至少保留——baseline 实际数）
- [ ] `ls plugin/hooks/*.sh | wc -l` = 12（baseline 13 - 1）
- [ ] Hook test suite 全绿（`plugin/hooks/tests/*.sh`）
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `test ! -f plugin/hooks/guard-plan-doc-patch.sh && echo OK` → Expected: OK
- `grep -c 'guard-plan-doc-patch' plugin/hooks/hooks.json` → Expected: 0
- `python3 -m json.tool plugin/hooks/hooks.json >/dev/null && echo OK` → Expected: OK
- `grep -n 'Step 6\|Step 8' plugin/hooks/validate-plan-dispatch.sh` → Expected: Step 6 存在；Step 8 不存在
- `grep -c 'path-a-re-review\|targeted-re-review' plugin/hooks/gate-codex-review.sh` → Expected: 0
- `ls plugin/hooks/*.sh | wc -l` → Expected: 12
- `bash plugin/hooks/tests/test_validate_plan_dispatch.sh` → Expected: PASS（若存在；run-all-tests 会包含）
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(hooks): downgrade manifest check to WARN + remove path-a + delete guard-plan-doc-patch (D9)"
**Risk flags:** production-risk + high-risk
**发布风险:** Hook 删除 / 降级影响 production guardrail —— 缓解：Pack 内逐项验证保留 hook 行为不变 + hook test 套件 + Plan Implementation Review 时 grep 验证保留 hook 不变
**AFK / HITL:** AFK
**Dependencies:** None（与 Pack 5 独立——Pack 5 已删 path-a-re-review.md 文件，Pack 7 删的是 hook 中的 branch；hooks.json 改动与 Pack 5 互不冲突）
**Out of scope:** 
- state.sh path-a-escalation 子命令（Issue 002 D3）
- workflow-state.path_a_escalation 字段（Issue 002）
- SKILL.md / reference 中 path-a-escalation 使用引用（Issue 002）

#### Implementation tasks
- [ ] Step 1: Read 3 个 hook 脚本完整内容做 baseline
  - Run: `wc -l plugin/hooks/guard-plan-doc-patch.sh plugin/hooks/validate-plan-dispatch.sh plugin/hooks/gate-codex-review.sh`
  - Read validate-plan-dispatch.sh L74-103 (Step 6) + L124-130 (Step 8) 区段
  - Read gate-codex-review.sh 全文（91 行）
- [ ] Step 2: Read 当前 hooks.json L73-85（Write matcher）
- [ ] Step 3: 跑 hook test baseline
  - Run: `bash plugin/scripts/run-all-tests.sh 2>&1 | tail -20` → 记录通过的 hook test 数
- [ ] Step 4: Edit `plugin/hooks/validate-plan-dispatch.sh` Step 6 — L83-91 的 `if ! grep -q '## Pack Execution Manifest' ...; then echo BLOCKED ... exit 2; fi` 改为：
  ```
  if ! grep -q '## Pack Execution Manifest' "$PLAN_PATH"; then
    echo "[multi-model-workflow] WARN: plan $PLAN_ID at $PLAN_PATH missing '## Pack Execution Manifest' — Worker may work from plan body. (D9 降级)" >&2
    # 不 exit 2，继续后续 step
  fi
  ```
- [ ] Step 5: Edit validate-plan-dispatch.sh — 删除 L124-130 整段 `# Step 8: Path A escalation` + `if [[ "$REVIEW_INTENT" == "path-a-re-review" ]]; then ... exit 2; fi` 块
- [ ] Step 6: Edit `plugin/hooks/gate-codex-review.sh` — 找到 `case ... in` 块，删除 `path-a-re-review)` 和 `targeted-re-review)` 两个 case 分支（含其内部 `exit 2` 检查）；保留 `baseline)` 和 default 分支
- [ ] Step 7: 删除 guard-plan-doc-patch.sh
  - Run: `rm plugin/hooks/guard-plan-doc-patch.sh`
- [ ] Step 8: Edit `plugin/hooks/hooks.json` — 删除 L80-83 中 PreToolUse/Write/guard-plan-doc-patch entry（保留 guard-doc-edit.sh entry）
- [ ] Step 9: 验证 hooks.json JSON 合法
  - Run: `python3 -m json.tool plugin/hooks/hooks.json >/dev/null` → Expected: exit 0
- [ ] Step 10: 验证 hook 数
  - Run: `ls plugin/hooks/*.sh | wc -l` → Expected: 12
- [ ] Step 11: 跑 hook test suite
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS（必要时新增/调整 test_validate_plan_dispatch 验证 WARN 行为）
- [ ] Step 12: Commit `refactor(hooks): downgrade manifest check to WARN + remove path-a + delete guard-plan-doc-patch (D9)`

---

### Task Pack 8: Scripts 合并 — dispatch-review.sh + dispatch-route-worker.sh（D8）

**Issue:** Small Issue 8
**Goal behavior:** 新建 2 个合并脚本，每个含 validate + record 子命令；旧 4 个脚本改为 shim 仅做 exec 转发；所有 producer（SKILL.md / reference / build template / hook）从旧调用形式（`bash plugin/scripts/<old>.sh <args>`）迁移到新形式（`bash plugin/scripts/dispatch-<x>.sh <validate|record> <args>`）。

**Owned files / responsibilities:**
- Create: `plugin/scripts/dispatch-review.sh`（含 validate + record 子命令）
- Create: `plugin/scripts/dispatch-route-worker.sh`（同模式）
- Create: `plugin/scripts/tests/test_dispatch_review_shim.sh`（验证 shim 转发等价）
- Modify: `plugin/scripts/record-review-dispatch.sh` → shim
- Modify: `plugin/scripts/validate-review-dispatch.sh` → shim
- Modify: `plugin/scripts/record-route-worker-dispatch.sh` → shim
- Modify: `plugin/scripts/validate-route-worker-dispatch.sh` → shim
- Modify: 所有 producer 文件（grep 找全）— `plugin/skills/*/SKILL.md` + `plugin/skills/*/references/*.md` + `plugin/build/templates/*.md.tmpl` + `plugin/hooks/*.sh`

**Read first:**
- 设计文档 §4.2 决策 8 + §5.8 Scripts CLI 合同变化
- `plugin/scripts/record-review-dispatch.sh` 全文（76 行）
- `plugin/scripts/validate-review-dispatch.sh` 全文（213 行）
- `plugin/scripts/record-route-worker-dispatch.sh` 全文（48 行）
- `plugin/scripts/validate-route-worker-dispatch.sh` 全文（90 行）
- 用 grep 找 producer：
  - `grep -rln 'record-review-dispatch\.sh\|validate-review-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/`
  - `grep -rln 'record-route-worker-dispatch\.sh\|validate-route-worker-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/`

**Contract anchors:**
- Owner: Issue 001
- Provider: 2 个新合并脚本 + 4 个 shim
- Consumer: 所有 producer 文件（SKILL.md / reference / build template / hook）
- Verification: grep 验证 producer 全部使用新调用形式 + shim 转发等价 + 全量测试通过

**Acceptance criteria:**
- [ ] `test -x plugin/scripts/dispatch-review.sh`
- [ ] `test -x plugin/scripts/dispatch-route-worker.sh`
- [ ] `bash plugin/scripts/dispatch-review.sh --help 2>&1 | grep -c 'validate\|record'` ≥ 2
- [ ] `bash plugin/scripts/dispatch-route-worker.sh --help 2>&1 | grep -c 'validate\|record'` ≥ 2
- [ ] 4 个旧脚本仍存在且每个 ≤ 10 行（shim 化）
  - `wc -l plugin/scripts/record-review-dispatch.sh plugin/scripts/validate-review-dispatch.sh plugin/scripts/record-route-worker-dispatch.sh plugin/scripts/validate-route-worker-dispatch.sh`
- [ ] 旧脚本仍可调用且转发等价（test_dispatch_review_shim.sh 通过）
- [ ] `grep -rln 'validate-review-dispatch\.sh\|record-review-dispatch\.sh\|validate-route-worker-dispatch\.sh\|record-route-worker-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/ | wc -l` = 0（所有 producer 已迁移）
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿（含新增 test_dispatch_review_shim.sh）

**Verification commands:**
- `test -x plugin/scripts/dispatch-review.sh && echo OK` → Expected: OK
- `test -x plugin/scripts/dispatch-route-worker.sh && echo OK` → Expected: OK
- `wc -l plugin/scripts/record-review-dispatch.sh` → Expected: ≤ 10
- `wc -l plugin/scripts/validate-review-dispatch.sh` → Expected: ≤ 10
- `wc -l plugin/scripts/record-route-worker-dispatch.sh` → Expected: ≤ 10
- `wc -l plugin/scripts/validate-route-worker-dispatch.sh` → Expected: ≤ 10
- `grep -rln 'validate-review-dispatch\.sh\|record-review-dispatch\.sh\|validate-route-worker-dispatch\.sh\|record-route-worker-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/ 2>/dev/null | wc -l` → Expected: 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(scripts): merge review-dispatch + route-worker-dispatch into dispatch-<x>.sh with shim (D8)"
**Risk flags:** runtime + migration
**发布风险:** Producer 漏迁移导致 shim 期被迫延长 —— 缓解：Pack 内 grep 全 producer 验证；shim 期持续到 Issue 003 之后清理（Open Item）
**AFK / HITL:** AFK
**Dependencies:** None（与其他 Pack 独立——Pack 9 D1 抽取后会修改 SKILL.md 内的 review-dispatch 锚点引用方式，但不会改这些脚本调用本身；Pack 8 完成后 producer 全用新形式，Pack 9 修改时只动锚点 → Read 指令转换）
**Out of scope:** Shim 删除（deferred 到 Issue 003 后清理阶段）

#### Implementation tasks
- [ ] Step 1: 找全 producer
  - Run: `grep -rln 'validate-review-dispatch\.sh\|record-review-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/` → 记录产出列表
  - Run: `grep -rln 'validate-route-worker-dispatch\.sh\|record-route-worker-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/` → 记录产出列表
- [ ] Step 2: Read 4 个旧脚本全文，分析参数 + 输出格式
  - Read record-review-dispatch.sh / validate-review-dispatch.sh / record-route-worker-dispatch.sh / validate-route-worker-dispatch.sh
- [ ] Step 3: 写 failing 测试 — `plugin/scripts/tests/test_dispatch_review_shim.sh`
  - Behavior：调用 `bash plugin/scripts/validate-review-dispatch.sh <test args>` 和 `bash plugin/scripts/dispatch-review.sh validate <test args>`，两者输出应完全相同；同理 record 子命令
  - 测试使用 fixture 在 `/tmp/dispatch-shim-test-<run-id>/` 隔离
  - Key assertions：stdout / stderr / exit code 三方对齐
- [ ] Step 4: 跑测试确认失败
  - Run: `bash plugin/scripts/tests/test_dispatch_review_shim.sh` → Expected: FAIL because dispatch-review.sh does not exist
- [ ] Step 5: 写 `plugin/scripts/dispatch-review.sh`
  - 入口：`case "$1" in validate) shift; <validate logic>;; record) shift; <record logic>;; *) usage;; esac`
  - 选择实现策略：
    - Option A：把 validate-review-dispatch.sh + record-review-dispatch.sh 的核心逻辑 inline 进 dispatch-review.sh 的两个子命令块（旧脚本变 shim 直接 exec 转发）
    - Option B：dispatch-review.sh 内 `case` 分支转发到原脚本 — 但这会让 shim 反向调用，造成循环。**用 Option A**
  - 加 `--help` / `-h` 输出
  - 加 `chmod +x`
- [ ] Step 6: 写 `plugin/scripts/dispatch-route-worker.sh` — 同 Option A 模式
- [ ] Step 7: 改写 4 个旧脚本为 shim
  - record-review-dispatch.sh：`#!/usr/bin/env bash\nexec "$(dirname "$0")/dispatch-review.sh" record "$@"`
  - validate-review-dispatch.sh：`exec ".../dispatch-review.sh" validate "$@"`
  - record-route-worker-dispatch.sh / validate-route-worker-dispatch.sh：同模式
  - 每个文件 ≤ 10 行（含 shebang 和注释）
- [ ] Step 8: 跑 shim 测试
  - Run: `bash plugin/scripts/tests/test_dispatch_review_shim.sh` → Expected: PASS
- [ ] Step 9: 迁移所有 producer
  - 对 Step 1 grep 结果中每个文件，Edit 替换：
    - `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh"` → `bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-review.sh" validate`
    - `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-dispatch.sh"` → `bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-review.sh" record`
    - 同模式对 route-worker
  - 注意：`plugin/build/templates/review-dispatch.md.tmpl` 内部对脚本的引用也要改（该模板 Pack 9 会被 canonical 化但本 Pack 仍可独立修改）
- [ ] Step 10: 验证 producer 清零
  - Run: `grep -rln 'validate-review-dispatch\.sh\|record-review-dispatch\.sh\|validate-route-worker-dispatch\.sh\|record-route-worker-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/ | wc -l` → Expected: 0
- [ ] Step 11: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 12: Commit `refactor(scripts): merge review-dispatch + route-worker-dispatch into dispatch-<x>.sh with shim (D8)`

---

### Task Pack 9: Canonical reference 抽取（D1）

**Issue:** Small Issue 9
**Goal behavior:** 3 个高频 inject 锚点（review-dispatch / repair-routing / disposition-table）从 build template 注入模式改为 plugin-rooted canonical reference 模式。canonical 内容从 `.tmpl` 抽取时**排除** `[variant=targeted-re-review]` 子模块（advisor approach）—— canonical 文件从第一天就干净，不含 targeted-re-review 残留。所有原 inject 位置改为 plugin-rooted Read 指令（禁相对路径）。`codex-review/SKILL.md` 中 `[variant=content-only]` 锚点**本轮不动**（§10 第 15 条）。

**Owned files / responsibilities:**
- Create: `plugin/skills/_shared/` 目录
- Create: `plugin/skills/_shared/review-dispatch.md`（≈ 50-80 行，含路标 blockquote）
- Create: `plugin/skills/_shared/repair-routing.md`（≈ 30-45 行）
- Create: `plugin/skills/_shared/disposition-table.md`（≈ 30-50 行）
- Modify: 12 处 `<!-- BEGIN: review-dispatch -->` 锚点位置（除 codex-review/SKILL.md 的 content-only 锚点）— 全部改为 plugin-rooted Read 指令
- Modify: 9 处 `<!-- BEGIN: repair-routing -->` 锚点位置
- Modify: 6 处 `<!-- BEGIN: disposition-table -->` 锚点位置
- Modify: `plugin/build/build.sh`（跳过 3 个 resolver；不删 .tmpl 源）
- Modify: `plugin/build/tests/test_review_evidence_table.sh`（改扫 canonical 而非 BEGIN 锚点）
- Modify: `plugin/scripts/verify-maturity.sh` L58-59（删旧 anchor count 检查 + 新增 4 条 canonical 检查）
- Modify: `plugin/architecture-draft.md`（build template anchor 表更新；review-dispatch.content-only 留作下轮说明）

**Read first:**
- 设计文档 §4.2 决策 1
- 设计文档 §4.2 决策 1"与决策 13 的执行顺序"段（解释为何采用"抽取时归一化"approach）
- 设计文档 §5.4 + §5.5
- `plugin/build/templates/review-dispatch.md.tmpl` 全文 — 识别 `[variant=baseline]` 主路径段 vs `[variant=targeted-re-review]` 子模块
- `plugin/build/resolvers/review-dispatch.sh`（理解 resolver 如何处理 variant）
- `plugin/build/templates/repair-routing.md.tmpl` 全文
- `plugin/build/templates/disposition-table.md.tmpl` 全文
- 用 grep 找全 27 处锚点位置：
  - `grep -rln 'BEGIN: review-dispatch' plugin/skills/` → 12 文件
  - `grep -rln 'BEGIN: repair-routing' plugin/skills/` → 9 文件
  - `grep -rln 'BEGIN: disposition-table' plugin/skills/` → 6 文件
- `plugin/scripts/verify-maturity.sh` L55-65 当前检查

**Contract anchors:**
- Owner: Issue 001
- Provider: `plugin/skills/_shared/{review-dispatch,repair-routing,disposition-table}.md`（3 个 canonical 新建）
- Consumer: 27 个 SKILL.md / reference / template 中原 inject 位置 — 改为 plugin-rooted Read 指令；codex-review/SKILL.md 仍 inject content-only（不动）
- Verification: verify-maturity.sh 新增 4 条 canonical 检查 + grep 无残留 BEGIN/END 锚点（除 codex-review） + 无相对路径 `_shared/` / `../_shared/` 引用

**Acceptance criteria:**
- [ ] `test -d plugin/skills/_shared/`
- [ ] `test -f plugin/skills/_shared/review-dispatch.md` 且 `wc -l` ≥ 50 且 ≤ 100
- [ ] `test -f plugin/skills/_shared/repair-routing.md` 且 `wc -l` ≥ 30 且 ≤ 60
- [ ] `test -f plugin/skills/_shared/disposition-table.md` 且 `wc -l` ≥ 30 且 ≤ 60
- [ ] `head -5` 每个 canonical 文件含路标 blockquote（`> **使用场景**` 或同义）
- [ ] `grep -i 'targeted-re-review\|targeted re-review' plugin/skills/_shared/review-dispatch.md` 返回空（canonical 干净）
- [ ] `grep -rln '<!-- BEGIN: review-dispatch -->' plugin/skills/ | grep -v 'codex-review' | wc -l` = 0
- [ ] `grep -rln '<!-- BEGIN: review-dispatch \[variant=content-only' plugin/skills/codex-review/` ≥ 1（codex-review 保留）
- [ ] `grep -rln '<!-- BEGIN: repair-routing -->' plugin/skills/ | wc -l` = 0
- [ ] `grep -rln '<!-- BEGIN: disposition-table -->' plugin/skills/ | wc -l` = 0
- [ ] `grep -rn '\.\./\_shared/\|^_shared/' plugin/skills/ | wc -l` = 0（无相对路径引用）
- [ ] 至少 10 处 SKILL.md / reference 含字符串 `plugin/skills/_shared/review-dispatch.md`（grep 验证 Read 指令存在）
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0（build 不再处理 3 个 canonical 化的 resolver）
- [ ] `bash plugin/scripts/verify-maturity.sh` 整体 pass（新检查通过 + 旧 anchor count 检查已删）
- [ ] `bash plugin/build/tests/test_review_evidence_table.sh` 通过（已迁移到扫 canonical）
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `ls plugin/skills/_shared/` → Expected: `review-dispatch.md repair-routing.md disposition-table.md`
- `wc -l plugin/skills/_shared/*.md` → Expected: 每个 30-100 行
- `grep -ci 'targeted-re-review\|targeted re-review' plugin/skills/_shared/review-dispatch.md` → Expected: 0
- `grep -rln '<!-- BEGIN: review-dispatch -->' plugin/skills/ | grep -v 'codex-review' | wc -l` → Expected: 0
- `grep -rln '<!-- BEGIN: repair-routing -->' plugin/skills/ | wc -l` → Expected: 0
- `grep -rln '<!-- BEGIN: disposition-table -->' plugin/skills/ | wc -l` → Expected: 0
- `grep -rln '<!-- BEGIN: review-dispatch \[variant=content-only' plugin/skills/codex-review/` → Expected: ≥ 1
- `grep -rn '\.\./\_shared/\|^_shared/' plugin/skills/` → Expected: empty
- `grep -rln 'plugin/skills/_shared/review-dispatch\.md' plugin/skills/ | wc -l` → Expected: ≥ 10
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(build): extract review-dispatch + repair-routing + disposition-table to plugin/skills/_shared/ canonical (D1)"
**Risk flags:** high-risk
**发布风险:** 模板系统去重可能导致某 SKILL.md 漏 Read 指令引用——缓解：grep 全量验证 + verify-maturity 新增 4 条检查 + Plan Implementation Review 时 Coordinator 亲跑一次完整 Codex review 派发验证 SKILL.md → canonical 链路
**AFK / HITL:** AFK（实现）+ HITL（Plan Impl Review 时人工验证 review 派发链路）
**Dependencies:** Pack 2, 3, 4, 5, 6, 7, 8（先做小且独立的清扫，减少 Pack 9 内合并冲突面；Pack 8 producer 迁移完成后，Pack 9 修改 SKILL.md 中的 review-dispatch 锚点 → Read 指令不会与脚本名冲突）
**Out of scope:** 
- `codex-review/SKILL.md` 的 `[variant=content-only]` 锚点（§10 第 15 条本轮不动）
- 删除 `.tmpl` 源文件（保留作为内容历史源；Issue 002 D13 才删 variant=targeted-re-review 子模块）
- 删除 `plugin/build/resolvers/{review-dispatch,repair-routing,disposition-table}.sh`（resolver 文件保留——content-only 变体仍依赖 review-dispatch.sh resolver；只跳过非 content-only 调用）

#### Implementation tasks
- [ ] Step 1: 找全锚点位置（baseline）
  - Run: `grep -rln 'BEGIN: review-dispatch' plugin/skills/` → 12 文件
  - Run: `grep -rln 'BEGIN: review-dispatch \[variant=content-only' plugin/skills/codex-review/` → 1 文件（codex-review/SKILL.md）
  - Run: `grep -rln 'BEGIN: repair-routing' plugin/skills/` → 9 文件
  - Run: `grep -rln 'BEGIN: disposition-table' plugin/skills/` → 6 文件
- [ ] Step 2: Read review-dispatch.md.tmpl 全文，识别 `[variant=targeted-re-review]` 段落边界
  - 关键：找到 `**Targeted re-review**` 子段（Step 3 内的）和任何标记为 `[variant=targeted-re-review]` 的内容
  - 记录该段起止
- [ ] Step 3: Read repair-routing.md.tmpl + disposition-table.md.tmpl 全文
- [ ] Step 4: 写 `plugin/skills/_shared/review-dispatch.md`
  - 顶部添加路标 blockquote：`> **使用场景**：派发 Codex review 时按本文件格式构造 prompt + 调用 dispatch-review.sh validate/record · **完成后回到** 调用方 phase skill 的对应 step`
  - 内容：从 review-dispatch.md.tmpl 抽取，**排除**所有 `[variant=targeted-re-review]` 段（保留 `[variant=baseline]` 主路径 + 通用部分如 `### Evidence` 表 / `### Confidence rubric` / `### Pre-emit Verification Gate` 等）
  - 把 `targeted-re-review` 相关的整段（Step 3 中的 "Targeted re-review" 子段及之下的 `--resume` 描述）整段省略
  - 内容中所有脚本调用使用 `dispatch-review.sh validate` / `dispatch-review.sh record` 形式（Pack 8 已迁移）
  - 完整、可直接 Read 使用
- [ ] Step 5: 验证 canonical 干净
  - Run: `grep -ci 'targeted-re-review\|targeted re-review\|--resume' plugin/skills/_shared/review-dispatch.md` → Expected: 0
- [ ] Step 6: 写 `plugin/skills/_shared/repair-routing.md`
  - 顶部路标 blockquote
  - 内容：从 repair-routing.md.tmpl 完整抽取（该模板无 targeted-re-review variant，全量保留）
- [ ] Step 7: 写 `plugin/skills/_shared/disposition-table.md`
  - 顶部路标 blockquote
  - 内容：从 disposition-table.md.tmpl 完整抽取
  - 注意：disposition enum 10 值含 `path-a` —— Issue 001 不删 path-a disposition 值（Issue 002 D3 才删）；canonical 保留 path-a 描述
- [ ] Step 8: 替换 12 处 review-dispatch 锚点位置为 Read 指令
  - 对每个文件（除 codex-review/SKILL.md）：找到 `<!-- BEGIN: review-dispatch -->` ... `<!-- END: review-dispatch -->` 整段，整段替换为：
    ```
    **Read** `plugin/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。
    ```
  - 注意：merge-integration-review.md 在同一文件中有 review-dispatch + disposition-table + repair-routing 三处锚点，每处独立替换
  - **codex-review/SKILL.md 跳过**（内含 [variant=content-only] 不动）
- [ ] Step 9: 替换 9 处 repair-routing 锚点位置为：
  ```
  **Read** `plugin/skills/_shared/repair-routing.md` 并按其流程处理 review findings。
  ```
- [ ] Step 10: 替换 6 处 disposition-table 锚点位置为：
  ```
  **Read** `plugin/skills/_shared/disposition-table.md` 并按其 disposition 选项处理 findings。
  ```
- [ ] Step 11: Edit `plugin/build/build.sh` — 在 `resolve_anchor` 函数或 process_skill_file 中加入 skip 逻辑：
  ```bash
  # Skip 3 canonical-converted anchors (D1)
  case "$anchor_name" in
    review-dispatch|repair-routing|disposition-table)
      if [[ "$variant" != "content-only" ]]; then
        return 1  # Treat as inactive — build does not inject
      fi
      ;;
  esac
  ```
  - 保留 content-only 变体的处理（codex-review/SKILL.md 用）
- [ ] Step 12: Edit `plugin/build/tests/test_review_evidence_table.sh` — 原本 `done < <(grep -rl "BEGIN: review-dispatch" "$PLUGIN_DIR/skills" | sort)` 改为扫 canonical：`done < <(echo "$PLUGIN_DIR/skills/_shared/review-dispatch.md"; grep -rl "BEGIN: review-dispatch \[variant=content-only" "$PLUGIN_DIR/skills" | sort)`
- [ ] Step 13: Edit `plugin/scripts/verify-maturity.sh` L58-59 — 删除：
  ```
  check "≥10 review-dispatch anchors" bash -c "[ \$(grep -rl 'BEGIN: review-dispatch' '$PLUGIN_DIR/skills/' | wc -l) -ge 10 ]"
  check "≥1 disposition-table anchor" bash -c "[ \$(grep -rl 'BEGIN: disposition-table' '$PLUGIN_DIR/skills/' | wc -l) -ge 1 ]"
  ```
  替换为 5 条新检查：
  ```
  check "canonical review-dispatch exists" test -f "$PLUGIN_DIR/skills/_shared/review-dispatch.md"
  check "canonical repair-routing exists" test -f "$PLUGIN_DIR/skills/_shared/repair-routing.md"
  check "canonical disposition-table exists" test -f "$PLUGIN_DIR/skills/_shared/disposition-table.md"
  check "no stale review-dispatch standard anchor" bash -c "[ \$(grep -rln '<!-- BEGIN: review-dispatch -->' '$PLUGIN_DIR/skills/' | grep -v 'codex-review' | wc -l) -eq 0 ]"
  check "no stale repair-routing anchor" bash -c "[ \$(grep -rln '<!-- BEGIN: repair-routing -->' '$PLUGIN_DIR/skills/' | wc -l) -eq 0 ]"
  check "no stale disposition-table anchor" bash -c "[ \$(grep -rln '<!-- BEGIN: disposition-table -->' '$PLUGIN_DIR/skills/' | wc -l) -eq 0 ]"
  check "no relative _shared/ references" bash -c "[ \$(grep -rn '\.\./\_shared/\|^_shared/' '$PLUGIN_DIR/skills/' | wc -l) -eq 0 ]"
  ```
- [ ] Step 14: Edit `plugin/architecture-draft.md` build template anchor 表：标记 review-dispatch / repair-routing / disposition-table 三个模板为 "inactive (canonical 化)"；review-dispatch.content-only 标 "保留（codex-review 单 site）"
- [ ] Step 15: 跑 build --check
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- [ ] Step 16: 跑 verify-maturity
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- [ ] Step 17: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 18: 验证 acceptance 全部满足（逐条跑 verification command）
- [ ] Step 19: Commit `refactor(build): extract review-dispatch + repair-routing + disposition-table to plugin/skills/_shared/ canonical (D1)`

---

### Task Pack 10: Reference 路标补齐 + 跳跃精简（D12）+ Architecture-draft 同步

**Issue:** Small Issue 10
**Goal behavior:** 给所有 reference（除 `_shared/`）顶部 5 行内补齐路标 blockquote；消除 3 处 reference 内部跳跃（execution-completion / final-review-completion / merge-rca-investigation）；折回 rca-pr-conflict-methodology.md 正文到 merge-rca-investigation.md；verify-maturity.sh 新增"路标完整性"检查；架构文档同步本 Issue 全部改动到 architecture-draft.md。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-discovery/references/discovery-formats.md`（顶部补路标）
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md`（顶部补路标）
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md`（折回 rca-pr-conflict-methodology 正文为 `## 方法论` 章节 + 路标已有不动）
- Delete: `plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`（折回后删）
- Modify: `plugin/skills/orchestrate-execution/references/execution-completion.md`（跳跃精简——把 "读取 execution-release-gate.md" / "读取 execution-repair-truncation.md" 改为 "详见 SKILL.md Step 13/14 Release Gate / 修复分流"）
- Modify: `plugin/skills/orchestrate-final-review/references/final-review-completion.md`（同上对 final-review-release-gate.md）
- Modify: `plugin/scripts/verify-maturity.sh`（新增"路标完整性"检查段）
- Modify: `plugin/architecture-draft.md`（同步本 Issue 全部改动：build template 表 / hook 表 / route enum 表 / reference 拓扑）

**Read first:**
- 设计文档 §4.2 决策 12
- 设计文档 §5.4 + §7.1（路标 verify-maturity 检查规则）
- `head -5` 4 个缺路标 reference（discovery-formats / learnings-trust-gate（已删——跳过）/ merge-brief-template / rca-pr-conflict-methodology）
- `plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md` 全文（要折回）
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md` L1-50（路标 + Self-Read Protocol 现状）
- `plugin/skills/orchestrate-execution/references/execution-completion.md` L1-60
- `plugin/skills/orchestrate-final-review/references/final-review-completion.md` L60-70
- `plugin/architecture-draft.md` 待同步章节：build template 表（找 grep `forbidden-shortcuts\|state-write\|trust-boundary`）+ hook 表（grep `guard-plan-doc-patch\|hooks 数`）+ route enum 表（grep `route.*8 值\|route.*4 值\|hotfix\|quickfix\|spike\|maintenance`）+ reference 拓扑（grep `route-extensions/\|multi-pr-explorer-handbook`）

**Contract anchors:**
- Owner: Issue 001（Pack 10 = 收尾）
- Provider: 4 个 reference 路标补齐 + 3 处跳跃精简 + architecture-draft 同步
- Consumer: verify-maturity 路标完整性检查 + 后续 Plan Review 用 architecture-draft 做基线对照
- Verification: head -5 grep 路标命中率 100%（_shared/ 除外）+ verify-maturity 路标段通过 + architecture-draft 与 Issue 001 完成态一致

**Acceptance criteria:**
- [ ] `head -5 plugin/skills/orchestrate-discovery/references/discovery-formats.md | grep -cE '> \*\*流程位置\*\*|> \*\*使用场景\*\*|> \*\*完成后回到\*\*'` ≥ 1
- [ ] `head -5 plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md | grep -cE '> \*\*流程位置\*\*|> \*\*使用场景\*\*|> \*\*完成后回到\*\*'` ≥ 1
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`（已折回 merge-rca-investigation.md 后删除）
- [ ] `grep -c '## 方法论' plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md` ≥ 1（含折回正文）
- [ ] `grep -c '读取 execution-release-gate\.md\|读取 execution-repair-truncation\.md' plugin/skills/orchestrate-execution/references/execution-completion.md` = 0
- [ ] `grep -c '读取 final-review-release-gate\.md' plugin/skills/orchestrate-final-review/references/final-review-completion.md` = 0
- [ ] 跑全 reference 路标体检（除 _shared/）：每个 reference head -5 命中路标 — 全 PASS
  - Verification 命令：`for f in $(find plugin/skills -type f -name '*.md' -not -path '*/\_shared/*' -path '*/references/*'); do head -5 "$f" | grep -qE '> \*\*流程位置\*\*|> \*\*使用场景\*\*|> \*\*完成后回到\*\*' || echo "MISSING: $f"; done` → Expected: empty output
- [ ] `plugin/scripts/verify-maturity.sh` 含路标完整性检查段（grep 验证存在）
- [ ] `plugin/architecture-draft.md`：
  - build template 表反映 10 active（含 review-dispatch.content-only）+ 3 canonical
  - hook 表反映 12 hooks（不再含 guard-plan-doc-patch）
  - route enum 表反映 4 值 + phase_skip / commit_format_override 字段
  - reference 拓扑不再含 multi-pr-explorer-handbook / route-extensions/ / path-a-re-review / learnings-confidence-audit / learnings-trust-gate / rca-pr-conflict-methodology 等已删条目
- [ ] `bash plugin/scripts/verify-maturity.sh` 整体 pass
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿

**Verification commands:**
- `head -5 plugin/skills/orchestrate-discovery/references/discovery-formats.md | grep -cE '流程位置|使用场景|完成后回到'` → Expected: ≥ 1
- `head -5 plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md | grep -cE '流程位置|使用场景|完成后回到'` → Expected: ≥ 1
- `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md && echo OK` → Expected: OK
- `grep -c '## 方法论' plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md` → Expected: ≥ 1
- `grep -c '读取 execution-release-gate\.md\|读取 execution-repair-truncation\.md' plugin/skills/orchestrate-execution/references/execution-completion.md` → Expected: 0
- `for f in $(find plugin/skills -type f -name '*.md' -not -path '*/\_shared/*' -path '*/references/*'); do head -5 "$f" | grep -qE '流程位置|使用场景|完成后回到' || echo "MISSING: $f"; done` → Expected: empty
- `grep -c 'signpost\|路标完整性\|流程位置' plugin/scripts/verify-maturity.sh` → Expected: ≥ 1（新增检查段）
- `grep -c 'guard-plan-doc-patch' plugin/architecture-draft.md` → Expected: 0 (已删) 或 仅出现在 history/changelog 段
- `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(refs): signpost completeness + jump elimination + architecture-draft sync (D12)"
**Risk flags:** normal
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** Pack 5（learnings-trust-gate.md 在 Pack 5 已删，Pack 10 不会试图给其补路标）, Pack 9（_shared/ 路径基线 + verify-maturity canonical 检查就位，Pack 10 加路标检查 不与之冲突）
**Out of scope:** 
- 进一步压缩 execution-completion / final-review-completion 等 reference 的字符数（Issue 003 D21 / D22 处理）
- jump-elimination 改动至 SKILL.md（Issue 003 处理 SKILL.md 内容压缩）

#### Implementation tasks
- [ ] Step 1: 跑全 reference 路标体检 baseline
  - Run: `for f in $(find plugin/skills -type f -name '*.md' -not -path '*/\_shared/*' -path '*/references/*'); do head -5 "$f" | grep -qE '流程位置|使用场景|完成后回到' || echo "MISSING: $f"; done` → 期待此时输出 2-3 个 MISSING（discovery-formats / merge-brief-template / rca-pr-conflict-methodology——后者将被删）
- [ ] Step 2: Edit `plugin/skills/orchestrate-discovery/references/discovery-formats.md` 顶部添加：
  ```
  > **使用场景**：起草 CONTEXT.md / ADR / scope.md 时按本文件 schema 输出 · **完成后回到**：调用方（discovery-discussion.md / discovery-design-document.md）
  ```
- [ ] Step 3: Edit `plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md` 顶部添加：
  ```
  > **使用场景**：multi-pr-merge 流程的 9 段 merge-brief 合成模板 · **完成后回到**：调用方 phase skill
  ```
- [ ] Step 4: Read `rca-pr-conflict-methodology.md` 全文
- [ ] Step 5: Edit `merge-rca-investigation.md` — 在合适位置（Step 4 的"读 rca-pr-conflict-methodology.md"段附近）添加 `## 方法论` 子章节，把 rca-pr-conflict-methodology.md 的 5 步方法论正文整段折入；同时把原 Step 4 中"读 rca-pr-conflict-methodology.md，按其中 5 步方法论执行调查"改写为"按本文件 ## 方法论 章节中 5 步执行调查"
- [ ] Step 6: 删除 rca-pr-conflict-methodology.md
  - Run: `rm plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`
- [ ] Step 7: Edit `plugin/skills/orchestrate-execution/references/execution-completion.md`
  - L9 附近的 "**触发** → 读取 execution-release-gate.md 执行 Release Gate 流程" 改为 "**触发** → 详见 SKILL.md Step 13（Release Gate 条件分支）"
  - L49 附近的 "按修复分流三条路径（读取 execution-repair-truncation.md）" 改为 "按 SKILL.md Step 14 修复分流三条路径"
  - 注意：本 Pack 只动 reference 文件，不动 SKILL.md（Issue 003 才压缩 SKILL.md Steps 13/14）
- [ ] Step 8: Edit `plugin/skills/orchestrate-final-review/references/final-review-completion.md`
  - L63 附近的 "**触发** → 读取 final-review-release-gate.md 执行 Release Gate 流程" 改为 "**触发** → 详见 SKILL.md Step 18（Release Gate 条件分支）"
- [ ] Step 9: 跑全 reference 路标体检
  - Run: `for f in $(find plugin/skills -type f -name '*.md' -not -path '*/\_shared/*' -path '*/references/*'); do head -5 "$f" | grep -qE '流程位置|使用场景|完成后回到' || echo "MISSING: $f"; done` → Expected: empty
- [ ] Step 10: Edit `plugin/scripts/verify-maturity.sh` — 新增"路标完整性"检查段（建议放在 §6.11 之后或 §6.12 标号）：
  ```bash
  echo ""
  echo "=== 6.12: Reference signpost completeness (D12) ==="
  missing=$(for f in $(find "$PLUGIN_DIR/skills" -type f -name '*.md' -not -path '*/\_shared/*' -path '*/references/*'); do head -5 "$f" | grep -qE '流程位置|使用场景|完成后回到' || echo "$f"; done)
  if [[ -n "$missing" ]]; then
    echo "FAIL: missing signpost blockquote (top-5 lines) in:"
    echo "$missing"
    fail=$((fail+1))
  else
    echo "PASS: all references have signpost blockquote"
    pass=$((pass+1))
  fi
  ```
- [ ] Step 11: Edit `plugin/architecture-draft.md`
  - 找到 build template 表（grep `forbidden-shortcuts\|state-write\|trust-boundary`），把 3 个删除的模板从 active 列移除；添加 3 个 canonical reference 行
  - 找到 hook 表（grep `13 hooks\|hooks 数\|guard-plan-doc-patch`），把 guard-plan-doc-patch 删除；hook 数从 13 改为 12
  - 找到 route enum 表（grep `8 值\|route.*hotfix`），把 8 值改为 4 值；新增 phase_skip / commit_format_override 字段说明
  - 找到 reference 拓扑表（grep `multi-pr-explorer-handbook\|route-extensions`），删除已删的 7 个条目（multi-pr-*-handbook ×3 + learnings-confidence-audit + learnings-trust-gate + path-a-re-review + rca-pr-conflict-methodology），删除 execution / workflow 一侧 route-extensions/ 目录提及
  - 备注：本 Pack 是 Issue 001 收尾，把 1200 行 architecture-draft.md 中所有 Issue 001 触及的章节一次性同步——不展开成多次 grep + 多次 edit，应一次 Read 1200 行后批量做 Edit
- [ ] Step 12: 跑 verify-maturity（含新 §6.12）
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- [ ] Step 13: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 14: 整 Issue 收尾——跑 plugin 完整成熟度验证
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
  - Run: `python3 -m json.tool plugin/.claude-plugin/plugin.json >/dev/null` → Expected: exit 0
  - Run: `python3 -m json.tool plugin/hooks/hooks.json >/dev/null` → Expected: exit 0
- [ ] Step 15: Commit `refactor(refs): signpost completeness + jump elimination + architecture-draft sync (D12)`

---

### Task Pack 11: 删除 arbitrary meta-limits（D24）

**Issue:** Small Issue 11
**Goal behavior:** 删除 `pack-count-validator.sh` 和 orchestrate-plan-writing 中对它的调用；不再用 magic number 限制 Plan 文档的 Task Pack 数量；§2.1 Hook 上限按设计文档已改为"行为验证而非总数验证"。

**Owned files / responsibilities:**
- Delete: `plugin/scripts/pack-count-validator.sh`
- Modify: `plugin/skills/orchestrate-plan-writing/SKILL.md`（删除 "Pack 数量检查" 一段，调用 validator + WARN/OVER_THRESHOLD 分流表）
- Modify: `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`（如含 ≤8 / "8 packs" 推荐表述则删除；保留按文件 scope 拆分的方法论）
- Modify: `plugin/scripts/verify-maturity.sh`（如含 `Hook 数 ≤ 10` 检查则改为"`hooks.json` 无 `guard-plan-doc-patch` 条目"按行为验证；新增"pack-count-validator 已删除"检查段）
- Modify: `plugin/architecture-draft.md`（如含 "Pack ≤ 8 / ≤ 12" / "pack-count-validator" 描述则删除）

**Read first:**
- 设计文档 §4.2 决策 24（本 Pack 唯一权威）
- 设计文档 §2.1 Hook 行（已改为"N（不设 arbitrary 上限）"）
- 设计文档 §7.1 verify 检查清单——找 "Hook 行为变化" + "pack-count-validator 已删除" 两条
- `plugin/scripts/pack-count-validator.sh` 全文（删前确认）
- `plugin/skills/orchestrate-plan-writing/SKILL.md` 搜 "pack-count-validator" / "Pack 数量检查" / "WARN_THRESHOLD" / "OVER_THRESHOLD"
- `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md` 搜 "≤8" / "≤ 8" / "8 packs"
- `plugin/scripts/verify-maturity.sh` 搜 "Hook 数" / "≤ 10" / "pack-count-validator"

**Contract anchors:**
- Owner: Issue 001（Pack 11 = 决策 24 唯一落地）
- Provider: pack-count-validator.sh 删除 + SKILL.md "Pack 数量检查" 段删除 + verify-maturity Hook 检查改行为验证
- Consumer: orchestrate-plan-writing skill（不再调用 validator）+ Plan 文档作者（不再被 magic number 限制）
- Verification: validator 文件不存在 + SKILL.md 不含 validator 引用 + verify-maturity 按行为验证 hook

**Acceptance criteria:**
- [ ] `test ! -f plugin/scripts/pack-count-validator.sh && echo OK` → Expected: OK
- [ ] `grep -c 'pack-count-validator' plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: 0
- [ ] `grep -c 'WARN_THRESHOLD\|OVER_THRESHOLD' plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: 0
- [ ] `grep -c 'Pack 数量检查' plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: 0
- [ ] `grep -c '≤ *8 *pack\|≤8 *pack\|8 *packs' plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md` → Expected: 0（若原本无表述则免改）
- [ ] `grep -c 'Hook 数.*≤ *10\|Hooks.*≤ *10' plugin/scripts/verify-maturity.sh` → Expected: 0（如原本含 ≤10 字面验证则删除）
- [ ] `grep -c 'guard-plan-doc-patch' plugin/scripts/verify-maturity.sh` ≥ 1（按行为验证仍保留）
- [ ] `bash plugin/scripts/verify-maturity.sh` → Expected: PASS（含 §6.12 路标段 + 新的 hook 行为段）
- [ ] `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] `grep -rc 'pack-count-validator' plugin/` → Expected: 0（全 plugin 无残留）

**Verification commands:**
- `test ! -f plugin/scripts/pack-count-validator.sh && echo OK` → Expected: OK
- `grep -rc 'pack-count-validator' plugin/ | grep -v ':0$' | head` → Expected: empty
- `grep -c 'Pack 数量检查\|pack-count-validator' plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: 0
- `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: PASS

**Commit boundary:** 单 atomic commit, scope = "refactor(arbitrary-limits): drop pack-count-validator + hook count ceiling (D24)"
**Risk flags:** normal — 只删工具脚本和文档表述，不动 runtime 路径
**发布风险:** N/A
**AFK / HITL:** AFK
**Dependencies:** Pack 7（hook 降级 / 删除 guard-plan-doc-patch 已完成）→ verify-maturity 改 "Hook 数 ≤ 10" 为行为验证才有意义；Pack 10（architecture-draft 同步已完成）→ Pack 11 收尾清理 architecture-draft 中可能仍存在的 Pack ≤8 描述
**Out of scope:** 
- 不动 state.sh `--threshold-percent 80` direction check（budget direction check 有具体 budget 公式依据，非 arbitrary）
- 不动 state.sh `packs_in_session < 5` Worker autonomy 启发（v3.8.0 Worker Loop 设计依据，非 arbitrary）
- 不动 §2.1 SKILL.md ≤ 300 / reference ≤ 250 / phase chars ≤ 50000（基于 token economy + sub-agent 加载预算，有可观测理由）

#### Implementation tasks
- [ ] Step 1: Read `plugin/scripts/pack-count-validator.sh` 确认无其他 consumer 调用（grep `pack-count-validator` 全 plugin/）
  - Run: `grep -rn 'pack-count-validator' plugin/` → 记录所有引用点
- [ ] Step 2: 删除 `plugin/scripts/pack-count-validator.sh`
  - Run: `rm plugin/scripts/pack-count-validator.sh`
- [ ] Step 3: Edit `plugin/skills/orchestrate-plan-writing/SKILL.md`
  - 找到 "Pack 数量检查" 一段（含 `bash ... pack-count-validator.sh <plan-file>` + WARN_THRESHOLD / OVER_THRESHOLD 表格 + OK/WARN/OVER_THRESHOLD 三档分流表），整段删除
  - 后续段（Plan Review 派发）的引用如有 "Pack 数量检查通过后" 文字，改为 "Plan Entry Gate + Inventory Gate 通过后"
- [ ] Step 4: Read `plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md` 搜 ≤8 / 8 packs / OVER_THRESHOLD 表述
  - Run: `grep -nE '≤ *8|8 *pack|OVER_THRESHOLD|WARN_THRESHOLD' plugin/skills/orchestrate-plan-writing/references/plan-writing-methodology.md`
  - 如有命中：删除对应表述，保留方法论文本（"按文件 scope 拆分 Task Pack"）
- [ ] Step 5: Read `plugin/scripts/verify-maturity.sh` 搜 Hook 数 ≤ 10 / pack-count-validator
  - Run: `grep -nE 'Hook 数|hooks.*≤|pack-count-validator' plugin/scripts/verify-maturity.sh`
  - 把"Hook 脚本数 ≤ 10"硬验证改为按行为验证：保留对 `guard-plan-doc-patch` 不存在的检查；删除对 `hooks/*.sh` 总数 ≤ 10 的硬检查
  - 新增"pack-count-validator 已删除"段：`test ! -f plugin/scripts/pack-count-validator.sh`
- [ ] Step 6: Edit `plugin/architecture-draft.md`
  - Run: `grep -nE 'pack-count-validator|Pack ≤ *8|≤ *8 *pack|≤ *12 *pack|WARN_THRESHOLD|OVER_THRESHOLD' plugin/architecture-draft.md`
  - 如有命中：删除对应段落；如 hook 表里有 ≤ 10 字面，改为 "按行为验证（无 guard-plan-doc-patch）"
- [ ] Step 7: 跑 verify-maturity（含新的 hook 行为段 + pack-count-validator 删除段）
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: PASS
- [ ] Step 8: 跑全量测试
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: PASS
- [ ] Step 9: 残留 grep
  - Run: `grep -rc 'pack-count-validator' plugin/` → Expected: 0
- [ ] Step 10: Commit `refactor(arbitrary-limits): drop pack-count-validator + hook count ceiling (D24)`

---

## Pack Execution Manifest

| Pack | Title | Status | Dependencies |
|------|-------|--------|--------------|
| - [ ] **Pack 1** | Agent frontmatter 瘦身（D11 局部） | pending | None |
| - [ ] **Pack 2** | 死模板 forbidden-shortcuts 内联并删除（D2.a） | pending | None |
| - [ ] **Pack 3** | 死模板 state-write 内联并删除（D2.b） | pending | None |
| - [ ] **Pack 4** | 死模板 trust-boundary 内联并删除（D2.c） | pending | None |
| - [ ] **Pack 5** | 孤儿 + 副本 reference + verify-maturity §6.11 清扫（D2.d） | pending | None |
| - [ ] **Pack 6** | Route 4-7 折叠为 Route 1 + flags（D10） | pending | None |
| - [ ] **Pack 7** | Hook 降级 / 删除（D9） | pending | None |
| - [ ] **Pack 8** | Scripts 合并：dispatch-review.sh + dispatch-route-worker.sh（D8） | pending | None |
| - [ ] **Pack 9** | Canonical reference 抽取（D1） | pending | 2, 3, 4, 5, 6, 7, 8 |
| - [ ] **Pack 10** | Reference 路标补齐 + 跳跃精简 + architecture-draft 同步（D12） | pending | 5, 9 |
| - [ ] **Pack 11** | 删除 arbitrary meta-limits — pack-count-validator + hook 总数上限（D24） | pending | 7, 10 |

**串行执行顺序建议**：1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11（按本表顺序，Pack 11 在 Pack 10 architecture-draft 同步之后做收尾，确保 architecture-draft 中 D24 涉及的描述也一并清理）

---

## Open Items

- **[resolved by D24]** 原 [needs-evaluation] Hook 数 §2.1 目标 ≤ 10 不可达问题——决策 24 直接删除此 arbitrary 上限。Pack 11 落地后 verify-maturity 按行为验证（无 guard-plan-doc-patch），不再硬验总数。
- **[out-of-scope clarification]** Pack 9 canonical 抽取采用"抽取时归一化"（exclude `[variant=targeted-re-review]` during extraction），是设计 D1 "或等价做法" 授权范围内的合理实现选择——不是预执行 Issue 002 的 D13。Issue 002 D13 仍在 `.tmpl` 源中删除该 variant（对已抽取的 canonical 是 no-op）。
- **[out-of-scope]** Shim 期持续——Pack 8 完成后保留 4 个旧脚本作为 shim，整个 Issue 002/003 期间不删；Issue 003 关闭后单独清理阶段删除 shim。
- **[out-of-scope]** `execution-worker-handbook.md` 路径 bug 完整 8 处修正归 Issue 003 D21；Issue 001 Pack 5 仅清理 architecture-draft.md L286 / L299 两处（这两处描述了不存在的孤儿文件）。
- **[out-of-scope]** Discovery SKILL.md Steps 3-6 `Skill({ skill: "grill-with-docs" })` 显式调用 + discovery-discussion.md L80 改写归 Issue 003 D15。
