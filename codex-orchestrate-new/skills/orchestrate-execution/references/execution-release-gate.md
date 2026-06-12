# Early Release Gate

> **流程位置**：`orchestrate-execution` Step 13 · 仅 Plan 中有 Pack 触碰发布风险面时进入 · 不触发时跳到 Step 14

Plan Implementation Review 通过后，检查该 Plan 中是否有任何 Pack 触发 Early Release Gate：

**触发条件**（任一成立）：
- Plan 内任何 pack 的 `发布风险` 涉及 migration / deploy order / rollback / manual production gate，且必须在后续 Plan 实现前决定
- Plan Implementation Review finding 暴露的问题必须先判定 release strategy 才能修
- 等到 Final Review 才审会造成不可逆数据、权限、账务或 runtime 风险
- 用户明确要求

**触发时**：

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

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

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

```
spawn_agent({
  agent_type: "complex_pack_executor",
  message: "
    <DISPATCH_ENVELOPE>

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

修复后由 Coordinator 自验：对照 release risk surface、修复 diff 和 verification commands 确认 blocker 已闭合；自验仍有疑虑时升级 RCA 或 BLOCKED，不派发额外 review。

---
> **下一步**：通过 → Step 14（SKILL.md 主体「标记 Plan 完成 + 推进」）。需修复 → Coordinator 自验闭合或升级 RCA。BLOCKED → 返回 verdict。
