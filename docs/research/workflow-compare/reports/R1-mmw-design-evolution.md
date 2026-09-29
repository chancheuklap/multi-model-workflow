# R1 MMW 的 pstack 分层架构：演进派设计

立场：以 MMW 已经跑通的部分为基础。先问「现在哪里真的坏了或重复了」，只在能拿到用户第 2 条要求所列收益的地方动；同时真正建立 mode、playbook、原则三层，不回避已定方向（Memory `8ec53374`）。本文只定架构层面的决定，不逐个归置部件。

标注：「已核实」= 本轮回到原文或跑命令看到；「推断」= 由写法推出、原文没直说；「未确定」集中在第 14 节。

---

## 0. 结论先读

1. **一个 mode，不是两个。** 新增一个本仓自有技能 `mmw`（`mmw-v2/skills/mmw/`），它是全集唯一的路由。它模型可触发，另由消费仓库 `AGENTS.md` 的 `## External References` 里一行指向它；不依赖 Cursor 的 `mode: true` / `reminder:`，也不进 `shared.md`。
2. **playbook 和原则是 `mmw` 技能目录里的文件，不是技能。** `playbooks/<task>.md`、`principles/<slug>.md`、`references/phase-boundaries.md` 按相对路径到达，这与现有 `references/` 的到达方式相同，已在每夜的生产运行中用着，不引入新的宿主行为。
3. **新 playbook 只有一份：`playbooks/idea-to-tickets.md`**（想法 → spec → 票 → 交给 `dispatch`）。它给现在无家可归的头部内容一个家（N10 B1–B5、`ask-matt` 的主流程与 Context hygiene），并收走上游文本里两句纯「下一步」。wayfinder、triage、改 bug、代码健康不另写 playbook，只在 mode 的路由表里各占一行：它们各自只调一个技能，另写成 playbook 就是 C.6 信号 5。
4. **脚本启动的角色不经过 mode。** worker、reviewer、advisor、orchestrator 的操作文件就是它们的 playbook，原位不动：worker = `implement`，reviewer = `code-review` 的 `references/session.md`，advisor = `advisor` 的 `references/advising.md`，orchestrator = `dispatch` 的 `references/night.md` 与 `one-ticket.md`。这符合规范 C.1 第 7 问（单一入口、单一任务类型用操作文件）。「角色 = playbook + `models.json` 一行」已经由 `dispatch.sh start`/`advise` 的启动提示词加 `models.py` `ALLOWED_AGENTS` 实现（ADR 0015 的延续），不另建 agent 定义文件，也不在 mode 里放角色表。
5. **原则层起步只有两条**：`silence-is-never-a-pass`（ADR 0008）与 `the-tracker-is-the-state`（ADR 0019、0020）。门槛写死：跨任务、有可观察触发、改变一个决定、至少被 mode 或一份 playbook 引用、理由现在没有 agent 读得到的家。N9 的其余 16 个候选不建文件，理由见第 7 节。
6. **上游回到原文的主要手段是「分叉」，不是逐句回退。** `implement`、`code-review`、`to-tickets`、`to-spec` 四个技能的上游行已不到一半（N3 §5、N4 §5，merge-note 自述）。它们整体搬进 `mmw-v2/skills/`（名字不变），`mmw-v2/upstream/` 里的四份恢复成上游原文、不再安装。`ask-matt` 残留目录同样恢复原文。其余上游技能只移走纯「下一步」句；调用开关、description 触发句、改变能力的改动、防错守卫、host 中立写法留在上游文本里，按规则记 merge-note。
7. **旧规则里唯一被废止的是做法，不是意图。** 事实 7 的「MMW ships no router skill」废止，改成「一个 mode 是唯一路由，由 lint 与实际同步」；它防的「第二份副本漂移」由「顺序只有一个家」加机器检查保住。`merge-notes/README.md` 手写的 7 个用户触发名单，改成可推导的规则加 lint。
8. **新增一个 lint**（`mmw-v2/tests/lib/` 下，与现有三个共用检查同级）：mode 与 playbook 点名的技能都在 `skills.txt` 且模型可触发；引用的原则存在且已索引；每份 playbook 都被 mode 路由；`dispatch.sh` 启动提示词点名的技能存在。这就是 Memory `ce037679` 要的「与实际同步的总图」的机械部分。
9. **最大的风险是 mode 没被加载。** 同为模型可触发路由的 `ask-matt` 在 Claude Code 会话里实际调用 0 次（N10 §7，已核实口径有限）。所以 mode 的加载靠 `AGENTS.md` 常驻一行，而这一行是否真让五个宿主在任务开头打开 `mmw`，要先实测（第 11 节 T1）。实测不过，第 3 阶段（从上游与自有技能里删「下一步」句）不做。

---

## 1. 读了什么、核实了什么

- 通读：`L7-pstack-component-contract.md` 全文；`N10-mmw-routing-and-invocation.md` 全文；`N11-mmw-gaps.json` 全文。
- 分节读：`N3` §5、`N4` §5、`N8` §9–11、`N9` §9–12；其余 N 报告读了标题结构。
- 回到原文核实（本轮读过）：`SKILL-SET-RULES.md` 全文；`mmw-v2/skills.txt`；`mmw-v2/prompt/shared.md` 与 `prompt/README.md`；`install.sh` 1–90 行；`dispatch` 的 `SKILL.md`、`references/night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md` 开头；`implement`、`code-review`、`verify-ticket`、`ui-acceptance`、`design-pages`、`advisor` 的 `SKILL.md`；`design-pages/references/pull.md` 后半；`write-screen-contract` `## Next`；`to-spec` `## Next`；`to-tickets` 第 8 步；`grill-with-docs`；`wayfinder` `### Work through the map`；`improve-codebase-architecture` `### 4`；`prototype` 规则 6 与 `UI.md` `## Next`、`LOGIC.md` 结尾；`grilling` 结尾；残留 `ask-matt/SKILL.md` 与 `PHASE-BOUNDARIES.md` 全文；`setup-matt-pocock-skills/SKILL.md`；`merge-notes/README.md` 全文；ADR 0003、0014、0015、0022 全文；`dispatch.sh` 100–115、1925–1990、2040–2080 行；`relay.py` `wake_text`；`turn-guard.py` 头注释与阻断消息；`tool-guard.py` 头注释；`verify-ticket.py` `resume_at` 与 `run_preflight`；`models.py` `ALLOWED_AGENTS`；`~/.mmw/models.json`；pstack 的 `poteto-mode/SKILL.md`、`playbooks/bug-fix.md`、`playbooks/session-pickup.md`。
- 用上游 squash 提交 `5b1a4c51` 比对了 10 个上游技能的原始 frontmatter，以及 `wayfinder`、`prototype`、`improve-codebase-architecture` 的原文片段。
- Memory（`nmem m show` 读原文）：`8ec53374`、`756fc056`、`b388b852`、`411750f5`、`ce037679`、`f4c3d378`、`fe94802d`、`c155ffc2`、`292e8f2d`、`9040c9cf`、`ec59cec8`。
- 本会话自己的可用技能列表里没有 `grill-me`、`grill-with-docs`、`handoff`、`teach`、`wait-what`、`improve-codebase-architecture`、`setup-matt-pocock-skills`。这说明 Claude Code 上用户触发的技能模型看不到（已核实，与 N10 §10.1 一致）。
- 对 pstack 快照每个技能目录跑了一次 grep，模式是 `subagent_type|Task|run_in_background|pstack-models|grok-4|claude-opus|AskQuestion|/loop|cursor|Cursor|readonly`。23 个原则与 `blast-radius`、`bro`、`figure-it-out`、`tdd`、`teach`、`technical-writing`、`unslop` 命中 0 个文件；`poteto-mode` 36 个，其余能力技能 1–4 个。这个模式只能粗筛，命中 0 不等于与宿主无关。
- 采用 N 报告结论前按 N11 纠正：`ask-matt` 已不安装，N3、N6 列出的 `ask-matt -> …` 边不存在；worker 不读 `## On waking`（N10 B9 正确，N1 §2.1 错）。本文没有用到 N11 列为 thin_claims 的其他结论。

没有读的：`dispatch.sh` 其余约 4400 行、`relay.py` 其余部分、各 runner 适配器、`to-tickets`/`to-spec` 的 reference 全文、`docs/contexts/night/how-it-works.md`。凡依赖这些的陈述都标了推断。

---

## 2. 现在哪里真的坏了或重复了（驱动改动的清单）

只有这张表里的问题会引出改动；不在表里的部件原样不动（第 13 节）。

