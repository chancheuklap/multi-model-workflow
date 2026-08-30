# 07 角色名与标签 / 状态机

审计范围：`CONTEXT.md`、`AGENTS.md`、`docs/agents/`、`docs/adr/`、`mmw-v2/`（排除 `upstream-diagram-design`、`upstream/docs`、`upstream/CHANGELOG.md`、`upstream/README.md`、`upstream/skills/in-progress`）。

---

## 目录：每个角色的全部叫法

先给两张清单，正文的发现引用它们。

### A. 角色名清单

| 角色 | 定义在哪 | 各文件用的叫法 |
| --- | --- | --- |
| main agent | `CONTEXT.md:11-13` | `main agent（主 agent）`；`mmw-v2/skills/dispatch/models.md:4` 「the orchestrator」；`mmw-v2/skills/dispatch/SKILL.md:70-71` 「you / your own pane」；脚本里是 Herdr 名 `mmw-main`（`dispatch.sh:36`、`board.py:498`） |
| worker | `CONTEXT.md:15-17` | `worker`（`verify-ticket/SKILL.md:30-33`、`dispatch/SKILL.md:32`、`board.py:287`）；`implement/SKILL.md` 全篇只用「you」，一次都没出现 worker；Herdr pane token `role=worker`（`dispatch.sh:240`） |
| junior-worker / senior-worker | `CONTEXT.md:19-25` | 只在 `models.md:24-25` 与 `dispatch/SKILL.md:32` 出现；`board.py:941` 的 `--role` 默认值 |
| verifier | `CONTEXT.md:27-29` | `verifier`（`agents/verifier/body.md:1`、`models.md:27-31`）；`merge-notes/implement.md:15` 写「verifier 子代理」——CONTEXT.md 把它列进 `_Avoid_` |
| reviewer | `CONTEXT.md:31-33` | `reviewer` = 整个 code-review 会话（`models.md:26`、`dispatch/SKILL.md:32`）；`merge-notes/code-review.md:5,43` 里 `reviewer` = 三个子代理之一；`merge-notes/implement.md:15` 写「reviewer 会话」——`_Avoid_` 里的词 |
| dispatcher | `CONTEXT.md:35-37` | code-review 里的派发者（`code-review/SKILL.md:6`、`merge-notes/code-review.md:5,7,19,22,33,40,43`）；同时 `board.py:58,241,287`、`hook.py:20`、`verify-ticket.py:753,781` 用 `dispatcher` 指 `dispatch.sh` 这个脚本 |
| user | `CONTEXT.md:39-41` | `user`（`dispatch/SKILL.md:106`）；`the maintainer`（`triage/SKILL.md:40,48,65,71,89`）；`the reporter`（`triage/SKILL.md:44,73`、`docs/agents/triage-labels.md:8`）；`human`（`docs/agents/triage-labels.md:10`）；`your / you`（`docs/agents/triage-labels.md:20`、`CONTEXT.md:598`）；`a person`（`dispatch/SKILL.md:62`、`implement/SKILL.md:36`）；`the driving dev`（`docs/agents/issue-tracker.md:41`） |
| 底层词 host | 未登记 | `host`（`models.md:22` 表头、`agent.json` 的 `"hosts"`）／`harness`（`models.md:9,15,16`、`references/editing-models.md` 全篇）／`宿主`（`AGENTS.md:19-22`、`assemble.py:39-41`）／`agent kind`（`editing-models.md:26`）／Herdr 的 `agent` 字段（`board.py:271`） |
| 底层词 session / subagent | `models.md:7-11` 划的线 | session = 有 launch arguments、跑在 Herdr pane 里；subagent = launch arguments 是 `—`、跑在派它的 session 里。CONTEXT.md 的 Roles 段与这条线一致（worker/reviewer 是 session，verifier 是 subagent） |

### B. 五个标签的语义清单

| 标签 | `CONTEXT.md` | `docs/agents/triage-labels.md` | `triage/SKILL.md` |
| --- | --- | --- | --- |
| `needs-triage` | :586「something arriving from outside, or a ticket an agent could not finish」 | :7「Maintainer needs to evaluate this issue」／:21 同 CONTEXT.md | :32「maintainer needs to evaluate」／:60「evaluation in progress」 |
| `needs-info` | :590「Waiting on more information.」（没有主语） | :8「Waiting on reporter for more information」 | :33 同左；:44「returns to `needs-triage` once the reporter replies」 |
| `ready-for-agent` | :594 队列 + assignee 说明在不在做 | :9「ready for an AFK agent」／:19 同 CONTEXT.md | :34 同；:38 PR 语义 |
| `ready-for-human` | :598 必须是 `reaction` 或 `reach` 两类之一 | :10「Requires human implementation」／:20「一行说明为什么不能委派」 | :35；:79「四个理由：judgment calls, external access, design decisions, manual testing」 |
| `wontfix` | :610「Will not be done.」 | :11「Will not be actioned」 | :81-84 三种子情况，其中 rejected enhancement 要写 `.out-of-scope/` |

