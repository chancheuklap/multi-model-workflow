# 09 步骤级走查：四条执行路径上的分岔与断点

模拟四个执行者各走一遍，每一步看「这一步让我去读/跑什么、那个东西在别的文件里叫什么、是否存在、步骤是否一样」。

---

## 路径一：main agent 白天（对话 → to-spec → to-tickets → `--lint` → `dispatch.sh run`）

## 发现 1：票没有一步被挂成 spec 的原生 sub-issue，而夜里的 `board.py` 和 `--lint` 只认原生 sub-issue
- 类型：断点
- 后果：主 agent 完整照 `to-tickets` 走完，晚上 `dispatch.sh run <spec>` 起来的 `board.py --watch` 一张票都看不到，整夜什么都不派、直接写 `NIGHT SUMMARY` 退出；而白天的 `--lint` 只会打一行「no sub-issues」并 return 0，回读那一步查不出来。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:116` 「Use the platform's native blocking / sub-issue relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues.」——这一句只管**阻塞边**，全篇没有一句说把票挂到 spec 底下
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:176` 「A reference to the parent issue on the tracker, followed by the numbered Implementation Decisions sections this ticket implements ("#535, Implementation Decisions sections 5 and 7").」——`## Parent` 是正文里的一个引用，不是原生关系
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:122-141` 「### 8. Read every ticket back」全步没有「sub-issue 关系已建立」这一条
  - `mmw-v2/skills/dispatch/scripts/board.py:148` 「rows = gh_json(["api", f"repos/:owner/:repo/issues/{spec}/sub_issues"], [])」
  - `mmw-v2/skills/dispatch/SKILL.md:79` 「`<spec>` | The spec issue whose sub-issues are tonight's tickets. Digits only」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:146-154` `fetch_sub_issues` 同一个端点
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:855` 「print(f"ticket graph: #{spec} has no sub-issues, so there is no batch to check")」后面 `return 0`——静默放行
- 建议正名：以 `board.py` 与 `verify-ticket.py` 用的原生 sub_issues 关系为准，在 `to-tickets` 第 7 步加一句「每张票用 `gh api repos/{owner}/{repo}/issues/<spec>/sub_issues` 挂到 spec 下」，并在第 8 步回读里加一条核对；`verify-ticket.py:855` 的「no sub-issues」改成 ERROR 而不是 return 0。

## 发现 2：`frontier` 一个词四份定义
- 类型：重复定义
- 后果：出票人按 CONTEXT.md 理解成「Owns 不相交的并行集合」去切票，board 按五条机器判据算，wayfinder 那份还规定「first in map order wins」只取一张——同一个词在三个执行者手里是三件事。
- 证据：
  - `CONTEXT.md:97-98` 「**frontier**: The set of tickets that may be worked in parallel right now. The hard rule: no two tickets on one frontier may have overlapping `## Owns`.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:118` 「Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.」
  - `docs/agents/issue-tracker.md:43` 「**Frontier query**: list the map's open children …, drop any with an open blocker … or an assignee; first in map order wins.」
  - `mmw-v2/skills/dispatch/scripts/board.py:375-380` 「r["state"] == "OPEN" and "ready-for-agent" in r["labels"] and not r["blockers"] and not r["assignees"] and r["worker"] is None」
  - `docs/research/code-landing/17-night-loop.md:75` 「frontier = open ∧ `ready-for-agent` ∧ blockedBy 全 CLOSED ∧ 无 assignee ∧ 没有活着的 pane（`docs/agents/issue-tracker.md` 的定义加最后一项）」——它引的那份是 wayfinder 地图的，不是 spec 的
- 建议正名：以 `board.py:375-380` 的五条为 `frontier` 的唯一定义，写进 `CONTEXT.md:97`；CONTEXT.md 现在那句「Owns 不相交」是**出票时的约束**，改叫别的名（例如「同一 frontier 的 Owns 不相交」作为 `## Owns` 词条的一条规则），不要占用 `frontier` 这个名字；`17-night-loop.md:75` 的引用改指 `board.py`。

