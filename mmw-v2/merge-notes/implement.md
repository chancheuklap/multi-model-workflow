# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

这份技能的正文是本仓库自己的文本：拉上游时不合并进来，下面各行记的是每一段为什么这样写。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步是 `verify-ticket.py <n> --preflight`，`NOT_READY` 就停，这一行只写命令和这一条；为什么排第一（这条 pipeline 里没有别的东西 claim 票，第 8 步关不了不归你的票）只写在这里。六项核对、claim、baseline run 与未提交改动的 `CARRIED:` 都由脚本做，每条拒绝与 `CARRIED:` 自己说下一步，所以正文不复述。标题与 `## What to build` 是否描述同一个 vertical slice，`to-tickets` 发布回读时已经查过；`## Owns` 里标或不标 `(new)` 不影响判定（`owns_globs` 的 docstring："`(new)` is a note"）；真自相矛盾的票由写码规则里的 `contract` 规则接住，正文不再单独核对一遍。缺 `## Owns`、`## Read first` 或 `## Seam` 的旧票不给退路：两个 tracker 的 154 张 agent 票都带这三节，缺的只有 `ready-for-human` 票，worker 不接。理由：claim 与开工前的核对是固定操作，交给脚本比写成正文指令可靠。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 `Owns check` 保留。同一段末尾一句：自己拿起票（不是被 `start` 起来）的会话在 claim 之前照 `dispatch` 技能的 `references/inside-a-ticket.md` 做；`adopt` 为什么必跑写在那份文件里，被 `start` 起来的 worker 不读它。上游改开工段 → 这一句保留 |
| 「开写之前先读」那一段 | 我们改的：票读全、本票开着的 sub-issue（`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100`——不带 `--paginate` 只回第一页 30 条且不留标记，worker 会把看不见的子票当作不存在，当 `## What to build` 的补充，做与不做写进 `Decisions I made on my own`）→ `## Read first` 逐份读到结论（research 文件里回答其问题的那部分，不是"末节"：本仓约 30 份报告的最后一节几乎都是来源清单或未核实事项、ADR 标题下那段无标题的决定、拉进仓库的 design package、prototype 叶子 `README.md` 读到它的 verdict），其中记录已拍板结论的条目是 baseline，`the baseline is the contract`，不是参考；两类 baseline 处理不同：design package 逐字照抄，prototype 按正式标准重写、保住 verdict 定下的形状 → 沿 `## Parent` 读 spec 的 Problem Statement 和 Solution（谁在用、为什么要，`## Read first` 与验收标准都不写这个）再只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文；票和验收标准都没说到的地方，按 Problem Statement 点名的人会怎么用来选 → 领域词汇表（根 `CONTEXT.md`，或 `CONTEXT-MAP.md` 列出、本票涉及的各 context 的 `CONTEXT.md`），它有对应的词就用那个词。多 context 的仓库根上没有 `CONTEXT.md`，只写「根 `CONTEXT.md`」的话 worker 要么跳过词汇表，要么读错一份。理由：整份 spec 会淹掉票指名的小节；baseline 的 contract 地位防默默偏离。prototype 那一项指向叶子 `README.md` 读到它的 verdict，与同一句里另外三项同构——四项都是打开就找得到的位置（research 文件的末节、ADR 的那一节、拉进仓库的整个目录、叶子 `README.md`）；照着哪一块写由 verdict 自己说，不必再写一条禁令去排除 HTML 外壳或 harness。两类 baseline 的差别不写出来，worker 会对着一个 prototype 的 variant 逐字抄，把原型阶段的粗糙一起抄进正式代码。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，`narrowed reading` 与 `the baseline is the contract` 保留 |
| `state the seam` 那一段 | 我们删的：这一句只是把票上的 `## Seam` 字段抄到屏幕上，自主会话里没有人读它。测试真正要落在票的 `## Seam` 上这一层，已经在下面 `tdd` 交接句里说了（`Read the tdd skill's SKILL.md and follow it where possible, at pre-agreed seams.`），够用。上游若把这句加回来 → 不收 |
| `state the seam` 与 `/tdd` 之间的 writing rules 段 | 我们加的：一串动作——`## Read first` 里每条 baseline、`## Parent` 指名的 spec 小节和 ticket acceptance criteria 都是 contract（`the baseline is the contract`），值、文案、状态与接口形状从 baseline 抄而不是凭记忆重写；`the contract does not fit` 是任一份缺状态、字段、交互或用例、同一 domain 的两份互相矛盾，或 acceptance criterion 测不到它所说的行为。worker 对本票跑 `verify-ticket.py <n> --sub-issue contract <file>`，body 点名 AC、逐字引用错处、写同一依据里仍成立而必须保留的部分，继续不依赖它的工作；其中错的是 `CHECK` 时还写它该是什么（正文 `A wrong CHECK is a contract child too`）。只有 main agent 或 user 改已发布 spec、ticket body 和 acceptance criterion，改好后 worker 才继续。不默默改 baseline、不默默绕过；过不了的检查用改代码或 abandon 那条 acceptance criterion 来答，不弯 baseline、不弯 the harness、不弯测试——这一款给的是正面动作接一句底线，而不是并排的第三个 never，且它指向的 abandon 就是同一份文件 closing steps 第 1 步的 `ABANDON: AC<n> failed`；改函数前 grep 每个调用方、修共用处；新写的东西取代了已有的分支、guard 或文件时，同一个 commit 删掉它——不再要求每加一个分支都先点名一个要删的东西，那样 worker 会硬找一个去删，或因找不到而不敢加必要的 guard；写 helper 前先在仓库与 `## Read first` 找现成；加文件、依赖、配置前把已有的为何不够写进 `Decisions I made on my own`（原来只说 `say why`，自主会话里没有人听，这样才进 reviewer 的 Spec axis 逐行判的清单）；安全、防数据丢失、无障碍与票里明确要的（`## What to build`、每条 acceptance criterion、baseline、`## Seam` 的接口）不许简化，正文用正面说法 `Whatever you simplify, keep intact:`；`skipped: [X], add when [Y]` 的格式写在收尾第 7 步填 `<fill>` 那里，那是它被填的时刻；`Owns two grades`——为过 acceptance criterion 不得不改的 `## Owns` 外文件照改、由 closing comment 的 `Outside Owns:` 记录，顺手想改的不改、对本票跑 `--sub-issue deferred`。同段还有 `Put no question on the screen`，见下方同名一节。规则写成动作 + 票字段。那次对照实验（ponytail，记录在 Nowledge Mem）比较的是同一条纪律写成散文与写成动作，证明的是规则要写成动作；它没有测规则旁边的一句理由。理由句只在能改变清单外情形下的选择时才写，贴在它管的规则旁边：baseline 那条加了两句——baseline 是别人已经付过代价的决定，照抄／改进的差别就在这里；答案关系到剩下的工作时结束回合等 `contract` 子票叫醒主 agent；bullet 末尾加一句检查为什么值得信——诚实的 `HANDOFF REQUIRED` 代价小，假的 `ALL MET` 代价大，且会传给建在它之上的每一张票。`Put no question on the screen` 末尾加一句：这些行是给 reviewer 逐行判、给用户早上读的，产品里看得见的选择（一个标签、一个默认值、页面显示或隐藏什么）最值得写一行。上游加了写码期间的纪律段 → 收上游措辞，这些条并进去 |
| 读 `## Read first` 那一段末尾加一行：`## Read first` 列了 screen contract 时，读 `references/writing-interface-code.md` | 我们改的，来自 mmw #447 第 8 节。界面写码规则不写在 `SKILL.md`。上游改读入段 → 收上游措辞，这一行保留 |
| writing rules 里不再放界面写码规则（`[data-story-root]` 与 `data-ui` id、story adapter 与四列 boundary test、一条代码路径） | 我们改的：这些句子从 writing rules 挪进 `references/writing-interface-code.md`，见下方同名一节。上游改 writing rules → 收上游措辞，这些句子仍只住在那份文件 |
| `Run typechecking regularly, single test files regularly, and the full test suite once at the end.` | 我们改的：末尾不跑 full suite，改跑仓库自己的说明为本票改动点名的测试，并写明 `--closeout` 自己跑仓库的 `checks`。理由：用户级 prompt 的 rule 15 和消费仓库的 `AGENTS.md` 都默认禁止全量测试，worker 手上三条指令互相矛盾时只能凭习惯选；仓库的 `checks` 由 `--closeout` 跑，worker 不必自己跑全量来替它。上游改这一句 → 收上游措辞，full suite 不回来 |
| `Run typechecking regularly` 之后、「Once done」之前的测试范围段 | 我们加的。`tdd` 那一行、`Run typechecking regularly` 与这一段三段排在 `## Claim, read in, write the code` 末尾、写码规则之后：三段都是写码时的指引，放在 `## Shared experience while implementing` 底下，读者会把它们当成 Memory 那一节的内容。验证手段随意、scratch 脚本不必保留；只在票要求或仓库本来就为这类改动留测试时提交测试，规模比照相邻测试文件（每条声明的行为约一个测试）——临时检查因此不会成为永久测试文件，正文不另写这一句；这段只管多出来的东西，票要的每个行为仍要完整实现。来源是 Anthropic 的 `Prompting Claude Fable 5.1` 指南 `Keep changes and tests to what the task asks for` 一节：`Owns two grades` 管改动范围，这段补上测试文件数量。上游若加了同类约束 → 收上游措辞 |
| `## Shared experience while implementing` | 我们加的，来自 mmw #427 与 `docs/notes/stage-two-shared-experience-layer.md` 的第 4、5 节。这一节是 worker 每次都要的部分：首次 prompt 的两份索引与打开记录的 `memories show` 命令、current evidence authority、两级精确 search command（搜索词只用报错、命令与组件，并以 `--` 隔开：Nowledge 对含有记录里没有的具体标识的搜索词整批不返回，对以 `-` 开头的搜索词当作选项解析）、三项同时成立的 capture gate。原来的"每个里程碑再评一次"是空转句，同一段第一句"三项一成立就存"已经说了；`MMW_TASK_SCOPE` 为空时不写也从正文删掉，改成 `references/saving-memory.md` 的保存命令自己判断——scope 不是 `mmw-map-*` 或 `mmw-spec-*` 就直接退出，不写任何东西，确定的条件交给命令，不必让 worker 记住它。存与改在 `references/saving-memory.md`，capture gate 成立或要更正一条记录时才读：map/standalone labels、scope 检查、标题写组件与行为且 `证据` 写出涉及的仓库路径（下一名 worker 的 Related experience 按路径排序）、五项正文与可执行的 `nmem memories add --stdin` 命令、`learning`/`procedure`、安全排除、写失败不挡工单、`supersede`/`deprecate` 命令。理由：两个 tracker 的 Memory space 合计 66 条 `mmw-experience`，对 154 张 agent 票，多数 run 什么都不存。派工给的环境值不列：命令直接用 `$NMEM_SPACE` 等变量。派工 prompt 只给数据并指向这一节，所以 worker 读到的规则只有这一份。`summary` 的 lifecycle 和 `retro` 的固定 id 写入由各自脚本负责，不教 worker 操作它们。上游改写码段或新增通用记忆步骤 → 收上游措辞，保留这一节与 `references/saving-memory.md`，命令与字段不概括 |
| 「Once done」之后的 closing steps | 我们改的：八步，顺序是 worker 自跑（`ticket.checked`，run `self`）→ DECISIONS → reviewer → worker 最终全量运行（`--reverify --actor worker`）→ Audit → `--touched` → `--draft` → `--closeout`。最终全量运行排在最后一个写 commit 的步骤之后，并重跑全部标准；closeout 只接受 actor 为 worker、commit 为 `HEAD`、shape 与票面一致且结果满足关票条件的最新 reverify。DECISIONS 排在 reviewer 之前：Spec axis 要对 DECISIONS 的每一行给 `reasonable` 或 `should not`，`--touched` 也从 review 里取这个判断，评论晚于 review 就永远没有东西可判；review 修一轮里新做的决定不补进 DECISIONS，由收尾评论带最终版。第 3 步 `start <n> reviewer` 不带开关，启动后结束回合，由 relay 在 `reviewer.reported` 落票时叫醒；读事件后 `ack`。`start` 退出 2 是 pipeline fault：用 `verify-ticket.py <n> --sub-issue fault <file>` 记录后停止。票内发现不修的，写成 `refuted:`，判据照抄 BMAD `step-04-review.md`：查过、坏结果不在所引位置发生，写出反驳这条具体说法的依据。四个子命令 `--decisions`、`--touched`、`--draft`、`--closeout` 的每条拒绝自己说下一步，exit code 在 `verify-ticket.py --help`，正文不复述；worker 写草稿时要满足的规则（各个 `<fill>` 怎么填、`ABANDON:` 放在它的 criterion 下）写在第 7 步；首行是 `ALL MET` 还是 `HANDOFF REQUIRED` 与 `Counts:` 不再要 worker 手算再核对，`--closeout`（含 `--check-only`）照草稿里的 `ABANDON:` 行自己写，`draft_problems` 本来就用 `tally()` 重算并拒绝不一致，第 7 步与 Done when 都不再提这两行。第 8 步的拒绝首行本身已经说了失败的是什么、去哪看其余问题，正文不复述；仓库 `checks` 失败时的机械下一步（改代码、跑那套 suite、commit、重跑第 4 步最终运行、再关票一次）也挪进那条拒绝的 stderr，正文只留一句判断：检查失败且失败的检查覆盖了本次合并带进来的某张票改过的代码，这个失败就是合并的，归 `resolving-merge-conflicts` 技能。`ABANDON` 三种 kind 那一段放在续跑表之后、第 1 步之前：第 1 步就用到它。第 4 步不启动 session。第 8 步不 archive agent；单票 `land <n>` 或批次 `advance` 才收 workspace 与 session，也没有单独关闭 pane 的步骤。`failed` 与 `stuck` 不设轮数门槛。以下几条只写在这里，正文不写：「tracker 由 closeout 关、不手动关」只在第 8 步写一次（`Never close the ticket or swap its labels yourself — a hook blocks the command`），「Once done」那一段不重复；重新提示后先再 claim 的理由是 `advance` 重派时收回 claim、第 8 步拒绝不归你的票；第 4 步没有修一轮，理由是第 1 步的自跑与第 3 步的 review fix 就是修的轮次；第 6 步只有命令，步骤顺序已经把它排在第 3 步之后；第 1 步 clean merge 变红那一句只点名 `resolving-merge-conflicts` 技能，它读什么写在那份技能里；第 1 步在"note each trade-off"之后加了一句，说清楚对面那一边在 MMW 里是什么：已经关票、`reverify` 会在 base branch 上重跑它判据的票，丢了它的行为不会当场失败，会在几小时后落到另一张没人在做的票上，而且 bounce 之后的重试不再有 reviewer；两边真的水火不容，是切票时漏了一条边，保留已落地的一边、对两张票一起开 `contract` 子票，跟写码规则里"一个文件一个时刻只有一个作者"的判断是同一条逻辑，来自 `resolving-merge-conflicts` 的定稿；第 1 步 `integrate` 的 exit 3 只写「照 stderr 做，每个取舍记进 `Decisions I made on my own`」，见 `## Integrate before the worker criteria`；第 1 步 `verify-ticket.py <n>` 的 exit 3 写成结束回合、`worker.queued` 叫醒后 ack 再跑，exit 4 不写，它的 stderr 自己说再跑；第 3、5、8 步各以一行 `Done when` 收尾（第 3 步：review comment 在票上，session 的状态不算，票内发现各有 fixed 或 `refuted:`，仍成立的票外发现各有 `finding` child；第 5 步：说得出对每个 **What to build** 的点和每条 baseline，分支在哪里跟着做，或收尾评论哪一行说它没做到；第 8 步：`--closeout` 退出 0）；第 5 步 Audit 本身也改了目的：不是重读全票、追每条 `EVIDENCE:`（`EVIDENCE:` 由脚本写进事件，这条完成标准不会失败，是一道走不完的手续），而是照用户早上读收尾评论那样，对着分支再读一遍票，查 **What to build** 每一点在产品里成立、每条 baseline 在适用之处被照做，查不到的写进收尾评论；`stuck` 不收产品运行中的人工步骤与连不上产品，那两种照 `ui-acceptance` 技能五条规则的第 3、4 条开 `fault` 并停下，一种情况只有一条路；第 3 步只说一次「One reviewer per round; after `reviewer.lost`, start another.」，正面写，续跑表各行不再重复这条；第 8 步的 landing 与不开 pull request 合成一句：main agent 落地，本会话跑 `land` 会停掉自己，不写 `dispatch.sh` 这个脚本名，「Nothing in this pipeline reads a pull request」的理由见 `## Closeout pushes the ticket branch, no pull request`。理由：worker 必须在 review fix 的最后一次 commit 后留下唯一的 final proof，closeout 只负责核验证据与改变 tracker 状态；session 生命周期属于 landing。上游改收尾时，保留这些规则、八步顺序、最终全量运行和 closeout 条件。 |
| 第 7 步的 `--draft` 那一句 | 我们改的：不给路径。见 `## 草稿落在仓库之外`。首行是 `ALL MET` 还是 `HANDOFF REQUIRED`、`Counts:` 这两行不再要 worker 自己填或重数：`--closeout`（含 `--check-only`）照草稿里的 `ABANDON:` 行自己算，`draft_problems` 本来就用 `tally()` 核对、算错就拒绝，worker 只管把每个 `ABANDON:` 行放到它的 criterion 下面。 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型自己就能调用 implement，所以两处一起删。上游若再带回来 → 仍然删 |
| frontmatter 的 `description` | 我们加的：上游那一句之后加 `Use when you were dispatched onto a ticket, or picked one up yourself.`，只写触发条件。模型自己调用它，描述就是它被选中的依据；认领、写码、收尾这些过程写在正文里，不进描述（`writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Descriptions`）。上游改那一句 → 收上游措辞，触发句保留 |
| `Use /tdd where possible, at pre-agreed seams.` | host 中立：改成 `` Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams. ``，即 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Hand-offs` 里的第一种写法（要词汇、就地照办）。句末加一段：`CHECK:` 点名了测试用例时，那个用例就是第一条红测试，写代码前先跑、看它为什么红；缺文件、import 错、用例名打错这几种红证明不了什么，只有因为行为还没写才红才算数。理由：流水线里没有别的环节能证明"这条测试能失败"——认领时的 baseline 跑在测试存在之前，review 的 Tests axis 只读不跑，来自 `tdd` 的定稿（该定稿把这句放在这里而不是 `tdd` 自己的正文，因为上游 `tdd` 有意不加强这一点）。上游改这一句 → 收上游措辞，斜杠调用照这种写法换掉，`CHECK:` 那段跟着这一句留在这里 |
| `## Claim, read in, write the code`、`## Closing steps` 两个标题 | 我们加的：两个标题让读者按标题找到开工段与收尾八步；没有它们，收尾八步落在 `## Shared experience while implementing` 底下。上游加标题 → 收上游的，这两个保留 |

