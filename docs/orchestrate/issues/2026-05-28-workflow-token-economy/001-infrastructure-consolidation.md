# Issue 001 — 基础设施层重构（Template & Reference & Routes）

## What to build

把 plugin 的"广义基础设施层"做一次系统级清理与去重，覆盖：

- **Canonical reference 抽取**（决策 1）：`review-dispatch` / `repair-routing` / `disposition-table` 三个高频 inject 锚点抽取到 `plugin/skills/_shared/` plugin-rooted 绝对路径，禁止相对路径形式。所有原 inject 锚点位置改为 `Read` 引用。
- **死模板 + 孤儿文件批量删除**（决策 2）：删除 `forbidden-shortcuts.md.tmpl` + 2 active anchor inline / `state-write.md.tmpl` + inline / `trust-boundary.md.tmpl` + inline；删除 3 个 multi-pr handbook（共 455 行）；折回 `learnings-confidence-audit.md` / `learnings-trust-gate.md`；删除 `path-a-re-review.md`；删除 `route-extensions/` 副本目录。同步 `verify-maturity.sh` §6.11 共 6 行（3 个 `-f` + 3 个 `grep -q 'Self-Read Protocol'`）。
- **脚本合并**（决策 8）：`record-/validate-review-dispatch.sh` 对合并为 `dispatch-review.sh` 含 `validate` / `record` 子命令；`record-/validate-route-worker-dispatch.sh` 对合并为 `dispatch-route-worker.sh` 同模式。shim 期保留旧 4 个脚本作为转发，渐进迁移所有 producer 引用。
- **Hook 行为变化**（决策 9）：删除 `guard-plan-doc-patch.sh`；`validate-plan-dispatch.sh` Step 6 Manifest 检查从 exit 2 降为 WARN；删除 Step 8 Path A；`validate-multi-pr-dispatch.sh` (b)(d) **保持 exit 2**（不降级）；删除 `gate-codex-review.sh` 的 `--resume` / `targeted-re-review` / `path-a-re-review` 三个分支整段。
- **Routes 4-7 折叠**（决策 10）：runtime route enum 4 值（formal / bug-investigation / multi-pr-merge / direct-repair），Hotfix / Quick Fix / Spike / Maintenance 改为 Route 1 formal + `phase_skip[]` flags + `commit_format_override` + `budget_status: "unlimited"`。
- **外部 Skill 集成对齐 + agent frontmatter 瘦身**（决策 11）：移除 stale `skills:` frontmatter 字段；保留必要的外部 skill inline 引用。
- **Reference 跳跃精简 + 路标补齐**（决策 12）：所有 `plugin/skills/*/references/*.md`（除 `_shared/`）顶部 5 行内必须含路标 blockquote。

完成本 issue 后：基础设施层（模板 / 脚本 / hook / route enum / agent frontmatter / 路标）达到 token economy 标准；下游 Issue 002 / 003 才能在干净的合同基线上展开。

## Small issues

