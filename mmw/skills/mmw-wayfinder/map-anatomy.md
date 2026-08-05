# map 和 ticket 长什么样

`wayfinder:map` 这个标签既不是状态也不是类型，只是「这张 issue 是一张 map」的记号。阻塞关系用 GitHub 原生 issue dependencies，加边命令 `mmw issue link <被挡的> --blocked-by <挡它的>`，UI 里看得见。

**收尾时切出来的 spec issue 同样挂在 map 底下，但不带任何 `wayfinder:` 标签。** 这就是区分办法：带 `wayfinder:<类型>` 的是 decision ticket，不带的是 spec。

## map

map 是 issue tracker 上的一张 issue，打 `wayfinder:map` 标签。它是这项 effort 的唯一索引。map 的 ticket 是这张 map 的子 issue。

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

<!-- 范围内、但还开不出 ticket 的 fog of war。判据见本文「fog of war 还是 ticket」一节 -->

## Out of scope

<!-- 判在 destination 之外的工作。关掉，不再回来。判据见本文「什么算判出范围」一节 -->
```

## ticket

每张 ticket 是这张 map 的一个**子 issue**，tracker 给的编号就是它的身份。正文是那个问题，**一张 ticket 只解一个决定**——解出两个决定的是两张 ticket：

```markdown
## Question

<这张 ticket 要解掉的决定或调查>
```

答案不写进正文，它在解掉的时候作为结案评论记录。解 ticket 过程中产出的东西从 issue 链过去，不粘进正文。

## 每张 ticket 的两条属性

建 ticket 的时候把两条属性一起定下来：

1. **它是 HITL 还是 AFK**——这件活要不要人在对话里参与才做得完。一件活只分这两种：

   | 词 | 展开 | 含义 | 判据 |
   | --- | --- | --- | --- |
   | **HITL** | human in the loop | 必须有人在对话里一来一回才做得完 | 少了那个人的回答，这件事根本没有答案 |
   | **AFK** | away from keyboard | agent 自己就能做完，人不在也跑得动 | 人回来只需要看结果，不需要中途参与 |

   这两个词成对使用，不另写中文说法——拆开翻译就散了。

   这条轴跟**人工审批关卡**不是一回事：人工审批关卡要求用户批准指定产物或动作之后才允许流程转换；HITL 说的是这件活本身需要人参与。一件 AFK 的活照样可能撞上人工审批关卡。

2. **它是哪一个类型**——写成 `wayfinder:<类型>` 标签，四个取值见本文「四个类型」一节。

HITL 还是 AFK 不单独打标签，从类型推出来；只有 `wayfinder:task` 例外。

**HITL 的 ticket 不许 agent 替那个人回答。** 派一个 subagent 自问自答、或者主 agent 自己替用户把问题答掉，这张 ticket 解出来的决定不作数。

## 四个类型

| 标签 | HITL 还是 AFK | 什么时候打这个标签 | 谁来解 |
| --- | --- | --- | --- |
| `wayfinder:grilling` | HITL | 默认。另外三个标签都不适用就打它 | 主 agent 跑 `/mmw-grilling`，一次问用户一个问题 |
| `wayfinder:prototype` | HITL | 关键问题是「它该长什么样」或者「它该怎么表现」——光靠说定不下来，要有一个能上手的东西摆在面前才评得动 | 主 agent 跑 `/mmw-prototype` 做一个粗糙版本，用户走查 |
| `wayfinder:research` | AFK | **要用的知识在当前工作目录之外**：第三方文档、外部接口、本地知识库。仓库里读得到的不打这个标签 | 主 agent 按 `/mmw-research` 派一个 subagent 去查。一项决定被实测结果阻塞，而且实测需要 test plan、多候选对比、多轮测量、真实凭证或真实环境时，转 `/mmw-prototype` 的 `EVIDENCE.md`。受控实测遵守 `EVIDENCE.md` 第 3 步的实测人工审批关卡 |
| `wayfinder:task` | 两种都可能 | 某个决定做得出来之前必须先完成的具体操作：注册一个服务好让它的接口能被评判、开通权限、把数据搬过来看清它的形状。这是四类里唯一做事而不做决定的，它靠解除对某个决定的阻塞立足 | agent 自己做得完的是 AFK，agent 自己做；必须人动手的（要账号、要付钱、要点鼠标）是 HITL，agent 交一份精确的操作清单给用户 |

**`wayfinder:task` 的 HITL 还是 AFK 从标签上看不出来，必须读这张 ticket 的正文才判得出。** 认领它之前先读正文。

## 认领

把 ticket 指派给自己就是**认领**，命令是 `mmw issue claim <编号>`。open 且没有 assignee 的 ticket，就是还没人认领的。**认领成功之前不要做任何事**，并行的另一个会话才会跳过它。认领失败说明已经被别人占住，取下一张。

## 阻塞与 frontier

阻塞用 tracker 的**原生**依赖关系。只有 tracker 没有原生依赖时才退回到正文里写约定。

一张 ticket 的**阻塞解除**，是指所有阻塞它的 ticket 都已关掉。**frontier** 是那些 open、无阻塞、还没人认领的子 issue，也就是已知区域的边缘，用 `mmw issue frontier <map 编号>` 取，一行一张，按编号升序。

## fog of war 还是 ticket

这张 map 是**刻意**不完整的：看不见的东西不要画。还开着的 ticket 之外是 **fog of war**——那些你看得出要来、但还钉不住的决定和调查，因为它们悬在还没解开的问题上。解掉一张 ticket 会驱散它前面的 fog of war，此刻能说清楚的部分就从 `Not yet specified` 里拿出来，建成新的 ticket。

判据是你此刻能不能把问题**精确地陈述出来**，不是你此刻能不能回答它。

- **建成 ticket**：问题已经很锐了，哪怕它被阻塞着、你现在动不了。
- **写进 `Not yet specified`**：你还没法把它说得这么锐。不要提前把 fog of war 切成 ticket 大小的块——它比一张 ticket 粗，等 frontier 走到那里，一块 fog of war 可能变成好几张 ticket，也可能一张都不是。

`Not yet specified` 一节写的就是这片模糊视野：怀疑存在的那个问题，以后要回来看的那块地方。已经决定的（在 `Decisions so far`）、已经是 ticket 的、以及范围外的都不放这里。

## 什么算判出范围

fog of war 只会**朝着** destination 聚集。destination 固定了范围，所以它之外的工作是**判出范围**的——那不是 fog of war，也不属于 `Not yet specified`，它有自己的 `Out of scope` 一节。落到这里靠的是范围，不是清晰度。

判出范围的工作不再回来。frontier 走到 destination 就停了，它只有在 destination 被重画时才回来，而且是作为一个新的 effort，不是接着做。

已经存在的一张 ticket 后来发现坐在 destination 之外——画图时圈错了，或者被某次解答暴露出来——就**关掉它**，并在 `Out of scope` 一节留一行：概要加上为什么出范围，链到那张关掉的 ticket。同时在 `.out-of-scope/` 写一份，一个概念一个文件——产物去向表在 [closing.md](closing.md) 第 2 步。

它不进 `Decisions so far`，那里只记真正走过的路线。
