---
name: orchestrate-multi-pr-merge
description: "多个来自同一大设计/大计划的并行 PR 需要合并审查时由 orchestrate-workflow Route 3 调用。覆盖完整流程：阅读全部文档建立正确状态理解 → 并行 explorer 发现 PR 间冲突 → 冲突分类与修复分流（简单 / 复杂根因明确 / 系统性根因不明）→ 系统性冲突派 root-cause-analyst 调查根因 → coding worker 落地修复 → Coordinator 验证 → Codex 跨 PR 集成审查 → 按依赖顺序合并 → 返回 verdict 给 orchestrate-workflow 执行 Closing。纯 Coordinator 技能：主线程读取本技能执行调度、冲突分析、修复路由和合并操作；不由 Sub-Agent 消费。"
---

# Orchestrate Multi-PR Merge

多个来自同一大设计/大计划的并行 PR 需要合并。PR 与 PR 之间可能存在代码冲突、功能冲突、意图冲突——这些 PR 各自经历了路线 1（Formal Orchestrate），各自通过了自己的 Final Review，但它们之间的交互尚未验证。

**核心原则**：
- 冲突是 **PR 与 PR 之间**的冲突，不是 PR 与 main 的冲突。
- 代码合并冲突好解决，**功能和意图冲突**最难、最需要思考。
- **Coordinator 读文档**建立方向，**Explorer 做代码验证**——节省主线程上下文。
- **系统性冲突先调查再修**——不让 worker 盲目尝试修复根因不明的冲突。
- 修复后由 **Coordinator 验证**，因为 Coordinator 最了解冲突的方向和正确状态。
- 所有 PR **并行分析**，不是逐个顺序处理。

**Multi-PR Merge 不做 Closing**——不 push，不 PR，不 cleanup。这些是 orchestrate-workflow Closing 的职责。以 verdict 返回结束。

**Multi-PR route 不创建 Budget File**——Codex 审查 dispatch 控制在合理范围内（通常 2-4 次：1-2 full review + 1-2 targeted re-review）。

---

# 第一部分：入口 + 文档理解

## Step 1：读取全部文档

Multi-PR Merge 的前提是所有参与合并的 PR 都来自同一个大设计/大计划。Coordinator 必须建立**全局理解**。

读取以下文档：

| 文档 | 读取内容 |
| --- | --- |
| **大设计文档** | 整体目标、架构方案、模块划分、合同边界、发布风险 |
| **大计划文档** | Task Pack inventory、File/Responsibility Map、依赖关系、合并顺序 |
| **大 Issue 层级** | 各 PR 对应哪些 Issue，Issue 间的依赖和优先级 |
| **各 PR 的小文档** | 每个 PR 自己的 design doc / plan / issue / PR description |
| **各 PR 的代码变更** | `gh pr diff <number>` 或 `git diff main...<branch>` 获取每个 PR 的 diff |
| **各 PR 的 review 记录** | 每个 PR 的 Pack Review / Final Review verdict 和 findings |

## Step 2：建立"合并后正确状态"的理解

基于全部文档，Coordinator 在脑中建立一个模型：**所有 PR 合并后，系统应该是什么样子**。

具体产出（写在工作笔记中，不生成文件）：
1. **行为清单**：合并后系统应该具备的所有行为（从大设计文档提取）
2. **合同地图**：所有跨 PR 的 contract surface（Pydantic model、API、DB schema、JSON payload、registry、migration）
3. **文件交叉矩阵**：哪些文件被多个 PR 修改，或被一个 PR 修改、另一个 PR 依赖
4. **合并顺序**：基于 PR 间的依赖关系确定合并顺序（dependency 先合，dependent 后合）
5. **风险热点**：最可能产生冲突的区域（共享 contract、migration、shared state、UI 集成点）

## Step 3：Scope Contract + Git State

继承 orchestrate-workflow 写的 Scope Contract。验证：

- 当前分支状态（`git status --short --branch`）
- 所有 PR 分支都可达（`git branch -a | grep <branch>`）
- 没有 stale dirty files 干扰合并

---

# 第二部分：并行 PR 分析 — Explorer 派发

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