### 1. Agent frontmatter 瘦身（D11 局部）
**Type:** AFK
**What to build:** 从 `plugin/agents/docs-worker.md` 和 `plugin/agents/plan-writer.md` 的 frontmatter 中移除 `skills:` 字段；保留 `pack-executor` / `complex-pack-executor` / `root-cause-analyst` 的 `skills:` 字段（每次都用得到）。body 中按需 `Skill({...})` 调用的引导保留。
**Acceptance criteria:**
- [ ] `plugin/agents/docs-worker.md` 顶部 frontmatter 不含 `skills:` 字段
- [ ] `plugin/agents/plan-writer.md` 顶部 frontmatter 不含 `skills:` 字段
- [ ] `pack-executor.md` / `complex-pack-executor.md` / `root-cause-analyst.md` 的 `skills:` 字段保持不变
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 2. 死模板 `forbidden-shortcuts` 内联并删除（D2 part a）
**Type:** AFK
**What to build:** 把 `<!-- BEGIN: forbidden-shortcuts -->` 锚点内的内容直接内联到 `orchestrate-final-review/SKILL.md` L155 和 `orchestrate-execution/SKILL.md` L480 两处目标文件（删除 BEGIN/END 注释，保留内容）；之后删除模板源 `plugin/build/templates/forbidden-shortcuts.md.tmpl` 和 resolver `plugin/build/resolvers/forbidden-shortcuts.sh`。
**Acceptance criteria:**
- [ ] `grep -rn 'BEGIN: forbidden-shortcuts' plugin/` 返回空
- [ ] `plugin/build/templates/forbidden-shortcuts.md.tmpl` 不存在
- [ ] `plugin/build/resolvers/forbidden-shortcuts.sh` 不存在
- [ ] 原内容仍在 final-review/SKILL.md L155 和 execution/SKILL.md L480 附近（不带锚点）
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 3. 死模板 `state-write` 内联并删除（D2 part b）
**Type:** AFK
**What to build:** 把 `<!-- BEGIN: state-write -->` 锚点内的内容内联到 `orchestrate-execution/SKILL.md` L211（删除 BEGIN/END 注释）；删除模板源 `plugin/build/templates/state-write.md.tmpl` 和 resolver `plugin/build/resolvers/state-write.sh`。
**Acceptance criteria:**
- [ ] `grep -rn 'BEGIN: state-write' plugin/` 返回空
- [ ] `plugin/build/templates/state-write.md.tmpl` 不存在
- [ ] `plugin/build/resolvers/state-write.sh` 不存在
- [ ] 原内容仍在 execution/SKILL.md 该位置（不带锚点）
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 4. 死模板 `trust-boundary` 内联并删除（D2 part c）
**Type:** AFK
**What to build:** 把 `<!-- BEGIN: trust-boundary [variant=worker] -->` 锚点内的内容内联到 `orchestrate-execution/SKILL.md` L187（删除 BEGIN/END 注释）；删除模板源 `plugin/build/templates/trust-boundary.md.tmpl` 和 resolver `plugin/build/resolvers/trust-boundary.sh`。
**Acceptance criteria:**
- [ ] `grep -rn 'BEGIN: trust-boundary' plugin/` 返回空
- [ ] `plugin/build/templates/trust-boundary.md.tmpl` 不存在
- [ ] `plugin/build/resolvers/trust-boundary.sh` 不存在
- [ ] 原 [variant=worker] 内容仍在 execution/SKILL.md 该位置
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 5. 孤儿 + 副本 reference 与 verify-maturity §6.11 清扫（D2 part d）
**Type:** AFK
**What to build:** 
- 删除 3 个 multi-pr handbook 孤儿文件：`multi-pr-conflict-worker-handbook.md` / `multi-pr-explorer-handbook.md` / `multi-pr-integration-review-handbook.md`
- 把 `learnings-confidence-audit.md`（60 行）和 `learnings-trust-gate.md`（21 行）折回 `orchestrate-execution/SKILL.md` 的 Worker 返回处理段（保留内容作为 SKILL.md 子章节）
- 删除 `path-a-re-review.md`（孤儿 + 与决策 3 配套；但 Issue 001 只删文件本身，不动 state.sh path-a-escalation——Issue 002 负责）
- 删除整个 `plugin/skills/orchestrate-execution/references/route-extensions/` 目录（4 个 DEPRECATED 副本：route-4/5/6/7）
- 修改 `verify-maturity.sh` §6.11（L379-394）：删除 6 行 handbook 检查（3 个 `test -f` + 3 个 `grep -q 'Self-Read Protocol'`），改为单条检查"`merge-brief-template.md` 存在 + 4 个 merge-* references 各角色 Self-Read 内容已覆盖"
- 修正 `execution-worker-handbook.md` 文件名 bug：本 Pack 不动（Issue 003 D21 完整修正 8 处引用）。本 Pack 仅在 architecture-draft.md L286 / L299 删除"execution-worker-handbook（Worker 自读）"裸引用（这两处提及的是文件不存在的孤儿描述）；L53 / L338 / SKILL.md L202 / agent 文件 / worker-loop.md.tmpl 由 Issue 003 修
**Acceptance criteria:**
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-conflict-worker-handbook.md`
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-explorer-handbook.md`
- [ ] `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/multi-pr-integration-review-handbook.md`
- [ ] `test ! -f plugin/skills/orchestrate-execution/references/learnings-confidence-audit.md`
- [ ] `test ! -f plugin/skills/orchestrate-execution/references/learnings-trust-gate.md`
- [ ] `test ! -f plugin/skills/orchestrate-execution/references/path-a-re-review.md`
- [ ] `test ! -d plugin/skills/orchestrate-execution/references/route-extensions/`
- [ ] `grep -n 'Self-Read Protocol' plugin/scripts/verify-maturity.sh` 不再返回 §6.11 三处 handbook 行
- [ ] `grep -c '6.11' plugin/scripts/verify-maturity.sh` ≥ 1（新检查存在）
- [ ] `grep -n 'execution-worker-handbook' plugin/architecture-draft.md` 仅返回 L53 / L338（剩余 2 处由 Issue 003 修）；L286 / L299 已删
- [ ] orchestrate-execution/SKILL.md 含原 learnings-confidence-audit 60 行 + learnings-trust-gate 21 行的内容（grep 关键标题）
- [ ] `bash plugin/scripts/verify-maturity.sh` 整体 pass
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 6. Route 4-7 折叠为 Route 1 + flags（D10）
**Type:** AFK
**What to build:** 
- 修改 `plugin/state-schema/workflow-state-v1.json`：`route` enum 从 8 值缩为 4 值（`formal / direct-repair / multi-pr-merge / bug-investigation`，保留 runtime 全称），新增 `phase_skip`（array of phase enum，默认 `[]`）和 `commit_format_override`（string\|null，默认 null）字段
- 修改 `plugin/scripts/state.sh init`：初始化 `phase_skip: []`, `commit_format_override: null`
- 修改 `orchestrate-workflow/SKILL.md`：删除 Step 1 表中 Route 4-7 四行；新增"Route 1 Variant Table"段落（≈80-120 行），把原 route-4-hotfix.md / route-5-quickfix.md / route-6-spike.md / route-7-maintenance.md 的核心规则（每个 ≈20-30 行）整合进来；Entry Gate 识别 hotfix/quickfix/spike/maintenance 关键词 → Route 1 + 对应 `phase_skip` + `budget_status: unlimited` + （hotfix 时）`commit_format_override: "hotfix-unreviewed"`
- 删除 `plugin/skills/orchestrate-workflow/references/route-extensions/` 整个目录（4 个文件）
- 保留 `pending_post_push_reviews` 机制不动（hotfix 真正特殊的状态）
**Acceptance criteria:**
- [ ] `jq '.properties.route.enum | length' plugin/state-schema/workflow-state-v1.json` = 4
- [ ] `jq '.properties.route.enum' plugin/state-schema/workflow-state-v1.json` 输出 `["formal","direct-repair","multi-pr-merge","bug-investigation"]`（顺序不强制）
- [ ] `jq '.properties.phase_skip' plugin/state-schema/workflow-state-v1.json` 不为 null
- [ ] `jq '.properties.commit_format_override' plugin/state-schema/workflow-state-v1.json` 不为 null
- [ ] `test ! -d plugin/skills/orchestrate-workflow/references/route-extensions/`
- [ ] `orchestrate-workflow/SKILL.md` 含 "Route 1 Variant Table" 字符串
- [ ] `grep -c "Route [4-7]:" plugin/skills/orchestrate-workflow/SKILL.md` = 0
- [ ] `bash plugin/scripts/state.sh init --run-id test-001 --slug test --route formal` 成功，生成的 JSON 含 `phase_skip: []` 和 `commit_format_override: null`
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 7. Hook 降级 / 删除（D9）
**Type:** AFK
**What to build:** 
- 删除 `plugin/hooks/guard-plan-doc-patch.sh` 整文件 + `plugin/hooks/hooks.json` 中第 80-83 行 PreToolUse/Write 中对应 entry
- 修改 `plugin/hooks/validate-plan-dispatch.sh` Step 6 (L83-91)：Manifest 缺失从 `exit 2` 改为 `echo "[WARN] Manifest missing — Worker may work from plan body"` 并 `exit 0`
- 修改 `plugin/hooks/validate-plan-dispatch.sh` Step 8 (L124-130)：整段删除（Path A 检查；Issue 002 才删 Path A 概念，但本 hook 检查已无产值——它读 `path_a_escalation` 字段，Issue 002 会删字段；本 Pack 先删 hook 检查，状态字段 Issue 002 删）
- 修改 `plugin/hooks/validate-multi-pr-dispatch.sh` (b)(d) 检查：**保持 exit 2 不动**（Alignment Review C5）
- 修改 `plugin/hooks/gate-codex-review.sh`：删除 `path-a-re-review` 分支（L54-65 附近）+ `targeted-re-review` 分支（L66-75 附近，含 `--resume` 检查）；保留 `uncommitted packs` 检查
**Acceptance criteria:**
- [ ] `test ! -f plugin/hooks/guard-plan-doc-patch.sh`
- [ ] `grep -c 'guard-plan-doc-patch' plugin/hooks/hooks.json` = 0
- [ ] `plugin/hooks/validate-plan-dispatch.sh` Step 6 Manifest 缺失输出含 `WARN` 字符串且 `exit 0`
- [ ] `plugin/hooks/validate-plan-dispatch.sh` 不再含 "Step 8: Path A escalation" 段
- [ ] `grep -c 'path-a-re-review\|targeted-re-review' plugin/hooks/gate-codex-review.sh` = 0
- [ ] `plugin/hooks/validate-multi-pr-dispatch.sh` (b)(d) 仍 `exit 2`（grep `exit 2` 出现次数与改前一致或减少不超过 1）
- [ ] `python3 -m json.tool plugin/hooks/hooks.json >/dev/null` 成功
- [ ] hook tests `plugin/hooks/tests/*.sh` 全绿（运行 `bash plugin/scripts/run-all-tests.sh`）
- [ ] Hook 脚本数 `ls plugin/hooks/*.sh | wc -l` = 12（13-1）
**Blocked by:** None

