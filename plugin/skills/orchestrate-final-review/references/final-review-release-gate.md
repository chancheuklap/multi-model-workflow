# Final Release Gate

> **流程位置**：`orchestrate-final-review` Steps 16-18 · 仅 diff 触碰发布风险面时进入 · 不触发时跳到 Step 19

## Step 16：判断是否触发 Final Release Gate

清扫完成后，检查最终 diff 是否触碰发布风险面。

**触发条件**（任一成立）：
- diff 触碰 migration
- diff 触碰 billing / 账务
- diff 触碰 permission / 权限
- diff 触碰 runtime / 进程管理
- diff 触碰 cross-service contract
- diff 触碰 deploy order / rollback strategy
- diff 触碰 manual production gate
- diff 触碰 API compatibility（对外 API 变更）

**不触发时** → Step 19（业务汇报）。

**Execution 已通过 Early Release Gate 的 risk surface** → 已覆盖的不重审。只审新增的或 Final Review 修复引入的发布风险面。

## Step 17：派发 Release Reviewer

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

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/final-release-gate.md`：

```markdown
## Scope
Release-risk review for the final implementation.
Code quality and spec compliance have already passed.
Only assess release risk.

## Full diff
git diff <starting_commit>..HEAD

## Risk surface
<specific risk areas triggered>

## 发布风险和人工门禁
<paste from plan>

## Already covered by Early Release Gate
<list of risk surfaces already reviewed during Execution, if any>

## Review focus
- Migration 安全：顺序、回滚、数据完整性
- Deploy order：服务依赖、API 兼容、蓝绿/灰度策略
- Permission / billing：权限变更、账务一致性、审计链
- Runtime：进程管理、重启安全、状态恢复
- Rollback：每个变更是否可安全回滚
- Manual gate：是否所有 manual production gate 都有验证证据

## Release blocker 定义
以下为 release blocker（必须修复才能发布）：
- 数据丢失或无法回滚
- 权限绕过
- 账务不一致
- 合同未同步（provider 改了 consumer 没跟）
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

Budget：Release Gate 最多 2 个 dispatch（含 early + final），已包含在全局 `3P+12` 预算中。如果 Execution 已用 1 个 early release gate，此处还有 1 个。

## Step 18：处理 Release Gate 结果

| Release Gate Verdict | 动作 |
| --- | --- |
| `pass` | 记录 release review 通过 → Step 19 |
| `needs repair` | 修复 release blocker |
| `blocked` | 报告用户 |

**Release blocker 修复**：

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
<!-- END: repair-routing -->

1. 评估 blocker 严重程度和修复范围
2. 简单（≤ 2 文件、修复方向明确）→ Coordinator 直接修
3. 复杂 → 派 `complex-pack-executor`：

```
Agent({
  subagent_type: "complex-pack-executor",
  description: "Fix Final Release blocker: <blocker summary>",
  prompt: "
    ## Scope
    修复 Final Release Gate 发现的 release blocker。

    ## Release blocker
    <paste accepted blocker finding — severity / locator / evidence / impact / remediation>

    ## Risk surface
    <migration / deploy / rollback / permission / billing / runtime>

    ## Source design
    <path>

    ## Affected files
    <list>

    ## Acceptance criteria
    - [ ] Release blocker 已修复
    - [ ] 回归测试通过
    - [ ] 不引入新的发布风险
    - [ ] 不改变 source design / plan 的 baseline

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

4. 需要用户决策（如 rollback 策略选择）→ 询问用户
5. 修复后做 targeted release re-review：只审修复变更 + 原 release risk surface。不重跑 baseline review（除非修复改变了 source design / plan / shared contract / migration / permission / billing / runtime baseline）

Release blocker 修复最多 2 轮。超过 → BLOCKED，报告用户。

---
> **下一步**：Release Gate 通过 → Step 19（回到 `final-review-completion.md` 业务汇报）。BLOCKED → 返回 verdict。
