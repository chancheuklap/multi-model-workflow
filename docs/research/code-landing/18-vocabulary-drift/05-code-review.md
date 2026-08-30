# 05 code review 簇：漂移审计

仓库根：`/Users/cheuklapchan/multi-model-workflow/.claude/worktrees/upstream-pull`。以下路径全部相对该根。

## 发现 1：reviewer 的 base-commit 到底怎么算，三份文件互相指、没有一份写

- 类型：断点
- 后果：worker 走到收尾第 3 步时没有任何规则可依，只能自己编一个起点 commit；同一张票换个 worker 就换一份 diff，review 的覆盖范围不可复现，编错了还会在 `code-review/SKILL.md` 第 18 行「diff 为空就停」处白白烧掉一轮。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 「`bash ~/.agents/skills/dispatch/scripts/dispatch.sh <n> reviewer <base-commit>` starts the reviewer session — the dispatch skill's SKILL.md says how to fill the arguments」
  - `mmw-v2/skills/dispatch/SKILL.md:33` 「| `[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from |」——被指名的这份文件只说它是什么，没说怎么算出来
  - `CONTEXT.md:526` 「The first argument of the review dispatch line: where the diff starts.」——同样只有定义
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:170` 「`[ -n "$base" ] || refuse "the reviewer needs the commit its review starts from"`」——脚本只检查非空，不校验也不推导
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:244` 「`base = git("merge-base", "main", "HEAD", cwd=root)`」——同一条流水线里 `Outside Owns:` 用的正是这个起点，但没有任何文件把它接给 reviewer
- 建议正名：在 `mmw-v2/skills/dispatch/SKILL.md` 的 `[base-commit]` 行写死一条算法，并让 `CONTEXT.md:525` 的 base-commit 条目复述它。默认选 `git merge-base main HEAD`，理由：`Outside Owns:` 已经用它，两处同一个起点，closing comment 与 REVIEW 首行的范围才对得上。

## 发现 2：code review 是两个轴还是三个轴，四处说法不一致

- 类型：分岔
- 后果：读 `CONTEXT.md` 的 dispatcher 条目或读 `ask-matt` 的人只会派两个子代理，Tests 轴——这条流水线里唯一怀疑「绿色证明了什么」的读者——整个消失，且没人会发现少了一份报告。
- 证据：
  - `CONTEXT.md:36` 「Inside code review, the role that starts the two reviewing subagents, collects both reports, and writes the comment.」
  - `CONTEXT.md:498` 「One of the three axes: does the change follow this repository's documented coding standards」——同一份 `CONTEXT.md` 自相矛盾
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:6` 「You run three read-only sub-agents over one diff and write their reports onto one ticket.」
  - `mmw-v2/upstream/skills/engineering/README.md:30` 「**[code-review](./code-review/SKILL.md)**: Two-axis review of the diff since a fixed point」
  - `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md:25` 「then closes out by running **`/code-review`**, a two-axis review (Standards + Spec) of the diff, before committing」
- 建议正名：以 `code-review/SKILL.md` 的三个轴为准。改 `CONTEXT.md:36`（two→three、both→all three）、`README.md:30`、`ask-matt/SKILL.md:25`。`merge-notes/code-review.md:41`（上游加第三个轴怎么合）已经预备了这条路，但没覆盖这两处上游散文。

## 发现 3：code review 跑在提交之前还是提交之后，两套说法

