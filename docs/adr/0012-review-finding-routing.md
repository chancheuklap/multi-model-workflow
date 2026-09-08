---
date: 2026-09-08
amends: []
---

# 一条 out-of-ticket 的 review finding 什么时候值一张票：按四步门槛路由，先匹配者胜，默认自己改

`code-review` 的三个 axis 在每张票的 diff 上产出 **review finding**；其中 **out-of-ticket** 的那些由 worker 开成 review 子票。2026-09-07 到 09-08 的 #216 那一夜是一次完整的实测：

| 代 | 派出的票 | 产出的 review 子票 | 每票 |
| --- | --- | --- | --- |
| 1 | 7（#217–#223） | 21（#224–#244） | 3.0 |
| 2 | 4（#254–#257） | 12（#258–#269） | 3.0 |
| 3 | 2（#270、#271） | 5（#272–#276） | 2.5 |
| 4 | 0 | 0 | — |

**每票约 3 张，三代几乎不变。**数量下降不是缺陷被找完，是每一轮派的票更少。这个循环不会自己停，只在有人停止投喂时停。那 38 张子票里，**27 张（71%）的修复目标完全落在它自己那张票的 `## Owns` 之内**。

分拣规则把 `## Owns` 收进 in-ticket 之后（`mmw-v2/upstream/skills/engineering/code-review/SKILL.md` 第 3 节，#278），剩下的 **out-of-ticket** **review finding** 仍要路由。门槛由 main agent 在收口轮对每一张幸存的 **out-of-ticket** 子票执行。**程序本身写在
`mmw-v2/skills/dispatch/references/night.md` 第 4 步**，因为那是执行它的地方，而夜跑在
consuming repository——那里没有本仓的 `docs/`，一份只存在于这里的判据等于没有判据。这一份
记的是门槛为什么落在那几处、否决了什么。

四步加一道前置，按顺序判，先匹配者胜：

- **第 0 步（前置，不是分类）**：拿当前 `HEAD` 核这条 **review finding** 正文写的条件。已经不成立就关掉，不做任何事。那 38 张里 9 张（24%）属此类。
- **第 1 步**：它落在另一张**还开着**的票的 `## Owns` 里吗 → 开票，且这张票 `Blocked by` 那张活票。不看大小：并发约束不是工作量，main agent 在 **base branch** 直接改会让下一次 `advance` 合并那张活票时冲突。
- **第 2 步**：存在一条已经绿了的 `CHECK:`，而它点名的那样东西是坏的或没被执行到 → 开票，`senior-worker`，并要求 **negative control**。这一类的错法是「没有人会发现」，属 `docs/adr/0008-silence-is-never-a-pass.md`。
- **第 3 步**：修它要动几个文件。一个 → main agent 自己改；两个及以上、且它们之间有**设计上的**咬合（一处的改法决定另一处的改法，不定下来两处都写不对）→ 开票，`senior-worker`。数文件不是数工作量，是数这个改动有没有一个判官该看一眼的跨文件形状。**一个名字在文档里的回声不算咬合**：改名连同它在 `CONTEXT.md`、`night.md`、\`SKILL.md\` 里的复述是机械的，`grep` 就能验证全改到了，仍走「自己改」。
- **第 4 步**：都不匹配 → main agent 自己改。**默认是自己改，不是开票。**

原先在第 3 步与第 4 步之间还有一步「要改的是本仓多张票都指着的文件吗」，名单写死为根
`CONTEXT.md`、根 `AGENTS.md`、任何 `SKILL.md`、`night.md`、`docs/agents/*.md`、
`merge-notes/*`、`downstream-notes/*`，判「自己改」。它被删掉（mmw #297）。两个理由：那份
名单是本仓自己的路径，在 consuming repository 里没有对应物；而它想表达的性质——纯文字、
`grep` 能验证改全了——正是现在第 3 步里那条例外的原话。名单还比那条性质宽：一处
`SKILL.md` 的改动若同时要改一个脚本，按名单走「自己改」，按性质走「开票」，而后者才对，
它不是纯文字。

## Considered Options

- **每夜由 main agent 临时判断该不该开票。** 否决。#216 的比率三代不变，临时判断没有收敛；门槛写死，下一夜才能读出它是紧了还是松了。
- **把门槛留在这份 ADR 里，由 `night.md` 指过来。** 否决（mmw #297）。夜跑在 consuming repository，那里读不到 `docs/adr/`；main agent 拿到的是一个打不开的路径加一句「六步，先匹配者胜」，只能即兴——`mmw-v2/skills/drive-target/scripts/refusal.py` 开头记着即兴的代价。操作指令住在执行它的那份技能里，ADR 留决策与否决。
- **默认开票。** 否决。开票是把同一条 **review finding** 再投进循环。默认自己改，只有第 1、2、4 步的那几类才开票。
- **给 main agent 自己的提交再起一个 reviewer。** 否决。现有 `code-review` 要一个 ticket number，Spec axis 读 `## Read first`，这些提交两样都没有。替代是下面三条可审计规则，早上从 `git log` 就能审这一整轮。
- **在探测层少报 review finding，或给每票子票数设上限。** 否决。问题在路由不在探测；那一夜最值钱的 #253（测试跳过十个用例还打印 `all passed`）正是 Standards axis 找出来的。把 **review finding** 藏起来不是处理掉。

## Consequences

- 收口轮连同这四步一道写在 `mmw-v2/skills/dispatch/references/night.md` 第 4 步，排在 `reverify` 与 `summary` 之前。main agent 自己改的那些守三条可审计规则：
  1. 一个提交对应一张（或一组同源）子票，commit message 按号关闭它们。
  2. 只动那张子票点名的文件。
  3. 跑受影响的测试套件，commit message 引用看到的那一行（`ran 188 skipped 0` 这种，不是「测试通过」）。
- 超出这三条的修复就是一张票。这是逃生口，也是防止第 4 步被滥用的闸。
- 会让这个决定被推翻的证据：收口轮之后 `reverify` 出红票，或 `git log` 审出超出三条规则的改动混在 main agent 自己的提交里。
