# R6 ticket run 单元的归置

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4，引用写成「R4 D3.5 f」）逐项归置 ticket run 单元。准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）。技能文本现行规则 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）是被审视的对象。

单元范围：`implement`（含 `references/writing-interface-code.md`、`references/saving-memory.md`）、`code-review`（含 `references/session.md` 与四个 axis 文件）、`tdd`、`verify-ticket`（含 `references/linting.md`、`references/sub-issues.md`、`scripts/` 与 `mmw-v2/upstream-unlazy/` 的 gate-check）、`resolving-merge-conflicts`、`advisor`；角色 worker、reviewer、advisor；`docs/notes/stage-two-shared-experience-layer.md` 与 Nowledge Memory 的使用。

标注：「已核实」= 本轮回到原文或跑只读命令看到的；「推断」= 由原文推出；「未确定」集中在第 10 节。「收益」一栏只用用户要求 2 的六种：去掉经 grep 核实的真重复；给无处安放的内容一个家；让上游回到原文；被两个以上调用方复用；以后加外来技能不必改现有文字；消除已核实的断点或冲突。

---

## 0. 结论

1. **本单元的三个角色各保持一个操作文件，不拆层。** worker 是 `implement` 的 `SKILL.md`，reviewer 是 `code-review` 的 `references/session.md`，advisor 是 `advisor` 的 `references/advising.md`（R4 D3.1；L7 C.1 第 7 问）。不新建 playbook、原则文件或技能。
2. **`implement` 与 `code-review` 整目录分叉进 `mmw-v2/skills/`，名字不变；`mmw-v2/upstream/` 里的两份恢复 `5b1a4c51` 原文、不安装**（第 2 批）。收益是让上游回到原文：`implement` 现 101 行里上游原句只剩 `name` 与第 6 行，`code-review` 56 条上游非空行只存活 15 条（F1、F2）。技能文本本身不改，启动提示词不改。
3. **`tdd`、`resolving-merge-conflicts` 留在上游，不分叉、不改。** 它们的改动都属 R4 D5.3 的 e 类（改变能力）与 a 类（宿主中立）。R4 D5.3 举例说「段里夹着的 MMW 名词移到调用方」，本文核对后不做：两处段落无论如何仍与上游不同，挪走名词拿不到「回到原文」的收益（第 2 节 X2）。
4. **第 1 批只改脚本印出的锚点和一段测试：**
   - `implement` `## Closing steps` 八步各加粗体步骤名；`verify-ticket.py` `resume_at` 改印步骤名、改正 docstring；`tests/verify-ticket/test_preflight.py` 第 458–517 行的断言同一次提交改（F3）。
   - `tool-guard.py` 的 `NO_QUESTION` 改成角色中立时，本单元提供三个锚点：`implement` 的 `Put no question on the screen`、`code-review` `references/session.md` §3 的 `Could not tell`、`advisor` `references/advising.md` `## How to answer` 第 4 条 `Missing information gets named precisely`。第三个是 R4 D3.5 f 漏掉的：`dispatch.sh advise` 在发起方的工作树里起 advisor，worker 发起时那个目录是 `issue-<n>`，`tool-guard.py` 按目录名管辖它（F5，已核实代码；实际触发无证据）。
5. **三条起步原则在本单元各有引用处，只加句末括注**（第 3 批，原则文件存在之后）：`rerun-dont-reroute` → `implement` 第 18 行；`silence-is-never-a-pass` → `implement` 第 30 行、`session.md` §1；`the-tracker-is-the-state` → `implement` 第 74 行。
6. **与 R4 不一致的一处：`verify-ticket/SKILL.md` 第 16 行保留**（R4 D5.2 要删）。重复声称在 description 首句，第 16 行是把它送回 `implement` 的那一句；删它留下重复、拿掉出路（第 2 节 X1）。
7. **其余全部原样不动**，包括四个 axis 文件、`sub-issues.md`、`linting.md`、`verify-ticket.py` 除 `resume_at` 外的全部、`events.py`、gate-check、`advisor` 全文、`## Shared experience while implementing`、`saving-memory.md`、阶段二设计说明（第 7 节逐条写理由）。

---

## 1. 本轮回到原文核实的事实

| # | 事实 | 出处 | 结果 |
|---|---|---|---|
| F1 | 上游 `implement/SKILL.md` 15 行（含 `disable-model-invocation: true`，`agents/openai.yaml` 带 `policy.allow_implicit_invocation: false`）；现文 `SKILL.md` 101 行 + 两份 reference 57、54 行 | `git show 5b1a4c51:skills/engineering/implement/SKILL.md`；`wc -l` | 已核实 |
| F2 | 上游 `code-review/SKILL.md` 87 行，模型可触发，description 是「review since X」的通用分支审查；现 6 个 Markdown 共 322 行（15 + 101 + 54 + 60 + 55 + 37） | `git show 5b1a4c51:…/code-review/SKILL.md`；`wc -l` | 已核实。N3 §5 的「56 条上游非空行存活 15 条」未重算 |
| F3 | `resume_at` 返回 `step 1…5` 编号；docstring 引用的段首句「A ticket that already carries a run of your own」已不存在（现 `implement` 第 74 行是「A ticket you are prompted back into」）；`test_preflight.py` 第 458–517 行逐字断言 `RESUME: step <k> (…)`，第 450 行 docstring 也写「the resume table in the `implement` skill's `## Closing steps`」 | `verify-ticket.py` 第 2148–2181 行；`test_preflight.py` | 已核实 |
| F4 | `NO_QUESTION` 让改变交付的问题「write `ABANDON: AC<n> decision …` and open a needs-triage sub-issue」；`implement` 第 23 行让它开 `--sub-issue decision` 然后「the rest of the work carries on」 | `tool-guard.py` 第 74–80 行；`implement/SKILL.md` 第 23 行 | 已核实（同 R4 V9） |
| F5 | `advise_one` 用 `git rev-parse --show-toplevel` 作 advisor 的工作目录，启动提示词是 `Use the advisor skill.` 加 brief，不带 `AUTONOMOUS`；`tool-guard.py` `governed_ticket()` 按工作目录名 `issue-<n>` 判管辖，头注释写「every session a runner starts on a ticket — worker and reviewer」 | `dispatch.sh` 第 2052–2079 行；`tool-guard.py` 第 29–36 行、`governed_ticket` | 已核实代码。worker 是否在夜里咨询过 advisor：N7 §6 记「复审未找到任何一次 `dispatch.sh advise` 的真实使用记录」 |
| F6 | `code-review` 全部文件没有「屏幕上没人回答问题」的处理；`session.md` §3 有 `Could not tell`，§5 有 `unverified: <what would settle it>` | `code-review` 全文（本轮通读） | 已核实 |
| F7 | `spec-reviewer.md` 第 35 行说「A `Missing` against a row's `calls` is the finding that blocks closeout, so word it with the row id first」；`verify-ticket.py` 里 `review_problems` 为 0 处，现行机制 `review_finding_problems` 对任何 in-ticket 行一视同仁 | `grep -c review_problems`；`verify-ticket.py` 第 2241 行 | 已核实 |
| F8 | relay 送给 worker 的唤醒只有三种：`reviewer.reported`、`reviewer.lost`、`worker.queued`；`implement` 对每种恰好一处处理（前两种在第 3 步，第三种在第 1 步） | `relay.py` 头注释第 39–47 行；`implement` 第 78、84 行 | 已核实。接线 lint 第 2 类今天就能通过 |
| F9 | `writing-interface-code.md` 三处按编号写「closing step 1」；SSR 第 81 行的「by title rather than by number」只管「another skill」 | 两文件原文 | 已核实。同一技能内部的编号引用不在该规则内 |
| F10 | `tdd` 相对上游只改三段（第 22、26、38 行）；`tests.md`、`mocking.md`、`agents/openai.yaml` 逐字相同；上游 `tdd` 没有调用开关 | `git show 5b1a4c51:… \| diff` | 已核实 |
| F11 | `resolving-merge-conflicts` 相对上游改了 description 与第 1–3 步（clean merge 变红的分支）；上游没有调用开关；`dispatch.sh` 第 2520 行的 `integrate` 拒绝文字按名点名它 | `diff`；`dispatch.sh` | 已核实 |
| F12 | 除 `verify-ticket/SKILL.md` 自己的表外，没有技能点名 `references/linting.md`；`to-tickets` 第 7、8 步与 `night.md` 第 49、146 行各自写了自己的 `--lint` 命令 | `grep -rn linting.md`；`grep lint` | 已核实（与 N2 R11、R12 一致） |
| F13 | 词表 `_Home_` 指向 `mmw-v2/upstream/skills/engineering/{implement,code-review}/…` 的共 22 行：`docs/contexts/ticket-run/CONTEXT.md` 19 行、`tickets/CONTEXT.md` 2 行、`toolbox/CONTEXT.md` 1 行；另有 `docs/notes/stage-two-shared-experience-layer.md` 第 7 行等、ADR 0012 第 19 行 | `grep -rn` | 已核实 |
| F14 | `mmw-v2/skills/` 下的自有技能都没有 `agents/openai.yaml`；自有技能 `advisor` 的正文有 em-dash，`check_upstream_em_dashes.py` 只扫 `mmw-v2/upstream/skills/` | `ls mmw-v2/skills/*/agents`；该检查头注释 | 已核实。分叉后这两个技能离开该检查的范围，与其他自有技能一致 |
| F15 | 没有测试钉住 `session.md` §1、`spec-reviewer.md` 第 35 行、`Put no question on the screen`、`Could not tell`、`Missing information gets named precisely` 这些句子；只有 `test_preflight.py` 引用 `## Closing steps` | `grep -rln` `mmw-v2/tests` | 已核实（补上 N3 §10 留下的未查项） |
| F16 | 阶段二设计说明第 7 行自述「其余内容与代码不一致时以代码为准」；它 §5 的 bash 块没有 `saving-memory.md` 第 14–15 行的 scope 检查 | 两文件原文 | 已核实。说明已与技能分歧，但它自己声明了技能优先 |
| F17 | 本单元涉及的用户决定：`0ac93ab8` 规则唯一出处（写码在 `implement`、测试在 `tdd`、审查在 `code-review` 各 axis、仓库规则在 `CODING_STANDARDS.md`、`TESTING.md`）；`9d6755c0` DECISIONS 先于 review；`4756d4d3` 减法检查不另立评审轴；`fe94802d` 平级调用、不改写上游 frontmatter | `nmem --json m show` | 已核实。分叉不违反 `fe94802d`：自有文本进自有目录，上游目录恢复原文，没有嵌套 |

