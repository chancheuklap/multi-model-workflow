# N3：implement + code-review + tdd 单元清点

清点对象的版本：`dev` 的 `f2ba7593`（2026-09-29）。上游原文：最近一次 squash 提交 `5b1a4c513d027a598a277aa45892a6823381f9a9`（`Squashed 'mmw-v2/upstream/' changes from 6654f6b6..c55ee460`），用 `git show 5b1a4c51:skills/engineering/<skill>/<file>` 读。

本报告只清点事实，不决定归置。标注约定：「原文」= 文件里写着；「推断」= 我从多处合读得出、文件没有一句话这么说；「已核实 / 未核实」只用于从线索材料（`docs/research/workflow-compare/reports/`、`docs/reviews/`）取来的结论；「实测」= 本次用只读命令（`git`、`gh issue list`、`gh api .../comments`、`nmem --json memories show/search`、`verify-ticket.py --help`）得到的数字。

## 0. 读了什么

- 逐字读完：单元内全部 17 个文件（下表）；`mmw-v2/merge-notes/implement.md`（270 行）、`code-review.md`（209 行）、`tdd.md`（19 行）；三个技能在 `5b1a4c51` 的全部上游文件（implement 2 个、code-review 2 个、tdd 4 个）；`mmw-v2/skills/dispatch/SKILL.md`；`mmw-v2/skills/verify-ticket/references/sub-issues.md`；`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（176 行全读）；`mmw-v2/merge-notes/README.md` 前 65 行；`docs/contexts/ticket-run/CONTEXT.md` 第 236–331 行及全部词条标题。
- 脚本只读到能说明它决定什么的程度：`verify-ticket.py` 的模块 docstring、`--help` 全文（已运行）、`run_preflight`、`resume_at`、`review_finding_problems`、`spec_judgement`、`run_decisions` 的签名与期望标题；`dispatch.sh` 的文件头注释（第 1–79 行）、`usage()`、子命令分派表（第 4640 行起）、`AUTONOMOUS`/`PRODUCT_RULES`（第 108–109 行）、`worker_memory_packet` 注释、`reviewer_rules_packet` 注释、`start` 里拼 worker/reviewer prompt 的一段（第 1900–1990 行）、`adopt_ticket` 注释、`integrated_ticket_numbers`、`integrated_since_start`、`integrate_ticket` 及其冲突报告、`wait_one` 注释；`tool-guard.py` 第 1–90 行（`NO_QUESTION` 文本）。
- ADR 读了标题与首段决定：0008、0010、0011、0012（全文）、0013、0015、0019、0020、0026、0027、0029、0031。
- 线索材料读过：`M3-mmw-ticket.md` 全文；`I3-mmw-ticket-intent.json` 中与三技能相关的条目；`I5-mmw-field-evidence.json` 全文前 12 KB（problems、working_well、nights 前段）；`docs/reviews/2026-09-28-lightweight/implement.md`、`code-review.md`、`tdd.md` 全文；`docs/reviews/2026-09-23-skill-set/汇总.md` 与 `docs/reviews/2026-09-28-lightweight/汇总.md` 中 grep 命中段；`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` 全文。`docs/research/mmw-structure/2026-09-06-handoff.md` 只 grep，未命中三技能名，未通读。T1–T4、C1–C5 JSON 未读（体量大，本单元结论均回到原文核实，不依赖它们）。
- 实测数据来源：本仓 tracker 的 85 张 `mmw:ticket` 票（#336–#589 之间有 REVIEW 的 73 张）全部 1,290 条评论。另一个 tracker（agentflow）与 Chameleon 未查。

## 1. 部件清单

| 文件 | 行 / 词 | 是什么 | 给谁用、何时 |
| --- | --- | --- | --- |
| `mmw-v2/upstream/skills/engineering/implement/SKILL.md` | 101 / 2727 | worker 做一张票的全过程：认领、读入、写码规则、Memory、收尾八步 | 被 `dispatch.sh start <n> worker` 起的 worker（prompt 原文 "Use the implement skill to work ticket #N"），以及自己拿起票的会话；每次运行全读 |
| `…/implement/references/writing-interface-code.md` | 57 / 880 | page ticket 的写码法：取设计侧值、写组件与 story adapter 与四列 boundary test、按 `DIFF` 就地修、设计侧错误的出路、一条代码路径 | worker，仅当票的 **Read first** 列了 screen contract（`SKILL.md` 第 16 行末句）；另被 `ui-acceptance/SKILL.md` 第 18 行的路由表指到 |
| `…/implement/references/saving-memory.md` | 54 / 308 | 存、改 Nowledge Memory 的可执行命令与正文五项格式 | worker，仅当 save conditions 三项同时成立或要更正一条记录（`SKILL.md` 第 66–68 行） |
| `…/implement/agents/openai.yaml` | 3 | Codex 的显示名与短描述；上游的 `policy.allow_implicit_invocation: false` 已删 | Codex host |
| `…/code-review/SKILL.md` | 15 / 145 | 一句目的 + `## Find your moment` 两行表：会话走 `references/session.md`，axis 走各自文件 | reviewer 会话与每个 axis subagent，每次全读 |
| `…/code-review/references/session.md` | 101 / 1195 | reviewer 的五步：钉 diff、起 axis、逐条核实、分 in/out-of-ticket、写 review report；`## Active Rules` | reviewer 会话（prompt 未点 axis 时），每次全读 |
| `…/code-review/references/standards-reviewer.md` | 54 / 819 | Standards axis：`CODING_STANDARDS.md` + 领域词汇 + 12 条 Fowler smell baseline + less-code 问 + deletion test | Standards axis subagent（或不能起 subagent 时的会话本身） |
| `…/code-review/references/spec-reviewer.md` | 60 / 1038 | Spec axis：读票及其指向物、`DECISIONS`、已并入票的语义冲突、page ticket 的 screen contract / story page / story adapter；三类 finding + `Decisions` 判断 | Spec axis |
| `…/code-review/references/tests-reviewer.md` | 55 / 824 | Tests axis：以 `CHECK:` 点名的测试为范围，读 `TESTING.md`，按六种测试 smell 判；两条永不报 | Tests axis |
| `…/code-review/references/ui-reviewer.md` | 37 / 476 | UI axis（试点）：跑 story criterion 取截图，报 element parity 覆盖不到的外观问题 | UI axis，仅当票有 story criterion（`session.md` §2） |
| `…/code-review/agents/openai.yaml` | 3 | Codex 显示名与短描述（已改为一张 ticket、四个 axis） | Codex host |
| `mmw-v2/upstream/skills/engineering/tdd/SKILL.md` | 38 / 648 | 上游 TDD 参考：好测试的定义、seam、三个反模式、循环三条规则（本仓改了 3 段） | worker（`implement` 第 30 行要它读）；`ask-matt` 的 No 分支里无票的会话；用户直接调用 |
| `…/tdd/tests.md` | 77 / 291 | 好/坏测试示例与 red flags（与上游逐字相同，已核实） | 按需；Tests axis 每次读（`tests-reviewer.md` §3） |
| `…/tdd/mocking.md` | 59 / 202 | 何时 mock、为可 mock 而设计（与上游逐字相同，已核实） | 按需；Tests axis 每次读 |
| `…/tdd/agents/openai.yaml` | 3 | 与上游相同 | Codex host |
| `mmw-v2/skills/dispatch/references/inside-a-ticket.md` | 13 / 177 | 自己拿起票的会话：先 `adopt`，`adopt` 的退出码，夜外关票后把 `land` 交给用户 | 自己拿票的会话，在 claim 之前（`dispatch/SKILL.md` moment 2；`implement` 第 12 行指过来） |
| `mmw-v2/skills/dispatch/references/one-ticket.md` | 14 / 349 | 夜外单票：`open-ticket`、`start worker`、对各种唤醒的处理、`land` | **不是 worker 读的**：是单票编排者（orchestrator）读的（`dispatch/SKILL.md` moment 4 "starting one worker on one ticket"）。原文 "this session becomes the ticket's orchestrator" |
| `mmw-v2/merge-notes/implement.md` | 270 | 维护者文档：每段意图、上游再动时怎么取舍、事故来源 | 拉上游或改技能的人；agent 运行时不读 |
| `mmw-v2/merge-notes/code-review.md` | 209 | 同上，另含「哪一段挪去了哪个文件」对照表与「下次拉上游怎么合」 | 同上 |
| `mmw-v2/merge-notes/tdd.md` | 19 | tdd 改了哪 3 段；`tests.md`/`mocking.md` 不改，因 Tests axis 按小节名引用 | 同上 |

单元之外但与之硬连的文件（未列入清点，只作连线）：`verify-ticket.py`（4,253 行）、`dispatch.sh`（4,761 行）、`tool-guard.py`、`verify-ticket/references/sub-issues.md`、`mmw-v2/upstream/docs/engineering/{implement,code-review,tdd}.md`（给人看的文档页，不装进 host）。

## 2. 内容分类表

类型缩写：**顺序**、**做法**、**规则+理由**、**命令接口**、**重入分派**、**格式模板**、**目的立场**、**沉积**。「读法」列：谁读、何时、每次还是分支。

### 2.1 `implement/SKILL.md`