| # | 问题 | 性质 | 核实 |
| --- | --- | --- | --- |
| P1 | 「在工作目录里有个想法」没有模型可达的入口（N10 B1）。`grill-with-docs` 是用户触发；`ask-matt` 已删 | 断点 | 已核实 frontmatter 与本会话技能列表 |
| P2 | 用户说「grill me」时模型加载的是 `grilling`，它的结尾不点名任何下一步；只有用户触发的 `grill-with-docs` 点名 `to-spec`（B2） | 断点 | 已核实 `grilling` 结尾 |
| P3 | 「走 spec 流水线还是直接 `tdd`」「谁来检查」没有家，只在残留 `ask-matt` 第 26 行（B3） | 无家内容 | 已核实 |
| P4 | `prototype` LOGIC/EXP 分支没有下一步，规则 6「fold the validated decision into the real code」在没有 map 时会让 agent 绕过 spec 直接写生产代码（B4） | 断点（推断会发生，无实地记录） | 已核实规则 6 与 `LOGIC.md` 结尾 |
| P5 | 阶段边界的五选一与 Context hygiene 没有安装（B5） | 无家内容 | 已核实 |
| P6 | 三个 description 各自声称 `implement` 某一步的活，进来后又被送回 `implement`：`dispatch`「Start a reviewer from inside a ticket」、`ui-acceptance`「before writing a page ticket's code」（B7、R7、R8） | 真重复 | 已核实两份 `SKILL.md` 的 description 与第 1 行 |
| P7 | worker 被唤醒时不被指到 `dispatch` `## On waking`，缺第 1 步「重跑被打断的命令」（B9） | 断点 | 已核实 `implement` 全文无 `On waking` |
| P8 | orchestrator 上下文被压缩后，唤醒文字 `#<n> <event>` 不指向任何技能（B8） | 断点（推断，无实地记录） | 已核实 `wake_text` |
| P9 | 上游文本里写着 MMW 流程：四个技能大半是本仓文本（`implement` 15→101 行，`code-review` 87→15 行加 6 份 reference，`to-tickets` 105→206 行，`to-spec` 75→127 行）；另有纯「下一步」句写进上游：`grill-with-docs` 末句、`prototype` `UI.md` `## Next` | 与方向冲突；每次拉上游都有冲突 | 已核实行数（引 N3、N4）与原文句子 |
| P10 | 残留 `ask-matt` 目录带本仓改动，却没有 merge-note；两份 merge-note 仍以它为出处（B10、B11） | 断点（下次拉上游时） | 引 N10，已核实目录内容 |
| P11 | 事实 7 字面「MMW ships no router skill」与已定方向冲突 | 规则冲突 | 已核实 |
| P12 | `merge-notes/README.md` 的「两处同增同删」在四份 merge-note 里复述，7 个技能的名单完整写了三处（R2、R4） | 真重复 | 引 N10 §5，本轮核实 README 第 20–24 行 |
| P13 | `verify-ticket.py` 的 `RESUME:` 行按编号引用 `implement` `## Closing steps` 的步骤（`step 3 (…)`），`test_preflight.py` 钉着这些字面；`resume_at` 的 docstring 引用的段首句「A ticket that already carries a run of your own」在 `implement` 里已不存在（现在是「A ticket you are prompted back into」） | 按编号跨组件引用（C.6 信号 8 的实例）；docstring 已漂移 | 已核实 |

---

## 3. 总体形态

```
~/.agents/skills, ~/.claude/skills  (install.sh 按 skills.txt 软链到已安装 checkout，运行中冻结)
│
├─ self/mmw                         ← mode：唯一路由（新）
│   ├─ SKILL.md                     Where you are 表、头部判断、路由表、原则索引
│   ├─ playbooks/idea-to-tickets.md 头部 playbook（新）
│   ├─ principles/*.md              原则（新，起步 2 条）
│   └─ references/phase-boundaries.md  （由残留 ask-matt 迁入）
│
├─ 角色 playbook（原位，不动）：self/implement（分叉后）、self/code-review（分叉后）、
│   self/dispatch 的 references/night.md 与 one-ticket.md、self/advisor 的 references/advising.md
│
├─ 能力技能：其余自有技能与上游技能（上游尽量原文）
│
└─ 脚本：dispatch.sh、relay.py、watchdog.py、turn-guard.py、tool-guard.py、verify-ticket.py、
         models.py、各 oracle……（不动）

项目私有（消费仓库）：.mmw/、docs/agents/*.md、AGENTS.md 里指向 mmw 的一行（新）、
                     CODING_STANDARDS.md、TESTING.md
用户私有：~/.mmw/models.json（角色 → host/model/effort）、~/.mmw/installed-root
宿主级提示：shared.md（不承载 mode）
```

---

## 4. Q1 调用模型

### 4.1 每种到达方式各到哪一类组件

| 到达方式 | 到哪里 | 依赖的宿主行为 | 状态 |
| --- | --- | --- | --- |
| 人在会话里说一句话 | 消费仓库 `AGENTS.md` `## External References` 的一行（常驻）→ 模型加载 `mmw` → `Where you are` 表 → `playbooks/idea-to-tickets.md` 或路由行 → 按名加载能力技能 | (H1) 常驻文件里的一行能让模型在任务开头加载指定技能；(H2) 压缩后仍在上下文里 | **未核实，第 11 节 T1、T2** |
| 同上，备用 | `mmw` 的 description 自动触发 | 各宿主把 description 扫进系统提示（`AGENTS.md` `## Key Conventions`，已在用） | 已在生产中依赖；但同类的 `ask-matt` 实际调用 0 次，所以只当备用 |
| 用户斜杠 | `/mmw`、任何技能；7 个用户触发技能只能这样到达 | 已在用 | 不变 |
| description 自动触发 | 能力技能与角色技能（`implement`、`code-review`、`advisor`、`dispatch`、`retro` 等） | 已在用 | 不变；只删 P6 的两处重复声称 |
| 技能按名点名 | mode 与 playbook 点名能力技能（「the `to-spec` skill」）；其他技能点名 mode 内的文件（「the `mmw` skill's `principles/<slug>.md`」） | 被点名的技能必须模型可触发：Claude Code 上用户触发的技能不在模型列表里（本会话已核实）。点名另一个技能的文件，是现在的写法（例：`PRODUCT_RULES` 指向 `ui-acceptance` 的一节），每夜在用 | 已在生产中依赖 |
| mode 内部 | `SKILL.md` → `playbooks/`、`principles/`、`references/` 按相对路径 | 与现有 `references/` 相同 | 已在生产中依赖 |
| `dispatch.sh` 拼的启动提示词 | 「Use the implement skill to work ticket #N」→ `implement`；「Use the code-review skill to review ticket #N from base commit B」→ `code-review` 表第 1 行；「Use the advisor skill.」+ brief → `advisor` 第 2 行 | 已在用；`tests/dispatch/test_dispatch.sh`、`test_profiles.py` 钉着提示词字面 | **不变**，不经过 mode |
| relay 唤醒 `#<n> <event>` | 上下文里已有的角色技能；worker 加一行指向 `dispatch` `## On waking`（修 P7）；压缩后靠 `AGENTS.md` 那一行 → mode 的唤醒行 → `dispatch` `## On waking` → 角色文件（修 P8） | H1、H2 | `wake_text` 不改 |
| watchdog 与 turn guard 的消息 | 只到 orchestrator；`night.md` 事实表第 3 行已路由 | 已在用 | 不变 |
| hook 拒绝并改道（`tool-guard.py`） | worker、reviewer | 已在用 | 不变 |

### 4.2 哪些组件模型可触发，哪些只被点名

- **模型可触发**（description 进每个宿主的技能列表）：`mmw`；mode、playbook 或 `dispatch.sh` 启动提示词点名的每个技能；现在已模型可触发的其余技能保持原样。
- **只被点名、不是技能**：playbook、原则、mode 的 reference。它们没有 frontmatter，不进任何宿主的技能列表，所以没有常驻开销，也不存在「调用开关」在五个宿主上各自怎么解读的问题。
- **只由用户斜杠**：现有 7 个不变（`setup-matt-pocock-skills`、`grill-me`、`grill-with-docs`、`handoff`、`teach`、`improve-codebase-architecture`、`wait-what`）。新规则：playbook 不点名它们。路由遇到它们时，mode 照 `ask-matt` 原句告诉用户名字和理由，不替用户重建它（「give the user its name and the reason, and do not rebuild it」）。

### 4.3 mode 怎样被加载（替代 Cursor 的 `mode: true` / `reminder:`）

1. **主路：消费仓库 `AGENTS.md` 的一行。** 放在 `## External References`，例如 `| A task a person brings here, a wake after a compacted context, or not knowing which skill fits | the \`mmw\` skill |`。
   - 为什么放这里：它按项目常驻；五个宿主都读仓库根的 `AGENTS.md`（Claude Code 经 `CLAUDE.md` 的 `@AGENTS.md`；Cursor、Grok、Pi 是否读是**推断**，需 T1 实测）；它只在用 MMW 的仓库里付一行常驻成本。
   - 为什么不放 `shared.md`：ADR 0014 否决把 caller 侧规则写进用户级提示词的两条理由在这里同样成立（到不了 Cursor；为不相干的项目每回合付常驻成本）；而且 `shared.md` 是 owner 的全局提示，不属于 MMW（N8 §9.1）。
   - 谁写这一行：`mmw` 自己的 `Where you are` 表里有一行「本仓库 `AGENTS.md` 没有指向本技能的行 → 加上」。`manage-agents-md/SKILL.md` 第 150 行写明「Other skills add rows under … `## External References`」，`setup-matt-pocock-skills` 第 4 步也是这样加行的，所以不必改 `manage-agents-md`。
