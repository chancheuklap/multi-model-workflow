# Multi-PR 冲突发现 + 分类

> **流程位置**：`orchestrate-multi-pr-merge` Steps 4-8 · 无冲突 → Step 16（`merge-integration-review.md`）；系统性冲突 → Step 9（`merge-rca-investigation.md`）；复杂/简单冲突 → Step 12（`merge-conflict-repair.md`）

## Step 4：确定 Explorer 分析策略

**并行分析所有 PR**，不逐个顺序处理。分析维度：

| 维度 | 检查内容 |
| --- | --- |
| **代码交叉** | 多个 PR 修改同一文件 / 同一函数 / 同一行 |
| **功能交叉** | PR A 实现的功能依赖 PR B 修改的接口或行为 |
| **意图交叉** | PR A 和 PR B 对同一领域概念做出不同假设 |
| **合同交叉** | 多个 PR 修改同一 contract surface（Pydantic model / API / DB schema） |
| **状态交叉** | 多个 PR 操作同一 shared state / cache / global config |
| **迁移交叉** | 多个 PR 各自创建 migration，合并后顺序可能冲突 |

## Step 5：派发 Code-Explorer

根据风险热点和 PR 数量，派发 1-N 个 code_explorer（或 complex_code_explorer for 多模块交叉）。可并行派发。

```
spawn_agent({
  agent_type: "<code_explorer | complex_code_explorer>",
  message: "
    ## Scope
    分析多个并行 PR 之间的代码 / 功能 / 意图关系。
    这些 PR 来自同一个大设计，各自已通过 Final Review。
    你的任务是发现 PR 之间的冲突——不是评判单个 PR 的质量。

    ## PRs to analyze
    | PR | Branch | 变更范围 | 核心行为 |
    | --- | --- | --- | --- |
    <paste per-PR summary>

    ## 大设计目标
    <paste from big design doc — overall goal + architecture>

    ## 合同地图
    <paste cross-PR contract surfaces>

    ## 文件交叉矩阵
    <paste files modified by multiple PRs>

    ## 分析维度

    ### 1. 代码冲突
    - 同一文件 / 同一函数被多个 PR 修改
    - Import 冲突、命名冲突
    - 预期严重程度：低（git merge 通常可自动解决）

    ### 2. 功能冲突
    - PR A 的功能依赖 PR B 的接口，但 PR B 改了接口
    - PR A 和 PR B 都修改同一业务流程的不同环节
    - 预期严重程度：中（需要理解两个 PR 的行为才能判断）

    ### 3. 意图冲突
    - PR A 对某个领域概念的理解与 PR B 不同
    - PR A 的设计假设与 PR B 的设计假设矛盾
    - 预期严重程度：高（可能需要设计层面决策）

    ### 4. 合同冲突
    - 同一 Pydantic model / API / DB schema 被不同 PR 以不同方式修改
    - schema_version / migration 顺序冲突
    - 预期严重程度：高（合同破损影响全局）

    ### 5. 隐式依赖
    - PR A 假设某个 state / config / behavior 存在，但 PR B 改变了它
    - 不在文件交叉矩阵中但通过运行时行为耦合
    - 预期严重程度：最高（最难发现）

    ## 输出要求
    对每个发现的冲突，报告：
    - 冲突类型（代码 / 功能 / 意图 / 合同 / 隐式依赖）
    - 涉及的 PR
    - 涉及的文件和行
    - 冲突的具体内容（两个 PR 各自做了什么、为什么冲突）
    - 严重程度（低 / 中 / 高 / 阻塞）
    - 你对冲突根因的初步判断（如果有）

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 files / branches / diffs
    ### Result
    冲突清单：
    | # | 类型 | PRs | 文件 | 描述 | 严重程度 | 初步根因 |
    无冲突区域：
    <areas confirmed conflict-free>
    ### Verification
    ### Open Items
  "
})
```

## Step 6：接收 Explorer 返回

汇总所有 explorer 的冲突发现。去重（多个 explorer 可能发现同一冲突）。

| Explorer Verdict | 动作 |
| --- | --- |
| `pass`（所有 explorer 无冲突） | 跳到 Step 16（Codex 跨 PR 集成审查） |
| `needs repair`（有冲突） | 进入 Step 7（冲突分类） |
| `needs context` | 补充信息后重新派发 |
| `blocked` | 报告用户 |

---

## Step 7：对每个冲突做三级分类

Coordinator 逐个审阅 explorer 发现的冲突，做修复路由判定：

| 分类 | 条件 | 路由 |
| --- | --- | --- |
| **简单** | 代码级冲突（import 顺序、同文件不同区域）；≤ 2 文件；修复方向明确 | Step 8：Coordinator 直接修 |
| **复杂、根因明确** | 功能 / 合同冲突；涉及多文件；但冲突原因清楚——两个 PR 对同一接口做了不同改动，谁该 win 很清楚 | Step 12：派 coding worker |
| **复杂、系统性 / 根因不明** | 意图冲突 / 隐式依赖 / 多个冲突相互关联；冲突原因不清楚——两个 PR 各自看起来都对但合在一起出问题；或需要理解整体架构才能判断哪种解法正确 | Step 9：先派 root_cause_analyst 调查 |

**分类判定规则**：
- 如果 Coordinator 在 5 分钟内能看懂冲突、确定修复方向 → 简单或复杂根因明确
- 如果 Coordinator 需要深入理解两个 PR 的交互才能判断 → 系统性
- 如果 explorer 的"初步根因"是"不确定" → 系统性
- 如果多个冲突彼此关联（修一个会影响另一个）→ 系统性
- 意图冲突和隐式依赖默认走系统性路径

## Step 8：简单冲突 — Coordinator 直接修

1. 读两个 PR 的 diff，理解冲突
2. 基于"合并后正确状态"判断修复方向
3. 直接修改代码
4. 跑相关测试确认修复
5. 进入 Step 14（Coordinator 验证）

---
> **下一步**：无冲突 → Step 16（merge-integration-review.md）。简单冲突已修 → Step 14（Coordinator 验证）。复杂冲突 → Step 12（merge-conflict-repair.md）。系统性冲突 → Step 9（merge-rca-investigation.md）。
