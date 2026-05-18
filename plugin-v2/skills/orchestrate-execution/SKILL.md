---
name: orchestrate-execution
description: "Plan Review 通过后、已有 reviewed plan + confirmed Task Pack inventory 时主动使用。覆盖完整 Pack 执行循环：预执行准备 → 逐 Pack 派 Worker → Pack Review → Coordinator 验证 + Disposition → 修复分流 → Targeted Re-Review → 修复截断 → Release Gate → Git Checkpoint → 循环释放。纯 Coordinator 技能：主线程读取本技能执行调度、review 接收、修复路由和进度追踪；不由 Sub-Agent 消费。"
---

# Orchestrate Execution

覆盖从 Plan Review 通过到所有 Pack 通过的完整执行循环。Coordinator 按本技能逐步执行——不由 Worker 或 Reviewer 消费。

**核心原则**：Fresh worker per pack + 单次 Codex cross-model review + Coordinator 亲验 finding + 修复分流三路径 = 高质量、快速迭代。

**连续执行**：不要在 pack 之间暂停向用户汇报或询问"要不要继续"。除非遇到无法自主解决的 BLOCKED 或影响产品方向的业务决策，否则连续执行所有 pack 直到全部完成。

---

# 第一部分：预执行准备

## Step 1：读取 Plan Task Pack Inventory

读取已通过 Plan Review 的计划文档，提取：

- 所有 Task Pack 的编号、标题、issue reference
- 每个 pack 的 `Dependencies`、`Parallel safety`、`Risk flags`、`发布风险`
- Source design path、Source issues paths
- File / Responsibility Map
- 发布风险和人工门禁表

**验证 Plan 完整性**：每个 pack 必须有 goal behavior / owned files / acceptance criteria / verification commands / contract anchors（触碰合同时）/ mockup anchors（UI 时）/ commit boundary / risk flags。缺字段的 pack 不进入执行——返回 `NEEDS_PLAN_REVISION`，让 orchestrate-plan-writing 修复。

## Step 2：构建 Pack 执行队列

根据 pack 间的 `Dependencies` 和 `Parallel safety` 字段，构建执行顺序：

**串行条件（默认）**：同一文件 / 同一 Pydantic model / 同一 DB migration tree / 同一 JSON registry / billing / permission / auth / runtime / deployment / rollback / release gate / 同一 UI action contract。

**并行条件**：pack 间无共享 owned files、无共享 contract surface、各自可独立验证。并行 pack 使用 `isolation: "worktree"` 在独立 worktree 中执行。

排列结果：`pack_queue = [[pack1], [pack2, pack3], [pack4], ...]`，其中嵌套数组内的 pack 可并行。

## Step 3：验证 Scope Contract + Git Checkpoint

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）。验证 editable artifacts 包含 plan 中所有 owned files。

**Git Checkpoint**：
- `git status --short --branch` 确认当前分支、无 stale dirty files
- 不在 main / master / release branch 上（应已在 workflow entry gate 创建 work branch）
- 区分当前 scope 改动和用户/其它线程改动——不 stage 不属于当前 scope 的 dirty files

**Budget File**：读取 `.claude/multi-model-workflow/active-run-id` 找到 budget file，确认 `pack_count` 与 plan 中 Task Pack 数量一致。不一致时更新 budget file。

---

# 第二部分：Worker 派发协议

## Step 4：选择 Worker 类型

按 pack 的 `Risk flags` 选择 agent：

| Risk flags | Agent | 模型 |
| --- | --- | --- |
| `normal` | `pack-executor` | Sonnet |
| `high-risk` / `production-risk` / `billing` / `permission` / `migration` / `runtime` / `HITL` | `complex-pack-executor` | Opus 4.7 |

## Step 5：构造 Pack Brief

Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。Coordinator 从 plan 中提取并在 prompt 中写全以下所有字段：