---

## 2. 与 R4 不一致或需要补充之处

| # | R4 的写法 | 本文的处理 | 理由 |
|---|---|---|---|
| X1 | D5.2：删 `verify-ticket/SKILL.md` 第 16 行，收益「去掉 B7 的重复声称」 | **保留第 16 行** | 重复声称在 description 首句「Run one ticket's acceptance criteria, and close the ticket when they pass」（N10 B7 第 3 条原文如此）。第 16 行「A worker's claim, criteria runs and closeout are steps of the `implement` skill.」是把凭这句进来的 agent 送回 `implement` 的出路。删掉它，description 的重叠还在，进来的 agent 在表里找不到跑判据、关票这一行。改 description 首句才是去掉重叠的做法，但没有一次记录在案的误走，改了会改变宿主启动时扫描的触发（列入第 10 节 U4） |
| X2 | D5.3 e 类：「段里夹着的 MMW 名词移到调用方」，例子含 `tdd` 的 seam 与重构去处、`resolving-merge-conflicts` 的 clean-merge 分支 | **不挪** | `tdd` 第 22 行的「写在纸上、不是一次对话」与第 38 行的两个去处本身是 e 类，要留；把「its `## Seam` section」换成「the ticket names」之后这两行仍与上游不同，拿不到「回到原文」，而 `implement` 第 30 行还要多一句把 **Seam** 对上号，净增文字、不改变任何决定（L7 C.6 信号 2）。`resolving-merge-conflicts` 第 2 步的「ticket and closeout evidence」同理：去掉后那一步读什么就说不清 |
| X3 | D3.5 f：`NO_QUESTION` 点名 `implement` 的步骤名与 `code-review` 的对应处 | **补 advisor，并定出 reviewer 的锚点** | F5：advisor 在 `issue-<n>` 里同样被管辖，收到的却是只对 worker 成立的出路（`Decisions I made on my own`、`ABANDON`）。三个角色各自的出路今天都已写在各自的操作文件里（F6、`advising.md` 第 18 行），不需要新文字，只需要指针与 lint 登记 |
| X4 | D3.2：角色文件「下一轮编辑时顺带加 `**Leaves:**`」 | **不加** | `implement` 第 8 步的 Done when 与收尾评论已经说了留下什么、给谁；加一行是位置得当的指引的复述（L7 C.6 信号 3） |
| X5 | D3.5 a 例子 `RESUME: Start the reviewer (…)` | 第 3 步取名 **Review round** | 第 3 步包含起 reviewer、被唤醒、修一轮、开 `finding` 子票；`RESUME:` 会在「reviewer.reported, no run of your own since」时指向它，此刻要做的是修，不是起 reviewer。名字是工程决定 |

---

## 3. 归置表

「批」指 R4 第 11 节的落地批次。「不动」行的理由见第 7 节同编号。

