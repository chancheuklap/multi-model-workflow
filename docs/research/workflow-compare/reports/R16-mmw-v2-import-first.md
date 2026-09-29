# R16 MMW v2 升级架构：导入优先

本文给出 MMW 升级后的完整架构。设计立场是**导入优先**：先定义「pstack 的 playbook、原则、能力技能怎样不改或少改就落进 MMW」这套接口，再让 MMW 自己的每一段内容按同一套接口归层。接口是否成立，用第 9 节在纸面上真的搬一批 pstack 组件来检验，逐个写出落在哪、原文改几处、MMW 因此要长出什么。

**材料与写法。**

- pstack 快照在 `docs/research/code-landing-refs/pstack/`（`.cursor-plugin/plugin.json` `"version": "0.15.4"`，`LICENSE` 为 MIT）。下文以 `skills/`、`poteto-mode/` 开头的 pstack 路径都相对这个目录。
- 报告简称：
  - L7 = `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（准绳）；
  - R13 = `R13-pstack-design-essence.md`，R14 = `R14-mmw-layer-mixing-inventory.md`；
  - R4 V1–V17、R12 M1–M30 是这两份报告「已核实」的事实，直接引用编号。R4、R12 的保守结论不采用。
  - N1–N10 只作线索；`N11-mmw-gaps.json` 列出的错误都不采用。
- MMW 路径不带前缀时相对 `mmw-v2/`。`SKILL.md` 行号含 frontmatter。SSR = `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`。
- 标注：「原文」是文件里写着的；「已核实」是本轮回到原文或跑命令看到的；「推断」是由原文推出、原文没直接写的；需要实测才能定的放第 12 节，并写明怎么测。
- 新写的规则文字只取自三处：MMW 现有文本、pstack 原文、用户已有的决定。每条都给出处。把现有内容**搬到正确的层**不算新写。

**硬约束**（任务给定，只有这些算约束）：

- **H1** 宿主不换（Claude Code、Codex、Grok、Pi、Cursor；runner 用 Orca 等），没有 Cursor 的 `mode: true` / `reminder` 常驻机制。
- **H2** Claude Code 上，带 `disable-model-invocation: true` 的技能不在模型的技能列表里，按名也调不到（R4 V1）；description 在宿主启动时扫入，改了要新会话才生效。
- **H3** 会话内派出的子代理跑在本会话宿主的模型上；跨厂商只能另起会话（`docs/adr/0015-no-custom-subagents.md` `## Consequences`）。
- **H4** 脚本送进活会话的一条消息必须是一行（`skills/dispatch/scripts/watchdog.py` 第 813 行，R12 M1）。
- **H5** Self-hosting boundary（根 `AGENTS.md` `## Self-hosting boundary`）：一次 watch 期间冻结已安装版本，运行中的流程不读工作树里正在被改的版本。
- **H6** 夜里的会话屏幕前没人，不能向人提问。

另有一条用户已有的决定，任务说明写明：`mmw-v2/prompt/shared.md` 是用户的全局规则，**不由 MMW 改写**。本文把它当作与硬约束同级的边界，记作 **U0**。

---

## 0. 结论（先读这里）

### 0.1 改造前后，一眼能看出的区别

| 看什么 | 改造前 | 改造后 |
|---|---|---|
| 组件类型 | 只有一种：技能。顺序、做法、判断、角色、路由都写在 35 个技能的正文、reference、结尾段里 | 七种，各有目录：mode、playbook、原则、能力技能、reference、脚本（lever）、配置。外加外来组件目录 `upstream-pstack/` |
| 「做一张票要走哪些步」 | 读 `implement`（101 行，上游原文 15 行），再被送去 `verify-ticket`、`dispatch` 的 moment 表、`code-review` 的 `session.md` | 读 `skills/mmw/playbooks/work-a-ticket.md`，编号步骤从认领到 closeout 一份文件 |
| 「从想法到关票」 | 按 SSR 事实 7 把 17 句「下一步」结尾段按顺序拼起来（R14 第 2 节） | 读 mode `## Playbooks` 路由表，每类任务一行、指向一个 playbook |
| 能力技能的结尾 | 「The `to-tickets` skill.」「return to the dispatch skill's `references/night.md` `## 5`」 | 交回什么（交付物），没有「下一步」「谁调用我」 |
| 上游技能 | 带 +1674/−415 行本仓改动（R12 M5），其中流程与路由分布在 11 个技能里 | 回到原文，只留 merge-note 记下的边缘改动（宿主中立措辞、确属能力扩展的文件） |
| 跨任务的判断 | 29 条，平均每条散在 6 处以上，写成不同文字（R14 第 3 节） | `skills/mmw/principles/` 一个目录，mode 一张索引；调用方只写名字加一句本地限定 |
| 脚本送进会话的文字 | 按步骤编号续跑（`resume_at` 返回「step 1」到「step 5」），按字面点名 `night.md`、`## On waking` | 只点名 playbook 与步骤标题，全部取自一张锚点表 `anchors.py`，lint 核对锚点存在 |
| 加一个 pstack 的 playbook 或原则 | 没有地方放 | 放进 `playbooks/` 或 `principles/`，路由表或索引加一行；导入脚本做机械改写 |
| `dispatch` 技能 | 一个技能装六个时刻：起 reviewer、跑夜、跑单票、改模型、开任务板 | 不再是技能：四个时刻成了 playbook，改模型成了能力技能 `setup-mmw`，脚本成了 mode 的 lever |

### 0.2 十四条设计决定

| # | 决定 | 依据 |
|---|---|---|
| D1 | 一个 mode 技能 `mmw`，放 `skills/mmw/`，**模型可触发**。目录照 `poteto-mode/` 布局：`SKILL.md`、`playbooks/`、`principles/`、`references/`、`scripts/` | H2（带开关的 mode 按名调不到）；L7 A.1；R13 E6、I-1 |
| D2 | MMW 的每一种工作流都是 playbook，共 14 份 MMW 自有、5 份 pstack 原文导入、3 份按条件导入。worker、reviewer、两种 orchestrator 的操作文件都是 playbook | L7 A.2；R13 E10、E12 |
| D3 | 能力技能只讲一件事怎么做、交回什么。上游技能回到原文；`to-spec`、`to-tickets` 因多数正文是 MMW 的能力而分叉为 MMW 自有技能；新拆出 `shared-experience`、`setup-mmw` 两个能力技能；`dispatch` 技能解散 | L7 A.3、B.2 硬规律 3；R14 第 4、6 节 |
| D4 | 原则层是 `skills/mmw/principles/<slug>.md` 普通文件，格式与 pstack 原则逐字相同（含 frontmatter）。首批 10 条 MMW 自有、15 条 pstack 原文，另加导入组件的依赖闭包 4 条 | H2；L7 A.4；R14 3.1–3.2 |
| D5 | **调用开关按来源保持原样**。上游与 pstack 的技能保留原来的 `disable-model-invocation`；mode 给一条「按安装目录读 `SKILL.md`」的解析规则，让 playbook 仍能在 H2 下点名它们 | H2；`grill-with-docs` 已在用「读另一个技能的 `SKILL.md`」的做法（N10 第 6 节） |
| D6 | 流水线脚本是 mode 的 lever，搬到 `skills/mmw/scripts/`；脚本只点名 playbook 与步骤标题，标题集中在 `anchors.py` | L7 A.6、B.2 硬规律 2；R12 K-2 |
| D7 | 「现在在哪一步」由脚本算：worker 的 `RESUME:`、orchestrator 的 `dispatch.sh where`，都返回步骤标题，不返回编号 | R14 W3；R12 K-3；H5、H6 |
| D8 | 六个「槽位」集中在 mode：control（驱动界面）、delivery（交付改动，替代 PR）、forge、子代理简报、模型角色、宿主工具。导入的组件只点名槽位，mode 一处解析 | R13 I-4、I-8、I-10、I-11、I-13 |
| D9 | `~/.mmw/models.json` 扩出两类角色：会话内角色（H3 下只能同宿主）与面板角色（每个成员一个另起的会话）；新 lever `panel.sh` 起面板、收答案 | H3；R13 E9、I-5、I-6 |
| D10 | pstack 以 subtree 引入 `mmw-v2/upstream-pstack/`；能力技能进 `skills.txt`（新前缀 `ps/`），playbook 与原则由 `scripts/import.py` 复制进 `skills/mmw/` | R13 I-12；R4 D7.2 |
| D11 | 一个连线 lint `tests/lib/check_wiring.py`，每个测试套件先跑：方向、按名、无编号引用、槽位可解析、能力技能里没有角色与流程词 | L7 E.1 第 2、17 条；pstack `principle-encode-lessons-in-structure` |
| D12 | 夜里无人时，执行协议的 skip 行与「点名改变决定的原则」写进该 playbook 的交付物（closeout、评审报告、决策轨迹） | H6；R13 E7 |
| D13 | `retro` 的去处加 `principle`、`playbook`、`mode` 三个，教训按层回流 | pstack `principle-encode-lessons-in-structure` `**Feedback loop:**`；`skills/retro/scripts/retro.py` 第 31–32 行 |
| D14 | SSR 搬到 `docs/skill-set/`（R12 K-38），事实 7 与 `### Hand-offs` 第 5 条改为「顺序住在 playbook」；新 ADR 记下这一改变 | R14 T38；SSR 第 17 行（R12 M8） |

### 0.3 纸面导入的结果（第 9 节）

- **6 条原则**（prove-it-works、fix-root-causes、laziness-protocol、encode-lessons-in-structure、sequence-verifiable-units、never-block-on-the-human）：正文与 frontmatter **改 0 处**，只改文件位置；每条在 mode 索引加 1 行。检出两处依赖：`sequence-verifiable-units` 点名 `build-the-lever`，`prove-it-works` 点名 `show-me-your-work`，所以两者要同批导入，否则 lint 报悬空引用。
- **6 个能力技能**（how、why、architect、interrogate、show-me-your-work、unslop）：`how`、`unslop` 改 0 处；`why`、`interrogate`、`show-me-your-work` 各改 1 处（都是 Cursor 专有路径或来源）；`architect` 改 0 处，但依赖闭包带进 `arena`（改 2 处）和另外 3 条原则。每个导入的技能另生成一个 `agents/openai.yaml`（Codex 的调用开关，H1）。
- **playbook**：`bug-fix.md`、`investigation.md`、`feature.md` 改 0 处，靠 mode 里的三条别名（「Opening a PR」「Cursor's `/loop` command」「the control skill」）落位。`shipping.md` 不能当 MMW 的落地流程：它建立在 PR 与 `gh`/Origin 上，并调用 bun 写的 `watch-pr`；它的 9 步在 MMW 里逐条都有对应物（第 9.3 节），所以只作为「用 PR 交付的仓库」的条件路由导入，并且等用户决定要不要引入 bun。
- 这次纸面导入顺带补上了 MMW 三个已核实的断点：修 bug 之后没有下一步（N10 B6）、「走 spec 流水线还是当场做完」无家可归（N10 B3）、`prototype` 的 LOGIC/EXP 分支没有下一步（N10 B4）。

### 0.4 留在原处的内容与它的约束

只有下列内容按类型本该搬走、却留在原处，每条写明约束。其余一切都搬到按类型该在的层。

| 内容 | 留在哪 | 约束 |
|---|---|---|
| watchdog 告警里的那条命令（例如 `dispatch.sh resume <n> …`） | 告警那一行 | H4：告警必须一行；判断部分搬进 playbook |
| 启动提示词里的 mode 名、playbook 名、票号、`unattended` 标记 | `dispatch.sh` 拼的提示词 | H1：没有常驻机制，脚本启动的会话只能由提示词点名 mode |
| `tool-guard.py`、`turn-guard.py` 的拦截 | 各宿主的 hook 配置 | H1、H6：结构性强制只能在宿主 hook 上做；文字缩成指向 mode 的一句 |
| `mmw-v2/prompt/shared.md` 的结构与措辞 | 原处 | U0 |
| 已安装 checkout 与 `~/.mmw/installed-root` | 原处 | H5 |
| 各宿主的调用开关（`disable-model-invocation` 与 Codex 的 `agents/openai.yaml` `policy`） | 技能目录里 | H1、H2：宿主按技能目录读开关 |

### 0.5 需要用户决定的事

1. pstack 首批导入的范围（第 9 节：原则 15 条加依赖 4 条、能力技能 7 个、playbook 5 份加条件导入 3 份），以及今后「先导入、后裁剪」还是「逐个审批」。
2. 是否引入 bun（pstack 的 `watch-pr`、`orch` 需要它；根 `AGENTS.md` `## Package Manager` 目前只列 bash、python3、uv、node）。不引入则 babysit、shipping、orchestrate 不导入。
3. `dispatch.sh check` 在 `--check` 失败时自动跑完整 `install.sh`，与根 `AGENTS.md`「`install.sh` runs only when the user explicitly authorises it」冲突（R12 M7）。建议改为只报告。
4. 上游 `implement` 回到原文（用户触发）后是否继续安装。
5. 消费仓库可不可以有私有 playbook（`.mmw/playbooks/`，只在人在场的会话里用）。
6. Cursor 收不到 `shared.md`（根 `AGENTS.md` `## Key Conventions`），Cursor 上跑的会话是否由用户在应用里补同样的规则。
7. 每批迁移中需要授权运行 `install.sh`（第 11 节）。

---

## 1. 判据

### 1.1 七类内容与它们的家

判别问题：这段内容决定的是什么？

| 它决定的是 | 家 | 判据出处 |
|---|---|---|
| 遇到 X 用 Y、自主权到哪、回复怎么写、任务该走哪个 playbook、槽位解析到哪 | mode | L7 A.1 |
| 一类任务里各项能力的先后、门槛、谁拥有什么、何时停、交什么回复 | playbook | L7 A.2 |
| 一件事怎么做、交回什么（一个有名字的交付物） | 能力技能 | L7 A.3、C.3 |
| 跨任务、有触发情境、能改变一个具体决定的判断 | 原则 | L7 A.4（四条门槛） |
| 分支才读的材料、交给另一个读者（子代理、另起的会话）的模板、会增长的目录、适配器契约 | reference | L7 A.5 |
| 每次结果都一样的状态、投递、检查 | 脚本（lever） | L7 A.6；SSR 事实 2 |
| 角色到宿主和模型的绑定；消费仓库的目标配置 | 配置 | L7 A.8、A.11 |
| 给维护者与人读的决定、词表、写作规则 | 仓库文档 | L7 A.9 |

### 1.2 两个动作词

第 10 节对照表只用这些动作词：

- **搬**：内容按类型不在该在的层，搬过去。
- **就位**：内容已经在按类型该在的层，不动（附类型依据）。这不是「留在原处」。
- **拆**：一个文件混装几类内容，按类型拆到各层。
- **回原文**：上游或外来组件的本仓改动撤回，原文恢复。
- **删**：内容是另一处的第二份，或已被新的家覆盖。
- **留在原处（Hx）**：按类型本该搬走，但有已核实的硬约束。只有 0.4 节那几行。

### 1.3 从 pstack 学的精髓，与本设计的对应

R13 归纳了 pstack 的十二条精髓（E1–E12）。本设计逐条落实：

| 精髓 | 本设计里的落点 |
|---|---|
| E1 按「谁决定」分层 | 第 1.1 节判据；第 10 节逐件归层 |
| E2 只按名字连线、方向单一 | D11 的 lint；第 8.4 节方向规则 |
| E3 能力技能不知道调用方 | 第 5 节每个能力技能的「剥离」列；lint 第 5 类 |
| E4 playbook 只编排 | 第 4 节骨架与 22 份 playbook |
| E5 原则只被点名 | 第 6 节；原则是普通文件，不是技能 |
| E6 mode 集中路由与常驻纪律 | 第 3 节；四条到达路径 |
| E7 执行协议 | 第 7 节；无人时写进交付物 |
| E8 脚本只管确定性部分 | 第 8 节；三处越界的修法 |
| E9 模型角色与技能分离 | D9；第 9.4 节 |
| E10 自动化包复用共享组件 | 夜间角色即 playbook；共享能力按名调用 |
| E11 教训按层回流 | D13 |
| E12 不拆的纪律 | 第 5 节「就位」的依据；第 4.1 节规则簇 |

pstack 自己的错误（L7 E.1）不照抄：按步骤编号跨组件引用、原则引用五种写法、角色标签没有解析器、本地闸门与上层授权没写优先级、外部依赖没有安装检查。每一条在本设计里都有对应的 lint 或 mode 句（第 8.3 节）。

---

## 2. 目标目录树

### 2.1 `mmw-v2/`（到文件一级）

「←」后写内容来源；「新」表示新建的文件，其正文来源仍按上文规矩。

