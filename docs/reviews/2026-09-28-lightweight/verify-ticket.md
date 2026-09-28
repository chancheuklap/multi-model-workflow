# verify-ticket

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能的文字主要毛病是 `references/linting.md` 把 lint 的规则逐条复述了一遍，而这些规则每一条在 lint 自己的输出里都带着原因和改法。`SKILL.md` 第 10 行 "The ticket is the only state…" 与 `sub-issues.md` 表格的 "Not this kind" 一列是真正的判断依据，保留。子 issue 的"种类"缺一句说明它决定谁、在什么时候读，这一句补上。脚本里有一组真实缺陷要修（D4 的三处异常类型）。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `references/sub-issues.md`，`## Which kind it is` 之前 | The kind decides who reads the child and when: `fault` and `contract` wake the main agent tonight, which repairs the pipeline or the source and resumes this ticket; `decision` and `deferred` reach the user in the morning, in the night summary, while you carry on; a `finding` waits for the night's closing pass. None of these readers has seen your session, so the body stands on its own. | 在 `contract` 与 `decision` 之间拿不准时：没有它，worker 只能按表格字面对照；有了它，会按"谁能回答、什么时候回答"来选，也会把正文写成别人能独立读懂的样子。各种类的去向已按代码核对：`night.md` 的处理表、`status.py` 的 `routed_line` 注释（`deferred`、`decision` 列在 `Sub-issues opened tonight:`）。 |
| I2 | `references/linting.md`，删减后的正文（接在三条命令之后） | The graph it checks is the tracker's blocking links, the same ones `--preflight` refuses on and `advance` dispatches from, so an edge is fixed there, not in a ticket body. The batch is ready when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose. | 后两句是原文保留下来的判断（边改在哪里；什么时候算好）。（按 advisor 意见删去了"每条 finding 自带改法"那一句：它是在复述 agent 眼前的输出。） |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `references/linting.md` 第 13、17–21、25、29、31–35、37、39–47 行（两次 lint 的理由、草稿格式、如何认出 spec、worker 标签、screen contract 各条、fetch stub、`[uncovered-section]`/`[undecidable-check]`/`[parent-order]`/`[screen-contract]` 汇总） | 删。全文从 1,431 词减到约 150 词。 | 每条的 `ERROR`/`WARN` 文本都自带原因和改法；草稿格式在 `to-tickets` 第 7 步、写票规则在 `to-tickets` 的 `cutting-interface-tickets.md`、Critical flows 形状在 `to-spec`，写的人在写的那一刻读得到。merge-note 与 downstream-note 里把 `linting.md` 当作规则所在地的指向，一起改到脚本或对应技能。 |
| D2 | `linting.md` `## Exit codes` 与 `references/sub-issues.md` `## Exit codes` | 先把 `--lint`、`--sub-issue`、`--review` 的退出码补进 `verify-ticket.py --help` 的 `EXIT_CODES`，再删这两节 | 退出码放在脚本旁边。 |
| D4 | 三处异常类型对不上：`run_baseline_if_needed`、`blocker_fold`、`ticket_spec`（调查员"脚本"一节逐条列了行号） | 改为捕获 `TrackerReadError`，让拒绝信息如实说明已写入了什么 | 真实缺陷。其中 `ticket_spec` 那处在子 issue 已建好之后告诉 agent "retry the same command"，会建出重复的子 issue。 |
| D5 | `verify-ticket.py` `lint_retired_base` 与 `RETIRED_BASE_RE` | 删函数、正则与 `[retired-base]` 规则。**前提**：先在每个消费仓库跑 `gh search issues mmw-base --state open`，确认没有还在读旧键的开着的票 | 守的是 #341 已退役的两个 git config 键，正常写出的新票走不到这条检查；没有测试。 |
| D6 | `verify-ticket.py` `review_problems` 与 `ROW_ID_RE`，连同 `test_screen_contract.py` 的 `TestReviewProblems`；以及 `implement` 的 `references/writing-interface-code.md` 第 41 行（"When the review's Spec axis reports a `Missing` that names one of this ticket's screen-contract rows…"） | 两边一起删 | `review_finding_problems` 已要求每条 in-ticket finding 都有 `fixed <commit>` 或 `refuted:`，而 `code-review` 把针对本票合同行的 `Missing` 归为 in-ticket；旧检查是它的子集，还会把碰巧提到行 id 的编号行误当成 `Missing`。 |
| D7 | `PIPELINE_SCRIPTS[...]["retired"]` | 删；`help_flags` 改成也用 `shutil.which` 找判官；未知 flag 的消息补上 "addresses come from .mmw/target.json" | `help_flags` 已按判官 `--help` 报出未列的 flag，这份清单只是换了一种说法。 |
| D8 | `--timeout` 参数 | 删 | 除测试外没有调用方；票上的 `TIMEOUT:` 行才是在用的机制。 |
| D9 | `IN_TICKET_ITEM_RE`（旧 review 格式） | `--review` 只接受现行格式；确认没有旧格式 review 挂在开着的票上之后，closeout 端也删 | 同时接受两种格式，等于没有强制现行格式。 |
| D10 | 重复的小工具函数（`GH_ENV` 三份、"取 gh stderr 最后一行" 四份、`_gh` 与 `issue_tree._run_gh`、Spec 轴切分两次） | 各留一份 | 约减 20 行。 |
| D11 | `ticket_entries` 逐票 `fetch_blocked_by`、`lint_spec` 逐票 `fetch_ticket` | 复用 `issue_tree.read` 已带回的字段，blocker 超过 10 条时再单查 | 减少对 tracker 的调用。 |
| D12 | `events.py` 模块 docstring 第 50–52 行（`child` 打印四个字段） | 改为五个（多 `reason`） | 注释与代码不符。 |
| D13 | `tests/verify-ticket/test_draft.py` 第 119 行伪造的 `.mmw-base-branch` | 删 | 脚本已不读这个键。 |