| 位置（行） | 段落 | 类型 | 读法 |
| --- | --- | --- | --- |
| 1–4 | frontmatter `description`："…Use when you were dispatched onto a ticket, or picked one up yourself." | 分派（触发条件） | host 启动时扫描 |
| 6 | "Implement the work described by the user in the spec or tickets." | 上游原句；对被派来的 worker 不准确（票由 `to-tickets` 写，非 user）——2026-09-28 复审 B-1 指出，未改（已核实该句仍在） | 每次 |
| 8 | 两个脚本名裸写的说明 | 命令接口 | 每次 |
| 12 | 认领：`verify-ticket.py <n> --preflight`；`NOT_READY` 就停；自拿票先读 `inside-a-ticket.md` | 顺序 + 命令接口 + 分派 | 每次；分派句只影响自拿票分支 |
| 14 | 前任 worker 的 `wip(#<n>): uncommitted work of …` 提交是本票工作 | 重入 + 做法 | 每次读，只在续做时起作用 |
| 16 | 读入：票全文与评论、open sub-issues（附 `gh api --paginate …` 命令）、**Read first** 各项读到结论、baseline 是合同、design package 照抄 / prototype 按正式标准重写、spec 只读 Problem Statement + Solution + 点名的 Implementation Decisions + Testing Decisions + Out of Scope、票不说时按 Problem Statement 点名的人选、领域词汇表、有 screen contract 时读 reference | 顺序（读的先后）+ 做法 + 规则+理由（"not the whole spec"）+ 分派（末句） | 每次 |
| 18 | `--sub-issue` 的规则在 `sub-issues.md`；pipeline fault → `--sub-issue fault` 然后停 | 命令接口 + 分派 | 每次读，fault 分支才用 |
| 20–28 | `While writing code:` 七条 code-writing rules | 见下 | 每次；review 修复轮再次适用（第 84 行） |
| 22 | 第 1 条：baseline 是合同；为何（"a decision someone already paid for"）；不成立时开 `contract` child 并写什么；答案决定其余工作时结束回合；只有 orchestrator / user 改已发布 spec；过不了的检查用改代码或 abandon 答；为何检查值得信（诚实 `HANDOFF REQUIRED` 代价小、假 `ALL MET` 代价大） | 规则+理由 + 目的立场 + 命令接口 + 重入（结束回合等唤醒） | 每次 |
| 23 | 第 2 条：Put no question on the screen；取最可能选项写进 **Decisions I made on my own**；改变交付的问题开 `decision` child；每行写给 reviewer 与早上的用户 | 规则+理由 + 格式（行的读者） | 每次 |
| 24 | 改函数前 grep 调用方；被取代的分支、guard、文件同一 commit 删 | 做法 | 每次 |
| 25 | 写 helper 前先找现成 | 做法 | 每次 |
| 26 | 加文件/依赖/配置前在 Decisions 写为何现有的不够 | 规则（有落点） | 每次 |
| 27 | 简化时保住：安全、防数据丢失的错误处理、无障碍、票明确要的 | 规则 | 每次 |
| 28 | **Owns** 两档 + 并行票文件的例外（"one file has one writer at a time and the cut missed an edge"） | 规则+理由 + 命令接口（`deferred`、`contract`） | 每次 |
| 30 | 读 `tdd` 的 `SKILL.md` 在约定 seam 上照办；`CHECK:` 点名的用例是第一条红测试，红的原因必须是行为缺失；理由：认领时的 baseline 跑在测试存在之前、review 只读不跑 | 分派（hand-off 到 `tdd`）+ 做法 + 规则+理由 | 每次 |
| 32 | 定期跑类型检查与单测文件；末尾跑仓库说明为本票改动点名的测试；`--closeout` 自跑仓库 `checks` | 做法 + 命令接口 | 每次 |
| 34 | 验证手段随意；只在票要求或仓库本来就为这类改动留测试时提交测试；票要的每个行为仍要完整实现 | 规则（范围） | 每次 |
| 38–41 | 首次 prompt 带两份 Memory 索引；打开相关记录的 `nmem --json memories show` | 命令接口 + 做法 | 每次 |
| 47–49 | 当前工件、证据、用户与仓库指令、票、spec 压过 Memory；用前核实 | 规则 | 每次 |
| 51–64 | 遇到解释不了的行为：先按 task scope 再按 `mmw-experience` 搜；查询只用报错+命令+组件，前加 `--`（理由：Nowledge 对含未知标识的查询整批不返回） | 做法 + 规则+理由 + 命令接口 | 每次读，出事时用 |
| 66–68 | save conditions 三项；存或改去读 `saving-memory.md` | 规则 + 分派 | 每次读，分支用 |
| 72 | "Once done, commit…" | 顺序 | 每次 |
| 74 | 被重新提示回票：先 `--preflight`，按其 `RESUME:` 行续 | 重入与分派 | 续做分支 |
| 76 | 三种 `ABANDON`（`failed`/`stuck`/`decision`）各自定义与下游后果；`stuck` 不收产品运行中的人工步骤（归 `ui-acceptance` Five rules 3、4） | 规则+理由 + 格式 | 每次 |
| 78–80 | 第 1 步：`dispatch.sh integrate <n>`（exit 3 照 stderr、取舍记 Decisions、对面是已关票为何不能丢、两边不能同时成立开 `contract`；干净合并变红用 `resolving-merge-conflicts`；exit 2 → fault）→ `verify-ticket.py <n>`（exit 3 结束回合等 `worker.queued`）；轮数由 worker 判断，`ABANDON: AC<n> failed …`；Done when | 顺序 + 命令接口 + 规则+理由 + 重入 | 每次 |
| 81–83 | 第 2 步：`--decisions <file>`，两节格式，只发一次，理由（review 要逐行判） | 顺序 + 格式模板 + 规则+理由 | 每次 |
| 84–86 | 第 3 步：`dispatch.sh start <n> reviewer` 后结束回合；被 `#<n> reviewer.reported` 叫醒；`wait`、`ack`；start exit 2 的两种处理；一轮一个 reviewer，`reviewer.lost` 后再起；先修票内一轮（`refuted:` 判据）再对票外开 `finding`；Done when | 顺序 + 命令接口 + 重入（唤醒）+ 格式（`refuted:`） | 每次 |
| 87–89 | 第 4 步：`--reverify --actor worker`，在最后一个写 commit 的步骤之后，无修复轮 | 顺序 + 命令接口 | 每次 |
| 90–92 | 第 5 步 Audit：像用户早上读收尾评论那样对着分支再读票；不成立的写进收尾评论，final run 后不再提交 | 做法 + 目的立场 | 每次 |
| 93–95 | 第 6 步 `--touched` | 命令接口 | 每次 |
| 96–98 | 第 7 步：只等一句人话的判据写 `ABANDON: … decision` 并开 `decision` child；`--draft`（不给路径）；各 `<fill>` 的填法 | 格式模板 + 命令接口 | 每次 |
| 99–101 | 第 8 步：`--closeout <draft>`；不手动关票（hook 拦）；不开 PR、不跑 `land`；仓库 checks 失败且覆盖了并入票改的代码 → `resolving-merge-conflicts` | 命令接口 + 规则+理由 | 每次 |

### 2.2 `implement/references/writing-interface-code.md`（仅 page ticket 分支读）

| 位置 | 段落 | 类型 |
| --- | --- | --- |
| 1–3 | 何时读；两份 baseline 各管一块（design package 管外观与逐字文案，screen contract 管调用、字段、状态、失败、时序）；screen-contract 行对不上的 `contract` child 还要点名 wayfinder map 的 alignment ticket | 分派 + 规则+理由 |
| 5–17 `## Before the first line` | 读本票 screen-contract 行；`uv run story-parity.py … --render-only --out <mktemp>` 取设计侧截图与值；Done when | 顺序 + 命令接口 |
| 19–29 `## Write the product` | 按 `story-parity.md` 写组件与 story 页；同一轮写 story adapter 与每行四列 boundary test；story criterion 是 red-before-green 的例外及理由；从代码同步的 design system 照抄类名；Done when | 做法 + 规则+理由 + 分派（指 ui-acceptance 两个 reference） |
| 31–37 `## Fix in place` | 跑 story criterion，读 `DIFF` 行；先判设计值是否可信；只改点名的 id 与属性；像素差异图是证据不是判决；轮数与 `ABANDON:` 归收尾第 1 步；Done when | 做法 + 规则+理由 |
| 39–53 `## When the design side is the defect` | 四种情形开 `contract` child；判据保持红，`ABANDON` kind `stuck`，票以 `HANDOFF REQUIRED` 结束；child 文件首行与第二行的固定内容（第二行是中文固定句）；不动 design package；Done when | 命令接口 + 格式模板 + 重入（结局） |
| 55–57 `## One code path` | story 页数据只来自 story adapter；产品请求路径不因数据源、查询参数、构建开关换投影；理由句 | 规则+理由 |

### 2.3 `implement/references/saving-memory.md`（save 分支读）

| 位置 | 段落 | 类型 |
| --- | --- | --- |
| 3–11 | 只存可复用、对协作者安全的工程事实；排除项；`learning`/`procedure`；标签从环境取；标题写组件与行为；`证据` 写仓库路径（理由：Related experience 按路径排序） | 规则+理由 |
| 13–38 | 可执行 bash：`MMW_TASK_SCOPE` 不是 `mmw-map-*`/`mmw-spec-*` 就打印 `not saved` 退出；`nmem --json memories add --stdin …`；五项中文正文模板 | 命令接口 + 格式模板 |
| 40 | 写失败不挡票 | 规则 |
| 42–54 | 只改本 Space 的记录；先存替代再 `supersede`，不再适用则 `deprecate`；两条命令 | 规则 + 命令接口 |

### 2.4 `code-review/SKILL.md` 与 `references/`

