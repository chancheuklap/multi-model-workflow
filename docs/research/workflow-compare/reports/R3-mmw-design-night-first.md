# R3 MMW 的 pstack 分层架构设计（夜间优先）

本文为 MMW（`mmw-v2/` 的技能合集与夜间落地流水线）定 pstack 分层架构的具体形态。只定架构层面的决定，不逐个归置部件。设计立场：从无人值守的夜出发（脚本启动的多个会话、事件唤醒、上下文压缩后的重入、hook 拦截、冻结版本），先让这部分在新架构里更稳、更好改，再让白天的部分与之一致。

准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7），引用写成「L7 C.1 第 7 问」这类形式。事实清单是 N1–N10 与 `N11-mmw-gaps.json`（下称 N1…N11）。凡采用的结论都回到原文核对过，核对情况见第 17 节。标「推断」的是由原文推出、原文没有直接写的；做不出判断的放在第 16 节。

---

## 0. 结论摘要

1. **两个入口，不是一个。** 流水线入口就是现有的 `dispatch` 技能，保持很薄：角色表、`## On waking`、流水线常驻规则。白天的工具箱入口是新建的 `mmw` 技能：头部判断、路由表、原则索引。分成两个的理由是夜里每次重入都要读入口，而 `dispatch` 的脚本、唤醒与处理动作本来就是一个天然整体（N10 第 9 节「事件 → 收件人 → 动作这条链」）。
2. **夜里的三个角色各用一个操作文件，不拆成三层。** worker、orchestrator、单票 orchestrator 都是单一入口、单一任务类型（L7 C.1 第 7 问），各自一个 playbook 文件放在 `mmw-v2/skills/dispatch/playbooks/`。reviewer 与 advisor 仍是能力技能（`code-review`、`advisor`），它们的会话文件就是操作文件。
3. **角色 = 启动提示词里点名的「技能 + 角色名」+ `~/.mmw/models.json` 一行。** 不建 agent 定义文件，ADR 0015 保留。worker 的启动提示词改为点名 `dispatch` 技能的 worker 角色，不再点名 `implement`。
4. **脚本发给会话的每条消息都带一行固定的角色指针。** 这些消息包括 relay 的唤醒、`dispatch.sh resume`、watchdog 告警。指针只写技能、文件和锚点，不带规则，也不复述 tracker 已有的内容。它取代 ADR 0020 中「唤醒只带 `#<n> <event>`」的写法。原意（不复述票上数据）保留。
5. **重入点由脚本从事件算出，按步骤标题指向 playbook，一个 lint 核对锚点存在。** worker 已有 `verify-ticket.py --preflight` 的 `RESUME:` 行；orchestrator 的 `dispatch.sh status` 也打印一行同类的 `RESUME:`。两者都改为印步骤标题，不印编号（现状按编号引用，违反 `SKILL-SET-RULES.md` `### Vocabulary` 末条）。
6. **原则 7 条，是 `mmw` 技能目录下的文件，不做成技能。** 路径为 `mmw-v2/skills/mmw/principles/<slug>.md`。夜间 playbook 只在需要判断的步骤里括注点名，不设常驻索引。已有归宿的规则不再抽成原则，包括 `shared.md`、`CODING_STANDARDS.md`、`SKILL-SET-RULES.md` 里的规则。
7. **上游回原文按段分类处理。** 流程接线段回退，由 playbook 接上。改变能力本身的段保留，但要去掉 MMW 名词。MMW 文本已过半的技能（`implement`、`code-review`、`to-spec`、`to-tickets`）移出 subtree，subtree 里的副本恢复原文。上游技能的调用方式恢复为上游自己的设置。
8. **`SKILL-SET-RULES.md` 事实 7 的「MMW ships no router skill」废止**，改写为三句：路由有一个家（mode）；下一步有一个家（playbook，或 MMW 自有能力的交还行）；两者互相存在由 lint 核对。原来要防的两件事都保住：第二份副本漂移，某一跳没有下一步（#538）。
9. **冻结规则落到文件位置上。** 运行时读的一切（mode、playbook、原则、reference）都在已安装技能目录里。运行时从不读工作树里的 `mmw-v2/` 或 `docs/`。脚本与它引用的锚点在同一个提交里一起冻结。
10. **夜里不依赖任何未核实的宿主行为。** 包括 `disable-model-invocation` 在各宿主的语义、斜杠经 runner 投递、常驻提醒、压缩钩子。白天 mode 的触发率是全设计里最不确定的一环，列入第 16 节并给出实测办法。

---

## 1. 读了什么、怎么核对

- **全文读过：**
  - L7；N1、N3、N8、N9、N10、N11 全文；N4 第 5、8、9 节；N5 第 0、5、8、9 节。
  - `mmw-v2/skills/dispatch/SKILL.md`、`references/night.md`、`one-ticket.md`、`inside-a-ticket.md`。
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`code-review/SKILL.md`。
  - `mmw-v2/skills/{verify-ticket,ui-acceptance,design-pages,advisor}/SKILL.md`。
  - `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`、`mmw-v2/merge-notes/README.md`。
  - `mmw-v2/prompt/shared.md`、`mmw-v2/prompt/README.md`。
  - `docs/adr/0003`、`0006`、`0014`、`0015`。
  - 未安装的 `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 与 `PHASE-BOUNDARIES.md`。
  - pstack 快照 `docs/research/code-landing-refs/pstack/skills/poteto-mode/SKILL.md`、`playbooks/bug-fix.md`、`session-pickup.md`、`pause-safely.md`、`orchestrate.md` 前 30 行、`agents/poteto-agent.md`。
- **按需读过：**
  - `dispatch.sh` 第 100–112 行（`AUTONOMOUS`、`PRODUCT_RULES`），以及第 1741、1949、1967、2072 行的提示词拼装。
  - `verify-ticket.py` 的 `resume_at` 与 `run_preflight`（第 2148–2235 行）。
  - `relay.py` 的 `WAKES`（第 291–299 行）与 `wake_text`（第 385–389 行）。
  - `turn-guard.py` 头注释（第 1–70 行）与拦截消息（第 290–312 行）。
  - `tool-guard.py` 头注释与 `NO_QUESTION`（第 1–95 行）；`watchdog.py` 第 735、780 行。
  - `install.sh` 第 452–456 行；`code-review/references/session.md` `## 2`。
  - 上游的交接行：`grill-with-docs/SKILL.md`、`to-spec/SKILL.md` `## Next`、`wayfinder/SKILL.md` 第 126 行、`prototype/UI.md` `## Next`、`to-tickets/SKILL.md` `<issue-template>`。
  - 上游原版 `implement`（`git show 5b1a4c51:skills/engineering/implement/SKILL.md`）。
- **Memory：** 用 `nmem m show` 读了 `8ec53374`、`756fc056`、`ce037679`、`fe94802d`、`411750f5`、`f4c3d378` 全文。
- **没读：**
  - `dispatch.sh` 其余大部分；relay 与 watchdog 的实现体；各 runner 适配器的动词实现。
  - 各能力技能的 reference 全文，本设计不逐个归置它们。
  - N2、N6、N7 只按标题检索，没通读。
  - 凡依赖这些部分的结论都标了推断。

---

## 2. 设计立场：夜里什么必须成立

从原文归纳出夜里的五个事实。架构的每个决定都先对照它们：

| # | 夜里的事实 | 出处 | 对架构的要求 |
|---|---|---|---|
| F1 | 会话由脚本启动，第一条消息是 `dispatch.sh` 拼的提示词。worker 收到 `Use the implement skill to work ticket #<n>. …`，reviewer 收到 `Use the code-review skill to review ticket #<n> from base commit <base>. …`，axis subagent 收到同一句加 `, axis Standards`，advisor 收到 `Use the advisor skill.` 加简报 | `dispatch.sh` 第 1949、1967、2072 行；`code-review/references/session.md` `## 2` | 被提示词点名的东西必须在各宿主上模型可达 |
| F2 | 唤醒只带 `#<n> <event>`，收件人按角色定：worker 收 `reviewer.reported`、`reviewer.lost`、`worker.queued`；orchestrator 收 `ticket.passed`、`ticket.returned`、`ticket.refused`、`child.opened`、`worker.lost`、`relay.recovered` | `relay.py` `WAKES`、`wake_text`（docstring「nothing the tracker already says」） | 会话被压缩后，唤醒文字本身不指向任何技能（N10 B8，推断）；worker 走 `implement` 时不会被指到 `## On waking` 第 1 步「重跑被打断的命令」（N10 B9，已核实） |
| F3 | 重入点来自票上的事件：`--preflight` 打印 `RESUME: step 3 (…)`；orchestrator 靠 `night.md` 开头的事实表 | `verify-ticket.py` `resume_at`；`night.md` 第 13–22 行 | 脚本按**步骤编号**指向文本：`resume_at` 的 docstring 还指向已删除的段落；watchdog 告警指向已被掏空的 `### Exit codes of resume`（N1 9.1 第 1、2 条，已核实）；事实表缺「`spec.retroed` 已记录、用户尚未验收」一行（按表逐行读，已核实） |
| F4 | hook 与技能加载无关，独立生效：`tool-guard.py` 按工作目录名 `issue-<n>` 管 worker 与 reviewer；`turn-guard.py` 按 runner `self` 只管 orchestrator | 两个脚本的头注释 | 强制层不能依赖 mode 是否被加载。hook 的拒绝文字必须和它指向的文本说同一件事：`NO_QUESTION` 与 `implement` 第 23 行已经有出入（N11 contradictions 第 1 条，已核实原文） |
| F5 | 一次 watch 期间运行的是 `~/.mmw/installed-root` 记录的冻结版本；技能软链指向已安装的 checkout | 根 `AGENTS.md` `## Self-hosting boundary`、`## Gotchas` | 夜里读的每份文字都要在已安装的技能目录里。pstack 的「运行中从 trunk 重读组件」（L7 B.1 末行）不能照搬 |

**由此得出的夜间设计原则（本设计自用，不是要新建的「原则」组件）：** 入口越少越好；重入由脚本算、文本只写判断；指针只指向同一提交里的锚点；强制层只拒绝，不承担路由。

---

## 3. 总形态：各层在 MMW 里是什么、在哪