### 3.1 implement（worker 角色操作文件）

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| I1 | `mmw-v2/upstream/skills/engineering/implement/`（`SKILL.md`、`references/`、`agents/openai.yaml`） | `mmw-v2/skills/implement/`；能力技能，同时是 worker 的操作文件 | 移动（分叉）；`mmw-v2/skills.txt` `engineering/implement` → `self/implement` | 整目录，文字不变 | 让上游回到原文（F1）；`merge-notes/README.md` `## 本仓自有正文的技能` 里「自动合进来的上游段落也改回本仓的」这一手工步骤对它不再需要 | 技能文本 ±0；移动 215 行 | SSR `### Upstream skills` 第 112 行「fewer than half … reviewed as the set's own text」与 README 该节 → R4 D5.3 f 的分叉表。原意（拉上游时不悄悄撤掉本仓正文）：分叉后 subtree pull 不碰它，上游改动由人读 diff 按判断移植 | 2 |
| I2 | `mmw-v2/upstream/skills/engineering/implement/` | 同一路径；上游原文，不安装 | 回到上游原文（`5b1a4c51`） | `SKILL.md`、`agents/openai.yaml`；两份 reference 在上游不存在，随 I1 离开 | 让上游回到原文 | 上游目录约 −195 行 MMW 文本 | 同上 | 2 |
| I3 | frontmatter `name`、`description` | 原位 | 不动 | — | — | 0 | — | — |
| I4 | 第 6 行「Implement the work described by the user …」 | 原位 | 不动 | — | — | 0 | — | — |
| I5 | 第 8 行（两个脚本名裸写） | 原位 | 不动 | — | — | 0 | — | — |
| I6 | `## Claim, read in, write the code` 第 12–16 行 | 原位 | 不动 | 认领、wip、读入 | — | 0 | — | — |
| I7 | 第 18 行（fault → 开 `fault` 子票后停） | 原位 | 改写：句末加 `(the \`mmw\` skill's principle \`rerun-dont-reroute\`)` | 第 18 行末 | 被两个以上调用方复用：同一原则还被 `dispatch` `## On waking` 第 1 步、`night.md` `## 3` 的 `fault` 行引用（R4 D4.4）。改变的决定：一个看似能绕过去的流水线故障，worker 不自己换路 | +1 行内括注（约 8 词） | 无 | 3 |
| I8 | code-writing rules 第 20–28 行 | 原位 | 不动；第 23 行的 `Put no question on the screen` 登记进锚点常量 | 第 23 行 | 登记本身属 D3.5 f 与 lint 第 1 类（消除 F4 的冲突） | 0 | SSR `### Hand-offs`「Each event gets one instruction」由 lint 执行 | 1 |
| I9 | 第 30 行（`tdd` 交接、第一条红测试） | 原位 | 改写：句末加 `(the \`mmw\` skill's principle \`silence-is-never-a-pass\`)` | 第 30 行末 | 被两个以上调用方复用（`session.md` §1、`night.md` 收口、`to-tickets`）。改变的决定：`CHECK:` 没点名测试用例时，worker 仍要证明它依赖的检查能失败，而不是把一次绿当证据 | +约 8 词 | 无 | 3 |
| I10 | 第 32–34 行 | 原位 | 不动 | — | — | 0 | — | — |
| I11 | `## Shared experience while implementing` 第 36–68 行 | 原位 | 不动；标题登记为锚点（`dispatch.sh` 第 1741 行的 worker 首次提示词按标题点名它） | — | lint 第 1 类覆盖一处今天没人核对的脚本锚点 | 0 | — | 1 |
| I12 | `## Closing steps` 第 72 行 | 原位 | 不动 | — | — | 0 | — | — |
| I13 | 第 74 行（被重新提示后先 `--preflight`、按 `RESUME:` 续） | 原位 | 改写：句末加 `(the \`mmw\` skill's principle \`the-tracker-is-the-state\`)` | 第 74 行末 | 被两个以上调用方复用（`mmw` `## Where you are`、`night.md`、`idea-to-tickets`）。改变的决定：会话记忆与 `RESUME:` 不一致时信 `RESUME:` | +约 8 词 | 无 | 3 |
| I14 | 第 76 行 `ABANDON` 三种 | 原位 | 不动 | — | — | 0 | — | — |
| I15 | 第 1–8 步 | 原位 | 改写：每步开头加粗体步骤名，内容不动。建议名：**Integrate and run.**、**Post the decisions.**、**Review round.**、**Final run.**、**Audit.**（已有）、**Tell touched tickets.**、**Draft the closing comment.**、**Close out.** | 八步的首句 | 消除已核实的断点：`RESUME:` 按编号跨技能引用，docstring 已漂移（F3）；SSR 第 81 行已要求按标题引用 | 约 +20 词 | SSR 第 81 行保留；由 lint 第 1 类执行 | 1 |
| I16（已被 R12 K-43 改定） | `references/writing-interface-code.md` | `mmw-v2/skills/implement/references/`（随 I1） | 不动 | 含三处「closing step 1」 | — | 0 | — | — |
| I17 | `references/saving-memory.md` | 同上 | 不动 | — | — | 0 | — | — |
| I18（已被 R12 K-20 改定） | `agents/openai.yaml` | `mmw-v2/skills/implement/agents/`（随 I1） | 不动 | — | — | 0 | — | — |
| I19 | `mmw-v2/upstream/docs/engineering/implement.md`（给人读，不装） | 原位 | 回到上游原文 | 全页（现 +19/−5） | 让上游回到原文；同时去掉 N3 §2.7 记下的两处过时句 | −14 行 | 无 | 2 |
| I20 | `mmw-v2/upstream/skills/engineering/README.md` 的 `implement` 行 | 原位 | 回到上游原文 | 该行（同文件其余行属别的单元） | 让上游回到原文 | ±0 | 无 | 2 |
| I21 | `mmw-v2/merge-notes/implement.md` | 原位；仓库文档（分叉的移植记录） | 改写三处 | 开头「源目录」与「拉上游时不合并」一段改为分叉起点提交与「读上游 diff、按判断移植」；删 `frontmatter 的 disable-model-invocation …` 一行；改第 31 行关于 `--closeout` 查行 id 的过时句 | 去掉经 grep 核实的真重复（开关规则在 README `## disable-model-invocation` 已有，N10 R2、R4）；消除已核实冲突（F7 同类，N3 §2.7） | 约 −3 行 | README `## 本仓自有正文的技能` → 分叉表 | 2 |

### 3.2 code-review（reviewer 能力技能；`references/session.md` 是 reviewer 操作文件）

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则与原意 | 批 |
|---|---|---|---|---|---|---|---|---|
| C1 | `mmw-v2/upstream/skills/engineering/code-review/` | `mmw-v2/skills/code-review/`；能力技能 | 移动（分叉）；`skills.txt` → `self/code-review` | 整目录，文字不变 | 让上游回到原文（F2） | 移动 325 行 | 同 I1 | 2 |
| C2 | 同一上游路径 | 同一路径；上游原文，不安装 | 回到上游原文 | `SKILL.md` 87 行、`agents/openai.yaml` | 让上游回到原文 | 上游目录约 −235 行 MMW 文本 | 同 I1 | 2 |
| C3 | `SKILL.md`（目的句、`## Find your moment` 两行表） | 原位 | 不动 | — | — | 0 | — | — |
| C4 | `references/session.md` §1 `## 1. Pin the diff` | 原位 | 改写：第 13 行「Post it as the review …; then stop.」后加 `(the \`mmw\` skill's principle \`silence-is-never-a-pass\`)` | §1 | 被两个以上调用方复用。改变的决定：规则没写到的情形（某个 axis 什么都没回、或回报读不出来）按原则写成「查不了」，而不是在末尾的每 axis 一行里写成 0 条 | +约 8 词 | 无 | 3 |
| C5 | `session.md` §2–§5、`## Active Rules` | 原位 | 不动；§3 的 `Could not tell` 登记为 reviewer 的「无人值守时的问题」锚点 | §3 | 消除已核实冲突：`NO_QUESTION` 对 reviewer 给的是 worker 专属出路（F4、F6、N11 missing_edges 第 2 条） | 0 | SSR「Each event gets one instruction」由 lint 执行 | 1 |
| C6 | `references/standards-reviewer.md` | 原位 | 不动 | — | — | 0 | — | — |
| C7 | `references/spec-reviewer.md` 第 35 行 | 原位 | 改写：删「is the finding that blocks closeout, so」这半句理由，保留「word it with the row id first」 | `### The UI a page ticket owns` 第一段末句 | 消除已核实冲突：句子声称的机制已不存在（F7） | 约 −8 词 | 无 | 2 |
| C8 | `references/tests-reviewer.md` | 原位 | 不动 | — | — | 0 | — | — |
| C9 | `references/ui-reviewer.md` | 原位 | 不动 | — | — | 0 | — | — |
| C10（已被 R12 K-20 改定） | `agents/openai.yaml` | 随 C1 | 不动 | — | — | 0 | — | — |
| C11 | `mmw-v2/upstream/docs/engineering/code-review.md` | 原位 | 回到上游原文 | 全页（现 +23/−26） | 让上游回到原文；去掉 N3 §2.7 记下的「first `worker.started.base`」过时句 | +3 行 | 无 | 2 |
| C12 | 上游 `README.md` 的 `code-review` 行 | 原位 | 回到上游原文 | 该行 | 让上游回到原文 | ±0 | 无 | 2 |
| C13 | `mmw-v2/merge-notes/code-review.md` | 原位；仓库文档 | 改写三处 | 开头源目录；`## 下次拉上游怎么合` 改为读上游 diff、按判断移植；第 102 行过时句 | 消除已核实冲突（F7 同一过时理由） | 约 ±0 | 同 I21 | 2 |

