---
date: 2026-08-11
amends: []
---

# research 索引的章节指引只指路，不限定读取范围

`mmw/skills-src/mmw-research/MAIN.md:106` 规定 research 索引必写「下游怎么用」，写法是由写 research 的一方点名哪几张 decision ticket 该读哪几节。`0010-ticket-consumption-declaration.md` 定的必读材料声明方向相反：decision ticket 自己声明要读哪几件产物。两条同时存在。现在改为：两条并存，各管一层——必读材料声明是产物级合同，章节指引是 research 报告内部的地图；章节指引不再点名 decision ticket 编号，也不再限定读哪几节，两边不一致时以必读材料声明为准。理由是它们回答的不是同一个问题：一个是「读哪几件产物」，一个是「这件产物里哪几节讲什么」。

## Considered Options

- **只留必读材料声明，删掉章节指引。** 否决。research 报告是长文档，`docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md` 有十二节；必读材料声明只写到产物级，删掉章节这一层之后读的人要自己在十二节里翻。而且必读材料声明是人写的，漏写时没有任何机制发现——`0006-artifact-reference.md` 对同类漏写的兜底是「由 ① spec 审和 ② plan 审发现」，decision ticket 没有这两道审。章节指引写在产物那一侧，agent 打开报告就看得到，是漏写时唯一还能兜住它的东西。
- **保持章节指引原样，继续点名 decision ticket 编号并限定读哪几节。** 否决。它当合同用时会裁剪视野，而且已经发生过：`issue-20` 的 research 索引给 `#21` 点名「第 1、2、3、4 节」，`#21` 因此没有读第 8 节 `"The registry is computed, not written."`；`#27` 与 `#23` 随后各自决定把索引写成仓库文件，直到 `#30` 对照复核才发现，再开 `#31` 去解。它还只能点到写下它那一刻已经存在的 ticket——`issue-20` 写下时 `#30` 到 `#35` 都不存在，而 `#30` 用了那份报告的十二节。
- **prototype 的 `README.md` 也加章节指引。** 否决。两者形态不同：research 索引是摘要，正文在 `report.md` 里；prototype 的 `README.md` 本身就是索引，它列变体 key、页面 URL、目录和接线文件与资产的对应关系（`mmw/skills-src/mmw-prototype/UI.md:30,40,61`），而且 `UI.md:7` 已经在用点名机制。再加一节是把同一件事写两遍。
- **改「点名」的定义，让它同时覆盖产物级和章节级。** 否决。`docs/context/delivery-workflow.md` 的「点名」明写「写下一条**产物引用**」，粒度就是产物级，定义本身没有歧义。歧义来自章节那一节没有自己的名字。给它一个 canonical 名字之后冲突消失，「点名」不动。

## Consequences

- `docs/context/delivery-workflow.md` 增加 canonical 术语**章节指引**，`_Avoid_` 收掉「下游用途」「下游怎么用」「点名」三种旧说法；「research 索引」的定义里「下游用途」改为「章节指引」。「点名」的定义不变。
- `mmw/skills-src/mmw-research/MAIN.md:106` 的「下游怎么用」改写成章节指引：逐节说明各节讲什么，不写 decision ticket 编号，不写「只该读哪几节」。
- prototype 的 `README.md` 不增加这一节。这条规则只管 research 索引。
- 必读材料声明的补全那一步跑一条命令取清单，列出这项 effort 名下已保存的 research、prototype 和已关闭 decision ticket 的结论评论，认领者从清单里挑，不凭记忆。清单当场算出，形态与 `0008-computed-index.md` 一致。判断「这张 ticket 要读哪几份」仍然是人和 agent 的判断，机器不碰。
- 章节指引不再点名 ticket 编号，因此不再依赖「写 research 时下游 ticket 已经建好」这个时序。`mmw/skills-src/mmw-wayfinder/charting.md` 第 4 步建 ticket、第 5 步跑 research 的顺序与本决定无关了。
- 命令的名字与参数、章节指引的书写格式、`MAIN.md:106` 的确切措辞留给 spec 阶段。

## 与 aidlc-workflows v2 的对照

出处是 `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md`。

- **方向与 aidlc 一致。** aidlc 没有上游点名下游这一层：上游只在 `produces[]` 声明自己产出什么名字（第 1 节），谁要读由下游在 `consumes[]` 自己声明（第 5 节）。本决定把合同地位交给 ticket 侧的必读材料声明，与它同向。
- **章节这一层是 aidlc 没有的问题。** 它的产物落点是 `<record>/<phase>/<producer-stage>/<canonical-name>.md`（第 4 节），一个 canonical name 对一个文件，文件内部不再分节；MMW 的 research 报告是十二节的长文档，所以有 aidlc 不存在的内部导航需求。这一层本决定自己定，不照搬。
- **在 written 与 computed 之间取声明这一侧。** aidlc 的名称注册表是 `"The registry is computed, not written."`（第 8 节），而 `consumes[]` 是写死在阶段 frontmatter 里的。章节指引与必读材料声明同样都是写下来的声明：注册表可以从声明派生，声明本身派生不出来。补全那一步用的清单则是 computed 的那一侧。

来源：Wayfinder decision ticket #34「research 索引的「下游怎么用」与 ticket 自己声明必读材料，两条方向留哪一条」，map #18「MMW 产物归纳与接线合同」。
