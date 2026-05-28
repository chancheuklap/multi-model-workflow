# Phase Skill 优化与压缩 Implementation Plan

**Goal:** 在 Issue 001（基础设施）+ Issue 002（合同 + 状态机清理）的干净基线上，对 6 个 phase skill 做最后一层压缩与精修，达成 v3.9.0 发布候选状态。
**Source design:** docs/orchestrate/design/2026-05-28-workflow-token-economy.md
**Source issue:** docs/orchestrate/issues/2026-05-28-workflow-token-economy/003-phase-skill-optimization.md
**Execution owner:** Orchestrate Workflow
**Blocked by:**
- **Issue 001 (Infrastructure)** — Pack 3.1 需要 D2 死模板清理后的 reference 基线；Pack 3.6 需要 D2 三个 multi-pr handbook 删除完成；Pack 3.7 需要 agent frontmatter 瘦身（D11）完成
- **Issue 002 (Contracts & State)** — Pack 3.3 budget 公式公式（D13）已确定；Pack 3.4 修改 `worker-loop.md.tmpl` 须在 D6 segment 5 重写之后；Pack 3.5 / 3.6 须在 D13（targeted re-review 全局删除）之后
**Architecture:**
- 6 个 SKILL.md 累计瘦身 30-40%（Discovery 主流程并行派 Explorer / grill-with-docs 升格 Step 0 / 外部精华 3 条 / GitHub Issue 发布完全删除 / mockup 留空间）
- 4 处 codex-reviewer Self-Read Protocol 死内容清零（design-review-angles / plan-review-dispatch / execution-review-dispatch / final-review-angles）
- 8 处 `execution-worker-handbook` 引用整树清零（含 worker-loop.md.tmpl L12 critical runtime bug）
- Final Review repair 三轮 → 二段（repair-once + RCA escalation），Phase 软上限 10 → 3
- Multi-PR Coordinator 端最小职责 5 处重复 → SKILL.md 顶部通用模板；Phase 软上限 = 1
- Sub-agent 事实校验机制写入 3 个 agent description + 4 个 SKILL.md + agent-return-handler.sh + architecture-draft 新章节

**Tech stack:** bash hook + Claude Code Plugin 锚点 build 系统（`plugin/build/build.sh`）+ Markdown reference + JSON state schema（本 plan 主要触碰 .md / .sh / .tmpl，不动 schema）
**Quality gate:** 进入 Plan Review 前必须通过过度设计 / 设计不足自审。

## File / Responsibility Map

**Modify:**
- `plugin/skills/orchestrate-discovery/SKILL.md` — Steps 1-2 重写为并行 Explorer 派发；Step 0 grill-with-docs；Step 1.5 Explorer 校验门控；mockup 留空间；删 L37 Route Dispatch
- `plugin/skills/orchestrate-discovery/references/design-review-angles.md` — 删除顶部 Self-Read Protocol
- `plugin/skills/orchestrate-discovery/references/discovery-discussion.md` — 删除末尾 grill-with-docs 角色段
- `plugin/skills/orchestrate-discovery/references/discovery-design-document.md` — L29 prototype snippet 例外类型精确化
- `plugin/skills/orchestrate-discovery/references/issue-splitting.md` — 合并双模板 + 完全删除 GitHub Issue 发布逻辑
- `plugin/skills/orchestrate-plan-writing/SKILL.md` — budget 公式 `3P + 12` → `2P + 6`；加 sub-agent 事实校验 Step
- `plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md` — 删除顶部 Self-Read Protocol
- `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` — 删除顶部 Self-Read Protocol
- `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` — budget 公式 + 分配文字同步
- `plugin/skills/orchestrate-execution/SKILL.md` — handbook 路径修正；加 sub-agent 事实校验 Step
- `plugin/skills/orchestrate-execution/references/execution-review-dispatch.md` — 删除顶部 Self-Read Protocol
- `plugin/agents/pack-executor.md` — handbook 路径修正（Read 步骤）
- `plugin/agents/complex-pack-executor.md` — handbook 路径修正
- `plugin/agents/code-explorer.md` — frontmatter description 追加事实校验声明
- `plugin/agents/complex-code-explorer.md` — frontmatter description 追加事实校验声明
- `plugin/agents/root-cause-analyst.md` — frontmatter description 追加事实校验声明
- `plugin/build/templates/voice-directive.md.tmpl` — Anti-Sycophancy 段追加 Push twice 规则
- `plugin/build/templates/worker-loop.md.tmpl` — L12 handbook 路径修正（critical runtime bug）
- `plugin/skills/orchestrate-final-review/SKILL.md` — preamble 删除 targeted re-review 句
- `plugin/skills/orchestrate-final-review/references/final-review-angles.md` — 删除顶部 Self-Read Protocol
- `plugin/skills/orchestrate-final-review/references/final-review-repair.md` — Step 11 整段删除；Step 12 二段化；软上限 10→3；L52 区段删 targeted dispatch
- `plugin/skills/orchestrate-final-review/references/final-review-release-gate.md` — Step 18 删 targeted release re-review
- `plugin/skills/orchestrate-final-review/references/final-review-completion.md` — Step 15 删 targeted re-review
- `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` — 顶部追加 Coordinator dispatch 通用步骤；加 sub-agent 事实校验 Step
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-preparation.md` — 删 Coordinator 端最小职责重复段
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-discovery.md` — 删 Coordinator 端最小职责重复段
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md` — 删 Coordinator 端最小职责重复段
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md` — 删 Coordinator 端最小职责重复段；删 3 个 handbook 引用
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` — Step 18 重写（删 targeted re-review）+ 软上限 1 + 删 Coordinator 端最小职责重复段
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-completion.md` — "不存在非阻塞项" 改为单行引用 Final Review Step 13
- `plugin/hooks/agent-return-handler.sh` — NEXT 指令追加 sub-agent 事实校验提醒
- `plugin/architecture-draft.md` — 删除 `execution-worker-handbook` 全部 4 处引用；新增「Sub-agent 信任边界」章节

**Test:**
- 复用 `plugin/hooks/tests/*.sh` 现有套件
- 复用 `plugin/scripts/tests/*.sh` 现有套件
- `bash plugin/scripts/run-all-tests.sh` 全量通过
- `bash plugin/scripts/verify-maturity.sh` 全量通过（含本 plan 引入的新检查项）

**Docs / rules / registry / migration / release gate:**
- `plugin/architecture-draft.md` — 同步 Sub-agent 信任边界 + 删除 handbook 引用
- `bash plugin/build/build.sh --apply --plugin-dir plugin`（每次改 `.tmpl` 模板后必跑）
- 无 release gate（本 plan 不涉及"用户可感知"功能变化，但 Pack 3.4 含 critical runtime bug 修复——见发布风险表）

## 发布风险和人工门禁

| 风险面 | Task Pack | Risk flag | 提前 review | Manual gate owner |
| --- | --- | --- | --- | --- |
| Worker 启动失败（handbook 路径不存在）| Pack 3.4 | runtime / production-risk | Plan Implementation Review 必须亲跑 worker-loop.md.tmpl build → 启动一次 Worker dispatch 验证 Read 路径不报错 | Coordinator |
| Discovery 主流程 Step 0/1.5 插入破坏既有 Compaction Recovery 顺序 | Pack 3.1 + Pack 3.7 | normal | Plan Implementation Review 跑 mock Discovery flow 一次 | Coordinator |
| `voice-directive.md.tmpl` 改动未同步到 6 个 SKILL.md | Pack 3.1 | normal | `bash plugin/build/build.sh --check --plugin-dir plugin` 通过；Plan Implementation Review 亲验 | Coordinator |
| GitHub Issue 发布删除后某 Coordinator 旧流程仍尝试 `gh issue create` | Pack 3.2 | normal | grep 整 plugin 无 `gh issue create` 在 Discovery 流程内残留 | Coordinator |
| Budget 公式落地遗漏（外部 README / architecture-draft 残留 `3P + 12`）| Pack 3.3 | normal | `grep -r "3P + 12" plugin/` 整 plan-writing/ 整树 0 结果（其他 plan 旧引用由 Issue 002 D13 闭合）| Coordinator |

---

### Task Pack 3.1: Discovery SKILL.md 主流程重写（D14 + D15 + D16 + D19）

