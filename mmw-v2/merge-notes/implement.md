# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的「开写之前先读」那一段 | 我们加的：票读全 → 顺 Parent 读 spec 全文 → 读 spec 的 `## Sources` 链的 prototype 与 research 到结论 → 读 ADR 与领域词汇表 → 用一句话说出这张票在哪个 seam 上测，然后动手。`## Sources` 这个名字是我们在 `to-spec` 模板里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，只把它没有的那几项（Sources、说出 seam）并进去，不并列两段。其余段落我们没改，全取上游 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型能自己派 implement，所以两处一起删。上游若再带回来 → 仍然删 |
