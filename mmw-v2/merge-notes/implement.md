# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

这份技能的正文是本仓库自己的文本：拉上游时不合并进来，下面各行记的是每一段为什么这样写。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步跑 `verify-ticket` 技能的 `--preflight`，这一行只说它是第一步；为什么排第一（这条 pipeline 里没有别的东西 claim 票，第 8 步关不了不归你的票）只写在这里；分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、还拦着它的 blocker（未关的，或通过了而还没合并进基线的）、assignee 六项核对、六项全过由它 claim、打印 `NOT_READY` 就停，都住在那份技能的 `references/claiming.md`。六项逐项点名，是因为 `verify-ticket.py` 的 `refusals()` 就是这六条：worker 撞上标签或 assignee 那两条时，要认得出这是 preflight 的正常拒绝而不是脚本坏了。之后核对标题与 `## What to build` 描述同一个 vertical slice、`## Owns` 每条 glob 匹配现存路径或标 `(new)`，没有 `## Owns` 的旧票就从 `## Seam` 与 `## Parent` 指名小节推导并评论到票上。理由：claim 与开工前的核对是固定操作，交给脚本比写成正文指令可靠；旧票补齐 `## Owns` 才有写界。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 `Owns check` 保留。同一段末尾加一句：自己拿起票（不是被 `start` 起来）的会话在 claim 之前先跑 `<dispatch> adopt <n>`，让 `worker.started` 写上自己的 runner 与会话号、并确保有 relay 看守这张票；不跑，reviewer 的报告都叫不醒它，`start <n> reviewer` 也会拒绝。上游改开工段 → 这一句保留 |
| 「开写之前先读」那一段 | 我们改的：票读全、本票开着的 sub-issue（`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100`——不带 `--paginate` 只回第一页 30 条且不留标记，worker 会把看不见的子票当作不存在，当 `## What to build` 的补充，做与不做写进 `Decisions I made on my own`）→ `## Read first` 逐份读到结论（research 的末节、ADR 标题下那段无标题的决定、拉进仓库的 design package、prototype 叶子 `README.md` 读到它的 verdict），其中记录已拍板结论的条目是 baseline，`the baseline is the contract`，不是参考；两类 baseline 处理不同：design package 逐字照抄，prototype 按正式标准重写、保住 verdict 定下的形状 → 沿 `## Parent` 只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文 → 领域词汇表（根 `CONTEXT.md`，或 `CONTEXT-MAP.md` 列出、本票涉及的各 context 的 `CONTEXT.md`），它有对应的词就用那个词。多 context 的仓库根上没有 `CONTEXT.md`，只写「根 `CONTEXT.md`」的话 worker 要么跳过词汇表，要么读错一份。没有 `## Read first` 的旧票退回读 spec `## Sources` 全部。理由：整份 spec 会淹掉票指名的小节；baseline 的 contract 地位防默默偏离。prototype 那一项指向叶子 `README.md` 读到它的 verdict，与同一句里另外三项同构——四项都是打开就找得到的位置（research 文件的末节、ADR 的那一节、拉进仓库的整个目录、叶子 `README.md`）；照着哪一块写由 verdict 自己说，不必再写一条禁令去排除 HTML 外壳或 harness。两类 baseline 的差别不写出来，worker 会对着一个 prototype 的 variant 逐字抄，把原型阶段的粗糙一起抄进正式代码。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，`narrowed reading` 与 `the baseline is the contract` 保留 |
| `state the seam` 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时照 `tdd` 技能 `## Seams: where tests go` 推出。推导并先评论到票上这条规则只写在 `tdd` 那一段（见 [tdd.md](tdd.md)）：worker 两份都读，这里只指过去，不再写一遍。上游有同类要求 → 收上游，指向 `tdd` 的这半句保留 |
| `state the seam` 与 `/tdd` 之间的 writing rules 段 | 我们加的：一串动作——`## Read first` 里每条 baseline、`## Parent` 指名的 spec 小节和 ticket acceptance criteria 都是 contract（`the baseline is the contract`），值、文案、状态与接口形状从 baseline 抄而不是凭记忆重写；`the contract does not fit` 是任一份缺状态、字段、交互或用例、同一 domain 的两份互相矛盾，或 acceptance criterion 测不到它所说的行为。worker 对本票跑 `<engine> <n> --sub-issue contract <file>`，body 点名 AC、逐字引用错处、写同一依据里仍成立而必须保留的部分，继续不依赖它的工作；其中错的是 `CHECK` 时还写 expected correction。只有 main agent 或 user 改已发布 spec、ticket body 和 acceptance criterion，改好后 worker 才继续。不默默改 baseline、不默默绕过；过不了的检查用改代码或 abandon 那条 acceptance criterion 来答，不弯 baseline、不弯 the harness、不弯测试——这一款给的是正面动作接一句底线，而不是并排的第三个 never，且它指向的 abandon 就是同一份文件 closing steps 第 1 步的 `ABANDON: AC<n> failed`；改函数前 grep 每个调用方、修共用处，加分支或 guard 前先点名并删掉它让其多余的分支或文件；写 helper 前先在仓库与 `## Read first` 找现成；加文件、依赖、配置前说出已有的为何不够；安全、防数据丢失、无障碍与票里明确要的（`## What to build`、每条 acceptance criterion、baseline、`## Seam` 的接口）不许简化，正文用正面说法 `Whatever you simplify, keep intact:`；收尾写 `skipped: [X], add when [Y]`；`Owns two grades`——为过 acceptance criterion 不得不改的 `## Owns` 外文件照改、由 closing comment 的 `Outside Owns:` 记录，顺手想改的不改、对本票跑 `--sub-issue deferred`。同段还有 `Put no question on the screen`，见下方同名一节。措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效。上游加了写码期间的纪律段 → 收上游措辞，这些条并进去 |
| 读 `## Read first` 那一段末尾加一行：`## Read first` 列了 screen contract 时，读 `references/writing-interface-code.md` | 我们改的，来自 mmw #447 第 8 节。界面写码规则不写在 `SKILL.md`。上游改读入段 → 收上游措辞，这一行保留 |
| writing rules 里不再放界面写码规则（`[data-story-root]` 与 `data-ui` id、story adapter 与四列 boundary test、一条代码路径） | 我们改的：这些句子从 writing rules 挪进 `references/writing-interface-code.md`，见下方同名一节。上游改 writing rules → 收上游措辞，这些句子仍只住在那份文件 |
| `Run typechecking regularly` 之后、「Once done」之前的测试范围段 | 我们加的。`tdd` 那一行、`Run typechecking regularly` 与这一段三段排在 `## Claim, read in, write the code` 末尾、写码规则之后：三段都是写码时的指引，放在 `## Shared experience while implementing` 底下，读者会把它们当成 Memory 那一节的内容。验证手段随意、scratch 脚本不必保留；只在票要求或仓库本来就为这类改动留测试时提交测试，规模比照相邻测试文件（每条声明的行为约一个测试）——临时检查因此不会成为永久测试文件，正文不另写这一句；这段只管多出来的东西，票要的每个行为仍要完整实现。来源是 Anthropic 的 `Prompting Claude Fable 5.1` 指南 `Keep changes and tests to what the task asks for` 一节：`Owns two grades` 管改动范围，这段补上测试文件数量。上游若加了同类约束 → 收上游措辞 |
| `## Shared experience while implementing` | 我们加的，来自 mmw #427 与 `docs/notes/stage-two-shared-experience-layer.md` 的第 4、5 节。一节讲完 worker 的全部 Memory 合同：派工给的五个环境值、首次 prompt 的两份索引（Current task shared experience、Related experience）与打开记录的 `memories show` 命令、两级精确 search command（搜索词只用报错、命令与组件，并以 `--` 隔开：Nowledge 对含有记录里没有的具体标识的搜索词整批不返回，对以 `-` 开头的搜索词当作选项解析）、三项同时成立的 capture gate、`MMW_TASK_SCOPE` 为空时不写、map/standalone labels、标题写组件与行为且 `证据` 写出涉及的仓库路径（下一名 worker 的 Related experience 按路径排序）、五项正文与可执行的 `nmem memories add --stdin` 命令、`learning`/`procedure`、安全排除、current evidence authority、`supersede`/`deprecate` 命令、写失败不挡工单。派工 prompt 只给数据并指向这一节，所以 worker 读到的规则只有这一份。`summary` 的 lifecycle 和 `retro` 的固定 id 写入由各自脚本负责，不教 worker 操作它们。上游改写码段或新增通用记忆步骤 → 收上游措辞，保留整节，命令与字段不概括 |
| 「Once done」之后的 closing steps | 我们改的：八步，顺序是 worker 自跑（`ticket.checked`，run `self`）→ DECISIONS → reviewer → worker 最终全量运行（`--reverify --actor worker`）→ Audit → `--touched` → `--draft` → `--closeout`。最终全量运行排在最后一个写 commit 的步骤之后，并重跑全部标准；closeout 只接受 actor 为 worker、commit 为 `HEAD`、shape 与票面一致且结果满足关票条件的最新 reverify。DECISIONS 排在 reviewer 之前：Spec axis 要对 DECISIONS 的每一行给 `reasonable` 或 `should not`，`--touched` 也从 review 里取这个判断，评论晚于 review 就永远没有东西可判；review 修一轮里新做的决定不补进 DECISIONS，由收尾评论带最终版。第 3 步 `start <n> reviewer` 不带开关，启动后结束回合，由 relay 在 `reviewer.reported` 落票时叫醒；读事件后 `ack`。`start` 退出 2 是 pipeline fault：用 `<engine> <n> --sub-issue fault <file>` 记录后停止。票内发现不修的，写成 `refuted:`，判据照抄 BMAD `step-04-review.md`：查过、坏结果不在所引位置发生，写出反驳这条具体说法的依据。四个子命令 `--decisions`、`--touched`、`--draft`、`--closeout` 的行为与 exit code 留在 `verify-ticket` 的 `references/closeout.md`。第 4 步不启动 session。第 8 步不 archive agent；单票 `land <n>` 或批次 `advance` 才收 workspace 与 session，也没有单独关闭 pane 的步骤。`failed` 与 `stuck` 不设轮数门槛。以下几条只写在这里，正文不写：「tracker 由 closeout 关、不手动关」只在第 8 步写一次（`Never close the ticket or swap its labels yourself — a hook blocks the command`），「Once done」那一段不重复；重新提示后先再 claim 的理由是 `advance` 重派时收回 claim、第 8 步拒绝不归你的票；第 4 步没有修一轮，理由是第 1 步的自跑与第 3 步的 review fix 就是修的轮次；第 6 步只写「它读 review comment，所以第 3 步没做完就被拒」；第 1 步 clean merge 变红那一句只点名 `resolving-merge-conflicts` 技能，它读什么写在那份技能里；第 1 步 exit 3 只写「照 stderr 做，每个取舍记进 `Decisions I made on my own`」，见 `## Integrate before the worker criteria`；第 3、5、8 步各以一行 `Done when` 收尾（第 3 步：review comment 在票上，session 的状态不算，票内发现各有 fixed 或 `refuted:`，仍成立的票外发现各有 `finding` child；第 5 步：说得出每条 criterion 最新的 `EVIDENCE:` 行，和 `## Read first` 每一项在分支里落在哪；第 8 步：`--closeout` 退出 0）；`stuck` 不收产品运行中的人工步骤与连不上产品，那两种照 `ui-acceptance` 技能五条规则的第 3、4 条开 `fault` 并停下，一种情况只有一条路；第 3 步只说一次「One reviewer per round; after `reviewer.lost`, start another.」，正面写，续跑表各行不再重复这条；第 8 步的 landing 与不开 pull request 合成一句，`land <n>` / `advance` 只写一次，不写 `dispatch.sh` 这个脚本名，「Nothing in this pipeline reads a pull request」的理由见 `## Closeout pushes the ticket branch, no pull request`。理由：worker 必须在 review fix 的最后一次 commit 后留下唯一的 final proof，closeout 只负责核验证据与改变 tracker 状态；session 生命周期属于 landing。上游改收尾时，保留这些规则、八步顺序、最终全量运行和 closeout 条件。 |
| 第 7 步的 `--draft` 那一句 | 我们改的：不给路径。见 `## 草稿落在仓库之外`。`Counts:` 在这一步填完草稿之后重数：这一行由 `--draft` 写出，第 5 步 Audit 时还不存在，而 worker 补进草稿的 `ABANDON:` 行会改变它。 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型自己就能调用 implement，所以两处一起删。上游若再带回来 → 仍然删 |
| frontmatter 的 `description` | 我们加的：上游那一句之后加 `Use when you were dispatched onto a ticket, or picked one up yourself.`，只写触发条件。模型自己调用它，描述就是它被选中的依据；认领、写码、收尾这些过程写在正文里，不进描述（`writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Descriptions`）。上游改那一句 → 收上游措辞，触发句保留 |
| `Use /tdd where possible, at pre-agreed seams.` | host 中立：改成 `` Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams. ``，即 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Hand-offs` 里的第一种写法（要词汇、就地照办）。上游改这一句 → 收上游措辞，斜杠调用照这种写法换掉 |
| `` ## Resolve `<engine>` and `<dispatch>` once ``、`## Claim, read in, write the code`、`## Closing steps` 三个标题 | 我们加的：`<engine>` 与 `<dispatch>` 在第一次使用（认领段的 `<dispatch> adopt`）之前、在一个固定形状的 `## Resolve … once` 节里定义一次，写明路径随机器与 host 不同；原来这两句在写码规则前一段，已经晚于第一次使用。另两个标题让读者按标题找到开工段与收尾八步：没有它们，收尾八步落在 `## Shared experience while implementing` 底下。上游加标题 → 收上游的，这三个保留 |

## writing-interface-code.md

`references/writing-interface-code.md` 是新文件。理由：#447 第 8 节。`SKILL.md` 读入一步加一行指向它；文件开头一段只说何时读它、两份基线在 `SKILL.md`；接着一次定义 `<ui-acceptance scripts>`（ui-acceptance 技能的 `scripts/`，从那个技能的 `SKILL.md` 解析）。内容：写代码前用 `uv run <ui-acceptance scripts>/story-parity.py --contract … --pages … --render-only --out <mktemp 目录>` 取各 scene 的截图与每个 `data-ui` id 的文字、位置尺寸、样式值；`[data-story-root]` 放在组件自己的根上，该根带 design page 根上同一个 `data-ui` id，对应元素也带同一个 id；同一轮写 story adapter 与四列 boundary test；design system 从代码同步时照抄 design page 上的产品类名；就地改是运行 → 读 `DIFF` 行 → 改 → 再运行，修的是行点名的 id 与属性，轮数与 `ABANDON:` 仍在 `SKILL.md` 收尾第 1 步；设计值明显可疑、改一处必然违背另一处、design page 缺控件或流转与合同对不上时，`<engine> <n> --sub-issue contract <file>`，正文第一行是 Claude Design 页面和站不住的值（它就是 child 的标题），下一行写「由 design-pages 的 pull 入口处理：在能调用 Claude Design MCP 工具的会话里，在 Claude Design 里改，再 pull」（worker 与夜里的主 agent 未必接了 Claude Design，这张 child 只能在白天由接了它的会话处理），其余引用站不住的原文和同一出处里仍成立的部分，design package 仍由 design-pages 的 pull 入口写，本票其余部分继续；一条代码路径按 story 说法：story 页的数据只来自 story adapter 读的 scene data，产品的请求路径不因数据来源、查询参数或构建开关换投影。两份基线的分工仍在 `SKILL.md`。

上游把界面写码规则写回 `SKILL.md` → 挪进这份文件，指针保留。上游改收尾第 1 步去解释 `DIFF` 行 → 那几句仍只住在这份文件。

## 草稿落在仓库之外

第 7 步只写 `<engine> <n> --draft`，不带 out-file，正文只说 `Give that run no path of your own.`。为什么不要自己挑路径只写在这里：草稿把票点名的每个文件名都写进去（收尾评论本来就该这么写），而第 8 步的 `--closeout` 会拿消费仓库自己的 `checks` 扫整个工作树——草稿落在树里就成了那些检查要读的又一个文件。

2026-09-11 `agentflow-hq/agentflow` 的 #831 撞上了：产品判据全绿、验收员也过了，票关不掉，挡住它的是它自己一分钟前写出的 `.mmw/closeout-831.md`——该仓库一条「文档不许提 reference 文件名」的守卫在草稿里读到了票中提到的两个文件名。只要消费仓库有任何一条扫自己 Markdown 的守卫，每一张这样的票都会被自己的草稿挡一次。

落点由 `verify-ticket.py` 自己选（`mktemp` 造的目录，不是 `/tmp` 下的固定名），并打印 `DRAFT: wrote <path>`；不落 `MMW_HOME` 的 state 目录，因为根 `AGENTS.md` 写明那里「不放一个字节的 ticket state」，而收尾草稿正是 ticket state。

