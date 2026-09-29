# N10 MMW 的路由、description 与交接图（routing, descriptions, hand-off graph）

本单元只做事实清点：一个 agent 从「用户说了一句话」或「脚本启动了我」出发，靠什么机制走到哪个技能的哪个时刻；哪里断开、哪里重复；引入 mode 路由技能与 `SKILL-SET-RULES.md` 事实 7 的关系。不做归置决定。

## 0. 读了什么、怎么核实

- 安装清单：`mmw-v2/skills.txt` 全文。**实际是 35 个技能行，不是任务描述里的 34 个**（`grep -vcE '^#|^$' mmw-v2/skills.txt` 输出 35：engineering 17、productivity 7、self 10、dd 1）。
- 35 个 `SKILL.md` 的 frontmatter 全部读过；24 个上游技能的 `agents/openai.yaml` 全部读过；与最近一次上游 squash 提交 `5b1a4c51`（`git log --format=%H --grep "Squashed 'mmw-v2/upstream/'" -1`）逐个比对了 frontmatter 与行数。diagram-design 与它自己的 squash 提交 `8a85636a` 比对。
- 全文读过的 `SKILL.md`：`dispatch`、`design-pages`、`ui-acceptance`、`verify-ticket`、`code-review`、`advisor`、`implement`、`to-spec`、`grill-me`、`grilling`、`grill-with-docs`、`handoff`、`wait-what`、`research`、`resolving-merge-conflicts`、`prototype`、`tdd`。只读了开头与结尾（入口、分派表、下一步）的：`to-tickets`（1–31、111–206 行）、`triage`（1–24、47–116）、`wayfinder`（1–20、72–128）、`improve-codebase-architecture`（1–17、62–75）、`wizard`、`setup-matt-pocock-skills`、`diagnosing-bugs`（1–12、114–138）、`write-screen-contract`（1–26、75–121）、`retro`（1–50、148–210）、`exe-release`、`code-checkers`、`manage-agents-md`（1–30、297–330）。其余技能正文与本单元无关，没读。
- reference：`dispatch` 的 `references/inside-a-ticket.md`、`one-ticket.md`、`night.md` 全文；`design-pages` 的 `references/pull.md` 15–45 行、`edit-pages.md` 25–40 行；`prototype` 的 `UI.md` 100–125 行、`LOGIC.md` 与 `EXP.md` 末段。
- 脚本：`dispatch.sh` 读了文件头注释（1–107 行）、`--help` 输出、`start` 的提示词拼装（1925–2080 行）、Memory 索引与 reviewer Rules 两段提示词（1720–1745、1825–1836 行）；没有逐行读其余约 4500 行。`relay.py` 读了文件头（1–80）、`WAKES`（291–299）、`wake_text`（385–389）。`watchdog.py` 读了告警格式（74–110）。`turn-guard.py` 读了文件头（1–45）与阻断消息（296–311）。`tool-guard.py` 读了文件头（1–40）。
- 约束材料：`SKILL-SET-RULES.md` 全文；`SKILL-MECHANICS.md` 的 `## Invocation`、`## Splitting by invocation`、`## Router skills`；上游维护者规则 `mmw-v2/upstream/.agents/invocation.md` 全文与 `mmw-v2/upstream/CLAUDE.md` 1–25 行；`mmw-v2/merge-notes/README.md` 全文；各 merge-note 中与 frontmatter、结尾段有关的行（`grep` 定位后读）；ADR 0003、0010、0014、0015。
- 提交：`06163a0f`（删除 ask-matt）全文 diff；`c9f4e5c7`、`5181acc2`、`2b92efe3`、`19a85c2c` 的提交说明。
- Memory（`nmem --json m search`，再 `m show` 读全文）：`411750f5`、`ce037679`、`f4c3d378`、`fe94802d`、`8ec53374`、`756fc056`、`d4f9f347`、`81134d05`、`90018687`、`c155ffc2`。四个指定查询里「互调只写名字」没有直接命中，内容由 `ce037679` 覆盖。
- 线索材料（只作线索，采用处都回原文核实，逐条标注）：`docs/reviews/2026-09-28-lightweight/ask-matt.md`、`汇总.md`；`docs/reviews/2026-09-23-skill-set/汇总.md`；`docs/research/workflow-compare/reports/M1-mmw-front.md`、`M2`、`M3`、`L1-pstack-mode-and-short-playbooks.md`；`docs/research/mmw-structure/2026-09-06-handoff.md`。
- 实地使用证据：本会话对 `~/.claude/projects/**/*.jsonl` 做了 `grep` 计数（见第 6 节，口径有限）。Codex、Grok、Pi、Cursor 的会话记录没有查。
- 已安装版本与所读版本一致：安装目录 `.worktrees/mmw-installed` 在 `61f1065c`（= `main`），当前 `dev` 在 `f2ba7593`；两者之间 `mmw-v2/skills`、`mmw-v2/upstream/skills`、`skills.txt`、`merge-notes` 没有差异（`git diff --stat` 为空）。

## 1. 部件清单

| 部件 | 是什么 | 给谁用、何时 |
| --- | --- | --- |
| `mmw-v2/skills.txt` | 安装清单，35 行，决定哪些技能进 host 的技能列表 | `install.sh` 安装时；host 启动时看到的列表由它间接决定 |
| 35 份 `SKILL.md` frontmatter | `name`、`description`，7 份另有 `disable-model-invocation: true`，`handoff`/`teach`/`wait-what` 有 `argument-hint`，`diagram-design` 有 `license`、`metadata` | host 启动时扫入系统提示（`AGENTS.md` `## Key Conventions`：「only the frontmatter `description` is scanned at host start and needs a new session」）；模型据此自动加载；人读斜杠列表 |
| 24 份 `agents/openai.yaml`（只有上游两个 bucket 有） | Codex 的界面元数据 `interface.display_name`、`short_description`；7 份有 `policy.allow_implicit_invocation: false` | Codex host；本仓自写的 10 个技能没有这份文件（`SKILL-SET-RULES.md` `### Descriptions` 第 4 条） |
| `## Find your moment` 表（5 个技能：`dispatch`、`design-pages`、`ui-acceptance`、`verify-ticket`、`code-review`）及同类表：`advisor` 无标题的两行表、`manage-agents-md` `## Find your situation`、`prototype` `## Pick a branch`（上游列表形式）、`dispatch` `references/night.md` 开头的事实表 | 技能内部的分派表：按角色或处境把读者送到一个 reference | 加载了该技能的 agent，在任何有副作用的步骤之前 |
| 结尾段（「下一步」） | `to-spec` `## Next`；`write-screen-contract` `## Next`；`design-pages` `references/edit-pages.md` `## Next` 与 `references/pull.md` `## Reached from here`；`prototype` `UI.md` `## Next`；`to-tickets` 第 8 步末句；`wayfinder` `### Work through the map` 第 6 步；`improve-codebase-architecture` `### 4. Hand the decision on`；`grill-with-docs` 第 7 行末句；`verify-ticket` `## Reached from here`；`implement` 第 8 步；`retro` 第 186 行 `Done when`；`dispatch` `references/inside-a-ticket.md` `## After the closeout`、`one-ticket.md` 第 4 步、`night.md` `## 5`、`## 6` | 刚做完本技能工作的 agent |
| `dispatch.sh` 提示词拼装 | `AUTONOMOUS`、`PRODUCT_RULES` 两个常量（108–109 行）；worker 提示词 `Use the implement skill to work ticket #$number.`（1949 行）；reviewer 提示词 `Use the code-review skill to review ticket #$number from base commit $base.`（1967 行）；Memory 索引尾句（1740 行）；reviewer Rules 包（1833 行）；advisor 提示词 `Use the advisor skill.` + 简报文件（2072 行） | runner 启动的新会话的第一条消息 |
| `dispatch.sh` 文件头注释与 `--help` | 子命令清单与行为说明 | 维护者（头注释）；agent（`--help`、拒绝信息） |
| `relay.py` `WAKES` 与 `wake_text` | 哪个事件叫醒谁；叫醒消息的文字只有 `#<n> <event>` 或 `relay.recovered since <time>` | worker 会话与 orchestrator 会话，由 runner 的 `send` 投递 |
| `watchdog.py` 告警行 | `watchdog: …` 开头的一行消息，直接投给 orchestrator | orchestrator 会话 |
| `turn-guard.py` 阻断消息 | `MMW turn guard: …`，orchestrator 回合结束时由 host 的 Stop 钩子注入 | orchestrator 会话 |
| `tool-guard.py` | PreToolUse 钩子：拒绝 `gh issue close`、拒绝向屏幕提问、拒绝结束进程，并说明问题该去哪里 | `issue-<n>` worktree 里的 worker 与 reviewer |
| `SKILL-SET-RULES.md` 事实 7（17 行）、`### Descriptions`（65–70）、`### Hand-offs`（84–96）、`### Prompts written for other agents`（98–102）、`### Load and disclosure`（23–34） | 本仓技能文本规则的唯一归属 | 写、改、复审技能的 agent |
| `SKILL-MECHANICS.md` `## Invocation`、`## Router skills` | 上游原文（与 `5b1a4c51` 无差异）：两种调用方式的取舍；路由技能是用户触发、只能提示 | 写技能的 agent |
| `mmw-v2/upstream/.agents/invocation.md` | 上游仓库维护者规则：用户触发的技能「no other skill can」调用；技能互调写成「Call the Skill tool with …」 | 上游维护者；本仓 agent 不加载 |
| `mmw-v2/merge-notes/README.md` `## disable-model-invocation`（18–24 行） | 两处开关同增同删；上游技能默认模型可触发；保留用户触发的 7 个名单 | 拉上游的维护者 |
| 提交 `06163a0f` | 把 ask-matt 移出 `skills.txt`，删掉它的 merge-note | 历史记录 |
| 残留目录 `mmw-v2/upstream/skills/engineering/ask-matt/` | 未安装；`SKILL.md` 96 行（上游 90）、`PHASE-BOUNDARIES.md`、`agents/openai.yaml` 仍带本仓改动 | 无人加载；下次拉上游时会被合并 |
| `mmw-v2/prompt/shared.md` | 用户级提示词，常驻四个 host；不点名任何技能，第 11 行把无人会话的提问和汇报交给「its skills」 | 每个会话 |
| Memory 记录 | 用户对调用方式的历次裁定 | 下一轮决策 |