```
mmw-v2/
├── install.sh                      ← 现有；skills.txt 多一种前缀 ps/；hook 路径改到 skills/mmw/scripts/hooks/；
│                                     新增 mode-reminder hook 的登记；--check 多两项（第 8.2 节）
├── skills.txt                      ← 现有；第一行 self/mmw；新增 self/setup-mmw、self/shared-experience、
│                                     self/to-spec、self/to-tickets；删 self/dispatch；新增 ps/<name> 若干
├── skills/
│   ├── mmw/                                    ★ mode（模型可触发）
│   │   ├── SKILL.md                            新；各节来源见第 3 节
│   │   ├── playbooks/
│   │   │   ├── define-a-change.md              ← to-spec ## Next、to-tickets 第 20/160 行、grill-with-docs 第 7 行、
│   │   │   │                                     several-specs.md 的循环、ask-matt 主流程第 3 步、improve-codebase-architecture ### 4
│   │   │   ├── map-a-large-effort.md           ← wayfinder 第 6 步、interface-and-remake.md 的地图结构
│   │   │   ├── design-an-interface.md          ← prototype UI.md ## Next 与第 3、6 步、design-pages 的交接段、
│   │   │   │                                     write-screen-contract ## Next、to-spec 第 2 步闸门
│   │   │   ├── triage-an-issue.md              ← triage 第 5 步第 82、94 行
│   │   │   ├── run-a-night.md                  ← dispatch/references/night.md 全文
│   │   │   ├── run-one-ticket.md               ← dispatch/references/one-ticket.md
│   │   │   ├── work-a-ticket.md                ← implement SKILL.md 正文、dispatch/references/inside-a-ticket.md、
│   │   │   │                                     verify-ticket/references/sub-issues.md 第 13–23 行、tdd 第 22/38 行、
│   │   │   │                                     resolving-merge-conflicts 第 2 步的票句、ui-acceptance 第 38 行
│   │   │   ├── review-a-ticket.md              ← code-review/references/session.md、code-review ## Find your moment
│   │   │   ├── accept-a-night.md               ← night.md ## 6、triage/references/pipeline-issues.md、
│   │   │   │                                     docs/agents/issue-tracker.md ## Morning queries
│   │   │   ├── ship-a-release.md               ← exe-release SKILL.md 第 1–5 步、references/driving.md
│   │   │   ├── onboard-a-repository.md         ← setup-matt-pocock-skills 第 51/63 行、code-checkers 第 6/8 步、
│   │   │   │                                     ui-acceptance 的 target.json 段、night.md 1b 的 target_config --check
│   │   │   ├── authoring-a-skill.md            ← SSR ## Editing、## Verifying、REVIEWING-A-SKILL-SET.md、
│   │   │   │                                     根 AGENTS.md Gotchas 发布四步、merge-notes/README.md、downstream-notes/README.md
│   │   │   ├── bring-in-a-component.md         ← 根 AGENTS.md <important if … upstream …>、merge-notes/README.md、R4 D7.2–D7.3
│   │   │   ├── deliver-a-change.md             ← 上游 implement「Commit your work to the current branch」、
│   │   │   │                                     implement 第 99 行、根 AGENTS.md Gotchas 发布四步
│   │   │   ├── bug-fix.md                      ← pstack 原文（导入）
│   │   │   ├── feature.md                      ← pstack 原文（导入）
│   │   │   ├── investigation.md                ← pstack 原文（导入）
│   │   │   ├── session-pickup.md               ← pstack 原文（导入）
│   │   │   ├── pause-safely.md                 ← pstack 原文（导入）
│   │   │   └── （条件导入）opening-a-pr.md、babysit.md、shipping.md ← pstack 原文，只路由给用 PR 交付的仓库
│   │   ├── principles/
│   │   │   ├── <MMW 自有 10 条>.md             新；规则与理由逐字取自第 6.2 节所列原文
│   │   │   └── <pstack 导入 15 条 + 依赖 4 条>.md ← skills/principle-<slug>/SKILL.md 原文
│   │   ├── references/
│   │   │   ├── orchestrator-events.md          ← night.md ## 3 的表、### Exit codes of `resume`、one-ticket.md 第 3 步各行、
│   │   │   │                                     watchdog 八种告警、turn guard 一行（run-a-night 与 run-one-ticket 共用）
│   │   │   ├── review-axes/standards.md        ← code-review/references/standards-reviewer.md
│   │   │   ├── review-axes/spec.md             ← code-review/references/spec-reviewer.md
│   │   │   ├── review-axes/tests.md            ← code-review/references/tests-reviewer.md
│   │   │   ├── review-axes/ui.md               ← code-review/references/ui-reviewer.md
│   │   │   ├── phase-boundaries.md             ← upstream ask-matt/PHASE-BOUNDARIES.md（上游原文的副本，merge-note 记来源）
│   │   │   ├── transcripts/{claude,codex,grok,pi,cursor}.md  新；每宿主的会话记录位置（第 9.5 节 I-14，待实测填）
│   │   │   └── （条件导入）bugbot-triage.md    ← pstack poteto-mode/references/bugbot-triage.md
│   │   └── scripts/                            ★ lever
│   │       ├── dispatch.sh                     ← skills/dispatch/scripts/dispatch.sh（提示词、anchors 改动见第 8 节）
│   │       ├── relay.py、watchdog.py、status.py、statedir.py、ghlist.py  ← skills/dispatch/scripts/
│   │       ├── runners/{orca,paseo,herdr}.sh   ← skills/dispatch/scripts/runners/
│   │       ├── hooks/tool-guard.py、hooks/turn-guard.py  ← skills/dispatch/scripts/
│   │       ├── hooks/mode-reminder.py          新（第 3.3 节路径 3）
│   │       ├── anchors.py                      新；R12 K-2 的锚点表
│   │       ├── panel.sh                        新；D9
│   │       └── import.py                       新；D10
│   ├── setup-mmw/                              能力：角色 → 宿主、模型、档位；runner；只读查询
│   │   ├── SKILL.md                            ← dispatch/references/editing-models.md
│   │   ├── hosts.json                          ← dispatch/hosts.json
│   │   └── scripts/models.py                   ← dispatch/scripts/models.py（加 role 查询与两类新角色）
│   ├── shared-experience/                      能力：打开、搜索、保存、更正 Memory 记录
│   │   ├── SKILL.md                            ← implement ## Shared experience while implementing、
│   │   │                                         night.md ## 4 Memory 决定段的做法部分
│   │   └── references/saving-memory.md         ← implement/references/saving-memory.md
│   ├── to-spec/                                MMW 自有（分叉）；去掉 ## Next、description 触发句、第 2 步的退回路线
│   ├── to-tickets/                             MMW 自有（分叉）；去掉第 1 步第 20 行与第 8 步第 160 行
│   ├── verify-ticket/                          能力：命令参考与判据判断（第 5 节）
│   ├── ui-acceptance/                          能力；接收 references/writing-interface-code.md
│   ├── advisor/、retro/、design-pages/、write-screen-contract/、exe-release/、code-checkers/、manage-agents-md/
│   │                                           能力；各自剥离见第 5 节
├── upstream/                                   mattpocock subtree；技能回到原文（第 5.2 节）
├── upstream-diagram-design/、upstream-unlazy/  就位
├── upstream-pstack/                            ★ 新：cursor/plugins 的 pstack/ 子目录，subtree split 后引入
│   └── skills/…                                原样；能力技能从这里装，playbook 与原则由 import.py 复制
├── merge-notes/                                就位；新增 pstack.md 与每个改过的 pstack 组件一份
├── downstream-notes/                           就位；新增本次升级影响消费仓库的说明（第 11 节）
├── prompt/                                     就位（U0）
├── board/                                      就位；board_data.py 第 27 行与 codeversion.py 的路径字面改（R12 M22）
├── migrations/                                 就位
└── tests/
    ├── lib/check_wiring.py                     新；D11
    ├── wiring/                                 新套件；每类 lint 一个必须失败的反例
    └── 其余 12 个套件                           就位；dispatch、relay、verify-ticket 的断言随提示词与锚点改（第 8 节）
docs/
├── skill-set/SKILL-SET-RULES.md、REVIEWING-A-SKILL-SET.md   ← 从 writing-for-agents 目录搬出（R12 K-38）
├── adr/0032-mmw-ships-one-mode.md              新；记下 D1–D5 与被取代的 SSR 事实 7
└── contexts/toolbox/CONTEXT.md                 加 mode、playbook、principle、capability skill、lever、slot 六个词条
```

### 2.2 消费仓库、`~/.mmw/`、宿主安装目录

```
<消费仓库>/
├── AGENTS.md                ## External References 多一行：本仓库的工作走 `mmw` 技能
│                            （onboard-a-repository 用 manage-agents-md 写入；manage-agents-md 第 150 行
│                              已规定「Other skills add rows under … ## External References」，R4 V14）
├── .mmw/target.json         就位；新增可选键 delivery（closeout | promote | pr）与 control（表面 → 技能）
├── .mmw/harness/、journeys/、stories/   就位
├── docs/agents/{issue-tracker,triage-labels,domain}.md   就位
├── docs/specs/<effort>/screen-contract.yaml、prototypes/<effort>/   就位
├── .worktrees/issue-<n>、merge-<branch>   就位（名字归流水线）
└── （用户决定 0.5 第 5 条）.mmw/playbooks/<slug>.md   只在人在场的会话里路由

~/.mmw/
├── models.json              rows（四个另起会话的角色，就位）+ session_roles（会话内角色）+ panels（面板角色）
├── installed-root           就位（H5）
├── boards.json              就位
└── state/<owner>__<name>/   watches.json、relay.lock 等就位；新增 panels/<id>/<member>.md（panel.sh 收答案处）

~/.agents/skills/、~/.claude/skills/   软链：mmw、MMW 能力技能、upstream 能力技能、ps/ 能力技能
```

### 2.3 命名规则

| 组件 | 规则 | 例 |
|---|---|---|
| playbook 文件 | kebab-case，动词开头；文件首行 `### <显示名>`，没有 frontmatter（与 pstack 相同，L7 A.2） | `work-a-ticket.md`，首行 `### Work a ticket` |
| playbook 步骤 | `N. **<标题>.** <正文>`；标题是锚点，脚本与别的文件只按标题引用 | `6. **Get reviewed.** …` |
| playbook 规则簇 | `#### <名字>`，只放常设规则，不进 todo（L7 A.2、D.1） | `#### Baselines` |
| 原则文件 | `principles/<slug>.md`；frontmatter `name: principle-<slug>`、`description: "Apply …"`，与 pstack 同构 | `principles/the-baseline-is-a-contract.md` |
| 能力技能 | 目录名 = `name`，kebab-case；与已装技能重名时不导入，或经用户同意以 `pstack-<name>` 改名导入 | `setup-mmw`；`pstack-tdd`（若导入） |
| 锚点 | `anchors.py` 里一个常量对应一个 playbook 文件名、步骤标题、规则簇名或模板标题 | `WORK_GET_REVIEWED = ("work-a-ticket", "Get reviewed")` |
| 脚本指针（一行内） | `· mmw <playbook-slug>` 或 `RESUME: <playbook-slug> § <步骤标题>` | `#12 reviewer.reported · mmw work-a-ticket` |

### 2.4 角色的物理位置

一个角色由四样东西组成，各在一层：

| 角色 | 操作文件（playbook） | 模型绑定（配置） | 启动方式（lever） | 会话里的常驻纪律 |
|---|---|---|---|---|
| worker | `playbooks/work-a-ticket.md` | `models.json` rows `junior-worker` / `senior-worker` | `dispatch.sh start <n> worker` | mode（提示词点名） |
| reviewer | `playbooks/review-a-ticket.md` | rows `reviewer` | `dispatch.sh start <n> reviewer` | mode |
| 评审 axis | `references/review-axes/<axis>.md`（子代理简报） | 会话内，跑在 reviewer 的模型上（H3） | reviewer 派子代理 | 简报首句要求读 mode `## Principles` |
| 夜的 orchestrator | `playbooks/run-a-night.md` | 人启动的会话 | 用户说「今晚跑 spec #N」 | mode（description、hook） |
| 单票 orchestrator | `playbooks/run-one-ticket.md` | 同上 | 同上 | 同上 |
| advisor | 能力技能 `advisor`（`references/advising.md`） | rows `advisor` | `dispatch.sh advise <brief>` | 提示词「Use the advisor skill.」 |
| 面板成员 | 调用方能力技能的 reference 模板（如 `interrogate/references/reviewer-prompt.md`） | `models.json` `panels.<role>` 每项一个 | `panel.sh start` | 简报 |

---

## 3. mode：`skills/mmw/SKILL.md`

### 3.1 frontmatter

- `name: mmw`
- `description`：照 pstack mode 的两句式（L7 A.1），第一句写它是什么，第二句写「Use for …」。内容取自路由表的任务名：「MMW's working mode: matches a task to its playbook, indexes the principles, and sets autonomy for attended and unattended sessions. Use for a bug fix, a feature, an investigation, defining, running or reviewing tickets, a night, a release, onboarding a repository, writing a skill, or a prompt that names an MMW playbook.」
- **不带** `disable-model-invocation`（H2：带了就按名调不到，脚本启动的会话就无法「Use the mmw skill」）。
- 没有 `mode`、`reminder` 键（H1：这些宿主不认）。
- Codex 侧的 `agents/openai.yaml` 不写 `policy` 行，保持可隐式触发（`merge-notes/README.md` 的「两处开关同增同删」）。

### 3.2 正文，逐节

章节顺序照 pstack mode（L7 A.1）：`## Non-negotiables` → `## Principles` → `## Autonomy` → `## Subagents` → `## Host tools` → `## Writing the reply` → `## Comments` → `## Re-entry` → `## Playbooks`。`## Host tools`、`## Re-entry` 是 MMW 多出的两节，分别替代 pstack 依赖的 Cursor 专有机制和 H6 下的重入。

**`## Non-negotiables`**

首段两句取自 pstack mode 第 15 行原文：「In your reply, name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf you read this session.」（「leaf SKILL.md」改为「leaf」：MMW 的原则是文件不是技能。这是 1 处措辞适配。）

接着一句层级优先级：用户级 `shared.md` > 本 mode > 所服务的 playbook（含它对原则的本地限定）> 原则 > 能力技能自带的闸门。出处：R13 E3、E6；R4 第 0 节第 1 条采用的「层级优先级句」；pstack 缺这一句（L7 C.2、E.1 第 18、30 条）。

然后是触发列表。每条都是现有文字从能力技能 description 或正文里**搬**来的「在某个时刻用我」：

| 触发 | 目标 | 来源 |
|---|---|---|
| 一个脚本或 hook 拒绝了你 | 照它点名的那一个下一步做，不即兴 | SSR 第 59、134–136 行；ADR 0008；R14 PC3 读的一侧 |
| 想手动关票、改队列 label、写事件 | 不做；状态只经脚本写 | `implement` 第 99 行；`tool-guard.py` `REFUSAL`；R14 PC6 |
| 要写一个页面票的代码 | `ui-acceptance` 的 `references/writing-interface-code.md` | `ui-acceptance` description 末句 |
| 架构选择、数据迁移、大重构、API 形状落定之前；一个问题试了两次仍不行 | `advisor` | `advisor` description；`references/consulting.md` `## When it is worth a session` |
| 干净的合并让仓库检查变红 | `resolving-merge-conflicts` | 该技能 description |
| 难 bug、性能退化，需要一个能变红的循环 | `diagnosing-bugs` | 该技能 description |
| 非平凡改动、「are we sure?」 | `how` | pstack mode 第 19 行（导入后生效） |
| 代码跨越函数边界 | `architect` | pstack mode 第 22 行（导入后生效） |
| 有争议的设计 | `interrogate` | pstack mode 第 24 行（导入后生效） |
| 英文散文产物 | `unslop`；给用户的回复按 `## Writing the reply` | pstack mode 第 26 行 |
| 长时间、无人或多阶段的白天工作 | `show-me-your-work` 的决策轨迹 | pstack mode 第 35 行 |
| 驱动一个界面（复现、验证） | control 槽位：浏览器与 Web → `playwright-cli` 或 `ui-acceptance` 的 oracle；本机原生窗口 → `computer-use`；Orca 内置浏览器 → `orca-cli`；CLI → 直接跑命令；`.mmw/target.json` `control` 可覆盖；缺失则停下并说出缺什么 | pstack mode 第 30 行、`bug-fix.md` 第 1 步；各技能 description；ADR 0008 |
| 任务中途发现一个技能坏了 | 夜里：`fault` 子票后停；白天：修它，按 **Authoring or modifying a skill** 走 | `implement` 第 18 行；pstack mode 第 34 行 |
| 要开 worktree | 只开在主工作树的 `.worktrees/` 下，不用 `issue-<n>`、`merge-<branch>` 两种名字 | 根 `AGENTS.md` `## Key Conventions`；R13 I-15 |
| 会话要交给另一个 agent 或宿主 | `handoff` | `handoff` description；N10 B5（今天没有任何技能点名它） |
| 打开任务板 | `bash scripts/dispatch.sh board` | `dispatch/SKILL.md` 表第 6 行 |
| 换宿主、模型、档位或 runner | `setup-mmw` | `dispatch/SKILL.md` 表第 5 行 |

**`## Principles`**

- 首句取自 pstack mode 第 39 行：「Read the leaf in full for any principle you apply. Each entry names when it applies.」
- 解析规则一句：`principle-<slug>`、「the **<slug>** principle」、「the **<slug>** principle skill」、「**principle-<slug>**」都指 `principles/<slug>.md`。这一句让 pstack 的五种引用写法（L7 E.1 第 1 条）不改就能解析。
- 索引分组照 pstack 的 Core、Architecture、Verification、Delegation、Meta 五组，加一组 **Pipeline** 放 MMW 自有原则。每行写成 `**<显示名>** (**principle-<slug>**). <何时适用>. <一句要点>.`
- 索引行由 lint 与各原则文件的 `description` 核对（第 8.3 节第 6 类），修掉 pstack「一句话摘要在四处重复、措辞不一」（L7 E.1 第 14 条）。全表见第 6 节。

**`## Autonomy`**

- 人在场：用户级 `shared.md` 规则 1–3 管「谁决定什么」。本节不复述（U0；R13 E5 末条）。
- 无人（提示词带 `unattended`，或 `tool-guard.py` 拦下了一次提问）：
  - 屏幕上不放问题。取票、baseline、spec 最可能的那个选项，写一行进本 playbook 的决定记录，继续做。会改变交付内容的问题：`verify-ticket.py <n> --sub-issue decision <file>`，其余照做。出处：`implement` 第 23 行。
  - 三个角色各自的决定记录：worker 写 closeout 的 `Decisions I made on my own`（`implement` 第 23 行）；reviewer 写报告里的「Could not tell: …」（`code-review/references/session.md` 第 45 行，R12 M11）；advisor 写「Missing information gets named precisely.」那一条（`advisor/references/advising.md` 第 18 行，R12 M11）。这修掉了 `NO_QUESTION` 只给 worker 出路的缺边（N11 missing_edges 第 2 条；R4 V9）。
  - 不可逆的写（合并、推送、关票、发布）只由脚本做。出处：`implement` 第 99 行「Open no pull request: the orchestrator lands the ticket」；pstack mode 第 83 行「Always pause for irreversible writes」在无人会话里的等价物是「不做」。
- 导入的原则与本节冲突时以本节为准。实例：pstack `principle-never-block-on-the-human` 的 `**Boundaries:**`「Irreversible actions … still require confirmation」在无人会话里没有人可确认，按上一条由脚本承担（L7 C.2 指出 pstack 自己在这里没写优先级）。