## 发现 3：`to-tickets` 第 8 步要跑 `verify-ticket.py <n> --lint`，既没给路径，也在本地文件形态下根本跑不起来
- 类型：断点
- 后果：主 agent 走到回读那一步，手上只有一个裸文件名，要么找不到脚本，要么（本地文件形态）拿 `01-slug.md` 当 `<n>` 传进一个只会 `gh issue view` 的脚本。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:134` 「`verify-ticket.py <n> --lint` has been run, and every ERROR it reports is fixed before you report the batch.」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:115` 「**Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:73-79` `fetch_body` 只会 `["gh", "issue", "view", str(number), "--json", "body", "-q", ".body"]`；`main()` 里 `parser.add_argument("ticket", type=int)`
  - 对照写全的那一处：`mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「First run `python3 ~/.agents/skills/verify-ticket/scripts/verify-ticket.py <n> --preflight`」
  - 第三种写法：`mmw-v2/skills/verify-ticket/SKILL.md:19-24` 「`scripts/verify-ticket.py`, next to this file. Resolve its absolute path once.」
- 建议正名：`to-tickets:134` 改成 `implement:8` 的完整形式 `python3 ~/.agents/skills/verify-ticket/scripts/verify-ticket.py <n> --lint`，并明写「只有真实 tracker 形态跑这一步」。

## 发现 4：`to-tickets` 走完之后，没有任何一份文件把主 agent 交到 `dispatch.sh run`
- 类型：断点
- 后果：白天最后一步是「报告这批票已发布」，主 agent 手上没有下一步；开夜那条命令只在 dispatch 技能里等着被人想起来。
- 证据：
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:141` 「Fix what fails before reporting the batch as published.」——全文结束在这里，不提 dispatch
  - `mmw-v2/skills/dispatch/SKILL.md:66-70` 「One command, typed once, after the last ticket of a spec is published.」——它知道自己排在 `to-tickets` 之后，`to-tickets` 不知道
  - `docs/research/code-landing/17-night-loop.md:38-40` 「白天 … → to-tickets → 票带 ready-for-agent 与阻塞边 / 夜里 主 agent 敲一条：dispatch.sh run <spec>」——只有这份研究文档把两头接上，而它不是技能正文
- 建议正名：在 `to-tickets/SKILL.md` 第 8 步末尾加一句指向 `dispatch` 技能的 `<dispatch> run <spec>`（并按 merge-note 的体例记一笔）。

## 发现 5：`to-spec` 不给 spec 打标签的理由，说的是「开工守卫四项检查它全都满足、拦不住」，而脚本第四项查的正是 `ready-for-agent` 标签
- 类型：脚本与文档不符
- 后果：merge-note 给出的理由已经不成立，下次拉上游按这条理由重新裁决会得出错误结论（真正拦不住的是别的东西，不是守卫）。
- 证据：
  - `mmw-v2/merge-notes/to-spec.md:12` 「派发方会挑到一张 spec，而开工守卫的四项检查它全都满足、拦不住」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:775` 「out.append(f"NOT_READY: #{number} has no ready-for-agent label, so it has not been cleared for an agent yet; …")」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:134-135` 「elif "ready-for-agent" not in labels: print("REFUSE ticket #" + number + " is not labelled ready-for-agent")」
- 建议正名：结论（不打标签）保留，把理由改成脚本现在的事实——不打标签的 spec 既进不了 `ready-for-agent` 队列，也过不了守卫与 `dispatch.sh` 的查票。

## 发现 6：「开工守卫核几项」四处四个数：四项 / 四项 / 五项 / 脚本六项
- 类型：分岔
- 后果：worker 看 `implement` 以为只查四样，撞上第五、六样（标签、assignee）的 `NOT_READY:` 时不知道这是守卫的正常拒绝还是脚本坏了。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:8` 「It checks the branch, the working tree, the ticket's state and its blockers, and claims the ticket for you when all four pass.」
  - `mmw-v2/merge-notes/implement.md:11` 「开工第一步跑 `verify-ticket.py <n> --preflight`——分支、工作区、票状态、blocker 四项核对」
  - `CONTEXT.md:325-326` 「**`--preflight`（开工守卫）**: The start-of-work guard. Checks branch, working tree, ticket state, blockers and assignee; only then claims the ticket.」（五项）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:762,766,771,775,781,786` 六条 `NOT_READY:`：branch、dirty、state、`ready-for-agent` 标签、blockers、assignee
- 建议正名：以脚本的六条为准，`implement:8`、`merge-notes/implement.md:11`、`CONTEXT.md:326` 三处一起改成六项并按同一顺序列名。

## 发现 7：「关票门核几项」两个数：十项 vs 七件事，脚本实际十七条
- 类型：分岔
- 后果：worker 被 `--closeout` 拒了之后，不知道自己面对的检查面有多大；`--check-only` 打出的问题数与文档给的数字对不上。
- 证据：
  - `CONTEXT.md:329-330` 「**`--closeout`（关票门）**: The closing gate. Reads the draft, checks ten things…」
  - `docs/research/code-landing/17-night-loop.md:18` 「关票门 | `--closeout` 核十项；`hook.py pretool` 拦手工关票」
  - `mmw-v2/skills/verify-ticket/SKILL.md:66-70` 「`--closeout` reads the draft against the ticket and the repository: the first line, the `ABANDON:` kinds, the three self-runs behind every `failed`, the recount behind `Counts:`, and a clean tracked working tree. A draft whose first line is `ALL MET` is held to two more…」（五 + 二）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:431-523` `draft_problems` 十三条 + `:525-541` `git_problems` 两条 + `run_closeout` 里 state、assignee 两条