## 2. 内容分类表

「读者/时刻」一栏说明谁在什么时候读、每次都读还是只在某个分支读。

| 段落 | 类型 | 读者/时刻 |
| --- | --- | --- |
| 28 个模型可触发技能的 `description` | 重入与分派（触发条件）；首句兼目的与立场（「是什么」） | host 每次启动扫入；模型每轮挑技能时都在上下文里 |
| 7 个用户触发技能的 `description` | 目的与立场（给人看的一行摘要） | 人在斜杠列表里看；Claude Code 上模型看不到（本会话可用技能列表里恰好缺这 7 个，已核实） |
| `disable-model-invocation` 与 `policy.allow_implicit_invocation` | 命令与接口（host 配置字段） | host 启动时 |
| `openai.yaml` `interface` 块 | 格式与模板（Codex 界面） | Codex 上的人 |
| `dispatch` 第 8 行「Choose the moment … Where you are is what the ticket's events say, not what this session remembers」 | 带理由的规则 | 每个加载 `dispatch` 的 agent，每次 |
| `dispatch` `## Find your moment` 的 night 定义句与 6 行表 | 重入与分派；第 6 行内联命令与退出码（命令与接口） | 每次；之后只读自己那一行 |
| `dispatch` `## On waking` 4 步 | 顺序 + 命令与接口（`ack`）+ 带理由的规则（「Until you ack it, the relay sends the same wake again」） | 每个被叫醒的会话；worker 走第 1 行时不被指到这里（见第 4 节 D7） |
| `design-pages` 开头两段 | 目的与立场（「a page that is wrong in the repository becomes a wrong product」） | 每次 |
| `design-pages` 表 | 重入与分派 | 每次 |
| `design-pages` 第 21 行「Only a session whose host has the Claude Design MCP tools …」 | 带理由的规则（按能力分流：没有工具就停下告诉用户） | 每次 |
| `design-pages` `## The state list` | 做法（指向 state list 的位置） | 分支 |
| `ui-acceptance` 开头三段 | 目的与立场（「these oracles are the only eyes on a UI」）+ 定义（product under test、oracle） | 每次 |
| `ui-acceptance` 表 9 行 | 重入与分派；第 7–9 行内联命令（命令与接口）；第 1、3 行把读者送回 `implement`、`to-tickets` 的 reference | 每次 |
| `ui-acceptance` `## Five rules while the product is running` 与末段 | 带理由的规则 + 命令与接口（阻塞经事件上报） | 每个运行产品的会话；`dispatch.sh` 的 `PRODUCT_RULES` 也把 worker 指到这里 |
| `verify-ticket` 开头三段 | 目的与立场 + 命令与接口（事件评论格式、`PATH`） | 每次 |
| `verify-ticket` 第 16 行「A worker's claim, criteria runs and closeout are steps of the `implement` skill.」 | 重入与分派（把 worker 送回 `implement`） | 每次 |
| `verify-ticket` 表与 `## Reached from here` | 重入与分派 + 带理由的规则（五条规则约束本技能每次运行） | 分支 |
| `code-review` 第 8 行 | 目的与立场（「what it misses ships」） | 每次 |
| `code-review` 表 | 重入与分派：按启动提示词里有没有 axis 名分两扇门 | 每次 |
| `advisor` 表 | 重入与分派 | 每次 |
| `night.md` 第 13–22 行事实表 | 重入与分派（「first row whose fact holds」） | orchestrator 每次进入或被叫醒 |
| `night.md` `### 3` 表 | 重入与分派（按事件选动作）+ 带理由的规则 | orchestrator 被叫醒时 |
| `one-ticket.md` 第 3 步事件清单 | 重入与分派 | night 之外的 orchestrator 被叫醒时 |
| `to-spec` `## Next`、`to-tickets` 第 8 步末句、`grill-with-docs` 末句、`prototype` `UI.md` `## Next`、`design-pages` `edit-pages.md` `## Next` | 顺序（点名下一个技能） | 各自完成时，每次 |
| `write-screen-contract` `## Next`、`design-pages` `pull.md` `## Reached from here` | 重入与分派（按有没有 map、有没有 screen contract、`改动分类` 分三到四支） | 完成时，按分支 |
| `wayfinder` 第 6 步 | 顺序 + 带理由的规则（map 不关，是决定的索引；新会话跑 `to-spec`） | 清图那一次 |
| `improve-codebase-architecture` `### 4` | 带理由的规则（「refactoring here would skip the tickets and the acceptance checks」）+ 顺序 | 用户确认候选后 |
| `implement` 第 8 步「Open no pull request: the orchestrator lands the ticket」 | 带理由的规则（返回调用方） | 每个 worker 收尾时 |
| `retro` 第 186 行 | 顺序（回到 `night.md` `## 5`） | 每次 retro 结束 |
| `inside-a-ticket.md` `## After the closeout`、`one-ticket.md` 第 4 步 | 顺序 + 命令与接口（`land`） | night 之外的分支 |
| `dispatch.sh` `AUTONOMOUS` | 带理由的规则（「cannot answer questions mid-task … will block the work」） | worker 与 reviewer 首条消息，每次 |
| `dispatch.sh` `PRODUCT_RULES` | 重入与分派（指向 `ui-acceptance` 的一节）+ 一句理由 | worker 首条消息，每次 |
| worker、reviewer、advisor 的首句 | 命令与接口（数据：技能名、票号、base commit） | 各自首条消息 |
| Memory 索引尾句「the implement skill's `## Shared experience while implementing` says how to use them」 | 重入与分派 | worker 首条消息 |
| `relay.py` `wake_text` | 命令与接口 | 被叫醒的会话 |
| `SKILL-SET-RULES.md` 事实 7 | 带理由的规则；「this is why MMW ships no router skill」一句是维护者对一个设计的理由（按同文件 `### Redundancy and bloat` 的 Sediment 表，这类句子的家是 ADR，推断属沉积） | 写或复审技能的 agent |
| `SKILL-SET-RULES.md` `### Descriptions`、`### Hand-offs` | 带理由的规则 | 同上 |
| `merge-notes/README.md` `## disable-model-invocation` | 带理由的规则 + 数据（7 个技能的名单） | 拉上游的维护者 |
| 提交 `06163a0f` 说明 | 沉积（按性质就是历史） | 查历史的人 |
| 残留 ask-matt `SKILL.md` 与 `PHASE-BOUNDARIES.md` | 原为重入与分派 + 目的与立场 + 带理由的规则；现在未安装，整体属沉积 | 无 |