## writing-interface-code.md

`references/writing-interface-code.md` 是新文件。理由：#447 第 8 节。`SKILL.md` 读入一步加一行指向它；文件开头一段说何时读它，以及界面票的两份基线各管哪一块（只有界面票用到，所以不放 `SKILL.md`），screen-contract 行对不上时 `contract` child 还要点名 alignment ticket（spec 出自 wayfinder map 时才有这张票；没有 map 的 spec 没有 alignment ticket，所以正文只在有 map 时要求点名）；内容：写代码前用 ui-acceptance 技能的 `uv run story-parity.py --contract … --pages … --render-only --out <mktemp 目录>` 取各 scene 的截图与每个 `data-ui` id 的文字、位置尺寸、样式值；`[data-story-root]` 放在组件自己的根上，该根带 design page 根上同一个 `data-ui` id，对应元素也带同一个 id；同一轮写 story adapter 与四列 boundary test，测试怎么命名、写好后跑一次 criterion 的 `--run` 确认恰好跑一个测试，指向 ui-acceptance 技能 `references/boundary-check.md` 的 `## Selecting one row's test`（这条规则 cutter 写 `--run`、worker 写测试都要用，只住那一处；worker 不读 `to-tickets` 的文件，名字不对时两遍都 exit 0，judge 报 `GREEN WITHOUT INTERACTION`，把 worker 引去改一条正确的断言）；design system 从代码同步时照抄 design page 上的产品类名；就地改是运行 → 读 `DIFF` 行 → 改 → 再运行，修的是行点名的 id 与属性，轮数与 `ABANDON:` 仍在 `SKILL.md` 收尾第 1 步；review 的 Spec axis 对本票某条 screen-contract 行报 `Missing` 时，收尾评论也要写出那个行 id（`--closeout` 查这一条），写在 `## Fix in place` 末尾；设计值明显可疑、改一处必然违背另一处、design page 缺控件或流转与合同对不上时，`verify-ticket.py <n> --sub-issue contract <file>`，正文第一行是 Claude Design 页面和站不住的值（它就是 child 的标题），下一行写「由 design-pages 的 pull 入口处理：在能调用 Claude Design MCP 工具的会话里，在 Claude Design 里改，再 pull」（worker 与夜里的主 agent 未必接了 Claude Design，这张 child 只能在白天由接了它的会话处理），其余引用站不住的原文和同一出处里仍成立的部分，design package 仍由 design-pages 的 pull 入口写，本票其余部分继续；一条代码路径按 story 说法：story 页的数据只来自 story adapter 读的 scene data，产品的请求路径不因数据来源、查询参数或构建开关换投影。