**Issue:** `docs/orchestrate/issues/2026-05-28-workflow-token-economy/003-phase-skill-optimization.md` Small issue #1
**Goal behavior:** Discovery 阶段 Coordinator 不再自读大范围仓库；用户进 Discovery 时第一动作是「同步启动 grill-with-docs + 按需并行派 N 个 Explorer」；Discovery 阶段对 UI/UX 需求暂停给用户调用 mockup skill 留空间；外部 to-PRD synthesize fast-path 与 Push twice 规则落地。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-discovery/SKILL.md` — Steps 1-2 重写 + 新增 Step 0（grill-with-docs 同步启动）+ Steps 3-9 之间插入 mockup 留空间说明 + 删除 L37 区段 "Route Dispatch" 错位行
- Modify: `plugin/skills/orchestrate-discovery/references/discovery-design-document.md` — L29 区段 prototype snippet 例外类型精确化（追加"state machine / reducer / schema / type shape"枚举）
- Modify: `plugin/build/templates/voice-directive.md.tmpl` — Anti-Sycophancy 段尾部追加 Push twice 一行

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 14 / 15 / 16 / 19
- `plugin/skills/orchestrate-discovery/SKILL.md` 全文（理解 Steps 1-2 当前结构）
- `plugin/skills/orchestrate-discovery/references/discovery-discussion.md` 末尾（确认"grill-with-docs 的角色"段位置——本 Pack 不删，由 Pack 3.2 删）
- `CLAUDE.md` 构建系统章节（改 `.tmpl` 必须跑 `build.sh --apply`）
- `plugin/build/README.md` 锚点工作流

**Contract anchors:**
- Owner: Pack 3.1
- Provider: 重写后的 `orchestrate-discovery/SKILL.md` Steps 0/1-2/1.5 占位（实际 Step 1.5 由 Pack 3.7 注入）
- Consumer: orchestrate-workflow Entry Gate（Route 1 进入 discovery phase 时读 SKILL.md）+ 所有可能进 Discovery 的角色
- Verification: 锚点 build check + grep + 手动跑 mock Discovery

**Mockup specs:** N/A（plugin 内部重构，无 UI）

**Acceptance criteria:**
- [ ] `orchestrate-discovery/SKILL.md` Step 0「同步启动 grill-with-docs」存在；CONTEXT.md 与 design document 同等地位措辞落地
- [ ] Steps 1-2 改写为「Coordinator 按范围派 code-explorer / complex-code-explorer / root-cause-analyst；Coordinator 只读浓缩报告 + 用户原话」；不再含"Coordinator 自己读 CLAUDE.md / SPEC / ADR / CONTEXT.md / agents.overrides.md / 近期 commits"措辞
- [ ] Steps 3-9 之间存在一段「mockup 留空间」声明（暂停讨论 / 给用户调用 frontend-design/prototype/Impeccable / Coordinator 不催促）
- [ ] Steps 1-2 增加一句 to-PRD synthesize fast-path（"PRD/issue/完整上下文已覆盖 Problem/Solution/Acceptance → 跳过 Steps 3-6 一问一答 → 直接进入 Steps 7-9"）
- [ ] L37 区段 `Route Dispatch` 错位行已删除
- [ ] `discovery-design-document.md` L29 区段 prototype snippet 例外类型已精确化为"state machine / reducer / schema / type shape"
- [ ] `voice-directive.md.tmpl` Anti-Sycophancy 段含 "Push twice" 一行
- [ ] `bash plugin/build/build.sh --apply --plugin-dir plugin` 跑过；`bash plugin/build/build.sh --check --plugin-dir plugin` 通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过

**Verification commands:**
- `grep -E "^## Step 0|同步启动 grill-with-docs" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: 至少 1 行命中
- `grep -E "并行派|按需派 Explorer|code-explorer" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: ≥ 2 行命中
- `grep "Coordinator 自己读 CLAUDE.md" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: 0 命中
- `grep "mockup" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: 命中"用户驱动 / 给时间 / 暂停"任一表述
- `grep "synthesize\|fast-path\|跳过 Steps 3-6" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: ≥ 1 行命中
- `grep "Route Dispatch" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: 0 命中
- `grep "state machine / reducer / schema / type shape" plugin/skills/orchestrate-discovery/references/discovery-design-document.md` → Expected: 命中
- `grep "Push twice" plugin/build/templates/voice-directive.md.tmpl` → Expected: 命中
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全 suite PASS

**Commit boundary:** 1 个 atomic commit `feat(discovery): Steps 0/1-2 重写 + mockup 留空间 + Push twice + prototype snippet 类型`
**Risk flags:** normal（discovery 流程入口结构改动 + 模板 build 同步）
**发布风险:** 见 plan 顶部表（Compaction Recovery 顺序破坏风险）
**AFK / HITL:** AFK
**Dependencies:** Issue 001 完成（特别是 D2 死模板清理 + D11 agent frontmatter 瘦身——避免与本 Pack 改 SKILL.md 冲突）
**Out of scope:**
- 删除 `discovery-discussion.md` 末尾 grill-with-docs 角色段（→ Pack 3.2）
- 删除 `design-review-angles.md` Self-Read Protocol（→ Pack 3.2）
- 完全删除 GitHub Issue 发布（→ Pack 3.2）
- Step 1.5 Explorer 校验门控（→ Pack 3.7）

#### Implementation tasks
- [ ] Step 1: 写失败测试——`bash plugin/build/build.sh --check --plugin-dir plugin` 在改动前后均通过
  - 文件：`plugin/build/build.sh` 输出
  - Behavior：build check 验证 `.tmpl` 与目标文件锚点段内容一致
  - Key assertions：改 `.tmpl` 后必须 `--apply` 否则 `--check` 报错
- [ ] Step 2: 在 `orchestrate-discovery/SKILL.md` Steps 1-2 之前插入 Step 0
  - 文件：`plugin/skills/orchestrate-discovery/SKILL.md`
  - Position：当前 `## Step 1` 之前
  - 内容：
    ```markdown
    ## Step 0：同步启动 grill-with-docs

    在第一轮用户对话前调用 `Skill({ skill: "grill-with-docs" })`，由该 skill 全程负责 CONTEXT.md 维护。CONTEXT.md 与 design document 是 Discovery 阶段的**双交付物**，地位等同。CONTEXT.md 路径写入 Scope Contract 作为 Discovery 权威文档之一（与 design path 并列）。
    ```
- [ ] Step 3: 重写 `orchestrate-discovery/SKILL.md` Steps 1-2 为并行 Explorer 派发
  - 文件：`plugin/skills/orchestrate-discovery/SKILL.md`
  - 旧文本：（含"Coordinator 自己读 CLAUDE.md / SPEC / ADR / CONTEXT.md / agents.overrides.md / 近期 commits"措辞的段）
  - 新文本：
    ```markdown
    ## Steps 1-2：仓库范围探查 + 并行 Explorer 派发

    Coordinator 不再自己读大范围仓库；按问题范围**并行派 N 个 Explorer**：
    - 窄范围（单模块 / 单文件链）→ `code-explorer`
    - 多模块 / 历史行为 / 架构摩擦 → `complex-code-explorer`
    - 已知根因不清且涉及 bug → `root-cause-analyst`

    模糊设计意图触发**多 Explorer 并行**调研（5 个并行是常见模式）。Coordinator 只读 Explorer 返回的浓缩报告 + 用户原话；不主动 grep 大范围仓库。

    **to-PRD synthesize fast-path**：若用户传入的 PRD / issue / 完整上下文已覆盖 Problem / Solution / Acceptance，跳过 Steps 3-6 一问一答 fast-path，直接进入 Steps 7-9 起草设计文档，最后让用户审稿。
    ```
- [ ] Step 4: 在 `orchestrate-discovery/SKILL.md` 插入「mockup 留空间」段
  - Position：紧跟 Step 0（grill-with-docs，本 Pack Step 2 已落地）之后、Steps 1-2（本 Pack Step 3 已重写）之前；或如果 SKILL.md 已含 `## Steps 3-6` 标题段，则放在 Steps 3-6 标题之前。先 grep 定位：`grep -n "^## Step 0\|^## Steps 1-2\|^## Steps 3-6" plugin/skills/orchestrate-discovery/SKILL.md` 取锚点；选 Step 0 之后第一个出现的 `## Step` 标题之前的位置插入。约束：必须在 Step 0 之后、所有 Step N 主流程之前（作为整 Discovery phase 适用的横切声明）。
  - 内容：
    ```markdown
    ### Mockup 生成留空间

    当设计涉及 UI/UX 且用户表达要生成 mockup 时，Coordinator 暂停当前 Step，给用户调用 `frontend-design` / `prototype` / 其他用户选用的 UI 设计 skill 留出完整时间和空间。Mockup 的生成方式、迭代节奏由用户主动驱动，Coordinator 不催促、不并行启动后续 Step、不替用户决定何时定稿。Mockup 与设计文档地位平等且迭代可能交叉——用户切回设计讨论 Step 时，按当前 Step 继续。
    ```
- [ ] Step 5: 删除 `orchestrate-discovery/SKILL.md` 中 `Route Dispatch` 行
  - 文件：`plugin/skills/orchestrate-discovery/SKILL.md`
  - 旧文本（在 preamble 段内）：`**Route Dispatch**：根据 Entry Gate 判定的 route 选择对应 phase skill。`
  - 新文本：（删除整行）
- [ ] Step 6: 修改 `discovery-design-document.md` L29 区段 prototype snippet 例外类型
  - 文件：`plugin/skills/orchestrate-discovery/references/discovery-design-document.md`
  - 旧文本：`不写具体 file path 或 code snippet（prototype snippet 例外）`
  - 新文本：`不写具体 file path 或 code snippet（prototype snippet 例外——例外类型仅限：state machine / reducer / schema / type shape）`
- [ ] Step 7: 修改 `voice-directive.md.tmpl` Anti-Sycophancy 段追加 Push twice
  - 文件：`plugin/build/templates/voice-directive.md.tmpl`
  - Position：Anti-Sycophancy 段末（"立场+证据+质疑最强版本" 一行之后）
  - 追加：
    ```
    Push twice：第一个回答默认是抛光过的，至少追问一轮才相信。
    ```
- [ ] Step 8: 跑 build apply 同步模板到所有目标文件
  - Run: `bash plugin/build/build.sh --apply --plugin-dir plugin` → Expected: exit 0，stderr 无 error
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- [ ] Step 9: 验证所有 acceptance verification commands 通过
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: 全 suite PASS
- [ ] Step 10: Suggested commit boundary
  - Message: `feat(discovery): Steps 0/1-2 重写 + mockup 留空间 + Push twice + prototype snippet 类型`

---

### Task Pack 3.2: Discovery references 清理 + GitHub Issue 发布完全删除（D17）

**Issue:** Small issue #2
**Goal behavior:** Discovery 阶段不再向 GitHub 推送 Issue；本地大 issue 文件是 Discovery 唯一产出；4 处 Discovery references 死内容（design-review-angles Self-Read / discovery-discussion 末尾段 / issue-splitting 双模板 / SKILL.md L37 已由 Pack 3.1 处理）全部清零。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-discovery/references/design-review-angles.md` — 删除顶部 `## Self-Read Protocol` 整段（约 10 行）
- Modify: `plugin/skills/orchestrate-discovery/references/discovery-discussion.md` — 删除末尾「grill-with-docs 的角色」段
- Modify: `plugin/skills/orchestrate-discovery/references/issue-splitting.md` — 合并本地大 issue 文件 + GH body 双模板为一套；删除 Step 12f 所有 `gh issue create` / 回写编号 / 模板 / 回写逻辑

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 17
- 三个目标 reference 文件全文
- Pack 3.1 commit（确认 SKILL.md Step 0 已落地后再删 discovery-discussion 末尾段）