- 建议正名：三处都不要写数字。`CONTEXT.md:330` 与 `17-night-loop.md:18` 改成「按 `verify-ticket.py` 的 `draft_problems` + `git_problems` 核对草稿与仓库」，把清单留在 `verify-ticket/SKILL.md` 一处。

---

## 路径二：worker（收到 `implement #n` → 全程 → 派 verifier → 派 reviewer → 收尾 → closeout）

## 发现 8：收尾第 3 步要给 reviewer 一个 `<base-commit>`，全仓库没有一句说它怎么算出来
- 类型：断点
- 后果：worker 走到收尾第 3 步停住：`implement` 说去看 dispatch 的 SKILL.md，dispatch 的 SKILL.md 说「它是 code review 的起点」，CONTEXT.md 说「是 review 派发词的第一个参数」——三处互相指，没有一处给出命令。不给它 `dispatch.sh` 直接 exit 2，这一轮 review 就没了。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 「`bash ~/.agents/skills/dispatch/scripts/dispatch.sh <n> reviewer <base-commit>` starts the reviewer session — the dispatch skill's SKILL.md says how to fill the arguments」
  - `mmw-v2/skills/dispatch/SKILL.md:33` 「`[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from」
  - `CONTEXT.md:525-526` 「**base-commit（起点 commit）**: The first argument of the review dispatch line: where the diff starts.」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:170` 「[ -n "$base" ] || refuse "the reviewer needs the commit its review starts from"」
  - 仓库里唯一算得出它的现成写法在别处：`mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:244` 「base = git("merge-base", "main", "HEAD", cwd=root)」
- 建议正名：在 `dispatch/SKILL.md:33` 的 `[base-commit]` 一格里直接写出命令 `git merge-base main HEAD`（与 `verify-ticket.py` 算 `Outside Owns:` 用的同一条），`implement:34` 保持指过去。

## 发现 9：派不出 verifier 时该怎么办，两份文件给了两条互斥的路，第三条（`self-reported`）只活在词表里
- 类型：分岔 + 幽灵词
- 后果：worker 在一个不能派子代理的宿主上，按 CONTEXT.md 会把 `VERDICT` 的 `by` 写成 `self-reported` 自己交差；按 `verify-ticket/SKILL.md` 应该整张票走 `HANDOFF REQUIRED` 交回去。两种做法一张票关、一张票不关。
- 证据：
  - `CONTEXT.md:269-270` 「**`self-reported`**: What the `by` field of `VERDICT` degrades to when no subagent could be dispatched.」
  - `mmw-v2/skills/verify-ticket/SKILL.md:70-72` 「`HANDOFF REQUIRED` is held to neither — it claims nothing was finished, so it is the way out of anything you cannot fix yourself, **including a verifier that never ran**.」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:33` 「Dispatch the verifier subagent with the prompt `verify #<n>` and nothing else.」——没有「派不出来时」的分支
  - `mmw-v2/agents/verifier/body.md:15-21` 只写 `VERDICT <commit> <level> by <model>`，不认识 `self-reported`
  - 全仓 grep：`self-reported` 在 `mmw-v2/` 下 0 处命中，只在 `CONTEXT.md:269` 与 `docs/research/`
