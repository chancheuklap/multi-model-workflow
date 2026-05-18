# Multi-PR Merge 完成：集成审查 + 合并 + 返回

所有冲突解决后（或 explorer 一开始就没发现冲突），进入 Codex 集成审查。

---

## 第一段：Codex 跨 PR 集成审查（Steps 16-18）

### Step 16：构造 Codex Dispatch

这不是 Pack Review（审查单个 pack），不是 Final Review（审查 design intent coverage）——这是**跨 PR 集成审查**，验证多个 PR 合在一起后系统是否正确。

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

### Step 17：接收 + Disposition

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

**Review 通过** → Step 19（顺序合并）。

**有 accepted findings** → Step 18。

### Step 18：集成审查修复

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

---

## 第二段：顺序合并 PR（Steps 19-21）

### Step 19：确定合并顺序

Codex 集成审查通过后，按依赖顺序合并 PR。

合并顺序基于 Step 2 确定的依赖关系：
1. 被依赖的 PR 先合（foundation / infra / contract provider）
2. 依赖方后合（consumer / feature / UI）
3. 无依赖关系的按计划文档中的顺序

### Step 20：逐个执行合并

**串行合并**——不并行，避免 merge conflict 级联。

对每个 PR 按顺序执行：

```bash
git merge <pr-branch> --no-ff -m "Merge PR #<number>: <title>"
```

**冲突处理**：
- 代码冲突（预期内，冲突解决阶段已处理的区域）→ 按已确定的解决方案应用
- 意外冲突（冲突解决阶段没发现的新冲突）→ 暂停合并，回到 Step 7 分类并处理

**每次 merge 后**：
1. 跑完整测试套件
2. 测试失败 → 暂停，调查原因（可能是合并引入的回归）
3. 测试通过 → 继续下一个 PR

### Step 21：全量集成验证

所有 PR merge 完成后：
1. 跑完整测试套件
2. 跑大设计文档中所有 validation commands
3. 确认合并后的行为与"合并后正确状态"模型一致

---

## 第三段：不存在非阻塞项

**铁律同样适用于 Multi-PR Merge。**

合并完成后，检查：
- 所有冲突解决记录中标记为 "out of scope" 的项 → 确认已开 GitHub issue
- 合并过程中 worker Open Items → 逐项处置（修复 / 开 issue / 确认不是问题）
- `git diff <base>..HEAD` 范围内新增的 TODO/FIXME → 处置

---

## Step 22：确定 Verdict

| 条件 | Verdict |
| --- | --- |
| 所有 PR 合并成功 + 集成审查通过 + 全量测试通过 | `MERGE_COMPLETE` |
| analyst 发现设计/意图冲突，需要重新对齐设计 | `NEEDS_DISCOVERY` |
| 冲突解决需要用户决策 | `NEEDS_USER_DECISION` |
| 无法自主解决 | `BLOCKED` |