## 3. 连线：当前的路由与交接图

### 3.1 八种到达机制

| 代号 | 机制 | 覆盖面 | 出处 |
| --- | --- | --- | --- |
| M1 | description 自动触发 | 28 个模型可触发技能 | frontmatter；`SKILL-SET-RULES.md` `### Descriptions` |
| M2 | 用户斜杠 | 35 个都行；7 个用户触发技能只能靠它 | `merge-notes/README.md` 第 20–22 行 |
| M3 | 技能正文点名另一个技能（「Read the `X` skill's `SKILL.md`」「the `X` skill」「`/X`」） | 见 3.3 的 edges | `SKILL-SET-RULES.md` `### Hand-offs` 第 95 行；Memory `ce037679` |
| M4 | 脚本拼的启动提示词 | `implement`（worker）、`code-review`（reviewer 与 axis）、`advisor` | `dispatch.sh` 1949、1967、2072 行 |
| M5 | 事件唤醒进已有会话 | worker：`reviewer.reported`、`reviewer.lost`、`worker.queued`；orchestrator：`ticket.passed`、`ticket.returned`、`ticket.refused`、`child.opened`（`contract`/`fault`/`decision`）、`worker.lost`、`relay.recovered`；另有 `watchdog:` 告警与 `MMW turn guard:` | `relay.py` `WAKES`；`watchdog.py` 74–110；`turn-guard.py` 306 行 |
| M6 | 技能内的 Find-your-moment 表 | 进入技能后选 reference | 第 1 节 |
| M7 | 钩子拒绝并改道 | worker 想提问 → 改为记默认或开 `decision` 子票；`gh issue close` → `--closeout` | `tool-guard.py` 文件头 |
| M8 | 常驻用户级提示词 | 只一句：无人会话的提问和汇报「goes where its skills route questions」 | `mmw-v2/prompt/shared.md` 第 11 行 |

**唤醒消息不带技能名。** `wake_text` 只发 `#<n> <event>`（`relay.py` 385–389 行：「nothing the tracker already says」）。收到它的会话靠自己上下文里已经加载的 `dispatch`/`implement` 知道怎么办。`watchdog:` 与 `MMW turn guard:` 同样不点名技能（后者点名了 `watchdog.py arm` 命令与 `fault` 子票）。

### 3.2 从起点到时刻

| 起点 | 机制 | 到达 | 时刻 | 出处 |
| --- | --- | --- | --- | --- |
| 用户在工作目录里有一个想法，想把它做出来 | 无模型可达的入口。用户需自己打 `/grill-with-docs`（用户触发）；或说出「grill」触发 `grilling`；或说「test-first」触发 `tdd` | `grill-with-docs` → `grilling` + `domain-modeling` → `to-spec` | 访谈 | 见第 4 节 B1 |
| 巨大、看不清路线的目标 | M1（`wayfinder` 的 description 含「Use when the way … is not visible yet」）或 M2 | `wayfinder` `### Chart the map` 或 `### Work through the map` | 按有没有 map | `wayfinder` 102–128 行 |
| 外来 issue 或被退回 `needs-triage` 的票 | M1 或 M2 | `triage` → `to-spec` → `to-tickets` | `## Triage a specific issue or PR` 第 5 步 | `triage` 76 行 |
| 需要可运行的答案 | M1（`prototype` 三类触发）或 M3（`wayfinder` 的 prototype 票） | `prototype` 的 `LOGIC.md`/`UI.md`/`EXP.md` | `## Pick a branch` | `prototype` 10–18 行 |
| UI 胜出方案 | M3（`UI.md` `## Next`） | `design-pages` → `edit-pages.md` → `pull.md` → `write-screen-contract` → `to-spec` | 链上每跳由生产方结尾段点名 | 第 1 节「结尾段」一行 |
| 已有对话要成 spec | M1（`to-spec` 四支触发）或 M3 | `to-spec` → `to-tickets` → `dispatch` | `to-spec` `## Next`；`to-tickets` 160 行 | 已核实 |
| 用户说「今晚跑 spec #N」 | M1（`dispatch`：「run a night as its orchestrator」） | `dispatch` 表第 3 行 → `night.md` 事实表 | `## 1` 至 `## 6` | `dispatch` 18 行 |
| `advance` 启动 worker | M4 | `implement` | `## Claim, read in, write the code`；再次唤醒回到 `## Closing steps` 的 `RESUME:` 行 | `dispatch.sh` 1949 行；`implement` 74 行 |
| worker 第 3 步 `start <n> reviewer` | M4 | `code-review` 表第 1 行 → `references/session.md`；axis 子代理走第 2 行 | 由提示词里有没有 axis 名决定 | `code-review` 14–15 行 |
| reviewer 报告写上票 | M5 → worker | `implement` 第 3 步 | `#<n> reviewer.reported` | `relay.py` `WAKES` |
| worker `--closeout` | M5 → orchestrator | `night.md` `### 3` | `ticket.passed`/`ticket.returned` | 同上 |
| 自己接手一张票 | M1（`implement`：「or picked one up yourself」）| `implement` 第 12 行 → `dispatch` `references/inside-a-ticket.md`（`adopt`） | 认领前 | 已核实 |
| `summary` 记下 `spec.closed` | M3（`night.md` 186 行）与 M1（`retro` description 以同一事件为触发） | `retro` → 回 `night.md` `## 5` | | 已核实 |
| 撞上一个决定 | M1（`advisor`） | `advisor` `references/consulting.md` → `dispatch.sh advise` → M4 → 另一会话 `advisor` 第 2 行 | | `advisor` 表 |
| 写页面票代码之前 | M1（`ui-acceptance`：「before writing a page ticket's code」） | `ui-acceptance` 表第 1 行 → 送回 `implement` 的 `references/writing-interface-code.md` `## Before the first line` | | 见第 4 节 B7 |
| 发包 | M1（`exe-release`） | `exe-release` 第 1–5 步 | | 结尾是用户安装实测，不点名下一步 |
| 会话要换 host 或交给他人；上下文要清空或压缩 | M2（`/handoff`）或 host 自带命令 | `handoff` | | 没有任何已安装技能点名 `handoff`（见 B5） |

### 3.3 edges

关系词：calls（点名另一技能做它的活）、hands-off-to（结尾段点名下一步）、runs-script、reads、writes-event、wakes、cites、configured-by、re-enters-at（被送回另一技能的某个时刻）。自拟五个：triggers-by-description（host 扫 description 后模型自动加载）、invoked-by-slash（只能由用户斜杠）、starts-with-prompt（脚本以首条消息点名技能启动会话）、refuses-and-redirects（钩子拒绝一个动作并说明去处）、removes-ask-matt（06163a0f 从安装清单删去 ask-matt）。`design-pages -> design-pages : re-enters-at` 指 `edit-pages.md` `## Next` 送到同技能的 `pull.md`。