**`## Subagents`**

- 用宿主的通用子代理（ADR 0015）。简报首句：「Read the `mmw` skill's `## Principles` and the playbook step you serve.」这是 `agents/poteto-agent.md` 正文唯一一句的等价物（R13 E6）。导入的组件写 `subagent_type: "poteto-agent"` 或 `generalPurpose` 时，一律读作「宿主的通用子代理，带这份简报」。
- 同一步的子代理在一条消息里一起发出，等它们全部回来。出处：`code-review/references/session.md` 第 23、33 行；`to-tickets` 第 113、119 行；`wayfinder` 第 76、114 行（R14 3.3）。
- 只读靠简报里一句「You are read-only: write nothing.」。宿主没有只读档。出处：`advising.md` 第 23 行；四个 axis 文件第 3 行（R14 PC15）。pstack 的 `readonly: true` 映射到这一句。
- 模型角色（D9）：
  - 「your configured <角色> model」：运行 `bash scripts/dispatch.sh role "<角色>"`。结果是 `inherit-parent` 就不指定模型；是一个本宿主能用的模型就指定它。H3 下会话内子代理不能换厂商。
  - 面板角色（值是列表，如 `interrogate reviewers`、`architect runners`、`arena runners`）：人在场时用 `bash scripts/panel.sh` 每项起一个另起的会话；没有面板配置时退化为本会话模型上的同模型面板，并在回复里写明「同模型面板，失去模型多样性」。依据：pstack mode 第 95 行「A second opinion is the same prompt against a different model. Agreement is high-signal.」
  - 无人会话不起面板，除非所服务的 playbook 点名。理由是成本（`consulting.md` 第 3 行「slow and expensive」）。
- 「You own every subagent's work. Review the diff and write your own summary, don't pass through what it said.」取自 pstack mode 第 95 行原文。

**`## Host tools`**

一张映射表，让 pstack 组件里的 Cursor 专有写法不改正文就能读懂（R13 I-13）：

| 组件里写的 | 在 MMW 读作 |
|---|---|
| `AskQuestion` | 人在场：在对话里问（`shared.md` 规则 1）；无人：见 `## Autonomy` |
| Cursor's `/loop` command、`/goal` | 宿主自带的循环命令（Claude Code 有 `loop`）；夜里是 relay 唤醒与 watchdog（ADR 0010、0020） |
| cloud agent | `dispatch.sh start` 或 `panel.sh` 起的另一个会话 |
| `create-skill` | `writing-for-agents` |
| `readonly: true` | 简报里的只读句 |
| `run_in_background: true` | 宿主支持就用；不支持就前台（第 12 节 U-4） |
| `agent-transcripts/`、`~/.cursor/projects/` | `references/transcripts/<宿主>.md` 写的位置 |
| `control-ui`、`control-cli`（cursor-team-kit） | control 槽位（`## Non-negotiables`） |
| `/deslop`（cursor-team-kit） | 没有对应物；跳过并写 `skip:` 行（外部依赖不存在，L7 E.1 第 27 条） |
| brain note | `shared-experience` 保存的一条 Memory 记录 |
| `gh`、`origin`、`gt` | forge 命令见消费仓库 `docs/agents/issue-tracker.md` |
| 「Run **Opening a PR**」 | 「Run **Deliver a change**」 |
| 一个技能的 `SKILL.md`，它不在你的技能列表里 | Claude Code 读 `~/.claude/skills/<name>/SKILL.md`，其余宿主读 `~/.agents/skills/<name>/SKILL.md`（`install.sh` 头注释：技能装这两处）。这是 D5 的解析规则 |

**`## Writing the reply`**

- 一句：「The user-level prompt (`shared.md`, rules 4–9) owns the reply; this mode does not restate it.」（U0；R13 E5 末条）
- 一句取自 pstack mode 第 109 行：「Every playbook ends with a reply written this way. The per-playbook lines name only the content unique to that playbook.」
- 无人会话的「回复」是 playbook 的交付物（closeout、评审报告、`NIGHT SUMMARY`）。出处：`shared.md` 前言「what it reports goes in the formats its skills give」。

**`## Comments`**

- 取自 pstack mode 第 113 行原文：「Keep a comment only for a non-obvious *why* the code can't show …」。导入的 `feature.md` 第 4 步写「Comments per **Comments**」，没有这一节就悬空。

**`## Re-entry`**（被唤醒、被压缩、被 `resume`）

1. 唤醒可能打断你正在跑的命令，先原样重跑它。出处：`dispatch/SKILL.md` 第 25 行；`principle-make-operations-idempotent`。
2. 读唤醒点名的票；唤醒不带 tracker 之外的内容。出处：第 26 行。
3. `bash scripts/dispatch.sh ack <n> <event>`，在任何长工作之前。`watchdog:` 与 `MMW turn guard:` 行不 ack。出处：第 27 行。
4. 问脚本你在哪：worker 跑 `verify-ticket.py <n> --preflight` 读 `RESUME:`；orchestrator 跑 `bash scripts/dispatch.sh where <spec 或 n>`。两者都印「playbook § 步骤标题」。出处：`implement` 第 74 行；R12 K-3。
5. 照那一步和所服务 playbook 的事件行做。
- 这一节修掉「worker 读不到 `## On waking` 第 1 步」（N10 B9，R14 W1 (a)）：它在 mode 里，每个角色都读。
- 原则一句：「Where you are is what the ticket's events say, not what this session remembers.」（`dispatch/SKILL.md` 第 8 行）以 `principle-the-tracker-is-the-state` 的名字点名。

**`## Playbooks`**

- 执行协议，取自 pstack mode 第 117 行原文：「Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to a playbook below, open its file, and copy its steps in verbatim.」
- 无人会话一句（D12）：skip 行与点名原则的句子写进本 playbook 的交付物。第 7 节展开。
- 升级路由，改写自 pstack mode 第 119 行的结构：大而看不清路的工作路由到 **Map a large effort**；要跑一整批票的路由到 **Run a night**。
- 路由表，每行 `- **<名字>.** <任务定义>. [用户原话]. [Distinct from …]. \`playbooks/<file>.md\`.`（L7 A.1）。全表见第 4.2 节。
- 三条别名（D8）：「**Opening a PR** means **Deliver a change**」；「the control skill means the control slot in `## Non-negotiables`」；「a Cursor command names its `## Host tools` row」。

**篇幅**：推断约 150–180 行（pstack mode 143 行；MMW 多 `## Host tools`、`## Re-entry` 两节）。实测见第 12 节 U-5。

### 3.3 怎样被加载

| 会话 | 到达路径 | 确定性 | 依据 |
|---|---|---|---|
| 脚本启动（worker、reviewer） | 启动提示词首句：「Use the mmw skill. Playbook: work-a-ticket. Ticket #n. Unattended.」 | 高：「Use the X skill」今天就是 worker、reviewer 的启动方式（`dispatch.sh` 第 1949、1967 行），读技能目录下的嵌套文件今天也在用（各技能的 Find-your-moment 表，N10 M6） | H1 下唯一确定的路径；H4 不限制启动提示词（Orca 以命令行参数传入，`runners/orca.sh` 第 25 行；paseo、herdr 待核，第 12 节 U-9） |
| 人启动 | ① mode 的 description 模型可触发；② 消费仓库 `AGENTS.md` 一行；③ 每回合一行提醒 hook | ①② 依赖模型选择；③ 确定 | H2；R4 X-1；本节路径 3 |
| 被唤醒 | 唤醒行末尾带 `· mmw <playbook>`（relay 知道收件人角色与 watch 类型，R4 V3） | 高 | H4：指针与事件同一行；R12 K-1 |
| 被压缩 | Claude Code 与 Codex 上用 `SessionStart`（压缩后）hook 注入一行「re-read the mmw skill and run the `## Re-entry` steps」；其余宿主靠下一次唤醒的指针或 `RESUME:` | 待实测 | 第 12 节 U-2 |

**路径 3：每回合提醒 hook**（pstack `reminder` 的替代）。

- `scripts/hooks/mode-reminder.py` 登记在宿主的「用户提交 prompt」事件上。当前工作树有 `.mmw/` 时打印一行，文字取自 pstack `reminder` 原文的结构：「New task? Playbook match or rigor needed → apply the mmw skill. Casual turn → don't.」没有 `.mmw/` 时什么都不打印。
- 已知可行：
  - Codex 的 `UserPromptSubmit`、`SessionStart` 处理器带 `additionalContextLimit`（`install.sh` 第 774、790–792 行），即能向上下文追加文字；
  - Claude Code 有 `UserPromptSubmit` 与 `SessionStart`（推断：宿主文档行为，本仓未实测）。
- 回应 ADR 0014 否决常驻规则的两条理由（R4 V16）：不在 `.mmw/` 仓库里就不付费；不写进 `shared.md`，而是 hook。
- Cursor、Grok、Pi 有无同类事件、能否注入，待实测（U-2）。没有的宿主只剩路径 ①②。

### 3.4 满足 H1、H2 的方式小结

- H1：不用 `mode: true`；常驻 = 提示词点名（脚本会话）+ description + `AGENTS.md` 一行 + hook（人会话）。
- H2：mode 自己不带开关；上游与 pstack 的能力技能保留原开关，靠 `## Host tools` 最后一行按路径读取（D5）；原则与 playbook 不是技能，没有开关问题。
- description 改动要新会话生效：每批迁移后提醒用户开新会话（第 11 节）。

---

## 4. playbook 总目录

### 4.1 骨架

照 pstack（L7 A.2），MMW 多两处：

```
### <显示名>

**You own <对象>. <动词>, <动词>.**       所有权行
<可选首段：本类任务的纪律、与相邻 playbook 的界线>
**Entry.** <从哪些情形进来；每个入口一行>             MMW 多出：多入口的 playbook
**Where you are.** <读哪条脚本输出定位>               MMW 多出：跨会话、会被唤醒的 playbook

1. **<标题>.** <祈使句>。点名一个能力技能、原则、脚本命令或别的 playbook。门槛与 Done when。
…

#### <规则簇>                                            常设规则，不进 todo

**Reply:** <本 playbook 独有的回复或交付物>
```

规则：

- 步骤只点名组件，不复述它们的做法（pstack `authoring-a-skill.md`「Delegate to other skills by path. Don't restate.」）。
- 原则用括注点名，并可写一句本地限定（L7 C.2）。
- 跨组件引用只按标题，不按编号（D11 lint 第 3 类）。
- pstack 的 playbook 没有 `**Entry.**`、`**Where you are.**` 也能用（R13 I-2）。

### 4.2 路由表（mode `## Playbooks` 的内容）

| 行 | 任务定义（节选） | Distinct from | 文件 | 定义出处 |
|---|---|---|---|---|
| **Define a change** | 把一段对话、一个想法、一张清空的地图、一个判为可做的 issue、一个架构决定，变成已发布的 spec 与通过 lint 的票 | Feature：那个由用户当场检查；这个由流水线检查 | `define-a-change.md` | `to-spec`、`to-tickets` description；ask-matt 主流程第 3 步「who checks the work」（R12 M29） |
| **Map a large effort** | 路线看不清、一个会话装不下的工作 | Define a change：一次访谈加一份 spec 装得下的 | `map-a-large-effort.md` | `wayfinder` description |
| **Design an interface** | 界面要设计、要翻新旧产品，或设计包要进仓库 | Define a change 的第 4 步从这里取 screen contract | `design-an-interface.md` | `prototype`、`design-pages`、`write-screen-contract` description |
| **Triage** | 不是你开的 issue 或外部 PR；流水线交回 `needs-triage` 的票 | Accept a night：早上的队列整体 | `triage-an-issue.md` | `triage` description |
| **Investigation** | 只读的问题：X 怎么工作、Y 为什么这样、我们确定 Z 吗、X 还是 Y | Define a change：调研之后要改代码时交回 | `investigation.md`（导入） | pstack mode 第 121 行 |
| **Bug fix** | 一个报告的缺陷，复现、找根因、修复，靠运行时证据 | Define a change：要经 spec 与夜的修复 | `bug-fix.md`（导入） | pstack mode 第 122 行 |
| **Feature** | 新增或改变行为，从一个命名的数据形状出发，用户当场检查 | Define a change | `feature.md`（导入） | pstack mode 第 127 行；ask-matt 主流程第 3 步 No 分支 |
| **Run a night** | 让一份 spec 的已发布票在一个 orchestrator 下从 `open` 跑到 `summary`（「今晚跑 spec #N」） | Run one ticket | `run-a-night.md` | `dispatch/SKILL.md` 第 12 行 |
| **Run one ticket** | 在任何夜之外给一张票起一个 worker | Work a ticket：那里你就是 worker | `run-one-ticket.md` | `dispatch/SKILL.md` 表第 4 行 |
| **Work a ticket** | 你被 `start` 放到一张票上，或自己拿起一张票 | Run one ticket | `work-a-ticket.md` | `implement` description |
| **Review a ticket** | 你被起为一张票的 reviewer | 能力技能 `code-review`：不绑票的评审 | `review-a-ticket.md` | `code-review` description |
| **Accept a night** | 夜后：读流水线的队列、让用户验收、`finish` | Triage：单个 issue | `accept-a-night.md` | `issue-tracker.md` `## Morning queries`；`night.md` `## 6` |
| **Ship a release** | 用当前分支的代码出正式安装包 | — | `ship-a-release.md` | `exe-release` description |
| **Onboard a repository** | 让一个仓库能被 MMW 跑：tracker 文档、`AGENTS.md`、检查器、`target.json` | — | `onboard-a-repository.md` | `setup-matt-pocock-skills`、`code-checkers`、`ui-acceptance` description |
| **Authoring or modifying a skill** | 写或改技能、playbook、原则，或任何 agent 读的文字 | — | `authoring-a-skill.md` | pstack mode 第 131 行；`writing-for-agents` description |
| **Bring in a component** | 在 MMW 仓库里导入一个 pstack 或其他上游组件，或拉一次上游 subtree | Authoring：写自己的 | `bring-in-a-component.md` | 根 `AGENTS.md` `<important if … upstream …>` |
| **Deliver a change** | 按本仓库收改动的方式交出一个完成的改动；导入的 playbook 写「Opening a PR」就是它 | — | `deliver-a-change.md` | 上游 `implement` 末句；根 `AGENTS.md` `## Gotchas` 第 1 条 |
| **Session pickup** | 接手前一个 agent 没做完的工作 | Re-entry：绑票的会话读 `RESUME:` | `session-pickup.md`（导入） | pstack mode 第 139 行 |
| **Pause safely** | 显式暂停、离线、宿主重启、即将压缩 | — | `pause-safely.md`（导入） | pstack mode 第 140 行 |
| 条件行 **Opening a PR / Babysit / Shipping** | 只在 `.mmw/target.json` `delivery: pr` 的仓库 | Deliver a change | 导入 | pstack mode 第 133、134、143 行 |

直接指向能力技能、不单列 playbook 的行（只调用一个技能、没有自己的门槛与交付物，L7 C.6 信号 5）：原型 → `prototype`；架构改进 → `improve-codebase-architecture`（它的决定进 **Define a change** 的入口）；画图 → `diagram-design`；写 `AGENTS.md` → `manage-agents-md`；教学 → `teach`；问卷 → `to-questionnaire`；人做的步骤 → `wizard`；看不懂 → `wait-what`；调研成文 → `research`。

### 4.3 逐份 playbook

「步骤」一列只写每步的标题与点名的组件；「T/PC」列出 R14 的原文来源编号，证明不需要新写规则。

#### P1 Define a change（`define-a-change.md`）

- **Entry**：一段对话或想法；`wayfinder` 地图清空；`triage` 判 `ready-for-agent`；`improve-codebase-architecture` 选定的决定；`prototype` LOGIC 或 EXP 分支的结论（补 N10 B4）。
- **所有权**：You own the batch. The user owns every product call.（`to-spec` 第 6 行：「A call on what the user sees, what happens to money, or what is in scope … is not yours」）
- **步骤**：
  1. **Decide who checks the work.** 小到用户会当场检查 → **Feature**；否则继续。出处 ask-matt 主流程第 3 步（R12 M29）。补 N10 B3。
  2. **Reach a shared understanding.** `grilling` 与 `domain-modeling`（即 `grill-with-docs` 的组合）。已达成就 `skip:`。
  3. **Settle observable questions by running them.** 能靠运行得出答案的分叉 → `prototype`（pstack mode 第 20 行）。
  4. **Take the interface from its contract.** 有界面：screen contract 有未对齐的行就先走 **Design an interface**。出处 `to-spec` 第 2 步第 22 行。
  5. **Write the spec.** `to-spec`；几份 spec 时一次只写第一份（`several-specs.md`）。
  6. **Cut and publish the tickets.** `to-tickets`，再 `verify-ticket.py <spec> --lint`、`--publish --drafts`（`to-tickets` 第 7 步；`linting.md`）。
  7. **Hand the batch over.** 告诉用户「run a night on spec #N」；**Run a night** 拥有其余。出处 `to-tickets` 第 160 行。
- **规则簇**：`#### Session boundaries`（同一会话还是新会话，见 `references/phase-boundaries.md`；`grill-with-docs` 第 7 行「in this same session」，`wayfinder` 第 126 行「in a fresh session」）。
- **原则**：`the-baseline-is-a-contract`、`name-it-as-the-glossary-does`、`a-check-must-be-able-to-fail`、`the-author-does-not-judge`（`to-tickets` 第 63 行，判断交给另一个会话）。
- **Where you are**：人在场；tracker 上 spec 是否已发布、票是否已起草（`principle-the-tracker-is-the-state`）。
- **Reply**：spec 号、票号、lint 结果、留给用户的产品问题。
- **T/PC**：T16–T18、T22–T24、T14、T36；PC8、PC9、PC27。

#### P2 Map a large effort（`map-a-large-effort.md`）

- **所有权**：You own the map.（`wayfinder` `## Plan, don't do`）
- **步骤**：1 **Chart the map.** `wayfinder` `### Chart the map`。2 **Resolve one decision ticket at a time.** `wayfinder` `### Work through the map`；调研票 → **Investigation** 或 `research`；原型票 → `prototype`；界面票 → **Design an interface**。3 **Start the spec in a fresh session.** 地图清空 → **Define a change**（`wayfinder` 第 126 行）。
- **Where you are**：地图在 tracker 上。
- **Reply**：地图上已决与未决的票。
- **T**：T21、T17、T36 on-ramp 第 3 条。

