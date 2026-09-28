# resolving-merge-conflicts

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：技能正文 217 词，上游写法加上本仓为"干净合并却检查变红"补的几句都成立，不动。两个缺口都在调用方 `implement` 那一侧：
- worker 解冲突时，不知道对面那一边是已经关掉的票。
- "干净合并却检查变红"只在 closeout 才暴露，而那一步原来不指向这个技能。

两处改动都记在 `implement` 定稿里（I12、I13），这里只列出来源。

### 增加（落在 `implement`）

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `implement` 第 1 步，"note each trade-off under `Decisions I made on my own`." 之后 | 见 `implement` 定稿 I12。 | 本技能第 3 步说"选符合合并目标的一边"，而 `integrate` 的合并没有这种目标。有了这句，worker 知道已落地的一边是合同，两边真正无法同时成立时，开 `contract` 子票交给主 agent，而不是自己挑一边。**推断**：没有找到这样出过事的记录，但 bounce 之后的重试不经过 reviewer（ADR 0027，#915 时间线可证），worker 的选择没有第二个人看。 |
| I2 | `implement` 第 8 步，repo-checks 失败那一处 | 见 `implement` 定稿 I13。 | 合并本身没有冲突、检查却变红时，worker 会把它当成自己的 bug 修，而不是去读合进来的票。 |

### 不采纳

- 让 `dispatch.sh integrate` 在干净合并后自己跑一遍 `checks`：每次带票的 `integrate` 都要多跑一遍整套检查，而这条路径还没有真实触发过（本仓 `.mmw/target.json` 没有 `checks`，agentflow 也没找到 `reason` 为 `checks` 的 bounce）。先补文字，真出现一次再改脚本。

## 结论

`mmw-v2/upstream/skills/engineering/resolving-merge-conflicts/SKILL.md` 共 217 词（正文 193 词，上游原版正文 117 词，本仓加了约 76 词加一行 description），没有 reference，没有脚本，只有上游的 `agents/openai.yaml`（两行，不涉及 `disable-model-invocation`）。本仓的改动全部落在一件事上：把"干净合并但仓库检查变红"也归给这个技能（#340），改动的每一段在 `mmw-v2/merge-notes/resolving-merge-conflicts.md` 都有条目，条目与现文一致。技能正文里没有可删的：没有历史碎碎念，没有复述脚本，没有死板的本仓流程；估计可删 0 词。

夜间 `advance` 的合并步骤**不直接**把冲突交给这个技能，这是有意的设计（`docs/adr/0023-origin-base-branch.md`、`docs/adr/0027-a-bounce-returns-once.md` 都否决了"main agent 在 merge worktree 里解冲突"）：`advance` 把冲突 abort 掉、写 `ticket.bounced`，下一次 `advance` 在原工作区重启该票的 worker，worker 按 `implement` 的续跑表回到第 1 步，`dispatch.sh integrate` 重现冲突并在 stderr 点名这个技能。这条链在真实夜里走通过（agentflow #915，下文有证据）。

问题不在技能本身，而在调用方那一行少了两样东西：一是 MMW 里"对面那一边"是已经关票、`reverify` 还会再跑一遍的票，而 bounce 之后这次合并不再经过 reviewer，技能那句 "pick the one matching the merge's stated goal" 在这里没有着落；二是"干净合并让检查变红"这种情况只在第 8 步 `--closeout` 才被发现，而第 8 步没有指向这个技能。两处都建议在 `implement` 的调用行补，不改上游原文。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | 无 |

逐项核过、判定不删的：