```edges
skills.txt -> host : configured-by
host -> code-review : triggers-by-description
host -> codebase-design : triggers-by-description
host -> diagnosing-bugs : triggers-by-description
host -> domain-modeling : triggers-by-description
host -> implement : triggers-by-description
host -> prototype : triggers-by-description
host -> research : triggers-by-description
host -> resolving-merge-conflicts : triggers-by-description
host -> tdd : triggers-by-description
host -> to-spec : triggers-by-description
host -> to-tickets : triggers-by-description
host -> triage : triggers-by-description
host -> wayfinder : triggers-by-description
host -> wizard : triggers-by-description
host -> grilling : triggers-by-description
host -> to-questionnaire : triggers-by-description
host -> writing-for-agents : triggers-by-description
host -> design-pages : triggers-by-description
host -> exe-release : triggers-by-description
host -> verify-ticket : triggers-by-description
host -> ui-acceptance : triggers-by-description
host -> manage-agents-md : triggers-by-description
host -> dispatch : triggers-by-description
host -> code-checkers : triggers-by-description
host -> diagram-design : triggers-by-description
host -> write-screen-contract : triggers-by-description
host -> advisor : triggers-by-description
host -> retro : triggers-by-description
user -> grill-with-docs : invoked-by-slash
user -> grill-me : invoked-by-slash
user -> handoff : invoked-by-slash
user -> teach : invoked-by-slash
user -> wait-what : invoked-by-slash
user -> improve-codebase-architecture : invoked-by-slash
user -> setup-matt-pocock-skills : invoked-by-slash
shared.md -> every-session : cites
grill-me -> grilling : calls
grill-with-docs -> grilling : calls
grill-with-docs -> domain-modeling : calls
grill-with-docs -> to-spec : hands-off-to
improve-codebase-architecture -> codebase-design : calls
improve-codebase-architecture -> grilling : calls
improve-codebase-architecture -> domain-modeling : calls
improve-codebase-architecture -> diagram-design : calls
improve-codebase-architecture -> to-spec : hands-off-to
tdd -> codebase-design : calls
wayfinder -> grilling : calls
wayfinder -> domain-modeling : calls
wayfinder -> prototype : calls
wayfinder -> research : calls
wayfinder -> design-pages : calls
wayfinder -> write-screen-contract : calls
wayfinder -> to-spec : hands-off-to
wayfinder -> setup-matt-pocock-skills : cites
triage -> grilling : calls
triage -> domain-modeling : calls
triage -> to-spec : hands-off-to
triage -> to-tickets : hands-off-to
triage -> dispatch : runs-script
triage -> setup-matt-pocock-skills : cites
prototype -> design-pages : hands-off-to
design-pages -> design-pages : re-enters-at
design-pages -> write-screen-contract : hands-off-to
design-pages -> wayfinder : hands-off-to
design-pages -> dispatch : runs-script
design-pages -> verify-ticket : runs-script
write-screen-contract -> to-spec : hands-off-to
write-screen-contract -> wayfinder : hands-off-to
to-spec -> write-screen-contract : re-enters-at
to-spec -> verify-ticket : runs-script
to-spec -> to-tickets : hands-off-to
to-spec -> setup-matt-pocock-skills : cites
to-tickets -> to-spec : re-enters-at
to-tickets -> verify-ticket : runs-script
to-tickets -> ui-acceptance : cites
to-tickets -> dispatch : hands-off-to
to-tickets -> setup-matt-pocock-skills : cites
dispatch -> verify-ticket : runs-script
dispatch -> ui-acceptance : runs-script
dispatch -> models.json : configured-by
dispatch -> implement : starts-with-prompt
dispatch -> code-review : starts-with-prompt
dispatch -> advisor : starts-with-prompt
dispatch -> implement : re-enters-at
dispatch -> retro : calls
dispatch -> to-tickets : cites
dispatch -> to-spec : cites
dispatch -> design-pages : cites
retro -> dispatch : hands-off-to
retro -> writing-for-agents : cites
implement -> dispatch : runs-script
implement -> verify-ticket : runs-script
implement -> tdd : calls
implement -> resolving-merge-conflicts : calls
implement -> ui-acceptance : cites
implement -> ticket : writes-event
code-review -> verify-ticket : runs-script
code-review -> ticket : writes-event
verify-ticket -> implement : re-enters-at
verify-ticket -> ui-acceptance : calls
ui-acceptance -> implement : re-enters-at
ui-acceptance -> to-tickets : re-enters-at
relay -> implement : wakes
relay -> dispatch : wakes
watchdog -> dispatch : wakes
turn-guard -> dispatch : wakes
tool-guard -> implement : refuses-and-redirects
tool-guard -> code-review : refuses-and-redirects
advisor -> dispatch : runs-script
code-checkers -> manage-agents-md : cites
manage-agents-md -> code-checkers : cites
wait-what -> diagram-design : cites
commit-06163a0f -> skills.txt : removes-ask-matt
```

## 4. 断点与弱点

以下每条标明「已核实」（回到原文或跑命令看到）或「推断」。

- **B1 头部没有模型可达的入口。** 「在工作目录里有个想法，想做出来」这句话，没有一个模型可触发技能的 description 覆盖。`grill-with-docs` 是用户触发（frontmatter 第 4 行）；`grilling` 只在「stress-test their thinking」或「'grill' trigger phrases」时触发；`tdd` 要「test-first」；`implement` 要已有 spec 或票；`wayfinder` 明写「Not for a well-scoped feature」。06163a0f 之前唯一覆盖它的是 ask-matt 的 description「Use when you know what you want to do … but not which skill does it」。已核实 frontmatter；「模型会怎么选」是推断。
- **B2 直接走 `grilling` 的路径没有下一步。** `grilling` 末句「Do not act on it until the user confirms you have reached a shared understanding」，不点名任何技能；只有包它的 `grill-with-docs` 在第 7 行点名 `to-spec`。用户说「grill me」时模型能加载的是 `grilling`（`grill-with-docs` 模型看不到），于是访谈结束后没有指向 `to-spec` 的文字。已核实原文；实际发生频率无证据。
- **B3 「走 spec 流水线还是直接 tdd」与「谁来检查」这两个判断现在无家可归。** 残留 ask-matt `SKILL.md` 主流程第 3 步写着「In this repository the branch also decides who checks the work … Take **No** only for a change small enough that the user will check it directly」。对已安装技能 `grep "single session|same session|who checks|multi-session"` 没有第二处（只命中 `wayfinder` 与 `grill-with-docs` 的会话连续性句子，见下条）。已核实。
- **B4 `prototype` 的 LOGIC 与 EXP 分支没有下一步。** 只有 `UI.md` 有 `## Next`（本仓加，`merge-notes/prototype.md` 第 59 行）；`LOGIC.md`、`EXP.md` 以 Anti-patterns 结尾。`SKILL.md` 规则 6 说「fold the validated decision into the real code」：无 map 时，这句会让 agent 直接写生产代码，绕过 spec 与票。有 map 时由 `wayfinder` 第 4 步接回，不断。已核实原文；绕过是否发生过无证据。
- **B5 阶段边界与会话卫生的判断没有安装。** `PHASE-BOUNDARIES.md`（五个选项：Continue、Clear、Handoff、Subagent、Compact）与 ask-matt 的 `### Context hygiene` 只在残留目录里。已安装技能里剩下两句会话规则：`grill-with-docs`「name the `to-spec` skill as the next step, in this same session」与 `wayfinder` 第 6 步「in a fresh session, run `to-spec`」；两句针对不同情形（无 map 时决定只在对话里；有 map 时决定在 tracker 上），不矛盾。`handoff` 现在没有任何已安装技能点名（`grep` 只命中上游 `productivity/README.md`，人读的）。已核实。
- **B6 `diagnosing-bugs` 到 `improve-codebase-architecture` 的交接从来不存在。** `diagnosing-bugs` `## Phase 5` 只写「Flag this for the next phase」，`## Phase 6` 不点名技能；上游 `5b1a4c51` 同样没有。线索来自 `docs/reviews/2026-09-28-lightweight/ask-matt.md` R3，已核实。且 `improve-codebase-architecture` 是用户触发，模型也够不到。
- **B7 三处「凭 description 进来，又被送回 `implement`」的往返。**
  - `ui-acceptance` 的 description「before writing a page ticket's code」→ 表第 1 行 → `implement` 的 `references/writing-interface-code.md` `## Before the first line`。而 `implement` 自己第 16 行已写「When **Read first** lists a screen contract, read `references/writing-interface-code.md`」。
  - `dispatch` 的 description「Start a reviewer from inside a ticket」→ 表第 1 行「No file: the `implement` skill's `## Closing steps`」。
  - `verify-ticket` 的 description 首句「Run one ticket's acceptance criteria, and close the ticket when they pass」→ 第 16 行「A worker's claim, criteria runs and closeout are steps of the `implement` skill.」
  三处都没断，是多一跳加载。`SKILL-SET-RULES.md` `### Descriptions` 第 2 条：「Two descriptions that claim the same job are a conflict」；这三个 description 各自声称了 `implement` 某一步的活。已核实原文；是否构成该条所说的冲突属判断，未下结论。