### 不采纳

- 原 D3（`--sub-issue` 遇到同标题未关闭的 child 时拒绝再开）：我当初引的 #414 讲的是 `--closeout` 被截断后重跑、事件写了两遍，不是子 issue；子 issue 重复打开没有出过事的记录。D4 修好后，唯一会诱导重开的那条错误提示（"retry the same command"）也没了。为没发生过的事加一道检查，是新的过度防御。
- 调查员给 `SKILL.md` 的补段（"Nobody watches a ticket being worked…"）：worker 读的是 `implement`，那里的 I1 已经写了"绿勾是为了让人不读代码也能信"；"红得意外、绿在动工之前"的处理在 `implement` 第 7 步的 `Green before work:` 已有规定。
- `linting.md` 补段里 "It does not say that a criterion would fail without the work…"：说不出它让读者改做哪件事；判据的含义在切票时由 quiz 与歧义扫描把关。
- `sub-issues.md` 补段里 "Write the body for that reader: what you ran, what you saw…"：每种 child 正文该写什么，`implement` 在开 child 的那一句已经写了。
- 用 node 调 `gates.mjs` 统一解析：设计选项，这一轮不做。
- `issue_tree.py` 的命令行入口：留作诊断工具。

## 结论

体量：技能文本 2,127 词（`SKILL.md` 319、`references/linting.md` 1,431、`references/sub-issues.md` 377，按 `wc -w` 含 frontmatter）；脚本 5,260 行（`scripts/verify-ticket.py` 4,020、`scripts/events.py` 955、`scripts/issue_tree.py` 285），另有 `scripts/gate-check/` 下三个指向 `mmw-v2/upstream-unlazy/scripts/` 的 symlink。前几轮已经把 worker 的 claim、criteria run、closeout 三份 reference 删掉，并入 `implement` 的 `## Closing steps`，所以 `SKILL.md` 现在基本只负责解析 `<engine>` 和做路由。

主要问题集中在 `references/linting.md`：它的 1,431 词里约 85% 是把 `--lint` 的每条规则、每个标记和退出码再写一遍。这些内容 lint 的 ERROR/WARN 消息里已经逐条写了，而且每条都带修法；写票时的规则另有归属，在 `to-tickets` 第 7 步、`cutting-interface-tickets.md` 和 `to-spec` 第 98 行。估计 `linting.md` 能从约 1,430 词减到约 200 词，`sub-issues.md` 能再删约 50 词；同时要补大约 250 词讲清目的的文字。整体净减约 1,000 词。

