# Codex 跨 PR 集成审查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 16-18 · 所有冲突解决后（或 explorer 未发现冲突）进入 · 通过后 → Steps 19-22（`merge-completion.md`）

这不是 Pack Review（审查单个 pack），不是 Final Review（审查 design intent coverage）——这是**跨 PR 集成审查**，验证多个 PR 合在一起后系统是否正确。

## Step 16：构造 Codex Dispatch

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Multi-PR integration review: <PR set>",
  prompt: "
    --model gpt-5.4

    ## Scope
    跨 PR 集成审查。多个并行 PR 来自同一大设计，各自已通过 Final Review。
    本次审查验证它们合在一起后是否正确。

    ## 大设计文档
    <path>

    ## PRs included
    | PR | Branch | 核心行为 | Final Review verdict |
    <paste>

    ## 冲突解决记录
    <paste resolved conflicts + how they were fixed>
    <if no conflicts: 'Explorer 确认无 PR 间冲突'>

    ## Combined diff
    <combined diff of all PRs against base>

    ## 合同地图
    <all cross-PR contract surfaces>

    ## Review angles

    ### 1. 组合行为正确性
    所有 PR 合在一起是否产出大设计描述的正确行为。
    每个 PR 各自正确不代表组合正确——关注交互、顺序、依赖。

    ### 2. 合同一致性
    跨 PR 的 Pydantic model / API / DB schema / JSON payload / registry 是否一致。
    一个 PR 提供的合同是否被另一个 PR 正确消费。

    ### 3. 迁移完整性
    多个 PR 的 migration 合并后：
    - 顺序是否正确
    - 是否有遗漏的 migration（PR A 改了 model，PR B 没有对应 migration）
    - 回滚是否安全

    ### 4. 状态一致性
    跨 PR 的 shared state 假设是否一致。
    并发访问 shared state 是否安全。

    ### 5. Import / 依赖
    合并后是否有循环 import。
    依赖版本是否一致。

    ### 6. 回归
    合并所有 PR 后，既有功能是否完好。
    跑完整测试套件并报告结果。

    ### 7. 冲突修复质量（如有）
    之前解决的冲突的修复是否正确、完整。
    修复是否引入了新问题。

    ## Calibration
    只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
    单个 PR 内部的代码质量——已在各自 Final Review 中覆盖，不再重复。
    措辞、命名、风格——不是 finding。

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    组合行为:
    合同一致性:
    迁移完整性:
    状态一致性:
    Import / 依赖:
    回归:
    冲突修复质量:
    Critical:
    Important:
    Disposition required:
    ### Verification
    ### Open Items
  "
})
```

## Step 17：接收 + Disposition

**Coordinator 不是传话筒**——逐条验证每个 finding：

1. 读代码确认 finding 是否成立
2. 对照大设计文档确认 spec 判断
3. 对照冲突解决记录确认修复判断

| Disposition | 动作 |
| --- | --- |
| `accepted` | 转成 repair payload |
| `rejected` | 记录反证 |
| `needs evidence` | 派 code-explorer 补证据 |
| `duplicate / already covered` | 链到已有记录 |
| `out of scope` | 开 GitHub issue |
| `user decision` | 询问用户 |

**Review 通过** → Step 19（`merge-completion.md`）。

**有 accepted findings** → Step 18。

## Step 18：集成审查修复

修复路由同冲突解决阶段：

- 简单修复（≤ 2 文件、不碰合同）→ Coordinator 直接修
- 复杂修复 → 派 worker

修复后做 **Targeted Re-Review**：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Multi-PR targeted re-review: <finding summary>",
  prompt: "
    --model gpt-5.4

    ## Scope
    Targeted re-review for Multi-PR integration repair.
    Only review the changes made to address the listed findings.

    ## Original findings
    <paste accepted findings>

    ## Repair diff
    <git diff of repair changes>

    ## Review focus
    - Each accepted finding has been addressed
    - Repair does not introduce new issues

    ## Calibration
    只验证修复是否解决了原始 finding。不做全面重审。

    ## Return Contract
    ### Verdict
    pass / needs repair / blocked
    ### Evidence
    ### Result
    Per-finding status:
    ### Verification
    ### Open Items
  "
})
```

最多 2 轮修复。超过 → BLOCKED。
