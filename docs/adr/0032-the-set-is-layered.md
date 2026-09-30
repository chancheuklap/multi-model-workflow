---
date: 2026-09-30
amends: []
---

# MMW 分成 mode、playbook、原则、能力技能、reference、脚本、角色与配置七种组件，按类型各住一层，每段内容默认搬到它该在的层，留在原处必须写明是 H1–H6 或 S 的哪一条

今天的 MMW 只有 skill 一种组件，五类内容写在同一批 skill 里。这份 ADR 记下分层之后各批要遵守的决定，供以后的批次和评审引用。它不推翻 0009–0031：那些 ADR 里的机制继续成立，其中的路径随各批作为仓库文档改。唤醒带步骤指针、从而修订 ADR 0020 的，由 ADR 0033 在 B2 写。pstack 以 subtree 引入的，由 ADR 0034 在 B1 写。

## 七种组件与各批要遵守的决定

mode 的名字是 `mmw`，全套只有这一个。下面是每种组件回答的问题和它的家。这些目录按批出现：B0 不建 `mmw-v2/skills/mmw/`；mode、原则和白天的 playbook 在 B1；`dispatch` 解散、脚本整目录搬进 `mmw/scripts/` 在 B2。

| 组件 | 回答什么问题 | 放在哪里 |
| --- | --- | --- |
| mode | 遇到什么情况用什么；任务走哪份 playbook；无人时能自己定什么；被唤醒后怎么接上 | `mmw-v2/skills/mmw/SKILL.md` |
| playbook | 一类任务从头到尾的步骤、谁拥有什么、交出什么 | `mmw/playbooks/`；一个仓库私有的在该仓库 `.mmw/playbooks/` |
| 原则 | 跨任务、能改变一个具体决定的判断 | `mmw/principles/principle-<slug>.md` |
| 能力技能 | 一件事怎么做、交回什么；不知道是谁调用它 | `mmw-v2/skills/<name>/` 与三个上游 subtree |
| reference | 只在某一步才读的材料，或交给 subagent、另起会话的简报 | 所属 skill 的 `references/`；mode 自己的在 `mmw/references/`，外来的在 `mmw/references/pstack/` |
| 脚本 | 每次结果都一样的状态读写、投递、检查 | 流水线的在 `mmw/scripts/`，外来的在 `mmw/scripts/pstack/`；能力自己的留在能力目录 |
| 角色与配置 | 哪个角色读哪份 playbook、用哪个模型、被什么事件叫醒到哪一步 | `mmw/roles.json` 与 `~/.mmw/models.json` |

**判据。** 每段内容默认搬到按类型该在的层。留在原处必须写明是下面 H1–H6 或 S 中的哪一条。「没有收益」「现在能跑」「改动面大」不作理由。这条判据同时是每张批次票的验收条件：这一批里每一段要么搬走，要么在 closeout 里点名留下它的那一条约束；在这一批或更早转为失败的连线检查、逐字搬运检查和结构 lint 通过；这一批点名的完整套件通过，开跑前写明理由。

**硬约束与边界 S。**

- **H1** 现役 host 是 Claude Code、Codex、Grok，runner 是 Orca（D3）。这些 host 没有 Cursor 的 `mode: true` / `reminder` 常驻机制。
- **H2** Claude Code 上，带 `disable-model-invocation: true` 的 skill 不在模型的 skill 列表里，按名也调不到；description 在 host 启动时扫入，改动要新会话才生效。
- **H3** 会话内派出的 subagent 跑在本会话 host 的模型上；跨厂商只能另起会话（ADR 0015 `## Consequences`）。
- **H4** runner 把送进会话的文字当键盘输入，换行即提交，所以脚本送进会话的一条消息必须是一行。
- **H5** Self-hosting boundary（根 `AGENTS.md` `## Self-hosting boundary`）：一次 watch 期间冻结已安装版本；运行中的流程不读工作树里正在被改的版本。
- **H6** 夜里的会话屏幕前没人，不能向人提问。
- **S** `mmw-v2/prompt/shared.md` 是用户的全局规则，对所有项目生效，MMW 不改写它。

**优先级。** `shared.md`（用户规则）> mode > 所服务的 playbook（含它对原则的本地限定）> 原则。能力技能自带的人工闸门不在这条链里：人在场时照闸门停；无人会话里 mode 不覆盖它，而是走本角色的无人出路。例如 `to-spec` 的产品闸门在无人会话里变成一条 `decision` 子票。这一句是新写的，依据见下面「新写的决定」。

**`dispatch` 与 `verify-ticket`。** B2 执行。`dispatch` 解散：路由进 mode；夜间、单票、接手一张票三份流程成为 playbook；改模型成为能力技能 `setup-mmw`；脚本整目录搬进 `mmw/scripts/`。`verify-ticket` 拆出 `events.py`（事件词表）与 `ticket_state.py`（认领、记录判据运行、决定、评审、`touched`、草稿、closeout、切子票这些写票状态的命令，放在 `mmw/scripts/`）。`verify-ticket` 只留跑一张票的判据、lint 票面、发布 spec 与票。