- 类型：分岔
- 后果：按 `ask-matt` / `engineering/README.md` 做的人先 review 再 commit，而三个子代理读的都是 `git diff <base-commit>...HEAD`——未提交的改动不在 HEAD 上，三份报告会一致地报「没有改动」或只看到上一次提交，这一轮 review 等于没跑。
- 证据：
  - `mmw-v2/upstream/skills/engineering/README.md:16` 「driving `/tdd` at pre-agreed seams and closing out with `/code-review` before committing」
  - `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md:25` 「a two-axis review (Standards + Spec) of the diff, before committing」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:30` 「Once done, commit your work to the current branch and close out in seven steps.」——review 是这七步里的第 3 步，在提交之后
  - `mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md:10` 「`git diff <base-commit>...HEAD`」
- 建议正名：以 `implement/SKILL.md:30` 为准（先提交再 review）。删掉 `README.md:16` 与 `ask-matt/SKILL.md:25` 的 "before committing"。

## 发现 4：同一份 SKILL.md 里，frontmatter 招揽的用法正文全部拒绝

- 类型：分岔
- 后果：`description` 是宿主唯一扫进去的一行，用户说「review 一下这个 PR」或「review since main」时模型会自动挑起这个技能，走到正文第 8 行发现必须要票号，只能反问用户；就算用户给不出票号，第 4 步也没有第二个落点——报告只会写进 `gh issue comment <ticket>`，无票就无处可写。
- 证据：
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:3` 「Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\".」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:8` 「Invoked as `code-review <base-commit> #<ticket>`. Both arguments come from the caller; when either is missing, ask for it.」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:54` 「`gh issue comment <ticket> --body-file <file>`」
  - `CONTEXT.md:483` 「**`code-review <base-commit> #<n>`**」——本仓登记在册的只有带票号这一种形态
- 建议正名：待用户拍板，两个选项——(a) 把 `description` 改成只描述派发形态（「Review one ticket's diff on a base commit and comment the report on that ticket」），放弃无票用法；(b) 保留无票用法，正文加一条无票时的落点（打印到 stdout / 写文件）。倾向 (a)：这条流水线里 review 的读者是修它的 worker，而 worker 只读票。

## 发现 5：五问把「接口够不够深」判给 Standards 轴，Standards 轴里没有这类判据

- 类型：断点
- 后果：出票人按 `to-tickets` 把「接口是不是 pass-through」「文字说清楚了没有」「错误信息有没有告诉调用方下一步」这三类判断踢出验收标准、交给 code review，但 Standards reviewer 的判据只有「仓库写下来的规范」加 Fowler 十二条坏味道，三类里没有一类会被真正判到——它们从票上消失，也没落到 review 上。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:51` 「Whether an interface is deep rather than a pass-through, whether a passage says enough, whether an error message tells the caller what to do next, whether the test behind a criterion could ever have failed. Code review decides these — its `Standards` axis for how the code is written」
  - `mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md:3` 「You review one diff against two questions: **does this code follow the conventions this repository documents?** and **does the same outcome exist with less code?**」
  - `mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md:16` 「`CODING_STANDARDS.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, a `docs/` page on conventions, a `CONTEXT.md` naming the domain vocabulary」——`codebase-design` 不在这份来源清单里
  - `mmw-v2/upstream/skills/engineering/codebase-design/SKILL.md:12` 「Use these terms exactly: don't substitute "component," "service," "API," or "boundary." Consistent language is the whole point.」
  - `mmw-v2/upstream/skills/engineering/tdd/SKILL.md:26` 「call the Skill tool with "codebase-design" for the vocabulary」——`tdd` 与 `improve-codebase-architecture` 都显式接上了这份词表，唯独判「代码写得怎么样」的 Standards 轴没有
- 建议正名：在 `standards-reviewer.md` 第 2 节的来源清单里加上 `codebase-design/SKILL.md`（module / interface / depth / seam / adapter / leverage / locality 与 deletion test），并在第 3 节的判据里补一条 depth 判据，措辞直接抄 `codebase-design/SKILL.md:63` 的 deletion test。理由：`to-tickets` 已经把这类判断路由到这个轴，路由的终点必须存在。

## 发现 6：Tests 轴的范围，CONTEXT.md 与 reference 给的是两条不同的边界

