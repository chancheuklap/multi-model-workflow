# 认领一条链

用户带着一张 map 来（编号或链接）。这个会话解**一条链**：解开一张 ticket，接着解被它解锁的那张，直到链到头。链到头就停。

## 1. 在主仓库里读

还不要建任何 worktree。这一步只读：

- `gh issue view <map 编号>` 读 map 正文，这是低分辨率视图，不要逐个打开 ticket。
- `git show <map 分支>:CONTEXT.md` 之类，按需读 map 分支上的文件。
- 按 `../../conventions/issue-tracker.md` 查一次 frontier。

frontier 空了，说明这张 map 该收口了，转 [closing.md](closing.md)。

## 2. 挑一张，认领，建这条链的 worktree

用户点了名就用那张，没点就取 frontier 上的第一张。

**先认领**：把它指派给自己。指派完成之前不要做任何事。

再建这条链的 worktree，从 map 分支分叉，slug 是 `<map 的 slug>-<链首 ticket 的短语>`，建法见 `../../conventions/worktrees.md`。建完 `EnterWorktree` 进去。这是这个会话唯一一次进 worktree。

## 3. 解它

**按需放大**：随时取任何相关的、或者已经关掉的 ticket 的完整正文；把 map 的 `Notes` 里点名的技能调起来。

按 ticket 的 `wayfinder:<类型>` 标签走：

- **`grilling`** — 要人在场。跑 `/mmw-grilling`，一次一个问题。这是默认类型。
- **`prototype`** — 要人在场。跑 `/mmw-prototype`，做一个成本低、具体的粗糙版本给用户走查。产物落 `docs/prototypes/<slug>/`，结论按那个技能的回灌规矩写成结案评论，评论里留一个指向产物的路径。关键问题是「它该长什么样」或者「它该怎么表现」时用这一类。
- **`research`** — 人不用在场。派一个子代理去查（`/mmw-dispatching-agents`），只查当前这一个决定要等的那条事实，答完就停。回执按 `/mmw-verifying-agent-output` 逐条复核，复核过的事实才写进 ticket 评论，没查清的另起一节列出来。
- **`task`** — 某个决定做得出来之前必须先完成的手工操作：注册一个服务好让它的 API 能被评判、开通权限、把数据搬过来看清它的形状。这是唯一一类做事而不是做决定的 ticket，它靠解除对某个决定的阻塞立足。agent 自己做得了就自己做完；做不了就停，见文末的下一步表。

要人在场的那三类，**agent 不许替人回答**。派一个子代理自问自答，解出来的决定不作数。

## 4. 记录这次解答

按顺序做完六件事：

1. 答案写成**结案评论**贴在这张 ticket 上，然后**关掉**它。
2. 往 map 的 `Decisions so far` 追加一行索引。**追加之前先重新拉一次最新正文**，写完再读一次确认自己那行在。
3. 这个决定难以回退、而且真有取舍，就另写一份 ADR。**并行的链之间会撞编号**，所以链上先写成 `docs/adr/draft-<ticket 编号>-<短语>.md`，等链到头合回 map 分支时统一改成正式编号。判据见 `/domain-modeling`。
4. 谈出来的新术语追加进 `CONTEXT.md`。
5. 更新 map：这次答案让哪块 fog of war 说得清楚了，就从 `Not yet specified` 里拿出来建成新 ticket，再连阻塞关系（先建后连边）。
6. 这次答案要是暴露出某张 ticket 坐在 destination 之外，就判它出范围——关掉它，在 `Out of scope` 留一行，并在 `.out-of-scope/` 写一份。判据见 [map-anatomy.md](map-anatomy.md)。这个决定让 map 的其他部分作废了，就更新或删掉那些 ticket。

改 map 正文时**只改自己动过的那几行**。另一路正在同时改它，整份重写会覆盖对方刚写进去的结论。

## 5. 这条链还有下一张吗

查这次解开的这张 ticket 解锁了谁，逐个确认两件事：阻塞是否全部清了，有没有 assignee。

两条都满足就回第 2 步的认领，接着解，**还在同一棵 worktree 里**。一张 ticket 可能被两条链同时解锁，谁先指派上谁继续，另一个就算链到头。

## 6. 这条链收尾

链到头之后：

1. 把这条链写的 `draft-<ticket 编号>-<短语>.md` 逐个改成正式 ADR 编号（四位、从 `0001` 起、只增不改，见 `../../conventions/domain.md`），提交。
2. 合回 map 分支。链会话不能跳到别的 worktree，所以用 `git -C` 指过去。**`.worktrees/` 是相对主仓库的，而你现在在链的 worktree 里，所以先把主仓库路径取出来**：

   ```bash
   MAIN=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
   MAP="$MAIN/.worktrees/<map 的 slug>"

   git -C "$MAP" status --porcelain   # 有输出就是不干净，停下来报给用户，不硬合
   git -C "$MAP" merge --no-ff <这条链的分支名>
   ```

   map 的 worktree 已经不在（用户清理过）就先建回来：`git -C "$MAIN" worktree add .worktrees/<map 的 slug> <map 分支>`。worktree 只是分支的载体，随便建。
3. 再查一次 frontier。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 5 步查到下一张，阻塞清了而且没人认领 | **自己继续**：回第 2 步认领它，接着解同一条链 |
| `task` 类 ticket，agent 自己做不了 | **停**：给一份精确的操作清单——要做什么、做完之后哪些结果事实要记下来（凭证放在哪、新的地址、数据行数）——等用户做完再回第 4 步 |
| 这条链收尾完，frontier 上还有 | **停**：报这条链做完了、frontier 上还剩哪几张，让他另开一个会话认领下一条 |
| 这条链收尾完，frontier 空了 | **自己继续**：读 [closing.md](closing.md)。收口这件事 agent 做得了，不用停 |
| 某份 spec 已经可以提前开始做 | **停**：判据在 [closing.md](closing.md) 的「提前派生」一节，三条齐了才报，报的时候说明另开一个会话去做这份 spec |