2. **备用：description 自动触发。**
3. **人工：`/mmw`。**
4. **没有采用的：** 用 `UserPromptSubmit` 一类钩子每轮注入一句（最接近 `reminder:`）。理由：各宿主的钩子事件不同；钩子也会在 worker 与 reviewer 的会话里跑；`install.sh` 管的钩子已经有两个宿主的已知缺口（N8 §9.3）。T1 不过时，它是第一个后备方案。

### 4.4 不依赖、以及必须依赖的宿主行为

- **不依赖：** `mode`、`reminder`、`alwaysApply`、`paths`、`subagent_type` 与 agent 定义文件（ADR 0015）；任何宿主对 `disable-model-invocation` 技能的按名读取；runner 投递斜杠命令（启动提示词继续用「Use the X skill」）；运行中从 trunk 重读组件（与 Self-hosting boundary 冲突，规范 B.1）。
- **必须依赖、需要实测的：**
  - H1：`AGENTS.md` 的一行能让模型在任务开头加载 `mmw`；
  - H2：压缩后 `AGENTS.md` 仍在上下文里；
  - H3：Cursor、Grok、Pi 读仓库根的 `AGENTS.md`；
  - H4：`mmw` 的 description 与 `grilling`、`wayfinder`、`to-spec`、`dispatch` 的 description 并排时，不抢同一个请求（`### Descriptions` 第 2 条）。
  - 这四项都在第 11 节。

### 4.5 被放弃的备选（N10 §10.4 的 A–E）

| 模型 | 放弃理由 |
| --- | --- |
| A 维持现状 | P1–P5 继续无家；P9 继续存在，与 `8ec53374`「上游尽量回到原文」相反 |
| B pstack 式：能力技能全部只被点名（`disable-model-invocation: true`） | Claude Code 上用户触发的技能模型根本够不到（本会话已核实）；`dispatch.sh` 的「Use the implement skill」依赖 `implement` 模型可触发（`merge-notes/implement.md` 第 24 行）；pstack 靠 Cursor 的 `mode`/`reminder` 常驻，MMW 的五个宿主没有对应机制 |
| C 纯 C：mode 模型可触发，只靠 description 加载 | 实地证据不利：`ask-matt` 就是这种形态，调用 0 次。本设计保留 C 的 description，但主路改成 `AGENTS.md` 一行 |
| D 纯 D：只按「谁启动会话」分层 | 本设计对脚本启动的会话采用 D（角色不经过 mode）；但只做 D 时，头部内容没有 playbook，用户已定的 playbook 层不成形 |
| E 不加路由，把缺口补进现有技能 | 要继续往上游文本里写 MMW 流程，与 `411750f5`、`8ec53374` 相反 |

**采用：** 人启动的会话用 C（mode + playbook），加 `AGENTS.md` 一行做加载；脚本启动的会话用 D（启动提示词直达角色 playbook）。

---

## 5. Q2 mode

### 5.1 几个 mode：一个

- **一个 mode `mmw`。** 放弃「工具箱一个、流水线一个」的理由：
  - 两个 mode 要求模型先在两个路由之间选，本身就是两个 description 抢同一个开头（`### Descriptions` 第 2 条）。
  - 流水线在夜里的部分由脚本路由到角色，不需要 mode。
  - 工具箱里的独立技能（`research`、`wizard`、`diagram-design`、`handoff`、`wait-what` 等）靠各自的 description 就能到达。给它们一张列表，就是 `ask-matt` 的 `## Standalone`：一份会漂移的第二份地图（事实 7 原本要防的问题；漂移证据见 `docs/reviews/2026-09-23-skill-set/汇总.md` 第 44 行、`docs/reviews/2026-09-28-lightweight/ask-matt.md` R1–R4，引 N10 §7）。
- **也放弃每个角色一个 mode**（pstack `poteto-agent` 式）：启动提示词已经点名角色技能；ADR 0015 已经决定不交付 agent 定义。

### 5.2 `mmw/SKILL.md` 装什么

按 pstack mode 的判据（规范 A.1）逐项筛过，只留会改变决定、又在别处没有家的内容：

| 节 | 内容 | 来源与收益 |
| --- | --- | --- |
| 开头两三句 | mode 做什么：把一个人带来的任务送到对的 playbook 或技能；一次把被唤醒或被压缩的会话送回它的位置 | 事实 1 |
| `## Where you are` | 第一行事实成立就走那一行（`night.md` 事实表的写法）：(a) 你的第一条消息由脚本拼出、点名了一个技能 → 按那个技能做，本技能不适用；(b) 收到 `#<n> <event>`、`relay.recovered since …`、`watchdog:` 或 `MMW turn guard:` → `dispatch` 技能的 `## On waking`，再看你角色的文件；(c) 本仓库 `AGENTS.md` 没有指向本技能的行 → 加上；(d) 正在一个阶段的边界 → `references/phase-boundaries.md`；(e) 一个人带来一件任务 → `## Head judgement` 与 `## Routes` | (a) 防止 worker 被 `AGENTS.md` 那一行带进 mode；(b) 修 P8；(d) 给 P5 一个家 |
| `## Head judgement` | 这件事要多个会话、还是小到用户自己检查就够。前者走 spec 流水线：每张票有脚本跑的验收判据、独立会话的 reviewer、关闭的票作为记录；后者用 `tdd` 在本会话里做，并告诉用户检查的人是他 | 迁入残留 `ask-matt` 第 22–26 行；修 P3 |
| `## Routes` | 一张表，每行 = 触发情境 → 去处 + 本行独有的门槛。只列会改变决定的行（见下） | 修 P1；wayfinder 的去向在 wayfinder 自己的第 6 步里，这里不重复 |
| `## Principles` | 每条一行：`- **<Title>** (\`<slug>\`). <何时适用>. <一句规则>.`，外加一句「应用某条原则时读 `principles/<slug>.md`」 | pstack mode `## Principles` 的写法 |

`## Routes` 的行（草案，只到架构粒度）：

| 情境 | 去处 | 本行独有的门槛 |
| --- | --- | --- |
| 一个想法、一个要做的功能或改动 | `playbooks/idea-to-tickets.md` | — |
| 太大、看不清路线 | `wayfinder` 技能 | 它的第 6 步给出 map 清空后的下一步 |
| 外来 issue，或流水线退回 `needs-triage` 的票 | `triage` 技能 | 它的第 5 步把 agent-ready 的送进 `to-spec` |
| 有东西坏了 | `diagnosing-bugs` 技能；修法按 `## Head judgement` 走 | 发现没有好的 seam：告诉用户 `improve-codebase-architecture` 合适，它只在用户点名时启动（修 B6 的断点，不改上游） |
| 跑一夜、跑一张票、改 host/model/runner、开任务板 | `dispatch` 技能 | — |
| 出包 | `exe-release` 技能 | — |

### 5.3 与 `shared.md` 的分工

- `shared.md` 是 owner 面向所有项目、所有会话的规则（谁决定什么、怎么汇报、怎么工作）。它不点名技能，第 11 行把无人会话的提问和汇报交给「its skills」。本设计不改它。
- mode 只装 MMW 专有的路由与头部判断，不复述 `shared.md` 的任何一条。pstack mode 里的 `## Autonomy`、`## Writing the reply`，在 MMW 里的对应物就是 `shared.md` 规则 1–5，所以 mode 不设这两节（N8 §9.2 第 5 条）。
- Cursor 读不到 `shared.md`（ADR 0007），这是宿主级提示的问题，不由 mode 解决。

### 5.4 大小上限

mode 被加载后，整份在上下文里（事实 3）。上限定为 100 行以内。超过时，先把只有某个分支才读的内容移进 `references/`（事实 5）。

---

## 6. Q3 playbook

### 6.1 放在哪里

- **头部 playbook**：`mmw-v2/skills/mmw/playbooks/<task>.md`。
- **角色 playbook**：原位不动（第 0 节第 4 条）。
- 放弃把角色 playbook 搬进 `mmw/playbooks/`：
  - 搬过去拿不到任何一种所列收益；
  - 启动提示词要改成「Use the mmw skill's playbooks/worker.md」，测试钉着现在的字面（`test_dispatch.sh` 第 2830 行、`test_profiles.py` 第 70 行，已核实）；
  - worker 会因此多加载一份它用不上的路由表。

### 6.2 格式（照 pstack 骨架，按 MMW 规则调整）

```
# <Name>

**You own <对象>. <一句立场>.**

<一段：这类任务为什么要这个顺序、结果交给谁、与相邻路由的区别>

## Where you are          （只有跨会话、会被压缩或唤醒的 playbook 才有）
| The fact | Go to |      （事实只取 tracker 与仓库里看得到的：spec 是否已发布、票是否已发布、map 是否存在…）

## Steps
1. **<Step name>.** <可勾掉的祈使动作>. <门槛、例外、理由>.
   Done when <完成判据>.
2. …

**Reply:** <本 playbook 独有的回复内容>；每个没做的步骤各一行：步骤名 + 理由。
```

相对 pstack 的调整：