脚本大多数防御都有真实事故作依据：`closeout_lock` 和 `completed_closeout` 来自 #414（工具调用被截断，事件被写了两遍）；`TrackerReadError` 来自 #440；`require_judges` 来自 2026-09-08 那次调用漏传 `--tools`，否则会把整批票判红。所以脚本能删的只有约 100–130 行，包括两条已经没有触发条件的历史检查、一条重复的 closeout 检查、一个没人传的参数，以及几处重复的小工具函数。另外发现三处真实缺陷：异常类型对不上，导致三处 `except` 捕不到，其中一处可能让 agent 重开一个重复的子 issue。

"灵魂"不完整。`SKILL.md` 写了"ticket 是唯一的状态"这条架构原则，但没说这些运行对全局的意义：没有人看着票被做，早上用户、main agent 和之后的夜里读的就是这些事件，所以一次运行只有在"本可能出另一种结果"时才有价值。`sub-issues.md` 教了怎么选 kind，但没说 kind 就是路由：它决定谁在什么时候读这张子 issue。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| 1 | `references/linting.md` 第 13 行 "A batch is linted twice: its drafts before publishing…"，以及 `## --drafts before publishing` 第 21 行 "The run ends with the checks it could not run…" | 6 | `to-tickets/SKILL.md` 第 156 行已经写了 "The drafts run of step 7 does not stand in for it: only this run sees the tracker's labels, sub-issues and blocking links"；`verify-ticket.py` 的 `DRAFTS_NOT_CHECKED`（第 3773–3778 行）在每次 `--drafts` 运行末尾都打印这份清单（第 3889–3891 行） | 由 `to-tickets` 第 8 步和脚本输出承担。无剩余风险 | 删 |
| 2 | `linting.md` `## --drafts before publishing` 第 17–19 行 "`<dir>` holds one draft file per ticket…"、"Each draft gets everything a published ticket gets…" | 6、1 | 草稿形状完整写在 `to-tickets/SKILL.md` 第 141 行（写草稿的 agent 在这一步读它）；`[layer-label]`、`[unknown-draft]`、`[draft-unreadable]`、`[spec-unreadable]` 各自的 ERROR/WARN 文本都写了原因和修法（`lint_drafts` 第 3836–3874 行，`read_draft` 第 3785–3813 行） | 由 `to-tickets` 第 7 步和脚本消息承担。丢掉的一句是"其他头行是写草稿的人的备注，不读"，没有流程依赖它 | 删 |
| 3 | `linting.md` `## --lint on a batch` 第 25 行 "Given a ticket, `--lint` checks that ticket…"（怎样认出 spec、closed ticket 怎么算） | 1 | 在复述 `reads_as_spec`（第 3691–3707 行）、`lint_spec`（第 3738–3764 行）的分支；closed ticket 由脚本打印 `WARN … [closed-ticket]` 说明（第 3756 行）；`dispatch/references/night.md` 第 49 行也写了 "a closed ticket's findings do not count" | 由脚本输出承担。无剩余风险 | 删 |
| 4 | `linting.md` 第 29 行 "For the worker: `dispatch.sh` starts a ticket on the `models.json` row…" | 1、6 | `lint_worker` 的消息本身就是这两句（第 2586–2589 行）；worker 标签怎么选写在 `to-tickets` 第 6 步的 **Worker** 行 | 由脚本消息和 `to-tickets` 承担。无剩余风险 | 删 |
| 5 | `linting.md` 第 31–35 行 "The same run checks the criterion shapes against the screen contract…" 到 Critical flows 一整段 | 1、6 | 每条规则的 ERROR/WARN 文本都在 `lint_screen_contract`（第 3390–3560 行），并带修法；写票规则的归属是 `to-tickets/references/cutting-interface-tickets.md`；Critical flows 行的形状写在 `to-spec/SKILL.md` 第 98 行，看不懂某行时的 ERROR 还会原样引用 `CRITICAL_FLOW_SHAPE`（第 3383–3387 行） | 由脚本消息、`to-tickets`、`to-spec` 承担。剩余风险：有人把 `linting.md` 当成规则总表来维护（见"与其他技能的重复"里的 merge-note 指针），删后规则的说明只剩在脚本的 docstring 里 | 删；同时改指向它的 merge-note 和 downstream-note |
| 6 | `linting.md` 第 37 行 "A flag inside a quoted `--run` value belongs to…"（fetch stub 规则） | 6 | `ui-acceptance/references/boundary-check.md` 第 38 行写了同一条；lint 消息在第 3393–3394 行 | 由 `boundary-check.md` 和脚本消息承担。无剩余风险 | 删 |
| 7 | `linting.md` 第 39、41、45、47 行（`[uncovered-section]`、`[undecidable-check]`、`[parent-order]`、`[screen-contract]` 汇总） | 1 | 每条的 WARN/ERROR 文本都自带原因和修法：`print_uncovered_sections` 第 3137 行，`lint_undecidable_checks` 第 2719–2731 行，`parent_order_findings` 第 3577–3580 行 | 由脚本消息承担。无剩余风险 | 删 |
| 8 | `linting.md` `## Exit codes` 第 49–53 行 | 1、6 | `dispatch/references/night.md` 第 49 行已经写了这三个退出码，还加了唯一需要判断的一条："tracker 答不上来时重跑，不改票"。`--help` 的 `EXIT_CODES`（第 3897–3917 行）里没有 `--lint`、`--sub-issue`、`--review` | 由脚本 `--help` 承担 | 先把 `--lint`、`--sub-issue`、`--review` 的退出码补进 `EXIT_CODES`，再从 `linting.md` 删掉 |
| 9 | `references/sub-issues.md` `## Exit codes` 第 25–27 行 | 1 | exit 1 的 stderr 已经写了 "do not open it again"（第 1624–1626、1634–1635 行） | 由 stderr 和 `EXIT_CODES` 承担。剩余风险：工具调用被截断时 agent 看不到 stderr（#414 的真实情形），所以"不可重跑"这一点要留在正文里，见 B | 删这一节，把退出码补进 `EXIT_CODES`，正文加 B 里那一句 |
| 10 | `verify-ticket.py` `lint_retired_base` 与 `RETIRED_BASE_RE`（第 117–119、2629–2650、3672–3673 行） | 3、5 | 这是在守 #341 退役的两个 git config 键。技能文本里已经没有任何地方教人写它们（全仓 grep 只剩 `downstream-notes/341-origin-base-branch.md` 这份变更记录）；这条检查没有测试；在 `agentflow-hq` 上搜 "mmw-base"，2026-09-12 之后的命中全是 `mmw-baseline` 子串，不是真的在读这两个键。正常写出来的新票走不到这条检查 | 由流水线提供的 `$MMW_BASE_REF` 和 downstream-note 341 承担。剩余风险：2026-09-11 之前写的、至今没落地的票如果还在读这两个键，会假绿。删之前在每个消费仓库跑一次 `gh search issues mmw-base --state open` 确认 | 删函数、正则和 `[retired-base]` 这条规则 |
| 11 | `verify-ticket.py` `review_problems` 与 `ROW_ID_RE`（第 2109–2134 行，调用在第 2403 行） | 6 | 它比 `review_finding_problems`（第 2137–2178 行，2026-09-15 #436 加的）早，覆盖的是后者的一个子集：`code-review/references/session.md` 第 4 步把"碰到 `## Read first` 里 baseline 的 finding"归为 in-ticket，所以针对本票合同行的 `Missing` 会出现在 `## In-ticket` 里，而后者要求每一行都有 `fixed <commit>` 或 `refuted:`。另外它的触发条件 `^\s*\d+\.\s` 会把 Spec 轴里任何提到本票行 id 的编号行都当成 Missing | 由 `review_finding_problems` 承担。剩余风险：reviewer 只在 Spec 轴正文里写了 Missing、没列进 `## In-ticket`。这是 review 格式的缺陷，更好的办法是让 `--review` 拒收这种报告 | 删，连同 `test_screen_contract.py` 的 `TestReviewProblems` 四条测试 |
| 12 | `verify-ticket.py` `PIPELINE_SCRIPTS[...]["retired"]`（第 2767–2772、3092–3095 行） | 3、6 | `help_flags` 已经会把判官 `--help` 里没列的 flag 报出来（第 3096–3100 行）；而 `require_judges` 保证判官一定找得到，所以这份"已退役 flag"清单只是换了一种说法 | 由 `help_flags` 承担。剩余风险：判官只在 `PATH` 上时，`help_flags` 用的是 `tool()`，找不到文件就跳过检查 | 删 `retired`；`help_flags` 改成也用 `shutil.which`；未知 flag 的消息补上 "addresses come from .mmw/target.json" |
| 13 | `verify-ticket.py` `--timeout` 参数（第 3938 行，`check_timeout` 的 `asked` 参数） | 5 | 除了测试，没有任何调用方传它（grep 了 `dispatch.sh`、各技能文本）；`to-tickets/SKILL.md` 第 199–201 行教的机制是票上的 `TIMEOUT:` 行 | 由 `TIMEOUT:` 承担。无剩余风险 | 删 |
| 14 | `verify-ticket.py` `IN_TICKET_ITEM_RE`，也就是 "Historical rows"（第 52–53、1281–1293 行） | 3、5 | `code-review/references/session.md` 第 5 步规定每行都要写 `[<category>]` 和 `source:`；可 `--review` 同时接受旧格式，等于没有强制执行现行格式。未验证：还有没有开着的票挂着 2026-09-15 之前格式的 review | 由现行格式承担。剩余风险：确有旧 review 的开着的票，closeout 会拒收 | `--review` 只接受新格式；closeout 端确认没有旧 review 挂在开着的票上之后，也删掉旧格式 |
| 15 | 重复的小工具函数：`GH_ENV` 有三份（`verify-ticket.py` 第 137 行、`events.py` 第 806 行、`issue_tree.py` 第 62 行）；"取 gh stderr 最后一行"有四份（`tracker_failure` 第 150 行、`gh_detail` 第 342 行、`events.read_comments` 第 822 行、`issue_tree._ask` 第 236 行）；`_gh`（第 360 行）和 `issue_tree._run_gh`（第 176 行）；Spec 轴切分写了两次（第 1242–1243、2123–2124 行） | 6 | 读源码时逐处看到 | 共用一份就行。无剩余风险 | 各留一份，约减 20 行 |
| 16 | `ticket_entries` 对每张票单独调一次 `fetch_blocked_by`（第 332–339、1195 行）；`lint_spec` 对每张子票再调一次 `fetch_ticket`（第 3748 行） | 6 | `fetch_sub_issues` 用的 `issue_tree.read` 已经带回每张票的 `labels`、`blockedBy`、`state`（`issue_tree.py` 第 100–103 行） | 由 tree 读取承担。剩余风险：tree 里 blocker 最多取 10 条，`totalCount > 10` 时要回退到单查 | 复用 tree，只在超过上限时单查 |
| 17 | `issue_tree.py` 的 `main()` 命令行入口（第 270–281 行） | 5 | 生产代码里没有调用方（board 和 `status.py` 都是 import `read`）；只有 `docs/notes/stage-two-shared-experience-layer.md` 第 38 行手动用过一次 | 可选。它当诊断工具，成本很低 | 可留 |
| 18 | `mmw-v2/tests/verify-ticket/test_draft.py` 第 119 行伪造 `git config … .mmw-base-branch` | 3 | `verify-ticket.py` 已经不再读这个键 | 无 | 删掉这个假分支 |

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 10 行 "The ticket is the only state. Every run reads it fresh… which is the only part any program reads."：它让 agent 不在本地存状态、不手改事件评论，也知道第一行怎么写都不影响程序。`docs/adr/0019-ticket-state-is-a-fold-of-events.md` 在 agent 这一侧就靠这一句落地。
- `SKILL.md` 第 20 行 "Resolve it from this file's own location; the path differs by machine and by host."：防止 agent 把解析出的绝对路径写死。`SKILL-SET-REVIEW.md` 点名要保留这类句子。
- `SKILL.md` 第 22 行 "A criterion names a judge by its bare name… a judge run by hand needs that directory on `PATH`."：agent 手动复现一条 `CHECK:` 时，碰到 `command not found` 能靠这句知道原因。
- `SKILL.md` 第 35 行 `## Reached from here` 那一条：把碰产品、端口、进程的情况交给 `ui-acceptance` 的五条规则。
- `sub-issues.md` 表格的 "Not this kind" 一列，尤其是第 1 行 "A process you did not start that looks stuck: it is another run's, and you never end it" 和第 3 行 "An internal name or data structure whose alternatives have no observable difference; decide it and record it in `DECISIONS`"：这是 `SKILL-SET-REVIEW.md` 推荐的"判据加对照例子"写法。前一句防止 agent 杀掉别人的进程，后一句防止它把不影响结果的小事都开成 decision 去问人。
- `sub-issues.md` "Ask these questions in order. The first yes decides the kind."：这个顺序是真实的判断依据，不是形式。比如一个坏掉的判官同时像 contract 和 fault，按顺序它先落到 `fault`，而 fault 要求 worker 停下。
- `linting.md` 第 27 行末句 "The graph comes from the tracker's blocking links, the same ones `--preflight` refuses on and `advance` dispatches from."：让 agent 知道图的问题要去 tracker 上的 blocking link 改，不是改票正文。精简时并进新正文。
- `linting.md` 第 43 行 "every `WARN` has been looked at and either fixed or kept on purpose"：这是完成判据。精简时并进新正文。