- 第 2 步本仓加的 "identify each ticket represented by its new first-parent merge commits"：`dispatch.sh` 的 `integrated_ticket_numbers`（`mmw-v2/skills/dispatch/scripts/dispatch.sh` 第 2472 行起）已经算出同一份清单，`integrate` 干净合并时印在 stdout（"incoming tickets: #a #b"），冲突时印在 stderr。所以走 `integrate` 的 worker 手里已经有这份清单。但这个技能还会在不走 `integrate` 的地方被用到：bounce 原因为 `checks` 的重试（清单在 `ticket.bounced` 评论里，不在 `integrate` 输出里）、单独使用、以及将来 `finish` 失败后的处理（见"交接问题"）。这一句只有十来个词，删掉后这些场景的 agent 要自己想怎么找票。留。
- 第 3 步的 "Always resolve; never `--abort`."：`tool-guard.py` 里没有拦 `merge --abort` 的代码（grep `abort` 0 处），这句是唯一的约束，而且与 `implement` 第 99 行 "Never rebase, abort or push from this integration command" 一致。它是 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 里明说要留的那类禁止句。留。
- 第 2 步上游原有的 "check the PRs"：MMW 不开 pull request（`docs/adr/0023-origin-base-branch.md` 的 Considered Options 最后一条），这几个字在 MMW 里找不到东西。但它不会让 agent 做错事，只是多一次空查；merge-note 明写保留。按上游规则不报。
- 第 5 步 "If rebasing, continue the rebase"：MMW 不 rebase，这句在夜里走不到，但它是上游原文，对单独使用有用，不会误导。不报。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 8 行（第 2 步）"Understand deeply why each change was made, and what the original intent was."：整份技能的立足点。它把"解冲突"从挑文本块变成在两个意图之间做选择；没有它，剩下的就只是 `git checkout --ours/--theirs`。
- 第 10 行（第 3 步）"Preserve both intents where possible. Where incompatible, pick … and note the trade-off."：给出了默认目标（两边都保住）和退路的代价（要写下丢了什么）。agentflow #915 的 worker 在 closeout 的 `Decisions I made on my own` 里写了 "On the bounced merge, preserved #916's current-seed 29-item consumer assertion …; the archived 15-item representation remains a separate contract."，就是照这句做的。
- 第 10 行 "Do **not** invent new behaviour."：防止 agent 为了让两边都能编译而写出两边都没有的第三种行为。这是合并里最难被审出来的错误，因为 diff 看上去"两边都照顾到了"。
- 第 10 行本仓加的 "With no conflict markers, trace the failing path across the merged tickets rather than treating either side in isolation."：干净合并变红时，没有冲突标记告诉 agent 该看哪里；这句告诉它问题在两张票的交界处，不在任何一边单独的代码里。merge-note 明写这一条必须留。
- 第 8 行本仓加的 "read its ticket and closeout evidence before changing the combined behavior"：closeout 证据就是对面那张票证明过什么；先读它，修的时候才不会把对面已经验过的行为改掉。
- 第 12 行（第 4 步）"Fix anything the merge broke."：把检查结果和"合并的责任"绑在一起，而不是只跑一遍看看。

上游 `mmw-v2/upstream/docs/engineering/resolving-merge-conflicts.md` 里有两句很好的"为什么"（"The failure mode this exists to kill is resolving by flag …" 与 "a merge is the easiest place in git to produce code that satisfies both branches and passes neither's tests"），但 docs 页不随技能装进宿主，agent 看不到。我**不建议**把它们搬进 `SKILL.md`：同一份 docs 页明说这个技能有意写得很薄（"That is a thin margin over a good model, and it is meant to be"），而且现有第 2、3 步的措辞已经足以让 agent 做对。搬进来是一处新的上游改动，换不来行为上的变化。

### 缺口与补充草稿