| pstack 层 | MMW 的实现 | 位置 | 谁到达它 |
|---|---|---|---|
| mode（常驻规则与路由） | 两个入口技能。流水线入口：`dispatch` 的 `SKILL.md`（角色表 + `## On waking` + 流水线常驻规则）。工具箱入口：`mmw` 的 `SKILL.md`（头部判断 + 路由表 + 原则索引） | `mmw-v2/skills/dispatch/SKILL.md`；新建 `mmw-v2/skills/mmw/SKILL.md` | 启动提示词、唤醒指针、description、用户斜杠 |
| playbook（步骤顺序） | 流水线 playbook：`night.md`、`worker.md`（由 `implement` 移来）、`one-ticket.md`。白天 playbook：从想法到发布的票；画地图；被退回的票；让一个仓库接入 MMW | `mmw-v2/skills/dispatch/playbooks/`；`mmw-v2/skills/mmw/playbooks/` | mode 的路由表或角色表；唤醒指针；其他 playbook 按文件名点名 |
| 能力技能（一步怎么做） | `verify-ticket`、`ui-acceptance`、`design-pages`、`write-screen-contract`、`code-review`（移出 subtree）、`to-spec`、`to-tickets`（移出 subtree）、`advisor`、`retro`、`exe-release`、`code-checkers`、`manage-agents-md`、`diagram-design`，以及回到原文的上游技能 | `mmw-v2/skills/<名>/`；`mmw-v2/upstream*/skills/…` | playbook 步骤按名点名；description；用户斜杠；启动提示词（`code-review`、`advisor`） |
| 原则（为什么、何时用） | 7 个文件 | `mmw-v2/skills/mmw/principles/<slug>.md` | playbook 与能力技能括注点名；`mmw` 的索引 |
| 脚本 | 不变：`dispatch.sh`、relay、watchdog、`verify-ticket.py`、oracle、`models.py` 等。新增两处：角色指针表；锚点 lint | 原位 | playbook 步骤写出命令 |
| 角色（agent 定义） | 启动提示词里的「技能 + 角色名」+ `models.json` 一行（`junior-worker`、`senior-worker`、`reviewer`、`advisor`）；orchestrator 没有行，由用户启动 | `dispatch.sh` `start_one`、`advise_one`；`~/.mmw/models.json` | `dispatch.sh start`、`advise` |
| 配置 | 不变：`~/.mmw/models.json`、`hosts.json` | 原位 | 脚本显式读，不靠注入 |
| 项目私有组件（L7 A.11） | 消费仓库的 `.mmw/`、`docs/specs/<effort>/screen-contract.yaml`、`prototypes/`、`docs/agents/*.md`、`AGENTS.md`/`CODING_STANDARDS.md`/`TESTING.md` | 消费仓库 | 能力技能与票的 `## Read first` |
| 强制层（pstack 没有） | `tool-guard.py`、`turn-guard.py` | `mmw-v2/skills/dispatch/scripts/` | 宿主的 hook |

---

## 4. Q1 调用模型

### 4.1 每种到达方式各到达哪些组件

沿用 N10 3.1 的八种机制（M1–M8），并写出新架构下每种机制的规则：

| 机制 | 新架构的规则 | 到达的组件 |
|---|---|---|
| M1 description 自动触发 | description 只写触发条件（保留 `SKILL-SET-RULES.md` `### Descriptions`）。能力技能的 description 不写流水线位置。以角色为触发（「when you were started as …」）的写法只留给被启动提示词点名的三个技能 | `mmw`、`dispatch`、MMW 自有能力技能、上游原文本来就模型可触发的技能（`tdd`、`prototype`、`grilling`、`domain-modeling`、`codebase-design`、`diagnosing-bugs`、`research`、`resolving-merge-conflicts`、`wizard`、`writing-for-agents`、`diagram-design`） |
| M2 用户斜杠 | 全部技能都能用。上游原文为用户触发的技能只能靠它 | 同上，另加 `grill-me`、`grill-with-docs`、`handoff`、`teach`、`wait-what`、`improve-codebase-architecture`、`setup-matt-pocock-skills`，以及恢复原文后的 `triage`、`wayfinder`、`to-questionnaire`（见 8.3） |
| M3 技能正文按名点名 | 方向规则照 L7 B.2：mode → playbook、能力、原则；playbook → 能力、原则、playbook（按文件名）；能力 → 能力（子任务）、原则；原则 → 原则、能力。**能力技能不点名 playbook，原则不点名 playbook。** 被夜间文本点名的技能必须模型可见（见 4.3） | 全部 |
| M4 启动提示词 | 只带「技能名 + 角色名 + 启动时已知的数据」，不带规则（保留 `### Prompts written for other agents`） | worker → `dispatch`（角色 worker）；reviewer → `code-review`；axis → `code-review` + axis；advisor → `advisor` |
| M5 事件唤醒与 `resume` | 文字 = `#<n> <event>` + 一行角色指针（新增，见 6.4）。每个唤醒事件在收件角色的 playbook 里只有一个处理行 | worker → `dispatch/playbooks/worker.md`；orchestrator → `night.md` 或 `one-ticket.md` |
| M6 技能内分派表 | 分两种：角色表与重入表放在 mode 与 playbook；能力内部的分支表留在能力里（见 8.1） | — |
| M7 hook 拒绝并改道 | 拒绝文字给事实和唯一出路（ADR 0008），所指锚点必须存在（lint）。hook 不负责路由 | worker、reviewer（`tool-guard`）；orchestrator（`turn-guard`） |
| M8 常驻提示 | `shared.md` 不放任何 MMW 路由（理由见 5.3）。是否往消费仓库的 `AGENTS.md` 加一行激活 mode，列入第 16 节，靠实测决定 | — |

### 4.2 五个宿主上的情况

本设计依赖的宿主事实，以及它们的出处：

| 事实 | Claude Code | Codex | Grok | Pi | Cursor | 出处 |
|---|---|---|---|---|---|---|
| 扫描技能目录 | `~/.claude/skills` | `~/.agents/skills` | 同 | 同 | 同 | ADR 0006（2026-08-26 用探针实测） |
| 技能内的相对路径文件（`references/…`，以及新的 `playbooks/…`、`principles/…`）能按「技能名 + 文件」读到 | 现有做法在用，例如 `implement` 读 `dispatch` 的 `references/inside-a-ticket.md` | 同 | 同 | 同 | 同 | `SKILL-SET-RULES.md` `### Paths and host neutrality`；现有文本到处在用。**不是新依赖** |
| 用户触发技能对模型不可见 | 已核实（N10 第 0、4 节，本会话的技能列表里没有那 7 个） | 未核实（按 `policy.allow_implicit_invocation`） | 未核实 | 未核实 | 未核实 | N10 第 11 节 |
| 用户级提示词 `shared.md` 常驻 | 是 | 是 | 是 | 是 | 否，只能在 app 里手贴 | ADR 0007；`mmw-v2/prompt/README.md` |
| 回合结束 hook 能不能拦住结束 | 能（exit 2） | 能 | 能 | 只能发一条 follow-up | 只能发 `followup_message` | `turn-guard.py` 头注释（2026-09-10 实测） |
| 提问工具有没有 hook 拦截 | 有 | 有 | 有 | 没有 | 没有 | `install.sh` 第 454–455 行 `QUESTION_TOOLS` 只列三家 |
| 仓库根 `AGENTS.md` 进每个会话 | 经 `CLAUDE.md` 的 `@AGENTS.md` | 是 | 是 | 是 | `manage-agents-md` 称是 | `manage-agents-md/SKILL.md` 第 8 行（「on every host」，本报告没有实测 Cursor）；ADR 0007 第 16–18 行 |

### 4.3 哪些模型可触发，哪些只被点名

- **夜里只依赖模型可见的技能与它们目录里的文件。** 这是唯一按「用户触发 / 模型触发」作区分的地方，理由是 F1：夜里没有人能打斜杠，而用户触发技能在 Claude Code 上对模型不可见（已核实）。因此下面这些技能必须保持模型可触发：
  - `dispatch`；
  - `code-review`（MMW 自有，启动提示词与 axis 提示词都点名它）；
  - `advisor`；
  - `verify-ticket`、`ui-acceptance`、`retro`；
  - 移出 subtree 后的 `to-spec`、`to-tickets`（夜里 closing pass 要读 `to-tickets` 的 `<issue-template>`、`to-spec` 的 `references/revising-a-spec.md`，见 `night.md` 第 98、141 行）；
  - `tdd`、`resolving-merge-conflicts`（worker playbook 点名它们）。
- **上游技能按上游自己的设置。** 上游写着 `disable-model-invocation: true` 的，MMW 不再翻转（见 8.3）。
- **`mmw`（工具箱 mode）模型可触发**，description 写头部触发条件；也可以用 `/mmw`。
- **playbook 与原则不是技能**，没有 frontmatter，不进任何宿主的技能列表，只被按「技能名 + 文件」点名。这与 pstack 一致（L7 A.2 布局、A.4 的原则虽是技能但全部 `disable-model-invocation: true`，只被点名）。好处是系统提示里不多出 7 条原则和 7 份 playbook 的 description。

### 4.4 mode 怎样被加载（MMW 没有 `mode: true` 与 `reminder:`）

| 会话 | 怎样进 mode | 依据 |
|---|---|---|
| worker | 启动提示词点名 `dispatch` 与角色 → 读 `SKILL.md` 角色表 → `playbooks/worker.md`。唤醒、`resume`、压缩之后，靠消息里的角色指针回到同一处 | F1、F2；6.4 |
| reviewer、axis、advisor | 启动提示词直接点名能力技能，不经过 mode。它们是一次性会话：不会被唤醒，也不会重入（reviewer 按 `session.md` `## 2`「Hold this turn」一直占着回合；丢失时由 worker 另起一个） | `session.md` `## 2`；`implement` 第 3 步 |
| orchestrator | 用户说「今晚跑 spec #N」→ `dispatch` 的 description 或 `/dispatch` → 角色表 → `night.md`。之后每次唤醒、每条 watchdog 告警、每次压缩，都靠消息里的角色指针回到 `night.md` 的 `## Find where you are` | F2、F3 |
| 白天有人在的会话 | `mmw` 的 description 或 `/mmw`；或直接斜杠某个能力技能（实际使用以这种为主：`/wayfinder` 22 次，N10 第 7 节实测，本报告没有复核） | N10 第 7 节 |

pstack 的 `reminder` 管的是「新任务时重新套用 mode」（L7 E.2）。夜里不需要它，因为每条到达会话的消息都自带指针。白天没有等价物，这是本设计最弱的一环：同样是模型可触发的路由，ask-matt 在 Claude 会话里被调用 0 次（N10 第 7 节，已核实）。办法与实测见第 16 节 U1。

### 4.5 不依赖的宿主行为、必须实测的宿主行为

**夜间部分不依赖：**

1. 任何宿主上 `disable-model-invocation` 的语义；
2. runner 把斜杠（`/implement`）投进会话后会不会被当成技能调用（N10 第 11 节，未核实）。启动提示词继续用散文「Use the X skill」；
3. `mode: true`、`reminder:`、`alwaysApply` 这类常驻注入；
4. 宿主的压缩钩子（SessionStart / PreCompact 一类）；
5. 读一个用户触发技能目录里的文件；
6. hook 用于路由。hook 只拒绝，而且它的判定只看工作目录名或 `self`，与技能加载无关（F4）。

**夜间部分仍然依赖、但今天已经在用的（不是新增依赖）：**

- 模型能加载一个用散文点名的模型可触发技能；
- 能按「技能名 + 相对路径」读该技能目录里的文件；
- runner 的 `send` 能把文字送进活着的会话；
- 宿主在启动时扫描 description。

**必须实测才能定的（列入第 16 节）：**

- U1：白天 mode 的触发率，以及消费仓库 `AGENTS.md` 里一行激活句是否有效。
- U2：压缩后，只凭「唤醒 + 角色指针」能否回到正确的步骤。
- U3：恢复为用户触发的上游技能，在 Codex、Grok、Pi、Cursor 上对 mode 是否可见。只影响白天。

### 4.6 放弃的备选

| 备选（N10 10.4） | 放弃的理由 |
|---|---|
| A 维持现状 | 头部缺口 B1、B3、B5 没有家；上游文本继续承载 MMW 流程，与 `8ec53374` 方向相反；夜里 F2、F3 的断点照旧 |
| B pstack 式「只被点名」：一个 mode，其余全部 `disable-model-invocation` | 夜里依赖未核实的宿主行为：用户触发技能在 Claude Code 上对模型不可见，而 reviewer 与 axis 的提示词点名 `code-review`（F1）。它还需要常驻机制，而 `shared.md` 到不了 Cursor、按回合付费（ADR 0014 `## Considered Options` 第 2 条） |
| C 单一 mode 模型可触发、能力技能保留触发 | 夜里每次重入都要读白天的头部路由；`dispatch` 的脚本与处理动作本是一个整体，被拆到两个技能目录 |
| D 按「谁启动会话」分层，只给人启动的头部加 mode | **本设计是 D 的加强版**：D 不动夜间链路；本设计同时把 worker 的文本移出上游，并加固重入（指针、标题锚点、lint）。D 本身没有解决 F2、F3 |
| E 不加路由，把缺口补进现有技能 | 继续往上游文本写 MMW 流程（`411750f5` 第 3 条、`8ec53374`） |
| 新增：每个 playbook 做成一个模型可触发技能（例如 `mmw-worker`） | 30 份左右的 description 进系统提示，彼此抢触发；正是 L7 C.6 信号 11（把任务流程做成能力技能） |
| 新增：用宿主的压缩钩子重新注入角色 | 只在部分宿主上有，属于未核实的宿主行为；把指针放进消息本身在五个宿主上都成立 |