上游改第 7 步 → 收上游措辞，但 `--draft` 后面不带 out-file 这一点保留。

## Reaching the two scripts

The closeout and the preflight name the `verify-ticket` skill and the run they
want; step 4 names the `dispatch` skill. None of them writes a script path. The script
lives inside the skill, so the skill is what resolves it, from its own `SKILL.md`'s
location: that is right on all five hosts, and it keeps installing the skill and having
the script the same event. Naming the skill also puts the exit codes and the refusal
table in front of the worker at the moment it runs the command, which a path does not.
Upstream writes a path into any of these steps → replace it with the skill and the run.

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

Closing step 1 begins with `<dispatch> integrate <n>`, then runs the worker's criteria. A clean merge that turns the repository checks red also goes to `resolving-merge-conflicts`; that skill reads the merged tickets and their closeout evidence, and step 1 does not restate it.
It merges `origin/<base branch>` into the ticket branch with a fixed merge message,
so the worker that knows this ticket resolves conflicts and clean-merge regressions before
review and verification. Exit 2 becomes a `fault` when the pipeline itself failed. On
exit 3, `integrate` prints the incoming tickets, the conflicted files and the procedure
(`resolving-merge-conflicts`, the checks affected by those tickets, commit, run
`integrate` again) on stderr, which the worker reads at the moment it acts, so step 1 says
only to do what stderr says and to note each trade-off under `Decisions I made on my own`:
`resolving-merge-conflicts` step 3 says to note a trade-off and names no place. The
`dispatch` skill's `references/inside-a-ticket.md` row for `integrate` points to step 1
and states no exit code. The command never pushes, rebases or aborts. Step 1 keeps the worker-run command and points its exit 3 to
`verify-ticket/references/running-criteria.md` under **A criterion that runs the
product**. The run used to wait up to 90 seconds inside the command and hand back 3
to be run again, which cost the worker a model turn every 90 seconds for as long as
slots stayed held; the relay now wakes it when a slot-ending event lands. Upstream
rewrites the first closing step → keep integration before the criteria and keep that
pointer.

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