---

## 发现 1：`ready-for-human` 票必须带什么，四份文件给四种规定
- 类型：分岔
- 后果：triage 判出来的 `ready-for-human` 票带一行散文理由，to-tickets 写出来的同标签票带 `reaction`/`reach` 一个词加五个字段；两种票混在同一个队列里，早上读票的人拿不到同一组信息，而 `to-tickets` 第 8 步的回读又只按后一种核对，triage 出的票核不过也没人核。
- 证据：
  - `CONTEXT.md:598` 「In your queue: a ticket carrying one thing only a person can do, **of kind `reaction` or `reach`**, naming what to look at and what makes it right. Applied when the ticket is written, **or by triage once it has judged**.」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:79` 「`ready-for-human`: same structure as an agent brief, but **note why it can't be delegated (judgment calls, external access, design decisions, manual testing)**.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:81` 「Write one such ticket per thing to be looked at, labelled `ready-for-human`. It is shorter than the template below and **holds five things only**」（:84 「**Which kind**: *reaction* or *reach*, in one word.」）
  - `docs/agents/triage-labels.md:20` 「`ready-for-human` means the ticket is in your queue, and **the ticket says in one line why it cannot be delegated**.」
  - `mmw-v2/merge-notes/to-tickets.md:21` 「上游给的四个理由是「判断、只有人有的访问权、设计决定、手工测试」，**这四个词现在是混的**……改成两类」——merge-note 自己说这四个词已经废了，但 `triage/SKILL.md:79` 里原样还在，merge-notes 里也没有一条覆盖 triage 的这一段（`mmw-v2/merge-notes/triage.md` 全文只管 frontmatter 一行）。
- 建议正名：以 `to-tickets/SKILL.md:81-87` 的五样加 `reaction`/`reach` 为准（`CONTEXT.md:598` 已经这么写）。把 `triage/SKILL.md:79` 的四个理由改成同一套，并在 `merge-notes/triage.md` 里记一条；`docs/agents/triage-labels.md:20` 那一行改成指向这套，不要另起措辞。

## 发现 2：`ready-for-human` 票到底核「四样」还是「五样」，同一份 merge-note 里自相矛盾
- 类型：分岔
- 后果：做回读那一步的 agent 不知道要核几项；照 `:19` 找不到第四项是什么，照 `:21` 又和 `to-tickets/SKILL.md:136-139` 实际列的两条核对项对不上。
- 证据：
  - `mmw-v2/merge-notes/to-tickets.md:19` 「`ready-for-human` 的票核**它自己该有的四样**」
  - `mmw-v2/merge-notes/to-tickets.md:21` 「同时列明这种票必须给到的**五样**：Parent、是哪一类、看什么……、什么算对、Blocked by」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:136-139` 回读那一步实际只列两条：「- The kind is named, *reaction* or *reach*.」「- **What to look at** is a link that opens, and **what makes it right** is there to judge against.」
- 建议正名：统一成「五样」，并把回读那两条补全成五条逐项核对，或明写回读只核其中哪三样、为什么另两样由别的步骤保证。

## 发现 3：`/triage` 的「四个 outcome」在任何一份 triage 文档里都没有列出来
- 类型：断点
- 后果：`CONTEXT.md` 与 `docs/agents/triage-labels.md` 都让读者去 `/triage` 找「四个 outcome」，而 `triage/SKILL.md` 的「Apply the outcome」一节列的是**五**条（多一条 `needs-triage` 自身），状态转移那句列的是**四**个但没有叫它 outcome。读者走到这里数不出是哪四个。真正把四个数出来的地方是一句代码注释，谁都不会读到。
- 证据：
  - `CONTEXT.md:586` 「`/triage` reads it and recommends **one of the four outcomes**.」
  - `docs/agents/triage-labels.md:21` 「`/triage` reads it, reproduces what it can, and recommends **one of the four outcomes**.」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:77-85` 「5. **Apply the outcome:**」下面五条：`ready-for-agent` / `ready-for-human` / `needs-info` / `wontfix` / `needs-triage`
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:44` 「from there it moves to `needs-info`, `ready-for-agent`, `ready-for-human`, or `wontfix`」（四个，但没写「outcome」这个词）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:135-136` 「A worker that could not finish has not established what the ticket needs next — **a person, more information, another agent, or nothing at all**.」——这是唯一把四个数清楚的地方，写在一段 docstring 里
- 建议正名：在 `triage/SKILL.md` 的「Apply the outcome」标题下明写「四个 outcome：`needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`；`needs-triage` 是留在原地不是 outcome」，`CONTEXT.md:586` 与 `docs/agents/triage-labels.md:21` 保持现有措辞不动。