| 调整 | 理由 |
| --- | --- |
| 每步加粗短名，作为稳定标识；别处按名字引用（「`idea-to-tickets` 的 **Spec**」），不按编号 | pstack 按编号跨组件引用没有任何检查，是它最脆的连线（规范 E.1 第 2 条、C.6 信号 8）；`SKILL-SET-RULES.md` `### Vocabulary` 已要求「by title rather than by number」 |
| 每步写 `Done when` | 本仓规则 `### Rules and completion criteria` |
| pstack 把 playbook 步骤原样抄进 todo 列表，没做的写 `skip: <reason>`；MMW 改成在 `**Reply:**` 里逐个交代没做的步骤 | todo 列表是会话记忆，压缩后会丢，也不是每个宿主都有；「看得见它没做什么」这个原意保住了（规范 D.1） |
| 需要重入的 playbook 在开头放 `## Where you are` 事实表 | MMW 已跑通的做法（`night.md` 第 13–22 行） |
| `**Reply:**` 只写独有内容，写法由 `shared.md` 管 | 照 pstack mode 第 109 行的分工 |

### 6.3 唯一的新 playbook：`idea-to-tickets.md` 的骨架

步骤名与内容来源：

1. **Grill.** 跑 `grilling` 技能，配合 `domain-modeling` 技能；每解决一个术语就写进 `CONTEXT.md`，按 `domain-modeling` 的说法提出 ADR。
   - 来源：`grill-with-docs` 的本仓正文。playbook 直接点名 `grilling` 与 `domain-modeling`，因为 `grill-with-docs` 是用户触发的，点名它，Claude Code 上的模型够不到。
   - 修 P2。
2. **Runnable questions.** 一个问题要运行才能回答时，用 `prototype` 技能。
   - LOGIC/EXP 的结论写进叶子目录的 `README.md`，带回第 1 步，这时不写生产代码。这是调用方限定被调方范围的写法（规范 C.2 的 `no-comments` 例子），不改上游规则 6。修 P4。
   - UI 胜出方案交给 `design-pages` 技能，在宿主有 Claude Design 工具的会话里进行。之后的链由 `design-pages`、`write-screen-contract` 自己的结尾段带到 `to-spec`（见第 8.1 节，不另写界面 playbook）。
   - 来源：`prototype` `UI.md` `## Next`（从上游收走）、残留 `ask-matt` 第 19–21 行。
3. **Someone else knows.** 卡在别人脑子里的知识 → `to-questionnaire` 技能。
4. **Who checks.** 对已经谈定的内容套用 mode 的 `## Head judgement`。走 No → `tdd`，本 playbook 结束。修 P3。
5. **Spec.** `to-spec`。门槛：第 1 步到第 6 步留在同一个没被清空、没被压缩的上下文里；接近上下文上限时，照 `references/phase-boundaries.md` 在最近的阶段边界压缩。
   - 来源：残留 `ask-matt` `### Context hygiene`、`grill-with-docs` 末句「in this same session」。修 P5。
6. **Tickets.** `to-tickets`。来源：`to-spec` `## Next`。
7. **Hand to the night.** 交给 `dispatch` 技能：开一夜，或一张票在夜外跑。什么时候开夜由用户决定。来源：`to-tickets` 第 8 步末句。

- `## Where you are`：已发布的 spec 没有票 → **Tickets**；票已发布并通过 lint → **Hand to the night**；有 prototype 结论、没有 spec → **Who checks**。
- `**Reply:**` 写：谈定了什么；spec 与票的编号；走了哪条路、谁来检查；没做的步骤。
- 其他路由从中途接入：wayfinder 清图后、triage 判 agent-ready、`improve-codebase-architecture` 定下决定后，都进 **Spec**。这就是这份 playbook 被三个以上入口复用的地方。

C.6 自查：它有所有权行、自己的门槛（**Who checks**、上下文不断）、自己的交付物（已发布并通过 lint 的票），调用 7 个技能，所以不是信号 5；步骤按名字引用，所以不是信号 8。

### 6.4 脚本启动的会话怎样直接进入指定 playbook

不变。启动提示词点名角色技能，角色技能的 `SKILL.md` 就是 playbook，或者用一张按提示词形状分门的表把会话送进 playbook（`code-review`、`advisor`）。worker 的 `AGENTS.md` 里也会有指向 `mmw` 的那一行，mode 的 `Where you are` 第 (a) 行把它送回启动提示词点名的技能。这一行是否足够，要实测（T1 的第 6 个提示）。

### 6.5 重入：三种现有机制都保留，统一到一条原则下

| 场景 | 机制 | 本设计的改动 |
| --- | --- | --- |
| orchestrator 被唤醒或刚进来 | `night.md` 开头的事实表 | 不动 |
| orchestrator 被压缩后收到唤醒 | 现在没有（P8） | `AGENTS.md` 那一行 → mode 的 `Where you are` 第 (b) 行 |
| worker 被 `resume` 叫回来 | `--preflight` 打印 `RESUME: step N (…)` | 可选：改为打印步骤名，同一次提交改 `implement` 的步骤标题与 `test_preflight.py`，并修 `resume_at` 的 docstring（P13）。这一项只在别的改动碰到 `## Closing steps` 时顺带做 |
| worker 被唤醒 | `implement` 第 1、3 步各自写了 ack，但没有「重跑被打断的命令」 | `implement` 里加一句：被唤醒时先按 `dispatch` 技能的 `## On waking` 做（修 P7）。放在 `## Closing steps` 开头，与 `RESUME:` 那句相邻 |
| 头部会话被压缩 | 现在没有 | `idea-to-tickets` 的 `## Where you are`，事实取自 tracker |

统一的原则是 `the-tracker-is-the-state`：位置从 tracker 与仓库里的事实推出，不从会话记忆推出（`dispatch` `SKILL.md` 第 8 行已这样写）。pstack 的 `session-pickup` 靠读旧 transcript 重建状态，MMW 不采用：transcript 的位置和格式都是宿主专有的（规范 E.2），而 MMW 的状态本来就在票上。

### 6.6 C.1 第 7 问（benny 式操作文件）对三个角色是否适用

- **worker：适用。** 单一入口（启动提示词）、单一任务（一张票）。`implement` 就是它的操作文件，不拆成 mode + playbook + 技能。
- **reviewer：适用。** `code-review` 的表按提示词里有没有 axis 名分门，这是区分角色，不是按任务类型路由。`references/session.md` 是操作文件。
- **orchestrator：大体适用。** 一个角色、几个子任务（一夜、一张票、收口、retro、`finish`），由人的一句话进入。`dispatch` 的 `## Find your moment` 对 orchestrator 起到了小 mode 的作用，`night.md` 的事实表负责重入。不另建一层。
- **advisor：适用。**

---

## 7. Q4 原则

### 7.1 存放形式：`mmw/principles/<slug>.md`，不是每条一个技能

| 备选 | 结论 | 理由 |
| --- | --- | --- |
| pstack 式每条一个技能，设成模型可触发 | 否 | 每条的 description 都进五个宿主每个会话的系统提示（事实 3 的注意力预算） |
| pstack 式每条一个技能，设成 `disable-model-invocation: true` | 否 | Claude Code 上按名够不到（本会话已核实） |
| 写进 `shared.md` | 否 | ADR 0014 的两条理由；而且 `shared.md` 属于 owner，不属于 MMW |
| **mode 目录下的文件** | 采用 | 没有常驻开销（只有 mode 被加载时，索引那一行进上下文）；按相对路径到达，与宿主无关；从别的技能引用时写「the `mmw` skill's principle `<slug>`」 |

### 7.2 命名与写法

- slug 用规则本身的短英文 kebab（五个词以内）。原则出自某份 ADR 时，沿用那份 ADR 的文件名，例如 `silence-is-never-a-pass`。
- 正文格式：
  - `# <Title>`；
  - 一到三句规则，写成事实而不是程序（Memory `ec59cec8`：陈述事实优于规定程序）；
  - `**Why:**`；
  - `**Applies when:**`（可观察的触发）；
  - 可选 `**The test:**`；
  - 可选 `**Not:**`（与相近原则的界线）。
- 不写历史，不列调用方（调用方列表会漂移）。
- 引用写法只有一种（pstack 有五种，规范 E.1 第 1 条）：
  - mode 与 playbook 内：`(principle \`<slug>\`)`；
  - 其他技能：`the \`mmw\` skill's principle \`<slug>\``。
  - lint 检查每个 slug 都存在、都已索引。

### 7.3 够格的门槛

规范 A.4 的四条（能用短名字说出口、有可观察触发、改变一个具体决定、跨任务），再加两条 MMW 的条件：

5. **至少被 mode 或一份 playbook 引用。** 只被脚本启动的角色用到的规则，照 `SKILL-SET-RULES.md` `### Load and disclosure`「A rule sits in the text of the agent that must follow it」留在角色文本里。worker 不加载 mode，给它一个指针就是一次跳转（规范 C.2「规则的读者读不到原则」）。
6. **理由现在没有 agent 读得到的家**（只在 ADR、`CODING_STANDARDS.md` 或不存在），或者多处各写了一版彼此不同的理由（N9 §9.3 第 4 条）。