**Contract anchors:**
- Owner: Pack 3.2
- Provider: 简化后的 issue-splitting.md（单模板 + 无 GH 发布）
- Consumer: orchestrate-discovery Step 12 大 issue 拆分流程
- Verification: grep 0 残留 GitHub Issue 发布字符串 + Self-Read 死内容清零

**Mockup specs:** N/A

**Acceptance criteria:**
- [ ] `design-review-angles.md` 顶部无 `## Self-Read Protocol` 段；按"流程位置"路标 blockquote 之后直接进入 `## Codex Dispatch 公共部分`
- [ ] `discovery-discussion.md` 末尾无 `**grill-with-docs 的角色**` 段
- [ ] `issue-splitting.md` 整文只剩一套 issue body 模板（本地大 issue 文件 = GH body + `## Design context refs` + `## Small issues` 两节）
- [ ] `issue-splitting.md` 无 `gh issue create` / `GitHub Issue 发布` / `回写编号` / Step 12f 中所有 GH 发布相关流程
- [ ] `verify-maturity.sh` 路标完整性检查通过（design-review-angles 顶部仍有"流程位置"blockquote 作为路标）

**Verification commands:**
- `grep -c "^## Self-Read Protocol" plugin/skills/orchestrate-discovery/references/design-review-angles.md` → Expected: 0
- `grep "grill-with-docs 的角色" plugin/skills/orchestrate-discovery/references/discovery-discussion.md` → Expected: 0 命中
- `grep -E "gh issue create|GitHub Issue 发布|回写编号" plugin/skills/orchestrate-discovery/references/issue-splitting.md` → Expected: 0 命中
- `grep -c "^### .* GitHub Issue" plugin/skills/orchestrate-discovery/references/issue-splitting.md` → Expected: 0（无独立 GH body 章节）
- `head -5 plugin/skills/orchestrate-discovery/references/design-review-angles.md` → Expected: 顶部含 `> **流程位置**` 路标 blockquote（路标未误删）
- `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0

**Commit boundary:** 1 个 atomic commit `chore(discovery): 删除 4 处死内容 + GitHub Issue 发布完全删除`
**Risk flags:** normal
**发布风险:** 见 plan 顶部表（GH Issue 发布旧流程残留风险）
**AFK / HITL:** AFK
**Dependencies:** Pack 3.1（先有 Step 0 才能删 discovery-discussion 末尾段）
**Out of scope:** Step 1.5（→ Pack 3.7）；SKILL.md 主流程（→ Pack 3.1）

#### Implementation tasks
- [ ] Step 1: 删除 `design-review-angles.md` 顶部 Self-Read Protocol 整段
  - 文件：`plugin/skills/orchestrate-discovery/references/design-review-angles.md`
  - 旧文本（含路标 blockquote 之后到 `## Codex Dispatch 公共部分` 之前）：
    ```markdown
    ## Self-Read Protocol

    你是 codex-reviewer（执行 Design Review）。启动时按以下顺序执行：

    1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`gate`、feature slug。
    2. 读 `<project_root>/CLAUDE.md` 和 `<project_root>/CONTEXT.md`（若存在）获取项目基线、不变量、contract wall。
    3. 读 `docs/orchestrate/design/<slug>.md` 获取设计文档全文。
    4. 读本文件（你正在读的这份手册），理解 Review Angles 与 Return Contract 格式。
    5. 按两个 Baseline Review angle 独立验证，遵守 Pre-emit Verification Gate，输出 findings。
    ```
  - 新文本：（整段删除；保留路标 blockquote 之后直接进 `## Codex Dispatch 公共部分`）
- [ ] Step 2: 删除 `discovery-discussion.md` 末尾「grill-with-docs 的角色」段
  - 文件：`plugin/skills/orchestrate-discovery/references/discovery-discussion.md`
  - 旧文本：
    ```markdown
    **grill-with-docs 的角色**：不是辅助工具——是 Domain Alignment 的核心执行方式。始终用其方法论挑战术语、交叉验证代码、更新 CONTEXT.md。
    ```
  - 新文本：（整段删除）
- [ ] Step 3: 合并 `issue-splitting.md` 双模板 + 删除 GitHub Issue 发布
  - 文件：`plugin/skills/orchestrate-discovery/references/issue-splitting.md`
  - 改动：找到 Step 12f / GitHub Issue body 模板 / `gh issue create` / 回写编号逻辑，整段删除；保留单一本地大 issue 文件模板（结构：GH body 部分 + `## Design context refs` 节 + `## Small issues` 节）
- [ ] Step 4: 跑 verification
  - Run: `grep -c "^## Self-Read Protocol" plugin/skills/orchestrate-discovery/references/design-review-angles.md` → Expected: 0
  - Run: `grep "grill-with-docs 的角色" plugin/skills/orchestrate-discovery/references/discovery-discussion.md` → Expected: 不命中（exit 1 from grep）
  - Run: `grep -E "gh issue create|GitHub Issue 发布" plugin/skills/orchestrate-discovery/references/issue-splitting.md` → Expected: 不命中
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0
- [ ] Step 5: Suggested commit
  - Message: `chore(discovery): 删除 4 处死内容 + GitHub Issue 发布完全删除`

---

### Task Pack 3.3: Plan Writing 压缩 + budget 公式同步（D20）

**Issue:** Small issue #3
**Goal behavior:** plan-writer / Plan-Review dispatch reference 顶部死 Self-Read Protocol 清零；验证 budget 公式 `2P + 6` 已由 Issue 002 Pack 2.2 落地（本 Pack 不重复编辑，仅验证 + 补充分配文字细节如需要）。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md` — 删除顶部 `## Self-Read Protocol` 整段（约 10 行）
- Modify: `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` — 删除顶部 `## Self-Read Protocol` 整段（约 10 行）
- Verify: `plugin/skills/orchestrate-plan-writing/references/plan-gates.md` — 确认 budget 公式 `2P + 6` 已由 Issue 002 Pack 2.2 落地；如分配文字细节不足（缺少决策 20 权威表述的完整分配解释），补充完善
- Verify: `plugin/skills/orchestrate-plan-writing/SKILL.md` — 确认 `budget_total = 2P + 6` 已由 Issue 002 Pack 2.2 落地

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 20（公式分配权威表述）
- Issue 002 D13 commit / plan（确认 targeted re-review 全局删除已落地）
- 4 个目标文件全文

**Contract anchors:**
- Owner: Pack 3.3（Self-Read Protocol 清理）；budget 公式由 Issue 002 Pack 2.2 负责（本 Pack 仅验证 + 补充分配细节）
- Provider: 公式权威表述（`plan-gates.md` 即新唯一源，Issue 002 Pack 2.2 已落地基础公式）
- Consumer: `state.sh budget initialize` / `track-review-budget.sh` / `gate-codex-review.sh`（budget 余量检查）/ 所有 phase 内 review dispatch
- Verification: grep `3P + 12` 在 plan-writing/ 整树清零；grep `2P + 6` 命中 2 处权威位置

**Mockup specs:** N/A

**Acceptance criteria:**
- [ ] `plan-writer-dispatch.md` 顶部无 `## Self-Read Protocol` 段
- [ ] `plan-review-dispatch.md` 顶部无 `## Self-Read Protocol` 段
- [ ] `plan-gates.md` budget 公式行改为：`budget.review_total = 2P + 6`、`budget.effort_total = (2P + 6) * 2`
- [ ] `plan-gates.md` 公式分配解释改为决策 20 权威表述（每 Plan 2 次 review + Design Review 2 + Final Review 2 + Release Gate 1 + Multi-PR Integration Review 1）
- [ ] `plan-gates.md` 不含"每 Plan 最多 2 次 repair re-review"或同义表述（targeted re-review 已删，修复由 Coordinator 自验闭合）
- [ ] `orchestrate-plan-writing/SKILL.md` 公式数字行改为 `2P + 6`
- [ ] plan-writing/ 整树无 `3P + 12` / `3P+12` 字符串残留

**Verification commands:**
- `grep -c "^## Self-Read Protocol" plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md` → Expected: 0
- `grep -c "^## Self-Read Protocol" plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md` → Expected: 0
- `grep "2P + 6\|2P+6" plugin/skills/orchestrate-plan-writing/references/plan-gates.md` → Expected: ≥ 2 行命中（公式行 + 分配解释）
- `grep "2P + 6\|2P+6" plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: ≥ 1 行命中
- `grep -r "3P + 12\|3P+12" plugin/skills/orchestrate-plan-writing/` → Expected: 0 命中
- `grep -i "每 Plan 最多 2 次 repair re-review\|repair re-review 余量" plugin/skills/orchestrate-plan-writing/references/plan-gates.md` → Expected: 0 命中
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS

**Commit boundary:** 1 个 atomic commit `chore(plan-writing): 删 Self-Read 死内容 + budget 公式 3P+12 → 2P+6`
**Risk flags:** normal
**发布风险:** 见 plan 顶部表（外部 README / architecture-draft 残留旧公式风险——本 Pack 仅闭合 plan-writing/ 内；其他位置由 Issue 002 D13 闭合）
**AFK / HITL:** AFK
**Dependencies:** Issue 002 D13（targeted re-review 机制全局删除前提）；Pack 3.3 不与其他 Pack 共改 plan-writing/ 文件
**Out of scope:** dispatch-envelope-v1.json schema / state.sh init 中字段（属 Issue 002）；Final Review / Multi-PR 软上限（→ Pack 3.5 / 3.6）

#### Implementation tasks
- [ ] Step 1: 删除 `plan-writer-dispatch.md` 顶部 Self-Read Protocol
  - 文件：`plugin/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md`
  - 旧文本：从 `## Self-Read Protocol` 标题到下一个 `##` 之前
  - 新文本：（整段删除；保留顶部"流程位置"blockquote 作为路标）
