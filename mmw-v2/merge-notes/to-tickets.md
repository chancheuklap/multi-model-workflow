# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求全部技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 3 步末尾的「Sharpen … into gates」与「Grade …」两段、第 4 步清单里的 Grade 与 Gates 两行及定级校准一问 | 我们加的，spec `docs/specs/landing-closeout/landing-closeout.md`「验收关卡格式」「定级与阻塞边」：验收条目升级为关卡（ADR 0022），每票打 `worker:junior` / `worker:senior`，定级只在用户批准拆分时可降。上游改第 3、4 步措辞 → 收上游，把这几段按原位并回去 |
| 第 5 步「A real issue tracker」一条 | 我们改写的：阻塞边必须用 GitHub 原生依赖 API 建立，命令引用 `docs/agents/issue-tracker.md`「Wayfinding operations」；正文 `Blocked by:` 文字不算边；发布时加定级标签。上游改这条 → 保留「原生依赖、不写正文文字、加定级标签」三点，其余取上游 |
| 两个模板的验收条目（`CHECK:` / `EXPECT:` / `MANUAL:` 缩进行）、local 模板的 `**Grade:**` 行、issue 模板删掉的 `## Blocked by` 小节、模板后的 `<gate-rules>` 块 | 我们加的。`<gate-rules>` 里五条写法意译自 `docs/specs/landing-closeout/discipline-sources.md` 第 2 章「Author gates that can fail」（该节第六条「按后果复核人工关卡」由 `MANUAL:` 标注承接）；自证例子在 `mmw-v2/skills/self-check/reference/gate-examples.md`。issue 模板不再有 `## Blocked by`：边在原生依赖里。上游改模板 → 收上游的其他字段，验收小节与 `<gate-rules>` 以我们的为准 |
| `<vertical-slice-rules>` | 删掉「Each slice is sized to fit in a single fresh context window」这一条。我们的 spec 通常很大，这条把切片推得过细；粒度由第 4 步问用户来定。上游改这条措辞 → 仍然删。上游把它换成别的尺寸规则 → 也删，保持切片尺寸不设机械上限。其余段落我们没改，全取上游 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