### 8. Scripts 合并：`dispatch-review.sh` 和 `dispatch-route-worker.sh`（D8）
**Type:** AFK
**What to build:** 
- 新建 `plugin/scripts/dispatch-review.sh`：含 `validate` 和 `record` 两个子命令，分别调用原 `validate-review-dispatch.sh` 和 `record-review-dispatch.sh` 的逻辑（不复制内容，直接 source 共享函数或 inline 两段实现）
- 新建 `plugin/scripts/dispatch-route-worker.sh`：含 `validate` 和 `record` 两个子命令，对应 `validate-route-worker-dispatch.sh` 和 `record-route-worker-dispatch.sh`
- 改写旧 4 个脚本为 shim：每个旧脚本仅含 `exec "$(dirname "$0")/dispatch-<x>.sh" <validate|record> "$@"`
- 迁移所有 producer 引用为新合并脚本（grep `record-review-dispatch.sh\|validate-review-dispatch.sh\|record-route-worker-dispatch.sh\|validate-route-worker-dispatch.sh` 在 plugin/skills/ / plugin/build/templates/ / plugin/hooks/ 找全并修改为 `dispatch-<x>.sh <subcommand>` 形式）
- shim 期：Issue 001 内迁移完所有 producer 后保留 4 个 shim 文件不删（design §5.8：所有 producer 完成迁移 + 一轮 Plan Implementation Review 通过后才删除 shim——这一轮 PIR 在 Final Review 阶段完成，shim 删除在 Issue 003 之后的清理阶段）。本 Pack 仅完成新建 + shim 化 + producer 迁移
**Acceptance criteria:**
- [ ] `test -x plugin/scripts/dispatch-review.sh`
- [ ] `test -x plugin/scripts/dispatch-route-worker.sh`
- [ ] `bash plugin/scripts/dispatch-review.sh --help` 输出含 `validate` 和 `record`
- [ ] `bash plugin/scripts/dispatch-route-worker.sh --help` 输出含 `validate` 和 `record`
- [ ] 旧 4 个脚本仍存在（shim），但每个文件 ≤ 10 行
- [ ] `grep -rln 'validate-review-dispatch\.sh\|record-review-dispatch\.sh\|validate-route-worker-dispatch\.sh\|record-route-worker-dispatch\.sh' plugin/skills/ plugin/build/templates/ plugin/hooks/ | wc -l` = 0（producer 全部迁移）
- [ ] 旧脚本 shim 在 `plugin/scripts/tests/` 中至少有一个测试验证 shim 转发等价（新建测试）
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** None