- [ ] Step 2: 删除 `plan-review-dispatch.md` 顶部 Self-Read Protocol
  - 文件：`plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
  - 同 Step 1 模式
- [ ] Step 3: 验证 `plan-gates.md` budget 公式已由 Issue 002 Pack 2.2 落地 + 补充分配细节
  - 文件：`plugin/skills/orchestrate-plan-writing/references/plan-gates.md`
  - 验证：`grep "2P + 6" plugin/skills/orchestrate-plan-writing/references/plan-gates.md` → Expected: ≥ 1 行命中（Issue 002 Pack 2.2 已改）
  - 如 Pack 2.2 的分配文字仅写了简要说明，补充为决策 20 权威表述（完整分配：`2P` = 每 Plan 2 review + `+6` = Design Review 2 + Final Review 2 + Release Gate 1 + Multi-PR Integration Review 1 + "修复后由 Coordinator 自验闭合"）
  - 如已完整：跳过本步
- [ ] Step 4: 验证 `orchestrate-plan-writing/SKILL.md` 公式已由 Issue 002 Pack 2.2 落地
  - 文件：`plugin/skills/orchestrate-plan-writing/SKILL.md`
  - 验证：`grep "2P + 6" plugin/skills/orchestrate-plan-writing/SKILL.md` → Expected: ≥ 1 行命中（Issue 002 Pack 2.2 已改）
  - 如命中：跳过本步
- [ ] Step 5: 跑 verification
  - Run: `grep -r "3P + 12\|3P+12" plugin/skills/orchestrate-plan-writing/` → Expected: 0 命中
  - Run: `grep "2P + 6" plugin/skills/orchestrate-plan-writing/references/plan-gates.md` → Expected: ≥ 2 行
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
- [ ] Step 6: Suggested commit
  - Message: `chore(plan-writing): 删 Self-Read 死内容 + budget 公式 3P+12 → 2P+6`

---

### Task Pack 3.4: Execution 阶段微调（D21 + Alignment Review C1 完整版）

**Issue:** Small issue #4
**Goal behavior:** Worker 启动 Step 2 `Read execution-worker-handbook.md` runtime bug 修复——`plugin/` 整树无 `execution-worker-handbook` 字符串残留；execution-review-dispatch.md 顶部死 Self-Read Protocol 清零。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-execution/SKILL.md` — Handbook 路径行（约 L202 区段）改为 `execution-worker-dispatch.md`
- Modify: `plugin/agents/pack-executor.md` — Read handbook 步骤路径修正
- Modify: `plugin/agents/complex-pack-executor.md` — 同上
- Modify: `plugin/build/templates/worker-loop.md.tmpl` — Step 2 Read handbook 路径修正（critical runtime bug）
- Modify: `plugin/architecture-draft.md` — 2 处 `execution-worker-handbook` 引用：L53 区段 `读 execution-worker-handbook` → `读 execution-worker-dispatch` / L338 区段 `Read execution-worker-handbook.md` → `Read execution-worker-dispatch.md`（L286 / L299 两处已由 Issue 001 Pack 5 删除，本 Pack 不重复处理）
- Modify: `plugin/skills/orchestrate-execution/references/execution-review-dispatch.md` — 删除顶部 `## Self-Read Protocol` 整段
- Build apply: 跑 `bash plugin/build/build.sh --apply --plugin-dir plugin` 同步 worker-loop.md.tmpl 改动到所有目标文件

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 21（含 8 处引用表）
- Issue 002 D6 完成态（worker-loop.md.tmpl segment 5 重写已落地，可改 L12 而无 file ownership 冲突）
- 6 个目标文件全文 + `CLAUDE.md` 构建系统章节

**Contract anchors:**
- Owner: Pack 3.4
- Provider: 整树清零的 handbook 引用集；`execution-worker-dispatch.md`（已存在，无需创建）作为 Worker 启动 Step 2 的唯一权威源
- Consumer: 任何 dispatch 的 pack-executor / complex-pack-executor Worker（启动时 Read 此路径）
- Verification: `grep -r execution-worker-handbook plugin/` 0 命中

**Mockup specs:** N/A

**Acceptance criteria:**
- [ ] `grep -r execution-worker-handbook plugin/` 整树 0 结果
- [ ] `plugin/skills/orchestrate-execution/SKILL.md` Handbook 路径行含 `execution-worker-dispatch.md`，不含 `execution-worker-handbook.md`
- [ ] `plugin/agents/pack-executor.md` Read handbook 步骤路径为 `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-dispatch.md`
- [ ] `plugin/agents/complex-pack-executor.md` 同上
- [ ] `plugin/build/templates/worker-loop.md.tmpl` Step 2 Read handbook 路径为 `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-dispatch.md`
- [ ] `plugin/architecture-draft.md` L53 / L338 区段 Read handbook 步骤改为 `execution-worker-dispatch.md`（L286 / L299 已由 Issue 001 Pack 5 处理）
- [ ] `execution-review-dispatch.md` 顶部无 `## Self-Read Protocol` 段
- [ ] `bash plugin/build/build.sh --apply --plugin-dir plugin` 跑过；`--check` 通过
- [ ] `bash plugin/scripts/run-all-tests.sh` 通过
- [ ] `bash plugin/scripts/verify-maturity.sh` 通过

**Verification commands:**
- `grep -r execution-worker-handbook plugin/` → Expected: 0 命中
- `grep "execution-worker-dispatch.md" plugin/agents/pack-executor.md plugin/agents/complex-pack-executor.md plugin/build/templates/worker-loop.md.tmpl` → Expected: 3 个文件均命中
- `grep -A2 "^## Self-Read Protocol" plugin/skills/orchestrate-execution/references/execution-review-dispatch.md` → Expected: 0 命中
- `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
- `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0

**Commit boundary:** 1 个 atomic commit `fix(execution): 6 处 handbook 路径修正 + 删 Self-Read 死内容 (critical runtime bug)`
**Risk flags:** runtime / production-risk（worker-loop.md.tmpl 注入 worker-prompts，Worker 实际 Read 此路径——本 Pack 修复 runtime bug）
**发布风险:** 见 plan 顶部表（Worker 启动失败风险）
**AFK / HITL:** AFK（Plan Implementation Review 必须亲跑一次 Worker dispatch 验证 Read 路径不报错）
**Dependencies:** Issue 002 D6（worker-loop.md.tmpl segment 5 重写已完成）；本 Pack 不与 Pack 3.1（discovery）/ Pack 3.5（final review）/ Pack 3.6（multi-pr）共改文件
**Out of scope:** segment 5 fallback 路径双路径（属 Issue 002 D6）；sub-agent 事实校验 Step（→ Pack 3.7）

#### Implementation tasks
- [ ] Step 1: 修正 `plugin/skills/orchestrate-execution/SKILL.md` Handbook 路径行
  - 文件：`plugin/skills/orchestrate-execution/SKILL.md`
  - 旧文本（约 L202 区段）：`Handbook：<$(pwd)/plugin/skills/orchestrate-execution/references/execution-worker-handbook.md>`
  - 新文本：`Handbook：<$(pwd)/plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md>`
- [ ] Step 2: 修正 `pack-executor.md` Read handbook 步骤
  - 文件：`plugin/agents/pack-executor.md`
  - 旧文本：`Read `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-handbook.md``
  - 新文本：`Read `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-dispatch.md``
- [ ] Step 3: 修正 `complex-pack-executor.md` Read handbook 步骤
  - 文件：`plugin/agents/complex-pack-executor.md`
  - 同 Step 2 模式
- [ ] Step 4: 修正 `worker-loop.md.tmpl` Step 2 Read handbook 路径（critical runtime bug）
  - 文件：`plugin/build/templates/worker-loop.md.tmpl`
  - 旧文本：`Read `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-handbook.md``
  - 新文本：`Read `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-dispatch.md``
- [ ] Step 5: 修正 `architecture-draft.md` 2 处 handbook 引用（L286 / L299 已由 Issue 001 Pack 5 处理）
  - 文件：`plugin/architecture-draft.md`
  - L53 区段（"5 步严格启动序列"段）：`读 execution-worker-handbook` → `读 execution-worker-dispatch`
  - L338 区段（Read handbook 步骤）：`Read execution-worker-handbook.md` → `Read execution-worker-dispatch.md`
- [ ] Step 6: 删除 `execution-review-dispatch.md` 顶部 Self-Read Protocol
  - 文件：`plugin/skills/orchestrate-execution/references/execution-review-dispatch.md`
  - 旧文本：`## Self-Read Protocol` 标题到下一个 `##` 之前的整段
  - 新文本：（整段删除；保留顶部"流程位置"blockquote）
- [ ] Step 7: 跑 build apply 同步 worker-loop.md.tmpl 改动到所有目标文件
  - Run: `bash plugin/build/build.sh --apply --plugin-dir plugin` → Expected: exit 0
  - Run: `bash plugin/build/build.sh --check --plugin-dir plugin` → Expected: exit 0
- [ ] Step 8: 跑 verification
  - Run: `grep -r execution-worker-handbook plugin/` → Expected: 0 命中
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0
- [ ] Step 9: Suggested commit
  - Message: `fix(execution): 6 处 handbook 路径修正 + 删 Self-Read 死内容 (critical runtime bug)`

---

### Task Pack 3.5: Final Review 阶段微调（D22）

**Issue:** Small issue #5
**Goal behavior:** Final Review 阶段 targeted re-review 机制残留代码 / 文本全部清零；repair 三轮模型截断为二段（Round 1 修复 → Coordinator 自验 → 失败则 RCA → 仍失败 BLOCKED）；Phase 内部 review dispatch 软上限从 10 降为 3（2 baseline + 0 targeted + 最多 1 release gate）；final-review-angles.md 顶部死 Self-Read Protocol 清零。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-final-review/references/final-review-angles.md` — 删除顶部 `## Self-Read Protocol` 整段（约 11 行）
- Modify: `plugin/skills/orchestrate-final-review/references/final-review-repair.md` — 删除 Step 11 整段（约 122 行）+ Step 12 三轮截断改为二段 + L52 区段删 targeted dispatch + 软上限 10 → 3
- Modify: `plugin/skills/orchestrate-final-review/references/final-review-release-gate.md` — Step 18 区段删 targeted release re-review 路由
- Modify: `plugin/skills/orchestrate-final-review/references/final-review-completion.md` — Step 15 区段删 "复杂修复 → targeted re-review (Budget 消耗 1)"
- Modify: `plugin/skills/orchestrate-final-review/SKILL.md` — preamble L52 区段删除 "targeted re-review 使用 task --background --resume" 句

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 22（含 7 项级联清理表）
- Issue 002 D13 完成态（targeted re-review 全局机制删除前提）
- 5 个目标文件全文（特别是 `final-review-repair.md` Step 11/12 完整段）