- 类型：分岔
- 后果：按 `CONTEXT.md` 做的 Tests reviewer 对 diff 里没被 `CHECK:` 点名的测试文件一个字不报，而 `SKILL.md` 第 3 节还在等着把这类发现归到 `## Out-of-ticket` 里——那一栏永远是 `None`，一整类问题静默消失。
- 证据：
  - `CONTEXT.md:506` 「The third axis: are the test cases the criteria name worth trusting. It reads only the test files named by a `CHECK:`, and reports neither coverage nor a test the criteria never asked for.」
  - `mmw-v2/upstream/skills/engineering/code-review/references/tests-reviewer.md:23` 「A test file in the diff that no `CHECK:` names is still worth a finding, but say so — it lands in a different pile than one a criterion depends on.」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:49` 「- Any other test file in the diff → **out-of-ticket**.」
- 建议正名：以 `tests-reviewer.md:23` 为准。把 `CONTEXT.md:506` 改成「以 `CHECK:` 点名的测试文件与用例为票内范围，diff 里其余测试文件仍可报，归票外」。

## 发现 7：dispatcher（派发者）在两个地方指两个不同的东西

- 类型：命名撞车
- 后果：`board.py`、`hook.py`、`verify-ticket.py` 里的 "the dispatcher" 是起 worker 会话的那个（`dispatch.sh` / 主 agent / board），`CONTEXT.md` 登记的 dispatcher 是 code review 内部收三份报告的那个角色。读 `NOT_READY` 提示「the dispatcher starts this ticket again once those close」的 worker，按词表会以为是某个 code review 里的角色会重开它的票。
- 证据：
  - `CONTEXT.md:36` 「Inside code review, the role that starts the two reviewing subagents, collects both reports, and writes the comment. It neither judges nor fixes anything itself.」
  - `mmw-v2/skills/dispatch/scripts/board.py:241` 「dispatcher gives it `issue-<n>` before it prompts, and only the dispatcher uses that name」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:20` 「the dispatcher sets `MMW_TICKET` on the worker's pane」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:781` 「`NOT_READY: #{number} is blocked by {names}; stop — the dispatcher `」
- 建议正名：待用户拍板。选项 A：`CONTEXT.md` 的 dispatcher 改写成两义合一的宽定义（「起会话并把 prompt 交给它的那一方」），code review 内部那个角色另起一名（如 review dispatcher）。选项 B：把三份脚本里的 "the dispatcher" 换成 `dispatch.sh`（脚本名，不是角色名），dispatcher 只留给 code review。倾向 B：脚本注释指的本来就是那一个具体脚本。

## 发现 8：reviewer 一个词，同时指不评审任何东西的那个会话和评审的那三个子代理

- 类型：命名撞车
- 后果：「reviewer 的 suggestion」「reviewer 报了 X」这类句子无法确定说的是会话还是某一个轴；写 merge-note 的人按「一个 reviewer 一份 reference」数出三个 reviewer，而 `models.md` 里 `reviewer` 只有一行、且它「reviews nothing yourself」。
- 证据：
  - `CONTEXT.md:32` 「The Claude Code session a worker starts through Herdr to run one round of code review.」
  - `mmw-v2/skills/dispatch/models.md:26` 「| reviewer | claude | `opus` | — | `--permission-mode bypassPermissions --model {model} -n issue-{n}-review` |」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:6` 「You review nothing yourself, and you are the only one of the four agents that writes anything.」
  - `mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md:58` 「belong to two other reviewers running beside you」
  - `mmw-v2/merge-notes/code-review.md:43` 「`references/` 下只放 reviewer 的判据，一个 reviewer 一份」
- 建议正名：三个子代理统一叫 `Standards reviewer` / `Spec reviewer` / `Tests reviewer`（三份 reference 的 H1 已经是这三个名字），单独一个 `reviewer` 只指 `models.md` 里那一行的会话；`CONTEXT.md` 的「Code review」一节补登这三个名字。

## 发现 9：`issue-<n>-review` 被写成分支名，实际是会话显示名

- 类型：脚本与文档不符
- 后果：按词表找 `issue-<n>-review` 分支的人找不到（reviewer 是只读的，不建 worktree、不建分支，它就在 worker 的 worktree 里 split 一个 pane）；真要照这句去建分支，reviewer 反而会离开被审的那份代码。
- 证据：
  - `CONTEXT.md:396` 「The Herdr name and branch name of a worker and of its reviewer. Must be unique among live agents.」
  - `mmw-v2/skills/dispatch/models.md:26` 「`--permission-mode bypassPermissions --model {model} -n issue-{n}-review`」——`claude --help` 第 129 行：`-n, --name <name>  Set a display name for this session`
  - `mmw-v2/skills/dispatch/models.md:24` 「`-w issue-{n} --worktree-base main --force --trust --model {model}`」——worker 那行才有真正开 worktree、定分支的参数
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:204` 「`pane="$(herdr pane split --pane "$caller" --direction "$direction" --cwd "$root" --no-focus \`」——reviewer 落在 caller 的 pane 旁边，cwd 就是 worker 的 worktree
- 建议正名：`CONTEXT.md:395-396` 改成「`issue-<n>` 是 worker 的 Herdr 名与分支名；`issue-<n>-review` 只是 reviewer 的 Herdr 名与会话显示名，reviewer 不建分支，它在 worker 的 worktree 里跑」。

## 发现 10：三个 reviewing subagent 不在 models.md 里，而 models.md 声称所有派出去的 agent 都在

- 类型：断点
- 后果：想给 Tests 轴换个更强的模型的人，按 `references/editing-models.md` 找不到可改的行；三个子代理只能继承 reviewer 会话的默认 subagent 模型，`CONTEXT.md:392` 「for every agent」这句是空的。
- 证据：
  - `mmw-v2/skills/dispatch/models.md:3` 「One row per `(agent, host)`. Every agent this pipeline sends out is here except the」
  - `CONTEXT.md:392` 「The one table defining, for every agent, its host, model, thinking effort and launch command.」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:22` 「## 2. Launch three sub-agents in parallel」
  - `mmw-v2/agents/` 下只有 `advisor`、`claim-checker`、`verifier` 三个 subagent 定义目录，`mmw-v2/agents/assemble.py:44` 「这里只取启动参数为 — 的那些行，也就是 subagent」
