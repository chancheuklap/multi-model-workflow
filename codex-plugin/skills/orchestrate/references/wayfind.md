# Wayfind · 探路(讨论态前缀阶段,读本文全文)

> 触发:终点大致明确、但决策空间在雾里——连"要决定什么"都还没法准确表述,单个会话装不下。两个条件**同时**成立才配进本阶段;能框成普通 investigate 问题的不进(那是 investigate 的活)。
>
> 定位:本阶段**只产决策,不产交付物、不写码**。探路探的是"怎么走到目的地",不是走。产生"已经可以动手了"的冲动 = 探路完成的信号,立刻收口交接,不在本阶段动手。

## 工件(都进 git,跨会话长寿)

- **决策地图** `docs/design/<slug>/wayfind/map.md`——**索引,不是仓库**:目的地一段、已决清单(每条一行 gist + 决策文件链接)、frontier、Not yet specified 区。地图只写 gist,细节只住决策文件,不两处重复。
- **决策文件** `docs/design/<slug>/wayfind/d-<NN>-<名字>.md`——一决策一文件:问题 / 为什么挡路 / 候选答案(带取舍)/ 结论 / 证据(`file:line` / url)。
- 汇报、进度板、地图里引用决策用**名字**带链接,不裸用编号。

## 起图(第一轮)

1. **命名目的地**:一段话写清"走到哪算到"(一份可交接的 spec?一个锁死的决策?一次就地改造?)——它塑形所有 ticket。
2. **先建全部能准确表述的决策 ticket**(编号 d-01 起);表述不清的留在 map 的 Not yet specified 区,不硬编问题。
3. **第二遍连 blocking edges**:谁挡谁,连完算 frontier(blocker 全解的集合)。

## 每轮循环(讨论态 attended,HITL)

1. 读 map(每轮只读这份索引)→ 从 frontier 领**一个**决策(一轮一个,上下文预算纪律;纯调研 ticket 可并行派)。
2. 事实归你查(内部 `rg`/read;成规模的调研读 `investigate.md` 照它的编排器跑,承重结论回引第一方来源)。**决策归用户**:用已装 `grilling` skill 一次一问、每问附推荐,与用户解开。
3. 解开即落盘:结论写进该决策文件;map 更新——已决区加一行 gist+链接、frontier 重算、Not yet specified 里因前置解开而"毕业"的转成新 ticket(编号续排,第二遍连边)。
4. `mmw note` 留一句书签(当前 frontier / 在解决策)——跨会话靠它 + map + 决策文件续跑,不靠会话记忆。

## 收口(双条件)

frontier 清空(已表述决策全解)**且**剩余 Not yet specified 经用户确认不挡路(留给 investigate 回答)→ 把结论写进 map 顶部「路径」节(一句话路径 + investigate 该回答的问题清单),handoff:

```bash
mmw handoff --conclusion pass --produced docs/design/<slug>/wayfind/
```

→ advance 到 investigate(`prev_outputs` 自动带 wayfind 目录;它拿「路径」节当投查输入,不重探已决决策)。

中途发现方向本身错了 / 用户要改目的地 → `mmw handoff --conclusion needs-redirection`(讨论态掉头不计成本);缺用户才能补的输入 → `needs-context`。

## 红线

- 只产决策:任何"顺手把活干了"的冲动都是收口信号,先交接再动手。
- map 只索引:细节进决策文件,map 不复述(防双写漂移)。
- 用户确认达成共同理解前,不把任何决策标"已决"。