---

## 5. Q2 mode

### 5.1 数量：两个

| mode | 装什么 | 不装什么 | 为什么独立 |
|---|---|---|---|
| **流水线入口 `dispatch`**（现有技能，保留名字） | ① 角色表（worker、自己接手的票并入 worker 行、orchestrator、单票、改模型、开任务板），按「你的提示词或消息怎么说你」匹配；② `## On waking` 四步（原样，三个 playbook 共用）；③ 流水线常驻规则，只收三个角色都要守的：位置由票上事件定、等待就结束回合（指向原则 `state-on-the-ticket`，不复述）；「Where you are is what the ticket's events say」一句保留 | 原则索引、白天路由、任何一个角色的步骤 | 夜里每次重入都会读到它，所以必须薄；它与 `dispatch.sh`、relay、`WAKES` 是同一个天然整体（N10 第 9 节；N1 第 8 节「`## On waking` 四步」「relay + watchdog + turn guard + statedir」） |
| **工具箱入口 `mmw`**（新建） | ① 头部判断（见 5.2）；② 路由表：到达情形 → 白天 playbook 或能力技能；遇到 spec、票或夜时交给 `dispatch`；③ 原则索引（7 行，每行写「名字 · 何时适用 · 一句要点」，照 pstack mode `## Principles` 的写法）；④ 用户触发技能的点名方式：「告诉用户打 `/X`」 | `shared.md` 已经常驻的规则（汇报写法、自主权边界、证据），见 5.3；任何夜间内容 | 只在有人的会话里读；改它不碰夜间链路 |

**为什么不合成一个 mode：**

- 合并后，每次夜间重入都要读白天的头部路由。
- 把 `## On waking` 与 `WAKES` 的处理行拆到另一个技能目录，会让「改 relay 的唤醒表」变成改两个技能。这与目的「修改只动一处」相反。
- 两个入口之间只有一个交接点：票已经发布（`to-tickets` 第 8 步交给 `dispatch`）。这个交接点今天就存在。

**为什么不给 reviewer 和 advisor 各加一个 mode：** 它们单一入口、单一任务、不重入（L7 C.1 第 7 问），能力技能自己的会话文件已经是操作文件。

### 5.2 头部判断放哪里（N10 B1–B5，与未安装的 ask-matt）

| 头部判断 | 现在 | 新家 | 收益类别 |
|---|---|---|---|
| B1 「在工作目录里有个想法，想把它做出来」没有模型可达的入口 | 无；ask-matt 的 description 曾覆盖，已删 | `mmw` 的 description 与路由表第一行 → 白天 playbook「从想法到发布的票」 | 给无处安放的内容一个家 |
| B2 直接走 `grilling` 之后没有下一步 | 只有 `grill-with-docs` 的末句点名 `to-spec` | 该 playbook 的第一步：「一起运行 `grilling` 与 `domain-modeling` 两个技能」（这正是 `/grill-with-docs` 做的，两个都模型可触发）；下一步由 playbook 点名 | 把 MMW 流程从上游文本移走；消除断点 |
| B3 走 spec 流水线还是直接 `tdd`；谁来检查 | 只在未安装的 ask-matt 主流程第 3 步：「In this repository the branch also decides who checks the work … Take **No** only for a change small enough that the user will check it directly」 | `mmw` 的一行闸门：Yes → 进 playbook；No → `tdd`，并告诉用户由他本人检查、没有验收脚本、没有 reviewer | 给无处安放的内容一个家 |
| B4 `prototype` 的 LOGIC 与 EXP 分支没有下一步 | 只有 `UI.md` 有 `## Next` | 由该 playbook 的原型步骤统一接回：「原型的结论回到本 playbook 的 spec 步骤」；上游 `UI.md` `## Next` 回退 | 同上 |
| B5 阶段边界（Continue、Clear、Handoff、Subagent、Compact） | 只在 ask-matt 的 `PHASE-BOUNDARIES.md` | 原则 `phase-boundary`（7.4），`mmw` 索引点名 | 给无处安放的内容一个家 |
| 上下文卫生：在 `to-tickets` 跑完之前不要清空或压缩 | ask-matt `### Context hygiene` | 「从想法到发布的票」playbook 的首段，作为这个 playbook 的纪律 | 同上 |

**ask-matt 本身怎么处理：** 不装，残留目录恢复上游原文。它的路由（主流程终点是 `implement`）与 MMW 的流程相反，所以不能原样装；需要的三块内容已按上表安置。这样也解决了 N10 B10：残留目录带着本仓改动，却没有 merge-note。

### 5.3 与用户级提示 `mmw-v2/prompt/shared.md` 的分工

- **`shared.md` 的范围：** 它是所有项目、四个宿主每一回合的常驻提示，读者设定是 owner。它管两件事：怎样对 owner 汇报；工程上的一般纪律，例如 rule 14 先找现成、rule 15 不跑全量测试。它不点名任何技能，第 11 行把无人会话的提问与汇报交给「its skills」。
- **mode 的范围：** MMW 专属的路由与规则，按需载入。
- **三条分工规则：**
  1. **mode 不复述 `shared.md`。** pstack mode 的 `## Autonomy`、`## Writing the reply` 在内容上与 `shared.md` rule 1–5 重叠（N8 9.2 第 5 条），MMW 不把它们搬进 mode：它们已有常驻的家，搬过去就是第二份副本。
  2. **`shared.md` 不放 MMW 路由。** 理由与 ADR 0014 否决把 caller 侧规则写进用户级提示词相同：到不了 Cursor；为一件局部的事付每回合的常驻成本。另外，`shared.md` 是 owner 在所有项目上的提示，MMW 路由只在接入 MMW 的仓库有意义。
  3. **`shared.md` 第 11 行保留。** 它假定存在一个比它更具体的层来承接「怎么问、怎么报」（N8 9.2 第 3 条）。新架构里这个层就是 mode、playbook 和启动提示词。
- **一处重复，定下唯一的家：**
  - 同一句「不在屏幕上提问」现在有三个载体：`AUTONOMOUS` 常量进每个 worker 与 reviewer 的启动提示词，`implement` 第 23 行，`tool-guard.py` `NO_QUESTION`。其中 `NO_QUESTION` 与 `implement` 给的出路不同（F4）。
  - 新架构的分工：
    - 禁令的唯一载体是启动提示词里的 `AUTONOMOUS`。它进每个宿主，也包括收不到 `shared.md` 的 Cursor。
    - 出路（写进 `Decisions I made on my own`，或开 `decision` 子票）只在 worker playbook 写一次。
    - `NO_QUESTION` 只给角色中立的出路，并点名 worker playbook 的那一步标题。它必须角色中立，因为 `tool-guard` 按目录分不出 worker 与 reviewer（F4）。
  - 收益：消除一处已核实的冲突。

---

## 6. Q3 playbook

### 6.1 放在哪里

| 目录 | 放什么 | 理由 |
|---|---|---|
| `mmw-v2/skills/dispatch/playbooks/` | `night.md`（现 `references/night.md`）、`worker.md`（由 `implement` 正文移来，吸收 `inside-a-ticket.md`）、`one-ticket.md` | 与 `dispatch.sh`、`WAKES`、`## On waking` 同在一个技能目录，一起冻结、一起测（`mmw-v2/tests/dispatch/`） |
| `mmw-v2/skills/dispatch/references/` | 只留分支材料：`editing-models.md`，以及随 worker 移来的 `writing-interface-code.md`、`saving-memory.md` | 照 L7 A.5：只在某个分支读的内容进 reference |
| `mmw-v2/skills/mmw/playbooks/` | 白天：`idea-to-tickets.md`（从想法到发布的票）；`charting-a-map.md`（吸收 wayfinder 的 `mmw:map` label、`## Notes` 里写 effort 目录名、`interface-and-remake.md` 两支、「地图清空后新会话跑 `to-spec`」）；`handed-back-tickets.md`（吸收 triage 的 `references/pipeline-issues.md`）；`adopting-mmw.md`（吸收 `setup-matt-pocock-skills` 的 MMW 部分，按顺序接 `manage-agents-md` 与 `ui-acceptance` 的 `target_config.py --check`） | 每个都有自己的门槛与交付物（L7 C.6 信号 5），而且每个都让一份上游文本回到原文 |

`references/` 改名 `playbooks/` 的收益：playbook 格式（所有权行、标题锚点、`Done when`）可以只对这个目录跑 lint（6.5），reference 不受这套格式约束。这属于「消除一处已核实的断点」，对应 F3 的失效锚点。没有收益的改名不做，见第 13 节。

### 6.2 格式：pstack 骨架加 MMW 的调整

```
# <任务类型名>

**You own <对象>. <动词>, <动词>.**            ← 所有权行（pstack 原样）
Entered by: <启动提示词里的角色 | 唤醒 | 用户 | mode 某一行>.   ← MMW 加：夜里的入口各不相同，写出来

<可选首段：本类任务的纪律、与相邻 playbook 的界线>

## Find where you are                          ← 只在可重入的 playbook 里有
<脚本打出的那一行（RESUME: / status 首行）是答案；表只解释它的取值>

## Steps
1. **<稳定标题>.** <一句可执行的动作>. <门槛、例外、理由>. (principle: <slug>)
   Done when <票上的事件或脚本的退出码>.      ← MMW 保留的完成判据写法
2. …

## <规则簇>                                     ← pstack orchestrate 的 #### 写法，不进步骤
（例：While a worker holds a ticket；Authority order for a contract child）

**Leaves:** <下一个读者在哪里读到什么>          ← 无人值守的 playbook 用它
**Reply:** <本 playbook 独有的回复内容>          ← 只在有人读回复的白天 playbook 用
```

与 pstack 的差异，逐条给理由：

| 调整 | 理由 |
|---|---|
| 步骤用**稳定标题**当锚点，不用编号当锚点 | 脚本要指向步骤（`RESUME:`、watchdog 告警）。按编号引用是 pstack 最脆的连线（L7 E.1 第 2 条），MMW 已经为此出错（F3）。`SKILL-SET-RULES.md` `### Vocabulary` 末条本来就要求「by title rather than by number」 |
| 每步写 `Done when` | 夜里没有人看回复，完成只能由票上事件或退出码判定；MMW 已有此规则（`### Rules and completion criteria`） |
| 无人值守的 playbook 写 `**Leaves:**`，不写 `**Reply:**` | 读 orchestrator 与 worker 产物的是早上冷读的用户和下一个会话（`night.md` 第 5 段），所以写明留在哪里、给谁 |
| `Entered by:` 行 | 同一文件会被三种方式进入（首次启动、唤醒、`resume`）。写明入口，读者才能核对自己是怎么来的 |
| 不采用 pstack 的「把步骤原样抄进 todo、跳过的写 `skip:`」协议 | 夜里的步骤由脚本把关：`--closeout` 核对草稿，`summary` 拒绝仍有未路由 finding 的夜，`finish` 要 `spec.retroed`。再加 todo 协议不会改变任何决定（L7 C.6 信号 2、4） |

