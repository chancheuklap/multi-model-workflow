# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步跑 `verify-ticket` 技能的 `--preflight`——分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、未关的 blocker、assignee 六项核对，六项全过由它 claim；打印 `NOT_READY` 就停，原因已由脚本评论到票上，不再写第二遍。六项逐项点名，是因为 `verify-ticket.py` 的 `refusals()` 就是这六条：worker 撞上标签或 assignee 那两条时，要认得出这是 preflight 的正常拒绝而不是脚本坏了。之后核对标题与 `## What to build` 描述同一个 vertical slice、`## Owns` 每条 glob 匹配现存路径或标 `(new)`，没有 `## Owns` 的旧票就从 `## Seam` 与 `## Parent` 指名小节推导并评论到票上。理由：claim 与开工前的核对是固定操作，交给脚本比写成正文指令可靠；旧票补齐 `## Owns` 才有写界。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 `Owns check` 保留 |
| 「开写之前先读」那一段 | 我们改的：票读全、本票开着的 sub-issue（`gh api repos/{owner}/{repo}/issues/<n>/sub_issues`，当 `## What to build` 的补充，做与不做写进 `Decisions I made on my own`）→ `## Read first` 逐份读到结论（research 的末节、ADR 的 Decision、从 Claude Design 下载的 handoff package、prototype 叶子 `README.md` 读到它的 verdict），其中记录已拍板结论的条目是 baseline，`the baseline is the contract`，不是参考；两类 baseline 处理不同：handoff package 逐字照抄，prototype 按正式标准重写、保住 verdict 定下的形状 → 沿 `## Parent` 只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文 → 根 `CONTEXT.md`。没有 `## Read first` 的旧票退回读 spec `## Sources` 全部。理由：整份 spec 会淹掉票指名的小节；baseline 的 contract 地位防默默偏离。prototype 那一项指向叶子 `README.md` 读到它的 verdict，与同一句里另外三项同构——四项都是打开就找得到的位置（research 文件的末节、ADR 的那一节、下载下来的整个目录、叶子 `README.md`）；照着哪一块写由 verdict 自己说，不必再写一条禁令去排除 HTML 外壳或 harness。两类 baseline 的差别不写出来，worker 会对着一个 prototype 的 variant 逐字抄，把原型阶段的粗糙一起抄进正式代码。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，`narrowed reading` 与 `the baseline is the contract` 保留 |
| `state the seam` 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时从 spec 的 Testing Decisions 推出并先评论到票上再动手。上游有同类要求 → 收上游，「先写回票」这条保留 |
| `state the seam` 与 `/tdd` 之间的 writing rules 段 | 我们加的：一串动作——`## Read first` 里每条 baseline 是 contract（`the baseline is the contract`），值、文案、状态与接口形状从 baseline 抄而不是凭记忆重写，`the contract does not fit`（缺状态、字段、交互或用例，或两条 baseline 矛盾）就对本票跑 `<engine> <n> --sub-issue baseline <file>`，不默默改 baseline、不默默绕过；过不了的检查用改代码或 abandon 那条 acceptance criterion 来答，不弯 baseline、不弯 the harness、不弯测试——这一款给的是正面动作接一句底线，而不是并排的第三个 never，且它指向的 abandon 就是同一份文件 closing steps 第 1 步的 `ABANDON: AC<n> failed`；改函数前 grep 每个调用方、修共用处，加分支或 guard 前先点名并删掉它让其多余的分支或文件；写 helper 前先在仓库与 `## Read first` 找现成；加文件、依赖、配置前说出已有的为何不够；安全、防数据丢失、无障碍与票里明确要的（`## What to build`、每条 acceptance criterion、baseline、`## Seam` 的接口）不许简化；收尾写 `skipped: [X], add when [Y]`；`Owns two grades`——为过 acceptance criterion 不得不改的 `## Owns` 外文件照改、由 closing comment 的 `Outside Owns:` 记录，顺手想改的不改、对本票跑 `--sub-issue outside-owns`。同段还有 `Put no question on the screen`，见下方同名一节。措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效。上游加了写码期间的纪律段 → 收上游措辞，这些条并进去 |
| 读 `## Read first` 那一段末尾加「目标树」一段（照 `targets/<page>.aria` 与 `.classes` 写，再跑判据；`--render-only` 看设计侧）；writing rules 里「一条代码路径」改成目标无关的表述（任何请求路径不得按数据源在不在、按查询参数、按构建开关选投影），并加「每个表面组件的根带 `data-screen="<mount>"`，谁建谁带」一条 | 我们改的，来自 mmw #115。原句是 Electron/SPA 形状的特例；老板控制台的服务端在 `hasattr(db_pool)` 分支下渲染预览投影，同一条纪律要能抓住它，而且在服务端渲染目标上它是让 `observe` 有意义的前提。目标树前置一次，判据从「审判」变成「规格」。上游改这两处 → 收上游措辞，这两条保留 |
| `Run typechecking regularly` 之后、「Once done」之前的测试范围段 | 我们加的：验证手段随意、scratch 脚本不必保留；只在票要求或仓库本来就为这类改动留测试时提交测试，规模比照相邻测试文件（每条声明的行为约一个测试），不把临时检查变成永久测试文件；这段只管多出来的东西，票要的每个行为仍要完整实现。来源是 Anthropic 的 `Prompting Claude Fable 5.1` 指南 `Keep changes and tests to what the task asks for` 一节：`Owns two grades` 管改动范围，这段补上测试文件数量。上游若加了同类约束 → 收上游措辞 |
| 「Once done」之后的 closing steps | 我们改的：八步。`self-run`（`<engine> <n>`，写完码那一条 run；一条 acceptance criterion 试几轮由 worker 自己判断，closeout 不数轮次，`ABANDON: AC<n> failed` 那一行写清每轮试了什么）→ `<dispatch> start <n> verifier`，`create_agent` 之后在 shell 里 `paseo wait <id>` 再读首行 `VERDICT`，把打印出的 `initialPrompt` 原样传（`verify #<n> 按 <path> 行事`），只 start 一次；verifier 是 Paseo agent，`start` 是唯一起法，host 的 `spawn_subagent` / `Agent` 不能替代——换不了 provider，Paseo 也看不见它；start 退出 2 是流水线故障，`<engine> <n> --sub-issue pipeline <file>` 然后停 → `<engine> <n> --decisions <file>` 留一条 `DECISIONS`（一张票只留一条，review 后的修一轮不再发）→ `<dispatch> start <n> reviewer`，`create_agent` 之后在 shell 里 `paseo wait <id>` 再读首行 `REVIEW `；start 退出 2 是流水线故障，`<engine> <n> --sub-issue pipeline <file>` 然后停；start 退出 2 之外的失败（通知 `errored` / `was closed` 且没有 `REVIEW `）不在这里写，`dispatch/SKILL.md` 的 `Find your command` reviewer 一行给兜底，第 4 步只指向那一行；in-ticket finding 修一轮并重跑第 1 步，out-of-ticket 的 `<engine> <n> --sub-issue review <file>`，不复审 → `Audit`（重读票与 `## Read first`，每条 acceptance criterion 追到 `EVIDENCE:`，重数 `Counts:`）→ `<engine> <n> --touched` → 只等人一句话的 criterion 写 `ABANDON: AC<n> decision` 并 `<engine> <n> --sub-issue decision <file>`，再 `<engine> <n> --draft <out-file>` 填两个 `<fill>`；`Sub-issues opened:` 是本票的 sub-issue → `<engine> <n> --closeout <draft>`，不 archive 任何 agent（archiving 是 merge 之后的 `advance`，workspace 一起）。派发只有 `create_agent` 一条（`dispatch/SKILL.md` `## One path: create_agent`），第 2、4 步只写命令和要读的首行。三个 `ABANDON` kind：`failed` 与 `stuck` 都不看轮次、都把票交回；`decision` 开 sub-issue 不挡 `ALL MET`。理由：关票是一道门不是一个动作；idle sessions 不花钱，所以没有关 pane 那一步；pull request 整步退场，见下方 `No pull request, and no push`。轮次既不设上限也不设下限。「第三轮就放弃」把还能修好的 criterion 变成 `HANDOFF REQUIRED`；「至少三轮」只让第一轮就确认修不了的 worker 再全量跑两轮。`Branch: … Commit: … PR: …` 三个值写一行、没有 pull request 时把理由接在 `PR: none` 后面。上游改收尾 → 收上游措辞，八步顺序、四个子命令、`start <n> verifier` 与 `start <n> reviewer` 不带开关、`paseo wait <id>` 在 `create_agent` 之后、第 2 步的 `spawn_subagent` 禁令、`--sub-issue pipeline` 然后停、第 4 步指向 `dispatch/SKILL.md` 的 reviewer 一行而不复述兜底、closeout 不 archive、没有关 pane 那一步、`failed` 与 `stuck` 都不看轮次、`--closeout`、`No pull request, and no push` 必须保留 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型自己就能调用 implement，所以两处一起删。上游若再带回来 → 仍然删 |

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
review comment its reviewer was still writing. Upstream brings a wait command or a
timeout number back → drop them; the wait is `paseo wait <id>` after `create_agent`,
see `## Block on paseo wait <id>` below.

