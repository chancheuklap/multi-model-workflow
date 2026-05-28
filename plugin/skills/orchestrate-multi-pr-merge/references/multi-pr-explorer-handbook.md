# Multi-PR Explorer Handbook

> **角色**：code-explorer 或 complex-code-explorer，负责 Multi-PR 冲突发现分析。
> **流程位置**：orchestrate-multi-pr-merge Steps 4-6，并行分析所有 PR，报告冲突。

## Self-Read Protocol

启动时按以下顺序执行，缺少任何步骤 → BLOCKED，不猜测：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`：
   - §2 PR 表：获取所有 PR 的 branch、大设计文档路径、核心行为。
   - §3 合同地图、文件交叉矩阵：获取已知风险热点，作为分析起点。
3. 读大设计文档（来自 merge-brief §2 的 `big_design_path`），理解跨 PR 的整体目标。
4. 读本文件（你正在读的这份 handbook），理解分析维度和 Return Contract 格式。
5. 并行分析所有 PR，按 5 维分析框架识别冲突，输出结构化报告。

---

## 5 维冲突分析框架

对每个 PR 对（cross-product，不是顺序对），检查以下 5 个维度：

### 维度 1：代码冲突

**检查**：同一文件 / 同一函数 / 同一行被多个 PR 修改？

工具：
```bash
# 获取各 PR 的修改文件列表
git diff --name-only main...<branch_A>
git diff --name-only main...<branch_B>
# 找交集
comm -12 <(git diff --name-only main...<branch_A> | sort) \
         <(git diff --name-only main...<branch_B> | sort)
```

**典型症状**：import 冲突、函数签名冲突、同一行不同修改。
**预期严重程度**：低（git merge 通常能自动解决，但仍须报告）。

### 维度 2：功能冲突

**检查**：PR A 的功能依赖 PR B 修改的接口或行为？

步骤：
1. 读 PR A 的 commit message + PR description，理解功能意图。
2. 读 PR B 的 diff，找到 PR A 依赖的接口位置。
3. 判断 PR B 的修改是否破坏了 PR A 的依赖假设。

**典型症状**：PR A 调用 PR B 已修改的函数签名；PR A 依赖 PR B 已删除的字段。
**预期严重程度**：中（需理解两个 PR 行为才能判断）。

### 维度 3：意图冲突

**检查**：PR A 和 PR B 对同一领域概念做出不同假设？

步骤：
1. 从各 PR 的设计文档提取"核心假设"列表（用户模型、数据流、状态机）。
2. 比对相关领域概念的定义——不同 PR 的理解是否一致？

**典型症状**：两个 PR 都改了"user 的主键"，但一个假设 id，另一个假设 email；两个 PR 对"active state"有不同定义。
**预期严重程度**：高（可能需要设计层面决策）。

### 维度 4：合同冲突

**检查**：同一 contract surface 被不同 PR 以不兼容方式修改？

来源：merge-brief §3.2 合同地图，以及自行搜索：
```bash
# 搜索 Pydantic model 修改
git diff main...<branch> -- "*.py" | grep "^+.*class.*BaseModel"
# 搜索 migration 修改
git diff --name-only main...<branch> | grep "migrations"
```

**典型症状**：同一 Pydantic model 被两个 PR 以不同方式扩展；两个 migration 操作同一张表。
**预期严重程度**：高（合同破损影响全局，且通常难以在运行时发现）。

### 维度 5：隐式依赖

**检查**：PR A 假设某个 state/config/behavior 存在，但 PR B 改变了它（不在文件交叉矩阵中，通过运行时行为耦合）？

这是最难发现的冲突。检查方法：
1. 找 PR A 中所有对外部状态的读取（env var、config、cache、全局变量）。
2. 搜索 PR B 是否修改了这些状态的来源。
3. 检查 PR A 依赖的"行为契约"——如某个函数总是返回某种格式，PR B 是否改变了这个格式？

**典型症状**：PR A 假设 `get_user()` 返回包含 `email` 的 dict，PR B 将返回值改为 Pydantic model；PR A 读取 env var 而 PR B 重命名了该 env var。
**预期严重程度**：最高（最难发现，运行时才爆）。

---

## 严重程度分级

| 严重度 | 定义 | 行动 |
| --- | --- | --- |
| `blocker` | 合并后系统立即无法启动或核心功能完全失效 | 必须修复后才能进行集成审查 |
| `high` | 合并后关键功能异常，但系统可启动 | 在 integration review 前必须修复 |
| `medium` | 合并后次要功能异常 | 可在 integration review 后修复，但需记录 |
| `low` | 合并后仅影响边缘场景或代码质量 | 可作为 open item，不阻塞合并 |

---

## 输出规范（Return Contract）

每个冲突独立报告，格式如下：

```markdown
### Conflict C-NNN（Coordinator 分配 id）

- **type**: code | function | intent | contract | implicit-dep | migration-order
- **involved_prs**: [#NNN, #MMM]
- **files**: [file:line 列表]
- **description**: 
  - PR #NNN 做了什么：<具体说明>
  - PR #MMM 做了什么：<具体说明>
  - 冲突原因：<为什么两者不兼容>
- **severity**: blocker | high | medium | low
- **evidence**: <代码引用，file:line + 代码片段>
- **suggested_classification**: simple | complex-clear | systemic（供 Coordinator 参考，不强制）
```

无冲突时报告：

```markdown
### No Conflicts Found

- PRs analyzed: [#NNN, #MMM, ...]
- Analysis coverage: [列出检查过的维度 + 工具]
- Confidence: high | medium（低于 medium 需说明原因）
```

最后附 Return Contract 汇总：

```markdown
## Verdict
CONFLICTS_FOUND | NO_CONFLICTS

## Evidence
（简要描述分析覆盖面）

## Result
- Conflicts found: <count>
- Per-conflict: <conflict 列表>

## Verification
（运行过哪些命令）
```