### 缺口与补充草稿

- `SKILL.md` 第 10 行之后。缺的是：这些运行对全局意味着什么。worker 和 main agent 读完只知道"跑 CHECK、贴事件"，不知道一次运行的价值在于"它本可能出另一种结果"。做浅了的表现：`Green before work:` 里列出的判据被当成白捡的绿，criterion 红了就去绕开它。`implement` 第 117 行确实要求解释 `Green before work`，但没给理由，agent 只会照格式填一行。
  > Nobody watches a ticket being worked. What the user reads in the morning, what the main agent lands on, and what a later night re-runs are the events these runs leave on the ticket, so a run is worth something only if it could have come out the other way. A criterion that passes without the work, or fails for a reason unrelated to it, is a false statement to every one of those readers. A surprising result, red where you expected green or green before any work was done, is news about the criterion or the product: explain it on the ticket, never route around it.

- `sub-issues.md` `## Which kind it is` 之前。缺的是：kind 就是路由。agent 在 `contract` 和 `decision` 之间犹豫时，不知道前者今晚就会叫醒 main agent 去改来源，后者要等用户早上看。它也不知道子 issue 的读者没见过它的会话。依据是 `dispatch/references/night.md` 第 84–87 和 116–118 行的处理表，以及 `relay.py` 第 297 行。
  > The kind decides who reads the child and when, so pick it by who can answer it. `fault` and `contract` wake the main agent tonight, which repairs the pipeline or the source and resumes this ticket. A `decision` waits for the user in the morning while you carry on with the default. `finding` and `deferred` wake nobody: findings are routed at the end of the night, deferred work by triage. Write the body for that reader, who has not seen your session: what you ran, what you saw, what the source says, and what in it still holds.
  >
  > Opening a child is not undone by running the command again. If a call's result was lost, look for its `child.opened` on this ticket before you run it a second time.

  第二段的依据是 #414：工具调用被截断，没有 stdout 也没有退出码，但底下的进程已经执行完了，agent 按规矩重跑。`--closeout` 和 `--decisions` 都有防重跑机制，`--sub-issue` 没有。

