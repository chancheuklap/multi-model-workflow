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