| 文件 · 位置 | 段落 | 类型 | 读法 |
| --- | --- | --- | --- |
| `SKILL.md` 1–4 | description：审一张 ticket 的 diff，四个 axis 名，两条触发 | 分派 | host 扫描 |
| `SKILL.md` 8 | "A worker wrote this diff … what it misses ships." | 目的立场 | 会话与每个 axis 每次读 |
| `SKILL.md` 10–15 | `## Find your moment` 表 | 重入与分派 | 每次 |
| `session.md` 3 | 会话角色一句 | 目的立场 | reviewer 每次 |
| §1 5–15 | 三条 git 命令；三点 diff 的理由；ref 不解析或空 diff 也要作为 review 贴到票上；Done when | 顺序 + 命令接口 + 规则+理由 |
| §2 17–33 | story criterion 的定义；三或四个 axis；能起 subagent 时一条消息全起、不指定模型、prompt 只一句（给出句式）；不能起时顺序自跑并各写文件；**Hold this turn** 直到全部 axis 回报（理由：worker 睡在报告上） | 顺序 + 分派（host 能力分支）+ 格式（prompt 句式）+ 规则+理由 |
| §3 35–51 | 为何核实（两种错都有代价）；到引用处读到能答是否；三种结论 Holds / `refuted` / Could not tell；`refuted` 进 `## Withdrawn`；不定严重度、不修、不因修复大而丢；Done when | 做法 + 规则+理由 + 格式 |
| §4 53–63 | 分拣原则一句；六条 in-ticket 条件；`should not` 归 in-ticket；已并入票的 finding 按修复落点；两类各自下一步 | 规则+理由（带清单） |
| §5 65–97 | `verify-ticket.py <ticket> --review <file>`；首行 `REVIEW <base>..<HEAD>`；各节顺序；每条 finding 行的固定格式；category 取值；无代码位置时引 `<path>:1`；`unverified:`；每 axis 一行汇总；不跨 axis 排序合并及三条对照理由；Done when | 格式模板 + 命令接口 + 规则+理由（"Rank nothing across axes"） |
| `## Active Rules` 99–101 | 启动 prompt 列出已批准的 reviewer Rules 或 `none`；只在其范围内用来决定检查什么；Rule、Memory、worker 的推理都不能当 finding 的来源 | 规则 | 每次读；当前 0 条生效规则（见 §6） |
| `standards-reviewer.md` 3–5 | 两个问题；只读；读票与三点 diff | 目的 + 做法 | Standards axis 每次 |
| §1 7–9 | 只读 `CODING_STANDARDS.md` 与领域 glossary；缺文件时一行说明 | 做法 + 规则 |
| §2 11–39 | 两条约束（repository overrides；always a judgement call）；less-code 问及理由（"An author rarely deletes what it just added"）；deletion test；跳过工具已管的；12 条 smell 各 "what it is → how to fix" | 规则+理由 + 做法（上游原文 12 条） |
| §3 41–50 | 报告四类、标 hard / judgement；一条一项；Under 400 words 及理由 | 格式模板 |
| 52–54 | What is not yours：其余归别的 axis，"Report what you would report if they did not exist" | 规则（边界） |
| `spec-reviewer.md` 3–5 | 一个问题；只读；读票与 diff | 目的 + 做法 |
| §1 7–18 | 最新首行 `DECISIONS` 评论；只读 Parent 点名小节、Testing Decisions、Out of Scope、标为 baseline 的 Read first；理由句；无 Parent / spec 读不到的处理 | 做法 + 规则+理由 |
| §1 20–31 | `dispatch.sh integrated <ticket>`；读每张并入票与其收尾评论；四个 semantic-conflict angles；修复落点是否在本票 Owns | 命令接口 + 做法 |
| §1 33–39 | page ticket：screen contract 行按四列读、`Missing` 对 `calls` "blocks closeout, so word it with the row id first"；story root 位置；story adapter 画出每个 `shows` 值 | 做法 + 规则（page ticket 分支） |
| §2 41–50 | Missing / Scope creep / Built wrong + Decisions 两词判断；每条要引原文 | 格式 + 规则+理由 |
| §3 52–54 | 分组；Under 400 words 及理由 | 格式 |
| 56–60 | 不打开 design package（外观由 element parity 判）；其余归别的 axis | 规则+理由 |
| `tests-reviewer.md` 3–7 | 一个问题；只读不跑；"You are the only reader who asks whether a green result proves anything" | 目的立场 |
| §1 9–27 | 范围 = `CHECK:` 点名的测试文件与用例 + `boundary-check.py --run` 的产品测试 + `journey.py` 脚本；无则一行停；未被点名的测试文件也可报；boundary 与 journey 断言怎么看 | 做法 + 分派（无范围即停） |
| §2 29–31 | 读 `TESTING.md`，违反即 `documented-standard`；文件规则压过六种形状；缺文件一行说明 | 规则 |
| §3 33–44 | 读 `tdd` 的 `tests.md`、`mocking.md`；六种形状，前五种各指向 `tdd` 文件里的小节或 red flag，第六种 Only the happy path 全文 | 分派（跨技能读）+ 规则 |
| §4 46–48 | 报告格式；健全的用例也要说；Under 400 words | 格式 |
| 50–55 | 永不报 coverage（理由：只在约定 seam 测）；永不追加票外判据（理由：判据在工作前由别人写） | 规则+理由 |
| `ui-reviewer.md` §1 5–13 | 抄 story criterion 的 `--contract`/`--pages`，`uv run story-parity.py … --out <mktemp>`；看三种图；`DIFF`/`STORY OK` 不是本 axis 的判决 | 命令接口 + 做法 |
| §2 15–25 | 三类：`unpaired-decoration`、`overall-look`、`design-page-wrong`；已有 `DIFF` 的不报；"Sort nothing." | 格式 + 规则 |
| §3 27–33 | 引仓库 `path:line` 而不是临时 PNG；Under 400 words | 格式模板 + 规则+理由 |
| 35–37 | 元素事实归 story criterion；用起来的感觉归 reaction ticket | 规则（边界） |

### 2.5 `tdd`

| 文件 · 位置 | 段落 | 类型 | 读法 |
| --- | --- | --- | --- |
| `SKILL.md` 8 | TDD 是 red→green；本技能是让循环产出值得留的测试的参考；每个循环都适用 | 目的立场（上游） | worker 每张票读 |
| 10 | 读 `CONTEXT.md`（若有）、尊重相关 ADR | 做法（上游，软依赖） | 同上 |
| 12–16 `## What a good test is` | 通过公开接口验证行为；指向 `tests.md`、`mocking.md` | 规则+理由（上游） | 同上 |
| 18–26 `## Seams: where tests go` | seam 定义；只在约定 seam 测（本仓改：约定写在纸上，带票即 `## Seam`，无票才与用户确认）；`Ask:` 一句；形状不确定时读 `codebase-design` 的 `SKILL.md`（本仓改：去掉 "the Skill tool"） | 规则+理由 + 分派（带票/无票）+ hand-off | 同上 |
| 28–32 `## Anti-patterns` | Implementation-coupled、Tautological、Horizontal slicing，各有 tell | 规则+理由（上游） | 同上 |
| 34–38 `## Rules of the loop` | Red before green；One slice at a time；Refactoring is not part of the loop（本仓改：给理由与带票/无票两种去处，区分"保持改动正确"与重构） | 规则+理由 | 同上 |
| `tests.md` 全文 | 好测试特征、坏测试 red flags、tautological 示例 | 做法 + 示例（上游） | worker 按需；Tests axis 每次 |
| `mocking.md` 全文 | 只在系统边界 mock；Don't mock 清单；依赖注入与 SDK 式接口 | 做法（上游） | 同上 |

### 2.6 `dispatch` 的两份入口 reference

| 文件 · 位置 | 段落 | 类型 | 读法 |
| --- | --- | --- | --- |
| `inside-a-ticket.md` 1–5 | 先 `bash scripts/dispatch.sh adopt <n>`，理由（否则 reviewer 的报告叫不醒任何人、`start <n> reviewer` 会拒绝） | 顺序 + 规则+理由 | 自拿票会话，claim 前，一次 |
| 7–9 `## Exit codes` | `adopt <n> [--into <branch>]` 从哪运行、夜外加 `--into`、exit 2 | 命令接口 | 同上 |
| 11–13 `## After the closeout` | 夜外 adopt 的票无 orchestrator：被 `ticket.passed`/`ticket.returned` 叫醒后 `ack`，告诉用户跑 `land`；本会话不许跑 `land`（它停掉票上事件点名的所有会话） | 重入 + 规则+理由 | 同上，关票后 |
| `one-ticket.md` 3 | 夜外单票无 spec，`land <n>` 是全部结局；唤醒处理见 `SKILL.md` `## On waking` | 目的 + 分派 | 单票 orchestrator |
| 5–14 | 四步：`open-ticket`（把 board URL 交给用户）→ `start <n> worker`（在 origin 上存在的目标分支的检出里）→ 各唤醒的处理（`worker.lost`、`ticket.refused`、`child.opened` 的 fault / decision、contract 与 watchdog 指向 `night.md`）→ `land <n>`，bounce 时告诉用户 | 顺序 + 命令接口 + 重入与分派 | 同上 |

### 2.7 沉积（历史、来源、过时说明）

技能正文里几乎没有：`git grep` 这三个技能目录，没有 "no longer / used to / #<issue>" 式的改动记录（2026-09-28 复审 A 节也这么说，已核实本次 grep 同样只命中 `saving-memory.md` 的 "no longer applies"，指记录状态）。沉积集中在 merge-note（其主题就是改动，按规则应在那里）与以下几处**过时文本**（本次核实）：

- `verify-ticket.py` `resume_at` 的 docstring 仍写 "the resume table in the `implement` skill's `## Closing steps`, the paragraph starting 'A ticket that already carries a run of your own'"——该表已于 2026-09-28 移出技能，`SKILL.md` 现只剩第 74 行一句。
- `spec-reviewer.md` 第 35 行 "A `Missing` against a row's `calls` is the finding that blocks closeout, so word it with the row id first"、`merge-notes/code-review.md` 第 102 行 "`verify-ticket --closeout` refuses a draft that does not answer it"、`merge-notes/implement.md` 第 31 行 "收尾评论也要写出那个行 id（`--closeout` 查这一条），写在 `## Fix in place` 末尾"：`verify-ticket.py` 里已无 `review_problems`（grep 0 命中），`writing-interface-code.md` `## Fix in place` 也没有那句。现行机制是 `review_finding_problems`：**任何** in-ticket finding 都要在草稿里有 `fixed <commit>` 或 `refuted: …`，不单独认 row id。推断：「row id first」的理由已不成立，句子本身无害但理由过时。
- `mmw-v2/upstream/docs/engineering/implement.md` 第 9 行仍写 "It ships with `disable-model-invocation: true`" 与 `/implement` 用法；第 33 行 "A run is five beats" 下列 6 条。
- `mmw-v2/upstream/docs/engineering/code-review.md` 第 39 行 "between the first `worker.started.base`"，与 `merge-notes/code-review.md` 第 133 行强调的 *newest*（`newest_worker_field`，mmw #413 的修正）矛盾。

