# 认领一条链

用户带着一张 map 来（编号或链接）。这个会话解**一条链**：解开一张 ticket，接着解被它解锁的那张，直到不能再往下走。判断能不能往下走的规矩在第 5 步。

## 1. 读取 map

这一步只读：

- `gh issue view <map 编号>` 读 map 正文，不要逐个打开 ticket。
- 按需读取 map 分支上的文件。领域文档落点通过 `mmw domain path` 取得，再运行 `git show <map 分支>:<落点>`。
- `mmw issue frontier <map 编号>` 查一次 frontier。它给出全部可认领的 ticket，一行一张。

frontier 为空时，不建立链任务。停止并让用户恢复拥有 map 分支的任务；该任务读取 [closing.md](closing.md)。

## 2. 挑一张，认领，建立链任务 worktree

用户点了名就用他点的那张，没点就取 frontier 上的第一张。

**先认领**：`mmw issue claim <编号>`。它已经被别的会话占住就会失败，那就取下一张。认领成功之前不要做任何事。

链任务的 slug 使用 `<map slug>-<链首 ticket 短语>`。父分支必须是 map 分支；链任务从 map 分支当前已提交的 HEAD 开始。

[[mmw-host-action:prepare-task-worktree]]

## 3. 解它

**按需放大**：随时取任何相关的、或者已经关掉的 ticket 的完整正文；把 map 的 `Notes` 一节点名的技能调起来。

建 ticket 时怎么选这四个类型见 [map-anatomy.md](map-anatomy.md)，本节只写解的时候怎么做（HITL / AFK 归属见本文第 5 步内的归属表，判下一张归不归你时要用）：

| 标签 | 解法 |
| --- | --- |
| `wayfinder:grilling` | 跑 `/mmw-grilling`，一次问用户一个问题 |
| `wayfinder:prototype` | 跑 `/mmw-prototype` 做一个粗糙版本给用户走查。产物落 `docs/prototypes/<slug>/`，结论按 `/mmw-prototype` 的回填规矩写成结案评论，评论里留一个指向产物目录的路径 |
| `wayfinder:research` | 按 `/mmw-research` 派一个 subagent 去查，只查这一个决定要等的那条事实，答完就停。按 `/mmw-verifying-agent-output` 验证过的事实才写进 ticket 评论，没查清的另起一节列出来 |
| `wayfinder:task` | agent 自己做得完就自己做完，把结果事实记进结案评论：凭证放在哪、新的地址是什么、数据有多少行。必须人动手的，停下来交一份精确的操作清单给用户，等他做完再回第 4 步 |

**HITL 的 ticket 不许 agent 替那个人回答。**

## 4. 记录这次解答

六件事按顺序做完：

1. 答案写成**结案评论**贴在这张 ticket 上，然后**关掉**它。
2. 往 map 的 `Decisions so far` 一节追加一行索引。**追加之前先重新拉一次 map 的最新正文**，写完再读一次确认自己那行在。
3. 这个决定难以回退、而且真有取舍，就另写一份 ADR。**链上先写草稿名** `draft-<ticket 编号>-<kebab-标题>.md`，落点跑 `mmw domain dirs` 取 `adr` 那一行；等这条链走完、合回 map 分支时再统一改成正式编号。几条链同时跑，各自取号必定撞，草稿名是绕开它的办法（见 `/mmw-domain-modeling` 的 `ADR-FORMAT.md`）。什么样的决定才够格写 ADR，判据也在那个技能里。
4. 谈出来的新术语追加进领域文档。落点跑 `mmw domain path` 取：`single` 使用命令返回的 leaf；`map` 使用 Map 为这条链登记的实际 leaf 路径。
5. 更新 map：这次答案让哪块 fog of war 说得清楚了，就从 `Not yet specified` 一节里拿出来建成新 ticket，再连阻塞关系（先建 issue，拿到编号再连边）。
6. 这次答案要是暴露出某张 ticket 坐在 destination 之外，就判它出范围：关掉它，在 `Out of scope` 一节留一行，并在 `.out-of-scope/` 写一份。判据见 [map-anatomy.md](map-anatomy.md) 的「什么算判出范围」一节。这个决定让 map 的其他部分作废了，就更新或删掉作废的那些 ticket。

