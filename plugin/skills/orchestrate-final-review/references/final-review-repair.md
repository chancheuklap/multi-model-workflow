# Final Review 修复分流 + 截断

> **流程位置**：`orchestrate-final-review` Steps 9-12 · 仅 needs repair 时进入

## Step 9：修复路由

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

所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 默认自验收（verification commands + acceptance criteria 对照）。仅当满足 exception 条件（3+ 文件控制流修改 / 用户要求 / RCA 根因修复 / Path A 自修）时派发 targeted Codex re-review。Targeted re-review 必须用 `codex-companion.mjs task --background --resume` 复用 baseline reviewer 的 JOB_ID；只有 source baseline 改变时才 full phase review rerun。gate-codex-review.sh 强制此规则。

- **路径 A**（≤ 2 文件、不碰合同边界、意图明确）：Coordinator 直接修 → 跑验证 → Step 11
- **路径 B**（多文件、根因已知）：

<!-- BEGIN: sendmessage-resume [variant=worker] -->
**Worker SendMessage Resume 步骤**（pack-executor / complex-pack-executor 修复）：

1. `state.sh agent-id get --run-id <run_id> --pack-id <pack_id>` 读取 execution-state 中的 agent_id
2. 若返回 null/empty -> 立即标记 BLOCKED 给用户 + `state.sh transition --actor Coordinator --to blocked`（不允许创建新 agent）
3. 将完整修复 prompt 写入 `.claude/multi-model-workflow/worker-prompts/<pack-id>-repair-<round>.md`。该文件必须以 DISPATCH_ENVELOPE 开头，包含 accepted findings、Coordinator 亲验证据、repair scope、verification commands 和 Return Contract。调用 SendMessage 时只发送该文件全文，不在 tool call message 里另写补充说明。
4. 调用：
   ```
   SendMessage({
     to: "<agent_id>",
     summary: "修复 <finding_ids>",
     message: "<full contents of .claude/multi-model-workflow/worker-prompts/<pack-id>-repair-<round>.md>"
   })
   ```
5. 等待 SendMessage 返回（同步）
6. 解析返回结果 → `state.sh transition --actor Coordinator --to returned`
6b. 修复完成后运行 verification commands + 对照 acceptance criteria + grep 确认变更
6c. `state.sh self-verify append --run-id <run_id> --pack-id <pack_id> --repair-round <N> --verification-passed <yes|no> --exception <none|3plus_files_control_flow|user_requested|rca_root_cause|path_a_self_fix>`
7. 写 `state.sh disposition append` 或 `state.sh update --field plans[N].packs[M].repair_round`
<!-- END: sendmessage-resume -->