- **B8 orchestrator 被唤醒时只靠会话上下文。** `wake_text` 不带技能名；若 orchestrator 会话被压缩或清空后再收到 `#12 ticket.passed`，文字本身不指向 `dispatch` 或 `night.md`。`dispatch` 的 description 有「run a night as its orchestrator」，模型可能据此重新加载。推断；无实地证据。
- **B9 worker 不被指到 `## On waking`。** `dispatch.sh` 头注释末段说 `ack`「is in SKILL.md under `## On waking`, which every moment shares」，但 `dispatch` 表第 1 行把 worker 直接送到 `implement` `## Closing steps`，`implement` 没有指向 `## On waking`。`implement` 自己写了 `worker.queued` 与 `reviewer.reported` 的 ack，所以 ack 不缺；缺的是 `## On waking` 第 1 步「A wake can cut short a command you were running. Run that command again first」。已核实原文；后果推断。
- **B10 残留 ask-matt 目录不是「unmodified copy」。** 06163a0f 提交说明写「mmw-v2/upstream/skills/engineering/ask-matt/ itself, an unmodified copy of the mattpocock/skills subtree, is untouched」。实测 `git diff 5b1a4c51:skills/engineering/ask-matt HEAD:mmw-v2/upstream/skills/engineering/ask-matt --stat`：`SKILL.md` 74 行改动、`PHASE-BOUNDARIES.md` 22 行、`agents/openai.yaml` 删 2 行；description 与 `disable-model-invocation` 都是本仓版本。它的 merge-note 已随提交删除。后果：下次 `git subtree pull` 时这几段会冲突，而说明其取舍的文件已不存在；`SKILL-SET-RULES.md` `### Upstream skills` 第 1 条「A skill adapted from upstream without a merge-note is a finding」字面上适用（它未安装，是否算在 skill set 内属判断）。已核实。
- **B11 merge-note 仍以 ask-matt 为出处。** `merge-notes/triage.md` 第 12 行、`wayfinder.md` 第 21 行把 description 触发句的来源写成「取自 `ask-matt/SKILL.md`」。只影响维护者，不影响 agent。已核实。
- **B12 `dispatch.sh` 两份用法说明不一致。** 文件头注释（5–26 行）缺 `integrated`、`findings`、`memory-list` 三个子命令；`--help` 输出有，4721、4727 行的分派也有；`night.md` `## 4` 用了 `findings` 与 `memory-list`。已核实。只影响维护者读头注释。

## 5. 重复（全仓 `grep` 核实）

| # | 内容 | 出现位置 | 判定 |
| --- | --- | --- | --- |
| R1 | 「description 只写触发」 | 规则本体：`SKILL-SET-RULES.md` 67 行。作为理由复述：`merge-notes/code-review.md` 30、`implement.md` 25、`triage.md` 11、`to-tickets.md` 13；Memory `411750f5` | 真重复（同一意思），但 merge-note 是维护者文档，`SKILL-SET-RULES.md` `### Load and disclosure` 第 8 条允许「a merge-note … may explain it to maintainers」 |
| R2 | 两处开关「同增同删」 | 本体：`merge-notes/README.md` 20 行；上游 `.agents/invocation.md` 10 行。复述：`to-spec.md` 41、`triage.md` 36、`to-tickets.md` 50、`wayfinder.md` 27 | 真重复，且违反 README 自己第 24 行「下面每份说明只写它那个 skill 站在哪一边，不复述这条规则」 |
| R3 | 「host 启动时只扫这一行」这个理由 | `merge-notes/triage.md` 12、`to-spec.md` 11、`wayfinder.md` 21、`to-questionnaire.md` 12（`implement.md` 25 同义）；`SKILL-SET-RULES.md` 69；`docs/contexts/toolbox/CONTEXT.md` 97；`AGENTS.md` 56 | 真重复，七处 |
| R4 | 7 个用户触发技能的名单 | `merge-notes/README.md` 22；`improve-codebase-architecture.md` 11（「另外六个」）；`teach.md` 22（「另外六个」）；`handoff.md` 11、`grill-me.md` 11（「七个之一」） | 名单完整列出三处，真重复；「七个之一」只是指针 |
| R5 | 「每个技能结尾点名下一步」 | `SKILL-SET-RULES.md` 事实 7（17 行）与 `### Hand-offs`（92 行）；`REVIEWING-A-SKILL-SET.md` 22 行的检查 | 同一文件内事实与检查各一次，文件的设计就是「事实服务检查」，半重复 |
| R6 | 被唤醒后 ack | `dispatch` `## On waking` 第 3 步（通用）；`implement` 第 1 步（`worker.queued`）、第 3 步（`reviewer.reported`）；`one-ticket.md` 第 3 步；`inside-a-ticket.md` `## After the closeout`；`night.md` `### 3` 第 1 步（指针） | `implement` 与 `dispatch` 对 worker 各写一次，同一意思；其余是按角色的实例或指针 |
| R7 | 「worker 起 reviewer」这一时刻 | `dispatch` description「Start a reviewer from inside a ticket」；`implement` 第 3 步 | 两个技能都声称这一时刻，`dispatch` 表第 1 行用送回的方式化解（B7） |
| R8 | 「写页面票代码前读 `writing-interface-code.md`」 | `implement` 16 行；`ui-acceptance` description 与表第 1 行 | 同 R7（B7） |
| R9 | `PRODUCT_RULES` 提示词 | `dispatch.sh` 109 行「Before you start, reach or stop the product, read 'Five rules while the product is running' in the ui-acceptance skill.」；规则本体在 `ui-acceptance` 28–38 行 | 提示词只放指针和一句原因，不是规则复述；按 `SKILL-SET-RULES.md` `### Prompts` 第 2 条，指针式可接受。推断 |
| R10 | `retro` 的触发 | `retro` description「right after the dispatch skill's `summary` records `spec.closed`」；`night.md` 186 行「invoke the `retro` skill」 | 同一交接的两端，不是重复（`### Descriptions` 第 2 条：调用方与被调方可共享触发词） |
| R11 | 「路由技能」的立场 | `SKILL-SET-RULES.md` 事实 7「MMW ships no router skill」；上游 `SKILL-MECHANICS.md` `## Router skills`「cured by a router skill」 | 不是重复，是方向相反的两条（上游说用户触发技能多了就该有路由技能，本仓说不要） |
| R12 | `dispatch.sh` 用法 | 头注释 5–26 行；`--help` | 真重复，且已漂移（B12） |
| R13 | 「a skill is named by `/X` or the `X` skill」 | `SKILL-SET-RULES.md` 95、118 行；`merge-notes/README.md` `## host 中立` 28 行（指针）；Memory `ce037679` | 规则一处，其余指针；同文件两次（Hand-offs 与 Paths）属半重复 |

只是同词、不算重复：`to-tickets` 98、182 行与 `prototype` `UI.md` 95 行的「router」指 Web 路由；`wayfinder` 3 行的「more than one agent session」是范围描述。

## 6. 上游差异（本单元涉及的 frontmatter 与结尾段）

行数：「原文 → 现状」是 `SKILL.md` 全文行数，便于看出改动面；本单元只核对了 frontmatter 与结尾段的改动。

