# retro

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：retro 的认识论写得很好，调查员的保留清单全部成立："靠记忆和汇报发现线索，靠原始记录定案""缺一个来源只是缩小分析，不等于问题没发生""相似只是线索，不是同因"。缺的是 retro 这件事本身的"为什么"：
- 谁读它的产出：用户、triage、下一次 retro。
- 原因要落在环境上，不落在 agent 身上。这是上游 retro 的核心，本仓只剩一个名词。
- 为什么两次才算模式。
- 为什么不同的教训去不同的地方。这条的理由在 `70c9a93f` 被删了。

另外，agent 在替脚本抄值；有一个真实缺陷（跨仓库 proposal 落地后查不到）；第 1 步要求把 912 KB 的输出"全部读完"。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | 引言 "The script writes outputs; the agent judges causes and dispositions." 之前 | Three readers act on this record: the user, who reads `NIGHT RETRO` before accepting the night; whoever triages each proposal, which becomes a `needs-triage` issue in its `repository` read by someone who did not watch the night, so its title and body stand on their own; and the next retro, which searches these problems for repeats. A problem the evidence does not carry costs twice: a triage decision now, and a false match later that makes one incident look like a pattern. | 写 proposal 时，没有它会写成只有当晚上下文才看得懂的笔记；有了它，会写成能独立读懂的 issue。后一句让 agent 不把一个弱来源撑成 problem。已核对 `retro.py` 第 606 行确实以 `needs-triage` 开 issue。 |
| I2 | 紧接 I1 | Look for what in the environment let the mistake through: a check that did not exist, an instruction that arrived too late, a fact the agent could not reach. A cause addressed to "the agent" changes nothing on the next run. A night whose evidence supports no problem is a valid retro; record `none` rather than stretching a weak source into a finding. | 把原因写成"worker 没仔细看"时：这种 Prevention 改变不了下一夜任何事，有了这句 agent 会去找环境里的缺口。后一句让"没问题"成为正当结果，#415 那次 0 个 problem 就是如实记录。这是上游 retro 的 "You are suggesting improvements to the coding agent's **environment**" 在本仓的落点。 |
| I3 | `## Decide` 第 11 步开头 | Every prevention has a standing cost: a check runs on every commit, and an `AGENTS.md` line or skill sentence is read by every later agent. One occurrence is dealt with in `Handled here`; a pattern, shown by two independent occurrences or by a blocker a worker already flagged for this retro, is worth that cost. | 没有理由时，agent 会把门槛当成要凑够的数，去找弱关联的历史记录。有了它，一次性问题安心只写 `Handled here`。依据：设计文档 `docs/notes/stage-two-shared-experience-layer.md` `### 20. 设计边界`。 |
| I4 | `## Prevention destinations` 末段，替换 "Choose the destination whose reader acts on the lesson. A coding standard a reviewer can check goes in a reviewer Rule rather than in text every worker reads."（恢复 `70c9a93f` 删掉的依据，并吸收上游后来加的"先看已有 check"） | Choose the destination whose reader acts on the lesson. Workers carry the heaviest context: they explore, implement and debug; the reviewer receives a diff and has room to spare. So a standard only judgement can apply goes to the reviewer's Rules; a violation with a fixed shape (a banned call, an import form, a file location) goes to a `check`, which no one has to remember; and `AGENTS.md` keeps only short pointers nearly every task needs. Before proposing a check, look at the repository's existing check commands: one that exists but is not wired in, or is silently broken, is the finding. | 表格给了去处，这段给选择的理由。遇到表格没覆盖的情况，agent 靠它判断。最后一句来自上游 changeset `retro-deterministic-checks.md`，本仓版本缺这一条。 |
| I5 | `## Analyze` 第 7 步末尾 | This is how the reviewer improves: two `invalid` findings of one category point to a reviewer Rule to change, and two valid findings of one kind point to a check. A finding another ticket fixed was right, and does not count against the reviewer. | 没有用途说明，`review_learning` 只会写成 "none" 或流水账。依据：设计文档 `#### intent reconciliation 与 review learning`。 |
| I6 | `## Analyze` 第 6 步末尾 | It catches a night that met every criterion yet delivered something other than what the spec asked for. | 让 agent 知道这一步要抓什么，而不是走个形式写 "aligned"。 |
| I7 | `## Gather` 第 1 步，把 "read all of it before analysis" 改为右栏（配合 D9） | Find where the night went off course in `tickets[].events` and `spec_events` (returns, queued workers, fault children, handoffs, reviewer findings), then open the comment bodies behind those events. | 实测 spec #555 的 `gather` 输出 912 KB，其中判据运行输出占 526 KB。"全部读完"做不到，只能照做而浪费上下文，或不照做却以为自己照做了。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 第 2 步 "Carry its `evidence_checked`, `task_root` and `observed.base_commit` into the analyzed JSON unchanged, copied by program…"；模板里这三个字段 | `finalize` 从自己新跑的 `gather` 取这三项并写入；"分析基于旧数据"的检测保留，改为比较第 1 步存下的输出与新跑的结果，并跳过 `spec.retroed` 回执。第 2 步只留 "A missing source narrows the analysis…" | 脚本手里早有正确的值，却要 agent 抄一遍再逐字比对；第一次写 Memory 失败后，自己贴的回执会让清单"过期"。 |
| D2 | 第 13 步 "`observed.at` is the actual retro time"；模板 `"spec": 0` | 删；`finalize` 用自己的时间戳和参数里的编号 | 脚本已生成这两项。 |
| D3 | 第 5 步 "and write the problem's `cause` exactly as you passed it, because `finalize` repeats that search" | 删；脚本改为 `memory_show(memory_id)` 核实：在本仓库 Space、带 `mmw-retro` label、正文包含那条原始证据 URL | 重跑语义搜索证明不了同因，结果还会随新增记录变化；这个格式约束也限制了 agent 修正措辞。 |
| D4 | 第 10 步 "Reopen the primary source behind every subagent report…" | 删 | 引言与第 5 步已说；`finalize` 会重新打开每条证据。 |
| D5 | 第 11 步末句与 `## Prevention destinations` 首句中"proposal 要等用户批准"的两处重复 | 删，引言那句保留 | 全文三处同义。 |
| D6 | 第 13 步 "Keep every source reference and missing-evidence statement in it." | 删 | D1 之后清单由脚本写入；缺证据的 problem 脚本会拒绝。 |
| D8 | 第 12 步 `changes_made` 的四个必答项与 `validate_prompt()` 的对应校验 | 改为一句自由文字 "which of missing context, ambiguity, success criteria or late information the change addresses"，脚本只要求非空 | 9 次真实 retro 的 7 个 proposal 里没有一个带 `prompt_change`；一处改动通常只落在一类，另外三类要写"没变"，是填表。 |
| D9 | 脚本 S6：`gather` 原样带上每条 comment 正文 | 每个 event 带上 comment URL；正文只保留说明原因的几类事件（`reviewer.reported`、`ticket.returned`、`child.opened`），其余按 URL 按需打开 | 配合 I7。输出预计降到约五分之一（推断）。 |
| D10 | 脚本 S10（缺陷）：跨仓库 proposal 的落地提交在别的仓库，本地看不到 | 另外接受 `https://github.com/<proposal 的 repository>/commit/<sha>`，用 `gh api` 核实；第 3 步证明形式的列表加一项 | 实例：MMW 提交 `42b3e278` 已修好 #441，agentflow 的 retro 仍记"没找到证据"。 |
| D11 | 脚本 S1、S2、S3、S7、S8、S9 | S1 删 `valid_closing()` 里与 `summary` 重复的校验（"字段不存在记为 unreadable"保留）；S2 只确认 Space 存在，修复交给 dispatch；S3 删不遵守 `--limit` 的防护；S7 缓存证据读取；S8、S9 简化 | 调查员逐条给了位置与四问；S2 的拒绝会连带挡住 `finish`。 |
| D12 | 脚本 S4：spec 父 issue 没有 `mmw:map` label 时整次 retro 被拒绝 | 改为记 `{"kind": "parent", "number": n}` 并在 `evidence_checked` 里说明，不拒绝 | `task_root` 只写进 Memory 的一行说明，不参与判断；一个标签不对就挡住 retro 和 `finish`，代价与问题不相称。 |