### 3.3 tdd、resolving-merge-conflicts（上游能力技能）

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益 | 体量 | 被取代的旧规则 | 批 |
|---|---|---|---|---|---|---|---|---|
| T1 | `tdd/SKILL.md` 第 22、26、38 行 | 原位；上游能力技能 | 不动（e 类、a 类） | `**Test only at pre-agreed seams.**`、`codebase-design` 指向、`**Refactoring is not part of the loop.**` | — | 0 | — | — |
| T2 | `tdd/tests.md`、`mocking.md`、`agents/openai.yaml` | 原位 | 不动 | — | — | 0 | — | — |
| T3 | `merge-notes/tdd.md` | 原位 | 不动 | — | — | 0 | — | — |
| RM1 | `resolving-merge-conflicts/SKILL.md` | 原位；上游能力技能 | 不动（description 与第 1–3 步为 e 类） | — | — | 0 | — | — |
| RM2 | `upstream/docs/engineering/resolving-merge-conflicts.md` | 原位 | 不动 | — | — | 0 | — | — |
| RM3 | `merge-notes/resolving-merge-conflicts.md` | 原位 | 不动 | — | — | 0 | — | — |

### 3.4 verify-ticket（自有能力技能）与 gate-check

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 | 批 |
|---|---|---|---|---|---|---|---|---|
| V1 | `SKILL.md` 第 8–12 行 | 原位 | 不动 | — | — | 0 | — | — |
| V2 | `SKILL.md` 第 16 行 | 原位 | 不动（与 R4 D5.2 不同，见 X1） | — | — | 0 | — | — |
| V3 | `SKILL.md` 表两行、`## Reached from here` | 原位 | 不动 | — | — | 0 | — | — |
| V4 | `references/linting.md` | 原位 | 不动 | — | — | 0 | — | — |
| V5 | `references/sub-issues.md` | 原位 | 不动 | — | — | 0 | — | — |
| V6（已被 R12 K-2、K-47 改定） | `scripts/verify-ticket.py` `resume_at` | 原位；脚本 | 改写：返回值由编号改为步骤名，名字从锚点常量取（例 `RESUME: Review round (reviewer.reported, no run of your own since)`；退回时 `RESUME: Integrate and run, then Final run onward (ticket.returned)`）；docstring 改为指向 `implement` `## Closing steps` 的步骤名 | 第 2148–2181 行 | 消除已核实断点（F3） | 约 ±15 行 | 无 | 1 |
| V7 | `verify-ticket.py` 其余 | 原位 | 不动 | — | — | 0 | — | — |
| V8 | `events.py`、`issue_tree.py` | 原位 | 不动 | — | — | 0 | — | — |
| V9 | `scripts/gate-check/` 三个相对链接；`mmw-v2/upstream-unlazy/scripts/…` | 原位 | 不动 | — | — | 0 | — | — |
| V10 | `merge-notes/unlazy.md` | 原位 | 不动 | — | — | 0 | — | — |
| V11 | `mmw-v2/tests/verify-ticket/test_preflight.py` 第 450 行 docstring、第 458–517 行八条断言 | 原位 | 改写：断言改为步骤名；另加一条：每个 `resume_at` 可能的取值都能在 `implement/SKILL.md` 里逐字找到（与 lint 第 1 类同源） | 同左 | 同 V6（改动与测试同一提交） | 约 ±20 行 | 无 | 1 |

### 3.5 advisor（自有能力技能；`references/advising.md` 是 advisor 操作文件）

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益 | 体量 | 被取代的旧规则 | 批 |
|---|---|---|---|---|---|---|---|---|
| A1 | `advisor/SKILL.md` | 原位 | 不动 | — | — | 0 | — | — |
| A2 | `references/consulting.md` | 原位 | 不动；`## The brief` 的「All five parts」登记为锚点（`dispatch.sh` 第 2057 行拒绝文字「write the five parts consulting.md lists」） | `## The brief` | lint 第 1 类覆盖一处今天没人核对的脚本锚点 | 0 | — | 1 |
| A3 | `references/advising.md` | 原位 | 不动；`## How to answer` 第 4 条 `Missing information gets named precisely` 登记为 advisor 的「无人值守时的问题」锚点 | 第 18 行 | 消除已核实冲突（F5，X3） | 0 | — | 1 |

### 3.6 角色、配置、脚本文字

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益 | 体量 | 被取代的旧规则 | 批 |
|---|---|---|---|---|---|---|---|---|
| R1 | `dispatch.sh` 第 1949 行 worker 启动提示词；第 1967 行 reviewer；第 2072 行 advisor | 原位；角色 = 启动提示词 + `~/.mmw/models.json` 一行 | 不动 | — | — | 0 | — | — |
| R2 | `~/.mmw/models.json` 的 `junior-worker`、`senior-worker`、`reviewer`、`advisor` 行 | 原位；配置 | 不动 | — | — | 0 | — | — |
| R3 | 锚点常量模块（R4 D1.2 的角色指针表与 D3.6 第 1 类的常量模块，本文取同一个文件：`mmw-v2/skills/dispatch/scripts/anchors.py`，由 dispatch 单元新建） | 同左；脚本 | 新建条目（本单元提供）：`implement` 八个步骤名、`## Closing steps`、`## Shared experience while implementing`、`Put no question on the screen`；`session.md` 的 `Could not tell`；`advising.md` 的 `Missing information gets named precisely`；`consulting.md` 的 `All five parts` | — | 消除已核实断点（F3、F4、F5）；lint 只对一处常量核对 | +约 15 行 | 无 | 1 |
| R4 | `tool-guard.py` `NO_QUESTION` | 原位（dispatch 单元的文件） | 改写（dispatch 单元执行）：不再给 worker 专属出路，按角色点名 R3 的三个锚点 | — | 消除已核实冲突（F4、F5、F6） | ±0 | 无 | 1 |

### 3.7 Memory 与文档

| # | 现在位置 | 新位置与层 | 动作 | 具体小节 | 收益（证据） | 体量 | 被取代的旧规则 | 批 |
|---|---|---|---|---|---|---|---|---|
| M1 | `docs/contexts/ticket-run/CONTEXT.md`、`tickets/CONTEXT.md`、`toolbox/CONTEXT.md` 的 22 行 `_Home_` | 原位；仓库文档 | 改写：路径改到 `mmw-v2/skills/{implement,code-review}/…` | F13 所列行 | 消除断点：分叉后路径失效，SSR `### Vocabulary` 第 80 行把「entry citing a file that does not hold those facts」算作 finding | ±0 | 无 | 2 |
| M2 | `docs/notes/stage-two-shared-experience-layer.md` | 原位；仓库文档 | 改写：只改指向两个技能的路径（第 7 行等） | 路径 | 消除断点（路径失效） | ±0 | 无 | 2 |
| M3 | 同上文件的正文 | 原位 | 不动 | — | — | 0 | — | — |
| M4 | ADR 0012（第 19 行含旧路径）、0014、0026、0031 | 原位 | 不动 | — | — | 0 | — | — |
| M5 | Nowledge Memory 的使用：`dispatch.sh` `worker_memory_packet`、`reviewer_rules_packet`；`implement` 第 36–68 行；`saving-memory.md`；`session.md` `## Active Rules` | 原位 | 不动 | — | — | 0 | — | — |

---

## 4. 角色操作文件草图

本单元不产生新的 playbook，参与两份已有的：`mmw` 的 `## Head judgement` 与 `idea-to-tickets` 的 **Who checks** 在 No 分支点名 `tdd`（R4 D2.2、D3.3）。下面三份是角色操作文件，写到「做什么、点名谁」。所有权行不加：启动提示词已经说了这个会话拥有哪张票（「work ticket #N」「review ticket #N from base commit …」「the brief」），再写一行是复述。

### 4.1 worker：`implement`（分叉后 `mmw-v2/skills/implement/SKILL.md`）

