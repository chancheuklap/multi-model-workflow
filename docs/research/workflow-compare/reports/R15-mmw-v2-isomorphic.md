# R15 MMW v2 同构架构：按 pstack 的分层重建 MMW

本文给出 MMW（`mmw-v2/`）升级后的完整架构。立场是同构派：新 MMW 的结构尽量与 pstack 相同，mode 目录下挂 `playbooks/`、`principles/`、`references/`、`scripts/`，能力技能与 mode 平级、只讲一步怎么做；只在硬约束 H1–H6 处偏离，偏离处写明替代机制。

**判据**（任务给定，本文照此执行）：每一段内容默认搬到按类型该在的层。留在错层只有一个理由：已核实的硬约束 H1–H6，或已核实的运行故障，并写明是哪一条。「没有收益」「现在能跑」「脚本和测试按字面点名它」「改动面大」都不算。

**材料**：
- 准绳 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）。
- 两份底稿：`R13-pstack-design-essence.md`（下称 R13，精髓 E1–E12、接口 I-1–I-16）与 `R14-mmw-layer-mixing-inventory.md`（下称 R14，任务顺序 T1–T38、原则候选 PC1–PC29、天然整体 W1–W7、playbook 候选 PB1–PB15）。
- R4、R12 中标「已核实」的事实直接引用（记作 R4 V<n>、R12 M<n>），它们的保守结论不用。N11 列的错误不用。
- 本轮回到原文读了：pstack `skills/poteto-mode/SKILL.md` 全文，playbook `bug-fix.md`、`feature.md`、`opening-a-pr.md`、`session-pickup.md`、`pause-safely.md`、`authoring-a-skill.md` 全文，`principle-prove-it-works`、`principle-never-block-on-the-human`、`agents/poteto-agent.md` 全文；MMW 的 `implement/SKILL.md`、`dispatch/SKILL.md`、`night.md`、`one-ticket.md`、`inside-a-ticket.md`、`verify-ticket/SKILL.md` 全文，`code-review/SKILL.md` 前 15 行与上游 squash 原文前 60 行，残留 `ask-matt/SKILL.md` 与 `PHASE-BOUNDARIES.md` 全文，`install.sh` 头注释与 hook 登记段，`dispatch.sh` 第 104–112、1940–1972、2066–2076 行，`tool-guard.py` 第 70–82 行，`relay.py` 第 285–392 行，`retro.py` 第 25–35 行，三个 runner 适配器头注释，`docs/agents/issue-tracker.md` `## Morning queries`，ADR 0015 `## Consequences`。

**标注**：「原文」＝文件里写着；「已核实」＝本轮回原文或跑命令看到；「推断」＝由原文推出；需要实测的写进第 11 节。

**硬约束**（只有这些算约束）：
- H1 宿主不换（Claude Code、Codex、Grok、Pi、Cursor；runner 用 Orca 等），没有 Cursor 的 `mode: true` / `reminder`。
- H2 Claude Code 上，带 `disable-model-invocation: true` 的技能不在模型的技能列表里，按名也调不到（R4 V1）；description 在宿主启动时扫入，改动要新会话才生效。
- H3 会话内子代理跑在本会话宿主的模型上；跨厂商只能另起会话（ADR 0015 `## Consequences`）。
- H4 脚本送进活会话的一条消息必须是一行（`watchdog.py` 第 813 行，R12 M1）。
- H5 Self-hosting boundary：一次 watch 期间冻结已安装版本，不从工作树重读（根 `AGENTS.md`）。
- H6 夜里的会话屏幕前没人，不能向人提问。

另有一条任务给定的边界：`mmw-v2/prompt/shared.md` 是用户的全局规则，MMW 不改写它，下文记作「任务边界 S」。

---

## 0. 结论（先读这里）

1. **升级后的 MMW 与 pstack 同构，改造前后的区别一眼可见。**
   - 新增一个 mode 技能 `mmw`（`mmw-v2/skills/mmw/`），目录布局照 `poteto-mode/`：`SKILL.md` 加 `playbooks/`、`principles/`、`references/`、`scripts/`。
   - MMW 的每一种工作流都成为 `mmw/playbooks/` 下的一个文件，共 18 份；夜间与单票的四个角色流程也在其中。另有本仓库私有的 2 份放在根 `.mmw/playbooks/`。
   - 原则层是 `mmw/principles/` 一个目录：MMW 自建 11 条，另从 pstack 原文落位 13 条（需用户确认，第 5 节 U-D3）。
   - 流水线脚本（`dispatch.sh`、`relay.py`、`watchdog.py`、两个 hook 等）搬进 `mmw/scripts/`，成为只由 playbook 步骤与 hook 调用的 lever。
   - 技能 `dispatch` 解散：路由表进 mode，`## On waking` 进 mode 的 `## Where you are`，三份 reference 成为 playbook，改模型与开任务板成为新的能力技能 `setup-mmw`（对应 pstack 的 `setup-pstack`）。
   - 能力技能里再也没有「下一步」「谁调用我」「worker」「night」这类句子（R14 列出的 17 句「下一步」与 38 处任务顺序全部离开能力技能）。上游技能除调用开关（H2）外回到 squash `5b1a4c51` 原文；`implement`、`code-review` 回到上游原文。
2. **最关键的三处纠正**（相对 R4、R12）：
   - 角色操作文件是 playbook，不是能力技能。`implement` 的 101 行正文里，worker 的顺序进 `playbooks/ticket-work.md`，通用写码规则进 `mmw/references/writing-code.md`，界面写码进 `ui-acceptance`，上游 `implement` 回到 15 行原文。上游原文本身就是一个五行的编排（tdd → typecheck → code-review → commit），按同构判据它是 playbook，成为 `playbooks/direct-change.md` 的骨架（L7 C.1 第 3 问）。
   - 「现在在 playbook 的哪一步」是 mode 层的计算，不是能力技能的。`verify-ticket.py` `resume_at`（第 2148–2182 行）搬到 mode 脚本，由新子命令 `dispatch.sh where` 印出 `RESUME: <playbook> **<步骤名>**`；能力技能的脚本不再知道 worker 的步骤。
   - 脚本启动的会话也在 mode 下工作（R4 第 0 节第 4 条反过来）。启动提示词第一句点名 mode 与 playbook，唤醒、告警、压缩后的 hook 行都带同一个指针。
3. **mode 的到达不依赖任何单一宿主行为**，四条路径叠加（第 2.2 节）：启动提示词（确定）；唤醒与告警的同行指针（确定，H4）；`SessionStart`/`SubagentStart`/`UserPromptSubmit` 类 hook 注入一行（Claude Code 的 `SubagentStart` 注入已在本会话观察到，Codex 的 `SessionStart`、`UserPromptSubmit` 注入由 `install.sh` 第 774 行 `CODEX_CONTEXT_EVENTS` 证实，其余宿主待测 U-2）；模型可触发的 `mmw` description 加消费仓库 `AGENTS.md` 一行（备用）。
4. **外来组件直接落位**：pstack 的 playbook 放进 `playbooks/`、原则放进 `principles/`（文件名不变，去掉 `disable-model-invocation`），各加一行路由或索引；它们依赖的 Cursor 机制、PR、forge、control、模型角色由 `mmw/references/slots.md` 一张表解析；机械改写由导入脚本 `mmw-v2/import/import_component.py` 做，改动写 merge-note（第 8 节）。
5. **分六批落地**（第 10 节）。每批是本仓库的票，由当时已安装的冻结版本跑，只在没有 watch 打开时发布，每批后流水线仍能跑。需要用户做的：批 1、2a、2b、3 授权跑一次 `install.sh`，每批后开新会话；批 2b 后验收一次小规模的真实夜；另有 6 项用户决定（第 11.2 节）。
6. **自查**（第 12 节）：第一版草图的每一项都「达到」或「超出」。有两项的「达到」依赖实测：非 Claude 宿主上的 todo 工具（U-4），以及 Cursor、Grok、Pi 上的 hook 注入（U-2）。两者都有备用路径，不因此缩小结构。

---

## 1. 目标目录树

### 1.1 `mmw-v2/`（升级后，到文件一级；`←` 写来源）

```
mmw-v2/
├── skills.txt                          登记：self/mmw、self/setup-mmw 新增；self/dispatch 删；engineering/implement 删（U-D1）；
│                                       engineering/to-spec、to-tickets 改为 self/（分叉）
├── skills/
│   ├── mmw/                            ── mode（模型可触发）
│   │   ├── SKILL.md                    Non-negotiables / Principles / Autonomy / Where you are / Subagents /
│   │   │                               Writing the reply / Playbooks（执行协议、优先级、路由表）
│   │   ├── playbooks/
│   │   │   ├── idea-to-tickets.md      ← ask-matt 主流程、to-spec ## Next、to-tickets 第 20/160 行、grill-with-docs 第 7 行…
│   │   │   ├── large-effort.md         ← wayfinder 第 6 步、ask-matt on-ramp
│   │   │   ├── interface-design.md     ← prototype UI.md ## Next、design-pages 交接段、write-screen-contract ## Next
│   │   │   ├── direct-change.md        ← 上游 implement 原文五行、ask-matt 第 24–26 行
│   │   │   ├── bug-fix.md              ← ask-matt「Something's broken」、N10 B6
│   │   │   ├── triage.md               ← triage 第 5 步第 82、94 行
│   │   │   ├── investigation.md        ← research、wayfinder 第 5 步、to-spec ## Sources
│   │   │   ├── repository-onboarding.md ← setup-matt-pocock-skills 第 17/51/63 行、code-checkers 第 6/8 步
│   │   │   ├── authoring-a-skill.md    ← SSR ## Editing/## Verifying、根 AGENTS.md Gotchas 第 1 条
│   │   │   ├── release.md              ← exe-release 第 1–5 步、references/driving.md
│   │   │   ├── session-pickup.md       ← pstack 同名、PHASE-BOUNDARIES.md
│   │   │   ├── pause-safely.md         ← pstack 同名、PHASE-BOUNDARIES.md 第 3 问
│   │   │   ├── morning-acceptance.md   ← night.md ## 5 末段与 ## 6、triage references/pipeline-issues.md、issue-tracker ## Morning queries
│   │   │   ├── night.md                ← dispatch/references/night.md（orchestrator）
│   │   │   ├── one-ticket.md           ← dispatch/references/one-ticket.md（单票 orchestrator）
│   │   │   ├── ticket-work.md          ← implement 正文（worker）
│   │   │   ├── ticket-adoption.md      ← dispatch/references/inside-a-ticket.md
│   │   │   └── ticket-review.md        ← code-review/references/session.md（reviewer）
│   │   ├── principles/
│   │   │   ├── principle-<slug>.md     MMW 自建 11 条（第 5 节）
│   │   │   └── principle-<slug>.md     pstack 原文落位 13 条（文件名与 pstack 相同）
│   │   ├── references/
│   │   │   ├── slots.md                control / delivery / forge 槽位与宿主工具映射（第 8 节）
│   │   │   ├── phase-boundaries.md     ← 残留 ask-matt/PHASE-BOUNDARIES.md
│   │   │   ├── writing-code.md         ← implement 第 24–28 行的通用部分
│   │   │   ├── saving-memory.md        ← implement/references/saving-memory.md
│   │   │   ├── interface-and-remake.md ← wayfinder/references/interface-and-remake.md
│   │   │   └── review-axes/{standards,spec,tests,ui}.md   ← code-review 四个 axis 文件（子代理简报）
│   │   └── scripts/                    ── lever（只被 playbook 步骤、mode 触发行与 hook 调用）
│   │       ├── dispatch.sh             ← dispatch/scripts/（新增子命令 where；可选 panel）
│   │       ├── relay.py  watchdog.py  status.py  statedir.py  ghlist.py
│   │       ├── runners/{orca,paseo,herdr}.sh
│   │       ├── tool-guard.py  turn-guard.py        hook
│   │       ├── mode-hook.py            新：SessionStart / SubagentStart / UserPromptSubmit 一行注入
│   │       └── anchors.py              新：角色表与脚本印出的全部文字锚点
│   ├── setup-mmw/                      ── 能力（改 host/model/effort/runner；查角色的模型；开任务板）
│   │   ├── SKILL.md                    ← dispatch description 的对应部分、## Find your moment 第 5、6 行
│   │   ├── references/editing-models.md ← dispatch/references/editing-models.md
│   │   └── scripts/models.py  hosts.json   ← dispatch/scripts/（新增 config get）
│   ├── verify-ticket/                  能力：跑判据、切子票、lint/publish 一批、closeout
│   ├── ui-acceptance/                  能力：+ references/writing-interface-code.md（← implement）
│   ├── design-pages/                   能力：+ references/state-list-format.md（← prototype UI.md 第 6 步）
│   ├── write-screen-contract/  retro/  advisor/  exe-release/  code-checkers/  manage-agents-md/
│   ├── to-spec/  to-tickets/           分叉的 MMW 能力（上游目录回原文）
├── upstream/                           mattpocock squash subtree：除调用开关外回到原文
├── upstream-diagram-design/  upstream-unlazy/   不变
├── upstream-pstack/                    新：pstack 的 squash subtree（导入来源，不直接安装）
├── import/
│   ├── import_component.py             新：把外来 playbook / 原则复制进 mmw/ 并做机械改写
│   └── pstack.map                      新：改写表（原则引用写法、相对路径、槽位词）
├── merge-notes/  downstream-notes/     仓库文档（不变的层）
├── prompt/                             用户级提示词（任务边界 S，不改）
├── board/  migrations/                 不变
└── tests/
    ├── lib/check_wiring.py             新：接线 lint，每个套件先跑（第 7.4 节）
    └── <suite>/                        路径随批次更新
```

### 1.2 本仓库根与消费仓库

