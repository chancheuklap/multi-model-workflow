# Early Release Gate

> **流程位置**：`orchestrate-execution` Step 13 · 仅 Plan 中有 Pack 触碰发布风险面时进入 · 不触发时跳到 Step 14

Plan Implementation Review 通过后，检查该 Plan 中是否有任何 Pack 触发 Early Release Gate：

**触发条件**（任一成立）：
- Plan 内任何 pack 的 `发布风险` 涉及 migration / deploy order / rollback / manual production gate，且必须在后续 Plan 实现前决定
- Plan Implementation Review finding 暴露的问题必须先判定 release strategy 才能修
- 等到 Final Review 才审会造成不可逆数据、权限、账务或 runtime 风险
- 用户明确要求

**触发时**：

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Reviewer model and reasoning come from `agents/codex_reviewer.toml`. Do not pass per-phase model overrides in the dispatch call; the TOML agent config is the source of truth.
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport spawn_agent`.
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>"
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

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/release-gate-plan-N.md`：

```markdown
## Scope
Early Release Gate for Plan N: <plan title>.
Code quality and spec compliance have already passed Plan Implementation Review.
Only assess release risk — this Plan cannot wait for Final Review.

## Plan
<plan number + title>

## Packs with release risk
<list packs that triggered this gate, with their risk flags>

## Changed files
<list from worker return>

## Risk surface
<specific risk areas: migration / deploy order / rollback / manual gate / billing / permission / runtime>

## 发布风险和人工门禁
<paste from plan>

## Review focus
- Migration 安全：顺序、回滚、数据完整性
- Deploy order：服务依赖、API 兼容
- Permission / billing：权限变更、账务一致性
- Runtime：进程管理、重启安全
- Rollback：每个变更是否可安全回滚
- Manual gate：是否有验证证据

## Release blocker 定义
- 数据丢失或无法回滚
- 权限绕过
- 账务不一致
- 合同未同步
- registry / migration / catalog 未闭合
- deploy order 导致 401/500
- release gate 无验证证据

## Calibration
只标记 release blocker。代码质量、风格、设计——不在此 review 范围。

## Return Contract
### Verdict
pass / blocked / needs repair
### Evidence
### Result
Release Risk:
Blockers:
Manual verification needed:
Rollback assessment:
Deploy order assessment:
### Verification
### Open Items
```

多个 Plan 涉及同一发布风险面时，在最后一个相关 Plan 的 Release Gate 中统一审查。Budget：Release Gate 最多 2 个 dispatch（含 early + final），已包含在全局 `3P+12` 预算中。

**Release blocker 修复**：

```
spawn_agent({
  agent_type: "complex_pack_executor",
  message: "
    [repair-round-N]
    ## Scope
    修复 Early Release Gate 发现的 release blocker。

    ## Plan
    <plan number + title>
    ## Affected packs
    <affected pack numbers>

    ## Release blocker
    <paste accepted blocker finding — severity / locator / evidence / impact / remediation>

    ## Risk surface
    <migration / deploy / rollback / permission / billing / runtime>

    ## Affected files
    <list>

    ## Acceptance criteria
    - [ ] Release blocker 已修复
    - [ ] 回归测试通过
    - [ ] 不引入新的发布风险

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Fix applied per blocker
    - Rollback impact: <if applicable>
    ### Verification
    ### Open Items
  "
})
```

修复后只做 targeted release re-review（scope 缩小到修复 diff + 原 release risk surface）。

---
> **下一步**：通过 → Step 14（execution-completion.md）。需修复 → targeted release re-review。BLOCKED → 返回 verdict。
