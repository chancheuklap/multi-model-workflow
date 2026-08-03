# 认领一条链

用户带着一张 map 来（编号或链接）。这个会话解**一条链**：解开一张 ticket，接着解被它解锁的那张，直到不能再往下走。判断能不能往下走的规矩在第 5 步。

## 1. 在主仓库里读

还不要建任何 worktree。这一步只读：

- `gh issue view <map 编号>` 读 map 正文，不要逐个打开 ticket。
- 按需读 map 分支上的文件，例如 `git show <map 分支>:CONTEXT.md`。
- 按 `docs/agents/issue-tracker.md` 的「Wayfinding operations」一节查一次 frontier。

frontier 空了，说明这张 map 该收尾了，转 [closing.md](closing.md)。

## 2. 挑一张，认领，建这条链的 worktree

用户点了名就用他点的那张，没点就取 frontier 上的第一张。

**先认领**：把它指派给自己。指派完成之前不要做任何事。

再建这条链的 worktree，从 map 分支分叉，slug 是 `<map 的 slug>-<链首 ticket 的短语>`，建法见 `docs/agents/worktrees.md`。建完 `EnterWorktree` 进去。这是这个会话唯一一次进 worktree。

## 3. 解它

**按需放大**：随时取任何相关的、或者已经关掉的 ticket 的完整正文；把 map 的 `Notes` 一节点名的技能调起来。

四个类型各自的选用判据和 HITL / AFK 归属见 [map-anatomy.md](map-anatomy.md)，本节只写解的时候怎么做：

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
3. 这个决定难以回退、而且真有取舍，就另写一份 ADR。链上先写成 `docs/adr/draft-<ticket 编号>-<短语>.md`，等这条链走完、合回 map 分支时再统一改成正式编号。判据见 `/domain-modeling`。
4. 谈出来的新术语追加进 `CONTEXT.md`。
5. 更新 map：这次答案让哪块 fog of war 说得清楚了，就从 `Not yet specified` 一节里拿出来建成新 ticket，再连阻塞关系（先建 issue，拿到编号再连边）。
6. 这次答案要是暴露出某张 ticket 坐在 destination 之外，就判它出范围：关掉它，在 `Out of scope` 一节留一行，并在 `.out-of-scope/` 写一份。判据见 [map-anatomy.md](map-anatomy.md) 的「什么算判出范围」一节。这个决定让 map 的其他部分作废了，就更新或删掉作废的那些 ticket。

改 map 正文时**只改自己动过的那几行**，不整份重写。

## 5. 判断这条链还能不能往下走

查这次解开的这张 ticket 解锁了哪些 ticket，**逐张**按下面两关判。

**第一关，这张还归不归你。** 查两样：阻塞的 ticket 是否全部关掉了，它有没有 assignee。有一样不满足就跳过这张。一张 ticket 可能被两条链同时解锁，谁先指派上谁继续，另一条到此为止。

**第二关，这张是 HITL 还是 AFK。** 这一关在指派之前判，判法：

| 这张 ticket 的标签 | 判定 |
| --- | --- |
| `wayfinder:research` | AFK |
| `wayfinder:grilling`、`wayfinder:prototype` | HITL |
| `wayfinder:task` | 读它的正文才判得出：agent 自己做得完是 AFK，必须人动手是 HITL |

**判成 AFK**：认领它，回第 3 步接着解，还在同一棵 worktree 里。

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

1. 这条链写的每一份 `docs/adr/draft-<ticket 编号>-<短语>.md` 逐个改成正式 ADR 编号（四位、从 `0001` 起、只增不改，见 `docs/agents/domain.md`），提交。
2. 合回 map 分支。这个会话不能跳到别的 worktree，所以用 `git -C` 指过去。**`.worktrees/` 是相对主仓库的路径，而这个会话现在在链的 worktree 里，所以先把主仓库路径取出来**：

   ```bash
   MAIN=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
   MAP="$MAIN/.worktrees/<map 的 slug>"

   git -C "$MAP" status --porcelain   # 有输出就是不干净，停下来报给用户，不硬合
   git -C "$MAP" merge --no-ff <这条链的分支名>
   ```

   map 的 worktree 已经不在（用户清理过）就先建回来：`git -C "$MAIN" worktree add .worktrees/<map 的 slug> <map 分支>`。
3. 再查一次 frontier。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 5 步判出下一张归你、而且是 AFK | **自己继续**：认领它，回第 3 步接着解同一条链 |
| 第 5 步判出下一张归你、但是 HITL | **停**：不要认领它。报这条链解掉了哪几张 ticket、下一张是哪张、它为什么要人参与，让用户另开一个会话认领它 |
| 手上这张是 `wayfinder:task`，而且必须人动手 | **停**：交一份精确的操作清单——要做什么、做完之后哪些结果事实要记下来（凭证放在哪、新的地址是什么、数据有多少行）——等用户做完再回第 4 步 |
| 第 6 步判出某份 spec 三条都齐了 | **停**：报这份 spec 现在可以开始做，让用户另开一个会话走 `/mmw-to-spec` |
| 这条链走完，frontier 上还有 ticket | **停**：报这条链解掉了哪几张、frontier 上还剩哪几张（用名字，不用编号），让用户另开一个会话认领下一条 |
| 这条链走完，frontier 空了 | **自己继续**：读 [closing.md](closing.md) |
