# `grill-with-docs` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md:1-5 -->

```yaml
---
name: grill-with-docs
description: 通过 relentless 访谈使计划或设计更加明确，并在过程中创建文档（ADR 和术语表）。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/grill-with-docs/SKILL.md:7 -->

运行一场 `/grilling` session，并使用 `/domain-modeling` 技能。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/grill-with-docs/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Grill with Docs"
  short_description: "对一项设计进行 grilling，并编写相应文档"
policy:
  allow_implicit_invocation: false
```
