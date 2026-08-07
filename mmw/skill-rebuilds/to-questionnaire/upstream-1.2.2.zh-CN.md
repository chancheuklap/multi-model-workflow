# `to-questionnaire` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:1-5 -->

```yaml
---
name: to-questionnaire
description: 把一个你无法完整回答的决定整理成问卷，交给其他人填写。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:7 -->

把用户无法独自回答的事项整理成一份**问卷**，也就是一份 Markdown 文档。用户可以把它交给一个人异步填写，也可以在会议中与对方一起填写。收件人掌握用户欠缺的知识；问卷负责把这些知识引出来。

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:9 -->

**追问发送安排，不追问主题本身。** 只围绕用户始终能够回答的**发送安排**访谈用户：问卷发给谁，以及用户需要拿回什么。文档中的问题再对准收件人掌握的知识与用户需求之间的**缺口**。

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:11 -->

1. **问卷发给谁？** 在一次问答中询问收件人的角色、专长，以及收件人与用户的关系。这些信息决定问卷的语气和需要携带多少上下文。当你知道收件人是谁，以及对方掌握哪些用户不掌握的知识时，这一步完成。

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:13 -->

2. **你需要拿回什么？** 在一次问答中询问用户无法独自解决、需要由这个人提供的具体决定或事实。当你得到一份具体清单，列明用户最终必须能够完成什么或决定什么时，这一步完成。

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:15 -->

3. **编写问卷。** 针对第 1 至第 2 步确定的缺口拟定问题，并遵循下方的“文档结构”。把问卷写入当前目录中的 `to-questionnaire-<slug>.md`，其中 slug 来自主题；随后报告文件路径。当文件已经存在，而且用户在第 2 步点名的每一项内容都有问题覆盖时，这一步完成。

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:17-19 -->

## 文档结构

把文档组织成一份 **discovery questionnaire**：用户缺少上下文，收件人掌握这些上下文。按重要程度从高到低排列问题，因为异步沟通可能只有一次回答机会。问题超过少量时，按主题放进不同的 `##` 标题。使用下方模板编写。

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/SKILL.md:21-53 -->

<questionnaire-template>

# <问卷标题>

**目的：** 说明这份问卷为何存在，以及哪个决定取决于这些答案。

**来自：** <用户> — **发给：** <收件人> — **答案将怎样使用：** <答案去向>

## 上下文

用一个段落帮助没有参与用户思考过程的收件人理解情况。信息要足以让对方给出高质量答案，但不要写满一页。

## 回答方式

说明截止时间和大致所需投入。部分答案和“我不知道”都有价值；对不确定的内容作出标记，不要直接跳过。

## <主题标题>

每个主题使用一个 `##` 章节。每个章节内按重要程度从高到低排列问题。每道问题只包含一个意思，绝不把多个问题合在一起。每道问题下方直接提供回答占位。只有问题可能被误解或容易得到敷衍回答时，才增加一行“为什么这很重要”。

<question-example>
### 系统上线时预计需要承受多大负载？

_为什么这很重要：答案决定我们现在就按突发流量配置资源，还是把它推迟。_

>
</question-example>

## 还有其他内容吗？

最后用一个兜底问题收尾：有没有我们没有问到、但应该知道的内容？

</questionnaire-template>

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/productivity/to-questionnaire/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "To Questionnaire"
  short_description: "把决定整理成供他人回答的问卷"
policy:
  allow_implicit_invocation: false
```