上游把界面写码规则写回 `SKILL.md` → 挪进这份文件，指针保留。上游改收尾第 1 步去解释 `DIFF` 行 → 那几句仍只住在这份文件。

## 草稿落在仓库之外

第 7 步只写 `verify-ticket.py <n> --draft`，不带 out-file，正文只说 `Give that run no path of your own.`。为什么不要自己挑路径只写在这里：草稿把票点名的每个文件名都写进去（收尾评论本来就该这么写），而第 8 步的 `--closeout` 会拿消费仓库自己的 `checks` 扫整个工作树——草稿落在树里就成了那些检查要读的又一个文件。

2026-09-11 `agentflow-hq/agentflow` 的 #831 撞上了：产品判据全绿、验收员也过了，票关不掉，挡住它的是它自己一分钟前写出的 `.mmw/closeout-831.md`——该仓库一条「文档不许提 reference 文件名」的守卫在草稿里读到了票中提到的两个文件名。只要消费仓库有任何一条扫自己 Markdown 的守卫，每一张这样的票都会被自己的草稿挡一次。

落点由 `verify-ticket.py` 自己选（`mktemp` 造的目录，不是 `/tmp` 下的固定名），并打印 `DRAFT: wrote <path>`；不落 `MMW_HOME` 的 state 目录，因为根 `AGENTS.md` 写明那里「不放一个字节的 ticket state」，而收尾草稿正是 ticket state。