### 不采纳

- 原 D7（`gather` 比较 `HEAD` 与 `origin/<into>`，不一致时 `finalize` 拒绝）：检出不在 base branch 上导致 retro 出错，只是我从 `night.md` 推出来的可能，没有一次实际发生的记录。`## Resolve <retro> once` 里那句要求保留原样，不加脚本检查。
- C3（把第 3–12 步改成不编号的小节）：顺序真正依赖的部分已由三个命令承载；编号本身不妨碍判断，改结构的收益不抵风险。
- 脚本 S5（`observed_check` 对 `--output` 等参数的拦截）：删掉后 `git diff --output=<path>` 能在检出里写文件，这几行也很便宜。

## 结论

`mmw-v2/skills/retro/SKILL.md` 正文 1,561 词、192 行，唯一的脚本 `mmw-v2/skills/retro/scripts/retro.py` 794 行；没有 reference 和模板。这个技能不臃肿：正文大部分是 `finalize` 会拿来裁决的规则（证据形式、同因判定、proposal 门槛），按 `SKILL-SET-REVIEW.md` `### Scripts and judgement` 这类文字应当留在正文。主要问题有三处：(1) 让 agent 手工搬运脚本自己就有的值（`evidence_checked`、`task_root`、`observed`、`spec`），再用一次重复的 `search` 去核对 agent 搬得对不对，正文因此多出几条只为迁就脚本的约束；(2) 在 2026-09-23 的第 70c9a93f 次提交里，"worker 的上下文最紧，reviewer 只看 diff"这段判断依据被删掉了，正文只剩结论，没留理由；(3) 正文从来没告诉 agent 自己的产出由谁读、proposal 会变成什么、为什么要两次独立发生才提案。正文可删约 230 词，建议补回约 260 词，净词数基本不变；脚本可删约 70 行，另需新增约 15 行，用来修一个真实缺陷：跨仓库的 proposal 已经落地，下一次 retro 却无法证明（证据见 `## 与其他技能的重复或交接问题` 第 1 条）。"灵魂"部分：证据观（先发现、后核实）完整；"为什么这样做、为谁做"这一层缺失。