| 技能 | 原文 → 现状（行） | 调用方式 | description | 结尾段 | merge-note | 性质 |
| --- | --- | --- | --- | --- | --- | --- |
| `implement` | 15 → 101 | 用户 → 模型 | 加「Use when you were dispatched onto a ticket, or picked one up yourself.」 | 第 8 步「Open no pull request」返回调用方 | `implement.md` 24、25 | MMW 流程写进上游（正文几乎全是本仓写的，`merge-notes/README.md` `## 本仓自有正文的技能`） |
| `to-spec` | 75 → 127 | 用户 → 模型 | 加四支触发 | 加 `## Next` | `to-spec.md` 11、12、30、41 | MMW 流程 |
| `to-tickets` | 105 → 206 | 用户 → 模型 | 改写，加触发 | 加第 8 步，末句交给 `dispatch` | `to-tickets.md` 13、15、28、50 | MMW 流程（本仓自有正文） |
| `triage` | 112 → 116 | 用户 → 模型 | 删后半句，加两支触发 | 第 5 步送 `to-spec`、`to-tickets` | `triage.md` 11、12、15、36 | MMW 流程 |
| `wayfinder` | 128 → 128 | 用户 → 模型 | 加两句触发与一句非触发 | 加第 6 步 | `wayfinder.md` 11、18、21、27 | MMW 流程 |
| `to-questionnaire` | 54 → 55 | 用户 → 模型 | 改「you」为「the user」，加触发 | 无 | `to-questionnaire.md` 11、12、19 | MMW 接入 |
| `code-review` | 87 → 15 | 不变（模型） | 改为「one ticket's diff」四 axis 与角色触发 | 无（表分两扇门） | `code-review.md` 30、151 | **改变能力**：只审一张票、四个 axis |
| `prototype` | 26 → 27 | 不变 | 删「throwaway」，加第三类「how … implemented」 | `UI.md` 加 `## Next` | `prototype.md` 25、59 | **改变能力**（多一个 EXP 分支）+ MMW 流程 |
| `resolving-merge-conflicts` | 14 → 14 | 不变 | 加「clean merge makes the repository checks fail」 | 无 | `resolving-merge-conflicts.md` 11 | **改变能力**（多一种触发） |
| `writing-for-agents` | 81 → 81 | 不变 | 「modifying AGENTS.md or CLAUDE.md」放宽为「any document an agent will consume」 | 无 | `writing-for-agents.md` 11 | 接入 |
| `grill-with-docs` | 7 → 7 | 不变（用户） | 不变 | 「Call the Skill tool twice」改为读两份 `SKILL.md`，并加「name the `to-spec` skill as the next step, in this same session」 | `grill-with-docs.md` 14；`README.md` `## host 中立` | host 中立 + MMW 流程 |
| `grill-me` | 7 → 7 | 不变（用户） | 不变 | 「Call the Skill tool with」改为读 `SKILL.md` | `README.md` `## host 中立` | host 中立 |
| `improve-codebase-architecture` | 71 → 75 | 不变（用户） | 不变 | 加 `### 4. Hand the decision on` | `improve-codebase-architecture.md` 16 | MMW 流程 |
| `wait-what` | 7 → 10 | 不变（用户） | 不变；加 `argument-hint` | 无 | `wait-what.md` 33 | 能力扩展（`visual`） |
| 其余 10 个上游技能 | — | 不变 | 不变 | — | — | — |
| `diagram-design` | frontmatter 与 `8a85636a` 相同 | 模型 | 不变 | — | `diagram-design.md` | — |

调用方式的历史（已核实提交说明）：`2b92efe3`（2026-08-23）把 `implement` 改为模型可触发；`5181acc2`（2026-08-24）把 ask-matt、`grill-with-docs`、`improve-codebase-architecture`、`to-spec`、`to-tickets`、`triage`、`wayfinder`、`teach`、`to-questionnaire` 改为模型可触发，理由「漏打指令或要自动化时，agent 现在能自己判断该用哪个技能」；`c9f4e5c7`（2026-09-23）把 `grill-with-docs`、`teach`、`improve-codebase-architecture` 改回用户触发（理由在各 merge-note：`grill-with-docs.md` 11「与 `grilling` 抢同一个请求」；`improve-codebase-architecture.md` 11「worker 在 ticket 里 … 若自己触发它，night 里没有人回答」；`teach.md` 22 会往产品根目录写教学文件）；`06163a0f`（2026-09-28）移除 ask-matt。

**结论（已核实）：** 本单元里上游技能的改动，除 `code-review`、`prototype`、`resolving-merge-conflicts` 三处扩了能力以外，全部是把 MMW 的流程写进上游文本：调用方式翻转、description 补触发句、结尾段补下一步。这些正是 Memory `8ec53374` 所说「上游技能尽量回到原文，MMW 流程移入自有 playbook」要搬走的那一类。

## 7. 价值证据

| 部件 | 防的是什么 | 实地证据 |
| --- | --- | --- |
| 结尾段点名下一步（「K7」方案） | agent 在某一跳找不到下一步就自己发明做法 | #538（`gh issue view 538`，已核实，CLOSED 2026-09-21）：「一个 agent 在某一跳找不到下一步，就会自己发明一套做法——这正是变色龙 9 月那 25 张 sub-issue 里有 22 张耗在流水线自身的成因」 |
| ask-matt（已删） | 用户不记得该用哪个技能 | 本会话 `grep` `~/.claude/projects` 全部 jsonl：`"skill":"ask-matt"` 或 `<command-name>/ask-matt` 只命中一个文件，而那一处是前一轮复审员自己的 `grep` 命令文本，真实调用 0 次（已核实）。线索来源 `2026-09-28-lightweight/ask-matt.md` 同一结论；它还说 Codex 只有一个调研会话读过该文件，本会话未核实 |
| ask-matt 的漂移 | 路由表与被指技能失同步 | `2026-09-23-skill-set/汇总.md` 44 行（两条走不通的路线）；`2026-09-28-lightweight/ask-matt.md` R1–R4；上游 `CLAUDE.md` 21 行的同步规则只约束上游（已核实） |
| 用户触发的 7 个 | 与别的技能抢同一触发；无人值守时被启动 | `c9f4e5c7` 提交说明与三份 merge-note 理由（已核实）；是否真发生过抢触发或夜里误启：无证据 |
| description 只写触发 | 路由写在 description 里会漂移 | Memory `411750f5`（2026-09-23 用户裁定）；`2026-09-23-skill-set/汇总.md` 65 行「12 个本仓写的 description 原来夹带了路由、流程或产出」 |
| frontmatter YAML 合法性检查 | description 解析失败则 host 读不到技能 | 2026-09-23 `advisor`、`ui-acceptance` 两份 frontmatter 不是合法 YAML（`汇总.md` 52 行；`19a85c2c` 提交说明），随后加了 `mmw-v2/tests/lib/check_own_skill_frontmatter.py` |
| 启动提示词只放数据 | 模型现写 prompt 会替被启动方划定范围 | ADR 0014 `## 要修的是什么`：「advisor 是这条流水线里唯一由模型现写 prompt 的 agent」 |
| 角色型 description（`code-review`、`advisor`、`implement`） | 被启动的会话凭提示词里的技能名与角色找到自己 | ADR 0014 `## 为什么这修法要动那扇门`：description 是 caller 恒在上下文的位置；无失败记录 |
| `## On waking` 的 ack | relay 重启后重发同一唤醒 | `relay.py` 文件头；具体失败夜无证据 |
| `tool-guard.py` 的提问拦截 | 无人会话把问题放上屏幕后卡住 | 文件头理由；Memory 与提交里有无触发记录，本单元未查 |
| Find-your-moment 表 | 重入时重复副作用；读者读错 reference | `c9f4e5c7`「door -> moment」改名；具体失败无证据 |
| 实际使用分布（口径：jsonl 中字符串出现次数，含重复记录与子代理日志，只作量级） | — | Skill 工具：`code-review` 1153、`verify-ticket` 121、`writing-for-agents` 30、`to-tickets` 27、`advisor` 27、`dispatch` 24、`grilling` 21、`to-spec` 18、`domain-modeling` 16、`prototype` 8、`implement` 6、`wayfinder` 6、`grill-with-docs` 5、`teach` 4、`triage` 2、`exe-release` 2、`design-pages` 2、`research` 1、`wizard` 1、`codebase-design` 1。斜杠：`/wayfinder` 22、`/writing-for-agents` 18、`/wait-what` 12、`/handoff` 10、`/to-spec` 7、`/to-tickets` 4、`/grill-with-docs` 2、`/grill-me` 2、`/resolving-merge-conflicts` 2、`/triage` 1、`/dispatch` 1。读法（推断）：流水线尾部靠脚本提示词与 description 驱动；头部（`wayfinder`、`to-spec`）用户主要用斜杠启动；用户触发的 `wait-what`、`handoff` 确有使用 |