上游改第 7 步 → 收上游措辞，但 `--draft` 后面不带 out-file 这一点保留。

## Reaching the two scripts

The claim and the closing steps write `verify-ticket.py` and `dispatch.sh` bare, each
named once by the skill that owns it (the `verify-ticket` and `dispatch` skills). None
of them writes a script path: the script lives inside the skill, so the agent already
holding that skill resolves it. Each run's refusal says what to do next, and
`verify-ticket.py --help` lists the exit codes. Upstream writes a path into any of these
steps → replace it with the bare script name.

## Waiting on the reviewer carries no number

A number in the skill text is a number a worker shrinks — one did, and skipped a
review comment its reviewer was still writing. Upstream brings a timeout number back →
drop it; the worker ends its turn and is woken, see `## How the worker learns its
reviewer is done` below.

## Closeout pushes the ticket branch, no pull request

Step 8 calls `--closeout`, which pushes `issue-<n>` to origin without force before it
closes the ticket, and opens no pull request. `worker.started.into` is the shared record
of which base branch the ticket branch belongs to. `dispatch.sh land` and `advance`
fetch origin and perform the merge, so a pull request would only be a second merge queue
that nothing in this pipeline reads.

The `Branch: … Commit: … PR: …` line stays, with `PR: none` and the reason that the main
agent will merge the ticket branch into `worker.started.into`. Upstream brings a
pull request or a worker-run push back → drop it. Keep the closeout-owned push and its
no-force rule.