- 建议正名：待用户拍板。选项 A：给 `Standards` / `Spec` / `Tests` 三个 reviewer 各加一行 `—` 启动参数的 subagent 行并建 `mmw-v2/agents/<名>/`。选项 B：在 `models.md:3` 那句话上写明例外——「code review 的三个轴子代理由 reviewer 会话按其宿主默认模型起，不在此表」。

## 发现 11：diff 为空或 base 解析不了时，reviewer 什么都不写到票上，worker 要空等 1800 秒

- 类型：断点
- 后果：`code-review/SKILL.md` 自己第 67 行的原则（只存在于会话里的报告谁也读不到）被它自己的失败路径违反；worker 的 `dispatch.sh wait` 只认首行 `^REVIEW `，于是这一轮从「起点 commit 写错了」变成一次 30 分钟的沉默超时，票上留下的是一句「did not report back」，与真实原因无关。
- 证据：
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:18` 「A ref that does not resolve or a diff with no files is a failure here, before three sub-agents spend a context each on nothing: say which one it was and stop.」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:67` 「The reviewers ran in a session that ends; the ticket outlives it... A report that exists only in this conversation reaches nobody.」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 「`dispatch.sh wait <n> "^REVIEW " 1800` waits for the report; done means the comment is on the ticket, never a session's state.」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:321` 「`--body "$who did not report back within ${seconds}s. This round was skipped and the ticket carried on."`」
- 建议正名：以第 67 行的原则为准——`SKILL.md` 第 1 步的失败也要 `gh issue comment`，首行仍是 `REVIEW <base>..<HEAD>`，正文一行说明是哪一种失败。这样 worker 的 wait 立刻返回，30 分钟不再浪费。

## 发现 12：baseline 一个词在这一簇里有三个意思，其中一个还是 CONTEXT.md 划掉的死词