## 3. 连线

### 3.1 对外交接（产出什么、谁读）

| 产出 | 由谁产出 | 形式 | 谁读、做什么 |
| --- | --- | --- | --- |
| `ticket.claimed` / `ticket.refused`、baseline `ticket.checked` | worker 跑 `--preflight` | 票上事件 | relay 把 `ticket.refused` 送给 orchestrator（`one-ticket.md` 第 11 行）；closeout 用 baseline 填 `Green before work:` |
| 代码提交、`Merge <into> into issue-<n>` | worker、`dispatch.sh integrate` | `issue-<n>` 分支 | reviewer 的三点 diff；`advance`/`land` 合并 |
| `ticket.checked`（run `self`、`reverify` actor `worker`） | `verify-ticket.py <n>` / `--reverify --actor worker` | 事件 | `--preflight` 的 `RESUME:` 计算；closeout 只认 HEAD 上最新的 worker reverify（ADR 0026） |
| `worker.queued` | `verify-ticket.py` 无产品 slot 时 | 事件 | relay 在 slot 释放后叫醒 worker |
| `DECISIONS` 评论 / `worker.decided` | `--decisions <file>` | 两节固定标题 | Spec axis 逐行判 `reasonable`/`should not`；`--touched` 用 `spec_judgement` 读判断；早上的用户 |
| `reviewer.started` | worker 跑 `dispatch.sh start <n> reviewer` | 事件 + 新会话 | reviewer 会话；watchdog 判活，丢失时写 `reviewer.lost` 叫醒 worker |
| axis 报告 | 各 axis subagent | 回给会话 | reviewer 会话 §3 核实 |
| review report / `reviewer.reported` | reviewer 跑 `--review <file>` | 首行 `REVIEW <base>..<HEAD>` 的评论 | relay 叫醒 worker（`#<n> reviewer.reported`）；worker 修票内、开票外；closeout 的 `review_finding_problems` 对照；`retro` 读 review category（`retro/SKILL.md` 第 89 行，`retro.py` `BODY_KEPT_EVENTS`） |
| `child.opened`（`fault`/`contract`/`decision`/`deferred`/`finding`） | worker 跑 `--sub-issue` | 子 issue + 事件 | `fault`/`contract` 当夜叫醒 orchestrator（`night.md` 第 82–84 行）；`decision`/`deferred` 早上给用户；`finding` 等收口轮 `route`（`night.md` 第 108 行起） |
| `worker.touched` | `--touched` | 事件 | 被改了 Owns 文件的兄弟票的 worker |
| 收尾草稿 | `--draft`（落在仓库外） | 文件 | worker 填 `<fill>`，`--closeout` 核对 |
| `ticket.passed` / `ticket.returned`、推送 `issue-<n>` | `--closeout` | 事件 + 关票或交回 | orchestrator 的 `advance`/`land`；夜外 adopt 时是 worker 自己，再交给用户 |
| Memory 记录（`mmw-experience` 标签） | worker 按 `saving-memory.md` | Nowledge | 后续 worker 的首次 prompt 索引（ADR 0031）；`night.md` 收口轮第 151 行起关闭本 spec 的记录 |
| 夜外单票的 board URL、`land` 结果 | 单票 orchestrator（`one-ticket.md`） | 终端 | 用户 |

### 3.2 输入（谁交给本单元）

- worker 首次 prompt：`dispatch.sh` 第 1949 行 `"Use the implement skill to work ticket #$number. $AUTONOMOUS $PRODUCT_RULES"` + Memory 索引；环境 `NMEM_SPACE`、`NMEM_AGENT_ID=mmw-worker`、`MMW_TASK_SCOPE`、`MMW_SPEC`、`MMW_TICKET`。
- reviewer 首次 prompt：第 1967 行 `"Use the code-review skill to review ticket #$number from base commit $base. $AUTONOMOUS"` + reviewer Rules 数据；`NMEM_AGENT_ID=mmw-reviewer`。
- 票体字段（`to-tickets` 模板）：`## What to build`、`## Owns`、`## Read first`、`## Parent`、`## Seam`、`## Acceptance criteria`（`CHECK:`/`EXPECT:`）。spec 小节（`to-spec`）：Problem Statement、Solution、Implementation Decisions、Testing Decisions、Out of Scope。
- 仓库文档：`CODING_STANDARDS.md`（Standards axis）、`TESTING.md`（Tests axis）、`CONTEXT.md`/`CONTEXT-MAP.md`（worker、Standards axis、tdd）、`AGENTS.md` 的测试命令（第 32 行 "the tests the repository's own instructions name"）。
- page ticket：`screen-contract.yaml`（`write-screen-contract`）、design package（`design-pages` pull）。

```edges
dispatch.sh(start worker) -> implement : hands-off-to
dispatch.sh(start worker) -> Nowledge Mem : reads (worker_memory_packet builds the two indexes)
dispatch.sh(start reviewer) -> code-review : hands-off-to
dispatch.sh(start reviewer) -> reviewer Rules (nmem rule_stack) : reads (reviewer_rules_packet)
dispatch/SKILL.md(moment 1) -> implement : re-enters-at (## Closing steps)
dispatch/SKILL.md(moment 2) -> inside-a-ticket.md : hands-off-to
dispatch/SKILL.md(moment 4) -> one-ticket.md : hands-off-to
ask-matt -> implement : hands-off-to
ask-matt -> tdd : hands-off-to (No branch, no ticket)
implement -> inside-a-ticket.md : cites (self-picked ticket, before claim)
inside-a-ticket.md -> dispatch.sh adopt : runs-script
inside-a-ticket.md -> dispatch.sh ack : runs-script
one-ticket.md -> dispatch.sh open-ticket|start|ack|resume|land : runs-script
one-ticket.md -> night.md : cites (contract child, watchdog, turn guard)
implement -> verify-ticket.py --preflight : runs-script
verify-ticket.py --preflight -> implement : re-enters-at (RESUME: step k)
implement -> to-tickets ticket fields : reads (What to build, Owns, Read first, Parent, Seam, Acceptance criteria)
implement -> to-spec spec sections : reads (Problem Statement, Solution, named Implementation Decisions, Testing Decisions, Out of Scope)
implement -> CONTEXT.md / CONTEXT-MAP.md : reads
implement -> writing-interface-code.md : hands-off-to (Read first lists a screen contract)
implement -> saving-memory.md : hands-off-to (save conditions hold)
implement -> tdd : calls (read SKILL.md, follow at pre-agreed seams)
implement -> verify-ticket sub-issues.md : cites
implement -> verify-ticket.py --sub-issue : runs-script (fault, contract, decision, deferred, finding)
verify-ticket.py --sub-issue -> child.opened : writes-event
child.opened(fault|contract) -> orchestrator : wakes (via relay)
implement -> dispatch.sh integrate : runs-script
implement -> resolving-merge-conflicts : calls (exit 3 or clean merge turns checks red; closeout checks fail on incoming code)
implement -> verify-ticket.py (criteria run) : runs-script
verify-ticket.py -> ticket.checked : writes-event
verify-ticket.py -> worker.queued : writes-event
worker.queued -> implement : wakes (via relay)
implement -> verify-ticket.py --decisions : runs-script
verify-ticket.py --decisions -> worker.decided : writes-event
implement -> dispatch.sh start reviewer : runs-script
dispatch.sh start reviewer -> reviewer.started : writes-event
implement -> dispatch.sh wait / ack : runs-script
implement -> verify-ticket.py --reverify --actor worker : runs-script
implement -> verify-ticket.py --touched : runs-script
verify-ticket.py --touched -> worker.touched : writes-event
implement -> verify-ticket.py --draft : runs-script
implement -> verify-ticket.py --closeout : runs-script
verify-ticket.py --closeout -> ticket.passed|ticket.returned : writes-event
ticket.passed|ticket.returned -> orchestrator : wakes (via relay)
implement -> ui-acceptance Five rules : cites (stuck vs fault)
implement -> nmem memories show/search : runs-script
saving-memory.md -> nmem memories add/supersede/deprecate : runs-script
writing-interface-code.md -> ui-acceptance story-parity.py --render-only : runs-script
writing-interface-code.md -> ui-acceptance references/story-parity.md : cites
writing-interface-code.md -> ui-acceptance references/boundary-check.md : cites (## Selecting one row's test)
writing-interface-code.md -> tdd : cites (declared exception to Red before green)
writing-interface-code.md -> verify-ticket.py --sub-issue contract : runs-script
writing-interface-code.md -> design-pages references/pull.md : cites (child body second line)
tool-guard.py(question gate) -> implement : cites (NO_QUESTION points at Decisions / decision child)
code-review SKILL.md -> session.md : hands-off-to (no axis named)
code-review SKILL.md -> standards/spec/tests/ui-reviewer.md : hands-off-to (axis named)
session.md -> code-review (axis subagents) : calls (host general-purpose subagent, one sentence prompt)
session.md -> verify-ticket.py --review : runs-script
verify-ticket.py --review -> reviewer.reported : writes-event
reviewer.reported -> implement : wakes (via relay)
reviewer.lost -> implement : wakes (watchdog, via relay)
standards-reviewer.md -> CODING_STANDARDS.md : reads
standards-reviewer.md -> CONTEXT.md / CONTEXT-MAP.md : reads
spec-reviewer.md -> DECISIONS comment : reads
spec-reviewer.md -> dispatch.sh integrated : runs-script
spec-reviewer.md -> screen-contract.yaml : reads (page ticket)
tests-reviewer.md -> TESTING.md : reads
tests-reviewer.md -> tdd tests.md / mocking.md : reads
ui-reviewer.md -> ui-acceptance story-parity.py : runs-script
reviewer.reported(review category) -> retro : reads
retro -> reviewer Rules : writes (reviewer-rule destination)
tdd -> codebase-design : calls (read SKILL.md for vocabulary when interface shape is in question)
tdd -> CONTEXT.md : reads (soft)
verify-ticket.py spec_judgement -> review report ## Spec : reads (path and should not/reasonable on one line)
verify-ticket.py review_finding_problems -> review report ## In-ticket : reads
```