## Integrate before the worker criteria

Closing step 1 begins with `dispatch.sh integrate <n>`, then runs the worker's criteria. A clean merge that turns the repository checks red also goes to `resolving-merge-conflicts`; that skill reads the merged tickets and their closeout evidence, and step 1 does not restate it.
It merges `origin/<base branch>` into the ticket branch with a fixed merge message,
so the worker that knows this ticket resolves conflicts and clean-merge regressions before
review and verification. Exit 2 becomes a `fault` when the pipeline itself failed. On
exit 3, `integrate` prints the incoming tickets, the conflicted files and the procedure
(`resolving-merge-conflicts`, the checks affected by those tickets, commit, run
`integrate` again) on stderr, which the worker reads at the moment it acts, so step 1 says
only to do what stderr says and to note each trade-off under `Decisions I made on my own`:
`resolving-merge-conflicts` step 3 says to note a trade-off and names no place. The
command never pushes, rebases or aborts. Step 1 keeps the worker-run command and says
what its exit 3 needs from the worker: end the turn, and on the `#<n> worker.queued` wake
ack it and run the same command again. The run used to wait up to 90 seconds inside the command and hand back 3
to be run again, which cost the worker a model turn every 90 seconds for as long as
slots stayed held; the relay now wakes it when a slot-ending event lands. Upstream
rewrites the first closing step → keep integration before the criteria and keep that
exit-3 sentence.

