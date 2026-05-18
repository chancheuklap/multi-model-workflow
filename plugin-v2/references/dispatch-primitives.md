# Dispatch Primitives

Coordinator 首次派发 sub-agent 时加载。适用所有 phase 和 route。

## 调度方式

本系统使用两种调度机制，必须区分：

- **Skill tool 调用**：orchestrate-discovery、orchestrate-plan-writing、to-issues、diagnose、prototype、improve-codebase-architecture、zoom-out、triage、grill-with-docs、tdd 均为 Skill tool 调用目标。到达对应节点时，coordinator 使用 `Skill({ skill: "<name>" })` 加载并执行。Skill 内容注入当前主线程上下文，由 coordinator 直接执行（不派 sub-agent）。
- **Agent tool 派发**：coding worker、code explorer、root-cause-analyst、docs-worker 通过 Agent tool 派发为独立 sub-agent。Codex review 通过 `Agent({ subagent_type: "codex:codex-rescue", prompt: "..." })` 派发（Custom Agents 表指定具体 model flag）。

Sub-agent 的 frontmatter `skills:` 字段在启动时自动预加载 skill 内容，sub-agent 无需运行时调用 Skill tool。

## Dispatch Checklist

1. 写 Scope Contract（workflow Step 4）。
2. 判断本次属于 baseline review / targeted re-review / release gate / worker / repair / explorer / docs worker / upstream route。
3. spawn reviewer 前检查 `${CLAUDE_PLUGIN_ROOT}/references/review-budget.md` 全局预算和 per-phase 规则。
4. 读当前 phase reference，抽取 prompt payload。
5. 触碰合同边界时读 `${CLAUDE_PLUGIN_ROOT}/references/contract-boundary.md`，写 Contract anchors。
6. worker / reviewer 不 commit；Git Checkpoint 由主线程管理。
7. prompt 必须自足——包含 phase、source docs、anchors、payload、verification、risk flags 和 Return Contract；不要只写"按 reference 做"。
8. 收到结果后按当前 phase reference 的 Reception 做 disposition；没有 disposition 的 finding 不能进入 repair。

## Pack Brief

派 worker 时 prompt 至少包含：

```text
Pack / Issue / Scope / Goal behavior / Implementation tasks /
Owned files / Read first / Contract anchors / Mockup anchors /
Acceptance criteria / Verification commands / Risk flags /
发布风险 / Commit boundary / AFK-HITL / Dependencies /
Parallel safety / Out of scope / Return contract
```

Formal Orchestrate 的 Pack Brief 必须来自已通过 Plan Review 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。

## Return Contract

所有 sub-agent 使用这些顶层 heading：

```text
### Verdict
pass / blocked / needs repair / needs context

### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots

### Result
- 本次 changed / found / reviewed 的内容

### Verification
- 已运行的 commands 和结果
- 未运行的 checks 和原因

### Open Items
- parent 必须处理的问题
```

Phase reference 和 agent definitions 可以在 `### Result` 内定义 role-specific payload headings，但不得替换标准顶层 headings。

## Finding Shape

```text
- severity:
  confidence:
  locator:
  evidence:
  impact:
  remediation:
```

## Reception Rules

收到 finding 后，parent 不是传话筒——必须主动验证正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。收到 sub-agent 结果后过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。

### Disposition 定义

| disposition | parent 动作 |
| --- | --- |
| `accepted` | 转成 repair / doc / issue / upstream payload；写明 route、owner、affected artifacts 和 targeted re-review scope |
| `rejected` | 记录反证；不派 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 explorer 或让 reviewer 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding、pack、commit、test 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权或项目规则要求时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计、计划或发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

### `needs evidence` Explorer Dispatch

```
Agent({
  subagent_type: "<code-explorer | complex-code-explorer>",
  description: "Supplement evidence: <finding summary>",
  prompt: "
    ## Scope
    只读调查。Reviewer 提出了一条 finding，但 Coordinator 无法验证其正确性——
    需要你查找证据来确认或否认这条 finding。

    ## Finding 待验证
    <paste finding — severity / locator / evidence / impact / remediation>

    ## Reviewer 的主张
    <reviewer 声称什么行为/问题存在>

    ## Coordinator 存疑点
    <为什么 Coordinator 无法自行判断——缺哪些信息>

    ## 相关文件
    <paste affected files / modules>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 files / tests / logs / commands
    ### Result
    - Facts: confirmed facts with locators
    - Finding assessment: confirmed / refuted / partially confirmed + evidence
    - Inferences: clearly marked
    - Recommended next probe: <if unable to fully assess>
    ### Verification
    ### Open Items
  "
})
```

窄范围（单文件 / 单调用链）用 `code-explorer`；多模块 / 跨边界用 `complex-code-explorer`。

## 修复归属（单一来源）

Disposition 为 `accepted` 后：