关系 `wakes (via relay)` 指：事件写在票上，由 `relay.py` 读到后经 runner 的 `send` 送给等它的会话（ADR 0020）；不是写事件的脚本直接报信。

## 4. 重复

用 `grep -rn`（范围 `mmw-v2/`、`docs/contexts/`、`docs/agents/`、根 `AGENTS.md`、`TESTING.md`、`CODING_STANDARDS.md`、`mmw-v2/prompt/`；merge-notes 与 docs/reviews 另计）核实。

| 内容 | 本单元位置 | 其他出现处 | 判定 |
| --- | --- | --- | --- |
| `refuted` 判据 "Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count." | `implement/SKILL.md` 第 84 行；`session.md` 第 44 行 | `merge-notes/code-review.md` 第 175 行（记录）；`docs/contexts/ticket-run/CONTEXT.md` **Holds / `refuted` / Could not tell** | 真重复（逐字），两份读者不同（worker / reviewer），各在行动时读到。2026-09-28 复审判"两份都留"（已核实原文） |
| 不在屏幕上提问 | `implement/SKILL.md` 第 23 行 | `dispatch.sh` 第 108 行 `AUTONOMOUS`（进每个 worker/reviewer prompt）；`tool-guard.py` 第 76–79 行 `NO_QUESTION`（host 的提问工具被拦时的拒绝文本） | 真重复（同一意思，三个载体）。**有出入**：`NO_QUESTION` 说改变交付的问题要 "write `ABANDON: AC<n> decision …` and open a needs-triage sub-issue"；`implement` 第 23 行只说开 `decision` child 并继续，`ABANDON … decision` 只在第 7 步「判据只等一句人话」时写。推断：对同一事件给出两种略有差别的指令（SKILL-SET-RULES `### Hand-offs` "Each event gets one instruction"） |
| pipeline fault 的范围 | `implement/SKILL.md` 第 18 行（已缩为 "the pipeline's own scripts, a hook, or `.mmw/target.json`"） | `verify-ticket/references/sub-issues.md` 第 19 行（完整清单）；`ui-acceptance/SKILL.md` 第 36 行 Five rules 第 5 条；`docs/contexts/ticket-run/CONTEXT.md` 第 158 行 | 真重复（同一定义），`implement` 那份是缩写 |
| 五种 child kind 的时机与定义 | `implement/SKILL.md` 第 18、22、23、28、84、96 行 | `sub-issues.md` 的 kind questions 表；`CONTEXT.md` **child kind** | 部分重复：`implement` 给「何时开」，`sub-issues.md` 给「是哪种」的判别表。`sub-issues.md` 第 23 行反指 `implement` 的 bullet 名 |
| 并行票不写同一文件 | `implement/SKILL.md` 第 28 行 | `to-tickets/SKILL.md` 第 107 行 "no two tickets that can run at the same time write the same file"；`sub-issues.md` 第 23 行 | 同一规则两个执行点（切票者 / worker），merge-note 第 258 行明言 "One rule now holds in two places"。真重复，有意为之 |
| in-ticket 六条件 | `session.md` 第 57 行 | `docs/contexts/ticket-run/CONTEXT.md` **review finding** 词条逐项复述六条；`sub-issues.md` 第 22 行只取 Owns 一条 | glossary 词条是真重复（同一清单）；`sub-issues.md` 是同一边界的另一面 |
| smell baseline 12 条 | `standards-reviewer.md` 第 28–39 行 | `mmw-v2/upstream/docs/engineering/code-review.md` 第 43 行（名字清单）；上游 `CHANGELOG.md` | 文档页是重复（给人看，不装进 host） |
| deletion test | `standards-reviewer.md` 第 22、48 行 | `codebase-design/SKILL.md` 第 65 行；`improve-codebase-architecture/SKILL.md` 第 35 行；上游 docs | 真重复（措辞照抄 `codebase-design`，merge-note 第 35 行明言"全文写在这里"以免 axis 读整份 `codebase-design`）。同文件内第 22 行（判据）与第 48 行（报告时写什么）不再重复：2026-09-28 复审 D2 删掉的第 22 行后半句已不在（已核实） |
| 只在约定 seam 测 / 不追 coverage | `tdd/SKILL.md` 第 22 行；`implement/SKILL.md` 第 30 行 "at pre-agreed seams"；`tests-reviewer.md` 第 52 行 | 上游 `README.md` 第 201 行、`skills/engineering/README.md` 第 21 行、`docs/engineering/implement.md` 第 36 行、`to-spec.md` docs 第 34 行 | `tests-reviewer.md` 的 Coverage 是同一原则的推论（同义）；README/docs 是给人的复述 |
| 六种测试 smell | `tests-reviewer.md` §3 | `tdd/tests.md`、`mocking.md`（前五种的出处）；`tdd/SKILL.md` `## Anti-patterns`（Implementation-coupled、Tautological 又各写一遍）；`CONTEXT.md` **Only the happy path** | `tests-reviewer.md` 只写名字与指针，不抄正文（2026-09-23 汇总第 108 行："改为 `code-review` 直接读 `tdd` 的原文"，已核实）。`tdd/SKILL.md` 与 `tests.md` 之间的重叠是上游自身的 |
| 全量测试禁令 | `implement/SKILL.md` 第 32 行（改为跑仓库点名的测试） | `mmw-v2/prompt/shared.md` 第 47 行 rule 15；上游 `docs/engineering/implement.md` 第 95 行仍写 full suite | 同义（`implement` 的改动就是为与 rule 15 一致，merge-note 第 19 行）；docs 页未同步 |
| 四列 boundary test 的定义 | `writing-interface-code.md` 第 23 行（"asserts `calls`, `shows`, `next` and `on_failure` of one row"）；`tests-reviewer.md` 第 25 行 | `ui-acceptance/references/boundary-check.md` 第 17–19 行（定义之家）；`docs/contexts/ui-acceptance/CONTEXT.md` 第 214 行 | 一句话复述定义（同义），测试选法只住 `boundary-check.md` |
| `DECISIONS` 两节格式 | `implement/SKILL.md` 第 81 行 | `verify-ticket.py` `run_decisions` 的期望标题（第 1347 行）与拒绝文本；`spec-reviewer.md` 第 9 行（读者一方） | 生产者 / 脚本 / 读者三方同名，属交接两端，不是冗余 |
| review report 行格式 | `session.md` 第 82 行 | `verify-ticket.py` `CAT_IN_TICKET_ITEM_RE` 与其拒绝文本；`docs/engineering/code-review.md` 第 37 行；`CONTEXT.md` **review category** | 脚本 regex 是同一格式的机器端；docs 页与 glossary 是复述 |
| `RESUME` 的续跑映射 | `implement/SKILL.md` 第 74 行一句 | `verify-ticket.py` `resume_at`（计算之家）；`merge-notes/implement.md` 第 135 行（映射全文） | 映射只有一份在代码里（已核实）；merge-note 的全文是维护记录 |
| `adopt` 为何必须 | `inside-a-ticket.md` 第 5 行 | `dispatch.sh` 第 925–932 行 `adopt_ticket` 注释；`docs/contexts/night/CONTEXT.md` 第 158 行；ADR 0020 首段 | 同义（注释与 glossary 复述） |
| `land` 会停掉票上点名的所有会话 | `inside-a-ticket.md` 第 13 行；`implement/SKILL.md` 第 99 行 | — | 同一事实两处，读者分支不同（adopt 的会话 / started 的 worker） |
| 夜外单票流程 | `one-ticket.md` | `night.md` 第 3 步唤醒表（contract、watchdog 行被 `one-ticket.md` 引用而非复制） | 不重复（引用） |
| worker 读入与 Spec axis 读法 | `implement` 第 16 行；`spec-reviewer.md` §1 | merge-note code-review 第 16 行："这套读法与 `implement` 的 narrowed reading 是同一套" | 同义规则，两个读者（写的人、审的人）。**不完全一致**：worker 另读 spec 的 Problem Statement 与 Solution（2026-09-28 加），Spec axis 不读 |
| "Under 400 words" | 四个 axis 文件 | SKILL-SET-RULES 第 102 行（以上游 `code-review` 为例） | 同词，规则引用 |
| 人读文档页 | 三技能 | `mmw-v2/upstream/docs/engineering/{implement,code-review,tdd}.md` | 与技能内容大面积同义；implement / code-review 两页有过时句（见 §2.7） |

## 5. 上游差异

总览（上游 = `5b1a4c51`；行/词为全部 Markdown）：

| 技能 | 上游 | 现在 | 上游原句存活 |
| --- | --- | --- | --- |
| implement | `SKILL.md` 15 行 / 70 词，2 个文件 | `SKILL.md` 101 行 / 2727 词 + 2 个 reference（57+54 行，880+308 词） | 只剩 frontmatter 的 `name` 与正文第一句 "Implement the work described by the user in the spec or tickets."（实测逐行比对） |
| code-review | `SKILL.md` 87 行 / 1064 词，2 个文件 | 6 个 Markdown 共 322 行 / 4497 词 | 56 条非空上游行中 15 条逐字存活：frontmatter 两行 + 12 条 smell（实测） |
| tdd | `SKILL.md` 38 行 / 559 词 + `tests.md` + `mocking.md` | `SKILL.md` 38 行 / 648 词；`tests.md`、`mocking.md` 逐字相同；`agents/openai.yaml` 相同 | 除 3 段外全部逐字 |