#### P3 Design an interface（`design-an-interface.md`）

- **Entry**：界面要设计；翻新旧产品（`interface-and-remake.md` 的选择清单）；设计系统要建（`design-pages` `references/design-system.md`）。
- **步骤**：1 **Find the winning layout.** `prototype` 的 UI 分支。2 **Take it to Claude Design.** `design-pages`（只有带 Claude Design 工具的会话能做，`design-pages` 第 21 行的闸门留在技能里）。3 **Pull the design package.** `design-pages` pull；第一次 pull 拆掉原型脚手架（`pull.md` `## After the first pull`）。4 **Write the screen contract.** `write-screen-contract`。5 **Return to the spec.** 首次 → **Define a change** 第 5 步；重跑 → `to-spec` 的 `references/revising-a-spec.md`（`write-screen-contract` `## Next`）。
- **规则簇**：`#### Change classes`（`edit-pages.md` `## Next` 的 `改动分类` 四路）；`#### Contract children answered by a pull`（`pull.md` 对应段；run-a-night 的 contract 行引用它）。
- **原则**：`the-baseline-is-a-contract`。
- **Reply**：设计包路径、screen contract 的行数与对齐状态。
- **T**：T22、T25、T26、T16 第 2 步。

#### P4 Triage（`triage-an-issue.md`）

- **步骤**：1 **Judge the issue.** `triage` 的状态机。流水线自己开的 issue → **Accept a night** 的 `#### Pipeline issues`。2 **Turn a ready issue into a spec.** `ready-for-agent` → **Define a change**（`triage` 第 82 行）。3 **Close the issue against its spec.**（同行）。
- **Reply**：四种结果之一与理由。
- **T**：T19 第 82、94 行。

#### P5 Run a night（`run-a-night.md`）

- **所有权**：取自 `night.md` 第 3–11 行（orchestrator 只推进、只路由，不改代码）。
- **Where you are**：`bash scripts/dispatch.sh where <spec>` 印 `RESUME: run-a-night § <步骤标题>`（R12 K-3）。
- **步骤**（`night.md` `## 1`–`## 5`）：
  1. **Check and open.** `dispatch.sh check <spec>`、`open <spec>`。
  2. **Find what the batch cannot run on.** `target_config.py --check`；`verify-ticket.py <spec> --lint`。
  3. **Advance, then end your turn.** `dispatch.sh advance <spec>`（`principle-woken-not-polled`）。
  4. **Act on each wake.** mode `## Re-entry`，然后 `references/orchestrator-events.md` 里该事件的那一行。
  5. **Run the closing pass.** `reverify`、`findings`、`route`、`--lint`；Memory 决定用 `shared-experience`（`dispatch.sh memory-list`）。
  6. **Summarize and retro.** `dispatch.sh summary`，然后 `retro` 技能，直到 `spec.retroed`。
  7. **Hand the night to the user.** → **Accept a night**。
- **规则簇**：`#### Contract children`（`night.md` 第 96–100 行）；`#### Closing pass`（`## 4` 整块）；`#### Suspending the night`（原节）。
- **reference**：`references/orchestrator-events.md` 与 **Run one ticket** 共用。它补齐 R14 W1 的两处缺口：`MMW turn guard:` 一行（N11 missing_edges 第 1 条），`watchdog.py` 第 94–109 行的全部八种告警各一行（R12 M16）。
- **原则**：`woken-not-polled`、`the-tracker-is-the-state`、`silence-is-never-a-pass`、`rerun-dont-reroute`、`the-baseline-is-a-contract`、`separate-before-serializing-shared-state`。
- **Reply**：`NIGHT SUMMARY` 与 `spec.retroed`。
- **T/PC**：T7、T27、T37 的 orchestrator 部分；PC4、PC5、PC12、PC14、PC24。

#### P6 Run one ticket（`run-one-ticket.md`）

- **步骤**（`one-ticket.md` 四步）：1 **Open the ticket's watch.** `dispatch.sh open-ticket <n>`，把任务板 URL 给用户。2 **Start the worker, then end your turn.** `dispatch.sh start <n> worker`。3 **Act on each wake.** `## Re-entry` 与 `references/orchestrator-events.md`。4 **Land it.** `dispatch.sh land <n>`，Done when exit 0。
- **Reply**：`land` 的摘要行；`bounced` 时哪张票、`ticket.bounced` 写了什么。
- **T**：T8。

#### P7 Work a ticket（`work-a-ticket.md`）

- **Entry**：`start` 起的 worker（提示词点名）；自己拿票（先 `dispatch.sh adopt <n>`，`inside-a-ticket.md`）；被提示回来（`RESUME:`）。
- **所有权**：You own this ticket's branch until its closeout. The orchestrator lands it.（`implement` 第 99 行）
- **Where you are**：`verify-ticket.py <n> --preflight` 印 `RESUME: work-a-ticket § <标题>`（D7）。
- **步骤**（`implement` 全文；标题即 `resume_at` 的新返回值）：
  1. **Claim.** `verify-ticket.py <n> --preflight`；`NOT_READY` 就停。
  2. **Read yourself in.** `implement` 第 16 行的读入顺序；有 screen contract → `ui-acceptance` 的 `references/writing-interface-code.md`。
  3. **Write the code.** `tdd`，限定句：「at the seams the ticket's `## Seam` names; the first red test is the case a `CHECK:` names」（`tdd` 第 22 行本仓加句与 `implement` 第 30 行）。
  4. **Integrate and run every criterion.** `dispatch.sh integrate <n>`，`verify-ticket.py <n>`（原 closing 第 1 步）。
  5. **Post the decisions.** `verify-ticket.py <n> --decisions <file>`（第 2 步）。
  6. **Get reviewed.** `dispatch.sh start <n> reviewer`，结束回合；修票内 finding，写 `refuted:`，票外开 `finding` 子票（第 3 步）。限定句：「the fix round is the pass `tdd` judges with fresh eyes」（`tdd` 第 38 行本仓加句）。
  7. **Run every criterion one final time.** `verify-ticket.py <n> --reverify --actor worker`（第 4 步）。
  8. **Audit against the ticket.**（第 5 步）
  9. **Tell the touched tickets.** `verify-ticket.py <n> --touched`（第 6 步）。
  10. **Draft the closing comment.** `verify-ticket.py <n> --draft`（第 7 步）。
  11. **Close out.** `verify-ticket.py <n> --closeout <draft>`（第 8 步）；自己拿票的 → 告诉用户去跑 `land`（`inside-a-ticket.md` `## After the closeout`）。
- **规则簇**：
  - `#### Baselines`：`implement` 第 22 行的规则部分；理由换成点名 `the-baseline-is-a-contract`、`silence-is-never-a-pass`。
  - `#### Decisions I made on my own`：第 23 行的写法（决定行写给 reviewer 与早上的用户）。
  - `#### Code`：第 24–27 行，点名 `migrate-callers-then-delete-legacy-apis`、`subtract-before-you-add`、`laziness-protocol`；「keep intact」清单留在这里（它绑定票的 **What to build**、**Seam**，L7 C.2）。
  - `#### Owns`：第 28 行；点名 `separate-before-serializing-shared-state`。
  - `#### Sub-issues`：`sub-issues.md` 第 13–23 行的五个 kind 问题。
  - `#### ABANDON kinds`：第 76 行。
  - `#### Integration`：第 78 行的合并规则；`sequence-verifiable-units` 的本地限定：「"rebase onto clean trunk" is `dispatch.sh integrate`, a merge; never rebase」（第 78 行「Never rebase, abort or push from this integration command」）。
  - `#### While the product runs`：指向 `ui-acceptance` 的 `## Five rules while the product is running`（替代 `PRODUCT_RULES` 提示词，`dispatch.sh` 第 109 行）；`fault` 子票后停（`ui-acceptance` 第 38 行）。
  - `#### Shared experience`：何时开 Memory、何时存 → `shared-experience`。
  - `#### Events`：`reviewer.reported`、`reviewer.lost`、`worker.queued` 三行（`relay.py` `WAKES`，R14 W1）。
- **Reply（交付物）**：通过 `--closeout` 的收尾评论。
- **T/PC**：T1–T5、T9、T13、T15、T28、T29、T37 的 worker 部分；PC1、PC2、PC8、PC9、PC12、PC21、PC22。

#### P8 Review a ticket（`review-a-ticket.md`）

- **Entry**：提示词点名票与 base commit（`dispatch.sh` 第 1967 行）。
- **所有权**：取自 `code-review/SKILL.md` 第 8 行：「This review is the first reading by anyone who did not write it: what it reports, the worker fixes before the ticket closes; what it misses ships.」
- **步骤**（`session.md` `## 1`–`## 5`）：1 **Pin the diff.** 2 **Run the axes.** 四份简报 `references/review-axes/*.md`，一条消息同时发出，只读。3 **Verify every finding the axes report.**（`principle-prove-it-works`）4 **Sort every finding into in-ticket or out-of-ticket.** 5 **Write one review report on the ticket.** `verify-ticket.py <n> --review <file>`，它唤醒 worker。
- **规则簇**：`#### Active Rules`（reviewer Rules 来自 Nowledge）；`#### Report format`（`session.md` 第 73–95 行，它是交付物本身，L7 C.4）。
- **原则**：`the-author-does-not-judge`、`prove-it-works`、`silence-is-never-a-pass`（`unverified:`）。
- **Reply（交付物）**：`REVIEW` 报告。
- **T**：T10、T11。

#### P9 Accept a night（`accept-a-night.md`）

- **步骤**：1 **Read the morning queues.** `docs/agents/issue-tracker.md` `## Morning queries`：先 `needs-triage`，再 `ready-for-human`。2 **Route each pipeline issue.** `triage` 加 `#### Pipeline issues`，`dispatch.sh route`。3 **Put what only the user can do in front of them.**（`principle-human-steps-stay-human`）4 **Finish the accepted night.** 只在用户验收之后：`dispatch.sh finish <spec>`（`night.md` `## 6`）。
- **规则簇**：`#### Pipeline issues`：`triage/references/pipeline-issues.md` 全文（「A ticket handed back」「ready-for-agent」两节）。
- **Reply**：落地了什么、还开着什么、等用户的是什么。
- **T**：T20、T19 第 90 行、T34、`night.md` `## 5` 末段与 `## 6`。

#### P10 Ship a release（`ship-a-release.md`）

- **所有权**：Ship what is on the current branch now.（`exe-release` 第 10 行）
- **步骤**（`exe-release` `## 1`–`## 5`）：1 **Check the preconditions.** 2 **Name the products for this run.** 3 **Drive one product per loop.** `exe-release` 的 `scripts/release-flow.sh`。4 **Check every package came from one commit.** 5 **Hand the install test to the user.**（`human-steps-stay-human`）
- **规则簇**：`#### Driving the loop`：`driving.md`（「Do not resume from session memory」→ 点名 `the-tracker-is-the-state`）。
- **Reply**：每个产品的包路径与提交；等用户安装实测。
- **T**：T30。

#### P11 Onboard a repository（`onboard-a-repository.md`）

- **步骤**：1 **Set up the tracker docs.** `setup-matt-pocock-skills`（第 51、63 行的流水线约定作为本步限定）。2 **Write AGENTS.md.** `manage-agents-md`，含 `mmw` 那一行。3 **Give it checkers.** `code-checkers`；结果写进 `.mmw/target.json` `checks`。4 **Fill the target.** `ui-acceptance`，`target_config.py --check`。5 **Prove a night can start.** `dispatch.sh check <spec>` 在一份测试 spec 上 exit 0。
- **Reply**：`target.json` 是否完整、`check` 的结果。
- **T**：T32、T33。

#### P12 Authoring or modifying a skill（`authoring-a-skill.md`）

- 与 pstack 同名文件**不导入**。理由（第 9.2 节）：pstack 原文末段「Tell it to do the thing and skip the reason」与 SSR 事实 1「next to a rule, the reason for it」正面冲突。导入脚本遇到同名 playbook 时报冲突，交用户决定。
- **步骤**：1 **Write it with `writing-for-agents`.** 2 **Place each sentence by its type.** 按本文第 1.1 节（D14 之后的 `docs/skill-set/SKILL-SET-RULES.md`）。3 **Record upstream edits.** merge-note；影响消费仓库 → downstream-note。4 **Run the smallest suites that prove it, and the wiring lint.** `TESTING.md` `## Which suites a change needs`；`check_wiring.py`。5 **Deliver it.** → **Deliver a change**。
- **原则**：`encode-lessons-in-structure`、`laziness-protocol`（「Consolidate decisions」对应 SSR 的「one home」）。
- **T**：T35、T38。

#### P13 Bring in a component（`bring-in-a-component.md`）

- 第 9 节是它的规则来源。**步骤**：1 **Pull the upstream.** `git subtree pull` 进 `upstream-pstack/`。2 **Pass the entry checks.** 第 9.1 节的五问。3 **Place it.** 能力技能 → `skills.txt` 加 `ps/<name>`；playbook、原则 → `bash scripts/import.py <路径>`。4 **Register it.** 路由表或原则索引加一行；有改动就写 merge-note。5 **Prove the wiring.** `check_wiring.py`、`install.sh --check`。6 **Deliver it.** → **Deliver a change**（技能列表变了，需要用户授权跑 `install.sh`）。
- **T**：根 `AGENTS.md` `<important if … upstream …>`。

#### P14 Deliver a change（`deliver-a-change.md`）

- **步骤**：1 **Find how this repository takes changes.** 在票的工作树里 → 交付就是 closeout，本 playbook 不适用（`implement` 第 99 行）；本仓库（MMW 自己）→ 第 2 步；`.mmw/target.json` `delivery: pr` → **Opening a PR**（导入原文）；其余 → 提交到当前分支并告诉用户（上游 `implement` 末句「Commit your work to the current branch.」）。2 **Promote it.** 根 `AGENTS.md` `## Gotchas` 第 1 条的四步；第三步在任何 watch 开着时等（H5）。
- **Reply**：提交、发布到了哪一步、还差什么。

#### P15–P19 导入的 pstack playbook

`bug-fix.md`、`feature.md`、`investigation.md`、`session-pickup.md`、`pause-safely.md` 原文不改，详见第 9.3 节。每份在 MMW 里依赖的组件与别名：

| playbook | 依赖 | 靠什么落位 |
|---|---|---|
| `bug-fix.md` | control 槽位、`how`、`why`、`architect`（→ `arena`）、`interrogate`、`tdd`（MMW 已装的同名技能）、`sequence-verifiable-units`、Opening a PR、Cursor's `/loop`、「your configured bug-fix model」 | mode 三条别名；`## Host tools`；`## Subagents` 的角色查询 |
| `feature.md` | `how`、`architect`、`arena`、`interrogate`、`separate-before-serializing-shared-state`、`model-the-domain`、`sequence-verifiable-units`、Laziness Protocol、`**Comments**` 节 | 同上；mode `## Comments` |
| `investigation.md` | `how`、`why`、`unslop`；「throughput checkpoint」概念（定义在 `feature.md` 第 3 步） | `feature.md` 同批导入 |
| `session-pickup.md` | `agent-transcripts/`、cloud-agent URL、`guard-the-context-window`、`prove-it-works` | `## Host tools` 的 transcript 行 |
| `pause-safely.md` | `wip:` 提交、`/tmp/<slug>-resume.md`、show-me-your-work | 无宿主依赖 |

MMW 对 `bug-fix.md` 的补充放在 mode 的触发行（「难 bug → `diagnosing-bugs`」），不改导入文件。这样 N10 B6「`diagnosing-bugs` 之后没有下一步」由 `bug-fix.md` 第 3 步「If it crosses a function boundary, `architect` first」接住。

### 4.4 覆盖检查

用户草图的十二类工作流与 playbook 的对应：白天定义 → P1（及 P2、P3）；夜间编排 → P5；做一张票 → P7；评审一轮 → P8；单票 → P6；早上验收与 finish → P9；修 bug → `bug-fix.md`；出包 → P10；分诊 → P4；调研 → `investigation.md` 加 `research` 行；给仓库接入 MMW → P11；写技能 → P12。另有 P13、P14、`feature.md`、`session-pickup.md`、`pause-safely.md` 五份超出草图。

---

## 5. 能力技能总目录

### 5.1 MMW 自有的能力技能

「剥离」列写从技能里拿走的内容与去处；「剩下」写纯能力。行数带「约」的是推断（R14 第 6 节），实测在迁移后（U-6）。