## 8. 约束

| 约束 | 内容 | 出处 |
| --- | --- | --- |
| 事实 5 | 按分支渐进加载 | `SKILL-SET-RULES.md` 15 行 |
| 事实 6 | 技能是按名字组合的平级件；不复制别的技能的文件、不复述别的技能的规则 | 16 行 |
| 事实 7 | 一个家；「this is why MMW ships no router skill, since every description is already in the agent's runtime」；description 说何时开始，结尾段说下一步；「Read in pipeline order, the closing sections walk from an idea to a closed ticket with no gap, and no two skills claim one moment」 | 17 行 |
| `### Descriptions` | 只写触发；并排读，两个 description 抢同一件事是冲突；不写 host 与 runner 名；本仓自写技能没有 host 侧清单 | 65–70 行 |
| `### Load and disclosure` | 分派表在任何有副作用的步骤之前；pick-one 用表 | 25–31 行 |
| `### Hand-offs` | 每个事件在全集只有一条指令；每个技能以下一步或返回的调用方结尾，被返回的技能要有入口；点名技能不写路径 | 88–96 行 |
| `### Prompts written for other agents` | 启动提示词只放启动时已知的数据；规则经技能到达 | 100–102 行 |
| `### Paths and host neutrality` | 技能写作 `/X` 或 `the X skill`；不点名宿主的调用工具 | 116–118 行 |
| `### Upstream skills` | 上游文本只在改变 agent 行为时改；接入先在边缘做 | 106–112 行 |
| `SKILL-MECHANICS.md` `## Invocation` | 用户触发技能「no other skill can」调用；模型触发技能的 description 常驻上下文 | 上游原文 |
| `SKILL-MECHANICS.md` `## Router skills` | 路由技能是一个用户触发技能，「can only hint, never fire them」 | 上游原文 |
| 上游 `.agents/invocation.md` | 「A user-invoked skill may invoke model-invoked skills, but it can never reach another user-invoked skill」；两处开关保持一致 | 8、10 行（上游维护者规则，本仓 agent 不加载） |
| `merge-notes/README.md` | 上游技能默认模型可触发；7 个保留用户触发；本仓自写技能 frontmatter 只有两个键 | 18–24 行；由 `check_own_skill_frontmatter.py` 检查（`AGENTS.md` Commands 表） |
| ADR 0014 | description 是 caller 恒在上下文的位置；把 caller 侧规则写进用户级提示词被否决：`shared.md` 到不了 Cursor，且每回合付常驻上下文 | `docs/adr/0014-advisor-has-one-door.md` `## 为什么这修法要动那扇门`、`## Considered Options` |
| ADR 0015 | 只交付技能；需要派活时用 host 自带的通用 subagent | `docs/adr/0015-no-custom-subagents.md` |
| ADR 0010（被 0020、0022 修订） | agent 之间靠事件叫醒，不轮询 | `docs/adr/0010-agents-are-woken-not-polled.md` |
| `AGENTS.md` | `skills.txt` 独自决定安装；description 改动要新会话才生效 | `## Key Conventions` |
| Memory `411750f5`（2026-09-23） | description 只留触发；路由由正文负责；上游能不改就不改，接入在边缘做 | 用户裁定 |
| Memory `ce037679`（2026-09-28） | 技能间写名字即可；「MMW 不系统区分用户调用与模型调用，不要拿这条去要求 MMW」；以唯一性与系统性要求 MMW，系统性包括「有一张与实际同步的总图」 | 用户裁定 |
| Memory `f4c3d378`（2026-09-19） | 方案以技能为第一层编排；不在技能层做独立准确的路由，agent 会在技能间无意义跳转 | 用户要求 |
| Memory `fe94802d`（2026-08-25） | 平级调用、禁止嵌套、不改上游 frontmatter；「给 diagram-design 设置 disable-model-invocation: true 来强制层级调用的方案被直接排除」 | 用户裁定 |
| Memory `c155ffc2` | 调用方只给角色名与票号 | 用户意见 |
| Memory `8ec53374`（2026-09-29） | 改造为 pstack 分层：mode（常驻规则 + 路由）/ playbook / 能力技能 / 原则 / lever 脚本 / agent 定义；上游技能尽量回到原文，MMW 流程移入自有 playbook | 已拍板方向 |
| Memory `756fc056`（2026-09-29） | 旧规则（点名事实 7）是审视对象而非约束；问它原本防什么、新架构能否更好地解决；同时不得形式上拆散 MMW | 用户警告 |

注：`ce037679` 写于 2026-09-28 14:45 UTC（22:45 +0800），要求「一张与实际同步的总图」；48 分钟后 `06163a0f`（23:33 +0800）删掉了集内唯一的总图 ask-matt。这张「总图」指给人看的图还是给 agent 加载的路由，记录里没有写明，未确定。仓里现存的整体图 `docs/research/workflow-compare/mmw-map.html`（最后改于 2026-09-24，`f073860b`）是研究产物，不被任何技能加载。

## 9. 天然整体

- **一个开关的两个文件。** `SKILL.md` 的 `disable-model-invocation` 与 `openai.yaml` 的 `policy.allow_implicit_invocation`：拆开处理就是一半 host 用户触发、一半模型触发（`merge-notes/README.md` 20 行）。
- **description 与它的分派表。** description 决定何时加载，Find-your-moment 表决定进来后去哪；表离开 `SKILL.md` 就多一跳（事实 5；`### Load and disclosure` 25 行要求表在 `SKILL.md`）。
- **启动提示词的形状与接收方的表行。** `code-review` 表按「prompt names this skill, a ticket and a base commit, and names no axis」分门；`dispatch.sh` 1967 行正好拼出这个形状。改一边另一边就失配。`advisor` 表第 2 行「your prompt is a brief and nothing else」与 2072 行同理。
- **事件 → 收件人 → 动作这条链。** `relay.py` `WAKES`（谁被叫醒）、`dispatch` `## On waking`（ack）、`night.md` `### 3` 表与 `implement` 第 1、3 步（做什么）。按设计，脚本只管投递、技能文本管动作（`dispatch.sh` 头注释末段）；每个事件一条指令（`### Hand-offs` 91 行）。把某个事件的动作拆到第三处会破坏这一条。
- **`dispatch` 的表与 `## On waking`。** 后者被头注释称为「every moment shares」，是表的公共前置。
- **`night.md` 事实表与各节。** 事实表只是本文件各节的索引，重入者靠它跳到对的节；离开本文件就失去意义。
- **界面链的结尾段。** `prototype` `UI.md` `## Next` → `design-pages` `edit-pages.md` `## Next` → `pull.md` `## Reached from here` → `write-screen-contract` `## Next` → `to-spec`。每跳一句，写在生产方；#538 记录了其中任一跳缺失的代价。
- **一条边的两端。** `to-spec` `## Next` 与 `to-tickets` 第 1 步「A plan or a conversation with no published spec goes through the `to-spec` skill first」；`night.md` 186 行与 `retro` 186 行的返回句。

## 10. 引入 mode 路由技能与事实 7 的关系

### 10.1 事实 7 的两条理由各自在哪里成立

