# `wait-what` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/productivity/wait-what/SKILL.md:1-5 -->

```yaml
---
name: wait-what
description: 停一下。上一条消息没有让人听明白——重新表述。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/productivity/wait-what/SKILL.md:7 -->

等一下——我不明白你现在讲到哪一步了。换一种方式重新说明：补一点上下文，使用 ASD-STE100 简化技术英语（Simplified Technical English），并采用 `CONTEXT.md` 中的通用语言。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/productivity/wait-what/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Wait What"
  short_description: "补上我缺少的上下文，用更简单的方式重新说明"
policy:
  allow_implicit_invocation: false
```
