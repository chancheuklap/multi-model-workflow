# Issue 003 — Phase Skill 优化与压缩

## What to build

在 Issue 001（基础设施）+ Issue 002（合同清理）完成后的干净基线上，对 6 个 phase skill 做最后一层压缩与精修：

- **Discovery 阶段集成**（决策 14-19）：
  - Explorer agent 并行派发（与 Plan-writing 对称）
  - `grill-with-docs` 提升为 Step 0 同步入口；CONTEXT.md 与 design 同等地位
  - 外部精华轻量引入 3 条（synthesize fast-path / prototype-snippet 例外 / Push twice）；**显式不引入** Forcing Questions 三问
  - Discovery 文档压缩（删 Self-Read Protocol 死内容 / Route Dispatch 错位行 / grill-with-docs 重复）；合并两个 issue template
  - **完全删除 GitHub Issue 发布**（不是 opt-in 而是 fully delete）；issue 本地文件保留
  - Mockup 生成留时间和空间（最小化，仅一行规则——用户主动调用 frontend-design/prototype 等 skill）
- **Sub-agent 事实校验机制（横切）**（决策 18 / Content Review C3 闭合）：
  - `plugin/agents/code-explorer.md` / `complex-code-explorer.md` / `root-cause-analyst.md` description 含 "Coordinator must verify" 表述
  - `orchestrate-discovery/SKILL.md` 新增 Step 1.5（Explorer 报告校验门控）
  - `orchestrate-plan-writing` / `orchestrate-execution` / `orchestrate-multi-pr-merge` SKILL.md 同步加 Step
  - `agent-return-handler.sh` 输出 "⚠️ 写入交付物前必须校验本次返回的事实声明"
  - `architecture-draft.md` 新增"Sub-agent 信任边界"章节
- **Plan Writing 压缩**（决策 20）：删 `plan-writer-dispatch.md` L5-15 + `plan-review-dispatch.md` L5-13 Self-Read Protocol 死内容；budget 公式同步落地（Issue 002 已确定公式，此处落地到 plan-gates.md L46 + orchestrate-plan-writing/SKILL.md L172）
- **Execution 微调**（决策 21 / Alignment Review C1 完整版）：**8 处** `execution-worker-handbook` 引用全部修正为 `execution-worker-dispatch.md`：
  1. `plugin/skills/orchestrate-execution/SKILL.md` L202
  2. `plugin/agents/pack-executor.md` L71
  3. `plugin/agents/complex-pack-executor.md` L69
  4. `plugin/build/templates/worker-loop.md.tmpl` L12（**critical runtime bug**）
  5-8. `plugin/architecture-draft.md` L53 / L286 / L299 / L338
  
  + 删 `execution-review-dispatch.md` L5-15 Self-Read 死内容
- **Final Review 微调**（决策 22）：
  - `final-review-angles.md` L5-15 Self-Read 死内容删除
  - `final-review-repair.md` Step 11 整段（122 行 targeted re-review）+ Step 12 三轮截断改为二段（repair-once + RCA escalation）
  - L353 Phase 软上限重算为 **3**（2 baseline + 0 targeted + 1 release gate）
  - `final-review-release-gate.md` Step 18 / `final-review-completion.md` Step 15 / `SKILL.md` L52 同步删除 targeted re-review 引用
- **Multi-PR 微调**（决策 23）：
  - "Coordinator 端最小职责" section 重复 5 处提取为 SKILL.md 顶部通用 4 step 模板
  - `merge-completion.md` "不存在非阻塞项" 改为单行引用 Final Review 清扫
  - `merge-integration-review.md` 末尾补 Phase 软上限 = **1**（1 integration review + 0 targeted）
  - 决策 13 在 Multi-PR 的 5 处级联清理（targeted re-review 模板 / gate 命名 / 2 轮修复 → 1 轮 + 自验 / Step 18 重写 / handbook L40-41）