`mmw-v2/merge-notes/README.md` `## 本仓自有正文的技能`（原文）："`code-review`、`implement`、`to-tickets` … 正文却几乎全是本仓写的。拉 upstream 时不合并上游对这三个技能的改动"。SKILL-SET-RULES `### Upstream skills` 末条："When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text. Its upstream original remains the measure of length"。所以 implement 与 code-review 按本仓自有文本对待，tdd 按上游技能对待。

### 5.1 tdd（逐段，全部已核实 diff）

| 段 | 改动 | 内容类型 | merge-note 条目 | 改能力还是写入 MMW 流程 |
| --- | --- | --- | --- | --- |
| 第 22 行 `**Test only at pre-agreed seams.**` | "confirm them with the user" 改为：约定是写下的东西；带票即 `## Seam`；无票才与用户确认 | 规则 + 分派 | `tdd.md` 第 11 行 | 写入 MMW 流程（无人值守时约定的载体）；方法本身不变，"No test is written at an unconfirmed seam" 保留 |
| 第 26 行 `codebase-design` 指向 | "call the Skill tool with" 改为 "read the `codebase-design` skill's `SKILL.md`" | 分派（hand-off 写法） | `tdd.md` 第 12 行，引 README `## host 中立` | host 中立，不改能力 |
| 第 38 行 **Refactoring is not part of the loop.** | 原 "It belongs to the review stage (see the `code-review` skill)" 改为理由 + 带票（review 后的修复轮）/ 无票（全绿后专门一轮）两个去处 + 区分保持正确与重构 | 规则+理由 | `tdd.md` 第 13 行 | 两者兼有：给无票单用补了去处（改变能力的适用面），带票时写入 MMW 的修复轮 |

### 5.2 implement（本仓自有；按段对应 merge-note）

| 现段 | 类型 | merge-note 条目 | 改能力 / 写入流程 |
| --- | --- | --- | --- |
| frontmatter 删 `disable-model-invocation`，加触发句；`openai.yaml` 删 policy | 分派 | `implement.md` 第 24–25 行 | 改能力（模型可自调） |
| 第 12 行 claim | 顺序 + 命令 | 第 13 行 | 写入流程 |
| 第 14 行 wip | 重入 | `## An earlier worker's unfinished commits` | 写入流程 |
| 第 16 行读入 | 顺序 + 做法 + 规则 | 第 14 行；`## The design package is pulled, not downloaded`；第 17 行（指向 reference） | 主要是写入流程（票字段）；"baseline 是合同"、"只读点名小节"是改变工作方法的规则 |
| 删 "state the seam" | — | 第 15 行 | 写入流程 |
| 第 18 行 fault | 命令 | `## Code-writing rules open sub-issues through --sub-issue` | 写入流程 |
| 第 20–28 行 code-writing rules | 规则+理由 | 第 16 行；`## Put no question on the screen`；`## A file a parallel ticket owns …`；第 18 行（UI 规则迁出） | 改方法（grep 调用方、删被取代的、helper 先找、简化底线是通用写码纪律，来自 ponytail「五句」，Memory `1a5f844b`）+ 写入流程（child 路由） |
| 第 30 行 tdd 交接 + 第一条红测试 | 分派 + 做法 | 第 26 行 | 改能力（补"亲眼看红"这一步，上游 `docs/engineering/tdd.md` 明写有意不加强，故放在调用方）+ host 中立 |
| 第 32 行测试命令 | 做法 | 第 19 行 | 写入仓库规则（rule 15） |
| 第 34 行测试范围 | 规则 | 第 20 行（来源：Anthropic 指南 "Keep changes and tests to what the task asks for"） | 改方法 |
| 第 36–68 行 Shared experience | 命令 + 规则 | 第 21 行（mmw #427） | 写入 MMW 的 Memory 机制 |
| 第 70–101 行 Closing steps | 顺序 + 命令 + 格式 | 第 22–23 行；`## Reaching the two scripts`；`## Waiting on the reviewer carries no number`；`## Closeout pushes …`；`## Integrate before …`；`## A clean-merge regression …`；`## Closing steps: resume after a re-prompt`；`## How the worker learns …`；`## This ticket's sub-issues`；`## The in-ticket round is first …`；`## 草稿落在仓库之外` | 全部写入 MMW 流程；上游只有 "Once done, use /code-review… Commit your work" |
| 标题两个 | 分派 | 第 27 行 | 结构 |
| `writing-interface-code.md` 整份 | 做法 + 命令 | `## writing-interface-code.md`；`## Where a failing story-parity.py criterion is read`；`## Two baselines …`；`## The story criterion is a declared exception …`；`## A DIFF value is checked before it is copied`；`## Every script name says which skill owns it` | 改能力（UI 写码法）并写入 ui-acceptance 流程 |
| `saving-memory.md` 整份 | 命令 + 格式 | 第 21 行 | 写入 Memory 机制 |

merge-note 与现文不一致之处（按 SKILL-SET-RULES `### Upstream skills` "An entry that still states a replaced rule is a finding"）：`merge-notes/implement.md` 第 31 行关于 `Missing` 行 id 与 `--closeout` 的一句（见 §2.7），已核实与现文不符。其余条目逐条对照现文一致（已核实第 13–27 行、各 `##` 节）。

### 5.3 code-review（本仓自有；merge-note 有「哪一段挪去了哪个文件」表）

| 现位置 | 上游来源 | 类型 | merge-note 行 | 改能力 / 写入流程 |
| --- | --- | --- | --- | --- |
| `SKILL.md` 第 8 行目的句 + `## Find your moment` | 上游第 6–11 行开头与流程 | 目的 + 分派 | 第 7、9、29、33 行 | 结构（拆为按读者的文件） |
| `session.md` §1 | 上游第 1 步 | 顺序 + 命令 | 第 15、31 行 | 保留判断；失败也上票（写入流程） |
| `spec-reviewer.md` §1 读法 | 上游第 2 步四级查找 → 换成沿票走 | 做法 | 第 16 行 | 写入流程（票字段） |
| `standards-reviewer.md` §1–2 | 上游第 3 步 + smell baseline | 规则 | 第 17、34 行 | 来源清单收窄为 `CODING_STANDARDS.md` + glossary（改能力：不再读 `CONTRIBUTING.md`、`AGENTS.md`） |
| less-code 问 | 无 | 规则+理由 | 第 18 行 | 改能力（新判断） |
| deletion test | 无（取自 `codebase-design`） | 规则 | 第 35 行 | 改能力 |
| 各 axis §3 Report | 上游第 4 步 brief | 格式 | 第 19、20、36 行 | 保留要点；"Under 400 words" 加理由 |
| 粘贴 smell baseline 进 prompt | 退场 | — | 第 21 行 | 改为 axis 自读文件 |
| `session.md` §5 | 上游第 5 步 + `## Why two axes` | 格式 + 规则+理由 | 第 22、23 行；`## 报告和报信是同一次调用`；`## Review findings carry axis categories and sources` | 落点从"给用户"改为票上 + `--review`（写入流程） |
| `session.md` §3 核实 | 无（来自 BMAD `step-04-review.md` 第 36–40 行） | 做法 + 格式 | `## The session verifies every finding before it sorts` | 改能力 |
| `session.md` §4 分拣 | 无 | 规则 | 第 25 行；`## A file inside Owns is in-ticket` | 写入流程（ADR 0012） |
| `spec-reviewer.md` Decisions 判断 | 无 | 规则 + 格式 | 第 26 行 | 写入流程 |
| `spec-reviewer.md` 已并入票 | 无 | 命令 + 做法 | `## The Spec axis reviews tickets integrated …` | 改能力（语义冲突审查） |
| `spec-reviewer.md` page ticket 三段 | 无 | 做法 | 第 27 行；`## The Spec axis opens the screen contract`；`## … story page and the story adapter`；`## The component a story renders …` | 写入 ui-acceptance 流程 |
| `tests-reviewer.md` 整份 | 无（第三个 axis） | 全部类型 | 第 28、37、38 行；`## 第三个 axis：Tests` | 改能力（新 axis） |
| `ui-reviewer.md` 整份 | 无（试点第四 axis） | 全部类型 | 第 27 行；`## UI axis（试点）`；`## The UI axis and the reaction ticket …` | 改能力（试点） |
| `session.md` §2 能力分支 | 无 | 分派 | `## A host that cannot run subagents` | host 中立（改能力适用面） |
| `session.md` `## Active Rules` | 无 | 规则 | `## Active reviewer Rules stay in the session contract` | 写入 retro→reviewer 的规则机制 |
| axis 命名 | 上游 "sub-agent" | 词汇 | 第 39 行 | 词汇 |

merge-note 与现文不一致：第 102 行（row id 与 closeout，见 §2.7）。`## UI axis（试点）` 第 54 行提到"钉住这些句子的测试"：提交 `e2dab1d7` 与 `11c9798f` 删除了各套件的措辞断言，是否还有测试钉这些句子，本次未查（未确定）。

## 6. 价值证据

「实测」数字来自本仓 tracker 85 张 `mmw:ticket`（有 REVIEW 的 73 张，#336–#589）的评论；另一个 tracker 与 Chameleon 未查。

| 部件 / 段落 | 防的失败 | 证据 |
| --- | --- | --- |
| 收尾第 2 步 DECISIONS 在 reviewer 之前 | worker 替用户做的决定与越界改动无人审 | 用户决定 Memory `9d6755c0`（2026-09-02，已读原文）；2026-09-23 汇总第 41 行：此前"在每张票上都是空的"（已核实原句）。实测：73 条 `DECISIONS` 评论对 73 条 REVIEW；Spec 节中 `reasonable` 30 次、`should not` 8 次（按词计数，近似） |
| `session.md` §3 核实 | axis 误报变成修复工作；真问题被随手撤回 | 实测：73 份报告中 43 份有 `## Withdrawn`，共 38 行撤回条目（2026-09-28 复审说 42 条，计法不同，数量级一致，已核实）；`unverified:` 16 处 |
| 六条 in-ticket 条件中的 Owns 一条 | 票内能修的问题被开成子票，子票循环不收敛 | ADR 0012：#216 夜 38 张子票 27 张（71%）修复目标在本票 Owns 内（原文） |
| Tests axis | 按实现算法重算期望值的测试从写到关票无人怀疑 | 实测 category：Only the happy path 36、Tautological 29、Verified through a side channel 13、Named for the how 4、Implementation-coupled 3、Over-mocked 1；Memory `02fc9cc5`（四种假绿，已读原文） |
| `implement` 第 30 行"第一条红测试" | 测试从未红过、红的原因是缺文件或打错名 | Memory `02fc9cc5`；"流水线没有别的环节证明测试能失败"由代码合读（`tests-reviewer.md` "run no test"、baseline 跑在测试存在之前）。该句加入后是否改变行为：无证据（未跑过验证夜） |
| Standards less-code 与 deletion test | 作者不删自己加的代码 | 实测：`less-code` 50、`pass-through` 5；用户决定 Memory `4756d4d3`（不另立减法评审轴） |
| Standards `documented-standard` | 仓库自己的规则被违反 | 实测 186 条，是最多的一类 |
| "Under 400 words" | axis 报告挤掉 worker 的注意力 | 实测：Standards 73 次中 56 次超过（中位 732，最大 1954）；Spec 47 次；Tests 30 次；UI 7 次均未超。**这是规则未生效的证据**，理由句于 2026-09-28 加入，之后效果未测 |
| Spec axis 已并入票审查（`dispatch.sh integrated`） | 各自通过、合起来错；取错 base 把本票旧版当兄弟票 | mmw #413（merge-note 原文，未到 tracker 复查）；现由脚本 `integrated_since_start` 用 newest base（已核实代码） |
| Spec axis 读 screen contract | 桌面端从不调后端而票 `ALL MET` | Chameleon #549（merge-note，未核实） |
| UI axis | element parity 看不到的装饰与整体观感 | 实测：7 份报告有 `## UI`；类别 `design-page`（旧名）3、`overall-look` 2、`design-page-wrong` 1。试点，证据量小 |
| `## Active Rules` | Memory 或规则被当成 finding 来源 | 生效规则 0 条（2026-09-23 汇总第 121 行，2026-09-28 复审 A 节；本次未重查 nmem）。**无触发证据** |
| `session.md` §2 不能起 subagent 的分支 | 无 subagent 的 host 上 reviewer 无路可走 | spec #374 第 3 节（merge-note）；当前 reviewer 行跑 claude，分支未被走到（复审原文，未重查 `models.json`）。**无触发证据** |
| `session.md` §1 空 diff 也上票 | reviewer 无声结束、worker 永等 | 实测未见触发；可达性依据是 "Green before work" 允许空 diff（复审推理）。**无触发证据** |
| 收尾第 1 步 `integrate` 与两边不能同时成立 → `contract` | 丢掉已落地票的行为，数小时后 `reverify` 才发现 | merge-note 原文："no such incident has been found on record"。**无证据**（机制推理） |
| 第 8 步 clean-merge 回归判断句 | 两票各自绿、合起来红 | merge-note 原文："found no tracker record of this path firing yet"。**无证据** |
| `RESUME:` 续跑 | 被重新提示后不知从哪一步继续 | 实测：`worker.resumed` 字样在评论中出现 19 次；agentflow #916 两次（复审原文，未核实） |
| wip 提交段 | 新 worker 把前任未提交工作当外来改动还原 | 实测：13 条评论出现 `wip(#` |
| `contract` child 与结束回合 | 缺项或矛盾时默默偏离 baseline | 实测：13 个 `contract` child；`night.md` 第 92 行 watchdog 行处理"worker 在等你" |
| `fault` / `decision` / `deferred` / `finding` | 各自的路由 | 实测（按事件块 `kind` 字段，旧名 `review`/`pipeline` 等未计）：`finding` 94、`contract` 13、`fault` 6、`decision` 1、`deferred` 0。**`deferred` 在本仓 tracker 从未触发** |
| 三种 `ABANDON` | 放弃时诚实交回 | 实测：收尾评论 76 条 `ALL MET`、1 条 `HANDOFF REQUIRED`；`ABANDON:` 行共 2 条（`stuck` 1）。几乎未被行使 |
| `refuted:` 回应 | 不修的票内 finding 无依据 | 实测：收尾评论中 27 处 `refuted:` |
| 草稿不落仓库 | 消费仓库的 Markdown 守卫扫到草稿 | agentflow #831（merge-note，未核实） |
| `writing-interface-code.md` Fix in place 与"像素图是证据" | 为 1% 像素阈值改字体、行高 | Chameleon #548 十六轮（merge-note，未核实） |
| One code path | fixtures 喂的 scenario 路径让判据全绿 | Chameleon（merge-note，未核实） |
| story criterion 例外 | 两套纪律冲突无从选择 | #539（merge-note 原文）；无运行证据 |
| 并行票文件的例外 | 两张同时跑的票写同一文件引起合并冲突 | task-board 试点 #541、spec #555（merge-note，未核实）；I5-P4 外部夜 3 张界面票 bounce（线索，未核实） |
| in-ticket 先修再开票外 | 按已被推翻的文字开子票 | #235（merge-note，未核实） |
| tdd 书面 seam | 夜里无人确认 seam，worker 停等或伪造确认 | 实测：85 张票中缺 `## Seam` 的 3 张（#571、#564、#342）均为 `ready-for-human`，agent 票无缺 |
| tdd `Ask:` 一句在带票时可能读成提问 | worker 在 seam 上提问 | 复审推理，**无证据** |
| Memory 查询只用短标识 | Nowledge 对长查询整批不返回 | ADR 0031 "实测这条路径取不回任何东西"（原文） |
| `saving-memory.md` scope 检查 | 路由失败时写进错误 task | 提交 `ab009d42` 加入并测过；该测试文件 `test_memory_skill_commands.py` 在 `60202e94` 被删，现无测试执行这段 bash（已核实 `git log`） |
| `inside-a-ticket.md` | 自拿票的会话 reviewer 叫不醒 | 2026-09-23 汇总第 175 行把"手动接手 `adopt`"列为"路径从未发生"（原文）。**无触发证据** |
| `one-ticket.md` | 夜外单票没人落地 | 本次未查 `open-ticket` 事件实例。**未确定** |

## 7. 约束

| 约束 | 出处 | 约束了什么 |
| --- | --- | --- |
| 规则写成动作 + 票字段；理由句只在能改变清单外情形的选择时写，贴在它管的规则旁 | `merge-notes/implement.md` 第 16 行（2026-09-28 改写）；SKILL-SET-RULES fact 1、`## Editing` 第一条 | code-writing rules 的写法；第 22、23 行理由句 |
| 上游 `implement` 五句、MMW 每加一段须由 agent 做不出的判断付费 | SKILL-SET-RULES fact 4、`### Upstream skills` 末条 | implement 与 code-review 的体量衡量基准 |
| 能由脚本判定的交给脚本；文字不复述脚本 | SKILL-SET-RULES fact 2、`### Scripts and judgement` | 续跑表移进 `--preflight`；`Counts:` 与首行由 closeout 自算；退出码在 `--help` |
| 一处一家；axis 自己读文件而不是被粘贴 | SKILL-SET-RULES fact 7、`### Prompts written for other agents`；`merge-notes/code-review.md` 第 21 行 | reviewer prompt 只一句；Tests axis 按名字读 `tdd` 文件 |
| 按分支渐进加载 | SKILL-SET-RULES fact 5、`### Load and disclosure` | `writing-interface-code.md`、`saving-memory.md`、各 axis 文件拆出；session.md 单独一份 |
| host 中立，按能力写 | SKILL-SET-RULES `### Paths and host neutrality`；`merge-notes/README.md` `## host 中立` | "read the `tdd` skill's `SKILL.md`"；`session.md` §2 能力分支 |
| 描述只写触发 | SKILL-SET-RULES `### Descriptions` | 三个 description |
| 上游技能只在改变行为时改，逐段有 merge-note | SKILL-SET-RULES `### Upstream skills`；`merge-notes/README.md` | tdd 只改 3 段；`tests.md`/`mocking.md` 不动 |
| 三技能中 implement、code-review 正文为本仓自有，不合并上游 | `merge-notes/README.md` `## 本仓自有正文的技能` | 拉上游时的取舍 |
| `disable-model-invocation` 两处同增同删 | `merge-notes/README.md` `## disable-model-invocation` | implement 两处一起删 |
| subagent 的 brief 写明返回物与长度 | SKILL-SET-RULES `### Prompts written for other agents` 第 3 条 | "Under 400 words" 保留 |
| 闸口拒绝要点名事实、给唯一出路 | ADR 0008 | 技能不复述拒绝的下一步（第 8 步、`--draft`、`--decisions`） |
| agent 不互相轮询，由事件唤醒 | ADR 0010 → 0013 → 0020（relay） | 第 3 步起 reviewer 后结束回合；无等待数字（merge-note `## Waiting on the reviewer carries no number`）；reviewer "Hold this turn" |
| 报告落地与报信同一次调用 | ADR 0013（机制被 0020 取代，原则保留在 `--review`） | `session.md` 用 `--review` 而非 `gh issue comment` |
| 票的状态是事件折叠 | ADR 0019 | `RESUME:` 从事件计算；wip 与 `worker.started` |
| 不交付自定义 subagent，用 host 通用 subagent | ADR 0015 | `session.md` §2 "one of your host's general-purpose subagents"、不指定模型 |
| 取消 verifier，worker 做 final run，closeout 核验 | ADR 0026 | 第 4 步；不另起验证角色；UI axis 不另起 verifier（merge-note code-review 第 54 行） |
| 第一次 bounce 交回 worker、不再起 reviewer | ADR 0027 | `RESUME:` "step 1, then step 4 onward" |
| review finding 路由；不定严重度 | ADR 0012 | `session.md` §3 "you do not assign severity"；§4 Owns 条件 |
| 组件级 story，退役词 | ADR 0011 | spec-reviewer page ticket 段不提 `--mount` 等退役词（merge-note 第 116 行） |
| design package 只由 pull 写 | ADR 0029 | 读入段 "a design package pulled into the repository"；`writing-interface-code.md` 不改 design package |
| worker 开工 Memory 是有上限的索引 | ADR 0031 | `## Shared experience while implementing` |
| 用户决定：DECISIONS 评论先于 review，由 reviewer 判 | Memory `9d6755c0` | 收尾第 2 步、Spec axis Decisions |
| 用户决定：减法检查不另立评审轴 | Memory `4756d4d3` | less-code 放在 Standards axis |
| 用户决定：规则唯一出处（代码在 implement、测试在 tdd、审查在 code-review 各 axis、仓库代码规则在 `CODING_STANDARDS.md`→Standards、测试规则在 `TESTING.md`→Tests） | 2026-09-23 汇总 `## 八` "规则的唯一出处"；Memory `0ac93ab8` | standards/tests-reviewer 的来源清单 |
| 用户决定：reviewer Rules 送不到 axis 的问题"以后启用规则时再修" | 2026-09-23 汇总第 121 行 | `## Active Rules` 现状 |
| 用户级 rule 15：默认禁止全量测试 | `mmw-v2/prompt/shared.md` 第 47 行 | `implement` 第 32 行 |
| 词汇 recheck：`review report`、`code-writing rules`、`save conditions`、`semantic-conflict angles`、UI 类别名 | `docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` T17、T19、T21–T23 | 现文用词（已核实现文用新名） |
| Self-hosting boundary | 根 `AGENTS.md` | 本仓夜里运行的是 installed checkout 的这些技能，改它们不影响正在跑的夜 |