改动时要注意测试断言：见文末 `## 改动时要注意的测试断言`。过去那条把技能正文和设计文档逐字比对的断言，已在第 4e4ee6a5 次提交删除；现在还剩一条针对 frontmatter 的前缀断言，另有十来条断言检查拒绝信息中的原话。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `SKILL.md` `## Gather` 第 2 步 "Carry its `evidence_checked`, `task_root` and `observed.base_commit` into the analyzed JSON unchanged, copied by program…"；`## Finalize` 第 13 步 JSON 模板里的 `task_root`、`evidence_checked`、`observed.base_commit` 三个字段 | 1 | `retro.py` `check_analysis()` 第 426–433 行只把这三项和一次新的 `gather` 做相等比较，不相等就抛 `GatherChanged`；随后 `render()` 用的也是 agent 抄来的这份。也就是说，脚本手里早有正确的值，却要 agent 抄一遍、再逐字比对。副作用有测试为证：`mmw-v2/tests/retro/test_retro.py` `retry_finalize` 里，第一次 `finalize` 写 Memory 失败后，它自己贴出的 `unrecorded` 回执算作一条新的 spec comment，于是第一次的清单"过期"了，agent 只能重跑 `gather` 再抄一遍 | 由 `finalize` 负责：从它自己新跑的 `gather` 取这三项并写入。现有的"分析基于旧数据"检测（`GatherChanged`）要保留：改为比较第 1 步已存下的 `gather` 输出和新跑的结果，并跳过 `spec.retroed` 回执。剩余风险：无 | `finalize <spec> <analysis> <saved-gather>`，或让分析文件里记一个 `gather_file` 路径；正文删掉第 2 步第二句和模板里这三个字段，第 2 步只留 "A missing source narrows the analysis…" 那句 |
| A2 | `## Finalize` 第 13 步 "`observed.at` is the actual retro time"；模板里的 `"spec": 0` | 1 | `gather()` 第 329 行已经生成 `observed.at`；`finalize` 已经从参数拿到 spec 编号，第 424 行只检查两者是否一致 | `finalize` 用自己的时间戳和参数里的编号。剩余风险：无 | 删掉这句和两个字段；`check_analysis` 不再要求 `observed`、`spec` 两个字段 |
| A3 | `## Analyze` 第 5 步 "and write the problem's `cause` exactly as you passed it, because `finalize` repeats that search" | 1、5 | `check_analysis()` 第 499–502 行对每一个 earlier occurrence 都重跑一次 `search(category, cause)`，只为确认 agent 给的 Memory id 在搜索结果里。语义搜索的结果会随 Space 里新增的 Memory 变化；而且它证明不了"同因"，同因本来就是 agent 的判断。真实使用中，这条路径在 #445、#446、#555 三次 retro 里共走过 5 次（从各自 Retro Memory 的 `Earlier occurrences` 统计） | 改为 `memory_show(memory_id)`：确认它在本仓库 Space、带 `mmw-retro` label、正文包含那条原始证据 URL。这三项才是能机械核实的部分。剩余风险：agent 可以引用一条不是搜出来的 Retro Memory，但只要它确实引用了同一原始证据，这正是需要的 | 删掉这半句；脚本按上面改。`search` 子命令保留，它是 agent 发现历史的入口 |
| A4 | `## Decide` 第 10 步 "Reopen the primary source behind every subagent report, Memory match…" | 6 | 同一个意思已写在引言 "A problem exists only when… Use Memory, Thread, Working Memory, agent reports, and issue status to discover what to verify; use primary…to establish…"（第 18–22 行）和第 5 步 "reopen both"；此外 `finalize` 的 `evidence_source()` 会重新打开每一条证据 | 引言那段（agent 在一开始就读到）加上 `finalize` 的重开。剩余风险：无 | 删掉第 10 步 |
| A5 | `## Decide` 第 11 步末句 "Leave the proposed behaviour change for work the user approves, through the normal spec and ticket flow."；`## Prevention destinations` 首句 "A proposal asks for approval and changes none of these destinations." | 6 | 与引言 "Work the user approves applies the improvements later, through the normal spec and ticket flow."（第 15–16 行）同义，全文共三处 | 保留引言那句，并在其后接 B 节第 1 条草稿（proposal 变成 `needs-triage` issue）。剩余风险：无 | 删掉另外两处；`## Prevention destinations` 首段只留 "A problem's Prevention names one of them by its `destination` value" |
| A6 | `## Finalize` 第 13 步 "Keep every source reference and missing-evidence statement in it." | 2 | 做完 A1 后，清单由脚本写入；每个 problem 的 `evidence` 缺失时，`check_analysis` 第 481–483 行会拒绝 | 脚本。剩余风险：无 | 删掉 |
| A7 | `## Resolve <retro> once` "Run it from a checkout of the spec's repository whose `HEAD` is `origin/<base branch>`…" | 1（可选） | 脚本不检查这一点；而 `finalize` 会从工作区读取文件证据（`evidence_source()` 第 382–389 行）、`prompt_change` 的目标（第 533–539 行）和"已落地"用的文件证明（第 464 行）。`night.md` `## 5. The night is over` 让 main agent "From any checkout in this repository" 跑 `summary`，所以 retro 所在的检出很可能不在 base branch 上 | `gather` 比较 `git rev-parse HEAD` 与 `origin/<into>`：一旦不一致，`finalize` 在遇到文件证据时拒绝，并说明原因。剩余风险：无 | 脚本加上这项检查后，正文这句可缩成半句，或删掉；不加检查就保留原句 |

## B. 灵魂

### 保留，勿删

- `## Resolve <retro> once` "resolve it from this file's own location, since the path differs by machine and by host"：`SKILL-SET-REVIEW.md` `### Redundancy and bloat` 点名保留这一类句子，它能防止 agent 把解析出的路径写死。
- 引言 "Run an evidence-first retrospective… improvements to the coding agents' environment and workflow"：它规定了 retro 的对象是环境，不是追究某个 agent；同时说明改进要等用户批准后再做。
- 引言 "A problem exists only when… Use Memory, Thread, Working Memory, agent reports, and issue status to discover what to verify; use primary tracker, git, repository, and check evidence to establish what happened"：这是整个技能的认识论，即靠记忆和汇报去发现线索，靠原始记录去定案。删掉它，retro 就会把 agent 的自我评价当成事实。
- "The script writes outputs; the agent judges causes and dispositions."：一句话划清分工，让 agent 不去手写 Memory 或回执。
- `## Gather` "A missing source narrows the analysis; it never means that the corresponding problem did not happen."：它区分"查过是干净的"和"没查"。#415、#424 两次真实 retro 都是 `Evidence: partial`，这句话在那两次真的起了作用。
- `## Analyze` 第 3 步 "record `no-evidence-found`, not "not done". Issue closure alone is not landing evidence."：它要求 agent 如实写"没找到"，不能写成"没做"。
- `## Analyze` 第 4 步 "Merge duplicate representations of the same underlying event… Treat a shared path, similar title, or category as a search lead rather than proof of the same cause."：这是 agent 最容易判断错的一点，即把相似当成同因。
- `## Analyze` 第 5 步 "Count an earlier occurrence only when its original source opens, shows the same cause, and belongs to a different ticket, spec, or night… Two event comments on one ticket or spec are one occurrence, not two."：定义了什么算"重复"，门槛的意义全靠它。
- `## Analyze` 第 6 步 "Record aligned, diverged, or unverified; do not change the spec."：retro 只描述差距，不越权去改 spec。
- `## Analyze` 第 8 步七类问题及每类的 "Use when"：来自上游 `mmw-v2/upstream/skills/in-progress/retro/SKILL.md` 的主线，逼 agent 逐类看一遍，而不是只报最显眼的那个问题。
- `## Decide` 第 9 步 "two independent dispositions"（Handled here / Prevention）：它把"这次怎么处理"和"下次怎么避免"分开。真实记录里两者经常不同，例如 #555 那次是当场修复，同时提议加一个 check。
- `## Decide` 第 12 步 "Keep every unchanged sentence unchanged and submit both complete passages…" 和 "Read the `writing-for-agents` skill's `SKILL.md` before writing the proposed passage."：前者防止 agent 用改写过的段落偷换原文，后者在 agent 动手写的那一刻给出写作标准。
- `## Prevention destinations` 表格及末段 "Choose the destination whose reader acts on the lesson. A coding standard a reviewer can check goes in a reviewer Rule rather than in text every worker reads."：这是选择去处时唯一的判断原则。

### 缺口与补充草稿

- 引言之后：agent 不知道自己的产出由谁读、proposal 会变成什么。正文从没提 `finalize` 会在 `repository` 里开一个 `needs-triage` issue，也没提 `NIGHT RETRO` 是用户第二天早上决定是否接受这一夜的依据之一。后果是 proposal 的 title 和 body 写成只有当晚上下文才看得懂的笔记（第 11 步只说 "`title`, `body`"）。另外，一个站不住的 problem 会被下一次 retro 当作 earlier occurrence 搜到，把一次偶发放大成"模式"。
  > Three readers act on this record. The user reads `NIGHT RETRO` beside `NIGHT SUMMARY` before accepting the night. Each proposal becomes a `needs-triage` issue in its `repository`, judged by someone who did not watch the night, so its title and body must stand on their own. The next retro reads this Retro Memory to see which proposals landed and searches its problems for repeats. A problem the evidence does not carry therefore costs twice: a triage decision now, and a false match later that makes one incident look like a pattern.

- 引言之后（紧接上一条）：没有写该以什么态度找原因。上游原文 "You are suggesting improvements to the coding agent's **environment**" 在 MMW 里只剩一个名词 "environment"。没有这层意思，agent 容易把原因写成"worker 没仔细看"，这种 Prevention 改变不了下一夜任何事。也没有说"没问题"是正当结果：#415 那次 0 个 problem 就是如实记录。
  > Look for what in the environment let the mistake through: a check that did not exist, an instruction that arrived too late, a fact the agent could not reach. A cause addressed to "the agent" changes nothing on the next run. A night whose evidence supports no problem is a valid retro; record `none` rather than stretching a weak source into a finding.

- `## Decide` 第 11 步开头：门槛只写了规则，没写理由。agent 会把门槛当成要凑够的数，比如把同一 ticket 的两条 comment 硬算成两次，脚本 `occurrence()` 会拒绝，于是 agent 转而去找弱关联的历史记录；或者它不明白一次性问题为什么只写 `Handled here`。设计文档 `docs/notes/stage-two-shared-experience-layer.md` `### 20. 设计边界` 明确排除了"把一次阶段三问题当作重复问题提案"，理由却没进技能。
  > Every prevention has a standing cost: a check runs on every commit, and an `AGENTS.md` line or skill sentence is read by every later agent. One occurrence is dealt with in `Handled here`. A pattern, shown by two independent occurrences or by a blocker a worker already flagged for this retro, is worth that cost.

- `## Prevention destinations` 末段：恢复第 70c9a93f 次提交删掉的依据，并吸收上游后来加入的"机械规则归 check"。被删的原文是 "Implementation agents use the most context because they explore, implement, and debug. Reviewers receive a diff and use less context. Put stable coding standards in the reviewer's Rules, not in every worker prompt. Use AGENTS.md sparingly, mainly for navigation pointers; use docs as referenced detail; use a skill only for a repeatable multi-step workflow with a discoverable trigger, inputs, outputs, and Done when."。那次提交的理由是 "the destination paragraph keeps only the judgement the table lacks"，但表格给的是去处，这段给的是选择去处的理由；遇到表格没覆盖的情况，agent 要靠这个理由判断。这属于 `SKILL-SET-REVIEW.md` 列为 "These stay" 的 "a reason the agent needs to decide an edge case"。上游 `mmw-v2/upstream/.changeset/retro-deterministic-checks.md` 加的"先分机械和判断"和"先看已有 check"，MMW 版本也没有。
  > Workers carry the heaviest context: they explore, implement and debug. The reviewer receives a diff and has room to spare. So a standard only judgement can apply goes to the reviewer's Rules; a violation with a fixed shape (a banned call, an import form, a file location) goes to a `check`, which no one has to remember; and `AGENTS.md` keeps only short pointers nearly every task needs. Before proposing a check, look at the repository's existing check commands: one that exists but is not wired in, or is silently broken, is the finding.

- `## Analyze` 第 7 步：没说 `review_learning` 用来做什么。agent 分不清为什么要区分 invalid 和 fixed-elsewhere，写出来的就只有"none"或流水账。设计文档 `#### intent reconciliation 与 review learning` 给过用途，技能没接住。
  > This is how the reviewer improves: two `invalid` findings of one category point to a reviewer Rule to change, and two valid findings of one kind point to a check. A finding another ticket fixed was right, and does not count against the reviewer.

- `## Analyze` 第 6 步（一句即可）：没说 intent reconciliation 要抓的是什么。
  > It catches a night that met every criterion yet delivered something other than what the spec asked for.

- `## Gather` 第 1 步：见 C1。改写后要给 agent 一个读法，替代 "read all of it"。
  > On a large night the output runs to hundreds of kilobytes, most of it criterion output. Find where the night went off course in `tickets[].events` and `spec_events` (returns, queued workers, fault children, handoffs, reviewer findings), then open the comment bodies behind those events.

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `## Gather` 第 1 步 "read all of it before analysis" | 实测：在本仓库对已完成的 spec #555 只读运行 `retro.py gather 555`，输出 912,066 字节；其中 `tickets[].comments` 占 817 KB，而 `ticket.checked` 回执正文（判据运行输出）就占 526 KB。按字面读完会耗掉大半上下文，所以 agent 要么照做而浪费上下文，要么不照做却默认自己照做了。这句只能照做，没有给判断留余地 | 换成 B 节最后一条草稿；脚本侧见 `## 脚本` S6 |
| C2 | `## Decide` 第 12 步 `changes_made` 的四个必答项 "`context_or_constraints`… `ambiguity`… `success_criteria_or_requirement`… `timing`, each explaining whether that class changed or explicitly saying it did not"；`retro.py` `validate_prompt()` 第 527–532 行 | 一处改动通常只落在一类，另外三类必须写"没变"，这是填表，不是思考。真实使用：9 次 retro（本仓库 7 次、agentflow 2 次）共产生 7 个 proposal（#441、#443、#478、#490、#506、#507、#587），没有一个带 `prompt_change`（逐个查了 issue 正文里有没有 `Prompt target`）。这条路径从未被走到，模板却是最细的一处 | 保留 `target_file`、`heading`、`source`、两段完整原文和 `expected_behavior`（这些是审批人需要的）。`changes_made` 改成一句自由文字："which of missing context, ambiguity, success criteria or late information the change addresses"；脚本只要求非空。约省 60 词、6 行 |
| C3 | `## Analyze`、`## Decide` 的编号 3–12 | 真正有先后依赖的只有两处：先有 problem 才能 `search`，先确定 earlier occurrences 才能判断门槛。其余几项（上次 proposal 的跟进、intent、review learning、七类问题）彼此独立，编号却暗示必须按这个顺序做 | 顺序依赖由 `## Gather` → `search` → `## Finalize` 三个命令承载，必须保留。`## Analyze`、`## Decide` 内部改成不编号的小节（例如 "What counts as a problem"、"Is it a repeat"、"Where the lesson goes"、"When it becomes a proposal"），每节写目标、判定标准，并配上 B 节对应的理由。词数基本不变 |
| C4 | `## Analyze` 第 5 步 "write the problem's `cause` exactly as you passed it" | 这是为迁就脚本的重复搜索而加的格式约束，限制了 agent 在分析过程中修正措辞 | 随 A3 删除 |

## 脚本

`mmw-v2/skills/retro/scripts/retro.py`：

- S1 重复校验，`valid_closing()` 第 174–198 行：把 `spec.closed.payload.memory_closing` 的完整结构重新校验了一遍（total/returned 相等、ids 不重复、`supersede` 必须带 `replacement_id`）。`summary` 在写 `spec.closed` 之前已经做过全部这些检查，见 `mmw-v2/skills/dispatch/scripts/dispatch.sh` 第 3783–3868 行的内嵌 Python。retro 只需要取出 `decision=propose` 的 id。"字段不存在或不是对象时记为 unreadable"这条要保留：#415、#424 两次真实 retro 走的正是这条路径（这两个 spec 早于 `memory_closing` 字段出现）。可删约 18 行。
- S2 重复且会造成阻塞，`space()` 第 112–115 行：先读回 Space，要求 `defaultRetrievalMode == "shared"`、`sharedSpaceIds == ["mmw-toolbox"]`，否则 `gather`、`search`、`finalize` 全部拒绝。这组条件与 `dispatch.sh` 第 498–503 行的 `exact()` 相同，而 dispatch 在开夜时会建好并修复这个 Space。共享设置对 retro 自己的读写没有影响；拒绝的后果是 retro 写不成，进而 `finish` 被挡（`dispatch.sh` 第 4040–4052 行）。建议只确认 Space 存在，修复交给 dispatch。可删约 3 行。
- S3 过度防御，`memory_list()` 第 156–157 行 "latest list ignored its requested limit"：防的是 nmem 不遵守 `--limit`。四问：没有触发记录；正常输入走不到这里；前提是推理出来的；删掉后用 `rows[:limit]` 就能兜住。可删 2 行，连同第 154–155 行那条注释。
- S4 过度防御，后果还比问题本身重，`gather()` 第 239–246 行：spec 的父 issue 没有 `mmw:map` label 时整次 retro 被拒绝。`task_root` 只在 `render()` 里写成 Memory 的一行 "Task root:"，不参与任何判断；因为一个标签不对就挡住 retro，进而挡住 `finish`，代价与问题不相称。有没有触发过：没查到记录（推断）。建议记为 `{"kind": "parent", "number": n}`，并在 `evidence_checked` 里加一条说明，不再拒绝。
- S5 过度防御、收益很小，`observed_check()` 第 359–362 行：已经限定只能用 `rg`，以及 git 的七个只读子命令；在这之上又拦截 `--output`、`--ext-diff`、`--textconv`。这里防的是写分析 JSON 的那个 agent 自己，而它本来就有 shell。四问前两问都是"否"，所以算过度防御。但删掉后 `git diff --output=<path>` 能在检出里写文件，剩余风险真实存在，而这几行本身也便宜。结论：可以不动。
- S6 输出形状，`gather()` 第 271–274 行：`tickets[].comments` 原样带上每条带 mmw 标记的 comment 正文，在 #555 上占 817 KB。而 `events` 里只有 comment id，没有 URL，agent 引用证据时仍得回头去 `comments` 里找 URL。建议给每个 event 带上它的 comment URL；正文只保留 `reviewer.reported`、`ticket.returned`、`child.opened` 这几类说明原因的事件，其余按 URL 按需打开（`finalize` 本来就会重新打开）。这样功能不丢，输出大约降到原来的五分之一（推断：按这几类事件所占字节估算）。
- S7 重复读取：`check_analysis()` 第 493–498 行对每条证据调用一次 `evidence_source()`（`gh api` 或 `git show`，或重跑 check），`qualifies()` 第 546 行对同一批 URL 又全部再开一遍；第 499 行还在循环里对每个 earlier occurrence 重跑一次相同的 `search()`。缓存一次结果即可；A3 做完后第 499 行整个去掉。
- S8 没有实际作用的结构，第 513–515 行 `for key in ("prompt_change",): if key in proposal:`：只循环一个元素，直接写 `if "prompt_change" in proposal:` 即可。
- S9 重复逻辑，`gather()` 第 222–225 行与第 263–267 行：spec 和 ticket 各写了一遍"遍历 comment，是 event 就加入清单"。可以合成一个函数，约省 4 行。
- S10 缺陷（不是减重项，是要补的功能），`check_analysis()` 第 453–465 行对"已落地"的证明：只接受本地 `git cat-file -e <sha>`、本地文件、active Rule 或 Memory。跨仓库 proposal 的落地提交在另一个仓库里，本地检出看不到。详见下一节第 1 条。建议另外接受 `https://github.com/<proposal 的 repository>/commit/<sha>`，用 `gh api repos/<o>/<n>/commits/<sha>` 核实。约增 8 行，正文第 3 步证明形式的列表里加一项。

合计：可删约 70 行（S1 18、S2 3、S3 4、S4 净 0、S6 约 10、S7 5、S8 1、S9 4、A1/A2/A3/C2 对应的校验约 25），新增约 15 行（S10、A1 的比较、A7 的检查）。

## 与其他技能的重复或交接问题