原则层与 ADR 不算重复：ADR 记的是给维护者看的决定与否决项；原则是 agent 在行动时读的规则加理由。`SKILL-SET-RULES.md` `### Load and disclosure` 原本就这样分工：「a merge-note, an ADR or the glossary may explain it to maintainers, but the sentence the agent acts on is in the skill text」。

### 7.4 起步的两条（N9 候选逐条过门槛）

| 候选 | 结论 | 理由 |
| --- | --- | --- |
| PC1 + PC2 → `silence-is-never-a-pass` | **建** | 跨 7 个技能；理由只在 ADR 0008，技能里各写一版（`implement:22`、`night.md:7`、`ui-acceptance:34`，N9 §9.3）；`idea-to-tickets` 的 **Spec**、**Tickets**（判据要能失败）与 `night.md` 收口第 2 步都用。调用方原有的句子不删 |
| PC5 + PC6 → `the-tracker-is-the-state` | **建** | 理由在 ADR 0019、0020；mode 的唤醒行、`idea-to-tickets` 的 `## Where you are`、`night.md` 都依赖它 |
| PC8 基线即合同 | 暂不建 | `implement` 第 22 行已带完整理由，而唯一的读者（worker）不加载 mode；新 playbook 里用它的只有 **Runnable questions** 一处。第二个 mode 侧调用方出现时再建 |
| PC4 不轮询 | 暂不建 | 读者是角色与脚本作者，mode 与头部 playbook 用不到 |
| PC12 一个文件一个写者 | 暂不建 | `to-tickets`、`implement`、`night.md` 各自已有适配本场景的句子；新层只会加一份副本 |
| PC17 重跑可接上 | 暂不建 | 同上，而且主要由脚本保证 |
| PC7 脚本管确定性、文字管判断；PC3、PC18 拒绝的形状；PC16 一个家 | 不建 | 读者是写技能或脚本的人，家在 `writing-for-agents` 与 `CODING_STANDARDS.md` |
| PC9、PC10、PC11、PC13、PC14 | 不建 | 已在 `shared.md`（规则 1、4、10、12、13、15），再写一份就是重复 |
| PC15 只读靠文字 | 不建 | 只有 2 个技能用 |
| 残留 `ask-matt` 的 `PHASE-BOUNDARIES.md` | 进 `mmw/references/phase-boundaries.md`，不做原则 | 有触发、会改变决定，但 57 行，是一棵有序的判断树，按 reference 的判据（规范 A.5）更合适。mode 索引里给它一行 |

---

## 8. Q5 能力技能与 playbook 的分界

### 8.1 五张 Find-your-moment 表逐行判

| 技能与行 | 判定 | 处理 |
| --- | --- | --- |
| `dispatch` 第 1 行（worker 起 reviewer → `implement` `## Closing steps`）与 description「Start a reviewer from inside a ticket」 | 属于任务顺序，已在 worker 的 playbook（`implement` 第 3 步点名 `dispatch.sh start <n> reviewer`）；这一行只是来回跳一次 | **删** description 的这一句和第 1 行（修 P6）。worker 仍按名找到 `dispatch`，因为 `implement` 第 8 行点名了它的脚本 |
| `dispatch` 第 2 行（自己拿票 → `inside-a-ticket.md`） | 能力（`adopt` 命令与收口后的处理） | 留 |
| `dispatch` 第 3、4 行（`night.md`、`one-ticket.md`） | 角色 playbook | 留在原处；mode 的路由表指向 `dispatch` |
| `dispatch` 第 5、6 行 | 能力 | 留 |
| `dispatch` `## On waking` | 被唤醒会话共用的前置步骤 | 留；`implement` 与 mode 各加一个指针 |
| `verify-ticket` 第 16 行重定向与两行表 | 能力内部；description 描述的正是这个脚本的能力 | 留 |
| `ui-acceptance` 第 1 行（写页面票代码 → `implement` 的 reference）与 description「or before writing a page ticket's code」 | worker 的任务顺序，`implement` 第 16 行已写 | **删**（修 P6） |
| `ui-acceptance` 第 3 行（写判据 → `to-tickets` 的 reference） | 交给另一个技能，不是重复声称 | 留 |
| `ui-acceptance` 其余行与 `## Five rules while the product is running` | 能力内部；`PRODUCT_RULES` 指向它 | 留 |
| `design-pages` 四行、`edit-pages.md` `## Next`（同技能内）、`pull.md` `## Reached from here` | 能力内部。`Reached from here` 按技能自己的输出分支（`改动分类`、有没有 screen contract），第三支还带着动作本身（推到 `origin/<base branch>`、`reverify`），与 `pull.md` 其余部分是一个整体（N10 §9） | 留。**因此不写界面 playbook**：它只会复述这些结尾段（C.6 信号 3、9） |
| `write-screen-contract` `## Next` | 按自己的输出（第一次写还是 Re-runs）分支 | 留 |
| `code-review` 两扇门 | 按提示词形状区分角色，属于能力内部 | 留 |
| `advisor` 两扇门 | 同上；ADR 0014 要求 caller 的规则在 description 里 | 留 |

### 8.2 自有能力技能的结尾：什么留、什么移

- **留：** 下一步取决于本技能自己输出的结尾（`pull.md`、`write-screen-contract`）。这是「交回什么」的一部分，pstack 能力技能也有这一节（`## What to hand back`、`## Output contract`，规范 A.3）。
- **移：** 只重述 playbook 顺序的结尾句：分叉后 `to-spec` 的 `## Next`、`to-tickets` 第 8 步末句。它们换成一句固定的返回句：「Then return to the playbook that sent you; with none, the `mmw` skill routes what follows.」这样既守住 #538 的教训（任何一跳都不能让 agent 找不到下一步），顺序又只剩一个家。

### 8.3 上游技能回到原文的规则

一段上游文本上的 MMW 改动，按下面顺序判定，第一个「是」决定去处：

1. **这个技能的行，上游的已不到一半吗？** 是 → **分叉**：整体搬进 `mmw-v2/skills/<同名>/`，`skills.txt` 改成 `self/<名>`；`mmw-v2/upstream/` 里那一份恢复成最近一次 squash 的原文，不安装；`merge-notes/README.md` 一张「分叉表」记下名字、上游路径、分叉起点提交，并规定每次拉上游都读一遍这些技能的上游 diff，按判断移植。当前命中：`implement`、`code-review`、`to-tickets`、`to-spec`。
   - 收益：上游回到原文；`## 本仓自有正文的技能` 这个特例和每次拉上游的冲突处理都消失。
   - 代价：`to-spec` 以后拿不到自动合并；另外三个本来就声明不合并（`merge-notes/README.md` 第 36 行）。
2. **是调用开关吗？** `disable-model-invocation` 与 `policy.allow_implicit_invocation` 两处一起。按新规则（第 9 节）留在上游文本里，merge-note 只写站哪一边。
3. **是 description 的触发句吗？** 它决定什么能到达这个技能，属于接入。留，记 merge-note（`411750f5`：接入在边缘做，description 就是边缘）。
4. **改变了能力，或者删掉它 agent 就会做错吗？**（即使 playbook 在上下文里，也会做错。）留，记 merge-note。实例：
   - `prototype` 的 EXP 分支；
   - `resolving-merge-conflicts` 多出的触发；
   - `tdd` 的 seam 与重构去处；
   - `triage` 第 5 步：不改就会给原始 issue 打 `ready-for-agent`；
   - `improve-codebase-architecture` `### 4`：不改就会在会话里直接重构，绕过票与验收；
   - `wayfinder` 第 6 步：清图的停止判据、「map 留着不关」、新会话，与下一步写在同一步里，拆开会散。
5. **是 host 中立写法吗？**（「call the Skill tool」→「read the X skill's `SKILL.md`」）留（`merge-notes/README.md` `## host 中立`）。
6. **只是点名下一个技能的句子吗？** 移进 playbook，上游那句恢复原文。当前命中：`grill-with-docs` 末句、`prototype` `UI.md` `## Next`。
7. **以上都不是**（文风、措辞）→ 恢复上游原文（`SKILL-SET-RULES.md` `### Upstream skills` 现有规则）。

残留 `ask-matt` 目录整个恢复上游原文、不安装。它带本仓改动的内容按第 5、6 节迁入 `mmw`；`merge-notes/triage.md` 第 12 行、`wayfinder.md` 第 21 行把出处改成 `mmw`（修 P10）。

---

## 9. Q6 旧规则逐条处理

### 9.1 `SKILL-SET-RULES.md`