- 建议正名：删掉 `CONTEXT.md:269-270` 的 `self-reported` 词条，以 `verify-ticket/SKILL.md:70-72` 的 `HANDOFF REQUIRED` 为唯一出口；或者反过来在 `implement:33` 与 `verifier/body.md` 里把降级路径写全。**待用户拍板**，但两条并存必须消掉一条。

## 发现 10：`17-night-loop.md` 的 code review 那一行漏掉 `<base-commit>`，照它敲 `dispatch.sh` 直接 exit 2
- 类型：断点
- 后果：读这份方案文档的人（或按它复述给 worker 的 agent）会以为 reviewer 只要票号。
- 证据：
  - `docs/research/code-landing/17-night-loop.md:17` 「一轮 code review | `dispatch.sh <n> reviewer` + `dispatch.sh wait <n> "^REVIEW"`，超时跳过 | #67/#70，S9」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:169-170` 「if [ "$reviewing" = 1 ]; then [ -n "$base" ] || refuse "the reviewer needs the commit its review starts from"」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 写的是 `dispatch.sh <n> reviewer <base-commit>` 与 `"^REVIEW "`（带尾空格）
- 建议正名：`17-night-loop.md:17` 补上 `<base-commit>`，正则统一成 `implement:34` 的 `"^REVIEW "`。

## 发现 11：收尾评论的固定格式写了两遍，两遍不兼容
- 类型：冗余 + 分岔
- 后果：按 `08-failure-vocabulary.md` §7.1 写出来的草稿，`--closeout` 的 `COUNTS_RE` 直接不匹配（它要 `Counts: <k> met, <m> unmet, <n> abandoned of <total>`），`VERDICT_RE` 也认不出 `VERIFIER (…)` 那一行，草稿被拒。
- 证据：
  - `docs/research/code-landing/08-failure-vocabulary.md:216,221,223`「EVIDENCE: exit <code>; matched "<...>"; <sha>」「VERIFIER (<模型家族>, <sha>): <裁决> for AC…」「Counts: met k / unmet m / abandoned n」
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:36-45` 「First line `ALL MET`, or `HANDOFF REQUIRED: …` / `Branch: … Commit: … PR: …` / `Post-verdict:` / … / `Counts: <k> met, <m> unmet, <n> abandoned of <total>`」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:47-51` 「COUNTS_RE = re.compile(r"^Counts:\s*(\d+)\s+met,\s*(\d+)\s+unmet,\s*(\d+)\s+abandoned of\s*(\d+)\s*$")」「VERDICT_RE = re.compile(r"^VERDICT\s+([0-9a-fA-F]{7,40})\b")」
  - `CONTEXT.md:242` 「written `VERDICT <full 40-character commit> <level> by <model> — <one line>`」
- 建议正名：以 `implement/SKILL.md:36-45` + `verify-ticket.py` 的正则为唯一格式；`08-failure-vocabulary.md` §7.1 是被 J 块决策取代的旧提案，在文首标明它已被取代，或删掉那一节。