## No pull request, and no push

Upstream's step 6 pushed the branch and opened a pull request. This pipeline opens
none, and the step is gone: nothing here reads a pull request — `code-review` takes its
diff from git, the verifier reads the ticket and the worktree, and the closeout
reads neither. What does read a branch is `dispatch.sh advance`, which merges it once the ticket
closes, on this machine, with no `gh` call at all, into the branch the main agent is on
when it runs `advance` — the branch it opened the night on, recorded at dispatch in
`git config branch.issue-<n>.mmw-base-branch`. `advance` does not read that record;
the skill text names it so the worker can write the `PR:` line. A pull request would
only be a second place to remember to merge and pull back from.

The `Branch: … Commit: … PR: …` line stays, with `PR: none — will be merged into <base
branch> by dispatch.sh advance`. It is written in the future tense on purpose: the
closing comment is written before the ticket closes, and the merge happens after.

Upstream brings the push or the pull request back → drop them again, and keep the
sentence saying which branch `advance` merges into and where that name is recorded.

## Put no question on the screen

One bullet in the writing rules. A worker that puts a question up gets no answer:
`hook.py`'s `question` gate refuses the host's question tool in every dispatched session
(`MMW_AUTONOMOUS=1`), and the refusal points at the same two ways out. So the bullet says
what to do instead: take the option the ticket, its baselines and the spec make most likely, record it
under **Decisions I made on my own**, and carry on; a question whose answer would change
what the ticket delivers gets a sub-issue. The recording place and the sub-issue route are
here too — this bullet is the third part, the one that says not to ask. Upstream rewrites
the writing rules → keep the bullet.