**Contract anchors:**
- Owner: Pack 3.5
- Provider: 二段 repair 模型（repair-once + RCA escalation）作为 Final Review 唯一 repair 路径
- Consumer: Coordinator 在 Final Review disposition → repair 路由时；`gate-codex-review.sh` 不再校验 targeted re-review --resume（属 Issue 002 D13）
- Verification: grep 整 final-review/ 0 `targeted re-review` 残留（共享 inject 由 D1 处理，本 Pack 仅 final-review/ 内）

**Mockup specs:** N/A

**Acceptance criteria:**
- [ ] `final-review-angles.md` 顶部无 `## Self-Read Protocol` 段
- [ ] `final-review-repair.md` 无 `## Step 11` 章节标题（整段已删）
- [ ] `final-review-repair.md` Step 12 改写为二段模型（repair-once + RCA escalation）；不含 "Round 3" / "Targeted Re-Review 消耗 Round 3 的 review budget" / "Analyst Resolution Routing 表中 Targeted Re-Review 行"
- [ ] `final-review-repair.md` Step 12 内 `Agent({subagent_type: "root-cause-analyst", ...})` dispatch prompt 块保留（仅内部措辞从"两轮上下文"改为"Round 1 上下文"）
- [ ] `final-review-repair.md` L52 区段不含 "targeted Codex re-review" / "exception 条件" / "exception_code" 派发逻辑
- [ ] `final-review-repair.md` Phase 软上限行为 `≤ 3（2 baseline + 0 targeted + 最多 1 release gate）`
- [ ] `final-review-release-gate.md` Step 18 区段不含 "修复后做 targeted release re-review"
- [ ] `final-review-completion.md` Step 15 区段不含 "复杂修复 → targeted re-review (Budget 消耗 1)"
- [ ] `orchestrate-final-review/SKILL.md` preamble 不含 "targeted re-review 使用 task --background --resume"
- [ ] `grep -ri "targeted re-review\|targeted-re-review" plugin/skills/orchestrate-final-review/` 0 结果（除共享 inject 已由 Issue 001 D1 处理）

**Verification commands:**
- `grep -c "^## Self-Read Protocol" plugin/skills/orchestrate-final-review/references/final-review-angles.md` → Expected: 0
- `grep -c "^## Step 11" plugin/skills/orchestrate-final-review/references/final-review-repair.md` → Expected: 0
- `grep -i "targeted re-review\|targeted-re-review" plugin/skills/orchestrate-final-review/` → Expected: 0 命中
- `grep -E "repair-once|RCA escalation|Round 1 修复 → Coordinator 自验" plugin/skills/orchestrate-final-review/references/final-review-repair.md` → Expected: ≥ 1 命中
- `grep 'subagent_type: "root-cause-analyst"' plugin/skills/orchestrate-final-review/references/final-review-repair.md` → Expected: ≥ 1 命中（dispatch prompt 块保留）
- `grep "Phase 内部 review dispatch 软上限" plugin/skills/orchestrate-final-review/references/final-review-repair.md` → Expected: 命中且含 `3` 或 "2 baseline + 1 release gate"
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS

**Commit boundary:** 1 个 atomic commit `chore(final-review): 删 Self-Read + Step 11 整段 + Step 12 三轮→二段 + 软上限 10→3`
**Risk flags:** normal
**发布风险:** 无（本 Pack 不涉及发布风险面；属 Coordinator 内部流程清理）
**AFK / HITL:** AFK
**Dependencies:** Issue 002 D13（targeted re-review 全局删除前提）
**Out of scope:** review-dispatch / repair-routing / disposition-table 共享 inject 在 final-review/ 文件中的处理（属 Issue 001 D1）；sub-agent 事实校验 Step（→ Pack 3.7）

#### Implementation tasks
- [ ] Step 1: 删除 `final-review-angles.md` 顶部 Self-Read Protocol
  - 文件：`plugin/skills/orchestrate-final-review/references/final-review-angles.md`
  - 旧文本：从 `## Self-Read Protocol` 标题到下一个 `##` 之前的整段
  - 新文本：（整段删除）
- [ ] Step 2: 删除 `final-review-repair.md` Step 11 整段
  - 文件：`plugin/skills/orchestrate-final-review/references/final-review-repair.md`
  - 旧文本：从 `## Step 11：Targeted Re-Review` 标题到下一个 `## Step 12` 之前的整段（约 122 行，含 `<!-- BEGIN: review-dispatch -->` ... `Open Items` 模板）
  - 新文本：（整段删除；Step 10 之后直接进入 Step 12）
- [ ] Step 3: 改写 `final-review-repair.md` Step 12 为二段模型（surgical edits，保留 RCA dispatch prompt 块）
  - 文件：`plugin/skills/orchestrate-final-review/references/final-review-repair.md`
  - 改动策略：**不整段删 Step 12**；做 4 处精确替换，保留 `Agent({subagent_type: "root-cause-analyst", ...})` dispatch prompt 块及其前导标题 `**Root-Cause-Analyst 截断调度**：` 不动
  - **子改动 3a**：替换 Step 12 开头三轮模型表
    - 旧文本：
      ```markdown
      ## Step 12：修复截断

      每个 gap 最多 3 个 repair round（2 个 Worker/Coordinator round + 1 个 root-cause-analyst round）。

      | Round | 动作 |
      | --- | --- |
      | Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
      | Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
      | Round 3（截断） | 仍 needs repair → **截断 Worker 循环**，新建 `root-cause-analyst` |
      ```
    - 新文本：
      ```markdown
      ## Step 12：修复截断（repair-once + RCA escalation）

      每个 gap 最多 1 个 repair round + 1 个 RCA escalation。

      | 阶段 | 动作 |
      | --- | --- |
      | Round 1 | 路径 B（SendMessage Worker）修复 → Coordinator 自验（grep / Read + verification commands 对照 acceptance criteria） |
      | RCA escalation | Coordinator 自验仍 needs repair → 新建 `root-cause-analyst` 调度（见下方 dispatch 模板） |
      | BLOCKED | Analyst Resolution 仍 `unable to determine` / `root cause in design/plan` 已写回上游 → 报告用户 |
      ```
  - **子改动 3b**：修改 RCA dispatch prompt 内部"两轮上下文"措辞为"一轮上下文"（保留 `Agent({...})` 块结构不动）
    - 旧文本（dispatch prompt 内）：
      ```
      ## 前两轮上下文
          - Round 1 accepted findings: <paste>
          - Round 1 修复内容: <paste>
          - Round 2 accepted findings: <paste>
          - Round 2 修复内容: <paste>
          - Git diff scope: <paste>
      ```
    - 新文本：
      ```
      ## Round 1 上下文
          - Round 1 accepted findings: <paste>
          - Round 1 修复内容: <paste>
          - Git diff scope: <paste>
      ```
  - **子改动 3c**：修改 RCA dispatch prompt 内部"不要重复前两轮的修复方法"
    - 旧文本：`不要重复前两轮的修复方法。`
    - 新文本：`不要重复 Round 1 的修复方法。`
  - **子改动 3d**：修改 Analyst Resolution Routing 表（删 Targeted Re-Review 行）+ 修改 Phase 软上限
    - 旧文本：
      ```markdown
      **Analyst Resolution 路由**：

      | Resolution | 下一步 |
      | --- | --- |
      | `fixed` | Targeted Re-Review（消耗 Round 3 的 review budget） |
      | `root cause found, not fixed` | 用 analyst findings dispatch worker（消耗 Round 3） |
      | `root cause in design/plan` | 写回 design doc / plan → 返回对应 upstream verdict |
      | `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
      | `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

      Round 3 的 Targeted Re-Review 仍 needs repair → BLOCKED，报告用户附完整排查记录。

      **Phase 内部 review dispatch 软上限**：10（2 baseline + 最多 3 gaps × 2 rounds + analyst round + final re-review）。
      ```
    - 新文本：
      ```markdown
      **Analyst Resolution 路由**：

      | Resolution | 下一步 |
      | --- | --- |
      | `fixed` | Coordinator 自验闭合（不再派 Targeted Re-Review）|
      | `root cause found, not fixed` | 用 analyst findings dispatch worker → Coordinator 自验 |
      | `root cause in design/plan` | 写回 design doc / plan → 返回对应 upstream verdict |
      | `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
      | `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

      RCA escalation 产出的不是 Codex review 派发，不消耗 review budget。Analyst 路径仍失败 → BLOCKED，报告用户附完整排查记录。

      **Phase 内部 review dispatch 软上限**：3（2 baseline + 0 targeted + 最多 1 release gate）。
      ```
- [ ] Step 4: 修改 `final-review-repair.md` L52 区段删 targeted dispatch
  - 文件：`plugin/skills/orchestrate-final-review/references/final-review-repair.md`
  - 旧文本：`所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 默认自验收（verification commands + acceptance criteria 对照）。仅当满足 exception 条件（3+ 文件控制流修改 / 用户要求 / RCA 根因修复 / Path A 自修）时派发 targeted Codex re-review。Targeted re-review 必须用 `codex-companion.mjs task --background --resume` 复用 baseline reviewer 的 JOB_ID；只有 source baseline 改变时才 full phase review rerun。gate-codex-review.sh 强制此规则。`
  - 新文本：`所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 自验收（verification commands + acceptance criteria 对照）即闭合，不再派发 targeted Codex re-review；自验仍有疑虑 → 升级 RCA 或 BLOCKED 报告用户。`
