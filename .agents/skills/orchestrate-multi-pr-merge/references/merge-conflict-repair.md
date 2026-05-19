# Multi-PR 冲突修复 + 验证 + 循环

> **流程位置**：`orchestrate-multi-pr-merge` Steps 12-15 · 冲突修复 + 验证循环

## Step 12：构造 Worker Dispatch

根据冲突是否经过 analyst 调查，dispatch prompt 的内容不同：

### 12a：有 Analyst Findings 的 Worker Dispatch

```
spawn_agent({
  agent_type: "<coding_worker | complex_coding_worker>",
  description: "Multi-PR conflict fix: <conflict summary>",
  prompt: "
    ## Scope
    修复 Multi-PR Merge 中发现的 PR 间冲突。

    ## 大设计文档
    <path>

    ## 冲突详情（来自 root_cause_analyst 调查）
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
spawn_agent({
  agent_type: "<coding_worker | complex_coding_worker>",
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

**Worker 类型选择**：涉及 migration / billing / permission / runtime / shared contract → `complex_coding_worker`；否则 `coding_worker`。

## Step 13：接收 Worker 返回

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | 进入 Step 14（Coordinator 验证） |
| `needs repair` | worker 自己有疑虑 → 审阅 concerns，能自主解决则补充信息后 send_input worker 继续；否则进入 Step 14 让验证环节处理 |
| `needs context` | send_input 补充上下文给原 worker |
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
| 修复不正确但方向对 | send_input worker 附修正意见 → 重新验证 |
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