- **入口：** 脚本启动提示词 `Use the implement skill to work ticket #N. $AUTONOMOUS $PRODUCT_RULES` 加两份 Memory 索引（`dispatch.sh start <n> worker`）；自己拿票的会话经 `dispatch` `## Find your moment` 第 2 行 → `references/inside-a-ticket.md` → 本文件。
- **角色配置：** `~/.mmw/models.json` 的 `junior-worker` 或 `senior-worker` 行（票上 **Worker** 一行决定）。
- **步骤：**
  1. **Claim.** `verify-ticket.py <n> --preflight`；自拿票先照 `dispatch` 的 `references/inside-a-ticket.md` 跑 `adopt`。
  2. **Read in.** 票、子票、**Read first**、**Parent** 指向的 spec 小节、`CONTEXT.md`；票列了 screen contract → `references/writing-interface-code.md`。
  3. **Shared experience.** 打开相关 Memory 记录；遇到解释不了的行为用 `nmem memories search`；三项条件成立 → `references/saving-memory.md`。
  4. **Write the code.** code-writing rules；子票照 `verify-ticket` 的 `references/sub-issues.md`；测试照 `tdd` 的 `SKILL.md`（principle `silence-is-never-a-pass`）；流水线故障 → `--sub-issue fault` 后停（principle `rerun-dont-reroute`）。
  5. **Integrate and run.** `dispatch.sh integrate <n>`；冲突或 clean merge 变红 → `resolving-merge-conflicts`；`verify-ticket.py <n>`；exit 3 结束回合，等 `#<n> worker.queued`。
  6. **Post the decisions.** `verify-ticket.py <n> --decisions <file>`。
  7. **Review round.** `dispatch.sh start <n> reviewer`，结束回合；`#<n> reviewer.reported` 唤醒后 `dispatch.sh wait`、`ack`；修票内一轮；票外 → `--sub-issue finding`；`reviewer.lost` → 再起一个。
  8. **Final run.** `verify-ticket.py <n> --reverify --actor worker`。
  9. **Audit.** 对着分支按用户早上的读法再读票。
  10. **Tell touched tickets.** `verify-ticket.py <n> --touched`。
  11. **Draft the closing comment.** 只等一句人话的判据 → `ABANDON: … decision` 加 `--sub-issue decision`；`verify-ticket.py <n> --draft`。
  12. **Close out.** `verify-ticket.py <n> --closeout <draft>`；手动关票被 `tool-guard.py pretool` 拦；仓库 checks 失败且落在并入票的代码上 → `resolving-merge-conflicts`。
  （5–12 即 `## Closing steps` 的八步，粗体名是新加的锚点；1–4 是现有的前两节，不加名字，因为没有脚本按它们重入。）
- **重入：** relay 唤醒行末尾的角色指针 → `dispatch` `## On waking` → `## Closing steps`；`dispatch.sh resume` 重新提示时，先 **Claim**，再按 `RESUME: <步骤名>` 续（principle `the-tracker-is-the-state`）。
- **Done when：** `--closeout` 退出 0。
- **留下：** 关闭或交回 `needs-triage` 的票、收尾评论、票上的事件、推送的 `issue-<n>` 分支、可能的子票与 Memory 记录。读者是 orchestrator（`advance` 或 `land`）与早上的用户。

### 4.2 reviewer：`code-review` 的 `references/session.md`

- **入口：** worker 跑 `dispatch.sh start <n> reviewer`；提示词 `Use the code-review skill to review ticket #N from base commit <base>. $AUTONOMOUS` 加已批准的 reviewer Rules；`code-review` `SKILL.md` 的表按「提示词没点名 axis」送到本文件。配置行 `reviewer`。
- **步骤（现有 `##` 标题）：**
  1. **Pin the diff.** 三条 `git` 命令；ref 读不出或 diff 为空也作为 review 贴到票上（principle `silence-is-never-a-pass`）。
  2. **Run the axes.** 宿主自带的通用 subagent，每个 axis 一句提示词 → 回到 `code-review` `SKILL.md` 的表 → `standards-reviewer.md`（读 `CODING_STANDARDS.md`）、`spec-reviewer.md`（跑 `dispatch.sh integrated`）、`tests-reviewer.md`（读 `tdd` 的 `tests.md`、`mocking.md` 与 `TESTING.md`）、`ui-reviewer.md`（跑 `ui-acceptance` 的 `story-parity.py`）；占住回合直到全部回报。
  3. **Verify every finding.** Holds / `refuted` / `Could not tell`。
  4. **Sort.** 六条 in-ticket 条件。
  5. **Write one review report.** `verify-ticket.py <ticket> --review <file>`。
- **重入：** 无。一次性会话；会话丢失时 watchdog 写 `reviewer.lost`，relay 唤醒 worker，由 worker 在 **Review round** 另起一个。
- **Done when：** `--review` 退出 0。
- **留下：** 票上首行 `REVIEW <base>..<HEAD>` 的评论与 `reviewer.reported` 事件；读者是 worker、`--closeout` 的 `review_finding_problems`、`retro`。

### 4.3 advisor：`advisor` 的 `references/advising.md`

- **入口：** 任一 agent 按 `advisor` 的 description 加载，读 `references/consulting.md`，写 brief，跑 `dispatch.sh advise <file>`；新会话的提示词是 `Use the advisor skill.` 加 brief，`SKILL.md` 的表按「提示词是 brief」送到本文件。配置行 `advisor`。
- **步骤：** `## The brief tells you what the caller knows`；`## How to answer` 1–5（第 4 条是没人回答问题时的出路）；`## What you never do`。
- **重入：** 无。
- **Done when：** 发起方在 runner 显示的会话里读到回答（`consulting.md` `## Start it` 的 Done when）。
- **留下：** 会话里的回答；会话 id 交给用户（见第 9 节 P2）。

---

## 5. 原则

### 5.1 本单元引用的起步原则（R4 D4.4）

| 原则 | 规则（一句） | 理由出处 | 本单元的引用位置 | 其他引用位置 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 一道检查、一次交付不能因为什么都没做而读起来像通过；检查要证明自己能失败；查不了就说查不了 | ADR 0008 | `implement` 第 30 行（第一条红测试）；`code-review` `session.md` §1（空 diff 也上票） | `night.md` 收口；`to-tickets` 写判据；`idea-to-tickets` **Tickets** |
| `the-tracker-is-the-state` | 你在哪一步由票上的事件决定，不由会话记忆决定；要等别人就结束回合，由事件叫醒 | ADR 0010、0019、0020 | `implement` 第 74 行（`RESUME:`） | `mmw` `## Where you are`；`idea-to-tickets` `## Where you are`；`night.md` |
| `rerun-dont-reroute` | 被打断的命令原样重跑；被拒绝或撞上流水线自身的故障，就修拒绝点名的事或报 blocked，不绕路、不换 host 或 runner | ADR 0010、0017、0018 | `implement` 第 18 行 | `dispatch` `## On waking` 第 1 步；`night.md` `## 3` 的 `fault` 行 |

`tests-reviewer.md` 开头「You are the only reader who asks whether a green result proves anything」是 `silence-is-never-a-pass` 的同义句，但不加括注：读者是只读自己这一份文件的 axis subagent，指针要它离开文件再找一个技能，而规则已完整写在它面前（L7 C.5）。

### 5.2 看起来像原则、应留在原处的规则

