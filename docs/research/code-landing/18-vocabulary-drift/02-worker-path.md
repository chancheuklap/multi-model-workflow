# 02 worker path：从领票到收尾的一致性审计

审计范围：`CONTEXT.md`、`mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`mmw-v2/merge-notes/implement.md`、`mmw-v2/skills/verify-ticket/`（`SKILL.md`、`scripts/verify-ticket.py`、`scripts/hook.py`、`scripts/gate-check/`、`tests/`）、`mmw-v2/skills/dispatch/`（`SKILL.md`、`models.md`、`scripts/dispatch.sh`、`scripts/board.py`）、`mmw-v2/agents/verifier/body.md`。`docs/research/code-landing/12-decisions.md` 只作旁证。

---

## 发现 1：`hook.py pretool` 的动作，词表说是「跑 dry run 再按退出码决定」，脚本是「见到就拒，什么都不跑」

- 类型：脚本与文档不符
- 后果：worker 读词表会以为草稿合格时 `gh issue close` 能放行，于是先写草稿再直接关票；实际那条命令永远被拒。反过来，脚本里为「hook 只转述 stderr 第一行」而设计的报错格式失去了理由，读代码的人会去找一个不存在的调用点。
- 证据：
  - `CONTEXT.md:378` 「The host-side enforcement of the closing gate: when a command tries to close a ticket or swap its label, it runs the dry run and refuses on a non-zero exit.」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:14-17` 「It refuses rather than checks. A worker typing `gh issue close` has by definition not been through `--closeout`, so there is no draft of its to check; a gate that guessed one and let the command through when the guess passed would produce exactly the outcome it exists to prevent」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:150-152` 「if command is None or not leaves_the_agent_lane(command, number): return 0 / refuse(host, REFUSAL.format(n=number))」——全函数没有 `subprocess`，`tests/test_hook.py:99-106` 的 `run.assert_not_called()` 也把这一点钉死了
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:820-822` 「# The pretool hook that stands between a worker and `gh issue close` relays only the first line of this, so the first line carries the count and the way to read the rest.」
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:402-404` 「The pretool hook between a worker and `gh issue close` relays only stderr's first line, so that line has to say how many problems there are and how to read the rest.」
  - 旁证 `docs/research/code-landing/12-decisions.md:380` 「`pretool`：`gh issue close` / 换标签前跑 `--closeout --check-only`，非零 deny」——这是词表那句的出处，实现后来改掉了，词表和两处注释没跟上
- 建议正名：以 `hook.py` 为准，改写 `CONTEXT.md:378` 为「一律拒绝，不跑任何命令」；同时删掉 `verify-ticket.py:820-822` 与 `test_closeout.py:402-404` 里「hook 只转述第一行」的理由，改成「一次跑完给出全部问题，避免每轮只修一条」这类站得住的理由。

---

## 发现 2：`--preflight`（开工守卫）到底核对几项，四份文件给出四、五、六三个数，而且没有一份点名 `ready-for-agent` 标签这一项

- 类型：分岔
- 后果：worker 或读者按 merge-note 的「四项」推断哪些情况会被拦住，会得出错误结论。`mmw-v2/merge-notes/to-spec.md:12` 正是这样推的——它说 spec「开工守卫的四项检查它全都满足、拦不住」，据此把「不给 spec 打 `ready-for-agent`」写成 to-spec 的改动理由；但脚本第五项就是查 `ready-for-agent`，没有这个标签的 spec 本来就会被拦。理由和事实对不上，下一次有人依这条理由回滚就会拆掉一道真在起作用的闸。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「It checks the branch, the working tree, the ticket's state and its blockers, and claims the ticket for you when all four pass.」（四）
  - `mmw-v2/merge-notes/implement.md:11` 「分支、工作区、票状态、blocker 四项核对，全过由它认领」（四）
  - `mmw-v2/merge-notes/to-spec.md:12` 「而开工守卫的四项检查它全都满足、拦不住」（四）
  - `CONTEXT.md:326` 「Checks branch, working tree, ticket state, blockers and assignee; only then claims the ticket.」（五，多了 assignee，仍无标签）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:761-788` `refusals()` 依次检查 branch、dirty、state、`"ready-for-agent" not in labels`、blockers、assignee（六）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:775-776` 「NOT_READY: #{number} has no ready-for-agent label, so it has not been cleared for an agent yet」
  - 同一个测试文件自己也对不上：`tests/test_preflight.py:1` 「The opening guard: four conditions」、`:99-100` 「Each of the four conditions is set up before a worker exists」，而常量叫 `ALL_SIX` 且列了六项（`:105-112`）
- 建议正名：以 `refusals()` 的六项为准，四处散文（`implement/SKILL.md:8`、`merge-notes/implement.md:11`、`CONTEXT.md:326`、`tests/test_preflight.py:1,99`）一起改成六项并逐项点名（分支、未提交的 tracked 改动、票的 state、`ready-for-agent` 标签、未关的 blocker、assignee）。`merge-notes/to-spec.md:12` 的理由要重写。

---

## 发现 3：收尾七步的第 3 步要一个 base-commit，活文件里没有任何一处说这个值怎么算出来

- 类型：断点
- 后果：worker 走到「起 reviewer」这一步拿不到参数。`implement/SKILL.md` 把它推给 dispatch 技能，dispatch 技能只说「它是 code review 的起点」，`code-review/SKILL.md` 说「问调用方要」——夜里无人值守的 worker 问不了谁，于是每个 worker 自己编一个起点，同一张票两次 review 的 diff 范围不一样。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 「`bash ~/.agents/skills/dispatch/scripts/dispatch.sh <n> reviewer <base-commit>` starts the reviewer session — the dispatch skill's SKILL.md says how to fill the arguments」
  - `mmw-v2/skills/dispatch/SKILL.md:33` 「`[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from」——没有算法
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:8` 「Both arguments come from the caller; when either is missing, ask for it.」
  - `CONTEXT.md:526` 「The first argument of the review dispatch line: where the diff starts.」——同样没有算法
  - 旁证 `docs/research/code-landing/12-decisions.md:140` 「结论：起点 `git merge-base main HEAD`，不记进票（每票一个 worktree、按阻塞关系串行开工，分支都从 main 开）」——算法只活在这份研究文件里
- 建议正名：把 `git merge-base main HEAD` 写进 `mmw-v2/skills/dispatch/SKILL.md` 的 `[base-commit]` 那一行（`implement/SKILL.md` 已经指向那里），`CONTEXT.md:526` 的 base-commit 条目同步补上这一句。

---

## 发现 4：`issue-<n>-review` 被词表定义成「reviewer 的分支名」，但没有任何东西给 reviewer 开这条分支；reviewer 就在 worker 的 `issue-<n>` 上跑

- 类型：命名撞车（一个词在两处指不同东西）
- 后果：读词表的人会以为 review 在自己的分支上做，于是去找那条不存在的分支、或者担心 reviewer 的改动会污染 worker 的树。同一条目还把 worker 的 `issue-<n>` 说成「Herdr 名和分支名」，掩盖了一件真事：开这条分支的是宿主 CLI 的启动参数（`models.md` 的 launch 列），不是 `dispatch.sh`，而 `--preflight` 的拒绝语却拿「the host opens this worktree」当既成事实说给 worker 听。
- 证据：
  - `CONTEXT.md:396` 「The Herdr name and branch name of a worker and of its reviewer. Must be unique among live agents.」
  - `mmw-v2/skills/dispatch/models.md:26` `| reviewer | claude | `opus` | — | `--permission-mode bypassPermissions --model {model} -n issue-{n}-review` |`——`-n` 是 claude 的会话名，整行没有任何 worktree/分支参数
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:196` 「name="issue-$number-review"」，`:204` 「pane="$(herdr pane split --pane "$caller" --direction "$direction" --cwd "$root" --no-focus」——reviewer 只是把调用方的 pane 劈开，cwd 仍是 `$root`，也就是 worker 的 worktree
  - 对照 worker 两行确实带 worktree 参数：`mmw-v2/skills/dispatch/models.md:24` 「`-w issue-{n} --worktree-base main --force --trust --model {model}`」、`:25` 「`--worktree=issue-{n} --worktree-ref main …`」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:762-764` 「the host opens this worktree on issue-{number}, so it started you somewhere else — stop, do not switch branches yourself」
  - 旁证 `docs/research/code-landing/12-decisions.md:456` 「`agent name` = `issue-<n>` / `issue-<n>-review`（CLI 定位句柄，可预测，唤醒方不必查表）」——原意就只是 agent name
- 建议正名：`CONTEXT.md:396` 改成「worker 与 reviewer 的 Herdr agent 名」，另起一句说明分支只有 `issue-<n>` 一条、由 `models.md` 里 worker 那行的 `-w` / `--worktree=` 参数开出、reviewer 与 verifier 都在这同一条分支上工作。

---

## 发现 5：写码前那一段纪律，词表叫「ponytail 五句（the five sentences）」并列了五条，merge-note 叫「写码纪律七条」，`SKILL.md` 正文是七个 bullet

- 类型：分岔（兼幽灵词：`ponytail` 这个词只在 `CONTEXT.md` 出现一次，别处无锚点）
- 后果：worker 被要求「照五句做」时，无法判断 `SKILL.md` 那七个 bullet 里哪两个不算数；reviewer 修 finding 时 merge-note 说「受写码纪律七条同样约束」，词表里查不到「七条」这个词。两处各数各的，谁也说不清是一件事还是两件事。
- 证据：
  - `CONTEXT.md:651-653` 「**ponytail 五句（the five sentences）**: The five things to do before writing code: grep every caller before changing a function, and delete what a new branch makes unnecessary before adding it; look for something existing before writing a helper; say why what exists is not enough before adding a file, a dependency or a configuration; never simplify away four named things; write `skipped: [X], add when [Y]` at the end.」
  - `mmw-v2/merge-notes/implement.md:14` 「我们加的：七条动作——…上游加了写码期间的纪律段 → 收上游措辞，这七条并进去」
  - `mmw-v2/merge-notes/implement.md:15` 「修 finding 受写码纪律七条同样约束」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:18-24` 正文是七个 `-` 起头的 bullet（契约、grep 调用方、先找现成 helper、说出为何不够、不许简化、`skipped:`、Owns 两档）
  - `ponytail` 全仓库只有 `CONTEXT.md:651` 一处（`grep -rn ponytail mmw-v2 CONTEXT.md AGENTS.md docs/`）
  - 旁证 `docs/research/code-landing/12-decisions.md:273` 「`implement/SKILL.md` 五句第 1 句并入『加分支前点名并删掉它让其多余的』」——五条里第 1 条后来吸收了第 6 条，条数就此对不上了
- 建议正名：待用户拍板，两个选项——(a) 词表条目改名为「写码纪律七条（the seven working rules）」并按 `SKILL.md` 的七个 bullet 重列，`merge-notes/implement.md` 的「七条」自然对上；(b) 保留「五句」但在词表里写明另外两条（契约、Owns 两档）已在 `CONTEXT.md:635` 与 `:647` 单独立目，并把 merge-note 的「七条」改成「五句加契约、Owns 两档」。无论哪种，`ponytail` 这个只在一处出现、无处可查的词都该去掉。

---

## 发现 6：收尾评论的 `Branch:` / `Commit:` / `PR:`，词表说是三行，`SKILL.md` 与测试样本写成一行

- 类型：分岔
- 后果：两个 worker 写出两种形状的收尾评论，早上读票的人和以后想解析这三个值的脚本都要处理两种格式。`--closeout` 对这三行一个字都不检查，所以两种都过得去，漂移不会被拦。
- 证据：
  - `CONTEXT.md:292` 「The three lines under the first line. When there is no pull request, `none` plus the reason.」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:38` 「   - `Branch: … Commit: … PR: …`」（一行，且没提「no PR 时要写理由」）
  - `mmw-v2/merge-notes/implement.md:15` 「首行 ALL MET / HANDOFF REQUIRED、Branch/Commit/PR、Post-verdict:、每条 AC 四行…」（并列成一项，看不出几行）
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:40` 「body = [first, "", "Branch: issue-77  Commit: 9b1d40c7  PR: none", ""]」（一行，`PR: none` 后无理由）
- 建议正名：待用户拍板。若要将来能解析，选三行（改 `SKILL.md:38` 与 `test_closeout.py:40`）；若要评论紧凑，选一行（改 `CONTEXT.md:292`）。任选其一后，「没有 PR 时 `none` 加理由」这句要出现在 `SKILL.md` 的草稿格式里，现在只有词表有。

---

## 发现 7：`--closeout` 核对几件事，词表说十件，`verify-ticket/SKILL.md` 数出七件，脚本实际约十六件

- 类型：分岔
- 后果：worker 被拒后想自查「还差哪几件」，按哪一份都数不齐；`--check-only` 打印的问题条数会超出它以为的上限，读者无法判断是自己漏读还是脚本多查了。
- 证据：
  - `CONTEXT.md:330` 「The closing gate. Reads the draft, checks ten things, and only then posts the comment and closes the ticket or swaps its label.」
  - `mmw-v2/skills/verify-ticket/SKILL.md:66-70` 「`--closeout` reads the draft against the ticket and the repository: the first line, the `ABANDON:` kinds, the three self-runs behind every `failed`, the recount behind `Counts:`, and a clean tracked working tree. A draft whose first line is `ALL MET` is held to two more: the ticket carries the verifier's `VERDICT`, and the draft accounts for every commit since it.」（五 + 二）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:431-522` `draft_problems()` 逐项 append：首行形状、`ABANDON` kind 合法、`ABANDON` 指向的标准存在、`ALL MET` 撞上 failed/stuck、`CHECK:` 裸续行、勾了但 `EVIDENCE: pending`、`ALL MET` 却有 unmet、`failed` 的三轮 self-run、`Counts:` 缺失、`Counts:` 对不上、首行与 `Counts:` 对不上、无 `VERDICT`、缺 `Post-verdict:`
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:525-540` `git_problems()` 再加两项（tracked 未提交、分支不含 main），`:812-817` 再加两项（票非 OPEN、不是我认领的）
- 建议正名：`CONTEXT.md:330` 去掉「ten」这个数（改成「reads the draft, checks it against the ticket and the repository」），把可数清单交给 `verify-ticket/SKILL.md`；`SKILL.md:66-70` 那份清单补齐到与 `draft_problems()` + `git_problems()` + `run_closeout()` 一一对应。

---

## 发现 8：`self-run` 评论的第二行，词表只登记了 `UNMET: <n> (met: <m>)` 一种，全过时那一行其实是 `ALL MET`

- 类型：重复定义 / 命名撞车
- 后果：`ALL MET` 在词表里被定义成「收尾评论两种首行之一」；实际它还会出现在 self-run 评论的第二行。任何按「看到 `ALL MET` 就是收尾评论」判断的人或脚本会认错评论；反过来，按词表读 self-run 评论的人在全过那一次找不到 `UNMET:` 行，会以为脚本没写。
- 证据：
  - `CONTEXT.md:228` 「The second line of a `self-run` or `reverify` comment. A `reverify` adds `reran:` and `previously met reverified:`.」
  - `CONTEXT.md:284` 「One of the two possible first lines: every criterion passed and the ticket may close.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:35` 「SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")」，`:713` 「summary = [l for l in printed.splitlines() if SUMMARY_RE.match(l)]」，`:735-737` 把 `summary` 直接接在 `"reverify" if reverify else "self-run"` 之后
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:685` 「console.log("ALL MET (" + totalMet + " met" + verifyNote + ")" + where);」
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:387` 「met_run = "\n".join(["self-run", "ALL MET", "", …」——测试自己就构造了这种评论
- 建议正名：`CONTEXT.md:228` 改成「`self-run` / `reverify` 评论的第二行是 gate-check 的汇总行：全过时是 `ALL MET (<n> met…)`，否则是 `UNMET: <n> (met: <m>)`」；`CONTEXT.md:284` 的 `ALL MET` 条目补一句「同一个字符串也作为 gate-check 的汇总行出现在 `self-run` 评论第二行，判定收尾评论只看首行」。

---

## 发现 9：「评论以 `Outside Owns:` 结尾」这句写在讲 `--closeout` 的段落里，但只对 `self-run` 评论成立

- 类型：断点
- 后果：worker 读完 `--closeout` 那两段，接着读到「The comment ends with Outside Owns」，会把收尾评论草稿的 `Outside Owns:` 放到末尾，于是 `skipped:`、`Sub-issues opened:`、`Counts:`、`Decisions I made on my own` 四段位置全错；而 `Counts:` 一旦不在，`--closeout` 会拒（`no Counts:` 那条只按前缀找行，位置不影响，但读者不知道），草稿要返工一遍。
- 证据：
  - `mmw-v2/skills/verify-ticket/SKILL.md:66-73` 是 `--closeout` 段，紧接着 `:75-77` 「The comment ends with **Outside Owns**: files this branch changed since it left `main` that no `## Owns` glob covers.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:735-743` 只有 `run_checks()`（`self-run` / `reverify`）把 `"Outside Owns: "` 放在最后一行
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:41-45` 草稿固定形状里 `Outside Owns:` 之后还有 `skipped:`、`Sub-issues opened:`、`Counts:`、`Decisions I made on my own` 四项
  - `CONTEXT.md:300` 「The files changed outside `## Owns`. Computed by the ticket script and copied into the draft; `None` when empty.」——「copied into」而非「ends with」
- 建议正名：`mmw-v2/skills/verify-ticket/SKILL.md:75` 的主语从「The comment」改成「The `self-run` and `reverify` comment」，并明说收尾评论里这一行是抄过去的、位置由 `implement` 的草稿格式定。

---

## 发现 10：`先验（probe first）` 是只在词表里存在的词，worker 路径上没有任何一步做这件事

- 类型：幽灵词
- 后果：词表把它列进「Working discipline」，读者以为开工前有一道「先把不确定的技术问题验掉、答案写进代码注释和票上」的步骤，去 `implement/SKILL.md` 找不到，也没有脚本或评论承载它。要么是该做而没落地，要么是死词。
- 证据：
  - `CONTEXT.md:671-673` 「**先验（probe first）**: Settle one uncertain technical question before starting, and write the answer into the code comment and onto the ticket.」
  - `grep -rn "先验\|probe first" mmw-v2 CONTEXT.md AGENTS.md docs/agents docs/adr` 在活文件里只命中 `CONTEXT.md:671` 一处
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 全文（50 行）没有对应步骤；`mmw-v2/merge-notes/implement.md` 的逐段意图表也没有这一段
- 建议正名：待用户拍板——要么把这一步写进 `implement/SKILL.md`（放在「说出 seam」之后、写码纪律之前，并说清答案写到票上的哪种评论里），要么从 `CONTEXT.md` 删掉这个条目。

---

## 发现 11：linter 的问题标签，词表登记了五个，脚本实际打印十个以上，其中 `unexplained-edge` 是本仓自己加的

- 类型：脚本与文档不符
- 后果：读词表的人以为标签是封闭的五个，收敛判据（「ERROR 改到没有，WARN 逐条看过」）落到一个没登记的标签上时，不知道该按 ERROR 还是 WARN 处理，也无处查这个标签是什么意思。
- 证据：
  - `CONTEXT.md:357` 「**`cycle` / `dangling` / `dollar-without-m` / `manual-gate` / `shared-state`**: The problem tags the linter reports.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:985` 「print("  WARN  " + finding + "  [unexplained-edge]")」——本仓自己加的，词表没有
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs:118,123,128,133,137,143,149` 依次输出 `tautological-check`、`weak-expect`、`path-read-as-regex`、`manual-gate`、`unmeasured-number`、`activity-not-outcome`、`mostly-manual`
  - `mmw-v2/skills/verify-ticket/tests/test_verify_ticket.py:245` 「self.assertIn("weak-expect", printed)」——测试断言的标签词表里没有
  - 另注：词表列的 `cycle` / `dangling` 根本不是方括号标签，脚本打印的是整句 `"cycle detected: …"`（`verify-ticket.py:599`）与 `"dangling dependency: …"`（`:562`）
- 建议正名：`CONTEXT.md:357` 改成两句——vendored 的 `gate-lint` 报七个标签（照抄七个名字）、本仓 `verify-ticket.py` 另加 `dollar-without-m`（ERROR）、`shared-state` 与 `unexplained-edge`（WARN）；票图的环与悬空另立一条，说明它们是整句不是标签。

---

## 发现 12：收尾测试里的 `EVIDENCE:` 样本有两种写法，其中一种不是引擎会写出来的形状

- 类型：脚本与文档不符
- 后果：`test_closeout.py` 的主样本用的是引擎从不产出的 EVIDENCE 形状，所以收尾门对真实 EVIDENCE 行的行为其实没被这些用例覆盖；照着这个样本手写草稿的人也会写出一个和 `self-run` 评论对不上的形状。
- 证据：
  - `CONTEXT.md:170` 「The fixed shape the gate checker writes into `EVIDENCE:` — `exit=…; shell=…; cwd=…; path=…; EXPECT=matched; output-sha256=…; output-bytes=…`」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:579-581` 「return ("exit=0; shell=" + clean(shell) + "; cwd=" + clean(result.cwd) + "; path=" + pathEvidence + "; EXPECT=matched; output-sha256=" + fingerprint.sha256 + "; output-bytes=" + fingerprint.bytes)」
  - `mmw-v2/skills/verify-ticket/tests/test_closeout.py:21` 「  EVIDENCE: 3f9c2e1a; cwd=.; exit=0; matched "6 passed"; 2026-08-29」、`:26` 「  EVIDENCE: exit 1; "1 passed, 1 failed"」——两条都不是上面那个形状
  - 同一文件 `:262` 「  EVIDENCE: exit=0; EXPECT=matched; output-bytes=16」才是真形状
- 建议正名：把 `test_closeout.py:21,26` 的样本换成引擎真会写的形状（`:262` 那一种），使收尾门在真实 EVIDENCE 上被覆盖。

---

## 发现 13：`PASS AC:AC<n>` 的词表定义说「re-run 之后打印」，实际每一次运行都打印

- 类型：重复定义（定义范围不同）
- 后果：读者以为只有 `--reverify` 的输出里有这行，看 `self-run` 的终端输出时会以为运行没成功。
- 证据：
  - `CONTEXT.md:232` 「The compact per-criterion status printed after a re-run.」
  - `mmw-v2/skills/verify-ticket/scripts/gate-check/gate-check.mjs:561` 「console.log("  PASS " + qualify(result.file, result.gate.id) + ": " + result.gate.title);」——在 `runGate` 的结果分支里，与 `--reverify` 无关
  - `mmw-v2/skills/verify-ticket/tests/test_verify_ticket.py:122` 「self.assertNotIn("RUN  AC:AC2", printed)」——同族的 `RUN` 行也是每次运行都打印
- 建议正名：`CONTEXT.md:232` 改成「每跑一条标准就打印一行的紧凑状态，`RUN` / `PASS` / `FAIL` / `STALE` 同族」。

---

## 发现 14：`dispatcher（派发者）` 的词表定义说 code review 起「两个」子代理，同一份词表下面列了三个轴

- 类型：重复定义
- 后果：worker 走到收尾第 3 步、或读 review 报告时，按词表数不出该有几份报告，少一份也看不出来。
- 证据：
  - `CONTEXT.md:36` 「Inside code review, the role that starts the two reviewing subagents, collects both reports, and writes the comment.」
  - `CONTEXT.md:497,503,505` 依次定义 「**`Standards` axis**: One of the three axes」、「**`Spec` axis**: The second axis」、「**`Tests` axis**: The third axis」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:3` 「Runs the three reviews in parallel sub-agents and reports them on the ticket.」
- 建议正名：`CONTEXT.md:36` 的「two … both」改成「three … all three」。
