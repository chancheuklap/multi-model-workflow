# Multi-PR 系统性冲突 — Root-Cause-Analyst 调查

> **流程位置**：`orchestrate-multi-pr-merge` Steps 9-11 · 仅系统性冲突时进入

## Self-Read Protocol

你是 root-cause-analyst（执行 Multi-PR 系统性冲突调查）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`，获取大设计文档路径、PR 列表、合同地图。
3. 读大设计文档（来自 merge-brief）理解整体目标 + 架构方案 + 模块划分。
4. 读本文件 `## 方法论` 章节，按其中 5 步方法论执行调查。
5. 理解 Return Contract 格式。
6. 使用 Multi-PR Conflict Investigation 方法论，从"交互"而非"错误"的视角调查。

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

    ## Merge context
    读 `.claude/multi-model-workflow/merge-brief-<run_id>.md` 获取：
    - 大设计文档路径（你自读该文档，获取整体目标 + 架构方案 + 模块划分）
    - 参与合并的 PR 列表（PR / Branch / 核心行为 / 对应 Issue）
    - Explorer 发现的冲突列表（type / PRs / files / description / severity）
    - Coordinator 的正确状态理解（合并后系统应该是什么样子）
    - 合同地图（cross-PR contract surfaces）

    ## Methodology
    启动后按本文件 ## 方法论 章节中 5 步执行调查。

    ## 你的任务

    使用 Multi-PR Conflict Investigation 方法论（模式 3）。
    从"交互"而非"错误"的视角出发——不是某段代码错了，而是两段各自正确的
    代码合在一起产生了矛盾。

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

**`unable_to_determine` Explorer Dispatch**：

```
Agent({
  subagent_type: "complex-code-explorer",
  description: "Supplement PR conflict investigation: <conflict cluster>",
  prompt: "
    ## Scope
    只读调查。Root-cause-analyst 无法确定 PR 间冲突的根因，需要更多信息。

    ## Analyst 已排除的假设
    读 dispatch prompt 中 Coordinator 传入的 analyst 已排除假设摘要（含证据）。

    ## Merge context
    读 `.claude/multi-model-workflow/merge-brief-<run_id>.md` 获取：
    - PR 列表和各 branch（你自行 git diff 获取相关代码段）
    - 大设计文档路径（你自读该文档）

    ## 待澄清的冲突
    读 dispatch prompt 中 Coordinator 传入的 analyst 未解决冲突摘要。

    ## 调查方向
    <Coordinator 根据 analyst 排除路径判断的下一步方向——
     隐式依赖 / 运行时行为耦合 / 配置传播 / 时序依赖等>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 PRs / files / diffs / docs
    ### Result
    - Facts: confirmed facts with locators
    - Inferences: hypotheses, clearly marked
    - Excluded paths: hypotheses checked and ruled out with evidence
    - Recommended next probe: <for analyst re-dispatch>
    ### Verification
    ### Open Items
  "
})
```

Explorer 返回后：用 explorer findings 补充 analyst prompt，重新 dispatch `root-cause-analyst`（Step 9）。**Analyst ↔ Explorer 循环最多 1 次**（analyst → explorer → analyst）。第 2 轮 analyst 仍返回 `unable_to_determine` → BLOCKED，报告用户。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 analyst 自读：

1. 写 `merge-brief-<run_id>.md`（若已写则复用），确保包含 PR 列表、设计文档路径、冲突列表、合同地图、正确状态理解。
2. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`phase: "multi-pr-merge"`、`agent_role: "root-cause-analyst"`。
3. 触发 analyst 派发，保存 `agentId`。
4. 等待 analyst 返回后按 Step 11 路由表处置。

---

## 方法论

PR 冲突与 bug 不同——不是某段代码错了，而是两段各自正确的代码合在一起产生了矛盾。调查要从"交互"而非"错误"的视角出发。

### 第一步：理解每个 PR 的意图链

对每个冲突涉及的 PR：
1. 读 PR 的 design doc / plan / issue，理解这个 PR 要实现什么
2. 读 PR 的代码变更（diff），理解它实际做了什么
3. 标注：意图（design says）→ 实现（code does）→ 假设（code assumes）

重点关注"假设"——PR A 假设某个接口不会变、某个状态一定存在、某个行为是确定的，但 PR B 恰好改变了这个假设的前提。

### 第二步：映射交互点

不是逐行 diff，而是画出 PR 间的交互图：
- 共享文件修改点（同一文件的不同修改）
- 数据流交叉点（PR A 写的数据被 PR B 读、或反向）
- 控制流交叉点（PR A 改变了某个条件/路径，PR B 的行为依赖这个路径）
- 合同交叉点（同一 contract surface 被不同方式修改）
- 时序交叉点（PR A 假设某个操作先发生，PR B 改变了时序）
- 状态交叉点（PR A 和 PR B 对同一 shared state 有不同期望）

### 第三步：分类冲突根因

每个冲突只有一个根因，属于以下类型之一：

| 根因类型 | 含义 | 典型表现 |
| --- | --- | --- |
| **设计遗漏** | 大设计没有预见到这两个 PR 的交互 | 设计文档没有描述 A 和 B 的协调方式 |
| **实现偏离** | 某个 PR 偏离了自己的 design | PR A 的 design 说"保持接口不变"但代码改了 |
| **缺失协调** | 设计说了 A 和 B 要协调，但没有显式合同 | 两个 PR 通过 shared state 隐式耦合 |
| **隐式耦合** | 两个 PR 没有明确依赖但通过运行时行为耦合 | PR A 依赖的全局 config 被 PR B 改变 |
| **合同版本冲突** | 两个 PR 各自更新同一合同但方向不同 | Pydantic model 被 A 加字段、被 B 改字段 |
| **迁移顺序冲突** | 两个 PR 的 migration 合并后顺序有问题 | A 和 B 各自创建的 migration 存在隐式依赖 |

### 第四步：对每个冲突提出解决方案

对每个冲突，基于大设计文档判断：
1. **哪个 PR 的方向更符合设计意图**——如果设计明确了优先级，按设计走
2. **需要修改哪个 PR 的代码**——尽量只改一边，降低复杂度
3. **修改的具体方向**——不写代码（那是 worker 的活），写清修改方向和验收标准
4. **是否需要更新设计文档**——如果冲突暴露了设计遗漏

如果冲突是设计层面的（两个 PR 的目标本身矛盾），**不要自己决定方向**——标注为 `design_conflict`，让 Coordinator 回到 Discovery 或询问用户。

### 第五步：评估关联性

如果多个冲突相互关联（修一个会影响另一个），标注关联关系和建议的修复顺序。

---
> **下一步**：root_cause_identified / implementation_deviation → Step 12（`merge-conflict-repair.md`）。design_conflict → 返回 verdict。unable_to_determine → 派 explorer 补信息或 BLOCKED。