| 技能 | 剩下（纯能力） | 剥离 → 去处 |
|---|---|---|
| `setup-mmw`（新） | 改角色的宿主、模型、档位与 runner；只读查询一个角色的值；`hosts.json` | 来源：`dispatch/references/editing-models.md`、`models.py`、`hosts.json` |
| `shared-experience`（新） | 按 index 打开记录、按错误搜索、三条件判断何时存、怎样更正与 deprecate；`references/saving-memory.md` | 来源：`implement` `## Shared experience while implementing`、`saving-memory.md`、`night.md` `## 4` Memory 决定段的做法部分。「何时用」留在 P5、P7 |
| `verify-ticket` | 判据怎样跑、`CHECK`/`EXPECT` 的判定、子票命令、lint 与发布命令（约 25 行）加脚本 | 第 16 行「A worker's claim … are steps of the `implement` skill」→ 删（P7 承担）；`## Reached from here` → mode 触发行；`sub-issues.md` 第 11 行 kind → 读者 → P7、`orchestrator-events.md`；第 13–23 行 → P7 `#### Sub-issues`；`linting.md` 的「何时 lint」→ P1、P5 |
| `ui-acceptance` | 全部规则、五份 reference、九个脚本；接收 `writing-interface-code.md`（约 430 行） | description 末句「before writing a page ticket's code」→ mode 触发行；第 38 行 → P7；规则 3–5 的理由 → 点名 `human-steps-stay-human`、`rerun-dont-reroute`；`PRODUCT_RULES` 提示词 → P7 `#### While the product runs` |
| `advisor` | `consulting.md` 的 `## Start it`、`## The brief`、`## The question stays open`；`advising.md` | description 的触发保留（直接调用时要用）；`## When it is worth a session` 的门槛同时成为 mode 触发行（mode 引用它，不复述） |
| `retro` | 第 1–13 步、`## Prevention destinations`（加 `principle`、`playbook`、`mode`） | description「right after the dispatch skill's `summary` records `spec.closed`」→ P5 第 6 步；第 186 行 → 删；第 8 行「从 `origin/<base branch>` 跑」是本能力的前置条件，就位 |
| `design-pages` | pull、draw、design-system、两份模板、`## The state list`（与 `state-list-format` 同放，R14 W6） | `edit-pages.md` `## Next`、`pull.md` `## Reached from here` → P3；`## A contract child answered by this pull` → P3 规则簇；第 21 行「worker 从不做」→ P7 |
| `write-screen-contract` | 第 1–7 步、`Re-runs`、格式文件、三个脚本 | `## Next` → P3 |
| `exe-release` | `key.md`、`new-product.md`、release engine 脚本（约 320 行） | `SKILL.md` 第 1–5 步、`driving.md` → P10 |
| `code-checkers` | 全部 | 第 6、8 步的接入顺序 → P11 |
| `manage-agents-md` | 全部 | 第 50 行子代理默认 → mode `## Subagents` |
| `to-spec`（分叉为 MMW 自有） | 上游 75 行加 MMW 的 spec 能力（seam、状态可达、API contract、visual acceptance、Critical flows、Sources），约 135 行 | description 触发句 → 路由表；第 2 步的退回路线 → P3；`several-specs.md` 的「停下、让用户重跑」→ P1；`## Next` → 删 |
| `to-tickets`（分叉为 MMW 自有） | 切片、五问、四行判据、blocking edges、Owns、`<issue-template>`、三份 reference（约 450 行） | 第 20 行、第 160 行 → P1；第 6 步子代理段 → mode `## Subagents` |
| `dispatch` | —（解散） | `SKILL.md` 表 → 路由表；`## On waking` → mode `## Re-entry`；`night.md` → P5 与 `orchestrator-events.md`；`one-ticket.md` → P6；`inside-a-ticket.md` → P7 Entry；`editing-models.md` → `setup-mmw`；脚本 → `skills/mmw/scripts/` |

**为什么 `to-spec`、`to-tickets` 分叉而不是回原文**：它们的正文多数是 MMW 的能力，不是流程。`merge-notes/to-spec.md` 第 31 行自认「不到一半的行是上游的」（R4 V11）；`to-tickets` 被 `merge-notes/README.md` 列为「本仓自有正文的技能」（N10 第 6 节）。把 MMW 的能力留在上游目录，每次 `git subtree pull` 都在这些段落冲突（R12 M5）。分叉后上游目录回到原文、不安装（`skills.txt` 不能有重名，`install.sh` 第 164 行），MMW 版装为 `self/to-spec`、`self/to-tickets`。

### 5.2 上游（mattpocock）能力技能

| 技能 | 升级后 | 撤回的本仓改动 → 去处 | 保留的边缘改动（merge-note 记录） |
|---|---|---|---|
| `implement` | **回原文**（15 行，带 `disable-model-invocation: true`，恢复 `agents/openai.yaml` `policy`） | 全部正文 → P7；`writing-interface-code.md` → `ui-acceptance`；`saving-memory.md` → `shared-experience` | 无。是否继续安装：用户决定 0.5 第 4 条 |
| `code-review` | **回原文**（87 行双轴评审，模型可触发） | `session.md` → P8；四个 axis → `references/review-axes/` | 无 |
| `grilling` | **回原文**（28 行） | 第 28 行 → mode `## Autonomy` 与原则；第 30–44 行 → `attack-the-premise`、`redesign-from-first-principles`、`fix-root-causes`、`subtract-before-you-add`、`laziness-protocol` | 无（`merge-notes/grilling.md` 自认这段是外加判断，R14 4.2） |
| `tdd` | 回原文，差 3 句 | 第 22、38 行票句 → P7 第 3、6 步的限定句 | 第 26 行宿主中立 |
| `grill-with-docs` | 回原文 | 第 7 行「name the `to-spec` skill as the next step, in this same session」→ P1 | 「Call the Skill tool」改为读 `SKILL.md`（宿主中立） |
| `wayfinder` | 回原文（含 `disable-model-invocation: true`） | description 触发句 → 路由表；第 6 步 → P2；`mmw:map` 标签 → `docs/agents/issue-tracker.md` 已持有 | 宿主中立的子代理措辞 |
| `triage` | 回原文（含开关） | description 触发句 → 路由表；第 70、82、90、94 行 → P4、P9；`pipeline-issues.md` → P9 规则簇 | 标签约定在 `docs/agents/triage-labels.md`（配置） |
| `to-questionnaire` | 回原文（含开关） | description 触发句 → 路由表 | 「you」改「the user」 |
| `prototype` | 回原文，加能力扩展 | 规则 6 的「之后做什么」、`UI.md` 第 3 步交接与 `## Next` → P1、P3；`## State list` 格式 → `design-pages` | EXP 分支（`EXP.md`、`evidence-page.md`，确属能力扩展，旁加文件） |
| `improve-codebase-architecture` | 回原文 | `### 4. Hand the decision on` → P1 Entry | `HTML-REPORT.md` 用 `diagram-design`；第 41 行免 §3（调用方限定，L7 C.2） |
| `resolving-merge-conflicts` | 回原文，加能力扩展 | 第 2 步「After a clean merge of `origin/<base branch>`, identify each ticket …」→ P7 `#### Integration` | 「clean merge 但检查变红」的触发（能力扩展） |
| `codebase-design` | 回原文 | 第 10 行「the task that brought you here decides what you do next」→ 删（mode 与 playbook 已承担） | 第 16 行术语规则放宽 |
| `setup-matt-pocock-skills` | 回原文，加本仓格式 | 第 17、51、63 行 → P11 | 第 82–84 行写 `## External References` 的格式（与 `manage-agents-md` 第 150 行一致） |
| `writing-for-agents` | 回原文 | 第 8 行指向 SSR 的一句 → 删；SSR、RSS → `docs/skill-set/`（R12 K-38） | description 放宽为「any document an agent will consume」 |
| `teach`、`wait-what`、`handoff`、`grill-me`、`wizard` | 就位 | 无流程句（R14 4.2） | 工作区规则、`VISUAL.md`、宿主中立措辞 |
| `diagnosing-bugs`、`domain-modeling`、`research` | 就位（与上游零差异，R14 第 6 节） | — | — |
| `ask-matt`（未安装的残留目录） | **回原文**（N10 B10：它不是 unmodified copy） | `PHASE-BOUNDARIES.md` 的上游原文副本 → `skills/mmw/references/phase-boundaries.md`；主流程第 3 步的「谁来检查」→ P1 第 1 步 | — |
| `diagram-design`（第二个上游） | 就位 | — | merge-note 已有 |

### 5.3 从 pstack 导入的能力技能

见第 9.4 节逐个分析。首批：`how`、`why`、`architect`、`arena`、`interrogate`、`show-me-your-work`、`unslop`。与已装技能重名的 `tdd`、`teach` 不导入：MMW 的同名技能满足 pstack 组件里「the **tdd** skill」的点名（第 9.2 节）。

### 5.4 能力技能的共同规则

- 以交付物结尾（pstack 的 `## Output Format`、`**Reply:**`，L7 A.3），不写「下一步」。
- 不出现角色与流程词（lint 第 5 类）：`the worker`、`the orchestrator`、`dispatched onto`、`you were started as`（例外见下）、playbook 名、`## Next`、`Reached from here`、`return to`、`hand over to`。
- 例外：`advisor` 的「you were started as the advisor」是它作为另起会话的入口，与 pstack agent 定义同类（L7 A.7）；lint 允许在 description 与首段各出现一次，需要注释标明。
- 自带的人工闸门保留（L7 A.3），优先级由 mode 一句决定（第 3.2 节）。
- 自检问题（R13 E3）：离开 MMW 的流水线，在一个没有 `.mmw/`、没有票的仓库里，它还能用吗？不能用的句子不属于它。`verify-ticket` 的「票」是它的对象，不是它的调用方，所以不违例。

---

## 6. 原则层

### 6.1 存放、格式与引用

- **存放**：`skills/mmw/principles/<slug>.md`，普通文件，不是技能（H2：pstack 的原则全带 `disable-model-invocation: true`，装成技能在 Claude Code 上按名调不到；装成模型可触发的技能又会让 25 条 description 进每个会话的技能列表，与「只被点名」相反，R13 E5）。
- **格式**：与 pstack 原则逐字同构（L7 A.4）：frontmatter `name: principle-<slug>`、`description: "Apply <情境>. <规则摘要>."`，pstack 原有的 `disable-model-invocation: true` 照留（文件不是技能，这个键不起作用，留着让导入改 0 处）；正文 `# <Title>`、一到三句规则、`**Why:**`、`**Pattern:**`，可选 `**Stop:**`、`**The test:**`、`**Boundaries:**`、「Distinct from …」。
- **MMW 自有原则的写法约束**：规则与理由逐字取自第 6.2 节「出处」列的原文；原文没有理由的，不写 `**Why:**`（pstack 23 条里也只有 16 条有，L7 A.4）。
- **引用**：MMW 自己写的文字只用一种写法「the **<slug>** principle」，可跟一句本地限定。pstack 的五种写法由 mode `## Principles` 的解析规则接受，导入的文字不改。
- **被读到的方式**：mode 索引每个任务读；应用某条时读全文；playbook、能力技能、reference、其他原则按名点名；回复（或无人时的交付物）点名改变了决定的那条。
- **方向**：原则只指向原则或能力技能，不指向 playbook、脚本、mode（L7 B.2 硬规律 1；lint 第 1 类）。

### 6.2 MMW 自有原则（10 条，Pipeline 组）

| slug | 规则（取自出处原文） | 理由出处 | 被谁点名 | 吸收的 R14 编号 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 一道闸口跑了一遍却什么都没做、或一项检查跑不了，要当作这样报告；检查红了就修产品或放弃判据，从不弯 baseline、harness 或测试 | ADR 0008 第 8 行「它跑了一遍却什么都没做，有人会发现吗？」；`implement` 第 22 行「An honest `HANDOFF REQUIRED` costs them one look in the morning; a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on this one inherits it.」 | P5、P7、P8；`ui-acceptance` 第 10 行；`code-checkers` 第 58 行；`retro`；`CODING_STANDARDS.md` `## Skills and scripts` 第 4 条 | PC1、PC22 |
| `a-check-must-be-able-to-fail` | 一项检查要在行为缺席时失败才算证明；失败输出里也会出现的 `EXPECT` 证明不了什么；因缺文件、导入错误而红的测试不算红 | `to-tickets` 第 84 行「`ok`, `passed` or `done` on their own also appear in failing output」（R12 M25）；`implement` 第 30 行 | P1、P7；`ui-acceptance` 的 oracle reference；`code-checkers` 第 5 步；`git-hooks.md` | PC2 |
| `the-baseline-is-a-contract` | 已定的结论（用户的回答、胜出的原型、签字的页面）照抄，不凭记忆重写、不改进；不成立时开 `contract` 子票公开重开，从不悄悄改或绕 | `implement` 第 22 行「A baseline is a decision someone already paid for … Rewriting it from memory, or improving it, reopens that decision where nobody who made it can see; a `contract` child reopens it where they can.」 | P1、P3、P5、P7、P9；`design-pages`；`write-screen-contract` 第 18 行；`to-tickets` 第 174 行 | PC8（15 处） |
| `the-tracker-is-the-state` | 你在哪一步，看票上的事件，不看会话记得什么；状态只经写事件的脚本改变 | `dispatch/SKILL.md` 第 8 行（R12 M25）；ADR 0019；`exe-release/references/driving.md`「Do not resume from session memory」 | mode `## Re-entry`；P5、P6、P7、P10；`verify-ticket` | PC5、PC6 |
| `woken-not-polled` | 谁都不轮询另一个 agent；起了别人就结束回合，等 relay 唤醒 | ADR 0010 标题；`night.md` 第 11 行 | P5、P6、P7；`ui-acceptance` 第 38 行 | PC4 |
| `rerun-dont-reroute` | 被打断的命令原样重跑（命令可重入）；起不来的东西停下并报告，不循环重试、不绕过、不改环境 | `dispatch/SKILL.md` 第 25 行「A wake can cut short a command you were running.」；`ui-acceptance` 规则 5「A workaround built instead hides it from every ticket after yours.」 | mode `## Re-entry`；P5、P7；`ui-acceptance` 规则 4、5 | PC17、PC18 |
| `the-author-does-not-judge` | 对工作的判断交给没写它的读者（另一个会话或子代理） | `code-review/SKILL.md` 第 8 行「This review is the first reading by anyone who did not write it: what it reports, the worker fixes before the ticket closes; what it misses ships.」 | P1（`to-tickets` 第 63 行）、P7、P8；`advisor`；导入的 `show-me-your-work`「Self-review is not a substitute」 | PC20 |
| `name-it-as-the-glossary-does` | 领域词表里有词的东西，用那个词 | `implement` 第 16 行；理由取自 `shared.md` 规则 6「I take that name to search, to write tickets, and to hand to the next agent」 | P1、P4、P7；`domain-modeling` | PC27 |
| `no-secrets-in-artifacts` | 凭据不进票、Memory、交接文档、日志、spec | `diagnosing-bugs` `## Redact`；根 `AGENTS.md` `## Gotchas` 末条「a credential written into any file under its `scripts/<…>` is loaded by every other run」 | `shared-experience`；`handoff`；`ui-acceptance` `product-answers.md` 第 96 行 | PC28 |
| `human-steps-stay-human` | 只有人能做的步骤单列交给人；agent 不代做，也不报告成做了 | `ui-acceptance` 规则 3「satisfying it makes a broken automation look healthy, and the next run has no person in it」；`shared.md` 规则 11 | P9、P10；`ui-acceptance`；`to-tickets` `person-ticket.md`；`wizard` | PC29 |

四条门槛（L7 A.4）逐条都满足：短名；触发情境可观察（闸口没干活、写 `EXPECT`、baseline 不成立、被唤醒、命令被打断、要判断工作、给东西命名、要写产物、遇到只有人能做的步骤）；能改变一个具体决定；跨两个以上的 playbook 或能力技能。

### 6.3 导入的 pstack 原则（15 条）与吸收关系

| pstack 原则 | 组 | 吸收的 MMW 规则 | 调用方留下什么 |
|---|---|---|---|
| `prove-it-works` | Verification | PC1 的「真物验证」部分、PC11、PC14 | P8 第 3 步点名；`shared.md` 规则 4、15 不动（U0） |
| `fix-root-causes` | Verification | PC19 的一部分、PC18 的一部分 | `bug-fix.md` 原文已点名 |
| `sequence-verifiable-units` | Verification | — | P7 `#### Integration` 的本地限定（不 rebase） |
| `test-behavior-not-implementation` | Verification | PC23 | `tdd` 的做法不动 |
| `laziness-protocol` | Core | PC21、PC24 的一部分、PC16（「Consolidate decisions」） | P7 `#### Code` |
| `subtract-before-you-add` | Core | PC21 | P7 `#### Code` |
| `attack-the-premise` | Core | PC19（`grilling` 第 32–44 行） | `grilling` 回原文 |
| `redesign-from-first-principles` | Core | PC19 | 同上 |
| `build-the-lever` | Core | PC7 | `sequence-verifiable-units` 点名它，同批导入 |
| `make-operations-idempotent` | Architecture | PC17 的设计一侧 | mode `## Re-entry` 第 1 条 |
| `migrate-callers-then-delete-legacy-apis` | Architecture | PC21 | P7 `#### Code` |
| `separate-before-serializing-shared-state` | Architecture | PC12 | P5、P7 `#### Owns`；`to-tickets` 保留 Owns 与 blocking edges 的领域规则（L7 C.2） |
| `guard-the-context-window` | Delegation | PC26 | mode `## Subagents` |
| `never-block-on-the-human` | Delegation | PC9 | mode `## Autonomy` 写优先级 |
| `encode-lessons-in-structure` | Meta | PC25、PC7 | `retro` 的去处；P12 |

依赖闭包另有 4 条：随 `architect` 的 `exhaust-the-design-space`、`foundational-thinking`、`outcome-oriented-execution`（第 9.4 节），随 `feature.md` 的 `model-the-domain`（第 9.3 节）。

不建原则、改为引用 `shared.md` 的 MMW 规则：PC10（规则 10）、PC13（规则 13）、PC14（规则 15）、PC24（规则 1「Anything outside the scope I gave you is asked about, not done」）。理由：`shared.md` 已在 4 个宿主常驻，它就是这些规则的家（U0）；再建原则会成第二份。PC3（读拒绝的一侧）、PC15（只读）进 mode，不是原则：前者是一条触发，后者绑定宿主缺只读档这一机制（L7 C.2 第一行）。

### 6.4 与 MMW 已有规则重合时怎么办（导入规则）

1. **同义**：导入 pstack 原文；MMW 各处的复述换成「点名 + 一句本地后果」。例：PC12 → `separate-before-serializing-shared-state`，`implement` 第 28 行只留「one file has one writer at a time and the cut missed an edge」这一本地后果。
2. **部分覆盖**：导入 pstack 原文，同时保留 MMW 自有原则覆盖剩下的部分，在 MMW 原则里写「Distinct from」。例：`silence-is-never-a-pass`「Distinct from **prove-it-works**, which says how to verify; this says what to report when a check did not run or did nothing.」（区别句是 MMW 写的，内容取自 ADR 0008 与 pstack 原文的对照，不是新规则。）
3. **冲突**：导入原文，冲突由 mode `## Autonomy` 或所服务 playbook 的限定句按第 3.2 节的层级解决。例：`never-block-on-the-human` 的不可逆动作确认 vs 无人会话。
4. **与 `shared.md` 重复**：照样导入。划界：`shared.md` 管「怎样向用户汇报、谁决定什么」，原则管「怎样做这一步」。`shared.md` 不改（U0）。

