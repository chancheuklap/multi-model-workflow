# Final Review 修复分流 + 截断

> **流程位置**：`orchestrate-final-review` Steps 9-12 · 仅 needs repair 时进入

## Step 9：修复路由

所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 默认自验收（verification commands + acceptance criteria 对照）。仅当满足 exception 条件（3+ 文件控制流修改 / 用户要求 / RCA 根因修复 / Path A 自修）时派发 targeted Codex re-review。Targeted re-review 必须 `send_input` 到 baseline reviewer `agent_id`；只有 source baseline 改变时才 full phase review rerun。

- **路径 A**（≤ 2 文件、不碰合同边界、意图明确）：Coordinator 直接修 → 跑验证 → Step 11
- **路径 B**（多文件、根因已知）：

<!-- BEGIN: sendmessage-resume [variant=worker] -->
**Worker send_input Resume 步骤**（pack_executor / complex_pack_executor 修复）：

1. `state.sh agent-id get --run-id <run_id> --pack-id <pack_id>` 读取 execution-state 中的 agent_id
2. 若返回 null/empty -> 立即标记 BLOCKED 给用户 + `state.sh transition --actor Coordinator --to blocked`（不允许创建新 agent）
3. 调用：
   ```
   send_input({
     target: "<agent_id>",
     message: "<含 DISPATCH_ENVELOPE 的修复 prompt，repair_round >= 1>"
   })
   ```
4. 等待原 agent 返回：`wait_agent({ targets: ["<agent_id>"], timeout_ms: 600000 })`
5. 解析返回结果 → `state.sh transition --actor Coordinator --to returned`
5b. 修复完成后运行 verification commands + 对照 acceptance criteria + grep 确认变更
5c. `state.sh self-verify append --run-id <run_id> --pack-id <pack_id> --repair-round <N> --verification-passed <yes|no> --exception <none|3plus_files_control_flow|user_requested|rca_root_cause|path_a_self_fix>`
6. 写 `state.sh disposition append` 或 `state.sh update --field plans[N].packs[M].repair_round`
<!-- END: sendmessage-resume -->

Worker 修复后返回 → 进入 Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
spawn_agent({
  agent_type: "complex_code_explorer",
  message: "
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

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex_pack_executor）；涉及多个 pack 的系统性问题 → Step 10（判定 Plan 维度）。

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
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `model: "gpt-5.5"`, `reasoning_effort: "xhigh"`
   - `cursor.phase in {execution, final-review, bug-investigation, direct-repair, multi-pr-merge, hotfix, quickfix, maintenance}` -> `model: "gpt-5.4"`, `reasoning_effort: "xhigh"`
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport spawn_agent`.
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
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport send_input`.
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Budget: after `wait_agent` returns for either baseline review or targeted re-review, run `bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" budget increment-review --run-id "<run_id>"`.
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

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/final-review-repair-<round>.md`：

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

每个 gap 最多 3 个 repair round（2 个 Worker/Coordinator round + 1 个 root_cause_analyst round）。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → **截断 Worker 循环**，新建 `root_cause_analyst` |

**Root-Cause-Analyst 截断调度**：

```
spawn_agent({
  agent_type: "root_cause_analyst",
  message: "
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
