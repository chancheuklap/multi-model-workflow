---
date: 2026-08-11
amends: []
---

# decision ticket 自己声明必读材料，wayfinder 交接按它传

一张 decision ticket 解开之后产生的结论，没有任何一步会送到后面那张 ticket 手里：`mmw/skills-src/mmw-wayfinder/charting.md` 第 4 步规定 ticket 正文「只写 `Question`」，`walking.md:46-51` 的四行交接表里 `wayfinder:grilling` 一行只有「调用」两个字。现在改为：decision ticket 正文增加**必读材料声明**一节，建 ticket 的会话写当时已知的，认领它的会话在开工前补进 blocker 关闭后新产生的材料；wayfinder 交接的四行一律把这一节的产物引用传给下游技能。理由是「这张 ticket 该读哪几节」是写的人的判断，从 map 上算不出来。

## Considered Options

- **每次现算，不写在 ticket 上。** 否决。从 map 的 `Decisions so far` 与已关闭 ticket 现算，只能算出「这项 effort 里所有已关闭的 ticket」，得到的正是 map #18 Notes 里那句「先读这两份 research」——本决定的起因就是它失效。`docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/README.md` 的「下游怎么用」能点名到「第 1、2、3、4 节」，说明这项判断存在且算不出来。
- **建 ticket 时一次写死，之后不补。** 否决。`charting.md` 是第 4 步建 ticket、第 5 步才跑 research，`#21` 到 `#26` 建立时 `#19` 与 `#20` 都还没有结论，一次写死必然是空的。
- **只修 `wayfinder:grilling` 一行。** 否决。`docs/research/mmw-artifact-wiring/issue-30/aidlc-decision-audit/report.md` 第 3 节查实，被 research 索引点过名而没用上的是 `#21` 与 `#26` 两张；prototype 与 research 两行同样不传已有结论。
- **靠机械校验发现「必读材料没被用上」。** 否决。机器判得出那一节在不在，判不出材料有没有真的被使用。判据是结论评论的**材料使用记录**这一节写出来了，与 `0007-mechanical-check-boundary.md` 的边界一致。

## Consequences

- ticket 正文规则从「只写 `Question`」改成两节。`charting.md` 第 4 步、`walking.md` 第 5 步和 `mmw-wayfinder/SKILL.md` 的 ticket 模板三处跟着改。
- `walking.md` 第 2 步 claim 之后多一步「补全必读材料声明」。解 ticket 的会话因此要写 ticket 正文，并发写面从「只有建 map 的会话改 map 正文」扩大到「认领者改自己那张 ticket」。
- 声明里两类条目：仓库产物写产物引用（`0006-artifact-reference.md`），tracker 产物写 issue 编号——结论评论落在 tracker，不占仓库路径。
- 结论评论增加**材料使用记录**一节，逐条写每项材料用上了没有、没用上的理由。map #18 Notes 里那条「必须写与 aidlc 的对照」的约束是这一节的特例。
- 范围段 `issue-<编号>` 改由调用方传。`mmw/skills-src/mmw-grilling/SKILL.md:62` 那条「解决 Wayfinder 的 decision ticket 时用 `issue-<编号>`」的自定规则删掉：范围段只有 decision ticket 有（`docs/context/artifact-location.md`），下游判断不了自己的调用来源。
- `/mmw-grilling` 的「取得事实」一节增加一步：提问前先看被点名的材料里是不是已经有答案。按 `.agents/skills/upstream-skill-fidelity/SKILL.md` 第 4 节六分类，这一步归 MMW 接线，不是语义漂移——上游原句是 `"don't ask the user for anything you could look up yourself"`，先看已有材料是这条要求的更省的执行方式。
- 被点名的材料不存在时区分两种：生产它的 ticket 按设计没跑、或用户当时选择不保存 research，属于预期缺失，继续；声明了、生产方也跑过、却找不到，停下问用户，不编造内容。

## 与 aidlc-workflows v2 的对照

出处是 `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md`。

- **照搬第 5 节的三步。** aidlc 是上游 `produces[]` 声明名字、下游 `consumes[]` 声明同一个名字、引擎解析成实际路径。MMW 只有第一步的一个变体——research 索引的「下游怎么用」（`mmw/skills-src/mmw-research/MAIN.md:106` 规定必须写），而且方向相反，是上游点名下游。本决定补上第二步；第三步由下游自己跑 `mmw artifact path`，理由沿用 `0005-artifact-path-command.md`：MMW 没有引擎层。
- **照搬第 9 节的缺失分类**，含 `"filtered to artifacts that exist on disk"` 的过滤理由——不对被跳过的上游产生必然失败的检查。
- **在 written 与 computed 之间与 aidlc 取同一侧。** aidlc 的名称注册表是 `"The registry is computed, not written."`（第 8 节），而 `consumes[]` 是写死在阶段 frontmatter 里的声明。本决定同样把声明写下来：注册表可以从声明派生，声明本身派生不出来。
- **两段式补全是 aidlc 没有的问题。** 它的阶段图预先固定，产物在阶段定义时就已知；MMW 的 map 是 fog 逐步驱散出来的，建 ticket 时上游还没跑。
- **材料使用记录是 aidlc 没有的机制。** 它的执行者是引擎驱动的阶段，读哪些上游由 `directive.consumes` 决定，不存在「人没读」这条路径；MMW 的 decision ticket 由人和 agent 一起解，必须有痕迹才知道漏没漏。
- **不照搬第 7 节。** aidlc 的 conductor 只拿引擎已解析好的路径，自己不解析。理由沿用 `0006-artifact-reference.md`：MMW 没有那个进程。