- 类型：命名撞车（含幽灵词）
- 后果：Spec reviewer 只读它自己那一份 reference，看到「The baseline directory is out of scope for you」时，按 `CONTEXT.md:632` 的 baseline 定义会把 `## Read first` 里所有记录已拍板结论的条目（ADR 的 Decision、prototype 选定的 artifact、spec 指名小节）都当成「不许读」，而这些正是 Spec 轴判「有没有照要求做」的依据——整个轴会被自己关掉。
- 证据：
  - `CONTEXT.md:632` 「Anything under `## Read first` that records a settled conclusion: the chosen artifact of a prototype... the Decision of an ADR, the resolution of a decision ticket, and the spec sections `## Parent` names.」
  - `mmw-v2/upstream/skills/engineering/code-review/references/spec-reviewer.md:46` 「**The baseline directory is out of scope for you.** A ticket with UI acceptance criteria names a baseline directory in its `## Read first`」
  - `CONTEXT.md:537` 「_Avoid_: 开发交接包, 基线目录, UI 基线」——「基线目录」是登记在册的死词
  - `CONTEXT.md:502` 「The second axis: does the change match what the ticket or the spec asked for. It does not look at the handoff package.」——同一条禁令，`CONTEXT.md` 用的是正名「handoff package」
  - `mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md:25` 「A documented-standard breach can be hard; a baseline smell never is.」——第三个意思：smell baseline
  - `mmw-v2/merge-notes/code-review.md:18` 「不读 `prototypes/` 下的基线目录」
- 建议正名：`spec-reviewer.md:46` 与 `merge-notes/code-review.md:18` 里的 "baseline directory"／「基线目录」一律换成 `handoff package`／交接包（`CONTEXT.md:536` 的正名），并在同一句里给出它的位置 `prototypes/<task>/<issue>/UI/`（叶子目录）。smell baseline 与 test smell baseline 保持全称，不单说 "baseline"。

## 发现 13：seam 一个词，票的 `## Seam` 与 codebase-design 的 seam 是两个定义

- 类型：重复定义
- 后果：Standards reviewer 若接上 `codebase-design`（见发现 5），会拿 Feathers 意义上的 seam 去读票的 `## Seam`——后者说的是「在哪一层验、测试放哪个目录、抄哪个先例文件」，不是「能改行为而不用改那处代码的位置」；两边讨论的不是一件事。
- 证据：
  - `CONTEXT.md:58` 「Which layer this ticket is verified at, which directory the tests live in, and which existing file to copy the shape from.」
  - `mmw-v2/upstream/skills/engineering/codebase-design/SKILL.md:22` 「**Seam** _(Michael Feathers)_: a place where you can alter behaviour without editing in that place; the *location* at which a module's interface lives.」
  - `mmw-v2/upstream/skills/engineering/tdd/SKILL.md:26` 「When the shape of that interface is itself in question (how deep the module is, where the seam belongs...)」
- 建议正名：待用户拍板。选项 A：`CONTEXT.md:57` 的条目名保持 `## Seam`（它是票里的字面小节名，改不得），但定义里补一句「这一节记的是 `codebase-design` 意义上的 seam 落在哪一层，加上验证目录与先例文件」，把两个定义显式接起来。选项 B：在 `CONTEXT.md` 里单独登记 codebase-design 的 seam 一条，注明两者关系。

## 发现 14：merge-note 说「上游只有 SKILL.md 一个文件，冲突一定落在 SKILL.md 上」，同一份文件八行后又给 agents/openai.yaml 立了条目

- 类型：分岔
- 后果：下次拉上游的人按第 37 行只盯 `SKILL.md`，`agents/openai.yaml` 的冲突（上游那一行的措辞）会被漏掉或被 `git` 直接吞掉我们的三轴改写；「四个文件」这个数也和实际的五个对不上。
- 证据：
  - `mmw-v2/merge-notes/code-review.md:37` 「上游只有 `SKILL.md` 一个文件，我们有四个，冲突一定落在 `SKILL.md` 上。」
  - `mmw-v2/merge-notes/code-review.md:43` 「5. 四个文件一律英文，不写出处、不写落地记录。」
  - `mmw-v2/merge-notes/code-review.md:45-49` 「### agents/openai.yaml ... | `interface.short_description` | 改成三个轴。上游改这一行 → 收上游措辞，轴数按我们的 |」
  - `git log --oneline -- mmw-v2/upstream/skills/engineering/code-review/agents/openai.yaml` 显示它来自 subtree 合入的 `641415dc`，之后被 `5db279c3` 改写——它确实是上游文件