完成本 issue 后：6 个 phase skill 全部达到 token economy 目标；Plugin 进入 v3.9.0（或对应版本）发布候选状态。

## Small issues

### 1. Discovery SKILL.md 主流程重写（D14 + D15 + D16 + D19）
**Type:** AFK
**What to build:** 把 `orchestrate-discovery/SKILL.md` Steps 1-2 从"Coordinator 自读 CLAUDE.md / SPEC / ADR / CONTEXT.md / agents.overrides.md / 近期 commits"重写为"按需并行派 code-explorer / complex-code-explorer / root-cause-analyst，Coordinator 只读浓缩报告 + 用户原话"。在 Steps 1-2 之前插入 Step 0「同步启动 grill-with-docs」声明 CONTEXT.md 与设计文档地位平等。在 Steps 3-9 之间插入「mockup 留时间空间」轻量说明。Steps 1-2 段同时引入 to-PRD synthesize fast-path 一句话。修改 `build/templates/voice-directive.md.tmpl` Anti-Sycophancy 段追加 Push twice 一行，跑 build apply 同步到所有 SKILL.md。修改 `discovery-design-document.md` L29 prototype snippet 例外类型精确化。
**Acceptance criteria:**
- [ ] `grep -E "Step 0|grill-with-docs" plugin/skills/orchestrate-discovery/SKILL.md` 命中含 Step 0 同步启动语句
- [ ] `grep -c "code-explorer\|complex-code-explorer\|root-cause-analyst" plugin/skills/orchestrate-discovery/SKILL.md` ≥ 3（Steps 1-2 派发清单）
- [ ] `grep "mockup" plugin/skills/orchestrate-discovery/SKILL.md` 命中"用户驱动 / 给时间"表述
- [ ] `grep "Push twice" plugin/build/templates/voice-directive.md.tmpl` 命中
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` 通过（模板与文件一致）
- [ ] `grep "state machine / reducer / schema / type shape" plugin/skills/orchestrate-discovery/references/discovery-design-document.md` 命中 prototype snippet 例外类型
**Blocked by:** Issue 001 (D2 死模板清理后的 reference 基线)

### 2. Discovery references 清理 + GitHub Issue 发布删除（D17）
**Type:** AFK
**What to build:** 删除 `design-review-angles.md` 顶部 Self-Read Protocol（≈10 行）。删除 `orchestrate-discovery/SKILL.md` L37 `Route Dispatch` 错位行（Discovery 是 route 终点非 router）。删除 `discovery-discussion.md` 末尾「grill-with-docs 的角色」段（已被 Pack 1 移到 SKILL.md Step 0）。合并 `issue-splitting.md` 中两套 issue body 模板（本地大 issue 文件 + GitHub Issue body）为一套：本地文件 = GH body + `## Design context refs` + `## Small issues` 两节。**完全删除 GitHub Issue 发布**——删除 issue-splitting.md 中 Step 12f（强制 `gh issue create` + 回写编号 + 模板 + 回写逻辑整段）。
**Acceptance criteria:**
- [ ] `grep -A2 "^## Self-Read Protocol" plugin/skills/orchestrate-discovery/references/design-review-angles.md` 不命中（顶部 Self-Read 已删）
- [ ] `grep "Route Dispatch" plugin/skills/orchestrate-discovery/SKILL.md` 不命中
- [ ] `grep "grill-with-docs 的角色" plugin/skills/orchestrate-discovery/references/discovery-discussion.md` 不命中
- [ ] `grep -E "gh issue create|GitHub Issue|发布到 GitHub" plugin/skills/orchestrate-discovery/references/issue-splitting.md` 不命中（GitHub Issue 发布步骤完全删除）
- [ ] `issue-splitting.md` 只剩一套 issue body 模板（本地大 issue 文件）
**Blocked by:** Pack 3.1（Step 0 已落地，再删 discovery-discussion.md 旧段；本 Pack 必须不与 3.1 同时改 SKILL.md/discovery-discussion.md）

