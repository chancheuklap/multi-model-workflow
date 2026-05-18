---
name: orchestrate-workflow
description: "正式开发流程主入口。用户给出新功能、系统性改造、系统性 bug、wrong state、performance regression、design / SPEC / ADR、PRD / issue、backlog、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、截图反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。负责 Entry Gate 分类、Resume Gate、Infrastructure Setup、Phase Dispatch 路由和 Closing；不自己执行 Phase 内部逻辑——加载对应 phase skill 执行。"
---

# Orchestrate Workflow

主线程入口。职责：Entry Gate → Resume Gate → Infrastructure Setup → Phase 路由 → Closing。

**核心原则**：Workflow 只做路由和基础设施——不写设计、不写计划、不派 worker、不做 review。每个 phase 的内部逻辑由对应 phase skill 负责。Workflow 的价值在于正确判断"现在该进哪个 phase"和"phase 返回后下一步去哪"。

**连续执行**：除非遇到需要用户决策的业务问题或无法解决的 BLOCKED，否则 phase 之间不暂停、不汇报、不问"要不要继续"。Phase skill 返回后直接路由到下一个 skill。

---

# 第一部分：Entry Gate

## Step 1：分类输入

| 路线 | 输入信号 | 下一步 |
| --- | --- | --- |
| **Route 1: Formal Orchestrate** | 新功能、系统性改造、含混 feedback、缺 design/issue/plan、PRD/issue/backlog、测试反馈、UI/UX 反馈、截图反馈、已有 design 但未 review、已有 plan 但未 review、已有 reviewed plan 要继续执行 | Step 2（Resume Gate） |
| **Route 2: Bug Investigation** | bug report / error log / regression / failing test，根因不明 | Step 4（Infrastructure）→ Step 15（analyst） |
| **Route 3: Multi-PR Merge** | 多个并行 PR 需要合并审查（来自同一大设计/大计划的并行落地） | Step 4（Infrastructure）→ Step 19（multi-pr） |

**模糊输入**：无法判定路线时，一次只问一个问题收窄定位。不猜测、不默认走 Formal。

**不进入 orchestrate 的输入**：
- 只问概念/状态/解释 → 直接回答，不创建 scope
- 一句话能答完的事实问题 → 直接回答
- 用户说"先等等"/"先搁着" → 等用户下次再触发

---

# 第二部分：Resume Gate

## Step 2：Within-Conversation Resume

同一对话内 phase skill 返回的 verdict 直接路由到下一 phase（见第四/五/六部分的 verdict 表）。不重新走 Entry Gate 或 Infrastructure Setup。

## Step 3：Cross-Conversation Resume

新对话接手上一个 session 的工作。检查 artifact 状态决定从哪里继续。

### 3a：检测活跃运行

```bash
cat .claude/multi-model-workflow/active-run-id 2>/dev/null
find .claude/multi-model-workflow/budget-*.json -mmin -60 2>/dev/null
```

- **无活跃运行** → 从 Entry Gate（Step 1）开始
- **有活跃运行且 stale（> 1h 无更新）** → 清理旧文件，从 Entry Gate 开始
- **有活跃运行且 fresh** → 进入 3b

### 3b：Source Stability 检查

Budget file 记录 `last_gate_phase` 和 `last_gate_timestamp`。检查 source artifacts 自上次 gate 通过后是否被修改：

```bash
git log --oneline --since="<last_gate_timestamp>" -- <design_path> <plan_path> <issue_paths>
```

| 条件 | 从哪里继续 |
| --- | --- |
| Design doc 存在但无 Design Review 通过记录 | orchestrate-discovery（Design Review 阶段） |
| Design doc 在 Design Review 后被修改 | 重新进入 Design Review |
| Plan 存在 + Design Review 通过 + design 未变 | orchestrate-plan-writing（Plan Review 阶段） |
| Plan 在 Plan Review 后被修改 | 重新进入 Plan Review |
| Packs 部分完成 + plan 未变 | orchestrate-execution（从上次完成的 pack 继续） |
| 所有 packs 完成 + 代码未变 | orchestrate-final-review |
| Final Review 通过 | Closing（Step 21） |

### 3c：恢复 Infrastructure

Scope Contract 和 Budget File 已存在 → 读取并验证。`pack_count` 或 `editable artifacts` 与当前 plan 不一致 → 更新。

