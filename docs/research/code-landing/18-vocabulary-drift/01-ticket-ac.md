# 簇 01：票（ticket）与 spec 的结构、验收标准（AC）的写法与 lint

审计范围：`CONTEXT.md`、`mmw-v2/upstream/skills/engineering/{to-tickets,to-spec,wayfinder,triage}`、`mmw-v2/skills/verify-ticket/`（含 `scripts/verify-ticket.py` 与 vendored 的 `gate-check/`）、`mmw-v2/merge-notes/{to-tickets,to-spec,wayfinder,triage}.md`、`docs/agents/{issue-tracker,triage-labels}.md`，以及 `mmw-v2/` 全域、`AGENTS.md`、`docs/adr/` 的术语追踪。

共 20 条发现，按严重程度排序。

---

## 发现 1：`ready-for-agent` 这一个标签指向两种互不兼容的票体——`triage` 出的 agent brief 与 `to-tickets` 出的七节票

- 类型：断点
- 后果：`/triage` 把一张外部 issue 打成 `ready-for-agent` 并贴一份 agent brief 之后，这张票就进了 agent 队列；夜里 `board.py` 的 frontier 只看 `state == "OPEN"` 与 `"ready-for-agent" in labels`，会把 worker 派上去。worker 跑 `--preflight` 通过（preflight 也只看标签），然后 `implement` 找不到 `## Read first`、`## Seam`、`## Owns`，`verify-ticket.py <n>` 从 `## Acceptance criteria` 读出空账本，`--lint` 打印「没有验收标准」。同一个队列里两种形状的票，派发方无法分辨。
- 证据：
  - `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md:3` 「An agent brief is a structured comment posted on a GitHub issue or PR when it moves to `ready-for-agent`. It is the authoritative specification that an AFK agent will work from.」
  - `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md:60-63` 「**Acceptance criteria:**\n- [ ] Specific, testable criterion 1」（无 `CHECK:` / `EXPECT:` / `EVIDENCE:`，且用 `**Acceptance criteria:**` 粗体而非 `## Acceptance criteria` 小节）
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:209` 「Every criterion here carries a command. A judgement goes to code review; a thing only a person can look at is its own `ready-for-human` ticket, blocked by this one.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:963-965` 「if not section(body, "Acceptance criteria"):\n        print(f"#{number} carries no `## Acceptance criteria`, so only the ticket graph "」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs:133-135` 「add(file, "error", id, "manual-gate",\n        "no CHECK, so nobody but this ticket's own author decides it: ...")」
  - `mmw-v2/skills/dispatch/scripts/board.py:376-378` 「if r["state"] == "OPEN"\n            and "ready-for-agent" in r["labels"]」
- 建议正名：待用户拍板。选项一：`triage` 的 `ready-for-agent` 出口改成「把 issue 挂到一份 spec 下、走 `to-tickets` 出票」，agent brief 降级为 `needs-triage` 阶段的调查记录；选项二：`AGENT-BRIEF.md` 的模板改成 `<issue-template>` 的七节 + 四行验收标准，`triage.md` merge-note 记下这次改写。现在两份都没有 merge-note 提到过对方。

---

## 发现 2：`ready-for-human` 票的内容在三处各写一遍，`triage` 用的还是 merge-note 明写已经作废的四个理由

- 类型：分岔
- 后果：`to-tickets` 出的 `ready-for-human` 票是一张「去看一眼」的票（一个 kind 词、一个能点开的链接、一条什么算对）；`triage` 出的同标签票是「人来实现」的票，理由从「判断、外部访问、设计决定、手工测试」四个词里挑。用户早上打开同一个 `ready-for-human` 队列，两种票要用完全不同的方式处理，而 `triage` 那四个词正是 `merge-notes/to-tickets.md:21` 判定「现在是混的」并已在 `to-tickets` 里换掉的那四个。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:81-86` 「Write one such ticket per thing to be looked at, labelled `ready-for-human`. It is shorter than the template below and holds five things only: … **Which kind**: *reaction* or *reach*, in one word. … **What to look at**: a link that opens, not a command to run.」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:79` 「`ready-for-human`: same structure as an agent brief, but note why it can't be delegated (judgment calls, external access, design decisions, manual testing).」
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:35` 「`ready-for-human`: needs human implementation」
  - `docs/agents/triage-labels.md:20` 「`ready-for-human` means the ticket is in your queue, and the ticket says in one line why it cannot be delegated.」
  - `mmw-v2/merge-notes/to-tickets.md:21` 「上游给的四个理由是「判断、只有人有的访问权、设计决定、手工测试」，这四个词现在是混的——「判断」大半归了 code review，「设计决定」是五问的第五问、根本不该进这个盒子。」
  - `CONTEXT.md:598` 「In your queue: a ticket carrying one thing only a person can do, of kind `reaction` or `reach`, naming what to look at and what makes it right. Applied when the ticket is written, or by triage once it has judged.」
- 建议正名：以 `to-tickets/SKILL.md:81-87` 的两类（`reaction` / `reach`）加五样为准，理由是 `CONTEXT.md:598` 已经把「或由 triage 判完之后打上」写进定义，而 triage 那一侧从没跟着改。`triage/SKILL.md:35` 与 `:79`、`docs/agents/triage-labels.md:10` 与 `:20` 一起改写，并给 `merge-notes/triage.md` 补一行。

---

## 发现 3：出票时从没有人把票挂成 spec 的 sub-issue，而 `--lint` 的票图与 `board.py` 的夜跑都只认 sub-issue

- 类型：断点
- 后果：`to-tickets` 第 7 步只说「发布一张 issue 一张票」，`## Parent` 是一句文字引用；GitHub 的 sub-issue 关系没有任何一步去建。结果 `verify-ticket.py <n> --lint` 走到票图那一段拿到空列表，打印「no sub-issues, so there is no batch to check」并返回 0——cycle、dangling、启动层级全都静默跳过，而 `to-tickets` 第 8 步的收敛判据（ERROR 清零）看上去是过了的。夜里 `board.py --watch <spec>` 同样一张票都拿不到。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:116` 「publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native blocking / sub-issue relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues.」（这一句讲的是**阻塞边**，不是票与 spec 的父子关系）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:853-856` 「numbers = fetch_sub_issues(spec)\n    if not numbers:\n        print(f"ticket graph: #{spec} has no sub-issues, so there is no batch to check")\n        return 0」
  - `mmw-v2/skills/dispatch/SKILL.md:79` 「`<spec>` | The spec issue whose sub-issues are tonight's tickets. Digits only」
  - `docs/agents/issue-tracker.md:41` 只在「Wayfinding operations」下给了 sub-issue 的建法（wayfinder 地图的 child ticket），`## When a skill says "publish to the issue tracker"`（`:28-30`）只说「Create a GitHub issue.」
  - 对照：`mmw-v2/upstream/skills/engineering/implement/SKILL.md:18` 用的是 `gh issue create --parent <spec> --label needs-triage`，说明这个仓库知道 `--parent`，只是出票那一步没用。
- 建议正名：以脚本为准——`to-tickets` 第 7 步的 GitHub 分支必须写明「每张票用 `gh issue create --parent <spec>` 建，或建完补挂 sub-issue」，第 8 步回读加一条「spec 的 sub-issue 数等于本批票数」。理由是两个脚本都已经把 sub-issue 当唯一的批次来源，改脚本比改两个脚本便宜。

---

## 发现 4：`## Implementation Decisions` 在 `CONTEXT.md` 和 `to-spec` 模板里是两样东西，`我检查 / 你检查` 只存在于 `CONTEXT.md`

- 类型：重复定义
- 后果：照 `CONTEXT.md` 写 spec 的人会写出一份「落地顺序 + 每节一次改动一次提交一次检查 + 我检查/你检查」的清单；照 `to-spec` 的模板写的人会写出一份「编号小节 + 每条决定标出处」的决定表。两份 spec 的 `## Implementation Decisions` 长得完全不一样，而票的 `## Parent` 要按「第 N 节」指回去、`## Read first` 要从小节里抄出处。
- 证据：
  - `CONTEXT.md:111-112` 「**`## Implementation Decisions`**:\nThe landing order. One change, one commit, one check per section.」
  - `CONTEXT.md:131-132` 「**我检查 / 你检查**:\nThe two kinds of check that close each section of `## Implementation Decisions`. 我检查 is what the main agent runs itself; 你检查 is what it hands the user to look at.」
  - `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md:50-60` 「The implementation decisions that were made, grouped into numbered subsections (`### 1. …`, `### 2. …`) that tickets point at by number. Each subsection can cover: … **Every decision names where it came from**, at the end of the sentence or table row that states it」
  - `mmw-v2/merge-notes/to-spec.md:16` 「我们改的：小节编号（`### 1.`），每条决定句末标出处（决定票号 / ADR / research 路径）」——merge-note 记的三条里没有落地顺序、没有提交、没有我检查/你检查。
  - 全域 grep：`我检查` / `你检查` / `landing order` / `one change, one commit` 只在 `CONTEXT.md` 出现，`to-spec/SKILL.md` 与任何 merge-note 里都没有。
- 建议正名：以 `to-spec/SKILL.md:50-64` 为准，`CONTEXT.md:111-112` 改写成「编号小节，每条决定标出处；票按小节号指回」；`我检查 / 你检查` 若确实是想保留的做法，要么写进 `to-spec` 模板要么从 `CONTEXT.md` 删掉——现在它是一个只有词表知道的规矩。

---

## 发现 5：前提消失的验收标准，一处说在行里写 `撤销`，一处说把这条从小节里删掉

- 类型：分岔
- 后果：两种做法在计数上不同。删掉这条，`Counts:` 的 `<total>` 少一；在行里标 `撤销` 而不填 `EVIDENCE:`，`tally()` 会把它数成 unmet，`ALL MET` 永远过不去，而 `--closeout` 也不认识 `撤销` 这个词，只会报「is ticked but its EVIDENCE is pending」或「first line is `ALL MET` but 1 criteria are unmet」。
- 证据：
  - `CONTEXT.md:193-194` 「**撤销**:\nThe end state of a criterion whose premise no longer holds, written in the criterion line in place of passed or failed.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:58` 「A criterion whose premise later disappears is taken out of the section rather than left there without a command; the number is not reused, and the closing comment says what became of it.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:378-390` `tally()` 只认三种状态（abandoned / met / unmet），没有第四种；`ABANDON_KINDS = ("decision", "failed", "stuck")`（`:43`）里也没有对应项。
- 建议正名：以 `to-tickets/SKILL.md:58` 为准（删掉这条、编号不重用、收尾评论交代），`CONTEXT.md:193-195` 的 `撤销` 条目随之改写或删除。理由是脚本这一侧根本没有实现 `撤销`。

---

## 发现 6：`--preflight` 到底核对几项，三处写了三个数，没有一个等于脚本实际做的六项

- 类型：脚本与文档不符
- 后果：worker 看到 `NOT_READY: #<n> has no ready-for-agent label` 时，`implement/SKILL.md` 与 merge-note 都没有告诉它 preflight 会看标签；有人排查「为什么开工被拦」时，按文档里的四项或五项去核对，找不到真正的原因。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「It checks the branch, the working tree, the ticket's state and its blockers, and claims the ticket for you when all four pass.」（四项）
  - `CONTEXT.md:326` 「Checks branch, working tree, ticket state, blockers and assignee; only then claims the ticket.」（五项）
  - `mmw-v2/merge-notes/implement.md:11` 「开工第一步跑 `verify-ticket.py <n> --preflight`——分支、工作区、票状态、blocker 四项核对」（四项）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:761,765,770,774,777,783` 六项：branch、dirty、`state != "OPEN"`、`"ready-for-agent" not in labels`、blockers、`assigned to ... not you`
- 建议正名：以 `refusals()`（`verify-ticket.py:749-788`）为准，三处都改成「分支、工作区、票状态、`ready-for-agent` 标签、blocker、认领人」六项。

---

## 发现 7：linter 的问题标签，`CONTEXT.md` 登记的五个里两个根本不是标签，实际打印的十一个里六个没登记

- 类型：脚本与文档不符
- 后果：`to-tickets` 第 8 步的收敛判据是「ERROR 改到没有，WARN 逐条看过」。但票图的三种错误（cycle、dangling、duplicate）打印时既没有 `ERROR` 字样也没有方括号标签，只有一句 `cycle detected: #81 -> #82`；一个按 `ERROR` 过滤输出的人会漏掉它们，尽管它们照样把退出码打成 1。反过来，`unexplained-edge` 是本仓自己写的 WARN，词表里查不到。
- 证据：
  - `CONTEXT.md:357-358` 「**`cycle` / `dangling` / `dollar-without-m` / `manual-gate` / `shared-state`**:\nThe problem tags the linter reports.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:981-985` 实际打印三个标签：`"  ERROR " + finding + "  [dollar-without-m]"`、`"  WARN  " + finding + "  [shared-state]"`、`"  WARN  " + finding + "  [unexplained-edge]"`
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs:103,118,123,128,133,137,143,149` 另有八个：`parse`、`tautological-check`、`weak-expect`、`path-read-as-regex`、`manual-gate`、`unmeasured-number`、`activity-not-outcome`、`mostly-manual`
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:556,562,599` 票图三种错误的原文：`f"duplicate ticket: #{entry['id']}"`、`f"dangling dependency: #{entry['id']} is blocked by #{dep}, which is not a ticket under this spec"`、`"cycle detected: " + " -> ".join(...)`——都不带 `ERROR` 前缀，也不带方括号标签
  - `CONTEXT.md:362` 「The linter's two levels, and the only thing its exit code says is whether an `ERROR` is left.」
- 建议正名：两件事。(1) `CONTEXT.md:357-358` 改成实际打印的十一个标签，或改成「一个类别名 + 指向 `gate-lint.mjs` 与 `verify-ticket.py` 的标签常量」。(2) 票图那三行打印加 `ERROR` 前缀与 `[cycle]` / `[dangling]` / `[duplicate-ticket]` 标签，否则 `CONTEXT.md:362` 那句「退出码只说明还剩不剩 ERROR」在票图这一路上是假的。

---

## 发现 8：`frontier` 一个词，四份文件给了四种成员判据

- 类型：重复定义
- 后果：出票人按 `to-tickets:118`（阻塞全关就在 frontier 上）划分 `## Owns`，但 `CONTEXT.md:98` 说 frontier 的硬规矩是 Owns 两两不相交，而 `board.py` 实际派发时还要求无认领人、无活会话。同一句「同一 frontier 上的两张票」，出票人和夜跑算出来的集合不是同一个。wayfinder 那一侧的 frontier 又是另一个对象（地图的子票，不是实现票）。
- 证据：
  - `CONTEXT.md:97-98` 「**frontier**:\nThe set of tickets that may be worked in parallel right now. The hard rule: no two tickets on one frontier may have overlapping `## Owns`.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:118` 「Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.」
  - `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md:68` 「the **frontier** is the open, unblocked, unclaimed children, the edge of the known.」
  - `mmw-v2/skills/dispatch/scripts/board.py:375-380` 「return [r for r in rows\n            if r["state"] == "OPEN"\n            and "ready-for-agent" in r["labels"]\n            and not r["blockers"]\n            and not r["assignees"]\n            and r["worker"] is None]」
  - `mmw-v2/upstream/skills/productivity/grilling/SKILL.md:8` 「The **frontier** is every decision whose prerequisites are already settled」（第五种：不是票，是问题）
- 建议正名：待用户拍板。可行的一条：`CONTEXT.md` 把 frontier 定义成 `board.py:frontier()` 的那五个条件（因为那是唯一真正会被执行的判据），把「Owns 两两不相交」单独立一条术语（例如「Owns 不相交规则」），指明它是出票时的人工判据、不是 frontier 的定义的一部分；wayfinder 与 grilling 的 frontier 各自加限定词（地图 frontier / 问题 frontier）。

---

## 发现 9：阻塞关系有两份，GitHub 原生依赖和 `## Blocked by` 正文，没有任何一步核对它们一致

- 类型：分岔
- 后果：只写正文不建原生边——`--lint` 的票图查得出 cycle 与 dangling，但 `--preflight` 与 `board.py` 都看不见阻塞，票会被提前派出去。只建原生边不写正文——preflight 与夜跑对，`--lint` 的票图把每张票当作零依赖，启动层级全是 level 0，cycle 检不出来。唯一的对账是第 8 步一句要人自己数的话。
- 证据：
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:189-194` 票图读正文：「for line in section(body, "Blocked by"):\n        for m in ISSUE_REF_RE.finditer(line):」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:777-778` preflight 读原生：「blockers = [b for b in ticket.get("blockedBy", {}).get("nodes", [])\n                if b.get("state") != "CLOSED"]」
  - `mmw-v2/skills/dispatch/scripts/board.py:162,172` board 读原生：「nodes = (raw.get("blockedBy") or {}).get("nodes") or []」/「"blockers": [int(n["number"]) for n in nodes」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:213` 「The issue number of each blocking ticket, or "None (can start immediately)". On a tracker with native blocking links, add the same edges there too.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:128` 「On a tracker with native blocking links, the number of links equals the number of **Blocked by** entries.」（只数个数，不核对指向谁）
- 建议正名：待用户拍板。选项一：`--lint` 增加一步，把 `## Blocked by` 的票号与 `gh issue view --json blockedBy` 的票号做集合比对，不一致报 ERROR——这样第 8 步那条人工核对就有机器兜底。选项二：票图改成读原生依赖，`## Blocked by` 正文降级为给人看的副本。

---

## 发现 10：同一个技能里两份票模板，节名形态、节的数量、每节的要求都不同，而 `--lint` 只吃其中一份

- 类型：分岔
- 后果：走 local-files 分支出的票带 `**Status:** ready-for-agent` 一行、用 `**Read first:**` 粗体而不是 `## Read first` 小节、没有 `## Acceptance criteria` 标题；`verify-ticket.py` 的 `section()` 只认 `## <heading>`，所以第 8 步那条「跑 `verify-ticket.py <n> --lint`」在这一分支上根本跑不起来（也没有 `<n>`）。两份模板对同一节的要求也不同：`Read first` 一份要求逐行标出基线、一份不要求；`What to build` 一份要求分点、一份不要求。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:159` 「**Status:** ready-for-agent」（`<issue-template>` 与 `CONTEXT.md:43-71` 的七节里都没有 Status）
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:151` 「**Read first:** the source material behind this ticket's sections (decision tickets, ADRs, research files, prototype directories), copied from the sources those sections cite.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:184` 「Whatever here records a settled conclusion … is a **baseline**: a contract, not a reference, marked as one on its line. The exact values and the verbatim copy in the criteria come from the handoff package README where there is one.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:149` 对 `**What to build:**` 无「分点」要求，`:180` 有：「Write it as numbered points, one thing per point」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:134` 「`verify-ticket.py <n> --lint` has been run」（这一条在两个分支上都列着）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:157-160` 「for i, line in enumerate(lines):\n        if line.strip() == f"## {heading}":」（只认 `## ` 小节）
  - `AGENTS.md`「Issue tracker」段：「本仓 issue 在 GitHub Issues，全部操作走 `gh` CLI。」
- 建议正名：待用户拍板。选项一：`<local-ticket-template>` 改成与 `<issue-template>` 同一套 `## ` 小节（保留 Status 一行），两份的节内要求同步，`merge-notes/to-tickets.md:20` 补一行说明；选项二：第 8 步的 `--lint` 那一条明写「只适用于真 tracker 分支」，并在 local 分支给出等价的人工核对。

---

## 发现 11：`## Testing Decisions` 里那个要抄的东西，spec 那侧叫 `prior art`，票那侧叫 `precedent`

- 类型：命名撞车
- 后果：`to-tickets` 让出票人「从 Testing Decisions 的层、目录和它点名的 precedent 推出 `CHECK:`」，但 spec 模板里那一项写的是 prior art。出票人在 spec 里搜 precedent 搜不到，得自己认出这两个词是一件事。`merge-notes/to-tickets.md:23` 明写过这次改名的理由，但只改了票那一侧。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md:71` 「The test layers this feature lands in, each with its directory and the prior art to copy (i.e. similar types of tests in the codebase)」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:69` 「`CHECK:` comes from Testing Decisions — its layer, that layer's directory, and the precedent it names.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:188` 「the test layer and directory from the spec's Testing Decisions, and the precedent to copy.」
  - `mmw-v2/merge-notes/to-tickets.md:23` 「「the prior art to copy」改成「the precedent to copy」，与第 4 步「the precedent it names」用同一个词——同一样东西两个名字，读的人要自己认出它们是一件事。」
  - `CONTEXT.md:116` 「Test layer, then directory, then precedent, then the command to run before committing.」；`CONTEXT.md:135` 「**先例**:」
- 建议正名：以 `precedent` / `先例` 为准（`CONTEXT.md:135` 已登记），把 `to-spec/SKILL.md:71` 的 `prior art` 改掉，并在 `merge-notes/to-spec.md` 补一行——现在只有 `merge-notes/to-tickets.md:23` 记着这次改名。

---

## 发现 12：`HANDOFF REQUIRED:` 一个首行串，两个不同的行格式，其中一个会被抄进 `self-run` 评论

- 类型：命名撞车
- 后果：`gate-check` 打印的汇总行 `HANDOFF REQUIRED: 2 abandoned (met: 3, unmet: 1)` 被 `SUMMARY_RE` 选中、抄进 self-run 评论；worker 若照抄这一行去写收尾草稿的首行，`--closeout` 的 `HANDOFF_RE` 匹配不上，报「first line is neither `ALL MET` nor `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`」。同一个词开头的两行，一个是运行汇总、一个是收尾判词，格式不兼容。
- 证据：
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:686-687` 「console.log("HANDOFF REQUIRED: " + totalAbandoned + " abandoned (met: " +\n    Math.max(0, totalMet - extraUnmet.size) + (effectiveUnmet ? ", unmet: " + effectiveUnmet : "") + ...」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:49-50` 「HANDOFF_RE = re.compile(\n    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(([^)]*)\),\s*(\d+)\s+unmet,\s*(\d+)\s+met of\s*(\d+)\s*$")」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:35` 「SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")」（gate-check 的那一行会被选进评论）
  - `CONTEXT.md:287-288` 「**`HANDOFF REQUIRED`**:\nThe other first line, in full `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`.」（只登记了一种）
- 建议正名：以 `CONTEXT.md:288` 的收尾格式为准，`CONTEXT.md` 另立一条登记 gate-check 的汇总行（例如 `HANDOFF REQUIRED: <n> abandoned (met: …)` 汇总行），并在 `verify-ticket/SKILL.md` 明写「self-run 评论里的这一行不是草稿首行」。

---

## 发现 13：`ready-for-human` 票该有几样，定义说五样、merge-note 说四样、回读只核三样

- 类型：分岔
- 后果：回读那一步是这类票唯一的自检（没有 lint、没有脚本），而它漏掉了 `Parent` 和 `Blocked by`——后者正是定义里写「这是整批里最要紧的一条边」的那一条。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:81` 「It is shorter than the template below and holds five things only:」，`:83-87` 列 Parent / Which kind / What to look at / What makes it right / Blocked by
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:138-139` 「- The kind is named, *reaction* or *reach*.\n- **What to look at** is a link that opens, and **what makes it right** is there to judge against.」（三样）
  - `mmw-v2/merge-notes/to-tickets.md:19` 「`ready-for-human` 的票核它自己该有的四样」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:87` 「**Blocked by**: the ticket that produces the thing. This is the edge that matters most in the batch — wrong, and the person is sent to look at something that does not exist yet.」
- 建议正名：以定义的五样为准，回读那两条补成五条，merge-note 的「四样」改成「五样」。

---

## 发现 14：`CONTEXT.md` 对 spec 两个小节的定义比 `to-spec` 模板窄，`## Sources` 少了五类和「none」规矩，`## Testing Decisions` 丢了 seam 首句

- 类型：重复定义
- 后果：`## Read first` 是从 `## Sources` 按票挑出来的（`merge-notes/to-spec.md:18`）。照 `CONTEXT.md` 写 spec 的人只列四类来源，prototype 目录、交接包、实测证据、测试规则、上游 spec 都不会出现在 `## Sources` 里，票的 `## Read first` 也就无从抄；「无则填 none」这条区分「没有」和「忘了写」的规矩也丢了。`## Testing Decisions` 同理：`merge-notes/to-spec.md:17` 说首句必须固定写 seam，`CONTEXT.md` 的定义里没有 seam 这个词。
- 证据：
  - `CONTEXT.md:123-124` 「**`## Sources`**:\nThe map, decision tickets, ADRs and research files this spec rests on.」（四类）
  - `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md:80-90` 「Links to the first-hand material this spec was built from, one line per kind. Write "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":」后接九条：Wayfinder map / Decision tickets / Upstream specs / ADRs / Research files / Prototype branches or directories / Domain docs / Evidence / Test rules
  - `CONTEXT.md:115-116` 「**`## Testing Decisions`**:\nTest layer, then directory, then precedent, then the command to run before committing.」
  - `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md:68` 「The first sentence names the **seam** confirmed in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed.」
  - `mmw-v2/merge-notes/to-spec.md:18` 「一手来源固定九类（map、决定票、上游 spec、ADR、research、prototype、领域文档、实测证据、测试规则），每类无则填「none」。」
- 建议正名：以 `to-spec/SKILL.md` 的模板为准，`CONTEXT.md:123-124` 改成「九类一手来源，每类无则写 none」，`CONTEXT.md:115-116` 补上 seam 首句。

---

## 发现 15：仓库里有两份 CONTEXT.md，第二份禁用 `ticket` 这个词，而第一份整套词表建在 `ticket` 上

- 类型：命名撞车
- 后果：`AGENTS.md` 说「单 context：根 `CONTEXT.md`」，但 `mmw-v2/upstream/CONTEXT.md` 也是一份活的领域词表，且和根词表在最核心的词上对立：它把工作单元叫 **Issue**，把 `ticket` 列进 `_Avoid_`。任何一个把 `mmw-v2/upstream/` 当活代码读的 agent（AGENTS.md 明说 upstream 可编辑）会拿到两份互斥的命名规矩。
- 证据：
  - `AGENTS.md`「Domain docs」段：「单 context：根 `CONTEXT.md`（这条流水线的全部固定词，动词汇先读它）加 `docs/adr/`。」
  - `mmw-v2/upstream/CONTEXT.md:11-13` 「**Issue**:\nA single tracked unit of work inside an **Issue tracker** … \n_Avoid_: ticket (use only when quoting external systems that call them tickets, or for a **Decision ticket**, see below)」
  - `CONTEXT.md:15-16` 「**worker**:\nAn independent session dispatched to do one ticket, running the whole path from claiming the ticket to writing the closing comment.」（根词表全篇用 ticket）
  - `AGENTS.md`「约定」段只把 upstream 的 `AGENTS.md`、`CLAUDE.md` 列为「原样不动」，没有提 `CONTEXT.md`。
- 建议正名：待用户拍板。选项一：给 `mmw-v2/upstream/CONTEXT.md` 写一条 merge-note，说明它只描述上游仓库自身、本仓一律以根 `CONTEXT.md` 为准，并把 `_Avoid_: ticket` 那一句划为上游范围；选项二：把它并入 `AGENTS.md` 的「原样不动」清单，并在 `AGENTS.md` 的 Domain docs 段点名它不是本仓词表。

---

## 发现 16：`ready-for-afk` / 「AFK-ready」是死标签，仍写在两处活文件里

- 类型：幽灵词
- 后果：`docs/agents/triage-labels.md` 是「技能说角色名 → 查这张表拿真标签串」的映射文件，它举的例子用的角色名（AFK-ready）在表里没有一行对得上；照这个例子去查表的 agent 找不到落点。
- 证据：
  - `docs/agents/triage-labels.md:13` 「When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.」
  - `mmw-v2/upstream/CONTEXT.md:19` 「A canonical state-machine label applied to an **Issue** during triage (e.g. `needs-triage`, `ready-for-afk`).」
  - `docs/agents/triage-labels.md:9` 表里只有 「`ready-for-agent` | `ready-for-agent` | Fully specified, ready for an AFK agent」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:116` 「Apply the `ready-for-agent` triage label to every ticket an agent works」
- 建议正名：两处的 `ready-for-afk` / `AFK-ready` 改成 `ready-for-agent`。

---

## 发现 17：`gate` 是每张票上都会出现的词，词表里没有它

- 类型：幽灵词
- 后果：worker 和用户读到的每一条 `self-run` / `reverify` 评论里都写着 gate（`AC.md: 4 gates`、`UNMET AC:AC2`、`4/7 gates are runnable`），而所有文档、`CONTEXT.md` 和技能正文一律叫它 criterion / 验收标准。读票的人要自己认出这两个词是一件事，而 `CONTEXT.md:5` 明说「词表固定这条流水线发明的每个词的名字」。
- 证据：
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:654` 「console.log(basename(ledger.file) + ": " + ledger.doc.gates.length + " gates");」（这一行进评论）
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs:150` 「runnable.length + "/" + live.length + " gates are runnable; a mostly manual ledger is prose with checkboxes"」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:361` 「(met, total) read off the ledger: a met gate is ticked with real evidence.」
  - `CONTEXT.md:65-66` 「**`## Acceptance criteria`**:\nThe numbered list of criteria.」——`CONTEXT.md` 全篇没有 `gate` 的条目，只有 `gate-check` / `gate-lint` / `关票门` 这三个复合词
- 建议正名：`CONTEXT.md` 的「Acceptance criteria」节加一条 `gate`，注明「vendored 引擎对 criterion 的叫法，只出现在它打印的行里，散文里一律写 criterion / 验收标准」。理由是改 vendored 脚本的字符串代价大于登记一个别名。

---

## 发现 18：`[fixture]` 票和 `落地 <n>/15` 两个标题前缀，登记了，但没有任何一步产生它们或读它们

- 类型：幽灵词
- 后果：`CONTEXT.md:694` 把「对着一张 `[fixture]` 票真跑一遍技能」定为技能行为层的测试做法，但没有任何文件说 `[fixture]` 票怎么建、谁建、和普通票有什么区别；`落地 <n>/15` 声称是标题前缀，而 `to-tickets` 对标题的全部要求是一句「short descriptive name」，也没有任何地方描述那十五步是哪十五步。
- 证据：
  - `CONTEXT.md:89-91` 「**`[fixture]` ticket（`[fixture]` 票）**:\nTitle prefix marking a ticket made to exercise the pipeline itself rather than to deliver anything.\n_Avoid_: 虚构票, fixture 票」
  - `CONTEXT.md:93-95` 「**落地 `<n>/15`**:\nTitle prefix saying which of the fifteen steps this ticket is.」
  - `CONTEXT.md:693-694` 「**技能行为层（skill-behaviour layer）**:\nRun the skill for real against a `[fixture]` ticket inside a worktree and check what appears on the ticket.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:99` 「- **Title**: short descriptive name」（第 6 步对标题的全部要求）
  - 全域 grep：`落地 <n>/15`、`[fixture]` 票的前缀写法在 `mmw-v2/`、`AGENTS.md`、`docs/agents/`、`docs/adr/` 里除 `CONTEXT.md` 外零命中
- 建议正名：待用户拍板。若这两个前缀仍在用，`to-tickets` 第 6 步的 Title 要求里要写明；若不在用，从 `CONTEXT.md` 删掉，`CONTEXT.md:694` 改成别的说法。

---

## 发现 19：`--closeout` 与 `--reverify` 的行为，文档写的和脚本做的对不上

- 类型：脚本与文档不符
- 后果：(a) `CONTEXT.md` 说关票门「查十件事」，`verify-ticket/SKILL.md` 列了七件，脚本实际有十七项判据——按十件或七件去自查草稿的人会被拒。(b) `--reverify` 在三处被描述成三件不同的事：只重跑 self-run 打过勾的、重跑每一条包括打过勾的、以及从 self-run **或** reverify 评论继承账本。
- 证据：
  - `CONTEXT.md:329-330` 「**`--closeout`（关票门）**:\nThe closing gate. Reads the draft, checks ten things, and only then posts the comment and closes the ticket or swaps its label.」
  - `mmw-v2/skills/verify-ticket/SKILL.md:66-72` 「reads the draft against the ticket and the repository: the first line, the `ABANDON:` kinds, the three self-runs behind every `failed`, the recount behind `Counts:`, and a clean tracked working tree. … held to two more」（五 + 二 = 七）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:431-522`（`draft_problems` 十三项）、`:525-540`（`git_problems` 两项）、`:813-817`（票非 OPEN、未认领两项）
  - `mmw-v2/skills/verify-ticket/SKILL.md:32` 「re-running what the worker's `self-run` ticked instead of trusting it」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:994-995` 「parser.add_argument("--reverify", action="store_true",\n                        help="re-run every criterion, including the ones already ticked")」
  - `mmw-v2/skills/verify-ticket/SKILL.md:36` 「`--reverify` re-runs what the newest `self-run` comment ticked」 对 `verify-ticket.py:277` 「if first in ("self-run", "reverify"):」
- 建议正名：`CONTEXT.md:330` 去掉「ten」这个数（改成「读草稿、核对票与仓库两侧的一组条件」或指向 `draft_problems`）；`verify-ticket/SKILL.md:32,36` 改成「重跑每一条，包括已经打过勾的；账本取自最新的 `self-run` 或 `reverify` 评论」。

---

## 发现 20：两个已登记为 `_Avoid_` 的词仍在活文件里；`gate-check.mjs` / `gate-lint.mjs` 被 `_Avoid_` 禁掉，可它们就是文件名

- 类型：幽灵词
- 后果：(a) `顶格续行` 在 `CONTEXT.md` 是死词，merge-note 里仍在用，词表的 `_Avoid_` 因此不可信。(b) `CONTEXT.md` 把 `gate-check.mjs` / `gate-lint.mjs` 列进 `_Avoid_`，但那是磁盘上真实的文件名，`verify-ticket.py`、`UPSTREAM.md`、`gate-lint.mjs` 自己的用法说明都必须写出它——一条无法遵守的命名规矩会让读者怀疑整份 `_Avoid_`。
- 证据：
  - `CONTEXT.md:153-155` 「**代码块围栏（fenced check）**: … _Avoid_: 隐式续行, 顶格续行」
  - `mmw-v2/merge-notes/to-tickets.md:15` 「多行命令写进代码块围栏，没有围栏的顶格续行是解析错误」
  - `CONTEXT.md:203-205` 「**`gate-check`**: … _Avoid_: `gate-check.mjs`」；`CONTEXT.md:207-209` 「**`gate-lint`**: … _Avoid_: `gate-lint.mjs`」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:32-33` 「GATE_CHECK = HERE / "gate-check" / "gate-check.mjs"\nGATE_LINT = HERE / "gate-check" / "gate-lint.mjs"」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md:20` 「| `gate-check.mjs` | The approval store is removed」
- 建议正名：(a) `merge-notes/to-tickets.md:15` 的「顶格续行」改成「没有围栏的续行」。(b) `CONTEXT.md:205` 与 `:209` 的 `_Avoid_` 改成「不要用文件名指代这个角色（`gate-check.mjs` 指文件本身时照写）」，或直接删掉这两条 `_Avoid_`。

---

## 附：一条越界但同簇的观察

`/triage` 的结果个数：`CONTEXT.md:586` 与 `docs/agents/triage-labels.md:21` 都写「recommends one of the four outcomes」，而 `mmw-v2/upstream/skills/engineering/triage/SKILL.md:77-85` 的「Apply the outcome」列了**五**个（`ready-for-agent`、`ready-for-human`、`needs-info`、`wontfix`、以及 `needs-triage`「apply the role. Optional comment if there's partial progress.」）。按「四个」去等结果的读者不会预期「继续留在 needs-triage」也是一个正式出口。建议以技能正文的五个为准，两处文档改成「五个」，或把 `needs-triage` 明写为「不算出口的停留」。
