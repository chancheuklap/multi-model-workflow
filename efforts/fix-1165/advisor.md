# Advisor answer: candidate dispatch and prompt placement (brief 20261019-063512-190e/1)

## Recommendation

按计划写进票，结构不改：prototype 为顶层、architect 并入 `prototype/SKETCH.md`、arena 是全套技能里唯一派 candidate 的地方、启动句固定为 `--follow "the arena skill's references/candidate.md"`、专属规则经 brief 交给 candidate。我核对了计划点名的每个文件、`check-interfaces.py`、`dispatch.sh` 的 brief 页脚、research 技能的同类先例，以及 `upstream/pstack/skills/architect/SKILL.md` 与 `upstream/mattpocock/skills/engineering/prototype/UI.md` 的原文。四处要改，一处要交给 owner，列在下面。

**决定性的风险**：计划把 architect `## Phase B: Sketch` 的第二段（"Any other change … takes the Phase A sketch as its design … with no arena"）当作 Sediment 删掉。它不是 Sediment，是一次行为变更：今天一张票内部的代码形状仍由规划会话做 Phase A 落地并画一份草图；按计划，它什么也得不到，只剩票里按 feature.md 第 5 步和 mmw-mode `## Non-negotiables`"Any code → name the data shape first" 点名的数据形状，由 worker 自己定形。diff 证实这一段是 MMW 自己加的，不是 pstack 原文，所以可以删；但要在票和 commit message 里写成决定，并写明兜底（票里点名的数据形状）。这是 `## For the owner` 里唯一的一条。

## Four corrections to the plan

1. **门槛的措辞保住 intent 25。** DESIGN-INTENTS 第 25 条写的是 "a code shape that reaches beyond one ticket is settled by competing sketches"。计划把 prototype/SKILL.md 的门槛后半句换成 architect 的三种情况，第 25 条就不再是事实。写法：标题句保留 "the shape reaches beyond one ticket"，三种情况作为它的判定（an interface that code outside this change calls / a data shape stored or passed between subsystems / a change spanning more than one subsystem）。这样第 25 条只改 Home 行，正文不动。

2. **专属文件放 `## Task`，不放 `## Known`。** 走 brief 而不是 `--follow` 是对的，理由有二：`check-interfaces.py` 的 `FOLLOWED` 只检查反引号里的字面量，按调用方变化的 follow 串要么是非字面量（正则不过，或根本不被检查，等于废掉第 6 条保证），要么是 arena 里一张按调用方列的表（正是要删掉的"被调用方记住调用方"）；research 技能已有同一先例，investigator 读 brief 点名的 `references/sources/<category>.md`。但 `dispatch.sh` 的 `brief_footer` 把 `## Known` 定义为 "what the session that sent you already has, so start from it and do not redo it"，一个 candidate 读到这句会把那里的文件当成已完成的背景而略读。定义产物形状的文件（sketch-candidate.md、rationale-template.md、design-red-flags.md、ui-variant.md）属于"要做什么"，写进 `## Task`："the artifact, shaped per <files>"；`## Known` 只留 grounding 路径和输出目录。candidate.md 里"读完 brief 点名的每个文件再开工"那句照样保留。

3. **arena 的 rubric 规则和 UI 的 Done 不能互相打架。** arena `## Phase A: Frame` 第 2 条 "Candidates only see the task" 和 `## Phase B` "The rubric stays out of every brief"，碰上计划里 UI 的 rubric 等于 `ui-variant.md` 的 Done（candidate 必读），字面上矛盾。在 arena 加一句区分：挑选者用来排序的 rubric 不进 brief；一份 candidate 自己的完成标准（Done when）是任务的一部分。UI.md 里 "The owner chooses the base, not the score" 这句必须留下，计划改写后的那句已含"the owner picks"，确认它不被合并掉。

4. **改名漏网的两处。** 按 SKILL-SET-RULES `## Editing` 的 grep 规则：`writing-for-agents/UPSTREAM.md` 第 92 行（P19 行）两次写 `architect`，计划的维护清单没列；`rationale-template.md` `## Alternatives considered` 末句 "not other runner candidates" 的 runner 与改名 runner-prompt.md 的理由相同（Vocabulary：runner 在 MMW 指启动会话的程序），改为 candidates。模板是 pstack 原文（upstream-map.tsv 第 59 行），一个词的改动写进 commit message。

## The three doubts in the brief, answered

- **690 词的代价**：接受。另一条路是让 feature/bug-fix 直接点名 SKETCH.md，那门槛就得在每个调用点重写一遍，正是现在要消灭的重复。prototype/SKILL.md 瘦到约 900 词后，多出的是 `## Pick a branch` 和六条通用规则，其中规则 1 和 6 草图分支本来就要用。
- **arena 三条通用化**：比原第 8 行干净。原句让被调用方记住一个调用方，违反 SKILL-SET-RULES fact 6（never restates another skill's rules）和 `### Hand-offs`（A sentence written for one caller can misread under another）。三条各有调用方交代的位置：SKETCH.md 的 rubric 段、UI.md 第 2 步改写句。
- **"Design it twice" 删除**：成立。下一段固定跑三到四个角度，exhaust-the-design-space 挂到 Run three 那句即可。

## Checked and sound

- 单一发送者的类比成立：researcher 三个发送者各自硬编码 follow 串；advisor、reviewer、retro-analyst 各一个发送者。arena 一处发送、一个 follow 串，比 researcher 还严格。
- 2026-10-19 agentflow 的 Codex 会话去读 `prototype/SKETCH.md` 并失败，说明模型已经按"四个对等分支"的形状在找文件；计划的目录形状和它一致。
- UI.md 第 2 步搬进 ui-variant.md 的句子里，只有 "Sharing too much code" 一句是 mattpocock 原文，其余都是 MMW 自己的，不受 `### Upstream skills` 的限制。
- `docs/contexts/` 没有 architect、arena 的词条，不需要改 glossary；`ui-acceptance/CONTEXT.md:98` 的叶目录路径含 SKETCH，不变。
- blast-radius 第 6 步删除与 P19 Departure 一致。

## For the owner

❓ 一件事要你定：以后"一张票内部"的代码形状，规划会话不再画草图。

今天是这样：任何跨函数边界的改动，规划会话都会先把周边代码弄清楚，画一份接口草图，worker 照草图写。只有影响到票外的形状才开擂台（多份草图比选）。

计划之后是这样：只有影响到票外的形状才画草图，而且一画就是擂台。票内部的形状不画草图，票里写清数据形状，由夜里的 worker 自己定接口。

对你的影响：省掉规划会话一轮落地和画图的 token；代价是票内接口的质量从"规划会话定好"变成"worker 自己定、reviewer 把关"。我建议接受，因为票里本来就要写数据形状，而且这一层的错改起来便宜。不接受的话，计划里 SKETCH.md 保留一条"票内形状：落地后画一份草图，不开擂台"的分支即可，其余不动。

## Problems

None
