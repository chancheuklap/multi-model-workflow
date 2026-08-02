---
name: wayfinder
description: 把一大块活——大到一个 agent 会话装不下——规划成 issue tracker 上一张共享的 map，上面挂 decision ticket，一次解一张，直到通往 destination 的路清楚为止。用户带着一个很大、很松、一时看不到头的想法过来，或者报出一张已有的 map 要接着往下走时用它。
---

一个还很松的想法来了——大到一个 agent 会话装不下，而且裹在雾里：从这里到 **destination** 的路还看不见。Wayfinding 干的是找到这条路，不是朝着 destination 猛冲。本技能把这条路画成仓库 issue tracker 上一张**共享的 map**，然后一次一张地解它的 **decision ticket**——那些解出来是一个决策的问题，不是一次构建里的切片——直到路线清楚。

destination 每个 effort 各不相同，给它命名是画图的第一个动作，它塑造后面每一张 ticket。它可能是一份要交出去继续迭代的 spec，可能是一个开始做计划之前必须锁死的决策，也可能是一次就地完成的改动，比如一次数据结构迁移。这张 map 与领域无关——工程活、课程内容，形状对得上就能用。

## 只做规划，不做执行

Wayfinder 默认是**规划**：每张 ticket 解掉一个决策，路清楚了这张 map 就算完——在有人真去做那件事之前，没有什么还需要决定的了。想直接动手干活的那股冲动，通常正是你已经走到 map 边界、该交棒的信号。某个 effort 可以在自己的 **Notes** 里推翻这一条，把执行也纳进 map；没写就产出决策，不产出交付物。

## 用名字称呼

每一张 map 和 ticket 都是一张 issue，所以它有一个**名字**——它的标题。凡是人要读的地方——你的叙述、map 的 Decisions so far——都用这个名字称呼它，不要用裸的 id、编号或 slug。一整墙 `#42、#43、#44` 没法读，名字扫一眼就懂。id 和 URL 不会消失——名字外面包着它的链接——但它们躺在名字*里面*，不顶替名字。

## 这张 map

map 是本仓库 issue tracker 上的一张 issue，打 `wayfinder:map` 标签——它是权威产物。它的 ticket 是这张 map 的子 issue。

map 是一份**索引**，不是一个仓库。它列出已经做出的决策，并指向持有细节的那些 ticket；一个决策只住在一个地方——它自己那张 ticket——所以 map 从不复述它，只给一句概要再链过去。

**map、它的子 ticket、阻塞关系、frontier 查询在物理上落在哪里，取决于 tracker。** issue tracker 应该已经给你了——没有就跑 `/setup`。查 tracker 那份文档的「Wayfinding operations」一节，看*本*仓库怎么表达这些东西。没有给你任何 tracker 时，退回到本地 markdown 那种 tracker。

### map 的正文

整张 map 的低分辨率视图，每个会话加载一次。open 的 ticket **不**列在这里——它们是 open 的子 issue，靠查询找出来。

```markdown
## Destination

<走到这张 map 的尽头是什么样子——这个 effort 要找到的那份 spec、那个决策或那次改动。一两行；每个会话在挑 ticket 之前都先对准它。>

## Notes

<领域；每个会话都该查阅的技能；这个 effort 的固定偏好>

## Decisions so far

<!-- 索引——每张关掉的 ticket 一行：够判断相关性就行，要细节再顺着链接放大到那张 ticket -->

- [<关掉的 ticket 标题>](链接) —— <答案的一句话概要>

## Not yet specified

<!-- 见「Fog of war」：范围内、但还开不出 ticket 的雾；frontier 推进时它会毕业 -->

## Out of scope

<!-- 见「Out of scope」：被判在 destination 之外的活；关掉，永不毕业 -->
```

### Ticket

每张 ticket 是这张 map 的一个**子 issue**；tracker 给的 issue id 就是它的身份。它的正文是那个问题，大小按一个 100K token 的 agent 会话来裁：

