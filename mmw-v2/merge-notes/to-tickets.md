# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 2 步「Explore the codebase」 | 我们改的：标题去掉 `(optional)`，正文改成「只有 spec 的 Implementation Decisions 已点名每张票写哪个模块或目录时才可省」。理由：`## Owns` 要求出票人知道目录布局，而一次目录级 `ls` 很便宜。上游改这一步 → 收上游措辞，这个条件保留 |
| 第 3 步拆成「### 3. Draft vertical slices」与「### 4. Write each acceptance criterion」 | 我们拆的：切片规则与 wide refactor 留在第 3 步，验收标准的全部规则移进新的第 4 步，其后各步顺延一号。理由：加上四行形态、CHECK/EXPECT 推导与三条 CHECK 规则之后，第 3 步一半篇幅在讲怎么写标准，而 wide refactor 又排在这堆标准规则之后——同一个标题下两个概念，读的人在切片与标准之间来回跳。上游改这两段的措辞 → 收上游，仍然分成两步，标准那一步永远排在切片之后、连边之前 |
| 写验收标准那一步的第 4 条 | 我们换掉的：上游写的是「每条标准写明在哪验」。改成一句判据加一棵五问判定树——**判定由一条命令下，否则它不是验收标准**；顺次问，停在第一个 yes：判定是一次比对且材料机器够得着 → 写成标准；判定是一次评价且材料够得着 → 归 code review 的三个轴之一（`Standards` 怎么写、`Spec` 是不是要的那件事、`Tests` 某条 `CHECK:` 点名的用例值不值得信），它在另一个会话里跑；被判的性质是一个人的反应 → 单开一张 `reaction` 类的票；机器判得了但够不着（设备、凭证、真实环境）→ 单开一张 `reach` 类的票，并写明补上什么之后它就不需要；不是在验而是在取舍 → 取默认值往下走、写进收尾评论，走不下去才是决策票且该更早问。理由：这一节里每条标准都由机器跑、再由 verifier 跑一遍，「过了」才是事实而不是写代码那一个的看法；一条判定人只有自己的标准留在这里，正好废掉这一节存在的理由。上游自己加了验收标准的写法 → 收上游措辞，五问保留 |
| 写验收标准那一步、五问之后的五段（四行形态、CHECK/EXPECT 从哪来、不许自己找对象、自带前置状态、围栏） | 我们加的整块。四行形态：`- [ ] AC<n>:` / `CHECK:` / `EXPECT:` / `EVIDENCE: pending`，编号出票时编、不重排——账本按编号引用，行号不稳定。CHECK 从 spec 的 Testing Decisions 的层、目录、先例推出，EXPECT 把先例跑一次抄成功那一行——不这么写就会写出永远不可能匹配的期望。CHECK 不许搜索它验的对象（对象要么是这张票自己，从 `$MMW_TICKET` 或分支名 `issue-<n>` 来，要么在票上按编号指名）——「搜出来取第一个」验错过东西，也造过一条不可能失败的检查。CHECK 自带前置状态并还原——每条一个独立 shell、cwd 固定在仓库根，而分支、票、工作区是共享的，复验还会把每条再跑一遍。多行命令写进代码块围栏，没有围栏的续行是解析错误——它遇到空行会静默丢掉后面的行。上游自己加了 CHECK/EXPECT 的写法 → 收上游，这五段并进去 |
| 发布那一步的标签句 | 改成两个落点：agent 做的票打 `ready-for-agent`，要人判的那张单独的票打 `ready-for-human`。要人判的是另一张形态不同的票（没有 Seam、Owns 与验收标准），不是这张票换个标签。上游改这句 → 收上游措辞，两个落点保留 |
| 发布那一步的真 tracker 分支 | 我们加的：在 GitHub 上每张票都建成 spec 的原生 sub-issue（`gh issue create --parent <spec>`，或建完用 `sub_issues` API 挂上去）。理由：上游那一句讲的是**阻塞边**，票与 spec 的父子关系没有任何一步去建；而 `verify-ticket.py --lint` 的票图与 `board.py --watch` 都只从 `repos/{owner}/{repo}/issues/<spec>/sub_issues` 取本批票——不挂上去，白天 lint 打一行「no sub-issues」就 return 0，夜里一张票也派不出来。上游改这一步 → 收上游措辞，这一句保留 |
| 「Give each ticket its blocking edges」独立成一步 | 我们把它从切片那一步摘出来单独成步，那一句原文一字未改，其后各步顺延。技能正文是 agent 顺序执行的：连边留在切片那一步、排在验收标准之前时，它手上只有切片的标题，边只能凭印象连；独立成步且排在验收标准之后时，每张票的验收标准都已写完。上游改这一段的措辞 → 收上游，仍独立成步、仍排在验收标准之后 |
| 写验收标准那一步开头的三条规则 | 我们加的（从 `archive/mmw/skills-src/mmw-to-tickets/SKILL.md` 搬回）：外部可观察行为、精确值从 spec 或原型制品抄、一条一断言。原本还有第四条「每条写明在哪验」，已被五问判定树取代。上游自己加了验收标准规则 → 收上游，三条里它没有的并进去 |
| 「Read every ticket back」那一步 | 我们加的整步：发布完逐张回读，核对标题与 What to build 同一片、Blocked by 全是能解析的票号、原生依赖边数与 Blocked by 行数相等、spec 的 sub-issue 数等于本批票数、Read first 与 Seam 非空且指向交接包时注明它是契约、`Owns` 非空且同一 frontier 两两不重叠、带验收标准的每张票跑 `python3 ~/.agents/skills/verify-ticket/scripts/verify-ticket.py <n> --lint`（写全路径，参数是这张票的 issue 号），`ready-for-human` 的票核它自己该有的五样（Parent、是哪一类、看什么、什么算对、Blocked by）；这一步末尾把主 agent 交到 `dispatch.sh run <spec>`，命令在 dispatch 技能的 SKILL.md 里。理由：一次真实发布把 8 张票的标题错位了一格，没有回读就没人发现；后来又出过整批票的 `EXPECT:` 全都不可能匹配，脚本静态就查得出。`--lint` 的收敛判据分两级——ERROR 改到没有，WARN 逐条看过后决定改还是留；没有 `CHECK:` 的标准报的是 ERROR，它是一条归错了档的标准。回读不是给票的内容打分，是对「发布」这个动作自检，所以给人判的票不被豁免，只是核对的东西不同；给人判的票核五样而不是三样，因为漏掉的 Parent 与 Blocked by 里，后者正是那种票上最要紧的一条边——连错了，人早上会被指去看一个还不存在的东西。末尾那句交接，是因为这一步走完主 agent 手上就没有下一步了，开夜那条命令只写在 dispatch 技能里等人想起来。上游改了步骤编号 → 顺延，这一步永远在发布之后 |
| `<issue-template>` | 我们改的：加 `Parent` 写到小节号、`Read first`（本票小节引用的出处，无则 None）、`Seam`（从 spec Testing Decisions 抄的验证层与目录）、`Owns`（本票可写的仓库相对路径，一行一条，Seam 的测试目录或测试文件必含，新建的标 `(new)`，禁绝对路径、`..`、裸 `**`）四节；`Blocked by` 只写票号。`Owns` 排在 `Seam` 之后，因为两节是一对：Seam 说在哪验，Owns 说在哪写。粒度跟着分工走——独占目录写目录 glob，多票分工同一目录写到文件级；硬判据只有「同一 frontier 两票不得相交」，切不开的共用文件加 Blocked by 边。`Read first` 另写明凡记录已拍板结论的条目（prototype 获胜 artifact、Claude Design 交接包、ADR 的 Decision、decision ticket 的 resolution）是基线——契约不是参考，逐行标明；精确值与逐字文案从交接包 README 抄。`What to build` 要求分点写：人在网页上扫标题找那一件，agent 没有出票人的上下文照着做，两边都读不动一大段连排文字。验收标准从 `- [ ] Criterion 1` 改成四行形态，两条示例都带命令，并写明判断归 code review、只有人看得了的另开一张票。`implement` 靠 `Read first`、`Seam`、`Owns` 三个节名读票，改名要同步改 `implement`。上游改模板 → 收上游结构，这几节接回去 |
| 「Work only a person can do」那一段 | 我们改的：上游给的四个理由是「判断、只有人有的访问权、设计决定、手工测试」，这四个词现在是混的——「判断」大半归了 code review，「设计决定」是五问的第五问、根本不该进这个盒子。改成两类，且要求票上用一个词点明是哪一类：`reaction`（被判的性质就是一个人的反应，人是量具，消不掉）与 `reach`（机器判得了但够不着，补上一个测试账号、一台备用机、一个 runner 就能消掉）。同时列明这种票必须给到的五样：Parent、是哪一类、看什么（一个点开就能看的链接，不是一条要跑的命令）、什么算对、Blocked by。理由：这是全流水线唯一一个不向机器交代理由的出口，一行散文防不住，写不出自己是哪一类就说明它归错了档；而它的读者是早上、在手机上、没有上下文的人，缺「什么算对」他只能回答「我说不上来」。上游改这一段 → 收上游措辞，两类与那五样保留 |
| 模板之后的路径禁令那一句 | 我们改的：上游原句是「avoid specific file paths」，先收窄成「不写实现文件路径」，再明写两个例外——`Seam` 的测试目录或测试文件，`Owns` 的路径。理由：禁令反对的是散在描述里、一改名就错的实现路径；`Owns` 写的不是「代码在哪」而是「你可以写哪」，文件在它里面怎么挪都不影响真值，而且它过期是可见失效（glob 匹配不到任何现存路径），不是静默误导。上游改这一句 → 收上游措辞，两个例外保留 |
| `<issue-template>` 的 `## Seam` 段 | 我们改的：「the prior art to copy」改成「the precedent to copy」，与第 4 步「the precedent it names」用同一个词——同一样东西两个名字，读的人要自己认出它们是一件事。同段末句「A ticket whose only verification is a human check names the device and the steps」删掉：只有人判得了的事已经是另一张票，这张票上不会只剩人工验证。上游改这段 → 收上游，一个词保留、那一句仍然删 |
| 发布那一步的 Local files 分支与 `<local-ticket-template>` | 删掉，发布地只剩真 tracker，`description`、回读那一步与模板后那句里对本地形态的引用一并清掉。理由：本仓的票必须有 issue 号才走得动——`dispatch.sh` 按 `issue-<n>` 开分支、`verify-ticket.py <n>` 按票号跑验收标准并把结论评论回票上、`board.py` 从 spec 的 `sub_issues` 取当晚的 frontier，三样都只认 tracker 上的号；本地文件形态出的票一步都走不了，留着只是给出票人一个走不通的选项，而且它那套粗体行加 `**Status:**` 与 `<issue-template>` 的七节不同形，`--lint` 也只认七节那种。上游再改那一段 → 不收 |
| `<vertical-slice-rules>` | 删掉「Each slice is sized to fit in a single fresh context window」这一条。我们的 spec 通常很大，这条把切片推得过细；粒度由 Quiz the user 那一步问用户来定。上游改这条措辞 → 仍然删。上游把它换成别的尺寸规则 → 也删，保持切片尺寸不设机械上限。其余段落我们没改，全取上游 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |
