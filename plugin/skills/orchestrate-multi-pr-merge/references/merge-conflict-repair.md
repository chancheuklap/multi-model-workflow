# Multi-PR 冲突修复 + 验证 + 循环

> **流程位置**：`orchestrate-multi-pr-merge` Steps 12-15 · 冲突修复 + 验证循环

## Step 12：构造 Worker Dispatch

根据冲突是否经过 analyst 调查，dispatch prompt 的内容不同：

### 12a：有 Analyst Findings 的 Worker Dispatch

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Multi-PR conflict fix: <conflict summary>",
  prompt: "
    ## Scope
    修复 Multi-PR Merge 中发现的 PR 间冲突。

    ## 大设计文档
    <path>

    ## 冲突详情（来自 root-cause-analyst 调查）
    | # | 冲突 | 根因类型 | 涉及 PR | 修复方向 | 需改哪个 PR |
    <paste from analyst return>

    ## 根因分析
    <paste analyst's detailed root cause analysis>

    ## 修复顺序
    <paste if analyst identified dependency between conflicts>

    ## 涉及的 PR 代码
    PR A (<branch>):
    <relevant diff sections>

    PR B (<branch>):
    <relevant diff sections>

    ## 合同地图
    <paste affected contract surfaces>

    ## Acceptance criteria
    - [ ] 每个列出的冲突已解决
    - [ ] 修复方向与 analyst 的建议一致（除非有更好的方案，需说明理由）
    - [ ] 回归测试通过
    - [ ] 不引入设计文档未要求的新功能
    - [ ] 不破坏任何一个 PR 已通过 Final Review 的行为

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Per-conflict resolution
    ### Verification
    ### Open Items
  "
})
```

### 12b：无 Analyst 的 Worker Dispatch（复杂但根因明确）

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Multi-PR conflict fix: <conflict summary>",
  prompt: "
    ## Scope
    修复 Multi-PR Merge 中发现的 PR 间冲突。

    ## 大设计文档
    <path>

    ## 冲突详情（来自 explorer 发现 + Coordinator 分析）
    <paste conflict description + Coordinator's fix direction>

    ## 涉及的 PR 代码
    <relevant diff sections from both PRs>

    ## 合同地图
    <paste if contract boundary involved>

    ## Coordinator 判定的修复方向
    <which PR should win on each point + why>

    ## Acceptance criteria
    - [ ] 冲突已解决
    - [ ] 修复与 Coordinator 判定的方向一致
    - [ ] 回归测试通过
    - [ ] 不破坏任何 PR 已通过 Final Review 的行为

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Conflict resolution summary
    ### Verification
    ### Open Items
  "
})
```

**Worker 类型选择**：涉及 migration / billing / permission / runtime / shared contract → `complex-pack-executor`；否则 `pack-executor`。

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

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

回归证据必须包含以下至少一项：
- 先失败后通过的 public-behavior test、contract test、migration / schema test 或 build/template check。
- 相关验证命令及结果，能覆盖 accepted finding 的修复面。
- 无法自动化时写明 `manual validation gate`：人工检查对象、检查步骤、通过标准和 release 前责任人。

Release Gate 在宣布 review repair 完成前，必须确认每个 accepted finding 都有回归证据或 `manual validation gate`。
<!-- END: repair-routing -->

## Step 13：接收 Worker 返回

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | 进入 Step 14（Coordinator 验证） |
| `needs repair` | worker 自己有疑虑 → 审阅 concerns，能自主解决则补充信息后 SendMessage worker 继续；否则进入 Step 14 让验证环节处理 |
| `needs context` | SendMessage 补充上下文给原 worker |
| `blocked` | 技术阻塞：尝试拆分冲突 / 换更强模型。业务阻塞：询问用户 |

---

## Step 14：Coordinator 验证修复

修复后由 **Coordinator 验证**，不是 explorer，因为 Coordinator 最了解冲突的方向和正确状态。

验证步骤：
1. 读修复后的代码，确认修复方向与预期一致
2. 对照"合并后正确状态"模型，确认修复后的行为符合设计意图
3. 检查修复是否引入新的冲突（改了 PR A 的代码后，是否与 PR C 产生新冲突）
4. 跑相关测试确认修复有效

| 验证结果 | 动作 |
| --- | --- |
| 验证通过 | 标记该冲突为"已解决"→ Step 15 |
| 修复不正确但方向对 | SendMessage worker 附修正意见 → 重新验证 |
| 修复方向有问题 | 重新评估冲突分类 → 可能需要升级为系统性冲突走 RCA |
| 修复引入新冲突 | 新冲突进入 Step 7 分类 |

## Step 15：冲突解决循环控制

回到 explorer findings 检查。

**退出条件**（任一成立）：
- 所有 explorer 发现的冲突都已标记"已解决"且 Coordinator 验证通过
- 所有新发现的冲突（修复引入的）也已解决

**退出后** → Step 16（Codex 跨 PR 集成审查）。

**循环上限**：每个冲突最多 3 轮修复尝试（与 Execution 修复截断对齐）。第 2 轮仍未解决 → 升级为系统性冲突走 RCA。第 3 轮仍未解决 → BLOCKED。

**不在循环中做的事**：不逐冲突派 Codex review。Codex 审查在所有冲突解决后做一次集成审查。这避免 review 消耗激增。

---
> **下一步**：所有冲突解决 → Step 16（`merge-integration-review.md`）。3 轮未解决 → BLOCKED。
