# 解决一张 decision ticket

用户带着一张 map 来（编号或链接）。这个会话只解决一张 decision ticket。完成回填和交回后停止，不沿新 frontier 继续。

## 1. 读取 map

这一步只读：

- `gh issue view <map 编号>` 读 map 正文，不逐个打开 ticket。
- 读取 map 正文的 `产物目录`。这个值在整个 effort 内保持不变。
- 按需读取 map 分支上的文件。领域文档落点通过 `mmw domain path` 取得，再运行 `git show <map 分支>:<落点>`。
- `mmw issue frontier <map 编号>` 查一次 frontier。它给出全部可认领的 ticket，一行一张。

frontier 为空时，不建立 decision ticket 任务。停止并让用户恢复拥有 map 分支的任务；该任务读取 [closing.md](closing.md)。

## 2. 挑一张，认领，建立任务 worktree

用户点了名就用他点的那张。用户没有点名时，取 frontier 上的第一张。

先运行 `mmw issue claim <编号>` 完成认领。认领失败说明另一个会话已经占用，改取下一张。认领成功前不调查、不讨论、不修改文件。

任务 slug 使用 `<map slug>-<ticket 短语>`。父分支必须是 map 分支；任务从 map 分支当前已提交的 HEAD 开始。任务 slug 只识别任务，不决定产物落点。

Codex App 在任务创建时已经准备好 detached worktree。确认任务范围和父分支后，运行 `mmw task bind codex/<slug> "<用户原话>" --from <父分支或基点 SHA>`。命令必须返回任务分支名和起始提交；当前状态不是 detached、工作区不干净、分支已存在或父分支不正确时停下。

## 3. 解决这张 ticket

按需读取相关或已关闭 ticket 的完整正文，并调用 map `Notes` 点名的技能。

先确认 ticket 原样继承了 map 的 `产物目录`，并且 `issue 子目录` 是这张 ticket 的 `issue-<编号>`。然后计算精确路径：

```bash
mmw artifact path prototype <产物目录> issue-<编号>
mmw artifact path evidence <产物目录> issue-<编号>
mmw artifact path scratch <产物目录> issue-<编号>
```

只把这三条命令的实际输出传给 prototype 或外部系统实测流程，不传 worktree slug 代替路径。

| 标签 | 解法 |
| --- | --- |
| `wayfinder:grilling` | 跑 `$mmw:mmw-grilling`，把 `Question` 谈成双方确认的共同理解；提问方式全部由该技能决定 |
| `wayfinder:prototype` | 跑 `$mmw:mmw-prototype` 做一个粗糙版本给用户走查；传入 prototype 产物路径和 scratch 路径的精确输出，结案评论指向 prototype 产物路径 |
| `wayfinder:research` | 按 `$mmw:mmw-research` 派一个 subagent，只调查这一个决定等待的事实；按 `$mmw:mmw-verifying-agent-output` 验证后再写入 ticket 评论。如果调查升级为外部系统实测，向 `$mmw:mmw-prototype` 传入 evidence 产物路径和 scratch 路径的精确输出 |
| `wayfinder:task` | agent 能完成就执行，并在结案评论记录结果事实；必须人动手时，简单操作给精确清单，包含多个步骤、值采集或 secret 落点的流程使用 `/wizard` 生成脚本 |

HITL ticket 不许 agent 替用户回答。

## 4. 记录这次解答

按顺序完成六件事：

1. 把答案写成结案评论，然后关闭 ticket。
2. 往 map 的 `Decisions so far` 追加一行索引。修改前重新读取 map 最新正文；修改后再次读取，确认该行存在。
3. 按 `$mmw:mmw-domain-modeling` 的完整 ADR 判据评估决定。三项判据全部成立时，先写 `draft-<ticket 编号>-<kebab-标题>.md`。ADR 目录通过 `mmw domain dirs` 取得。
4. 把新术语写入拥有该概念的 leaf。领域文档落点通过 `mmw domain path` 取得。
5. 把这次答案已经驱散的 fog of war 从 `Not yet specified` 移出。能精确表述的部分建立为新 ticket。新 ticket 原样继承 map 的 `产物目录`；取得 tracker 编号后，回填自己的 `issue-<编号>` 子目录，再连接阻塞关系。
6. 这次答案若证明某张 ticket 位于 destination 之外，关闭该 ticket，在 `Out of scope` 留一行，并在 `.out-of-scope/` 保存理由。若其他 ticket 已失效，同步更新或删除。

修改 map 正文时只改本次涉及的行，不整份重写。

## 5. 判断能否提前切出 spec

不必等 map 收尾才切 spec。当前决定完成后，某份 spec 同时满足三条，就可以另开会话进入 `$mmw:mmw-to-spec`：

| 条件 | 怎么查 |
| --- | --- |
| 题目已经清楚 | 能说明它交付什么，不需要其他决定定义它自己 |
| 依赖的决定全部关闭 | 每条都能在 `Decisions so far` 找到 |
| 剩余 fog 不会波及它 | 逐条检查 `Not yet specified` |

这一步只报告可切出的 spec，不在当前会话继续写 spec。

## 6. 提交并交回 map 任务

1. 把本任务写的 ADR 草稿逐个改为正式编号。每次运行 `mmw domain adr-next` 取得一个新编号。提交全部改动。
2. 记录任务分支名、`git rev-parse HEAD` 和建立任务时的 map 基点 SHA。
3. 把分支名、HEAD SHA、基点 SHA 和报告交回 map 任务。map 任务先运行 `mmw result verify`，验证报告与 diff，再运行 `mmw result integrate`。
4. map 任务集成后重新查询 `mmw issue frontier <map 编号>`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 手上是必须由人完成的 `wayfinder:task` | **停**：给用户精确操作清单，等结果回来后继续本张 ticket |
| 当前 ticket 已解决，任务结果已交回 | **停**：报告解决的 ticket 和当前 frontier；新 ticket 由另一个会话认领 |
| 第 5 步发现一份 spec 已满足三项条件 | **停**：报告这份 spec 已可开始，让用户另开会话走 `$mmw:mmw-to-spec` |
| map 任务集成后发现 frontier 为空 | **移交**：map 任务读取 [closing.md](closing.md) |
