# Bug Investigation Route — Dispatch Templates + Flow

> **流程位置**：`orchestrate-workflow` Steps 15-18 · Route 2 Bug Investigation

## Self-Read Protocol

你是 root-cause-analyst。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`bug_context`（包含 `description`、`error_log`、`file_paths[]`、`previous_attempts`）。
2. 读 `bug_context.file_paths[]` 中列出的所有相关源文件，理解 bug 所在上下文。
3. 读本文件（你正在读的这份手册），理解 Return Contract 格式与 Coordinator 处置路由。
4. 独立调查根因，遵循假设驱动流程：列假设 → 寻证据 → 排除 → 得结论。
5. 输出 Verdict，说明 Resolution、Root cause、Fix（若已修复）、Excluded hypotheses、Regression risk。

## Step 15：Dispatch root-cause-analyst

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Bug Investigation: <bug title>",
  prompt: "
    ## 调度场景
    Bug Investigation 入口。用户报告 bug/error/regression，根因不明，从零调查。

    ## Bug context
    读 `DISPATCH_ENVELOPE.bug_context`，该字段包含：
    - `description`: 用户报告的 bug 描述
    - `error_log`: 错误日志、失败测试、regression 描述（若有）
    - `file_paths`: 相关文件路径列表（若已知）
    - `previous_attempts`: 用户提到的已尝试修复方式（若有）

    注：`envelope.bug_context` 由 Coordinator 在派发时填入 `DISPATCH_ENVELOPE` JSON 块。

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