```markdown
## Question

<这张 ticket 要解掉的决策或调查>
```

每张 ticket 带一个 `wayfinder:<type>` 标签，取值是 `research`、`prototype`、`grilling`、`task` 之一（见「Ticket 类型」一节）。

一个会话通过把 ticket 指派给驱动这张 map 的开发者来 **claim** 它，而且是**在做任何事情之前先指派**，这样并发的会话会跳过它。那个 assignee *就是* claim：一张 open 且没有 assignee 的 ticket 就是没被 claim 的。

阻塞用 tracker 的**原生**依赖关系——这一点很要紧，因为它能在 tracker 自己的界面里*可视地*把 frontier 呈现出来，人不用打开 map 就看得见哪些能拿。只有在 tracker 缺原生阻塞时才退回到正文里写约定。一张 ticket 的**阻塞解除**，是指所有阻塞它的 ticket 都关掉了；**frontier** 是那些 open、无阻塞、未被 claim 的子 issue——已知区域的边缘。

答案不属于正文——它在解掉的时候记录（见「走过这张 map」一节）。解 ticket 过程中产出的资产从 issue 链过去，不粘进正文。

## Ticket 类型

每张 ticket 要么是 **HITL**——人在环里，和一个能替自己说话的人一起做；要么是 **AFK**，由 agent 独自驱动。HITL 的 ticket 只能通过那场实时交流解掉，agent 绝不替人说他那一半（一个自问自答的 grilling agent 就破了这条）。

- **Research**（AFK）：读文档、第三方 API，或者知识库这类本地资源，把某个决策在等的一条事实挖出来。由一个 `/research` **subagent** 解掉。当前工作目录之外的知识才用得上它。
- **Prototype**（HITL）：做一个便宜、粗糙、具体的东西让人有得可反应，把讨论的保真度抬上去——一份提纲、一个粗版本、一个桩，或者用 `/prototype` 技能写出界面／逻辑代码。把这个原型作为资产链到 issue 上。「它该长什么样」或者「它该怎么表现」是关键问题时用它。
- **Grilling**（HITL）：用 `/grilling` 和 `/domain-modeling` 对谈，一次一个问题。这是默认情形。
- **Task**（HITL 或 AFK）：某个*决策*做得出来之前必须先发生的手工活——没有什么要决定、要做原型或要调研的，但讨论被它挡着。注册一个服务好让它的 API 能被评判、开通权限、把数据搬过来好看清它的形状。这是唯一一类*做事*而不是*决策*的 ticket——它凭解除对某个决策的阻塞立足，不是凭交付 destination。agent 能自己干就自己干（AFK）；干不了就交给人一份精确的清单（HITL）。活干完就算解掉；答案里记下干了什么，以及后面 ticket 要依赖的那些结果事实（凭证放在哪、新的 URL、行数）。

## Fog of war

这张 map 是*刻意*不完整的：看不见的东西就别画。live 的 ticket 之外是 **fog of war**——那些你看得出要来、但还钉不住的决策和调查，因为它们悬在还没解开的问题上。解掉一张 ticket 会驱散它前面的雾，把此刻能说清楚的部分毕业成新的 ticket——一次一张，直到通往 destination 的路清楚、一张 ticket 都不剩。

map 的 **Not yet specified** 一节就是写下那片朦胧视野的地方：怀疑存在的那个问题，以后要回来看的那块地方。它是*朝着* destination 的、还没被发现的 frontier——这里的东西全在范围内，只是还不够锐、开不出 ticket。视野允许写多细就写多细；它同时也是给协作者看的路标，让人知道这个 effort 往哪去。

**是雾还是 ticket？** 判据是你此刻能不能把问题*精确地陈述出来*，*不是*你此刻能不能回答它。

- **开 ticket**：问题已经很锐了——哪怕它被阻塞着、你现在动不了。
- **写进 Not yet specified**：你还没法把它说得那么锐。不要提前把雾切成 ticket 大小的块：它比一张 ticket 粗，等 frontier 走到那里，一块雾可能毕业成好几张 ticket，也可能一张都不是。

