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

按以下步骤派发 Codex review（`CODEX_SCRIPT` 未定义时先执行 `CODEX_SCRIPT="$(find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" -type f 2>/dev/null | head -1)"`）：
1. 写 prompt → `review-prompts/<gate>.md`
2. `node "$CODEX_SCRIPT" task --background --prompt-file .claude/multi-model-workflow/review-prompts/<gate>.md --model gpt-5.4 --effort xhigh` → 记录 JOB_ID，写入 `review-prompts/<gate>.job-id`
3. `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000`（run_in_background: true）
4. `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` → 存到 `review-results/<gate>.md`

Compaction 恢复：有 `.job-id` 无对应 `review-results/` → 从 Step 3 继续。

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
