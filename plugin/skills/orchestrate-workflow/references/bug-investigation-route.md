# Bug Investigation Route — Dispatch Templates + Flow

> **流程位置**：`orchestrate-workflow` Steps 15-18 · Route 2 Bug Investigation

## Step 15：Dispatch root-cause-analyst

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Bug Investigation: <bug title>",
  prompt: "
    ## 调度场景
    Bug Investigation 入口。用户报告 bug/error/regression，根因不明，从零调查。

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

Coordinator 整理 analyst report 写入 `.claude/multi-model-workflow/bug-seed-<run_id>.md`：

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

此时执行三项基础设施操作：
1. **写入 Bug Seed 文件**：写入 `.claude/multi-model-workflow/bug-seed-<run_id>.md`。
2. **更新 Scope Contract**：更新 `.claude/multi-model-workflow/scope-<run_id>.md` 的 Source artifacts（加入 `bug-seed-<run_id>.md`）、Editable artifacts（加入 design / plan）和 Out of scope。
3. **创建 Budget File**（Step 2c）。

## Step 17：Simple Bug — Codex Review

Analyst 已修复代码。

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (`CODEX_SCRIPT` unset: `CODEX_SCRIPT="$(find ~/.claude/plugins -path '*/codex/scripts/codex-companion.mjs' -type f 2>/dev/null | head -1)"`)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex-reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `--model gpt-5.5 --effort xhigh`
   - `cursor.phase in {execution, final-review}` -> `--model gpt-5.4 --effort xhigh`
3. Dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
   - **Targeted re-review** (gate name contains `-repair-`):
     `node "$CODEX_SCRIPT" task --background --resume --prompt-file <path> <model flags>`
   -> record JOB_ID into `review-prompts/<gate>.job-id`
4. Wait: `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000` (run_in_background: true)
5. Result: `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `review-results/<gate>.md`

**Confidence rubric (REQUIRED in every review prompt)**:
- 1-3: low confidence. Coordinator may suppress without deep investigation.
- 4-6: medium. Coordinator must gather additional evidence before disposition.
- 7-10: high. Coordinator should default to accept unless contradicted by evidence.

**Pre-emit Verification Gate**：

每个 finding 必须满足以下条件才能进入报告：

1. **引用触发 finding 的具体代码行**——file:line + 该行的原始文本。
   - "field X doesn't exist on model Y" → 引用 class Y 的定义体，证明字段缺失
   - "dict.get() might return None" → 引用 dict 的初始化代码
   - "race condition between A and B" → 引用 A 和 B 两处代码

2. **无法引用 = finding 未验证**。将 confidence 强制设为 4-5（从主报告中抑制，移入附录）。
   不要通过虚构 confidence 7+ 来绕过此门槛。

3. **框架元编程特例**：当符号来自 ORM 元类、装饰器、代码生成器时，引用生成该符号的元构造，而非期望在类体中 grep 到字面名称。

**Rationalization Prevention**：
- "This looks fine" 不是 finding。要么引用证据证明确实没问题，要么标记为未验证。
- "likely handled elsewhere" → 读并引用处理代码，或标记 unknown。
- "probably tested" → 给出测试文件和方法名，或标记 unknown。

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

**证据表 (REQUIRED)**：
Reviewer 必须在 `### Evidence` 下填写半结构化证据表。证据表证明 reviewer 实际检查过什么；它不是设计意图摘要，也不能替代阅读 source artifacts。

| 字段 | 必填内容 |
| --- | --- |
| 已读设计 / mockup / plan 来源 | 实际读过的文档、计划、mockup 或用户上下文。 |
| 已检查代码或产物路径 | 已检查的源码、生成产物、state schema、hooks、templates 或文档路径。 |
| 已运行命令或验证 | 实际执行的命令、脚本、测试、build check 或人工验证。 |
| Finding 证据 | 支撑 finding 的路径、行号、diff、命令输出或可复现行为。 |
| 假设 | 影响 verdict 的前提和未被源码直接证明的判断。 |
| 未验证项 | 相关但未能验证的内容，以及原因。 |

