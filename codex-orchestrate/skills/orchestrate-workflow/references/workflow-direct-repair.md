# Direct Repair（READY_FOR_REPAIR mini-route）

> **流程位置**：`orchestrate-workflow` Step 8a · 仅 Discovery 返回 `READY_FOR_REPAIR` 时进入

已批准 design 下的明确实现偏离。不走完整 Formal Orchestrate——派 worker 修复 + Codex review + Closing。

## 1. 派 Worker（按 risk flags 选择 agent）

```
spawn_agent({
  agent_type: "<pack_executor | complex_pack_executor>",
  message: "
    ## Scope
    修复已批准 design 下的实现偏离。

    ## Source design
    <path>（已通过 Design Review）

    ## Deviation
    <current behavior vs design intent>

    ## Fix scope
    <affected files>

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

## 2. Codex Review

<!-- BEGIN: review-dispatch -->
**Codex review dispatch**

1. Write prompt -> `.codex/multi-model-workflow/review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select review kind:
   - Design Review / Plan Review / issue hierarchy review -> `--review-kind document`
   - Implementation / bug / direct repair / final / integration / release-risk review -> `--review-kind code`
3. Dispatch through native Codex Review:
   - **Baseline review** (gate name does not contain `-repair-`):
     `bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" submit --lane codex --review-kind <document|code> --prompt-file <path> --result-file <result-path>`
   - **Targeted re-review** (gate name contains `-repair-`):
     `bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" submit --lane codex --review-kind <document|code> --resume --prompt-file <path> --result-file <result-path>`
   -> record JOB_ID into `.codex/multi-model-workflow/review-prompts/<gate>.job-id`
   -> baseline job files record Codex `thread_id`; targeted re-review must resume that thread and must fail if no completed baseline thread exists.
4. Wait: `bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" status --job-id "$(cat .codex/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000`
5. Result: `bash "$PLUGIN_ROOT/scripts/review/review-lane.sh" fetch --job-id "$(cat .codex/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `.codex/multi-model-workflow/review-results/<gate>.md`

Model routing is mandatory and lives in `review-lane.sh`:
- document review -> `gpt-5.5` / `xhigh`
- code review -> `gpt-5.4` / `xhigh`

Claude Review is not part of the Codex runtime. All formal and ad-hoc review lanes use native Codex Review.

**Confidence rubric (REQUIRED in every review prompt)**:
- 1-3: low confidence. Coordinator may suppress without deep investigation.
- 4-6: medium. Coordinator must gather additional evidence before disposition.
- 7-10: high. Coordinator should default to accept unless contradicted by evidence.

**Pre-emit Verification Gate**：

每个 finding 必须满足以下条件才能进入报告：

1. **引用触发 finding 的具体代码行**——file:line + 该行的原始文本。
   - "field X doesn't exist on model Y" -> 引用 class Y 的定义体，证明字段缺失
   - "dict.get() might return None" -> 引用 dict 的初始化代码
   - "race condition between A and B" -> 引用 A 和 B 两处代码

2. **无法引用 = finding 未验证**。将 confidence 强制设为 4-5（从主报告中抑制，移入附录）。
   不要通过虚构 confidence 7+ 来绕过此门槛。

3. **框架元编程特例**：当符号来自 ORM 元类、装饰器、代码生成器时，引用生成该符号的元构造，而非期望在类体中 grep 到字面名称。

**Rationalization Prevention**：
- "This looks fine" 不是 finding。要么引用证据证明确实没问题，要么标记为未验证。
- "likely handled elsewhere" -> 读并引用处理代码，或标记 unknown。
- "probably tested" -> 给出测试文件和方法名，或标记 unknown。

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery: `.job-id` present but no `review-results/` -> resume from Step 4.
<!-- END: review-dispatch -->

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/direct-repair-review.md`：

```markdown
## Scope
Review a direct repair for design deviation.

## Source design
<path>

## Deviation and fix
<description + changed files>

## Review angles
- Fix aligns with design intent
- No regression / scope creep
- Contract integrity maintained

## Calibration
Targeted repair review only.

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
### Verification
### Open Items
```

## 3. Handle Review Return

| Verdict | 动作 |
| --- | --- |
| `pass` | Closing |
| `needs repair` | 路径 A（≤2 文件直接修）或路径 B（send_input/resume_agent worker）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

Direct Repair 不创建 budget file。

---
> **下一步**：Codex review 通过 → Closing（`workflow-closing.md`）。BLOCKED → 返回 verdict。
