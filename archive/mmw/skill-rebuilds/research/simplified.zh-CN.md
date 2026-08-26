# `research` 1.2.2 精简稿

## `SKILL.md`

```yaml
---
name: research
description: 对照高可信度的一手来源调查一个问题，并把调查结论记录为仓库中的一份 Markdown 文件。用户要求研究一个主题、收集文档或 API 事实，或者把阅读工作交给后台 agent 时使用。
---
```

启动一个**后台 agent** 执行 research，使你能在它阅读资料时继续工作。

它的任务如下：

1. 对照**一手来源**调查问题。一手来源包括官方文档、源代码、spec 和第一方 API；不要使用对这些来源的二手转述。每项断言都要追溯到拥有该事实的来源。
2. 把调查结论写入一份 Markdown 文件，并为每项断言标注来源。
3. 把文件保存到仓库已有的同类笔记位置。遵循现有约定；如果没有约定，就选择一个合理位置，并说明保存位置。

## `agents/openai.yaml`

```yaml
interface:
  display_name: "Research"
  short_description: "依据高可信度来源执行 research"
```