Worker 修复后返回 → 进入 Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
Agent({
  subagent_type: "complex-code-explorer",
  description: "Investigate unknown root cause: Final Review finding",
  prompt: "
    ## Scope
    只读调查。Final Review 报告了症状但无法确定根因。找到根因，不写代码。

    ## 症状描述
    <paste accepted finding — severity / locator / evidence / impact>

    ## 已知上下文
    - Source design: <path>
    - Plan: <path>
    - Affected packs: <list>
    - 相关文件: <affected files>
    - Git diff scope: git diff <starting_commit>..HEAD

    ## 调查方向
    <Coordinator 初步判断——跨 pack 交互 / 时序 / 隐式依赖 / 合同闭合 / 状态污染等>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 files / tests / logs / commands
    ### Result
    - Facts: confirmed facts with locators
    - Root cause assessment: <root cause + evidence, if found>
    - Recommended fix direction: <路径 A（Coordinator 直接修）/ 路径 B（Worker 修）+ 理由>
    - Excluded paths: hypotheses checked and ruled out with evidence
    - Recommended next probe: <if root cause not found>
    ### Verification
    ### Open Items
  "
})
```

Explorer 返回后路由：

| Explorer Result | 动作 |
| --- | --- |
| Root cause found + 推荐路径 A | Coordinator 直接修复 → Step 11 |
| Root cause found + 推荐路径 B | 派 Worker 修复 → Step 11 |
| Root cause not found | 报告用户，附 explorer 已排除路径 |

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex-pack-executor）；涉及多个 pack 的系统性问题 → Step 10（判定 Plan 维度）。

---

## Step 10：Implementation Gap 回 Execution 的判定

如果 accepted findings 涉及多个 pack 的系统性问题（不是单点修复），Coordinator 先判断 **Plan 维度**，再决定路由：

### Step 10a：Plan 维度判定

| 情况 | 路由 |
| --- | --- |
| 所有 affected packs 属于**同一 Plan** | **留在 Final Review**——按 Path B 修复 + 该 Plan targeted re-review（Step 11）。不回 Execution |
| Affected packs **跨越多个 Plan** 且系统性（shared contract / migration 顺序 / cross-plan state） | → Step 10b（回 Execution 判定） |

### Step 10b：回 Execution 的条件（任一成立）

- 跨 Plan 的系统性问题（shared contract 不一致、migration 顺序错误、cross-plan state 竞争）
- 需要重新执行某个完整 pack
- plan 的 Source Coverage Map 有未覆盖的 intent 需要新 pack 实现
- 修复影响其它 Plan 的 dependencies 或 contract surface

**留在 Final Review 修复的条件**（即使跨 Plan）：
- 涉及 1-2 个 pack 的少量文件
- 修复范围明确、不影响其它 pack
- 不需要新 pack

回 Execution → 读 budget file `execution_reflux_count`：0 → 可回流，返回 `NEEDS_EXECUTION` verdict，附 accepted findings 和 affected packs 及所属 Plan；≥1 → BLOCKED 报告用户。

---

## Step 11：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (`CODEX_SCRIPT` unset: `CODEX_SCRIPT="$(find ~/.claude/plugins -path '*/codex/scripts/codex-companion.mjs' -type f 2>/dev/null | head -1)"`)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex-reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `--model gpt-5.5 --effort xhigh`
   - `cursor.phase in {execution, final-review, bug-investigation, direct-repair, multi-pr-merge, hotfix, quickfix, maintenance}` -> `--model gpt-5.4 --effort xhigh`
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --transport Agent --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`
     Then record the dispatch: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<JOB_ID>"`.
   - **Targeted re-review** (gate name contains `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --transport SendMessage --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --resume --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`. The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer's recorded JOB_ID.
   - **Over-budget escape hatch**: if Review Budget is exhausted and the user explicitly asks to continue with another review, append `--allow-over-budget --override-reason "<brief user authorization>"` to the validate command and to the later complete command. Do not use this flag for convenience or for Effort Budget.
4. Wait: `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000` (run_in_background: true)
5. Result: `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `review-results/<gate>.md`
6. Complete: run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" --run-id "<run_id>" --gate "<gate>" --agent-id "<JOB_ID>" --result-file ".claude/multi-model-workflow/review-results/<gate>.md"` to mark the result durable and increment review budget exactly once. If Step 3 used the over-budget escape hatch, pass the same `--allow-over-budget --override-reason "<brief user authorization>"` here.
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
- `.job-id` present but no `review-results/<gate>.md` -> resume from Step 4 (wait + result) using that JOB_ID; once the result is saved and bookkeeping is complete, proceed to Step 6.
- `review-registry/<gate>.json` status is `completed` or `disposition_started`, and `review-results/<gate>.md` exists -> Read that exact result file and continue Coordinator disposition. Do not re-dispatch review and do not proceed to repair until `record-review-disposition.sh --status completed` has been recorded.
- If the `.job-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/final-review-repair-<round>.md`：

```markdown
## Scope
Targeted re-review for Final Review repair.
Only review the changes made to address the listed findings.

## Original findings
<paste accepted findings>

## Repair diff
<git diff of repair changes>

## Changed files
<repair-affected files only>

## Contract anchors
<if repair touches contract boundaries>

## Review focus
- Each accepted finding has been addressed
- Repair does not introduce new issues
- Verification commands pass

## Calibration
只验证修复是否解决了原始 finding。不做全面重审。

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
Per-finding status:
- <finding 1>: resolved / still present / new issue
### Verification
### Open Items
```


---

## Step 12：修复截断

每个 gap 最多 3 个 repair round（2 个 Worker/Coordinator round + 1 个 root-cause-analyst round）。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → **截断 Worker 循环**，新建 `root-cause-analyst` |

**Root-Cause-Analyst 截断调度**：

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Investigate Final Review repair failure: <finding>",
  prompt: "
    ## 调度场景
    Repair Truncation（Final Review）。Final Review 修了两轮，reviewer 仍报 needs repair。

    ## 前两轮上下文
    - Round 1 accepted findings: <paste>
    - Round 1 修复内容: <paste>
    - Round 2 accepted findings: <paste>
    - Round 2 修复内容: <paste>
    - Git diff scope: <paste>

    ## Source context
    - Source design: <path>
    - Plan: <path>
    - Affected packs: <list>

    ## 你的任务
    不要重复前两轮的修复方法。从不同维度切入——时序、状态污染、隐式依赖、配置漂移、跨 pack 交互。

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed / root cause in design/plan / unable to reproduce / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    - Regression risk: <what could break>
    ### Verification
    ### Open Items
  "
})
```

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

---
> **下一步**：修复通过 → Step 13（`final-review-completion.md`）。BLOCKED → 返回 verdict。