- `linting.md` 精简后的正文核心（放在三条命令之后）。缺的是：lint 能证明什么、不能证明什么。现在的文字让人以为"零 ERROR 就是批次正确"，main agent 于是把 lint 干净当成可以开夜的全部依据。
  > The lint reads how the batch is written, never what it means. Zero `ERROR` says every ticket can be started in order and every criterion can be run and decided. It does not say that a criterion would fail without the work, that the cut is right, or that the blocking links are the true dependencies: those were settled with the user before publishing, and this run cannot re-check them. The graph it checks is the tracker's blocking links, the same ones `--preflight` refuses on and `advance` dispatches from, so fix an edge there. Each `WARN` is a question the script cannot answer; answer it from the ticket and the spec, and keep it only when you can say in one line why the ticket is right as written. The batch is ready when `ERROR` is at zero and every `WARN` has been answered.

- 在 git 历史里找到、值得恢复的原文（建议放进 `implement`，见"与其他技能的重复或交接问题"）。它们在 9308ec7c（"docs(skills): cut the worker's load in implement and verify-ticket"）删 `references/running-criteria.md` 时一起没了：
  - "`--reverify` reads the ticket and runs every criterion again, including the ones the newest run ticked, so the worker's ticks are re-run rather than trusted."：说明最终运行为什么存在。`implement` 第 108 行只写了 "includes criteria earlier runs already ticked"，没写原因。
  - "Copy that line into the closing comment. It is something to explain there, not a verdict on the work."（说的是 `Outside Owns:`）：没有这句，agent 容易把 Owns 之外的改动当成扣分项，要么藏起来，要么该改时不敢改。

