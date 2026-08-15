# map 收尾

这张 map 已经没有 open 的 decision ticket 了，本文件负责收尾。

收尾在拥有 map 分支的会话里做。先运行 `git rev-parse --abbrev-ref HEAD`，跟 map 正文 `## 分支` 一节记的分支名比对，确认当前就在 map 分支上；不在就报告这一点并停止，让拥有 map 分支的会话来收尾。

重新读取 map 正文，再运行 `mmw issue children <map 编号>`。仍有带 `wayfinder:` 标签的 open decision ticket 时停止；map 保持 open，不执行收尾。

再确认每张已关闭 decision ticket 的结果都已经集成回 map 分支，而且没有遗留 `draft-<ticket 编号>-<slug>.md`。存在未集成的结果分支或 ADR 草稿时，先按 [walking.md](walking.md) 第 7 节完成集成和正式编号，再继续收尾；集成需要的任务分支名、HEAD SHA 和基点 SHA，从以 `<!-- mmw:handback -->` 开头的评论的 `## 交回` 取得。

## 1. 判断路线是否真的清楚

读取 Not yet specified 中的剩余内容，逐项应用 [SKILL.md](SKILL.md) 的“Fog of war”一节判据：

- 现在已经说得清楚了，而且它仍在通往 destination 的路上：按 [charting.md](charting.md) 第 4 步的两遍做法建成新的 decision ticket。
- 现在看清楚了，它越过了 destination：移进 `Out of scope`。已经有对应 ticket 的，按 [SKILL.md](SKILL.md) 的“Out of scope”一节关掉它并留下链接。
- 现在还是说不清楚，而且它仍在通往 destination 的路上：这张 map 还没做完。按 [charting.md](charting.md) 第 2 步的广度优先方式，对剩下这些再 grill 一次。谈完能说清楚的按第一项建 ticket，谈完发现越界的按第二项移走。谈完还是说不清楚的留在 `Not yet specified`，报告这一块是什么、现在缺哪些信息，然后停止。

完成全部分类后，按下表处理：

| 分类结果 | 处理 |
| --- | --- |
| 建立了新的 decision ticket | 运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`，报告新 ticket 和当前 frontier，然后停止；map 保持 open，不执行第 2、3 步 |
| 仍有通往 destination 的 fog | 报告仍无法形成 ticket 的 fog，然后停止；map 保持 open，不执行第 2、3 步 |
| 通往 destination 的路线已经清楚，而且没有尚待解决的 decision ticket | 继续第 2 步 |

## 2. 关闭 map

通往 destination 的路线已经清楚，而且没有尚待解决的 decision ticket 时，关闭 map issue：

```bash
gh issue close <map 编号>
```

## 3. 按 destination 移交

读 map 正文的 `Destination` 一节，按它写的是哪一种来处理。你只把 map 交出去，不替下一个技能先把它的输入准备好。

| `Destination` 写的是 | 处理 |
| --- | --- |
| 一份 spec | 交给 `/mmw-to-spec` 两样东西：map 名称和它的 URL 或编号，以及 map 正文 `## 分支` 的 slug（产物名字段）。一张 map 只出一份 spec。剩下的由 `/mmw-to-spec` 自己去读：它顺着 `Decisions so far` 进各张 decision ticket，再按 ticket 评论里的产物引用取 prototype 和 research。你不要先建一张 spec issue，也不要把内容复制一份给它 |
| 开始规划前必须锁定的一个决定 | 报告这个决定现在是什么，并给出 map 名称和它的 URL 或编号 |
| 一次就地完成的改动，而且 map 的 `Notes` 里写了这项 effort 要把执行也带进 map | 报告 map 已完成 |
| 一次就地完成的改动，而且 map 的 `Notes` 里没写这一条 | 报告路线已经清楚、但改动还没做，并给出 map 名称和它的 URL 或编号 |
| 以上都对不上 | 报告 `Destination` 原文和你无法归类的原因，请用户裁决交给谁 |

除了 spec 那一种，其余几种到这里 Wayfinding 就结束了：把已经形成的决定交出去，不要接着去把 destination 做掉。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| destination 是一份 spec，map 已关闭 | **移交**：`/mmw-to-spec`，交给它 map 名称及其 URL 或编号，以及 map 分支的 slug |
| destination 是已经锁定的决定，map 已关闭 | **停**：报告决定和 map 名称及其 URL 或编号 |
| destination 是已经完成的就地改动，map 已关闭 | **停**：报告 map 已完成 |
| destination 是尚未执行的就地改动，map 已关闭 | **停**：报告路线已经清楚、改动尚未执行，以及 map 名称及其 URL 或编号 |
| `Destination` 写的内容归不进上面任何一种 | **停**：报告 `Destination` 原文和无法归类的原因，请用户裁决 |