### 6.3 脚本启动的会话怎样直接进入指定 playbook

启动提示词格式（示例；具体措辞在实现时定）：

```
Use the dispatch skill as the worker on ticket #<n>. <AUTONOMOUS> <PRODUCT_RULES>
<Memory 索引（数据，原样）>
```

- `dispatch` 的 `SKILL.md` 角色表第一行匹配「your prompt names you the worker on a ticket」→ `playbooks/worker.md`。
- reviewer、axis、advisor 的提示词不变，仍直接点名能力技能。
- 自己接手票的会话（没有 `start` 在背后）由 `dispatch` 的 description「work a published ticket as its worker」进入同一行，`worker.md` 的第一步（`adopt`）只在「没有 `start` 在背后」时执行。
- **「角色 = playbook + `models.json` 一行」的落地：**

  | 角色 | `models.json` 行 | 入口 |
  |---|---|---|
  | worker | `junior-worker`、`senior-worker` | `dispatch` 的 worker 行 → `worker.md` |
  | reviewer | `reviewer` | `code-review` 的会话文件 |
  | advisor | `advisor` | `advisor` 的 advising 文件 |

  没有 agent 定义文件。pstack 需要 `poteto-agent` 的两个理由（L7 A.7：全新上下文；保证先读 mode），在 MMW 里分别由「runner 起一个新会话」和「启动提示词点名入口」满足。ADR 0015 保留。

### 6.4 被事件唤醒、被压缩后怎样从中间重入

**三件套：**

1. **消息里的角色指针（新增）。**
   - 所有由脚本送进会话的文字，末尾追加一行按收件角色固定的指针，例如：
     - worker：`Worker on #<n>: the dispatch skill's playbooks/worker.md, "Find where you are".`
     - orchestrator：`Orchestrator of spec #<s>: the dispatch skill's playbooks/night.md, "Find where you are".`
   - 这些文字包括 relay 的唤醒（`wake_text`）、`dispatch.sh resume` 的消息、watchdog 告警。
   - 角色到指针的对应表只放在一处，三个发送方都从它取。relay 从 `WAKES` 的 `to` 与 watch 已知道收件角色，所以不需要新数据。
   - **不带规则，不带 tracker 数据。** `wake_text` 的原意「nothing the tracker already says」保留；ADR 0020 的「只带 `#<n> <event>`」改写（9.3）。
   - 收益：消除已核实的断点 B9（worker 没有被指到 `## On waking` 第 1 步），也消除推断的断点 B8（orchestrator 压缩后唤醒文字不指向任何技能）。
2. **脚本算出的重入行。**
   - worker：现有 `--preflight` 的 `RESUME:` 行，改为印步骤标题。它的 docstring 还指向已删除的段落（F3），一并修。
   - orchestrator：`dispatch.sh status <spec>` 的第一行印同类的 `RESUME: <section title>`，从 `spec.opened`、`spec.suspended`、`spec.closed`、`spec.retroed` 与 frontier 算出。`night.md` 的事实表改为解释这一行的取值，不再让模型自己核对四种事件。
   - 收益：
     - 「在哪」的判定是确定性的，按 `SKILL-SET-RULES.md` 事实 2 应由脚本做；
     - 顺带补上事实表缺的那一行：`spec.retroed` 已记录、用户尚未验收（F3）。
   - 「用户已验收」不在事件里。脚本对这种情况印「recorded; waiting for the user's acceptance」，由会话自己判断用户是否已经说了。
3. **`## On waking` 四步（原样）。** 它留在 `dispatch` 的 `SKILL.md`。三个 playbook 的 `Find where you are` 都以「先做 `## On waking` 第 1–3 步」开头，不复述。

**被压缩后的具体路径（推断，需 U2 实测）：**

1. 被压缩的会话收到下一条消息。
2. 消息里的指针点名技能与文件。
3. 会话读 `dispatch/SKILL.md` 的 `## On waking` 与 playbook 的 `Find where you are`。
4. 跑 `--preflight` 或 `status` 拿到 `RESUME:`，在该标题处继续。

全过程不依赖会话记忆，这正是原则 `state-on-the-ticket`（PC5）。

**pstack 的 `session-pickup` 与 `pause-safely`（L7 D.2）：**

- 夜里不需要。暂停已有 `dispatch.sh suspend`；未提交的改动由 `start` 做成 `wip(#<n>)` 提交保存（`implement` 第 14 行）；接手由 `RESUME:` 完成。
- 白天有人在的会话，暂停与接手的判断归原则 `phase-boundary`，不另建 playbook（L7 C.6 信号 1）。

### 6.5 让脚本与文本不漂移：锚点 lint

在 `mmw-v2/tests/lib/` 加一个检查，与现有 `check_module_paths.py` 同层、由每个套件的 `run.sh` 先跑。它查五件事：

- 脚本印出的每个步骤标题，都作为 `**<标题>.**` 或 `## <标题>` 出现在所指的 playbook 里。涉及 `resume_at`、`status` 的 `RESUME:`、watchdog 告警里的节名、hook 拒绝文字里的节名。做法照 L7 A.6：字面检查器必须持有被匹配的原文（`check-plan.mjs` 的 `RULE`）；脚本从一个锚点常量模块取标题，测试断言每个常量在 playbook 里逐字出现。
- `WAKES` 的每个事件，在收件角色的 playbook 里恰好有一个处理行。这把 `SKILL-SET-RULES.md` `### Hand-offs`「Each event gets one instruction」变成检查。
- 两个 mode 的路由表点名的每个 playbook 文件都存在，每个 playbook 文件都至少被一个 mode 或 playbook 点名。这就是 Memory `ce037679` 要的「一张与实际同步的总图」，由机器保证同步。
- 角色指针表里的每个文件与锚点都存在。
- `night.md` 事实表里列出的每种消息（例如 `MMW turn guard:`）在 `## 3` 里都有处理行。现状 `night.md` 第 19 行把 `MMW turn guard:` 路由到 `## 3`，而 `## 3` 没有这一行（N11 missing_edges 第 1 条，已核实）。

冻结的安全性：脚本与它引用的锚点在同一个提交里，一起装进 installed checkout，一起冻结。lint 保证它们在这个提交里彼此一致。

### 6.6 L7 C.1 第 7 问：benny 式单一操作文件适用于谁

| 会话 | 单一入口？ | 单一任务类型？ | 结论 |
|---|---|---|---|
| worker | 是（启动提示词或 `adopt`） | 是（做一张票） | **适用。** `worker.md` 一个文件：按名点名共用能力（`tdd`、`resolving-merge-conflicts`、`verify-ticket`、`ui-acceptance`）与原则，不拆出 playbook 加能力技能两层。它的写码规则七条、收尾八步、`ABANDON` 三种都留在文件里（N3 第 8 节第 1、2 条的天然整体；L7 C.2「绑定具体机制」、C.4「只有一个调用方」） |
| reviewer | 是 | 是 | **适用。** 现状 `code-review` 的 `references/session.md` 就是操作文件；axis 文件是它派出的子代理读的 reference（L7 A.5 第一行：要转交给子代理的提示材料） |
| orchestrator（夜） | 是（用户开夜） | 是（跑一夜） | **适用。** `night.md` 一个文件；closing pass、Memory 收口、`reverify`/`summary`/retro、`finish` 不拆成能力技能：只有一个调用方，彼此有收据依赖（N1 第 8 节） |
| orchestrator（单票） | 是（`open-ticket`） | 是 | 适用，另一个文件。它按标题引用 `night.md` `## 3` 的处理行，不复制 |

这些操作文件之所以还要一个很薄的共同入口（`dispatch` 的 `SKILL.md`），唯一原因是 `## On waking` 被三个文件共用（「让一段内容能被两个以上 playbook 复用」）。不是为了在任务类型之间路由。

---

## 7. Q4 原则

### 7.1 存放形式与命名

| 选项 | 结论 | 理由 |
|---|---|---|
| pstack 式：每条一个技能 `principle-<slug>` | 否 | 做成用户触发：在 Claude Code 上对模型不可见，夜里点名会落空（F1）。做成模型可触发：每个项目每个会话的系统提示多 7 条 description，而原则不该被 description 触发（pstack 自己也全部关掉了自动触发，L7 A.4） |
| `mmw` 技能目录下的文件 `principles/<slug>.md` | **采用** | 五个宿主都按「技能名 + 文件」读得到（已有做法）；不进系统提示；随技能冻结 |
| 写进 `shared.md` | 否 | 到不了 Cursor，按回合付费（ADR 0014）；而且 `shared.md` 面向所有项目 |
| 写进 `CONTEXT.md` 词表 | 否 | 词表不是规则的家（`CONTEXT-MAP.md` 第 5 行；`SKILL-SET-RULES.md` `### Load and disclosure`「A rule … in the glossary … reaches no worker」） |

- **命名：** 英文短 slug，就是原则的短名，照 pstack（L7 A.4 门槛第一条：能用短名字说出口）。
- **文件格式：** 照 pstack 的高频形态：`# 标题`、一到三句规则、`**Why:**`（写本领域出过的事或用户的决定）、`**Pattern:**`、`**Boundaries:**`。`**Boundaries:**` 写明调用方的领域规则优先于原则的哪些地方（L7 C.2「调用方可以限定原则的范围」）。没有 frontmatter。

### 7.2 怎样被引用、怎样避免常驻上下文膨胀

- **夜间 playbook：** 步骤里保留本领域的具体规则，句末括注 `(principle: <slug>)`。只有当眼前的情形不在规则覆盖内时，才去读原则全文。依据是 L7 C.2 第一行：规则绑定具体机制时留在调用方，原则写方向；以及 `SKILL-SET-RULES.md`「A rule sits in the text of the agent that must follow it」。好处是夜里正常路径一份原则都不必读，文件读不到也不影响那一步。
- **`mmw` 的索引：** 7 行，白天每个任务读一次。
- **能力技能：** 可以括注点名原则（L7 B.2：能力 → 原则是常规方向）。
- **不采用** pstack 的「回复里写出每条改变了决定的原则，只引用本会话读过全文的」（mode `## Non-negotiables`）。夜里没有面向人的回复；白天的回复规矩已由 `shared.md` 管。

### 7.3 够格的门槛

L7 A.4 的四条，加 C.2 的「不拆」条件，加 MMW 的两条：

1. 能用一个短名字说出口；
2. 有可观察的触发情境；
3. 能改变一个具体决定；
4. 跨任务：至少两个 playbook 或能力技能，而且各自是不同的机制；
5. （C.2）规则没有绑定到只属于一个调用方的具体机制；读者读得到原则文件，读不到就在调用方复述；
6. （MMW）它的唯一读者群没有已经存在的家：写脚本的人读 `CODING_STANDARDS.md`，写技能的人读 `SKILL-SET-RULES.md`，所有会话读 `shared.md`；
7. （MMW）理由有依据：一次记录在案的运行，或用户的决定（`SKILL-SET-RULES.md` `## Editing` 第 1 条：凭空编的理由会被模型推广）。

### 7.4 采用的 7 条（候选来自 N9 第 9 节，已回原文核对其出处行）