### 9. Canonical reference 抽取（D1）
**Type:** AFK
**What to build:** 
- 新建目录 `plugin/skills/_shared/`
- 新建 `plugin/skills/_shared/review-dispatch.md`：从 `plugin/build/templates/review-dispatch.md.tmpl` 抽取内容；**抽取时排除 `[variant=targeted-re-review]` 子模块/段落**（advisor approach："canonical from day one"——Issue 002 D13 之后会删 .tmpl 中该 variant，canonical 不带残留），保留 baseline 主路径 + 顶部"使用场景"路标 blockquote + 使用 plugin-rooted 引用范例
- 新建 `plugin/skills/_shared/repair-routing.md`：从 `repair-routing.md.tmpl` 抽取完整内容 + 顶部路标 blockquote
- 新建 `plugin/skills/_shared/disposition-table.md`：从 `disposition-table.md.tmpl` 抽取完整内容 + 顶部路标 blockquote
- 替换所有原 `<!-- BEGIN: review-dispatch -->` / `<!-- BEGIN: repair-routing -->` / `<!-- BEGIN: disposition-table -->` 锚点位置为 plugin-rooted Read 指令：`**Read** \`plugin/skills/_shared/<name>.md\` 并按其格式...`；删除 BEGIN/END 注释和原 inject 内容（在 12+9+6=27 个位置，但其中 1 个是 `codex-review/SKILL.md` 的 `[variant=content-only]`——**本轮不动**，保留 inject + 模板 + resolver）
- 修改 `plugin/build/build.sh`：保留锚点系统但跳过 `review-dispatch` / `repair-routing` / `disposition-table` 三个 resolver（添加 skip 列表或注释掉 resolver 调用）；不删除 .tmpl 源文件（保留作为内容历史源，Issue 002 D13 才删 variant=targeted-re-review）
- 修改 `plugin/build/tests/test_review_evidence_table.sh`：原本扫描 BEGIN 锚点的 evidence table 测试改为扫描 canonical reference 文件 `_shared/review-dispatch.md`
- 修改 `plugin/scripts/verify-maturity.sh` L58-59：删除 "≥10 review-dispatch anchors" 和 "≥1 disposition-table anchor" 两条检查；新增 4 条新检查：
  1. `test -f plugin/skills/_shared/review-dispatch.md`
  2. `test -f plugin/skills/_shared/repair-routing.md`
  3. `test -f plugin/skills/_shared/disposition-table.md`
  4. `grep -rn '<!-- BEGIN: review-dispatch -->\|<!-- BEGIN: repair-routing -->\|<!-- BEGIN: disposition-table -->' plugin/skills/ | grep -v 'codex-review/SKILL.md' | wc -l` = 0
  5. `grep -rn '\.\./\_shared\|^_shared/' plugin/skills/ | wc -l` = 0（禁相对路径）