### 6.5 原则与 `shared.md` 的关系

- `shared.md` 是用户对所有项目的全局规则，层级最高，MMW 不改写（U0）。
- mode 不复述它；原则可以把它的规则号当作理由出处（上表 `name-it-as-the-glossary-does`、`human-steps-stay-human`）。
- 它不到达 Cursor（根 `AGENTS.md` `## Key Conventions`：Cursor 的用户级提示词在应用里维护）。Cursor 上跑的会话读不到 mode 里「`shared.md` owns the reply」所指的内容，这是已知缺口（0.5 第 6 条）。

---

## 7. 执行协议

### 7.1 人在场

照 pstack mode 第 117 行原文：匹配到的 playbook 的步骤逐字抄进 todo，排在任务自己的 todo 之前；不做的步骤留在列表里，写一行 `skip: <reason>`。只有编号步骤进 todo，规则簇与模板不进（L7 D.1）。回复点名改变了决定的原则（pstack mode 第 15 行）。长时间工作的决策轨迹交给 `show-me-your-work`（pstack mode 第 35 行）。

### 7.2 无人（夜里）

H6 下 todo 屏幕没人看，压缩后 todo 可能丢。所以：

| 角色 | skip 行与点名原则写在哪 | 为什么是这里 |
|---|---|---|
| worker | closeout 的 `## Decisions I made on my own`，每行 `skip <步骤标题>: <reason>` 或 `(<slug>) <决定>` | 这一节已存在，reviewer 判断、用户早上读（`implement` 第 23 行）；`--closeout` 已做格式检查 |
| reviewer | 评审报告里一段 | 报告就是交付物（P8） |
| orchestrator | `show-me-your-work` 的 TSV 轨迹，放主工作树 `.audit/night-<spec>.tsv`，`summary` 印它的路径 | pstack「Where it lives」原文；夜是长时间无人运行（pstack mode 第 35 行） |

- 早上的读者读的是票与夜的摘要（`shared.md` 前言）。所以这些行都落在票上或摘要指向的文件里，不只留在 todo 里。
- 重入时不重抄 todo，而是按 `RESUME:` 或 `where` 印的步骤标题接着做（第 3.2 节 `## Re-entry`）。
- 「逐字抄写」能否机器检查：worker 的 closeout 可以（`--closeout` 核对每个步骤标题要么在已完成的事件里出现，要么有 skip 行），推断可行、是否值得做在第 12 节 U-13；白天会话不能。

---

## 8. 脚本与 hook

### 8.1 要改的，为什么

| # | 改动 | 为什么 | 出处 |
|---|---|---|---|
| S1 | `skills/dispatch/scripts/*` 搬到 `skills/mmw/scripts/`，hook 进 `scripts/hooks/`，`models.py`、`hosts.json` 进 `setup-mmw` | 这些脚本只被 playbook 步骤与 hook 调用，是 mode 的 lever（L7 A.6；pstack `poteto-mode/scripts/`）；改模型是一项可单独调用的能力 | R14 4.1 `dispatch` 脚本段 |
| S2 | 新建 `anchors.py`：playbook 文件名、步骤标题、规则簇名、模板标题（`## Parent`、`## Owns`、`## Read first`、`## Seam`、`## Acceptance criteria`、`## State list`）、`EXPECT` 成功标记各一个常量 | 脚本只从这里取文本锚点；lint 核对每个锚点在目标文件里存在。修掉 R14 W3–W6 的字面耦合 | R12 K-2；L7 A.6「字面检查器持有被匹配的原文」 |
| S3 | 启动提示词：worker「Use the mmw skill. Playbook: work-a-ticket. Ticket #n. Unattended.」加 Memory 索引；reviewer「Use the mmw skill. Playbook: review-a-ticket. Ticket #n from base commit <sha>. Unattended.」加 Rules 包；删 `AUTONOMOUS`、`PRODUCT_RULES` | 规则的家是 mode 与 playbook，提示词只放数据（SSR `### Prompts written for other agents`）；`AUTONOMOUS` 与该条冲突（N10 第 8 节） | `dispatch.sh` 第 108–109、1949、1967 行；`test_dispatch.sh` 第 2830、6984、7199 行随改（R12 M19） |
| S4 | relay 唤醒行末尾加 `· mmw <playbook>`，按收件人角色与 watch 类型取 | 被压缩的会话凭这一行找回 playbook（N10 B8）；H4 要求同一行 | R12 K-1；R4 V3、V4（`ack` 不解析文字）；`tests/relay/test_relay.py` 相等断言随改（R4 V5） |
| S5 | `watchdog.py` 八种告警：保留命令，把「night.md's Exit codes of resume」换成锚点 `run-a-night`/`orchestrator-events` 的行名 | 脚本不往上写技能小节（L7 B.2 硬规律 2）；H4 | `watchdog.py` 第 735、780 行（R4 V2） |
| S6 | `turn-guard.py` 拦截文字加 `· mmw orchestrator-events` 指针 | 让 `MMW turn guard:` 有唯一的处理行 | `turn-guard.py` 第 306–311 行；N11 missing_edges 第 1 条 |
| S7 | `tool-guard.py` `NO_QUESTION` 缩成「Nobody is at the screen. Follow the mmw skill's ## Autonomy (unattended).」；`REFUSAL` 指向 P7 **Close out** | 一条事件一个指令（SSR `### Hand-offs` 第 4 条）；三个角色的出路都在 mode | `tool-guard.py` 第 71–80 行；长度 ≤ 256（R12 M2），本句约 80 字符 |
| S8 | `verify-ticket.py` `resume_at` 返回 `work-a-ticket § <标题>`，修掉失效的 docstring | 编号引用最脆弱（L7 C.6 信号 8）；docstring 引用的段落已不存在 | `verify-ticket.py` 第 2148–2182 行（R4 V10；R14 第 9 节第 1 条） |
| S9 | `dispatch.sh where [<spec>\|<n>]`：orchestrator 的定位，印 `RESUME: run-a-night § <标题>` | orchestrator 被压缩后与 worker 有同样的重入保障 | R12 K-3 |
| S10 | `dispatch.sh role "<角色>"`：只读，委托 `setup-mmw` 的 `models.py`；标签把空格与连字符视为相同 | 「your configured <角色> model」在 MMW 有值可查；修 pstack 标签没有解析器（L7 D.4） | R13 I-5 |
| S11 | `panel.sh start <面板角色> <brief>` 与 `panel.sh wait <id>`：按 `models.json` `panels.<角色>` 每项起一个会话（照 `advise_one` 的做法，`dispatch.sh` 第 2053–2080 行），成员把答案写进 `~/.mmw/state/<repo>/panels/<id>/<成员>.md`；`wait` 阻塞到全部到齐或某个会话消失（问 runner） | H3 下跨厂商面板只能另起会话；今天 advisor 的答案「Read the answer where the selected runner shows the session」（`consulting.md` 第 13 行），没有收集机制 | R13 I-6；U-6 |
| S12 | `import.py <pstack 路径>`：playbook → `skills/mmw/playbooks/`，原则 → `skills/mmw/principles/`；只做确定性改写：原则间相对链接、`principles/` 路径；遇到同名 playbook、同名技能、悬空依赖就拒绝并点名 | 机械改写不交给模型（pstack `principle-encode-lessons-in-structure`） | R13 I-12 |
| S13 | `hooks/mode-reminder.py`：用户提交 prompt 时，有 `.mmw/` 就打印一行 | pstack `reminder` 的替代（H1） | 第 3.3 节 |
| S14 | `retro.py` `DESTINATIONS` 加 `principle`、`playbook`、`mode` | 教训按层回流 | `retro.py` 第 31–32 行 |
| S15 | `dispatch.sh check` 的自动 `install.sh` 改为只报告 | 与「install.sh runs only when the user explicitly authorises it」冲突；pstack「The bucket is advice, not permission.」 | R12 M7；用户决定 0.5 第 3 条 |
| S16 | `install.sh`：`ours_skill_target` 认 `*/mmw-v2/upstream-pstack/skills/*`；`skills.txt` 前缀 `ps/`；hook 路径改；`--check` 加两项：路由表与步骤点名的技能与文件都已安装，`~/.mmw/state/*/watches.json` 里还开着的 watch（只报告） | 导入的组件能被安装；新架构的连线在安装侧也可检查 | `install.sh` 第 58–63、143–164 行；R4 第 11 节 |
| S17 | `board/board_data.py` 第 27 行、`codeversion.py` `LOADED` 的路径字面 | 随 S1 | R12 M22 |

### 8.2 脚本怎样点名 playbook 与步骤

- 一律「playbook slug + 步骤标题」或「playbook slug + 规则簇名」，取自 `anchors.py`，不写编号，不写仓库路径（技能内路径随技能目录冻结，H5）。
- 送进活会话的一律一行（H4）：`#12 reviewer.reported · mmw work-a-ticket`；`watchdog: #12 silent since 03:10 · run: dispatch.sh resume 12 "…" · mmw orchestrator-events § silent since`。
- 启动提示词可以多行（`runners/orca.sh` 第 25 行：第一条提示词以参数传入），paseo、herdr 待核（U-9）。

### 8.3 连线 lint：`tests/lib/check_wiring.py`

每个测试套件的 `run.sh` 先跑它（与 `check_module_paths.py` 同一位置，根 `AGENTS.md` Commands 表）。`tests/wiring/` 为每一类放一个必须失败的反例（R12 X-5 的做法）。

| 类 | 检查 | 防的是 |
|---|---|---|
| 1 方向 | 原则只指向原则或能力技能；脚本除 `anchors.py` 外不含技能正文的小节标题；能力技能不点名 playbook | L7 B.2 三条硬规律 |
| 2 可解析 | 路由表每行的文件存在；playbook 每步点名的技能已在 `skills.txt`、脚本命令存在、原则文件存在、reference 存在 | pstack 缺依赖检查（L7 E.1 第 27 条）；SSR 事实 7 原本防的「某一跳找不到下一步」 |
| 3 不按编号 | 跨文件出现「step N」「closing step N」「Phase X」「`## N`」即失败 | L7 E.1 第 2 条；R12 M13、M30 |
| 4 锚点 | `anchors.py` 每个常量在目标文件里字面存在 | R14 W3–W6 |
| 5 能力纯度 | 能力技能正文与 description 不含角色与流程词（第 5.4 节清单） | 混层回潮 |
| 6 索引一致 | mode `## Principles` 每行对应一个原则文件，要点与其 `description` 一致；每个原则文件都在索引里 | L7 E.1 第 14 条 |
| 7 事件覆盖 | `relay.py` `WAKES` 的每个事件、`watchdog.py` 的每种告警、`turn-guard.py` 的消息，在收件角色的 playbook 或 `orchestrator-events.md` 里各有一行 | R14 W1 |
| 8 一行 | 所有送进活会话的模板无换行 | H4 |
| 9 开关成对 | `disable-model-invocation` 与 `agents/openai.yaml` `policy` 同增同删 | `merge-notes/README.md` 第 20 行 |

### 8.4 hook 与宿主

| hook | 事件 | 宿主 | 状态 |
|---|---|---|---|
| `tool-guard.py` | 工具调用前（Bash、提问工具）；Cursor `beforeShellExecution` | 五个 | 就位（文字改，S7） |
| `turn-guard.py` | 回合结束（Claude/Codex/Grok `Stop`、Cursor `stop`、Pi `agent_settled`） | 五个 | 就位（文字改，S6） |
| `mode-reminder.py` | 用户提交 prompt | Codex（已知能注入）、Claude Code（推断能）；其余待测 | 新（U-2） |
| 压缩后重读 | `SessionStart`（压缩来源） | Codex 有此事件与注入；Claude Code 推断有 | 新（U-2） |

---

## 9. pstack 导入接口

### 9.1 接口清单与进门五问

在 R13 第 4 节 I-1–I-16 的基础上，逐项定下 MMW 的做法：

| # | pstack 依赖 | MMW 的接口 | 在哪 |
|---|---|---|---|
| I-1 | playbook 的位置与相对路径 `playbooks/`、`references/`、`scripts/` | `skills/mmw/` 同样布局，相对路径不改就能解析 | D1 |
| I-2 | playbook 骨架与粗体名点名 | 同一骨架；MMW 的可选段不影响 pstack 文件 | 第 4.1 节 |
| I-3 | 执行协议 | mode `## Playbooks` 首段原文；无人时写进交付物 | 第 7 节 |
| I-4 | `subagent_type: "poteto-agent"` | 宿主通用子代理 + 简报首句 | mode `## Subagents` |
| I-5 | 「your configured <角色> model (default …)」 | `dispatch.sh role`；会话内角色 `session_roles`，默认 `inherit-parent` | S10；D9 |
| I-6 | 面板角色（列表） | `models.json` `panels` + `panel.sh`；没有就降级并写明 | S11 |
| I-7 | 原则 `principle-<slug>` 与五种引用写法 | `principles/<slug>.md` + mode 解析规则 | 第 6.1 节 |
| I-8 | control 槽位 | mode 触发行的表；`target.json` `control` 覆盖 | 第 3.2 节 |
| I-9 | 能力技能的 `disable-model-invocation` | 保留；mode 的路径解析规则；导入脚本生成 `agents/openai.yaml` 带 `policy: allow_implicit_invocation: false` | D5 |
| I-10 | 「Run **Opening a PR**」 | 别名到 **Deliver a change**；用 PR 的仓库再转回导入的 `opening-a-pr.md` | P14 |
| I-11 | forge 选择在 6 个 playbook 里各写一份 | `docs/agents/issue-tracker.md` 是 forge 操作的一处；导入文件里的 forge 句不改（它们与之相容：`gh` 默认） | mode `## Host tools` |
| I-12 | 引入方式 | subtree + `ps/` + `import.py` + merge-note | D10 |
| I-13 | Cursor 专有工具与命令 | mode `## Host tools` 一张表 | 第 3.2 节 |
| I-14 | transcript 位置 | `references/transcripts/<宿主>.md`，照 pstack `why/references/sources/*.md` 的「按环境一份」 | U-8 |
| I-15 | worktree 约定 | mode 触发行（`.worktrees/` 下，避开两种名字） | 第 3.2 节 |
| I-16 | 回复写法冲突（长破折号、冒号） | 给用户的回复以 `shared.md` 为准；其余产物按 `unslop` | mode `## Writing the reply`、`## Non-negotiables` |

**进门五问**（`bring-in-a-component.md` 第 2 步；前四问取自 R4 D7.3，第五问取自 R13 第 4 节末）：

1. 能力技能：它产出一个能叫出名字的交付物、能脱离 mode 被调用吗？否则它是 playbook。
2. 它依赖的每个槽位（control、delivery、forge、子代理简报、模型角色、宿主工具）在 mode 里都有映射吗？
3. 它依赖 PR 吗？依赖就只路由给 `delivery: pr` 的仓库。
4. 它依赖跨厂商面板吗？`panel.sh` 在不在？不在就在 mode 写明降级。
5. 它运行中从 trunk 重读自己吗（`autopilot-full.md` 第 6 步、`multi-phase-plan.md` 模板）？这一步按 H5 删掉，删改写进 merge-note。

### 9.2 冲突规则

| 冲突 | 规则 | 实例 |
|---|---|---|
| 同名能力技能 | 不导入；MMW 的同名技能满足点名。用户要 pstack 版时由 `import.py` 以 `pstack-<name>` 改名，路由表写别名 | `tdd`、`teach`（`install.sh` 第 164 行拒绝重名） |
| 同名 playbook | 拒绝，交用户：保留 MMW 版、换用 pstack 版、或合并 | `authoring-a-skill.md`：pstack 原文「Tell it to do the thing and skip the reason」与 SSR 事实 1 冲突 |
| 原则与 MMW 规则 | 第 6.4 节四条 | — |
| 本地闸门与上层授权 | mode 的层级句 | pstack `bugbot-triage.md`「When in doubt, ask.」vs 无人会话 |
| 运行中从 trunk 重读 | 删（H5） | `autopilot-full.md` 第 6 步 |

### 9.3 纸面导入：playbook

**`bug-fix.md`**（15 行）

| 行 | 依赖 | MMW 落点 | 改原文 |
|---|---|---|---|
| 第 3 行 | 委派给子代理 | `## Subagents` 简报 | 0 |
| 第 7 行 第 1 步 | 「via the control skill (Non-negotiables)」 | mode 触发行的 control 槽位 | 0 |
| 第 8 行 第 2 步 | `how`、`why`；「Cursor's `/loop` command」 | 导入 `how`、`why`；`## Host tools` | 0 |
| 第 9 行 第 3 步 | `architect`；「your configured bug-fix model」 | 导入 `architect`（→ `arena`）；`dispatch.sh role "bug-fix"` | 0 |
| 第 10 行 第 4 步 | 「Inconclusive … is not a pass」 | 与 `silence-is-never-a-pass` 同向 | 0 |
| 第 11–12 行 第 5 步 | **tdd** skill；`sequence-verifiable-units` | MMW 的 `tdd`；导入原则 | 0 |
| 第 13 行 第 6 步 | **Opening a PR** | 别名 → **Deliver a change** | 0 |

结果：原文 0 处改动；路由表 1 行。MMW 因此需要：mode 的 control 槽位、`## Host tools` 的 `/loop` 行、Opening a PR 别名、`dispatch.sh role`、**Deliver a change** playbook。

**`investigation.md`**（14 行）：原文 0 处。依赖 `how`、`why`、`unslop`；第 2 步「throughput checkpoint」概念定义在 `feature.md` 第 3 步，所以 `feature.md` 同批导入。第 7–8 行「No PR, no babysit … re-route to Bug fix or Feature」只是交回，不需要 babysit 在场。MMW 的 `research` 由 mode 触发行覆盖「调研成文、放进仓库、被决定引用」（`research` description；根 `AGENTS.md`「a spec may cite」）。

**`feature.md`**（21 行）：原文 0 处。依赖 `how`、`architect`、`arena`、`interrogate`、`separate-before-serializing-shared-state`、`model-the-domain`（不在首批，第 4 步点名）、`sequence-verifiable-units`、Laziness Protocol、`**Comments**`。lint 会报 `model-the-domain` 悬空，所以它进首批的依赖闭包。首批导入的原则因此是 15 条加依赖闭包 4 条（`model-the-domain` 与 `architect` 带来的 3 条）。与 MMW 的界线由路由表「Distinct from Define a change」写明。