改 map 正文时**只改自己动过的那几行**，不整份重写。

## 5. 判断这条链还能不能往下走

查这次解开的这张 ticket 解锁了哪些 ticket，**逐张**按下面两关判。

**第一关，这张还归不归你。** 再查一次 `mmw issue frontier <map 编号>`，这次解开的这张所解锁的 ticket 里，出现在 frontier 上的才归你——没出现就是还被别的 ticket 挡着，或者已经被别的会话认领走了。一张 ticket 可能被两条链同时解锁，谁先认领上谁继续，另一条到此为止。

**第二关，这张是 HITL 还是 AFK。** 这一关在指派之前判，判法：

| 这张 ticket 的标签 | 判定 |
| --- | --- |
| `wayfinder:research` | AFK |
| `wayfinder:grilling`、`wayfinder:prototype` | HITL |
| `wayfinder:task` | 读它的正文才判得出：agent 自己做得完是 AFK，必须人动手是 HITL |

**判成 AFK**：`mmw issue claim <编号>`，回第 3 步接着解，还在同一棵 worktree 里。认领失败说明别的会话抢先了，这条链到此为止。

**判成 HITL**：**不要认领它。** 这条链到此为止，停下来交回用户。

这个会话**开工时在第 2 步认领的那张 ticket 不受本条规矩约束**，它是 HITL 还是 AFK 都由这个会话解。本条规矩管的是第 2 步那张之后的每一张。

## 6. 判断能不能提前切一份 spec 出去

不必等这张 map 收尾才切 spec。这条链走到这里，某份 spec 同时满足下面三条，就现在切出去，跟剩下的链并行做：

| 条件 | 怎么查 |
| --- | --- |
| 这份 spec 的题目已经清楚 | 说得出它交付什么，不需要等更多决定来定义它自己 |
| 它依赖的决定全部已经关掉 | 逐条在 map 的 `Decisions so far` 一节里找得到，没有一条还开着 |
| 还没说清楚的部分不会波及它 | 把 map 的 `Not yet specified` 一节逐条对一遍 |

三条齐了就现在切这一份，切法见 [closing.md](closing.md) 的「切出 spec」一节。任何一条不齐就等这张 map 收尾。

## 7. 这条链走完之后

1. 这条链写的每一份 `draft-<ticket 编号>-<kebab-标题>.md`（落点跑 `mmw domain dirs` 取 `adr` 那一行）逐个改成正式编号：`mmw domain adr-next` 取下一个号，改名，再取下一个，直到改完。编号只增不改。提交。
2. 记录链任务的分支名、`git rev-parse HEAD` 和建立链任务时的 map 基点 SHA。
3. 把分支名、HEAD SHA、基点 SHA 和链报告交回 map 任务。map 任务运行 `mmw result verify`，验证报告和 diff 后再运行 `mmw result integrate`。
4. map 任务集成后重新查询 `mmw issue frontier <map 编号>`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 5 步判出下一张归你、而且是 AFK | **自己继续**：认领它，回第 3 步接着解同一条链 |
| 第 5 步判出下一张归你、但是 HITL | **停**：不要认领它。报这条链解掉了哪几张 ticket、下一张是哪张、它为什么要人参与，让用户另开一个会话认领它 |
| 手上这张是 `wayfinder:task`，而且必须人动手 | **停**：交一份精确的操作清单——要做什么、做完之后哪些结果事实要记下来（凭证放在哪、新的地址是什么、数据有多少行）——等用户做完再回第 4 步 |
| 第 6 步判出某份 spec 三条都齐了 | **停**：报这份 spec 现在可以开始做，让用户另开一个会话走 `/mmw-to-spec` |
| 这条链走完 | **停**：交回分支名、HEAD SHA、基点 SHA、解掉的 ticket 和当前 frontier；由 map 任务验证并集成 |
| map 任务集成链结果后发现 frontier 为空 | **移交**：map 任务读取 [closing.md](closing.md) |