```text
Pack: <pack number + title>
Issue: <issue reference>
Scope: <editable artifacts for this pack>
Goal behavior: <end-to-end behavior description>
Implementation tasks:
  <paste ALL tasks with full text — don't让 worker 读 plan 文件>
Owned files:
  - Create: <path — responsibility>
  - Modify: <path — responsibility>
  - Test: <path — behavior covered>
Read first:
  - <source docs, ADRs, project rules, mockups>
Contract anchors:
  - boundary type / owner / provider / consumer / verifier
  - Pydantic model / schema_version / compatibility
  - registry / migration / catalog
  - repository / read model
  - tests / release gate
  - forbidden shortcuts
Mockup anchors:
  - path / viewport / states / interaction / visual verification
Acceptance criteria:
  - [ ] <each criterion>
Verification commands:
  - <command> → Expected: <result>
Commit boundary: <one atomic commit scope>
Risk flags: <normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL>
发布风险: <risk surface / N/A>
AFK / HITL: <manual gate requirements>
Dependencies: <pack dependencies>
Parallel safety: <can parallel with which packs / why>
Out of scope: <what NOT to touch>
Return contract:
  ### Verdict
  pass / blocked / needs repair / needs context
  ### Evidence
  ### Result
  - Changed files
  - Completed behavior (each with verification evidence)
  - Known gaps
  - Needs review
  ### Verification
  ### Open Items
```

**关键规则**：
- Pack Brief 必须来自已通过 Plan Review 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。
- 所有 task 完整文本直接贴在 prompt 中——不让 worker 读 plan 文件（节省 worker 上下文，确保 worker 拿到的是完整信息）。
- Coordinator 提供场景上下文（where this fits, dependencies, architectural context），让 worker 理解这个 pack 在整体中的位置。

## Step 6：派发 Worker

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Execute Task Pack N.M: <title>",
  prompt: "<Pack Brief>",
  isolation: "worktree"  // 仅并行 pack 使用
})
```

**记录返回的 agentId**——后续复杂修复需要用 SendMessage 继续该 worker（保有代码上下文）。

并行 pack 在同一消息中发送多个 Agent tool call，各自带 `isolation: "worktree"`。

---

# 第三部分：Worker 返回处理

## Step 7：接收 Worker 返回

Worker 返回四种状态：

| Worker Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `pass`（DONE） | 实现完成，全部测试通过 | 进入 Step 8（Pack Review） |
| `needs repair`（DONE_WITH_CONCERNS） | 实现完成但 worker 自己有疑虑 | 读 worker concerns。正确性/scope concerns → 视为 worker 自报 finding，按 Step 10 修复分流（路径 A/B/C）→ 修完进 Pack Review。纯观察性意见（"文件偏大"、"可能需要重构"）→ 记录到 Open Items，进 Pack Review |
| `needs context` | 缺信息无法继续 | SendMessage 补充上下文给原 worker（fallback: 新建同类 worker）；补充后 worker 继续 |
| `blocked` | 无法完成 | 技术阻塞：尝试自主解决（拆 pack / 提供更多上下文 / 换更强模型）。业务阻塞：询问用户（一次只问一个问题） |

**Worker scope drift 检测**：Worker 有时会"顺手修"scope 之外的东西。Coordinator 在 worker 返回后检查 Changed files 是否超出 Owned files。超出部分：属于当前 scope 其它 pack → 记录但不 revert；不属于当前 scope → 要求 worker revert 或 Coordinator 直接 revert，不让 out-of-scope 改动进入 Pack Review。

---

# 第四部分：Pack Review

## Step 8：派发 Codex Reviewer

Worker 返回 `pass` 或处理完 `needs repair` concerns 后，派发 **1 个** baseline Codex reviewer：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Pack Review: Task Pack N.M",
  prompt: "
    --model gpt-5.4

    ## Scope
    Review the implementation of Task Pack N.M: <title>

    ## Source artifacts
    - Plan: <path>
    - Source design: <path>
    - Pack acceptance criteria: <paste>
    - Verification commands: <paste>

    ## Changed files
    <list from worker return>

    ## Contract anchors
    <paste if this pack touches contract boundaries>

    ## Mockup anchors
    <paste if this pack has UI work>

    ## Review angles (single integrated review)

    ### Spec Compliance
    验 worker 是否实现了 pack 要求的一切（不多不少）：
    - 每条 acceptance criteria 是否满足
    - 是否有 missing requirements
    - 是否有 extra/unneeded work（YAGNI）
    - goal behavior 是否可从代码中确认

    ### Code Quality
    验实现是否正确、可维护：
    - TDD 纪律：测试测的是 public behavior，不是 mock behavior
    - 合同纪律：跨边界数据用正式 Pydantic contract，不是 bare dict
    - 不 mock 仓库内部业务模块
    - 文件职责清晰、接口定义好
    - 遵循项目既有模式

    ### Contract & Risk
    验高风险面是否正确处理：
    - Contract anchors 闭合（owner / provider / consumer / verification）
    - Migration / registry / catalog 完整
    - 发布风险标注准确
    - rollback / compatibility 考虑

    ## Calibration
    只标记会导致实际问题的 issue。实现者做出错误的东西或卡住——这是 issue。
    措辞、风格偏好、nice-to-have 建议——不是。
    除非有严重缺口（spec 不符、合同破损、测试不覆盖核心行为、引入安全风险），否则 approve。

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    Pack Review 结果：
    Spec compliance:
    Code quality:
    Contract & risk:
    Critical:
    Important:
    低置信度观察:
    Disposition required:
    ### Verification
    ### Open Items
  "
})
```

