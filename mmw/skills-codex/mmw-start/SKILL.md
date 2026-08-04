---
name: mmw-start
description: 多模型工作流的入口——判定这次的任务走哪条路，建 worktree 再移交。用户开始一件新任务、提一个新需求、报一个 issue 编号、说要接着做某张 map、说有东西坏了、或者只说要开工时用它；什么都没交代时它报当前进度。
argument-hint: "[bug|big] [要做的事，或者一张 map 的编号]"
---

本技能只做路由，这次任务本身一个字都不实现。

本次输入：`$ARGUMENTS`

这一栏为空、用户也没有在对话里交代要做什么，走 [resuming.md](resuming.md)。已经在一个任务 worktree 里的，同样走 [resuming.md](resuming.md)。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。有标签就直接用，不要再推断。

| 情况 | 下一步 |
| --- | --- |
| 一张 map 的编号或链接，或者他说要接着做某张 map | **移交**：`$mmw:mmw-wayfinder` |
| 一个 issue 编号，带着某个 `wayfinder:` 类型标签——那是一张 map 上的一条 decision ticket | **移交**：`$mmw:mmw-wayfinder` |
| 一个 issue 编号，挂在一张带 `wayfinder:map` 标签的 issue 底下、自己不带 `wayfinder:` 标签——那是收尾时切出来的一份 spec | **移交**：`$mmw:mmw-to-spec` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`$mmw:mmw-triage` |
| 一个 issue 编号，已是 `ready-for-agent`，brief 写明 `**Test seam:**`，而且只碰一处 | **移交**：`$mmw:mmw-implement` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`$mmw:mmw-diagnosing-bugs` |
| 一个 effort，还不知道要拆成哪几份 spec，或者挂了 `big` | **移交**：`$mmw:mmw-wayfinder` |
| 想先看看某个界面长什么样，或者不确定一套状态模型对不对 | **移交**：`$mmw:mmw-prototype` |
| 只要一条查得清的事实，比如某个库或某个外部接口的官方说法 | **移交**：`$mmw:mmw-research`，跳过第 2、3 步 |
| 一个新需求，或对已有需求的改进 | **移交**：`$mmw:mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`$mmw:mmw-improve-codebase-architecture`，跳过第 2、3 步 |
| 几条并行分支要集成到主线，某条分支要跟上已经推进的主线，或者手上有一个正在进行中的冲突 | **移交**：`$mmw:mmw-integrate`，跳过第 2、3 步 |

**先做原型还是先谈清楚**：他要的是先看见一个能跑的东西，走 `$mmw:mmw-prototype`；他要的是先把这件事说清楚，走 `$mmw:mmw-grilling`。分不出来时走 `$mmw:mmw-grilling`。

**effort 怎么认**：判据是这件事要拆成几份 spec。一份 spec 说得完、拆出的 ticket 都挂在这份 spec 底下，走 `$mmw:mmw-grilling`。要好几份 spec 才做得完，而且哪几份、按什么顺序都还没有答案，才是 `$mmw:mmw-wayfinder`。

带 issue 编号的，先 `gh issue view <编号> --comments` 把它读出来再判，不要只看编号。标签的含义见 `$mmw:mmw-triage`。

## 2. 定 slug

名字叫 **slug**，形状是 `<类型>-<短语>`：类型取 Conventional Commits 那一套，短语用 kebab 说清这次做什么。例如 `feat-phone-login`、`fix-refund-rounding`、`refactor-order-state`。

| 类型 | 用在 |
| --- | --- |
| `feat` | 新增用户可见的能力 |
| `fix` | 修一个缺陷 |
| `refactor` | 改内部结构，外部行为不变 |
| `perf` | 改性能 |
| `docs` | 只改文档 |
| `test` | 只改测试 |
| `chore` | 依赖、配置、构建脚本 |

类型取自第 1 步的判定结果：走 `$mmw:mmw-diagnosing-bugs` 的用 `fix`，新需求和先做原型的用 `feat`。类型同时约束范围——一个 `fix` 里混进新功能，说明当初的类型定错了，或者这次改动该拆成两个。

**一个 slug 贯穿五处**：worktree 目录名、分支名、`docs/specs/<slug>/`、这个目录里的主文件 `<slug>.md`、Wiki 上的 `Spec-<slug>.md`。别的技能提到 `<slug>` 时指的都是它。

类型前缀用连字符不用斜杠——斜杠会在 worktree 落点下建出子目录，破坏「目录不嵌套」。不带 issue 编号、不带日期。同名冲突时加一个区分词，不加序号。

**下面四种情况跳过这一步**，第 3 步也一并跳过：

- 用户报的是一张已有 map 的编号或链接。slug 由 `$mmw:mmw-wayfinder` 定。
- 判定走 `$mmw:mmw-improve-codebase-architecture`。slug 由它定，类型固定用 `refactor`。
- 判定走 `$mmw:mmw-research`。
- 判定走 `$mmw:mmw-integrate`。它在主仓库的主线上做，不要给它建 worktree。

## 3. 绑定 Codex App 已创建的 worktree

Codex App 在任务创建时已经固定当前 worktree。确认任务范围之前只读，不建分支、不改文件。

任务范围确认后，先确认当前 checkout 满足三条：它是 linked worktree；`HEAD` 是 detached；`git status --porcelain` 为空。然后运行与本 `SKILL.md` 同目录的 `scripts/bind-current-worktree.sh`：

```bash
bash <本技能目录>/scripts/bind-current-worktree.sh "codex/<slug>" "<用户交代这件事时的原话>"
```

脚本只在干净的 detached worktree 上创建分支，并用空提交保存用户原话。分支已经存在、当前 checkout 不是 detached、工作区不干净时，脚本必须失败。

从 map 派生的任务必须在创建 Codex App 任务时把 `startingState` 选为 map 分支。当前 `HEAD` 不包含 map 分支提交时停下，不能在已经创建的 worktree 里改基点。

当前任务不是 Codex App worktree 时停下，让用户新建 Worktree 任务。主 agent 不创建替代目录，也不切换当前任务的工作根目录。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起第 1 步判出的那个技能，把用户原话原样传过去 |
| 第 1 步那张表哪一行都对不上，或者同时对上互相冲突的两行 | **停**：把你认为可能的那两三条路线连同各自的判据摆给用户，让他点一条。不要挑一条最像的就往下走 |