- 修改 `plugin/architecture-draft.md`：更新 build template anchor 表（13 → 10 active；3 个 canonical 新增；`review-dispatch.content-only` 留作本轮保留说明）
**Acceptance criteria:**
- [ ] `test -d plugin/skills/_shared/`
- [ ] `test -f plugin/skills/_shared/review-dispatch.md` 且 ≥ 50 行
- [ ] `test -f plugin/skills/_shared/repair-routing.md` 且 ≥ 30 行
- [ ] `test -f plugin/skills/_shared/disposition-table.md` 且 ≥ 30 行
- [ ] `grep -i 'targeted-re-review\|targeted re-review' plugin/skills/_shared/review-dispatch.md` 返回空（normalize 干净）
- [ ] `grep -rln '<!-- BEGIN: review-dispatch -->' plugin/skills/ | grep -v 'codex-review' | wc -l` = 0
- [ ] `grep -rln '<!-- BEGIN: repair-routing -->' plugin/skills/ | wc -l` = 0
- [ ] `grep -rln '<!-- BEGIN: disposition-table -->' plugin/skills/ | wc -l` = 0
- [ ] `grep -rn '\.\./\_shared\|^_shared/' plugin/skills/ | wc -l` = 0（无相对路径引用）
- [ ] 至少 5 个 SKILL.md 或 reference 中含 `plugin/skills/_shared/review-dispatch.md` Read 指令（grep 验证）
- [ ] `codex-review/SKILL.md` 仍含 `<!-- BEGIN: review-dispatch [variant=content-only] -->` 锚点（本轮不动）
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` exit 0
- [ ] `bash plugin/scripts/verify-maturity.sh` 整体 pass
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** 2, 3, 4, 5, 6, 7, 8（先做小且独立的清扫，再做合同表面最大的 D1 抽取——减少 D1 Pack 内的合并冲突面）

### 10. Reference 路标补齐 + 跳跃精简（D12）
**Type:** AFK
**What to build:** 
- 给 4 个缺顶部路标的 reference 补齐 `> **流程位置** / **使用场景** / **完成后回到**` blockquote（5 行内）：
  1. `plugin/skills/orchestrate-discovery/references/discovery-formats.md`
  2. `plugin/skills/orchestrate-execution/references/learnings-trust-gate.md` — 由 Pack 5 折回 execution/SKILL.md 后已删除，此 Pack 跳过该文件（若仍存在则报错）
  3. `plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md`
  4. `plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`
- 跳跃精简 3 处（design D12）：
  1. `execution-completion.md` L9 / L49 对 `execution-release-gate.md` 和 `execution-repair-truncation.md` 的引用——**Issue 001 仅修改 reference 文件中的跳跃链路，不动 SKILL.md Steps 13/14 内容**（Issue 003 阶段会进一步压缩 SKILL.md）。改法：把 reference 内部"读取 execution-release-gate.md"行改为"详见 SKILL.md Step 13 Release Gate 分支"
  2. `final-review-completion.md` L63 对 `final-review-release-gate.md` 的引用——同处理
  3. `merge-rca-investigation.md` L12 / L40 对 `rca-pr-conflict-methodology.md` 的跳——把 `rca-pr-conflict-methodology.md` 的方法论正文（5 步方法论）作为 `## 方法论` 章节折回 `merge-rca-investigation.md`；删除 `rca-pr-conflict-methodology.md` 文件