**技能的位置。** 取代 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `## What skill text is for` 事实 7 的这句："A skill's place follows from its own text: its description says when it starts, and its closing section says what comes next." 同时取代 `### Hand-offs` 第 5 条："Each skill ends by naming what comes next, or the caller it returns to, and the skill it returns to has an entry for an agent arriving that way." 改为：一个 skill 的位置由 mode 路由表与 playbook 决定，能力技能以它交回什么结尾。文字改动在 B1，随该文件搬进 `mmw/references/skill-set-rules.md`。原句防的两件事，第二份副本漂移和某一跳找不到下一步（#538），改由「顺序只有一个家」加上连线检查第 2、7 类来防。

**逐字与改名。** 搬运的句子逐字保留，由逐字搬运检查（`check_verbatim_moves.py`）与结构 lint（`check_component_structure.py`）强制。搬文字的票带 `## Moves`。MMW 自有的名字按 `docs/specs/mmw-layering/renames.tsv` 与 `docs/research/workflow-compare/reports/R19-naming-table.md` 执行。上游 mattpocock 与 pstack 的名字不改（D9）。

**批次。** 分六批，每批由当时已安装的冻结版本跑，每批之后流水线仍能跑。D6、D7 之后，核心批次到 B2。B3–B5 与多模型面板（`dispatch.sh panel`、`panel-wait`、`models.json` 里的面板角色）按需，每次由用户点名组件，走私有 playbook **Import a component**。PR 交付不引入：`delivery: pr`、`opening-a-pr`、`babysit`、`shipping`、`bugbot-triage.md`、`watch-pr/` 与 bun 都不进（D2）。

**新写的决定。** R18 标成「新写」、没有现成来源的工程决定只有优先级这一条，依据是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md` `### C.2 「不拆」的条件：规则留在调用方正文里`：「pstack 没有写明哪一层优先。归置 MMW 时要显式写出优先级。」同节所引 `prototype.md`、`feature.md` 的限定句高于原则，是调用方可以限定原则、因而不必为每个例外改写原则的实例。能力技能的人工闸门在无人会话里走本角色的无人出路，是同一条新写的句子，用来和「能力技能自带的闸门保留」同时成立。

**B0 已落地的两个机制。**

- **watch 的 `kind`。** `watches.json` 里每个 watch 有字段 `kind`，由开它的命令写入：`dispatch.sh open` 写 `night`，`open-ticket` 写 `ticket`，`adopt` 写 `adopted-ticket`。B0 读它的是 `dispatch.sh where`（用来定角色）和 watchdog（`kind` 为 `adopted-ticket` 的 watch，告警不附 `dispatch.sh resume`，改为告诉用户）。没有 `kind` 的 watch，`where` 报 `UNKNOWN`。relay 按 `kind` 取收件角色不在 B0，由 ADR 0033 记。
- **`dispatch.sh where`。** 用当前会话对照票上的 `*.started` 事件和 watch 的 `kind` 定出角色，再从事件算出位置，印一行。四种输出是 `AT`、`BETWEEN`、`FRESH`、`UNKNOWN`；前三种退出 0，`UNKNOWN` 退出 2。角色到 playbook 取自 `roles.json`，事件到步骤的表在 `locations.py`。B0 里它与 `verify-ticket.py --preflight` 印出的 `RESUME:` 并存，没有会话被要求照 `where` 的输出行事；第一个这样要求的是 B1 mode 的 `## Re-entry`。B0 的用途是与 `RESUME:` 并行核对，并给以后的读者（mode、任务板）一个稳定接口。`roles.json` 在 B0 的读者只有 `where` 与 `check_wiring.py`；relay、watchdog、turn guard 和 start prompt 到 B2 才读它。B2 删掉 `resume_at`，`where` 成为唯一，同一批把 `--preflight` 改名为 `--claim`。

## 十二条原则的出处

原则文件不写出处。下面每条取 `docs/research/workflow-compare/reports/R18-mmw-architecture-v2.md` 第 5.2 节表的「理由出处」列，原则名用 `docs/research/workflow-compare/reports/R19-naming-table.md` `### 4.3 原则（MMW 自有 12 条）` 的新名，写成与文件名一致的 `principle-<slug>`。B1 写原则文件时若核实出某条出处不同，由那张票改这一节。

