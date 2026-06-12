# Multi-PR Merge 入口 + 文档理解

> **流程位置**：`orchestrate-multi-pr-merge` Steps 1-3 · 完成后 → Steps 4-8（`merge-conflict-discovery.md`）

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
| **各 PR 的 review 记录** | 每个 PR 的 Plan Implementation Review / Final Review verdict 和 findings |

## Step 2：创建 merge-brief + 建立"合并后正确状态"的理解

**merge-brief 是合成模型的唯一权威源，Step 2 必须创建，不得省略。**

```bash
# 1. 创建 merge-brief（幂等，已存在则保留）
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" merge-brief init \
  --run-id "<run_id>" --slug "<feature-slug>"

# 2. 更新 workflow-state.cursor.reference 指向 merge-brief
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" update \
  --run-id "<run_id>" \
  --field ".cursor.reference" \
  --value '".codex/multi-model-workflow/merge-brief-<run_id>.md"'
```

然后 Coordinator 读完所有 PR 文档后，按 `references/merge-brief-template.md` 直接 Edit merge-brief，填写以下内容（写完后禁止进入 Step 4）：

1. **§2 PR 表**：每个 PR 的 branch、大设计 path、大计划 path、Final Review verdict、核心行为（≤2 句）
2. **§3.1 行为清单**：合并后系统应该具备的所有行为（从大设计文档提取）
3. **§3.2 合同地图**：所有跨 PR 的 contract surface（Pydantic model、API、DB schema、JSON payload、registry、migration）
4. **§3.3 文件交叉矩阵**：哪些文件被多个 PR 修改，或被一个 PR 修改、另一个 PR 依赖
5. **§3.4 合并顺序**：基于 PR 间的依赖关系确定合并顺序（dependency 先合，dependent 后合）
6. **§3.5 风险热点**：最可能产生冲突的区域（共享 contract、migration、shared state、UI 集成点）

merge-brief 写完后验证：
```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" merge-brief verify --run-id "<run_id>"
```

## Step 3：Scope Contract + Git State

继承 orchestrate-workflow 写的 Scope Contract。验证：

- 当前分支状态（`git status --short --branch`）
- 所有 PR 分支都可达（`git branch -a | grep <branch>`）
- 没有 stale dirty files 干扰合并

---
> **下一步**：准备完成 → Steps 4-8（`merge-conflict-discovery.md`）。