```
<仓库根>/
├── AGENTS.md                           ## External References 一行：「A task here → the `mmw` skill」（备用到达路径）
├── .mmw/
│   ├── target.json  harness/  journeys/  stories/      不变（ui-acceptance 的产品答卷）
│   └── playbooks/                      新扩展点：本仓库私有、只给白天会话的 playbook（H5：夜间角色不读）
│       ├── INDEX.md                    一行一份，格式同 mode 路由表
│       └── （仅本仓库）upstream-pull.md、component-import.md
├── docs/agents/{issue-tracker,triage-labels,domain}.md    配置（setup-matt-pocock-skills 写）
├── docs/specs/<effort>/screen-contract.yaml  prototypes/  消费仓库产物
└── docs/skill-set/{SKILL-SET-RULES,REVIEWING-A-SKILL-SET}.md   仅本仓库：技能写作规则（← upstream writing-for-agents 目录）
```

### 1.3 `~/.mmw/`

```
~/.mmw/
├── models.json          角色 → host/model/effort；runner。角色键：junior-worker、senior-worker、reviewer、advisor
│                        （现有，已核实）；可选面板角色，值为列表（第 8.4 节）
├── installed-root       已安装 checkout（H5 的冻结点）
├── boards.json          任务板
└── state/<owner>__<name>/{watches.json, relay.lock, watchdog.lock, …}   watches.json 每个 watch 多一个 by 字段
```

### 1.4 命名规则

| 组件 | 位置 | 命名 | 依据 |
|---|---|---|---|
| mode | `mmw-v2/skills/mmw/SKILL.md` | 技能名 `mmw` | pstack `poteto-mode` |
| playbook | `mmw/playbooks/<slug>.md` | 名词短语，与 pstack 同一任务类型同名（`bug-fix`、`investigation`、`session-pickup`、`pause-safely`、`authoring-a-skill`）；文件首行 `### <Name>` | L7 A.2；同名是有意的：以后导入 pstack 同名 playbook 时是合并，不是并存 |
| 步骤名 | playbook 的编号步骤首个粗体短语 `1. **Claim.** …` | 脚本只按步骤名点名，不按编号 | L7 E.1 第 2 条；R12 M30 |
| 原则 | `mmw/principles/principle-<slug>.md` | 与 pstack 相同的 `principle-` 前缀；frontmatter 只留 `name`、`description` | L7 A.4；H2 |
| mode 的 reference | `mmw/references/<kebab>.md` | 只被 mode 与 playbook 读 | L7 A.5 |
| 能力技能 | `mmw-v2/skills/<name>/` 或上游 subtree | 不含 playbook 名、角色词 | L7 A.3 |
| 脚本 | 属于哪层放哪层的 `scripts/` | mode 的脚本只被 playbook、mode、hook 调用；能力的脚本可被任何上层调用 | L7 A.6、B.2 |
| 角色 | `mmw/scripts/anchors.py` `ROLES`（角色 → playbook、指针）＋ `~/.mmw/models.json`（角色 → 模型） | worker、reviewer、advisor、orchestrator | 第 7.1 节 |
| 私有 playbook | 消费仓库 `.mmw/playbooks/<slug>.md` | 同 playbook | pstack A.11 |

---

## 2. mode：`mmw`

### 2.1 内容（逐节）

frontmatter 只有 `name: mmw` 与 `description`，不带 `disable-model-invocation`（H2：带了就按名调不到，启动提示词里的「Use the mmw skill」会失效）。description 写到达条件：一个仓库里有 `.mmw/` 或 `docs/agents/issue-tracker.md` 时的任何新任务；提示词或 hook 行点名 `mmw` 时。

| 节 | 内容 | 来源（全部是现有文本或 pstack 原文） |
|---|---|---|
| `## Non-negotiables` | 首段照 pstack 第 15 行：回复或交付物里点名改变了决定的原则，只点名本会话读过全文的。其后是「条件 → 技能 / playbook / 脚本命令」触发行，每行一个，见下表 | pstack mode 第 13–35 行的形式 |
| `## Principles` | 索引，分组，每条「显示名（**principle-slug**）. 何时适用. 一句要点」；首句「应用哪条就读哪条全文」；另一句：用户全局规则（`shared.md` 规则 1–15）高于这里的每一条，原则只写这些规则没说的 | pstack 第 37–77 行；任务边界 S |
| `## Autonomy` | 两种会话。有人在场：按 `shared.md` 规则 1、2（不复述）。无人（提示词写 `unattended`，或工作树在 `.worktrees/issue-<n>`）：不向屏幕提问；各角色的唯一出路（worker：`Decisions I made on my own` 一行，会改变交付的开 `decision` 子票并继续；reviewer：报告里写 `Could not tell:`；advisor：`Missing information gets named precisely`）；产品事项的清单抄一次 | `dispatch.sh` 第 108 行 `AUTONOMOUS`；`tool-guard.py` `NO_QUESTION`；`implement` 第 23 行；`session.md` 第 45 行；`advising.md` 第 18 行（R12 M11）。清单抄一次是 H1 所迫：Cursor 收不到 `shared.md`（根 `AGENTS.md` Key Conventions） |
| `## Where you are` | MMW 独有（pstack 没有，H6）。被唤醒或被压缩的会话四步：1）唤醒打断的命令原样重跑；2）读唤醒点名的事件；3）`dispatch.sh ack`（`watchdog:`、`MMW turn guard:` 行不 ack）；4）跑 `bash scripts/dispatch.sh where <n 或 spec> --role <role>`，打开它印出的 playbook，从它点名的步骤名继续 | `dispatch/SKILL.md` `## On waking` 第 1–4 步（原文搬迁） |
| `## Subagents` | 用宿主的通用子代理（ADR 0015）；简报第一句「Use the `mmw` skill: read its `## Principles` and `<playbook>` step **<name>**」；只读靠简报一句「You are read-only」；子代理跑在本会话模型上，搬入的面板技能降级为同模型面板，除非走 `dispatch.sh panel`（H3）；报告写进文件，大块工作交给子代理 | ADR 0015；`session.md` 第 23、33 行；`to-tickets` 第 113–119 行；`manage-agents-md` 第 50 行；`wayfinder` 第 76、114 行；pstack mode 第 91–95 行 |
| `## Writing the reply` | 一句：回复写法以 `shared.md` 规则 4–9 为准。MMW 独有：无人会话的「回复」就是 playbook 的交付物（票上的 closeout、`REVIEW` 报告、`NIGHT SUMMARY`），点名原则与 `skip:` 行写在那里 | 任务边界 S；`shared.md` 前言末段「what it reports goes in the formats its skills give」 |
| `## Playbooks` | 1）执行协议（第 6 节）；2）优先级句：`shared.md` > mode > playbook > 能力技能的本地闸门；关于交付物之后做什么以 playbook 为准，关于怎么做以能力技能为准；3）无匹配：说出来，在 Non-negotiables 与原则下直接做，同一形状出现第二次就走 **Authoring or modifying a skill** 加一份 playbook；4）路由表（第 3.1 节），每行 `- **<Name>.** <任务类型>. [用户原话]. [Distinct from …]. \`playbooks/<file>.md\`.`；5）一句：本仓库 `.mmw/playbooks/INDEX.md` 列的私有 playbook 排在表后，只在白天会话里用 | pstack 第 115–143 行；R4 D2.2；pstack `authoring-a-skill.md` 第 10 行「A workflow you keep hitting but isn't captured → propose a new skill」 |

**`## Non-negotiables` 的触发行**（每行都来自现在散在各 description 或正文里的「在某个时刻用我」）：

| 条件 | 去处 | 现在的出处 |
|---|---|---|
| 架构选择、数据迁移、大重构或 API 形状即将定下；一个问题两次尝试没解决；对任务的读法有争议 | `advisor` 技能 | `advisor` description；`consulting.md` `## When it is worth a session` |
| 要启动、连上或停掉运行中的产品，碰进程或端口 | `ui-acceptance` 的 `## Five rules while the product is running` | `dispatch.sh` 第 109 行 `PRODUCT_RULES`；`verify-ticket` `## Reached from here` |
| 写代码时 **Read first** 列着 screen contract | `ui-acceptance` 的 `references/writing-interface-code.md` | `implement` 第 16 行末句 |
| 合并冲突，或干净合并后仓库检查变红 | `resolving-merge-conflicts` | `implement` 第 78、99 行 |
| 要关票、改票的标签、写事件 | 只经 `verify-ticket.py` 或 `dispatch.sh`；hook 会拦别的写法 | `implement` 第 99 行；`tool-guard.py` `REFUSAL`；`CODING_STANDARDS.md` State 第 3 条 |
| 要建 git worktree | 放在 `.worktrees/` 下，不用 `issue-<n>`、`merge-<branch>` 这两种名字 | 根 `AGENTS.md` Key Conventions |
| 只有人能做的一步（凭据、第三方控制台、装机实测） | `wizard`，或按 `to-tickets` `references/person-ticket.md` 开人工票；**principle-human-steps-stay-human** | `wizard` description；`ui-acceptance` 规则 3 |
| 人在场的会话走到阶段边界 | `references/phase-boundaries.md` | ask-matt `## Phase boundaries` |
| 问题出在用词，而不是流程 | `domain-modeling`、`codebase-design` | ask-matt `## Vocabulary underneath` |
| 刚说的话没被理解 | `wait-what` | ask-matt `## Standalone` |
| 打开任务板 | `bash scripts/dispatch.sh board`；exit 0 已打开或印出 URL，exit 2 看 stderr | `dispatch/SKILL.md` 表第 6 行 |
| 换 host、model、effort 或 runner | `setup-mmw` | `dispatch/SKILL.md` 表第 5 行 |
| 一步点名 control、delivery、forge 槽位，或 Cursor 专有工具 | `references/slots.md` | 第 8 节 |
| 流水线自身出错（脚本、hook、`.mmw/target.json`） | 夜里：`fault` 子票后停；白天：告诉用户，另开票修，不就地绕过；**principle-rerun-dont-reroute** | `implement` 第 18 行；`night.md` 第 82 行 |

篇幅估计：pstack mode 143 行；本 mode 约 150–170 行（推断，路由表 18 行加私有索引一句）。上下文成本见 U-5。

### 2.2 怎样被加载（满足 H1–H2）

| 会话 | 到达路径 | 确定性 |
|---|---|---|
| 脚本启动（worker、reviewer、advisor） | 启动提示词第一句：`Use the mmw skill. Role worker, ticket #<n>, unattended: playbooks/ticket-work.md.`（reviewer 同形，advisor 为 `Role advisor: the advisor skill's references/advising.md`）。环境变量加 `MMW_ROLE`、`MMW_PLAYBOOK`（`MMW_SPEC`、`MMW_TICKET` 已有，`dispatch.sh` 第 1955 行附近，已核实） | 确定：不依赖宿主行为。H2 只要求 `mmw` 模型可触发。启动提示词作为命令行参数传入（`runners/orca.sh` 第 21–25 行，已核实；paseo、herdr 推断同样，U-9），H4 不管它，但仍写成一行以免依赖 U-9 |
| 被唤醒（relay、watchdog、`resume`） | 唤醒行同一行末尾接指针：`#<n> reviewer.reported · mmw playbooks/ticket-work.md **Where you are.**`；由 `anchors.py` 按收件角色与 watch 的 `by` 生成 | 确定（H4 满足：同一行）。`ack` 按收件人加 ticket 加事件名匹配，不解析文字（R4 V4），加指针不影响 |
| 被压缩（上下文压缩后） | `mode-hook.py` 挂在 `SessionStart`（Claude Code 的 `compact` 来源）上：`MMW_ROLE` 有值就印同一个指针；orchestrator 会话由 `turn-guard.py` 已有的识别法（relay 登记的会话）认出，印 `playbooks/night.md` 或 `one-ticket.md` 的指针 | Claude Code、Codex 有注入事件（Codex：`install.sh` 第 774 行 `CODEX_CONTEXT_EVENTS` 含 `SessionStart`、`UserPromptSubmit`，已核实）；其余宿主 U-2。没有注入事件的宿主，下一次唤醒行自带指针，压缩与唤醒之间的空档由 watchdog 兜住（推断） |
| 会话内子代理 | `mode-hook.py` 挂 `SubagentStart`：印「Use the mmw skill: read its `## Principles`」；另由 `## Subagents` 的简报模板第一句保证 | Claude Code 的 `SubagentStart` 注入：本会话开头收到 Nowledge 插件的「SubagentStart hook additional context」，已观察到；其余宿主 U-2。简报一句不依赖 hook。这是 pstack `poteto-agent` 的替代（H3 下不能注册跨宿主子代理类型） |
| 人启动（白天） | 1）`mode-hook.py` 挂 `UserPromptSubmit`（或 `SessionStart`）：当前仓库有 `.mmw/` 或 `docs/agents/issue-tracker.md` 才印一行，照 pstack `reminder` 原文改写：「New task here? Playbook match or rigor needed → apply the mmw skill. Casual turn or user opts out → don't.」；2）`mmw` description 模型可触发；3）消费仓库 `AGENTS.md` `## External References` 一行（`manage-agents-md` 第 150 行允许技能加行，R4 V14）；4）`/mmw` 手动 | 1 待测 U-2；2、3 已有机制；ADR 0014 否决「写进 `shared.md`」的两条理由（到不了 Cursor；为偶发之事付每回合上下文，R4 V16）不适用：hook 只在 MMW 仓库印一行 |

---

## 3. playbook 总目录

### 3.1 路由表（mode `## Playbooks` 的内容，按 pstack 格式）

| # | 名字（文件） | 任务类型与用户原话 | Distinct from | 入口 |
|---|---|---|---|---|
| P1 | **Idea to tickets**（`idea-to-tickets.md`） | 一个想法、一个功能或改动，要变成一批可以夜里跑的票（「把这个做成 spec」「切票」） | Large effort：路线还看不见；Direct change：小到用户自己检查 | 路由；Large effort、Interface design、Bug fix、Triage 交过来的在 **Spec** 步进入 |
| P2 | **Large effort**（`large-effort.md`） | 一个会话装不下、从这里到终点的路还看不见的工作（绿地项目、大功能） | Idea to tickets：一次访谈加一份 spec 装得下（`wayfinder` description「Not for a well-scoped feature」） | 路由 |
| P3 | **Interface design**（`interface-design.md`） | 界面要设计或重新设计；设计包已签字要拉回仓库；screen contract 要重写 | Idea to tickets：没有界面决定 | 路由；P1 **Runnable questions** 的 UI 胜出方案 |
| P4 | **Direct change**（`direct-change.md`） | 小到用户会直接检查的改动，不开票、不跑夜 | Idea to tickets：要多个会话、要脚本跑判据与独立评审（ask-matt 第 26 行） | 路由；P1 **Who checks** 的 No |
| P5 | **Bug fix**（`bug-fix.md`） | 有东西坏了、报错、变慢（「debug」「diagnose」） | Triage：外来的、还没判断的 issue | 路由 |
| P6 | **Triage**（`triage.md`） | 不是自己创建的 issue 或外来 PR 在等判断 | Morning acceptance：流水线自己交回的票 | 路由 |
| P7 | **Investigation**（`investigation.md`） | 只读问题：X 怎么工作、为什么这样建、要查一手来源 | Bug fix：要修 | 路由 |
| P8 | **Repository onboarding**（`repository-onboarding.md`） | 给一个仓库接入 MMW | — | 路由 |
| P9 | **Authoring or modifying a skill**（`authoring-a-skill.md`） | 写或改技能、playbook、原则、mode | — | 路由；导入外来组件时由私有 playbook **Component import** 调用 |
| P10 | **Release**（`release.md`） | 出包、打安装包（「ship」「package」） | Morning acceptance 的 `finish`：合进 project branch，不出包 | 路由 |
| P11 | **Session pickup**（`session-pickup.md`） | 接手别的会话留下的在途工作（handoff 文件、会话记录、推上去的分支） | 夜间角色被唤醒：走 mode `## Where you are` | 路由 |
| P12 | **Pause safely**（`pause-safely.md`） | 人在场的会话要停下、换宿主、换目录、交给同事 | Night 的 `#### Suspending the night` | 路由；mode 触发行「阶段边界」 |
| P13 | **Morning acceptance**（`morning-acceptance.md`） | 早上验收一夜的结果，并在接受后 `finish` | Triage：外来 issue | 路由；P14 最后一步 |
| P14 | **Night**（`night.md`） | 今晚跑 spec #N（「开夜」） | One ticket：一张票、没有批次 | 路由；P1 **Hand to the night** |
| P15 | **One ticket**（`one-ticket.md`） | 在夜外起一个 worker 做一张票 | Ticket adoption：自己做 | 路由 |
| P16 | **Ticket work**（`ticket-work.md`） | 角色 worker：被 `start` 放到一张票上 | — | 启动提示词；P17 |
| P17 | **Ticket adoption**（`ticket-adoption.md`） | 自己拿起一张票做，没有 `start` | One ticket | 路由 |
| P18 | **Ticket review**（`ticket-review.md`） | 角色 reviewer：被 `start <n> reviewer` 起来 | 通用评审（没有票）：`code-review` 技能 | 启动提示词 |

不单列 playbook、路由表直接写一行指向能力的（它们只调一个技能、没有跨能力顺序，照 L7 C.6 信号 5 是形式拆散；这是按类型判定）：顾问 → `advisor`；换模型 → `setup-mmw`；代码架构整理 → 告诉用户运行 `/improve-codebase-architecture`，定下的决定进 P1 **Spec**；一次通用评审 → `code-review`；画图 → `diagram-design`；写 AGENTS.md → `manage-agents-md`；学一个概念 → `teach`；问卷 → `to-questionnaire`；人工步骤脚本 → `wizard`；无仓库的访谈 → `grill-me`。

本仓库私有（根 `.mmw/playbooks/`，只给白天会话）：**Upstream pull**（`upstream-pull.md`，← 根 `AGENTS.md` `<important if … upstream>` 与 `merge-notes/README.md`）；**Component import**（`component-import.md`，第 8.6 节）。

### 3.2 统一骨架

每份 playbook 照 pstack：`### <Name>`；粗体所有权行；可选首段写本类任务的纪律；编号步骤，每步 `N. **<步骤名>.** <祈使动作>`，点名一个能力技能、原则、脚本命令或别的 playbook；长 playbook 用 `#### <规则簇>` 放常设规则，只有 `#### Steps` 抄进待办（pstack `orchestrate.md`，L7 D.1）；末行 `**Reply:**` 只写独有内容。跨会话、会被唤醒的 playbook 多一段 `**Where you are.**`：只写「跑 `dispatch.sh where …`，照它印的步骤名继续」，不列事实表（事实由脚本算）。

### 3.3 逐份：所有权、步骤、重入、交付物

下列步骤只写骨架：步骤名、点名的组件、现有来源。步骤正文从来源原文搬，不新写规则。

**P1 Idea to tickets.** 所有权：你拥有这批票的形状，产品事项归用户。
1. **Grill.** `grilling` 加 `domain-modeling`（在工作目录里）；仓库外的一手事实用 `research`。用户输入 `/grill-with-docs` 的会话本身就处在这一步。← ask-matt 主流程第 1 步。
2. **Runnable questions.** 要跑才能回答的问题用 `prototype`；UI 胜出方案转 **Interface design**；LOGIC、EXP 的结论写进叶子 `README.md` 后回 **Grill**。← ask-matt 第 2 步；`prototype` 规则 6 的后半句（R14 T22）。
3. **Someone else knows.** 缺的知识在别人脑子里：`to-questionnaire`，结束回合。
4. **Who checks.** 要多个会话、要脚本判据与独立评审 → **Spec**；小到用户直接检查 → **Direct change**。← ask-matt 第 22–26 行（R12 M29）。
5. **Spec.** `to-spec`。从 **Grill** 到 **Tickets** 在同一个未清空的上下文里，临界时按 `references/phase-boundaries.md` 在边界压缩。几份 spec 时一次一份（`to-spec` `references/several-specs.md` 的循环部分）。← ask-matt `### Context hygiene`；`grill-with-docs` 第 7 行末句。
6. **Tickets.** `to-tickets`，然后 `verify-ticket.py <spec> --lint` 直到没有 `ERROR`（**principle-silence-is-never-a-pass**）。← `to-spec` `## Next`、`to-tickets` 第 20 行。
7. **Hand to the night.** 什么时候开夜由用户定；定了就走 **Night**。← `to-tickets` 第 160 行。

重入：`**Where you are.**` 按 tracker 与仓库的事实（spec 已发布无票 → **Tickets**；票已过 lint → **Hand to the night**；其余 → **Grill**），取自 R12 §2.2 的九行表，事实只取 tracker、仓库与用户本条消息（**principle-the-tracker-is-the-state**）。交付物：已发布、通过 lint 的票。**Reply:** 票号、跳过的步骤与理由。

**P2 Large effort.** 所有权：你拥有地图，不拥有构建。
1. **Chart the map.** `wayfinder`（地图标签见 `docs/agents/issue-tracker.md` `## Three label sets`）。
2. **Resolve one decision ticket at a time.** 研究票走 **Investigation**；界面票走 **Interface design**；带界面的地图结构按 `references/interface-and-remake.md`。
3. **Hand off at the clear map.** 地图清空后在新会话进 **Idea to tickets** 的 **Spec**，一次一份。← `wayfinder` 第 6 步第 126 行、ask-matt on-ramp 第 3 条「it hands off, it doesn't build」。

交付物：清空的地图与第一份 spec 的入口。**Reply:** 已解决与未解决的决定票。

**P3 Interface design.** 所有权：你拥有设计源的流转，设计由用户在 Claude Design 里签字。
1. **Sketch variants.** `prototype`（UI 分支）；记录胜出方案。
2. **Set up Claude Design.** `design-pages`。宿主没有 Claude Design 工具时，照 **Pause safely** 告诉用户运行 `/handoff` 换到有工具的宿主（R12 K-43）。
3. **Pull the signed-off design.** `design-pages` `references/pull.md`；首次 pull 后拆掉原型脚手架（`## After the first pull`）。
4. **Write the screen contract.** `write-screen-contract`。
5. **Stop on unaligned rows.** 有未对齐的行：开对齐票，或走 `write-screen-contract` 的 `Reverse sweep`。← `to-spec` 第 22 行闸门。
6. **Hand to the spec.** 首次：**Idea to tickets** 的 **Spec**；再次 pull 或 `Re-runs`：按 `改动分类` 分四路，spec 的改动走 `to-spec` `references/revising-a-spec.md`。← `edit-pages.md` `## Next`、`pull.md` `## Reached from here`、`write-screen-contract` `## Next`。

交付物：screen contract 与交给 spec 的入口。**Reply:** 设计包路径、未对齐的行。

**P4 Direct change.** 所有权：你拥有这次改动，用户直接检查它。
1. **Write it test-first.** `tdd`，在事先约定的 seam 上；写码规则按 `references/writing-code.md`。
2. **Run the checks.** 定期跑类型检查与单个测试文件；结束时跑仓库指令为这次改动点名的测试（`shared.md` 规则 15 高于上游原文「full test suite once at the end」）。
3. **Review.** `code-review`，固定点是本次改动的起点（**principle-a-reader-who-did-not-write-it**）。
4. **Deliver.** 按 `references/slots.md` 的 delivery 槽位：本仓库是根 `AGENTS.md` `## Gotchas` 第 1 条的四步发布；用 PR 的仓库开 PR。

← 上游 `implement` 原文五行（squash `5b1a4c51`，已核实）与 ask-matt 第 24 行。交付物：提交。**Reply:** 改了什么、怎么验证、请用户检查的点。

**P5 Bug fix.** 所有权：你拥有从复现到根因。
1. **Get a loop that goes red.** `diagnosing-bugs`（Phase 1 的反馈回路先于一切）。
2. **No good seam.** 告诉用户运行 `/improve-codebase-architecture`（它是用户触发的技能）。
3. **Fix.** 小：**Direct change**；要多个会话：**Idea to tickets** 的 **Spec**。回归测试用 `tdd`。

← ask-matt on-ramp「Something's broken」；N10 B6（`diagnosing-bugs` Phase 5 没有去处）。**principle-fix-root-causes**。**Reply:** 坏在哪、根因、修法、复现从红到绿的原样输出。

**P6 Triage.** 1. **Judge.** `triage` 技能的角色状态机。2. **Agent-ready.** 写 agent brief，进 **Idea to tickets** 的 **Spec**，spec 发布后关 issue 并链接 spec（R12 §2.3 `to-spec` 行，R7 A4）。3. **Pipeline hand-backs.** 流水线交回的票不在这里判，转 **Morning acceptance**。← `triage` 第 5 步第 82、94 行（R14 T19）。**Reply:** 每个 issue 的结论（四种之一）。

**P7 Investigation.** 1. **Read the code or delegate the reading.** 仓库内问题直接读；一手来源用 `research`（后台代理）。2. **File it where a decision cites it.** 研究文件落在仓库里，被 spec 的 `## Sources` 或地图票引用。← `research`、`wayfinder` 第 5 步、`to-spec` 模板 `## Sources`、根 `AGENTS.md`「a spec may cite」。**principle-clues-are-not-evidence**。**Reply:** 带出处的回答。

**P8 Repository onboarding.** 1. **Tracker and docs.** `setup-matt-pocock-skills`（← 第 17、51、63 行的流水线语句搬到本步）。2. **AGENTS.md.** `manage-agents-md`，加 `mmw` 一行。3. **Checkers.** `code-checkers`，结果写进 `.mmw/target.json` 的 `checks`（← `code-checkers` 第 6、8 步的顺序部分）。4. **Product answers.** 有界面的仓库：`ui-acceptance` 的 `target_config.py --check` 直到 exit 0。5. **Machine.** `bash mmw-v2/install.sh --check`（只读）。交付物：`.mmw/target.json` 完整，`--check` exit 0。**Reply:** 还缺哪些产品答案。

**P9 Authoring or modifying a skill.** 所有权：你拥有这份文字的层与声音。
1. **Place it.** 按 `docs/skill-set/SKILL-SET-RULES.md` 的分层判定（改写后的事实 7，第 7.5 节）决定它是 mode 行、playbook、原则、reference 还是能力技能。
2. **Write it.** `writing-for-agents`。
3. **Validate.** `check_wiring.py`、`check_own_skill_frontmatter.py`；相关套件（最小集合，`shared.md` 规则 15）。
4. **Record.** 改了上游技能 → merge-note；让消费仓库产物失效 → downstream-note。
5. **Deliver.** delivery 槽位；本仓库的第三步（移动已安装 checkout）等所有 watch 关闭（H5）；改了 description 的要开新会话（H2）。

← SSR `## Editing`、`## Verifying`；根 `AGENTS.md` Gotchas 第 1 条；pstack `authoring-a-skill.md`。**Reply:** 放在哪一层、为什么、验证结果。

**P10 Release.** 1. **Preconditions.** 2. **Name the products.** 3. **Drive each product.** `release-flow.sh`，照 `where` 的状态表（`#### Driving` 规则簇 ← `driving.md`）；manifest 用 `exe-release` 的 `references/key.md`。4. **Same-commit check.** 5. **User install test.** 用户装机实测（**principle-human-steps-stay-human**）。← `exe-release/SKILL.md` `## 1.`–`## 5.`。**Reply:** 安装包、提交号、等用户实测的点。

**P11 Session pickup.** 照 pstack 原文五步（定位轨迹、重建状态、对比已做与未做、路由到对应 playbook、按原始目标在真实产物上核对）。MMW 的轨迹来源：`handoff` 写的文件、推上去的分支、tracker 事件；票上的工作用 `dispatch.sh where`。宿主会话记录的位置按宿主不同，见 `references/slots.md`（U-8）。**principle-the-tracker-is-the-state**。

**P12 Pause safely.** 照 pstack 原文四步；「写续跑笔记」一步按 `references/phase-boundaries.md` 第 3 问：只有换宿主、换目录、交给同事、分出侧任务时才用 `handoff`（告诉用户运行），否则压缩或清空。

**P13 Morning acceptance.** 所有权：用户接受结果；你把接受前的事做完。
1. **Read the night.** `NIGHT SUMMARY`、`NIGHT RETRO`。
2. **Morning queries.** `docs/agents/issue-tracker.md` `## Morning queries` 两份清单，先 `needs-triage` 后 `ready-for-human`。
3. **Pipeline hand-backs.** 按 `#### Pipeline issues` 规则簇（← `triage/references/pipeline-issues.md` 全文）判断；子票用 `dispatch.sh route` 关。
4. **Retro proposals.** 用户批的提案进 **Idea to tickets** 的 **Spec** 或 **Authoring or modifying a skill**。
5. **Finish.** 用户接受后：`bash scripts/dispatch.sh finish <spec>`；不把 project branch 合进默认分支（那是用户的发布决定）。← `night.md` `## 6`。

交付物：`finish` exit 0。**Reply:** 接受了什么、交回了什么、等用户做的。

**P14 Night.**（orchestrator；← `night.md` 全文，逐节搬）所有权行 ← `night.md` 第 3 行；首段 ← 第 5–7 行，理由换成点名 **principle-woken-not-polled**、**principle-silence-is-never-a-pass**。
- `#### Steps`：1. **Check and open.** `dispatch.sh check`、`open`，把任务板 URL 交给用户。2. **Lint the batch.** `verify-ticket.py <spec> --lint`；有界面时 `target_config.py --check`。3. **First advance.** `dispatch.sh advance`，结束回合。4. **Each wake.** mode `## Where you are` 第 1–3 步，`status`，按 `#### Wake table` 处理每一行，`advance` 一次；前沿空且没有活代理 → **Closing pass**，否则结束回合。5. **Closing pass.** 按 `#### Closing pass`。6. **Close the night.** `reverify`、`summary --memory-decisions`。7. **Retro.** `retro` 技能，同一会话。8. **Hand to the morning.** 告诉用户看 `NIGHT SUMMARY`、`NIGHT RETRO`，接受后走 **Morning acceptance**。
- `#### Wake table`：`night.md` `## 3` 表全部行，**补齐**：`MMW turn guard:` 一行（R4 V7）；`watchdog.py` 第 94–109 行八种告警各一行（R12 M16）；`### Exit codes of resume` 补全退出码（R4 V8）。
- `#### Authority order`（← 第 96–100 行）；`#### Closing pass`（← `## 4` 整块，三条提交规则末句点名 **principle-rerun-dont-reroute** 与 `shared.md` 规则 15）；`#### Memory decisions`（← 第 151–157 行）；`#### Suspending the night`（← 同名节）。
- `**Where you are.**` 跑 `dispatch.sh where <spec> --role orchestrator`：`status.py` 按事件算出步骤名（取值含「Lint the batch」与 `spec.retroed` 已记录未验收一行，补 R4 V6 的缺行）。
- 交付物：`NIGHT SUMMARY`、`NIGHT RETRO`、各决定的理由评论。

**P15 One ticket.**（← `one-ticket.md` 四步）1. **Open the ticket.** `open-ticket`。2. **Start the worker.** `start <n> worker`，结束回合。3. **Each wake.** 本 playbook 的五行（passed/returned、lost、refused、fault、decision）；`contract`、`watchdog:`、`MMW turn guard:` 三类按 **Night** 的 `#### Wake table` 同名行（按行名引用，不按编号）。4. **Land.** `dispatch.sh land <n>`。交付物：`land` exit 0。

**P16 Ticket work.**（worker；← `implement` 正文）所有权：票的代码归你；spec、票体、判据、baseline 归 orchestrator 与用户。
- `#### Steps`：1. **Claim.** `verify-ticket.py <n> --preflight`；`NOT_READY` 停。2. **Read in.** 票、子票、**Read first**、**Parent** 的 spec 小节、词表（← 第 16 行）；有 screen contract → `ui-acceptance` `references/writing-interface-code.md`；Memory 按 `#### Memory`。3. **Write the code.** `tdd`，限定句：seam 是票 `## Seam` 点名的那些，评审之后的修复轮就是 tdd 的 refactor 轮（← `tdd` 第 22、38 行，回到本处）；`CHECK:` 点名的用例是第一条红测试（← 第 30 行）；按 `references/writing-code.md` 与 `#### Ticket rules while writing`。4. **Integrate and run.** `dispatch.sh integrate <n>`；exit 3 → `resolving-merge-conflicts`（← `resolving-merge-conflicts` 第 2 步的票语句回到本处）；`verify-ticket.py <n>`。5. **Post the decisions.** `--decisions`。6. **Review round.** `dispatch.sh start <n> reviewer`，结束回合（**principle-woken-not-polled**）；醒来读报告、`ack`、修票内问题或 `refuted:`、票外问题开 `finding` 子票。7. **Final run.** `--reverify --actor worker`。8. **Audit.** 9. **Tell touched tickets.** `--touched`。10. **Close out.** `decision` 子票、`--draft`、填写、`--closeout`；delivery 槽位：orchestrator land，不开 PR。
- `#### Ticket rules while writing`（← 第 22–23、27–28 行）：baseline 是合同（**principle-baseline-is-a-contract**，本地一句后果：假 `ALL MET` 让后面的票都继承它）；`Decisions I made on my own` 的写法；Owns 两档（**principle-separate-before-serializing-shared-state**）。
- `#### Sub-issue kinds`（← `verify-ticket/references/sub-issues.md` 第 13–23 行）；`#### ABANDON kinds`（← 第 76 行）；`#### Memory`（← `## Shared experience while implementing`，保存方法读 `references/saving-memory.md`）。
- `**Where you are.**` 跑 `dispatch.sh where <n> --role worker`，照 `RESUME: ticket-work **<步骤名>**` 继续。
- 交付物：`--closeout` 过的收尾评论（它就是 worker 的回复）。

**P17 Ticket adoption.**（← `inside-a-ticket.md`）1. **Adopt.** `dispatch.sh adopt <n> [--into <base>]`，从票的工作树。2. **Work it.** **Ticket work**。3. **After the closeout.** 醒来是 `ticket.passed` 或 `ticket.returned`：`ack`，告诉用户票已关、由谁 land。

**P18 Ticket review.**（reviewer；← `session.md`）所有权：你只读，只写一份报告。
1. **Pin the diff.** 2. **Run the axes.** 四个宿主通用子代理并行，简报是 `references/review-axes/{standards,spec,tests,ui}.md`；Standards 简报引用 `code-review` 技能的 smell baseline，不复写（上游原文 §3）。3. **Verify every finding.**（**principle-clues-are-not-evidence**）4. **Sort.** 票内、票外。5. **Write one review report.** `verify-ticket.py --review`。
- `#### Active Rules`（← 同名节）。无人会话里被拦下的提问：报告写 `Could not tell:`（← `session.md` 第 45 行；补 N11 的缺边）。
- 重入：一次性会话；丢失时 watchdog 写 `reviewer.lost`，worker 在 **Review round** 另起一个。交付物：`REVIEW <base>..<HEAD>` 评论与 `reviewer.reported`。

**advisor 会话**不是 playbook：它交出一个可命名的交付物（回答），是 `advisor` 能力的 reference `advising.md`（L7 A.5「交给另一个读者的模板」、C.3）。启动提示词只多一句点名 mode。

---

## 4. 能力技能总目录

「剥离」一列写离开的内容与去处；「剩下」写升级后只剩的纯能力。调用开关：playbook 或 mode 触发行点名、要由模型调用的，必须模型可触发（H2）；只由用户启动的保留上游的 `disable-model-invocation`，`agents/openai.yaml` 的 `policy` 同增同删（`merge-notes/README.md`）。

### 4.1 上游技能（mattpocock subtree）

| 技能 | 剥离 → 去处 | 剩下 | 回到原文？ | 调用开关 |
|---|---|---|---|---|
| `implement` | 全部 MMW 正文 → P16、`writing-code.md`、`ui-acceptance`、`saving-memory.md` | 上游 15 行原文 | 是；**不安装**（U-D1），原文内容是 P4 的骨架 | — |
| `code-review` | `## Find your moment`、`session.md` → P18；四个 axis 文件 → `mmw/references/review-axes/`；第 8 行理由 → **principle-a-reader-who-did-not-write-it** | 上游双轴评审（squash 原文），可在任何分支或 PR 上用 | 是 | 模型（上游原文就无开关） |
| `to-spec` | description 触发句、`## Next`、第 2 步闸门后半、several-specs 的循环 → P1、P3 | 上游 75 行 + MMW spec 扩展（seam、状态可达、模板各节，R14 §4.2） | 上游目录回原文；MMW 版分叉到 `mmw-v2/skills/to-spec/` | 模型 |
| `to-tickets` | 第 20、160 行 → P1；子代理段 → mode `## Subagents`；第 84、88 行理由 → **principle-silence-is-never-a-pass** 加本地一句 | 切片、五问、四行判据、blocking edges、Owns、模板与三份 reference | 同上，分叉 | 模型 |
| `triage` | description 触发句、第 70、82、90、94 行 → P6、P13；`pipeline-issues.md` → P13 规则簇；第 41 行标签 → `docs/agents/triage-labels.md` | 上游三份原文 | 是 | 去掉 `disable-model-invocation`（H2：P6 要调用它） |
| `wayfinder` | 第 6 步 → P2；`mmw:map` → `docs/agents/issue-tracker.md`；`interface-and-remake.md` → `mmw/references/` | 上游原文加宿主中立改写 | 是（宿主中立改写保留，merge-note 记） | 模型（H2） |
| `prototype` | 规则 6 的「之后做什么」、`UI.md` `## Next`、脚手架时机 → P1、P3；state list 格式 → `design-pages/references/state-list-format.md`（W6） | 上游 + EXP 分支（`EXP.md`、`evidence-page.md`，能力扩展，旁加文件） | 上游文件回原文 | 模型 |
| `grilling` | 第 28–44 行 → mode `## Autonomy`、`shared.md` 规则 1 与 **principle-attack-the-premise**、**principle-redesign-from-first-principles**、**principle-fix-root-causes**、**principle-subtract-before-you-add** | 上游 28 行 | 是 | 模型 |
| `grill-with-docs` | 第 7 行末句 → P1 **Spec** | 上游 | 是 | 用户 |
| `improve-codebase-architecture` | `### 4. Hand the decision on` → mode 路由行（R4 V12：整节是本仓加的） | 上游 + 改用 `diagram-design`（调用方限定被调能力，L7 C.2） | 是（除 diagram-design 用法） | 用户 |
| `codebase-design` | 第 10 行路由声明 → 删 | 上游 + 第 16 行术语放宽（能力改动） | 是（除第 16 行） | 模型 |
| `tdd` | 第 22、38 行票语句 → P16 限定句 | 上游 + 第 26 行宿主中立 | 是（除宿主中立） | 模型 |
| `resolving-merge-conflicts` | 第 2 步票语句 → P16 **Integrate and run** | 上游 + 「clean merge 变红」扩展 | 是（除扩展） | 模型 |
| `setup-matt-pocock-skills` | 第 17、51、63 行 → P8 | 上游 + `AGENTS.md` 写法 | 是（除写法） | 用户 |
| `writing-for-agents` | 第 8 行 → 删；SSR、RSS → `docs/skill-set/` | 上游原文 | 是 | 模型 |
| `to-questionnaire` | — | 上游 | 是 | 模型（H2：P1 调用） |
| `diagnosing-bugs`、`domain-modeling`、`research` | — | 上游原文（零差异，R14 §4.2） | 已是 | 模型 |
| `grill-me`、`handoff`、`teach`、`wait-what`、`wizard` | — | 上游 + 宿主中立或能力改动（`VISUAL.md`、工作区规则、bash 3.2） | 原样 | 按现状 |
| 残留 `ask-matt`（未装） | 主流程 → P1、P4；On-ramps → P2、P5、P6；Codebase health → 路由行；Phase boundaries → `mmw/references/phase-boundaries.md` | — | 恢复上游原文，不安装 | — |
| `diagram-design`（第二个上游） | — | 原样 | — | 模型 |

### 4.2 MMW 自有能力

| 技能 | 剥离 → 去处 | 剩下（纯能力） |
|---|---|---|
| `dispatch` | **解散**：description 与 `## Find your moment` → mode 路由表与 Non-negotiables；`## On waking` → mode `## Where you are`；`night.md` → P14；`one-ticket.md` → P15；`inside-a-ticket.md` → P17；`editing-models.md` → `setup-mmw`；脚本 → `mmw/scripts/`，`models.py`、`hosts.json` → `setup-mmw/scripts/` | — |
| `setup-mmw`（新） | — | 改 host、model、effort、runner（`models.py config` 的 `show`、`set`、`runner`，加只读 `config get <role>`）；读 `install.sh --check` 的输出；开任务板一句。对应 pstack `setup-pstack` |
| `verify-ticket` | description「Use when … a batch is about to be published」的时机 → P1、P14；第 16 行与 `## Reached from here` → mode 触发行与 P16；`sub-issues.md` 第 11 行 → 事件链 W1（`anchors.py` 与 P14、P16 的表）；第 13–23 行 kind 表 → P16；`linting.md` 的「何时」→ P1、P14；`resume_at` → `mmw/scripts/status.py`（`dispatch.sh where`） | 判据怎样跑、`CHECK`/`EXPECT`、事件格式、子票命令、lint 与 publish、closeout 的格式检查；脚本 `verify-ticket.py`、`events.py`、`issue_tree.py`、`gate-check/` |
| `ui-acceptance` | description「before writing a page ticket's code」→ mode 触发行；表第 1 行随 `writing-interface-code.md` 搬入变成本技能自己的行；第 38 行（worker 开 `fault` 后停）→ P16；规则 3–5 的理由 → **principle-human-steps-stay-human**、**principle-rerun-dont-reroute** 加本地机制 | 规则 1、2（租约、进程）、四个 oracle、五份 reference、`writing-interface-code.md`（← implement，三处「closing step 1」改成步骤名引用或删，W3） |
| `design-pages` | `edit-pages.md` `## Next`、`pull.md` `## Reached from here`、`## A contract child answered by this pull` → P3、P14；第 21 行「派出的 worker 从不做」→ P16 | pull、draw、edit、design-system、两份模板、`state-list-format.md`（新收） |
| `write-screen-contract` | `## Next` → P3、P1；第 8–10 行理由 → **principle-baseline-is-a-contract** | 第 1–7 步、`Re-runs`、格式文件与三个脚本 |
| `retro` | 第 8 行、第 186 行 → P14 **Retro**；第 16–35 行理由 → **principle-clues-are-not-evidence**、pstack 三条 | 第 1–13 步、`## Prevention destinations`（去处补 `principle`、`playbook`、`mode`，第 7.3 节） |
| `advisor` | `consulting.md` `## When it is worth a session` → mode 触发行 | 发起方怎样写 brief、怎样对待回答；`advising.md` 是另起会话的简报 |
| `exe-release` | 第 1–5 步、`driving.md` → P10 | `key.md`（写 release manifest）、`new-product.md`（把产品接进出包系统）、脚本 |
| `code-checkers` | 第 6、8 步的「接入顺序」→ P8 | 探测、配置、git hook |
| `manage-agents-md` | 第 50 行 → mode `## Subagents` | 其余 |

### 4.3 新拆出的内容

| 新位置 | 来源 | 为什么在这一层 |
|---|---|---|
| `mmw/references/writing-code.md` | `implement` 第 24–27 行（grep 调用方、先找现成、加文件先写理由、保留清单），各句换成点名 **principle-migrate-callers-then-delete-legacy-apis**、**principle-subtract-before-you-add** 与 `shared.md` 规则 14 | P4、P16 两个 playbook 共用；它不产出交付物，不是能力技能（L7 C.1 第 6 问） |
| `ui-acceptance/references/writing-interface-code.md` | `implement/references/` | 按设计基准写界面的方法属于持有 oracle 的能力；也消掉 N10 B7 的来回跳转 |
| `design-pages/references/state-list-format.md` | `prototype/UI.md` 第 6 步 | `pull_design.py` 第 983 行按字面读它（R12 M21），格式归写读双方里的能力一侧 |
| `setup-mmw` | `dispatch` 的配置部分 | 可以单独调用的配置能力 |

---

## 5. 原则层

### 5.1 存放与引用形式（满足 H2）

- **存放**：`mmw/principles/principle-<slug>.md`，普通文件，不是技能。理由：pstack 的原则全带 `disable-model-invocation: true`，照搬成技能在 Claude Code 上按名调不到（H2）；装成模型可触发的技能又会让二十多条 description 进每个会话的技能列表并与能力技能抢触发（R13 E5）。
- **格式**：与 pstack 相同。frontmatter 只有 `name`（等于文件名去掉 `.md`）与 `description`（情境触发 + 规则一句）；正文 `# <Title>`、一到三句规则、`**Why:**`、`**Pattern:**`，可选 `**Boundaries:**`、`**Stop:**`、`**The test:**`、「Distinct from …」。`**Why:**` 写观察到的故障与用户决定的内容，出处（ADR 号、行号）写进记录这次升级的 ADR，不进原则文件（R12 K-19 的做法）。
- **引用写法只有一种**：`**principle-<slug>**`（pstack mode 索引的写法）。`check_wiring.py` 核对每个引用都解析到 `mmw/principles/` 下的文件；导入脚本把 pstack 的另外四种写法（L7 E.1 第 1 条）改成这一种。
- **索引**：mode `## Principles` 每行由原则文件的 `description` 生成或由 lint 核对一致，修掉 pstack「一句话摘要在四处重复、措辞不一」（L7 E.1 第 14 条）。
- **调用方写法**：点名一次，加一句本地限定或本地后果（L7 C.2），不复述原则正文。上游技能正文里不加引用（上游回原文）。
- **点名义务**：mode `## Non-negotiables` 首段；无人会话写在交付物里（第 6 节）。

### 5.2 MMW 自建的原则（11 条）

「规则」一列是现有原文的归并，不新写；「引用方」是升级后点名它的组件。

| slug | 规则（归并自） | 理由出处 | 引用方 | pstack 近邻 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 什么都没做的检查、什么都没交的交付，读起来与通过无异；所以检查要能证明自己会失败（negative control），红了改产品不弯检查，查不了就写「查不了」（PC1、PC2、PC22） | ADR 0008 第 8 行；`implement` 第 22 行末两句；`night.md` 第 7 行；`ui-acceptance` 第 10 行 | P1 **Tickets**、P14 首段与 `#### Closing pass` 第 2 问、P16 `#### Ticket rules while writing`、`to-tickets` 第 84 行、`ui-acceptance` 第 10 行、`code-checkers` 第 5 步 | `prove-it-works`、`test-behavior-not-implementation` 末句 |
| `the-tracker-is-the-state` | 你在哪一步由持久记录（票上的事件、仓库）决定，会话记忆只是会丢的副本（PC5） | `dispatch/SKILL.md` 第 8 行；`night.md` 第 5 行；ADR 0019 | mode `## Where you are`、P1、P11、P14、P16 的 `**Where you are.**`、`exe-release` 的 driving 规则簇 | pstack `session-pickup.md` 第 6 行 |
| `woken-not-polled` | 谁都不轮询另一个代理；起了别人就结束回合，由事件叫醒（PC4） | ADR 0010；`night.md` 第 11 行；`dispatch/SKILL.md` 第 25–28 行 | P14、P15、P16 **Review round**、P17 | 无 |
| `rerun-dont-reroute` | 被打断的命令原样重跑；拒绝、产品连不上、流水线自身故障，按流水线给的路由上报，不绕路、不写重试循环、不换 host 或 runner（PC17 的重跑一半、PC18）。`**Boundaries:**` 与 `shared.md` 规则 11 的读法：规则 11 管「自己能完成的」（「If you can finish it, it is already finished」），流水线自身故障不是自己能完成的（读法，推断） | ADR 0010 第 35 行、0017、0018；`ui-acceptance` 规则 4、5；`implement` 第 18 行 | mode `## Where you are` 第 1 步、Non-negotiables 流水线故障行、P14 `fault` 行、P16 **Claim** | `make-operations-idempotent`、`fix-root-causes` |
| `baseline-is-a-contract` | 基准（用户的答案、胜出的原型、签字的页面）是别人已经付过代价的决定；不成立就开 `contract` 子票，从不悄悄改或绕着加（PC8） | `implement` 第 22 行「A baseline is a decision someone already paid for」 | P16、P14 `#### Authority order`、`design-pages` 第 10 行、`write-screen-contract` 第 18 行、`to-tickets` 第 174 行 | 无 |
| `refusals-name-one-next-step` | 读拒绝的一侧：拒绝点名一个事实、说为什么、给唯一下一步；收到拒绝的代理照那一步做，不即兴（PC3 的读者侧；写脚本的一侧留在 `CODING_STANDARDS.md`） | ADR 0008；`CODING_STANDARDS.md` Skills and scripts 第 4 条 | mode Non-negotiables、P14 **Each wake**、`ui-acceptance` 第 26、35 行 | 无 |
| `a-reader-who-did-not-write-it` | 判断交给一个没写它的读者（另一个上下文、另一个会话）（PC20） | `code-review` 第 8 行；`to-tickets` 第 63 行；`tdd` 第 38 行；`consulting.md` 第 9、37 行 | P4 **Review**、P16 **Review round**、P18、mode 顾问触发行 | pstack mode 第 95 行「A second opinion is the same prompt against a different model」 |
| `one-home-per-meaning` | 一个意思只有一个权威的家，别处点名它（PC16） | `writing-for-agents` 第 78 行；SSR 第 17、40 行；`design-pages` 第 6 行 | P9、`docs/skill-set/SKILL-SET-RULES.md`、`check_wiring.py` 的依据 | `encode-lessons-in-structure`（部分） |
| `human-steps-stay-human` | 只有人能做的一步单列出来，代理不代做，也不伪装成做了（PC29） | `ui-acceptance` 规则 3；`person-ticket.md` 第 3 行；`wizard` description；`exe-release` 第 5 步 | mode 触发行、P10 **User install test**、`ui-acceptance` 规则 3 | 无 |
| `secrets-stay-out-of-artifacts` | 凭据与个人数据不进任何产物（票、Memory、handoff、日志）（PC28） | `diagnosing-bugs` `## Redact`；`saving-memory.md` 第 4–5 行；`handoff` 第 14 行；`product-answers.md` 第 96 行 | mode Non-negotiables、`references/saving-memory.md`、P11、P12 | pstack 留在各技能里（L7 C.2 末段）；本判据下它满足四道门槛，照先例留下不算理由 |
| `clues-are-not-evidence` | Memory、顾问的话、别人的报告、axis 的 finding 是线索，行动前对当前仓库证据核实（PC11） | `implement` 第 47–49 行；`session.md` 第 89、101 行；`retro` 第 58、63–66 行；`advising.md` 第 15 行；`research` 第 10 行 | P7、P16 `#### Memory`、P18 **Verify every finding**、`retro` | `prove-it-works`（部分） |

### 5.3 由 pstack 原文落位的原则（13 条，U-D3）

它们正好接住 MMW 已有、但没有独立陈述的规则（R14 §3.2）。落位方式是导入脚本复制原文、改文件名与引用写法，不改正文。

| pstack 原则 | 接住的 MMW 规则 | MMW 调用方 |
|---|---|---|
| `prove-it-works` | PC14 的「引用看到的那一行」、PC11、PC22 的一部分 | P11 第 5 步、P16 **Audit**、P14 `#### Closing pass` 第 3 条 |
| `test-behavior-not-implementation` | PC23；PC2 的 negative control 一句 | P16 **Write the code**、P4 |
| `separate-before-serializing-shared-state` | PC12（一个文件同一时刻一个写者；Owns 两档） | P16、P14 `#### Closing pass` 第 1 问、`to-tickets` 第 44、90 行 |
| `make-operations-idempotent` | PC17（写脚本的一侧；另进 `CODING_STANDARDS.md` 一条） | `CODING_STANDARDS.md`、**principle-rerun-dont-reroute** 的 Distinct from |
| `attack-the-premise`、`redesign-from-first-principles`、`fix-root-causes` | PC19（`grilling` 第 30–44 行、`retro` 第 30–35 行） | P1 **Grill**、P5、`retro` |
| `subtract-before-you-add`、`laziness-protocol`、`migrate-callers-then-delete-legacy-apis` | PC21（`implement` 第 24–26 行）、PC24 的一部分 | `references/writing-code.md`、P18 Standards 简报 |
| `encode-lessons-in-structure` | PC25、PC7、PC6 的一部分；「Route to the right layer」 | P9、`retro` `## Decide` |
| `guard-the-context-window` | PC26 | mode `## Subagents`、P11 |
| `build-the-lever` | PC7 | P9、`CODING_STANDARDS.md` |

不落位的 pstack 原则（留待用户以后按需导入，结构上已能直接落位）：`never-block-on-the-human`（与 `shared.md` 规则 1 的「What only I can decide」范围不同，导入会造成两个家）、`minimize-reader-load`、`model-the-domain`、`boundary-discipline`、`type-system-discipline`、`foundational-thinking`、`outcome-oriented-execution`、`experience-first`、`exhaust-the-design-space`、`sequence-verifiable-units`。

### 5.4 与 `shared.md` 的关系（任务边界 S）

- `shared.md` 是用户写给所有项目的全局规则，经 `install.sh` 发给 Claude Code、Codex、Pi、Grok；Cursor 的用户级提示词在应用里维护（根 `AGENTS.md` Key Conventions）。MMW 不改写它。
- 分界：`shared.md` 已经说了的，MMW 不建原则，调用方点名「`shared.md` 规则 N」：PC9 → 规则 1（外加 mode `## Autonomy` 的无人出路）；PC10 → 规则 10；PC13 → 规则 13；PC14 → 规则 15；PC21 的「先搜现成」→ 规则 14；PC24 → 规则 1「Anything outside the scope I gave you is asked about, not done」。
- 优先级：`shared.md` 高于任何原则与 mode。与 pstack 原文冲突时（例：pstack mode「No long-dash character anywhere」对 `shared.md` 自己用 em dash），给用户的回复以 `shared.md` 为准（R13 I-16）。
- 唯一的复制：mode `## Autonomy` 抄一次产品事项清单，因为 Cursor 收不到 `shared.md`（H1）。Cursor 应用里的规则是否已有同样内容，用户决定是否补（U-D5）。

### 5.5 外来原则与 MMW 原则重合时

按 pstack `reflect/references/synthesizer.md` 第 17–22 行的四条（Existing-skill-first、Decision-changing、Structural-mechanism check、Already-covered）判：
1. 触发情境相同、规则相同：只留一个文件，另一个的独有句并进 `**Pattern:**`，改动写 merge-note；调用方全部改点那一个。
2. 触发情境不同：两个都留，各自写「Distinct from」。
3. 与 `shared.md` 同义：不导入。
4. 能由 lint、脚本或 hook 低成本强制：不导入成文字，转 `CODING_STANDARDS.md` 或 `check_wiring.py`。

---

## 6. 执行协议

**人在场的会话**（照 pstack mode 第 117 行）：匹配到 playbook 后，开一个待办列表，前几项是该 playbook 的编号步骤原样抄入（长 playbook 只抄 `#### Steps`）；决定不做的步骤留在列表里，写一行 `skip: <reason>`；`feature.md` 式的 `n/a: <reason>` 与「Mandatory: no skip-with-reason escape」照原文保留。回复里点名改变了决定的原则，只点名本会话读过全文的。

**无人会话**（H6：没人看待办；压缩后待办可能丢失）：
- 仍然抄进待办（宿主有待办工具时，U-4），但待办不是记录。
- `skip:` 行与点名原则的句子写进本 playbook 的交付物，不新增格式：worker 写在 `Decisions I made on my own` 里，形如 `skip: **Audit**: <reason>`；reviewer 写在 `REVIEW` 报告里；orchestrator 写在它为每个决定留下的理由评论里（`night.md` 第 5 行的要求）。MMW 的票事件就是 pstack `show-me-your-work` 的等价物，只写一处（R13 E7）。
- 位置不靠待办：`dispatch.sh where` 从事件算出步骤名。
- 可检查的部分：`verify-ticket.py --closeout` 已检查收尾评论格式；是否再核对「每个 `#### Steps` 步骤名要么在事件里有痕迹、要么有 `skip:` 行」，推断可行，放进 U-10 决定值不值得。

---

## 7. 脚本与 hook

### 7.1 `anchors.py`：角色与锚点的唯一登记处

新文件 `mmw/scripts/anchors.py`，不导入任何模块（R12 K-2 的做法）。内容：
- `ROLES`：角色 → playbook 文件、启动提示词首句模板、`models.json` 角色键。worker → `playbooks/ticket-work.md`；reviewer → `playbooks/ticket-review.md`；advisor → `advisor` 技能 `references/advising.md`；orchestrator（`by=open`）→ `playbooks/night.md`；orchestrator（`by=open-ticket`）→ `playbooks/one-ticket.md`；worker（`by=adopt`）→ `playbooks/ticket-adoption.md`。
- `POINTERS`：收件角色加 `by` → 指针文字（只含技能名、技能内路径、小节或步骤名）。
- 所有脚本印出的文字锚点：步骤名（`**Review round**` 等）、`## Where you are`、`## Five rules while the product is running` 等。

读者：`dispatch.sh`、`relay.py`、`watchdog.py`、`status.py`、`tool-guard.py`、`turn-guard.py`、`mode-hook.py`、`check_wiring.py`、`tests/relay`。「脚本按字面点名文字」由此集中到一处，lint 核对每个锚点在目标文件里存在（任务给定的做法：字面引用集中到锚点表再改）。

### 7.2 要改的脚本（为什么）

| 脚本 | 改动 | 为什么 |
|---|---|---|
| `dispatch.sh` | 路径随搬家（`scripts/` 相对 `mmw` 技能目录）；启动提示词首句改为点名 mode 与 playbook（第 2.2 节），`AUTONOMOUS`、`PRODUCT_RULES` 删（规则的家是 mode `## Autonomy` 与 P16 的规则簇，提示词只放数据：`unattended`、票号、Memory 索引）；设 `MMW_ROLE`、`MMW_PLAYBOOK`；新子命令 `where <n 或 spec> --role <r>`；第 79 行头注释改指 mode；`check` 失败时不再自动跑完整 `install.sh`，只报告（U-D2） | R13 E8：提示词里放规则与 SSR `### Prompts written for other agents` 冲突（N10 第 8 节）；「advice, not permission」（pstack `worktree-cleanup.md` 第 2 步）；R12 M7 |
| `status.py` | 收下 `verify-ticket.py` `resume_at` 的计算，按角色印 `RESUME: <playbook> **<步骤名>**`；orchestrator 的取值补上 **Lint the batch** 与「`spec.retroed` 已记录、未验收 → **Hand to the morning**」 | 位置是 mode 层的事（第 0 节第 2 条）；R4 V6、V10，R12 M17、M18 |
| `verify-ticket.py` | 删 `resume_at` 与 `--preflight` 的 `RESUME:` 行（由 `where` 接手）；docstring 的过时引用随之消失 | 能力脚本不知道 worker 的步骤（L7 B.2 第 3 条） |
| `relay.py` | `wake_text` 同一行接指针；`WAKES` 不变 | H4；R4 V3–V5 |
| `watchdog.py` | 八种告警各在同一行写出点名 P14 或 P15 `#### Wake table` 行名的指针；第 735、780 行「night.md's Exit codes of resume」改从 `anchors.py` 取 | H4；R4 V2、R12 M16 |
| `turn-guard.py` | 拦截文字保留命令，末尾接 P14 **Each wake** 的指针 | W1 断点（R4 V7） |
| `tool-guard.py` | `NO_QUESTION` 改成一句指针「Nobody is at the screen: the mmw skill's `## Autonomy` names your way out.」（≤256 字符，测试第 450 行）；`REFUSAL` 保留（它就是 `--closeout` 的下一步） | 一个事件一条指令；V9 的两处出路不一致由 mode 一处解决，也覆盖 reviewer、advisor（N11 缺边） |
| `mode-hook.py`（新） | 第 2.2 节的三种注入：`SessionStart`、`SubagentStart`、`UserPromptSubmit`；只在 MMW 仓库或 `MMW_ROLE` 有值时印一行 | pstack `mode: true` / `reminder` 的替代（H1） |
| `retro.py` | `DESTINATIONS` 加 `principle`、`playbook`、`mode`（第 31–32 行，已核实现有 8 个） | E11：教训按层回流，否则分层会重新变乱 |
| `models.py`（搬到 `setup-mmw`） | 加 `config get <role>`，只读 | I-5：让「your configured <role> model」有值可查 |
| `board/board_data.py` 第 27 行、`codeversion.py`、`retro.py` 的 `VERIFY` 路径、`install.sh` 读 runner `MMW_USES` 的路径 | 路径随搬家 | 字面引用，照判据一起改（R12 M22） |
| `install.sh` | `skills.txt` 变化；hook 路径指向 `~/.agents/skills/mmw/scripts/`；登记 `mode-hook.py` 的事件（各宿主有的才登记）；`--check` 列出开着的 watch（R12 K-32） | hook 是宿主来调的，路径变了要重新登记（`install.sh` 第 309–315 行注释） |

### 7.3 脚本怎样点名 playbook 与步骤

- 只按 `anchors.py` 里的名字点名：`mmw playbooks/<file>.md **<步骤名>**`、playbook 的 `**Where you are.**` 或 mode 的 `## Where you are`，不按编号（修 R12 M30 那类「closing step 1」）。
- 脚本送进活会话的一切都是一行（H4）；启动提示词也写成一行（不依赖 U-9）。
- 脚本不做判断：`where` 只报告位置，下一步由 playbook 的步骤决定（pstack「The bucket is advice, not permission」）。

### 7.4 接线 lint：`mmw-v2/tests/lib/check_wiring.py`

与 `check_module_paths.py` 同类，每个套件先跑。规则：
1. playbook 骨架：`### <Name>`、所有权行、编号步骤带粗体步骤名、`**Reply:**`。
2. 每个步骤点名的技能在 `skills.txt`，点名的 playbook、原则、reference、脚本子命令存在。
3. 方向：能力技能正文不出现 playbook 文件名、角色词（worker、reviewer、orchestrator 作角色）、`night`；原则只指向原则或能力技能；脚本里的文字锚点只来自 `anchors.py`。上游技能正文与 squash 原文的差异只能是登记过的调用开关与 merge-note 列出的能力改动。
4. 跨组件引用不按步骤编号。
5. 原则引用一种写法，全部可解析；mode 索引与原则 `description` 一致。
6. 路由表每行指向存在的 playbook，每份 playbook 有一行；`.mmw/playbooks/INDEX.md` 同理。
7. `anchors.py` 每个锚点在目标文件里存在；`relay.py` `WAKES` 的每个事件、`watchdog.py` 的每种告警在对应 playbook 的 `#### Wake table` 有一行（W1）。
8. 每个 `dispatch.sh` 子命令至少被一个 playbook 步骤或 mode 触发行点名（没有孤立的 lever）。

`install.sh --check` 对已安装 checkout 跑规则 2、6、7 的只读部分（依赖可解析，对应 benny 安装后「confirm … resolve」，R13 E10）。

### 7.5 仓库文档随之改的规则

- `SKILL-SET-RULES.md` 搬到 `docs/skill-set/`（R12 K-38），事实 7 与 `### Hand-offs` 第 5 条改写为：「一个技能的位置由 playbook 决定；能力技能以它交回什么结尾，不写下一步」。原句防的两件事（第二份副本漂移；某一跳找不到下一步，#538）由「顺序只有一个家」加 lint 规则 2、6 防住。
- `CODING_STANDARDS.md`：脚本的文字锚点只经 `anchors.py`；可重跑规则（`make-operations-idempotent`）。
- `TESTING.md`：接线 lint 一句；锚点表改动需要的套件。
- 新 ADR（0032 起）记录本次架构决定：mode、playbook、原则三层；`dispatch` 解散；修订 ADR 0020 的唤醒文字、ADR 0015 的 axis 调用方式（axis 子代理读 mode 的 `references/review-axes/`，仍按技能名解析，不读绝对路径）。
- `CONTEXT-MAP.md` 与 `docs/contexts/toolbox/CONTEXT.md`：新词条 mode、playbook、principle、slot、role pointer；约 85 处技能路径随搬家（R12 §2.8）。

---

## 8. pstack 导入接口

### 8.1 直接落位

| pstack 组件 | 落位 | 登记 | 改写（导入脚本做） |
|---|---|---|---|
| playbook `playbooks/<f>.md` | `mmw/playbooks/<f>.md` | mode 路由表一行 | 原则引用统一写法；「Run **Opening a PR**」→ delivery 槽位；「the matching control skill」→ control 槽位；`subagent_type: "poteto-agent"` → mode `## Subagents` 简报；运行中从 trunk 重读的句子删掉（H5，`autopilot-full.md` 第 6 步、`multi-phase-plan.md` 模板）。同名时（`bug-fix`、`investigation`、`session-pickup`、`pause-safely`、`authoring-a-skill`）是合并，按第 5.5 节四条 |
| 原则 `skills/principle-<s>/SKILL.md` | `mmw/principles/principle-<s>.md` | mode 索引一行 | 删 `disable-model-invocation`；相对链接 `../principle-x/SKILL.md` → `principle-x.md` |
| 能力技能 `skills/<name>/` | `mmw-v2/upstream-pstack/skills/<name>/`（subtree），`skills.txt` 加 `ps/<name>` 一行（新前缀，与 `engineering/`、`self/`、`dd/` 并列） | `skills.txt` 一行 | 被 playbook 点名、要模型调用的，去掉 `disable-model-invocation`（H2），merge-note 记；description 只留「是什么、直接调用时怎么说」，跨技能的「何时用」进 mode Non-negotiables |
| mode 的 reference、script | `mmw/references/`、`mmw/scripts/` | 被 playbook 相对路径引用，不改就能解析 | 无 |
| agent 定义 `agents/*.md` | 不导入成文件；内容进 mode `## Subagents` 简报 | — | ADR 0015；H3 |
| 自动化包 `automations/benny/` | 不整体导入；MMW 的夜间流水线就是它的等价物（R13 E10） | — | 共享的能力与原则照上两行导入 |

### 8.2 `references/slots.md`：Cursor 专有机制与槽位的解析表

| pstack 依赖 | MMW 解析 | 依据 |
|---|---|---|
| `mode: true`、`reminder` | `mmw` 技能加 `mode-hook.py` 加启动提示词 | H1；第 2.2 节 |
| `alwaysApply` 的 `pstack-models.mdc`；「your configured <role> model (default …)」 | 会话内子代理的角色一律按 `inherit-parent`（本会话模型，H3）；需要另起会话的角色查 `models.py config get <role>` | R13 I-5 |
| `Task` 的 `model`、`run_in_background`、`readonly` | 不指定模型（H3）；后台按宿主（U-4）；只读靠简报一句 | ADR 0015 |
| `subagent_type: "poteto-agent"` | 宿主通用子代理 + `## Subagents` 简报首句 + `SubagentStart` 注入 | 第 2.2 节 |
| `AskQuestion` | 人在场：在对话里问（`shared.md` 规则 1）；无人：mode `## Autonomy` 的出路 | H6 |
| `/loop`、`/goal`、cloud agent | relay 唤醒、watchdog、turn guard；另起会话用 `dispatch.sh start` | ADR 0010、0020 |
| `agent-transcripts/` | 各宿主的会话记录位置一行一个（U-8）；另有 tracker 事件与 `handoff` 文件 | R13 I-14 |
| 内置 `create-skill` | `writing-for-agents` | — |
| control 槽位（`control-ui`、`control-cli`） | 浏览器与 Web → `playwright-cli` 或 `ui-acceptance` 的 oracle；本机窗口 → `computer-use`；Orca 内置浏览器 → `orca-cli`；CLI → 直接跑。消费仓库可在 `.mmw/target.json` 覆盖；缺了就 fail closed（ADR 0008） | R13 I-8 |
| delivery 槽位（「Run **Opening a PR**」） | 票里：closeout，由 orchestrator land（ADR 0025）；白天直接改：按仓库的交付约定（本仓库是根 `AGENTS.md` Gotchas 第 1 条四步）；用 PR 的仓库：原样用导入的 `opening-a-pr.md`。`babysit`、`shipping`、`autopilot-*` 只在用 PR 的仓库路由，路由行写明条件 | R13 I-10 |
| forge 槽位（`gh` / Origin） | `docs/agents/issue-tracker.md`，一处 | R13 I-11 |
| worktree 约定 | `.worktrees/` 下，避开 `issue-<n>`、`merge-<branch>` | 根 `AGENTS.md` Key Conventions |

### 8.3 PR 与 MMW 落地方式的对应

pstack 的交付单位是 PR（7 个 playbook 以 Opening a PR 收尾，L7 E.1 第 3 条）。MMW 夜里的交付单位是票：worker `--closeout`，orchestrator `advance` 合进 project branch（ADR 0025），早上 `finish`。对应：`opening-a-pr.md` 的 **Commits** 段 ↔ worker 的提交与 `wip(#<n>)` 约定；**Descriptions** ↔ 收尾评论；**Babysit** ↔ orchestrator 的 **Each wake**；**Shipping** 的「independent per-PR verdict」↔ reviewer 与 `reverify`。在不用 PR 的仓库，导入的 playbook 最后一步经 delivery 槽位落到上表。

### 8.4 多模型面板（H3）

- H3 下跨厂商面板只能是多个另起的会话。新子命令 `dispatch.sh panel <brief> --role <panel-role>`：按 `models.json` 里该角色的列表（列表长度即扇出数，照 `setup-pstack` 第 3 步 (c)）逐项另起会话、送同一份简报，收齐后在一个文件里给发起方。`dispatch.sh advise`（ADR 0014）是单成员的先例。
- 没有 `panel` 时（批 5 之前，或 U-6 表明不划算），导入的 `arena`、`architect`、`interrogate` 以同模型面板运行，mode `## Subagents` 写明它失去「Agreement is high-signal」（pstack mode 第 95 行）的那部分价值。

### 8.5 导入一件组件要动几处

playbook：1 个文件 + 路由表 1 行。原则：1 个文件 + 索引 1 行。能力技能：subtree pull + `skills.txt` 1 行 + merge-note。改写全由 `import_component.py` 按 `pstack.map` 做；之后跑 `check_wiring.py` 与 `install.sh --check`。

### 8.6 私有 playbook **Component import**（本仓库 `.mmw/playbooks/component-import.md`）

1. **Pull.** `git subtree pull` 到 `mmw-v2/upstream-pstack/`（先对 `cursor/plugins` 做 `subtree split --prefix pstack`，R4 D7.2）。
2. **Check the slots.** 组件依赖的槽位在 `slots.md` 都有解析吗；依赖 PR 的只在用 PR 的仓库路由；依赖跨厂商面板的看 `panel` 在不在。
3. **Import.** `import_component.py <path>`。
4. **Merge or keep.** 与已有同名或同义组件按第 5.5 节判。
5. **Validate and deliver.** 走 **Authoring or modifying a skill** 的 **Validate**、**Record**、**Deliver**。

---

## 9. 改造前后对照表

动作词：**搬**（整体换位置）、**拆**（分给几处）、**删**（去掉，内容已有别处的家）、**回原文**、**改写**、**新建**、**本层**（按类型核对后本来就在该层，不是例外）、**留（H#）**（按类型该搬、因硬约束留下，写明编号）。部件清单沿 N1–N10 的分组，与 R12 第 4 节逐行对应。

### 9.1 N1 dispatch

| 部件 | 升级后（层、位置） | 动作 |
|---|---|---|
| `dispatch/SKILL.md` description | 触发分给 mode 路由表（P14、P15、P17）与 Non-negotiables；改模型部分进 `setup-mmw` description | 拆；技能解散 |
| 第 8 行 | 前半句 → **principle-the-tracker-is-the-state**；脚本自己找路径一句 → `mmw` 的 `scripts/` 说明 | 拆 |
| `## Find your moment` 六行 | mode 路由表与两条触发行 | 搬 |
| `## On waking` | mode `## Where you are` | 搬 |
| `references/night.md` | P14 `playbooks/night.md`（逐节，见第 3.3 节） | 搬，补 V6–V8、M16 缺行 |
| `references/one-ticket.md` | P15 | 搬 |
| `references/inside-a-ticket.md` | P17 | 搬 |
| `references/editing-models.md` | `setup-mmw/references/` | 搬 |
| `hosts.json`、`models.py` | `setup-mmw/scripts/` | 搬；`models.py` 加 `config get` |
| `dispatch.sh`、`relay.py`、`watchdog.py`、`status.py`、`statedir.py`、`ghlist.py`、`runners/*.sh` | `mmw/scripts/` | 搬 + 第 7.2 节改写 |
| `AUTONOMOUS`、`PRODUCT_RULES` | mode `## Autonomy`；P16 规则簇指针 | 删（提示词只留数据） |
| 启动提示词三处（第 1949、1967、2072 行） | 首句点名 mode 与 playbook | 改写 |
| `dispatch.sh check` 自动重装 | 只报告 | 改写（U-D2） |
| `tool-guard.py`、`turn-guard.py` | `mmw/scripts/` | 搬；`NO_QUESTION`、拦截文字改成指针 |
| 新 `anchors.py`、`mode-hook.py`、`where` 子命令 | `mmw/scripts/` | 新建 |
| `watchdog.py` 告警的一行形状 | 本层（脚本），每行接指针 | 本层；一行是 H4 的要求 |
| `docs/contexts/night/CONTEXT.md`、`how-it-works.md` | 仓库文档 | 本层；改路径与 **role pointer**、**wake** 词条 |
| ADR 0009、0010、0016–0018、0020–0025、0027 | 仓库文档 | 本层；新 ADR 修订 0020 一句 |

### 9.2 N2 verify-ticket

| 部件 | 升级后 | 动作 |
|---|---|---|
| `SKILL.md` 第 8–12 行 | 能力正文；理由换成点名原则 | 本层 |
| description 的时机半句 | P1、P14 | 拆 |
| 第 16 行、`## Reached from here` | mode 触发行、P16 | 删（去处已有） |
| `## Find your moment` 表 | 能力内部的分支表（切子票、lint） | 本层 |
| `references/linting.md` | 命令留能力；「何时」→ P1、P14 | 拆 |
| `references/sub-issues.md` | 命令留能力；第 11 行 → `anchors.py` 与 `#### Wake table`（W1）；第 13–23 行 → P16 `#### Sub-issue kinds` | 拆 |
| `verify-ticket.py` `resume_at` | `mmw/scripts/status.py`（`where`） | 搬 |
| `verify-ticket.py` 其余、`events.py`、`issue_tree.py`、`gate-check/` | 能力脚本 | 本层 |
| `upstream-unlazy/`、`merge-notes/unlazy.md` | 外来合集、仓库文档 | 本层 |
| `docs/contexts/ticket-run/`、`tickets/CONTEXT.md` | 仓库文档；`RESUME:` 词条改为 `where` | 本层，改写 |
| `tests/verify-ticket/`（`test_preflight.py` 第 450–517 行） | 断言随 `RESUME:` 搬到 `tests/dispatch` 的 `where` 场景 | 改写 |

### 9.3 N3 implement、code-review、tdd

| 部件 | 升级后 | 动作 |
|---|---|---|
| `implement/SKILL.md` 第 3、6、8 行 | 上游 description 与首句回原文；「命令写裸名」约定 → P16 首段 | 回原文、拆 |
| 第 10–34 行 | P16 **Claim**、**Read in**、**Write the code** 与 `#### Ticket rules while writing`；第 24–27 行通用部分 → `mmw/references/writing-code.md` | 拆 |
| 第 36–68 行 | P16 `#### Memory` | 搬 |
| 第 70–101 行 | P16 `#### Steps` 第 4–10 步与 `#### ABANDON kinds`；步骤名替代编号（W3） | 搬 |
| `references/writing-interface-code.md` | `ui-acceptance/references/` | 搬；三处「closing step 1」改名引用 |
| `references/saving-memory.md` | `mmw/references/` | 搬 |
| `implement`（上游原文） | 不安装（U-D1）；内容是 P4 骨架 | 回原文 |
| `code-review/SKILL.md` | 上游双轴原文，安装 | 回原文 |
| `code-review/references/session.md` | P18 | 搬 |
| 四个 axis 文件 | `mmw/references/review-axes/`；Standards 中复写的 smell baseline 改为点名上游 `code-review` §3 | 搬 |
| `tdd/SKILL.md` 第 22、38 行 | P16 限定句 | 搬；`tdd` 回原文（第 26 行宿主中立留，merge-note） |
| `tdd/tests.md`、`mocking.md` | 上游原文 | 本层 |
| `merge-notes/implement.md`、`code-review.md` | 改为记「回原文、内容去了哪里」 | 改写 |
| `upstream/docs/engineering/{implement,code-review}.md`、`skills/engineering/README.md` 两行 | 上游原文 | 回原文 |

### 9.4 N4 to-spec、to-tickets、triage

| 部件 | 升级后 | 动作 |
|---|---|---|
| `to-spec/SKILL.md` | `mmw-v2/skills/to-spec/`（MMW 能力扩展）；上游目录回原文 | 搬（分叉）、回原文 |
| `to-spec` description 触发句、`## Next`、第 2 步闸门后半、`several-specs.md` 的循环 | P1、P3 | 拆 |
| `to-spec` 第 6 行 | `shared.md` 规则 1 点名 + 本地一句 | 改写 |
| `revising-a-spec.md` | 能力（它改的是自己的交付物，L7 C.3） | 本层 |
| `to-tickets/SKILL.md` | 分叉；第 20、160 行 → P1；第 113–119 行 → mode `## Subagents` | 搬、拆 |
| `<issue-template>`、三份 reference | 能力；模板标题登记进 `anchors.py`（W4） | 本层 |
| `triage` description 触发句、第 70、82、90、94 行 | P6、P13 | 拆；`triage` 回原文 |
| `triage` 第 41 行 | `docs/agents/triage-labels.md` | 搬 |
| `triage/references/pipeline-issues.md` | P13 `#### Pipeline issues` | 搬 |
| `AGENT-BRIEF.md` 本仓改写 | 路由句 → P6；其余能力 | 拆 |
| `docs/agents/*.md` | 配置 | 本层；`## Morning queries` 的顺序 → P13（文件留查询命令） |
| 三份 merge-note | 改写 | 改写 |

### 9.5 N5 其他上游技能

| 部件 | 升级后 | 动作 |
|---|---|---|
| `prototype` 规则 6 后半、`UI.md` `## Next`、脚手架时机 | P1、P3 | 拆；上游文件回原文 |
| `prototype` `EXP.md`、`evidence-page.md` | 能力扩展（旁加文件） | 本层 |
| `prototype` `UI.md` state list 段 | `design-pages/references/state-list-format.md` | 搬（W6） |
| `wayfinder` 第 6 步、`mmw:map`、`interface-and-remake.md` | P2；`docs/agents/issue-tracker.md`；`mmw/references/` | 拆、搬 |
| `wayfinder`、`triage`、`to-questionnaire` 的调用开关 | 模型可触发，与上游原文不同 | **留（H2）**：P2、P6、P1 要由模型调用 |
| `grilling` 第 28–44 行 | mode `## Autonomy`、pstack 四条原则 | 拆；回原文 |
| `grill-with-docs` 第 7 行末句 | P1 **Spec** | 搬 |
| `improve-codebase-architecture` `### 4` | mode 路由行 | 搬 |
| `codebase-design` 第 10 行 | — | 删 |
| `resolving-merge-conflicts` 第 2 步票语句 | P16 | 搬 |
| `setup-matt-pocock-skills` 第 17、51、63 行 | P8 | 搬 |
| `writing-for-agents` 第 8 行；SSR、RSS | 回原文；`docs/skill-set/`，事实 7 改写 | 回原文、搬 |
| `domain-modeling`、`research`、`diagnosing-bugs`、`grill-me`、`handoff`、`teach`、`wait-what`、`wizard` | 能力 | 本层 |
| 残留 `ask-matt` | 内容分给 P1、P2、P4、P5、P6、mode；目录回上游原文，不装 | 拆、回原文 |
| 相关 merge-note | 改写 | 改写 |

### 9.6 N6 界面链

| 部件 | 升级后 | 动作 |
|---|---|---|
| `ui-acceptance` description 半句、表第 1 行、第 38 行 | mode 触发行；本技能自己的 reference 行；P16 | 拆 |
| `ui-acceptance` 规则 1、2 | 能力 | 本层 |
| 规则 3–5 | 点名原则 + 本地机制 | 改写 |
| `ui-acceptance` 五份 reference、9 个脚本 | 能力 | 本层 |
| `design-pages` 交接段、第 21 行 | P3、P14、P16 | 拆 |
| `design-pages` 其余与脚本 | 能力 | 本层 |
| `write-screen-contract` `## Next` | P3、P1 | 搬 |
| `write-screen-contract` 其余 | 能力 | 本层 |
| `docs/contexts/ui-acceptance/CONTEXT.md` 与 ADR 0002、0004、0011、0028–0030 | 仓库文档；`_Home_` 随搬家 | 本层，改写 |

### 9.7 N7 retro、advisor、exe-release、code-checkers、manage-agents-md、diagram-design

| 部件 | 升级后 | 动作 |
|---|---|---|
| `retro` 第 8、186 行 | P14 **Retro** | 搬 |
| `retro` 其余、`retro.py` | 能力；`DESTINATIONS` 加三项 | 本层，改写 |
| `advisor` `consulting.md` `## When it is worth a session` | mode 触发行 | 搬 |
| `advisor` 其余、`advising.md` | 能力与简报 reference | 本层 |
| `exe-release` 第 1–5 步、`driving.md` | P10 | 搬 |
| `exe-release` `key.md`、`new-product.md`、脚本 | 能力 | 本层 |
| `code-checkers` 第 6、8 步的顺序 | P8 | 拆 |
| `manage-agents-md` 第 50 行 | mode `## Subagents` | 搬 |
| `diagram-design` 全部 | 外来能力 | 本层 |

### 9.8 N8 基座

| 部件 | 升级后 | 动作 |
|---|---|---|
| `prompt/shared.md` 与 `prompt/` 其余 | 用户层 | 不改（任务边界 S）；mode 按规则号引用它 |
| `skills.txt` | 登记层 | 改写（第 1.1 节） |
| `install.sh` | 安装器 | 改写（第 7.2 节） |
| `~/.mmw/models.json` | 配置 | 本层；可选面板角色 |
| `board/` | 本层；两处路径 | 改写 |
| `migrations/` | 本层 | 不涉及 |
| `tests/lib/` | + `check_wiring.py` | 新建 |
| 根 `AGENTS.md` | Gotchas 第 1 条的四步 → P9 **Deliver** 与 delivery 槽位点名它（它是本仓库的交付约定，仍住在 `AGENTS.md`）；`<important if … upstream>` → 私有 P **Upstream pull**；Commands 表与 External References 加 mode 行 | 拆、改写 |
| `CODING_STANDARDS.md`、`TESTING.md` | 仓库文档；跨任务立场改为点名原则 | 本层，改写 |
| `merge-notes/`、`downstream-notes/` | 仓库文档 | 本层 |
| `tests/AGENTS.md`、`board/AGENTS.md` | 仓库文档 | 本层 |

