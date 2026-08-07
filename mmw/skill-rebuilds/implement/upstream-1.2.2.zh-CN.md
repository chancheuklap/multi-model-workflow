# `implement` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:1-5 -->

```yaml
---
name: implement
description: "根据一份 spec 或一组 ticket 实施一项工作。"
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:7 -->

实施用户在 spec 或 ticket 中描述的工作。

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:9 -->

只要可行，就在预先约定的 seam 上使用 `/tdd`。

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:11 -->

定期运行类型检查，定期运行单个测试文件，并在最后运行一次完整测试套件。

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:13 -->

完成后，使用 `/code-review` 审查这项工作。

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/SKILL.md:15 -->

把改动提交到当前分支。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/implement/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Implement"
  short_description: "根据 spec 或 ticket 实施工作"
policy:
  allow_implicit_invocation: false
```