## 发现 12：`dispatch/SKILL.md` 列的 exit 2 原因只有三条，脚本有十条以上，其中一条正是 worker 第 3 步最容易撞上的
- 类型：脚本与文档不符
- 后果：worker 拿到 exit 2 去对文档的三条原因，一条也对不上（「reviewer 没给起点 commit」「只有 reviewer 能带起点 commit」「不在 git 仓库里」「没有可切的 pane」都不在表里），只能当成未知故障。
- 证据：
  - `mmw-v2/skills/dispatch/SKILL.md:39` 「`2` | Nothing was started. The reason is on stderr: not inside Herdr, no such role, or the ticket is not ready to be worked on」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:157,170,172,187,192,199,202,206,219` 九处额外的 `refuse`，例如 `:172` 「refuse "only the reviewer takes a base commit"」、`:199` 「refuse "no calling pane to split, so the reviewer has nowhere to go"」
- 建议正名：`dispatch/SKILL.md:39` 那格改成「原因在 stderr，逐字读它」，不再枚举——枚举一份会漂移的清单比不枚举更糟。

## 发现 13：`MMW_TICKET`——词表说「hook 找它的第一处」，hook 只有一处、没有第二处
- 类型：脚本与文档不符
- 后果：读者以为 hook 有兜底路径（比如分支名），于是以为没有 `MMW_TICKET` 的会话也被关票门管着；实际上没有变量就完全没有 gate。
- 证据：
  - `CONTEXT.md:399-400` 「**`MMW_TICKET`**: The ticket number injected into the session's environment at dispatch. The first place a hook looks for it.」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:19-22` 「It is told: the dispatcher sets `MMW_TICKET` on the worker's pane. **No variable, no gate.**」
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:83-84` 「value = os.environ.get("MMW_TICKET", "").strip(); return int(value) if value.isdigit() else None」
  - 对照另一处「两个来源」的说法：`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:73` 「the number comes from `$MMW_TICKET`, or from the branch name `issue-<n>`」（那是 `CHECK:` 的两个来源，不是 hook 的）
- 建议正名：`CONTEXT.md:400` 改成「hook 唯一的判据：没有它就没有 gate」。

---

## 路径三：reviewer（收到 `code-review <base> #n` → 全程 → 回报）

## 发现 14：`CONTEXT.md` 自己说 code review 起「两个」reviewing subagent，同一份文件后面又定义了三个轴
- 类型：重复定义
- 后果：reviewer 一进来读词表定位自己要派几个子代理，同一份文件给两个答案；派两个就少一轴 `Tests`，而那一轴是这条流水线唯一问「这个绿色证明了什么」的读者。
- 证据：
  - `CONTEXT.md:35-36` 「**dispatcher（派发者）**: Inside code review, the role that starts the **two** reviewing subagents, collects both reports, and writes the comment.」
  - `CONTEXT.md:497-507` 依次定义 「**`Standards` axis**: One of the **three** axes」「**`Spec` axis**: The second axis」「**`Tests` axis**: The third axis」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:6` 「You run **three** read-only sub-agents over one diff」
  - `mmw-v2/merge-notes/code-review.md:5` 「我们把三个 reviewer 的判据各拆一份出去 … 并加了第三个轴」
- 建议正名：`CONTEXT.md:36` 改成 three，并把「collects both reports」改成 three。

## 发现 15：`dispatcher（派发者）` 一个词指两件事——code review 内部的角色，和 `dispatch.sh` / `board.py`
- 类型：命名撞车
- 后果：worker 读 `verify-ticket.py` 的 `NOT_READY:` 文案「the dispatcher starts this ticket again once those close」，按词表理解成「code review 的派发者」，完全找错人；反过来 reviewer 读到「派发者的夜间总结」也会以为是自己。
- 证据：
  - `CONTEXT.md:35-36` 「**dispatcher（派发者）**: **Inside code review**, the role that starts the two reviewing subagents…」——词表把这个名字整个划给了 code review
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:781` 「stop — the dispatcher starts this ticket again once those close, so do not wait or retry」（指 `board.py`/`dispatch.sh`）
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:753` 「the host opens the worktree on `issue-<n>`, the dispatcher checks the state, the labels and the blockers before it starts anyone」（指 `dispatch.sh`）
  - `mmw-v2/skills/dispatch/scripts/board.py:241` 「the dispatcher gives it `issue-<n>` before it prompts, and only the dispatcher uses that name」（指 `dispatch.sh`）
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:20` 「the dispatcher sets `MMW_TICKET` on the worker's pane」（指 `dispatch.sh`）
  - `docs/research/code-landing/08-failure-vocabulary.md:200` 「派发者的夜间总结（不是票上）列出「因 #N HANDOFF 而未派的票」」（指 `board.py`）
- 建议正名：`dispatcher / 派发者` 归 `dispatch.sh` + `board.py` 这一侧（脚本正文已经这么用，改脚本注释的成本最高）；code review 内部那个角色改用 `code-review` 自己的词，`SKILL.md:6` 里它自称的是「You are the dispatcher」——建议改成 `review dispatcher（评审派发者）` 并同步 `CONTEXT.md:35`。

