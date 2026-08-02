# map 收尾

frontier 上一张 ticket 都不剩了。收尾就是把这张 map 结束掉：清算 `Not yet specified` 一节剩下的条目、把这张 map 上做出的决定各自归位、切出 spec、关掉 map issue。

进来的方式有两种，都合法：

- **刚解完最后一条链**，这个会话还在那条链的 worktree 里。就地做，收尾写的文件跟着这条链的分支一起合回 map 分支。
- **新会话进来发现 frontier 空了**，这个会话还在主仓库。`EnterWorktree` 进 map 的 worktree 做，map 的 worktree 不在就先 `git worktree add` 建回来。

## 1. 清算 `Not yet specified` 剩下的条目

把 map 的 `Not yet specified` 一节剩下的条目原样列给用户看，问他里面还有没有会挡住后续工作的。

这一步要用户拍板：agent 判得出一个条目说不说得清楚，判不出它对用户重不重要。

用户点出会挡路的，就把它建成新的 decision ticket、连好阻塞关系，然后停——见文末的下一步表。用户没点出来的原样留在 `Not yet specified` 一节里，跟着 map issue 一起关掉。

## 2. 决定各自归位

map issue 关掉之后就不再是查阅入口，所以这张 map 上做出的决定要按类型分开落到仓库里。**去向表在 `docs/agents/issue-tracker.md` 的「`/mmw-wayfinder` 的产物不上 Wiki，但也不能死」一节，那里是唯一权威，本文不复述。**

走 map 的过程中该写的已经写了，这一步是补漏：逐条过一遍 map 的 `Decisions so far` 一节，看有没有当时判成「可回退」、现在回头看其实难以回退的。判成难以回退的补一份 ADR。

## 3. 切出 spec

map 按**决定**组织，spec 按**能独立设计和实现的一块功能**组织。这一步把已经定好的决定重新分组，看哪些凑起来是一份做得下去的东西。**只分组，不重新讨论任何决定。**

一组一份 spec，各建一张 issue 挂在 map 底下，正文写清楚两件事：这份 spec 交付什么，它依赖 map 的 `Decisions so far` 一节里的哪几条。spec issue 跟 decision ticket 同处一层，靠**带不带 `wayfinder:` 类型标签**区分：decision ticket 带，spec issue 不带。

切出来只有一份，说明当初路由判早了——一份 spec 说得完的事本该走 `/mmw-grilling` 再 `/mmw-to-spec`，不必画 map。已经发生的不用回头重来，照样把这一份切出去走下去。

走链的中途也可以提前切 spec，判据见 [walking.md](walking.md) 的「判断能不能提前切一份 spec 出去」一节。

## 4. 关掉 map

关掉 map issue。把第 1 步到第 3 步写下的文件提交进 map 分支；刚解完最后一条链的会话，随这条链的分支合回 map 分支。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步用户点出还有会挡路的条目，已经建成 decision ticket | **停**：报新建了哪几张 ticket（用名字，不用编号），让用户另开一个会话认领 |
| 决定归位完、spec 切完、map issue 关掉 | **停**：报这张 map 收尾了、切出了哪几份 spec（用名字，不用编号），说明每份 spec 各开一个会话去做 |

每份 spec 的 worktree 从 map 分支分叉，做完合回 map 分支；整个 effort 收尾时 map 分支才合回主线（见 `docs/agents/worktrees.md`）。