Compaction recovery: `.job-id` present but no `review-results/` -> resume from Step 4.
<!-- END: review-dispatch -->

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/bug-fix-review.md`：

```markdown
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
```

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`，补充上下文后重新 dispatch，不进入 per-finding 处理。

| Verdict | 动作 |
| --- | --- |
| `pass` | Step 21（Closing） |
| `needs repair` | Coordinator 验证 finding → 路径 A（Coordinator 直接修，≤2 文件）或路径 B（新建 worker 修复）→ targeted re-review（重用 Step 17 模板，scope 缩小到修复 diff）→ 最多 2 轮 → Closing |
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

Worker 返回处理：

<!-- BEGIN: repair-routing -->
## 统一修复分流

所有 review repair 先由 Coordinator 对 accepted findings 做亲验和 disposition；未 accepted 的 finding 不进入修复。修复 prompt 只携带 accepted finding、证据、scope、受影响文件、验证门槛和 targeted re-review 范围。

| Finding / 修复形态 | Claude plugin 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 自修，随后运行对应验证。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 通过现有 `SendMessage` resume 原 `pack-executor`；没有可用 agent id 时按当前 phase 的阻塞规则处理。 |
| 跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板问题 | 使用 `complex-pack-executor` 路径，修复 prompt 写清 owner / provider / consumer / migration / deploy order / rollback / manual gate。 |
| 根因不清，只知道症状 | 先派 `code-explorer` 或 `complex-code-explorer` 做只读调查，拿到 confirmed root cause 后再进入 Path A、原 worker 或 complex path。 |
| 系统性 bug、重复修复失败、未知 regression | 使用 `root-cause-analyst` 路径；要求列可证伪假设、排除证据和下一步修复方向。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，把 affected plans、affected packs、producer / consumer 断点和必须重跑的验证交给 execution repair。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing；不要用代码临时补设计缺口。 |
| Path A repair targeted re-review 失败 | 升级 Path B，优先 `SendMessage` 原 worker；跨边界则走 `complex-pack-executor`。 |

**Claude-native dispatch 规则**：
- 新派发使用 `Agent({ subagent_type: "<agent-name>", ... })`；已有 worker / plan-writer 修复优先使用 `SendMessage({ to: "<agent_id>", ... })` resume。
- Agent 名使用 Claude plugin 现有连字符：`pack-executor`、`complex-pack-executor`、`code-explorer`、`complex-code-explorer`、`root-cause-analyst`、`plan-writer`。
- Review 修复后的 targeted re-review 使用现有 `codex-companion.mjs` review dispatch；repair gate 使用独立 gate 名，不能覆盖 baseline 结果。
- 本分流块只定义 owner 和升级条件；各 phase 的 round 上限、state 写入和 release gate 仍以所在 reference 为准。

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

回归证据必须包含以下至少一项：
- 先失败后通过的 public-behavior test、contract test、migration / schema test 或 build/template check。
- 相关验证命令及结果，能覆盖 accepted finding 的修复面。
- 无法自动化时写明 `manual validation gate`：人工检查对象、检查步骤、通过标准和 release 前责任人。

Release Gate 在宣布 review repair 完成前，必须确认每个 accepted finding 都有回归证据或 `manual validation gate`。
<!-- END: repair-routing -->

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | Codex review（同 Step 17）→ Closing |
| `needs repair` | 读 concerns；正确性问题 → SendMessage worker 修复；观察性意见 → 记录，进 Codex review |
| `needs context` | SendMessage 补充上下文给 worker |
| `blocked` | 技术阻塞：换更强模型 / 拆 scope；业务阻塞：询问用户 |

---
> **下一步**：修复通过 Codex review → Closing（`workflow-closing.md`）。root cause in design/plan → 创建 budget file + 转入 Route 1（SKILL.md Steps 7-14）。
