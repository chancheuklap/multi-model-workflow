# implement

源目录：`mmw-v2/upstream/skills/engineering/implement/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 第一句之后的开工段 | 我们改的：开工第一步跑 `verify-ticket` 技能的 `--preflight`——分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、未关的 blocker、assignee 六项核对，六项全过由它 claim；打印 `NOT_READY` 就停，原因已由脚本评论到票上，不再写第二遍。六项逐项点名，是因为 `verify-ticket.py` 的 `refusals()` 就是这六条：worker 撞上标签或 assignee 那两条时，要认得出这是 preflight 的正常拒绝而不是脚本坏了。之后核对标题与 `## What to build` 描述同一个 vertical slice、`## Owns` 每条 glob 匹配现存路径或标 `(new)`，没有 `## Owns` 的旧票就从 `## Seam` 与 `## Parent` 指名小节推导并评论到票上。理由：claim 与开工前的核对是固定操作，交给脚本比写成正文指令可靠；旧票补齐 `## Owns` 才有写界。上游加了同类前置检查 → 收上游措辞，`--preflight` 第一步与 `Owns check` 保留 |
| 「开写之前先读」那一段 | 我们改的：票读全 → `## Read first` 逐份读到结论（research 的末节、ADR 的 Decision、从 Claude Design 下载的 handoff package、prototype 叶子 `README.md` 读到它的 verdict），其中记录已拍板结论的条目是 baseline，`the baseline is the contract`，不是参考；两类 baseline 处理不同：handoff package 逐字照抄，prototype 按正式标准重写、保住 verdict 定下的形状 → 沿 `## Parent` 只读票指名的 Implementation Decisions 小节 + Testing Decisions + Out of Scope，不读 spec 全文 → 根 `CONTEXT.md`。没有 `## Read first` 的旧票退回读 spec `## Sources` 全部。理由：整份 spec 会淹掉票指名的小节；baseline 的 contract 地位防默默偏离。prototype 那一项指向叶子 `README.md` 读到它的 verdict，与同一句里另外三项同构——四项都是打开就找得到的位置（research 文件的末节、ADR 的那一节、下载下来的整个目录、叶子 `README.md`）；照着哪一块写由 verdict 自己说，不必再写一条禁令去排除 HTML 外壳或 harness。两类 baseline 的差别不写出来，worker 会对着一个 prototype 的 variant 逐字抄，把原型阶段的粗糙一起抄进正式代码。`## Read first`、`## Seam` 是我们在 `to-tickets` 模板里加的节名，`## Sources` 是 `to-spec` 里加的，改那边就同步改这里。上游自己写了开写前的读取步骤 → 收上游，`narrowed reading` 与 `the baseline is the contract` 保留 |
| `state the seam` 那一段 | 我们加的：seam 抄票的 `## Seam`；票没有这节时从 spec 的 Testing Decisions 推出并先评论到票上再动手。上游有同类要求 → 收上游，「先写回票」这条保留 |
| `state the seam` 与 `/tdd` 之间的 writing rules 段 | 我们加的：一串动作——`## Read first` 里每条 baseline 是 contract（`the baseline is the contract`），值、文案、状态与接口形状从 baseline 抄而不是凭记忆重写，`the contract does not fit`（缺状态、字段、交互或用例，或两条 baseline 矛盾）就在 spec 下开 sub-issue（`needs-triage`），不默默改 baseline、不默默绕过；过不了的检查用改代码或 abandon 那条 acceptance criterion 来答，不弯 baseline、不弯 the harness、不弯测试——这一款给的是正面动作接一句底线，而不是并排的第三个 never，且它指向的 abandon 就是同一份文件 closing steps 第 1 步的 `three-round cap`；改函数前 grep 每个调用方、修共用处，加分支或 guard 前先点名并删掉它让其多余的分支或文件；写 helper 前先在仓库与 `## Read first` 找现成；加文件、依赖、配置前说出已有的为何不够；安全、防数据丢失、无障碍与票里明确要的（`## What to build`、每条 acceptance criterion、baseline、`## Seam` 的接口）不许简化；收尾写 `skipped: [X], add when [Y]`；`Owns two grades`——为过 acceptance criterion 不得不改的 `## Owns` 外文件照改、由 closing comment 的 `Outside Owns:` 记录，顺手想改的不改、开 sub-issue。同段还有 `Put no question on the screen`，见下方同名一节。措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效。上游加了写码期间的纪律段 → 收上游措辞，这些条并进去 |
| `Run typechecking regularly` 之后、「Once done」之前的测试范围段 | 我们加的：验证手段随意、scratch 脚本不必保留；只在票要求或仓库本来就为这类改动留测试时提交测试，规模比照相邻测试文件（每条声明的行为约一个测试），不把临时检查变成永久测试文件；这段只管多出来的东西，票要的每个行为仍要完整实现。来源是 Anthropic 的 `Prompting Claude Fable 5.1` 指南 `Keep changes and tests to what the task asks for` 一节：`Owns two grades` 管改动范围，这段补上测试文件数量。上游若加了同类约束 → 收上游措辞 |
| 「Once done」之后的 closing steps | 我们改的：`self-run`（`verify-ticket` 技能，写完码那一条 run；同一条 acceptance criterion 至多三轮，第三轮写 `ABANDON: AC<n> failed`）→ dispatch 一次 verifier（prompt 只有 `verify #<n>`，不 dispatch 第二次）→ 用 `dispatch` 技能起 reviewer 并等它的 review comment（一轮、修一轮、不复审；完成条件是 review comment 在 ticket 上；超时跳过这一轮；in-ticket finding 修掉、out-of-ticket 的开 sub-issue，修 finding 受 writing rules 同样约束，reviewer 的 suggestion 是加东西时先找可删的）→ `Audit`（重读票与 `## Read first`，每条 acceptance criterion 追到 `EVIDENCE:`，重数 `Counts:`）→ 把只等人拍一句话的 acceptance criterion 切成 `decision` 类 sub-issue、closing comment 写成草稿文件（固定格式：first line `ALL MET` / `HANDOFF REQUIRED`、`Branch: … Commit: … PR: …` 一行且没有 pull request 时写 `PR: none — <理由>`、`Post-verdict:`、每条 acceptance criterion 四行、`Outside Owns:`、`skipped: [X], add when [Y]`、`Sub-issues opened:` 收本票工作期间开的四类 sub-issue（`the contract does not fit`、`## Owns` 之外的顺手改动、out-of-ticket review finding、`ABANDON: decision`）、`Counts:`、`Decisions I made on my own`）→ `closeout`（`verify-ticket` 技能，草稿写好那一条 run）由脚本贴评论并关票或换标签，worker 不亲手关票换标签（`hook.py` 拦）→ 关掉第 3 步 reviewer 跑在里面的 Herdr pane。三个 `ABANDON` kind 各有准入：`failed` 要票上数得出三条 `self-run`、`stuck` 不看轮次、`decision` 开 sub-issue 不挡 `ALL MET`。理由：关票是一道门不是一个动作，上游三步（评论证据 → pull request → 关票）被 closing steps 吸收；pull request 那一步整个退场，见下方 `No pull request, and no push`。`Branch: … Commit: … PR: …` 三个值写一行、没有 pull request 时把理由接在 `PR: none` 后面，是为了早上读票的人和以后想解析它们的脚本只面对一种形状；`Sub-issues opened:` 四类逐条点名，是因为正文里要求开 sub-issue 的地方就是这四处，只说「上面两类」会漏掉另外两处。上游改收尾 → 收上游措辞，closing steps 的顺序、`three-round cap`、`--closeout` 这道 closeout、`No pull request, and no push` 必须保留 |
| frontmatter 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation` | 我们删的：上游两处都设了只许人触发，我们要模型自己就能调用 implement，所以两处一起删。上游若再带回来 → 仍然删 |

## Reaching the two scripts

The closeout and the preflight name the `verify-ticket` skill and the run they
want; step 3 names the `dispatch` skill. None of them writes a script path. The script
lives inside the skill, so the skill is what resolves it, from its own `SKILL.md`'s
location: that is right on all five hosts, and it keeps installing the skill and having
the script the same event. Naming the skill also puts the exit codes and the refusal
table in front of the worker at the moment it runs the command, which a path does not.
Upstream writes a path into any of these steps → replace it with the skill and the run.

## Waiting on the reviewer carries no number

`dispatch.sh wait <n> "^REVIEW "` passes no seconds: the timeout lives in the script
(`WAIT_DEFAULT_SECONDS`), and a number in the skill text is a number a worker shrinks —
one did, and skipped a review comment its reviewer was still writing. Upstream brings a
number back → drop it again.

## No pull request, and no push

Upstream's step 6 pushed the branch and opened a pull request. This pipeline opens
none, and the step is gone: nothing here reads a pull request — `code-review` takes its
diff from git, the verifier reads the ticket and the worktree, and the closeout
reads neither. What does read a branch is `dispatch.sh advance`, which merges it into
`git config branch.issue-<n>.mmw-base-branch` once the ticket closes, on this machine,
with no `gh` call at all. A pull request would only be a second place to remember to
merge and pull back from.

The `Branch: … Commit: … PR: …` line stays, with `PR: none — will be merged into <base
branch> by dispatch.sh advance`. It is written in the future tense on purpose: the
closing comment is written before the ticket closes, and the merge happens after.

Upstream brings the push or the pull request back → drop them again, and keep the
recorded base branch, which `advance` needs.

## Put no question on the screen

One bullet in the writing rules. A worker that puts a question up gets no answer:
`board.py` comments the form on the ticket as `BLOCKED:`, presses the host's close key, and
sends `continue` — nobody answers, and asking again spends the re-prompts `WAKE_LIMIT`
allows, until the ticket is handed back to `needs-triage`. So the bullet says what to do
instead: take the option the ticket, its baselines and the spec make most likely, record it
under **Decisions I made on my own**, and carry on; a question whose answer would change
what the ticket delivers gets a sub-issue. The recording place and the sub-issue route are
here too — this bullet is the third part, the one that says not to ask. Upstream rewrites
the writing rules → keep the bullet.

## Closing steps: resume after a re-prompt

One sentence added to the "Once done" paragraph: a ticket that already carries a `self-run`, `VERDICT` or `REVIEW` comment is resumed at the step after the newest of them. `board.py` re-prompts a stopped worker with `continue` and nothing else, so the skill has to know it may be entering the closing steps mid-way. On the next upstream pull keep this sentence with the closing steps.

## Where a failing `visual-parity.py` criterion is read

Two sentences added to step 1 of the closing steps. That script prints a single `DIFF <scene> <viewport> <pct>% box=… — <reasons>` line; which reasons bring sub-lines out under them, and what `NEGATIVE CONTROL FAILED` means, are written only in the verify-ticket skill. Every other refusal in the closing steps explains itself in its own stderr, so this is the one place the worker has to be sent elsewhere. The second sentence says to fix only what the line names and run once more, not to chase the pixel share: on ticket #548 of the chameleon repository a worker whose tree already matched spent sixteen parity runs changing fonts, line heights and renderer flags against a 1% pixel threshold, and abandoned the criterion. Upstream rewrites step 1 → keep both sentences.
