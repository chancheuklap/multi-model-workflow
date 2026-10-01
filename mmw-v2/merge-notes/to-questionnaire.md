# to-questionnaire

源目录：`mmw-v2/upstream/skills/productivity/to-questionnaire/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 上游原文，没改；`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false` 一起留着，`skills.txt` 带 `+model-invoked`。规则见 [README.md](README.md#disable-model-invocation) |
| 第 3 步 "Write the questionnaire." 之后新增一句（本仓加） | "The user's open questions are rarely the ones to send. Recast each into something the recipient can answer from their own position and in their own words, and keep the link back to the decision it serves."：本技能常在一轮 `grilling` 之后被调用，对话里堆的是工程术语写成的 frontier 问题，收件人往往不是工程师；上游文档页写了这条标准，但技能正文没有。上游改这一段前后文 → 收上游措辞，这一句接在后面 |