## 发现 16：reviewer 要给三个子代理「绝对路径」，但没有一处说这三份 reference 装在哪
- 类型：断点
- 后果：reviewer 会话是 Claude Code（`models.md` 的 reviewer 行），技能装在 `~/.claude/skills/`；`SKILL.md` 给的是相对链接，正文却要求绝对路径，reviewer 只能靠猜自己是从哪装的。
- 证据：
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:29` 「your instructions: <absolute path to that agent's reference file>」
  - `mmw-v2/upstream/skills/engineering/code-review/SKILL.md:34-36` 「[`references/standards-reviewer.md`](references/standards-reviewer.md)」——相对
  - 对照有写全的：`mmw-v2/upstream/skills/engineering/implement/SKILL.md:8,32,34` 一律写死 `~/.agents/skills/<skill>/scripts/…`
  - `mmw-v2/install.sh:45,47` 「NEUTRAL_DIR="$HOME_DIR/.agents/skills"」「CLAUDE_DIR="$HOME_DIR/.claude/skills"」
- 建议正名：`code-review/SKILL.md:34-36` 的表里把路径写成 `~/.agents/skills/code-review/references/<name>.md`（与 `implement` 同一套写法），相对链接留给人读。

---

## 路径四：main agent 早上（`mmw board:` 行 / `NIGHT SUMMARY` / 早上五条查询 → triage 被交回的票）

## 发现 17：「早上五条查询」三份说法：五条 / 两条 / 「第三条」，而五条里没有一条查夜里被交回的 `needs-triage`
- 类型：分岔 + 断点
- 后果：夜里 `board.py` 与 `--closeout` 把出事的票一律换成 `needs-triage`（发现 18 的四种首行都落在这里），早上照 CONTEXT.md 那五条跑，第一条查的是 `ready-for-human`，捞不到任何一张；第四条虽然带 `needs-triage`，但它的注释说自己是「夜里新开的 sub-issue」，读者不会拿它当出事清单。
- 证据：
  - `CONTEXT.md:613-614` 「**早上五条查询（the five morning queries）**: … handed to a human, closed yesterday, claimed by me and still open, newly triaged under a spec, and blocked.」
  - `docs/research/code-landing/08-failure-vocabulary.md:183-187` 五条命令，第 1 条 `--label ready-for-human`，第 4 条 `--label needs-triage --search "is:issue parent:<spec 号>"  # 夜里新开的 sub-issue`
  - `docs/research/code-landing/12-decisions.md:553` 「早上**两条**查询因此变成 `is:open label:needs-triage`（夜里倒下的，可以先让 agent 跑一遍 `/triage`）与 `is:open label:ready-for-human`（确实只有你做得了的）」
  - `mmw-v2/skills/dispatch/scripts/board.py:768-769` 「gh(["issue", "edit", str(number), "--remove-label", "ready-for-agent", "--add-label", "needs-triage"])」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:139-143` `hand_back_for_triage` 同样两条标签
  - `docs/research/code-landing/08-failure-vocabulary.md:190` 「第三条依赖 implement 开工时 `--add-assignee @me` 认领；现行 `implement/SKILL.md` 没有这一步」——这句本身已经过期（`--preflight` 会认领）
- 建议正名：以 `12-decisions.md:553` 的裁决为准重写这一组查询，落到一份活文件（`docs/agents/issue-tracker.md` 或 `dispatch/SKILL.md`）而不是研究文档；`CONTEXT.md:613-614` 的条目改成指向那一份，并把「newly triaged under a spec」改成 `needs-triage` 的真实含义（**没有人判过**，不是「刚判过」）。

## 发现 18：`board.py` 发给主 agent 的第四个 case 字符串是 `night over`，`dispatch/SKILL.md` 只给了三个 case 名
- 类型：脚本与文档不符
- 后果：主 agent 收到 `mmw board: night over #60 — run board.py --once`，去技能里对表只找到 `WAKEUP LIMIT` / `REDISPATCHED` / `TIME LIMIT` 三个字面值，判不出这是第二种情况（夜间结束）还是一条它不认识的行。
- 证据：
  - `mmw-v2/skills/dispatch/scripts/board.py:823` 「self.for_main.append(MAIN_LINE.format(case="night over", n=self.spec))」
  - `mmw-v2/skills/dispatch/scripts/board.py:499` 「MAIN_LINE = "mmw board: {case} #{n} — run board.py --once"」
  - `mmw-v2/skills/dispatch/SKILL.md:105-106` 「A limit was reached — `WAKEUP LIMIT`, `REDISPATCHED`, `TIME LIMIT` …」「The night ended | `NIGHT SUMMARY` is the newest comment on the spec」——第二行给的是票上的评论首行，不是这条 prompt 里的 case 字面值
  - `CONTEXT.md:447-448` 「**`mmw board: <case> #<n> — run board.py --once`**」同样不列 case 的取值