| 条目 | 处理 | 原本防什么 | 新架构怎样解决、原意怎样保住 |
| --- | --- | --- | --- |
| 事实 1 理解而不只步骤 | 保留 | agent 遇到步骤没写到的情形 | 同样适用于 playbook 与原则（原则的 `**Why:**`） |
| 事实 2 脚本管确定性 | 保留 | 文字复述脚本、判断藏进脚本 | 不变。它是原则候选 PC7，但读者是写技能的人，家留在 `writing-for-agents` |
| 事实 3 注意力是预算 | 保留 | 读到用不上的材料 | 新用途：mode 设 100 行上限；mode 不放角色表 |
| 事实 4 先定方向再信任 | 保留 | 僵硬、脆弱的清单 | playbook 步骤只写门槛与判断 |
| 事实 5 按分支渐进加载 | 保留 | 碎片、跳转 | playbook 按任务类型一文件一类，正是按分支拆 |
| 事实 6 技能是按名组合的平级件 | **改写** | 嵌套、复制别的技能的文件 | 加一句：playbook 与原则是 `mmw` 技能里的文件，别的技能按「the `mmw` skill's …」点名。「不复制、不复述」保留 |
| 事实 7 一个家；「MMW ships no router skill」；「description 说何时开始，结尾段说下一步」；「结尾段从想法走到关票没有缺口」 | **改写，废止「no router」一句** | 第二份副本（把流程重述成地图）会漂移；两个技能抢同一时刻 | 顺序只有一个家：playbook。能力技能的结尾只说交回什么，或者用那句固定返回句。mode 是唯一路由，由 lint 与实际同步（Structural-mechanism check）。「从想法走到关票没有缺口」改成：mode 的路由加 playbook 的步骤连起来走到关票，由 `REVIEWING-A-SKILL-SET.md` 的走查从 mode 出发来检查。**这不是「加」一份地图**：顺序句从能力技能里「搬」进 playbook（N10 §10.3「搬而不是加」） |
| `### Load and disclosure` 全部 | 保留 | 跳转、碎片、规则写错读者 | 「A rule sits in the text of the agent that must follow it」正是原则层不替换角色文本的理由（第 7.3 节第 5 条） |
| `### Redundancy and bloat` | 保留 | 重复、缓存、沉积 | 不变 |
| `### Scripts and judgement` | 保留 | 同事实 2 | 新 lint 就是它的一次应用 |
| `### Descriptions` 只写触发；并排读；不写 host | 保留 | 路由写进 description 会漂移；两个 description 抢一件事 | 并排检查的范围扩到 `mmw` 的 description；P6 的两处重复声称删掉 |
| `### Vocabulary` | 保留 | 一词多义、自造词 | 在 `docs/contexts/toolbox/CONTEXT.md` 加 **mode**、**playbook**、**principle** 三个词条；**playbook** 取 pstack 的意思（一类任务的步骤顺序），与 `why/references/source-playbook.md` 的用法区分 |
| `### Hand-offs`「每个技能以下一步或返回的调用方结尾」 | **改写** | agent 在某一跳找不到下一步就自己发明做法（#538） | playbook 的步骤点名下一步；能力技能以交回什么结尾；下一步取决于自身输出的自有技能保留分支；链上的自有技能以固定返回句结尾 |
| `### Hand-offs` 其余（每个事件一条指令、按名点名不写路径、硬依赖一行） | 保留 | — | 不变 |
| `### Prompts written for other agents` | 保留 | 模型现写的 prompt 替被启动方划范围（ADR 0014） | 启动提示词不变 |
| `### Upstream skills` | **补充** | 上游被改写后无法跟进 | 「fewer than half」一句从「按本仓文本审」升级为「分叉出 subtree」；接入改动的七级判定（第 8.3 节）写进这一节 |
| `### Paths and host neutrality` | 保留 | 路径与宿主绑定 | grep 检查的范围扩到 `playbooks/`、`principles/` |
| `### Rules and completion criteria`、`### Examples`、`### Refusals`、`## Editing`、`## Verifying` | 保留 | — | playbook 步骤同样用 `Done when` |

### 9.2 ADR

| ADR | 处理 | 说明 |
| --- | --- | --- |
| 0003 不打包成插件 | 保留 | mode 是技能，不需要 pstack 的 `plugin.json` |
| 0006 装进中立目录 | 保留 | `mmw` 与分叉技能照同样的软链安装 |
| 0007 提示词源在仓库 | 保留 | mode 不进 `shared.md` |
| 0008 沉默永远不是通过 | 保留 | 成为原则 `silence-is-never-a-pass` 的理由源 |
| 0010、0020、0022 唤醒而非轮询 | 保留 | `wake_text` 不加技能名；P8 由 mode 的唤醒行解决 |
| 0014 advisor 一扇门 | 保留 | 它否决「caller 规则进用户级提示词」的理由，同样用来否决 mode 进 `shared.md`。`AGENTS.md` 一行不违反这两条理由：它按项目常驻，并且预期五个宿主都读（H3 待测） |
| 0015 不交付 subagent | 保留 | 「角色 = playbook + `models.json` 一行」就是它的延续。pstack 的 `poteto-agent`、Comment Sicko 不引入 |
| 0019 票上状态是事件的 fold | 保留 | 成为原则 `the-tracker-is-the-state` 的理由源 |
| **新 ADR（待写）** | 新增 | 两条决定：(1) 一个 mode；playbook 与原则放在它的目录里；`AGENTS.md` 一行负责加载，取代事实 7 的「no router」；(2) 上游行不到一半的技能分叉出 subtree |

### 9.3 `merge-notes/README.md`

| 节 | 处理 | 原本防什么 | 新做法 |
| --- | --- | --- | --- |
| `## disable-model-invocation` 的 7 个名单 | **改写成规则** | 两个开关不一致；用户触发的技能与别的技能抢触发（`grill-with-docs`）、夜里被 worker 自己触发（`improve-codebase-architecture`） | 规则：「mode、playbook 或 `dispatch.sh` 启动提示词点名的上游技能，两个开关都去掉；其余保持上游设置」。lint 检查被点名的技能都模型可触发。按这条规则推出来，今天的 7 个恰好都没被点名，所以都保持用户触发，原来防的两类问题照样防住。四份 merge-note 里对这条规则的复述删掉（P12） |
| `## host 中立` | 保留 | — | — |
| `## 本仓自有正文的技能` | **废止** | 拉上游时误合并本仓正文 | 由分叉取代，改成分叉表 |

### 9.4 Memory 里的写法决定

| 记录 | 处理 | 说明 |
| --- | --- | --- |
| `411750f5`：description 只留触发；上游能不改就不改，接入在边缘做 | 保留，并加强 | 分叉与第 8.3 节的七级判定是它的落实 |
| `ce037679`：技能间写名字、不写路径 | 保留 | playbook 与原则按技能名加文件名点名 |
| `ce037679`：「不系统区分用户调用与模型调用」 | **改写** | 调用开关改为从 playbook 推出，由 lint 检查，作者不必逐个判断。原意（不给作者加负担、不按调用方式要求 MMW）保住 |
| `ce037679`：「一张与实际同步的总图」 | 落实 | mode 的路由表是给 agent 的图，lint 保证同步；给人看的图不在本设计范围（N10 §11 未确定这句指哪一种） |
| `f4c3d378`：以技能为第一层编排 | 保留 | mode 本身是技能 |
| `fe94802d`：平级调用、禁止嵌套 | 保留 | — |
| `fe94802d`：不改上游 frontmatter；用 `disable-model-invocation` 强制层级被排除 | **改写前半，保留后半** | 前半在 `2b92efe3`、`5181acc2` 之后已不成立，改成「只许按第 9.3 节的规则翻转调用开关」。后半保留，并补上理由：Claude Code 上用户触发的技能模型够不到，用开关强制层级会让 playbook 断掉 |
| `c155ffc2`：调用方只给角色名与票号 | 保留 | 启动提示词不变 |
| `ec59cec8`：陈述事实优于规定程序 | 保留 | 原则文件的写法 |
| `8ec53374`：「agent 定义 = 读哪个 playbook + `models.json` 一行」 | 落实 | 不建文件，就是现在的启动提示词加 `models.json` 行（ADR 0015） |
| `292e8f2d`：pstack 只作研究快照，进入形式待定 | 本设计给出规则 | 见第 10 节 |

---

## 10. Q7 扩展路径

### 10.1 从 pstack 或其他合集加东西

| 要加的 | 怎样进来 | 需要改的现有文字 |
| --- | --- | --- |
| 一条原则 | 复制进 `mmw/principles/<slug>.md`：去掉 frontmatter（它在这里不是技能），正文照抄；来源记在 `merge-notes/` 下一份按来源开的说明里（例如 `pstack.md`：pstack 路径、快照提交、MMW 改了什么）。pstack 的 23 条原则对宿主专有词的 grep 都是 0 命中（第 1 节，粗筛），大多可以照抄 | mode `## Principles` 加一行；lint 自动检查。加之前先过 Already-covered 检查：例如 `principle-prove-it-works` 与 `silence-is-never-a-pass` 可能重叠 |
| 一种工作流 | 在 `mmw/playbooks/` 写一份 MMW 格式的 playbook，每步点名本集的技能；pstack 原文只作来源，记进上面那份说明 | mode `## Routes` 加一行 |
| 一个能力技能，可以照原文用 | 整仓可 subtree 的，照 mattpocock 的做法：`mmw-v2/upstream-<源>/` 加 `skills.txt` 前缀。pstack 在 `cursor/plugins` 这个多插件仓库里，subtree 只能拉整个仓库：先在本地克隆里 `git subtree split --prefix pstack`，再对切出来的分支 `subtree add/pull` | `skills.txt` 加一行 |
| 一个能力技能，要改成与宿主无关 | 分叉进 `mmw-v2/skills/<名>/`，来源记进说明。pstack 做子代理编排的技能（`how`、`why`、`arena`、`interrogate`、`reflect`、`swarm`、`architect`）都带 `Task` 参数、`subagent_type` 或模型 slug（grep 命中 1–4 个文件），改写后的文本会与上游持续冲突，所以分叉比 subtree 省事 | `skills.txt` 一行；有 playbook 点名它时加上 playbook 那一步 |

加一个新组件时，不需要改任何现有技能的正文。要动的只有三张登记表：`skills.txt`、mode 的路由表、原则索引，lint 检查三者一致。这就是「扩展只加不改」的实现。

### 10.2 Cursor 专有机制的替代（规范 E.2）

| pstack 机制 | MMW 的替代 |
| --- | --- |
| `mode: true`、`reminder:` | `AGENTS.md` 一行，加 `mmw` 的 description（第 4.3 节）；钩子注入是后备方案 |
| `disable-model-invocation: true` 集中调用权 | 第 9.3 节的规则加 lint；playbook 与原则不是技能，也就没有开关 |
| `paths:` 按文件类型加载 | 不引入。需要时写成 description 的触发分支，或由调用方点名 |
| `alwaysApply` 的 `pstack-models.mdc` | `~/.mmw/models.json`，只由 `models.py config` 写（ADR 0024）；脚本显式读取，不靠注入 |
| `agents/*.md` 加 `subagent_type` | 宿主自带的通用 subagent 加技能（ADR 0015）；按能力写（「a host that can run subagents」） |
| `Task` 的 `model`、`readonly` 等参数 | 按能力写；只读靠文字（N9 PC15） |
| `/loop`、`/goal`、云端代理、唤醒链 | relay 唤醒、watchdog、turn guard（ADR 0010、0021、0022） |
| 运行中从 trunk 重读组件 | **禁止**（Self-hosting boundary）；所有 playbook 与原则只按技能相对路径读，解析到冻结的已安装 checkout |
| 内置 `create-skill` | `writing-for-agents` |
| `AskQuestion` | `shared.md` 规则 1 加 `tool-guard.py question` |
| `agent-transcripts/` | 不依赖；交接用 `handoff`，重入用 tracker |
| `cursor-team-kit` 的 `control-ui` / `control-cli` | `ui-acceptance` 的 oracle 与 `playwright-cli` |
| `show-me-your-work` 决策记录 | 票上的事件与 `Decisions I made on my own` |

### 10.3 项目私有组件（规范 A.11）在 MMW 里对应什么

| pstack | MMW |
| --- | --- |
| 目标仓库 `.cursor/skills/verify-<app>/` | 消费仓库 `.mmw/`（`target.json`、harness、journeys、stories），由 `ui-acceptance` 的 `target_config.py` 维护 |
| `pstack-models.mdc` | `~/.mmw/models.json` |
| benny 的配置、feature map | `docs/agents/*.md`（由 `setup-matt-pocock-skills` 写）；`CODING_STANDARDS.md`、`TESTING.md`（由 `manage-agents-md` 写） |
| 让 mode 常驻的机制 | **新**：`AGENTS.md` `## External References` 里指向 `mmw` 的一行，由 `mmw` 自己加 |
| `<handle>-mode` | 暂不需要。以后某个消费仓库要私有 playbook 时，放在仓库里，由 mode 的 `Where you are` 表按「本仓库有 `.mmw/playbooks/`」这个事实去读（推断出的扩展点，现在不建） |

---

## 11. Q8 风险与验证

### 11.1 风险

| # | 风险 | 可能性 | 后果 | 验证 |
| --- | --- | --- | --- | --- |
| K1 | mode 没被加载（H1、H3 不成立） | 中到高（`ask-matt` 调用 0 次） | 头部照旧即兴；第 3 阶段删掉结尾句后，比现在更差 | T1；不过就不做第 3 阶段，改试钩子注入 |
| K2 | 压缩后丢了 `AGENTS.md`（H2），orchestrator 收到 `#n ticket.passed` 不知道怎么办 | 低（推断） | 一夜停住，但 watchdog 与 turn guard 仍在 | T2 |
| K3 | `mmw` 的 description 抢了 `grilling`、`wayfinder`、`to-spec` 的请求（H4） | 中 | 多绕一跳，不会断 | T1 的并排提示 |
| K4 | worker 被 `AGENTS.md` 那一行带进 mode，又没被第 (a) 行送回 | 低 | worker 多读一份文件；最坏是偏离 `implement` | T1 第 6 个提示；dispatch 的一个假 runner 场景 |
| K5 | 分叉改了四个技能的源路径，`install.sh --check` 报旧软链；`tests/verify-ticket/test_draft.py` 引用了上游路径（已核实） | 确定会发生 | 改完不跑 `install.sh`，宿主读到的还是旧的 | 分叉那张票同一次提交改测试；发布时需要用户授权跑一次 `install.sh`（`AGENTS.md` Gotchas：只在用户明确授权时运行） |
| K6 | 冻结运行时：变更本身作为票在本仓库跑，跑它的是旧的已安装版本 | 确定会遇到 | 若在同一批票里给本仓库 `AGENTS.md` 加指向 `mmw` 的行，而已安装版本还没有 `mmw`，会话就会看到一个不存在的技能名 | 顺序规则：`mmw` 先随一次发布进入已安装 checkout，并跑过 `install.sh`，之后才给任何仓库加那一行。变更自身的测试只在隔离的测试 home 里跑（Self-hosting boundary） |
| K7 | 拉上游：分叉前的 `mmw-v2/upstream/` 历史里有本仓改动，恢复原文的那次提交与下一次 squash 可能冲突 | 低 | 一次性的冲突处理 | T6：在丢弃分支上试拉一次 |
| K8 | 原则被引用，却改变不了任何决定（C.6 信号 7） | 中 | 多读的文字 | `SKILL-SET-RULES.md` `## Verifying` 的真实走查：记录 agent 是否打开了原则文件、之后是否做了不同的选择 |
| K9 | lint 本身漏报（例如按名点名的写法有多种） | 中 | 同步只是表面上的 | lint 只认一种点名写法；引用写法统一由 `### Hand-offs` 规定 |
| K10 | `RESUME:` 改成步骤名时，`test_preflight.py` 与 `resume_at` 要一起改 | 确定（只在做这一项时） | 不同步的话 worker 被送错步骤 | 同一次提交；已有的 `test_preflight.py` 会拦住 |

### 11.2 验证

- **T1 加载实测。**
  - 设置：在一个带 `AGENTS.md` 指向行的临时消费仓库里（用 tracker 的假实现），五个宿主各起全新会话。
  - 六个提示：「我有个想法想做出来」「这个页面坏了」「grill me on X」「/to-spec」「今晚跑 spec #N」，以及一条 worker 形状的启动提示词。
  - 记录：会话打开了哪些 `SKILL.md` 与 playbook 文件，从 transcript 或宿主日志读。
  - 通过：线上角色所在的宿主（claude、codex、grok）在前五个提示里至少 4 次打开 `mmw`，第六个提示不偏离 `implement`；cursor 与 pi 如实记录结果。
- **T2 压缩后重入。** 用 `tests/dispatch` 的假 runner 与假 tracker 开一夜，对 orchestrator 会话执行宿主的压缩命令，再经 runner 投递 `#3 ticket.passed`。检查它先 ack，再跑 `status` 与 `advance`。
- **T3 worker 唤醒。** 修 P7 之后，在一夜真实运行里查 worker 被 `reviewer.reported` 唤醒时，是否重跑了被打断的命令。
- **T4 按名到达。** 持有 mode 的会话照 `idea-to-tickets` 做到 **Spec**，在五个宿主上确认它都能加载 `to-spec`。
- **T5 lint。** 新 lint 放进每个 `run.sh` 开头的共用检查；另写反例，证明它能失败（把一个被点名的技能设成用户触发，lint 必须报错）。
- **T6 拉上游演练。** 分叉与恢复之后，在丢弃分支上 `git subtree pull`，期望恢复过的目录零冲突。
- **T7 冻结。** 扩展现有的路径 grep，确认 `mmw/` 下没有仓库路径、没有爬出技能目录的相对路径、没有「from trunk」。发布后跑 `install.sh --check`。
- **T8 走查。** 按 `SKILL-SET-RULES.md` `## Verifying`，给一个全新 agent 本仓库任务板的一个小想法，走 `idea-to-tickets`；另给一个 map 已清空的 wayfinder 场景。报告它打开了哪些文件、在哪里猜、在哪里停。

### 11.3 落地顺序（每一阶段都作为本仓库的票，在没有 watch 开着时发布）

- **阶段 0：** 跑 T1–T2 需要的实测环境（只读，不改产品）。
- **阶段 1（只加）：**
  - 新建 `mmw`（`SKILL.md`、`idea-to-tickets.md`、两条原则、`phase-boundaries.md`）、新 lint、新 ADR、词条；
  - 做 P6、P7 两处小修；
  - 发布，需要一次用户授权的 `install.sh`；
  - 之后给消费仓库加 `AGENTS.md` 那一行；跑 T1、T2、T4、T8。
- **阶段 2（分叉）：** 四个技能搬到 `self/`，上游恢复原文；残留 `ask-matt` 恢复原文；`merge-notes` 改写；T6；发布，需要一次用户授权的 `install.sh`。
- **阶段 3（删，前提是 T1 通过）：**
  - 删上游的两句纯下一步（`grill-with-docs` 末句、`prototype` `UI.md` `## Next`）；
  - `to-spec` `## Next` 与 `to-tickets` 第 8 步末句换成返回句；
  - 改写 `SKILL-SET-RULES.md` 的事实 6、事实 7 与 `### Hand-offs`。
  - 这一阶段放在最后，因为它是唯一会在 mode 没被加载时让情况变差的一步。

---

## 12. 改动清单、收益与 C.6 自查

| # | 改动 | 所列收益中的哪一种 |
| --- | --- | --- |
| C1 | 新建 mode `mmw`（`Where you are`、`Head judgement`、`Routes`、原则索引） | 给无处安放的内容一个家（P1、P3、P5、P8）；让以后加外来技能时不必改现有文字（登记表） |
| C2 | `playbooks/idea-to-tickets.md` | 家（P2、P4、Context hygiene）；把 MMW 流程移出上游文本（两句）；被 3 个以上入口复用 |
| C3 | `principles/` 两条 | 家（ADR 里的理由现在没有 agent 读得到）；被 mode、`idea-to-tickets`、`night.md` 复用 |
| C4 | `references/phase-boundaries.md` | 家（P5） |
| C5 | 消费仓库 `AGENTS.md` 一行 | 消除断点（P1、P8 的加载问题）；取代 Cursor 专有机制 |
| C6 | 分叉 `implement`、`code-review`、`to-tickets`、`to-spec` | 上游回到原文（P9） |
| C7 | 残留 `ask-matt` 恢复原文 | 上游回到原文；消除断点（P10） |
| C8 | 删 `dispatch`、`ui-acceptance` 的重复声称 | 去掉经 grep 核实的真重复（P6） |
| C9 | `implement` 指向 `## On waking` 的一句 | 消除已核实的断点（P7） |
| C10 | 调用开关改成规则加 lint；删 merge-note 里的复述 | 去掉真重复（P12）；规则变机制 |
| C11 | 新 lint | 规则变机制（事实 7 原意的机械部分） |
| C12 | 改写 `SKILL-SET-RULES.md` 的事实 6、7 与 `### Hand-offs`、`### Upstream skills` | 消除已核实的规则冲突（P11） |
| C13 | （可选）`RESUME:` 改打印步骤名 | 消除已核实的漂移与按编号引用（P13） |

**C.6 形式拆散的 11 个信号逐条自查：**

1. **没有先确认已有组件不是合适的归宿。** 头部内容没有已安装的归宿（P1–P5 已核实）；界面链已有归宿，所以没建界面 playbook；角色 playbook 原位不动。**未触发。**
2. **新增内容不改变决定。** C1 的每一行路由都改变去处或门槛；列表里去掉了只重复 description 的独立技能。C3 用第 7.3 节的门槛筛过。**未触发**（原则部分待 K8 实测）。
3. **重复已有的、位置得当的指引。** mode 不复述 `shared.md`；原则 `silence-is-never-a-pass` 与调用方原句并存，这是读者不同的可接受重复（规范 C.5），而且 mode 侧原来没有这条理由。**部分触发，已说明。**
4. **本可以由机制强制的规则写成了文字。** 同步问题交给 lint（C10、C11）。**未触发。**
5. **playbook 只调一个技能，没有门槛、所有权、交付物。** 只建了 `idea-to-tickets`；wayfinder、triage、bug、代码健康只作为路由行。**未触发。**
6. **reference 每次都读、只有一个调用方、读者是本代理。** `phase-boundaries.md` 只在阶段边界那一行分支才读。**未触发。**
7. **原则说不出改变哪个决定，或只适用一步。** 两条都跨三个以上位置，决定写在第 7.4 节。**未触发**（K8 实测）。
8. **拆完需要按步骤编号引用。** playbook 步骤按名引用；C13 顺带去掉一处现有的编号引用。**未触发。**
9. **拆出的内容没有第二个调用方、也不减少重复。** 角色 playbook 不搬，正是因为会触发这一条。**未触发。**
10. **把单入口的固定流程拆成三层。** worker、reviewer、advisor、orchestrator 都保持操作文件。**未触发。**
11. **把只在流程之间复用的内容做成能力技能。** 没有新建能力技能；`idea-to-tickets` 是 playbook，不是技能。**未触发。**

---

## 13. 不动清单

| 部件 | 不动的理由 |
| --- | --- |
| `dispatch` `references/night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md`、`## On waking` | orchestrator 的操作文件已经有事实表重入，而且是单入口单任务（C.1 第 7 问）；搬进 mode 拿不到任何收益 |
| `implement` 的全部步骤内容（除 C9 一句、C13 可选项；C6 只是整体搬家） | worker 的操作文件；`RESUME:` 与测试钉着它的结构 |
| `code-review` 的门表、`references/session.md` 与四个 axis | 角色区分与能力内部；启动提示词的形状与门表是一个整体（N10 §9） |
| `verify-ticket` 全部 | 能力内部；description 描述的正是它的能力 |
| `ui-acceptance` 除第 1 行与 description 那一句之外的全部，包括 `## Five rules while the product is running` | 能力内部；`PRODUCT_RULES` 指向它 |
| `design-pages` 全部（包括 `pull.md` `## Reached from here`、`edit-pages.md` `## Next`）、`write-screen-contract` `## Next` | 按自身输出分支，与技能其余部分是一个整体 |
| `advisor`、`retro`、`exe-release`、`code-checkers`、`manage-agents-md`、`diagram-design` | 单一能力，入口靠 description 或调用方，没有第 2 节的问题 |
| `triage` 第 5 步、`wayfinder` 第 6 步、`improve-codebase-architecture` `### 4`、`tdd`、`prototype` EXP、`resolving-merge-conflicts`、`to-questionnaire`、`writing-for-agents` 的 description | 第 8.3 节第 2–5 级：接入、改变能力或防错，留在上游文本并记 merge-note |
| `grilling`、`domain-modeling`、`codebase-design`、`research`、`wizard`、`handoff`、`teach`、`wait-what`、`diagnosing-bugs`、`grill-me`、`setup-matt-pocock-skills` | 上游原文或只有 host 中立改动；B6 的断点由 mode 路由行处理，不改 `diagnosing-bugs` |
| 7 个用户触发技能的调用开关 | 按新规则推出，结果与现在相同 |
| 其他技能的 description 触发句 | 第 8.3 节第 3 级；只在 T1 显示与 `mmw` 冲突时才重审 |
| `dispatch.sh` 的 `AUTONOMOUS`、`PRODUCT_RULES` 与三种启动提示词 | 测试钉着；已经是「数据加一个指针」（N10 R9） |
| `relay.py` `wake_text`、`watchdog.py`、`turn-guard.py`、`tool-guard.py` | 脚本层，已跑通；P8 不靠改唤醒文字解决 |
| `models.json` 结构、`models.py` | 「角色 = playbook + 一行」已经实现 |
| `shared.md`、`hosts/*.md`、`render.py` | 宿主级提示，不是 MMW 的 mode |
| `CODING_STANDARDS.md`、`TESTING.md` | 仓库规则，由 review axis 读 |
| 现有 ADR 正文（只在被新 ADR 取代的地方按惯例加注） | ADR 记录决定 |
| task board、`migrations/`、`tests/` 结构 | 与分层无关 |
| N9 的 16 个未建的原则候选 | 第 7.4 节，各有理由 |
| `dispatch.sh` 头注释与 `--help` 的漂移（B12） | 真问题，但不属于架构，留给普通票 |

---

## 14. 未确定

| 事项 | 需要什么实测或决定 |
| --- | --- |
| H1：`AGENTS.md` 的一行能否让五个宿主在任务开头加载 `mmw` | T1 |
| H2：压缩后 `AGENTS.md` 是否仍在上下文里 | T2，每个宿主各一次 |
| H3：Cursor、Grok、Pi 是否读仓库根的 `AGENTS.md`（Grok 有 `[compat.claude]`，行为可能不同） | T1 的前置检查 |
| H4：`mmw` 的 description 是否与 `grilling`、`wayfinder`、`to-spec` 抢请求 | 并排走查加 T1 |
| Codex、Grok、Pi、Cursor 能否按名读取用户触发的技能 | 本设计不依赖它；只有将来想放宽「被点名的技能必须模型可触发」时才需要测 |
| 分叉后 `to-spec` 失去上游自动合并的实际代价 | 要看上游 `to-spec` 此后的改动频率；每次拉上游时读 diff 记录 |
| 原则文件是否真的改变 agent 的决定 | K8 的走查 |
| 是否从 pstack 引入任何原则或技能 | 属于用户的范围与优先级决定；本设计只给出进入的方式 |
| Memory `ce037679` 的「总图」是给人看的图还是给 agent 的路由 | 用户一句话即可；本设计先按给 agent 的路由加 lint 落实 |
| 私有 playbook 扩展点（`.mmw/playbooks/`） | 等到第一个消费仓库真有需要再决定；现在不建 |