### 3. Plan Writing 压缩 + budget 公式同步（D20）
**Type:** AFK
**What to build:** 删除 `plan-writer-dispatch.md` 顶部 Self-Read Protocol（≈10 行）+ `plan-review-dispatch.md` 顶部 Self-Read Protocol（≈10 行）。修改 `plan-gates.md` L46 区段：`budget.review_total = 3P + 12` → `2P + 6`，`budget.effort_total = (3P + 12) * 2` → `(2P + 6) * 2`，并把公式分配解释从 `3P + 12` 改写为「`2P`：每 Plan 2 次 review（Plan Review + Plan Implementation Review）；`+6`：Design Review 2 + Final Review 2 + Release Gate 1 + Multi-PR Integration Review 1」。删除"每 Plan 最多 2 次 repair re-review"表述。修改 `orchestrate-plan-writing/SKILL.md` L172 区段：`budget_total = 3P + 12` → `2P + 6`。
**Acceptance criteria:**
- [ ] `grep -A2 "^## Self-Read Protocol" plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md` 不命中
- [ ] `grep -A2 "^## Self-Read Protocol" plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` 不命中
- [ ] `grep "2P + 6" plugin/skills/orchestrate-plan-writing/references/plan-gates.md` 命中
- [ ] `grep "3P + 12" plugin/skills/orchestrate-plan-writing/` 不命中（公式已统一）
- [ ] `grep "2P + 6" plugin/skills/orchestrate-plan-writing/SKILL.md` 命中
**Blocked by:** Issue 002 (D13 公式确定)

### 4. Execution 阶段微调（D21）
**Type:** AFK
**What to build:** 修正 8 处 `execution-worker-handbook` 字符串引用：(1) `plugin/skills/orchestrate-execution/SKILL.md` Handbook 路径行 → `execution-worker-dispatch.md`；(2) `plugin/agents/pack-executor.md` Read handbook 步骤 → `execution-worker-dispatch.md`；(3) `plugin/agents/complex-pack-executor.md` 同上；(4) `plugin/build/templates/worker-loop.md.tmpl` Step 2 Read handbook → `execution-worker-dispatch.md`（critical runtime bug——template 注入 worker-prompts，Worker 实际 Read 此路径）；(5-8) `plugin/architecture-draft.md` 全部 4 处 `execution-worker-handbook` 字符串引用：L53 Read handbook 行 / L286 reference 清单中 `execution-worker-handbook（Worker 自读）` 整体删除（决策 2 已折回，无独立 handbook 文件）/ L299 文件清单同处理 / L338 Read handbook 步骤 → `execution-worker-dispatch.md`。删除 `execution-review-dispatch.md` 顶部 Self-Read Protocol（≈10 行）。修改 worker-loop.md.tmpl 后跑 `build.sh --apply` 同步到所有目标文件。
**Acceptance criteria:**
- [ ] `grep -r execution-worker-handbook plugin/` 整树 0 结果
- [ ] `grep "execution-worker-dispatch.md" plugin/agents/pack-executor.md` 命中
- [ ] `grep "execution-worker-dispatch.md" plugin/agents/complex-pack-executor.md` 命中
- [ ] `grep "execution-worker-dispatch.md" plugin/build/templates/worker-loop.md.tmpl` 命中
- [ ] `grep -A2 "^## Self-Read Protocol" plugin/skills/orchestrate-execution/references/execution-review-dispatch.md` 不命中
- [ ] `bash plugin/build/build.sh --check --plugin-dir plugin` 通过
**Blocked by:** Issue 002 D6（worker-loop.md.tmpl segment 5 重写已完成，避免 file ownership 冲突）

