# to-questionnaire

源目录：`mmw-v2/upstream/skills/productivity/to-questionnaire/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 补了一句「Use when …」：模型可触发的技能，host 启动时只扫这一行，原文只说「我是什么」挑不出何时用；也把原文的 "you" 改清楚成"用户答不了"，不是 agent 自己答不了。上游改这一行 → 收上游对前半句的措辞，末句保留 |
| 第 3 步 "Write the questionnaire." 之后新增一句（本仓加） | "The user's open questions are rarely the ones to send. Recast each into something the recipient can answer from their own position and in their own words, and keep the link back to the decision it serves."：本技能常在一轮 `grilling` 之后被调用，对话里堆的是工程术语写成的 frontier 问题，收件人往往不是工程师；上游文档页写了这条标准，但技能正文没有。上游改这一段前后文 → 收上游措辞，这一句接在后面 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |
