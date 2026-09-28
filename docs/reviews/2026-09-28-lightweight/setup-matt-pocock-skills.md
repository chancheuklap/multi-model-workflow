# setup-matt-pocock-skills

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能的问题不在冗余，而在于它不知道自己写出的文件在 MMW 里是流水线的一部分。它照上游提供 GitLab、本地 markdown、label 改名这些选项，可流水线只认 GitHub 和默认的 label 名。它的重跑会改写各仓库手工维护过的几节。它也不负责建流水线要用的 label，xiaohuangya 至今缺 `junior-worker`、`senior-worker` 和全部 `mmw:*` label。调查员的五段补充都有证据，采纳，并压短。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 开头，第 15 行之后 | What you write here is read at the moment of acting by every skill that publishes or triages an issue, and by every agent that explores this codebase; a wrong command or label is repeated by each spec, ticket and night after it, without an error. So make these files true of this repository rather than filling in the templates: check a command against the repository before you write it down. | 没有它，agent 照模板填完就交差，不去核对命令在这个仓库里能不能跑（sub-issues 开没开、`gh` 指向的是不是这个 repo）。 |
| I2 | `**Section A: Issue tracker.**`，"Default posture" 那段之后 | In this toolbox the tracker is also the landing pipeline's store: the skills that publish specs and tickets, the night's scripts and the task board talk to GitHub Issues through `gh` and to nothing else. Any other choice leaves the planning skills usable by hand, but no night can run on this repository; say that when you propose it. | 上游说本地 markdown "good for solo projects"，而你正是一个人用，这句会把 agent 推向一个跑不了夜间流程的选择，而且选完不会报错。只认 GitHub 是 `to-spec` 合并说明里已定的范围，这里只是让技能把它说出来。 |
| I3 | `**Section B**` 改名选项处 | The night's scripts and the ticket skills write the default label strings verbatim; an override changes what `triage` applies and nothing else. In a repository the pipeline runs on, keep the defaults. | 四个脚本和 `to-tickets` 都写死默认 label 名，没有一个读 `triage-labels.md`；改名后只有 `triage` 跟着用新名字，两边就分叉了。 |
| I4 | 第 4 步，替换 "a file that already exists under `docs/agents/` is updated in place, keeping the sections the seed lacks" | A file that already exists under `docs/agents/` is this repository's own record, and the seed is only where it started: change what this run's answers change, add what the seed has and the file lacks, and leave every other line as it stands. Report the other differences from the seed to the user instead of resolving them. | 原文字面上会按种子重写"种子也有的那几节"，而本仓的落地件正是在这些节里写了自己的规则。合并说明因此提醒维护者"重跑前先备份"，但执行重跑的 agent 读不到合并说明。补上这句后，那段备份警告可以删掉。上游对重跑的定位本来就是核对（`.out-of-scope/setup-skill-verify-mode.md`）。 |
| I5 | `**Section C: Domain docs.**` 之后（本仓加一句，不改上游原文） | An existing `CONTEXT-MAP.md` settles this section as multi-context, whether or not the repository is a monorepo; describe the layout it already has. | 上游只在看到 monorepo 信号时才提供多 context 布局。本仓和 agentflow 都有 `CONTEXT-MAP.md`，却没有 monorepo 信号（已 `ls` 核实），照字面重跑会写出与实际布局相反的 `domain.md`。 |
| I6 | 第 1 步与第 4 步查找指针处 | A pointer to a `docs/agents/` file in another shape (an `## Agent skills` block, an `## Issue tracker` section) counts as that file's row: replace it with the row rather than adding a second pointer. | agentflow、xiaohuangya、mmw-e2e-lab 用的都是旧格式的指针块，重跑时 agent 会原样保留旧块再加一组，同一份文件被指两次。**推断**：还没有重跑的记录。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 种子 `issue-tracker-github.md` `## Wayfinding operations` **Map** 那一行列举的四节名 | 改为 "holding the map body the `wayfinder` skill writes"；两个 label 与那条命令保留；落地件第 78 行、合并说明同步 | 已经过时（`wayfinder` 的 map 正文有五节），也没有人照着这里写。 |
| D2 | 种子 `## Three label sets` 的颜色与说明表，以及 `to-spec`、`to-tickets`、`wayfinder` 各一句 "create it as `docs/agents/issue-tracker.md` `## Three label sets` gives, when the repository lacks it" | 三组 label（layer、queue、grade）的名字、颜色与说明只在 `verify-ticket.py` 里定义一次：把现有的 `CLASS_LABELS` 扩成三组，`to-spec`、`to-tickets` 共用的那一个发布命令（见这两份定稿的 D1）在发布时缺什么建什么；`dispatch.sh` 的 `ensure_label` 改为读这份定义。种子表格删掉，改为一句指向它；三个技能那一句删掉；本技能不另加建 label 的步骤，也不另写脚本 | 同一组颜色与说明现在有四份（`verify-ticket.py` 的 `CLASS_LABELS`、`dispatch.sh` 的 `ensure_label`、种子、落地件）；queue 和 grade 两组没有任何东西负责建，xiaohuangya 因此缺 label，第一次发票就会失败。label 在第一次发布时由发布命令补齐，就不需要单独的建 label 脚本和记得去跑它的那句话 |

## 结论

技能目录共 3,158 词：`SKILL.md` 987 词，五份种子模板 2,155 词（`issue-tracker-github.md` 887、`issue-tracker-gitlab.md` 596、`domain.md` 270、`issue-tracker-local.md` 267、`triage-labels.md` 135），`agents/openai.yaml` 16 词；没有脚本。本仓改过的部分不多：`SKILL.md` 约 170 词（第 24、67、74、76、78 行与第 80 行后半句，替换了上游约 190 词的 `## Agent skills` 块），`issue-tracker-github.md` 约 310 词（`**Every list read is a whole list.**` 与 `## Three label sets`），其余三份种子只有 host 中立的措辞改动。这些本仓内容里几乎没有可以直接删的（净删不到 100 词）；问题在另一边：技能不知道自己是在为 MMW 的 landing pipeline 配一个 consuming repository，所以在三处会把 agent 带错。第一，它照上游提供 GitLab、本地 markdown 与 label 改名，而流水线脚本只认 GitHub 和默认的 label 字符串。第二，流水线要写的 label 没有人负责建：`xiaohuangya` 现在就缺 `junior-worker`、`senior-worker` 和四个 `mmw:*`。第三，重跑时它会按种子改写已经手工维护过的落地文件。上游原文的"灵魂"（先探查再问、推荐答案放前面、`proceed silently`、`Flag ADR conflicts`）是完整的；缺的是本仓应补的那一两句"这些文件在 MMW 里被谁读、错了会怎样"。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| 1 | `issue-tracker-github.md` `## Wayfinding operations` 第 68 行 **Map**："holding the Destination / Notes / Decisions-so-far / Not yet specified body" | 6（重复，且已过时） | `wayfinder/SKILL.md` `### The map body`（第 26–53 行）的 map 正文有五节，第五节是 `## Out of scope`；种子只列四节。落地件 `docs/agents/issue-tracker.md` 第 78 行同样只列四节。合并说明 `mmw-v2/merge-notes/setup-matt-pocock-skills.md` 那一行写的是"正文四节写成 `wayfinder` 技能实际写的"，它本身也已经过时 | `wayfinder` 建 map 时读的是它自己的 `### The map body` 模板，这一份清单没人拿来照着写。删掉后没有剩余风险 | 改成 "holding the map body the wayfinder skill writes"，两个 label 与那条 `gh issue create` 命令保留。落地件第 78 行同改；合并说明里"四节名保留"改成"两个 label 保留" |
| 2 | `issue-tracker-github.md` `## Three label sets` 第 32–40 行的颜色与说明表（"The layer labels, with the colour and description a repository that lacks one creates it with"），以及三个技能里对应的一句："create it as `docs/agents/issue-tracker.md` `## Three label sets` gives, when the repository lacks it"（`to-spec/SKILL.md:34`、`to-tickets/SKILL.md:143`、`wayfinder/SKILL.md:112`） | 1 + 6 | 同一组颜色与说明现在有四份：`verify-ticket.py:62–65` 的 `CLASS_LABELS`、`dispatch.sh:4290` 的 `ensure_label`（只有 `mmw:ticket`）、这份种子、落地件 `docs/agents/issue-tracker.md:47–50`。每个 consuming repository 的落地件里还各有一份。建 label 是确定性操作，现在交给 agent 手抄。更要紧的是，queue 和 grade 两组 label（`needs-triage`、`ready-for-agent`、`ready-for-human`、`junior-worker`、`senior-worker`）没有任何技能或脚本负责建（`grep "label create"` 只命中上面两个 `ensure_label`）。用 `gh label list` 查的结果：`xiaohuangya` 只有四个 queue label（2026-09-07 建，与它的 `docs/agents/` 提交同一天，推断是手工建的），没有 `junior-worker`、`senior-worker`，也没有任何 `mmw:*`；`mmw-e2e-lab` 的 queue label 建于 2026-08-30，grade label 建于 2026-09-05，也是事后补的。上游自己把这个问题记成已知 bug：`mmw-v2/upstream/docs/engineering/triage.md:76`（mattpocock/skills #616） | 由一个脚本负责：它持有全部三组 label 的名字、颜色和说明（直接扩展 `verify-ticket.py` 的 `CLASS_LABELS`，不另起一份），已存在的 label 不动。本技能第 4 步写完文件后跑它一次；`dispatch.sh` 与 `verify-ticket.py` 里现有的两个 `ensure_label` 继续按需自建。剩余风险：这个改动之前配好的仓库不会自动补建 label，其中缺 `mmw:spec` 或 `mmw:map` 的仓库，第一次发 spec 或建 map 时 `gh issue create --label` 会直接报错（我没亲手复现这条报错，按 `gh` 的已知行为推断）。报错是显性的，agent 能看出缺什么，也能跑那个脚本。补建时的风险只剩颜色不统一 | 1）加这个 label 脚本（在 `verify-ticket.py` 加一个只做这件事的子命令，或者单独一个小脚本 import 同一张表）。2）本技能第 4 步加一句 "Create the labels the pipeline writes with `<that command>`; it leaves existing labels alone."。3）种子与落地件的 `## Three label sets` 只留第一张表和 "Put on by" 这一列，删掉颜色和说明两列，以及第 32–33 行的 `gh label create` 句子。4）三个技能里 "create it as … gives, when the repository lacks it" 那半句删掉。估计文字净删约 60 词（种子）+ 60 词（落地件）+ 45 词（三个技能），脚本增加 15–30 行 |

没有列进来的本仓内容，逐条看过，结论是留：

- `SKILL.md` 第 78 行 "Write `docs/agents/triage-labels.md`, and its row, only when…"：同一个条件在第 51、68、85 行也出现了，但这一句是上游原句（"Include the `### Triage labels` sub-block…"）换了对象后的改写，并不是本仓新加的重复。另外在本机，`triage` 由 `mmw-v2/skills.txt:26` 固定安装，这个条件永远成立，但这是上游为别的安装方式留的分支，不影响行为，不提。
- 第 76 行 `CLAUDE.md` 那一段：内容上和 `manage-agents-md` 重复，但问题在交接，不在冗余，见"与其他技能的重复或交接问题"第 1 条。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 15 行 "This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write."：这句给整个技能定了姿态，说明它是一次对话、要先看清再动笔，不是模板填空。
- `SKILL.md` 第 21 行 "Read whatever exists; don't assume"：重跑与已有布局的所有情况都靠这一句兜住（见下面的缺口 3、4）。
- `SKILL.md` 第 36 行 "Lead each section with the recommended answer so the user can accept it in a word"，以及第 49 行 "Leave it off and don't raise it"：这两句让 agent 明白用户的注意力是成本，不需要问的就不问。
- `SKILL.md` 第 30 行 "their absence means single-context, which is almost every repo"：防止 agent 给小仓库套一个多 context 的布局。
- `SKILL.md` 第 92 行 "re-running this skill is only necessary if…"：告诉用户这些文件是可以直接手改的，技能跑完以后它们就归仓库自己所有。
- `issue-tracker-github.md` 第 7–12 行 `**Every list read is a whole list.**`，尤其是 "Both truncate in silence… an agent that cannot see a ticket treats it as absent"：有真实事故作依据（合并说明记的 2026-09-06 agentflow spec #537，37 张子票里只看到 30 张）。这句理由正是让 agent 在种子没列到的列表命令上也自己补 `--limit`/`--paginate` 的原因。修剪时容易被当成修辞删掉，务必保留。
- `issue-tracker-github.md` 第 24 行 "Three sets, each answering one question, none standing in for another" 与第 42 行 "A layer label puts an issue in no queue."：这两句挡住的是最常见的误用，即拿 layer label 当 queue label 用。
- `domain.md` 第 11 行 "**proceed silently**… creates them lazily when terms or decisions actually get resolved"、第 45 行 "that's a signal: either you're inventing language… or there's a real gap"、`## Flag ADR conflicts`：这是种子写给之后每个读它的 agent 的工作态度，是整个 domain 层的核心。

### 缺口与补充草稿

1. **位置**：`SKILL.md` 开头，第 15 行之后。**缺什么**：技能完全没说它写出的文件在 MMW 里被谁、在什么时候读。`to-spec`、`to-tickets`、`wayfinder` 发 issue 时要按 `## Three label sets` 打 label；`triage` 读 `triage-labels.md` 和 PR 开关；每个探查代码的技能都读 `domain.md`。这些文件写错一处，之后每一份 spec、每一张票、每一夜都会原样照做，而且不会有任何报错。只把这一步当成"装一下配置"的 agent，会照模板填完就交差，不去核对命令在这个仓库里是否真能跑（例如 sub-issues 有没有开、`gh` 指向的是不是这个 repo）。
   > What you write here is read at the moment of acting by every skill that publishes or triages an issue, and by every agent that explores this codebase; a wrong command or label is repeated by each spec, ticket and night after it, without an error. The job is to make these files true of this repository, not to fill in the templates: check a command against the repository before you write it down.

2. **位置**：`SKILL.md` `**Section A: Issue tracker.**`，第 42 行 "Default posture" 那段之后；在 Section B 第 57 行之后加对应的一句。**缺什么**：MMW 的 landing pipeline 只认 GitHub（`to-spec` 的合并说明写了 "landing pipeline 只跑在 GitHub 上"；`dispatch.sh`、`verify-ticket.py`、`status.py` 里没有任何 `glab` 或 `.scratch` 分支）；四个脚本（`dispatch.sh`、`status.py`、`verify-ticket.py`、`tool-guard.py`）和 `to-tickets/SKILL.md:143` 都直接写死 `ready-for-agent` 等字符串，没有一个脚本读 `triage-labels.md`（grep 结果为空）。技能却照上游说本地 markdown "good for solo projects or repos without a remote"。这个用户正是一个人用，这句话会把 agent 推向一个跑不了夜间流程的选择。Section B 的改名选项也一样：改名后只有 `triage` 会跟着用新名字，流水线还在打旧名字，两边就分叉了。另外 `## Three label sets` 只存在于 GitHub 种子里，选了其他 tracker，三个技能指向的这个标题就不存在。
   > In this toolbox the tracker is also the landing pipeline's store: the skills that publish specs and tickets, the night's scripts and the task board talk to GitHub Issues through `gh` and to nothing else. Any other choice leaves the planning skills usable by hand but no night can run on this repository; say that when you propose it.

   Section B 加：
   > The night's scripts and the ticket skills write the default label strings verbatim; an override changes what `triage` applies and nothing else. In a repository the pipeline runs on, keep the defaults.

3. **位置**：`SKILL.md` 第 4 步第 80 行，"a file that already exists under `docs/agents/` is updated in place, keeping the sections the seed lacks"。**缺什么**：这半句只保住了"种子没有的节"，没有说种子也有的那几节怎么处理。字面读下来，那几节会按种子重写。本仓的落地件恰恰在这些节里写了本仓自己的规则：`triage-labels.md` 的 Meaning 列，`domain.md` 的 `## Before exploring, read these`、`## File structure`、`## Use the vocabulary in CONTEXT.md`。所以合并说明开头那段才要维护者"重跑这个技能之前先备份"，Nowledge Mem 里也有一条记忆（`610dbea8`，2026-09-01）专门提醒这件事。可是真正执行重跑的 agent 看不到合并说明。上游自己对"重跑"的定位是核对（`mmw-v2/upstream/.out-of-scope/setup-skill-verify-mode.md`："don't rewrite anything, just check my existing files against the current seed templates and report drift"）。
   > A file that already exists under `docs/agents/` is this repository's own record, and the seed is only where it started: change what this run's answers change, add what the seed has and the file lacks, and leave every other line as it stands. Report the other differences from the seed to the user instead of resolving them.

   补上这句以后，合并说明里"先备份"那段警告就可以删掉。

4. **位置**：`SKILL.md` `**Section C: Domain docs.**` 第 59–61 行。**这是上游原文在 MMW 里会让 agent 做错的一处。** 原文只有在找到 monorepo 信号时才提供 multi-context，否则 "write it without asking"；第 36 行的括号更直接写成 "Section C when there's no monorepo"。可是 MMW 的两个真实多 context 仓库，本仓和 `agentflow`，都有 `CONTEXT-MAP.md`，却都没有 `pnpm-workspace.yaml`、`package.json` 或 `packages/`（`ls` 核实过）。在这两个仓库里重跑，照字面会写出 single-context 的 `domain.md`，和仓库的实际布局相反。第 21 行 "don't assume" 能部分兜住，但第 36 行的括号给的例子正好指向相反的方向。只加一句本仓的话，不改上游原文：
   > An existing `CONTEXT-MAP.md` settles this section as multi-context, whether or not the repository is a monorepo; describe the layout it already has.

5. **位置**：`SKILL.md` 第 1 步第 24 行与第 4 步第 74 行。**缺什么**：第 24 行只查 `## External References` 里有没有指向 `docs/agents/` 的行。三个 consuming repository 里，`agentflow`（`AGENTS.md:49`）和 `xiaohuangya`（`AGENTS.md:48`）用的是上游旧格式的 `## Agent skills` 块，`mmw-e2e-lab` 用的是 `## Issue tracker`（第 26 行）和 `## Domain docs`（第 32 行）两节。在这几个仓库重跑，agent 会把旧块当成 "user edits to the surrounding sections" 原样保留，再另加一组行，结果同一份文件被指了两次。这一条的风险是推断的：还没有重跑的记录。
   > A pointer to a `docs/agents/` file in another shape (an `## Agent skills` block, an `## Issue tracker` section) counts as that file's row: replace it with the row rather than adding a second pointer.

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| — | — | 没有。第 1–5 步的编号流程和 "One section, one answer, then the next" 都是上游原文，节奏本身就是这个技能的用法：面对用户逐节确认。它没有替 agent 做判断，在 MMW 里也不会导致做错。本仓加的第 4 步两段是精确的写入约定：行写在哪、不重复、`CLAUDE.md` 的形状，都是为了不和 `manage-agents-md` 冲突，属于真依赖，不是作者的偏好。第 76 行的问题在交接，见下一节 | — |

## 脚本

无。本技能没有 `scripts/`。和它相关的脚本逻辑见 A2：label 的颜色与说明分别写在 `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py:62–65`（`CLASS_LABELS`，四个 layer label）和 `mmw-v2/skills/dispatch/scripts/dispatch.sh:4287–4297`（`ensure_label`，只有 `mmw:ticket`）。两个 `ensure_label` 的逻辑相同（建 label，遇到 "already exists" 就算成功），一个是 Python，一个是 bash。`dispatch.sh` 那份是 `CLASS_LABELS` 中一项的手抄。建议 `dispatch.sh` 调同一个 label 脚本，这样颜色和说明只留一份。

## 与其他技能的重复或交接问题