## C. 死板的流程

本技能的文本里没有需要放开的死板流程。worker 的编号步骤和 resume 表都在 `implement`，不属于这份报告。`sub-issues.md` 那五个有序问题靠顺序化解重叠，本身是判断依据，保留（见 B）。`linting.md` 是一份规则目录，不是流程，问题归在 A 的冗余。

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| 1 | `verify-ticket.py` `review_problems` 与 `spec_judgement`（第 1236–1250、2112–2134 行）：用正则在 reviewer 的自由正文里找 `Missing\|缺失`、编号行、"should not"、"reasonable" | 用脚本去猜人写的散文，是一种死板的替代判断：编号行只要碰巧提到行 id 就被当成 Missing，措辞一换就漏掉 | `review_problems` 按 A#11 删掉；`spec_judgement` 只在 `--touched` 和 `--draft` 里给提示，不拦任何东西，可以保留，但不要再加别的依赖它的拦截 |

## 脚本

过度防御和重复都已列在 A#10–18。下面几条是读分支时发现的、与"轻量"无关的真实缺陷。它们会让拒绝消息说错话，按 `docs/adr/0008-silence-is-never-a-pass.md` 的标准要单独修：

- `run_baseline_if_needed`（第 1963–1981 行）用 `except (OSError, subprocess.CalledProcessError)` 包住 `fetch_comments` 和 `fetch_body`。可这两个函数已经把这些异常全部转成了 `TrackerReadError`（第 158–180 行，#440），所以这里的 `except` 是死代码。tracker 读取失败时，异常一路冒到 `main()` 第 4012 行，打印 "Nothing was run or written; retry the same command"，而这时 claim 和 `ticket.claimed` 其实已经写上去了。
- `blocker_fold`（第 1861–1866 行）是同一个问题：`--preflight` 里某个 blocker 的评论读取失败时，本该按 `events.blocker_hold` 记成 "the tracker did not answer for it"，现在走不到这条路径，整个 preflight 直接 exit 2，也不写 `ticket.refused`。
- `ticket_spec`（第 208–215 行）只捕 `ParentUnreadable`、`CalledProcessError`、`OSError`。当 tracker 没有 parent link、要回退去读 `fetch_body` 时，抛出的 `TrackerReadError` 会漏出去。在 `run_sub_issue` 里，这发生在子 issue 已经建好之后（第 1630–1636 行只捕 `OSError`、`CalledProcessError`），于是 `main()` 告诉 agent "retry the same command"，结果会重开一个重复的子 issue。只有 tracker 上没有 parent link 的票会走到这条路径（手工建的票），概率低，但后果正是 `run_sub_issue` 的 docstring 说要防的那种。
- `events.py` 模块 docstring 第 50–52 行说 `child` 打印四个字段 "kind<TAB>spec<TAB>resolution<TAB>became"，第 945–946 行实际打印五个（多一个 `reason`）。
- 与 vendored gate-check 的接入：merge-note `mmw-v2/merge-notes/unlazy.md` 说的三个 symlink、传给 gate-check 的参数（`--cwd`、`--reverify`、`--timeout`、调 gate-lint 时不加 `--strict`）都与代码一致，没有发现问题。有一处结构性重复：`parse_criteria`（第 720–785 行）和 `ledger_with_results`（第 615–664 行）在 Python 里把 `gates.mjs` 的 `parseGates` 又实现了一遍，第 723–730 行的 docstring 自己也承认"两个读者意见不一"出过事故。可选的改法是写一个很小的 node 程序调用 `parseGates` 和 `gateState`、输出 JSON，让这份解析只剩一个读者。代价是 closeout 读草稿时也要经过 node；closeout 本来就依赖 node，所以没有新增依赖。这是设计上的选项，不是必须改的问题。