- **缺口 1：`implement` 第 1 步交给这个技能时，没告诉 worker "对面那一边"在 MMW 里意味着什么。** 技能第 3 步说 "Where incompatible, pick the one matching the merge's stated goal"。在 `integrate` 的合并里，合并的"既定目标"就是一行 "Merge <into> into issue-<n>"，等于没有；worker 只能自己决定保哪一边。而 MMW 里两边的分量不一样：
  - 对面是已经关票、已经落地的票。收夜时 `reverify` 会在 base branch 上把每张已落地票的判据再跑一遍，红的票被重开进 `needs-triage`（`mmw-v2/skills/dispatch/references/night.md` 第 214 行）。worker 如果为了保住自己票的行为把对面的行为改掉，这里不会失败，要到几个小时后才在**另一张没人在做的票**上变红。
  - bounce 之后的重试不再启动 reviewer（`implement` 续跑表第 86 行；`docs/adr/0027-a-bounce-returns-once.md` 第 8 行"不再启动 reviewer，因为 reviewer 已经审过 ticket 自己的改动"）。#915 的时间线证实了这一点：bounce 22:20，重试 worker 22:22 认领，22:29 关票，22:30 落地，中间没有 `reviewer.started`。所以重试时的冲突解法，除了 worker 自己，没有第二个人看。`Decisions I made on my own` 那一行是唯一的记录，而且没人会逐行判它（Spec axis 只在 review 里判 DECISIONS）。
  - 两张票的判据互不相容，本质是切票时漏了一条边。`implement` 第 34 行对同样的情况已经有答案："one file has one writer at a time and the cut missed an edge"，走 `contract` 子票。但这条写在"写代码"一节，worker 在第 1 步解冲突时不一定把两件事联系起来。

  agent 因此会怎么做错（推断，没有找到实际发生的记录）：碰到真正不相容的两边，它会按技能第 3 步挑一边、记一行 trade-off，然后继续关票；如果挑的是自己这边，代价会在 `reverify` 时落到对面那张票上。

  建议放在 `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 99 行，紧接 "note each trade-off under `Decisions I made on my own`." 之后（这是调用方在行动那一刻读的那一行，符合 `SKILL-SET-REVIEW.md` `### Upstream skills` 的"先在调用方接"；不改上游原文）：

  > The incoming side is closed tickets, and the closing pass's `reverify` runs their criteria again on the base branch: a resolution that drops their behaviour passes here and reopens their ticket hours later. Read their criteria before choosing. Where theirs and yours cannot both hold, the cut missed an edge: keep what landed and run `<engine> <n> --sub-issue contract <file>` naming both tickets. After a bounce this merge gets no second review, so that `Decisions` line is the only record of what you chose.

  它改变做法的地方：给了技能里"merge's stated goal"在 MMW 里的具体答案（已落地的一边是合同，不是可以取舍的一方）；把真正的不相容从"worker 私下挑一边"改成"交给 main agent 的 `contract` 子票"，与 `implement` 第 34 行同一个逻辑；并告诉 worker 为什么这次要格外认真（没人复审）。约 80 词。

- **缺口 2："干净合并让仓库检查变红"只在第 8 步被发现，而第 8 步不指向这个技能。** `implement` 第 99 行写 "A clean merge that makes repository checks red uses the `resolving-merge-conflicts` skill too."，但在第 1 步，worker 通常不知道检查是不是红的：
  - `<engine> <n>` 只跑本票判据；仓库的 `checks`（`.mmw/target.json`）只在 `--closeout` 里跑（`mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 第 2438–2445 行，全文只有这一处调用 `run_target_json_checks`），也没有单独跑它的子命令。
  - 所以第 1 步那句只在一种情况下能生效：bounce 原因为 `checks` 的重试，`ticket.bounced` 评论里写着 "Failed checks: …"（`dispatch.sh` `bounce_ticket`）。第一次 `integrate` 后的干净合并回归，要到第 8 步 closeout 才露出来，而第 8 步只说 "fix the code, run that suite yourself, commit, make step 4's final run again, and close out again"，没有提示这可能是合并的问题、该去读合进来的票。
  - `mmw-v2/merge-notes/implement.md` `## Integrate before the worker criteria` 写的意图是 worker "resolves conflicts and clean-merge regressions before review and verification"。对冲突，这个意图实现了；对干净合并回归，没有实现：它在 review 之后才被发现，修复也不会再被审。

  我在两个 tracker 上没有找到 `reason` 为 `checks` 的 `ticket.bounced`（本仓 `.mmw/target.json` 没有 `checks` 键，永远不会有；agentflow 用 `gh search` 查 "Failed checks" 没有命中 bounce 评论），所以这条路径还没有真实触发过的记录。但它是正常输入就能走到的路径（两张票各自检查全绿、合在一起变红，正是 #337 立项要抓的"并行票的功能冲突"），不是过度防御。

  建议只补文字，放在 `implement` 第 120 行（第 8 步）"When it stops because the repository's own checks failed," 这一句里：

  > When it stops because the repository's own checks failed and the failing check covers code an incoming ticket of your integration changed, the failure is the merge's: use the `resolving-merge-conflicts` skill. Otherwise fix the code, run that suite yourself, commit, make step 4's final run again, and close out again.

  另一种做法是让 `dispatch.sh integrate` 在干净合并且带进了票时自己跑一遍 `checks`、红了用新的退出码点名这个技能，这样回归能在 review 之前被发现，符合 merge-note 的原意。代价是每次带票的 `integrate` 都多跑一遍整套检查，而且这条路径还没有真实触发过。我倾向先补文字，等真出现一次再考虑改脚本。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| — | — | 无 | 不改 |