- 修改 `plugin/scripts/verify-maturity.sh` 新增"路标完整性"检查：所有 `plugin/skills/*/references/*.md`（除 `_shared/`）顶部 5 行内必须含 `> **流程位置**` 或 `> **使用场景**` 或 `> **完成后回到**` 任一 blockquote，无则报错
**Acceptance criteria:**
- [ ] `head -5 plugin/skills/orchestrate-discovery/references/discovery-formats.md` 含 `流程位置\|使用场景\|完成后回到` 任一
- [ ] `head -5 plugin/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md` 含路标 blockquote
- [ ] `head -5 plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md` — 此文件已被删除合并到 merge-rca-investigation.md 中，跳过；改为验证 `test ! -f plugin/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`
- [ ] `merge-rca-investigation.md` 含 `## 方法论` 标题且行数比改前多 ≈80
- [ ] `execution-completion.md` 不再含直接 `读取 execution-release-gate.md` 或 `execution-repair-truncation.md` 句式
- [ ] `final-review-completion.md` 不再含直接 `读取 final-review-release-gate.md` 句式
- [ ] `verify-maturity.sh` 新增 signpost 检查段落（grep `signpost\|路标` 验证存在）
- [ ] 对所有 references（除 `_shared/`）跑一遍 head -5 grep 验证，全部命中路标
- [ ] `bash plugin/scripts/verify-maturity.sh` 整体 pass
- [ ] `bash plugin/scripts/run-all-tests.sh` 全绿
**Blocked by:** 5（learnings-trust-gate.md 由 Pack 5 删除/折回）, 9（_shared/ 路径基线由 Pack 9 建立，verify-maturity 检查互不冲突）

## Blocked by

- None — 可立即启动