## 8. 天然整体

1. **`implement` 收尾八步 + `ABANDON` 三种 + 第 74 行续跑句**（第 70–101 行）。顺序由脚本定死：`--decisions` 只接受一次且必须在 reviewer 之前（Spec axis 要逐行判）；`--touched` 读 review 的 Spec 节；final run 必须在最后一个写 commit 的步骤之后，closeout 只认 HEAD 上 actor 为 worker 的最新 reverify；`--draft` 后 `--closeout`。`RESUME:` 的步骤号指向这八步的编号。`ABANDON` 定义被第 1、4、7 步引用。拆开会让编号引用与脚本条件失去对应。
2. **code-writing rules 七条**（第 20–28 行）。修复轮也受它们管（第 84 行 "under the code-writing rules that governed the first write"），`sub-issues.md` 第 23 行按 bullet 名反指。它们是一次读入、整轮写码都适用的一组，按条拆会产生多次跳转。
3. **`session.md` §1–§5**。单一读者每次全读；§3 的三种结论决定 §4 分拣的输入与 §5 的 `## Withdrawn`、`unverified:`；§5 的格式被 `verify-ticket.py` 的 regex 读。merge-note 第 9 行："`references/session.md` 从头到尾只有 reviewer 一个读者，而且它每次都要读全"。
4. **`spec-reviewer.md` §1 读法 ↔ `session.md` §4 六条件**。merge-note code-review 第 25 行原文："baseline、`## Out of Scope`、`## Testing Decisions` 三条与 `references/spec-reviewer.md` 第 2 节让 Spec axis 读它们是一对，拆开做无效"。跨两个文件的整体。
5. **DECISIONS 三方格式**：`implement` 第 2 步（写）、`spec-reviewer.md` §1/§2 的 `Decisions` 行（判，路径与判断词同一行）、`verify-ticket.py` `run_decisions` / `spec_judgement`（机读）。改其中一方，另两方失效。
6. **review report 格式**：`session.md` §5 行格式 ↔ `verify-ticket.py` `CAT_IN_TICKET_ITEM_RE` / `review_finding_problems` ↔ `implement` 第 7 步 `Review findings:` 的 `fixed`/`refuted:` 回应 ↔ `retro` 读 category。
7. **smell baseline 12 条 + 两条约束**（`standards-reviewer.md` §2）。上游整块；两条约束（repository overrides、judgement call）同时管 less-code 与 deletion test。
8. **Tests axis §3 ↔ `tdd/tests.md`、`mocking.md`**。形状名就是 review category；前五种只有指针，内容在 `tdd`。改 `tdd` 小节名须同改 §3（`merge-notes/tdd.md` 第 19 行）。跨技能整体，且有意不复制。
9. **`writing-interface-code.md` 整份**。一个分支（page ticket）一次读全；`## Fix in place` 与 `## When the design side is the defect` 的先后有意义（先判设计值再复制，merge-note `## A DIFF value is checked before it is copied`）；story criterion 例外依附 `tdd` 的 Horizontal slicing。
10. **`tdd/SKILL.md` 整份**。上游有意做成每个循环都查的参考（第 8 行 "Every section applies on every cycle"），`writing-interface-code.md` 与 `tests-reviewer.md` 都按其中的名字引用。
11. **`saving-memory.md` 命令块**。一段要逐字执行的 bash（scope 检查、标签、五项正文），部分拆出就不能运行。
12. **`refuted` 一词**跨 `implement` 第 3 步与 `session.md` §3：同一判断一个名字，两份各给自己的读者（merge-note code-review 第 175 行）。
13. **`inside-a-ticket.md`** 三段：adopt、退出码、夜外关票后。只有自拿票分支读，三段在同一次会话里依次用到。
14. **`one-ticket.md` 四步**：一个完整的编排循环（开 watch、起 worker、处理唤醒、`land`），与 `night.md` 共享唤醒处理但以引用方式。

## 9. 线索材料核实情况

| 线索结论 | 出处 | 核实结果 |
| --- | --- | --- |
| implement 收尾有续跑表 | M3 §5 第 2 条、§2 | **已过时**：表已移进 `--preflight` 的 `RESUME:`（`verify-ticket.py` 第 2226 行；`SKILL.md` 第 74 行） |
| Audit 追到每条最新 `EVIDENCE:` | M3 §2 第 11 行；I3「Audit、--touched 与 closing draft」 | **已过时**：现为对着分支按用户读法再读票（`SKILL.md` 第 90–92 行） |
| `session.md` 标题 "Write one review comment on the ticket" | M3、I3 | **已过时**：现为 "Write one review report on the ticket"（vocabulary T19） |
| start exit 2 按 stderr 再起一次，否则 fault | M3 §2 第 8 行 | 已核实（`SKILL.md` 第 84 行） |
| 72 条 REVIEW、Standards 56 次超 400 词、43 条有 Withdrawn | 2026-09-28 code-review 复审 A1、B | 已核实（实测 73 条、56 次、43 份；中位数计法不同） |
| `test_memory_skill_commands.py` 执行 `saving-memory.md` 的 bash | 2026-09-28 implement 复审 A10 | **已过时**：该测试在 `60202e94` 删除 |
| `review_problems` 按 row id 拦 closeout | 2026-09-28 implement 复审 A11 | 已核实已删除；但 `spec-reviewer.md` 与两份 merge-note 仍写这个理由（§2.7） |
| `implement` 仍写 `/tdd` | Memory `0f2c3a8d`（2026-09-22） | **已修**：现为 "Read the `tdd` skill's `SKILL.md`" |
| 84 张票里只有 3 张 `ready-for-human` 缺 `## Seam` | 2026-09-28 tdd 复审 | 已核实（85 张，同 3 张） |
| `tests.md`、`mocking.md` 与上游逐字相同 | 2026-09-28 tdd 复审 | 已核实（`diff` 无输出） |
| 2026-09-28 复审各"定稿"条目已落地 | 各复审文件 `## 定稿` | implement I1–I14、D1–D9 与 code-review I1–I7、D1 已在现文找到（逐条对照）；code-review D2（删 deletion test 半句）、D3 已落地；tdd I1、I2 已落地 |
| 154 张 agent 票都有 Seam、66 条 `mmw-experience` | `merge-notes/implement.md` 第 13、21 行；`tdd.md` 第 11 行 | 未核实（含另一个 tracker） |

## 10. 未确定

- 另一个 tracker（agentflow）与 Chameleon 的 review、child、ABANDON 数据未查；§6 的实测只代表本仓 85 张票。
- 当前生效的 reviewer Rules 数与 `~/.mmw/models.json` 的 reviewer 行未重查（沿用 2026-09-23/28 的原文）。
- `one-ticket.md` 与 `inside-a-ticket.md` 在实地是否被走过（`open-ticket`、`adopt` 事件实例）未查。
- 是否仍有测试钉住 `session.md` 或 `ui-reviewer.md` 的句子（merge-note code-review 第 54 行提到）未查。
- `ticket.bounced` 在评论中出现 57 次，是字符串计数，包含提及而非事件本身，未用作证据。
- `verify-ticket.py` 与 `dispatch.sh` 只读了上文列出的函数与注释；关于它们其余行为的陈述来自 `--help`、注释与线索材料。
- 2026-09-28 加入的理由句（第 22、23 行、`SKILL.md` 第 8 行、`tests-reviewer.md` 第 5 行、`session.md` §3 开头等）是否改变了 agent 行为：没有验证夜，无证据。