| slug | 规则（一句） | 合并了 N9 哪几条 | 依据 | 主要引用处 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 一道检查、一次交付不能因为什么都没做而读起来像通过；检查要证明自己能失败；查不了就说查不了 | PC1、PC2 | ADR 0008；`implement` 第 22 行自带的理由（「a false `ALL MET` lands broken behaviour under a green mark」） | worker 收尾；`to-tickets` 写判据；oracle；`code-checkers`；retro |
| `rerun-dont-reroute` | 命令被打断就原样重跑，命令本来可以重跑；被拒绝或撞上流水线故障，就修拒绝点名的事或报 blocked，不绕路、不写重试循环、不换 host 或 runner | PC17、PC18 | ADR 0010、0017、0018（用户 2026-09-10 否决重试与换 host）；`ui-acceptance` Five rules 第 4、5 条；`refusal.py` 头注释记的 2026-09-05 事故 | `## On waking` 第 1 步；`night.md` `## 2` exit 4；worker 的 fault 步骤 |
| `state-on-the-ticket` | 你在哪由票上的事件决定，不由会话记忆决定；要等别人就结束回合，由事件叫醒，不轮询 | PC4、PC5 | ADR 0010、0019、0020；`dispatch/SKILL.md` 第 8 行原句 | 三个流水线 playbook 的 `Find where you are`；`exe-release` 续跑 |
| `baseline-is-a-contract` | 已定的结论照抄，不重写；不成立时开 `contract` 子票，让决定者看得见，不悄悄改也不绕开 | PC8 | `implement` 第 22 行自带的理由；ADR 0029 | worker；`night.md` 的 contract 处理；`design-pages` pull；triage |
| `one-writer-per-file` | 同一时刻一个文件只有一个写者：能并行的票不写同一个文件；共享入口要么归一张票，要么加 `Blocked by` | PC12 | `implement` 第 28 行理由；`to-tickets` 第 107 行；ADR 0012 第 1 步 | `to-tickets` 切票；worker 改 `## Owns` 以外的文件；closing pass |
| `clues-are-not-evidence` | Memory、reviewer Rule、别票的通过结论、简报、相似的标题，只决定去看什么；结论要当前的一手来源 | PC11 | `implement` 第 48–49 行；`code-review` 的 `session.md` 第 101 行；`spec-reviewer.md` 第 22 行；retro | worker；reviewer；retro；advisor |
| `phase-boundary` | 在两段工作之间，按顺序问五个问题：先排除 Continue，Compact 是兜底 | ask-matt 的 `PHASE-BOUNDARIES.md`（上游原文，N10 B5） | 上游原文；用于没有别的家的 B5 | `mmw` 的索引；白天 playbook 的衔接点 |

`phase-boundary` 的正文取上游原文，注明出处，并记入 10.2 所说的外来清单。理由：ask-matt 整体不装（5.2），这份文件在 MMW 里没有别的家；`SKILL-SET-RULES.md` `## Editing` 要求「Text taken from another source keeps its authors' wording」。

**不做成原则的候选（均有依据）：**

| 候选 | 为什么不做 |
|---|---|
| PC9 用户只决定产品事项；PC10 写给冷读的读者；PC13 文件只写现状；PC14 最小测试集并引用看到的那一行 | 已经住在 `shared.md` rule 1、2、10、13、4、15，常驻四个宿主；再写一份就是第二份副本（门槛 6） |
| PC3 拒绝三段式 | 唯一读者是写脚本的人，家在 `CODING_STANDARDS.md` 与 `refusal.py` |
| PC6 协议状态只由脚本写 | 由 `tool-guard.py` 与脚本强制，属于机制（L7 C.1 第 2 问；C.6 信号 4） |
| PC7 确定性交给脚本；PC16 一个家 | 唯一读者是写技能的人，家在 `SKILL-SET-RULES.md` 事实 2、7 |
| PC15 只读靠文字自守 | 只在 `advisor` 与 `code-review` 两处，是同一个宿主限制的两个实例，不是跨任务的判断 |

---

## 8. Q5 能力技能与 playbook 的分界

### 8.1 各「Find your moment」表的分行判定

判据：一行如果把读者送去**另一个技能的步骤**，或者说的是「在流程的这一刻来这里」，就是任务顺序，归 playbook 或 mode。一行如果按**本能力的输入或产物**选本技能自己的材料，就是能力内部，留在原处（L7 C.3）。

| 技能 · 行 | 内容 | 判定 | 去向 |
|---|---|---|---|
| `dispatch` 第 1 行 | worker → 「No file: the `implement` skill's `## Closing steps`」 | 任务顺序（角色入口） | 角色表 worker 行 → `playbooks/worker.md` |
| `dispatch` 第 2 行 | 自己接手的票 → `inside-a-ticket.md` | 任务顺序（worker 入口的一个分支） | 并入 `worker.md` 第一步 |
| `dispatch` 第 3、4 行 | orchestrator → `night.md`；单票 → `one-ticket.md` | 任务顺序（角色入口） | 角色表 → `playbooks/` |
| `dispatch` 第 5、6 行 | 改模型 → `editing-models.md`；开任务板 → 一条命令 | 能力（对脚本与配置的操作） | 留作 mode 里指向能力的行（pstack mode 也路由到技能，L7 A.1） |
| `dispatch` description「Start a reviewer from inside a ticket」 | 为了让 worker 找到 `dispatch.sh` 而写的触发 | 任务顺序漏进了 description（N10 B7 第 2 处） | 删去；worker 本来就在 `dispatch` 里 |
| `verify-ticket` 第 16 行「A worker's claim, criteria runs and closeout are steps of the `implement` skill」 | 把读者送回另一个技能 | 任务顺序（B7 第 3 处） | 删去；由 worker playbook 点名 `verify-ticket.py` 的各个命令 |
| `verify-ticket` 表：`sub-issues.md`、`linting.md`；`## Reached from here` → `ui-acceptance` | 按本能力的用途分支；硬依赖 | 能力内部 | 留 |
| `ui-acceptance` 第 1 行：写页面票代码之前 → `implement` 的 `writing-interface-code.md` | 另一个技能的步骤 | 任务顺序（B7 第 1 处） | 删去，description 里的「before writing a page ticket's code」也删去；由 worker playbook 在「读入」那一步点名（随 worker 移入 `dispatch/references/`） |
| `ui-acceptance` 第 3 行：往票上写判据 → `to-tickets` 的 `cutting-interface-tickets.md` | 另一个技能的材料 | 任务顺序 | 删去；`to-tickets` 自己点名它 |
| `ui-acceptance` 第 2、4–9 行；`## Five rules while the product is running` | story 服务、DIFF、boundary test、journey、`target.json`、harness、lease | 能力内部 | 留；Five rules 仍由 `PRODUCT_RULES` 指针送到 |
| `design-pages` 四行（edit-pages、draw、pull、design-system） | 同一能力的四个子任务 | 能力内部 | 留；`pull.md` 中「当 pull 回答一个 `contract` 子票」一段按输入分支，也留 |
| `design-pages` `edit-pages.md` `## Next`、`pull.md` `## Reached from here`；`write-screen-contract` `## Next` | MMW 自有能力的交还行，点名下一个能力 | 能力 → 能力（L7 B.2 常规方向） | **不动**（第 13 节） |
| `code-review` 两行（会话 / axis） | 本能力怎样执行 | 能力内部（L7 C.3） | 留 |
| `advisor` 两行（consulting / advising） | 同上 | 能力内部 | 留 |
| `night.md` 事实表 | playbook 自己的重入表 | playbook | 留在 playbook，改为解释 `RESUME:`（6.4） |

### 8.2 上游回原文的规则

**按段分类，不按技能整体分类。** 每个改过的段落，按下表归入一类：

| 类别 | 例子（出处 N3 第 5 节、N4 第 5 节、N5 5.2、N10 第 6 节） | 处理 |
|---|---|---|
| a. 宿主中立的措辞：`the Skill tool` 或斜杠改成散文点名 | `grill-me`、`handoff`、`tdd` 第 26 行、`wayfinder` 若干处 | **保留**，照 merge-note。这改变了其他四个宿主上的行为：「the Skill tool」只在一个宿主上存在（`merge-notes/README.md` `## host 中立`） |
| b. 调用方式翻转、description 补的触发句 | `triage`、`wayfinder`、`to-questionnaire` 删 `disable-model-invocation`；各处 description 末句 | **回退**到上游设置；MMW 的可达性由 mode 与 playbook 提供（8.3） |
| c. 点名 MMW 下一步的交接行 | `grill-with-docs` 末句「name the `to-spec` skill …」；`wayfinder` 第 6 步；`prototype` `UI.md` `## Next`；`improve-codebase-architecture` `### 4.` | **回退**；由白天 playbook 点名 |
| d. MMW 的存放位置、label、被脚本解析的格式 | `prototype` 规则 1 的 `prototypes/<effort>/<issue>/…`、`UI.md` 第 6 步的 `## State list`（`pull_design.py` 解析）；`wayfinder` 的 `mmw:map`；`setup-matt-pocock-skills` 的 label 三套 | **回退**；由 playbook 那一步给出「运行 X，产物按 Y 的格式放在 Z」。这正是 `SKILL-SET-RULES.md` `### Upstream skills` 第 3 条「Connect outside the upstream text first … in the line a caller reads」 |
| e. 改变能力本身、放在 MMW 之外也成立的方法 | `tdd` 三段（seam 写在纸上；重构的两个去处）；`prototype` 的 EXP 分支与「不再用完即扔」；`resolving-merge-conflicts` 的 clean-merge 分支；`grilling` 的「只问属于用户的决定」与第一性原理块；`codebase-design` 的范围限定；`wizard` 两句；`teach`；`wait-what` 的 `visual`；`to-questionnaire` 一句；`improve-codebase-architecture` 改用 `diagram-design` 出图 | **保留**，每段一个 merge-note 条目；段里夹着的 MMW 名词移到调用方。例：`resolving-merge-conflicts` 第 2 步里的 `origin/<base branch>` 与「closeout evidence」（N5 5.2），改为通用措辞，MMW 的具体化写在 worker playbook 里调用它的那一步 |
| f. 上游行数不到一半、实为 MMW 自有的技能 | `implement`（上游只剩 name 与一句）、`code-review`（56 行中 15 行存活）、`to-tickets`（60 中 30）、`to-spec`（45 中 31，merge-note 自认不到一半） | **移出 subtree。** `implement` 的正文变成 `dispatch/playbooks/worker.md`；`code-review`、`to-spec`、`to-tickets` 保留原名，成为 `mmw-v2/skills/` 下的 MMW 自有能力技能；subtree 里的副本恢复原文，不装（同名不能同装，见 11 R4） |

**收益（全部可核对）：**

- `merge-notes/README.md` `## 本仓自有正文的技能` 这个例外消失。它现在要求每次拉上游时手工把自动合进来的上游段落改回本仓的，这是一个会悄悄撤掉改动的手工步骤（同 README 第 15 行对 unlazy 的警告）。
- N10 R1–R4 的 merge-note 复述，随 b 类回退一起消失。
- 残留 ask-matt 的冲突隐患（N10 B10）消失。

**什么样的 MMW 改动可以留在上游文本里：** 只有 a 类与 e 类，而且 e 类要满足三条：

- 删掉 MMW 名词之后仍然成立；
- 有 merge-note 条目写明它改变的行为；
- 技能的主体仍是上游的（保留行数过半）。

超过一半的改写就不再是「上游技能加改动」，而是 MMW 自有的能力（f 类）。

### 8.3 上游技能的调用方式

- 原规则（`merge-notes/README.md` `## disable-model-invocation`）：「上游技能默认让模型可触发，只保留 7 个用户触发」。新规则：**上游技能保持上游自己的设置；两个文件（`SKILL.md` 与 `agents/openai.yaml`）同增同删这一条保留。**
- 影响：`triage`、`wayfinder`、`to-questionnaire` 回到用户触发。`implement`、`to-spec`、`to-tickets` 也回到用户触发，但它们不装，由 MMW 自有的版本或 playbook 顶替。
- 夜里不受影响：4.3 的清单里没有这三个技能。
- 白天的代价：模型不能自己启动这三个技能，要由 mode 告诉用户打斜杠。实际使用以斜杠为主（`/wayfinder` 22 次，Skill 工具 6 次；`/triage` 1 次，Skill 工具 2 次；N10 第 7 节，仅 Claude Code，本报告没有复核）。这是用户可见的变化，列入第 15 节请用户确认。