**Budget check**：派发前读 budget file，确认 `budget_used + 1 ≤ budget_total`。达到 80% 时触发 Direction Check（重述 current phase / 剩余 packs / 累计 findings / 是否继续）。超过预算时停止并报告用户。

---

# 第五部分：Coordinator 验证 + Disposition

## Step 9：接收 Review Findings

**Coordinator 不是传话筒**——必须主动验证 finding 的正确性：

1. **读代码**：检查 reviewer 说的是否与代码事实一致
2. **跑测试**：reviewer 说测试不覆盖 → 跑一下确认
3. **对照 source artifacts**：reviewer 说 spec 不符 → 对照 plan 和 design document 确认
4. **用自己的判断力质疑和确认**：不因为 reviewer 说了就当真，也不因为 worker 说通过就放行

逐条 disposition：

| Disposition | 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts、repair scope、targeted re-review scope |
| `rejected` | 记录反证；不 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 `code-explorer` / `complex-code-explorer` 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding / pack / commit / test；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计/计划/发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Pack Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ 跳到 Step 14（Release Gate 检查）。

**Pack Review needs repair**（有 accepted finding）→ 进入 Step 10。

---

# 第六部分：修复分流

## Step 10：修复路由（三条路径）

所有 repair prompt 只携带 accepted findings，不夹带 rejected / out-of-scope / low-confidence observations。

### 路径 A：Coordinator 直接修复

**条件**：≤ 2 文件、不触碰合同边界、不需新增测试、意图明确。

1. Coordinator 读 diff、理解 finding
2. 直接修改代码
3. 跑 verification commands 确认修复
4. 进入 Step 11（Targeted Re-Review）

### 路径 B：SendMessage 给原 Worker

**条件**：多文件、需要代码上下文、需要新增/修改测试、但根因已知。

1. 检查 SendMessage 是否可用（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）
2. 可用 → SendMessage 给 saved agentId，附 accepted findings
3. 不可用 → 新建同类 agent（`pack-executor` 或 `complex-pack-executor`），prompt 含 accepted findings + pack brief subset + git diff scope
4. Worker 修复后返回 → 进入 Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

1. 新建 `complex-code-explorer`，prompt 含症状描述 + 相关文件 + 调查方向
2. Explorer 返回只读调查结果（不修代码）
3. 根据调查结果选择路径 A 或 B 继续修复

### 修复归属快速判定

| 信号 | 路径 |
| --- | --- |
| "这行该返回 X 而不是 Y" + ≤ 2 文件 | A（Coordinator 直接修） |
| "缺 migration / 缺 consumer 同步 / 测试不覆盖" | B（Worker 修） |
| "行为异常但不清楚为什么" / "这里看起来有时序问题" | C（Explorer 查） |
| accepted finding 涉及 migration / billing / permission / runtime / shared contract | B（用 complex-pack-executor） |

---

# 第七部分：Targeted Re-Review + 修复截断

## Step 11：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分 + 受影响 source artifacts + contract surface + mockup anchors + verification。不做 full review rerun。

派发方式同 Step 8，但 scope 缩小到：
- changed files（修复涉及的文件）
- accepted findings（原 finding 是否解决）
- 受影响 angle（spec / quality / contract / risk 中与修复相关的）

## Step 12：修复预算 + 截断

**修复预算**：每个 pack 最多消耗 **2 个 Worker repair round + 1 个 root-cause-analyst round = 总共 3 个 repair round**。这是 per-pack 上限；全局 review budget 优先——Direction Check 在 80% 时触发，可能在某个 pack 用满 3 轮之前就要求停下来评估方向。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → **截断 Worker 循环**，新建 `root-cause-analyst` |