**Not yet specified** 里不放已经决定的（在 Decisions so far）、已经是 live ticket 的、以及范围外的（下一节）。

## Out of scope

雾只会*朝着* destination 聚集。destination 定住了范围，所以它之外的活是 **out of scope**——那不是雾，也不属于 **Not yet specified**。它有自己的 **Out of scope** 一节：你有意识地判在*这个* effort 之外的活。落到这里靠的是范围，不是清晰度。

范围外的活永不毕业——frontier 到 destination 就停了——所以它只有在 destination 被重画时才回来，而且是作为一个新的 effort，不是接着做。

判一件事出范围是一个划范围的动作，不是路线上的一步。已经存在的一张 ticket 后来发现坐在 destination 之外——画图时圈错了，或者被某次解答暴露出来——就**关掉它**（关掉的 ticket 明确不在 frontier 上），并在 **Out of scope** 一节留一行：概要加上为什么出范围，链到那张关掉的 ticket。它不进 **Decisions so far**，那里记的是真正走过的路线，而一条范围边界不是路线上的一步。

## 怎么被叫起来

两种模式。无论哪种，**一个会话解掉的 ticket 绝不超过一张**——research ticket 除外。

### 画这张 map

用户带着一个还很松的想法来。

1. **给 destination 命名。** 跑一场 `/grilling` 加 `/domain-modeling`，把这张 map 要找的东西钉死——那份 spec、那个决策或那次改动。destination 定住范围，所以它第一个定下来。
2. **画出 frontier。** 再 grill 一次，这次**广度优先**：在整个空间上铺开，而不是在某一条线上扎深，把还开着的决策和现在就能迈的第一步捞出来。**如果这一步没捞出任何雾**——通往 destination 的路已经清楚了，整趟路程一个会话就装得下——那你不需要 map。停下来问用户想怎么走。
3. **建这张 map**（打 `wayfinder:map` 标签）：Destination 和 Notes 填好，Decisions so far 留空，把雾勾进 **Not yet specified**。
4. **把现在就能说清楚的 ticket 建成 map 的子 issue**——然后用**第二遍**把阻塞边连上（issue 得先有 id 才能互相引用）。连边把它们分成 frontier 和被阻塞的两拨；还说不清楚的全部留在雾里，也就是 **Not yet specified** 一节。
5. **把 research subagent 放出去。** 刚建的每一张 `research` ticket，各起一个 `/research` subagent 并行去解，findings 捕获在一个一次性的 `research/<name>` 分支上，从 ticket 留一个 context pointer 指过去。
6. 停——画图是一个会话的活，它一张都不亲手解。

### 走过这张 map

用户带着一张 map 来（URL 或编号）。ticket 是**可选的**——没给的话，挑下一个决策的是你，不是用户。

1. 加载这张 **map**——低分辨率视图，不是每张 ticket 的正文。
2. 挑 ticket。用户点了名就用那张；没点就按顺序取 frontier 上的第一张。**claim 它**：做任何事之前先指派给自己。
3. 解它——**按需放大**：随时按需取任何相关的或已关掉的 ticket 的完整正文；把 `## Notes` 里点名的技能调起来。拿不准就用 `/grilling` 和 `/domain-modeling`。
4. 记录解答：把答案作为一条**结案评论**贴上去，**关掉**这张 issue，再往 map 的 Decisions so far **追加一个 context pointer**。
5. 把新冒出来的 ticket 加进去（先建后连边）；这次答案让哪些雾能说清楚了就让它毕业，并把毕业掉的那块从 **Not yet specified** 里清掉，让它只以新 ticket 的形式存在。答案要是揭示出某张 ticket——这张或别张——坐在 destination 之外，就**判它出范围**，而不是在路线上把它解掉。这个决策让 map 的其他部分作废了，就更新或删掉那些 ticket。

用户可能会把没被阻塞的 ticket 并行跑起来，所以要预期有别的会话正在同时改 tracker。