---

## 9. Q6 旧规则逐条处理

「原防」写这条规则原本要防的问题，「新解」写新架构怎样处理。

### 9.1 `SKILL-SET-RULES.md` `## What skill text is for` 七条事实

| # | 处理 | 原防 | 新解 |
|---|---|---|---|
| 1 交出理解，不只交出步骤 | 保留 | 步骤覆盖不到的情形，agent 无所适从 | 同样适用于 playbook 首段与原则的 `**Why:**` |
| 2 脚本管确定性，文本管判断 | 保留，并扩大 | 文本复述脚本；判断被藏进状态机 | 新增两处落地：重入位置由脚本算（6.4）；锚点一致由 lint 查（6.5） |
| 3 注意力是预算 | 保留 | 读了不用的材料 | 是 playbook 与原则不做成技能（不进系统提示）、夜间不设原则索引的依据 |
| 4 先给方向，再信任 | 改写一句 | 把每一步都写死，流程会僵硬、易碎 | 「Upstream's `implement` is five lines」这个参照在 `implement` 回到原文后仍然成立，但 worker playbook 从此是 MMW 自有文本，长度按「每句由一个判断付费」衡量，不再拿上游 `implement` 当尺子 |
| 5 按分支渐进加载 | 保留，补一句 | 把每次都要读的材料拆碎 | playbook 按任务类型成文件；reference 按分支成文件；原则按需读 |
| 6 技能是按名字组合的平级件 | 改写 | 复制别的技能的文件；复述别的技能的规则 | 平级组合仍适用于能力技能之间。新增层次方向（L7 B.2）：mode → playbook → 能力、原则；能力不点名 playbook；原则只点名原则或能力。playbook 与原则是 mode 技能目录里的文件，不是嵌套技能，与 Memory `fe94802d` 不冲突 |
| 7 一个家；「this is why MMW ships no router skill」；description 说何时开始、结尾说下一步 | **「no router skill」废止**，其余改写 | ① 路由表是第二份副本，会漂移（ask-matt 的漂移：`docs/reviews/2026-09-23-skill-set/汇总.md` 第 44 行两条走不通的路线，N10 第 7 节已核实）；② 某一跳没有下一步时 agent 自己发明做法（#538，N10 第 7 节已核实） | ① 路由的唯一家是 mode；「下一步」的唯一家是 playbook（MMW 自有能力的交还行除外，第 13 节）；上游技能不再带 MMW 的下一步，所以不存在第二份。② mode 与 playbook 的互相存在由 lint 检查（6.5），代替靠人维护的同步规则（上游 `CLAUDE.md` 第 21 行的做法）。③ 「no two skills claim one moment」保留，并扩为 playbook 之间、以及 playbook 与能力之间 |

### 9.2 各节检查

| 节 | 处理 | 要点 |
|---|---|---|
| `### Load and disclosure` | 保留，改写一处 | 「The table that finds the reader's moment sits before any step with side effects」分成两类：角色表与重入表在 mode 与 playbook；能力内部的分支表在能力。「A rule sits in the text of the agent that must follow it」保留，并成为原则层的边界（7.2） |
| `### Redundancy and bloat` | 保留 | 7.4 的「不做成原则」一表就是它的应用 |
| `### Scripts and judgement` | 保留，新增一条 | 「脚本印出的、指向文本的锚点，由 lint 核对」 |
| `### Descriptions` | 保留「只写触发」，改写一处 | 能力技能的 description 不写流水线位置（删 B7 三处）；角色触发只留给被启动提示词点名的 `dispatch`、`code-review`、`advisor` |
| `### Vocabulary` | 保留 | 词表增加 mode、playbook、principle、role pointer 四个词条（`docs/contexts/toolbox/CONTEXT.md`） |
| `### Hand-offs` | 改写一条，其余保留 | 「Each skill ends by naming what comes next, or the caller it returns to」改为：playbook 的步骤点名下一步；能力技能以交还的产物结尾；MMW 自有能力可以保留点名下一个能力的交还行；上游能力不加。「Each event gets one instruction」由 lint 执行 |
| `### Prompts written for other agents` | 保留，补一条 | 脚本送进会话的消息可以带角色指针，指针不是规则 |
| `### Upstream skills` | 改写 | 换成 8.2 的六类规则；「When fewer than half … reviewed as the set's own text」改为「… 移出 subtree」 |
| `### Paths and host neutrality` | 保留，补一条 | 运行时文本不指向工作树里的 `mmw-v2/` 或 `docs/`（冻结，F5） |
| `### Rules and completion criteria`、`### Examples`、`### Refusals …`、`## Editing`、`## Verifying` | 保留 | `Done when` 适用于 playbook 的每一步 |

### 9.3 ADR

| ADR | 处理 | 原防 | 新解 |
|---|---|---|---|
| 0003 不打包成插件 | 保留 | 插件只盖得住部分交付面、部分宿主 | pstack 是 Cursor 插件，MMW 不照搬它的交付方式；新的各层都是技能目录里的文件，`install.sh` 只多几行 `skills.txt` |
| 0006 技能装两处 | 保留 | 同名撞车、宿主各取一份 | 移出 subtree 的同名技能只装一份（11 R4） |
| 0007 提示词源在仓库 | 保留 | 四份手工拷贝漂移 | mode 不进 `shared.md`（5.3） |
| 0008 沉默不算通过 | 保留 | 闸口什么都没做却读起来像通过 | 原则 `silence-is-never-a-pass` 的依据 |
| 0010、0017 被唤醒而不轮询；夜里没有时钟 | 保留 | 轮询与定时器 | 原则 `state-on-the-ticket` |
| 0012 closing pass 的文本放 `night.md` | 保留 | 消费仓库读不到本仓 `docs/adr/` | 扩大为冻结规则的一半：运行时文本只在技能目录（F5） |
| 0014 advisor 一扇门；否决把 caller 规则写进 `shared.md` | 保留 | 到不了 Cursor；按回合付费 | 同理，mode 与原则都不进 `shared.md` |
| 0015 不交付 subagent | 保留 | 五种壳、模型与权限字段的维护负担 | 「角色 = 提示词 + 一行」，不建 agent 定义（6.3） |
| 0019 票的状态是事件的 fold | 保留 | 首行协议易碎；会话记忆不可靠 | 重入行由 fold 算出 |
| 0020 唤醒从 board 发出，文字只带 `#<n> <event>` | **改写一句**（新 ADR 修订 0020） | 唤醒文字复述 tracker 内容会过时或自相矛盾 | 文字 = `#<n> <event>` + 固定的角色指针；指针不含 tracker 数据，原意保住 |
| 0018、0021、0022、0023–0027、0031 | 保留 | — | 本设计不碰 runner、判活、落地、Memory 的机制。N11 记下的 0012 与 `night.md`、0027 与实现之间的已有分歧，与本设计无关，另行处理 |

### 9.4 `mmw-v2/merge-notes/README.md`

| 节 | 处理 | 原防 → 新解 |
|---|---|---|
| `## 上游更新时怎么用` | 保留 | — |
| `## disable-model-invocation`：两处同增同删 | 保留 | 防一半宿主用户触发、一半宿主模型触发。仍然成立 |
| 同节：「上游 skill 默认让模型可触发……保留 7 个」 | 废止 | 原防「user 漏说技能名时 agent 认不出」→ 由 mode 路由与 MMW 自有能力承担；上游设置恢复原样（8.3），也符合 Memory `fe94802d`「不得修改上游 frontmatter」 |
| `## host 中立` | 保留 | 8.2 a 类 |
| `## 本仓自有正文的技能` | 废止 | 原防：拉上游时覆盖本仓正文 → 这些技能移出 subtree，不再有需要防的情形 |

### 9.5 Memory 里的写法决定

| Memory | 处理 | 说明 |
|---|---|---|
| `411750f5` 三条：description 只写触发；`CONTEXT.md` 不是权威；上游能不改就不改 | 全部保留，第 3 条被加强 | 8.2 把「接入在边缘做」推到底：接线移进 playbook |
| `ce037679`：写名字不写路径 | 保留 | 指针写「技能名 + 技能内相对路径」，与它一致 |
| `ce037679`：「MMW 不系统区分用户调用与模型调用」 | 改写 | 只在一处区分：夜里点名的技能必须模型可见（4.3）。其余地方不据此提要求 |
| `ce037679`：「有一张与实际同步的总图」 | 落地 | mode 的路由表就是给 agent 加载的总图，同步由 lint 保证（6.5） |
| `fe94802d`：平级调用、禁止嵌套、不改上游 frontmatter | 保留 | 本设计恢复上游 frontmatter；playbook 与原则不是嵌套技能 |
| `f4c3d378`：技能层要做独立、准确的路由 | 保留意图 | mode 本身就是技能，路由在技能层完成 |
| `415f96d0`：理由只放 ADR（已被 2026-09-28 复审推翻） | 维持推翻 | 跨任务的理由放原则的 `**Why:**`，单处的理由贴在规则旁 |
| `8ec53374` | 细化 | 「agent 定义 = 读哪个 playbook + 一行」落地为启动提示词加一行，不建文件 |
| 提交 `5181acc2` 翻转调用方式的理由（「漏打指令或要自动化时 agent 能自己判断」） | 由新机制取代 | 夜里的自动化本来就靠启动提示词与唤醒；白天靠 mode |

---

## 10. Q7 扩展路径

### 10.1 从 pstack 或其他合集加一个能力技能

| 路径 | 用于 | 做法 | 放弃的备选 |
|---|---|---|---|
| **git subtree** | 源仓库本身就是一个技能合集（如 mattpocock/skills、diagram-design、unlazy 的现有做法） | 照现有 `mmw-v2/merge-notes/README.md`：拉取；每个改动段落写 merge-note 条目；技能进 `skills.txt` | — |
| **钉住提交的快照目录** | 源仓库是多插件的大仓库（pstack 在 `cursor/plugins` 里），而且只要其中几个技能 | 新建 `mmw-v2/upstream-pstack/skills/<名>/`，记录源提交；一个小脚本按清单重新拷贝并显示差异；每个技能一份 merge-note，写明 Cursor 机制的替换（10.4） | 对整个 `cursor/plugins` 做 subtree：带进无关插件，每次拉取都要逐个过滤。直接用研究快照 `docs/research/code-landing-refs/pstack/`：根 `AGENTS.md` 明写它只读、不当事实、脚本不运行 |
| **原样安装** | 只在 Cursor 上用 | 不经 MMW；装 Cursor 插件 | 在 MMW 里就是只有一个宿主能用，违反宿主中立 |

**进门检查（每个外来能力技能都要过）：**

1. 它产出一个能叫出名字的交付物，并且能脱离 mode 被调用（L7 C.1 第 4 问）。否则它是 playbook，照 10.3 处理。
2. 它的 Cursor 专有机制都有替代（10.4 表）。替代不了的（例如依赖 `/loop`、cloud agent），就不收。
3. 与已装技能的 description 并排读，不抢同一件事（`### Descriptions` 第 2 条）。
4. 如果它会被夜里点名，必须模型可见（4.3）。

### 10.2 加一条原则