- [ ] Step 5: 修改 `final-review-release-gate.md` Step 18 区段删 targeted release re-review
  - 文件：`plugin/skills/orchestrate-final-review/references/final-review-release-gate.md`
  - 旧文本：`5. 修复后做 targeted release re-review：只审修复变更 + 原 release risk surface。不重跑 baseline review（除非修复改变了 source design / plan / shared contract / migration / permission / billing / runtime baseline）`
  - 新文本：`5. 修复后由 Coordinator 自验：对照 release risk surface + 跑 verification commands 验证修复点已落地；不再派发 targeted release re-review。`
- [ ] Step 6: 修改 `final-review-completion.md` Step 15 区段
  - 文件：`plugin/skills/orchestrate-final-review/references/final-review-completion.md`
  - 旧文本：
    ```
    3. 简单修复（Coordinator 直接改）→ 不需要额外 review
    4. 复杂修复（派了 worker）→ 做 targeted re-review（Budget 消耗 1）
    ```
  - 新文本：
    ```
    3. 简单修复（Coordinator 直接改）→ Coordinator 自验闭合
    4. 复杂修复（派了 worker）→ Coordinator 自验闭合（不再派 targeted re-review；自验仍有疑虑 → RCA 或 BLOCKED）
    ```
- [ ] Step 7: 修改 `orchestrate-final-review/SKILL.md` preamble L52 区段
  - 文件：`plugin/skills/orchestrate-final-review/SKILL.md`
  - 旧文本：`Baseline review 使用 `codex-companion.mjs task --background` 启动 background job；targeted re-review 使用 `task --background --resume` 复用同一 JOB_ID。`
  - 新文本：`Baseline review 使用 `codex-companion.mjs task --background` 启动 background job。修复后由 Coordinator 自验闭合，不再派发 targeted re-review。`
- [ ] Step 8: 跑 verification
  - Run: `grep -i "targeted re-review\|targeted-re-review" plugin/skills/orchestrate-final-review/` → Expected: 0 命中
  - Run: `grep "Phase 内部 review dispatch 软上限" plugin/skills/orchestrate-final-review/references/final-review-repair.md` → Expected: 命中且含 `3`
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
- [ ] Step 9: Suggested commit
  - Message: `chore(final-review): 删 Self-Read + Step 11 整段 + Step 12 三轮→二段 + 软上限 10→3`

---

### Task Pack 3.6: Multi-PR Merge 阶段微调（D23）

**Issue:** Small issue #6
**Goal behavior:** Multi-PR Coordinator 端最小职责 5 处重复段提取为 SKILL.md 顶部通用模板；targeted re-review 在 Multi-PR 的 5 处级联清理完整落地；Phase 内部 review dispatch 软上限 = 1；merge-completion 的"不存在非阻塞项"重述改为单行引用；merge-conflict-repair worker dispatch prompt 中 3 个 handbook 残留引用删除。

**Owned files / responsibilities:**
- Modify: `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` — 顶部追加「Coordinator dispatch 通用步骤」一段（4 step 通用模板）
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-preparation.md` — 删除末尾 `## Coordinator 端最小职责` 段（约 8 行），改为引用 SKILL.md 顶部通用模板
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-discovery.md` — 同上
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-rca-investigation.md` — 同上
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md` — 同上 + dispatch prompt 中删除对 3 个 multi-pr handbook 的引用（已被 Issue 001 D2 删除）
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` — Step 18 重写删 targeted re-review（含 prompt 模板 + DISPATCH_ENVELOPE 块 + "gate 名 multi-pr-repair-<round>" + "最多 2 轮修复"）+ 末尾追加 Phase 软上限 ≤ 1 + 删 `## Coordinator 端最小职责` 段
- Modify: `plugin/skills/orchestrate-multi-pr-merge/references/merge-completion.md` — "不存在非阻塞项" 段改为单行引用 Final Review Step 13

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 23（含 4 项级联清理表 + 3 条新优化）
- Issue 001 D2（3 个 multi-pr handbook 删除前提）
- Issue 002 D13（targeted re-review 全局机制删除前提）
- 7 个目标文件全文（特别是 `merge-integration-review.md` Step 18 完整段 + 5 个 `## Coordinator 端最小职责` 段当前内容确认 4 step 通用结构）

**Contract anchors:**
- Owner: Pack 3.6
- Provider: SKILL.md 顶部「Coordinator dispatch 通用步骤」一段（4 step 通用模板）作为 Multi-PR Coordinator dispatch 的唯一权威源
- Consumer: 4 类 Multi-PR Coordinator dispatch（merge-preparation / conflict-discovery / RCA / conflict-repair / integration-review）；merge-completion 清扫逻辑引用 Final Review Step 13
- Verification: grep 整 multi-pr-merge/ 0 `targeted re-review` / `multi-pr-repair-` 残留；`## Coordinator 端最小职责` 在 references/ 内整段 0 出现

**Mockup specs:** N/A

**Acceptance criteria:**
- [ ] `orchestrate-multi-pr-merge/SKILL.md` 顶部存在「Coordinator dispatch 通用步骤」一段（4 step 通用模板：写 merge-brief + 写 DISPATCH_ENVELOPE + 派发 + 处理返回）
- [ ] 5 个 reference 文件均不再含 `## Coordinator 端最小职责` 重复整段；保留单行引用 SKILL.md 通用模板可接受
- [ ] `merge-integration-review.md` Step 18 区段不含 `<!-- DISPATCH_ENVELOPE ... review_intent: "targeted-re-review"` 模板；不含 "gate 名使用 multi-pr-repair-<round>" 行；"最多 2 轮修复" 改为 "1 轮修复 + Coordinator 自验 → 失败 BLOCKED"
- [ ] `merge-integration-review.md` 末尾追加 "Phase 内部 review dispatch 软上限：1（1 integration review + 0 targeted re-review）" 一行
- [ ] `merge-completion.md` "不存在非阻塞项" 段改为单行引用 "清扫纪律同 Final Review Step 13（详见 `final-review-completion.md`）"，保留 multi-PR 独有的清扫来源列表
- [ ] `merge-conflict-repair.md` dispatch prompt 中无 `multi-pr-conflict-worker-handbook` / `multi-pr-explorer-handbook` / `multi-pr-integration-review-handbook` 字符串残留

**Verification commands:**
- `grep "Coordinator dispatch 通用步骤\|merge-brief 写作流程" plugin/skills/orchestrate-multi-pr-merge/SKILL.md` → Expected: ≥ 1 命中
- `grep "^## Coordinator 端最小职责" plugin/skills/orchestrate-multi-pr-merge/references/*.md` → Expected: 0 命中（章节标题不再存在）
- `grep -i "targeted re-review\|targeted-re-review\|multi-pr-repair-" plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` → Expected: 0 命中
- `grep "Phase 内部 review dispatch 软上限" plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` → Expected: 命中且含 `1`
- `grep -E "multi-pr-explorer-handbook|multi-pr-conflict-worker-handbook|multi-pr-integration-review-handbook" plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md` → Expected: 0 命中
- `grep "Final Review Step 13\|清扫纪律同 Final Review" plugin/skills/orchestrate-multi-pr-merge/references/merge-completion.md` → Expected: 命中
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
- `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0

**Commit boundary:** 1 个 atomic commit `chore(multi-pr): 提取 Coordinator dispatch 通用模板 + targeted re-review 级联清理 + 软上限 1`
**Risk flags:** normal
**发布风险:** 无
**AFK / HITL:** AFK
**Dependencies:** Issue 001 D2（3 个 multi-pr handbook 删除）+ Issue 002 D13（targeted re-review 全局机制删除）
**Out of scope:** sub-agent 事实校验 Step（→ Pack 3.7）；review-dispatch 共享 inject 在 multi-pr/ 文件中的处理（属 Issue 001 D1）

#### Implementation tasks
- [ ] Step 1: 在 `orchestrate-multi-pr-merge/SKILL.md` 顶部追加「Coordinator dispatch 通用步骤」一段
  - 文件：`plugin/skills/orchestrate-multi-pr-merge/SKILL.md`
  - Position：紧跟现有 `## merge-brief 写作流程` 段之后（已验证该 section 存在于当前 SKILL.md L114 区段）、`## Steps 1-3：入口 + 文档理解` 之前。先 grep 定位：`grep -n "^## merge-brief 写作流程\|^## Steps 1-3" plugin/skills/orchestrate-multi-pr-merge/SKILL.md` 取得两个锚点行号，在两行之间插入新段。
  - 内容：
    ```markdown
    ## Coordinator dispatch 通用步骤

    Multi-PR Merge 阶段 4 类 dispatch（explorer / analyst / worker / reviewer）均遵循以下通用模板：

    1. 写 `merge-brief-<run_id>.md`（若已写则复用），确保包含 PR 列表、设计文档路径、合同地图、冲突解决记录、各阶段当前 stage
    2. 写 `DISPATCH_ENVELOPE`：填入 `run_id`、`gate`（对应阶段名）、`review_intent: "baseline"`（reviewer 类）或 agent_role（其他类）
    3. 写 dispatch prompt 文件 / 派发：reviewer 类走 review-prompts + validate/record；其他类直接 Agent 调用
    4. 等待返回 → 跑 result/complete 脚本 → Coordinator 校验返回事实 → 写入 merge-brief 对应段

    各阶段 reference（merge-preparation / merge-conflict-discovery / merge-rca-investigation / merge-conflict-repair / merge-integration-review）只描述该阶段特有的 prompt 模板与返回处置，**不再重复 Coordinator dispatch 通用步骤**。
    ```
- [ ] Step 2: 删除 `merge-preparation.md` 末尾 `## Coordinator 端最小职责` 整段
  - 文件：`plugin/skills/orchestrate-multi-pr-merge/references/merge-preparation.md`
  - 旧文本：`## Coordinator 端最小职责` 标题到下一个 `##` 或文件末尾的整段
  - 新文本：（整段删除；可选保留单行引用 "Coordinator dispatch 通用步骤见 SKILL.md 顶部"）
