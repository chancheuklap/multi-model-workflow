# Early Release Gate

> **流程位置**：`orchestrate-execution` Step 13 · 仅 pack 触碰发布风险面时进入 · 不触发时跳到 Step 14

Pack Review 通过后，检查该 pack 是否触发 Early Release Gate：

**触发条件**（任一成立）：
- pack 的 `发布风险` 涉及 migration / deploy order / rollback / manual production gate，且必须在后续 pack 实现前决定
- baseline finding 暴露的问题必须先判定 release strategy 才能修
- 等到 Final Review 才审会造成不可逆数据、权限、账务或 runtime 风险
- 用户明确要求

**触发时**：按 `orchestrate-workflow/references/external-review-lanes.md` 定义的方式提交 Codex review 任务。

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/release-gate-N.M.md`：

```markdown
## Scope
    Early Release Gate for Task Pack N.M.
    Code quality and spec compliance have already passed Pack Review.
    Only assess release risk — this pack cannot wait for Final Review.

    ## Pack
    <pack number + title + risk flags>

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

多个相邻 high-risk packs 同一发布风险面时合并一次。Budget：Release Gate 最多 2 个 dispatch（含 early + final），已包含在全局 `2N+12` 预算中。

**Release blocker 修复**：

```
Agent({
  subagent_type: "complex-pack-executor",
  description: "Fix release blocker: Pack N.M <blocker summary>",
  prompt: "
    ## Scope
    修复 Early Release Gate 发现的 release blocker。

    ## Pack
    <pack number + title>

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