1. 过 7.3 的七条门槛。多数 pstack 原则在 MMW 里已有同义的家：`prove-it-works` 对 `shared.md` rule 4；`never-block-on-the-human` 对 rule 1 与 `AUTONOMOUS`；`encode-lessons-in-structure` 对 `SKILL-SET-RULES.md` 事实 2。这些不收。
2. 收的原则，逐字抄进 `mmw-v2/skills/mmw/principles/<slug>.md`，写明出处，记入外来清单。
3. 在 `mmw` 的索引加一行。
4. 在用到它的 playbook 步骤括注。

现有文字只因为「加括注」而改动，这是唯一的改动。

### 10.3 加一种工作流

- **白天：** 在 `mmw-v2/skills/mmw/playbooks/` 加一个文件，在 `mmw` 路由表加一行。不改其他任何文字（扩展只加不改）。
- **夜里：** 新的任务类型如果是现有角色的一个分支（例如 worker 遇到一种新票），就加到那个角色的 playbook 里。新的角色要同时改四样：
  - `models.py` 的 `ALLOWED_AGENTS`；
  - `dispatch.sh` 的 `start_one`；
  - relay 的 `WAKES`；
  - 角色指针表。

  这一处「加角色要改代码」不去消除（第 13 节），因为新角色必然带来新事件，脚本反正要改。

### 10.4 Cursor 专有机制怎么替换（L7 E.2）

| pstack 的机制 | MMW 的替换 |
|---|---|
| `mode: true` + `reminder:` | 夜里：消息里的角色指针（6.4）。白天：`mmw` 的 description 与 `/mmw`；是否在消费仓库 `AGENTS.md` 加激活句，由 U1 实测定 |
| `disable-model-invocation` | 上游技能照上游设置；MMW 自有技能 frontmatter 只有 `name` 与 `description`，保持模型可触发；夜里点名的一律模型可见 |
| `paths:` | 写成 description 里的一个分支，或写成 playbook 里「改到 X 类文件时读 Y」 |
| `.mdc` + `alwaysApply` 的模型配置 | `~/.mmw/models.json`，由脚本显式读取（`models.py`）；技能正文不写模型名（ADR 0015：subagent 跑在会话自己的模型上） |
| `agents/*.md` + `subagent_type` | 启动提示词 + `models.json` 一行；子代理用宿主自带的通用 subagent，提示词只写一句（`code-review` 的 `session.md` `## 2`） |
| `Task` 的 `readonly` | 在 reference 开头写「You are read-only」（ADR 0015 的先例） |
| `/loop`、`/goal`、cloud agent、唤醒链 | relay 唤醒 + watchdog + turn guard + runner（Orca、Paseo、Herdr） |
| 运行中 `git show origin/main:` 重读组件 | **禁止**（F5）。外来 playbook 里的这一步删掉 |
| 内置 `create-skill` | `writing-for-agents` |
| `AskQuestion` | 有人的会话里可用；在 `issue-<n>` 工作树里被 `tool-guard` 拒绝 |
| `agent-transcripts/` 的路径 | 不支持；依赖它的技能不收 |
| `cursor-team-kit` 的 `control-ui`、`control-cli` | 按角色找本机的等价技能（`playwright-cli`、`computer-use`）或 `ui-acceptance` 的 oracle；在 playbook 里按能力点名 |

### 10.5 项目私有组件（L7 A.11）在 MMW 里对应什么

| pstack | MMW |
|---|---|
| 项目私有的 `verify-<app>` 技能与 feature map | 消费仓库的 `.mmw/`：`target.json`，以及 `harness/`、`journeys/`、`stories/`（本仓库根的 `.mmw/` 就是一例）；由 `ui-acceptance` 生成与核对 |
| 模型角色配置 | `~/.mmw/models.json`（用户级，不在仓库） |
| benny 的配置与路由表 | `docs/agents/*.md`（`setup-matt-pocock-skills` 生成）；`docs/specs/<effort>/screen-contract.yaml`；`prototypes/`；`AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`（`manage-agents-md` 生成） |
| 个人的 `<handle>-mode` | 不设 |

**一条边界（夜间优先）：** 项目私有组件只能是数据与答案，不能是流水线角色的指令。也就是说，消费仓库不放自己的 playbook 给 worker 或 orchestrator 读。理由：

- worker 在夜里改的正是这个仓库，它的指令若读自工作树，就会在运行中被改，这与 Self-hosting boundary 的用意相同（F5）。
- 项目需要的特殊做法，由票的 `## Read first` 带进来，读者是做这张票的 worker。

生成这些组件的顺序（setup → `manage-agents-md` → `target_config.py --check` → 激活句）放进白天 playbook `adopting-mmw.md`。

---

## 11. Q8 风险与验证

| # | 风险 | 可能的后果 | 验证办法 |
|---|---|---|---|
| R1 夜间重入 | 压缩后的 orchestrator 或 worker 只看指针，读错文件或读错节 | 重复副作用（例如再跑一次 `advance`），或停在一个没人叫醒的地方 | ① lint（6.5）保证指针与锚点存在；② U2 实测：在隔离的测试 home 里，用假 tracker 给一个全新会话只发一条「唤醒 + 指针」，看它打开哪些文件、停在哪一步（这是 `SKILL-SET-RULES.md` `## Verifying` 的「fresh agent given only the trigger」）；③ `tests/dispatch` 加场景：唤醒、`resume` 与告警的文字都含指针 |
| R2 多宿主 | 某宿主读不到跨技能文件；`mmw` 或 `dispatch` 的 description 在某宿主上不触发；Pi、Cursor 没有提问拦截 | 夜里：worker 起不来或读不到 playbook；白天：mode 不被用 | 照 ADR 0006 的探针法：五个宿主各起一个新进程，提示词为「Use the dispatch skill as the worker on ticket #N」，看它打开的文件。Pi、Cursor 缺提问拦截是现状（N8 9.3），文字仍是唯一约束，本设计不加重也不减轻 |
| R3 冻结运行时 | 迁移本身会改启动提示词、`wake_text`、`RESUME:` 的格式、技能路径。若在一次 watch 期间移动 installed checkout，旧 relay 进程会继续发旧格式（ADR 0022：升级前要先停旧 relay），新 worker 却读新 playbook | 同一夜里两个版本混用 | ① 遵守 Self-hosting boundary：只在两次 watch 之间迁移。② 把这条文字规则变成机制：移动 installed checkout 前，`install.sh --check` 报出所有仍打开 watch 的状态目录。这一条是推断的收益，现状没有任何脚本拒绝（N8 第 6 节末行）。③ 迁移分三批（见本表末），每批之间跑一夜 |
| R4 上游拉取与同名 | `code-review`、`to-spec`、`to-tickets` 移出后，subtree 里有同名的原文副本；若有人把 `engineering/code-review` 加回 `skills.txt`，两份同名技能都装上，宿主静默取其中一份（ADR 0006 的撞名实测） | 夜里 reviewer 读错技能 | 在 `check_own_skill_frontmatter.py` 或 `install.sh --check` 加一条：`skills.txt` 里两行解析出同一个 `name` 就失败。测法：造一个重复行，跑 `--check` |
| R5 白天 mode 没人用 | 同 ask-matt（0 次调用），而上游技能又去掉了 MMW 的下一步 | 用户斜杠 `/wayfinder` 之后，地图清空时 agent 不再提醒「新会话跑 `to-spec`」 | U1 实测（第 16 节）。**迁移顺序：** 等 U1 显示 mode 能被用到之后，再回退 c 类交接行 |
| R6 worker 文本搬家后行为回退 | 这是使用最多的路径：`code-review` 被调用 1153 次（N10 第 7 节），每张票都有 worker | 收尾步骤漏做或顺序错 | 移动时逐字搬（`SKILL-SET-RULES.md` `## Editing`：结构性修改逐字搬运）；`tests/verify-ticket` 与 `tests/dispatch` 全过；然后在一个真实消费仓库跑一张真实的票（`## Verifying`） |
| R7 锚点改名 | 有人给 playbook 步骤改了标题，没改脚本常量 | `RESUME:` 指向不存在的标题 | lint 失败即拦下（6.5） |

**迁移分批（夜间优先）：**

1. **只加固，不搬文本：** 角色指针、`RESUME:` 改印标题、orchestrator 的 `RESUME:`、锚点 lint、同名检查、`night.md` 事实表补行。收益立即生效，风险最小。
2. **搬 worker：** `implement` 正文 → `dispatch/playbooks/worker.md`；启动提示词改；删 B7 三处；`code-review`、`to-spec`、`to-tickets` 移出 subtree，subtree 恢复原文。
3. **白天：** 建 `mmw`、原则与白天 playbook；按 U1 的结果回退 b、c、d 类上游段落。

---

## 12. 变更清单与各自的收益

收益只认任务说明里的六类：①去掉一处经 grep 核实的真重复；②给无处安放的内容一个家；③把 MMW 流程从上游文本移走、让上游回到原文；④让一段内容能被两个以上 playbook 或调用方复用；⑤让以后加外来技能时不必改现有文字；⑥消除一处已核实的断点或冲突。

| 变更 | 收益 | 核实依据 |
|---|---|---|
| 新建 `mmw` 技能（工具箱 mode） | ② | B1、B3 没有家（N10 B1、B3，grep 已核实） |
| `mmw` 的白天 playbook（4 份） | ②③ | B2、B4、B5；`wayfinder`、`triage`、`setup-matt-pocock-skills`、`grill-with-docs`、`prototype` 的流程段 |
| 7 个原则文件 | ②④ | 每条都被两个以上文件使用（N9 第 9 节的位置数）；`phase-boundary` 属于② |
| `implement` 正文 → `dispatch/playbooks/worker.md` | ③⑥ | 上游回原文；B9（`## On waking` 第 1 步）；B7 三处往返 |
| `references/` → `playbooks/`（`dispatch`） | ⑥ | 格式 lint 的作用范围；F3 的失效锚点 |
| `code-review`、`to-spec`、`to-tickets` 移出 subtree | ③ | `merge-notes/README.md` `## 本仓自有正文的技能` 的手工回退步骤 |
| 角色指针 | ⑥ | B9 已核实；B8 推断 |
| `RESUME:` 改印标题；orchestrator 的 `RESUME:` | ⑥ | `resume_at` docstring 失效；watchdog 指向被掏空的节；事实表缺行 |
| 锚点 lint | ⑥①（④） | 同上；`WAKES` 与处理行一一对应；mode 与 playbook 互相存在 |
| `NO_QUESTION`、`AUTONOMOUS` 与 worker 那一步的分工 | ①⑥ | N11 contradictions 第 1 条 |
| 删 B7 三处（description 与表行） | ⑥① | N10 B7、R7、R8 |
| ask-matt 残留恢复原文 | ③ | N10 B10 |
| 同名检查 | ⑥ | R4（ADR 0006 撞名实测） |
| 上游调用方式恢复 | ③① | N10 R2、R4（merge-note 复述） |

---

## 13. 不动清单

| 不动的东西 | 理由 |
|---|---|
| `dispatch` 这个名字；`dispatch.sh` 的子命令 | 脚本、测试、提示词、`tool-guard`、任务板都引用它；改名没有六类收益中的任何一类 |
| `dispatch.sh` 里的「角色 → 技能」对应（`start_one`、`advise_one` 的 case 分支），不做成数据文件 | 只有三行；新角色必然带新事件，脚本反正要改（10.3）；做成数据不去掉任何重复（L7 C.6 信号 9） |
| `models.json` 的四个固定角色 | 同上；ADR 0024 的锁与版本机制 |
| relay、watchdog、`turn-guard.py`、`tool-guard.py` 的位置（`dispatch/scripts/`），不另建 `mmw-v2/runtime/` | 它们导入 `statedir.py`、`watchdog.py`、`refusal.py`，是一个整体（N8 第 8 节）；2026-09-06 的这条建议没有收益，本次再次不采用（N8 第 7 节末条） |
| `night.md` 的长内容（closing pass、Memory 收口、`reverify`/`summary`/retro、`finish`、`suspend`） | L7 C.4：只有一个调用方，是这个 playbook 的产物，彼此有收据依赖（N1 第 8 节） |
| `## On waking` 留在 `dispatch` 的 `SKILL.md` | 三个 playbook 共用；它就是 mode 的公共前置 |
| `code-review` 的会话文件与四个 axis 文件；`advisor` 的两扇门 | 能力内部的多步流程（L7 C.3） |
| `verify-ticket` 的 `sub-issues.md`、`linting.md`；`ui-acceptance` 的 oracle 各行与 Five rules | 能力内部 |
| MMW 自有能力的交还行：`design-pages` `edit-pages.md` `## Next`、`pull.md` `## Reached from here`、`write-screen-contract` `## Next`、`to-spec` `## Next`、`to-tickets` 第 8 步、`retro` 返回 `night.md` `## 5` | 能力 → 能力是常规方向（L7 B.2）；#538 表明这类交还行有实际价值；移进 playbook 没有六类收益中的任何一类；上游纯度的顾虑不适用于 MMW 自有文本 |
| `shared.md` | 5.3 |
| `CODING_STANDARDS.md`、`TESTING.md`、`CONTEXT-MAP.md` 与各 `CONTEXT.md` 的结构 | 唯一读者各有其家；词表只增加四个词条 |
| 现有 ADR 正文 | ADR 记录决定；变化另写新 ADR 修订（shared.md rule 13 的例外） |
| `install.sh` 与 `skills.txt` 的机制 | 只改名单里的行 |
| `exe-release`、`code-checkers`、`manage-agents-md`、`retro`、`diagram-design`、`advisor` 的位置 | 都是能力技能，没有要搬的流程段 |
| 上游 e 类改动（`tdd` 三段、`prototype` EXP 分支等） | 改变能力本身，merge-note 已有 |
| pstack 的 todo 抄写与 `skip:` 协议 | 夜里的步骤由脚本把关（6.2） |
| pstack 的「在回复里点名改变了决定的原则」 | 夜里没有面向人的回复（7.2） |

---

## 14. 按 L7 C.6 的 11 个形式拆散信号逐条自查

| # | 信号 | 自查 |
|---|---|---|
| 1 | 新建组件前没有确认已有组件不是合适的家 | `mmw`：ask-matt（上游、路由相反、未装）与 `shared.md`（ADR 0014 已否决）都查过。原则：先排除 `shared.md`、`CODING_STANDARDS.md`、`SKILL-SET-RULES.md` 已有的（7.4）。白天 playbook：每个都吸收了一份现存于上游的 MMW 文本，不是凭空新建 |
| 2 | 新增内容不改变任何决定 | 指针改变重入时读哪个文件；`RESUME:` 改变从哪一步继续；每条原则写明改变的决定（7.4）；不采用 todo 协议正是因为它不改变决定 |
| 3 | 与已有的、位置得当的指引重复 | 原则避开 `shared.md` 已有的五条；mode 不复述 `shared.md` 的汇报规则 |
| 4 | 本可由机制强制的规则写成了文字 | 重入位置、锚点一致、事件与处理行、同名，都做成脚本或 lint |
| 5 | 拆出的 playbook 只调一个技能，没有门槛、所有权或交付物 | 「小改动走 `tdd`」只做成 mode 的一行，不做成 playbook；四份白天 playbook 各有门槛（例如 `idea-to-tickets` 的 Yes/No 与上下文卫生） |
| 6 | 拆出的 reference 每次都读、只有一个调用方、读者是本代理 | `inside-a-ticket.md` 并入 `worker.md`，而不是继续单列 |
| 7 | 新原则说不出改变哪个决定，或只适用于一个流程的一步 | 7.4 每条都跨两个以上机制；只在一处的规则留在原处（N9 9.4 全表不动） |
| 8 | 拆完后调用方要按步骤编号引用被拆出的部分 | 反过来：把现有的按编号引用改为按标题引用 |
| 9 | 拆出的内容没有第二个调用方，也不减少重复 | worker 的搬家以③⑥为收益，而不是以复用为收益；「角色表做成数据」因没有收益而不做 |
| 10 | 把单一入口的固定流程拆成 mode + playbook + 技能三层 | 明确不拆（6.6）：worker、reviewer、orchestrator 各一个操作文件 |
| 11 | 把只在任务流程之间复用的内容做成能力技能 | playbook 不是技能；closing pass、Memory 收口没有做成能力技能 |

---

## 15. 需要用户拍板的事项

按 `shared.md` rule 1，下面几项改变用户看到的东西或范围，由用户决定。其余都是工程决定，本报告已经给出。

1. **白天的取舍：** 上游技能回到原文后，用户直接斜杠 `/wayfinder`、`/grill-with-docs`、`/prototype` 时，技能结尾不再提示 MMW 的下一步，要由 `mmw` mode 或用户本人接上。建议等 U1 实测之后再回退这些交接行（11 R5）。
2. **`triage`、`wayfinder`、`to-questionnaire` 回到用户触发：** 模型不能再自己启动它们（8.3）。
3. **不装上游原文版的 `implement` 与 `code-review`：**
   - 上游原文 `implement` 写的是「run the full test suite once at the end」「use /code-review」。前者与 `shared.md` rule 15 相反；后者会落到 MMW 的逐票评审，而它离开票就没有用处。
   - 所以本设计不装这两个原文版本。装不装属于范围，请确认。

---

## 16. 未确定

| # | 问题 | 为什么定不了 | 需要的实测 |
|---|---|---|---|
| U1 | 白天 `mmw` mode 会不会被用到；消费仓库 `AGENTS.md` 里加一行激活句（例如「Building something in this repository goes through the `mmw` skill; a session whose prompt names its role follows that」）是否有效，值不值每回合一行的常驻成本 | ask-matt 的 0 次调用说明只靠 description 的路由可能没人用（N10 第 7 节），但 ask-matt 的触发句是「不知道用哪个技能时」，与本 mode 不同；Cursor 是否读项目 `AGENTS.md` 只有 `manage-agents-md` 第 8 行的断言；`manage-agents-md` 的固定格式里有没有位置放这一行，也没有核对 | 在一个消费仓库里，分别在有、无激活句的条件下，用 10 条代表性请求（「我想做 X」「地图清完了」「这个小改动」）各开新会话，记录 `mmw` 被加载的次数与交接是否接上；五个宿主各做一轮 |
| U2 | 压缩后，只凭「唤醒 + 指针」能不能回到正确的步骤 | 压缩的时机与摘要内容由宿主决定，仓库里读不到；夜里 orchestrator 会话被压缩的频率也没有记录 | 11 R1 ②：全新会话只收一条「唤醒 + 指针」作为代理测试；另在一个真实夜的 orchestrator 会话里手动触发一次压缩，再投递一条唤醒 |
| U3 | 恢复为用户触发的上游技能，在 Codex、Grok、Pi、Cursor 上对模型是否可见 | N10 只核实了 Claude Code | 各宿主起新进程，列出它看得到的技能 |
| U4 | `dispatch.sh status` 的 `RESUME:` 与 `night.md` 事实表的全部取值是否一一对应 | `status.py` 只读过头部（N1 第 0 节），`finish_preflight` 的内部条件未核实（N1 第 10 节） | 读 `status.py` 与 `finish_preflight` 全文后写出取值表，再加 `tests/dispatch` 场景 |
| U5 | `resume` 的消息加上指针后，worker 会不会把指针当成 orchestrator 的新指令 | 无运行证据 | 在 `tests/dispatch` 的假 runner 里看投递的文字；在一个真实 worker 上跑一次 `resume` |
| U6 | `code-review`、`to-spec`、`to-tickets` 移出 subtree 后，`mmw-v2/board/`、`retro.py` 等是否按文件路径导入了它们目录里的东西 | 没有 grep 全部导入（`TESTING.md` 提到 board 与 retro 按路径导入 `verify-ticket` 与 `dispatch` 的模块，没有提这三个技能） | `grep -rn "upstream/skills/engineering/\(code-review\|to-spec\|to-tickets\)"` 覆盖脚本与测试 |
| U7 | `pipeline-issues.md` 移进 `handed-back-tickets.md` 后，`triage` 的第 5 步能否恢复原文而不丢「外来 issue」一侧的 MMW 连接（进 `to-spec`→`to-tickets`） | N4 5.3 显示第 5 步同时有 b、c 两类改动与一处 e 类（`ready-for-human` 的重定义）；本报告没有逐段通读 `triage` | 逐段对照 `5b1a4c51` 原文，按 8.2 分类 |

---

## 17. 线索材料的采用与核对

| 采用的结论 | 来源 | 核对 |
|---|---|---|
| 启动提示词的原文与行号 | N1 3.2、N10 第 1 节 | 已回 `dispatch.sh` 第 108–109、1741、1949、1967、2072 行核对 |
| `WAKES`、`wake_text` | N1、N10 | 已读 `relay.py` 第 285–299、385–389 行 |
| `RESUME:` 由事件算出、按编号、docstring 失效 | N3 第 2.7 节 | 已读 `verify-ticket.py` 第 2148–2235 行 |
| watchdog 指向 `Exit codes of resume`，而该节只剩两句 | N1 9.1 | 已 grep `watchdog.py` 第 735、780 行；已读 `night.md` 第 102–104 行 |
| 事实表缺「retroed 已记录、未验收」一行 | N1 9.2 第 1 条（推断） | 已逐行读 `night.md` 第 13–22 行，缺行属实 |
| `NO_QUESTION` 与 `implement` 第 23 行出路不同 | N11 contradictions 第 1 条 | 已读两处原文 |
| B1–B5、B7、B9、B10 | N10 第 4 节 | 已读 `dispatch/SKILL.md`、`verify-ticket/SKILL.md`、`ui-acceptance/SKILL.md`、ask-matt 残留、`grill-with-docs`、`wayfinder` 第 126 行、`prototype/UI.md` `## Next` |
| 上游各技能保留行数与改动类别 | N3 第 5 节、N4 第 5 节、N5 5.1–5.2、N10 第 6 节 | 只核对了 `implement` 的上游原文（`git show`）与 `merge-notes/README.md`；其余行数沿用报告的实测，没有复核 |
| 实际调用次数 | N10 第 7 节（N11 指出漏列 `resolving-merge-conflicts`） | 没有复核，只用于量级判断 |
| 原则候选及其出现位置 | N9 第 9 节 | 核对了 `implement` 第 22、23、28、48–49 行，`dispatch/SKILL.md` 第 8 行，`ui-acceptance` Five rules，ADR 0008 标题；其余位置沿用 N9 的 grep |
| 宿主能力（hook、提问拦截） | N8 9.3 | 已读 `turn-guard.py` 头注释、`install.sh` 第 452–456 行 |
| 用户决定 | N1 7.4、N10 第 8 节 | 已用 `nmem m show` 读 6 条原文。N10 把 `f4c3d378` 转述为「不在技能层做独立准确的路由」，原文是条件句：「若不在技能层做独立且准确的路由与编排，agent 会……」，意思是要求在技能层做路由；本报告按原文使用 |
| pstack 的 mode、playbook 格式与 agent 定义 | L7 A.1、A.2、A.7、D.2 | 已读快照 `poteto-mode/SKILL.md` 全文与三份 playbook、`poteto-agent.md` |
