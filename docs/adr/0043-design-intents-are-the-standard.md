---
date: 2026-10-09
amends: []
---

# 改技能以 `writing-for-agents` 的 `DESIGN-INTENTS.md` 为标准：每次改动先说出它服务哪条意图，审查逐条意图追踪落地，一个结论只判一次

MMW 是把 Matt Pocock 的技能放进 pstack 的骨架，再加上自己的改良。改一份技能或审查一组技能时，agent 需要知道这套技能要守住什么，以及哪些上游做法是有意不要的。这些写在两份文件里：`mmw-v3/skills/writing-for-agents/DESIGN-INTENTS.md` 列 MMW 的 41 条设计意图，每条写它取了哪些上游意图、规则写在哪个文件；`UPSTREAM-INTENTS.md` 列 Matt 和 pstack 的意图和出处。前者只是索引，规则正文仍在执行它的 agent 读的那份文件里。Authoring or modifying a skill 的 Place it 先说出改动服务哪条意图；Review the skill set 逐条意图查它写在哪、谁在哪一步读到、靠脚本还是靠文字、交接形状和各处说法；拉上游新版后对照上游意图清单补齐。`SKILL-SET-RULES.md` 的 `## Editing` 写明修法不对已判过的结论再加一次判断。

## 为什么要写下来

主人不读代码，只能靠 agent 守住设计。此前这些意图只在一次对话和一个页面里：下一个 agent 拿不到，会把有意不要的上游做法当成缺陷补回来，或者用"再加一道验证"去修问题。主人的规则是：一个结论只验一次，失败就返回修好，进入下一步。

## Considered Options

- **意图表放在 `mmw-mode/references/`。** 否决。写 spec 的会话读 `writing-for-agents`，读不到 `mmw-mode/references/`（同 0040）。
- **把每条意图的规则全文写进意图表。** 否决。规则会有两份，执行它的 agent 读的那份和表里那份迟早不一致。表只写一句意图和它的规则在哪。
- **写一个脚本核对每条上游意图都在意图表里出现。** 暂不做。上游意图只在拉新版时变，那一步已要求对照补齐；还没有一次因为漏挂而出错。

## Consequences

- 一次技能改动先说出它服务的意图；会破坏某条意图或把某个有意不要的做法带回来的改动，先问主人。
- 增删或改动一条意图、或者它的规则换了文件，同一次提交更新意图表。
- 审查报告里每条问题写明它违反哪条意图。
