# `to-spec` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md:1-5 -->

```yaml
---
name: to-spec
description: 把当前对话整理成一份 spec，并发布到项目 issue tracker。不要再做访谈，只综合已经讨论过的内容。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md:7-9 -->

本技能使用当前对话上下文和对代码库的理解来生成一份 spec。**不要**访谈用户；只综合已经掌握的内容。

issue tracker 和 triage 标签词汇应该已经提供给你；如果没有，运行 `/setup-matt-pocock-skills`。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md:11-17 -->

## 流程

1. 如果还没有探索过仓库，就探索仓库，以理解代码库当前状态。整份 spec 都使用项目领域术语表中的词汇，并遵守本次涉及范围内的所有 ADR。

2. 勾勒将用于测试这项功能的 seam。已有 seam 应优先于新 seam。使用尽可能高层的 seam。确实需要新 seam 时，在能够达到的最高层提出。整个代码库中的 seam 越少越好；理想数量是一个。

向用户确认这些 seam 是否符合预期。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md:19 -->

3. 使用下方模板编写 spec，然后发布到项目 issue tracker。添加 `ready-for-agent` triage 标签，不需要再次 triage。

<!-- source: vendor/mattpocock-skills/skills/engineering/to-spec/SKILL.md:21-75 -->

<spec-template>

## Problem Statement

从用户角度说明用户正面对的问题。

## Solution

从用户角度说明这个问题的解决方案。

## User Stories

编写一份**很长的**编号 user story 清单。每条 user story 使用以下格式：

1. 作为 <角色>，我希望获得 <功能>，以便 <收益>

<user-story-example>
1. 作为一名手机银行客户，我希望看见自己各个账户的余额，以便对支出作出信息更充分的决定
</user-story-example>

这份 user story 清单必须极其详尽，并覆盖功能的所有方面。

## Implementation Decisions

列出已经形成的实施决定，可以包含：

- 将要建立或修改的 module
- 将要修改的 module interface
- 开发者作出的技术澄清
- 架构决定
- schema 变更
- API 合同
- 具体交互

**不要**写入具体文件路径或代码片段。这些内容可能很快过期。

例外：如果 prototype 产生的一段代码比文字更精确地编码了某项决定，例如状态机、reducer、schema 或类型形状，就把它内联到相关决定中，并简短注明它来自 prototype。只保留决定信息密集的部分；不要放入可运行 demo，只放重要片段。

## Testing Decisions

列出已经形成的测试决定，包含：

- 说明什么样的测试才是好测试，只测试外部行为，不测试实现细节
- 将测试哪些 module
- 测试先例，例如代码库中类似类型的测试

## Out of Scope

说明哪些内容不在这份 spec 的范围内。

## Further Notes

记录关于这项功能的其他说明。

</spec-template>

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/to-spec/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "To Spec"
  short_description: "把一段对话整理成 spec"
policy:
  allow_implicit_invocation: false
```