---

# 第三部分：Infrastructure Setup

## Step 4：Write Scope Contract

创建 `.claude/multi-model-workflow/scope-<run_id>.md`：

```markdown
# Scope Contract: <run_id>

## Source artifacts
- <用户明确提供的文档 / tracker refs / diff>
- <当前 phase 已确认的直接输入>

## Editable artifacts
- <source artifacts 或当前 phase 明确要求产出的 design / plan / pack / report>

## Read-only context
- <相关 issue、ADR、代码或 runbook——sub-agent 只能用来判断，不得变成交付范围>

## Out of scope
- <明确列出容易被误纳入的相关 issue、ADR、未来能力、其它文档或环境>

## Issue recording target
- <small issue hierarchy 写回哪里>
```

**规则**：
- Source artifacts 只包含用户明确提供的文档和当前 phase 已确认的直接输入
- Editable artifacts 只能是 source artifacts 或 phase 明确要求的产出
- Read-only context 只用于判断，不变成交付范围
- Out of scope 必须明确列出容易被误纳入的内容——阻止 sub-agent 和 reviewer 扩大范围

## Step 5：Git Checkpoint

```bash
git status --short --branch
```

| 状态 | 动作 |
| --- | --- |
| 在 main / master / release branch 上 | 创建 `work/<short-scope>` 分支 |
| 已在 work branch 上 | 继续 |
| 有 dirty files 属于当前 scope | 暂不 stage（后续 phase skill 在各自 Git Checkpoint 中处理） |
| 有 dirty files 不属于当前 scope | 不 stage、不动、不 stash |

## Step 6：Budget File（仅 Formal Orchestrate）

创建 `.claude/multi-model-workflow/budget-<run_id>.json` 和 `.claude/multi-model-workflow/active-run-id`：

```json
{
  "run_id": "formal-<YYYYMMDD>-<HHMMSS>",
  "budget_total": 0,
  "budget_used": 0,
  "pack_count": 0,
  "last_gate_phase": "entry",
  "last_gate_timestamp": "<ISO 8601>",
  "dispatches": []
}
```

`budget_total` 在 plan-writing Step 12a 确认 `pack_count` 后按公式 `2N + 12` 更新。Entry gate 时 pack count 未知，先写 0。

`active-run-id` 内容为 budget file 的文件名。

**Bug / Multi-PR route 不创建 budget file**——这些路线的 review 数量固定且有限。

---

# 第四部分：Route 1 — Formal Orchestrate

线性管线：Discovery → Plan Writing → Execution → Final Review → Closing。每个 phase skill 通过 `Skill({ skill: "<name>" })` 加载到主线程执行（不是 sub-agent）。

## Step 7：进入 orchestrate-discovery

```
Skill({ skill: "orchestrate-discovery" })
```

Discovery 在主线程执行。Coordinator 按 discovery SKILL.md 与用户讨论、维护 CONTEXT.md、生成设计文档、执行 Design Review。

## Step 8：Handle Discovery Return

| Discovery Verdict | Coordinator 动作 |
| --- | --- |
| `DISCOVERY_READY` | 检查 issue hierarchy：有 → Step 9；无 → 调用 `to-issues` → Step 9 |
| `DISCOVERY_NOT_NEEDED` | 已有足够清晰的 design → 检查 issue hierarchy → Step 9 |
| `READY_FOR_REPAIR` | 已批准 design 下的实现偏离 → Step 8a（Direct Repair mini-route） |
| `NEEDS_USER_DECISION` | 将问题呈现给用户（一次只问一个），等回答后重新进入 discovery |
| `BLOCKED` | 报告用户，附阻塞原因和已完成的讨论/设计进展 |

**更新 Budget File**：`last_gate_phase: "discovery"`, `last_gate_timestamp: <now>`。

### Step 8a：Direct Repair（READY_FOR_REPAIR mini-route）

已批准 design 下的明确实现偏离。不走完整 Formal Orchestrate——派 worker 修复 + Codex review + Closing。

**1. 派 Worker**

