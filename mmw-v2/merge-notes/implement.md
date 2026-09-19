# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步跑 `verify-ticket` 技能的 `--preflight`，这一行只说它是第一步与它为什么在这里；分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、还拦着它的 blocker（未关的，或通过了而还没合并进基线的）、assignee 六项核对、六项全过由它 claim、打印 `NOT_READY` 就停，都住在那份技能的 `references/claiming.md`。六项逐项点名，是因为 `verify-ticket.py` 的 `refusals()` 就是这六条：worker 撞上标签或 assignee 那两条时，要认得出这是 preflight 的正常拒绝而不是脚本坏了。之后核对标题与 `## What to build` 描述同一个 vertical slice、`## Owns` 每条 glob 匹配现存路径或标 `(new)`，没有 `## Owns` 的旧票就从 `## Seam` 与 `## Parent` 指名小节推导并评论到票上。理由：claim 与开工前的核对是固定操作，交给脚本比写成正文指令可靠；旧票补齐 `## Owns` 才有写界。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 `Owns check` 保留。同一段末尾加一句：自己拿起票（不是被 `start` 起来）的会话在 claim 之前先跑 `<dispatch> adopt <n>`，让 `worker.started` 写上自己的 runner 与会话号、并确保有 relay 看守这张票；不跑，reviewer 的报告都叫不醒它，`start <n> reviewer` 也会拒绝。上游改开工段 → 这一句保留 |
| 「开写之前先读」那一段 | 我们改的：票读全、本票开着的 sub-issue（`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100`——不带 `--paginate` 只回第一页 30 条且不留标记，worker 会把看不见的子票当作不存在，当 `## What to build` 的补充，做与不做写进 `Decisions I made on my own`）→ `## Read first` 逐份读到结论（research 的末节、ADR 标题下那段无标题的决定、从 Claude Design 下载的 handoff package、prototype 叶子 `README.md` 读到它的 verdict），其中记录已拍板结论的条目是 baseline，`the baseline is the contract`，不是参考；两类 baseline 处理不同：handoff package 逐字照抄，prototype 按正式标准重写、保住 verdict 定下的形状 → 沿 `## Parent` 只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文 → 根 `CONTEXT.md`。没有 `## Read first` 的旧票退回读 spec `## Sources` 全部。理由：整份 spec 会淹掉票指名的小节；baseline 的 contract 地位防默默偏离。prototype 那一项指向叶子 `README.md` 读到它的 verdict，与同一句里另外三项同构——四项都是打开就找得到的位置（research 文件的末节、ADR 的那一节、下载下来的整个目录、叶子 `README.md`）；照着哪一块写由 verdict 自己说，不必再写一条禁令去排除 HTML 外壳或 harness。两类 baseline 的差别不写出来，worker 会对着一个 prototype 的 variant 逐字抄，把原型阶段的粗糙一起抄进正式代码。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，`narrowed reading` 与 `the baseline is the contract` 保留 |
| `state the seam` 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时从 spec 的 Testing Decisions 推出并先评论到票上再动手。上游有同类要求 → 收上游，「先写回票」这条保留 |
| `state the seam` 与 `/tdd` 之间的 writing rules 段 | 我们加的：一串动作——`## Read first` 里每条 baseline、`## Parent` 指名的 spec 小节和 ticket acceptance criteria 都是 contract（`the baseline is the contract`），值、文案、状态与接口形状从 baseline 抄而不是凭记忆重写；`the contract does not fit` 是任一份缺状态、字段、交互或用例、同一 domain 的两份互相矛盾，或 acceptance criterion 测不到它所说的行为。worker 对本票跑 `<engine> <n> --sub-issue contract <file>`，body 点名 AC、逐字引用错处、写同一依据里仍成立而必须保留的部分，继续不依赖它的工作；其中错的是 `CHECK` 时还写 expected correction。只有 main agent 或 user 改已发布 spec、ticket body 和 acceptance criterion，改好后 worker 才继续。不默默改 baseline、不默默绕过；过不了的检查用改代码或 abandon 那条 acceptance criterion 来答，不弯 baseline、不弯 the harness、不弯测试——这一款给的是正面动作接一句底线，而不是并排的第三个 never，且它指向的 abandon 就是同一份文件 closing steps 第 1 步的 `ABANDON: AC<n> failed`；改函数前 grep 每个调用方、修共用处，加分支或 guard 前先点名并删掉它让其多余的分支或文件；写 helper 前先在仓库与 `## Read first` 找现成；加文件、依赖、配置前说出已有的为何不够；安全、防数据丢失、无障碍与票里明确要的（`## What to build`、每条 acceptance criterion、baseline、`## Seam` 的接口）不许简化；收尾写 `skipped: [X], add when [Y]`；`Owns two grades`——为过 acceptance criterion 不得不改的 `## Owns` 外文件照改、由 closing comment 的 `Outside Owns:` 记录，顺手想改的不改、对本票跑 `--sub-issue deferred`。同段还有 `Put no question on the screen`，见下方同名一节。措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效。上游加了写码期间的纪律段 → 收上游措辞，这些条并进去 |
| 读 `## Read first` 那一段末尾加「目标树」一段（照 `targets/<page>.aria` 与 `.classes` 写，再跑判据；`--render-only` 看设计侧）；writing rules 里「一条代码路径」改成目标无关的表述（任何请求路径不得按数据源在不在、按查询参数、按构建开关选投影），并加「每个表面组件的根带 `data-screen="<mount>"`，谁建谁带」一条 | 我们改的，来自 mmw #115。原句是 Electron/SPA 形状的特例；老板控制台的服务端在 `hasattr(db_pool)` 分支下渲染预览投影，同一条纪律要能抓住它，而且在服务端渲染目标上它是让 `observe` 有意义的前提。目标树前置一次，判据从「审判」变成「规格」。上游改这两处 → 收上游措辞，这两条保留 |
| writing rules 里 `data-screen` 那条之后加一句：写展示组件的同时写它的 story adapter 与边界测试 | 我们加的，来自 mmw #216 第 8 节。上游改 writing rules → 收上游措辞，这一句保留 |
| `Run typechecking regularly` 之后、「Once done」之前的测试范围段 | 我们加的：验证手段随意、scratch 脚本不必保留；只在票要求或仓库本来就为这类改动留测试时提交测试，规模比照相邻测试文件（每条声明的行为约一个测试），不把临时检查变成永久测试文件；这段只管多出来的东西，票要的每个行为仍要完整实现。来源是 Anthropic 的 `Prompting Claude Fable 5.1` 指南 `Keep changes and tests to what the task asks for` 一节：`Owns two grades` 管改动范围，这段补上测试文件数量。上游若加了同类约束 → 收上游措辞 |
| `## Shared experience while implementing` | 我们加的，来自 mmw #427 与 `docs/notes/stage-two-shared-experience-layer.md` 的第 4、5 节。一节讲完 worker 的全部 Memory 合同：派工给的五个环境值、首次 prompt 的两份索引（Current task shared experience、Related experience）与打开记录的 `memories show` 命令、两级精确 search command（搜索词只用报错、命令与组件，并以 `--` 隔开：Nowledge 对含有记录里没有的具体标识的搜索词整批不返回，对以 `-` 开头的搜索词当作选项解析）、三项同时成立的 capture gate、`MMW_TASK_SCOPE` 为空时不写、map/standalone labels、标题写组件与行为且 `证据` 写出涉及的仓库路径（下一名 worker 的 Related experience 按路径排序）、五项正文与可执行的 `nmem memories add --stdin` 命令、`learning`/`procedure`、安全排除、current evidence authority、`supersede`/`deprecate` 命令、写失败不挡工单、结束报告。派工 prompt 只给数据并指向这一节，所以 worker 读到的规则只有这一份。`summary` 的 lifecycle 和 `retro` 的固定 id 写入由各自脚本负责，不教 worker 操作它们。上游改 `While writing code` 到 `/tdd` 之间的流程或新增通用记忆步骤 → 收上游措辞，保留整节，命令与字段不概括 |
| 「Once done」之后的 closing steps | 我们改的：八步，顺序是 worker 自跑（`ticket.checked`，run `self`）→ reviewer → DECISIONS → worker 最终全量运行（`--reverify --actor worker`）→ Audit → `--touched` → `--draft` → `--closeout`。最终全量运行排在最后一个写 commit 的步骤之后，并重跑全部标准；closeout 只接受 actor 为 worker、commit 为 `HEAD`、shape 与票面一致且结果满足关票条件的最新 reverify。第 2 步 `start <n> reviewer` 不带开关，启动后结束回合，由 relay 在 `reviewer.reported` 落票时叫醒；读事件后 `ack`。`start` 退出 2 是 pipeline fault：用 `<engine> <n> --sub-issue fault <file>` 记录后停止。票内发现不修的，写成 `refuted:`，判据照抄 BMAD `step-04-review.md`：查过、坏结果不在所引位置发生，写出反驳这条具体说法的依据。四个子命令 `--decisions`、`--touched`、`--draft`、`--closeout` 的行为与 exit code 留在 `verify-ticket` 的 `references/closeout.md`。第 4 步不启动 session。第 8 步不 archive agent；单票 `land <n>` 或批次 `advance` 才收 workspace 与 session，也没有单独关闭 pane 的步骤。`failed` 与 `stuck` 不设轮数门槛。理由：worker 必须在 review fix 的最后一次 commit 后留下唯一的 final proof，closeout 只负责核验证据与改变 tracker 状态；session 生命周期属于 landing。上游改收尾时，保留这些规则、八步顺序、最终全量运行和 closeout 条件。 |
| 第 7 步的 `--draft` 那一句 | 我们改的：不给路径。见 `## 草稿落在仓库之外`。 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型自己就能调用 implement，所以两处一起删。上游若再带回来 → 仍然删 |