A sentence follows the trade-off instruction: the incoming side of this merge is closed
tickets whose criteria the closing pass's `reverify` runs again on the base branch, so a
resolution that drops their behaviour does not fail here, it reopens their ticket hours
later, and a bounce retry never starts a second reviewer, so nobody else checks the
resolution. Where the two sides truly cannot both hold, the cut missed an edge, same as
the **Owns** exception below: keep the landed side and open a `contract` child naming
both tickets, rather than the worker picking a side alone. From the `resolving-merge-conflicts`
skill's own review: no such incident has been found on record, but the mechanism (`reverify`
re-runs landed criteria, a bounce retry gets no reviewer) makes the risk real without one.
Upstream rewrites this sentence's neighbourhood → keep the reverify reason and the
`contract` route.

## A clean-merge regression surfaces only at closeout

`--closeout` is the only place that runs the repository's own `checks`; a clean merge
in step 1 does not run them. So a regression from combining two tickets that each
passed their own criteria alone surfaces only in step 8, after review, with no second
check on the fix. Step 8 now carries one judgement sentence: when the repository's
own checks fail and the failing check covers code an incoming ticket of your
integration changed, the failure is the merge's, and the worker uses
`resolving-merge-conflicts` rather than treating it as its own bug. The mechanical
next steps for an ordinary repository-checks failure (fix the code, run the suite,
commit, rerun step 4, close out again) moved into that refusal's own stderr, since
the moment to say them is the moment the refusal fires, not this skill's text.
`resolving-merge-conflicts`'s own review found no tracker record of this path firing
yet; it is a path normal inputs reach (two tickets each green alone, red together),
not over-defense. Upstream rewrites step 8 → keep the judgement sentence and leave
the ordinary-failure steps to the refusal.

## Put no question on the screen

One bullet in the writing rules. A worker that puts a question up gets no answer:
`tool-guard.py`'s `question` gate refuses the host's question tool in every dispatched session
(`MMW_AUTONOMOUS=1`), and the refusal points at the same two ways out. So the bullet says
what to do instead: take the option the ticket, its baselines and the spec make most likely, record it
under **Decisions I made on my own**, and carry on; a question whose answer would change
what the ticket delivers gets a sub-issue. The recording place and the sub-issue route are
here too — this bullet is the third part, the one that says not to ask. Upstream rewrites
the writing rules → keep the bullet.

## Closing steps: resume after a re-prompt