| 理由 | 成立处 | 不成立处 | 出处 |
| --- | --- | --- | --- |
| 「every description is already in the agent's runtime」 | 28 个模型可触发技能 | 7 个用户触发技能不在模型的列表里：本会话（Claude Code）可用技能列表里没有 `grill-me`、`grill-with-docs`、`handoff`、`teach`、`wait-what`、`improve-codebase-architecture`、`setup-matt-pocock-skills`（已核实）；其他 host 未核实 | 第 0、4 节 |
| 「closing sections walk from an idea to a closed ticket with no gap」 | 从 `to-spec` 起到关票、落地、retro、`finish` 一路连通 | 头部 B1–B5：没有模型可达的入口；`grilling` 与 `prototype` 的 LOGIC/EXP 分支没有下一步；「走流水线还是直接 tdd」与阶段边界的判断没有家 | 第 4 节 |

另外，06163a0f 删掉的不只是一份副本：ask-matt 里至少有三块内容在别处没有第二份（B3 的 Yes/No 与「谁来检查」、B5 的 `PHASE-BOUNDARIES.md` 与 `### Context hygiene`、B1 的「不知道该用哪个技能」入口）。已核实（`grep` 无其他命中）。

### 10.2 pstack 的 mode 与 ask-matt 不是同一种东西

- 上游 `SKILL-MECHANICS.md` 的路由技能（ask-matt 的原型）：用户触发，只能提示，给人减少要记的技能名。
- pstack 的 mode（`docs/research/code-landing-refs/pstack/skills/poteto-mode/SKILL.md`）：用户触发（`disable-model-invocation: true`）且带 `mode: true` 与 `reminder:` 两个只有它有的键；正文是常驻规则（Non-negotiables、Principles 索引、Autonomy、Subagents、回复写法）加 23 条 playbook 的路由表，playbook 文件持有步骤顺序；README：「the other skills are situational; the mode skill uses them for you as needed」。pstack 47 个技能中 46 个带 `disable-model-invocation: true`，唯一例外是 `setup-pstack`（已核实，与 `L1-pstack-mode-and-short-playbooks.md` 51–52 行一致）。mode 引用其他技能的方式是「Read the leaf skill in full」（正文 Principles 节首句）。`mode`、`reminder` 在 Cursor 上的确切行为，快照没有定义（未确定）。
- 所以 pstack 里「下一步是什么」只有一个家：playbook。能力技能不知道被谁调用。MMW 现在「下一步」的家是能力技能的结尾段（其中 6 处是本仓写进上游文本的，见第 6 节）。

### 10.3 相容与冲突

- **字面冲突。** 事实 7 写的是「MMW ships no router skill」。任何 mode 技能都违反这句字面。
- **理由上可以相容，条件是「搬」而不是「加」。** 事实 7 反对的是第二份副本（「A second copy is a finding … It has to be kept in step with the first」）。如果引入 mode/playbook 的同时，把现在写在能力技能结尾段里的「下一步」搬进 playbook，那么「下一步」仍只有一个家，只是家换了位置；如果只加 mode、不搬结尾段，就是 06163a0f 说明所说的「duplicates the flow」。
- **头部缺口是 mode 能提供的新家。** B1、B3、B5 的内容现在没有任何家，放进 mode 或 playbook 不构成重复。
- **Memory 之间的张力。** `ce037679` 要求有「一张与实际同步的总图」，同时说「不系统区分用户调用与模型调用」；`fe94802d` 否决过用 `disable-model-invocation` 强制层级调用；`8ec53374` 定了 mode/playbook 分层；`756fc056` 说这些旧规则都要重新审视。它们指向的方向不一致，由用户在下一轮裁定。

### 10.4 可选的调用模型与后果

| 模型 | 做法 | 后果 | 出处 |
| --- | --- | --- | --- |
| A 维持现状 | description 自动触发 + 结尾段 + 脚本提示词 + 事件唤醒；无路由技能 | 头部缺口 B1–B5 保持；上游文本继续承载 MMW 流程（第 6 节），与 `8ec53374`「上游尽量回到原文」相反；不新增常驻上下文 | 第 3、4、6 节 |
| B pstack 式「只被点名」 | 一个 mode 技能 + playbook；能力技能全部 `disable-model-invocation: true`，description 不再承担路由 | 常驻上下文变少（description 退出系统提示）。但：(1) 在 MMW 的 host 上用户触发技能「no other skill can」调用（`SKILL-MECHANICS.md`、上游 `invocation.md` 8 行），Claude Code 上它们不在模型列表里（本会话已核实），而 MMW 规定不写路径（`ce037679`），「Read the X skill's SKILL.md」可能找不到文件，未核实各 host 行为；(2) `dispatch.sh` 的「Use the implement skill …」「Use the code-review skill …」依赖这两个技能模型可触发（`merge-notes/implement.md` 24 行「我们要模型自己就能调用 implement」），改为用户触发后要换成斜杠形式，经 runner 投递斜杠是否生效未核实；(3) pstack 靠 Cursor 的 `mode`/`reminder` 让 mode 常驻，MMW 服务五个 host，没有对应机制；常驻层 `shared.md` 被 ADR 0014 否决过（到不了 Cursor、每回合付费）；(4) 与 `ce037679`、`fe94802d` 的既有裁定相反（二者按 `756fc056` 可被重审） | 10.2、第 8 节 |
| C mode 作为模型可触发的入口，能力技能保留触发型 description | mode 持有头部判断与 playbook；能力技能仍可被 description 直接加载；MMW 写进上游的结尾段搬进 playbook | 头部缺口有家；上游文本可向原文回退；但从中途直接进入某个能力技能的 agent（例如用户直接 `/to-spec`）不再从该技能读到下一步，除非 mode 也在上下文里；mode 的 description 要与 `grilling`、`wayfinder`、`to-spec` 的触发并排检查冲突（`### Descriptions` 第 2 条）；实地证据提示风险：同为模型可触发路由的 ask-matt 在 Claude 会话里被调用 0 次 | 第 7 节 |
| D 按「谁启动会话」分层 | 脚本启动的会话已经是「agent 定义 = 启动提示词 + `models.json` 一行」（`dispatch.sh start`/`advise` + `models.py` 的 `row_for_role`），夜间顺序已在 `night.md`；mode 只覆盖人启动的头部（想法 → spec/票；Yes/No；阶段边界） | 改动面最小；夜间与单票链路不动；mode 与结尾段的重叠只在头部几跳（`grill-with-docs` 末句、`wayfinder` 第 6 步、`improve-codebase-architecture` `### 4`、`to-spec` `## Next`），需决定这几句搬还是留 | `dispatch.sh` 1925–2080；`night.md` |
| E 不加路由，把头部缺口补进现有技能 | 例如给 `grilling` 或 `prototype` LOGIC/EXP 加下一步，把 Yes/No 写进某个技能 | 不加层；但继续往上游文本里写 MMW 流程，与 `411750f5`「接入优先在边缘做」和 `8ec53374` 的方向相反 | 第 6、8 节 |

## 11. 未确定

- 除 Claude Code 外，Codex、Grok、Pi、Cursor 如何对待 `disable-model-invocation`（Codex 按上游文档读 `policy.allow_implicit_invocation`，未实测），以及另一个技能写「Read the X skill's SKILL.md」时这些 host 能否读到一个用户触发技能。
- runner（paseo、orca、herdr）把以 `/implement` 开头的启动提示词投给新会话时，斜杠是否被当作技能调用。
- pstack 的 `mode: true`、`reminder:` 在 Cursor 上的确切语义。
- 第 7 节的调用计数是字符串出现次数，不是精确调用次数；只查了 Claude Code 的记录。
- B2、B4、B8、B9 的后果是否在真实会话里发生过：没有查到记录。
- Memory `ce037679` 的「总图」指给人看的图还是给 agent 的路由。
- 未通读的文件：`dispatch.sh` 其余约 4500 行、`relay.py` 其余部分、各技能未列在第 0 节的 reference；本报告对它们的陈述只限于第 0 节列出的段落。