按偏离涉及的 risk flags 选择 agent（同 execution Step 4 规则）：

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Direct repair: <deviation summary>",
  prompt: "
    ## Scope
    修复已批准 design 下的实现偏离。

    ## Source design
    <path>（已通过 Design Review）

    ## Deviation
    <discovery 报告的具体偏离：current behavior vs design intent>

    ## Fix scope
    <affected files from discovery report>

    ## Acceptance criteria
    - [ ] 行为与 design intent 一致
    - [ ] 回归测试通过
    - [ ] 不引入 design 未要求的新功能

    ## Contract anchors
    <if deviation touches contract boundaries>

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Completed behavior
    ### Verification
    ### Open Items
  "
})
```

**2. Codex Review**

Worker 返回 pass 后，派发 Codex 验证修复：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Direct repair review: <deviation summary>",
  prompt: "
    --model gpt-5.4

    ## Scope
    Review a direct repair for design deviation.

    ## Source design
    <path>

    ## Deviation and fix
    <deviation description + worker's changed files>

    ## Review angles
    - Fix aligns with approved design intent
    - No regression introduced
    - No scope creep beyond the stated deviation
    - Contract integrity maintained (if applicable)

    ## Calibration
    Targeted repair review — only assess fix correctness against design.

    ## Return Contract
    ### Verdict
    pass / needs repair / blocked
    ### Evidence
    ### Result
    ### Verification
    ### Open Items
  "
})
```

| Verdict | 动作 |
| --- | --- |
| `pass` | Step 21（Closing） |
| `needs repair` | Coordinator 验证 finding → 路径 A（≤2 文件直接修）或路径 B（SendMessage worker）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

Direct Repair 不创建 budget file（固定 1 worker + 1-2 review，成本有限）。

## Step 9：进入 orchestrate-plan-writing

```
Skill({ skill: "orchestrate-plan-writing" })
```

Plan-writing 在主线程执行。内部派发 plan-writer agent 和 Codex reviewer。

## Step 10：Handle Plan-writing Return

| Plan-writing Verdict | Coordinator 动作 |
| --- | --- |
| `PLAN_CREATED` | 确认 budget file（plan-writing 已在 Step 12a 更新 `pack_count: N`, `budget_total: 2N + 12`）→ Step 11 |
| `NEEDS_DISCOVERY` | 回到 Step 7，附 plan-writing 报告的具体缺口 |
| `NEEDS_DESIGN_REVIEW` | Design doc 未 review → 回到 discovery 的 Design Review 阶段 |
| `NEEDS_ISSUES` | 调用 `to-issues` → 重新进入 Step 9 |
| `NEEDS_TRIAGE` | 调用 `triage` → 重新进入 Step 9 |
| `NEEDS_DIAGNOSIS` | 调用 `diagnose` → 写回 design doc → 重新进入 Step 9 |
| `NEEDS_DECISION` | 询问用户（一次只问一个）→ 回答后重新进入 Step 9 |
| `NEEDS_ARCHITECTURE` | 调用 `improve-codebase-architecture` → 写回后重新进入 Step 9 |
| `NEEDS_CONTEXT` | 派 `code-explorer` / 调用 `zoom-out` → 补充后重新进入 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "plan-writing"`, `last_gate_timestamp: <now>`。`pack_count` 和 `budget_total` 已由 plan-writing Step 12a 写入。

## Step 11：进入 orchestrate-execution

```
Skill({ skill: "orchestrate-execution" })
```

Execution 在主线程执行。内部派发 worker、Codex reviewer、explorer、root-cause-analyst。

## Step 12：Handle Execution Return

| Execution Verdict | Coordinator 动作 |
| --- | --- |
| `EXECUTION_PASSED` | Step 13（Final Review） |
| `NEEDS_DISCOVERY` | 回到 Step 7，seed discovery with execution 报告 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9，附执行中发现的 plan 问题 |
| `NEEDS_ARCHITECTURE` | 调用 `improve-codebase-architecture` → 写回后判断：只影响当前 pack → 回 Step 11 继续；改变 plan anchors → 回 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "execution"`, `last_gate_timestamp: <now>`。

## Step 13：进入 orchestrate-final-review

```
Skill({ skill: "orchestrate-final-review" })
```

Final Review 在主线程执行。检查落地代码是否偏离设计和计划，清扫遗留尾巴。内部处理 Release Review（如有发布风险）。

## Step 14：Handle Final Review Return