### 5. Final Review 阶段微调（D22）
**Type:** AFK
**What to build:** 删除 `final-review-angles.md` 顶部 Self-Read Protocol（≈11 行）。删除 `final-review-repair.md` Step 11 整段（从 `## Step 11：Targeted Re-Review` 标题到该 Step 末尾 Open Items 模板，约 122 行）。Step 12 三轮模型截断改为二段：「Round 1 修复 → Coordinator 自验 → 失败则 RCA → 仍失败 BLOCKED」；删除 "Round 3 的 Targeted Re-Review" 整段路由 + Analyst Resolution Routing 表中 `Targeted Re-Review` 行。L52 区段"Repair 返回后 Coordinator 默认自验收... 仅当满足 exception 条件...时派发 targeted Codex re-review"删除条件 + targeted 派发，只留 Coordinator 自验。`final-review-release-gate.md` Step 18 区段"修复后做 targeted release re-review"删除，改为 Coordinator 自验。`final-review-completion.md` Step 15 区段"复杂修复（派了 worker）→ 做 targeted re-review（Budget 消耗 1）"删除。`orchestrate-final-review/SKILL.md` L52 区段 preamble 删除"targeted re-review 使用 task --background --resume"句。`final-review-repair.md` Phase 软上限行重算为 ≤ 3（2 baseline + 0 targeted + 最多 1 release gate）。
**Acceptance criteria:**
- [ ] `grep -A2 "^## Self-Read Protocol" plugin/skills/orchestrate-final-review/references/final-review-angles.md` 不命中
- [ ] `grep "## Step 11" plugin/skills/orchestrate-final-review/references/final-review-repair.md` 不命中（整段已删）
- [ ] `grep -i "targeted re-review\|targeted-re-review" plugin/skills/orchestrate-final-review/` 整 final-review/ 0 结果（除 disposition table 共享 inject 由决策 1 处理外，本 phase 内代码已清）
- [ ] `grep "Phase 内部 review dispatch 软上限" plugin/skills/orchestrate-final-review/references/final-review-repair.md` 命中且数字为 `3` 或同义"2 baseline + 1 release gate"
- [ ] `grep "repair-once + RCA\|repair-once\|RCA escalation" plugin/skills/orchestrate-final-review/references/final-review-repair.md` 命中二段模型
**Blocked by:** Issue 002 D13（targeted re-review 机制全局删除已确认）

### 6. Multi-PR 阶段微调（D23）
**Type:** AFK
**What to build:** 在 `orchestrate-multi-pr-merge/SKILL.md` 顶部新增「Coordinator dispatch 通用步骤」一段（4 step 通用模板：写 merge-brief + 写 DISPATCH_ENVELOPE + 派发 + 处理返回）。删除 5 个 reference 末尾的 `## Coordinator 端最小职责` section（`merge-preparation.md` / `merge-conflict-discovery.md` / `merge-rca-investigation.md` / `merge-conflict-repair.md` / `merge-integration-review.md`），改为单行引用 SKILL.md 通用模板。`merge-integration-review.md` Step 18 重写：删除 targeted re-review prompt 模板 + DISPATCH_ENVELOPE 块（≈55 行）+ "gate 名使用 multi-pr-repair-<round>"行 + "最多 2 轮修复"改为"1 轮修复 + Coordinator 自验 → 失败 BLOCKED"。`merge-integration-review.md` 末尾追加「Phase 内部 review dispatch 软上限：1（1 integration review + 0 targeted re-review）」。`merge-completion.md` "不存在非阻塞项" 段（≈9 行）改为单行引用「清扫纪律同 Final Review Step 13（详见 `final-review-completion.md`）」+ 保留 multi-PR 独有的清扫来源列表。`merge-conflict-repair.md` Step 12a/12b worker dispatch prompt 中删除对 3 个 handbook 的引用（已被 Issue 001/002 删除）。
**Acceptance criteria:**
- [ ] `grep -c "Coordinator dispatch 通用步骤\|merge-brief 写作流程" plugin/skills/orchestrate-multi-pr-merge/SKILL.md` ≥ 1
- [ ] `grep "## Coordinator 端最小职责" plugin/skills/orchestrate-multi-pr-merge/references/` 整 references 0 结果或保留 1 行引用 SKILL.md
- [ ] `grep -i "targeted re-review\|targeted-re-review\|multi-pr-repair-" plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` 0 结果
- [ ] `grep "Phase 内部 review dispatch 软上限" plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` 命中且数字为 `1`
- [ ] `grep "multi-pr-explorer-handbook\|multi-pr-conflict-worker-handbook\|multi-pr-integration-review-handbook" plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md` 0 结果
**Blocked by:** Issue 001 D2（3 个 multi-pr handbook 删除）+ Issue 002 D13