## 与其他技能的重复或交接问题

- `sub-issues.md` 表格的第 1、2、3、5 行，与 `implement/SKILL.md` 第 24、28、29、34 行对 fault、contract、decision、deferred 的定义几乎逐句重复。建议保留 `sub-issues.md` 这张表作为唯一的判定依据（`docs/contexts/ticket-run/CONTEXT.md` 的 _Home_ 已经指向它）；`implement` 那边只留"做什么"（继续还是停下、正文写什么），kind 的定义指回这张表。"流水线本身坏了"包括哪些部件，这份清单有五处副本：`implement` 第 24 行、`sub-issues.md` 第 19 行、`ui-acceptance/SKILL.md` 第 36 行、`ticket-run/CONTEXT.md`、`events.py` 第 83–87 行的注释。
- `--lint` 的退出码有两份（`linting.md`、`dispatch/references/night.md` 第 49 行），`--help` 里一份也没有。建议留 `night.md` 那份（main agent 行动时读的就是它，也带那条判断），脚本 `EXIT_CODES` 补上。
- Critical flows 行的形状有三份：`to-spec/SKILL.md` 第 98 行、`linting.md` 第 35 行、脚本里的 `CRITICAL_FLOW_SHAPE`。保留 `to-spec` 和脚本那两份。
- 精简 `linting.md` 时，要同步改这些把它当成规则所在地的指针：`mmw-v2/merge-notes/to-tickets.md` 第 29 行（"那次 run 读什么、报什么、退什么码写在…`references/linting.md`"）、第 147、149、174 行，以及 `mmw-v2/downstream-notes/455-journey-break.md` 第 20 行（"规则见 …linting.md"），改为指向脚本输出或 `to-tickets` / `to-spec`。
- B 里那两句从历史中找回的原文（"re-run rather than trusted"、"not a verdict on the work"）应该放进 `implement` 的第 4 步和第 2 步，那是 worker 真正做这件事时读的地方。请负责 `implement` 的调查员决定。
- `events.py` 和 `issue_tree.py` 放在本技能的 `scripts/` 下，但实际是整条流水线共用的库：dispatch 的 `relay.py`、`status.py` 和 board 的 `board_data.py`、`codeversion.py` 都从这里加载。这里只做记录；放在哪里本身不增加 agent 的阅读负担。
- `docs/adr/0008-silence-is-never-a-pass.md` 正文说拒绝消息的三段结构"写在 `mmw-v2/skills/verify-ticket/scripts/refusal.py`"，这个文件不存在，实际在 `mmw-v2/skills/ui-acceptance/scripts/refusal.py`（`mmw-v2/tests/dispatch/test_dispatch.sh` 第 2237–2238 行就是从那里拷的）。本技能目录下的 `__pycache__/refusal.*.pyc` 是 gitignore 掉的本地残留。

## 没查到的

- `mmw-v2/upstream-unlazy/` 的上游原代码没有和上游仓库做 diff，只核对了 merge-note 描述的接入点（symlink、传参）与代码一致。
- `mmw-v2/tests/verify-ticket/` 下的测试只 grep 了与删除候选相关的部分，没有通读，也没有运行。
- A#10 "旧票还在读 mmw-base" 只搜了 `agentflow-hq` 这个 owner；其他消费仓库没搜。A#14 "开着的票上还有没有旧格式 review" 没有核实。
- `reads_as_spec` 对没有 layer label 的 spec 的回退分支（第 3703–3707 行），没能查清还有没有不带 `mmw:spec` 的开着的 spec，所以没有列进删除项。
- `lint_check_effects`（`[shared-state]` WARN）有没有真实触发过，没查到证据；它只是一条 WARN，成本低，所以没列。
- `events.py` 里 `spec.retroed` 那约 50 行校验属于 retro 的范围，只确认了它确实有写入方（`retro.py`），没有评估是否过度。