| Final Review Verdict | Coordinator 动作 |
| --- | --- |
| `FINAL_REVIEW_PASSED` | Step 21（Closing） |
| `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` | Step 21（Closing），Final Review skill 已内部处理 Release Review |
| `NEEDS_EXECUTION` | 回到 Step 11（execution re-entry），只处理 Final Review 标出的具体问题 |
| `NEEDS_DISCOVERY` | design gap 严重到需要回 discovery → 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | plan gap 严重到需要回 plan → 回到 Step 9 |
| `BLOCKED` | 报告用户 |

### Budget 与 Backflow

回到 discovery / plan-writing / execution 时**不重置 `budget_used`**。回流的成本是真实的——Direction Check 在 80% 时仍然触发。Plan revision 改变了 `pack_count` → plan-writing Step 12a 更新 `budget_total = 2N + 12`。

**更新 Budget File**：`last_gate_phase: "final-review"`, `last_gate_timestamp: <now>`。

---

# 第五部分：Route 2 — Bug Investigation

## Step 15：Dispatch root-cause-analyst

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Bug Investigation: <bug title>",
  prompt: "
    ## Bug report
    <paste user's bug description>

    ## Reproduction / symptoms
    <paste error log, failing test, regression description>

    ## Relevant files (if known)
    <paste file paths, modules>

    ## What has been tried
    <paste if user mentioned previous attempts>

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed /
      root cause in design/plan / unable to reproduce / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    - Regression risk: <what could break>
    ### Verification
    ### Open Items
  "
})
```

## Step 16：Handle Analyst Return

| Resolution | Coordinator 动作 |
| --- | --- |
| `fixed` | analyst 已修复代码（未 commit）→ Step 17（Codex review） |
| `root cause found, not fixed` | 修复超出 analyst 能力 → Step 18（派 worker 修复） |
| `root cause in design/plan` | 系统性问题 → 转入 Formal Orchestrate（Route 1）：创建 budget file → 进入 Step 7（discovery），seed with analyst report |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | 报告用户，附 analyst 排除路径和已排除假设，请求协助判断方向 |

### `root cause in design/plan` → Discovery Seed

Coordinator 整理 analyst report 作为 Discovery 的输入 brief：

```text
## Bug-seeded Discovery

原始 bug: <description>
Analyst findings:
- Root cause: <analyst evidence>
- Affected modules: <list>
- Excluded hypotheses: <list>
- Recommended design change: <if analyst provided>

请以此为基础进行 Discovery 讨论，不需要用户从零描述问题。
```

此时执行两项基础设施操作：
1. **更新 Scope Contract**：scope 从 bug investigation 扩大为 full design + plan + execution。更新 `.claude/multi-model-workflow/scope-<run_id>.md` 的 Source artifacts（加入 analyst report）、Editable artifacts（加入 design / plan 预期产出）和 Out of scope。
2. **创建 Budget File**（Step 6）：后续走 Formal Orchestrate 完整管线。

## Step 17：Simple Bug — Codex Review

Analyst 已修复代码。派发 Codex 验证修复正确性：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Bug fix review: <bug title>",
  prompt: "
    --model gpt-5.4

    ## Scope
    Review a bug fix applied by root-cause-analyst.

    ## Bug
    <original bug description>

    ## Root cause
    <analyst's root cause finding>

    ## Fix applied
    <analyst's fix description + changed files>

    ## Review angles
    - Fix addresses the stated root cause
    - No regression introduced
    - Tests cover the fixed behavior
    - Contract integrity maintained (if applicable)

    ## Calibration
    Targeted bug fix review — only assess fix correctness and regression risk.
    Do not expand scope beyond the stated bug.

    ## Return Contract
    ### Verdict
    pass / needs repair / blocked
    ### Evidence
    ### Result
    ### Verification
    ### Open Items
  "
})
```

| Verdict | 动作 |
| --- | --- |
| `pass` | Step 21（Closing） |
| `needs repair` | Coordinator 验证 finding → 路径 A（Coordinator 直接修，≤2 文件）或路径 B（新建 worker 修复）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

## Step 18：Complex Bug — Worker Dispatch

