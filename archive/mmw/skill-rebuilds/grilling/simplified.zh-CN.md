# `grilling` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:1-4 -->

```yaml
---
name: grilling
description: relentless 地追问用户的计划、决定或想法。用户希望对自己的思路进行压力测试，或者使用任何“grill”触发语时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:6 -->

以 relentless 的方式访谈用户，直到双方形成共同理解。把这次访谈组织成一棵**设计树**：每个决定都会分叉出依赖它的决定。

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:8 -->

按**轮**遍历设计树。**frontier** 包含所有前置条件已经确定的决定，也就是现在提问时不需要猜测尚未听到的答案。每一轮提出整个 frontier：给每个问题编号，并给出你的推荐答案。随后等待用户回答，再进入下一轮。

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:10-16 -->

每个问题采用以下格式：

```
❓ **Q1** - **<问题标题>**：<问题正文；可以包含多个段落和多个选项>

➡️ <你的推荐答案>
```

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:18 -->

用户每回答一轮，设计树都会改变：已经确定的决定会把 frontier 向外推进，并解除依赖它们的问题。重新计算 frontier，再提出下一轮问题。如果一个问题的答案依赖本轮仍未解决的另一个问题，它属于**后续**轮次，不属于当前轮次。

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:20 -->

查明**事实**是你的工作，绝不是用户的工作。frontier 上的问题需要从环境中取得事实时，例如文件系统或工具，派一个 subagent 去查；凡是你能自行查找的内容，都不要向用户提问。不要让这项调查阻塞整个 frontier：正在进行的探索是一项尚未确定的前置条件，因此只有依赖它的问题等待 subagent 报告；立即提出 frontier 中其余问题。**决定**属于用户；逐项交给用户，并等待回答。

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/SKILL.md:22 -->

frontier 为空时，session 才完成：设计树的每个分支都已经访问，没有任何内容被静默假设。在用户确认双方已经形成共同理解之前，不得据此采取行动。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/productivity/grilling/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Grilling"
  short_description: "每轮提出一组问题，对思路进行压力测试"
```