The main agent's `resume` sends a stopped worker `continue` and what it settled, nothing else, so the skill has to know it may be entering the closing steps mid-way. Which step that is, is a deterministic function of the ticket's own events (mmw #315): the worker's own run is a `ticket.checked` event whose `run` is `self`, not a comment whose first line is `self-run`, because nothing in the pipeline reads a comment's first line. A `ticket.returned` or `ticket.bounced` newer than the newest `ticket.passed` sends the worker back to step 1, then to step 4 onward without starting a second reviewer (the reviewer already judged the ticket's own diff; the worker must prove the integrated result with the final full run); a run of the worker's own with no `worker.decided` goes to step 2; the reviewer start, sleep, report and fix round of step 3 are told apart by `worker.decided`, `reviewer.reported` and `reviewer.lost`; a run newer than the review with no final reverify goes to step 4; a worker reverify on `HEAD` goes to step 5. A `repo-checks` `ticket.checked` result of `unmet` and a `worker.queued` do not move the worker along this table at all: they already have a home in step 8 and in step 1's exit 3.

The 2026-09-28 lightweight review moved this lookup out of `SKILL.md`, where it read as a 333-word table the worker had to look itself up in, and into `verify-ticket.py`'s `--preflight`, which prints a `RESUME: step <k> (<event>)` line after `READY:` once claimed. `SKILL.md` keeps one sentence: claim again first, then carry on at the step `RESUME:` names. The mapping above is unchanged; only where it is computed changed.

Upstream rewrites the "Once done" paragraph → take its wording, but keep the lookup in `--preflight`'s `RESUME:` line rather than putting a table back into the skill text.

## Every script name says which skill owns it

`references/writing-interface-code.md` names the render-only command as `uv run story-parity.py …`, run with the `ui-acceptance` skill's `story-parity.py`, named once. `SKILL.md` does not name that script. The worker does not resolve the script's path itself: it already holds the `ui-acceptance` skill, which resolves its own `scripts/` from its own `SKILL.md`. Upstream puts a path into this command → drop it back to the bare script name.

## Where a failing `story-parity.py` criterion is read

The two sentences that used to sit in closing step 1 live in `references/writing-interface-code.md` under **Fix in place**. That script prints one `DIFF` line per difference — a `data-ui` id, one property, its design and product values — and what those lines and `NEGATIVE CONTROL FAILED` mean is written only in the ui-acceptance skill's `references/story-parity.md`. The second sentence says to fix only the named id and property and run once more, and that the pixel difference image is evidence rather than a verdict to shrink: on ticket #548 of the chameleon repository a worker whose tree already matched spent sixteen parity runs changing fonts, line heights and renderer flags against a 1% pixel threshold, and abandoned the criterion. How many rounds a criterion gets, and the `ABANDON:` line, stay in `SKILL.md` closing step 1; the reference points at that step and does not repeat them. Upstream rewrites step 1 → keep the `DIFF` sentences in that reference, not in `SKILL.md`, and keep rounds and `ABANDON:` in step 1.

## Two baselines with separate jurisdictions, and one code path

The opening paragraph of `references/writing-interface-code.md` carries the split for an interface ticket, which only interface tickets read: the design package binds look and verbatim copy, the screen contract (`docs/specs/<effort>/screen-contract.yaml`, from the `write-screen-contract` skill) binds calls, shown values, transitions, failure and timing; a conflict on the contract's domain opens its sub-issue naming the wayfinder map's alignment ticket when the spec came from a map (a spec with no map has none). One code path lives in `references/writing-interface-code.md` in story terms: the story page's data comes only from the story adapter reading scene data, and no request path of the product chooses its projection by whether a data source is present, by a query parameter, or by a build switch. Reason: Chameleon's renderer carried a `scenario` path fed from fixtures beside a `live` path fed from the backend, and every worker satisfied the acceptance criteria on the first. If upstream rewrites the baseline bullet, take its wording in `SKILL.md`; keep the two baselines and one code path only in that reference.

## Writing rules open sub-issues through `--sub-issue`

Three kinds live in the writing rules: `contract` when the contract does not fit,
`deferred` when a change outside **Owns** is merely convenient, `decision` when a
question would change what the ticket delivers. Closing step 3 uses `finding`. The
paragraph after the read-in step uses `fault` (a fault in the pipeline's own scripts, a
hook, or `.mmw/target.json` — the file's body is the command it ran and the output it
saw, then stop; the full list of what counts lives in `verify-ticket`'s
`references/sub-issues.md`, so it is not repeated here), and so does step 3's `start`
that exits 2 (step 3 says so in place), except that a refusal whose stderr says to start
again (a tracker or Nowledge failure, a runner that did not start) is run once more first:
those refusals name that next step, and one event gets one instruction.
`references/writing-interface-code.md` uses `contract` when the design side is the
defect: the file's first line is the Claude Design page and the value that does not
hold (that line is the child issue's title); the next line names the `design-pages` skill's
`references/pull.md`; the rest quotes what does not hold and what in the same source still
holds. All five are parented to this ticket.
`Put no question on the screen` is still the leading sentence of that bullet.

The five were `baseline`, `outside-owns`, `review`, `decision` and `pipeline` until
mmw #315 section 3 renamed them after who can answer each child rather than where it
came from; `verify-ticket.py` refuses the old names, so a pull that brings one back
breaks the step that uses it. Upstream rewrites the writing rules → keep the bullet and
these five kinds, parented to the ticket.

## How the worker learns its reviewer is done

Step 3 is `dispatch.sh start <n> reviewer` followed by the end of the turn. The relay wakes the worker with `#<n> reviewer.reported`; the worker reads that event and acknowledges it. Step 4 is the worker final full run in the same session. Nothing is polled. Step 3 says this once, and its `Done when` line says the review comment is on the ticket and a session's state never is; no separate paragraph after step 3 restates it as a prohibition ("never wait on the reviewer, never ask whether it is done").

Upstream brings its own wait loop or a timeout back → drop it: a worker that loops on a command it cannot finish inside a shell timeout is the polling this pipeline removed (`docs/adr/0010-agents-are-woken-not-polled.md`, whose mechanism `docs/adr/0020-wakes-come-from-the-board.md` replaced).

## An earlier worker's unfinished commits

One paragraph after the claim paragraph: the branch may carry an earlier worker's commits, among them `wip(#<n>): uncommitted work of …`. `dispatch.sh` makes that commit when a worker's session ended mid-turn (lost, suspended, replaced, retracted) and a new worker starts in the same worktree, or the worktree is archived; left uncommitted, those edits made the next `--preflight` refuse the worktree, and archiving deleted them. The paragraph tells the new worker the commit is the ticket's work, so it does not revert it as foreign. Upstream rewrites the opening → keep the paragraph.

## A ticket adopted outside a night lands by the user

A paragraph in the `dispatch` skill's `references/inside-a-ticket.md` under `## After the closeout`, which the adopting session reads before its claim; step 8 keeps only the main agent's landing, since a started worker never adopts. A session that adopted a ticket outside a night is the session its relay wakes, so no main agent exists to run `land`, and the relay `adopt` started runs until `land` stops it. The paragraph has the session ack its own `ticket.passed` or `ticket.returned` wake and hand `land <n>` to the user, and forbids that worker from running it because `land` stops every session the ticket's events name, the caller included. Upstream rewrites step 8 → keep the paragraph in `inside-a-ticket.md`, not in step 8.

### docs page

`mmw-v2/upstream/docs/engineering/implement.md` keeps the same behavior: the worker integrates `origin/<base branch>`, `--closeout` owns the push, and no pull request is created.

## This ticket's sub-issues

`Sub-issues opened:` on the closing-comment skeleton is this ticket's sub-issues
(`issues/<n>/sub_issues`), not the spec's children filtered by first line. The worker
also reads those open children at start of work, as a supplement to **What to build**.
Upstream puts `Sub-issues opened:` back under the spec → point it at the ticket.

## The in-ticket round is first, then out-of-ticket sub-issues

Closing step 3's internal order only. The eight closing steps stay in the same order. Inside step 3: the in-ticket round first (fix the in-ticket findings, re-run step 1's own run), then open out-of-ticket sub-issues; a finding whose body no longer holds is not opened.

Reason: the previous order opened the sub-issues from the review comment as written, so they were filed from text the in-ticket round then overturned (#235 is the instance: its body said to close the issue if a condition already held, and the in-ticket round had already made that condition hold).

If upstream rewrites step 3 → take its wording and put this internal order back. Do not reorder the eight steps.

## The design package is pulled, not downloaded

The read-yourself-in step listed `a handoff package downloaded from Claude Design`
among the baselines to read to their conclusion. ADR 0029 makes **pull** the only
writer of that package. `downloaded from Claude Design` points the worker
at the MCP tools, or at the "Handoff to Claude Code" export that
`design-pages/references/edit-pages.md` forbids, instead of at the committed
directory its own `## Read first` already names. It now reads `a design package
pulled into the repository`.

If upstream rewrites that sentence → take its wording and keep `pulled into the
repository`; do not take `downloaded from Claude Design` back.

## The story criterion is a declared exception to red before green

`references/writing-interface-code.md` under **Write the product** tells the
worker to write the component, then its story adapter and boundary tests, in one
pass. That is the mirror of `tdd`'s **Horizontal slicing** anti-pattern and runs
against its **Red before green**, and until #539 no file that covers writing
interface code named `tdd` at all, while `SKILL.md` still says to use it at pre-agreed seams. A
worker had two house disciplines and nothing to choose between them with, and
either choice could be called wrong by a review axis.

A paragraph now declares the exception in the house form `to-tickets` uses for
wide refactors: it names `tdd`, says the story criterion cannot run until the
component renders because element parity compares two rendered sides, and says
its expected values are not imagined, which is the thing `tdd`'s objection is
about, because they are the design side's values taken in the step before. Each
owned row's four-column boundary test stays its own red-green slice inside the
pass, at the seam the ticket's **Seam** names.

If upstream rewrites `tdd`'s loop rules → take its wording in `tdd`; keep this
exception, and keep its reason tied to element parity comparing rendered sides.

## A file a parallel ticket owns is never changed from here

The **Owns** bullet of the writing rules keeps its two grades (change a file outside
**Owns** when a criterion needs it; open `deferred` when the change is only convenient)
and adds one exception: a file owned by a ticket that can run beside this one, meaning
neither blocks the other directly or down a chain, is never changed from here, and the
worker opens a `contract` child instead.

The reason is the task-board pilot #541, cutting spec #555. `to-tickets` step 5 keeps
two tickets of one frontier from overlapping in **Owns**, so that two tickets running at
the same time never write one file; the worker-side rule let either of them write the
other's file anyway whenever a criterion needed it, which is the merge conflict the
**Owns** rule exists to prevent (a shared stylesheet was the case in hand). One rule now
holds in two places: `to-tickets` step 5 (a shared file is owned by one ticket and the
others are blocked by it) and this bullet; the `verify-ticket` skill's
`references/sub-issues.md` question 5 sends the worker to this bullet. A file owned by a ticket this one waits on, or by one that
waits on this one, can still be changed, and `--touched` still tells its owner.

If upstream rewrites the writing rules → take its wording; keep the exception and the
`contract` child it sends the worker to.

## A DIFF value is checked before it is copied

`references/writing-interface-code.md` **Fix in place** says that a `DIFF` line's id and property are the complete repair, and **When the design side is the defect**, placed after it, says that a clearly wrong design value is a `contract` child. Read in order, a worker had already copied the wrong value before it reached the second section. **Fix in place** now checks the design value first, against the same-role elements beside it and the design system's scale; a value that is clearly wrong goes to the `contract` child and is not copied. **When the design side is the defect** states the outcome: the criterion it blocks stays red, closing step 1 records it with an `ABANDON:` line of kind `stuck` pointing at that child (the kind for "cannot be done within the task", whose reason points at the sub-issue), and the ticket ends as `HANDOFF REQUIRED` for daytime, while the rest of the ticket continues. Reason: a walk of the real workflow in which a design page carried a wrong value; the text did not say which rule came first or how the ticket ends.

If upstream rewrites closing step 1 or the `ABANDON` kinds → take its wording and keep the order (check, then copy or open the child) and the red criterion ending the ticket as `HANDOFF REQUIRED`.