- 建议正名：`dispatch/SKILL.md:106` 的 Case 一格里补上字面值 `night over`，与另外三个并列。

## 发现 19：`17-night-loop.md` §11「状态」栏说第 3 步待返工、第 4/5 步没做，而这三样在 `board.py` 与 `dispatch.sh` 里都已经在了
- 类型：脚本与文档不符
- 后果：任何拿这份方案当进度表的人（包括早上被交回一张票、想弄清夜里那套机制到底做到哪一步的主 agent）会以为 `board.py` 还会发「句表」、还不会处理 `blocked`/重派/`NIGHT SUMMARY`、`dispatch.sh run` 还不存在。
- 证据：
  - `docs/research/code-landing/17-night-loop.md:207` 「3 | `board.py --watch`… | 已落地 `b9f405cb`，**待返工**：删掉句表，只发派发词；评论首行改 `BLOCKED:`」
  - `mmw-v2/skills/dispatch/scripts/board.py:487` 「DISPATCH_LINE = "implement #{n}"」，`:637`、`:683` 两处发的都是它，全文没有第二种句子
  - `mmw-v2/skills/dispatch/scripts/board.py:501` 「BLOCKED = "BLOCKED: {form}"」
  - `docs/research/code-landing/17-night-loop.md:208-209` 第 4、5 步「状态」栏都是「—」
  - `mmw-v2/skills/dispatch/scripts/board.py:652-683` `at_a_form`（`blocked`）、`:703-719` `redispatch`、`:818-843` `write_summary`、`:845-865` `tell_main` 全部已存在
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:331-378` `run_night` 已存在；`mmw-v2/skills/dispatch/SKILL.md:64-109` 已写 `run` 与「被重新 prompt」两节
- 建议正名：`17-night-loop.md` §11 的「状态」栏删掉（一份描述主题的文件不记自己的历史），或整表改成「已全部落地」，只留下 §13「还剩的实测项」。

## 发现 20：`17-night-loop.md` §7b 给的两种输出样例，与 `board.py` 实际打印的列名和动作词不是一套
- 类型：脚本与文档不符
- 后果：主 agent 被重新 prompt 后第一件事是 `board.py --once`；它拿到的是英文列头 `ticket agent agent_status phase ac wake note` 和 `5 tickets`，而文档里承诺的是「票 … 备注」「5 张票」，追加行里承诺的动作词「读票」「评论」在程序里根本不存在（`say()` 打的是 `comment` / `prompt` / `dispatch` / `label`）。
- 证据：
  - `docs/research/code-landing/17-night-loop.md:133-141` 「mmw board · 02:14 · spec #60 · 5 张票 · PARALLEL 2/2」「 票    agent          agent_status  phase       ac     wake  备注」
  - `mmw-v2/skills/dispatch/scripts/board.py:384-385` 「COLUMNS = (("ticket", 8), ("agent", 18), ("agent_status", 14), ("phase", 19), ("ac", 7), ("wake", 6), ("note", 0))」，`:405` 「lines.append(render_row({name: name for name, _ in COLUMNS}))」——表头就是这七个英文名
  - `mmw-v2/skills/dispatch/scripts/board.py:402` 「head.append(f"{len(rows)} tickets")」
  - `docs/research/code-landing/17-night-loop.md:146-152` 「02:16:33  #62  读票       最后一条评论 self-run：AC3、AC5 未过」——`board.py` 全文没有任何一处打印「读票」这一动作
  - `mmw-v2/skills/dispatch/scripts/board.py:676` 「say(f"#{row['ticket']}", "comment", f"BLOCKED: {form[:80]}")」
- 建议正名：把 §7b 的两段样例换成 `board.py` 的真实输出（英文列名与动作词），或者改 `board.py` 的 `COLUMNS`/`say()` 用词表的中文——**待用户拍板**；两份不能都留。

## 发现 21：`triage` 要求它贴的每条评论首行都是免责声明，而这条流水线全部靠「评论首行」当协议
- 类型：分岔
- 后果：早上主 agent 对一张被交回的票跑 `/triage`，`triage` 贴的评论首行是 `> *This was generated by AI during triage.*`；这条票之后再被派出去时，`dispatch.sh wait` 只读最新一条评论的首行、`board.py` 的 `last_first_line` / `has_closing_comment` 也只读首行，triage 的评论把首行协议位占掉了。
- 证据：
  - `mmw-v2/upstream/skills/engineering/triage/SKILL.md:12-16` 「Every comment or issue posted to the issue tracker during triage **must** start with this disclaimer: `> *This was generated by AI during triage.*`」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:308-309` 「first="$(printf '%s' "$comment" | head -n 1)"; if [ -n "$comment" ] && printf '%s' "$first" | grep -Eq "$pattern"」
  - `mmw-v2/skills/dispatch/scripts/board.py:185` 「**The first line of the ticket's newest comment: the pipeline's own status word.**」
  - `mmw-v2/skills/dispatch/scripts/board.py:207` 「return any(first_line(c).startswith(CLOSING_LINES) for c in ticket.get("comments") or [])」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:275-277` `previous_ledger`：「first = comment.strip().splitlines()[0].strip() …; if first in ("self-run", "reverify")」——首行要**恰好**是这两个词
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:30` 「A ticket that already carries a `self-run`, `VERDICT` or `REVIEW` comment is work you were prompted back into: resume at the step after the newest of them」——同样靠首行认
- 建议正名：`triage/SKILL.md:12` 的免责声明改成放在评论**末行**，或明写「本仓库的票上不加这一行——首行是流水线的协议位」，并在 `mmw-v2/merge-notes/` 下补一份 `triage.md` 记这条改动（现在 merge-notes 里没有 triage 这一份）。