## Closing steps: resume after a re-prompt

One sentence added to the "Once done" paragraph: a ticket that already carries a `self-run`, `VERDICT`, `DECISIONS` or `REVIEW` comment is resumed at the step after the newest of them. The main agent's `resume` sends a stopped worker `continue` and what it settled, nothing else, so the skill has to know it may be entering the closing steps mid-way. On the next upstream pull keep this sentence with the closing steps.

## Where a failing `visual-parity.py` criterion is read

Two sentences added to step 1 of the closing steps. That script prints a single `DIFF <scene> <viewport> <pct>% box=… — <reasons>` line; which reasons bring sub-lines out under them, and what `NEGATIVE CONTROL FAILED` means, are written only in the verify-ticket skill. Every other refusal in the closing steps explains itself in its own stderr, so this is the one place the worker has to be sent elsewhere. The second sentence says to fix only what the line names and run once more, not to chase the pixel share: on ticket #548 of the chameleon repository a worker whose tree already matched spent sixteen parity runs changing fonts, line heights and renderer flags against a 1% pixel threshold, and abandoned the criterion. Upstream rewrites step 1 → keep both sentences.

## Two baselines with separate jurisdictions, and one code path

Two things added under "While writing code". The baseline bullet gains the split for an interface ticket: the handoff package binds look and verbatim copy, the screen contract (`docs/specs/<effort>/screen-contract.yaml`, from the `align-screens` skill) binds calls, shown values, transitions, failure and timing; a conflict on the contract's domain opens its sub-issue naming the alignment ticket. A new bullet says an interface has one code path — data through the generated client, no prop that poses a component for a scene, fixtures only in the seed script. Reason: Chameleon's renderer carried a `scenario` path fed from fixtures beside a `live` path fed from the backend, and every worker satisfied the acceptance criteria on the first. If upstream rewrites that section, take its wording and put these two back.

## Writing rules open sub-issues through `--sub-issue`

Three kinds live in the writing rules: `baseline` when the contract does not fit,
`outside-owns` when a change outside **Owns** is merely convenient, `decision` when a
question would change what the ticket delivers. Closing step 4 uses `review`. The
paragraph that resolves `<engine>` uses `pipeline` (a fault in `verify-ticket.py`,
hook, driver, `.mmw/target.json` — the file's body is the command it ran and the
output it saw, then stop). All five are parented to this ticket.
`Put no question on the screen` is still the leading sentence of that bullet.
Upstream rewrites the writing rules → keep the bullet and these five kinds, parented
to the ticket.

## Finish notification shape

One sentence sits between closing steps 2 and 4: a `<paseo-system>` block whose first sentence is `Agent <id> (<title>) finished|errored|was closed|needs permission.`, and it carries an `<agent-response>`, arriving in the current turn when busy or as a new turn when idle. Upstream has no such sentence. Spec #118 §5 / ticket #129 What to build item 3. Keep it on the next pull.

## Block on `paseo wait <id>`

After `create_agent`, the worker blocks in this shell with
`paseo wait <id>` until the child finishes, then reads the ticket. Ending a turn to
wait for a notification spends the main agent's only finish notification for this
worker. A notification that arrives anyway is an extra turn; read the ticket. The
parenthesis on steps 2 and 4 says a host that cancels a long shell command ends the
wait, not the turn: run `paseo wait <id>` again until the child is idle (Grok does this).
Upstream writes "wait for the finish notification" as the wait → put `paseo wait <id>`
and the parenthesis back on steps 2 and 4.

## This ticket's sub-issues

`Sub-issues opened:` on the closing-comment skeleton is this ticket's sub-issues
(`issues/<n>/sub_issues`), not the spec's children filtered by first line. The worker
also reads those open children at start of work, as a supplement to **What to build**.
Upstream puts `Sub-issues opened:` back under the spec → point it at the ticket.