1. 跨仓库 proposal 的落地无法证明（真实发生过）。agentflow 的 retro `mmw-retro-agentflow-hq__agentflow-spec-914` 提了 proposal #441，由 MMW 负责修改。MMW 在 2026-09-16 用提交 42b3e278 "fix(#441): enforce complete night closeout" 完成了修改。两天后（2026-09-18）的 `mmw-retro-agentflow-hq__agentflow-spec-913` 仍把它记成 "https://github.com/chancheuklap/multi-model-workflow/issues/441 — 没找到证据"。按规则，agent 这样写没错：`finalize` 在 agentflow 检出里找不到 MMW 的提交。消费仓库的 retro 提出的 proposal 大多指向 MMW（本次见到的 #441、#443 都是），所以设计文档 `### 19. 效果指标` 里的"retro proposal 的实际落地率"在消费仓库上会一直偏低。修法见 `## 脚本` S10。这是工程层面的修复，不需要用户拍板。
2. `mmw-v2/skills/dispatch/references/night.md` `## 4. The closing pass` 第 176–181 行对 `propose` 的 `evidence` 做了规定（"the retro counts the proposal only when that string is one of its problem's sources"），与 retro 第 11 步的门槛内容重叠。两边都应保留：night.md 那句写给写 decisions 的 main agent，在它写的那一刻用得上；retro 那句写给判断门槛的 agent。
3. 上游 `mmw-v2/upstream/skills/in-progress/retro/SKILL.md` 是另一个技能（`mmw-v2/merge-notes/README.md` 第 38 行："不合进来"），但 MMW 版本的七类问题出自它。上游后来在 `Automated checks`、`Coding standards` 两类里加了"先看已有 check"和"机械违规交给 check"（`mmw-v2/upstream/.changeset/retro-deterministic-checks.md`），MMW 版本没有跟进。B 节第 4 条草稿吸收了这层意思，不需要去改上游。
4. `docs/notes/stage-two-shared-experience-layer.md` `#### retro/SKILL.md 的执行正文` 已声明以技能文件为准，没有复制正文，不存在重复。它的 `### 13` 与 `### 20` 里有技能缺失的理由（B 节第 3、5 条），应当把理由搬进技能，设计文档原样保留。

## 改动时要注意的测试断言

- `mmw-v2/tests/retro/test_retro.py` `complete_none` 第 207–208 行：`SKILL.md` 必须以 `---\nname: retro\ndescription: Retrospect one completed MMW spec night` 开头。改 frontmatter 或 description 的开头会让这条断言失败。本报告不建议改动它们。
- 以下断言检查拒绝信息中的原话，A1、A2、C2 的脚本改动会碰到它们：`retry_finalize` 第 462 行 `"evidence_checked must carry"`、`"gather 70 again"`（A1 改完后这一场景的期望要重写：`unrecorded` 回执不应再迫使 agent 重新 `gather`）；`prompt_and_record_contract` 第 401 行 `"prompt_change needs all fo"`（C2）、第 411 行 `"observed must contain"`（A2）；`proposal_threshold` 第 293、301 行 `"proposal has no two indep"`（不受影响）；`partial_evidence` 第 262 行与 `prompt_and_record_contract` 第 411 行的 `"because"`、`"finalize 70"`（`refusal_for()` 三段式结构，不受影响）。
- `test_retro.py` 的 `Fixture.analysis()` 第 149–161 行构造的分析文件里带有 `spec`、`task_root`、`evidence_checked`、`observed`。A1、A2 落地后要同步修改。
- `mmw-v2/tests/dispatch/test_dispatch.sh` `scenario_summary_retro` 第 3707–3716 行断言的是 `night.md` 里的原话（"invoke the `retro` skill in this same main-agent session"、"`finish` needs its `recorded` receipt"），不涉及 retro 的正文。
- 2026-09-23 的第 4e4ee6a5 次提交删掉了那条把技能正文与设计文档逐字比对的断言。目前没有测试逐字比对 retro 正文的其他部分。

## 没查到的

- S4（父 issue 不是 map 时拒绝）、S3（nmem 不遵守 limit）以及 `GatherChanged` 在真实运行中是否触发过：没有 retro 的运行日志，只能从 9 条 `spec.retroed` 回执（全部是 `recorded`）推断拒绝后被 agent 修正、重跑过的情况没有留下痕迹，所以"是否触发过"无法验证。
- S6 里"大约降到原来的五分之一"是按事件类别所占字节估算的，没有实际改写后测量。
- 没有跑测试套件（任务书要求只读）。对 `gather 555` 的实测是只读运行：`gh issue view`、`git`、`nmem memories list/show`，没有写入任何东西。
- agentflow 仓库的两次 retro 只读了它们的 Retro Memory，没有打开 agentflow 的 tracker 逐条核对。