A table added to the "Once done" paragraph, one row per state the ticket's own comments can be in, saying which closing step to resume at. The main agent's `resume` sends a stopped worker `continue` and what it settled, nothing else, so the skill has to know it may be entering the closing steps mid-way.

The resume table sends a worker with a run of its own and no `worker.decided` to step 2, distinguishes the reviewer start, sleep, report and fix round of step 3, then sends a worker whose run is newer than the review and that has no final reverify to step 4, and a worker reverify on `HEAD` to step 5. A `ticket.returned`, or a `ticket.bounced`, newer than the newest `ticket.passed` returns to step 1, then integrates the latest base and continues at step 4 without starting a second reviewer (a returned ticket that triage sent back to `ready-for-agent` is restarted carrying its `worker.decided`, `reviewer.reported` and worker reverify, which no other row matches; `--decisions` refuses a second run): the reviewer already judged the ticket's own diff, while the worker must prove the integrated result with the final full run. Every condition is read from ticket events, never session state.

A `reviewer.lost` after the newest reviewer start sends the worker back to that step start; without it the worker would sleep on a reviewer that will never report.

Every row is an event the ticket carries (mmw #315): the worker's own run is a `ticket.checked` event whose `run` is `self`, not a comment whose first line is `self-run` — nothing in the pipeline reads a comment's first line, so a table keyed on one would match nothing the scripts write. The paragraph after the table lists the events that do not move the worker: `worker.touched`, a `repo-checks` `ticket.checked` whose result is `unmet`, `worker.queued`, and `ticket.refused`. For the `repo-checks` and `worker.queued` events it points to the `verify-ticket` reference that says what to do (`references/closeout.md`, `references/running-criteria.md`): that is the file the worker holds when the event first arrives, so the instruction has one home there.

Upstream rewrites the "Once done" paragraph → take its wording and put the table back, rows and all, keyed on events.

## Every script name says which skill owns it

`references/writing-interface-code.md` names the render-only command as `uv run <ui-acceptance scripts>/story-parity.py …`; the token is the `ui-acceptance` skill's `scripts/`, resolved from that skill's own `SKILL.md`. `SKILL.md` does not name that script. A bare script name is a name the worker cannot turn into a path: `install.sh` puts the skill wherever the host reads its skills from, and that differs by machine and by host. Upstream puts a bare script name in `SKILL.md` or in this reference → keep the token.

## Where a failing `story-parity.py` criterion is read

The two sentences that used to sit in closing step 1 live in `references/writing-interface-code.md` under **Fix in place**. That script prints one `DIFF` line per difference — a `data-ui` id, one property, its design and product values — and what those lines and `NEGATIVE CONTROL FAILED` mean is written only in the ui-acceptance skill's `references/story-parity.md`. The second sentence says to fix only the named id and property and run once more, and that the pixel difference image is evidence rather than a verdict to shrink: on ticket #548 of the chameleon repository a worker whose tree already matched spent sixteen parity runs changing fonts, line heights and renderer flags against a 1% pixel threshold, and abandoned the criterion. How many rounds a criterion gets, and the `ABANDON:` line, stay in `SKILL.md` closing step 1; the reference points at that step and does not repeat them. Upstream rewrites step 1 → keep the `DIFF` sentences in that reference, not in `SKILL.md`, and keep rounds and `ABANDON:` in step 1.

## Two baselines with separate jurisdictions, and one code path

The baseline bullet under "While writing code" still carries the split for an interface ticket: the design package binds look and verbatim copy, the screen contract (`docs/specs/<effort>/screen-contract.yaml`, from the `write-screen-contract` skill) binds calls, shown values, transitions, failure and timing; a conflict on the contract's domain opens its sub-issue naming the alignment ticket. One code path lives in `references/writing-interface-code.md` in story terms: the story page's data comes only from the story adapter reading scene data, and no request path of the product chooses its projection by whether a data source is present, by a query parameter, or by a build switch. Reason: Chameleon's renderer carried a `scenario` path fed from fixtures beside a `live` path fed from the backend, and every worker satisfied the acceptance criteria on the first. If upstream rewrites that section, take its wording, put the two baselines back in `SKILL.md`, and keep one code path only in that reference.

## Writing rules open sub-issues through `--sub-issue`

Three kinds live in the writing rules: `contract` when the contract does not fit,
`deferred` when a change outside **Owns** is merely convenient, `decision` when a
question would change what the ticket delivers. Closing step 3 uses `finding`. The
paragraph after the seam sentence uses `fault` (a fault in `verify-ticket.py`,
`dispatch.sh`, a judge script, `lease.py`, a hook, `.mmw/target.json` — the file's body
is the command it ran and the output it saw, then stop), and so does step 3's `start`
that exits 2 (step 3 sends the worker to the `dispatch` skill's
`references/inside-a-ticket.md` **Exit codes**).
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

Step 3 is `<dispatch> start <n> reviewer` followed by the end of the turn. The relay wakes the worker with `#<n> reviewer.reported`; the worker reads that event and acknowledges it. Step 4 is the worker final full run in the same session. Nothing is polled. Step 3 says this once, and its `Done when` line says the review comment is on the ticket and a session's state never is; no separate paragraph after step 3 restates it as a prohibition ("never wait on the reviewer, never ask whether it is done").

Upstream brings its own wait loop or a timeout back → drop it: a worker that loops on a command it cannot finish inside a shell timeout is the polling this pipeline removed (`docs/adr/0010-agents-are-woken-not-polled.md`, whose mechanism `docs/adr/0020-wakes-come-from-the-board.md` replaced).

## An earlier worker's unfinished commits

One paragraph after the claim paragraph: the branch may carry an earlier worker's commits, among them `wip(#<n>): uncommitted work of …`. `dispatch.sh` makes that commit when a worker's session ended mid-turn (lost, suspended, replaced, retracted) and a new worker starts in the same worktree, or the worktree is archived; left uncommitted, those edits made the next `--preflight` refuse the worktree, and archiving deleted them. The paragraph tells the new worker the commit is the ticket's work, so it does not revert it as foreign. Upstream rewrites the opening → keep the paragraph.

## A ticket adopted outside a night lands by the user

One sentence at the end of step 8. A session that adopted a ticket outside a night is the session its relay wakes, so no main agent exists to run `land`, and the relay `adopt` started runs until `land` stops it. The sentence has the session ack its own `ticket.passed` or `ticket.returned` wake and hand `land <n>` to the user, and forbids that worker from running it because `land` stops every session the ticket's events name, the caller included. Upstream rewrites step 8 → keep the sentence.

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
holds in three places: `to-tickets` step 5 (a shared file is owned by one ticket and the
others are blocked by it), the `verify-ticket` skill's `references/sub-issues.md`
question 5, and this bullet. A file owned by a ticket this one waits on, or by one that
waits on this one, can still be changed, and `--touched` still tells its owner.

If upstream rewrites the writing rules → take its wording; keep the exception and the
`contract` child it sends the worker to.

## A DIFF value is checked before it is copied

`references/writing-interface-code.md` **Fix in place** says that a `DIFF` line's id and property are the complete repair, and **When the design side is the defect**, placed after it, says that a clearly wrong design value is a `contract` child. Read in order, a worker had already copied the wrong value before it reached the second section. **Fix in place** now checks the design value first, against the same-role elements beside it and the design system's scale; a value that is clearly wrong goes to the `contract` child and is not copied. **When the design side is the defect** states the outcome: the criterion it blocks stays red, closing step 1 records it with an `ABANDON:` line of kind `stuck` pointing at that child (the kind for "cannot be done within the task", whose reason points at the sub-issue), and the ticket ends as `HANDOFF REQUIRED` for daytime, while the rest of the ticket continues. Reason: a walk of the real workflow in which a design page carried a wrong value; the text did not say which rule came first or how the ticket ends.

If upstream rewrites closing step 1 or the `ABANDON` kinds → take its wording and keep the order (check, then copy or open the child) and the red criterion ending the ticket as `HANDOFF REQUIRED`.