技能是上游的五步编号列表，每一步都是方法本身（先看状态、再找来源、再解、再验、再收尾），顺序也有实际依赖：不读来源就解不了意图，不跑检查就不该提交。本仓的改动没有加新步骤，只是在第 1、2、3 步各加了一个"没有冲突标记时"的分支句，没有模板、没有穷举表。没有需要放开的地方。

## 脚本

技能本身没有脚本。与交接有关的 `dispatch.sh` 代码我读了，没有发现过度防御或死代码：

- `integrate_ticket`（第 2506 行起）与 `integrate_conflict_report`（第 2478 行起）：每条拒绝都对应一个真实前提（不在 `issue-<n>` 分支、有未提交改动、与 base 没有共同祖先）；冲突时保留 `MERGE_HEAD`、返回 3、不 abort，与技能的 "never `--abort`" 一致。
- `land_one_via_origin`（第 2993 行起）在冲突时 `git merge --abort` 再 `reset --hard`：这是脚本在自己的 merge worktree 里撤回，不是 agent 放弃合并，与技能不矛盾；ADR 0023 与 0027 说明了为什么落地合并不在这里解。
- `integrated_ticket_numbers`（第 2472 行）只认 `Merge branch 'issue-<n>'`，这正是 `land_one_via_origin` 第 3010 行写的落地提交标题，两边一致；技能第 2 步 "new first-parent merge commits" 与它、与 `code-review` 的 `references/spec-reviewer.md` `### Read tickets already integrated into the base branch` 用的是同一个算法。

## 与其他技能的重复或交接问题

- **`advance` → 本技能的交接链（重点）**：`advance` 不把冲突交给任何 agent，而是 bounce。链条是：`land_one_via_origin` 冲突 → abort、`bounce_ticket` 写 `ticket.bounced`（带冲突文件与之后落地的兄弟票）→ 当夜第一次 bounce 放回 `ready-for-agent`（`bounce_goes_to_triage`）→ main agent 按 `night.md` 第 78 行再跑一次 `advance` → 在原工作区启动新 worker（提示词只有 "Use the implement skill to work ticket #n"）→ `implement` 续跑表第 86 行回到第 1 步 → `integrate` 重现冲突、退出 3、stderr 点名本技能 → 解完在 `Decisions I made on my own` 记取舍 → 第 4 步起直到 closeout → 下一次 `advance` 落地。
  - 真实证据：agentflow #915（2026-09-15）。22:20:46 `ticket.bounced`（冲突文件 `tests/contracts/test_runtime_policy_delivery.py`，兄弟票 #916）→ 22:22:04 `worker.started` → 22:25:43 本票自跑 ALL MET → 22:28:50 仓库检查 1/1 → 22:29:00 `ticket.passed`，Decisions 里有保留 #916 断言的那一行 → 22:30:35 `ticket.landed`。重试 worker 的合并提交是 `cb154959b`（"Merge ticket #916 setting contracts into #915 consumer proofs"），`git show --remerge-diff` 显示它解了冲突标记。
  - `integrate` 自己的冲突在 agentflow 历史里出现过至少 5 次（`git show --remerge-diff` 有冲突标记的 `Merge work-monitor-720-722 into issue-7xx` / `issue-832` 提交，2026-09-12 到 13），都没有卡住流程。
  - 第二次 bounce、以及夜外 `land` 的 bounce，直接进 `needs-triage` 交给人，这是 ADR 0027 定的，不是交接缺口。