- **Design Review finding**：Coordinator 直接修设计文档。Design 是 coordinator 写的，拥有完整用户上下文。
- **Plan Review finding — 框架性内容**（header / coverage map / scope check / 发布风险表）：Coordinator 直接修 plan。
- **Plan Review finding — Task Pack 内容**（implementation tasks / owned files / verification / contract anchors）：SendMessage 原 plan-writer（保有 design + issue 上下文）；未启用 Agent Teams 时新建 plan-writer。
- **Plan Review finding — source artifact 问题**：upstream backflow（orchestrate-discovery / to-issues / improve-codebase-architecture），写回后 re-review plan。
- **Execution / Final Review — 简单修复**（≤ 2 文件、不触碰合同边界、不需新增测试、意图明确）：Coordinator 直接修复，跑验证后调度 targeted re-review。
- **Execution / Final Review — 复杂修复**：SendMessage 原 worker（异步，等通知）；未启用 Agent Teams 时新建同类 targeted-repair agent，prompt 含 accepted findings + pack brief subset + git diff scope。
- **Execution / Final Review — 根因不明（只读调查）**：新建 `complex-code-explorer`。
- **Execution — 第 2 轮 repair 仍 needs repair**：截断 worker 循环，新建 `root-cause-analyst`（始终新建，需要全新视角）。Route by analyst `Result.Resolution`：`fixed` → targeted re-review；`root cause found, not fixed` → 用 analyst findings 重新 dispatch worker；`root cause in design/plan` → 写回后 re-enter discovery / plan-writing；`unable to reproduce` → 报告用户，请求更多重现信息；`unable to determine` → BLOCKED，报告用户。
- **Bug Investigation 入口**：Entry Gate 判定根因不明的 bug/error/regression → 新建 `root-cause-analyst`。Route by analyst `Result.Resolution`：`fixed` → Codex review → Closing；`root cause found, not fixed` → 派 worker → Codex review → Closing；`root cause in design/plan` → 更新 Scope Contract + 创建 budget file → Formal Orchestrate（discovery seed）；`unable to reproduce` / `unable to determine` → 报告用户，请求更多信息。
- **Multi-PR Merge — 系统性冲突**：explorer 发现意图 / 隐式依赖 / 多冲突关联 → 新建 `root-cause-analyst`（模式 3）。Route by analyst `Result.Resolution`：`root_cause_identified` → 逐冲突 dispatch worker；`design_conflict` → 询问用户或回 discovery；`implementation_deviation` → dispatch worker 修偏离；`unable_to_determine` → 派 `complex-code-explorer` 补信息后重新 dispatch analyst，或 BLOCKED。
- **Multi-PR Merge — 复杂但根因明确**：功能 / 合同冲突但 Coordinator 清楚方向 → 直接 dispatch worker。
- **Multi-PR Merge — 简单冲突**（≤ 2 文件、代码级）：Coordinator 直接修。
- **READY_FOR_REPAIR**（已批准 design 下的实现偏离）：Direct Repair mini-route（workflow Step 8a）——派 worker → Codex review → Closing。
- **desired behavior 不清**：`orchestrate-discovery`（Skill 调用）。
- **bad seam / 架构摩擦**：`improve-codebase-architecture`（Skill 调用）；只影响当前 pack 回 Execution 继续，改变 plan anchors 回 Plan Review re-review。
- **满足 release gate**：`codex:codex-rescue --model gpt-5.5`（新建）。
- **改变产品范围**：user decision，停止执行。

## SendMessage vs 新建 agent

| 维度 | SendMessage | 新建 agent |
| --- | --- | --- |
| 上下文 | 保留 | 仅 prompt |
| 时序 | 异步（等通知） | 同步（阻塞） |
| 前提 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | 无 |
| 适用 | 同 pack review → 修复 | 未启用 / 跨 pack / 新问题 |

派修复前：检查 SendMessage 在工具列表中 → 有则 SendMessage（agentId）→ 无则新建同类 agent。

## Repair 术语

- `repair round`：一轮 = disposition → repair → targeted re-review。
- `targeted re-review`：只重审 accepted findings、repair diff、受影响 source artifacts、contract surface、mockup anchors 和 verification。
- `full phase review rerun`：重新派发该 phase 的 baseline review angles；只有 source design / issue / plan、scope、Task Pack inventory、shared contract、migration、permission、billing、runtime 或 mockup baseline 改变时才允许。

各 phase 写的"最多 N 轮修复"只限制 `repair round`。没有 accepted finding 就不进入 repair，也不触发 targeted re-review。

Repair prompt 只携带 accepted findings，不夹带 rejected、out-of-scope 或 low-confidence observations。Repair 返回后默认只做 targeted re-review。只有 source baseline 改变或 targeted review 发现新 blocker 时，才 full phase review rerun。