Analyst 找到根因但无法修复。按 risk flags 选择 worker：

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Fix bug: <bug title>",
  prompt: "
    ## Bug
    <original bug description>

    ## Root cause (from analyst investigation)
    <root cause + evidence + excluded hypotheses>

    ## Fix scope
    <affected files from analyst report>

    ## Acceptance criteria
    - [ ] Root cause addressed
    - [ ] Regression tests added
    - [ ] Existing tests pass

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Completed behavior
    ### Verification
    ### Open Items
  "
})
```

Worker 返回 → Codex review（同 Step 17）→ Closing。

---

# 第六部分：Route 3 — Multi-PR Merge

## Step 19：进入 orchestrate-multi-pr-merge

```
Skill({ skill: "orchestrate-multi-pr-merge" })
```

Multi-PR Merge 在主线程执行。Coordinator 读取所有相关文档，派发 explorer 验证 PR 间冲突，解决后派发 Codex 全量 review。

## Step 20：Handle Multi-PR Merge Return

| Verdict | Coordinator 动作 |
| --- | --- |
| `MERGE_COMPLETE` | Step 21（Closing） |
| `NEEDS_REPAIR` | Multi-PR skill 已内部处理修复循环；到这里说明修复失败 → 报告用户 |
| `BLOCKED` | 报告用户 |

---

# 第七部分：Closing

Architecture-draft 结论 11：提交、推送、开 PR 是兜底动作，应自动执行。

## Step 21：Final Verification

```bash
# 确认测试通过
<project test command>

# 确认 git 状态
git status --short
```

如果有 uncommitted changes（Bug route 的 analyst/worker fix）：
```bash
git add <fixed files + test files>
git commit -m "Fix: <bug title — root cause and fix summary>"
```

Formal Orchestrate 的 pack commits 已在 execution 的 Git Checkpoint 完成——此处无需再 commit，除非 Final Review 产生了新的 repair commit。

## Step 22：Push + Open PR

```bash
# Push
git push -u origin <branch>

# 检查是否已有 PR
gh pr list --head <branch> --json number --jq '.[0].number'
```

| 状态 | 动作 |
| --- | --- |
| PR 不存在 | `gh pr create` |
| PR 已存在 | `gh pr edit <number>` 更新 body |
| 无 remote 配置 | 提示用户配置 remote；不自动配置 |

PR body：

```markdown
## Summary
- <1-3 bullet points of what changed>
- Route: Formal Orchestrate / Bug Fix / Multi-PR Merge

## Artifacts
- Design: <path or N/A>
- Plan: <path or N/A>
- Issues created: <GitHub issue refs or N/A>

## Test plan
- <verification commands and results>

## Review history
- Reviews dispatched: <count>
- Findings: <accepted / rejected / out-of-scope counts>
- Repair rounds: <count>

🤖 Generated with [Claude Code](https://claude.com/claude-code) + multi-model-workflow
```

## Step 23：Report to User

一到两句话汇报：做了什么、PR link、关键决策。不做长篇总结。用户需要细节可以问。

## Step 24：Cleanup

```bash
rm .claude/multi-model-workflow/active-run-id
rm .claude/multi-model-workflow/budget-<run_id>.json
rm .claude/multi-model-workflow/scope-<run_id>.md
```

Bug / Multi-PR route 只删 scope file（无 budget file）。

---

# 第八部分：Global Constraints

## Hard Gates

- 没有验证证据，不得声称完成
- Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker
- 每个 phase 的 review 不可跳过（除非 Entry Gate 选择了 Bug Investigation）
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点
- 所有 phase skill 遵守"不存在非阻塞项"铁律——要么当场修复，要么开 GitHub issue

## Sub-agent 隔离

Sub-agent 不读 SKILL.md、不读 references/。每个 dispatch prompt 必须自足——包含 phase、source docs、anchors、verification、risk flags 和 Return Contract。Agent frontmatter `skills:` 字段自动预加载指定 skill，不需要运行时调用 Skill tool。

## Commit 纪律

- Sub-agent 不 commit；Coordinator 在 review/verification 通过后 stage 并提交
- Commit boundary = 回退边界：design/plan repair、通过 review 的 Task Pack、accepted finding repair 分别提交——不混在一个 commit 里
- 不 stage 不属于当前 scope 的 dirty files

## 禁止

- 跳过 Discovery 直接写 plan（除非 Resume Gate 确认 design 已 reviewed）
- 跳过 Plan Review 直接执行
- 跳过 Final Review 直接 Closing
- 用技术语言向用户汇报（用业务语言）
- 自己写生产代码（调度 worker）
- 每 task 一个 sub-agent（用 Task Pack 打包）
- 超过循环上限不处理