## 草稿落在仓库之外

第 7 步只写 `<engine> <n> --draft`，不带 out-file，并接一句说明为什么不要自己挑路径：草稿把票点名的每个文件名都写进去（收尾评论本来就该这么写），而第 8 步的 `--closeout` 会拿消费仓库自己的 `checks` 扫整个工作树——草稿落在树里就成了那些检查要读的又一个文件。

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

Closing step 1 begins with `<dispatch> integrate <n>`, then runs the worker's criteria.
It merges `origin/<base branch>` into the ticket branch with a fixed merge message,
so the worker that knows this ticket resolves conflicts and clean-merge regressions before
review and verification. Exit 3 uses `resolving-merge-conflicts`; exit 2 becomes a `fault`
when the pipeline itself failed. After a conflict is resolved, the worker runs the affected
checks, commits, and runs `<dispatch> integrate <n>` again. The command never pushes,
rebases or aborts. Step 1 keeps the worker-run command and points its exit 3 to
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

The resume table distinguishes the reviewer start, sleep, report and fix round, then sends a decided worker with no final reverify to step 4 and a worker reverify on `HEAD` to step 5. A newest `ticket.bounced` returns to step 1, then integrates the latest base and continues at step 4 without starting a second reviewer: the reviewer already judged the ticket's own diff, while the worker must prove the integrated result with the final full run. Every condition is read from ticket events, never session state.

