# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求全部技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 2 步「Explore the codebase」 | 我们改的：标题去掉 `(optional)`，正文改成「只有 spec 的 Implementation Decisions 已点名每张票写哪个模块或目录时才可省」。理由：`## Owns` 要求出票人知道目录布局，而一次目录级 `ls` 很便宜。上游改这一步 → 收上游措辞，这个条件保留 |
| 第 3 步验收标准第 4 条 | 我们改的：从「写明在哪验」改成「先问这条标准的读者是谁」，分三条出路——读者是 agent 且写得出命令 → `CHECK:`/`EXPECT:`；读者是 agent 但写不出命令 → 仍留在票上，做票的 agent 自己判、自己勾、`EVIDENCE:` 写读了什么；读者确实是人 → 单开一张票。判代码对不对、判一段话对 agent 够不够用、判一份 agent 自己拿得到的报告，读者都是 agent——不先问这一句，这三类会被当成人工项丢给用户。上游改这条 → 收上游，三条出路保留 |
| 第 3 步验收标准规则之后的五段（四行形态、CHECK/EXPECT 从哪来、不许自己找对象、自带前置状态、围栏） | 我们加的整块。四行形态：`- [ ] AC<n>:` / `CHECK:` / `EXPECT:` / `EVIDENCE: pending`，编号出票时编、不重排——账本按编号引用，行号不稳定。CHECK 从 spec 的 Testing Decisions 的层、目录、先例推出，EXPECT 把先例跑一次抄成功那一行——不这么写就会写出永远不可能匹配的期望。CHECK 不许搜索它验的对象（对象要么是这张票自己，从 `$MMW_TICKET` 或分支名 `issue-<n>` 来，要么在票上按编号指名）——「搜出来取第一个」验错过东西，也造过一条不可能失败的检查。CHECK 自带前置状态并还原——每条一个独立 shell、cwd 固定在仓库根，而分支、票、工作区是共享的，复验还会把每条再跑一遍。多行命令写进代码块围栏，没有围栏的顶格续行是解析错误——隐式续行遇到空行会静默丢掉后面的行。上游自己加了 CHECK/EXPECT 的写法 → 收上游，这五段并进去 |
| 第 3 步验收标准之后的「Work only a person can judge is its own ticket」 | 我们加的整段：要人判的事（读一份文本判可读性、对着基线看 UI、拿不准的措辞）单开一张 `ready-for-human` 的票，用阻塞边挂在产出被判之物的那张票后面，并写一行说明为什么不能委派（判断、只有人有的访问权、设计决定、手工测试——沿用 triage 技能对 `ready-for-human` 的定义）。理由：此前这类事写成票内的一条特殊标准，机器不判、也不计数，一张票上能攒好几条，早上全落在人头上。上游自己加了人工标准的写法 → 收上游，仍然单开票 |
| 第 6 步的标签句与 `<local-ticket-template>` 的 `Status` 行 | 改成两个落点：标准全带命令的打 `ready-for-agent`，要人判的打 `ready-for-human` 并带那一行理由。上游改这句 → 收上游措辞，两个落点保留 |
| 第 3 步末尾的 blocking edges 那一段 → 独立成「### 4. Give each ticket its blocking edges」 | 我们把它从第 3 步摘出来单独成一步，那一句原文一字未改，其后的 Quiz / Publish / Read back 各顺延一号。技能正文是 agent 顺序执行的：连边留在第 3 步、排在验收标准之前时，它手上只有切片的标题，边只能凭印象连；独立成步且排在验收标准之后时，每张票的验收标准都已写完。上游改这一段的措辞 → 收上游，仍独立成步、仍排在验收标准之后 |
| 第 3 步的验收标准四条规则 | 我们加的（从 `archive/mmw/skills-src/mmw-to-tickets/SKILL.md` 搬回）：外部行为、精确值、一条一断言、每条写明在哪验，写不出就退回 `/to-spec`。上游自己加了验收标准规则 → 收上游，四条里它没有的并进去 |
| 第 6 步之后的「### 7. Read every ticket back」 | 我们加的整步：发布完逐张回读，核对标题与 What to build 同一片、Blocked by 全是能解析的票号、原生依赖边数与 Blocked by 行数相等、Read first 与 Seam 非空且指向基线目录时注明它是契约、`Owns` 非空且同一 frontier 两两不重叠、每张票跑 `verify-ticket.py <n> --lint`。理由：一次真实发布把 8 张票的标题错位了一格，没有回读就没人发现；后来又出过整批票的 `EXPECT:` 全都不可能匹配，脚本静态就查得出。`--lint` 的收敛判据分两级——ERROR 改到没有，WARN 逐条看过后决定改还是留：没有 `CHECK:` 的标准本来就会报一条 WARN，要求它清零等于禁掉第二条出路。上游改了步骤编号 → 顺延，这一步永远在发布之后 |
| `<local-ticket-template>` 与 `<issue-template>` | 我们改的：加 `Parent` 写到小节号、`Read first`（本票小节引用的出处，无则 None）、`Seam`（从 spec Testing Decisions 抄的验证层与目录）、`Owns`（本票可写的仓库相对路径，一行一条，Seam 的测试目录或测试文件必含，新建的标 `(new)`，禁绝对路径、`..`、裸 `**`）四节；`Blocked by` 只写票号。`Owns` 排在 `Seam` 之后，因为两节是一对：Seam 说在哪验，Owns 说在哪写。粒度跟着分工走——独占目录写目录 glob，多票分工同一目录写到文件级；硬判据只有「同一 frontier 两票不得相交」，切不开的共用文件加 Blocked by 边。`Read first` 另写明下载回来的基线目录（含交接包 README）是契约不是参考。`What to build` 要求分点写：人在网页上扫标题找那一件，agent 没有出票人的上下文照着做，两边都读不动一大段连排文字。验收标准从 `- [ ] Criterion 1` 改成四行形态，并写明读者是人的标准不留在票上。`implement` 靠 `Read first`、`Seam`、`Owns` 三个节名读票，改名要同步改 `implement`。上游改模板 → 收上游结构，这几节接回去 |
| 模板之后的路径禁令那一句 | 我们改的：上游原句是「avoid specific file paths」，先收窄成「不写实现文件路径」，再明写两个例外——`Seam` 的测试目录或测试文件，`Owns` 的路径。理由：禁令反对的是散在描述里、一改名就错的实现路径；`Owns` 写的不是「代码在哪」而是「你可以写哪」，文件在它里面怎么挪都不影响真值，而且它过期是可见失效（glob 匹配不到任何现存路径），不是静默误导。上游改这一句 → 收上游措辞，两个例外保留 |
| `<vertical-slice-rules>` | 删掉「Each slice is sized to fit in a single fresh context window」这一条。我们的 spec 通常很大，这条把切片推得过细；粒度由 Quiz the user 那一步问用户来定。上游改这条措辞 → 仍然删。上游把它换成别的尺寸规则 → 也删，保持切片尺寸不设机械上限。其余段落我们没改，全取上游 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