- **`finish` 与 `open` 的合并冲突没有去处**：`finish` 把 base branch 合进 project branch 时冲突或检查变红，退出 1，merge 已被 abort（`dispatch.sh` `finish_spec` 第 4194 行起）。`night.md` 第 238 行只说退出 1 是什么意思，不说接下来谁做什么；`open` 的冲突也一样只有一句 "A conflict is the only refusal"（`docs/contexts/night/how-it-works.md` 第 51 行）。这时用户在场（`finish` 只在用户验收后跑），所以不会卡住夜里的工作，但 main agent 手里没有一条路：可行的做法是在一个 project branch 的 checkout 里合并 `origin/<base branch>`、用本技能解、推送，再跑 `finish`（`finish_spec` 看到 project branch 已包含 base 会走"already contained"分支、记 `spec.merged`）。我没有找到这种情况真实发生过的记录。这属于 `night.md` 的问题，建议由负责 `dispatch` 的调查者判断是否在第 238 行补半句。
- **`integrate` stderr 与技能第 4、5 步部分重复**："run the repository checks affected by the merged tickets, commit the merge, then run dispatch.sh integrate again" 复述了技能的"跑检查、提交"，但它是调用方的连接句，加了 MMW 才有的两点（检查范围、重跑 `integrate` 确认）。两边都留。
- **`mmw-v2/merge-notes/implement.md` `## Integrate before the worker criteria` 的两处与现实不符**：一是 "resolves conflicts and clean-merge regressions before review"（干净合并回归实际在 review 之后才被发现，见缺口 2）；二是 "It merges `origin/<base branch>` into the ticket branch with a fixed merge message"，冲突时提交信息是 worker 在 `git commit` 时自己写的（#915 的 `cb154959b` 就不是固定格式）。第二处没有任何程序依赖（`integrated_ticket_numbers` 只认 advance 的落地标题），无害，只是说明不准。
- **`ask-matt` 的技能清单条目**（`mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 82 行）复述了本技能的两种触发：这是路由表，该留。
- **`code-review` 的 `spec-reviewer.md`** 用同一个 first-parent 算法找已合入的票，审组合行为。它和本技能第 2 步是不同角色在不同时刻做的事，都该留；只是 bounce 重试时它不会再跑（缺口 1 的第二点）。

## 没查到的

- 没有读 worker 的会话记录，所以不知道 #915 以及 work-monitor 那几次 `integrate` 冲突里，worker 是否真的加载了这个技能，还是凭常识解的。能确认的只有结果：冲突解了、Decisions 里有取舍记录（#915）、流程没卡住。
- 缺口 1 描述的"挑了自己这边、把对面的行为改掉"没有找到实际案例，是从机制推出来的（`reverify` 会重跑已落地票、bounce 重试没有 reviewer）。
- `reason` 为 `checks` 的 bounce 只用 `gh search issues "Failed checks"` 在两个 tracker 上查过，GitHub 搜索对评论全文的覆盖不完整，可能有漏。
- 技能第 5 步 "Stage everything and commit"：在 ticket 工作区里，照字面 `git add -A` 可能把 worker 的临时脚本（`implement` 第 40 行允许不保留）一起提交进合并提交。这是上游原文，我没有找到发生过的记录，所以不报。
- 没有查上游 mattpocock/skills 在最近一次 squash（`5b1a4c51`）之后是否又改过这个技能。
