# Bug Investigation Route — Dispatch Templates + Flow

> **流程位置**：`orchestrate-workflow` Steps 15-18 · Route 2 Bug Investigation

## Step 15：Dispatch root_cause_analyst

```
spawn_agent({
  agent_type: "root_cause_analyst",
  message: "
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

Coordinator 整理 analyst report 写入 `.codex/multi-model-workflow/bug-seed-<run_id>.md`：

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
1. **写入 Bug Seed 文件**：写入 `.codex/multi-model-workflow/bug-seed-<run_id>.md`。
2. **更新 Scope Contract**：更新 `.codex/multi-model-workflow/scope-<run_id>.md` 的 Source artifacts（加入 `bug-seed-<run_id>.md`）、Editable artifacts（加入 design / plan）和 Out of scope。
3. **创建 Budget File**（Step 2c）。

## Step 17：Simple Bug — Codex Review

Analyst 已修复代码。

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `model: "gpt-5.5"`, `reasoning_effort: "xhigh"`
   - `cursor.phase in {execution, final-review}` -> `model: "gpt-5.4"`, `reasoning_effort: "xhigh"`
3. Dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>",
       model: "<phase-selected model>",
       reasoning_effort: "xhigh"
     })
     ```
     Record the returned reviewer `agent_id` into `.codex/multi-model-workflow/review-agents/<gate>.agent-id`.
   - **Targeted re-review** (gate name contains `-repair-`):
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Budget: baseline review is counted by `track-review-budget.sh` on `SubagentStart`. Targeted re-review must be counted after `wait_agent` returns by running `bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" budget increment-review --run-id "<run_id>"`.
6. Result: save the reviewer final message from `wait_agent` into `.codex/multi-model-workflow/review-results/<gate>.md`.

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

Compaction recovery: `.agent-id` present but no `review-results/` -> wait for that reviewer agent. If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/bug-fix-review.md`：

```markdown
## Scope
Review a bug fix applied by root_cause_analyst.

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
spawn_agent({
  agent_type: "<pack_executor | complex_pack_executor>",
  message: "
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

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | Codex review（同 Step 17）→ Closing |
| `needs repair` | 读 concerns；正确性问题 → send_input worker 修复；观察性意见 → 记录，进 Codex review |
| `needs context` | send_input 补充上下文给 worker |
| `blocked` | 技术阻塞：换更强模型 / 拆 scope；业务阻塞：询问用户 |

---
> **下一步**：修复通过 Codex review → Closing（`workflow-closing.md`）。root cause in design/plan → 创建 budget file + 转入 Route 1（SKILL.md Steps 7-14）。