- [ ] Step 3: 同 Step 2 处理 `merge-conflict-discovery.md`
- [ ] Step 4: 同 Step 2 处理 `merge-rca-investigation.md`
- [ ] Step 5: 同 Step 2 处理 `merge-conflict-repair.md` + 删除 dispatch prompt 中对 3 个 handbook 的引用
  - 文件：`plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
  - 子改动 a：删除 `## Coordinator 端最小职责` 整段
  - 子改动 b：在 Step 12a/12b worker dispatch prompt 中，找到任何 `multi-pr-conflict-worker-handbook` / `multi-pr-explorer-handbook` / `multi-pr-integration-review-handbook` 字符串残留，整段删除（决策 23 指出 conflict 详情 + 修复方向已在 merge-brief §4/§5 内）
- [ ] Step 6: 重写 `merge-integration-review.md` Step 18 区段 + 末尾追加软上限 + 删 `## Coordinator 端最小职责`
  - 文件：`plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
  - 子改动 a：找到 Step 18（修复后做 Targeted Re-Review）整段：从"修复后做 **Targeted Re-Review**"声明 → DISPATCH_ENVELOPE 模板 → "最多 2 轮修复" 一行，全部删除（约 55 行）
  - 子改动 a 新文本：
    ```markdown
    - 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
    - 复杂修复 → 派 worker

    修复后由 Coordinator 自验：对照 merge-brief §3（合同地图）/§7（集成审查 7 角度）+ 跑 validation commands；自验通过即闭合，自验失败 → BLOCKED 报告用户。

    1 轮修复 + Coordinator 自验 → 失败 BLOCKED（不再派 targeted re-review；不消耗 review budget）。
    ```
  - 子改动 b：删除 `## Coordinator 端最小职责` 整段（约 8 行）
  - 子改动 c：在文件末尾（或合适位置）追加：
    ```markdown
    **Phase 内部 review dispatch 软上限**：1（1 integration review + 0 targeted re-review）。
    ```
- [ ] Step 7: 改写 `merge-completion.md` "不存在非阻塞项" 段
  - 文件：`plugin/skills/orchestrate-multi-pr-merge/references/merge-completion.md`
  - 旧文本（约 9 行）：
    ```markdown
    ## 不存在非阻塞项

    **铁律同样适用于 Multi-PR Merge。**

    合并完成后，检查：
    - 所有冲突解决记录中标记为 "out of scope" 的项 → 确认已开 GitHub issue
    - 合并过程中 worker Open Items → 逐项处置（修复 / 开 issue / 确认不是问题）
    - `git diff <base>..HEAD` 范围内新增的 TODO/FIXME → 处置
    ```
  - 新文本：
    ```markdown
    ## 清扫纪律

    清扫纪律同 Final Review Step 13（详见 `final-review-completion.md`）。Multi-PR 独有清扫来源：
    - 所有冲突解决记录中标记为 "out of scope" 的项 → 确认已开 GitHub issue
    - 合并过程中 worker Open Items → 逐项处置（修复 / 开 issue / 确认不是问题）
    - `git diff <base>..HEAD` 范围内新增的 TODO/FIXME → 处置
    ```
- [ ] Step 8: 跑 verification
  - Run: `grep "^## Coordinator 端最小职责" plugin/skills/orchestrate-multi-pr-merge/references/*.md` → Expected: 0 命中
  - Run: `grep -i "targeted re-review\|targeted-re-review\|multi-pr-repair-" plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` → Expected: 0 命中
  - Run: `grep "Phase 内部 review dispatch 软上限" plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md` → Expected: 命中且含 `1`
  - Run: `grep -E "multi-pr-explorer-handbook|multi-pr-conflict-worker-handbook|multi-pr-integration-review-handbook" plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md` → Expected: 0 命中
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
- [ ] Step 9: Suggested commit
  - Message: `chore(multi-pr): 提取 Coordinator dispatch 通用模板 + targeted re-review 级联清理 + 软上限 1`

---

### Task Pack 3.7: Sub-agent 事实校验横切（D18）

**Issue:** Small issue #7
**Goal behavior:** Coordinator 在派 Explorer / plan-writer / pack-executor / root-cause-analyst 收回的事实声明（行号 / 计数 / 存在性 / 引用关系）必须亲验后再写入交付物或汇报；此原则在 plugin 强制层显式落地：3 个调研类 agent description 含校验声明，4 个 SKILL.md（discovery / plan-writing / execution / multi-pr-merge）含 Coordinator 抽验 Step，agent-return-handler.sh NEXT 指令含明确提醒，architecture-draft 含「Sub-agent 信任边界」章节。

**Owned files / responsibilities:**
- Modify: `plugin/agents/code-explorer.md` — frontmatter description 末尾追加事实校验声明
- Modify: `plugin/agents/complex-code-explorer.md` — 同上
- Modify: `plugin/agents/root-cause-analyst.md` — 同上
- Modify: `plugin/skills/orchestrate-discovery/SKILL.md` — 在 Steps 1-2（Pack 3.1 已重写）之后、Step 3 之前插入 Step 1.5「Explorer 报告校验门控」
- Modify: `plugin/skills/orchestrate-plan-writing/SKILL.md` — 主流程合适位置加 plan-writer 返回事实抽验 Step
- Modify: `plugin/skills/orchestrate-execution/SKILL.md` — 主流程合适位置加 pack-executor / root-cause-analyst 返回事实抽验 Step
- Modify: `plugin/skills/orchestrate-multi-pr-merge/SKILL.md` — 主流程合适位置加 4 类 dispatch 返回事实抽验 Step（与 Pack 3.6 顶部「Coordinator dispatch 通用步骤」第 4 step 协同）
- Modify: `plugin/hooks/agent-return-handler.sh` — 生成 Coordinator NEXT 指令处追加一行校验提醒
- Modify: `plugin/architecture-draft.md` — 新增「Sub-agent 信任边界」章节

**Read first:**
- `docs/orchestrate/design/2026-05-28-workflow-token-economy.md` §4.2 决策 18（含 5 处 grep verify 表）+ §7.1 verify-maturity 检查 "Sub-agent 事实校验落地"
- `~/.claude/CLAUDE.md` 中"子代理纪律"章节（用户全局已有的原则，本 Pack 把它落地到 plugin 强制层）
- Pack 3.1 / 3.3 / 3.4 / 3.6 commit（确认相关 SKILL.md 主流程已稳定后再插入 Step）
- 7 个目标文件当前内容

**Contract anchors:**
- Owner: Pack 3.7
- Provider: 7 处落地点合在一起构成 plugin 强制层
- Consumer: Coordinator（运行时读 SKILL.md + agent description）；hook 系统（agent-return-handler.sh 输出 NEXT 指令）
- Verification: §7.1 中 5 处 grep verify 全过

**Mockup specs:** N/A

**Acceptance criteria:**
- [ ] `code-explorer.md` / `complex-code-explorer.md` / `root-cause-analyst.md` 三个 agent 的 description 字段末尾均含中文表述：返回的事实声明（行号 / 计数 / 存在性 / 引用关系）由 Coordinator 必须亲验，sub-agent 不承担 ground truth 责任
- [ ] `orchestrate-discovery/SKILL.md` 含 `Step 1.5` 章节或同义"Explorer 报告校验门控"段，包含 4 项规则（高置信度抽样验 / 中低逐条验 / 跨外部仓库二次验 / 验证失败剔除并重派）
- [ ] `orchestrate-plan-writing/SKILL.md` / `orchestrate-execution/SKILL.md` / `orchestrate-multi-pr-merge/SKILL.md` 均含 sub-agent 事实校验同义表述（plan-writer / pack-executor / root-cause-analyst 返回事实须 Coordinator 抽验）
- [ ] `agent-return-handler.sh` 生成 Coordinator NEXT 指令的代码段含 "校验本次返回的事实声明" 输出
- [ ] `architecture-draft.md` 含「Sub-agent 信任边界」章节，明确 Coordinator 是事实的唯一 ground truth
- [ ] 本 Pack 不引入新 hook 阻断（保持决策 9 hook 简化方向）