Claude-native flow split-of-concerns:
- Coordinator runs `codex-companion.mjs` via Bash; the PostToolUse hook
  `hooks/track-review-budget.sh` auto-counts review budget the moment the
  `result` command fires (cap-guarded — won't double-count past exhaustion).
- The validate / record / complete scripts handle envelope checks, registry
  durability, and disposition recovery anchors — they do *not* touch budget
  counting (that's the hook's job on Claude).

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex-reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `--model gpt-5.5 --effort xhigh`
   - `cursor.phase in {execution, final-review, bug-investigation, direct-repair, multi-pr-merge, hotfix, quickfix, maintenance}` -> `--model gpt-5.4 --effort xhigh`
3. Validate envelope and dispatch (baseline vs targeted re-review — derived from `review_intent`):
   - **Baseline review** (envelope `review_intent: "baseline"`; gate name does not contain `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`
     Then write the registry entry: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<JOB_ID>"`.
   - **Targeted re-review** (envelope `review_intent: "targeted-re-review"`; gate name contains `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --resume --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`. The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer's recorded JOB_ID.
   - **Over-budget escape hatch**: if Review Budget is exhausted and the user explicitly authorizes another review, append `--allow-over-budget --override-reason "<brief user authorization>"` to the validate command (lets the dispatch through) and to the later complete command (records the override in the registry). Do not use this flag for convenience or for Effort Budget.
4. Wait: `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000` (run_in_background: true)
5. Result: `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `review-results/<gate>.md`
   - The `track-review-budget` hook auto-increments review_used here (cap-guarded).
6. Mark durable: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" --run-id "<run_id>" --gate "<gate>" --agent-id "<JOB_ID>" --result-file ".claude/multi-model-workflow/review-results/<gate>.md"`. If Step 3 used the over-budget escape hatch, pass the same `--allow-over-budget --override-reason "<brief user authorization>"` here to record the override in the registry.
6b. Disposition recovery anchor: before reading findings for disposition, run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-disposition.sh" --run-id "<run_id>" --gate "<gate>" --status started`; after all findings have disposition records, run the same command with `--status completed`.

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

**证据表 (REQUIRED)**：
Reviewer 必须在 `### Evidence` 下填写半结构化证据表。证据表证明 reviewer 实际检查过什么；它不是设计意图摘要，也不能替代阅读 source artifacts。

| 字段 | 必填内容 |
| --- | --- |
| 已读设计 / mockup / plan 来源 | 实际读过的 design、mockup、plan、issue、Scope Contract 或 review baseline 路径。没有对应来源时写 `不适用`，不能留空。 |
| 已检查代码或产物路径 | 实际检查的源码、生成产物、state schema、hooks、templates、文档或 runtime contract 路径。 |
| 已运行命令或验证 | 实际执行的命令、测试、build check、schema check、browser smoke 或 manual gate；未运行时写明原因。 |
| Finding 证据 | 每个 finding 的路径、行号、diff、命令输出或可观察行为；无证据的 finding 必须移入低置信度观察。 |
| 假设 | 影响 verdict 的前提，例如环境、账号、fixture、平台或 reviewer 未能直接验证的 upstream 状态。 |
| 未验证项 | 相关但未验证的内容和原因；没有未验证项时写 `无`。 |

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery:
- `.job-id` present but no `review-results/<gate>.md` -> resume from Step 4 (status + result) using that JOB_ID; once the result is saved and bookkeeping is complete, proceed to Step 6.
- `review-registry/<gate>.json` status is `completed` or `disposition_started`, and `review-results/<gate>.md` exists -> Read that exact result file and continue Coordinator disposition. Do not re-dispatch review and do not proceed to repair until `record-review-disposition.sh --status completed` has been recorded.
- If the `.job-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.

**Targeted re-review scope 收窄**：
当 envelope `review_intent=targeted-re-review` 且 `disposition_refs` 非空时，reviewer 只审 disposition_refs 中 finding 关联的 [Pack N.M] 对应 owned files；不重审全 Plan diff。新增问题超出 disposition scope → 列入 `Out of scope observations` 而非 finding。
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
**Finding-to-owner 修复分流 (REQUIRED)**：

这套规则在 reviewer 已经产出 finding、Coordinator 完成 disposition 之后使用。它不对 review 内容预先分风险等级，只根据 finding 的风险面、根因清晰度和修复形态选择 owner。

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 可自修；修完必须验证，Path A targeted re-review 失败时升级 Path B。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 使用 `SendMessage({ to: "<agent_id>", ... })` 续修原 `pack-executor`；已有 agent_id 时不得新建同类 worker。 |
| 高风险或跨边界修复：跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板 | 如果原 worker 是 `complex-pack-executor` 且仍适合承接，使用 `SendMessage` 续修原 agent；如果原 worker 是 `pack-executor`，或 finding 证明原 owner 不具备高风险合同能力，必须升级 owner。Formal Execution 中先形成新的 repair Pack / 回到 Execution 边界，再按新的 pending pack 派发 `complex-pack-executor`；non-execution route 中使用新的 route-worker escalation dispatch。两种情况都必须记录 `original_agent_id`、`context_ref`、`disposition_ref` 和 accepted finding refs。 |
| 根因不清，只知道症状 | 先派 `code-explorer` 或 `complex-code-explorer` 做只读补证；确认根因前不 patch。 |
| 系统性 bug、重复修复失败、未知 regression | 派 `root-cause-analyst`，要求列可证伪假设、排除证据和回归验证。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，附 affected plans / packs / 连接面 / producer-consumer 断点，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing；不得用代码 patch 代替 source artifact 修复。 |
| Release blocker | 简单且不碰合同边界可 Path A；涉及 migration / deploy order / rollback / permission / billing / runtime 时派 `complex-pack-executor`。 |
| Multi-PR 合并冲突 | 简单冲突可 Coordinator 修；跨 PR 合同、迁移、状态或依赖冲突派 `complex-pack-executor`；系统性冲突派 `root-cause-analyst`。 |

调度纪律：
- Targeted repair 默认优先 `SendMessage` 续修原 agent；但高风险 finding 不能被原普通 worker 绑定。如果原 worker 是 `pack-executor`，Coordinator 必须写明 `escalation_reason`，并按当前 route 的状态模型升级 owner。
- Formal Execution 的升级不能对同一个 `pack_id` 再次 `Agent({...})`：`validate-pack-dispatch.sh` 只允许 pending pack 首次派发，已有 `agent_id` 的同一 pack 普通修复只能 `SendMessage` 原 agent。若 accepted finding 证明必须换成 `complex-pack-executor`，Coordinator 必须回到 Execution/Plan 边界，把修复表达成新的 repair Pack 或 plan revision，使其拥有新的 `pack_id`、pending status、完整 Pack Brief 和独立 dispatch；不能用第二个 agent 冒充同一 Pack 的续修。
- Non-execution route 的升级派发不是原 worker 的续修：使用 `validate-route-worker-dispatch.sh --transport Agent`，envelope 里 `agent_id: null`、`pack_id: null`、`repair_round` 保留当前轮次、`idempotency_key` 使用新的 escalation key，并用 `record-route-worker-dispatch.sh` 写入独立 `.agent-id` 文件。只有同一 owner 的普通 follow-up 才使用 `SendMessage` 续修原 agent；缺失原 `agent_id` 仍然 BLOCKED，不能用新 worker 冒充续修。
- 升级派发 prompt 必须带上 `original_agent_id`、`context_ref`、`disposition_ref`、accepted findings、已确认风险面和回归证据要求，保证新 `complex-pack-executor` 能追溯原 context。
- `Path A` 只适用于真正小范围修复；失败或 targeted re-review 返回 `needs repair` 时必须升级，不重复同一修法。
- `needs evidence` finding 先补证再决定 owner。
- 所有 repair prompt 只携带 accepted findings 和 Coordinator 亲验后的修复指令，不转发 reviewer 原始输出。

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

| Finding 类型 | 优先证据 |
| --- | --- |
| Public behavior bug | 现有或新增 behavior / integration test。 |
| 合同、schema、migration、生成产物 bug | 合同检查、schema validation、migration check 或 build check。 |
| UI 行为 bug | Browser smoke、screenshot、DOM state validation 或现有 UI test。 |
| permission、billing、runtime、state machine、hook 问题 | integration check、state transition check、hook test，或带 owner 和步骤的 manual validation gate。 |
| 文档或 plan mismatch | 文档一致性证据和修正后的 source 链接。 |
| 只能环境验证的问题 | 明确 owner、命令、预期结果和阻塞条件的 manual validation gate。 |

Repair Return Contract 必须补充：
- `Regression evidence`: 命令、测试、build/schema/migration/hook check、browser evidence，或 manual validation gate。
- `Test choice`: 说明为何使用现有测试、新增高层测试、合同检查或 manual gate；不得为纯实现细节新增脆弱测试。
- `Unverified`: 仍未验证的边界和原因；没有则写 `无`。
<!-- END: repair-routing -->

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | Codex review（同 Step 17）→ Closing |
| `needs repair` | 读 concerns；正确性问题 → SendMessage worker 修复；观察性意见 → 记录，进 Codex review |
| `needs context` | SendMessage 补充上下文给 worker |
| `blocked` | 技术阻塞：换更强模型 / 拆 scope；业务阻塞：询问用户 |

## Coordinator 端最小职责

Coordinator 在派发 root-cause-analyst 时只需完成以下动作，其余由 analyst 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`phase: "bug-investigation"`、`agent_role: "root-cause-analyst"`。
2. 在 `envelope.bug_context` 中写入 `description`、`error_log`（若有）、`file_paths[]`（若已知）、`previous_attempts`（若有）。
3. 触发 `state.sh` 记录 analyst 派发状态，保存 `agentId` 以备 SendMessage 补充上下文。
4. 等待 analyst 返回，按 Step 16 路由表处置 Resolution。

---
> **下一步**：修复通过 Codex review → Closing（`workflow-closing.md`）。root cause in design/plan → 创建 budget file + 转入 Route 1（SKILL.md Steps 7-14）。