| 规则 | 现在位置 | 留在原处的理由 |
|---|---|---|
| baseline 是合同（N9 PC8） | `implement` 第 22 行；`spec-reviewer.md` 第 16 行 | 第二个读者（Spec axis）已有理由句「A baseline records a settled decision」；R4 第 15 节的进入条件（第二个调用方需要理由而那里没有）不成立 |
| Memory 是线索不是证据（N9 PC11 的一部分） | `implement` 第 47–49 行；`session.md` `## Active Rules` 第 101 行；阶段二说明 §7、§8 | 两处各绑定一个机制（worker 用前核实、reviewer 不作 finding 来源），规则与理由都在各自读者的文字里（L7 C.2 第一种理由） |
| 一个文件同一时刻一个作者（N9 PC12） | `implement` 第 28 行；`to-tickets` 第 107 行；`sub-issues.md` 第 23 行 | 理由「one file has one writer at a time and the cut missed an edge」已在唯一执行者 worker 的文字里；`to-tickets` 一侧属另一单元 |
| `refuted` 的判据 | `implement` 第 84 行；`session.md` 第 44 行（逐字相同） | 两个读者（worker、reviewer）各在行动时读到，同一概念一个名字；绑定 review 机制，只适用于 ticket run 这一种任务（L7 C.6 信号 7） |
| 不在屏幕上提问 | `AUTONOMOUS`；`implement` 第 23 行；`NO_QUESTION` | owner 对所有无人会话的规则已在 `shared.md`（R4 第 13 节第 3 问）；三个载体的分工由 R4 D3.5 f 与本文 R3、R4 定下，由 lint 执行 |
| 不追 coverage、只在约定 seam 测 | `tdd` 第 22 行；`tests-reviewer.md` 第 52 行 | 属 `tdd` 这一项能力的内部规则；Tests axis 一处是同一规则的读者侧推论 |
| advisor 不写文件、不被引导 | `advising.md`；`consulting.md` | ADR 0014 有意各侧一份；只有一个任务（咨询） |

---

## 6. 连线

```edges
script:dispatch.sh start worker -> skill:implement : starts-with-prompt
script:dispatch.sh start worker -> config:models.json#junior-worker|senior-worker : configured-by
script:dispatch.sh start worker -> skill:implement#Shared experience while implementing : reads-reference
skill:dispatch#Find your moment row 1 -> skill:implement#Closing steps : routes-to
skill:dispatch#Find your moment row 2 -> ref:dispatch/inside-a-ticket.md : routes-to
ref:dispatch/inside-a-ticket.md -> skill:implement : hands-off-to
skill:implement -> ref:dispatch/inside-a-ticket.md : reads-reference
skill:implement -> script:verify-ticket.py --preflight : runs-script
script:verify-ticket.py --preflight -> skill:implement#Closing steps/<step name> : re-enters-at
script:verify-ticket.py resume_at -> script:dispatch/anchors.py : reads-reference
script:relay.py -> script:dispatch/anchors.py : reads-reference
script:dispatch.sh resume -> skill:dispatch#On waking : re-enters-at
event:reviewer.reported -> skill:dispatch#On waking : wakes
event:reviewer.reported -> skill:implement#Review round : re-enters-at
event:reviewer.lost -> skill:dispatch#On waking : wakes
event:reviewer.lost -> skill:implement#Review round : re-enters-at
event:worker.queued -> skill:dispatch#On waking : wakes
event:worker.queued -> skill:implement#Integrate and run : re-enters-at
skill:implement -> ref:implement/writing-interface-code.md : reads-reference
skill:implement -> ref:implement/saving-memory.md : reads-reference
skill:implement -> ref:verify-ticket/sub-issues.md : reads-reference
skill:implement -> script:verify-ticket.py --sub-issue : runs-script
skill:implement -> skill:tdd : calls
skill:implement -> skill:resolving-merge-conflicts : calls
skill:implement -> skill:ui-acceptance#Five rules while the product is running : reads-reference
skill:implement -> script:nmem memories show|search : runs-script
skill:implement#Integrate and run -> script:dispatch.sh integrate : runs-script
script:dispatch.sh integrate -> skill:resolving-merge-conflicts : hands-off-to
skill:implement#Integrate and run -> script:verify-ticket.py (criteria run) : runs-script
skill:implement#Post the decisions -> script:verify-ticket.py --decisions : runs-script
skill:implement#Review round -> script:dispatch.sh start reviewer : runs-script
skill:implement#Review round -> script:dispatch.sh wait|ack : runs-script
skill:implement#Final run -> script:verify-ticket.py --reverify --actor worker : runs-script
skill:implement#Tell touched tickets -> script:verify-ticket.py --touched : runs-script
skill:implement#Draft the closing comment -> script:verify-ticket.py --draft : runs-script
skill:implement#Close out -> script:verify-ticket.py --closeout : runs-script
skill:implement#Close out -> hook:tool-guard.py pretool : enforced-by-hook
skill:implement#Put no question on the screen -> hook:tool-guard.py question : enforced-by-hook
skill:implement -> principle:rerun-dont-reroute : cites-principle
skill:implement -> principle:silence-is-never-a-pass : cites-principle
skill:implement -> principle:the-tracker-is-the-state : cites-principle
ref:implement/saving-memory.md -> script:nmem memories add|supersede|deprecate : runs-script
ref:implement/writing-interface-code.md -> script:ui-acceptance/story-parity.py : runs-script
ref:implement/writing-interface-code.md -> ref:ui-acceptance/story-parity.md : reads-reference
ref:implement/writing-interface-code.md -> ref:ui-acceptance/boundary-check.md : reads-reference
ref:implement/writing-interface-code.md -> skill:tdd : reads-reference
ref:implement/writing-interface-code.md -> script:verify-ticket.py --sub-issue contract : runs-script
ref:implement/writing-interface-code.md -> ref:design-pages/pull.md : hands-off-to
script:dispatch.sh start reviewer -> skill:code-review : starts-with-prompt
script:dispatch.sh start reviewer -> config:models.json#reviewer : configured-by
script:dispatch.sh start reviewer -> ref:code-review/session.md#Active Rules : reads-reference
skill:code-review -> ref:code-review/session.md : routes-to
skill:code-review -> ref:code-review/standards-reviewer.md : routes-to
skill:code-review -> ref:code-review/spec-reviewer.md : routes-to
skill:code-review -> ref:code-review/tests-reviewer.md : routes-to
skill:code-review -> ref:code-review/ui-reviewer.md : routes-to
ref:code-review/session.md -> skill:code-review : calls
ref:code-review/session.md -> script:verify-ticket.py --review : runs-script
ref:code-review/session.md -> principle:silence-is-never-a-pass : cites-principle
ref:code-review/session.md#Could not tell -> hook:tool-guard.py question : enforced-by-hook
ref:code-review/standards-reviewer.md -> doc:CODING_STANDARDS.md : reads-reference
ref:code-review/spec-reviewer.md -> script:dispatch.sh integrated : runs-script
ref:code-review/tests-reviewer.md -> ref:tdd/tests.md : reads-reference
ref:code-review/tests-reviewer.md -> ref:tdd/mocking.md : reads-reference
ref:code-review/tests-reviewer.md -> doc:TESTING.md : reads-reference
ref:code-review/ui-reviewer.md -> script:ui-acceptance/story-parity.py : runs-script
skill:tdd -> skill:codebase-design : reads-reference
mode:mmw#Head judgement -> skill:tdd : routes-to
playbook:idea-to-tickets#Who checks -> skill:tdd : calls
skill:advisor -> ref:advisor/consulting.md : routes-to
skill:advisor -> ref:advisor/advising.md : routes-to
ref:advisor/consulting.md -> script:dispatch.sh advise : runs-script
script:dispatch.sh advise -> skill:advisor : starts-with-prompt
script:dispatch.sh advise -> config:models.json#advisor : configured-by
script:dispatch.sh advise -> ref:advisor/consulting.md#The brief : reads-reference
ref:advisor/advising.md#Missing information gets named precisely -> hook:tool-guard.py question : enforced-by-hook
hook:tool-guard.py -> script:dispatch/anchors.py : reads-reference
skill:verify-ticket -> ref:verify-ticket/sub-issues.md : routes-to
skill:verify-ticket -> ref:verify-ticket/linting.md : routes-to
skill:verify-ticket -> skill:implement : hands-off-to
skill:verify-ticket -> skill:ui-acceptance : hands-off-to
ref:verify-ticket/sub-issues.md -> skill:implement#Claim, read in, write the code : reads-reference
ref:verify-ticket/sub-issues.md -> skill:ui-acceptance#Five rules while the product is running : reads-reference
ref:verify-ticket/linting.md -> script:verify-ticket.py --lint : runs-script
ref:design-pages/pull.md -> script:verify-ticket.py --sub-issue contract : runs-script
script:verify-ticket.py -> script:gate-check.mjs : runs-script
script:verify-ticket.py --lint -> script:gate-lint.mjs : runs-script
script:verify-ticket.py --closeout -> config:.mmw/target.json#checks : configured-by
script:tests/<suite>/run.sh -> lint:check_wiring.py : runs-script
lint:check_wiring.py -> script:dispatch/anchors.py : reads-reference
lint:check_wiring.py -> skill:implement : reads-reference
lint:check_wiring.py -> ref:code-review/session.md : reads-reference
lint:check_wiring.py -> ref:advisor/advising.md : reads-reference
lint:check_wiring.py -> ref:advisor/consulting.md : reads-reference
```

说明：`event:… -> skill:dispatch#On waking : wakes` 与紧随的 `re-enters-at` 两行合起来是角色指针的内容（R4 D1.2 给 worker 的那一行）。事件由 `verify-ticket.py` 的各子命令写到票上，由 relay 读到后送出；关系表里没有「写事件」，所以只画到唤醒为止。

---

## 7. 不动清单

| # | 部件或段落 | 不动的理由 |
|---|---|---|
| I3 | `implement` frontmatter | 只有两个键，description 只写触发；分叉后仍符合自有技能的检查（`check_own_skill_frontmatter.py`） |
| I4 | `implement` 第 6 行上游原句 | 2026-09-28 复审 B-1 指出对被派来的 worker 措辞不准（票不是 user 写的），但没有一次它导致错误决定的记录；改了说不出所列收益 |
| I5、I6、I10、I12、I14 | `implement` 第 8、12–16、32–34、72、76 行 | worker 操作文件的内部步骤，单一读者，每次全读（L7 C.1 第 7 问、C.3） |
| I8 | code-writing rules 七条 | 天然整体：修复轮按「the code-writing rules that governed the first write」整组引用，`sub-issues.md` 第 23 行按 bullet 名反指（N3 §8 第 2 条） |
| I11 | `## Shared experience while implementing` | 规则的唯一一份（worker 读），`dispatch.sh` 提示词只给数据并按标题指过来（阶段二说明 §3 原文）；ADR 0031 |
| I16（已被 R12 K-43 改定） | `writing-interface-code.md`（含三处「closing step 1」） | 只在 page ticket 分支读，一次读全；编号引用在同一技能内，不在 SSR 第 81 行的范围（F9），也不被脚本读 |
| I17 | `saving-memory.md` | 要逐字执行的 bash，只在保存分支读；scope 检查由命令自己做（N3 §8 第 11 条） |
| I18、C10 | 两份 `agents/openai.yaml` | 只带 Codex 的显示名，没有调用开关；删掉说不出收益 |
| C3 | `code-review` `SKILL.md` | 按提示词形状区分 reviewer 与 axis 的分派表，属能力内部 |
| C5 | `session.md` §2–§5、`## Active Rules` | reviewer 操作文件；§5 的格式被 `verify-ticket.py` 的 regex 读；`## Active Rules` 是 retro → reviewer Rules 机制的读者侧（阶段二说明 §8） |
| C6、C8、C9 | `standards-reviewer.md`、`tests-reviewer.md`、`ui-reviewer.md` | 每个 axis subagent 只读自己这一份文件（L7 C.5）；用户决定 `0ac93ab8` 定了规则唯一出处、`4756d4d3` 定了减法放在 Standards |
| — | `spec-reviewer.md` 除第 35 行外 | 同上；它的 §1 读法与 `session.md` §4 六条件是一对（N3 §8 第 4 条） |
| T1 | `tdd` 三段改动 | e 类与 a 类；挪走 `## Seam` 名词拿不到收益（X2） |
| T2 | `tests.md`、`mocking.md` | 上游逐字原文；Tests axis 按小节名读它们 |
| T3 | `merge-notes/tdd.md` | 每段已有条目，分类与 R4 D5.3 一致 |
| RM1–RM3 | `resolving-merge-conflicts` 全部 | clean merge 分支是 e 类（改变能力）；被 `implement` 两处与 `dispatch.sh` 第 2520 行按名调用，上游本来就模型可触发，推导规则（R4 D1.3）的结果与现状相同 |
| V1 | `verify-ticket/SKILL.md` 第 8–12 行 | 第 10 行「The ticket is the only state」绑定事件格式这一具体机制（L7 C.2 第一种理由），是 `the-tracker-is-the-state` 在本技能的具体化；加括注不改变任何决定，读者多是写票与开夜的 agent |
| V2 | 第 16 行 | 见 X1 |
| V3 | 两行表、`## Reached from here` | 能力内部按分支选 reference；交给 `ui-acceptance` 属能力调用（R4 D5.1） |
| V4 | `linting.md` | 删掉它能去掉三条命令的重复（F12），但它独有的一句「边在 tracker 上改，不在票正文改」没有别的家，要搬就得同时写进 `to-tickets` 第 8 步与 `night.md` `## 1b`，产生新的重复；description 的第二个触发也会失去目标。净收益为零 |
| V5 | `sub-issues.md` | 两个调用方（worker、`design-pages` `pull.md` 开 `contract`），天然整体（有序判定表，N2 §8）。`implement` 第 18、22、23、28 行与表的定义重叠，但 `implement` 给「何时开」、表给「是哪种」，且第 18 行已点名持有者（L7 C.5 的「点名持有者」写法） |
| V7 | `verify-ticket.py` 除 `resume_at` 外 | 已跑通；closeout 事务、preflight、草稿格式是天然整体（N2 §8） |
| V8 | `events.py`、`issue_tree.py` | 全流水线的库放在 `verify-ticket` 下是位置问题；搬走要改 `dispatch`、relay、status、board、retro 的导入与根 `AGENTS.md` Self-hosting boundary 点名的路径，拿不到所列收益 |
| V9、V10 | gate-check 与 `merge-notes/unlazy.md` | 五个改动文件逐段有条目（N2 §5 已核实）；上游行远多于一半，不满足分叉门槛 |
| A1–A3 | `advisor` 全文 | ADR 0014 的两扇门；三个锚点只登记、不改字 |
| R1、R2 | 三种启动提示词、`models.json` 四行 | 测试钉着提示词字面（R4 第 15 节）；角色 = 提示词 + 一行配置就是 ADR 0015 的形态 |
| M3 | 阶段二设计说明正文 | 设计说明是决定的记录（`shared.md` 规则 13 的例外），运行时从不读；它第 7 行已声明技能与代码优先（F16），所以 §5 bash 与技能的分歧不会误导 agent |
| M4 | ADR 正文（含 0012 第 19 行旧路径） | ADR 记录当时的决定，不改（R4 第 15 节） |
| M5 | Memory 的开工索引、搜索、保存、reviewer Rules | 机制已定（ADR 0031、阶段二说明）；规则各在读者文字里一份；本次架构改动不触及 |
| — | `tests-reviewer.md` 不加原则括注 | 见 5.1 末段 |
| — | `implement` 不加 `**Leaves:**` | 见 X4 |
| — | 另开普通票、不属架构：`docs/contexts/tickets/CONTEXT.md` 第 352、360 行 `_Home_` 指向不含那些事实的 `linting.md`（N2 §4.2）；ADR 0008 第 16 行指向已搬走的 `refusal.py`；gate-check 里 `verify-ticket.py` 从不传的 scope、lease 代码 | 真问题，与分层无关 |