## 发现 22：`--lint` 实际打的问题标签有 `unexplained-edge`，词表登记的五个里没有它
- 类型：幽灵词（反向：脚本有、词表无）
- 后果：出票人在 `--lint` 输出里看到 `[unexplained-edge]`，去 `CONTEXT.md` 查这个标签查不到，不知道它是 ERROR 还是 WARN、该不该改。
- 证据：
  - `CONTEXT.md:357-358` 「**`cycle` / `dangling` / `dollar-without-m` / `manual-gate` / `shared-state`**: The problem tags the linter reports.」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:985` 「print("  WARN  " + finding + "  [unexplained-edge]")」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:914-926` `lint_edges` 的正文
  - 对照另外两个确实存在的：`verify-ticket.py:981` 「[dollar-without-m]」、`:983` 「[shared-state]」；`mmw-v2/skills/verify-ticket/scripts/gate-check/gate-lint.mjs:133` 「add(file, "error", id, "manual-gate",」
- 建议正名：`CONTEXT.md:357-358` 加上 `unexplained-edge`，并说明它是 WARN。

## 发现 23：同一个 GitHub sub-issues 端点，两个脚本用两种占位符写法
- 类型：脚本与文档不符（同一动作两种写法）
- 后果：读者不知道哪一种才是这条流水线的写法；`to-tickets` 教出票人写 `CHECK:` 时给的是第三种上下文里的第三个样子。
- 证据：
  - `mmw-v2/skills/dispatch/scripts/board.py:148` 「f"repos/:owner/:repo/issues/{spec}/sub_issues"」
  - `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:149` 「f"repos/{{owner}}/{{repo}}/issues/{spec}/sub_issues"」
  - `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md:73` 「`gh api repos/{owner}/{repo}/issues/<n>/sub_issues`」
- 建议正名：三处统一成 `repos/{owner}/{repo}/…`（`to-tickets` 教给出票人的那一种，也是 `gh` 文档的写法）。
