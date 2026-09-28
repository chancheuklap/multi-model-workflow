# triage

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：上游 triage 为外来 issue 而写，可本仓和 agentflow 约 1300 个 issue 都是你自己开的，`needs-triage` 队列里几乎全是流水线自己的产出。所以这个技能最缺的，是对这个队列的真实交代：
- 里面装的是什么；
- 你早上要从 triage 拿到什么，就是每项收成一个你一句话能答的问题；
- 每一类来源已经有了哪些证据。

另有两个真实缺口：`reverify` 重开的票会被当成外来 issue，最坏的结果是票被关掉、另写一份 spec；`became-ticket` 之后票不回队列。上游原文不动，改动都在本仓的 `references/pipeline-issues.md`，以及 `SKILL.md` 里本仓加的那一句路由。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` `## Triage a specific issue or PR` 开头本仓加的那句，改为右栏 | An issue labelled `mmw:child` or `mmw:ticket`, or a retro proposal (title `Retro #<spec>: …`), came from this repository's own pipeline: read [references/pipeline-issues.md](references/pipeline-issues.md) first; it replaces step 1's reproduction and adds step 5's destinations. | 原条件只认 `ticket.returned` 与 `ticket.bounced`，`reverify` 重开的票（`ticket.regressed`）会走外来 issue 那一支：先复现，到 `ready-for-agent` 时"写一份 spec、关掉这张 issue"，也就是把一张已登记的票关掉。这在 #472、#491、agentflow #731 真实发生过。改为只看 label 和 retro 标题。 |
| I2 | `references/pipeline-issues.md` 开头，新段落 | Almost everything in this repository's `needs-triage` queue was put there by the pipeline, not by a reporter: a worker, a review, a merge or a re-run stopped because the next step needs a judgement no script can make. The user reads this queue first thing in the morning. For each item, find what the pipeline already established, turn it into one question the user can answer in a sentence, give your recommendation with its evidence, and once the user decides, put the work back where the pipeline picks it up. The evidence is already on the tracker; read a ticket's events with `python3 <events.py> fold <n>` rather than reproducing. An item left in `needs-triage` is read again tomorrow by someone with less context than you have now. | 没有它，agent 会把每张当成陌生人的报告从头调查，或者只贴一个 label，却不把问题收成一句你能拍板的话。末句是 "Staying at `needs-triage` is not an outcome." 背后的理由。依据：`docs/agents/issue-tracker.md` `## Morning queries` 把 triage 定为早上第一件事。 |
| I3 | 紧接 I2，按来源的一张短清单 | **A child a worker opened** (its body opens ``A `<kind>` child of #<n>.``): `decision`, the worker already took the default it names, so confirm or overturn it; `contract`, which authority wins, and the not-yet-started tickets the night moved to `needs-triage` wait on the same answer; `deferred`, whether a convenient change outside `## Owns` is worth a ticket; `fault`, what in the pipeline broke, here or in the toolbox; `finding`, one the night's closing pass did not reach. **A ticket handed back, bounced twice, or reopened by `reverify`**: `## A ticket handed back` below. **A ticket a night parked with no result**: it waits on an open `contract` child of its batch that names it; settle that child, then move every ticket it parked back to `ready-for-agent` together. **A retro proposal**: the retro already gathered the evidence; the user approves it or not, and approved work goes through the `to-spec` and `to-tickets` skills. | 每一类"要问用户什么"是不同的判断，这张清单把它们分开写。夜里被搁置的票要和它等的那个 `contract` child 一起处理，否则会逐张误判。 |
| I4 | `## A ticket handed back`，`ticket.bounced` 那句之后 | `ticket.regressed` means a landed ticket's criteria went red on the base branch. Read the commit it names, which criteria failed, and the sibling tickets that landed since: often a later ticket broke it, and the fix belongs there. While it still wears `needs-triage`, every `reverify` re-runs it and closes it again once it is green, so a regression something else already fixed needs no outcome from you. | 真实缺口（见 I1）。末句依据 `status.py` 的 `regressed_in_triage()` 与 `dispatch.sh` 的 reverify 分支。 |
| I5 | 同一节 `ticket.returned` 部分之后 | For `ticket.returned`, the closing comment's `ABANDON:` lines say why, and the kind points at the outcome. `stuck` on a credential, a device or a real environment is usually `ready-for-human` of kind `reach`. `failed` after rounds that each tried something raises one question: would a changed criterion, a split ticket or a `senior-worker` grade pass? Sending it back unchanged repeats the night. The worker's partial work stands in `.worktrees/issue-<n>`. | 没有它，agent 容易原样打回 `ready-for-agent`，第二夜再失败一次。`ABANDON:` 的三种 kind 由 `implement` 定义，正是选出口要用的判断。 |
| I6 | `## ready-for-agent` 表第二行，替换 D1 删掉的说明 | It leaves the queue labels alone: rewrite the body to `<issue-template>` (in `to-tickets`), swap `needs-triage` for `ready-for-agent`, add `junior-worker` or `senior-worker`, and lint it. `--lint` passes a ticket outside the agent queue, so it will not catch a missing label. | 功能缺口：`route_child()` 不改队列 label，child 是带着 `needs-triage` 创建的，frontier 只收 `ready-for-agent`，新票会一直停着，没人派工。从代码推出，tracker 上没找到 triage 走过这一行的实例。 |
| I7 | 表第一行（改挂到另一张票下）之后 | Only a ticket not yet started reads it: a worker reads its ticket's open sub-issues once, when it starts. | 早上 triage 时，这一批的票多数已经落地；改挂到已落地的票下，没有人会读到。 |
| I8 | 最后一段末尾 | With no night open on its spec, the `dispatch` skill's one-ticket run starts it instead. | 原文只写了开夜的情况；夜外 `land` 失败的票也会进 `needs-triage`（`one-ticket.md` 第 4 步）。 |
| I9 | `SKILL.md` 第 5 步，四个出口之后（适用于 `mmw:child`） | A child whose default was right, or whose fix is already on the base branch, is closed through `<dispatch> route <ticket> <child> fixed` or `stale <invalid\|fixed-elsewhere>` so its ticket records the route; `wontfix` means nobody will do it, not that it is done. | 真实错误：agentflow #620、#621、#622、#629 写着"已直接改完"，打的却是 `wontfix`；本仓 #265、#283 关掉时没经过 `route`，原票上没有 `child.closed`，看板读不到。这一条只是用对出口，不涉及当场动手修，那是下面要你决定的事。 |
| I10 | `references/pipeline-issues.md` 开头，新增 `` ## Resolve `<events.py>` once `` 一节 | `<events.py>` is `scripts/events.py` of the `verify-ticket` skill; resolve it from that skill's own `SKILL.md`, since the path differs by machine and by host. | I2 用到的 token 按 `SKILL-SET-REVIEW.md` 的规定集中定义（advisor 指出不应写在正文括号里）。 |

### 删除

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `pipeline-issues.md` 表第二行 "which moves `<m>` under the spec, swaps its layer label `mmw:child` for `mmw:ticket`, and records the route on the ticket it came from" | 删，只留命令；腾出的位置写 I6 | `route_child()` 做这三件事并自己报告。 |
| D2 | `## Gather context` 查父 issue 的方法（`parent:` 行、REST 注释） | 删；由 I3 的 "its body opens ``A `<kind>` child of #<n>.``" 承担 | child 正文第一行就写着类型和父票。 |
| D3 | `## Gather context` 与 `## A ticket handed back` 两处 "read … event trail … instead of reproducing" | 合并到 I2 一处 | 同一文件、同一句意思。 |
| D4 | `SKILL.md` 第 5 步 "`needs-info`, `ready-for-human`, and `wontfix` move nothing: the parent stays." | 挪到 `pipeline-issues.md` `## ready-for-agent`，写成"只有 `ready-for-agent` 会移动 child"；`merge-notes/triage.md` 对应一行跟着改 | 只对流水线的 child 有意义，却放在所有人都读的第 5 步里。 |
| D5 | "When the parent is a ticket, pick one destination" 的条件 | 删条件 | 进到这份 reference 的 child，父一定是票。 |
| D6 | `mmw-v2/upstream/docs/engineering/triage.md` 里本仓加的一段 | 恢复上游原文，删掉 merge-note 对应一行 | 这一页不装进任何宿主，没有 agent 读得到。 |

### 已定（2026-09-28）

早上 triage 不当场修小问题。triage 只负责把每一项判到正确的出口；小问题以后会另有一条专门的路。I9 只管"用对出口"（已经修好的走 `route … fixed`，不再打成 `wontfix`），不给 triage 任何改代码的权限，与这个决定一致。

### 不采纳

- 无。调查员的缺口草稿都有证据，I2–I8 是按原意压短后的版本。

## 结论

体量：`SKILL.md` 1193 词、`AGENT-BRIEF.md` 1339 词、`OUT-OF-SCOPE.md` 714 词、`references/pipeline-issues.md` 394 词，合计约 3640 词，没有脚本。其中本仓写的约 890 词：对上游 diff 的新增词，`SKILL.md` 约 282、`AGENT-BRIEF.md` 约 214（多数是替换），加上整份 `pipeline-issues.md`。`OUT-OF-SCOPE.md` 与上游逐字相同。

主要问题不是冗余，是覆盖面。本仓写的部分可删的只有约 80–100 词（复述 `route` 做了什么、重复的“读事件轨迹”、两处永远为真的条件），外加上游说明页里一段没有 agent 会读的副本（约 95 词）。真正的问题是：技能的主线是上游的“处理外来 issue”，而这一支在两个仓库 1300 张 issue 里一次都没发生过（`gh issue list --state all` 统计作者：multi-model-workflow 583 张、agentflow 717 张，作者全是 `chancheuklap`）。实际进入 `needs-triage` 的是流水线自己的产物，其中三类技能认不出来（`ticket.regressed` 重开的票、夜里因 `contract` 停下的未开工票、retro proposal）。认得出的那几类里，`became-ticket` 这一条漏了把票放回 agent 队列的那一步。

灵魂：上游部分（先验证再下判断、推荐后等人拍板、拒绝理由要经得起时间）完整。本仓部分缺一段话，告诉 agent 在 MMW 里早上的 triage 是什么：用户一天里第一件事，是把夜里卡在需要判断的地方的东西逐个变成一句话能拍板的决定，再把工作放回流水线。建议补约 250–300 词、删约 90 词，技能净增少许。

## A. 删除或改成脚本

| # | 位置 | 类别 | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `references/pipeline-issues.md` `## ready-for-agent` 表第二行，“which moves `<m>` under the spec, swaps its layer label `mmw:child` for `mmw:ticket`, and records the route on the ticket it came from” | 1 | `mmw-v2/skills/dispatch/scripts/dispatch.sh` `route_child()`（4399–4421 行）做的就是这三件事，结束时 stderr 打出 `#<child> became ticket #<n> under #<spec>` | `route` 自己做、自己报告；无剩余风险 | 删掉这段说明，只留命令；腾出的位置写脚本**不做**的事（见 B 缺口 G6） |
| A2 | `references/pipeline-issues.md` `## Gather context`，“First read the parent issue (the `parent:` line of `gh issue view <m>`, or `gh api … parent_issue_url`; the REST object has no `parent` field)” | 1 / 6 | `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` `run_sub_issue()`（1580–1640 行）创建的每个 child，正文第一行都是 ``A `<kind>` child of #<n>.``，类型和父票都在里面（实例：#586 ``A `decision` child of #570.``） | child 正文第一行；有人手改过第一行时，父票上的 `child.opened` 事件是准的。REST 那句注释修过一次真实错误（提交 `cf7b8f01`），查父的步骤删了它也就不需要了 | 换成一句：child 正文第一行写着它的类型和开它的票 |
| A3 | `references/pipeline-issues.md` `## Gather context` 与 `## A ticket handed back` 两处都写“read … event trail (its `ticket.checked` runs and its `reviewer.reported`) instead of reproducing” | 6 | 同一文件两节，同一句意思 | 合并后的那一节 | 合进 B 缺口 G1 草稿里那张按来源分的清单，只写一次 |
| A4 | `SKILL.md` 第 5 步开头，“`needs-info`, `ready-for-human`, and `wontfix` move nothing: the parent stays.” | 2 | “parent”只对流水线的 child 有意义；外来 issue 没有父票，这句却放在所有人都读的第 5 步里 | 挪到 `pipeline-issues.md` `## ready-for-agent`，写成“只有 `ready-for-agent` 会移动 child，其余出口都把它留在原票下” | 在 `SKILL.md` 删掉，`mmw-v2/merge-notes/triage.md` 对应一行跟着改 |
| A5 | `references/pipeline-issues.md` `## ready-for-agent`，“When the parent is a ticket, pick one destination” | 5 | 带 `mmw:child` 的 issue 只由 `run_sub_issue()` 以 `--parent <ticket>` 创建；变成 ticket 以后 `route` 会摘掉 `mmw:child`。进到这份 reference 的 child，父一定是票。前两问的答案都是“否” | 无须承担 | 删掉这个条件 |
| A6 | `mmw-v2/upstream/docs/engineering/triage.md` `## Verify before you brief` 第二段，“A ticket handed back by this repository's own pipeline already carries that evidence…” | 6 / 2 | 没有技能引用 `mmw-v2/upstream/docs/`（grep 过全仓），`mmw-v2/skills.txt` 只安装 `skills/` 下的目录，所以这一段没有 agent 会读到。它复述的是 `pipeline-issues.md` `## A ticket handed back`。同一页别处仍按上游写着相反的话（59 行 “the brief is the contract”，36 行 `ready-for-human` 的四个理由，97 行 “opens with” 免责声明），加这一段并没有让整页变对 | `pipeline-issues.md` 是 agent 实际加载的那份；这一页只给人看，而用户不读代码仓 | 恢复上游原文，删掉 merge-note 里 “docs page 的 `Verify before you brief`” 一行。注意：`to-spec`、`code-review`、`implement` 的 merge-note 也在同样维护说明页，是否整体停止这种做法，要一起定 |

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 5 步 “Staying at `needs-triage` is not an outcome.”：逼 triage 以一个决定收尾。否则同一张 issue 明早会被一个上下文更少的人再读一遍。
- `SKILL.md` `## Roles` “Work this repo plans for itself carries no category role: … a map, a spec and a decision ticket carry none and are not triaged.”：没有它，spec 和 decision ticket 身上没有 triage label，会被 `## Show what needs attention` 的 “Unlabeled” 一栏当成从没 triage 过的 issue 列出来。
- `SKILL.md` 第 5 步 `ready-for-human` 的 “nothing more”：用户早上打开的 `ready-for-human` 队列里，有 `to-tickets` 写的票，也有这里写的票，两边必须是同一个形状。
- `references/pipeline-issues.md` “skip `.out-of-scope/`: nobody rejected this request.”：一句话带着理由，agent 碰到清单外的情况时能自己推下去。
- `references/pipeline-issues.md` “Judging an issue agent-ready also answers where the work is done.”：把“贴 label”改成“决定工作在哪里做”，是这份 reference 存在的理由。
- `AGENT-BRIEF.md` 开头两段（“It is the record of the investigation, kept on the issue so it outlives the session that did the work.”，以及交给 `to-spec`、`to-tickets` 那一段）：说清楚这份东西给谁读、为什么要经得起时间。
- `AGENT-BRIEF.md` `### Complete acceptance criteria` “A finding nobody can check is an opinion.”，以及 `### Explicit scope boundaries` “It keeps the spec written from this agent brief on the request that was actually made”：两句都讲这条原则保护的是什么。
- 上游原文（不改，也不删）：第 1 步 “by domain concept (not just the request's wording), and report where you looked”；第 3 步 “insufficient detail (a strong `needs-info` signal)” 与 “A confirmed verification makes a much stronger agent brief”；`## Needs-info template` 下 “Questions must be specific and actionable”；`OUT-OF-SCOPE.md` “those aren't real rejections, they're deferrals” 与 “recording it would poison the dedup checks”。

### 缺口与补充草稿

- **G1 `references/pipeline-issues.md` 开头，以及 `SKILL.md` `## Triage a specific issue or PR` 开头那句把 issue 送过去的话。** 缺的是：在 MMW 里 `needs-triage` 队列装的是什么，用户要从 triage 拿到什么。现在技能主线是上游的外来 issue（复现报告人的步骤、查 `.out-of-scope/`），而两个仓库里一张外来 issue 都没有（见结论）。按 `docs/agents/issue-tracker.md` `## Morning queries`，triage 是用户早上第一件事（“Run the triage skill over it before anything else”）。agent 不知道这一点，就会把每张 issue 当成陌生人的报告从头调查，或者只贴个 label，却不把问题收成一句用户能拍板的话。建议把 `SKILL.md` 那句的触发条件改成只看 label：“An issue labelled `mmw:child` or `mmw:ticket`, or a retro proposal, came from this repository's own pipeline”。不必再判断 “newest result”，因为出现在 `needs-triage` 里的 `mmw:ticket` 都来自流水线。`pipeline-issues.md` 开头写：
  > Almost everything in this repository's `needs-triage` queue was put there by the pipeline, not by a reporter: a worker, a review, a merge or a re-run stopped because the next step needs a judgement no script can make. The user reads this queue first thing in the morning. For each item, find what the pipeline already established, turn it into one question the user can answer in a sentence, give your recommendation with its evidence, and once the user decides, put the work back where the pipeline picks it up. The evidence is already on the tracker; reproducing is rarely needed. Read a ticket's events with `python3 <events.py> fold <n>` (`<events.py>` is `scripts/events.py` of the `verify-ticket` skill). An item left in `needs-triage` is read again tomorrow by someone with less context than you have now.
  >
  > - **A child a worker opened** (`mmw:child`; its body opens ``A `<kind>` child of #<n>.``). The kind says what the user is asked. `decision`: the worker already took the default it names; confirm it or overturn it. `contract`: which authority wins; the not-yet-started tickets the night moved to `needs-triage` wait on the same answer. `deferred`: whether a convenient change outside `## Owns` is worth a ticket. `fault`: what in the pipeline broke, here or in the toolbox. `finding`: normally routed on the night's closing pass; an open one is one that pass did not reach.
  > - **A ticket its worker handed back** (fold `returned`): see `## A ticket handed back`.
  > - **A ticket that bounced twice** (fold `bounced`): the same section.
  > - **A landed ticket `reverify` reopened** (fold `regressed`): the same section.
  > - **A ticket with no result that a night parked** (`mmw:ticket` in `needs-triage`, not started): it waits on an open `contract` child of its batch that names it. Settle that child, then move every ticket it parked back to `ready-for-agent` together.
  > - **A retro proposal** (title `Retro #<spec>: …`; body `Problem`, `Sources`, `Prevention`, `Destination`): the retro already gathered the evidence. The user approves it or not; approved work goes through the `to-spec` and `to-tickets` skills like any other agent work.

  这样能改变 agent 做法的地方：它先按来源找现成的证据，不再去复现；它问的是用户一句话能答的问题，而不是只报一个 label。

- **G2 `references/pipeline-issues.md` `## A ticket handed back` 缺 `ticket.regressed`。** 证据：`docs/contexts/tickets/CONTEXT.md` `**needs-triage**` 条目把 “a landed ticket `reverify` reopened” 列为这个队列的来源；`dispatch.sh` 的 reverify 分支（3631–3650 行）重开票、加 `needs-triage`、写 `ticket.regressed`；`mmw-v2/skills/dispatch/scripts/status.py` `regressed_in_triage()` 的 docstring 写着 “Triage hands it to a worker by swapping that label for `ready-for-agent`”。真实发生过：#472、#491 连续两夜（见 #507），agentflow #731（见 #413）。可 `SKILL.md` 送进 reference 的条件只有 `ticket.returned` 与 `ticket.bounced`，一张重开的票会走外来 issue 那一支：复现报告人步骤，到 `ready-for-agent` 时“write a spec … close this issue”，也就是把一张已登记的票关掉再另写一份 spec。草稿（接在该节 `ticket.bounced` 那句后）：
  > `ticket.regressed` means a landed ticket's criteria went red on the base branch. Read the commit it names and which criteria failed, and the sibling tickets that landed since: often a later ticket broke it, and the fix belongs there. While it still wears `needs-triage`, every `reverify` re-runs it and closes it again once it is green, so a regression something else already fixed needs no outcome from you.

- **G3 `references/pipeline-issues.md` `## A ticket handed back` 缺退回票最直接的证据。** 这一节让 agent 读 `ticket.checked` 与 `reviewer.reported`，没提 `HANDOFF REQUIRED` 收尾评论里的 `ABANDON:` 行。按 `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 97 行，这些行写明是 `failed`、`stuck` 还是 `decision`，也写明每一轮试了什么。这正是选出口时要用的判断，缺了它 agent 容易原样打回 `ready-for-agent`，第二夜再失败一次。草稿：
  > For `ticket.returned`, the closing comment's `ABANDON:` lines say why, and the kind points at the outcome. `stuck` on a credential, a device or a real environment is usually `ready-for-human` of kind `reach`. `failed` after rounds that each tried something raises one question: would a changed criterion, a split ticket or a `senior-worker` grade pass? Sending it back unchanged repeats the night. The worker's partial work stands in `.worktrees/issue-<n>`.

- **G4 `references/pipeline-issues.md` `## ready-for-agent` 表第二行漏掉放回队列。** `route … became-ticket` 不碰队列 label（`route_child()` 4399–4421 行只改 `mmw:ticket`、`mmw:child` 和父票），而 child 是带着 `needs-triage` 创建的（`run_sub_issue()`）。这一行说的完成标准是 “`--lint <m>` passes”，可 `verify-ticket.py` `lint_worker()`（2582 行）对不在 agent 队列里的票直接判为干净。frontier 只收带 `ready-for-agent` 的票（`status.py` 411、457、660 行）。照这一行做完，新票会一直停在 `needs-triage`，没有人派工。`mmw-v2/skills/dispatch/references/night.md` 处理同一件事时写了 “label it for the agent queue”。这一条是从代码推出来的，tracker 上没找到 triage 走过这一行的实例。草稿（替换 A1 删掉的那段说明）：
  > It leaves the queue labels alone: rewrite the body to `<issue-template>` (in `to-tickets`), swap `needs-triage` for `ready-for-agent`, add `junior-worker` or `senior-worker`, and lint it. `--lint` passes a ticket outside the agent queue, so it will not catch a missing label.

  第一行（改挂到另一张票下）同样缺一个条件：按 `implement/SKILL.md` 第 20 行，worker 只在开工时读一次本票的 open sub-issue。早上 triage 时这一批的票多数已经落地。草稿：
  > Only a ticket not yet started reads it: a worker reads its ticket's open sub-issues once, when it starts.

- **G5 `references/pipeline-issues.md` 最后一段的交接只写了开夜的情况。** “The next `advance` on its spec … starts a worker” 只在这份 spec 还有夜开着时成立。`mmw-v2/skills/dispatch/references/one-ticket.md` 第 4 步说，夜外 `land` 失败的票也会进 `needs-triage`；`dispatch.sh`（2249–2257 行）的提示也分开夜、没开夜两种。草稿（接在该段末尾）：
  > With no night open on its spec, the `dispatch` skill's one-ticket run starts it instead.

- **与 `SKILL-SET-REVIEW.md` 的冲突**：G1 草稿最后一句（“An item left in `needs-triage` is read again tomorrow …”）按 `### Redundancy and bloat` 的 No-op 条可能被当作空态度删掉。依本任务书应保留：它讲的是后果，推着 agent 把每张都收成一个决定，这正是 “Staying at `needs-triage` is not an outcome.” 背后的理由。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `SKILL.md` 第 5 步 “the four outcomes are `needs-info`, `ready-for-agent`, `ready-for-human` and `wontfix`” | 封闭的四选一，漏掉了实际最常见的收尾：`decision` child 的默认值被确认、问题已经在 base branch 上修好、或者小到当场就能修。结果 agent 各自发挥：agentflow #620、#621、#622、#629 写着“已在 commit … 直接改完”，却打了 `wontfix`（意思是“不会做”）；本仓 #265、#283 写“已在基线分支上修掉”，关掉时没有出口 label，也没有经过 `route`，原票上就没有 `child.closed`（`mmw-v2/board/board_data.py` 读这个事件）。另一边，`night.md` `## 4. The closing pass` 对同类 child 明写 “The default is to fix it, not to open a ticket”，并且有 `route … fixed / stale` 两个出口 | 加一句结束标准。**要不要允许早上的 triage 自己动手修，由用户定**（见最终回复）。草稿：“Some items end here: the worker's default was right, the fix is already on the base branch, or the user has you make it now. Close a child through `<dispatch> route <ticket> <child> fixed` or `stale <invalid\|fixed-elsewhere>` so its ticket records the route. `wontfix` means nobody will do it, not that it is done.” |
| — | `SKILL.md` 第 5 步外来 issue 的 `ready-for-agent` 四步（brief → `to-spec` → 关 issue → `to-tickets`） | 不算死板：顺序真有依赖（`to-spec` 把 brief 当来源读；关 issue 时要链接到 spec；`to-tickets` 要从 spec 切票） | 保留 |
| — | 上游第 1–5 步编号流程 | 上游原文，在 MMW 里不会让 agent 做错 | 不报 |

## 脚本

无。技能自身没有脚本。它依赖的脚本行为已写在 A1、B G4 里（`dispatch.sh` `route_child()`、`verify-ticket.py` `lint_worker()`、`run_sub_issue()`）。我没有在这些函数里看到属于本技能的过度防御或死代码。

## 与其他技能的重复或交接问题

- `mmw-v2/upstream/docs/engineering/triage.md` 第二段与 `references/pipeline-issues.md` `## A ticket handed back`：留 reference，删说明页那段（A6）。
- `became-ticket`：`references/pipeline-issues.md` 表第二行与 `mmw-v2/skills/dispatch/references/night.md` `## 4. The closing pass` “The ones that become tickets” 一段，分别在 triage 和夜里主 agent 行动的那一刻加载，两份都留。`night.md` 那份更完整（有 “label it for the agent queue”），triage 这份按 G4 补齐。
- `docs/contexts/tickets/CONTEXT.md` `**needs-triage**` 的 `_Home_` 指向 triage 的 `SKILL.md`，可 `SKILL.md` 自己没列这个队列的来源。按 G1 补上来源清单以后，`_Home_` 应改指 `references/pipeline-issues.md`，同一条再补上 retro proposal 和夜里停下的未开工票两种来源。
- `mmw-v2/skills/retro/scripts/retro.py` `create_or_reuse()`（606 行）把 proposal 开成 `needs-triage`；`mmw-v2/skills/retro/SKILL.md` 第 15 行写 “Work the user approves applies the improvements later, through the normal spec and ticket flow”。retro 这边交代了去处，triage 这边没接住（G1 清单最后一条）。
- `mmw-v2/skills/design-pages/references/pull.md` 第 45 行会把夜里停下的票移回 `ready-for-agent`，只覆盖 Claude Design 那一种 `contract`；其余 `contract` 靠 triage（G1 清单“A ticket with no result that a night parked”）。

## 没查到的

- 没有真的跑一次 triage；G4（`became-ticket` 后停在 `needs-triage`）是从代码推出来的，tracker 上没找到 triage 走过这一行的实例（`became-ticket` 搜到的 #292 来自夜里的收尾步骤）。
- `## ready-for-agent` 表第三行（转到工具箱仓）：用 GraphQL 查了本仓最早 100 张和最新 100 张 issue 的 `TransferredEvent`（共约 583 张），都没有，所以这一行没触发过。它是正常输入能走到的（consuming repository 里的 `fault` child），不算过度防御。另一处推断没有验证：转移以后，正文第一行 `A … child of #<n>` 里的 `#<n>` 会按工具箱仓去解析，指向错误的 issue。
- `events.py fold` 的 `outcome` 字段是什么意思没有核实。G1 草稿只用了 `returned`、`bounced`、`regressed` 三个布尔字段（在 #491 上跑过 fold，确认有这三个字段）。
- `night.md` 只读了 `## 4. The closing pass` 与第 3 步的唤醒表，没读全文；`to-tickets` 的 `references/person-ticket.md`、`to-spec` 的 `references/revising-a-spec.md` 没打开，只确认 triage 指过去的路径与 merge-note 一致。
- `AGENT-BRIEF.md` 与 `OUT-OF-SCOPE.md` 在两个仓库都没有真实用例（没有外来 issue；两个仓库都没有 `.out-of-scope/` 目录），无法用实际使用去判断它们在 MMW 里的效果。
