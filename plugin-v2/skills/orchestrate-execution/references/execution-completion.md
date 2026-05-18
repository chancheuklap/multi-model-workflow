# Release Gate + Git + 并行合并 + Backflow + 进度

## Step 13：Early Release Gate

Pack Review 通过后，检查该 pack 是否触发 Early Release Gate：

**触发条件**（任一成立）：
- pack 的 `发布风险` 涉及 migration / deploy order / rollback / manual production gate，且必须在后续 pack 实现前决定
- baseline finding 暴露的问题必须先判定 release strategy 才能修
- 等到 Final Review 才审会造成不可逆数据、权限、账务或 runtime 风险
- 用户明确要求

**触发时**：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Early Release Gate: Pack N.M <risk surface>",
  prompt: "
    --model gpt-5.5

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
  "
})
```

多个相邻 high-risk packs 同一发布风险面时合并一次。Budget：Release gate 有独立预算（最多 2 个 dispatch，含 early + final）。

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

## Step 14：Git Checkpoint

1. `git add <owned files + test files + plan doc>`
2. `git commit -m "<Pack N.M: title — summary of behavior>"`
3. Commit boundary = 回退边界

**规则**：Worker 不 commit；Coordinator 统一提交。不 stage 非当前 scope 文件。Design/plan repair、Task Pack、finding repair 分别提交。

## Step 15：合并并行 Pack 的 Worktree

并行 pack 各自通过 Pack Review 后，按依赖顺序逐个合并：

1. 确定合并顺序（按 plan 中的 dependencies）
2. `git merge <worktree-branch> --no-ff`
3. 冲突处理：简单 → Coordinator 直接解决；复杂 → 新建 targeted-repair agent
4. 每次 merge 后跑完整测试
5. 全部 merge 完后再跑一次确认集成正确

**不并行合并**——串行避免 merge conflict 级联。

## Backflow + Upstream Skill 路由

| 问题类型 | Upstream Skill | 写回目标 |
| --- | --- | --- |
| design / domain gap | `orchestrate-discovery` | design document |
| architecture friction | `improve-codebase-architecture` | design doc / plan anchors |
| 术语 / domain 冲突 | `grill-with-docs` | domain docs + design document |
| module map / call chain | `zoom-out` | plan anchors / explorer brief |
| bug reproduction / hypothesis | `diagnose` | bug brief / design document |

**影响范围判定**：只影响当前 pack → 写回继续 / 改变 plan anchors → 回到 orchestrate-plan-writing / 暴露 design 缺口 → 回到 orchestrate-discovery。

## Plan Checkbox 维护

每个 pack 通过后勾选 plan 中的 implementation tasks + 更新 Coverage Map。Coordinator 验证 checkbox state 与 git diff 一致。

## 进度汇报

每完成 2-3 个 pack 后一行 FYI。不做长篇汇报。

## Re-Entry from Final Review

Final Review 打回时：按修复分流三条路径（读取 `execution-repair-truncation.md`）处理 → targeted re-review → Git Checkpoint → 返回 Final Review。不重新执行所有 pack。

## 不存在"非阻塞项"

**铁律。** 所有东西要么当场修复，要么立刻开 GitHub issue。Worker 说"先跳过"→ 不接受。Reviewer 说"Minor, not blocking" → Coordinator 仍需 disposition。