---

## 8. 形式拆散自查（L7 C.6）

1. **新建前没确认已有组件不是归宿。** 未触发：本单元不新建组件；锚点常量写进 dispatch 单元新建的同一个模块。
2. **新增内容不改变决定。** 部分风险，已说明：四处原则括注各写明了它改变的决定（I7、I9、I13、C4），但只在规则没覆盖的情形起作用；是否真的改变决定待 R4 T13 实测。步骤名改变的是脚本印出什么与 lint 核对什么。
3. **重复已有的、位置得当的指引。** 未触发：括注只点名原则，不复述；`tests-reviewer.md` 与 `implement` 的 `**Leaves:**` 正因这一条不加。
4. **本可由机制强制的规则写成文字。** 未触发，而且反过来：`RESUME:` 与 `implement` 的对应、`NO_QUESTION` 的三个出路、两处脚本按标题点名的小节，都交给锚点常量与 lint。
5. **playbook 只调一个技能。** 未触发：不新建 playbook。
6. **reference 每次都读、单一调用方、读者是本代理。** 未触发：不新建 reference。
7. **原则说不出改变哪个决定，或只适用一步。** 未触发：5.2 把只适用 ticket run 一种任务的规则（`refuted`、seam）留在原处。
8. **拆完需要按步骤编号引用。** 未触发，而且反过来：把 `RESUME:` 的跨技能编号引用改成按名。
9. **拆出的内容没有第二个调用方、不减少重复。** 未触发：分叉是整目录搬家，不拆内容；`linting.md` 正因拿不到净收益而不删。
10. **把单入口的固定流程拆成三层。** 未触发：worker、reviewer、advisor 各一个操作文件。
11. **把只在流程之间复用的内容做成能力技能。** 未触发：不新建技能。

---

## 9. 待用户决定

| # | 决定 | 会改变什么 | 建议 |
|---|---|---|---|
| P1 | R4 U3 在本单元的落点：分叉后，上游原版 `code-review`（「review since X」的通用分支审查，用户可在任何仓库用）与上游原版 `implement` 不能与 MMW 版同名并装 | 今天已安装的 `code-review`、`implement` 就是 MMW 版，所以分叉本身不改变你看到的任何东西；只有你想在 MMW 之外用上游的通用审查时才需要决定 | 现在不装；要用就得给分叉版改名，属于范围决定 |
| P2 | 夜里的 worker 若咨询 advisor，`consulting.md` `## Start it` 要求「the user has the session id」，但没写会话 id 放在哪里让你早上看到 | 你早上读到的收尾评论里是否出现 advisor 会话 id | 暂不定：至今没有一次 `dispatch.sh advise` 的使用记录（N7 §6）；出现第一次使用后再定，候选位置是 `Decisions I made on my own` 的一行 |

批次授权（第 2 批要跑一次 `install.sh`，因为 `implement`、`code-review` 的软链目标变了）沿用 R4 第 11 节，不另列。

---

## 10. 未确定

| # | 问题 | 需要的实测 | 定下什么 |
|---|---|---|---|
| U1 | advisor 在 `issue-<n>` 里是否真会调用宿主的提问工具、从而收到 `NO_QUESTION`（F5 只核实了代码路径） | `tests/dispatch` 加一个假 runner 场景：worker 工作树里跑 `advise`，对 advisor 会话投一次提问工具调用，断言拒绝文字点名 `Missing information gets named precisely` | X3 的锚点是否需要进第 1 批，还是随后 |
| U2 | advisor 启动提示词不带 `AUTONOMOUS`，在非票工作树里提问时有没有人会答 | 读 runner 的会话记录，或在隔离 home 里起一次 advisor 并给一个缺信息的 brief | 是否给 `advise_one` 的提示词加 `AUTONOMOUS`（属 dispatch 单元） |
| U3 | 原则括注是否改变决定，尤其 C4 设想的「某个 axis 什么都没回」 | R4 T8/T13 走查：给 reviewer 一个会让某 axis 返回空的票，看它在每 axis 一行里写 0 条还是写查不了，是否打开了原则文件 | 四处括注的去留 |
| U4 | `verify-ticket` description 首句「Run one ticket's acceptance criteria, and close the ticket when they pass」是否把人或 agent 误引进来（X1） | R4 T11 的并排读，加 T1 会话里给一句「跑一下 #N 的验收」看加载了哪个技能 | 改 description 首句，还是维持第 16 行 |
| U5 | 分叉后 Codex 对没有 `agents/openai.yaml` 的自有技能如何显示，以及保留这两份文件是否有影响 | 在 Codex 里列技能，对比 `advisor`（无该文件）与分叉后的 `implement` | I18、C10 是否删文件（推断无影响） |
| U6 | `resume_at` 在「worker reverify 不在 HEAD」等情形返回 `None`，此时 worker 只能读票自判；改印步骤名不影响这一点，但是否还有其他没覆盖的组合 | 读 `events.fold` 的 `apply()` 全文，列出 `resume_at` 的全部取值组合，补 `test_preflight.py` 场景 | V6 的完整取值表 |

---

## 读了什么

- 通读：R4 全文；L7 第 0 节、第 A 节（A.0–A.11）、第 C 节全文、第 D.1 节；N2、N3 全文；N7 的 advisor 部分（§1.2、§2.2、§3.2、§4、§6、§7 的相关行）；N11 全文；N10 B7–B9 段。
- 原文逐行读完：`implement/SKILL.md`、两份 reference、`agents/openai.yaml`；`code-review` 全部 6 个 Markdown 与 `agents/openai.yaml`；`tdd/SKILL.md` 及其与上游的 diff；`resolving-merge-conflicts/SKILL.md`、`agents/openai.yaml` 及 diff、它的 merge-note 与 docs 页 diff；`verify-ticket/SKILL.md`、`linting.md`、`sub-issues.md`；`advisor` 全部三个文件；`merge-notes/README.md` 第 1–65 行、`merge-notes/tdd.md` 全文、`merge-notes/implement.md` 第 1–28 行与全部标题、`merge-notes/code-review.md` 全部标题；`dispatch/SKILL.md`；`skills.txt`；`tool-guard.py` 第 1–220 行；`turn-guard.py` 头注释；`relay.py` 头注释第 1–69 行；阶段二设计说明的全部标题与 §3–§9。
- 读到回答问题为止：`verify-ticket.py` 第 2140–2240 行（`resume_at`、`run_preflight`）与 `review_finding_problems` 开头；`test_preflight.py` 第 445–517 行；`dispatch.sh` 第 105–112、1940–1975、2040–2080、2515–2525 行与第 1729–1741 行附近；`check_upstream_em_dashes.py` 头注释；上游 `5b1a4c51` 的 `implement`、`code-review` `SKILL.md`、`agents/openai.yaml` 与 engineering `README.md` diff。
- Memory：`nmem m show` 读了 `0ac93ab8`、`9d6755c0`、`4756d4d3`、`ce037679`、`fe94802d`。
- 没有读：`events.py` `apply()`、`verify-ticket.py` 的 screen contract lint 与 `--publish` 函数体、`dispatch.sh` 的 `resume_one`、`status.py`、各 runner 适配器、四个 axis 之外的 `ui-acceptance` 文件、`merge-notes/implement.md` 第 29 行以后与 `merge-notes/code-review.md` 各节正文（只读标题，I21、C13 的改写范围依据标题与 N3 §5.2、§5.3 的对照）。依赖这些的结论已标推断或列入第 10 节。