**Verification commands:**
- `grep -l "Coordinator 必须亲验\|亲验\|Coordinator must verify" plugin/agents/code-explorer.md plugin/agents/complex-code-explorer.md plugin/agents/root-cause-analyst.md` → Expected: 3 个文件均命中
- `grep -E "Step 1.5|Explorer 报告校验门控" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: 命中
- `grep -lE "Coordinator 抽验|sub-agent 事实校验|返回事实.*校验" plugin/skills/orchestrate-plan-writing/SKILL.md plugin/skills/orchestrate-execution/SKILL.md plugin/skills/orchestrate-multi-pr-merge/SKILL.md` → Expected: 3 个文件均命中
- `grep -c "校验本次返回的事实声明" plugin/hooks/agent-return-handler.sh` → Expected: 1（top-of-emit 仅 1 次，不在每个 verdict 分支重复）
- `grep "Sub-agent 信任边界" plugin/architecture-draft.md` → Expected: 命中
- `bash plugin/hooks/tests/test_agent_id_hook_guard.sh` （或对应 agent-return-handler 测试，若存在）→ Expected: PASS
- `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
- `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0

**Commit boundary:** 1 个 atomic commit `feat(plugin): sub-agent 事实校验机制落地（agents + SKILL.md + hook + architecture）`
**Risk flags:** normal
**发布风险:** 无（本 Pack 仅引入"提醒"层，不引入阻断）
**AFK / HITL:** AFK
**Dependencies:** Pack 3.1（Discovery Steps 1-2 已重写）+ Pack 3.3（Plan Writing SKILL.md 已稳定）+ Pack 3.4（Execution SKILL.md 已稳定，handbook 路径 bug 已修）+ Pack 3.6（Multi-PR SKILL.md 顶部通用模板已落地）
**Out of scope:** 新增 hook 阻断（设计明确不引入）；agent body 内容改动（只改 frontmatter description）；CLAUDE.md 全局规则的改动（属于用户全局，不在 plugin scope）

#### Implementation tasks
- [ ] Step 1: 在 `code-explorer.md` frontmatter description 末尾追加校验声明
  - 文件：`plugin/agents/code-explorer.md`
  - Position：frontmatter description 字段（多行字符串）末尾，在 `Do NOT use for:` 之后或合适位置
  - 追加：
    ```
    返回的事实声明（行号 / 计数 / 文件存在性 / 引用关系）由 Coordinator 必须亲验后再写入交付物或汇报。本 agent 是劳动力不是 ground truth，Coordinator 是事实的唯一权威。
    ```
- [ ] Step 2: 同 Step 1 处理 `complex-code-explorer.md`
- [ ] Step 3: 同 Step 1 处理 `root-cause-analyst.md`
- [ ] Step 4: 在 `orchestrate-discovery/SKILL.md` Steps 1-2 与 Step 3 之间插入 Step 1.5
  - 文件：`plugin/skills/orchestrate-discovery/SKILL.md`
  - Position：紧跟 Pack 3.1 重写的 Steps 1-2 段之后，Step 3 之前
  - 内容：
    ```markdown
    ## Step 1.5：Explorer 报告校验门控

    对每个 Explorer 返回的报告，Coordinator 必须在写入设计文档输入或与用户讨论前完成事实校验：

    1. **高置信度声明（confidence ≥ 7）**：抽样验 — 至少 grep / Read 1 个关键事实
    2. **中低置信度（confidence ≤ 6）或"存在性 / 不存在性"声明**：逐条 grep / Read 验
    3. **跨用户 skills / 跨外部仓库 / 跨主仓库的事实**：必须二次验（Explorer 默认只读 `plugin/`，会漏外部）
    4. **任何验证失败**：该声明从设计文档输入中剔除 → 重派 Explorer 或 Coordinator 亲查

    通过校验门控后再进入 Step 3 与用户讨论。
    ```
- [ ] Step 5: 在 `orchestrate-plan-writing/SKILL.md` 主流程加 sub-agent 事实校验 Step
  - 文件：`plugin/skills/orchestrate-plan-writing/SKILL.md`
  - Position：紧跟 `## Steps 9-10` 段落（"派 plan-writer + 收返"）之后、`## Steps 11-12b` 之前。先 grep 定位：`grep -n "^## Steps 9-10\|^## Steps 11-12" plugin/skills/orchestrate-plan-writing/SKILL.md` 取锚点；在两个标题之间插入。
  - 追加 / 插入：
    ```markdown
    **Plan-writer 返回事实校验**：Coordinator 收到 plan-writer 返回的 plan 文件路径、文件存在性、行号引用、Pack 数量声明等事实，必须抽验（≥ 1 个事实 grep / Read）后再进入 Plan Entry Gate。事实失实 → 重派 plan-writer 或 Coordinator 亲查。
    ```
- [ ] Step 6: 在 `orchestrate-execution/SKILL.md` 主流程加 sub-agent 事实校验 Step
  - 文件：`plugin/skills/orchestrate-execution/SKILL.md`
  - Position：紧跟 Worker 返回处置段、Plan Implementation Review 派发段之前。先 grep 定位：`grep -n "Plan Implementation Review\|^## Steps 4-9\|^## Step 8" plugin/skills/orchestrate-execution/SKILL.md` 取锚点；选首次出现 `Plan Implementation Review` 派发的章节标题之前插入。
  - 追加 / 插入：
    ```markdown
    **Worker / RCA 返回事实校验**：Coordinator 收到 pack-executor / complex-pack-executor / root-cause-analyst 返回的 commit hash、文件路径、行号、grep 结果、Pack 状态等事实，必须抽验（≥ 1 个事实 grep / Read / git show）后再进入 Plan Implementation Review 或下一 Pack 派发。事实失实 → 重派或 Coordinator 亲查。
    ```
- [ ] Step 7: 在 `orchestrate-multi-pr-merge/SKILL.md` 主流程加 sub-agent 事实校验 Step
  - 文件：`plugin/skills/orchestrate-multi-pr-merge/SKILL.md`
  - Position：紧跟 Pack 3.6 Step 1 已写入的 `## Coordinator dispatch 通用步骤` 段之后、`## Steps 1-3：入口 + 文档理解` 之前。先 grep 定位：`grep -n "^## Coordinator dispatch 通用步骤\|^## Steps 1-3" plugin/skills/orchestrate-multi-pr-merge/SKILL.md` 取锚点；在两标题之间插入。
  - 追加 / 插入：
    ```markdown
    **4 类 dispatch 返回事实校验**：Coordinator 收到 explorer / analyst / worker / reviewer 返回的 PR 列表、冲突点、文件路径、行号、grep 结果等事实，必须抽验（≥ 1 个事实 grep / Read / gh pr view）后再写入 merge-brief 对应段。事实失实 → 重派或 Coordinator 亲查。
    ```
- [ ] Step 8: 修改 `agent-return-handler.sh` 在 NEXT 指令前一次性输出校验提醒
  - 文件：`plugin/hooks/agent-return-handler.sh`
  - Position：找到所有 verdict 分支共同进入的 NEXT 指令输出区域。**统一在所有 verdict 路由前的入口处打印 1 次**（避免 5 个 verdict 分支各打 1 次造成噪音）。一般在 plan-return parsed 之后、verdict switch case 之前的位置插入。
  - **必须只插入 1 次**（top-of-NEXT-emit），不在每个 verdict 分支重复。
  - 插入行：
    ```bash
    echo "⚠️ 写入交付物前必须校验本次返回的事实声明（行号 / 计数 / 存在性 / grep 结果 / 引用关系）" >&2
    ```
  - 注意：保持原 NEXT 指令格式与下游消费者契约不变；本行仅追加为额外提醒，输出到 stderr 避免污染下游 stdout 解析
- [ ] Step 9: 在 `architecture-draft.md` 新增「Sub-agent 信任边界」章节
  - 文件：`plugin/architecture-draft.md`
  - Position：合适章节位置（如紧随 Sub-agent 层介绍后，或 Coordinator 角色章节之后）
  - 内容：
    ```markdown
    ## Sub-agent 信任边界

    Plugin 采用 Coordinator-Worker 分担架构：Coordinator 把专项工作（写设计 / 写 plan / 写代码 / 调研根因）下放到 sub-agent 以分担上下文压力 + 提升专项输出质量。但 sub-agent 的返回不是 ground truth。

    **核心原则**：sub-agent 是劳动力，Coordinator 是事实的唯一权威。

    **强约束**：sub-agent 返回的任何事实声明（行号 / 计数 / 文件路径 / 存在性 / grep 结果 / 引用关系 / Pack 状态 / commit hash）由 Coordinator 必须亲验后再写入交付物（design / plan / merge-brief / issue / commit message）或汇报给用户。

    **强约束在主流程文本中体现**（不在 hook 中）：
    - `agents/code-explorer.md` / `complex-code-explorer.md` / `root-cause-analyst.md` description 中明确事实校验责任
    - `orchestrate-discovery/SKILL.md` Step 1.5「Explorer 报告校验门控」
    - `orchestrate-plan-writing/SKILL.md` / `orchestrate-execution/SKILL.md` / `orchestrate-multi-pr-merge/SKILL.md` 主流程含 sub-agent 返回事实校验 Step
    - `hooks/agent-return-handler.sh` 输出 NEXT 指令含"⚠️ 写入交付物前必须校验本次返回的事实声明"提醒

    **不引入新的 Hook 阻断**：本机制是提醒层而非阻断层，保持 hook 简化方向。Coordinator 的校验责任由文本强制，不由 hook 强制。
    ```
- [ ] Step 10: 跑 verification
  - Run: `grep -l "Coordinator 必须亲验\|亲验" plugin/agents/code-explorer.md plugin/agents/complex-code-explorer.md plugin/agents/root-cause-analyst.md` → Expected: 3 个文件均命中
  - Run: `grep "Step 1.5\|Explorer 报告校验门控" plugin/skills/orchestrate-discovery/SKILL.md` → Expected: 命中
  - Run: `grep -lE "Coordinator 抽验|事实校验|返回事实" plugin/skills/orchestrate-plan-writing/SKILL.md plugin/skills/orchestrate-execution/SKILL.md plugin/skills/orchestrate-multi-pr-merge/SKILL.md` → Expected: 3 个文件均命中
  - Run: `grep "校验本次返回的事实声明" plugin/hooks/agent-return-handler.sh` → Expected: 命中
  - Run: `grep "Sub-agent 信任边界" plugin/architecture-draft.md` → Expected: 命中
  - Run: `bash plugin/scripts/run-all-tests.sh` → Expected: 全 PASS
  - Run: `bash plugin/scripts/verify-maturity.sh` → Expected: exit 0
- [ ] Step 11: Suggested commit
  - Message: `feat(plugin): sub-agent 事实校验机制落地（agents + SKILL.md + hook + architecture）`

---

## Out of scope（整 plan 级）

- D1-13（属 Issue 001 + 002）：模板系统去重 / 死模板与孤儿文件清理 / Path A 删除 / doc-patch 删除 / bug-seed-file 删除 / agent-context-check 删除 / state.sh 死命令 + scripts/lib 清理 / dispatch 脚本合并 / hook 简化 / Routes 4-7 折叠 / 外部 skill 集成对齐 + agent frontmatter 瘦身 / reference 跳跃精简 / targeted re-review 全局删除
- Coordinator checkbox toggle 规则（Issue 002 D4 内落地）
- worker-loop.md.tmpl segment 5 重写（Issue 002 D6 内落地，本 plan 只改 L12 path 修正）
- 任何新增 hook 阻断（D18 明确不引入）
- mockup 系统 / frontend-design skill 集成本体（D19 仅在 Discovery SKILL.md 留空间，不改 mockup 系统）
- codex-review skill（设计 §10 第 15 条本轮不动）
