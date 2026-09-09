# grill-with-docs

源目录：`mmw-v2/upstream/skills/engineering/grill-with-docs/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 末尾那两句「什么时候用我」（`Use when a plan or design has to be sharpened inside a working directory …` 与 `Not for a subject with no repository under it …`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；判据取自 `ask-matt/SKILL.md` 里 grill-me 与 grill-with-docs 那组对照。上游改这一行 → 收上游对前半句的措辞，末尾这两句保留 |
| 正文那一句（全文只有这一句） | host 中立：改成读 `grilling` 与 `domain-modeling` 两份技能的 `SKILL.md`，按它们说的跑这次会话。共同理由与三种替换写法见 [README.md](README.md#host-中立) |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |
