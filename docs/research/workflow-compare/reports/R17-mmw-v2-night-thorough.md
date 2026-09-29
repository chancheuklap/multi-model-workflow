# R17 MMW v2 升级后的完整架构（夜间彻底派）

本文给出 MMW 升级后的完整架构。立场是「夜间彻底派」：夜间流水线完整拆层，orchestrator、worker、reviewer 的流程全部成为 playbook；`dispatch`、`verify-ticket`、`ui-acceptance` 等成为纯能力技能，只讲命令怎么用、判定怎么读；跨角色的规则成为原则；位置与接线由脚本和 lint 保证。白天部分按同一结构处理。

**底稿与准绳。**

- 底稿：`docs/research/workflow-compare/reports/R13-pstack-design-essence.md`（下称 R13）、`R14-mmw-layer-mixing-inventory.md`（下称 R14）。
- 准绳：`L7-pstack-component-contract.md`（下称 L7）。
- 事实来源：清点报告 N1–N10、`N11-mmw-gaps.json`。
- R4、R12：只取其中「已核实」的事实，记作 R4 V<n>、R12 M<n>、R12 K-<n>，不取它们的结论。

**本轮回到原文读过的文件**（第 14 节有完整清单）：

- pstack：mode 全文；`bug-fix`、`orchestrate`、`session-pickup`、`pause-safely`、`authoring-a-skill`、`investigation`、`autonomous-run` 七个 playbook；`agents/poteto-agent.md`；`principle-attack-the-premise`、`principle-never-block-on-the-human`；另有 13 条原则的 frontmatter 与跨文件链接。
- MMW：
  - `dispatch/SKILL.md` 及其全部 references；
  - `implement/SKILL.md` 与它在上游 squash `5b1a4c51` 里的原文；
  - `code-review/SKILL.md`、`references/session.md`，以及上游原文的开头；
  - `verify-ticket/SKILL.md`、`references/sub-issues.md`；
  - `ui-acceptance/SKILL.md`、`advisor/SKILL.md`、`references/consulting.md`、`design-pages/SKILL.md`；
  - `SKILL-SET-RULES.md` 第 1–176 行；
  - 残留 `ask-matt/SKILL.md` 第 1–80 行、`PHASE-BOUNDARIES.md` 第 1–30 行；
  - `mmw-v2/merge-notes/README.md`；
  - `install.sh` 第 1–120、290–330、640–800 行；
  - 脚本片段：`dispatch.sh` 第 60–125、1720–1745、1935–1980、2040–2110、2190–2220、2335–2365 行，`watchdog.py` 第 85–115、728–785、805–820 行，`relay.py` 第 280–300、380–392 行，`turn-guard.py` 第 296–320 行，`tool-guard.py` 第 25–85 行，`verify-ticket.py` 第 2140–2185 行。

**标注。**

- 「原文」指文件里写着的内容。
- 「已核实」指本轮回到原文读到，或跑命令看到。
- 「推断」指由原文推出、原文没有直接写的内容。
- 需要实测才能定的，列在第 11 节「未确定」，并写明怎么测。
- 新写的文字只来自三处：MMW 现有文本、pstack 原文、用户已有的决定。每个新机制都注明它的来源。

**硬约束**（任务给定；只有这六条算约束）：

- H1：宿主不换，没有 Cursor 的 `mode: true` / `reminder`。
- H2：Claude Code 上带 `disable-model-invocation: true` 的技能，模型按名调不到；description 改动要开新会话才生效。
- H3：子代理跑在本会话宿主的模型上；要跨厂商，只能另起会话。
- H4：脚本送进活会话的一条消息必须是一行。
- H5：Self-hosting boundary。
- H6：夜里的会话屏幕前没人。

---

## 0. 结论（先读这里）

1. **改造的核心是把「顺序」和「谁调用我」从能力技能里全部移走，集中进 playbook。** 今天这两类句子分散在三种地方：
   - 17 句能力技能结尾的「下一步」（R14 第 2 节名单）；
   - 被当作角色操作文件的技能正文（`implement`、`code-review/references/session.md`、`dispatch/references/night.md`）；
   - 脚本送进会话的文字。

   改造后：
   - 能力技能以「交回什么」结尾；
   - 16 份 playbook 各自装一类任务从头到尾的顺序；
   - mode `mmw` 装路由、常驻纪律和重入协议；
   - 脚本只送数据，外加一个按固定格式写的步骤指针。这个格式由 lint 核对。
2. **层与位置**（第 1 节）：
   - `mmw-v2/skills/mmw/` 是唯一的 mode，按 pstack `poteto-mode/` 的布局放 `playbooks/`、`principles/`、`references/`、`scripts/`，另有两份数据文件：
     - `roles.json`：角色定义层，记录角色 → playbook → `models.json` 行；
     - `imports.tsv`：外来文件清单。
   - 能力技能留在 `mmw-v2/skills/<name>/`，外来能力技能留在各个 `upstream*/`。
   - 新增 `mmw-v2/upstream-pstack/`，给以后搬入 pstack 用。
3. **16 份 playbook 覆盖 MMW 的全部工作流**（第 3 节）：
   - 白天 8 份：`define-a-change`、`map-a-large-effort`、`design-an-interface`、`fix-a-bug`、`research-a-question`、`triage-an-issue`、`onboard-a-repository`、`ship-a-release`；
   - 夜间与单票 5 份：`run-a-night`、`accept-the-night`、`run-one-ticket`、`work-a-ticket`、`review-a-ticket`；
   - 只在本仓库用的 3 份：`author-a-skill`、`pull-an-upstream`、`import-a-component`。
   - 由 mode 路由表直接指向能力技能、不设 playbook 的请求有 12 类（改模型、开任务板、画图等）。它们都只调用一个能力，没有跨能力的顺序（L7 C.6 信号 5），按类型本来就属于能力技能这一层，不是「留在原处」。
4. **能力技能变纯**（第 4 节）：
   - `implement`、`code-review`、`grilling`、`codebase-design`、`grill-with-docs`、`tdd`、`triage` 等 13 个上游技能回到原文，或回到只剩三类边缘改动（宿主中立、调用开关、带 merge-note 的能力扩展）。
   - `to-spec`、`to-tickets` 的正文多数是 MMW 自己写的（R4 V11），改为 MMW 自有能力技能（`self/`），上游目录恢复原文、不再安装。
   - 新拆出一个能力技能 `shared-experience`，内容来自 `implement` 的 Memory 部分与 `saving-memory.md`。
   - `writing-interface-code.md` 并入 `ui-acceptance`；state list 的格式并入 `design-pages`。
   - `dispatch`、`verify-ticket` 的 `SKILL.md` 改写成命令参考：没有角色分派表，没有「下一步」。
5. **原则层是真正的一层**（第 5 节）：
   - `mmw/principles/` 放 11 份 MMW 自有原则（10 条通用判断，外加阶段边界一条），另有 14 条与 MMW 现有规则重合的 pstack 原则（经导入脚本搬入）。
   - 格式与 pstack 相同（frontmatter `name`、`description`，正文是规则、`**Why:**`、`**Pattern:**`）。
   - 因为 H2，原则是普通文件，不是技能。
   - `shared.md` 是用户的全局规则，MMW 不改写它；原则索引按规则号引用它的第 1、10、11、13、14、15 条。
6. **夜间在 H4–H6 下比现在更稳**（第 7 节）：
   - 每条唤醒、告警和启动提示词都带一个同一行的步骤指针，写法是 `mmw <playbook>#<步骤标题>`。
   - `RESUME:` 改为按步骤标题指路，不再按编号。
   - 新增 `dispatch.sh where`：会话被压缩后，靠它算出自己的角色和该做的步骤。
   - `check_wiring.py` 核对所有指针、所有「事件 → 处理行」、所有原则引用。
   - 今天已核实的四处断点都在改造中修掉：
     - worker 读不到 `## On waking`（N10 B9）；
     - `MMW turn guard:` 找不到处理行（R4 V7）；
     - 八种 watchdog 告警只有一种有处理行（R12 M16）；
     - `NO_QUESTION` 与 `implement` 给的出路不一致（R4 V9）。
7. **pstack 组件可以直接落位**（第 8 节）：
   - playbook、原则放进 `mmw/playbooks/`、`mmw/principles/`，在 mode 里加一行路由或索引；
   - 能力技能在 `skills.txt` 加一行 `ps/<name>`；
   - 机械改写由 `import_component.py` 完成；
   - Cursor 专有机制与 PR 依赖映射到 mode `## Slots` 的一张表；
   - 多模型面板（H3）用另起的会话实现，第一版不建。
8. **分四批落地**（第 10 节）。第 2 批（夜间层）受三组天然整体约束（R14 W1–W3），必须在同一批里改完。每批完成后流水线仍能照常跑：已安装的 checkout 只在没有 watch 打开时才移动（H5），回退方法是把已安装的 checkout 移回上一个 `main` 提交。
9. **需要用户决定的只有四件**（第 11.2 节）：
   - D1：是否现在就导入那 14 条 pstack 原则；
   - D2：`dispatch.sh check` 自动跑 `install.sh` 的行为，是改成只报告，还是改根 `AGENTS.md` 的规则；
   - D3：是否往你各个消费仓库的 `AGENTS.md` 加一行 mmw 指针；
   - D4：第 2 批的提升时机，以及用一个真实的夜做验收。

### 0.1 改造前后，一眼看得到的区别

| 看什么 | 改造前 | 改造后 |
|---|---|---|
| 「做一张票走哪些步」 | 读 `implement`；它再把你送到 `verify-ticket/references/sub-issues.md`、`dispatch/references/inside-a-ticket.md`、`ui-acceptance` 的五条规则、`code-review`。worker 醒来时还缺 `dispatch` 的 `## On waking` 第 1 步 | 读 `mmw/playbooks/work-a-ticket.md`：9 个带标题的步骤从头到尾；醒来时，唤醒消息那一行已经点名了步骤 |
| 「从想法到关票」的全流程 | 把 17 句结尾段按顺序拼起来（`SKILL-SET-RULES.md` 事实 7） | mode 路由表每类任务一行，每行指向一个 playbook 文件 |
| 能力技能的结尾 | 「The `to-tickets` skill.」「return to … `night.md` `## 5`」 | 交回什么（`Done when` 或交付物） |
| 上游技能 | 带 +1612/−358 行本仓改动（R14 第 0 节第 3 条） | 只剩宿主中立、调用开关、带 merge-note 的能力扩展三类 |
| 跨任务的判断 | 散在 ADR、`shared.md`、`SKILL-SET-RULES.md`、`CODING_STANDARDS.md` 和技能正文里，平均每条 6 处以上（R14 第 0 节第 2 条） | `mmw/principles/` 一个目录，mode 里一张索引；调用方只写名字，外加一句本地限定 |
| 角色 | 写在 `dispatch.sh` 的提示词字面、`relay.py` 的 `WAKES`、`dispatch/SKILL.md` 的 moment 表里 | `mmw/roles.json` 一个文件：角色 → playbook → `models.json` 行 |
| 搬入一个 pstack playbook 或原则 | 没有地方放 | 在 `mmw/playbooks/` 或 `mmw/principles/` 放一个文件，在 mode 里加一行 |
| 搬入一个 pstack 能力技能 | 没有来源目录 | 在 `skills.txt` 加一行 `ps/<name>` |
| 夜里被压缩的会话 | 靠残留的上下文 | 下一条唤醒带步骤指针，或者跑 `dispatch.sh where` |

---

## 1. 目标目录树与命名规则

### 1.1 各层的判据

| 层 | 放什么 | 判据出处 |
|---|---|---|
| mode | 跨 playbook 的触发、原则索引、自主权、子代理规则、重入协议、槽位映射、执行协议、路由表 | L7 A.1；`skills/poteto-mode/SKILL.md` 的 8 个 `##` 节 |
| playbook | 一类任务里多种能力的先后、门槛、所有权、何时停、交付什么；只属于这类任务的做法放在它的规则簇里 | L7 A.2、C.4 |
| 能力技能 | 一项可以命名的能力及其交付物；不知道是谁调用它；可以带自己的人工闸门 | L7 A.3、B.2 硬规律第 3 条 |
| 原则 | 跨任务、能用短名说出口、有可观察的触发情境、能改变一个具体决定的判断 | L7 A.4 |
| reference | 只在某个分支才读的材料、交给子代理的简报、会增长的目录、模板、被两份以上 playbook 共用的表 | L7 A.5 |
| 脚本 | 确定性的状态、投递、检查；不做判断 | L7 A.6；`SKILL-SET-RULES.md` 事实 2 |
| 角色定义 | 一个另起的会话读哪份 playbook、用 `models.json` 哪一行、由哪条命令起 | 用户已定方向（Memory `8ec53374`「agent 定义（读哪个 playbook + models.json 一行）」）；pstack `agents/poteto-agent.md` |
| 配置 | 角色 → 宿主、模型、档位；runner；消费仓库的目标配置 | L7 A.8 |
| 仓库文档 | ADR、词表、技能写作规则、runbook、merge-note、downstream-note | L7 A.9 |
| 外来组件 | 各个上游 subtree，由 merge-note 记录改动 | 根 `AGENTS.md` `## Key Conventions` |

### 1.2 `mmw-v2/`

```
mmw-v2/
├── skills.txt                         安装名单。前缀：engineering/ productivity/ self/ dd/ ，新增 ps/
├── install.sh                         唯一安装入口（改：装 self/mmw 与 ps/ 前缀；注册 mode_hook；--check 核连线）
├── skills/                            MMW 自有技能（self/）
│   ├── mmw/                           ← mode。模型可触发（H2）
│   │   ├── SKILL.md                   Non-negotiables / Principles / Autonomy / Subagents / Re-entry /
│   │   │                              Writing the reply / Slots / Playbooks（第 2 节）
│   │   ├── roles.json                 角色定义：worker、reviewer、night-orchestrator、ticket-orchestrator、advisor
│   │   ├── imports.tsv                本目录里每个外来文件：本地路径、来源路径、来源提交、做过的机械改写
│   │   ├── playbooks/                 16 份（第 3 节）
│   │   │   ├── define-a-change.md         ├── run-a-night.md
│   │   │   ├── map-a-large-effort.md      ├── accept-the-night.md
│   │   │   ├── design-an-interface.md     ├── run-one-ticket.md
│   │   │   ├── fix-a-bug.md               ├── work-a-ticket.md
│   │   │   ├── research-a-question.md     ├── review-a-ticket.md
│   │   │   ├── triage-an-issue.md         ├── author-a-skill.md       （只在本仓库）
│   │   │   ├── onboard-a-repository.md    ├── pull-an-upstream.md     （只在本仓库）
│   │   │   └── ship-a-release.md          └── import-a-component.md   （只在本仓库）
│   │   ├── principles/                MMW 自有 11 份 + pstack 14 份，同一个命名空间（第 5 节）
│   │   │   └── principle-<slug>.md
│   │   ├── references/
│   │   │   ├── subagent-brief.md              mode 用：派子代理的简报模板
│   │   │   ├── contract-authority.md          run-a-night 与 run-one-ticket 共用：contract 子票的权威顺序
│   │   │   ├── watchdog-alerts.md             run-a-night 与 run-one-ticket 共用：八种告警各怎么处理
│   │   │   ├── define-a-change/where-you-are.md
│   │   │   ├── map-a-large-effort/interface-and-remake.md
│   │   │   ├── accept-the-night/pipeline-issues.md
│   │   │   ├── review-a-ticket/standards.md、spec.md、tests.md、ui.md   四个 axis 子代理的简报
│   │   │   └── onboard-a-repository/label-sets.md、pipeline-store.md    写进消费仓库的 MMW 附加段
│   │   └── scripts/
│   │       ├── mode_hook.py           宿主 hook：会话开始、被压缩后、每次提交 prompt 时打印一行
│   │       └── import_component.py    import-a-component 第 2 步
│   ├── dispatch/                      能力：流水线命令行。SKILL.md 是命令参考
│   │   ├── SKILL.md、hosts.json、references/editing-models.md
│   │   └── scripts/dispatch.sh relay.py watchdog.py status.py turn-guard.py tool-guard.py
│   │               models.py statedir.py ghlist.py runners/{orca,paseo,herdr}.sh
│   ├── verify-ticket/                 能力：判据、事件、子票、lint、发布（scripts 不变）
│   ├── ui-acceptance/                 能力：被测产品、四个 oracle、lease
│   │   └── references/ …原五份 + writing-interface-code.md（从 implement 搬来）
│   ├── shared-experience/             能力（新拆）：Memory 的打开、搜索、保存、更正
│   │   ├── SKILL.md
│   │   └── references/saving-memory.md（从 implement 搬来）
│   ├── to-spec/                       能力（从上游目录分出的 MMW 自有文本）
│   ├── to-tickets/                    能力（同上）
│   ├── design-pages/                  能力 + references/state-list-format.md（R12 K-14）
│   └── write-screen-contract/ retro/ advisor/ exe-release/ code-checkers/ manage-agents-md/
├── upstream/                          mattpocock 原文；只允许三类改动，每处都有 merge-note
├── upstream-diagram-design/           同上
├── upstream-unlazy/                   gate-check 引擎（不装进宿主）
├── upstream-pstack/                   新：pstack 原文 subtree；能力技能以 ps/<name> 安装
├── merge-notes/                       每个改过的上游组件一份（pstack 的叫 pstack-<name>.md）
├── downstream-notes/
├── prompt/                            用户级提示词。shared.md 归用户所有，MMW 不改写
├── board/                             任务板（产品本身，不属于 MMW 的层）
├── migrations/
└── tests/
    ├── lib/check_wiring.py            新：连线 lint，每个套件先跑（第 7.4 节）
    ├── mmw/                           新：roles.json、mode_hook、import_component、where 的测试
    └── dispatch/ relay/ verify-ticket/ … 现有十二个套件
```

仓库文档：

```
docs/
├── skill-set/SKILL-SET-RULES.md       从 writing-for-agents 搬出（R12 K-38），加 ## Layers of the set
├── skill-set/REVIEWING-A-SKILL-SET.md
├── adr/0032-the-set-is-layered.md     新：mode / playbook / 能力 / 原则 / 脚本 / 角色
├── adr/0033-wakes-carry-a-step-pointer.md   新，amends 0020
├── adr/0034-pstack-enters-as-a-subtree.md   新
├── contexts/toolbox/CONTEXT.md        加词条：mode、playbook、principle、role、slot
└── contexts/night/CONTEXT.md          加词条：role pointer、where line
```

### 1.3 消费仓库

```
<consuming repo>/
├── AGENTS.md                          ## External References 里有 docs/agents/* 行（setup-matt-pocock-skills 写）；
│                                      是否加一行 mmw 指针待 D3
├── docs/agents/issue-tracker.md       tracker 操作、三组 label、## Morning queries（配置；onboard 写）
├── docs/agents/triage-labels.md、domain.md
├── .mmw/target.json、harness/、stories/、journeys/   被测产品的答卷（ui-acceptance 读）
├── docs/specs/<effort>/screen-contract.yaml
├── prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/
└── .worktrees/issue-<n>、merge-<branch>              流水线专用的名字
```

### 1.4 `~/.mmw/`（机器状态，不在仓库里）

```
~/.mmw/
├── installed-root                     已安装 checkout 的路径（H5 的锚）
├── models.json                        runner + 角色行：junior-worker、senior-worker、reviewer、advisor；
│                                      以后的面板角色（第 8.4 节）
├── boards.json
└── state/<owner>__<name>/             watches.json、relay.lock、watchdog.lock、watchdog.json、
                                       panels/<id>/（第 8.4 节，以后）
```

### 1.5 命名规则

| 组件 | 位置 | 名字 | 由什么核对 |
|---|---|---|---|
| mode | `skills/mmw/SKILL.md` | 技能名 `mmw`（R12 K-17），全套只有这一个 mode | `check_own_skill_frontmatter.py` |
| playbook | `skills/mmw/playbooks/<slug>.md` | slug 写成「动词-宾语」小写连字符；文件首行 `### <Title>`，没有 frontmatter（L7 A.2）；步骤写成 `N. **<Title>.** …`（`orchestrate.md` 的 `#### Steps` 写法） | `check_wiring.py` 第 1、6、7 类 |
| 步骤指针 | 脚本文字、唤醒、提示词、playbook 之间 | `mmw <slug>#<Step title>`，只按标题，禁止写编号（`SKILL-SET-RULES.md` 第 81 行「by title rather than by number」） | 第 1 类 |
| 原则 | `skills/mmw/principles/principle-<slug>.md` | frontmatter `name: principle-<slug>`；`description: "Apply when … . <规则摘要>."`（L7 A.4 模板）；MMW 自有的与 pstack 的共用一个命名空间，同名时导入脚本拒绝 | 第 4、5 类 |
| 原则引用 | 任何文本 | `mmw` 目录内写 `principle-<slug>`；其他地方写 ``principle-<slug>`（the `mmw` skill's `principles/`）``（R12 K-8 的两种写法之一） | 第 4 类 |
| reference | `skills/mmw/references/` | 只有一份 playbook 用：`references/<playbook-slug>/<name>.md`；两份以上共用：`references/<name>.md`；mode 自己用：`references/<name>.md` | 第 2 类 |
| mode 脚本 | `skills/mmw/scripts/` | 只放两种：由 playbook 某一步调用、且只有这一个调用方的；为 mode 注册的 hook | 人工评审 |
| 能力脚本 | `skills/<cap>/scripts/` | 被多个 playbook 或用户直接调用的，归拥有它的能力技能 | 人工评审 |
| 角色 | `skills/mmw/roles.json` 的键 | `worker`、`reviewer`、`night-orchestrator`、`ticket-orchestrator`、`advisor`；`models_row` 取 `models.json` 现有的行名 | 第 6 类 |
| 能力技能 | `skills/<name>/` 或 `upstream*/…/<name>/` | 维持现名；新拆的取源文字里已有的名字（`shared-experience` 取自 `implement` `## Shared experience while implementing` 与 `dispatch.sh` 第 1729 行「Shared experience for ticket」） | `install.sh` 查重 |

脚本放哪一层的判据是推断，由 L7 C.1 第 4 问推出：只有一个 playbook 调用、用户不会直接调用的脚本，放 `mmw/scripts/`（pstack 的 `orch`、`watch-pr` 就这样放在 mode 下）。被多个 playbook 或用户直接调用的，是一项能力，归能力技能：

- `dispatch.sh` 被 `run-a-night`、`run-one-ticket`、`work-a-ticket`、`accept-the-night`、`triage-an-issue` 五个 playbook 调用，用户还会直接用它改模型、开任务板；
- `verify-ticket.py` 被 7 个 playbook 调用。

所以这两份脚本留在各自的能力技能里，不是「留在原处」，而是按类型本就在这一层。

---

## 2. mode `mmw`

### 2.1 frontmatter

```
---
name: mmw
description: How work runs in a repository that uses the MMW landing pipeline: routes a task to its playbook, indexes the principles, and says what an unattended session may decide. Use in a repository whose issue tracker is set up for MMW or that has a `.mmw/` directory, when a start prompt names it, or when you were woken with a step pointer.
---
```

- 没有 `disable-model-invocation`，因为按 H2，带这个键的技能在 Claude Code 上按名也调不到，脚本起的会话就没法「Use the mmw skill」。
- description 不写宿主名，也不写 runner 名（`SKILL-SET-RULES.md` `### Descriptions` 第 3 条）。
- 触发条件里的「tracker set up for MMW」对应 `docs/agents/issue-tracker.md` 是否存在。这一条是推断，第 11 节 U-1 实测。

### 2.2 正文逐节

每节写三件事：放什么、来源、预计行数。行数都是推断。

**`## Non-negotiables`**（约 20 行）：MMW 独有的「遇到 X 就用 Y」。每条写一个条件和它指向的组件：

| 条件 → 指向 | 来源 |
|---|---|
| 协议状态（关票、改队列 label、写事件）→ 只经它的脚本。hook 会拦住手动做法 | `implement/SKILL.md` 第 99 行「Never close the ticket or swap its labels yourself: a hook blocks the command」；`tool-guard.py` `REFUSAL`；`CODING_STANDARDS.md` `## State and configuration` 第 3 条 |
| 一个 `CHECK:` 红了 → 改产品，或开子票质疑来源，不改检查（`principle-silence-is-never-a-pass`） | `implement` 第 22 行；`ui-acceptance/SKILL.md` 第 10 行 |
| 要起、停、触达产品，或碰进程、端口 → 先读 `ui-acceptance` 的 `## Five rules while the product is running` | `dispatch.sh` 第 109 行 `PRODUCT_RULES` |
| 一个撤销代价高的决定，或一个试了两次都没解决的问题 → `advisor` 技能 | `advisor/SKILL.md` description；`references/consulting.md` `## When it is worth a session` |
| 同一前提下两次修复都失败 → `principle-attack-the-premise` | pstack mode 第 46 行 |
| 合并冲突，或干净合并后检查变红 → `resolving-merge-conflicts` 技能 | `implement` 第 78、99 行 |
| 改了 `mmw-v2/upstream*/` 里的文本 → 写 merge-note；改动让消费仓库的产物失效 → 写 downstream-note | 根 `AGENTS.md` `## Key Conventions` |
| 流水线外自建 worktree → 放在 `.worktrees/` 下，避开 `issue-<n>`、`merge-<branch>` 两种名字 | 根 `AGENTS.md` `## Key Conventions`；R13 I-15 |
| 在本仓库、有 watch 打开时 → 不运行正在被改的 MMW，不移动已安装的 checkout（H5） | 根 `AGENTS.md` `## Self-hosting boundary` |
| 秘密 → 不进任何产物（`principle-no-secret-in-an-artifact`） | 第 5 节 |
| 一个阶段结束 → `principle-decide-at-phase-boundaries` | 残留 `ask-matt/PHASE-BOUNDARIES.md` |

**`## Principles`**（约 35 行）：

- 索引，分四组：Verification、State and waking、Collaboration、Engineering。每行写 `**<Title>** (principle-<slug>). <何时适用>.`。
- 「何时适用」一句取自原则 description 的第一句，由 lint 核对二者一致（第 7.4 节第 5 类）。
- 索引行不写规则句（R12 K-27）。规则句只在原则文件里，否则同一句核心规则会写成两份。
- 末尾一段「User rules」，按编号列 `mmw-v2/prompt/shared.md` 第 1、10、11、13、14、15 条的适用时机，不复述规则内容。
- 首句照 pstack mode 第 39 行：「Read the principle file in full for any principle you apply.」

**`## Autonomy`**（约 15 行）：

- **优先级**：`shared.md`（用户规则）> 本 mode > playbook > 能力技能自带的闸门。pstack 没写这一句（L7 E.1 第 18、30 条），MMW 写明。
- **有人在场的会话**：适用 `shared.md` 第 1–3 条。可以撤销的流水线动作（`advance`、`route`、`resume`）直接做。以下几件总是先问：
  - 把 project branch 合进默认分支（`night.md` 第 200 行「that remains the user's release decision」）；
  - 运行完整的 `install.sh`（根 `AGENTS.md` Gotchas「runs only when the user explicitly authorises it」）；
  - `finish` 只在用户验收之后跑（`night.md` `## 6`）。
- **无人会话**（脚本起的会话，启动提示词写 `Unattended`）：
  - 屏幕上不放问题，`tool-guard.py` 的 question gate 会拦住；
  - 产品层面的决定走本角色的出口，出口写在每份角色 playbook 的 `#### Unattended outlets` 里；
  - 流水线本身出故障时，开 `fault` 子票，然后停（`ui-acceptance` 规则 4、5）。
- **`shared.md` 第 11 条「redo it yourself」与「停下报告」的划界**：你自己的步骤失败了，照第 11 条重做；你代码之外的东西出故障（流水线、环境、够不到产品），`fault` 子票就是这一步的重做，不绕开它（原文依据：`ui-acceptance` 规则 5「not yours to route around」）。这修掉 R14 PC18 列出的张力。
- 这一节接住了 `dispatch.sh` 第 108 行 `AUTONOMOUS` 常量里的规则。常量随之删掉，启动提示词里只留 `Unattended` 这个数据（`SKILL-SET-RULES.md` `### Prompts written for other agents` 第 2 条）。

**`## Subagents`**（约 10 行）：

- 用宿主自带的通用子代理（ADR 0015）。简报照 `references/subagent-brief.md`，第一句要求子代理读 mode 的 `## Principles` 和它所服务的那一步。这对应 pstack 的 `agents/poteto-agent.md`。
- 一条消息同时派出，等全部回来（`code-review/references/session.md` 第 23、33 行）。
- 不点名模型（H3；`session.md` 第 23 行「Name no model and no thinking level」）。
- 只读靠简报里的一句话保证（ADR 0015；R14 PC15）。
- 报告写进文件（`session.md` 第 31 行）。
- 模型角色：会话内的角色一律跑在本会话的模型上（pstack 的 `inherit-parent`）；需要另起会话的角色见 `models.json`（`python3 …/models.py config show`）。

**`## Re-entry`**（约 8 行）：醒来和被压缩之后的协议，内容来自 `dispatch/SKILL.md` `## On waking`：

1. 唤醒可能打断了你正在跑的命令，先把它原样再跑一次（`principle-make-operations-idempotent` 的使用一侧）。
2. 读唤醒点名的那条票上的内容。
3. `dispatch.sh ack <n> <event>`。`watchdog:` 开头的行和 `MMW turn guard:` 行不 ack。
4. 去唤醒那一行指针点名的步骤。没有指针时（会话被压缩，或者收到的消息不是唤醒），跑 `dispatch.sh where`，照它印出的 playbook 和步骤做（`principle-the-tracker-is-the-state`）。

这一节修掉 N10 B9：今天 worker 走 `dispatch` 表第 1 行直接进 `implement`，读不到第 1 步。改造后 worker 按启动提示词读 mode，所以读得到。

**`## Writing the reply`**（约 4 行）：

- 回复写法由 `shared.md` 第 4–9 条决定，mode 不复述。
- MMW 只加一条：无人会话的交付物（closing comment、review 报告、写给 orchestrator 的评论）要带 `skip:` 行，并点名改变了决定的原则（第 6 节）。
- 对导入的 pstack 组件：它们关于标点的规则（mode 第 102–103 行）不管给用户的回复，给用户的回复以 `shared.md` 为准（R13 I-16）。

**`## Slots`**（约 20 行）：一张表，把导入组件和 MMW 自己的 playbook 共用的角色名，映射到 MMW 的实物。见第 8.2 节。

**`## Playbooks`**（约 40 行）：

- 首段是执行协议，见第 6 节。
- 升级路由（照 pstack mode 第 119 行）：没有 playbook 匹配时，直接在原则之下做这件事；同一类请求反复出现，就走 `author-a-skill` 提议一份 playbook。原文依据是 pstack `authoring-a-skill.md`「A workflow you keep hitting but isn't captured → propose a new skill」。pstack 的 `figure-it-out` 以后导入时，替换这一句。
- 路由表：每行写 `- **<Name>.** <任务类型>. [用户原话]. [Distinct from …]. \`playbooks/<slug>.md\`.`（L7 A.1），全表见第 3.1 节。

整个文件约 150–170 行，是推断，与 pstack mode 的 143 行（L7 A.0）同一量级。它对 worker 上下文的成本列入 U-5。

### 2.3 mode 怎样被加载（H1、H2）

| 会话 | 怎样读到 mode | 怎样找到 playbook 与步骤 | 依据 |
|---|---|---|---|
| 人启动的会话（白天） | ① mode 的 description 可被模型触发；② `mode_hook.py` 在 prompt 提交时打印一行：「This repository uses MMW: the `mmw` skill routes this task to its playbook.」，只在仓库有 `.mmw/` 或 `docs/agents/issue-tracker.md` 时打印 | mode 路由表 | ① H2；② pstack `reminder:`「New task? Playbook match or rigor needed -> apply /poteto-mode」的替代（L7 E.2）。宿主是否有这个 hook 事件见 U-2。只在 MMW 仓库打印，回应了 ADR 0014 的「为偶发之事付每回合的常驻上下文」（R4 V16） |
| 脚本启动的会话（worker、reviewer） | 启动提示词第一行：`Use the mmw skill. You are the worker of ticket #<n>: playbook work-a-ticket. Unattended.` | 提示词点名 playbook；续跑时 `--preflight` 的 `RESUME:` 点名步骤 | 与 pstack `poteto-agent`「Read the `poteto-mode` skill's `SKILL.md` in full before doing any work」同一个作用：worker 也在 mode 的常驻纪律下工作。R4 第 0 节第 4 条「脚本启动的会话不经过 mode」反过来 |
| 人启动、后来当上 orchestrator 的会话（开夜、单票） | 同白天会话 | `open` 与 `open-ticket` 打印的那一行末尾加指针 `mmw run-a-night#Handle each wake` | `dispatch.sh` 的 `open` 行已打印任务板 URL（`night.md` 第 40 行） |
| 被唤醒的会话 | 唤醒那一行带指针：`#<n> reviewer.reported · mmw work-a-ticket#Review round` | 指针（H4：必须和消息同一行，R12 K-1） | `relay.py` 第 385–389 行 `wake_text`；`watches.json` 能区分夜与单票（R4 V3） |
| 被压缩的会话 | 宿主若在压缩后有 hook 事件（Codex 的 `PostCompact`、`SessionStart`，见 `install.sh` 第 768–774 行 `CODEX_LABELS`；Claude Code 的 `SessionStart`，推断），`mode_hook.py` 跑 `dispatch.sh where` 并打印那一行。没有这个事件的宿主，等下一条唤醒带指针；同时 mode `## Re-entry` 第 4 步让会话自己跑 `where` | `where` 的输出 | U-2 实测 |
| advisor 会话 | 不加载 mode。提示词仍是「Use the advisor skill.」加简报 | `advising.md` | advisor 是能力技能自己用的子会话，与 pstack 中 `how`、`why` 的子代理同类（L7 A.3），不属于 mode 管的执行者 |
| 子代理（reviewer 的四个 axis 等） | 简报的第一句要求读 mode `## Principles` 与所服务的那一步 | 简报 | 第 2.2 节 `## Subagents` |

---

## 3. playbook 总目录

### 3.1 路由表（mode `## Playbooks` 的内容）

| 行 | 任务类型与 Distinct from | 目标 |
|---|---|---|
| Define a change | 要建的改动，一次访谈装得下（从对话、清空的地图、已分诊 issue、架构决定出发）。Distinct from Map a large effort：终点还看不见。Distinct from Fix a bug：先有缺陷 | `playbooks/define-a-change.md` |
| Map a large effort | 终点看不见，一个会话装不下（全新项目、大功能）。不用于范围清楚的功能 | `playbooks/map-a-large-effort.md` |
| Design an interface | 改动带界面：原型胜出之后，在 Claude Design 里设计、pull、写 screen contract | `playbooks/design-an-interface.md` |
| Fix a bug | 有东西坏了、在报错、在变慢 | `playbooks/fix-a-bug.md` |
| Research a question | 要一手来源回答一个问题，并把答案写进仓库。Distinct from Map：只回答一个问题 | `playbooks/research-a-question.md` |
| Triage an issue | 不是你建的 issue 或外部 PR。Distinct from Accept the night：那是流水线自己产出的 issue | `playbooks/triage-an-issue.md` |
| Run a night | 「今晚跑 spec #N」：一个 spec 的整批票 | `playbooks/run-a-night.md` |
| Accept the night | 夜跑完了：早上的队列、验收、`finish` | `playbooks/accept-the-night.md` |
| Run one ticket | 在夜之外跑一张票 | `playbooks/run-one-ticket.md` |
| Work a ticket | 被 `start` 派到一张票上；或者自己接一张票（入口 `Picked up yourself`） | `playbooks/work-a-ticket.md` |
| Review a ticket | 被起为某张票的 reviewer | `playbooks/review-a-ticket.md` |
| Ship a release | 出包、打包、做安装程序 | `playbooks/ship-a-release.md` |
| Onboard a repository | 让一个仓库接入 MMW | `playbooks/onboard-a-repository.md` |
| Author a skill | 在本仓库写或改一个组件（只在本仓库） | `playbooks/author-a-skill.md` |
| Pull an upstream | 拉一个上游 subtree 的更新（只在本仓库） | `playbooks/pull-an-upstream.md` |
| Import a component | 从 pstack 搬入 playbook、原则或能力技能（只在本仓库） | `playbooks/import-a-component.md` |
| Improve the architecture | 扫出加深模块的机会 → 告诉用户运行 `improve-codebase-architecture`（这个技能只能由用户触发），它定下的决定进 Define a change | 能力 |
| 直接能力（不设 playbook） | 改宿主、模型或 runner → `dispatch`（`references/editing-models.md`）；开任务板 → `dispatch`；第二意见 → `advisor`；画图 → `diagram-design`；写 AGENTS.md → `manage-agents-md`；装检查器 → `code-checkers`；教学 → `teach`；把刚才说的讲简单 → `wait-what`；问卷 → `to-questionnaire`；只有人能做的步骤 → `wizard`；交接 → `handoff`；重跑一次复盘 → `retro` | 能力 |

直接能力这一行按类型就属于能力层。依据是 L7 C.3 与 C.6 信号 5：这些请求都只调用一个技能，没有自己的门槛或交付顺序，为它们各建一份 playbook 就是形式上的拆散。它们今天也不装流程，只是没有路由表把请求引过去（`SKILL-SET-RULES.md` 事实 7「ships no router skill」）。

### 3.2 每份 playbook

格式照 L7 A.2：`### <Name>`、所有权行、可选首段、带标题的编号步骤、规则簇 `####`、`**Reply:**`。跨会话的 playbook 多一个 `**Where you are.**` 段（R13 E4）。

下面每步都写出它点名的组件：技能、原则、脚本命令或另一份 playbook。「来源」列出这份 playbook 的文字从哪里搬来。

#### PB-1 `run-a-night`（night-orchestrator）

- **入口**：路由行 Run a night；`roles.json` `night-orchestrator`；唤醒指针；`dispatch.sh status <spec>` 的 `RESUME:`。
- **所有权行**：「You own the night's decisions, never a worker's code.」原文依据：`night.md` 第 3 行「Every decision is yours」、第 96 行「its code is the worker's」。
- **首段**：早上的读者是冷读，理由要留在他会看的地方（`night.md` 第 5 行；点名 `shared.md` 第 10 条）。一夜的产出是一批可以验收的票（`night.md` 第 7 行，点名 `principle-silence-is-never-a-pass`）。
- **Where you are**：跑 `dispatch.sh status <spec>`，首行 `RESUME:` 点名步骤（R12 K-3）。脚本算不出的两件事写成两行：用户说开始了 → Check；用户已验收 → 交给 `accept-the-night`。
- **步骤**：
  1. **Check the machine and the batch.** `dispatch.sh check <spec>`（`dispatch`）；`verify-ticket.py <spec> --lint`（`verify-ticket`）；批次驱动 screen contract 时，再跑 `target_config.py --check`（`ui-acceptance`）。
  2. **Open and advance.** `dispatch.sh open <spec>`，把任务板 URL 交给用户；然后 `dispatch.sh advance <spec>`，结束回合（`principle-wake-dont-poll`）。
  3. **Handle each wake.** mode `## Re-entry` 第 1–3 步；`dispatch.sh status <spec>`；按 `#### Wake table` 处理表中匹配的每一行；`advance` 跑一次；frontier 为空且没有活着的 agent → 进 Closing pass。
  4. **Closing pass.** `dispatch.sh findings <spec>`；每条按 `#### Closing pass` 处理，用 `dispatch.sh route` 落地；新写的票用 `verify-ticket.py <n> --lint`；`advance`；循环到没有未路由的 finding。
  5. **Close the Memory records.** `dispatch.sh memory-list <spec>`；四种决定写法见 `shared-experience` 技能。
  6. **Reverify and summarize.** `dispatch.sh reverify <spec>`；`dispatch.sh summary <spec> --memory-decisions <file>`。
  7. **Retro.** 在本会话里用 `retro` 技能。
  8. **Hand the result to the user.** 告诉用户去读 `NIGHT SUMMARY`、`NIGHT RETRO`，接下来走 `accept-the-night`。
- **规则簇**：
  - `#### Wake table`：`night.md` `## 3` 的表，并补齐以下三类：
    - `MMW turn guard:` 行：照消息自己写的命令做（R4 V7）；
    - 八种 watchdog 告警：见共用的 `references/watchdog-alerts.md`（R12 M16）；
    - `resume` 的退出码：0 已送达；4 已交出、未确认；3 对方正在回合里，下一条唤醒时再跑；2 按 stderr 先 `retract`。这些退出码的含义来自本轮读的 `dispatch.sh` 第 2190–2216 行，修掉 R4 V8 指出的 `### Exit codes of resume` 空节。
  - `#### Contract children`：指向共用的 `references/contract-authority.md`，来自 `night.md` 第 96–100 行。
  - `#### Closing pass`：`night.md` 第 106–149 行整块搬来。理由句改为点名原则：
    - 第 126 行 Owns 并发 → `principle-separate-before-serializing-shared-state`；
    - 第 127 行 negative control → `principle-silence-is-never-a-pass`；
    - 第 131–137 行只跑受影响的测试 → `shared.md` 第 15 条。
  - `#### Suspending the night`：`night.md` 第 202–210 行。
  - `#### Unattended outlets`：无人时的出口，来自 `night.md` 第 100 行：把没开始的票移到 `needs-triage`，在子票上评论，把子票留给用户。
- **Reply**：
  - 早上一句话（`night.md` 第 188 行）；
  - `skip:` 行写在 spec 的评论里；
  - 点名改变了决定的原则。
- **来源**：`dispatch/references/night.md` 全文；`retro/SKILL.md` 第 186 行；`turn-guard.py` 第 306–311 行；`watchdog.py` 第 94–109 行。

#### PB-2 `accept-the-night`（有人在场）

- **入口**：路由行；`run-a-night` 第 8 步；`status` 的 `RESUME:` 在「spec 已 `spec.retroed`、用户尚未验收」这一状态时指向这里（补上 R4 V6 缺的那一行）。
- **所有权行**：「You own the morning queue; the user owns acceptance.」
- **步骤**：
  1. **Read the night out.** 把 `NIGHT SUMMARY`、`NIGHT RETRO` 的要点说给用户（`shared.md` 第 4、5 条）。
  2. **Work the needs-triage queue.** 按 `docs/agents/issue-tracker.md` `## Morning queries` 的第一条查询取出队列；每一条用 `triage` 技能处理，流水线产出的 issue 按 `references/accept-the-night/pipeline-issues.md` 处理；需要路由的用 `dispatch.sh route`。
  3. **Put the retro proposals to the user.** 标题为 `Retro #<spec>:` 的 issue，照 `pipeline-issues.md` 相应一行处理。
  4. **List what only the user can do.** 第二条查询 `ready-for-human`（`principle-only-a-person-does-a-person-step`）。
  5. **Merge the accepted night.** 只在用户验收之后跑 `dispatch.sh finish <spec>`；stderr 里给出的删除 worktree 命令交给用户。
- **Reply**：验收了什么；队列里还剩什么；`finish` 的结果。
- **来源**：`night.md` `## 5` 末段、`## 6`；`triage/references/pipeline-issues.md`；`triage/SKILL.md` 第 70、90 行；`docs/agents/issue-tracker.md` 第 86–91 行。

#### PB-3 `run-one-ticket`（ticket-orchestrator）

- **所有权行**：「You own one ticket's ending: start its worker, answer its wakes, land it.」
- **步骤**：
  1. **Open the ticket's watch.** `dispatch.sh open-ticket <n>`，把任务板 URL 交给用户。
  2. **Start the worker.** `dispatch.sh start <n> worker`，结束回合（`principle-wake-dont-poll`）。
  3. **Handle each wake.** mode `## Re-entry`；`#### Wake table`，其中 contract 子票指向 `references/contract-authority.md`，watchdog 告警指向 `references/watchdog-alerts.md`。
  4. **Land.** `dispatch.sh land <n>`；`bounced` 时告诉用户是哪张票、`ticket.bounced` 事件写了什么。
- **来源**：`dispatch/references/one-ticket.md` 全文。今天它把 contract、watchdog、turn guard 三类送到 `night.md` `## 3`（N1 edge）。改造后共用两份 reference，不再跨到另一份 playbook 里找处理行。

#### PB-4 `work-a-ticket`（worker）

- **入口**：`roles.json` `worker` 的启动提示词；路由行 Work a ticket（入口 `Picked up yourself`）。
- **所有权行**：「You own this ticket's branch until its closeout. Build to the baselines, prove each criterion, leave every decision on the ticket.」
- **Where you are**：`verify-ticket.py <n> --preflight` 印 `RESUME: <step title>`；没有这一行，就从 Claim 开始（`principle-the-tracker-is-the-state`）。
- **步骤**：
  1. **Claim.** 自己接的票：先跑 `dispatch.sh adopt <n>`。然后 `verify-ticket.py <n> --preflight`；`NOT_READY` 就停。分支上前一个 worker 留下的 `wip(#<n>)` 提交要接着做。
  2. **Read yourself in.** 依次读：
     - 票本身，以及它开着的子 issue；
     - **Read first**（`principle-the-baseline-is-a-contract`）；
     - **Parent** 指名的 spec 小节；
     - 词表；
     - 界面票：`ui-acceptance` 的 `references/writing-interface-code.md`；
     - 与本票相关的 Memory 记录：`shared-experience` 技能。
  3. **Write the code.** 用 `tdd` 技能，本地限定两句：`CHECK:` 点名的用例就是第一条红测试；要测的 seam 是票的 `## Seam`。`#### While writing code` 适用。
  4. **Integrate and run the criteria.** `dispatch.sh integrate <n>`；冲突或检查变红时用 `resolving-merge-conflicts` 技能；然后 `verify-ticket.py <n>`。
  5. **Post the decisions.** `verify-ticket.py <n> --decisions <file>`。
  6. **Review round.** `dispatch.sh start <n> reviewer`，结束回合（`principle-a-second-reader-judges`）。收到 `reviewer.reported` 后：票内的 finding 修掉或用 `refuted:` 驳回；票外的用 `verify-ticket.py <n> --sub-issue finding <file>`。
  7. **Final run.** `verify-ticket.py <n> --reverify --actor worker`。
  8. **Audit and tell the touched tickets.** 读票审一遍；`verify-ticket.py <n> --touched`。
  9. **Close out.** 只有人能回答的判据，写 `ABANDON: AC<n> decision …` 并开 `decision` 子票；`--draft`；把每个 `<fill>` 填完；`verify-ticket.py <n> --closeout <draft>`。
- **规则簇**：
  - `#### While writing code`：`implement` 第 22–28 行的做法部分，理由句换成点名原则：
    - 第 22 行 → `principle-the-baseline-is-a-contract`、`principle-silence-is-never-a-pass`；
    - 第 24 行 → `principle-migrate-callers-then-delete-legacy-apis`；
    - 第 25 行 → `principle-laziness-protocol` 与 `shared.md` 第 14 条；
    - 第 28 行 → `principle-separate-before-serializing-shared-state`。
  - `#### ABANDON kinds`：`implement` 第 76 行。
  - `#### When something wakes you`：`reviewer.reported`、`reviewer.lost`、`worker.queued`、orchestrator 的 `resume` 文字，每种各一行（W1）。
  - `#### Unattended outlets`：取代 `implement` 第 23 行与 `tool-guard.py` `NO_QUESTION` 两处说法不一的地方（R4 V9）。统一为：取最可能的选项，在 `Decisions I made on my own` 下写一行；答案会改变交付内容时，开 `decision` 子票并照做默认选项；被 `ABANDON: AC<n> decision` 挡住的判据在 Close out 那一步处理。
  - `#### Picked up yourself`：`dispatch/references/inside-a-ticket.md` 全文，包括关票后告诉用户去跑 `land`。
  - `#### Outside Owns`、`#### Memory while working`：`implement` 第 28 行，以及第 36–68 行里属于本票的部分；方法部分指向 `shared-experience`。
- **Reply**：`--closeout` 退出 0 的那条 closing comment 就是交付物。`skip:` 行与原则点名写在 `Decisions I made on my own` 下。
- **来源**：`implement/SKILL.md` 第 8–101 行；`inside-a-ticket.md`；`tdd/SKILL.md` 第 22、38 行；`resolving-merge-conflicts/SKILL.md` 第 2 步的票相关句；`ui-acceptance/SKILL.md` 第 38 行；`verify-ticket/references/sub-issues.md` 第 11 行里属于 worker 的部分。
- **步骤标题与脚本的对应**（W3）：`resume_at` 今天返回「step 1」到「step 5」（`verify-ticket.py` 第 2164–2181 行），改为返回步骤 4–8 的标题：Integrate and run the criteria、Post the decisions、Review round、Final run、Audit and tell the touched tickets。

#### PB-5 `review-a-ticket`（reviewer）

- **入口**：启动提示词 `Use the mmw skill. You are the reviewer of ticket #<n> from base commit <c>: playbook review-a-ticket. Unattended.`，后接 Rules 包（`dispatch.sh` 第 1833 行）。
- **所有权行**：「You own the one review report. Verify every finding; fix none.」依据 `session.md` 第 3、49 行。
- **Where you are**：票上已有本轮的 `reviewer.reported` → 已完成。否则从 Pin the diff 开始：前四步不写任何东西，重跑没有副作用（`principle-make-operations-idempotent`）。`dispatch.sh where` 同样能判断。
- **步骤**：
  1. **Pin the diff.** `git rev-parse`、`git diff <base>...HEAD --stat`；失败时直接写成报告，然后停。
  2. **Run the axes.** 每个 axis 派一个通用子代理，同一条消息里发出；简报是 `references/review-a-ticket/<axis>.md`；有 story criterion 的票才跑 UI axis；等全部回来（mode `## Subagents`；H3：四个 axis 都跑在本会话的模型上）。
  3. **Verify every finding.** 三种结论：Holds、`refuted`、Could not tell（`principle-clues-are-not-evidence`）。
  4. **Sort in-ticket and out-of-ticket.** 六类「票内」依据（`session.md` 第 57 行）。
  5. **Write the report.** `verify-ticket.py <n> --review <file>`。
- **规则簇**：
  - `#### Report format`：`session.md` 第 73–95 行。
  - `#### Active Rules`：`session.md` 第 99–101 行。
  - `#### Unattended outlets`：拿不准的写 `unverified: <what would settle it>`，不向屏幕提问。这给 `tool-guard.py` 管到的 reviewer 补上出口（R14 第 9 节第 2 条）。
- **Reply**：`--review` 退出 0。
- **来源**：`code-review/references/session.md` 全文；四个 axis 文件搬为简报。

#### PB-6 `define-a-change`

- **入口**：路由行。入口变体来自四处：一段对话、一张清空的地图、一个已分诊 issue、一个架构决定。
- **所有权行**：「You own the batch the night will build: every decision recorded, none made for the user.」依据 `to-spec/SKILL.md` 第 6 行「record decisions rather than make them」。
- **Where you are**：`references/define-a-change/where-you-are.md`，9 行事实表（R12 K-33），每行的事实都能在 tracker 或仓库里看到。
- **步骤**：
  1. **Interview.** 用 `grilling` 技能；词表与 ADR 用 `domain-modeling`；用户点名时用 `grill-with-docs`。第 1–5 步留在同一个上下文里（`principle-decide-at-phase-boundaries`）。
  2. **Settle runnable questions.** 答案要靠运行才能知道的问题，用 `prototype` 技能；界面问题转 `design-an-interface`，做完回到第 4 步。
  3. **Decide who checks.** 多会话的构建走 spec 路径，由脚本跑判据、另起 reviewer；小到用户会亲自检查的改动，就在本会话里用 `tdd` 技能直接做，这份 playbook 到此结束。依据：残留 `ask-matt/SKILL.md` 主流程第 3 步（R12 M29）。
  4. **Write the spec.** `to-spec` 技能。要切成几份 spec 时一次只写一份（`several-specs.md` 的循环）。来源是已分诊 issue 时，发布后关掉那个 issue 并在评论里链接 spec（ADR 0001 第 20 行；R12 K-15）。
  5. **Cut the tickets.** `to-tickets` 技能；歧义扫描交给一个没写这批票的子代理（`principle-a-second-reader-judges`）。
  6. **Lint the batch.** `verify-ticket.py <spec> --lint`（`verify-ticket`）。
  7. **Hand to the night.** 告诉用户：用 `run-a-night` 跑 spec #N，或用 `run-one-ticket` 跑单票。
- **Reply**：spec 链接；票的清单及各自的 worker 等级；lint 结果；问过用户的决定；下一步。
- **来源**：
  - `to-spec` `## Next`、第 1 步第 12 行、第 4 步；
  - `to-tickets` 第 20、160 行；
  - `grill-with-docs` 第 7 行末句；
  - `improve-codebase-architecture` `### 4. Hand the decision on`；
  - `verify-ticket/references/linting.md` 第 3 行；
  - 残留 `ask-matt` 主流程第 1–3 步与 `### Context hygiene`；
  - `several-specs.md`。

#### PB-7 `map-a-large-effort`

- **所有权行**：「You own the map, not the build.」依据上游 `wayfinder` `## Plan, don't do`。
- **步骤**：
  1. **Chart the map.** `wayfinder` 技能 `### Chart the map`；终点有界面或是翻新已有产品时，读 `references/map-a-large-effort/interface-and-remake.md`。
  2. **Resolve one ticket at a time.** `wayfinder` 技能 `### Work through the map`；调研类问题走 `research-a-question`；设计票与对齐票走 `design-an-interface`。
  3. **Hand the clear map on.** 没有未关的子票、「Not yet specified」也为空时，告诉用户：在一个新会话里，对这张地图跑 `define-a-change`。地图保持打开。
- **来源**：`wayfinder/SKILL.md` 第 126 行（第 6 步）；`wayfinder/references/interface-and-remake.md`；残留 `ask-matt` on-ramp 第 3 条。

#### PB-8 `design-an-interface`

- **所有权行**：「You own the path from a winning variant to a screen contract; the user owns how it looks.」依据 `design-pages/SKILL.md` 第 10 行「how they look is the user's call」。
- **步骤**：
  1. **Sketch variants.** `prototype` 技能，UI 分支。
  2. **Design in Claude Design.** `design-pages` 技能（`references/edit-pages.md`）。宿主没有 Claude Design 工具时，这个技能自己的闸门会停下，这时告诉用户运行 `handoff`（R12 K-10）。
  3. **Sign off and pull.** `design-pages` 技能（`references/pull.md`）；首次 pull 时拆掉原型的脚手架。
  4. **Write the screen contract.** `write-screen-contract` 技能；差距清单等用户回答。
  5. **Back to the spec.** 进入 `define-a-change` 的 Write the spec 一步；spec 已发布时，用 `to-spec` 的 `references/revising-a-spec.md`。
- **规则簇** `#### A contract child answered by a pull`：来自 `design-pages/references/pull.md` 同名段：评论 → `dispatch.sh route` → 移动票 → `resume`。
- **来源**：`prototype/UI.md` 第 3 步第 83 行与 `## Next`；`design-pages/references/edit-pages.md` `## Next`；`pull.md` `## After the first pull`、`## Reached from here`；`write-screen-contract` `## Next`；`to-spec` 第 2 步第 22 行。

#### PB-9 `fix-a-bug`

- **所有权行**：「You own the root cause and the proof.」
- **步骤**：
  1. **Build a red loop.** `diagnosing-bugs` 技能，Phase 1。
  2. **Find the root cause.** 继续 `diagnosing-bugs` 的后续 Phase（`principle-fix-root-causes`；两次修复都失败时，`principle-attack-the-premise`）。
  3. **Choose the route.** 有干净 seam 的小修复：在本会话里用 `tdd` 技能，先写失败的测试，由用户检查。没有能锁住这个 bug 的 seam：告诉用户运行 `improve-codebase-architecture`，然后进 `define-a-change`。修复需要一批票：进 `define-a-change`。
  4. **Verify on the same surface.** 原来的复现现在通过了（`principle-prove-it-works`）。
  5. **Deliver.** 按 mode `## Slots` 的 delivery 槽位交付。
- **Reply**：坏了什么、根因、修法、复现从红到绿的原样输出。依据 pstack `bug-fix.md` 的 `**Reply:**`。
- **来源**：残留 `ask-matt` on-ramp「Something's broken」；上游 `diagnosing-bugs`（零差异）；pstack `playbooks/bug-fix.md`。这一份补上 N10 B6：`diagnosing-bugs` 之后接什么没有着落。

#### PB-10 `research-a-question`

- **所有权行**：「You own a cited answer that a decision uses.」
- **步骤**：
  1. **Name the decision it feeds.** 地图上的票、spec 的 `## Sources`，或者一份 ADR。
  2. **Run the research.** `research` 技能（后台代理，一手来源，写成仓库里的 Markdown 文件）。
  3. **Link it where the decision is.** 解答评论、spec `## Sources`，或 ADR 引用这个文件（`principle-clues-are-not-evidence`）。
- **来源**：`research/SKILL.md` 的三步；`wayfinder` 第 5 步的调研子代理；`to-spec` 模板 `## Sources`；根 `AGENTS.md` 开头「a spec may cite」。
- 名字不用 pstack 的 Investigation：两者是不同的任务类型。pstack 的是只读回答代码问题，用 `how`/`why`；这份是写一份带出处的调研文件。以后搬入 pstack Investigation 时两份并存，路由表各带 Distinct from。

#### PB-11 `triage-an-issue`

- **步骤**：
  1. **Triage.** `triage` 技能第 1–4 步。
  2. **Apply the outcome.** `triage` 第 5 步的四种结果之一。
  3. **Route ready-for-agent work.** 写 agent brief，然后进 `define-a-change`，把这个 issue 作为来源。
- **来源**：`triage/SKILL.md` 第 82、94 行；残留 `ask-matt` on-ramp 第 1 条。

#### PB-12 `onboard-a-repository`

- **步骤**：
  1. **Set up the tracker.** `setup-matt-pocock-skills` 技能；然后把 `references/onboard-a-repository/label-sets.md`、`pipeline-store.md` 写进 `docs/agents/issue-tracker.md`。这两份的内容取自今天上游种子里 MMW 加的 `## Three label sets`、`mmw:map`，以及 `SKILL.md` 第 51、63 行。
  2. **Write the agent files.** `manage-agents-md` 技能。
  3. **Install the checkers.** `code-checkers` 技能（它自己的第 6 步把命令记进 `.mmw/target.json` 的 `checks`）。
  4. **Answer the product questions.** 只对有界面的仓库：`ui-acceptance` 技能 `target_config.py --check`，直到退出 0。
  5. **Check the machine.** `bash mmw-v2/install.sh --check`（只读）。
- **来源**：`setup-matt-pocock-skills/SKILL.md` 第 17、51、63 行；`code-checkers` 第 6、8 步；`night.md` 第 54–56 行。

#### PB-13 `ship-a-release`

- **所有权行**：「Ship what is on the current branch now.」原文，`exe-release/SKILL.md` 第 10 行。
- **步骤**：
  1. **Check the tree is clean.** `release-flow.sh init` 会拒绝脏的工作树。
  2. **Name the products.** `git ls-files '*.release-adapter.json'`；列出表格；不等回复。
  3. **Drive each product's release loop.** `exe-release` 技能（`references/driving.md` 讲怎样读 `where` 的状态）。
  4. **Same-commit check.** `release-flow.sh same-commit`。
  5. **The user installs it.** （`principle-only-a-person-does-a-person-step`）。
- **来源**：`exe-release/SKILL.md` 第 1–5 步。

#### PB-14 `author-a-skill`（只在本仓库）

- **步骤**：
  1. **Place it.** 按 `docs/skill-set/SKILL-SET-RULES.md` `## Layers of the set` 决定这份内容属于哪一层。
  2. **Write it.** `writing-for-agents` 技能加 `SKILL-SET-RULES.md` 的各项检查（`principle-one-home-per-meaning`、`principle-encode-lessons-in-structure`）。
  3. **Record what it changes elsewhere.** 改了上游文本 → 写 merge-note；消费仓库的产物失效 → 写 downstream-note。
  4. **Check the wiring and the suites.** `mmw-v2/tests/lib/check_wiring.py`；只跑受影响的套件（`TESTING.md`；`shared.md` 第 15 条）。
  5. **Walk a real task.** 依据 `SKILL-SET-RULES.md` `## Verifying`。
  6. **Release.** 根 `AGENTS.md` Gotchas 的四步；有 watch 打开时，第三步等（H5）。
- **来源**：根 `AGENTS.md` `## Gotchas` 第 1 条；`SKILL-SET-RULES.md` `## Editing`、`## Verifying`；pstack `authoring-a-skill.md`。

#### PB-15 `pull-an-upstream`（只在本仓库）

- **步骤**：
  1. **Pull the subtree.** 命令见 `mmw-v2/merge-notes/README.md`。
  2. **Resolve by the merge-notes.**
  3. **For unlazy, read every listed diff and run its suite.** `bash mmw-v2/tests/verify-ticket/run.sh`。
  4. **Re-import pstack components.** 只对 `upstream-pstack`：`import_component.py --refresh`，然后读它列出的差异。
  5. **Check.** `install.sh --check`；`check_wiring.py`。
  6. **Release.** 同 `author-a-skill` 的 Release 一步。
- **来源**：`merge-notes/README.md`「上游更新时怎么用」四步；根 `AGENTS.md` 的 `<important if … upstream …>` 块。

#### PB-16 `import-a-component`（只在本仓库）

- **步骤**：
  1. **Bring the source in.** `upstream-pstack/` subtree（第 8.1 节）。
  2. **Run the importer.** `python3 mmw-v2/skills/mmw/scripts/import_component.py <playbook|principle|skill> <name>`。
  3. **Map every slot it flags.** 按第 8.3 节的五个问题，逐项核对 mode `## Slots` 是否都有映射。
  4. **Register it.** 路由行（带 Distinct from）、原则索引行，或 `skills.txt` 的 `ps/<name>`。
  5. **Check.** `check_wiring.py`；`install.sh --check`。
  6. **Release.**
- **来源**：R13 第 4 节「搬入时的判断顺序」；pstack `authoring-a-skill.md` 第 2 步「Validate the skill: frontmatter has `name` and `description`, referenced files exist, cross-skill links resolve.」

### 3.3 不设 playbook、另作归属的工作流

| 工作流 | 去处 | 理由 |
|---|---|---|
| 阶段边界（继续、清空、交接、派子代理、压缩） | 原则 `principle-decide-at-phase-boundaries` | 它是一个判断树，不是多种能力的先后顺序；跨任务，有可观察的触发（一个阶段结束），能改变一个具体决定。符合 L7 A.4 四条门槛，原则可以带一段短程序（L7 A.4） |
| 暂停并留恢复点、从旧会话接手 | 以后导入 pstack 的 `pause-safely`、`session-pickup`（第 8 节）；夜里的角色会话由 mode `## Re-entry` 承担 | MMW 今天没有白天会话的这两类原文；写一份新的就是硬塞 |
| 挂起一夜 | `run-a-night` `#### Suspending the night` | 只属于这一个 playbook（L7 A.2） |
| 收口轮、Memory 决定 | `run-a-night` 的步骤与规则簇 | 同上 |
| advisor 会话 | `advisor` 能力技能 | 它是能力技能自己用的子会话（第 2.3 节） |

---

## 4. 能力技能总目录

下表的「剥离」一列写从哪里剥离了什么、去了哪里。上游行数差来自 R14 第 4 节与 R12 M5，都是已核实的数字。

| 技能 | 升级后只剩什么 | 剥离了什么 → 去哪里 | 上游状态 |
|---|---|---|---|
| `dispatch` | 命令参考：每个动词做什么；需要判断的退出码；怎样读 `status` 表与 `where` 行；`board`；`editing-models.md` | 第 3 行 description 的「Start a reviewer from inside a ticket」→ `work-a-ticket`；`## Find your moment` → mode 路由表与 `roles.json`；`## On waking` → mode `## Re-entry`；`night.md` → `run-a-night`、`accept-the-night` 与两份共用 reference；`one-ticket.md` → `run-one-ticket`；`inside-a-ticket.md` → `work-a-ticket`；第 8 行前半句 → `principle-the-tracker-is-the-state` | 自有 |
| `verify-ticket` | 判据怎样跑、结果怎样读；事件；子票五种 kind 及其含义（`sub-issues.md` 的 kind 问题表）；lint 与发布（`linting.md` 的命令） | 第 16 行、`## Reached from here` → 删，由 mode 与 `work-a-ticket` 承担；`sub-issues.md` 第 11 行「谁在何时读」→ 各角色 playbook 的唤醒表；第 5 问「Not this kind」一列对 `implement` 的引用 → 改成自足的句子；`linting.md` 第 3 行「何时 lint」→ `define-a-change`、`run-a-night` | 自有 |
| `ui-acceptance` | 被测产品、四个 oracle、lease；五份 reference；接收来的 `writing-interface-code.md`；五条规则中的规则 1、2 | description 的「before writing a page ticket's code」→ 改为「before writing code for a page a screen-contract row covers」；第 10 行、规则 3–5 → 改成点名原则加一句本地后果；第 38 行 worker 那句 → `work-a-ticket` | 自有 |
| `shared-experience`（新） | Memory 的打开、搜索（带 `--`、只用错误加命令加组件）、保存三条件、更正；`saving-memory.md`；四种关闭决定（`retain`、`propose`、`deprecate`、`supersede`）的写法 | 来源：`implement` `## Shared experience while implementing` 第 36–68 行里的方法部分；`night.md` 第 155 行里决定写法的部分。调用方：`work-a-ticket` 第 2 步、`run-a-night` 第 5 步，以及白天任何会话 | 新拆 |
| `implement` | 上游原文 15 行，包括 `disable-model-invocation: true` 与 `agents/openai.yaml` 的 `policy` 行（两处开关一起恢复，`merge-notes/README.md` `## disable-model-invocation`） | 第 3–101 行全部 → `work-a-ticket`、原则、`shared-experience`、`ui-acceptance` | 回原文。保留安装，由用户触发：没有 MMW 文件调用它，所以不在模型列表里也没有损失 |
| `code-review` | 上游原文，即 87 行的双轴评审（Standards、Spec），模型可触发（上游原文就没有 disable 键） | `## Find your moment`、`session.md` → `review-a-ticket`；四个 axis 文件 → `mmw/references/review-a-ticket/`；第 8 行 → `principle-a-second-reader-judges` | 回原文。一项不需要票的评审能力回来了；残留 `ask-matt` 第 28 行所说的「`code-review` has no use on a branch or PR without a ticket」不再成立 |
| `tdd` | 上游原文，外加第 26 行的宿主中立改写（有 merge-note） | 第 22、38 行的票相关句 → `work-a-ticket` Write the code 一步的本地限定 | 回原文 |
| `resolving-merge-conflicts` | 上游原文，外加「clean merge 但检查变红」的扩展（能力扩展，有 merge-note） | 第 2 步「After a clean merge of `origin/<base branch>`, identify each ticket …」→ `work-a-ticket` | 只剩一类改动 |
| `grilling` | 上游原文 28 行 | 第 28 行 → `shared.md` 第 1 条加 mode `## Autonomy`；第 30–44 行 → `principle-attack-the-premise`、`principle-redesign-from-first-principles`、`principle-fix-root-causes`、`principle-laziness-protocol` | 回原文。merge-note 自己写着「上游若自己写入…删掉我们这一段」 |
| `grill-with-docs` | 上游原文（用户触发） | 第 7 行末句 → `define-a-change` | 回原文 |
| `improve-codebase-architecture` | 上游原文，外加改用 `diagram-design` 画图的能力改动（有 merge-note） | `### 4. Hand the decision on` → 路由行 Improve the architecture 与 `define-a-change` 的入口 | 只剩一类改动 |
| `codebase-design` | 上游原文，外加第 16 行术语规则的放宽 | 第 10 行的路由声明 → 删 | 只剩一类改动 |
| `triage` | 上游原文，外加调用开关：它是 mode 的路由目标，必须模型可触发（H2），保留并写 merge-note | 第 41 行的 label → `docs/agents/triage-labels.md`（本来就在那里）；第 70 行与 `references/pipeline-issues.md` → `accept-the-night`；第 82、94 行 → `triage-an-issue`；第 90 行 → `accept-the-night`；`AGENT-BRIEF.md` 里「`to-spec` reads the agent brief」→ `triage-an-issue` | 只剩调用开关 |
| `wayfinder` | 上游原文，外加宿主中立改写、调用开关 | 第 6 步 → `map-a-large-effort`；`interface-and-remake.md` → `mmw/references/map-a-large-effort/`；`mmw:map` 字面 → 由 `docs/agents/issue-tracker.md` `## Three label sets` 持有（前提是 R12 K-34 的走查通过，否则作为调用开关以外的第四类改动留下，并写明） | 回原文（有条件） |
| `prototype` | 上游原文，外加 EXP 分支（`EXP.md`、`evidence-page.md`，属于能力扩展）；规则 1 的目录约定（这项能力的产物写在哪里，按类型属于能力） | 规则 6 的「之后做什么」、`UI.md` `## Next`、第 3 步「脚手架留到第一次 pull」→ `define-a-change`、`design-an-interface`；`UI.md` 第 6 步的 `## State list` 格式 → `design-pages/references/state-list-format.md`（R12 K-14） | 只剩能力扩展 |
| `setup-matt-pocock-skills` | 上游原文，外加种子里 `--limit`/`--paginate` 的读全表修正（能力） | 第 17、51、63 行与种子里的 MMW 段 → `onboard-a-repository` 及其 reference | 回原文 |
| `writing-for-agents` | 上游原文 | 第 8 行 → 删；`SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` → `docs/skill-set/`（R12 K-38） | 回原文 |
| `to-spec` | 改为 `self/to-spec`：MMW 的 spec 能力，包括 seam、状态可达、模板扩展、`revising-a-spec.md`、`several-specs.md` 里的判断部分；第 2 步第 22 行只保留「有未对齐的行就停」这道闸门 | `## Next` → 删；拆分循环 → `define-a-change`；退回对齐票或 `Reverse sweep` 的路由 → `design-an-interface`；第 6 行 → 点名 `shared.md` 第 1 条，自己的闸门保留（L7 A.3） | 上游目录恢复原文、不再安装。依据：R4 V11「不到一半的行是上游的」；`SKILL-SET-RULES.md` 第 112 行 |
| `to-tickets` | 改为 `self/to-tickets`：切片、五问、四行判据、blocking edge、Owns；`<issue-template>`（W4 的锚点）；三份 reference | 第 20、160 行 → `define-a-change`；第 113–119 行的子代理段 → mode `## Subagents`；第 84、88 行的理由 → 点名原则（本地理由已写的保留，R12 M25） | 同上。`merge-notes/README.md` `## 本仓自有正文的技能` 本来就这样看它 |
| `design-pages` | 四个分支、模板、`state-list-format.md`、它自己的宿主闸门（第 21 行前半句） | 第 21 行「a dispatched worker never runs it」→ `work-a-ticket` `#### While writing code`；`edit-pages.md` `## Next`、`pull.md` `## Reached from here` 与 contract 子票一段 → `design-an-interface`；第 25 行按编号引用「`UI.md` step 6」→ 同技能内的 `state-list-format.md` | 自有 |
| `write-screen-contract` | 第 1–7 步、`Re-runs`、格式 | `## Next` → `design-an-interface`；第 8–10 行 → 点名原则加一句本地后果 | 自有 |
| `retro` | 第 1–13 步；`## Prevention destinations`，加三个去处 `principle`、`playbook`、`mode`（R13 E11） | 第 186 行「return to … `night.md` `## 5`」→ 删（`run-a-night` 的 Retro 一步之后就是 Hand the result）；第 16–35 行的立场 → 点名 `principle-clues-are-not-evidence`，外加本地一句；第 8 行的前置条件按类型属于能力，就位 | 自有 |
| `advisor` | 两个角色文件，description 保留自己的触发 | 无剥离。mode `## Non-negotiables` 另外点名它 | 自有 |
| `exe-release` | 引擎命令参考；`driving.md`（怎样读 `where` 的状态，属于判定怎么读）；`key.md`、`new-product.md` | 第 1–5 步的顺序与第 10 行 → `ship-a-release` | 自有 |
| `code-checkers`、`manage-agents-md` | 全部（能力内部的步骤，L7 C.3） | 第 5 步探针的理由 → 点名 `principle-silence-is-never-a-pass`；在接入流程里的先后 → `onboard-a-repository` | 自有 |
| `research`、`diagnosing-bugs`、`domain-modeling`、`grill-me`、`handoff`、`to-questionnaire`、`wait-what`、`teach`、`wizard`、`diagram-design` | 全部 | 无（R14 第 6 节：零差异，或只有宿主中立与能力改动） | 就位 |

**上游回到原文或只剩边缘改动的，共 13 个**：`implement`、`code-review`、`tdd`、`grilling`、`grill-with-docs`、`codebase-design`、`writing-for-agents`、`setup-matt-pocock-skills`、`triage`、`wayfinder`、`prototype`、`resolving-merge-conflicts`、`improve-codebase-architecture`。另外 `to-spec`、`to-tickets` 的上游目录恢复原文，但不再安装；残留的 `ask-matt` 恢复原文，本来就不安装（R4 V13）。

**上游目录今后只允许三类改动**，写进 `merge-notes/README.md`：

1. 宿主中立。
2. 调用开关：mode 或 playbook 路由到的技能必须模型可触发（H2）。
3. 带 merge-note 的能力扩展：改变这项能力本身怎么做。

流程句、原则句、配置字面都不进上游文本。

**description 的规矩**：

- 能力技能的 description 只写「是什么、在哪些情况下加载」，不写流水线位置，也不写角色。这是 `SKILL-SET-RULES.md` `### Descriptions` 第 1 条的原意，今天被 `implement`、`ui-acceptance`、`dispatch` 违反。
- 跨技能的「在 MMW 流程的某一刻用我」，写进 mode `## Non-negotiables`。

---

## 5. 原则层

### 5.1 存放与引用（H2）

- **位置**：`mmw-v2/skills/mmw/principles/principle-<slug>.md`，普通文件，不是技能。原因（H2）：pstack 的原则都带 `disable-model-invocation: true`，照搬成技能，在 Claude Code 上按名调不到；做成模型可触发的技能，24 份 description 又会进每个会话的技能列表，与「只被点名、不被调用」相反（R13 E5）。
- **文件名不用 `SKILL.md`**：宿主扫描技能目录时，不会把它们当成嵌套技能（U-3 仍做一次探针）。
- **格式**：照 pstack，已对照 `principle-attack-the-premise` 原文：
  - frontmatter `name`、`description`（`"Apply when … . <规则摘要>."`）；
  - 正文 `# <Title>`、一到三句规则、`**Why:**`、`**Pattern:**`，可选 `**Stop:**`、`**The test:**`、「Distinct from …」。
- **读取**：mode `## Principles` 索引在任务开始时读；应用哪条原则，就读哪条的全文（pstack mode 第 39 行）。
- **引用**：只按第 1.5 节的两种写法；调用方写名字，外加一句本地限定（L7 C.2「调用方可以限定原则的范围」）。
- **点名义务**：回复或无人交付物里，点名改变了决定的原则，只点名本会话读过全文的原则（pstack mode 第 15 行）。

### 5.2 MMW 自有原则（10 条）

门槛照 L7 A.4 的四条：能用短名说出口；有可观察的触发情境；能改变一个具体决定；跨任务。每条的规则都取自已有的原文，下表写出处。

| slug | 规则（取自原文） | 出处 | 引用方 |
|---|---|---|---|
| `principle-silence-is-never-a-pass` | 一道检查跑了却什么都没做，或者一个绿灯可能来自产品正确之外的原因，就是失败；查不了就说查不了；检查红了改产品，或开子票质疑来源，不改检查；新建的检查先证明它会失败（negative control） | ADR 0008 标题与第 8 行；`implement` 第 22 行；`ui-acceptance` 第 10 行；`night.md` 第 7、127 行；R14 PC1、PC2、PC22 | `work-a-ticket`、`review-a-ticket`（`unverified:`）、`run-a-night`（Closing pass）、`ui-acceptance`、`code-checkers`、`retro` |
| `principle-the-tracker-is-the-state` | 你在哪一步，由持久记录（票上的事件、tracker、提交）决定，不由会话记忆决定；续跑时读记录，不重做已做的 | `dispatch/SKILL.md` 第 8 行；`verify-ticket/SKILL.md` 第 10 行「The ticket is the only state」；`exe-release/references/driving.md` 第 5 行；pstack `session-pickup.md` 第 2 步「The prior trail is authoritative input」 | mode `## Re-entry`、`work-a-ticket`、`run-a-night`、`ship-a-release` |
| `principle-wake-dont-poll` | 谁都不轮询另一个 agent；起了别人就结束回合，由事件叫醒 | ADR 0010 标题；`night.md` 第 11 行；`implement` 第 78、84 行；`one-ticket.md` 第 8 行 | `run-a-night`、`run-one-ticket`、`work-a-ticket` |
| `principle-the-baseline-is-a-contract` | 基线是有人已经付过代价的决定；照抄，不凭记忆重写、不改进；不成立就开 `contract` 子票，从不悄悄改 | `implement` 第 22 行（唯一带理由的一处）；R14 PC8 共 15 处 | `work-a-ticket`、`design-an-interface`、`run-a-night`（`contract-authority.md`）、`design-pages`、`write-screen-contract`、`to-tickets` |
| `principle-a-second-reader-judges` | 对一件工作的判断，交给一个没写它的读者 | `code-review/SKILL.md` 第 8 行；`to-tickets` 第 63 行；`tdd` 第 38 行「judged with fresh eyes」；`consulting.md` 第 9 行 | `work-a-ticket`（Review round）、`define-a-change`（歧义扫描）、`advisor` |
| `principle-refuse-with-one-next-step` | 拒绝要点名一个事实、说明原因、给出唯一的下一步；收到拒绝就照那一步做，不即兴发挥 | ADR 0008；`SKILL-SET-RULES.md` 第 12、59 行；`night.md` 第 66 行；R14 PC3 | mode（所有会话）、`author-a-skill`。写脚本那一侧的规则留在 `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条 |
| `principle-clues-are-not-evidence` | Memory、会话自述、相近代码的事实，都是线索；结论只立在当前的仓库、tracker 与运行结果上 | `implement` 第 47–49 行；`session.md` 第 39、101 行；`retro` 第 58 行；`research` 第 10 行 | `review-a-ticket`、`retro`、`research-a-question`、`shared-experience` |
| `principle-one-home-per-meaning` | 一个意思只有一个权威的家；别处按名指向它 | `SKILL-SET-RULES.md` 事实 7 前半句；`design-pages` 第 6 行；`editing-models.md` 第 3 行 | `author-a-skill`、`import-a-component` |
| `principle-no-secret-in-an-artifact` | 密钥、令牌与私人数据不进任何产物（Memory、交接文件、报告、票） | `diagnosing-bugs` `## Redact`；`saving-memory.md` 第 4–5 行；`handoff` 第 14 行；`product-answers.md` 第 96 行 | mode `## Non-negotiables`、`shared-experience`、`fix-a-bug` |
| `principle-only-a-person-does-a-person-step` | 只有人能做的步骤单列给人，agent 不代做，也不装作做了 | `ui-acceptance` 规则 3；`person-ticket.md` 第 3 行；`wizard` description；`exe-release` 第 5 步 | `ship-a-release`、`accept-the-night`、`work-a-ticket`（ABANDON kinds） |

外加 `principle-decide-at-phase-boundaries`，第 3.3 节已述，内容取自残留 `PHASE-BOUNDARIES.md` 的五个选项与判断树。算上它，MMW 自有原则共 11 份文件；上表列的是 10 条通用判断，它单列在第 3.3 节。

**R14 的其余候选不建成 MMW 原则**，逐条理由如下：

| 候选 | 去处 | 理由 |
|---|---|---|
| PC6 协议状态只由脚本写 | mode `## Non-negotiables` 第一条，hook 强制 | 绑定具体机制（L7 C.2） |
| PC7 确定性工作交给脚本 | pstack `principle-build-the-lever`、`principle-encode-lessons-in-structure` | 已有同义原则 |
| PC9 用户只决定产品事项 | `shared.md` 第 1 条，加 mode `## Autonomy` | 用户规则已有，不复写 |
| PC10 写给冷读者 | `shared.md` 第 10 条 | 同上 |
| PC13 文件只写现状 | `shared.md` 第 13 条 | 同上 |
| PC14 最小测试集 | `shared.md` 第 15 条 | 同上 |
| PC15 只读靠文字 | mode `## Subagents` | 绑定 ADR 0015 的机制 |
| PC17 中断后原样重跑 | 设计一侧用 pstack `principle-make-operations-idempotent`；使用一侧写进 mode `## Re-entry` 第 1 步 | 已有同义原则 |
| PC18 起不来就停 | mode `## Autonomy` 与 `shared.md` 第 11 条的划界句 | 它是一条优先级，不是新判断 |
| PC24 只做被要求的 | `shared.md` 第 1 条，加 `principle-laziness-protocol` | 已有 |
| PC25 两次独立发生才建防线 | pstack `principle-encode-lessons-in-structure`；「两次」这个门槛留在 `retro` | 参数属于领域（L7 C.2） |
| PC27 用领域词 | `shared.md` 第 6、8 条；各上游技能里「read `CONTEXT.md`」是上游原文 | 已有 |

### 5.3 承接 pstack 原则

| pstack 原则 | 接住的 MMW 规则（R14 第 3.2 节） | 搬入后 MMW 调用方写什么 |
|---|---|---|
| `principle-prove-it-works` | PC1、PC2、PC14 的一部分 | 名字，外加「在票里，真实产物就是 `verify-ticket.py` 在 `HEAD` 上的运行」 |
| `principle-encode-lessons-in-structure`、`principle-build-the-lever` | PC7、PC25 | 名字 |
| `principle-make-operations-idempotent` | PC17 | 名字 |
| `principle-separate-before-serializing-shared-state` | PC12 | 名字，外加 Owns 的领域规则（留在 `to-tickets`、`work-a-ticket`） |
| `principle-attack-the-premise`、`principle-redesign-from-first-principles`、`principle-fix-root-causes` | PC19 | 名字 |
| `principle-subtract-before-you-add`、`principle-laziness-protocol`、`principle-migrate-callers-then-delete-legacy-apis` | PC21 | 名字 |
| `principle-test-behavior-not-implementation` | PC23 | 名字；做法留在 `tdd` |
| `principle-guard-the-context-window` | PC26 | 名字 |
| `principle-never-block-on-the-human` | PC9 在执行一侧的部分 | 名字。与 `shared.md` 冲突时以 `shared.md` 为准，这一句写在 mode `## Autonomy` 的优先级句里 |

共 14 条。它们的正文从 pstack 原文逐字搬入（MIT 许可，`LICENSE` 保留在 subtree 里），唯一的改动是导入脚本的机械改写：

- 原则之间的相对链接 `../principle-x/SKILL.md` → `principle-x.md`（已核实：`principle-build-the-lever`、`principle-attack-the-premise` 有这种链接）；
- `principle-prove-it-works` 里的「**show-me-your-work** skill」映射到 audit-trail 槽位（第 8.2 节）。

**重合时怎么办**：

- 同一判断，MMW 与 pstack 都有：用 pstack 的原则文件，MMW 的具体化写在调用方的限定句里（L7 C.2）。
- 部分重合：MMW 原则写一句「Distinct from `principle-x`」划界（例：`principle-silence-is-never-a-pass` Distinct from `principle-prove-it-works`：一个管检查本身会不会失败，一个管有没有在真实产物上核对）。
- 冲突：按 mode `## Autonomy` 的优先级句处理，不改原则原文。pstack 自己也缺这一句，见 L7 E.1 第 30 条的例子（mode `## Autonomy` 放宽了 `never-block-on-the-human`）。
- 以后再搬入的原则：一个文件加索引一行；导入脚本拒绝同名。

**是否现在就搬入这 14 条**：这是 D1，由用户决定。原因是它把外来的规则文字放进每个会话的纪律里。如果不搬，第 1 批里这些规则的调用方先保留今天的本地句子，第 4 批再换成名字。

### 5.4 与 `mmw-v2/prompt/shared.md` 的关系

- `shared.md` 是用户写给所有项目、所有会话的全局规则，由 Claude Code、Codex、Pi、Grok 读取；Cursor 的副本由用户在应用里维护（根 `AGENTS.md` `## Key Conventions`）。MMW 不改写它。
- **划界**：`shared.md` 管「谁决定什么、怎么汇报、怎么工作」；mode 管 MMW 独有的触发、无人会话的出口、重入；原则层管跨任务的工程判断。
- **引用**：原则索引的「User rules」一段只写规则号和适用时机。调用方写「`shared.md` rule 10」，外加一句本地限定。技能里今天的翻版（R14 第 5.5 节；N9 D1、D4、D5、D6、D16、D17）改成点名规则号。
- **优先级**：`shared.md` 最高（mode `## Autonomy` 第一句）。

---

## 6. 执行协议

**白天、有人在场**：mode `## Playbooks` 首段照抄 pstack mode 第 117 行的写法：

> Open a todolist whose first items are the matched playbook's steps (their titles), copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`.

- 只有编号步骤进 todo，规则簇不进（L7 D.1）。
- 回复点名改变了决定的原则。
- 宿主是否都有 todo 工具，见 U-4。没有 todo 工具的宿主，在回复开头列出步骤标题和 skip 行。

**夜里、无人**（H6）：todo 屏幕没人看，会话压缩后 todo 可能丢失，早上的读者读的是票。所以：

| 角色 | skip 行与原则点名写在哪里 | 依据 |
|---|---|---|
| worker | closing comment 的 `Decisions I made on my own` 下，每行写 `skip: <step title>: <reason>`；原则名写在决定行里 | `implement` 第 23 行已有这一段；`verify-ticket.py` 第 1551 行的 draft 骨架含这一节（U-12 确认 `--closeout` 接受这种行） |
| reviewer | 报告末尾，在各 axis 汇总行之后 | `session.md` 第 91 行（报告格式） |
| orchestrator | spec 上的一条评论 | `night.md` 第 5 行「leaves its reason where that reader will look」 |

- 这不新增格式。票上的事件就是 pstack `show-me-your-work` 的等价物（R13 E7）。
- 收尾各步由机器保证不漏：`resume_at` 按事件算出做到哪一步，`--closeout` 核验 final run。skip 只涉及收尾之前的步骤。
- 能不能用 lint 检查「每个步骤标题都出现在 todo 或 skip 里」，属于推断；本轮不建这项检查（`SKILL-SET-RULES.md` `## Editing`：加机制要指名它会阻止的那次失败，目前没有）。

---

## 7. 脚本与 hook

### 7.1 数据：`mmw/roles.json`

```json
{
  "worker":              {"playbook": "work-a-ticket",  "models_row": ["junior-worker", "senior-worker"],
                          "started_by": "dispatch.sh start <n> worker", "wake_step": "When something wakes you"},
  "reviewer":            {"playbook": "review-a-ticket", "models_row": ["reviewer"],
                          "started_by": "dispatch.sh start <n> reviewer"},
  "night-orchestrator":  {"playbook": "run-a-night",     "started_by": "dispatch.sh open <spec>",
                          "wake_step": "Handle each wake"},
  "ticket-orchestrator": {"playbook": "run-one-ticket",  "started_by": "dispatch.sh open-ticket <n>",
                          "wake_step": "Handle each wake"},
  "advisor":             {"skill": "advisor",           "models_row": ["advisor"], "started_by": "dispatch.sh advise <file>"}
}
```

- 它是角色定义这一层（Memory `8ec53374`）。
- 脚本从已安装的 checkout 读它（`dispatch.sh` 按 `$SKILL_ROOT/../mmw/roles.json` 找，与它今天找 `verify-ticket` 的方法相同，见第 91–94 行注释），所以 watch 期间是冻结的版本（H5）。
- 这是本架构对 pstack「脚本不往上调用任何东西」（L7 B.2 硬规律第 2 条）的有意偏离。脚本要把被压缩、被唤醒的会话送回某一步，在 H4（一行）和 H6（没人能重新指路）之下，没有别的办法。偏离收在一处：脚本只读这份数据文件，只打印 `mmw <slug>#<title>` 这种字面，不含 playbook 的任何文字；由 lint 第 1、6 类核对。

### 7.2 要改的脚本

| 脚本 | 改什么 | 为什么 |
|---|---|---|
| `dispatch.sh` 第 108–109 行 | 删掉 `AUTONOMOUS`、`PRODUCT_RULES` 两个常量 | 规则的家是 mode `## Autonomy` 与 mode 的触发行；启动提示词只放数据（`SKILL-SET-RULES.md` `### Prompts written for other agents` 第 2 条）。已核实没有测试钉这两句（R12 M19） |
| `dispatch.sh` 第 1949、1967 行 | 启动提示词第一行改为 `Use the mmw skill. You are the <role> of ticket #<n>[ from base commit <c>]: playbook <slug>. Unattended.`，取值来自 `roles.json`；Memory 索引与 Rules 包照旧跟在后面 | W2：提示词的形状和接收方的入口在同一次提交里改；`test_dispatch.sh` 第 2830、6984、7199 行随之改（R12 M19） |
| `dispatch.sh` 第 1740 行 Memory 索引的尾句 | 改为「the `shared-experience` skill says how to use them」 | 那一节搬走了 |
| `dispatch.sh` 第 79 行头注释 | 改为指向 mode `## Re-entry` | 同上 |
| `dispatch.sh` `open`、`open-ticket` 打印的那一行 | 行末加 `· mmw run-a-night#Handle each wake`（单票用 `run-one-ticket`） | 人启动的会话在这一刻成为 orchestrator |
| `dispatch.sh` 新动词 `where` | 用 `self` 取当前会话的 runner 与会话号，再与票上 `*.started` 事件里的会话、以及 `watches.json` 里的 orchestrator 比对，打印一行 `ROLE: <role> #<n> · PLAYBOOK: <slug> · RESUME: <title>`；没有角色就打印 `ROLE: none` | 被压缩的会话不必记住自己是谁（`principle-the-tracker-is-the-state`）。可行性依据：`self` 动词已存在（`dispatch.sh` 头注释），relay 能区分 watch（R4 V3）。R12 K-3 已定 `status` 可以算出 `RESUME:`。能否认出会话见 U-14 |
| `dispatch.sh status` | 首行打印 `RESUME: <run-a-night step title>` | R12 K-3 |
| `dispatch.sh` 第 2344–2360 行 | `--check` 失败时，从「自动跑完整 `install.sh`」改为「只报告」，或者改根 `AGENTS.md` 的规则 | 与「`install.sh` runs only when the user explicitly authorises it」冲突（R12 M7）。这是用户定的规则，改哪一边由用户决定（D2） |
| `relay.py` 第 385–389 行 `wake_text` | 同一行末尾加 ` · mmw <slug>#<wake_step>`，slug 按收件角色与 watch 类型从 `roles.json` 取 | H4（R12 K-1、M1）。`ack` 不解析唤醒文字，不受影响（R4 V4）。`test_relay.py` 里断言整条文字完全相等的那些断言同一次提交改（R4 V5） |
| `watchdog.py` 第 735、780 行等 | 「as night.md's Exit codes of resume says」改为 `mmw run-a-night#Handle each wake`；八种告警都带指针，仍是一行 | R4 V2；H4 |
| `turn-guard.py` 第 306–311 行 | 消息末尾加指针；命令照旧 | R4 V7 |
| `tool-guard.py` 第 76–80 行 `NO_QUESTION` | 改为「Nobody is at the screen: the mmw skill's ## Autonomy, and your playbook's Unattended outlets.」，含前缀约 110 字符，在 256 上限内 | 修掉 R4 V9；覆盖 worker、reviewer（R14 第 9 节第 2 条）；`test_tool_guard.py` 第 440–450 行随之改（R12 M2）。字符数是推断，写的时候量 |
| `tool-guard.py` 第 71–75 行 `REFUSAL` | 加一句指向 `mmw work-a-ticket#Close out` | 拒绝要给唯一的下一步（`principle-refuse-with-one-next-step`） |
| `verify-ticket.py` 第 2148–2182 行 `resume_at` | 返回步骤标题，不返回编号；修正 docstring | W3；R4 V10；R14 第 9 节第 1 条。`test_preflight.py` 第 463–517 行随之改 |
| `retro.py` 第 31–32 行 `DESTINATIONS` | 加 `principle`、`playbook`、`mode` | R13 E11：教训要能落到对的那一层 |
| `models.py` | 新增只读子命令 `config role <label>`：从 `roles.json` 与 `models.json` 查出一个角色当前的宿主、模型、档位 | 让导入组件里「your configured <role> model」有值可查（R13 I-5） |
| `install.sh` | 装 `self/mmw`、`self/shared-experience`、`self/to-spec`、`self/to-tickets`；认 `ps/` 前缀（`upstream-pstack/skills/`）；注册 `mode_hook.py`；`--check` 另外核对 playbook 点名的每个技能都已安装，并列出开着的 watch 与活着的 relay、watchdog 锁（R12 K-32） | R13 E10 安装侧的一半；H5 |

### 7.3 新增的 hook：`mmw/scripts/mode_hook.py`

- **事件**：
  - prompt 提交时（Claude Code 与 Codex 的 `UserPromptSubmit`，后者见 `install.sh` 第 768–774 行 `CODEX_LABELS`）：只在 MMW 仓库打印一行提醒。
  - 会话开始、被压缩后（Codex 的 `SessionStart`、`PostCompact`；Claude Code 的 `SessionStart`，推断）：跑 `dispatch.sh where`，打印那一行。
  - 其余宿主见 U-2。
- **失败处理**：失败时不输出、退出 0。它是加载 mode 的辅助路径；主路径是启动提示词和唤醒指针。所以它失败不违反 ADR 0008（ADR 0008 管的是闸口，这不是闸口）。这一点写在脚本头注释里。
- **注册方式**：与 `turn-guard.py` 相同（`install.sh` 第 314 行注释所述的五个宿主各自的配置）。判断「是不是 Cursor 在调用」按 payload 字段，不按环境变量（根 `AGENTS.md` Gotchas 第 4 条）。

### 7.4 连线 lint：`mmw-v2/tests/lib/check_wiring.py`

它与 `check_module_paths.py` 同类，每个套件先跑。它做的是 pstack 缺的那一环（L7 E.1 第 2、17、27 条），依据是 pstack 自己的 `principle-encode-lessons-in-structure`。

| 类 | 核对什么 |
|---|---|
| 1 | 每个指针字面 `mmw <slug>#<title>`（在脚本、文本、`roles.json` 里）都能对到 playbook 里一个带粗体标题的步骤或 `####` 小节 |
| 2 | 每份 playbook、mode 点名的技能都在 `skills.txt` 里；点名的 reference 与脚本文件都存在 |
| 3 | 能力技能文本里不出现：`## Next`、`## Reached from here`、「return to」后接技能名、任何 playbook slug、按编号引用别的文件里的步骤（如 `step \d`、`closing step`） |
| 4 | 原则引用只用两种写法，目标文件都存在 |
| 5 | mode 原则索引与 `principles/` 一一对应，每行的「何时适用」等于该原则 description 的第一句 |
| 6 | `roles.json` ↔ playbook 文件 ↔ `relay.py` `WAKES` 加 `worker.queued`、`relay.recovered` ↔ `watchdog.py` 的告警前缀 ↔ `MMW turn guard:`：每个（角色，事件）在那个角色的 playbook 里恰好有一个处理行（R12 K-30） |
| 7 | playbook 骨架：`### <Name>`、所有权行、带粗体标题的编号步骤、`**Reply:**`；每一步至少点名一个组件（技能、原则、脚本命令、playbook），或标 `(judgement)` |
| 8 | 路由表：每份 playbook 恰好一行；每行的目标存在 |
| 9 | `imports.tsv` 的每个来源文件存在；导入文件里没有未映射的槽位关键词（第 8.3 节） |
| `--graph` | 打印一张由这些数据生成的连线总图，回应用户在 Memory `ce037679` 里要的「一张与实际同步的总图」 |

第 3 类的判定是字面规则，不判断语义；角色名（worker、orchestrator）作为领域词可以出现在能力技能里，比如 `open` 会把调用它的会话记为 orchestrator。所以第 3 类只查「下一步」「谁调用我」这两种句型。

第 0 批先以只报告的方式运行，列出今天的违例；第 3 批起改为不通过就失败。

---

## 8. pstack 导入接口

### 8.1 来源与安装

- 以 subtree 引入到 `mmw-v2/upstream-pstack/`，与其他三个上游相同（根 `AGENTS.md` `## Key Conventions`）。
- pstack 在 `cursor/plugins` 仓库的 `pstack/` 子目录里。`git subtree add` 取的是整个仓库，所以先在一个临时克隆里对 `pstack/` 做 `git subtree split`，再对分出的分支做 `subtree add`。这是推断，见 U-13。
- 命令与所用的提交记进 `merge-notes/pstack.md`。
- 用户偏好是不锁版本、积极升级（Memory「不锁版本，积极升级」），所以 `pull-an-upstream` 定期拉取。
- 安装与落位：
  - 能力技能：`skills.txt` 加 `ps/<name>`，`install.sh` 从 `upstream-pstack/skills/<name>` 装软链。
  - playbook 与原则：由 `import_component.py` 复制进 `mmw/playbooks/`、`mmw/principles/`，并在 `imports.tsv` 记下来源路径与来源提交。
  - 为什么复制而不用软链：pstack 文件里的相对链接按读者打开的路径来解析，软链会让它们指错。拉取更新后跑 `import_component.py --refresh`，列出差异。

### 8.2 mode `## Slots`：导入组件依赖的东西在 MMW 对应成什么

| 槽位 | pstack 里怎么写（出处） | MMW 对应 |
|---|---|---|
| control | 「the matching control skill」；`cursor-team-kit` 的 `control-ui`、`control-cli`（mode 第 30 行；`bug-fix.md` 第 1 步） | 浏览器与 Web 界面 → `playwright-cli`，或 `ui-acceptance` 的 story、journey；Orca 内置浏览器 → `orca-cli`；本机原生窗口 → `computer-use`；CLI → 直接跑命令。消费仓库可以在 `.mmw/target.json` 覆盖。找不到对应就停，并说出缺什么（`principle-silence-is-never-a-pass`） |
| delivery | 「Run **Opening a PR**」（7 个 playbook 的最后一步，L7 E.1 第 3 条） | 在票里：closeout，由 orchestrator 落地（`implement` 第 99 行；ADR 0025）。白天在本仓库：根 `AGENTS.md` Gotchas 的四步发布。在用 PR 的仓库：原样用 pstack 的 opening-a-pr。babysit、shipping、autopilot 只在用 PR 的仓库路由，路由行写明这个条件 |
| forge | `gh` 默认，`command -v origin` 探测（6 个 playbook 各一份，L7 A.2） | `docs/agents/issue-tracker.md`，一处 |
| audit trail | 「the **show-me-your-work** skill」（mode 第 35 行；`principle-prove-it-works`） | 在票里：票上的事件与 `Decisions I made on my own`；白天：在导入 `show-me-your-work` 之前，写在回复里 |
| subagent type | `subagent_type: "poteto-agent"`（mode 第 91 行） | 宿主的通用子代理，加 `references/subagent-brief.md` |
| model role | 「your configured <role> model (default …)」（`how` Step 2a） | 会话内的角色：跑在本会话的模型上（H3）。另起会话的角色：`models.py config role <label>` |
| panel role | `arena runners`、`architect runners`、`interrogate reviewers`（`setup-pstack` 第 3 步 (c)） | 第 8.4 节；建好之前，退化为同一模型的面板，并在回复里写明 |
| transcript | `~/.cursor/projects/<slug>/agent-transcripts/`（`session-pickup.md` 第 1 步） | 每个宿主一份 reference 变体，照 pstack `why/references/sources/*.md` 的做法；Nowledge Mem 的会话记录作为一个来源。未核实，见 U-8 |
| host tools | `AskQuestion`、`/loop`、`/goal`、cloud agent、`create-skill`、`readonly`（L7 E.2） | `AskQuestion` → 有人时在对话里问（`shared.md` 第 1 条），无人时走角色出口；`/loop`、`/goal` → 夜里用 relay 与 watchdog，白天用宿主自带的循环（如有，U-4）；cloud agent → `dispatch.sh start` 那种另起的会话；`create-skill` → `writing-for-agents` 加 `author-a-skill`；`readonly` → 简报里一句「You are read-only」（ADR 0015） |
| reply style | 「No long-dash character anywhere」「A colon as a mid-sentence connector is also out」（mode 第 102–103 行） | 给用户的回复以 `shared.md` 为准；其他产物按导入技能自己的规则（R13 I-16） |
| 运行中从 trunk 重读 | `autopilot-full.md` 第 6 步；`multi-phase-plan.md` 模板（L7 B.1） | 禁止（H5）。导入时删掉这一句，并写 merge-note |

### 8.3 `import_component.py`：只做机械的事

**它做的**：

1. 复制文件。
2. 改写原则之间的链接。
3. 能力技能：去掉 `disable-model-invocation`（H2；路由到它的技能必须模型可触发）。pstack 的 `bro`、`teach` 这类只该由用户触发的技能，按 `imports.tsv` 里一列「user-invoked」保留这个键。
4. 扫出槽位关键词（control skill、Opening a PR、`gh`/`origin`、`subagent_type`、configured … model、`AskQuestion`、`/loop`、`/goal`、cloud、`git show origin/main:`），打印成待办清单；有未映射的，退出码非 0。
5. 拒绝同名。

**它不做的**：改写需要判断的句子。这些由跑 `import-a-component` 的 agent 按第 8.2 节去改，并写 merge-note（L7 C.1 第 1 问：需要判断的留在文字里）。

**搬入前的五问**：

1. 它依赖的每个槽位在 mode 里都有映射吗？
2. 它依赖 PR 吗？依赖的话，只在用 PR 的仓库路由到它。
3. 它依赖跨厂商的面板吗？依赖的话，第 8.4 节的脚本在不在？不在，就在路由行写明降级。
4. 它运行中会从 trunk 重读自己吗？会的话，删掉那一句（H5）。
5. 改写完，lint 与 `install.sh --check` 都通过吗？

### 8.4 多模型面板（H3）

- **原因**：子代理不能换厂商（H3；ADR 0015 `## Consequences`）。所以一个跨厂商的面板只能是多个另起的会话。
- **设计**：`dispatch.sh panel <panel-role> <brief>`。
  - 按 `models.json` 里这个面板角色的列表，每一项另起一个会话。起会话的方法照 `advise_one`（`dispatch.sh` 第 2053–2080 行），提示词是「Use the advisor skill.」加简报，外加答案文件的路径。
  - 每个成员把答案写到 `~/.mmw/state/<repo>/panels/<id>/<member>.md`。
  - `dispatch.sh panel-wait <id>` 一直等到文件数等于成员数才返回。「一条会阻塞到对方完成的命令」是 `SKILL-SET-RULES.md` `### Hand-offs` 第 3 条认可的完成信号。
- **与 advisor 规则的关系**：`advising.md` 规定 advisor「writing nothing」。面板成员要写答案文件，这是例外，需要在 `advisor` 能力里写明。
- **何时建**：第一版不建。真正要搬入 `arena`、`architect`、`interrogate` 时再建，按 U-6 实测耗时与费用。

---

## 9. 改造前后对照表（N1–N10 的每个部件）

**动作的写法**：

- 搬：整块移到另一层。
- 拆：分成几块，分别去不同的层。
- 改：原地改写内容。
- 删：去掉。
- 回原文：恢复上游文本。
- 就位：按类型本来就在这一层，内容可能改，位置不动。不属于「留在原处」。
- 留（Hx）：按类型本该搬走，因为硬约束 Hx 留下。

### 9.1 N1 `dispatch`

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `SKILL.md` description | 能力 → 同处 | 改：写命令行的各项工作，删「Start a reviewer from inside a ticket」 |
| `SKILL.md` 第 8 行 | 前半句 → `principle-the-tracker-is-the-state`；后半句（脚本自己找路径）→ 能力 | 拆 |
| `## Find your moment` | 第 1、2 行 → `roles.json` 与 `work-a-ticket`；第 3、4 行 → mode 路由表；第 5、6 行 → 能力正文 | 拆、删表 |
| `## On waking` | mode `## Re-entry` | 搬 |
| `references/night.md` | `playbooks/run-a-night.md`、`accept-the-night.md`、`references/contract-authority.md`、`references/watchdog-alerts.md`；第 3–7 行 → 点名原则 | 拆、搬 |
| `references/one-ticket.md` | `playbooks/run-one-ticket.md` | 搬 |
| `references/inside-a-ticket.md` | `work-a-ticket` `#### Picked up yourself` | 搬 |
| `references/editing-models.md` | 能力（改配置是用户会直接调用的能力） | 就位 |
| `hosts.json` | 配置 | 就位 |
| `scripts/dispatch.sh` | 能力脚本（第 1.5 节的判据） | 就位；改（第 7.2 节） |
| `relay.py` | 能力脚本；唤醒文字的格式 | 就位；改：唤醒同一行带指针。唤醒必须是一行：留（H4） |
| `watchdog.py` | 能力脚本 | 就位；改：指针。告警必须是一行：留（H4） |
| `turn-guard.py`、`tool-guard.py` | hook 脚本（宿主来调用；ADR 0021） | 就位；改文字 |
| `status.py`、`statedir.py`、`ghlist.py`、`runners/*.sh` | 能力脚本 | 就位；`status.py` 加 `RESUME:` |
| `models.py` | 能力脚本 | 就位；加 `config role` |
| `docs/contexts/night/CONTEXT.md`、`how-it-works.md` | 仓库文档 | 就位；加词条、改 `_Home_` |
| ADR 0009、0010、0016–0018、0020–0025、0027 | 仓库文档 | 就位；新 ADR 0033 修订 0020 |

### 9.2 N2 `verify-ticket`

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `SKILL.md` 第 8–12 行 | 能力 | 就位；第 10 行改为点名 `principle-the-tracker-is-the-state` |
| 第 16 行、`## Find your moment`、`## Reached from here` | mode 与 playbook | 删 |
| `references/linting.md` | 命令 → 能力；第 3 行「何时 lint」→ `define-a-change`、`run-a-night` | 拆 |
| `references/sub-issues.md` | 命令与 kind 问题 → 能力；第 11 行 → 各角色 playbook 的唤醒表；第 5 问「Not this kind」一列改成自足的句子 | 拆 |
| `verify-ticket.py` | 能力脚本 | 就位；改 `resume_at` |
| `events.py`、`issue_tree.py`、gate-check 符号链接 | 能力脚本 | 就位 |
| `upstream-unlazy/` | 外来组件（判定引擎） | 就位 |
| `merge-notes/unlazy.md` | 仓库文档 | 就位 |
| `docs/contexts/ticket-run`、`tickets` | 仓库文档 | 就位；改 `_Home_` |

### 9.3 N3 `implement`、`code-review`、`tdd`

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `implement/SKILL.md` 第 1–101 行 | `work-a-ticket`、原则、`shared-experience`、`ui-acceptance` | 拆、搬；技能回原文 |
| `implement/references/writing-interface-code.md` | `ui-acceptance/references/` | 搬；三处「closing step 1」改成指针 |
| `implement/references/saving-memory.md` | `shared-experience/references/` | 搬 |
| `implement/agents/openai.yaml` | 外来组件 | 回原文（恢复 `policy` 行） |
| `code-review/SKILL.md` | 外来组件 | 回原文 |
| `code-review/references/session.md` | `review-a-ticket`；第 23–33 行 → mode `## Subagents` | 搬、拆 |
| 四个 axis 文件 | `mmw/references/review-a-ticket/` | 搬 |
| `code-review/agents/openai.yaml` | 外来组件 | 回原文 |
| `tdd/SKILL.md` | 第 22、38 行 → `work-a-ticket`；其余是外来组件 | 拆、回原文（第 26 行宿主中立保留） |
| `tdd/tests.md`、`mocking.md` | 外来组件 | 就位 |
| `merge-notes/implement.md`、`code-review.md` | 仓库文档 | 删，只剩开关一句，并入 README；`tdd.md` 缩短 |

### 9.4 N4 `to-spec`、`to-tickets`、`triage`

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `to-spec/SKILL.md` | `mmw-v2/skills/to-spec/`（能力）；`## Next`、拆分循环 → `define-a-change`；第 2 步的路由 → `design-an-interface` | 搬、拆；上游目录回原文 |
| `revising-a-spec.md`、`several-specs.md` 的判断部分 | 随 fork 走（能力） | 搬 |
| `to-tickets/SKILL.md` | `mmw-v2/skills/to-tickets/`；第 20、160 行 → `define-a-change`；第 113–119 行 → mode `## Subagents` | 搬、拆；上游目录回原文 |
| `ambiguity-scan.md`、`cutting-interface-tickets.md`、`person-ticket.md` | 随 fork 走 | 搬 |
| 各 fork 的 `agents/openai.yaml` | 删（R12 K-20：自有技能不带它） | 删 |
| `triage/SKILL.md` | 第 70、82、90、94 行 → `accept-the-night`、`triage-an-issue`；其余 → 外来组件 | 拆、回原文，只剩调用开关 |
| `triage/references/pipeline-issues.md` | `mmw/references/accept-the-night/` | 搬 |
| `triage/AGENT-BRIEF.md` 的本仓改动 | `triage-an-issue` | 拆、回原文 |
| `triage/OUT-OF-SCOPE.md` | 外来组件 | 就位 |
| `docs/agents/issue-tracker.md` | 配置（消费仓库的私有组件）；`## Morning queries` 里「先跑 triage」的顺序 → `accept-the-night` | 就位；查询命令留在文件里 |
| `docs/agents/triage-labels.md`、`domain.md` | 配置 | 就位 |
| `docs/contexts/tickets/CONTEXT.md` | 仓库文档 | 就位 |
| `merge-notes/to-spec.md`、`to-tickets.md` | 仓库文档 | 删（改在 README 的「已分出的技能」一节记一行）；`triage.md` 缩短 |

### 9.5 N5 其他上游技能

| 技能 | 动作 |
|---|---|
| `research`、`diagnosing-bugs`、`domain-modeling` | 就位（零差异） |
| `grill-me`、`handoff` | 就位（只有宿主中立） |
| `codebase-design` | 删第 10 行，其余就位 |
| `wizard`、`to-questionnaire`、`teach`、`wait-what` 与 `VISUAL.md` | 就位（能力改动与调用开关，merge-note 保留） |
| `resolving-merge-conflicts` | 拆：第 2 步的票相关句 → `work-a-ticket` |
| `grilling` | 拆：第 28–44 行 → 原则；回原文 |
| `grill-with-docs` | 拆：第 7 行末句 → `define-a-change`；回原文 |
| `improve-codebase-architecture` | 拆：`### 4` → 路由表与 `define-a-change`；画图改动就位 |
| `setup-matt-pocock-skills` 与种子 | 拆：MMW 段 → `onboard-a-repository`；回原文 |
| `prototype`（`EXP.md`、`evidence-page.md`、`UI.md`、`LOGIC.md`） | 拆：流程句 → playbook；`## State list` → `design-pages`；EXP 分支就位 |
| `wayfinder` 与 `interface-and-remake.md` | 拆：第 6 步 → `map-a-large-effort`；reference → `mmw/references/map-a-large-effort/`；回原文（`mmw:map` 视走查结果） |
| `writing-for-agents` 与 SSR、RSS | 拆：SSR、RSS → `docs/skill-set/`；回原文 |
| `ask-matt`（未安装） | 回原文；内容 → mode 路由表、`define-a-change`、`fix-a-bug`、`triage-an-issue`、`principle-decide-at-phase-boundaries` |
| `SKILL-MECHANICS.md`、`upstream/.agents/invocation.md` | 外来组件，就位 |

### 9.6 N6 界面链

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `ui-acceptance/SKILL.md` | 能力；第 10 行与规则 3–5 → 点名原则；第 38 行 → `work-a-ticket`；表第 1 行 → 本技能自己的 reference | 改、拆 |
| 五份 reference、九个脚本 | 能力 | 就位 |
| `design-pages/SKILL.md` | 能力；第 21 行后半句 → `work-a-ticket`；`## The state list` → `references/state-list-format.md` | 改、拆 |
| `edit-pages.md` `## Next`；`pull.md` `## Reached from here` 与 contract 子票一段 | `design-an-interface` | 搬 |
| `draw.md`、`design-system.md`、两份模板、`pull_design.py`、`check_editable_selectors.py` | 能力 | 就位 |
| `write-screen-contract/SKILL.md` `## Next`、第 8–10 行 | `design-an-interface`；原则 | 拆 |
| `write-screen-contract` 其余、`screen-contract-format.md`、三个脚本 | 能力 | 就位 |
| `docs/contexts/ui-acceptance/CONTEXT.md`、ADR 0011、0028–0030 | 仓库文档 | 就位 |

### 9.7 N7 独立技能

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `retro/SKILL.md` 第 186 行 | 删 | 删 |
| `retro` 第 16–35 行 | 点名原则，外加本地一句 | 改 |
| `retro` 其余、`retro.py` | 能力 | 就位；`DESTINATIONS` 加三项 |
| `advisor` 三份文件 | 能力 | 就位 |
| `exe-release/SKILL.md` 第 1–5 步、第 10 行 | `ship-a-release` | 搬 |
| `exe-release` 的 `driving.md`、`key.md`、`new-product.md`、脚本 | 能力 | 就位 |
| `code-checkers`、`manage-agents-md` | 能力 | 就位；理由句改为点名原则 |
| `diagram-design` | 外来组件 | 就位 |

### 9.8 N8 底座

| 部件 | 层 → 位置 | 动作 |
|---|---|---|
| `prompt/shared.md` | 用户所有（任务明令不改写） | 就位；原则索引按规则号引用它 |
| `prompt/hosts/*.md`、`render.py`、`README.md`、`tests/` | 仓库文档与安装 | 就位 |
| `skills.txt` | 配置 | 改：加四个 `self/`、`ps/` 前缀；去掉 `engineering/to-spec`、`engineering/to-tickets` |
| `install.sh` | 安装 | 改（第 7.2 节） |
| `~/.mmw/models.json` | 配置 | 就位；以后加面板角色 |
| `board/*` | 任务板产品，不属于 MMW 的层 | 就位 |
| `migrations/remove-verifier.py` | 一次性迁移 | 就位 |
| `tests/<name>/run.sh`、`tests/lib/*` | 测试 | 就位；加 `check_wiring.py` 与 `tests/mmw/` |
| 根 `AGENTS.md` | 仓库文档；Gotchas 第 1 条的发布四步 → `author-a-skill`（`AGENTS.md` 保留指针与 H5 那一句）；upstream 的 `<important if>` 块 → `pull-an-upstream` | 拆 |
| `CODING_STANDARDS.md` | 仓库文档；跨任务的立场改为点名原则 | 改 |
| `TESTING.md` | 仓库文档 | 就位 |
| `merge-notes/README.md` | 仓库文档 | 改：三类改动的规矩、已分出的技能、pstack 一节、`disable-model-invocation` 名单加 `implement` |
| `downstream-notes/` | 仓库文档 | 就位；启动提示词改名若影响消费仓库，按规定补一份（U-15） |

### 9.9 N9 ADR、词表、原则候选

| 部件 | 动作 |
|---|---|
| 31 份 ADR、`docs/adr/README.md` | 就位；新增 0032、0033、0034，更新索引 |
| `CONTEXT-MAP.md`、七份 `CONTEXT.md` | 就位；toolbox 加 mode、playbook、principle、role、slot，night 加 role pointer、where line |
| PC1–PC29 | 按第 5 节去 MMW 原则、pstack 原则、`shared.md` 规则号、mode 各节 |

### 9.10 N10 路由机制

| 部件 | 动作 |
|---|---|
| 35 份 frontmatter | 改：能力技能的 description 删流水线位置；回原文的恢复上游 description 与开关 |
| 24 份 `openai.yaml` | 随 frontmatter 成对改（`merge-notes/README.md` 的配对规则） |
| `## Find your moment` 五张表 | `dispatch`、`verify-ticket`、`code-review` 三张删；`design-pages`、`ui-acceptance` 两张是能力内部的分支，就位 |
| `advisor` 的两行表、`manage-agents-md` 的表、`prototype` 的 `## Pick a branch` | 就位（能力内部的分支） |
| 17 句「下一步」 | 全部删，内容进 playbook |
| `night.md` 的事实表 | `run-a-night` 的 `**Where you are.**` 加 `status` 的 `RESUME:` |
| `dispatch.sh` 的提示词常量与三条启动提示词 | 第 7.2 节 |
| `relay.py` `WAKES`、`wake_text`；`watchdog.py` 的告警；`turn-guard.py` 的消息 | 第 7.2 节 |
| SSR 事实 7、`### Hand-offs` 第 5 条 | 改（搬到 `docs/skill-set/` 之后）：「一个技能的位置由 playbook 与 mode 路由表决定；能力技能以交回什么结尾」 |
| 残留 `ask-matt` | 回原文 |

**本表里的「留（Hx）」只有两处**：`relay.py` 的唤醒文字、`watchdog.py` 的告警文字都必须保持一行（H4）。它们的内容照改，只是格式受 H4 约束。

---

## 10. 迁移批次（H5 下分批落地）

**每批都遵守的规矩**：

- 在开发 checkout 上完成。
- 测试只在隔离的 home 里、对假的 tracker、runner、仓库跑（根 `AGENTS.md` `## Self-hosting boundary`；`TESTING.md`）。
- 只有在没有 watch 打开、没有旧版本的 relay 与 watchdog 进程时（第 7.2 节 `install.sh --check`），才执行四步提升的第三步：移动已安装的 checkout。
- 回退：`git -C .worktrees/mmw-installed checkout --detach <上一个 main>`，不需要重装，因为软链指向这个 checkout（根 `AGENTS.md` Gotchas 第 1 条）。

| 批 | 内容 | 为什么这样分 | 完成后流水线的状态 | 用户要做什么 |
|---|---|---|---|---|
| 0 规则与护栏 | SSR、RSS 搬到 `docs/skill-set/`，加 `## Layers of the set`；ADR 0032；`check_wiring.py` 以只报告方式运行；新增词条 | 之后每一批的文字都按新规则写 | 行为不变 | 读 ADR 0032 |
| 1 mode、原则、白天层 | `skills/mmw/`：SKILL.md、11 份 MMW 原则、pstack 原则（取决于 D1）、`references/subagent-brief.md`；8 份白天 playbook 与 3 份本仓库 playbook；`upstream-pstack/` 与 `import_component.py`；白天技能回原文或分出（`grilling`、`grill-with-docs`、`codebase-design`、`improve-codebase-architecture`、`setup-matt-pocock-skills`、`writing-for-agents`、`wayfinder`、`prototype`、`to-spec` 与 `to-tickets` 分出、残留 `ask-matt`）；`design-pages/references/state-list-format.md`；路由表里夜间四行暂时指向 `dispatch` 技能 | 这些只有白天会话读，夜里的 worker、reviewer、orchestrator 仍读今天的 `implement`、`code-review`、`night.md`。`to-tickets` 分出后技能名与标题不变，`night.md` 第 141 行对它的引用照样有效 | 夜间不变；白天改由 mode 路由 | 授权运行 `install.sh`（`skills.txt` 有变动）；开新会话，让 description 生效；决定 D1 |
| 2 夜间层 | `work-a-ticket`、`review-a-ticket`、`run-a-night`、`run-one-ticket`、`accept-the-night`；两份共用 reference；`roles.json` 开始被脚本读；启动提示词、唤醒指针、watchdog、turn guard、`NO_QUESTION`、`REFUSAL`；`resume_at` 返回标题；`status` 的 `RESUME:`；`where`；`implement`、`code-review`、`tdd`、`resolving-merge-conflicts` 回原文；`triage` 的流水线段搬走；`dispatch`、`verify-ticket`、`ui-acceptance` 的 `SKILL.md` 改成能力；`shared-experience` 新建；各项测试同一次提交改 | 三组天然整体必须同一次提交：W1（事件 → 收件人 → 动作）、W2（提示词形状 ↔ 入口）、W3（步骤 ↔ `resume_at`）。拆开任何一组，会有一个读者走到错的一步（R14 第 7 节） | 全部由 playbook 驱动 | 在没有 watch 打开时批准提升（D4）；用一个小 spec 跑一个真实的夜作为验收 |
| 3 常驻与回流 | `mode_hook.py`（按 U-2 实测结果，决定注册在哪些宿主）；`retro.py` 的去处；`models.py config role`；`check_wiring.py` 改为不通过就失败；`install.sh --check` 的连线核对；`dispatch.sh check` 的行为（D2） | 依赖实测；不影响第 2 批的正确性 | 更多到达路径 | 授权运行 `install.sh`（新 hook）；决定 D2 |
| 4 按需导入 | 以后你要的 pstack 组件：`session-pickup`、`pause-safely`、`figure-it-out`、`show-me-your-work` 等；需要时再建面板脚本 | 由你排先后 | 不变 | 点名要搬什么 |

**第 2 批的全量测试理由**（`shared.md` 第 15 条要求先说明）：这批同时改了启动提示词、relay、hook、`verify-ticket.py` 四个边界，定点测试覆盖不到跨边界的风险，即「某个事件在新 playbook 里没有处理行」或「某条指针对不上」。所以要跑 `tests/dispatch/test_dispatch.sh all`、`relay`、`verify-ticket`、`liveness` 四个套件，另在隔离的 home 里用假 tracker 完整跑一夜。

---

## 11. 风险、需要的实测、需要用户决定的事

### 11.1 未确定（需要实测）

| # | 问题 | 为什么重要 | 怎么测 |
|---|---|---|---|
| U-1 | 启动提示词「Use the mmw skill … playbook work-a-ticket」能否让五个宿主的新会话读到 playbook 文件 | 夜间主路径 | 照 ADR 0006 的探针办法：在隔离的 home 里放一个探针 `mmw`，`playbooks/probe.md` 里写一个随机标记，用各宿主的非交互进程发这条提示词，看回复里有没有这个标记。读不到的宿主，改由脚本在提示词里给出已安装 checkout 里 playbook 文件的绝对路径（启动提示词由脚本生成，不受技能文本「不写路径」的规则约束） |
| U-2 | 各宿主有没有 prompt 提交、会话开始、压缩后的 hook 事件，能否往上下文注入一行 | 第 2.3 节的第三条到达路径 | 每个宿主装一个只打印标记的探针 hook，在有与没有 `.mmw/` 的目录里各提交一次、压缩一次，看模型能否复述标记。Codex 的事件名已知（`install.sh` 第 768–774 行） |
| U-3 | 技能目录里嵌套的 `.md`（principles、playbooks）会不会被某个宿主当成技能 | 会的话，原则会出现在技能列表里 | 设计上已避开 `SKILL.md` 这个文件名；仍在探针技能里放嵌套文件，看五个宿主的技能列表（Grok 用 `grok inspect --json`） |
| U-4 | 五个宿主是否都有 todo 工具与后台子代理 | 执行协议；槽位 | 各宿主的非交互进程列出可用工具 |
| U-5 | worker 每次启动读 mode 加 playbook 的上下文成本 | 第 2.3 节 | 写好之后量字节数；在隔离的 home 里跑一张测试票，比较开工前的上下文用量 |
| U-6 | 面板脚本起多个会话的耗时与费用 | 第 8.4 节 | 用 `advise` 的机制同时起 3 个会话，量到齐的时间 |
| U-7 | description 数量增加（新增 `mmw`、`shared-experience`，以及 `code-review` 回原文后的触发句）对触发准确度的影响 | H2 | 固定一组用户请求（取自 N10 第 3.2 节），改造前后各跑一次，数每个请求加载了哪个技能 |
| U-8 | 各宿主的会话记录位置与格式；Nowledge Mem 会话能否作为来源 | transcript 槽位 | 各宿主跑一个短会话，找记录文件；用 `nmem t search` 查同一会话 |
| U-9 | paseo、herdr 的第一条提示词是否以参数传入（orca 已核实是，`runners/orca.sh` 第 25 行） | 启动提示词多行是否受 H4 约束 | 读 `runners/paseo.sh`、`herdr.sh` 的 `start` 实现 |
| U-10 | 七份 `CONTEXT.md` 里有没有只写在词表里的行为规则 | 可能还有混层 | 逐份读 `docs/contexts/*/CONTEXT.md` |
| U-11 | 启动提示词点名 playbook 之后，worker、reviewer 会不会改去加载回到原文的上游 `implement`、`code-review` | 两者的 description 会竞争 | 在隔离的 home 里用假 tracker 跑一张票，看它打开了哪些文件 |
| U-12 | `--closeout` 与 `--review` 是否接受 `skip:` 行 | 第 6 节 | 读 `verify-ticket.py` 第 880–900、1347–1362 行，并跑一次 `--closeout --check-only` |
| U-13 | 能否从 `cursor/plugins` 的 `pstack/` 子目录做 subtree | 第 8.1 节 | 在临时克隆里 `git subtree split --prefix=pstack`，再 `subtree add` |
| U-14 | `dispatch.sh where` 能否在三种 runner 上认出当前会话 | 被压缩会话的回路 | `self` 的输出与 `worker.started`、`reviewer.started` 事件里记的会话号，在三种 runner 上各对比一次 |
| U-15 | 消费仓库的 `AGENTS.md` 或其他文件是否点名了 `implement` 技能或旧的提示词句子 | 是否需要 downstream-note | `rg -n "implement skill\|Use the implement" ~/agentflow ~/xiaohuangya` 等 |

### 11.2 需要用户决定的事

| # | 决定 | 我的建议与理由 |
|---|---|---|
| D1 | 第 1 批就导入那 14 条 pstack 原则吗 | 建议导入。它们与 MMW 现有的 18 条规则重合（R14 第 3.2 节），导入之后调用方只写一次名字，不必在第 4 批再改一遍。代价是外来的规则文字进入所有会话的纪律；冲突由 `## Autonomy` 的优先级句处理 |
| D2 | `dispatch.sh check` 在 `--check` 失败时自动跑完整 `install.sh`（R12 M7）：改成只报告，还是改根 `AGENTS.md` 的规则 | 建议改成只报告，保住你定的「只在授权时安装」。风险：开夜时安装不齐，这一夜仍会开，但 `check` 会把缺的东西写成警告，而且夜里用到的东西 `check` 另有核对（`dispatch.sh` 第 2344–2347 行注释） |
| D3 | 是否在你各个消费仓库的 `AGENTS.md` 加一行「This repository uses MMW: the `mmw` skill」 | 它是第四条加载路径，依赖模型会照一行文字去加载技能。改的是你所有仓库的指令文件，所以由你定（R12 K-25） |
| D4 | 第 2 批的提升时机，以及用哪个 spec 跑验收夜 | 需要没有 watch 打开；验收需要你早上看结果 |

我已自行做出的工程决定，写在这里备查：

- `implement` 回原文后保留安装、由用户触发；
- `to-spec`、`to-tickets` 分出为自有技能；
- 面板第一版不建；
- 阶段边界做成原则，而不是 playbook。

### 11.3 风险

- **第 2 批面大。** 已用两种方式应对：天然整体只在这一批一起改；回退是移回上一个提交，可以完全撤销。
- **偏离 pstack 的地方有三处**，各有理由：
  1. 脚本经 `roles.json` 往上指（H4、H6）；
  2. 原则是文件，不是技能（H2）；
  3. playbook 多一段 `**Where you are.**`（H6）。
- **Cursor 读不到 `shared.md`。** 原则索引引用的用户规则，在 Cursor 上靠你在应用里维护的副本（现状如此）。
- **用户以前的决定。** Memory `ce037679` 写着「不许过度设计过度防御」。本架构新增的机制只有六项：`roles.json`、`where`、指针字面、`mode_hook.py`、`check_wiring.py`、`import_component.py`。每项都指名了它要修的已核实断点，或它要满足的导入需求。其余全部是把现有文字搬到对的层。落地后用 `wc -l` 实测新旧总行数，写进第 2 批的报告。

---

## 12. 自查：与第一版草图的最低范围逐项对照

| 草图项 | 结果 | 依据 |
|---|---|---|
| 一个 mode：常驻规则 + 原则索引 + playbook 路由表 | 超出 | 第 2 节：另有 `## Autonomy`（人在场与无人两种会话，加优先级句）、`## Subagents`、`## Re-entry`、`## Slots`，以及四种加载路径 |
| 每一种工作流都是 playbook | 达到 | 16 份，覆盖草图列出的全部 12 类，另有地图、界面、单票、导入四类。不设 playbook 的请求都在第 3.1、3.3 节写了按类型的理由（单一能力，或是原则） |
| 白天定义 | 达到 | `define-a-change`（外加 `map-a-large-effort`、`design-an-interface`） |
| 夜间编排 | 达到 | `run-a-night` |
| 做一张票 | 达到 | `work-a-ticket` |
| 评审一轮 | 达到 | `review-a-ticket` |
| 单票 | 达到 | `run-one-ticket` |
| 早上验收与 finish | 达到 | `accept-the-night` |
| 修 bug | 达到 | `fix-a-bug` |
| 出包 | 达到 | `ship-a-release` |
| 分诊 | 达到 | `triage-an-issue`（流水线自己产出的 issue 在 `accept-the-night`） |
| 调研 | 达到 | `research-a-question` |
| 给仓库接入 MMW | 达到 | `onboard-a-repository` |
| 写技能 | 达到 | `author-a-skill`（外加 `pull-an-upstream`、`import-a-component`） |
| 能力技能只讲一步怎么做、不知道被谁调用 | 达到 | 第 4 节；lint 第 3 类强制 |
| 原则层是一个真正的层 | 超出 | 11 份 MMW 原则 + 14 份 pstack 原则；与 pstack 同一格式；原则层接住 `shared.md` 的规则号；lint 第 4、5 类 |
| 能承接 pstack 原则的结构 | 达到 | 第 5.3、8 节 |
| 脚本由 playbook 的步骤调用 | 达到 | 每步都写出命令；lint 第 7 类 |
| 上游技能回到原文 | 达到 | 13 个回原文或只剩边缘改动，外加 2 个上游目录恢复原文 |
| 外来组件可以直接落位 | 达到 | 第 8 节：文件加一行登记；导入脚本；槽位表 |
| 不小于第一版草图，也不重复 R4、R12 的保守结论 | 超出 | R4、R12：1 份 playbook、5 个角色流程留在能力技能里、2 条原则。本文：16 份 playbook、0 个角色流程留在能力技能里、25 份原则 |
| 没有来源的内容不硬塞 | 达到 | 每份 playbook 与原则都写了来源行；新机制写了依据；「暂停、接手」这两类因为 MMW 没有原文而不写，留给以后导入 |

**未达到的项：无。** 受硬约束影响、换了实现方式的有四项：

- mode 常驻（H1）：用启动提示词、description 与 hook 代替；
- 原则的形式（H2）：做成文件；
- 面板（H3）：用另起的会话，第一版不建；
- 唤醒指针的格式（H4）：必须一行。

---

## 13. 与底稿的差异（本轮改了 R13、R14 的哪些地方）

| 底稿的说法 | 本文的处理 | 理由 |
|---|---|---|
| R14 PB15 `session-pickup` 由 MMW 自己写 | 不写；阶段边界做成原则，暂停与接手留给以后导入 pstack 原文 | MMW 没有白天会话的这两类原文；用 pstack 的名字写一份 MMW 版本，将来导入时会同名冲突 |
| R14 把 `sub-issues.md` 的 kind 表放进 PB5 的规则簇 | 留在 `verify-ticket` 能力里 | `design-pages/references/pull.md` 也开 `contract` 子票，有第二个调用方（L7 C.1 第 4 问） |
| R14 把 `exe-release/references/driving.md` 放进 PB10 的规则簇 | 留在能力里 | 它讲的是怎样读引擎 `where` 的状态，属于「判定怎么读」 |
| R14 把 `advisor` 的 `## When it is worth a session` 放进 mode | 留在能力里，mode 另外点名 | 它是这个能力在任何项目里的触发条件，改动它会让非 MMW 会话失去触发 |
| R13 E3「description 只留是什么」 | description 保留自己的触发分支，只删流水线位置与角色 | 能力技能在 MMW 流程之外也要能被触发（H2） |
| R14 把 axis 文件当作 PB6 的 reference | 采用，并且 `code-review` 回到上游原文 | 四个 axis 与票绑定（Spec axis 读票与 `DECISIONS`，Tests axis 以 `CHECK:` 为范围） |

---

## 14. 本轮读了什么，没读什么

**全文读过**：

- pstack：`skills/poteto-mode/SKILL.md`；playbook `bug-fix.md`、`orchestrate.md`、`session-pickup.md`、`pause-safely.md`、`authoring-a-skill.md`、`investigation.md`、`autonomous-run.md`；`agents/poteto-agent.md`；`principle-attack-the-premise`、`principle-never-block-on-the-human`；`LICENSE` 首行；`plugin.json`。
- MMW：
  - `dispatch/SKILL.md`、`night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md`；
  - `implement/SKILL.md` 与 `git show 5b1a4c51:skills/engineering/implement/SKILL.md`；
  - `code-review/SKILL.md`、`references/session.md`、`agents/openai.yaml`，以及上游 `code-review/SKILL.md` 第 1–30 行；
  - `verify-ticket/SKILL.md`、`references/sub-issues.md`；
  - `ui-acceptance/SKILL.md`、`advisor/SKILL.md`、`advisor/references/consulting.md`、`design-pages/SKILL.md`、`grill-with-docs/SKILL.md`；
  - `mmw-v2/merge-notes/README.md`；`mmw-v2/skills.txt`；`N11-mmw-gaps.json`。
- 报告：L7 全文；N1–N10 的第 1 节（部件清单）；R4 第 1 节（V1–V17）；R12 第 1 节（M1–M30）与第 5 节 K-1–K-34；R13、R14（任务给出的全文）。

**部分读过**：

- `SKILL-SET-RULES.md` 第 1–176 行；
- `install.sh` 第 1–120、290–330、640–800 行；
- `dispatch.sh` 第 60–125、1720–1745、1935–1980、2040–2110、2190–2220、2335–2365 行，以及子命令列表；
- `watchdog.py` 第 85–115、728–785、805–820 行；
- `relay.py` 第 280–300、380–392 行；
- `turn-guard.py` 第 296–320 行；
- `tool-guard.py` 第 25–85 行；
- `verify-ticket.py` 第 2140–2185 行，以及 grep 结果；
- `retro/SKILL.md` 第 6–9、184–187 行与小节标题；
- `triage/SKILL.md` 第 68–95 行；`wayfinder/SKILL.md` 第 120–128 行；
- `to-spec/SKILL.md` 第 1–8、120–127 行；`to-tickets/SKILL.md` 第 18–21、156–162 行；
- `improve-codebase-architecture/SKILL.md` 第 70–76 行；
- 残留 `ask-matt/SKILL.md` 第 1–80 行、`PHASE-BOUNDARIES.md` 第 1–30 行；
- `docs/agents/issue-tracker.md` 第 86–91 行；`exe-release/SKILL.md` 第 1–40 行；
- `code-checkers`、`setup-matt-pocock-skills`、`write-screen-contract` 的小节标题；
- 13 条 pstack 原则的 frontmatter 与跨文件链接。

**没读、只经报告引用的**：

- pstack 其余 16 个 playbook 与多数能力技能；
- MMW 的 `writing-interface-code.md`、`saving-memory.md`、四个 axis 文件、`pipeline-issues.md`、`interface-and-remake.md`、`several-specs.md`、`revising-a-spec.md`、`driving.md`、`CODING_STANDARDS.md`、`TESTING.md`、全部 ADR 正文；
- runner 适配器的实现。

第 3、4 节对这些文件内容的分配依据的是 R14 的清点，属于转引。第 2 批动手前，要逐份读全文，再确认每一段的去处。

**推断汇总**：

- 第 1.5 节脚本归属的判据；
- mode 的行数；
- `where` 的可行性（U-14）；
- `NO_QUESTION` 新文的字符数；
- pstack subtree 的做法（U-13）；
- Claude Code 在压缩后是否有 hook 事件（U-2）。
