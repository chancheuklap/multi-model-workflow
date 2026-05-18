# Final Review 完成：清扫 + Release Gate + 业务汇报

> **流程位置**：`orchestrate-final-review` Steps 13-20 · 含 verdict 判定 · 完成后回到 SKILL.md 返回区

两个 baseline review 的 accepted findings 全部修复并通过 Targeted Re-Review 后（或两个 baseline 直接 pass），进入 Coordinator 主导的后续流程。

---

## 第一段：清扫遗留尾巴（Steps 13-15）

**这是 Coordinator 的职责**，不是 reviewer 的角度。Pack Review 和 baseline review 关注的是"做得对不对"；清扫关注的是"有没有漏做"。项目中不存在"非阻塞项"——所有东西要么当场修复，要么立刻开 GitHub issue。

### Step 13：收集遗留项

从三个来源收集所有可能的遗留尾巴：

**13a：Worker Open Items**

读取每个 pack 的 worker 返回的 `### Open Items`。Worker 经常在这里留下"不在 scope 内"或"建议后续处理"的东西。

**13b：代码扫描**

在 diff 范围内扫描遗留标记：

```bash
git diff <starting_commit>..HEAD --diff-filter=AM --name-only | xargs grep -n "TODO\|FIXME\|TBD\|XXX\|HACK\|defer\|later\|placeholder\|temporary\|workaround" 2>/dev/null || true
```

过滤掉 starting commit 之前已存在的遗留标记（`git show <starting_commit>:<file>` 对比）。只关注本次实现新增的。

**13c：Pack Review Disposition 记录**

读取 execution 过程中所有 pack 的 "out of scope" disposition——有些可能在 Final Review 视角下应该被解决。

### Step 14：逐项处置

对每个遗留项，Coordinator 必须做出明确处置——**不允许"先放着"**：

| 处置 | 条件 | 动作 |
| --- | --- | --- |
| **立即修复** | 在当前 scope 内、修复简单（≤ 2 文件）、不引入新风险 | Coordinator 直接修或派 worker |
| **开 GitHub Issue** | 不在当前 scope 内、或修复复杂需要独立 session | 立即开 issue，写明 current behavior / desired behavior / key interfaces / acceptance criteria / out of scope / risk flags |
| **确认不是问题** | 经查实遗留标记是合理的（如 TODO 指向未来 feature，不影响当前功能） | 记录确认理由，不删除标记也不开 issue |

**铁律**：处置完成后，不应存在任何含糊的遗留项。每一个 Worker Open Item、每一个新增 TODO/FIXME、每一个 "out of scope" disposition 都有明确的处置记录。

### Step 15：清扫修复验证

如果 Step 14 产生了代码修改：
1. 跑完整测试套件确认不回归
2. 跑所有 pack 的 verification commands
3. 简单修复（Coordinator 直接改）→ 不需要额外 review
4. 复杂修复（派了 worker）→ 做 targeted re-review（Budget 消耗 1）

---

## 第二段：Release Gate（Steps 16-18）

### Step 16：判断是否触发 Final Release Gate

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

### Step 17：派发 Release Reviewer

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Final Release Gate: <risk surface>",
  prompt: "
    --model gpt-5.5

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
  "
})
```

Budget：Release gate 有独立预算（最多 2 个 dispatch，含 early + final）。如果 Execution 已用 1 个 early release gate，此处还有 1 个。

### Step 18：处理 Release Gate 结果

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

## 第三段：业务汇报（Step 19）

Final Review 的两个 baseline 通过 + 遗留清扫完成 + Release Gate 通过（如有）后，组装业务汇报。

**汇报用业务语言**，不用技术术语。面向项目负责人 / 产品经理。

### 19a：新增能力

用业务语言描述用户或系统现在能做什么——每项能力是一个用户可感知的行为变化。不列函数名、文件路径或技术实现细节。

### 19b：验证证据

每项能力附上：
- 哪些测试验证了这个行为
- 关键验证命令的运行结果
- UI 验证截图（如有 UI 工作）
- Contract 验证证据（如有 contract 变更）

### 19c：残余风险

未解决的 manual gate、已知 edge case、deploy 注意事项。每项说明：
- 风险是什么
- 影响范围
- 缓解措施（如有）

### 19d：发布检查

| 检查项 | 状态 |
| --- | --- |
| Migration | 通过 / 不适用 / 需人工确认 |
| Rollback | 通过 / 不适用 / 需人工确认 |
| Deploy order | 通过 / 不适用 / 需人工确认 |
| Manual production gate | 通过 / 不适用 / 需人工确认 |

**业务汇报包含在 verdict 返回的 `### Business report` 中。orchestrate-workflow Closing 的 Step 23 将其呈现给用户。**

---

## Step 20：确定 Verdict

| 条件 | Verdict |
| --- | --- |
| 两个 baseline 通过 + 遗留清扫完成 + 无 release gate 触发 | `FINAL_REVIEW_PASSED` |
| 两个 baseline 通过 + 遗留清扫完成 + release gate 触发且通过 | `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` |
| accepted findings 涉及多 pack 系统性问题 | `NEEDS_EXECUTION` |
| design / context gap 需要 discovery 补充 | `NEEDS_DISCOVERY` |
| plan gap 需要修订 | `NEEDS_PLAN_REVISION` |
| 无法自主解决 | `BLOCKED` |