- **principle-silence-is-never-a-pass**：ADR 0008 第 8 行；`implement` 第 22 行末两句；`night.md` 第 7、127 行；`ui-acceptance` 第 10 行；`to-tickets` 第 84 行
- **principle-resume-from-durable-state**：`dispatch/SKILL.md` 第 8 行；`verify-ticket/SKILL.md` 第 10 行；`exe-release/references/driving.md` 第 5 行；ADR 0019
- **principle-agents-are-woken-not-polled**：ADR 0010；`night.md` 第 11 行；`implement` 第 78、84 行；`one-ticket.md` 第 8 行
- **principle-report-faults-through-the-pipeline**：`dispatch/SKILL.md` 第 25 行；ADR 0010、0017、0018；`ui-acceptance` 规则 4、5；`implement` 第 18 行
- **principle-the-baseline-is-a-contract**：`implement` 第 22 行「A baseline is a decision someone already paid for …」
- **principle-refusals-name-one-next-step**：ADR 0008；`SKILL-SET-RULES.md` 第 12、59 行；`night.md` 第 66 行
- **principle-a-second-reader-judges**：`code-review/SKILL.md` 第 8 行；`to-tickets` 第 63 行；`tdd` 第 38 行「judged with fresh eyes」；`consulting.md` 第 9、37 行
- **principle-clues-are-not-evidence**：`implement` 第 47–49 行；`session.md` 第 89、101 行；`retro` 第 58、63–66 行；`advising.md` 第 15 行；`research` 第 10 行
- **principle-one-home-per-meaning**：`writing-for-agents` 第 78 行；`SKILL-SET-RULES.md` 第 17、40 行；`design-pages` 第 6 行；`editing-models.md` 第 3 行
- **principle-human-steps-stay-human**：`ui-acceptance` 规则 3；`person-ticket.md` 第 3 行；`wizard` description；`exe-release` 第 5 步
- **principle-no-secrets-or-personal-data-in-artifacts**：`diagnosing-bugs` `## Redact`；`saving-memory.md` 第 4–5 行；`handoff` 第 14 行；`product-answers.md` 第 96 行；根 `AGENTS.md` `## Gotchas` 末条
- **principle-decide-at-phase-boundaries**：残留 `ask-matt/PHASE-BOUNDARIES.md` 的五个选项与判断树（上游原文，来源记在 `imports.tsv`）

「被打断的命令原样重跑」不单独成原则。它是 mode `## Re-entry` 第 1 步的操作文字，点名 pstack 的 **principle-make-operations-idempotent**。

## Considered Options

- **脚本留在 `dispatch` 这个能力技能里**（R17）。否决。那个理由只对任务板和改模型成立，而且会让 `roles.json` 变成能力脚本向上读 mode 的数据。采用的是 R15 的布局：脚本进 `mmw/scripts/`，`dispatch` 解散，并入 R17 的 `roles.json` 与 `imports.tsv`，以及 R16 拆出的两个能力技能（R16 叫 `shared-experience`，现名 `memory-records`；以及 `deliver-a-change`）。
- **`models.py`、`hosts.json` 搬进 `setup-mmw/scripts/`，hook 搬进 `mmw/scripts/hooks/`**（R18 的上一版）。否决。两处都切断同目录相对路径。前者让 B2 之后每次起 worker、reviewer、advisor 都失败。后者让两个 hook 导入失败后在 Claude Code 上静默放行。hook 与其他脚本平放。
- **`resume_at` 留在 `verify-ticket.py`**（R16、R17）。否决。能力脚本仍然知道 worker 的步骤。「现在在哪一步」由 `dispatch.sh where` 从事件计算。
- **回退不需要重跑 `install.sh`**（R17）。否决。B1、B2 改了 `skills.txt`，回退是把已安装 checkout 移回上一个 `main` 提交并重跑 `install.sh`。
- **hook 启动器找不到目标时一律退出 2**（R18 的上一版）。否决。Claude Code 把 PreToolUse 的 exit 2 当作拦截，目标不在时本机每个会话的每条命令都会被拦。改为按 hook 分别处理：辅助路径和 Stop 放行，受管会话的 tool-guard 仍拒绝。
- **整份采用 R16，或整份采用 R17，或不并入后两份而只留 R15。** 否决。R15 的目录是底稿，单独采用就没有 `roles.json`、`imports.tsv`，也没有 R16 拆出的两个能力技能（R16 叫 `shared-experience`，现名 `memory-records`；以及 `deliver-a-change`）。R16 把调用开关留在上游 subtree，并把导入原则 frontmatter 里的开关键留着；文件不是 skill，这个键没有作用，改为导入时删掉这一行、记在 `imports.tsv`，subtree 原文不动。R17 把脚本留在 `dispatch`，已在第一条否决。

## Consequences

- 七种组件、判据、优先级和这十二条原则的名字，是以后各批和评审引用的那一个决定。留在原处而不点名 H1–H6 或 S 的批次票不合格。
- 0009–0031 的机制仍成立。本 ADR 的 `amends` 是空的。ADR 0033 只记 B2 的用法：relay 按 `kind` 取收件角色，唤醒带步骤指针。ADR 0034 记 pstack 以 subtree 引入。
- B1 改写事实 7 与 `### Hand-offs` 第 5 条之后，能力技能不再以「下一步」或「谁调用我」结尾。在那之前，现行的 `SKILL-SET-RULES.md` 仍是评审 Standards 轴用的文本。
- B2 解散 `dispatch`、拆出 `ticket_state.py` 与 `events.py` 之后，流水线的状态不再住在能力技能里。B2 之前，`where` 与 `RESUME:` 两套定位一起存在。
- 核心批次到 B2。B3–B5、多模型面板和 PR 交付那一组都不在核心批次里。