**`shipping.md`（与 MMW 落地对应的一份）**：逐步对照 MMW 已有的对应物：

| shipping 步骤 | 内容 | MMW 的对应物 | 出处 |
|---|---|---|---|
| 1 | 每个 PR 由一个没写代码的 agent 独立验证，给 `PASS`/`FAIL` | reviewer 的评审（没写代码的会话）+ worker 的判据运行；`ticket.passed` | P7、P8；`the-author-does-not-judge` |
| 2 | 只落地从根开始连续的已验证段 | `advance` 按阻塞边合并已通过的票；未通过的不合并 | `night.md` `## 2`、`## 3` |
| 3 | 核对 verdict 仍描述当前补丁（patch-id） | 合并后收口轮 `reverify` 在 base 分支重跑已关票的判据；worker 最终运行必须在 `HEAD` | `night.md` `## 4`；`implement` 第 4 步 |
| 4–5 | 只准备并落地最底下的 PR，一次一个 | `advance` 一次合并一张、冲突即 `bounced` | ADR 0027 |
| 6 | 不把 `autoMergeRequest` 当就绪 | 就绪只看票事件 | `the-tracker-is-the-state` |
| 7 | 每次合并后重算 | 每次 `advance` 读票事件重算 frontier | ADR 0019 |
| 8 | 用 `watch-pr` 与 `/loop` 盯着 | relay 唤醒、watchdog | ADR 0010、0020、0021 |
| 9 | 停在天花板，报告下一个缺口 | `summary`、`NIGHT SUMMARY` | `night.md` `## 5` |

结论：MMW 的落地是 **Run a night** 加 **Accept a night** 的 `finish`，`shipping.md` 的每一步都有等价物，所以不拿它替换。它作为条件导入，只给 `delivery: pr` 的仓库；要导入就需要 `scripts/watch-pr/`（bun + TypeScript），这是用户决定 0.5 第 2 条。导入时改原文：`each a Cursor cloud agent` 与 `/loop` 由 `## Host tools` 读懂，改 0 处；`scripts/watch-pr/watch-pr` 的相对路径在 `skills/mmw/scripts/` 下解析，需同时导入该目录。

### 9.4 纸面导入：能力技能

| 技能 | 落在 | 改原文几处 | 改了什么 | 依赖 → MMW 要长出什么 |
|---|---|---|---|---|
| `how` | `upstream-pstack/skills/how/`；`skills.txt` `ps/how` | 0 | — | `generalPurpose`、`readonly`、「your configured how-explorer/how-explainer model」→ mode `## Subagents`、`session_roles`；另生成 `agents/openai.yaml` |
| `why` | `ps/why` | 1 | 第 62 行「list the available MCPs from the Cursor environment … inspect the `mcps/` directory Cursor exposes」→ 读宿主的工具列表（宿主中立，merge-note 记录） | `why-investigators`、`why-synthesizer` 角色；`readonly: false` 的理由「strips MCP」是 Cursor 行为，其余宿主无害 |
| `architect` | `ps/architect` | 0 | — | `arena`（依赖闭包）；`architect runners` 面板 → `panel.sh`；原则 `exhaust-the-design-space`、`foundational-thinking`、`outcome-oriented-execution`、`redesign-from-first-principles`、`fix-root-causes`、`subtract-before-you-add`；`interrogate` |
| `arena` | `ps/arena` | 2 | 第 28、41 行 `~/.cursor/rules/pstack-models.mdc` → 「the `arena runners` / `arena cross-judge pool` role (mmw `## Subagents`)」 | 面板与 cross-judge 池（「Prefer a different model family from the parent's」只能靠另起会话，H3）；原则 `separate-before-serializing-shared-state`、`redesign-from-first-principles`、`prove-it-works`；runner 写候选用的 worktree 按 I-15 落在 `.worktrees/` |
| `interrogate` | `ps/interrogate` | 1 | 第 36 行 `~/.cursor/rules/pstack-models.mdc` → 「the `interrogate reviewers` role (mmw `## Subagents`)」 | 「The adversarial signal comes from model diversity」（第 9 行）→ 没有 `panel.sh` 时 interrogate 失去其价值，所以 `panel.sh` 与 `panels.interrogate reviewers` 是它的前提；第 49 行的 slug 回退句在其余宿主无害 |
| `show-me-your-work` | `ps/show-me-your-work` | 1 | 第 55 行「under the active workspace's `agent-transcripts/` directory … Don't glob across `~/.cursor/projects/*/`」→ 「where `mmw` `references/transcripts/<host>.md` says」 | `scripts/log.sh`（bash，可用）；第 66 行「a subagent on a different model family」→ `panel.sh` 单成员，或降级；`prove-it-works` 点名它 |
| `unslop` | `ps/unslop` | 0 | — | 规则 13（不用 em dash）与 `tests/lib/check_upstream_em_dashes.py` 同向；规则 32 与 `shared.md` 规则 7 同源同例（「A dial worth turning」）；只管英文产物，给用户的回复以 `shared.md` 为准（I-16） |

每个导入技能保留 `disable-model-invocation: true`（改 0 处），由 `import.py` 旁加 `agents/openai.yaml`（新文件，不算改原文）。模型在 Claude Code 上经 mode `## Host tools` 最后一行按路径读取（D5，U-1）；人用斜杠命令。

### 9.5 纸面导入：原则

| 原则 | 位置 | 改原文 | 依赖与处理 |
|---|---|---|---|
| `prove-it-works` | `principles/prove-it-works.md` | 0 | 点名 `show-me-your-work` → 同批导入 |
| `fix-root-causes` | `principles/fix-root-causes.md` | 0 | 「Restart bugs: suspect state before code」与 MMW 的 relay、watchdog 状态文件同向 |
| `laziness-protocol` | `principles/laziness-protocol.md` | 0 | — |
| `encode-lessons-in-structure` | `principles/encode-lessons-in-structure.md` | 0 | 「brain note」→ `## Host tools`；「Route to the right layer」→ `retro` 新去处（D13） |
| `sequence-verifiable-units` | `principles/sequence-verifiable-units.md` | 0 | 点名 `prove-it-works`、`build-the-lever` → `build-the-lever` 同批导入；「Rebase onto clean trunk first」「Stack commits and PRs」→ P7 `#### Integration` 本地限定、Deliver a change |
| `never-block-on-the-human` | `principles/never-block-on-the-human.md` | 0 | `**Boundaries:**` 与无人会话 → mode `## Autonomy` 优先级；「Product direction comes from the human」与 `shared.md` 规则 1 同向 |

每条在 mode 索引加一行。六条共改原文 0 处，拉进 2 条依赖（`show-me-your-work` 技能、`build-the-lever` 原则）。

### 9.6 Cursor 专有机制的替代（汇总）

| 机制 | 替代 | 硬约束 |
|---|---|---|
| `mode: true`、`reminder` | 提示词点名、description、`AGENTS.md` 一行、prompt hook | H1 |
| `disable-model-invocation` 集中调用权 | 保留；mode 路径解析规则 | H2 |
| `alwaysApply` 的 `pstack-models.mdc` | `~/.mmw/models.json` + `dispatch.sh role` | H1 |
| `agents/*.md` + `subagent_type` | 通用子代理 + 简报（ADR 0015） | H3 |
| `Task` 的 `model` 跨厂商 | `panel.sh` 另起会话 | H3 |
| `/loop`、`/goal`、cloud agent | 宿主循环命令；relay、watchdog；`dispatch.sh start`、`panel.sh` | H1、H6 |
| 运行中从 trunk 重读 | 删 | H5 |
| `agent-transcripts/` | 每宿主一份 reference | H1 |
| `create-skill` | `writing-for-agents` | — |
| `AskQuestion` | 人在场直接问；无人按 `## Autonomy` | H6 |
| cursor-team-kit 的 `control-ui`、`control-cli`、`deslop` | control 槽位；`deslop` 无对应物，写 `skip:` | — |

### 9.7 PR 与 MMW 落地方式的对应

| 情形 | pstack | MMW |
|---|---|---|
| 夜里一张票 | —（pstack 没有） | closeout；orchestrator `advance` 合并进 project branch（ADR 0025） |
| 一夜的结果 | 一个 stack 经 babysit、shipping 落地 | `summary` → 用户验收 → `finish`（P5、P9） |
| 白天在本仓库 | Opening a PR | 发布四步（P14） |
| 白天在用 PR 的仓库 | Opening a PR、Babysit、Shipping | 同左，条件导入 |
| 其他仓库 | — | 提交到当前分支并告诉用户（上游 `implement` 末句） |

### 9.8 多模型面板（H3）

- 会话内：子代理只能跑在本会话宿主的模型上。Claude Code 的子代理可在同厂商的几个模型间选（推断，未实测），这是 `session_roles` 允许写本宿主模型名的原因。
- 跨厂商：只能另起会话。`panel.sh` 复用 `dispatch.sh` 的 `start_session` 与 runner 边界（ADR 0018），每个成员拿同一份填好的简报（pstack interrogate 第 57 行「The same filled template goes to all reviewers」），答案写进状态目录，`wait` 收齐。
- 降级：没有 `panels` 配置、无人会话、或 runner 不可用时，同模型面板；回复写明。
- 成本与可靠性待测（U-6）。

---

## 10. 改造前后对照表

动作词见第 1.2 节。「就位」列出类型依据；「留在原处」列出硬约束。

### 10.1 N1 `dispatch` 与夜

| 部件 | 去向（层 / 位置 / 动作） |
|---|---|
| `dispatch/SKILL.md` description | 删；各时刻进路由表（mode） |
| `SKILL.md` 第 8 行 | 拆：前半句 → 原则 `the-tracker-is-the-state`；脚本位置句 → 各 playbook 的命令写法 |
| `## Find your moment` | 搬 → mode 路由表 |
| `## On waking` | 搬 → mode `## Re-entry` |
| `references/night.md` | 搬 → P5；`## 3` 表与 `### Exit codes of resume` → `references/orchestrator-events.md`（补 turn guard、7 种 watchdog 告警） |
| `references/one-ticket.md` | 搬 → P6 |
| `references/inside-a-ticket.md` | 搬 → P7 Entry 与第 11 步 |
| `references/editing-models.md` | 搬 → 能力技能 `setup-mmw` |
| `hosts.json` | 搬 → `setup-mmw/hosts.json`（配置目录） |
| `scripts/dispatch.sh` | 搬 → `skills/mmw/scripts/`；提示词 S3；新子命令 `where`、`role` |
| `scripts/relay.py` | 搬 → `skills/mmw/scripts/`；S4 |
| `scripts/watchdog.py` | 搬；S5。告警里的命令**留在原处（H4）** |
| `scripts/turn-guard.py`、`tool-guard.py` | 搬 → `scripts/hooks/`；S6、S7。拦截机制在宿主 hook 上，属于 H1、H6 的结构性强制 |
| `scripts/status.py`、`statedir.py`、`ghlist.py`、`runners/*.sh` | 搬 → `skills/mmw/scripts/` |
| `scripts/models.py` | 搬 → `setup-mmw/scripts/`；加 `role` 与两类角色 |
| `docs/contexts/night/CONTEXT.md`、`how-it-works.md` | 就位（仓库文档，L7 A.9）；路径与术语随改 |
| ADR 0009、0010、0016–0018、0020–0025、0027 | 就位（决定记录）；0010 成为 `woken-not-polled` 的理由出处 |

### 10.2 N2 `verify-ticket`

| 部件 | 去向 |
|---|---|
| `SKILL.md` 第 8–12 行 | 就位（能力正文） |
| 第 16 行、`## Find your moment`、`## Reached from here` | 删 / 搬 → mode 触发行与 P7 |
| `references/sub-issues.md` 第 5–9 行 | 就位（命令） |
| 第 11 行 | 搬 → P7 与 `orchestrator-events.md`（R14 W1） |
| 第 13–23 行 | 搬 → P7 `#### Sub-issues` |
| `references/linting.md` | 拆：命令就位；「何时 lint」→ P1、P5 |
| `scripts/verify-ticket.py` | 就位（能力的 lever）；`resume_at` 改为返回标题（S8） |
| `scripts/events.py`、`issue_tree.py` | 就位（能力的 lever，mode 脚本按路径加载，方向是 mode → 能力） |
| unlazy 的 `gate-check`（vendored） | 就位（外来组件，`merge-notes/unlazy.md`） |
| `merge-notes/unlazy.md`、`docs/contexts/ticket-run`、`tickets` 的 `CONTEXT.md` | 就位 |
| ADR 0008、0012、0013、0019、0026 | 就位；0008 是 `silence-is-never-a-pass` 的出处 |

### 10.3 N3 `implement`、`code-review`、`tdd`

| 部件 | 去向 |
|---|---|
| `implement/SKILL.md` | 回原文；正文 → P7（步骤与规则簇）、原则、`shared-experience` |
| `implement/references/writing-interface-code.md` | 搬 → `ui-acceptance/references/`；三处「closing step 1」改为标题 |
| `implement/references/saving-memory.md` | 搬 → `shared-experience/references/` |
| `implement/agents/openai.yaml` | 回原文（恢复 `policy`） |
| `code-review/SKILL.md` | 回原文（双轴评审） |
| `code-review/references/session.md` | 搬 → P8 |
| 四个 axis reviewer 文件 | 搬 → `skills/mmw/references/review-axes/`（子代理简报，L7 A.5 第一行） |
| `code-review/agents/openai.yaml` | 回原文 |
| `tdd/SKILL.md` 第 22、38 行 | 搬 → P7 限定句；其余就位 |
| `tdd/tests.md`、`mocking.md` | 就位 |
| `merge-notes/implement.md`、`code-review.md` | 删改动条目（回原文后无改动可记）；`tdd.md` 只留宿主中立一条 |

### 10.4 N4 `to-spec`、`to-tickets`、`triage`

| 部件 | 去向 |
|---|---|
| `to-spec` 全目录 | 分叉 → `skills/to-spec/`（MMW 自有）；`## Next`、description 触发句、退回路线 → P1、P3；上游目录回原文、不安装 |
| `to-spec/references/revising-a-spec.md` | 就位于分叉后的技能（能力） |
| `to-spec/references/several-specs.md` | 拆：判断就位；「一次一份、停下」→ P1 |
| `to-tickets` 全目录 | 分叉 → `skills/to-tickets/`；第 20、160 行 → P1；子代理段 → mode |
| `to-tickets/references/*` 三份 | 就位（能力） |
| `triage/SKILL.md` | 回原文；流水线句 → P4、P9 |
| `triage/references/pipeline-issues.md` | 搬 → P9 `#### Pipeline issues` |
| `triage/AGENT-BRIEF.md` 本仓改写 | 回原文；「`to-spec` reads the agent brief」→ P4 |
| `triage/OUT-OF-SCOPE.md` | 就位 |
| `docs/agents/issue-tracker.md` | 就位（配置）；`## Morning queries` 的顺序 → P9 第 1 步（文件保留查询命令） |
| `docs/agents/triage-labels.md`、`domain.md`、`docs/contexts/tickets/CONTEXT.md` | 就位 |
| 三份 merge-note | `to-spec.md`、`to-tickets.md` 改为分叉说明；`triage.md` 删流水线条目 |

### 10.5 N5 其他上游技能

见第 5.2 节逐行。汇总：`prototype`、`wayfinder`、`grilling`、`grill-with-docs`、`improve-codebase-architecture`、`resolving-merge-conflicts`、`codebase-design`、`setup-matt-pocock-skills`、`writing-for-agents`、`to-questionnaire` 回原文（保留 merge-note 记录的能力扩展与宿主中立改动）；`grill-me`、`domain-modeling`、`research`、`diagnosing-bugs`、`wizard`、`handoff`、`teach`、`wait-what` 就位；`ask-matt` 残留目录回原文，`PHASE-BOUNDARIES.md` 副本 → mode reference。

### 10.6 N6 界面链

| 部件 | 去向 |
|---|---|
| `ui-acceptance/SKILL.md` | 拆：description 末句 → mode 触发行；第 38 行 → P7；其余就位 |
| `ui-acceptance/references/*` 五份、`scripts/*` 九个 | 就位（能力与它的 lever） |
| `design-pages/SKILL.md` | 拆：第 21 行「worker 从不做」→ P7；其余就位 |
| `design-pages/references/edit-pages.md` `## Next` | 搬 → P3 `#### Change classes` |
| `design-pages/references/pull.md` | 拆：第 1–4 步就位；交接与 `contract` 段 → P3 |
| `draw.md`、`design-system.md`、两份模板、两个脚本 | 就位 |
| `write-screen-contract/SKILL.md` `## Next` | 搬 → P3；其余就位 |
| `write-screen-contract` 格式文件与三个脚本 | 就位 |
| `to-tickets/references/cutting-interface-tickets.md` | 就位（`to-tickets` 能力） |
| `code-review/references/ui-reviewer.md` | 搬 → `references/review-axes/ui.md` |
| `docs/contexts/ui-acceptance/CONTEXT.md`、ADR 0002、0004、0011、0028–0030 | 就位 |

### 10.7 N7 独立技能

| 部件 | 去向 |
|---|---|
| `retro/SKILL.md` | 拆：description 触发与第 186 行 → P5；第 8 行就位（前置条件）；理由句 → 原则 |
| `retro/scripts/retro.py` | 就位；S14 |
| `advisor` 三份 | 就位；触发同时写进 mode（引用 `consulting.md`） |
| `exe-release/SKILL.md`、`references/driving.md` | 搬 → P10 |
| `exe-release/references/key.md`、`new-product.md`、全部脚本与模板 | 就位（能力与 lever） |
| `code-checkers` 全部 | 就位；第 6、8 步的接入顺序 → P11 |
| `manage-agents-md` 全部 | 就位；第 50 行 → mode |
| `diagram-design` 与 subtree | 就位 |

### 10.8 N8 底座