1. **`SKILL.md` 第 76 行与 `manage-agents-md`。** "when it exists carrying content of its own, move that content into `AGENTS.md`" 让本技能去做 `manage-agents-md` 的迁移，但本技能不知道目标格式。`manage-agents-md/SKILL.md` `### Root template` 规定根文件只能有固定几节，并且 "A root file carries only the sections above"。setup 的 agent 照这句把内容直接搬过去，结果就是一个不合格式的 `AGENTS.md`。这正是合并说明想避免的"两个技能互相拆台"。建议改成：保证 `CLAUDE.md` 第一行是 `@AGENTS.md`，原有内容不动，然后告诉用户由 `manage-agents-md` 来迁移。草稿：
   > When `CLAUDE.md` carries content of its own, add the line `@AGENTS.md` at its top, leave the rest, and tell the user that the `manage-agents-md` skill moves that content into `AGENTS.md`'s format.

   三个现有 consuming repository 的 `CLAUDE.md` 都已经合格（两个只有 `@AGENTS.md`，`mmw-e2e-lab` 没有这个文件），所以这是新仓库才会走到的路径，没有发生记录。
2. **`triage-labels.md` 的 Meaning 列和 `triage/SKILL.md` `## Roles`（第 26–37 行）。** 同一组含义有两份。`triage` 执行时读的是自己 `## Roles` 里的那份，其中已经写着 MMW 的 `ready-for-human` 含义（"one thing only a person can do, of kind `reaction` or `reach`"）。所以落地件的 Meaning 列即使被重跑还原成种子，`triage` 的行为也不会变。合并说明开头"重跑这个技能之前先备份"那段把这一列列为需要备份的理由，分量被高估了。留 `triage` 那一份；落地件那一列不必再作为保护对象。
3. **`docs/contexts/tickets/CONTEXT.md:214`（`**triage role**`）** 写的是 `triage-labels.md` 映射 "five state roles and two category roles"，但种子和落地件都只映射五个 state role。以文件为准，改 CONTEXT 那一条（`_Home_` 规则）。
4. **`ask-matt/SKILL.md:93`** 说 "Custom issue trackers also work."。在 MMW 里这只对手工使用成立，流水线跑不起来（理由同缺口 2）。那是 `ask-matt` 的上游原文，只记录；如果加缺口 2 的那句，setup 执行时会把实话讲给用户，`ask-matt` 这句可以不动。
5. **合并说明 `mmw-v2/merge-notes/setup-matt-pocock-skills.md` `### domain.md（种子）`。** 第 2–4 行写"弃上游"的那几段，改动实际落在落地件 `docs/agents/domain.md`，种子里并没有（`git diff` 种子与上游，只有 host 中立的两处改动）。拉上游的人会以为种子里有本仓内容要保。建议把这三行移到一个标明"落地件"的小节下，种子这一节只留 host 中立那一行。
6. **`issue-tracker-gitlab.md:41` 与 `issue-tracker-local.md:25`** 还写着 "the Notes / Decisions-so-far / Fog body"，和上游自己的 `wayfinder` 模板（`## Not yet specified`）不一致。这是上游内部的偏差，流水线也不走这两个 tracker，不提。

## 没查到的

- 没有 setup 在 consuming repository 里被重跑的记录：查了 `git log -- docs/agents` 和 Nowledge Mem。所以缺口 3、5 和交接问题第 1 条的风险都是推断，前提是"正常重跑能走到"，而不是"已经发生过"。
- A2 中"缺 label 时 `gh issue create --label` 直接失败"是按 `gh` 的已知行为推断，没有在仓库里复现；`~/.mmw/logs` 与 `~/.mmw/state` 里没搜到 `not found` 的 label 报错，说明到目前还没有哪一夜因此失败过。
- `xiaohuangya` 的 queue label 是谁建的，只从建立日期与 `docs/agents/` 提交同一天推断为手工建，没有找到直接记录。
- 没有读 `docs/adr/0005-docs-layer-adopted-by-v2.md` 的全文，只看了 grep 命中的那一行。
- `SKILL-SET-REVIEW.md` 和本任务书之间，就这个技能而言没有发现冲突：B 里保留的几段都属于它 `### Redundancy and bloat` 里 "a reason the agent needs to decide an edge case" 那一类。
