# `handoff` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md:1-6 -->

```yaml
---
name: handoff
description: 把当前对话压缩成一份 handoff 文档，供另一个 agent 接手。
argument-hint: "下一次 session 将用于什么？"
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md:8 -->

编写一份概括当前对话的 handoff 文档，使一个新的 agent 能够继续工作。把文件保存到用户操作系统的临时目录，不要保存到当前 workspace。

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md:10 -->

文档中包含一个 `suggested skills` 章节，建议 agent 应该调用哪些技能。

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md:12 -->

已经记录在其他产物中的内容不得重复，包括 spec、plan、ADR、issue、commit 和 diff。改为通过路径或 URL 引用这些内容。

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md:14 -->

隐去 API key、密码或个人身份信息等敏感信息。

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/SKILL.md:16 -->

用户传入参数时，把参数视为下一次 session 的工作重点说明，并据此调整文档。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/productivity/handoff/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Handoff"
  short_description: "把对话压缩成 handoff"
policy:
  allow_implicit_invocation: false
```
