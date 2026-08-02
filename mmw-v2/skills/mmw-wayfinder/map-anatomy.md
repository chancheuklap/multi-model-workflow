# map 和 ticket 长什么样

**map、它的子 ticket、阻塞关系、frontier 查询在本仓库怎么表达，看 `docs/agents/issue-tracker.md` 的「Wayfinding operations」一节。** 那份文档不在就跑 `/mmw-setup`。下面写的是形状，不是命令。

## map

map 是 issue tracker 上的一张 issue，打 `wayfinder:map` 标签，它是权威产物。它的 ticket 是这张 map 的子 issue。

map 是一份**索引**，不是一个仓库。它列出已经做出的决定，并指向持有细节的那些 ticket。一个决定只住在一个地方——它自己那张 ticket 的结案评论——所以 map 从不复述它，只给一句概要再链过去。

正文是整张 map 的低分辨率视图，开工前加载一次。还开着的 ticket **不**列在这里，它们是 open 的子 issue，靠查询找出来。

```markdown
## Destination

<走到这张 map 的尽头是什么样子——这个 effort 要找到的那份 spec、那个决定或那次改动。一两行；挑任何一张 ticket 之前先对准它。>

## Notes

<领域；每次接手都该查阅的技能；这个 effort 的固定偏好>

## Decisions so far

<!-- 索引。每张关掉的 ticket 一行，够判断相关性就行；要细节就顺着链接放大到那张 ticket -->

- [<关掉的 ticket 标题>](链接) —— <答案的一句话概要>

## Not yet specified

<!-- 范围内、但还开不出 ticket 的 fog of war。判据见下面「fog of war 还是 ticket」 -->

## Out of scope

<!-- 判在 destination 之外的工作。关掉，不再回来。判据见下面「什么算判出范围」 -->
```

## ticket

每张 ticket 是这张 map 的一个**子 issue**，tracker 给的编号就是它的身份。正文是那个问题，**一张 ticket 只解一个决定**——解出两个决定的是两张 ticket：

```markdown
## Question

<这张 ticket 要解掉的决定或调查>
```

每张 ticket 带一个 `wayfinder:<类型>` 标签，四个取值：`grilling`、`prototype`、`research`、`task`。四类各自怎么解，见 [walking.md](walking.md)。

答案不写进正文，它在解掉的时候作为结案评论记录。解 ticket 过程中产出的东西从 issue 链过去，不粘进正文。

## 认领

把 ticket 指派给自己就是**认领**。open 且没有 assignee 的 ticket，就是还没人认领的。**指派完成之前不要做任何事**，并行的另一路才会跳过它。

## 阻塞与 frontier

阻塞用 tracker 的**原生**依赖关系。这一点重要：原生依赖能在 tracker 自己的界面里直接看出哪些 ticket 可以取，人不用打开 map。只有 tracker 没有原生依赖时才退回到正文里写约定。

一张 ticket 的**阻塞解除**，是指所有阻塞它的 ticket 都已关掉。**frontier** 是那些 open、无阻塞、还没人认领的子 issue，也就是已知区域的边缘。

## fog of war 还是 ticket

这张 map 是**刻意**不完整的：看不见的东西不要画。还开着的 ticket 之外是 **fog of war**——那些你看得出要来、但还钉不住的决定和调查，因为它们悬在还没解开的问题上。解掉一张 ticket 会驱散它前面的 fog of war，此刻能说清楚的部分就从 `Not yet specified` 里拿出来，建成新的 ticket。

判据是你此刻能不能把问题**精确地陈述出来**，不是你此刻能不能回答它。

- **建成 ticket**：问题已经很锐了，哪怕它被阻塞着、你现在动不了。
- **写进 `Not yet specified`**：你还没法把它说得这么锐。不要提前把 fog of war 切成 ticket 大小的块——它比一张 ticket 粗，等 frontier 走到那里，一块 fog of war 可能变成好几张 ticket，也可能一张都不是。

`Not yet specified` 一节写的就是这片模糊视野：怀疑存在的那个问题，以后要回来看的那块地方。它同时是给协作者看的路标，让人知道这个 effort 往哪里去。已经决定的（在 `Decisions so far`）、已经是 ticket 的、以及范围外的都不放这里。

## 什么算判出范围

fog of war 只会**朝着** destination 聚集。destination 固定了范围，所以它之外的工作是**判出范围**的——那不是 fog of war，也不属于 `Not yet specified`，它有自己的 `Out of scope` 一节。落到这里靠的是范围，不是清晰度。

判出范围的工作不再回来。frontier 走到 destination 就停了，它只有在 destination 被重画时才回来，而且是作为一个新的 effort，不是接着做。

判一件事出范围是一个划范围的动作，不是路线上的一步。已经存在的一张 ticket 后来发现坐在 destination 之外——画图时圈错了，或者被某次解答暴露出来——就**关掉它**，并在 `Out of scope` 一节留一行：概要加上为什么出范围，链到那张关掉的 ticket。同时按 `docs/agents/issue-tracker.md` 的产物分流表在 `.out-of-scope/` 写一份，一个概念一个文件。

它不进 `Decisions so far`。那里记的是真正走过的路线，一条范围边界不是路线上的一步。