- 建议正名：把第 37 行改成「上游有 `SKILL.md` 与 `agents/openai.yaml` 两个文件，我们有五个，冲突落在这两个上」，第 43 行的「四个文件」相应改成「四个 Markdown 文件」。

## 发现 15：test smell baseline 与 tdd 的 tests.md / mocking.md 是同一批判据的两份副本

- 类型：冗余
- 后果：改了一边不改另一边，Tests reviewer 与写测试的 worker 会按两套不同的坏味道清单工作。这份重复是 merge-note 自己声明并交给人手工对齐的，没有任何脚本能发现它漂了。
- 证据：
  - `mmw-v2/merge-notes/code-review.md:29` 「**这两份文件是同一批判据的另一个副本：改 `tdd/tests.md` 或 `tdd/mocking.md` 时对着 `references/tests-reviewer.md` 第 2 节看一遍，反过来也一样。**」
  - `mmw-v2/upstream/skills/engineering/code-review/references/tests-reviewer.md:34` 「**Named for the how, not the what**: `checkout calls paymentService.process` describes the implementation」
  - `mmw-v2/upstream/skills/engineering/tdd/tests.md:31` 「test("checkout calls paymentService.process", async () => {」——同一个例子的另一份写法
- 建议正名：待用户拍板。选项 A：接受这份重复（reviewer 的判据必须自带全文，见 `merge-notes/code-review.md:19` 的理由），但把对齐义务从 merge-note 挪进两份文件本身各一行「另一份副本在 X」。选项 B：`tdd/tests.md` 改成指向 `tests-reviewer.md` 第 2 节，只留代码示例。倾向 A：子代理只读自己那一份 reference，跳转会失效。

## 发现 16：幽灵词「reviewer 会话」/ "reviewer session"

- 类型：幽灵词
- 后果：`CONTEXT.md` 把它划成死词、正名为 `reviewer`，但活文件里两处照旧在用，读者不确定 reviewer 与 reviewer 会话是不是两个东西。
- 证据：
  - `CONTEXT.md:33` 「_Avoid_: reviewer 会话, code-review 会话, 复核者」
  - `mmw-v2/merge-notes/implement.md:15` 「`dispatch.sh <n> reviewer <起点>` 起 reviewer 会话」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 「starts the reviewer session」
- 建议正名：两处都改成 `reviewer`（`dispatch.sh <n> reviewer <base-commit>` 起 reviewer / starts the reviewer）。注：`CONTEXT.md:32` 的定义本身就是「the ... session」，所以真正该修的可能是这条 `_Avoid_`——待用户拍板是删这条 `_Avoid_` 还是改这两处。

## 发现 17：幽灵词 orchestrator

- 类型：幽灵词
- 后果：`models.md` 的第一段用一个 `CONTEXT.md` 明令不用的词称呼主 agent，读者不确定 orchestrator 与 main agent 是不是同一个角色，而这句话正是「哪些 agent 在表里」的唯一界定。
- 证据：
  - `CONTEXT.md:13` 「_Avoid_: coordinator, 编排者, orchestrator, 出票的主 agent, 落地 agent」
  - `mmw-v2/skills/dispatch/models.md:4` 「orchestrator, which is the session you started yourself from the CLI. This is the only」
- 建议正名：改成 `main agent`（`CONTEXT.md:11` 的正名）。

## 发现 18：REVIEW 首行的占位符两种写法

- 类型：分岔
- 后果：`CONTEXT.md` 自己规定「名字本身就是字面字符串的术语只有一个名字」，这里却有两个写法；照 `CONTEXT.md` 抄的人会在首行里留下一个连字符。
- 证据：
  - `CONTEXT.md:521` 「**`REVIEW <base-commit>..<HEAD commit>`**」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:60` 「REVIEW <base commit>..<HEAD commit>」
  - `mmw-v2/merge-notes/code-review.md:20` 「首行固定 `REVIEW <base commit>..<HEAD commit>`」
- 建议正名：以 `SKILL.md:60` 为准（两处都写 `<base commit>`），改 `CONTEXT.md:521`。