**Root-Cause-Analyst 截断调度**：

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Investigate repair failure: Pack N.M",
  prompt: "
    Worker 修了两轮，reviewer 仍报 needs repair。

    ## 前两轮上下文
    - Round 1 accepted findings: <paste>
    - Round 1 worker 修复内容: <paste>
    - Round 2 accepted findings: <paste>
    - Round 2 worker 修复内容: <paste>
    - Git diff scope: <paste>
    - 原 Pack Brief: <paste relevant subset>

    ## 你的任务
    不要重复 worker 的方法。从不同维度切入——时序、状态污染、隐式依赖、配置漂移。

    ## Return contract
    ### Verdict
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed / root cause in design/plan / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    ### Verification
    ### Open Items
  "
})
```

**Analyst Resolution 路由**：

| Resolution | 下一步 |
| --- | --- |
| `fixed` | Targeted Re-Review（消耗 Round 3） |
| `root cause found, not fixed` | 用 analyst findings 重新 dispatch worker（消耗 Round 3） |
| `root cause in design/plan` | 写回 design doc / plan → 回到 orchestrate-discovery 或 orchestrate-plan-writing |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

Round 3 的 Targeted Re-Review 仍 needs repair → BLOCKED，报告用户。

---

# 第八部分：Release Gate + Git Checkpoint

## Step 13：Early Release Gate（Pack Review 通过后检查）

Pack Review 通过后，检查该 pack 是否触发 Early Release Gate：

**触发条件**（任一成立）：
- pack 的 `发布风险` 涉及 migration / deploy order / rollback / manual production gate，且必须在后续 pack 实现前决定
- baseline finding 暴露的问题必须先判定 release strategy 才能修
- 等到 Final Review 才审会造成不可逆数据、权限、账务或 runtime 风险
- 用户明确要求

**触发时**：派发 `codex:codex-rescue --model gpt-5.5`，只审 release-risk（不审普通代码质量）。多个相邻 high-risk packs 属于同一发布风险面时合并一次 release-risk review。

**Release blocker**：发现 release blocker → 派 `complex-pack-executor` 或询问用户。修复后只做 targeted release re-review；不重跑 baseline review。

## Step 14：Git Checkpoint

Pack Review 通过（+ Release Gate 通过，如有）后：

1. `git add <owned files + test files + plan doc>`——stage 属于当前 pack scope 的文件 + plan 文档（checkbox 更新）
2. `git commit -m "<Pack N.M: title — summary of behavior>"`
3. Commit boundary = 回退边界：如果后续 pack 失败需要回滚，可以 revert 到这个 commit

**规则**：
- Worker 不 commit；Coordinator 在 review 通过后统一 commit
- 不 stage 不属于当前 pack scope 的 dirty files
- Design/plan repair、通过 review 的 Task Pack、accepted finding repair 分别提交——不混在一个 commit 里

---

# 第九部分：不存在"非阻塞项"

**这是铁律，没有例外。**

项目中不存在"非阻塞项"这种概念。所有东西要么当场修复，要么立刻在 GitHub 上开 issue 记录。

Worker 返回时说"这个不影响功能，先跳过"——不接受。Coordinator 必须：
1. 判断它是否真的可以跳过（几乎不存在这种情况）
2. 如果确实不在当前 pack scope 内 → 立即开 GitHub issue 记录，写明 current behavior / desired behavior / key interfaces / acceptance criteria / out of scope / risk flags
3. 如果在 scope 内 → 要求 worker 修复

Reviewer 返回 finding 说"Minor, not blocking"——Coordinator 仍需 disposition：accepted → 修；rejected → 记录反证；out of scope → 开 issue。不能直接忽略。

Pack Review 通过不代表可以留尾巴。Final Review 会揪出所有遗留问题——提前处理好过被打回来。

---

# 第十部分：并行 Pack 合并

## Step 15：合并并行 Pack 的 Worktree

并行 pack 各自在独立 worktree 中完成 + 通过 Pack Review 后，按依赖顺序逐个合并：

1. 确定合并顺序（按 plan 中的 dependencies 排列）
2. 逐个执行：
   ```bash
   git merge <worktree-branch> --no-ff
   ```
3. 冲突处理：
   - 简单冲突（import 顺序、同文件不同区域）→ Coordinator 直接解决
   - 复杂冲突（同一函数、同一 contract surface）→ 新建 targeted-repair agent 修复
4. 每次 merge 后跑完整测试套件验证
5. 全部 merge 完成后再次跑完整测试确认集成正确

**不并行合并**——串行合并避免 merge conflict 级联。

---

# 第十一部分：Backflow + Upstream Skill 路由

执行过程中遇到非 implementation 问题时，使用 Skill tool 调用 upstream skill。调用前给出 Scope、source artifacts、允许输出和写回目标。结论必须写回 design document / plan / bug brief，再回到当前 pack 继续。

| 问题类型 | Upstream Skill | 写回目标 |
| --- | --- | --- |
| design / domain gap | `orchestrate-discovery` | design document |
| architecture friction / bad seam | `improve-codebase-architecture` | design doc / plan anchors |
| 术语 / domain 冲突 | `grill-with-docs` | domain docs + design document |
| 需要 module map / call chain | `zoom-out` | plan anchors / explorer brief |
| bug 需要 reproduction / hypothesis | `diagnose` | bug brief / design document |

**Backflow 影响范围判定**：

| upstream skill 结论 | 影响 | 下一步 |
| --- | --- | --- |
| 只影响当前 pack | 写回后继续当前 pack | 继续 Step 4 |
| 改变 plan anchors（其它 pack 的 owned files / dependencies / contract 受影响） | 写回后回到 orchestrate-plan-writing | Plan Review re-review |
| 暴露 design 缺口 | 写回后回到 orchestrate-discovery | Design Review |

---

# 第十二部分：Plan Checkbox + 进度追踪

## Plan Checkbox 维护

每个 pack 通过 Pack Review + Git Checkpoint 后：
1. 在 plan 文档中勾选该 pack 的所有 implementation tasks
2. 更新 plan 的 Source Coverage Map 标记已实现的 intent

**验证**：Coordinator 检查 plan checkbox state 是否与实际 git diff 一致。Worker 声称完成了但 plan 没勾 → 补勾。Plan 勾了但代码没做 → 取消勾选，重新进入 pack。

## 进度汇报

每完成 2-3 个 pack 后一行 FYI：
```
进度：已完成 Pack 1.1, 1.2, 2.1（3/7）。当前执行 Pack 2.2。累计 findings: 5 accepted, 2 rejected。
```

不做长篇汇报。用户需要详情时可以问。

---

# 第十三部分：Re-Entry from Final Review

Final Review 可能发现 implementation gap 或遗留尾巴，打回到 Execution。

**Re-entry 处理**：
1. Final Review 返回 accepted findings，标明哪些 pack 需要修复
2. Coordinator 按修复分流三条路径（Step 10）处理每个 finding
3. 修复后做 targeted re-review（只审修复部分）
4. 通过后重新 Git Checkpoint
5. 返回 Final Review 继续

**不重新执行所有 pack**——只处理 Final Review 标出的具体问题。

---

# 第十四部分：过渡到 Final Review

## Step 16：所有 Pack 通过

所有 pack 通过 Pack Review + Release Gate（如有）+ Git Checkpoint 后，返回 verdict。orchestrate-workflow 将路由到 orchestrate-final-review。

## 返回格式

```text
### Verdict
EXECUTION_PASSED | NEEDS_DISCOVERY | NEEDS_PLAN_REVISION | NEEDS_ARCHITECTURE | BLOCKED

### Pack execution summary
- Total packs: <count>
- Passed: <count>
- Parallel merges: <count>

### Per-pack results
| Pack | Worker | Risk | Repair rounds | Release gate | Status |
| --- | --- | --- | --- | --- | --- |
| 1.1 | pack-executor | normal | 0 | N/A | pass |
| 1.2 | complex-pack-executor | migration | 1 | early gate pass | pass |
| ... | ... | ... | ... | ... | ... |

### Review budget
- Budget total: <N>
- Budget used: <N>
- Direction checks triggered: <count>

### Findings summary
- Total findings received: <count>
- Accepted + repaired: <count>
- Rejected: <count>
- Out of scope (issues created): <count>

### Git state
- Commits: <list of pack commits>
- Branch: <current branch>
- Clean: yes / no (if no, explain)

### Plan checkbox progress
- Tasks completed: <count> / <total>
- Coverage map: <all intents covered / gaps>

### Open items
- Blockers / HITL: <if any>
- Issues created: <GitHub issue refs>
- Needs context: <specific gaps>

### Next route
- orchestrate-final-review / orchestrate-discovery / orchestrate-plan-writing / user decision / blocked
```
