# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求全部技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 3 步末尾的 blocking edges 那一段 → 独立成「### 4. Give each ticket its blocking edges」 | 我们把它从第 3 步摘出来单独成一步，那一句原文一字未改，其后的 Quiz / Publish / Read back 各顺延一号。技能正文是 agent 顺序执行的：连边留在第 3 步、排在验收标准之前时，它手上只有切片的标题，边只能凭印象连；独立成步且排在验收标准之后时，每张票的验收标准都已写完。上游改这一段的措辞 → 收上游，仍独立成步、仍排在验收标准之后 |
| 第 3 步的验收标准四条规则 | 我们加的（从 `archive/mmw/skills-src/mmw-to-tickets/SKILL.md` 搬回）：外部行为、精确值、一条一断言、每条写明在哪验，写不出就退回 `/to-spec`。上游自己加了验收标准规则 → 收上游，四条里它没有的并进去 |
| 第 6 步之后的「### 7. Read every ticket back」 | 我们加的整步：发布完逐张回读，核对标题与 What to build 同一片、Blocked by 全是能解析的票号、原生依赖边数与 Blocked by 行数相等、Read first 与 Seam 非空。理由：一次真实发布把 8 张票的标题错位了一格，没有回读就没人发现。上游改了步骤编号 → 顺延，这一步永远在发布之后 |
| `<local-ticket-template>` 与 `<issue-template>` | 我们改的：加 `Parent` 写到小节号、`Read first`（本票小节引用的出处，无则 None）、`Seam`（从 spec Testing Decisions 抄的验证层与目录）两节；`Blocked by` 只写票号；路径禁令收窄成「不写实现文件路径」。`implement` 靠 `Read first` 与 `Seam` 两个节名读票，改名要同步改 `implement`。上游改模板 → 收上游结构，这几节接回去 |
| `<vertical-slice-rules>` | 删掉「Each slice is sized to fit in a single fresh context window」这一条。我们的 spec 通常很大，这条把切片推得过细；粒度由 Quiz the user 那一步问用户来定。上游改这条措辞 → 仍然删。上游把它换成别的尺寸规则 → 也删，保持切片尺寸不设机械上限。其余段落我们没改，全取上游 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