| 部件 | 去向 |
|---|---|
| `prompt/shared.md` | **留在原处（U0）** |
| `prompt/hosts/*.md`、`render.py`、`README.md`、`tests/` | 就位（宿主提示词的生成与分发） |
| `skills.txt` | 就位；内容按 2.1 节改 |
| `install.sh` | 就位；S16 |
| `~/.mmw/models.json` | 就位（配置）；加 `session_roles`、`panels` |
| `board/*` | 就位（产品）；S17 |
| `migrations/remove-verifier.py` | 就位 |
| `tests/AGENTS.md`、12 个 `run.sh`、`tests/lib/*` | 就位；加 `check_wiring.py` 与 `tests/wiring/` |
| 根 `AGENTS.md` | 拆：`## Gotchas` 第 1 条的发布四步 → P14（`AGENTS.md` 留指针与 H5 那一句）；`<important if … upstream …>` → P13 指针；其余就位 |
| `CODING_STANDARDS.md` | 就位；`## Skills and scripts` 第 4 条、`## State and configuration` 第 3 条的跨任务立场改为点名原则 |
| `TESTING.md` | 就位 |
| `merge-notes/README.md` 与 24 份说明 | 就位；回原文的技能删对应条目；新增 pstack 说明 |
| `downstream-notes/` | 就位；新增一份（第 11 节 B3） |
| ADR 0003、0005、0006、0007、0015 | 就位；0015 是 `## Subagents` 的依据 |

### 10.9 N9 文档与原则来源

| 部件 | 去向 |
|---|---|
| `docs/adr/README.md`、31 份 ADR | 就位；新增 ADR 0032 |
| `CONTEXT-MAP.md`、7 份 `CONTEXT.md` | 就位；toolbox 加六个词条；只住在词表里的行为规则待查（U-10） |
| `CODING_STANDARDS.md`、`TESTING.md`、`shared.md` | 见 10.8 |
| PC1–PC29 各处散落的理由句 | 搬 → 原则层（第 6 节）；调用方留名字加本地一句 |

### 10.10 N10 路由与调用

| 部件 | 去向 |
|---|---|
| 35 份 `SKILL.md` frontmatter | 上游与 pstack 回原文的开关；MMW 自有的去掉角色与流程触发句；mode 新增一份 |
| 24 份 `agents/openai.yaml` | 跟随开关（lint 第 9 类） |
| 5 个 `## Find your moment` 表 | `dispatch`、`verify-ticket`、`code-review` 的表删（职能进路由表与 P7、P8）；`design-pages`、`ui-acceptance` 的表是能力内部分支，就位（R14 4.3） |
| 17 句「下一步」结尾段 | 删；顺序在 playbook |
| `dispatch.sh` 提示词拼装 | S3。mode 名、playbook 名、票号**留在原处（H1）** |
| `dispatch.sh` 头注释与 `--help` | 就位；头注释补齐 `integrated`、`findings`、`memory-list`（N10 B12） |
| `relay.py` `WAKES` 与 `wake_text` | 就位（lever）；S4 |
| `watchdog.py` 告警、`turn-guard.py` 消息、`tool-guard.py` | 见 10.1 |
| SSR 事实 7、`### Descriptions`、`### Hand-offs`、`### Prompts written for other agents` | 搬 → `docs/skill-set/`；事实 7 与 Hand-offs 第 5 条改写（D14） |
| 上游 `SKILL-MECHANICS.md` `## Router skills` | 就位（上游原文；它主张路由技能，与新架构同向） |
| `upstream/.agents/invocation.md`、`merge-notes/README.md` 开关段 | 就位 |
| 提交 `06163a0f` 的决定（移除 ask-matt） | 就位：路由职能由 mode 承担，ask-matt 仍不安装 |

---

## 11. 迁移批次

**规则**：每一批都作为本仓库的票，由当时已安装的冻结版本跑（H5）；新版本只在隔离的测试 home 里、对着假 tracker 与假 runner 测；发布照根 `AGENTS.md` `## Gotchas` 的四步，第三步只在没有 watch 开着时做。

| 批 | 内容 | 完成后流水线为何仍能跑 | 用户要做的 |
|---|---|---|---|
| **B0 地基** | `anchors.py`（只登记现有锚点）；`check_wiring.py` 报告模式；SSR、RSS 搬到 `docs/skill-set/` 并改写事实 7；ADR 0032；`retro.py` 三个新去处；toolbox 词条 | 不动任何运行时文字与提示词 | 认可 ADR 0032（它改变了「不设路由技能」的旧决定） |
| **B1 mode 与导入** | `skills/mmw/`（SKILL.md、principles 10+15+4 条、`references/phase-boundaries.md`、`transcripts/`）；白天 playbook P1–P4、P10–P14 与导入的 5 份；`upstream-pstack/` subtree 与 7 个 `ps/` 能力技能；`setup-mmw` 的只读 `role`；`models.json` 两类新角色（`models.py` 是唯一写者，ADR 0024）；`mode-reminder` hook | 夜间角色的文件与提示词都没动；白天多了路由，旧技能的「下一步」句暂时还在（lint 报告不拦） | 授权跑 `install.sh`（技能列表与 hook 变了）；开新会话（H2）；决定 0.5 第 1、2 条 |
| **B2 白天技能回原文** | 第 5.2 节的白天技能回原文；`to-spec`、`to-tickets` 分叉；`triage` 的 `pipeline-issues.md` 进 P9 的预备文件；lint 第 3、5 类转为失败 | 白天路由已由 B1 的 playbook 承担；夜间不读这些句子（worker 读 `implement`，orchestrator 读 `night.md`） | 授权 `install.sh`（`self/to-spec`、`self/to-tickets` 替换 `engineering/` 两项）；开新会话 |
| **B3 夜间角色**（一批两张票，同一个发布窗口） | 票 a：P5–P9、`orchestrator-events.md`、`review-axes/`、`shared-experience`、`ui-acceptance` 收 `writing-interface-code.md`；S3–S9 的提示词、唤醒指针、告警、`resume_at`、`where`；`implement`、`code-review` 回原文。票 b：S1 搬脚本、`setup-mmw` 接管 `models.py`、`dispatch` 解散、hook 重新登记、S17 | 新协议先在隔离 home 用假 runner 跑通 `tests/dispatch`、`tests/relay`、`tests/verify-ticket`；发布后第一夜用一份小 spec 试跑（第 12 节 U-1、U-3、X-2） | 在两夜之间授权 `install.sh`（hook 路径变了）；试跑一夜并验收；消费仓库的 downstream-note：`AGENTS.md` 加 `mmw` 一行、启动提示词与技能名变了 |
| **B4 收紧与扩展** | lint 全部转为失败；`panel.sh`；`import.py`；`deliver-a-change` 的 `delivery` 键；S15；条件导入 `opening-a-pr`、`babysit`、`shipping`（若引入 bun） | 只加 lever 与条件路由 | 决定 0.5 第 2、3、5 条；授权 `install.sh`（若技能列表变） |

**为什么 B3 不能再拆**：`dispatch` 目录一旦不在 `skills.txt`，它的软链被摘，已登记的 hook 路径 `~/.agents/skills/dispatch/scripts/tool-guard.py` 就失效（`install.sh` 头注释：hook 指向技能软链）。所以文字改动（票 a）与搬脚本（票 b）必须在同一个发布窗口里提升，否则中间状态不能跑夜。

**回退**：每批是一次到 `main` 的快进；已安装 checkout 退回上一个提交即回到上一批（根 `AGENTS.md` 发布第三步的逆操作），`install.sh --check` 确认。B3 回退还要重跑一次 `install.sh` 恢复 hook 路径（需授权）。

---

## 12. 风险与需要的实测

实测都在隔离的测试 home 里做，装开发版技能，不碰已安装的 checkout。

| # | 问题 | 为什么重要 | 怎么测 |
|---|---|---|---|
| U-1 | 五个宿主上，模型能否按 mode `## Host tools` 的路径规则读取一个带 `disable-model-invocation: true` 的技能（`~/.claude/skills/<name>/SKILL.md` 或 `~/.agents/skills/<name>/SKILL.md`） | D5 的前提；不成立就要改为去掉开关（R13 I-9 的做法） | 隔离 home 装一个带开关的探针技能，内含随机标记；在 mode 下给一个会走到它的 playbook 步骤，看回复是否出现标记。Claude Code 另测 Bash 沙箱开启时 Read 工具能否读 `~/.agents/skills` 下的软链目标（根 `AGENTS.md` Gotchas 第 2 条只说 hook 读不到） |
| U-2 | Claude Code、Grok、Pi、Cursor 有无「用户提交 prompt」与「压缩后会话开始」事件、能否注入一行 | 第 3.3 节路径 3 与压缩重读 | 每个宿主装只打印标记的探针 hook，在有、无 `.mmw/` 的目录各提交一次，看模型能否复述标记；再触发一次压缩 |
| U-3 | `skills/mmw/principles/*.md`、`playbooks/*.md` 这类嵌套文件会不会被某个宿主当成技能扫入 | 会的话，原则与 playbook 进技能列表 | 探针技能目录下放带 frontmatter 的嵌套 `.md`；看各宿主技能列表（Grok 用 `grok inspect --json`） |
| U-4 | 五个宿主是否都有 todo 工具与后台子代理 | 第 7 节；`## Host tools` 的 `run_in_background` 行 | 各宿主非交互进程列出可用工具 |
| U-5 | mode 实际篇幅与 worker 启动时多读的上下文 | 常驻纪律的代价；R4 曾以此否决 R2 | B1 后 `wc -l`；在隔离 home 用假 tracker 跑一张测试票，比较首个动作前的上下文用量 |
| U-6 | `panel.sh` 起 3 个会话的耗时、费用、收齐的可靠性 | 决定 `interrogate`、`arena`、`architect` 在 MMW 是否值得用 | 用 `advise_one` 的机制起 3 个会话，量到齐时间；故意杀掉一个，看 `wait` 是否报告而不挂住 |
| U-7 | description 数量变少（上游回到用户触发）后，人启动的会话能否仍找到正确入口 | 头部入口（N10 B1） | 取 N10 第 3.2 节的起点语句各一句，在五个宿主的新会话里看加载了什么 |
| U-8 | 各宿主的会话记录位置与格式；Nowledge Mem 的会话记录能否作为 `session-pickup` 的来源 | I-14 | 各宿主跑一个短会话，找记录文件；`nmem t search` 查同一会话 |
| U-9 | paseo、herdr 的第一条提示词是否以参数传入 | H4 是否管启动提示词 | 读 `runners/paseo.sh`、`runners/herdr.sh` 的 `start` 实现体（N11 unread 第 8 项） |
| U-10 | 七份 `CONTEXT.md` 里有没有只住在词表里的行为规则 | 这类规则也要按类型搬 | 逐份读，对每条词条的 `_Home_` 核对 |
| U-11 | 被压缩后，只凭唤醒指针与 `RESUME:` 能否回到正确的步骤 | D7 | 假 runner 开一夜，压缩 orchestrator 后投 `#3 ticket.passed · mmw run-a-night`（R12 X-2） |
| U-12 | `session_roles` 写本宿主的另一个模型时，Claude Code 子代理是否真的用它 | 第 9.8 节的推断 | 起一个指定模型的子代理，让它报告自己的模型 |
| U-13 | `--closeout` 核对「每个步骤要么完成要么有 skip 行」是否可行且值得 | 第 7.2 节 | 读 `run_closeout` 全文；在测试票上做一次 |
| U-14 | 标准 axis 简报与上游 `code-review` 的 smell baseline 是否重复 | 回原文后两处可能各有一份 | 对照 `standards-reviewer.md` 与上游 `code-review` 第 3 步 |
| U-15 | `cursor/plugins` 仓库能否 `git subtree split --prefix pstack` 干净切出 | D10 | 在本地克隆上试一次，比较切出的树与研究快照 |

另两项已知风险，不需实测：

- **Cursor 读不到 `shared.md`**：mode 把回复写法交给 `shared.md`，Cursor 上的会话拿不到（0.5 第 6 条）。
- **路由表可能漂移**：ask-matt 的历史是路由表与被指技能失同步（N10 第 7 节）。新设计的不同之处是路由行只指向 playbook 文件、不复述技能内容，并由 lint 第 2 类核对文件存在；是否足够，要看 B2 之后一段时间里 lint 抓到的次数（推断）。

---

## 13. 自查：与第一版草图的最低范围逐项对照

| 草图要求 | 结果 | 说明 |
|---|---|---|
| 一个 mode：常驻规则 | **超出** | 九节：Non-negotiables、Principles、Autonomy、Subagents、Host tools、Writing the reply、Comments、Re-entry、Playbooks；四条到达路径（第 3 节） |
| mode：原则索引 | **达到** | 六组，由 lint 与原则文件核对 |
| mode：playbook 路由表 | **达到** | 19 行加条件行与直接能力行，每行带 Distinct from |
| 白天定义是 playbook | **超出** | P1，另拆出 P2 地图、P3 界面 |
| 夜间编排是 playbook | **达到** | P5 |
| 做一张票是 playbook | **达到** | P7，`implement` 回原文 |
| 评审一轮是 playbook | **达到** | P8，`code-review` 回原文 |
| 单票是 playbook | **达到** | P6 |
| 早上验收与 finish 是 playbook | **达到** | P9 |
| 修 bug 是 playbook | **达到** | 导入 `bug-fix.md`，并补上 N10 B6 |
| 出包是 playbook | **达到** | P10 |
| 分诊是 playbook | **达到** | P4 |
| 调研是 playbook | **达到** | 导入 `investigation.md` 加 `research` 触发 |
| 给仓库接入 MMW 是 playbook | **达到** | P11 |
| 写技能是 playbook | **达到** | P12（与 pstack 同名文件的冲突已处理） |
| 能力技能只讲一步怎么做、不知道被谁调用 | **达到** | 第 5 节逐个剥离；lint 第 5 类强制；`dispatch` 解散 |
| 原则层是真正的层：MMW 自己的跨任务规则 | **超出** | 10 条 MMW 自有原则覆盖 PC1–PC29 中的 13 条；其余 16 条归 pstack 原则、`shared.md` 或 mode（第 6.3 节） |
| 原则层能承接 pstack 原则 | **超出** | 格式逐字相同，六条示范导入改 0 处；首批另导入 9 条，加依赖闭包 4 条（`model-the-domain`、`exhaust-the-design-space`、`foundational-thinking`、`outcome-oriented-execution`） |
| 脚本是 lever，由 playbook 步骤调用 | **达到** | 全部流水线脚本进 `skills/mmw/scripts/`；只点名标题；锚点表与 lint |
| 外来组件能直接落位 | **超出** | 16 项接口、进门五问、冲突规则、`import.py`、subtree 与 `ps/` 前缀 |
| 未达到的项 | 无 | 按类型本该搬却留在原处的只有第 0.4 节六行，各有 H1、H2、H4、H5、H6 或 U0 |

**对「越计划范围越小」的自查**：与 R4、R12 相比，本设计撤回了它们的三个收缩：五个角色流程留在能力技能里（改为 playbook，第 4.3 节 P5–P8）；只建 2 条原则（改为 10 条自有加 15 条导入）；`exe-release`、`dispatch` 不进路由表（改为 P10 与 P5、P6，且 `dispatch` 解散）。R12 以「字面引用多」「测试钉着」为由留下的内容，这里全部用锚点表与同批改测试处理（S2–S8）。

---

## 14. 本文读了什么，没读什么

**本轮回到原文读过**：

- pstack：`skills/poteto-mode/SKILL.md` 全文；`playbooks/` 下 `bug-fix.md`、`feature.md`、`refactoring.md`、`investigation.md`、`perf-issue.md`、`shipping.md`、`babysit.md`、`authoring-a-skill.md`、`session-pickup.md`、`pause-safely.md`、`opening-a-pr.md` 全文；六条原则全文；`how`、`why`、`architect`、`interrogate`、`show-me-your-work`、`unslop` 的 `SKILL.md` 全文；`arena`、`setup-pstack` 按依赖 grep；`LICENSE` 首行。
- MMW：`skills/dispatch/SKILL.md`、`one-ticket.md`、`inside-a-ticket.md` 全文；`night.md` 标题与第 145–160 行；`implement/SKILL.md` 全文与上游原文；`code-review/SKILL.md` 与上游原文、`session.md` 标题；`verify-ticket/SKILL.md` 全文；`ui-acceptance/SKILL.md` 第 1–38 行；`advisor/references/consulting.md` 全文；`skills.txt` 全文；`install.sh` 第 1–80、140–165、600–700、764–800 行；`dispatch.sh` 第 100–112、1940–1975、2040–2080 行；`verify-ticket.py` 第 2140–2185 行；`retro.py` 第 25–40 行；`diagnosing-bugs` `## Redact`；`to-tickets` 第 63、84 行与标题；`to-spec`、`exe-release`、`pipeline-issues.md` 标题；SSR 第 10–20、84–92 行；ADR 0008 第 1–11 行；`~/.mmw/models.json`；`docs/adr/` 目录。
- 报告：L7 第 0、A、B、C 节全文与 D.1–D.2；R13、R14 全文（任务附带）；R12 第 1 节 M1–M30 与第 10–12 节；R4 第 1 节 V1–V17 与第 10、11 节；N10 第 3、4、5、6、7 节；N11 全文；N1–N10 第 1 节部件清单。

**没有读、结论依赖它们的地方已标推断或列入第 12 节**：

- `night.md` 的 `## 3`、`## 4` 全文（P5 的步骤取自标题与 R14、R12 的核实）；`code-review/references/session.md` 与四个 axis 文件的正文（P8 与 U-14）；`to-spec`、`to-tickets` 的正文（分叉理由取自 merge-note 与 R4 V11、N10 第 6 节）。
- pstack 的 `arena`、`swarm`、`figure-it-out`、其余 17 条原则的正文（只按依赖 grep）；`scripts/watch-pr/` 的实现（bun 依赖取自 L7 A.6「poteto-mode 的脚本共用一个 `scripts/package.json`，由 `bootstrap.ts` 首次运行时自举依赖」与目录内容）。
- 各 runner 适配器实现、`status.py` 与 `run_closeout` 函数体、board 前端、各宿主的 hook 文档（U-2、U-9、U-13）。