根据风险热点和 PR 数量，派发 1-N 个 code-explorer（或 complex-code-explorer for 多模块交叉）。可并行派发。

```
Agent({
  subagent_type: "<code-explorer | complex-code-explorer>",
  description: "Multi-PR analysis: <PR set / dimension>",
  prompt: "
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

# 第三部分：冲突分类 + 修复分流

## Step 7：对每个冲突做三级分类

Coordinator 逐个审阅 explorer 发现的冲突，做修复路由判定：

| 分类 | 条件 | 路由 |
| --- | --- | --- |
| **简单** | 代码级冲突（import 顺序、同文件不同区域）；≤ 2 文件；修复方向明确 | Step 8：Coordinator 直接修 |
| **复杂、根因明确** | 功能 / 合同冲突；涉及多文件；但冲突原因清楚——两个 PR 对同一接口做了不同改动，谁该 win 很清楚 | Step 12：派 coding worker |
| **复杂、系统性 / 根因不明** | 意图冲突 / 隐式依赖 / 多个冲突相互关联；冲突原因不清楚——两个 PR 各自看起来都对但合在一起出问题；或需要理解整体架构才能判断哪种解法正确 | Step 9：先派 root-cause-analyst 调查 |

**分类判定规则**：
- 如果 Coordinator 在 5 分钟内能看懂冲突、确定修复方向 → 简单或复杂根因明确
- 如果 Coordinator 需要深入理解两个 PR 的交互才能判断 → 系统性
- 如果 explorer 的"初步根因"是"不确定" → 系统性
- 如果多个冲突彼此关联（修一个会影响另一个）→ 系统性
- 意图冲突和隐式依赖默认走系统性路径

---

# 第四部分：简单冲突 — Coordinator 直接修复

## Step 8：Coordinator 直接修

1. 读两个 PR 的 diff，理解冲突
2. 基于"合并后正确状态"判断修复方向
3. 直接修改代码
4. 跑相关测试确认修复
5. 进入 Step 14（Coordinator 验证）

---

# 第五部分：系统性冲突 — Root-Cause-Analyst 调查

这是 Multi-PR Merge 独特的调查场景。与 Bug Investigation（从零查 bug）和 Repair Truncation（worker 修两轮不过）不同，PR 冲突调查的对象是"两个各自正确的 PR 合在一起为什么出问题"。

## Step 9：构造 Analyst Dispatch

```
Agent({
  subagent_type: "root-cause-analyst",
  description: "Multi-PR conflict investigation: <conflict cluster summary>",
  prompt: "
    ## 调度场景
    Multi-PR Merge 冲突调查。这不是 bug，不是 repair 截断——这是多个并行 PR
    合并时发现的系统性冲突。每个 PR 各自正确（已通过 Final Review），但它们的
    交互产生了冲突。

    ## 大设计文档
    <path>（整体目标 + 架构方案 + 模块划分）

    ## 参与合并的 PR
    | PR | Branch | 核心行为 | 对应 Issue |
    | --- | --- | --- | --- |
    <paste>

    ## Explorer 发现的冲突
    <paste conflict list from explorer — type / PRs / files / description / severity>

    ## Coordinator 的正确状态理解
    <paste from Step 2 — 合并后系统应该是什么样子>

    ## 合同地图
    <paste cross-PR contract surfaces>

    ## 你的任务

    ### 调查方法论（PR 冲突专用）

    PR 冲突与 bug 不同——不是某段代码错了，而是两段各自正确的代码合在一起产生
    了矛盾。你的调查要从"交互"而非"错误"的视角出发。

    **第一步：理解每个 PR 的意图链**

    对每个冲突涉及的 PR：
    1. 读 PR 的 design doc / plan / issue，理解这个 PR 要实现什么
    2. 读 PR 的代码变更（diff），理解它实际做了什么
    3. 标注：意图（design says）→ 实现（code does）→ 假设（code assumes）

    重点关注"假设"——PR A 假设某个接口不会变、某个状态一定存在、某个行为是
    确定的，但 PR B 恰好改变了这个假设的前提。

    **第二步：映射交互点**

    不是逐行 diff，而是画出 PR 间的交互图：
    - 共享文件修改点（同一文件的不同修改）
    - 数据流交叉点（PR A 写的数据被 PR B 读、或反向）
    - 控制流交叉点（PR A 改变了某个条件/路径，PR B 的行为依赖这个路径）
    - 合同交叉点（同一 contract surface 被不同方式修改）
    - 时序交叉点（PR A 假设某个操作先发生，PR B 改变了时序）
    - 状态交叉点（PR A 和 PR B 对同一 shared state 有不同期望）

    **第三步：分类冲突根因**

    每个冲突只有一个根因，属于以下类型之一：

    | 根因类型 | 含义 | 典型表现 |
    | --- | --- | --- |
    | **设计遗漏** | 大设计没有预见到这两个 PR 的交互 | 设计文档没有描述 A 和 B 的协调方式 |
    | **实现偏离** | 某个 PR 偏离了自己的 design | PR A 的 design 说"保持接口不变"但代码改了 |
    | **缺失协调** | 设计说了 A 和 B 要协调，但没有显式合同 | 两个 PR 通过 shared state 隐式耦合 |
    | **隐式耦合** | 两个 PR 没有明确依赖但通过运行时行为耦合 | PR A 依赖的全局 config 被 PR B 改变 |
    | **合同版本冲突** | 两个 PR 各自更新同一合同但方向不同 | Pydantic model 被 A 加字段、被 B 改字段 |
    | **迁移顺序冲突** | 两个 PR 的 migration 合并后顺序有问题 | A 和 B 各自创建的 migration 存在隐式依赖 |

    **第四步：对每个冲突提出解决方案**

    对每个冲突，基于大设计文档判断：

    1. **哪个 PR 的方向更符合设计意图**——如果设计明确了优先级，按设计走
    2. **需要修改哪个 PR 的代码**——尽量只改一边，降低复杂度
    3. **修改的具体方向**——不写代码（那是 worker 的活），写清修改方向和验收标准
    4. **是否需要更新设计文档**——如果冲突暴露了设计遗漏

    如果冲突是设计层面的（两个 PR 的目标本身矛盾），你**不应该自己决定方向**——
    标注为"设计/意图冲突"，让 Coordinator 回到 Discovery 或询问用户。

    **第五步：评估关联性**

    如果多个冲突相互关联（修一个会影响另一个），要标注关联关系和建议的修复顺序。

    ## 停止条件

    - 冲突根因涉及设计层面决策 → 停止，标注为设计/意图冲突
    - 冲突涉及功能范围变更 → 停止，标注为业务决策
    - 3 个假设无确认证据 → 停止，报告已排除路径
    - 冲突太复杂需要更多 PR 上下文 → 停止，标注缺失信息

    ## 不重复规则

    每个假设必须和前几个不同维度。记录每个假设的排除证据。

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context

    ### Evidence
    - 实际检查过的 PRs / files / diffs / docs

    ### Result
    - Resolution: root_cause_identified / design_conflict / implementation_deviation / unable_to_determine
    - 冲突分析：
      | # | 冲突 | 根因类型 | 涉及 PR | 根因详述 | 修复方向 | 需改哪个 PR | 关联冲突 |
    - 设计影响：<大设计是否需要更新 / 无>
    - 建议修复顺序：<如果多个冲突有关联>
    - 排除的假设：<with evidence>
    - 回归风险：<修复后可能影响的区域>

    ### Verification

    ### Open Items
  "
})
```

## Step 10：接收 Analyst 返回

Coordinator 审阅 analyst findings，不是盲目接受——主动验证：

1. **对照设计文档**：analyst 的根因判断是否与设计意图一致
2. **对照 PR diff**：analyst 说的文件/代码/行为是否与实际代码一致
3. **评估修复方向**：analyst 建议的修复方向是否合理、是否有更简单的路径

## Step 11：Analyst Resolution 路由

| Analyst Resolution | Coordinator 动作 |
| --- | --- |
| `root_cause_identified` | 逐个冲突审阅修复方向 → 按修复顺序逐个 dispatch worker（Step 12） |
| `design_conflict` | 冲突在设计层面——两个 PR 的目标本身矛盾。两条路：(1) 回 orchestrate-discovery 让用户重新对齐设计 → 返回 `NEEDS_DISCOVERY`；(2) 当场询问用户做决策 → 拿到决策后继续 |
| `implementation_deviation` | 某个 PR 偏离了设计——定位到具体偏离，dispatch worker 修复偏离（Step 12） |
| `unable_to_determine` | 派 complex-code-explorer 补充信息后重新 dispatch analyst；或 BLOCKED 报告用户 |

---

# 第六部分：复杂冲突 — Coding Worker 修复

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

## Step 13：接收 Worker 返回

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | 进入 Step 14（Coordinator 验证） |
| `needs repair` | worker 自己有疑虑 → 审阅 concerns，能自主解决则补充信息后 SendMessage worker 继续；否则进入 Step 14 让验证环节处理 |
| `needs context` | SendMessage 补充上下文给原 worker |
| `blocked` | 技术阻塞：尝试拆分冲突 / 换更强模型。业务阻塞：询问用户 |

---

# 第七部分：Coordinator 验证 + 冲突解决循环

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

# 第八部分：Codex 跨 PR 集成审查

所有冲突解决后（或 explorer 一开始就没发现冲突），进入 Codex 集成审查。

## Step 16：构造 Codex Dispatch

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

## Step 17：接收 + Disposition

**Coordinator 不是传话筒**——逐条验证每个 finding：

1. 读代码确认 finding 是否成立
2. 对照大设计文档确认 spec 判断
3. 对照冲突解决记录确认修复判断

Disposition 表（同其他 phase）：

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

---

# 第九部分：顺序合并 PR

## Step 19：确定合并顺序

Codex 集成审查通过后，按依赖顺序合并 PR。

合并顺序基于 Step 2 确定的依赖关系：
1. 被依赖的 PR 先合（foundation / infra / contract provider）
2. 依赖方后合（consumer / feature / UI）
3. 无依赖关系的按计划文档中的顺序

## Step 20：逐个执行合并

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

## Step 21：全量集成验证

所有 PR merge 完成后：
1. 跑完整测试套件
2. 跑大设计文档中所有 validation commands
3. 确认合并后的行为与"合并后正确状态"模型一致

---

# 第十部分：不存在非阻塞项

**铁律同样适用于 Multi-PR Merge。**

合并完成后，检查：
- 所有冲突解决记录中标记为 "out of scope" 的项 → 确认已开 GitHub issue
- 合并过程中 worker Open Items → 逐项处置（修复 / 开 issue / 确认不是问题）
- `git diff <base>..HEAD` 范围内新增的 TODO/FIXME → 处置

---

# 第十一部分：返回

## Step 22：确定 Verdict

| 条件 | Verdict |
| --- | --- |
| 所有 PR 合并成功 + 集成审查通过 + 全量测试通过 | `MERGE_COMPLETE` |
| analyst 发现设计/意图冲突，需要重新对齐设计 | `NEEDS_DISCOVERY` |
| 冲突解决需要用户决策 | `NEEDS_USER_DECISION` |
| 无法自主解决 | `BLOCKED` |

## 返回格式

```text
### Verdict
MERGE_COMPLETE | NEEDS_DISCOVERY | NEEDS_USER_DECISION | BLOCKED

### PRs merged
| PR | Branch | Merge order | Status |
| --- | --- | --- | --- |
<per-PR status>

### Conflict resolution summary
- Total conflicts found: <count>
- Simple (coordinator fix): <count>
- Complex (worker fix): <count>
- Systemic (analyst → worker): <count>
- Design/intent conflicts: <count>

### Per-conflict details
| # | Type | PRs | Root cause | Resolution | Verified |
<per-conflict>

### Integration review
- Codex review verdict: pass / needs repair
- Findings: <count> / Accepted: <count> / Rejected: <count>
- Repair rounds: <count>

### Git state
- Branch: <current branch>
- Merge commits: <list>
- Clean: yes / no

### Test results
- Full suite: pass / fail
- Validation commands: pass / fail

### Open items
- Blockers: <if any>
- Issues created: <GitHub issue refs>
- Design updates needed: <if any>

### Next route
- orchestrate-workflow Closing / orchestrate-discovery / user decision / blocked
```