### 7. Sub-agent 事实校验横切（D18）
**Type:** AFK
**What to build:** 在 `plugin/agents/code-explorer.md` / `complex-code-explorer.md` / `root-cause-analyst.md` 三个 agent 的 frontmatter description 末尾追加一句中文表述：返回的事实声明（行号 / 计数 / 存在性 / 引用关系）由 Coordinator 必须亲验，sub-agent 不承担 ground truth 责任。在 `orchestrate-discovery/SKILL.md` Steps 1-2（已被 Pack 3.1 重写）之后、Step 3 之前插入 **Step 1.5：Explorer 报告校验门控**：高置信度抽样 1 个事实验、中低置信度逐条 grep/Read 验、跨用户 skills/跨外部仓库的事实二次验、验证失败该声明剔除并重派 Explorer 或 Coordinator 亲查。在 `orchestrate-plan-writing/SKILL.md` / `orchestrate-execution/SKILL.md` / `orchestrate-multi-pr-merge/SKILL.md` 主流程合适位置加同义 Step 表述：plan-writer / pack-executor / root-cause-analyst 返回的事实声明也须 Coordinator 抽验。修改 `agent-return-handler.sh`：在生成 Coordinator NEXT 指令处追加一行 "⚠️ 写入交付物前必须校验本次返回的事实声明"。在 `plugin/architecture-draft.md` 新增「Sub-agent 信任边界」章节（明确 Coordinator 是事实的唯一 ground truth，sub-agent 是劳动力不是信源）。本 Pack 不引入新 hook 阻断（保持决策 9 hook 简化方向）。
**Acceptance criteria:**
- [ ] `grep "Coordinator 必须\|Coordinator must verify\|亲验" plugin/agents/code-explorer.md plugin/agents/complex-code-explorer.md plugin/agents/root-cause-analyst.md` 三个文件 description 均命中
- [ ] `grep -E "Step 1.5|Explorer 报告校验门控" plugin/skills/orchestrate-discovery/SKILL.md` 命中
- [ ] `grep -l "校验本次返回\|sub-agent 事实校验\|Coordinator 抽验" plugin/skills/orchestrate-plan-writing/SKILL.md plugin/skills/orchestrate-execution/SKILL.md plugin/skills/orchestrate-multi-pr-merge/SKILL.md` 三个文件均命中
- [ ] `grep "校验本次返回的事实声明" plugin/hooks/agent-return-handler.sh` 命中
- [ ] `grep "Sub-agent 信任边界" plugin/architecture-draft.md` 命中
- [ ] `bash plugin/hooks/tests/test_agent_return_handler.sh` 若存在仍通过
**Blocked by:** Pack 3.1（Discovery Steps 1-2 重写）+ Pack 3.3（Plan Writing SKILL.md 已稳定）+ Pack 3.4（Execution SKILL.md 已稳定）+ Pack 3.6（Multi-PR SKILL.md 已稳定）

## Blocked by

- **001 (Infrastructure)** — D14 Explorer 集成需要 D2 死模板清理后的 reference 基线；D18 Sub-agent 校验需要 agent frontmatter 瘦身（D11）已完成
- **002 (Contracts & State)** — D20 budget 公式落地需要 D13 公式已确定；D21 修 `worker-loop.md.tmpl` L12 必须在 D6 segment 5 重写（Issue 002 Pack）之后，避免 file ownership 冲突