### 9.9 N9 ADR、词表、原则候选

| 部件 | 升级后 | 动作 |
|---|---|---|
| 31 份 ADR | 仓库文档 | 本层；新 ADR 记录本次决定 |
| `CONTEXT-MAP.md`、七份 `CONTEXT.md` | 仓库文档；新词条、`_Home_` 与路径 | 本层，改写 |
| PC1、PC2、PC22 | **principle-silence-is-never-a-pass** | 新建 |
| PC3 | 读者侧 **principle-refusals-name-one-next-step**；写者侧 `CODING_STANDARDS.md` | 拆 |
| PC4、PC5 | 两条 MMW 原则 | 新建 |
| PC6 | mode 触发行 + hook | 搬 |
| PC7、PC25、PC26、PC12、PC17、PC19、PC21、PC23 | pstack 原文落位（U-D3） | 新建（导入） |
| PC8、PC11、PC16、PC18、PC20、PC28、PC29 | MMW 原则 | 新建 |
| PC9、PC10、PC13、PC14、PC24 | `shared.md` 规则号 | 删复述，点名规则号 |
| PC15 | mode `## Subagents` | 搬 |
| PC27 | `domain-modeling`（词表的唯一家，ask-matt `## Vocabulary underneath`） | 本层 |

### 9.10 N10 路由与调用

| 部件 | 升级后 | 动作 |
|---|---|---|
| 35 份 frontmatter | description 只写「是什么、直接调用时怎么说」；「何时在流程里用」进 mode | 改写 |
| 调用开关 | 上游原文，除 playbook 要由模型调用的（H2） | 回原文 / **留（H2）** |
| 24 份 `agents/openai.yaml` | 与开关同增同删；分叉的删 | 改写 |
| 五张 `## Find your moment` 表 | 路由性的（`dispatch`、`verify-ticket` 第 16 行、`ui-acceptance` 第 1 行、`code-review`）→ mode 或 playbook；能力内部分支的（`design-pages`、`verify-ticket` 表）→ 本层 | 拆 |
| 结尾段 17 句「下一步」 | playbook | 搬（全部） |
| 八种到达机制（N10 §3.1） | 四条到达路径（第 2.2 节） | 改写 |
| SSR 事实 7、`### Hand-offs`、`### Prompts written for other agents` | `docs/skill-set/`，改写 | 搬、改写 |
| `SKILL-MECHANICS.md` `## Router skills` | 上游原文 | 本层 |

**「留（H#）」汇总**：只有两处。
1. 上游 `triage`、`wayfinder`、`to-questionnaire`（以及今后被 playbook 点名的上游技能）的调用开关与上游原文不同：H2。
2. mode `## Autonomy` 抄一次产品事项清单：H1（Cursor 收不到 `shared.md`）。

---

## 10. 迁移批次（H5 下分批，每批后流水线仍能跑）

共同规则：每批作为本仓库的票，由当时已安装的冻结版本跑；变更自己的测试只在隔离的测试 home 里、对着假 tracker 与假 runner 跑；发布照根 `AGENTS.md` `## Gotchas` 的四步，第三步（移动已安装 checkout）只在没有 watch 打开时做（`install.sh --check` 列出开着的 watch）。

| 批 | 内容 | 为什么这时流水线仍能跑 | 需要用户做的 |
|---|---|---|---|
| 0 保障 | `check_wiring.py`（报告模式）；`anchors.py`；`dispatch.sh where`（与 `--preflight` 的 `RESUME:` 并存）；四处已核实断点（V6、V7、V8、V9）；`--check` 列 watch | 只加不删；hook 与技能列表不变 | 无（普通验收） |
| 1 mode 与白天 | 先跑 U-1、U-2、U-3 探针（隔离 home）；再建 `skills/mmw/`：`SKILL.md`、白天 13 份 playbook（P1–P13；P13 的 **Finish** 步在批 2a 之前写 `dispatch` 技能的 `dispatch.sh finish`）、`phase-boundaries.md`、`slots.md`、`interface-and-remake.md`；删白天能力技能里的「下一步」句与 ask-matt 残留；`mode-hook.py` 登记 | 夜间角色不读任何被改的白天文字；`to-tickets` 第 160 行的去处由 P1 **Hand to the night** 接住 | 授权 `install.sh`；开新会话（H2）；U-D4（消费仓库 `AGENTS.md` 加一行） |
| 2a 脚本归位 | `dispatch/scripts/*` → `mmw/scripts/`，`models.py`、`hosts.json` → `setup-mmw/scripts/`；hook 路径重登记；board、retro、install 的路径；`dispatch` 的三份 reference 暂时改指新路径 | 只换位置不换行为；同一提交里改全部字面路径，lint 规则 2 核对 | 授权 `install.sh` |
| 2b 夜间角色 | P14–P18、`review-axes/`、`writing-code.md`、`saving-memory.md`；启动提示词、唤醒指针、watchdog、turn guard、`NO_QUESTION`；`resume_at` 删、`where` 成为唯一；`verify-ticket`、`ui-acceptance`、`design-pages`、`retro` 剥离；`implement`、`code-review` 回原文；`dispatch` 解散、`setup-mmw` 建成。W1–W3 是天然整体，必须同一次发布 | 跨越脚本与文字的边界，定向测试覆盖不到：发布前跑 `tests/dispatch`、`tests/relay`、`tests/verify-ticket`、`tests/liveness` 四个完整套件（理由写在票上，`shared.md` 规则 15），再在隔离 home 里对假 tracker 跑一整夜 | 授权 `install.sh`；开新会话；U-D1；挑一个小 spec 验收第一次真实夜 |
| 3 上游回原文 | `to-spec`、`to-tickets` 分叉；其余上游改动剥离；调用开关按 H2 规则；SSR、RSS 搬到 `docs/skill-set/` 并改写事实 7；merge-note | 能力的「怎么做」不变，只是位置与路由句 | 授权 `install.sh`（`skills.txt` 前缀变） |
| 4 原则与导入接口 | `upstream-pstack/` subtree；`import_component.py`、`pstack.map`；MMW 自建 11 条；导入 13 条（U-D3）；调用方点名；mode 索引；`retro` 去处；`models.py config get`；lint 转为失败模式 | 文件都在 `mmw` 目录内，目录软链不变，不需要 `install.sh` | U-D3 |
| 5 面板（可选） | `dispatch.sh panel` | 新增子命令 | 按 U-6 决定做不做 |

---

## 11. 风险与需要的实测

### 11.1 实测

| # | 问题 | 为什么重要 | 怎么测 |
|---|---|---|---|
| U-1 | 启动提示词「Use the mmw skill … playbooks/<x>.md」能否让五个宿主的新会话读到该 playbook | 第 2.2 节的确定路径 | 隔离 HOME 放探针技能，`playbooks/probe.md` 里放随机标记，用各宿主非交互进程送提示词，看回复有无标记（ADR 0006 的方法） |
| U-2 | 各宿主的 `SessionStart`（含压缩后）、`SubagentStart`、`UserPromptSubmit` 能否注入一行 | pstack `reminder` 与 `poteto-agent` 的替代 | 各宿主装只打印标记的探针 hook，在有无 `.mmw/` 的目录各试；Claude Code 另试压缩后；Codex 已知有注入事件（`install.sh` 第 774 行） |
| U-3 | `mmw/playbooks/*.md`、`principles/*.md` 会不会被某个宿主当成技能扫进列表 | 若会，原则与 playbook 进技能列表 | 探针技能目录下放嵌套 `.md`，看各宿主的技能列表 |
| U-4 | 五个宿主是否都有待办工具与后台子代理 | 执行协议 | 各宿主非交互进程列可用工具 |
| U-5 | worker、reviewer 每次启动读 mode（约 150–170 行）的上下文成本 | 到达路径 1 | mode 写好后量字节；隔离 home 跑一张测试票比较首个动作前的上下文用量 |
| U-6 | `panel` 起多个会话的耗时、费用与夜里收齐的可靠性 | 是否值得搬 `arena`、`interrogate` | 用 `advise` 的机制起 3 个会话，测到齐时间 |
| U-7 | 去掉 `disable-model-invocation` 的上游技能增多后，触发准确度 | H2 规则的代价 | 固定一组请求，改前改后数各加载了哪个技能 |
| U-8 | 各宿主会话记录的位置与格式 | P11 与 `slots.md` | 各宿主跑短会话找记录文件 |
| U-9 | paseo、herdr 的第一条提示词是否作为参数传入 | H4 管不管启动提示词 | 读 `runners/paseo.sh`、`herdr.sh` 的 `start` 实现体 |
| U-10 | closeout 是否要核对「每个步骤名有痕迹或有 `skip:`」 | 无人会话的执行协议能否被机器检查 | 批 2b 后看三夜的收尾评论，数漏写的步骤 |
| U-11 | hook 进程是否继承 runner 用 `--env` 设的 `MMW_ROLE` | 压缩后指针 | 探针 hook 打印环境变量 |

### 11.2 需要用户决定

| # | 决定 | 我的建议与理由 |
|---|---|---|
| U-D1 | 上游 `implement` 回原文后还装不装（装就留 `/implement`，它的「full test suite」与 `shared.md` 规则 15 冲突） | 不装：它的内容已是 P4 的骨架，装着还会与 P16 的入口竞争 |
| U-D2 | `dispatch.sh check` 失败时自动跑完整 `install.sh`，与根 `AGENTS.md`「`install.sh` runs only when the user explicitly authorises it」冲突（R12 M7） | 改成只报告 |
| U-D3 | 是否在批 4 就落位 13 条 pstack 原则 | 落位：它们正好接住 MMW 已有规则，零新写文字，也是导入接口的第一次实证 |
| U-D4 | 消费仓库 `AGENTS.md` 加 `mmw` 一行 | 加（备用到达路径） |
| U-D5 | Cursor 应用里的用户规则是否补上 `shared.md` 的内容 | 由你决定；mode 已抄了无人会话必需的一段 |
| U-D6 | 技能改名：`dispatch` 解散、`setup-mmw` 新建，`/dispatch` 不再存在 | 接受：用户说「开夜」由 mode 路由到 P14，不需要记技能名 |

### 11.3 风险

- **批 2b 面大**：一次改动跨脚本、hook、文字与测试。缓解：批 0 先把 lint、锚点、`where` 做成并行实现；W1–W3 同一次提交；四个完整套件加假 tracker 整夜。可以回退：已安装 checkout 退回上一个提交，重跑 `install.sh`。
- **mode 没被加载**：白天会话失去路由。缓解：四条到达路径叠加；批 1 先实测。
- **导入的 pstack 文字与 `shared.md` 冲突**：优先级句已写；导入时按第 5.5 节判。
- **原则层变长后变成摆设**：pstack 同样的风险；靠「点名义务」与 retro 的 `principle` 去处让它被用、被修。

---

## 12. 自查：与第一版草图的最低范围对照

| 草图项 | 结果 | 说明 |
|---|---|---|
| 一个 mode：常驻规则 | 达到（依赖 U-2，有备用路径） | `## Non-negotiables`、`## Autonomy`、`## Where you are`、`## Subagents`；四条到达路径 |
| mode：原则索引 | 达到 | 24 条，由 lint 与原则文件一致 |
| mode：playbook 路由表 | 达到 | 18 行加私有索引 |
| 白天定义 | 超出 | P1，另拆出 P2 Large effort、P3 Interface design |
| 夜间编排 | 达到 | P14，补齐 V6–V8、M16 缺行 |
| 做一张票 | 达到 | P16 |
| 评审一轮 | 达到 | P18 |
| 单票 | 达到 | P15，另有 P17 自己拿票 |
| 早上验收与 finish | 达到 | P13 |
| 修 bug | 达到 | P5 |
| 出包 | 达到 | P10 |
| 分诊 | 达到 | P6 |
| 调研 | 达到 | P7 |
| 给仓库接入 MMW | 达到 | P8 |
| 写技能 | 达到 | P9 |
| 其他工作流 | 超出 | P4 Direct change、P11 Session pickup、P12 Pause safely、私有 Upstream pull 与 Component import |
| 能力技能只讲一步怎么做、不知道被谁调用 | 达到 | 17 句「下一步」与全部角色句离开能力技能；lint 规则 3 强制；例外只有调用开关（H2） |
| 原则层是真正的层 | 超出 | 11 条自建 + 13 条 pstack 原文；一种引用写法；能直接接 pstack 原则 |
| 脚本是 lever，由 playbook 步骤调用 | 达到 | 流水线脚本进 `mmw/scripts/`；lint 规则 8 查孤立 lever；位置计算从能力脚本移到 mode 脚本 |
| 外来组件直接落位，只加文件与登记行 | 达到 | 第 8.5 节；导入脚本做机械改写 |
| 执行协议 | 达到（非 Claude 宿主依赖 U-4） | 无人会话写进交付物，不依赖待办工具 |

没有「未达到」项。依赖实测的两项（U-2、U-4）都有不依赖该实测的备用路径，结构不因实测结果缩小。

---

## 13. 本轮读了什么、没读什么

- **读了**：见文首「材料」。另读 L7 第 0 节与 C.1 全文、R12 第 1、2 节与第 4 节全文、R4 第 0、1 节与第 10 节、N11 全文，以及 N1–N10 的目录。
- **没有重读、按 R13、R14、R12 引用的**：`session.md`、四个 axis 文件、`advising.md`、`consulting.md` 的正文；`exe-release` 的 `driving.md`、`key.md` 正文；`design-pages` 各 reference 正文；`dispatch.sh` 其余区段与三个 runner 的实现体；`status.py`、`turn-guard.py` 全文。依赖它们的结论（例：`turn-guard.py` 能识别 orchestrator 会话，出自其头注释的转述 R12 §2.5）标为推断或放进第 11 节。
- 第 3.3 节的步骤骨架是由来源原文归纳的推断；落地时逐句从来源搬，搬完量行数。