## 发现 4：`needs-triage` 承接「agent 没做完的票」，但 `/triage` 全篇按「外来 issue + reporter」写，没有这条支路
- 类型：断点
- 后果：夜里 `board.py` 与关票门把票交回 `needs-triage`，指望 `/triage` 第二天自己捡起来；`/triage` 的三个 bucket、第 1 步的「reproduce it from the reporter's steps」「read `.out-of-scope/*.md`」、第 3 步的 Verify the claim，对一张自家没做完的票全都不成立，agent 走到这里没有可执行的步骤，只能自由发挥。
- 证据：
  - `CONTEXT.md:586` 「Nobody has judged it yet: something arriving from outside, **or a ticket an agent could not finish**. The one queue a skill picks up on its own」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:134-138` 「A worker that could not finish has not established what the ticket needs next……`needs-triage` is that state, and **it is the one queue a skill picks up on its own**.」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:57-61` 三个 bucket：「1. **Unlabeled**: never triaged. 2. **`needs-triage`**: evaluation in progress. 3. **`needs-info` with reporter activity since the last triage notes**」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:69` 「For a bug, reproduce it from the **reporter's** steps……(b) **prior rejection**: read `.out-of-scope/*.md`」——本仓根目录没有 `.out-of-scope/`，唯一一份是上游自己的 `mmw-v2/upstream/.out-of-scope/`
  - `mmw-v2/skills/dispatch/scripts/board.py:768-769` 「gh(["issue", "edit", str(number), "--remove-label", "ready-for-agent", "--add-label", "needs-triage"])」
- 建议正名：在 `triage/SKILL.md` 加一条支路「一张 `needs-triage` 的票带着 `HANDOFF REQUIRED` / `WAKEUP LIMIT:` / `TIME LIMIT:` / `REDISPATCHED:` 首行的评论时，读那条评论而不是 reporter，跳过复现与 `.out-of-scope/`」，并在 `merge-notes/triage.md` 记一条。

## 发现 5：`bug` / `enhancement` 两个 category role 在本仓的标签映射表里没有行
- 类型：断点
- 后果：`/triage` 要求每张 triage 过的票带一个 category role，又说 role 到真实标签串的映射「应该已经给你了，没有就叫用户跑 `/setup-matt-pocock-skills`」；本仓的映射表只有五个 state role，agent 走到这里要么去建两个没登记的标签，要么按 `triage/SKILL.md:42` 让用户重跑 setup——而重跑 setup 会覆盖掉这张表（见发现 15）。
- 证据：
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:40` 「**Every triaged issue should carry exactly one category role and one state role.**」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:42` 「These are canonical role names. The actual label strings used in the issue tracker may differ. **The mapping should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.**」
  - `docs/agents/triage-labels.md:5-11` 表里只有 `needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix` 五行，没有 `bug` / `enhancement`
  - `docs/agents/triage-labels.md:24` 「The category roles `bug` and `enhancement` belong to work arriving from outside. Tickets this repo plans for itself……**carry a state role and no category**.」——直接推翻 `SKILL.md:40` 的「every triaged issue」
  - `AGENTS.md:32` 「**五个规范角色**用默认标签串（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）」——只认五个
- 建议正名：以 `docs/agents/triage-labels.md:24` 为准（本仓自建票不带 category），并把这条例外写回 `triage/SKILL.md:40`，`merge-notes/triage.md` 加一条；或者把 `bug` / `enhancement` 两行补进映射表。待用户拍板选哪条。

## 发现 6：`frontier` 一个词五种定义，`board.py` 不看 `## Owns`
- 类型：分岔
- 后果：`CONTEXT.md` 说 frontier 的**硬规则**是同一 frontier 上两票 `## Owns` 不得相交；`board.py` 实际挑票时根本不读 `## Owns`。夜里两张 Owns 相交的票会被同时派出去，两个 worker 在两个 worktree 里改同一个文件，谁都不违反自己读到的那份规则。
- 证据：
  - `CONTEXT.md:98` 「The set of tickets that may be worked in parallel right now. **The hard rule: no two tickets on one frontier may have overlapping `## Owns`.**」
  - `mmw-v2/skills/dispatch/scripts/board.py:370-379` 「Open, in the agent lane, every blocker closed, nobody has claimed it, and no live session already holds it.」条件是 `state == "OPEN"` / `"ready-for-agent" in labels` / `not blockers` / `not assignees` / `worker is None`——整个 `board.py` 里 `owns` 零命中
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:118` 「Work the **frontier**: any ticket whose blockers are all done.」（只有 blocker 一条）
  - `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md:68` 「the **frontier** is the open, unblocked, unclaimed children, the edge of the known」
  - `mmw-v2/upstream/skills/productivity/grilling/SKILL.md:8` 「The **frontier** is every **decision** whose prerequisites are already settled」——指的是问题集合，不是票
- 建议正名：`## Owns` 不相交这条硬规则的执行点是出票时的回读（`to-tickets/SKILL.md:133`），不是夜里的挑票。把 `CONTEXT.md:98` 改成分两句：frontier 是「open + `ready-for-agent` + 无 blocker + 无 assignee + 无活会话」（照 `board.py` 抄），`## Owns` 不相交是出票时的判据而不是 frontier 的定义。`grilling` 那个 frontier 是另一件事，在 `CONTEXT.md` 里点名它不是同一个词。

## 发现 7：哪个 worker 跑在哪个宿主，`CONTEXT.md` 与 `models.md` 各写一遍，而 `AGENTS.md` 说只改 `models.md`
- 类型：分岔
- 后果：把 `models.md` 里 junior-worker 从 cursor 换到别家，照 `AGENTS.md:21` 就算改完了；`CONTEXT.md` 里那句「running on cursor」原地不动，下一个空上下文的会话读词汇表读到的是旧的。
- 证据：
  - `AGENTS.md:21` 「起会话的命令、**每个 agent 用哪个宿主哪个模型哪档思考强度，只改 `mmw-v2/skills/dispatch/models.md`**。」
  - `mmw-v2/skills/dispatch/models.md:3-4` 「One row per `(agent, host)`. Every agent this pipeline sends out is here……**This is the only place any of their models are written down.**」
  - `CONTEXT.md:20` 「The junior grade of worker, **running on cursor**.」
  - `CONTEXT.md:24` 「The senior grade of worker, **running on grok**.」
  - `CONTEXT.md:32` 「**The Claude Code session** a worker starts through Herdr to run one round of code review.」
  - `mmw-v2/skills/dispatch/references/editing-models.md:23` 「Only the rows with launch arguments **can move to another harness**.」——明说 reviewer 那一行可以换家
- 建议正名：`CONTEXT.md:20/24/32` 删掉宿主名，改成「the junior grade of worker」「the senior grade of worker」「the session a worker starts through Herdr to run one round of code review」，宿主只留在 `models.md`。

## 发现 8：`role` 一个词四义，其中两义在同一个脚本里同时使用
- 类型：命名撞车
- 后果：读 `dispatch.sh <ticket> <role>` 的人以为 `role` 的取值是 `junior-worker` / `senior-worker` / `reviewer`；去读 Herdr pane 上那个也叫 `role` 的 token，取到的是 `worker` / `reviewer`。`CONTEXT.md:407` 登记了这个 token 却没写它的取值集合，两边对不上时读者以为 token 坏了。
- 证据：
  - `mmw-v2/skills/dispatch/SKILL.md:32` 「| `<role>` | `junior-worker`, `senior-worker` or `reviewer`.」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:236-241` 「`token_role=reviewer`」/「`token_role=worker`」，:244 「`--token "role=$token_role"`」
  - `mmw-v2/skills/dispatch/scripts/board.py:256` 「`role = "reviewer" if named.group(2) else "worker"`」与 `board.py:525` 「`self.role = role`」（这个 role 是 `junior-worker`）在同一个类里并存
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:95-96` 「Prints ……for the first row whose **agent column** is the **role** asked for.」——脚本自己承认表头叫 `agent`、参数叫 `role`
  - `mmw-v2/skills/dispatch/models.md:22` 表头是 `| agent | host | model | effort | launch arguments |`；`CONTEXT.md:392` 也写「for every **agent**」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:25-30` 「Two **category** roles……Five **state** roles」——第四义，指标签
- 建议正名：给两个 token 取值起不同的词：CLI 参数保持 `<role>`（`junior-worker` / `senior-worker` / `reviewer`），pane token 改名 `kind`（`worker` / `reviewer`），并在 `CONTEXT.md:407-408` 写明取值集合。`models.md` 表头 `agent` 与 `dispatch/SKILL.md` 的 `<role>` 二选一，统一成一个词。triage 那一套叫 triage role，`CONTEXT.md` 里点名它不是同一个词。

## 发现 9：`dispatcher` 既指 code-review 里的派发者，也指 `dispatch.sh` 这个脚本
- 类型：命名撞车
- 后果：`board.py` 的注释说「the dispatcher gives it `issue-<n>`」，`hook.py` 说「the dispatcher sets `MMW_TICKET`」——读者按 `CONTEXT.md:35-36` 查这个词，查到的是 code review 里那个起子代理的角色，两件完全不同的东西。
- 证据：
  - `CONTEXT.md:35-36` 「**dispatcher（派发者）**: **Inside code review**, the role that starts the two reviewing subagents, collects both reports, and writes the comment.」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:6` 「You are **the dispatcher**. You run three read-only sub-agents over one diff」
  - `mmw-v2/skills/dispatch/scripts/board.py:241-244` 「**the dispatcher** gives it `issue-<n>` before it prompts, and only **the dispatcher** uses that name」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:20` 「It is told: **the dispatcher** sets `MMW_TICKET` on the worker's pane.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:781` 「`NOT_READY: #{number} is blocked by {names}; stop — **the dispatcher** `」
- 建议正名：脚本注释里的 `the dispatcher` 全改成 `dispatch.sh`（那是它的字面名，`CONTEXT.md:383` 已经登记）；`dispatcher（派发者）` 只留给 code review 里那个角色。

## 发现 10：`CONTEXT.md` 说 dispatcher 起「两个」reviewing subagent，实际是三个
- 类型：分岔
- 后果：读词汇表的人以为 code review 有两个轴；`CONTEXT.md` 自己在 `:497-507` 又定义了三个轴。同一份文件里数不对。
- 证据：
  - `CONTEXT.md:36` 「the role that starts **the two reviewing subagents**, collects **both** reports, and writes the comment」
  - `CONTEXT.md:497-507` 「**`Standards` axis**: **One of the three axes**……**`Spec` axis**: The second axis……**`Tests` axis**: The third axis」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:6` 「You run **three** read-only sub-agents over one diff……you are the only one of **the four agents** that writes anything.」
  - `mmw-v2/merge-notes/code-review.md:5` 「我们把**三个 reviewer** 的判据各拆一份出去……并加了第三个轴。」
- 建议正名：`CONTEXT.md:36` 改成「the three reviewing subagents……collects all three reports」。

## 发现 11：`reviewer` 既指整个 code-review 会话，也指它起的三个子代理
- 类型：命名撞车
- 后果：`merge-notes/code-review.md` 说「`references/` 下只放 reviewer 的判据，一个 reviewer 一份」，读者照 `CONTEXT.md:31-32` 理解成「一个会话一份 reference」，实际是「一个轴一份」。合上游的时候按错的理解放文件。
- 证据：
  - `CONTEXT.md:31-32` 「**reviewer**: **The Claude Code session** a worker starts through Herdr to run one round of code review.」
  - `mmw-v2/merge-notes/code-review.md:43` 「`references/` 下只放 **reviewer** 的判据，**一个 reviewer 一份**：派发者的正文没有第二个读者」
  - `mmw-v2/merge-notes/code-review.md:5` 「我们把**三个 reviewer** 的判据各拆一份出去」
  - 文件名本身：`mmw-v2/upstream/skills/engineering/code-review/references/standards-reviewer.md` / `spec-reviewer.md` / `tests-reviewer.md`
- 建议正名：三个子代理按 `code-review/SKILL.md:30-34` 的表头叫 **sub-agent**（`Standards` / `Spec` / `Tests`），`reviewer` 只留给那个会话；`merge-notes/code-review.md:5,43` 里的「reviewer」改成「轴」或「sub-agent」。

## 发现 12：仓库里有两份 `CONTEXT.md`，一份把 `ticket` 当正名，另一份把 `ticket` 列进 `_Avoid_`
- 类型：重复定义
- 后果：`AGENTS.md:36` 说本仓是「单 context：根 `CONTEXT.md`」，而 `mmw-v2/upstream/CONTEXT.md` 也是一份词汇表，且规定与根的正相反。`implement/SKILL.md:12` 让 worker「Then the root CONTEXT.md: every term you write comes from it」——它得先知道有两份、该读哪份。
- 证据：
  - `CONTEXT.md:15-16`（根）「**worker**: An independent session dispatched to do **one ticket**」——全篇以 `ticket` 为正名
  - `mmw-v2/upstream/CONTEXT.md:11-13` 「**Issue**: A single tracked unit of work inside an **Issue tracker**……_Avoid_: **ticket** (use only when quoting external systems that call them tickets, or for a **Decision ticket**)」
  - `AGENTS.md:36` 「**单 context**：根 `CONTEXT.md`（这条流水线的全部固定词，动词汇先读它）加 `docs/adr/`。」
  - `docs/agents/domain.md:26` 「Multi-context repo (**presence of `CONTEXT-MAP.md` at the root**)」——本仓没有 `CONTEXT-MAP.md`，所以按 `domain.md` 判定是单 context，`mmw-v2/upstream/CONTEXT.md` 属于「不该存在的第二份」
  - `AGENTS.md:22` 只豁免了两个文件名：「上游自带的 `AGENTS.md`、`CLAUDE.md` 原样不动」——`CONTEXT.md` 不在豁免名单里
- 建议正名：把 `mmw-v2/upstream/CONTEXT.md` 一起写进 `AGENTS.md:22` 的豁免名单（「上游自带的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动，不是本仓的词汇表」），或在 `AGENTS.md:36` 明写「`mmw-v2/upstream/CONTEXT.md` 是上游自己的词汇表，不适用于本仓」。待用户拍板。

## 发现 13：`mmw-v2/upstream/CONTEXT.md` 里的 `ready-for-afk` 是一个不存在的标签
- 类型：幽灵词
- 后果：读这份词汇表的人拿 `ready-for-afk` 去 `docs/agents/triage-labels.md` 查映射，表里没有这一行。
- 证据：
  - `mmw-v2/upstream/CONTEXT.md:19` 「A canonical state-machine label applied to an **Issue** during triage (e.g. `needs-triage`, **`ready-for-afk`**). Each role maps to a real label string in the **Issue tracker** via `docs/agents/triage-labels.md`.」
  - `docs/agents/triage-labels.md:9` 表里是 `ready-for-agent`，全仓 `ready-for-afk` 只此一处命中
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:34` 「- `ready-for-agent`: fully specified, ready for an AFK agent」
- 建议正名：同发现 12，看这份文件是否算本仓事实；若算，把 `ready-for-afk` 改成 `ready-for-agent`。

## 发现 14：`docs/agents/triage-labels.md:13` 指着一句所有技能都不说的话
- 类型：幽灵词
- 后果：这一行教读者「当技能提到某个 role（例如「apply the AFK-ready triage label」）时，去表里取对应的标签串」。全仓没有一处技能这么写；`triage/SKILL.md` 从头到尾直接写 `ready-for-agent`。读者拿着一个不存在的例子去对照，找不到落点。
- 证据：
  - `docs/agents/triage-labels.md:13` 「When a skill mentions a role (e.g. **"apply the AFK-ready triage label"**), use the corresponding label string from this table.」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:78` 「- `ready-for-agent`: post an agent brief comment」——技能直接用标签串本身
  - 全仓 `AFK-ready` 只在这一行与它的种子 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/triage-labels.md:13` 各出现一次
- 建议正名：这句是上游种子原样带下来的。要么删掉那个括号里的例子，要么换成一个真实存在的引用。

## 发现 15：`docs/agents/` 三份配置与 setup 技能的种子近逐字重复，且没有 merge-note 盯着
- 类型：冗余
- 后果：两份同样的 GitHub 约定（sub-issue 端点、native dependencies 的 `-F issue_id=`、frontier query、claim 命令）活在仓库里。上游改种子的时候，技能真正读的那份 `docs/agents/issue-tracker.md` 不会跟着动，而 `merge-notes/README.md` 的清单里没有 `setup-matt-pocock-skills`，谁都不会去看这一对。反过来，`docs/agents/triage-labels.md` 里本仓自己加的十一行（`## What carries a label here`）在种子里不存在，重跑一次 `/setup-matt-pocock-skills` 就没了。
- 证据：
  - `docs/agents/issue-tracker.md` 与 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md` 全文只差四处破折号／分号（`:14`、`:26`、`:42`、`:44`），内容完全一致
  - `docs/agents/domain.md` 与 `.../setup-matt-pocock-skills/domain.md` 只差三处标点（`:8-9`、`:45`、`:51`）
  - `docs/agents/triage-labels.md:1-13` 与 `.../setup-matt-pocock-skills/triage-labels.md:1-13` 逐字相同；本仓多出 `:15-25` 的 `## What carries a label here` 一节
  - `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/SKILL.md:104` 「Then write the docs files **using the seed templates in this skill folder** as a starting point」，:115 「re-running this skill is only necessary if they want to switch issue trackers or restart from scratch」——没有一句提醒重跑会盖掉下游改动
  - `mmw-v2/merge-notes/README.md:18-33` 的清单里没有 `setup-matt-pocock-skills`
  - `AGENTS.md:22` 「**改了上游技能就写或更新它的 merge-note**」
- 建议正名：给 `setup-matt-pocock-skills` 写一份 merge-note，记明「三份种子在本仓的落地件是 `docs/agents/` 下同名文件；`triage-labels.md` 的 `## What carries a label here` 是本仓加的，重跑 setup 前先备份」。

## 发现 16：`Sub-issues opened:` 收哪几类 sub-issue，三份文件三种答案
- 类型：分岔
- 后果：worker 写收尾评论时，照 `CONTEXT.md` 只把 `ABANDON: decision` 那些列进去，照 `implement/SKILL.md:43` 该列「both kinds above」，而它上面一共有**四处**要求开 sub-issue。列多列少都不算错，关票门也判不出来。
- 证据：
  - `CONTEXT.md:307-308` 「**`Sub-issues opened:`**: The sub-issues opened for **`ABANDON: decision` criteria**.」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:43` 「- `Sub-issues opened:` — **both kinds above**」
  - 而 `implement/SKILL.md` 里开 sub-issue 的地方有四处：:18（基线装不下）、:24（Owns 之外的顺手改动）、:34（code review 票外 finding）、:36（`ABANDON: decision`）
  - `CONTEXT.md:518` 「out-of-ticket findings become **sub-issues**」、`CONTEXT.md:644` 「keep going, **open a sub-issue under the spec**」、`CONTEXT.md:648` 「leave it alone and **open a sub-issue** when the change is merely convenient」——CONTEXT.md 自己也承认有四个来源
- 建议正名：`implement/SKILL.md:43` 把「both kinds above」换成「every sub-issue opened while working this ticket — baseline conflict, convenient change outside **Owns**, out-of-ticket review finding, `ABANDON: decision`」；`CONTEXT.md:308` 同步改成四类。

## 发现 17：同一个人在这套文档里有六个名字，其中「you」在三个技能里指三个不同的角色
- 类型：命名撞车
- 后果：`docs/agents/triage-labels.md:20` 的「your queue」指的是人的队列；同一批文档里 `implement/SKILL.md:8` 的「for you」指 worker，`dispatch/SKILL.md:71` 的「your own pane」指 main agent。一个空上下文的会话读到「your」时要靠猜。`needs-info` 的「reporter」在个人仓里根本没有对应的人，而 `CONTEXT.md:590` 干脆把主语删了。
- 证据：
  - `CONTEXT.md:39-41` 「**user（用户）**: The only reader of a ticket no agent may stand in for……_Avoid_: **人, 你**」
  - `docs/agents/triage-labels.md:20` 「`ready-for-human` means the ticket is in **your** queue」（you = 人）
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「claims the ticket **for you** when all four pass」（you = worker）
  - `mmw-v2/skills/dispatch/SKILL.md:71` 「renames **your own pane** `mmw-main` so the board can reach you」（you = main agent）
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:48` 「**The maintainer** invokes `/triage`」、:73 「reproduce it from **the reporter's** steps」
  - `docs/agents/triage-labels.md:8` 「Waiting on **reporter** for more information」 vs `CONTEXT.md:590` 「Waiting on more information.」（主语没了）
  - `docs/agents/issue-tracker.md:41` 「Once claimed, the ticket is assigned to **the driving dev**.」
- 建议正名：本仓只有一个人。`user（用户）` 是正名（`CONTEXT.md:39`）；`maintainer` / `reporter` / `driving dev` / `human` 在本仓落地的三份 `docs/agents/*.md` 里统一改成 `user`，`triage/SKILL.md` 里的上游措辞留着但在 `merge-notes/triage.md` 记一条「本仓 maintainer、reporter 是同一个 user」。技能正文里的「you」保持不动（它指的是读这份技能的那个 agent），但 `docs/agents/triage-labels.md:20` 的「your queue」改成「the user's queue」。

## 发现 18：一个宿主有四个名字，一个都没登记进词汇表
- 类型：重复定义
- 后果：改一行 `models.md` 要同时读懂「host 列」「harness」「宿主」「agent kind」是同一件事；`CONTEXT.md` 号称「fixes the name of every term that pipeline invents」，这四个都不在里面。
- 证据：
  - `mmw-v2/skills/dispatch/models.md:8-9` 「**the host column** says which **harness** that session is, and the arguments are handed to that **harness** untouched.」——一句话里两个名字
  - `mmw-v2/skills/dispatch/references/editing-models.md:13` 表头是 `| Harness | Ask it this |`，:26 「The **host cell** has to name an **agent kind** Herdr recognises.」
  - `AGENTS.md:19` 「技能正文对所有**宿主**是同一份：不把任何**宿主**当默认或首选」
  - `mmw-v2/agents/verifier/agent.json:5` 键名是 `"hosts"`；`mmw-v2/agents/assemble.py:41` 「表里一行一个 (agent, **宿主**)，五列 agent | **host** | model | effort | launch arguments」
  - `mmw-v2/skills/dispatch/scripts/board.py:271` 「`"host": agent.get("agent") or ""`」——Herdr 那边这个字段叫 `agent`
- 建议正名：在 `CONTEXT.md` 的「Dispatch」一节加一条 **host（宿主）**，定义「运行一个 session 的 CLI harness；`models.md` 的 `host` 列，Herdr 叫它 agent kind」，`_Avoid_: harness`（或反过来，二选一）。`references/editing-models.md` 的表头统一。

## 发现 19：「能不能让 agent 单干」这条轴有四套互不引用的词
- 类型：重复定义
- 后果：写票的人要在四套词里挑一套，读票的人四套都得认。
- 证据：
  - `CONTEXT.md:601-607` `reaction`（人是量具）／`reach`（机器判得了但够不着）
  - `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md:74` 「Every ticket is either **HITL** (human in the loop……) or **AFK**, driven by the agent alone.」
  - `docs/agents/triage-labels.md:9` 「Fully specified, ready for an **AFK agent**」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:79` 「note why it can't be delegated (**judgment calls, external access, design decisions, manual testing**)」
- 建议正名：以 `reaction` / `reach` 为准（`CONTEXT.md` 已登记，`to-tickets/SKILL.md:84` 已强制）；`HITL` / `AFK` 是 wayfinder 自己的一层，在 `CONTEXT.md` 里点名它管的是 decision ticket 不是 implementation ticket；`triage/SKILL.md:79` 那四个词照发现 1 处理。

## 发现 20：`models.md:4` 用了 `CONTEXT.md` 明令避开的 `orchestrator`
- 类型：幽灵词
- 后果：`models.md` 是所有 agent 的唯一名册，第一段就用了一个词汇表判死的词指 main agent；照名册找「orchestrator」这一行的人找不到（它本来就不在表里）。
- 证据：
  - `CONTEXT.md:13` 「_Avoid_: coordinator, 编排者, **orchestrator**, 出票的主 agent, 落地 agent」
  - `mmw-v2/skills/dispatch/models.md:4` 「Every agent this pipeline sends out is here except **the orchestrator**, which is the session you started yourself from the CLI.」
  - `CONTEXT.md:12` 「**main agent（主 agent）**: The single Claude Code session that runs all day」——就是同一件东西
- 建议正名：`models.md:4` 的 `the orchestrator` 改成 `the main agent`。（`CONTEXT.md:427` 的「夜间编排主循环（night orchestration loop）」是另一个词，不受影响。）

## 发现 21：`merge-notes/implement.md:15` 用了两个 `_Avoid_` 里的词
- 类型：幽灵词
- 后果：merge-note 是下次拉上游时的取舍依据，用死词写会把死词再带回技能正文。
- 证据：
  - `CONTEXT.md:29` 「_Avoid_: 复验者, **verifier 子代理**, subagent verifier」 vs `mmw-v2/merge-notes/implement.md:15` 「→ 派 **verifier 子代理**（prompt 只有 `verify #<n>`，不派第二次）」
  - `CONTEXT.md:33` 「_Avoid_: **reviewer 会话**, code-review 会话, 复核者」 vs `mmw-v2/merge-notes/implement.md:15` 「`dispatch.sh <n> reviewer <起点>` 起 **reviewer 会话**」
- 建议正名：分别改成「派 verifier」「起 reviewer」。

## 发现 22：票交回 `needs-triage` 时 assignee 不摘，而两份文档都说 assignee 表示「有没有人在做」
- 类型：脚本与文档不符
- 后果：一张被 `WAKEUP LIMIT:` 交回去的票，assignee 还挂着，`ready-for-agent` 已经摘掉。人早上跑 `CONTEXT.md:614` 那五条查询里的「claimed by me and still open」，看到的是一张「有人在做」的票，实际没人在做。更硬的一条：这张票 triage 完重新打上 `ready-for-agent` 之后，`board.py` 的 frontier 因为 `not r["assignees"]` 这一条永远挑不中它，夜里再也不会被派出去。
- 证据：
  - `CONTEXT.md:594` 「In the agent queue — waiting to be dispatched, or being worked right now; **the assignee says which**.」
  - `docs/agents/triage-labels.md:19` 「**Whether anyone is on it is the assignee's job to say.**」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:139-143` `hand_back_for_triage` 只跑 `["gh", "issue", "edit", str(number), "--remove-label", "ready-for-agent", "--add-label", "needs-triage"]`，没有 `--remove-assignee`
  - `mmw-v2/skills/dispatch/scripts/board.py:768-769` 同样只动标签
  - `mmw-v2/skills/dispatch/scripts/board.py:378` frontier 的条件里有 `and not r["assignees"]`
- 建议正名：交回 `needs-triage` 的那两处同时 `--remove-assignee`，理由与摘 `ready-for-agent` 同一条：票不在任何人手上了。

## 发现 23：ADR 0001 的一条 Consequence 没有任何技能执行
- 类型：断点
- 后果：ADR 说「spec 发布后，带 agent brief 的原 issue 关闭并挂到 spec issue 底下」，`to-spec` 的发布步骤里没有这个动作，`triage` 写完 agent brief 之后也不做。照 ADR 走的人找不到执行点，照技能走的人不知道有这条约定。
- 证据：
  - `docs/adr/0001-tracker-repo-authority.md:20` 「spec 发布后，**带 agent brief 的原 issue 关闭并挂到 spec issue 底下**。」
  - `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md:24` 「Write the spec using the template below……then publish it to the project issue tracker. **Leave it unlabelled**」——发布步骤全文，没有处理原 issue 的一句
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:78` 「- `ready-for-agent`: post an agent brief comment」——写完就完了
  - `mmw-v2/merge-notes/to-spec.md` 全文只有一条改动记录（第 1 步的 interview 措辞），不涉及这一条
- 建议正名：要么把这一步写进 `to-spec/SKILL.md` 的第 4 步并在 `merge-notes/to-spec.md` 记一条，要么在 ADR 0001 里说明这条 Consequence 目前靠人手工做。待用户拍板。

## 发现 24：`worker` 在 `exe-release` 里指另一样东西，`exe-release` 的主角又是一个没登记的角色名
- 类型：命名撞车
- 后果：全仓 grep `worker` 会同时捞到落地流水线的 worker 和 `exe-release` 里那个已经删掉的插件子进程；`exe-release` 自己的主角叫「驱动 agent」，词汇表里查不到。
- 证据：
  - `CONTEXT.md:15-16` 「**worker**: An independent session dispatched to do one ticket」
  - `mmw-v2/skills/exe-release/scripts/fix_dispatch.py:7` 「它引用的是 MMW 自己的东西（`$MMW_PLUGIN_DIR/plugin/scripts/**worker.sh**`）」，:14 「没有「派一个 agent 去修」这条路了，因为技能**不再自带 worker**」，:126 「把外部 **worker** 自建的提交回退成工作树改动」
  - `mmw-v2/skills/exe-release/scripts/fix_dispatch.py:14-15` 「但**驱动这次出包的本来就是一个会写代码的 agent**」，:25 「**驱动 agent** 读 receipt、按简报改代码、提交到当前分支、`resume`」
- 建议正名：`exe-release` 那边的 `worker` 改成 `外部修复进程` 或直接写 `worker.sh`（那是它的字面名）；「驱动 agent」要么登记进 `CONTEXT.md`，要么改成已登记的词。这一条优先级低——两套词分居在两个技能里，暂时不会互相踩到。