A `reviewer.lost` after the newest reviewer start sends the worker back to that step start; without it the worker would sleep on a reviewer that will never report.

Every row is an event the ticket carries (mmw #315): the worker's own run is a `ticket.checked` event whose `run` is `self`, not a comment whose first line is `self-run` — nothing in the pipeline reads a comment's first line, so a table keyed on one would match nothing the scripts write. The paragraph after the table lists the events that do not move the worker: `worker.touched`, a `repo-checks` `ticket.checked` whose result is `unmet`, `worker.queued`, and `ticket.refused`.

Upstream rewrites the "Once done" paragraph → take its wording and put the table back, rows and all, keyed on events.

## Every script name says which skill owns it

Two places in the body named a script with no skill beside it, against this file's own `## Reaching the two scripts` rule: `story-parity.py --render-only` in the target-trees paragraph, and "that skill is where the line is read" in closing step 1, whose only antecedent was a script name. Both now name the `ui-acceptance` skill and the render-only one says to resolve `scripts/` from that skill's own SKILL.md. A bare script name is a name the worker cannot turn into a path: `install.sh` puts the skill wherever the host reads its skills from, and that differs by machine and by host. Upstream touches either sentence → keep the skill name.

## Where a failing `story-parity.py` criterion is read

Two sentences added to step 1 of the closing steps. That script prints a single `DIFF <scene> <viewport> <pct>% (unaligned <pct>%) — <reasons>` line; which reasons bring sub-lines out under them, and what `NEGATIVE CONTROL FAILED` means, are written only in the verify-ticket skill. Every other refusal in the closing steps explains itself in its own stderr, so this is the one place the worker has to be sent elsewhere. The second sentence says to fix only what the line names and run once more, not to chase the pixel share: on ticket #548 of the chameleon repository a worker whose tree already matched spent sixteen parity runs changing fonts, line heights and renderer flags against a 1% pixel threshold, and abandoned the criterion. Upstream rewrites step 1 → keep both sentences.

## Two baselines with separate jurisdictions, and one code path

Two things added under "While writing code". The baseline bullet gains the split for an interface ticket: the handoff package binds look and verbatim copy, the screen contract (`docs/specs/<effort>/screen-contract.yaml`, from the `align-screens` skill) binds calls, shown values, transitions, failure and timing; a conflict on the contract's domain opens its sub-issue naming the alignment ticket. A new bullet says an interface has one code path — data through the generated client, no prop that poses a component for a scene, fixtures only in the seed script. Reason: Chameleon's renderer carried a `scenario` path fed from fixtures beside a `live` path fed from the backend, and every worker satisfied the acceptance criteria on the first. If upstream rewrites that section, take its wording and put these two back.

## Writing rules open sub-issues through `--sub-issue`

Three kinds live in the writing rules: `contract` when the contract does not fit,
`deferred` when a change outside **Owns** is merely convenient, `decision` when a
question would change what the ticket delivers. Closing step 2 uses `finding`. The
paragraph that resolves `<engine>` uses `fault` (a fault in `verify-ticket.py`,
hook, driver, `.mmw/target.json` — the file's body is the command it ran and the
output it saw, then stop), and so does step 4's start that exits 2. All five are
parented to this ticket.
`Put no question on the screen` is still the leading sentence of that bullet.

The five were `baseline`, `outside-owns`, `review`, `decision` and `pipeline` until
mmw #315 section 3 renamed them after who can answer each child rather than where it
came from; `verify-ticket.py` refuses the old names, so a pull that brings one back
breaks the step that uses it. Upstream rewrites the writing rules → keep the bullet and
these five kinds, parented to the ticket.

## How the worker learns its reviewer is done

Step 2 is `<dispatch> start <n> reviewer` followed by the end of the turn. The relay wakes the worker with `#<n> reviewer.reported`; the worker reads that event and acknowledges it. Step 4 is the worker final full run in the same session. Nothing is polled.

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

Closing step 2's internal order only. The eight closing steps stay in the same order. Inside step 2: the in-ticket round first (fix the in-ticket findings, rerun step 1's own run), then open out-of-ticket sub-issues; a finding whose body no longer holds is not opened.

Reason: the previous order opened the sub-issues from the review comment as written, so they were filed from text the in-ticket round then overturned (#235 is the instance: its body said to close the issue if a condition already held, and the in-ticket round had already made that condition hold).

If upstream rewrites step 2 → take its wording and put this internal order back. Do not reorder the eight steps.
