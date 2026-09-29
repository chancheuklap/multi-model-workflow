# R2 MMW 的 pstack 分层架构：忠实派设计

立场：尽量贴近 pstack 的结构与写法（`L7-pstack-component-contract.md` 第 A 节），只在 MMW 的多宿主、脚本启动会话、事件唤醒、冻结运行时确实做不到时偏离，每处偏离写明原因。本报告只定架构层面的决定；逐个部件的归置是下一轮的事，这里只给规则和用来检验规则的几个例子。

标注：「已核实」= 本轮回到原文或跑命令看到；「推断」= 由原文推出、没有直接证据；「未确定」= 做不出判断，第 15 节写明需要什么实测。路径不带前缀的，`mmw-v2/` 下的相对 `mmw-v2/`，pstack 的相对 `docs/research/code-landing-refs/pstack/`。

---

## 0. 结论（先读这里）

1. **一个 mode 技能 `mmw`，四个 playbook，原则做成 mode 目录下的文件，其余都是能力技能。** mode 的目录是 `mmw-v2/skills/mmw/`，其中 `SKILL.md` 放入口表、常驻规则、原则索引、路由表；`playbooks/` 放 `idea-to-tickets.md`、`night.md`、`one-ticket.md`、`worker.md`；`principles/` 放原则；`references/` 放只被 playbook 读的分支材料。pstack 的布局与此相同（`skills/poteto-mode/` 下挂 `playbooks/`、`references/`、`scripts/`，L7 A.1）。
2. **与 pstack 的三处根本偏离，都由已核实的宿主行为逼出：**
   - **能力技能不关模型触发。** 在 Claude Code 上，带 `disable-model-invocation: true` 的技能从模型的技能列表里整个消失（已核实：本会话的可用技能列表里没有 `grill-me`、`grill-with-docs`、`handoff`、`teach`、`wait-what`、`improve-codebase-architecture`、`setup-matt-pocock-skills` 七个）。上游维护者规则 `upstream/.agents/invocation.md` 也写明用户触发的技能 "no other skill can" 调用。pstack 那种「全部关掉、由 mode 按名调用」的做法在这台机器上会让 mode 够不到能力技能。用户 2026-08-25 的裁定（Memory `fe94802d`）也否决过「用 `disable-model-invocation` 强制层级调用」。
   - **原则不做成技能，做成 `mmw/principles/<slug>.md` 文件。** 原因同上：做成关掉触发的技能在 Claude Code 上按名找不到；做成可触发的技能又要为每条原则在每个会话里常驻一行 description，并且会被自动触发，与 pstack「You don't invoke principles」相反（`docs/guide/08-principles.md`，L7 A.4）。上游 `SKILL-MECHANICS.md` `## Invocation` 对「多方共用的材料」给的正是这个办法："Push it to a plain file outside the skill system"。
   - **mode 靠一行常驻提醒加自身 description 加载，而不是 `mode: true` 与 `reminder:`。** 这两个键只在 Cursor 上有意义，语义快照里也没定义（L7 E.2、F.1）。MMW 的等价物是 `prompt/shared.md` 里一行提醒（经 `~/.claude/CLAUDE.md` 与 `render.py` 生成的三份 `AGENTS.md` 到达 Claude Code、Codex、Pi、Grok），加上 mode 自己可触发的 description；脚本启动的会话由启动提示词直接点名 mode 与 playbook。
3. **MMW 的流程从上游文本里搬走，上游回到原文。** 规则见第 7 节：只有改变能力本身的改动（任何调用方都受益）和让 mode 够得到它的调用方式翻转，留在上游文本里；其余（结尾段点名下一步、为 MMW 路由加的触发句）搬进 playbook。正文过半是 MMW 写的三个上游技能（`implement`、`code-review`、`to-tickets`，`merge-notes/README.md` `## 本仓自有正文的技能`）：`implement` 的正文成为 `worker.md`，另两个搬到 `mmw-v2/skills/` 成为 MMW 自有技能，上游目录恢复原文、不安装。
4. **「下一步」只有一个家：playbook。** 这取代 `SKILL-SET-RULES.md` 事实 7 的「每个技能的结尾段点名下一步」与「MMW ships no router skill」。事实 7 要防的问题（一跳上找不到下一步就自己发明，#538 记录的 25 张 sub-issue 里 22 张耗在流水线自身，N10 第 7 节）由三样东西接住：playbook 持有整条顺序；常驻提醒让 playbook 在场；每个 playbook 开头一张按持久事实判断「我在哪一步」的表。
5. **单一入口、单一任务类型的流程不拆（L7 C.1 第 7 问）。** `night.md`、`worker.md` 各是一份完整的操作文件，只换目录，不拆成更多组件。ticket 的评审仍是一个能力技能（子代理编排型，与 pstack `interrogate` 同形），不进 mode。
6. **运行安全：** 整个改造是一次发布，只在没有任何 watch 打开时按 `AGENTS.md` `## Gotchas` 的四步提升；worker 的 `RESUME:` 行按步骤编号指向收尾步骤，搬家时编号保持不变，新旧版本之间才能接上（第 10 节 R3）。

---

## 1. 读了什么、核实了什么

**通读：** `L7-pstack-component-contract.md` 全文；`N10-mmw-routing-and-invocation.md` 全文；`N11-mmw-gaps.json` 全文；`upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` 全文；`merge-notes/README.md`；`prompt/shared.md`、`prompt/README.md`；`skills/dispatch/SKILL.md` 与 `references/night.md`、`inside-a-ticket.md`、`one-ticket.md` 全文；`upstream/skills/engineering/implement/SKILL.md`、`code-review/SKILL.md`、`skills/verify-ticket/SKILL.md`、`skills/ui-acceptance/SKILL.md`、`skills/design-pages/SKILL.md`、`skills/advisor/SKILL.md` 全文；残留的 `upstream/skills/engineering/ask-matt/SKILL.md` 与 `PHASE-BOUNDARIES.md` 全文；ADR 0003、0014、0015 全文；pstack `skills/poteto-mode/SKILL.md` 全文，`playbooks/bug-fix.md`、`session-pickup.md`、`pause-safely.md`、`authoring-a-skill.md`、`feature.md` 全文，`orchestrate.md` 前 30 行，`agents/poteto-agent.md`，`skills/principle-attack-the-premise/SKILL.md`。

**抽读：** `SKILL-MECHANICS.md` `## Invocation`、`## Router skills`；`upstream/.agents/invocation.md` 前 14 行；`dispatch.sh` 100–115 行与 1949、1967、2072 行；`relay.py` `WAKES`、`wake_text`；`turn-guard.py` 1–75、290–315 行；`tool-guard.py` 70–85 行（`NO_QUESTION`）；`verify-ticket.py` 2150–2230 行（`resume_at`）；`install.sh` 头注释；`models.py` `ALLOWED_AGENTS`；`~/.mmw/models.json`；`to-spec` `## Next`、`to-tickets` 第 8 步、`grill-with-docs` 全文、`wayfinder` `## Invocation`、`improve-codebase-architecture` `### 4`、`prototype/SKILL.md` 全文与 `UI.md` `## Next`；`design-pages/references/pull.md` `## Reached from here` 起、`edit-pages.md` `## Next`；`write-screen-contract/SKILL.md` `## Next`；`retro/SKILL.md` 180–210 行；N9 第 9–12 节；N8 第 9–11 节；N1 第 9–10 节。

**上游原文比对（已核实）：** 最近一次 squash 提交 `5b1a4c51` 里，`implement/SKILL.md` 是 15 行，frontmatter 带 `disable-model-invocation: true`，正文只写 "Use /tdd where possible … Once done, use /code-review to review the work. Commit your work to the current branch."；`to-spec`、`to-tickets`、`triage`、`wayfinder` 上游都带 `disable-model-invocation: true`；上游 `wayfinder` `### Work through the map` 只有 5 步，第 6 步是本仓加的。

**Memory（`nmem m show` 读原文）：** `8ec53374`（改造方向）、`756fc056`（旧规则是审视对象）、`ce037679`（名字即可调用、唯一性与系统性）、`fe94802d`（平级调用、不改上游 frontmatter、否决用 `disable-model-invocation` 强制层级）、`f4c3d378`（以技能为第一层编排）、`411750f5`（description 只写触发、上游能不改就不改）、`c155ffc2`（调用方只给角色名与票号）。

**N 报告的已知错误，本报告的处理：** 采用 N11 的更正：`ask-matt` 未安装（N3、N6 的 `ask-matt ->` 边不算活边）；`NO_QUESTION` 与 `implement` 第 23 行不一致（N3 对，N8 错，本轮回到 `tool-guard.py` 76–80 行核实）；worker 不会被指到 `## On waking`（N10 B9 对，N1 §2.1 错）。N1 §9.2 第 1 条（`night.md` 重入表缺「`spec.retroed` 已记录、用户尚未验收」一行）本轮对照 `night.md` 第 13–22 行核实成立。

**没有读、因而本报告不下结论的：** `dispatch.sh` 其余约 4500 行；各测试文件本体（哪些测试钉住了 `RESUME:` 的步骤编号，未查）；根目录 `.mmw/AGENTS.md`、`journeys/`、`stories/`；Codex、Grok、Pi、Cursor 的会话记录。

---

## 2. 总体形态

### 2.1 组件类型对照

| pstack 类型（L7 A 节） | MMW 里对应什么 | 位置 | 与 pstack 的差别 |
|---|---|---|---|
| mode（A.1） | `mmw` 技能 | `mmw-v2/skills/mmw/SKILL.md` | 可被模型触发；多一张入口表和 `## On waking`（见第 4 节） |
| playbook（A.2） | 四份 playbook | `mmw-v2/skills/mmw/playbooks/*.md` | 每步带 `Done when` 行；可跨会话的 playbook 开头有「我在哪一步」事实表 |
| 能力技能（A.3） | `skills.txt` 里除 `mmw` 外的全部技能 | 不变（三个自有正文技能搬到 `mmw-v2/skills/`） | 保持模型可触发 |
| 原则（A.4） | 原则文件 | `mmw-v2/skills/mmw/principles/<slug>.md` | 是文件不是技能；无 frontmatter，首行 `Apply when …` 顶替 description |
| reference（A.5） | 技能自己的 `references/`；只被 playbook 读的放 `mmw/references/` | 同 pstack | 无 |
| 脚本（A.6） | `dispatch.sh`、`relay.py`、`watchdog.py`、`verify-ticket.py`、oracles 等 | 留在各自技能的 `scripts/` | 无 |
| agent 定义（A.7） | 启动提示词 + `~/.mmw/models.json` 一行 | `dispatch.sh start/advise` + `models.py` | 不交付 subagent 文件（ADR 0015） |
| 配置（A.8） | `~/.mmw/models.json`；`shared.md` 的提醒行 | 插件目录之外，与 pstack 同思路 | 提醒行取代 `reminder:` |
| guide（A.9） | 无对应；人读的文档在 `docs/` | — | 不新建 |
| automation pack（A.10） | 无对应；夜间机制已由 relay/watchdog 承担 | — | 不新建 |
| 项目私有组件（A.11） | 消费仓库的 `.mmw/`、screen contract、生成的 `AGENTS.md` 等 | 消费仓库 | 见第 9.4 节 |

### 2.2 目录（只列新增或移动的；其余不动）

```
mmw-v2/skills/mmw/
  SKILL.md                      mode：入口表、常驻规则、原则索引、On waking、路由表
  playbooks/
    idea-to-tickets.md          新：头部流程（ask-matt 主流程 + 各技能结尾段的「下一步」）
    night.md                    移自 skills/dispatch/references/night.md，整份
    one-ticket.md               移自 skills/dispatch/references/one-ticket.md，整份
    worker.md                   移自 upstream/skills/engineering/implement/SKILL.md 的正文
  principles/<slug>.md          新：第 6 节
  references/
    writing-interface-code.md   移自 implement/references/
    saving-memory.md            移自 implement/references/
    adopting-a-ticket.md        移自 dispatch/references/inside-a-ticket.md
mmw-v2/skills/code-review/      移自 upstream/skills/engineering/code-review/（名字不变）
mmw-v2/skills/to-tickets/       移自 upstream/skills/engineering/to-tickets/（名字不变）
mmw-v2/upstream/skills/…        implement、code-review、to-tickets、ask-matt 恢复上游原文，不安装
```

`skills.txt` 的变化：去掉 `engineering/implement`，`engineering/code-review` 与 `engineering/to-tickets` 改成 `self/code-review`、`self/to-tickets`，加 `self/mmw`。行数仍是 35。

---

## 3. Q1 调用模型

### 3.1 八种到达方式在新形态下各到哪里

N10 §3.1 的 M1–M8 逐条对照：

| 到达方式 | 现在到哪里（已核实） | 新形态下到哪里 | 依赖的宿主行为 |
|---|---|---|---|
| 人在会话里说一句话 | 靠 28 个可触发技能的 description 自选；头部没有入口（N10 B1） | 常驻提醒行让模型先加载 `mmw`；`mmw` 路由表按任务类型送到 playbook 或能力技能 | 宿主会遵从用户级提示里的一行指令（未核实，见第 15 节 T1） |
| 用户斜杠 | 35 个都行；7 个只能靠它 | 不变；多一个 `/mmw` | 已有 |
| description 自动触发 | 28 个技能 | 29 个（加 `mmw`）；上游技能的 description 恢复原文后触发词变少 | 宿主扫描 `~/.agents/skills` 与 `~/.claude/skills`（`install.sh` 头注释声称五家都扫；grok、codex 上跑 worker 的实际夜间运行是旁证，推断） |
| 技能按名点名 | 能力技能互相点名，结尾段点名下一步 | playbook 点名能力技能；能力技能之间的横向调用保留；能力技能不再点名下一步 | 被点名的技能是模型可触发的（Claude Code 上已核实这是前提） |
| `dispatch.sh` 拼的启动提示词 | worker "Use the implement skill to work ticket #N."（1949 行）；reviewer "Use the code-review skill …"（1967 行）；advisor "Use the advisor skill."（2072 行） | worker："Use the mmw skill's `worker` playbook on ticket #N." 加原有的 `AUTONOMOUS`、`PRODUCT_RULES`；reviewer 与 advisor 不变 | 会话能按相对路径打开已加载技能里的文件（今天 `implement` 读 `references/writing-interface-code.md`、orchestrator 读 `references/night.md` 就靠它，推断在 grok、codex、claude 上成立） |
| relay 的事件唤醒（`#<n> <event>`，`relay.py` `wake_text`） | 会话靠上下文里已加载的 `dispatch` 或 `implement` 知道怎么办（N10 B8） | `mmw` 的 description 把这几种行列为触发；入口表第 2 行送到 `## On waking`，再送到本角色 playbook 的事实表 | 被压缩后的会话会重新加载 `mmw`（未核实，T2） |
| watchdog 告警行、`MMW turn guard:` | 只有 orchestrator 收到；`night.md` 事实表第 3 行接住 | 同一条路径（入口表 → On waking → `night.md` 事实表） | 同上 |
| 钩子拒绝（`tool-guard.py`） | 拒绝文字自带出路，出路与 `implement` 第 23 行不一致（已核实） | 拒绝文字改为指向 `worker.md` 里唯一的那一句 | 已有 |

### 3.2 哪些组件保留模型可触发，哪些只被点名

| 组件 | 模型可触发 | 理由 |
|---|---|---|
| `mmw`（mode） | 是 | 常驻提醒要有一个模型能加载的目标；被压缩或被唤醒的会话要能自己回来。pstack mode 是 `disable-model-invocation: true`，靠 `mode: true` 常驻（L7 A.1）；MMW 没有这个键，所以偏离 |
| 能力技能 | 保持现状：28 个可触发，7 个用户触发（`merge-notes/README.md` 第 22 行名单） | 见第 0 节第 2 条第一点。7 个用户触发的原样保留：mode 与 playbook 不需要按名调用它们，需要时写「告诉用户运行 `/handoff`」或像 `grill-with-docs` 那样读它点名的两个可触发技能 |
| playbook | 否（不是技能，没有 frontmatter） | 与 pstack 相同（L7 A.2 "没有 frontmatter，不注册为技能"）。只从 mode 路由表或启动提示词到达 |
| 原则 | 否（文件） | 只被点名 |
| reference、脚本 | 否 | 与 pstack 相同 |

**被放弃的备选：**

- **pstack 原样：能力技能全部 `disable-model-invocation: true`，只由 mode 与 playbook 点名。** 否决。Claude Code 上被关掉的技能模型看不见（已核实），mode 点名也够不到；与用户裁定 `fe94802d` 相反。它的好处（description 退出常驻上下文）在 MMW 里要用「每个技能写一个绝对路径」来换，而 `ce037679` 禁止写路径。
- **钩子在每轮注入提醒（`UserPromptSubmit`、`SessionStart` 类钩子），作为 `reminder:` 的替身。** 暂缓，作为 T1 失败时的后备。理由：它的常驻成本与提醒行相同，却要在五个宿主上各注册一种钩子；`turn-guard.py` 头注释只核实过五家都有回合结束事件，没有核实回合开始或提交提示词的事件（未确定）。
- **mode 只能由用户斜杠进入。** 否决。脚本启动和被唤醒的会话都没有人打斜杠；`ask-matt` 这种「用户记得去问」的入口在 Claude 会话记录里真实调用 0 次（N10 第 7 节，已由 N10 作者核实）。
- **N10 §10.4 的模型 D：脚本启动的会话不经过 mode，mode 只管人启动的头部。** 改动面最小，作为降级方案保留。忠实派不选它的原因：它把 `## On waking` 留在 `dispatch` 里，B9（worker 读不到「先重跑被打断的命令」）照旧；`implement` 的正文照旧留在上游目录里。

### 3.3 mode 怎样被加载

| 会话 | 加载路径 | 失败时的后果 |
|---|---|---|
| 人启动，Claude Code、Codex、Pi、Grok | `shared.md` 新增一行提醒（经 `~/.claude/CLAUDE.md` 软链与 `render.py` 生成的三份 `AGENTS.md`，`prompt/README.md` 表）；`mmw` 的 description | 回到今天的状态：靠各技能 description 自选；头部与结尾段的衔接要靠 mode（第 10 节 R1） |
| 人启动，Cursor | 只有 `mmw` 的 description；`shared.md` 到不了 Cursor（ADR 0007，`prompt/README.md` "Cursor 不在此列"） | 同上。可选补救：在 Cursor 的用户规则里手贴同一行，或由 `install.sh` 写一份用户级规则文件（pstack 用 `~/.cursor/rules/*.mdc` 加 `alwaysApply: true`，L7 A.8）；这在 MMW 上未核实，T5 |
| 脚本启动的 worker | 启动提示词点名 `mmw` 与 `worker` playbook | 与今天点名 `implement` 同一机制 |
| 脚本启动的 reviewer、advisor | 启动提示词点名能力技能（不变），不经过 mode | 无变化 |
| 被唤醒或被压缩后的 orchestrator、worker | 唤醒行本身在 `mmw` 的 description 触发词里；提醒行 | T2 |

提醒行的建议文字（给用户定稿，见第 15 节 U1）："In a repository, start, resume or finish a piece of engineering work through the `mmw` skill." 它对应 pstack `reminder: New task? Playbook match or rigor needed -> apply /poteto-mode.`，常驻成本是一句话。ADR 0014 否决「把 caller 侧规则写进用户级提示词」的两条理由（到不了 Cursor；为偶发之事付每回合常驻成本）里，第二条不适用于它：进入工程任务不是偶发之事；第一条原样存在，由上表的 Cursor 一行处理。

### 3.4 本方案不依赖、以及必须依赖的宿主行为

**不依赖：** `mode: true`、`reminder:`、`paths:`、`alwaysApply`（Cursor 规则作为可选补救，不是前提）；`disable-model-invocation` 在 Claude Code 以外的语义（本方案不为可达的技能打开它）；经 runner 投递斜杠命令是否生效（N10 §11 未确定，启动提示词用自然语言点名）；宿主的待办列表工具（有则用，没有不影响，见第 5.2 节）；宿主的具名子代理类型（ADR 0015）；从 trunk 重读组件（与 Self-hosting boundary 冲突，L7 B.1，不采用）。

**必须依赖、需实测（第 15 节）：** T1 各宿主遵从提醒行；T2 被压缩或被唤醒的会话凭唤醒行或提醒行回到 `mmw`；T3 各宿主能按相对路径打开 `mmw/playbooks/*.md`、按「the `X` skill's `path`」打开别的技能的文件（今天已在用，Pi 与 Cursor 上无证据）；T5 Cursor 的补救渠道。

---

## 4. Q2 mode

### 4.1 几个 mode

**一个。** 理由：

- pstack 只有一个（L7 A.0）。
- 头部判断「走 spec 流水线还是直接 `tdd`」（残留 `ask-matt/SKILL.md` 第 22–26 行）正好是工具箱与流水线的分界。两个 mode 会把这个判断放在两个 mode 的接缝上，谁都不持有它，还需要第三个东西在两个 mode 之间路由，这就是事实 7 担心的「第二份副本」。
- 工具箱里与流水线无关的技能（`diagram-design`、`code-checkers`、`manage-agents-md`、`exe-release`、`research`、`wizard` 等）各自的 description 已经能正确触发，mode 不需要为它们写路由行（见 4.3 的「不列入」规则），所以一个 mode 不会因为工具箱而变大。

**被放弃的备选：** 工具箱 mode 加流水线 mode（理由如上）；不设 mode、只把头部做成一个 `idea-to-tickets` 技能（N10 模型 E 的变体：头部缺口有家，但唤醒入口、`## On waking`、worker 的家都不解决，上游文本里的结尾段也搬不走，因为没有 playbook 接收它们）。

### 4.2 mode 装什么

按 pstack mode 的章节顺序（L7 A.1 "正文模板"），加 MMW 必需的两节。下表是章节骨架与每节的内容来源；每节的具体文字是下一轮的事。

| 章节 | 内容 | 来源（已核实） | 与 pstack 的差别 |
|---|---|---|---|
| frontmatter | `name: mmw`；`description` 只写触发：在仓库里开始、续做或结束工程工作；不知道该用哪个技能；处在阶段边界；提示词点名一个 `mmw` playbook；收到 `#<n> <event>`、`relay.recovered since …`、`watchdog: …`、`MMW turn guard: …` 行 | `SKILL-SET-RULES.md` `### Descriptions`；`check_own_skill_frontmatter.py` 只允许 `name`、`description` | 无 `mode`、`reminder`、`icon`、`color`、`disable-model-invocation` |
| `## Where you are`（新） | 三行的入口表：提示词点名了 playbook → 打开它；收到唤醒行 → `## On waking`，再到本角色 playbook 的事实表；人提出的请求 → `## Playbooks` | `dispatch/SKILL.md` `## Find your moment` 的第 1–4 行（按角色的那几行） | pstack 没有，因为 Cursor 上没有脚本启动与事件唤醒 |
| `## Non-negotiables` | 跨所有 playbook 的「条件 → 技能或 playbook」触发，只列 description 没有覆盖的：写代码前先做头部判断；起了别的 agent 就结束回合，由事件叫醒（N9 PC4）；票的状态只由脚本写（PC6，`tool-guard.py` 已机械拦截，这里只写一句）；流水线自身的故障停下报告、不绕过（PC18 与 `shared.md` 规则 11 的优先级在此写明） | N9 §9.1、§9.3 | pstack 的触发列表 17 条，多数指向 description 被关掉的技能；MMW 的技能 description 是活的，重复写就是 `### Descriptions` 第 2 条的冲突，所以只列 description 之外的 |
| `## Principles` | 原则索引，每行 `**名字** (principles/<slug>.md). 何时适用. 一句要点.` 与 "Read the leaf in full for any principle you apply." | pstack mode 第 39 行 | 指向文件而不是技能 |
| `## Autonomy` | 有人值守时 `shared.md` 规则 1、2 管；提示词说没人在看时（`AUTONOMOUS` 这句事实留在启动提示词里），屏幕上不放问题，问题去本 playbook 或技能写明的去处；层级：`shared.md`（owner 的话）高于 mode；playbook 的一步与能力技能正文冲突时，关于「交付物之后做什么」以 playbook 为准，关于「交付物怎么做」以能力技能为准 | `shared.md` 第 11 行；`dispatch.sh` 108 行；pstack E.1 第 20、30 条的教训（两层冲突而不写优先级） | pstack 的 Autonomy 放宽了它自己的原则而没写优先级（L7 C.2）；这里显式写 |
| `## Subagents` | 需要另起上下文时要宿主自带的通用 subagent 并让它用某个技能（ADR 0015）；子代理的 brief 写明返回什么、多长；只读靠文字（PC15 只在 `advisor` 与 `code-review` 里，不进 mode，这里不写） | `SKILL-SET-RULES.md` `### Hand-offs` 第 95 行、`### Prompts` 第 102 行 | 没有 `subagent_type`、`model` 参数、`run_in_background` |
| `## On waking`（移入） | `dispatch/SKILL.md` `## On waking` 四步原文 | 同左 | pstack 没有事件唤醒 |
| `## Playbooks` | 执行协议（第 5.2 节）；路由表 | pstack mode 第 117–143 行 | 路由目标可以是 playbook，也可以是能力技能（pstack 路由到 `figure-it-out` 的先例，L7 A.1） |

**不进 mode 的：** 回复写法（`shared.md` 规则 4–9 已是它的家，面向 owner；pstack 的 `## Writing the reply` 与之重叠，N8 §9.2 第 5 条已核实）；代码注释规则（MMW 没有对应内容，不为凑章节而写）；各 playbook 的步骤编号（L7 A.1 "怎样算写错"）；多分支的决策程序（同上；头部判断以路由表的两行加「Distinct from」写，不写成程序）。

### 4.3 路由表（草拟行，行文下一轮定）

| 行 | 目标 | 说明 |
|---|---|---|
| **Build something.** 一个要多次会话才能做完的改动，从想法、对话、清空的 wayfinder map、选定的架构候选或 triage 判为可做的 issue 出发 | `playbooks/idea-to-tickets.md` | 带「谁来检查」的理由：这条路给每张票脚本跑的验收标准、独立会话的 reviewer、关掉的票作记录（`ask-matt/SKILL.md` 第 26 行，原文在残留目录里，没有第二份，N10 B3 已核实） |
| **Small change.** 小到用户会直接检查的改动。Distinct from Build | `tdd` 技能，本会话 | 不设 playbook：它只调用一个技能，没有自己的门槛（C.6 信号 5） |
| **Foggy effort.** | `wayfinder` 技能；map 清空后进 Build 的对应入口 | `wayfinder` 第 6 步（本仓加的）搬进 `idea-to-tickets.md` |
| **Incoming issue.** 不是本流水线开的 issue，或流水线交回 `needs-triage` 的票 | `triage` 技能；判为可做的进 Build | `triage` 第 5 步里送 `to-spec`、`to-tickets` 的句子搬进 playbook |
| **Hard bug.** | `diagnosing-bugs` 技能；修法按 Build 与 Small change 的分界走 | 补上 N10 B6 的缺口（`diagnosing-bugs` 结尾不点名下一步，上游原样） |
| **Run a night.** | `playbooks/night.md` | 从 `dispatch` 的 description 里移出 |
| **One ticket outside a night.** | `playbooks/one-ticket.md` | 同上 |
| **Work a ticket.** 被 `start` 派上一张票，或自己接手一张 | `playbooks/worker.md` | 同上；`implement` 正文的新家 |

**不列入路由表的规则：** 一项能力本身就是一件完整的任务、且它的 description 已经正确触发的，不列（`advisor`、`exe-release`、`design-pages` 的单独使用、`research`、`wizard`、`to-questionnaire`、`writing-for-agents`、`manage-agents-md`、`code-checkers`、`diagram-design`、`resolving-merge-conflicts`）。列了就是同一触发写两处。

### 4.4 与 `shared.md` 的分工

| | `shared.md` | `mmw` |
|---|---|---|
| 读者 | owner 的每一个会话，不分项目（四个宿主；Cursor 不载入） | 做 MMW 工程工作的 agent，包括无人会话 |
| 语气 | owner 第一人称 | 给 agent 的祈使句 |
| 内容 | 决定权划分、汇报写法、证据要求、工作纪律 | 路由、原则索引、无人会话的自主规则、唤醒处理 |
| 改动 | 加一行提醒（需 owner 同意，U1）；第 11 行不改：它已经说无人会话的提问「goes where its skills route questions」，新形态下那个去处就是 mode 的 `## Autonomy` 与 playbook | 不复述 `shared.md` 的任何规则 |

---

## 5. Q3 playbook

### 5.1 位置与格式

**位置：** `mmw-v2/skills/mmw/playbooks/<task-type>.md`，文件名是任务类型，与 pstack 相同（L7 A.2）。

**格式：** 照搬 pstack 骨架，加两处 MMW 调整。

1. `### <名字>`，没有 frontmatter，没有 H1（pstack 原样；好处是以后从 pstack 导入的 playbook 不用改格式）。
2. 粗体所有权行 `**You own <对象>. <动词>, <动词>.**`。MMW 已有现成的所有权句可用：`night.md` 的 "While a worker holds a ticket, its code is the worker's"；`inside-a-ticket.md` 的「你接手了票」。
3. 可选首段：本类任务为什么这样做、谁依赖产出（`SKILL-SET-RULES.md` 事实 1；`night.md` 现有的前三段就是这类内容）。
4. **（MMW 加）「Find where you are」事实表**：凡是会被事件唤醒、被压缩、或跨会话接续的 playbook，开头一张表，按持久记录上的事实（票上的事件、仓库里的文件）决定从哪一步进入，"first row whose fact holds"。`night.md` 第 13–22 行就是这种表；`worker.md` 由 `verify-ticket.py --preflight` 的 `RESUME:` 行承担（见 5.3）；`idea-to-tickets.md` 新建一张，键是 map 是否存在与清空、prototype 叶目录 `README.md` 有无结论、设计包是否已拉进仓库、screen contract 是否存在、spec 是否已发布、票是否已发布且 lint 干净。偏离理由：pstack 用单独的 `session-pickup` playbook 从 Cursor 的 transcript 重建状态（L7 D.2），transcript 位置是宿主专有的（L7 E.2），而 MMW 的状态本来就在 tracker 与仓库里（ADR 0019；N9 PC5）。
5. 编号步骤，每步首句是一个可以勾掉的祈使动作。
6. **（MMW 加）每步一行 `Done when …`**：`SKILL-SET-RULES.md` `### Rules and completion criteria` 已有的规矩，`implement` 的收尾步骤全部这样写。它是 `RESUME:` 与事实表判断「这一步做完没有」的依据。pstack 没有这一行。
7. 可选的规则簇（`####` 小节）：只在执行中查阅、不抄进待办的常设规则。`night.md` 的 authority order、closing pass 的四步门槛与三条提交规则就是这类，对应 pstack `orchestrate.md` 的 `####` 规则簇（L7 A.2、C.4）。
8. 末行 `**Reply:**`。无人会话的 playbook 写明「屏幕上不回复；报告是 X」（worker：closing comment；night：`NIGHT SUMMARY` 与 `NIGHT RETRO`，外加给用户的一句话）。

**命令的写法：** playbook 在 `mmw` 目录里，自己的相对路径只解析到 `mmw` 内部，所以别的技能的脚本按今天 `implement` 第 8 行的先例写："Commands of the `verify-ticket` skill's `verify-ticket.py` and the `dispatch` skill's `dispatch.sh` are named bare below." `night.md` 与 `one-ticket.md` 现在写的 `bash scripts/dispatch.sh` 是相对 `dispatch` 目录的，搬家时必须改成这种写法（已核实：两份文件全文都用 `bash scripts/dispatch.sh`）。

### 5.2 执行协议（写在 mode 的 `## Playbooks` 开头）

- 匹配到 playbook 后打开它；宿主有待办列表时，把编号步骤原样抄为前几项，不做的一步留在列表里写 `skip: <reason>`（pstack mode 第 117 行）。宿主没有待办列表时，按步骤顺序做并在回复里列出跳过的步骤。写成能力（"a host that keeps a task list"），按 `SKILL-SET-RULES.md` `### Paths and host neutrality` 不点宿主名。
- 规则簇与模板不进待办（L7 D.1）。
- 上下文被清空或压缩之后、或被唤醒之后，从事实表（或 `RESUME:` 行）重新进入，不从摘要或记忆进入（原则 `resume-from-the-record`，第 6 节）。
- 重新匹配只在用户开始一件新任务时发生（pstack 的 "new task"，`docs/guide/02-poteto-mode.md`，L7 D.1）。

### 5.3 脚本启动的会话怎样直接进入指定 playbook

| 角色 | 启动提示词（数据） | 读到的顺序 |
|---|---|---|
| worker | "Use the mmw skill's `worker` playbook on ticket #N." + `AUTONOMOUS` + `PRODUCT_RULES` | `mmw/SKILL.md` 入口表第 1 行 → `playbooks/worker.md` |
| reviewer | 不变："Use the code-review skill to review ticket #N from base commit C." + `AUTONOMOUS` | `code-review/SKILL.md`（能力技能，表分 reviewer 与 axis 两个时刻，不变） |
| advisor | 不变："Use the advisor skill." + brief | `advisor/SKILL.md` 第 2 行 |
| orchestrator | 没有脚本启动它；人在会话里说「今晚跑 spec #N」 | 提醒行或 description → `mmw` 路由表 → `playbooks/night.md` |

`AUTONOMOUS` 留在提示词里：「用户不在看」是启动时已知的事实，符合 `SKILL-SET-RULES.md` `### Prompts written for other agents` 第 1 条（提示词只带启动时已知的数据）；它后半句的规则（「在屏幕上提问会卡住工作」）由 mode `## Autonomy` 承接。是否把后半句从提示词里删掉，要一次真实的 worker 运行确认行为不变（T6），在那之前不删。

`PRODUCT_RULES` 不变：它只是指针加一句原因（N10 R9）。

### 5.4 夜里被唤醒、被压缩后怎样从 playbook 中间重入

| 机制 | 现状（已核实） | 新形态 |
|---|---|---|
| orchestrator 的事实表 | `night.md` 第 13–22 行；缺「`spec.retroed` 已记录、用户尚未验收」一行（N1 §9.2 第 1 条，本轮核实） | 整表随 `night.md` 搬家；补这一行（这是修一个已核实的断点，不是搬家的附带） |
| worker 的 `RESUME:` 行 | `verify-ticket.py` `resume_at`（2150–2180 行）按事件算出 "step 1" 到 "step 5" 等字样，指向 `implement` `## Closing steps` 的编号 | 收尾步骤原样搬进 `worker.md`，编号与小节标题保持不变；`verify-ticket.py` 只改文档串里指向的文件名。这是一处按步骤编号的跨组件连线（L7 E.1 第 2 条说这是 pstack 最脆弱的连线），MMW 接受它，因为脚本必须持有它匹配的字面（L7 A.6 `check-plan.mjs` 的先例），条件是一个测试同时钉住两边（未查现有测试是否钉住，第 15 节 T7） |
| `## On waking` | 在 `dispatch/SKILL.md`；worker 走表第 1 行时不经过它（N10 B9） | 在 mode；入口表第 2 行让每个被唤醒的会话都先经过它，B9 消失；`implement` 第 1、3 步里重复写的 ack（N10 R6）改为指向 `## On waking` |
| 被压缩的 orchestrator 收到 `#12 ticket.passed` | 文字不指向任何技能（N10 B8） | `mmw` 的 description 把唤醒行列为触发词；提醒行；两者都要实测（T2） |
| 人启动的头部流程跨会话 | 靠各技能结尾段，Claude Design 那一跳在另一个宿主会话里（`design-pages/SKILL.md` 第 21 行） | `idea-to-tickets.md` 的事实表；拉完设计包的会话回到 `mmw` 后按表找到「写 screen contract」这一步 |

### 5.5 C.1 第 7 问：单一入口单一任务类型的流程是否适用

| 流程 | 入口 | 任务类型 | 结论 |
|---|---|---|---|
| worker | 启动提示词，或人接手一张票 | 做一张票 | 适用。`worker.md` 是一份完整的操作文件，按名调用 `tdd`、`resolving-merge-conflicts`、`ui-acceptance`、`verify-ticket.py`、`dispatch.sh`。不再拆出「一步怎么做」的能力技能：拆出的部分没有第二个调用方（C.6 信号 9、10）。它仍以 playbook 的形态住在 mode 里，因为人也会从 mode 路由到它（自己接手一张票） |
| reviewer | 只有启动提示词（和 axis 子代理） | 评审一张票 | 适用，而且它已经是 pstack 的「子代理编排型」能力技能（L7 A.3 形态表，与 `interrogate` 同形：派四个 axis 子代理，提示模板在 references，交付物是一份写上票的报告）。保持能力技能，不进 mode |
| orchestrator | 人的一句话 | 跑一夜 | 适用。`night.md` 不拆：它具备 L7 C.4 列出的不拆理由（单一调用方；它本身就是交付物的程序；规则簇是执行中查阅的判断；机械部分已在 `dispatch.sh`） |
| advisor 的回答方 | 启动提示词 | 回答一个决定 | 是 `advisor` 能力的第二个时刻，不单列 |

---

## 6. Q4 原则

### 6.1 存放形式与命名

- **形式：** `mmw-v2/skills/mmw/principles/<slug>.md`，一条一个文件。选它而不是 pstack 的「每条一个技能」，理由见第 0 节第 2 条第二点。
- **命名：** `<slug>` 用英文短语，优先所在领域的既有术语（`SKILL-SET-RULES.md` `### Vocabulary` 第 2 条），如 `negative-control`；从 pstack 导入的保留 pstack 的 slug（去掉 `principle-` 前缀），以便对照来源。
- **文件模板（pstack 高频形态，L7 A.4）：** `# Title`；一行 `Apply when <情境>.`（顶替 pstack 的 description）；一到三句规则；`**Why:**`；`**Pattern:**`；可选 `**Stop:**` / `**The test:**`；可选一句 `Distinct from …`。不写命令、参数、输出格式。
- **引用方式：** mode 与 playbook 写 `principles/<slug>.md`（同一技能内的相对路径）；能力技能写 "the `mmw` skill's `principles/<slug>.md`"（`SKILL-SET-RULES.md` `### Hand-offs` 第 95 行的跨技能文件写法）。调用方点名原则，同时保留本处的具体化，并可限定原则在本处的范围（L7 C.2 "调用方可以限定原则的范围"）。上游技能的文本里不加原则引用（它们回到原文）。
- **怎样避免常驻上下文膨胀：** 常驻的只有 mode 索引里每条一行；全文只在应用时读（pstack "Read the leaf skill in full for any principle you apply."）。mode 本身只在工程会话里加载，不在每个会话常驻。
- **宿主差异：** 没有。普通文件，不经过任何宿主的技能机制。

### 6.2 够格的门槛

同时满足 L7 A.4 与 C.2 的六条：

1. 能用一个短名字说出口；
2. 有可观察的触发情境；
3. 能改变一个具体决定（说不出改变哪个决定的，不收）；
4. 跨任务：在两个以上 playbook 或能力技能里适用；
5. 不绑定某个具体机制或领域参数（绑定的留在调用方正文，C.2 第一类）；
6. 不是 owner 写在 `shared.md` 里的规则（那里是它的家，复制一份就是第二份）。

「已被按名复用」不是前提（L7 第 0 节第 2 条）。

### 6.3 用门槛过一遍 N9 的候选（第一刀，下一轮逐条核原文）

| 候选（N9 §9.1） | 判定 | 理由 |
|---|---|---|
| PC1 假通过比诚实失败更坏 | 原则 | 7 个技能；理由现在每处各写一句且彼此不同（N9 §9.3 末条），收进 `**Why:**` 后调用方只留本处的具体句 |
| PC2 检查要证明自己能失败 | 原则 | 7 个技能；与 PC1 改变的决定不同（写检查时 vs 报结果时） |
| PC5 进度读自持久记录 | 原则（`resume-from-the-record`） | 5 个技能；新形态的重入协议（5.2）直接依赖它 |
| PC8 基线即合同 | 原则 | 7 个技能、15 处（N9 核实） |
| PC11 线索不是证据 | 原则 | 5 个技能；与 `shared.md` 规则 4 近而不同（那条讲对 owner 的汇报，这条讲 Memory、reviewer Rule、brief 的用法） |
| PC12 同一文件同一时刻一个写者 | 原则，考虑直接导入 pstack `principle-separate-before-serializing-shared-state` | 3 个技能；pstack 已有同义原则（本轮未读该原则原文，只据 L7 B.3 与 pstack mode 第 61 行的一句摘要，推断） |
| PC18 起不来就停、不静默替代 | 原则 | 3 个技能；同时是与 `shared.md` 规则 11 的已核实张力（N9 §9.3 第 1 条）的解决处：写明 11 条的「自己重做」适用于自己的工作，不适用于流水线自身的故障 |
| 阶段边界（`ask-matt/PHASE-BOUNDARIES.md`） | 原则 | 原文在未安装的残留目录，没有第二份（N10 B5 已核实）；跨任务；带一个五问的有序判断树，符合「原则可以带短的顺序程序」（L7 A.4）；照录上游作者原文，来源记进 merge-note |
| PC4 不轮询、由事件叫醒 | 不是原则，进 mode `## Non-negotiables` | 绑定 relay 机制（C.2 第一类） |
| PC6 协议状态只由脚本写 | 不是原则 | 绑定机制，且 `tool-guard.py` 已机械拦截（Structural-mechanism check）；文字只留在执行者那一步 |
| PC3、PC7、PC13–PC16 | 不是原则 | 读者是写脚本或写技能的人，家在 `CODING_STANDARDS.md`、`SKILL-SET-RULES.md`、`shared.md` |
| PC9、PC10、PC14 | 不是原则 | `shared.md` 规则 1、10、15 是它们的家 |
| PC15 只读靠文字 | 不是原则 | 只在 `advisor` 与 `code-review` 两处 |
| PC17 被打断后原样重跑 | 运行时部分已在 `## On waking` 第 1 步；写脚本的部分可导入 pstack `principle-make-operations-idempotent` 给脚本作者 | 下一轮定 |

---

## 7. Q5 能力技能与 playbook 的分界

### 7.1 判据

一段内容是「任务顺序」（进 playbook），当且仅当它回答「这个技能的交付物做完之后，下一步做什么、交给谁」，或按调用者的角色或任务类型把读者送到别处。一段内容是「能力内部」（留下），当它回答「怎样产出这个技能的交付物」，包括按分支选 reference、调用别的能力技能来完成本交付物、自带的人工闸门（L7 A.3 "自带人工闸门……不算写错"）。依据：L7 第 0 节第 1 条与 C.3 的共同判据；B.2 硬规律 3「能力技能不依赖 playbook」。

### 7.2 五张「Find your moment」表逐行分类

| 技能与行 | 分类 | 去处 |
|---|---|---|
| `dispatch` 第 1 行（worker 起 reviewer 或被唤醒） | 任务顺序（按角色） | mode 入口表与 `worker.md` |
| `dispatch` 第 2 行（自己接手） | 任务顺序 | `worker.md` 开头的分支，材料在 `mmw/references/adopting-a-ticket.md` |
| `dispatch` 第 3 行（night） | 任务顺序 | `playbooks/night.md` |
| `dispatch` 第 4 行（one ticket） | 任务顺序 | `playbooks/one-ticket.md` |
| `dispatch` 第 5 行（改 host、model、runner） | 能力内部 | 留下 |
| `dispatch` 第 6 行（task board） | 能力内部 | 留下 |
| `dispatch` `## On waking` | 跨 playbook 协议 | mode |
| `design-pages` 四行（建项目与签字、画页、拉取、设计系统） | 能力内部 | 留下；`edit-pages.md` `## Next` 指向同技能的 `pull.md`，属本能力的完成方式，留下 |
| `design-pages/references/pull.md` `## Reached from here` | 任务顺序（按有无 map、有无 screen contract、`改动分类` 决定下一个技能） | `idea-to-tickets.md` |
| `design-pages/references/pull.md` `## A contract child answered by this pull` | 任务顺序（`dispatch.sh route`、`resume` 这类流水线记账） | 夜间 `contract` 子票的后续，具体家下一轮定（`night.md` 的规则簇，或 `idea-to-tickets.md` 的一个入口） |
| `write-screen-contract` `## Next` | 任务顺序 | `idea-to-tickets.md` |
| `ui-acceptance` 第 1 行（写页面票代码之前） | 任务顺序（把 worker 送回 `implement`，N10 B7 的往返） | `worker.md` 的那一步；description 去掉 "before writing a page ticket's code" |
| `ui-acceptance` 第 3 行（把标准写到票上） | 指向 `to-tickets` 内部的路由 | 删除；`to-tickets` 自己持有 **Criterion shapes** |
| `ui-acceptance` 其余 7 行与 `## Five rules while the product is running` | 能力内部 | 留下 |
| `verify-ticket` 第 16 行 "A worker's claim … are steps of the `implement` skill." | 按角色的路由 | 删除，mode 入口表承担 |
| `verify-ticket` 两行（sub-issues、linting）与 `## Reached from here`（→ `ui-acceptance`） | 能力内部；后者是能力之间的横向调用 | 留下 |
| `code-review` 两行（reviewer、axis） | 能力内部（同一能力的两个时刻） | 留下 |
| `retro` 第 186 行 "then return to the dispatch skill's `references/night.md` `## 5`" | 点名调用方 | 删除后半句；`night.md` 第 5 步在调用 `retro` 之后继续 |
| `to-tickets` 第 8 步末句 "hand over to the `dispatch` skill" | 任务顺序 | `idea-to-tickets.md` |

### 7.3 上游技能回到原文的规则

**留在上游文本里的改动只有三类：**

1. **改变能力本身的改动**：任何调用方、在 MMW 之外使用这个技能都会受益，或者它改变的是这项能力做什么。例：`prototype` 的第三个分支 `EXP.md`；`resolving-merge-conflicts` 多出的「干净合并让检查变红」触发；`wait-what` 的 `visual`；`writing-for-agents` 适用范围放宽（N10 §6 标为「改变能力」或「能力扩展」的几项）。
2. **宿主中立的写法**：把 "Call the Skill tool" 改成读 `SKILL.md` 或按名点名（`merge-notes/README.md` `## host 中立`）。这是让能力在五个宿主上都能用，属于能力可用性。
3. **调用方式翻转**：`disable-model-invocation` 与 `policy.allow_implicit_invocation` 这一对，只在 mode 或某个 playbook 要按名到达它、而上游设成用户触发时翻转。今天翻转了六个（`implement`、`to-spec`、`to-tickets`、`triage`、`wayfinder`、`to-questionnaire`，已对照 `5b1a4c51` 核实上游都是 `true`）；`implement`、`to-tickets` 搬走后剩四个（`to-questionnaire` 以 `idea-to-tickets.md` 在「决定卡在别人脑子里」时点名它为前提）。没有别的办法让 mode 够得到它，只能改这一行（第 0 节第 2 条）。翻转连带 description：上游规则 `upstream/.agents/invocation.md` 说模型可触发的技能 description 要面向模型、带触发词，所以翻转后的 description 可以加「Use when …」，但只写这项能力本身的触发，不写 MMW 流程的分支（例：`to-spec` 现在的 "a wayfinder map or a triaged issue has to become a spec" 属流程分支，搬到 mode 路由表）。

**搬走的：** 结尾段点名下一步（`to-spec` `## Next`、`grill-with-docs` 末句、`wayfinder` 第 6 步、`improve-codebase-architecture` `### 4`、`prototype` `UI.md` `## Next`）；description 里为 MMW 流程加的分支（`to-spec`、`triage`、`wayfinder`；逐句判定下一轮做）；只为文风改的句子。`to-questionnaire` 把 "you" 改成 "the user" 是文风还是改变了读者（agent 还是用户），本轮没有读它的 merge-note 理由，未确定。

**只有 MMW 下游读的产物约定**（例：`prototype` 规则 1 的叶目录 `prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/`，`design-pages` 的 `pull_design.py` 读其中 `## State list`，N11 missing_edges 第 6 条）：按 `SKILL-SET-RULES.md` `### Upstream skills` 第 3 条「先在边缘接入」，放进上游技能目录旁加的一份 reference（上游没有这个文件，拉取不冲突），由 playbook 那一步点名。逐项归置下一轮做。

**正文过半是 MMW 写的上游技能：** 整体搬到 `mmw-v2/skills/`，上游目录恢复原文并不安装。`implement` 的正文进 `worker.md`（它是任务顺序）；`code-review`、`to-tickets` 保持名字、搬目录、仍是能力技能。好处：`merge-notes/README.md` `## 本仓自有正文的技能` 那条「冲突取本仓的，自动合进来的上游段落也改回」的特例整条消失，拉上游变成机械操作。代价：约 12 个文件与两份测试钉着 "Use the implement skill"（已 grep：`dispatch.sh`、`tool-guard.py`、`verify-ticket.py`、`ui-acceptance/SKILL.md`、`verify-ticket/SKILL.md`、`verify-ticket/references/sub-issues.md`、`write-screen-contract/references/screen-contract-format.md`、`SKILL-SET-RULES.md`、`tests/dispatch/test_dispatch.sh` 2830、5188、6984 行、`tests/dispatch/test_profiles.py` 70 行、`tests/verify-ticket/test_preflight.py`），同一次编辑一起改。

**放弃的备选：** 三个技能留在上游目录（维持特例）；改名（`ticket-review` 等）：好处只在「以后也想装上游原版」时出现，那是范围决定，交给 owner（U3），不为它先付改名成本。

**决定何时生效：** playbook 与能力技能正文冲突时的优先级写在 mode `## Autonomy`（4.2）：关于「交付物之后做什么」以 playbook 为准。这让 `prototype` 规则 6 的 "fold the validated decision into the real code" 可以回到上游原文，而 Build 流程里 prototype 那一步写明结论进 spec、代码由票来写（修 N10 B4）。风险：不在 Build 流程里的会话读到上游原文会直接写代码，这正是上游的本意，也是 Small change 路线的合法做法。

---

## 8. Q6 旧规则的处理

每条只问：它原本防什么；新架构能否更好地解决。

### 8.1 `SKILL-SET-RULES.md` 的七条事实

| 事实 | 处理 | 原本防的问题 | 新架构下怎样 |
|---|---|---|---|
| 1 技能交出理解而不只是步骤 | 保留，适用范围扩到 playbook 与原则 | 步骤覆盖不到的情形里 agent 无判断依据 | 原则文件的 `**Why:**` 正是这条的集中形式 |
| 2 脚本管确定性，文字管判断 | 保留 | 文字复述脚本；本可机械检查的规则写成文字 | 与 pstack `principle-encode-lessons-in-structure` 及 `synthesizer.md` Structural-mechanism check 同义（L7 C.1 第 2 问） |
| 3 注意力是预算 | 保留，加一条：mode 的文字每个工程会话都读，预算最紧 | 不相干材料挤占判断 | mode 目标篇幅不超过 pstack mode 的 143 行（推断的上限，第 15 节 T8 实测） |
| 4 先指明、再信任 | 保留 | 过度规定让流程僵硬、易碎 | 无变化 |
| 5 渐进加载按分支 | 保留 | 每次都读的材料拆成碎片多一跳 | `## On waking` 放在 mode 正文而不单列 reference，就是按这条（C.6 信号 6） |
| 6 技能是按名组合的平级件 | 改写 | 嵌套、复制别的技能的文件或规则 | 改为：能力技能之间平级、按名组合，不复制彼此的文件与规则（原意全保）；**新增**：能力技能不点名它的调用方，也不点名下一步（L7 B.2 硬规律 3）；playbook 按名点名能力技能，不复述它们的规则 |
| 7 一个家；「MMW ships no router skill」；description 说何时开始、结尾段说下一步 | 改写，其中两句废止 | 第二份副本漂移并与第一份矛盾（`ask-matt` 的漂移有记录：`docs/reviews/2026-09-23-skill-set/汇总.md` 第 44 行，N10 第 7 节）；一跳找不到下一步（#538） | 「一个家」保留原文。「no router skill」废止：它的理由是路由会成为流程的第二份（结尾段是第一份）；新形态把结尾段的「下一步」删掉、流程只在 playbook 里，mode 路由表只指向 playbook 而不复述流程，于是不存在第二份。「结尾段说下一步」改为「playbook 说下一步；能力技能以交付物结束并返回」。#538 那类断点由 playbook 持有整条顺序、提醒行让 playbook 在场、事实表支持跨会话接续来防；外加一条机械检查（8.2 `### Hand-offs` 行） |

### 8.2 各节检查

| 节 | 处理 | 说明 |
|---|---|---|
| `### Load and disclosure` | 保留，改一处 | 找时刻的表仍在任何有副作用的步骤之前；新增：能力技能的表只放本能力内部的时刻，按角色或任务类型的行放 mode 入口表（7.2 就是按这条分的） |
| `### Redundancy and bloat` | 保留 | 无变化 |
| `### Scripts and judgement` | 保留 | 无变化 |
| `### Descriptions` | 保留，补一条 | 补：mode 的 `## Non-negotiables` 不写已有 description 覆盖的触发，二者并排读时同样按第 2 条查冲突。「A branch naming the role an agent was started as is a trigger」保留给 `code-review`、`advisor` |
| `### Vocabulary` | 保留，注明一个已知例外 | 「按位置找的标题或步骤按标题引用、不按编号」与 `verify-ticket.py` `RESUME:` 的步骤编号不一致；这是现存事实，新形态不增不减，由测试钉住（T7） |
| `### Hand-offs` | 改写一条，保留其余 | 「Each skill ends by naming what comes next, or the caller it returns to」改为：每个 playbook 的每一步点名它用的技能，最后一步点名 `Reply`；能力技能以交付物结束。原意（没有无人接手的产出）保住，另加**机械检查**：一个 lint 检查 mode 与各 playbook 点名的每个技能都在 `skills.txt`、点名的每个 playbook、原则、reference 文件都存在（与现有 `tests/lib/check_module_paths.py` 同类，按 Structural-mechanism check 用机制代替「保持同步」的文字）。这条 lint 同时是 Memory `ce037679`「一张与实际同步的总图」的落地：mode 路由表加 playbook 就是那张图，lint 保证它与实际同步。「Each event gets one instruction」保留，新形态的 `## On waking` 与 `NO_QUESTION` 修正都是它的应用 |
| `### Prompts written for other agents` | 保留 | 启动提示词点名 mode 与 playbook、票号、base commit；`AUTONOMOUS` 作为启动时已知事实留下（5.3） |
| `### Upstream skills` | 保留并加细 | 加 7.3 的三类允许改动、「正文过半是 MMW 的搬到 `mmw-v2/skills/`」 |
| `### Paths and host neutrality` | 保留，补一句 | mode 内部的 playbook、原则、reference 按相对路径；从别的技能点名时写 "the `mmw` skill's `principles/x.md`" |
| `### Rules and completion criteria` | 保留，扩到 playbook | `Done when` 行 |
| `### Examples`、`### Refusals` | 保留 | 无变化 |

新增一节（下一轮写）：组件类型与归类判据，内容取自 L7 C.1 的判定顺序与 C.6 的信号，放在 `SKILL-SET-RULES.md` 里而不是新建 playbook：读者是写技能的 agent，它已经会加载这份文件。

### 8.3 ADR

| ADR | 处理 | 原本防的问题 | 新架构下怎样 |
|---|---|---|---|
| 0003 不打包成插件 | 保留 | 插件与安装器两条安装路径 | pstack 用 Cursor 插件，MMW 不跟；mode、playbook 都是技能目录里的文件，安装路径不变 |
| 0006 技能装到中立目录 | 保留 | 按宿主各装一份 | 无变化 |
| 0007 提示词源在仓库 | 保留，扩展 | 各宿主提示词手改漂移 | 提醒行也从 `shared.md` 经 `render.py` 分发 |
| 0010、0020、0022 事件唤醒 | 保留 | 轮询浪费回合、宿主时限 | 唤醒行成为 `mmw` 的触发词 |
| 0014 advisor 一扇门 | 保留决定；「caller 侧规则不进用户级提示词」的否决理由部分不适用于提醒行 | 为偶发事付常驻成本；到不了 Cursor | 提醒行不是偶发事的规则；Cursor 缺口由 3.3 表处理。新 ADR 记录这一区分 |
| 0015 不交付 subagent | 保留 | 五种壳、组装链 | agent 定义 = 启动提示词点名 playbook + `models.json` 一行，与 pstack 的 agent 定义（读 mode）对应，不需要 subagent 文件 |
| 0018 runner 一个边界、0019 状态是事件折叠、0024 `models.json` | 保留 | — | playbook 读事件，脚本写事件，不变 |
| 0012、0027 | 不在本次范围；N11 记录的两处分歧（0012 规则 2 与 `night.md`；0027 与 `advance` 实现）随 `night.md` 搬家原样带走，另行处理 | — | 搬家不改内容 |

新增一份 ADR：「MMW 有一个 mode 与 playbook」，记录取代了事实 7 的哪两句、原意怎样保住、三处偏离 pstack 的理由、放弃的备选。

### 8.4 `merge-notes/README.md` 的 `disable-model-invocation` 规则

| 条 | 处理 | 说明 |
|---|---|---|
| 两处开关同增同删 | 保留 | 防一半宿主用户触发、一半模型触发；新形态仍需要 |
| 上游技能默认模型可触发 | 保留做法，改写理由 | 原理由「user 漏说技能名时 agent 自己认得出」；新理由「mode 与 playbook 要按名到达它；在 Claude Code 上关掉触发等于从模型视野里移除」 |
| 7 个保留用户触发的名单 | 保留 | 它们的理由（抢触发、夜里无人回答、往产品根目录写文件，`c9f4e5c7`）与分层无关 |
| 「每份说明只写它那边，不复述这条规则」 | 保留，并执行 | N10 R2 核实有 4 份 merge-note 复述了它，是现存 finding |
| `## 本仓自有正文的技能` | 废止 | 三个技能搬走后没有对象 |

### 8.5 Memory 里的写法决定

| Memory | 处理 | 说明 |
|---|---|---|
| `411750f5` description 只写触发；上游能不改就不改，接入在边缘做 | 保留，并更彻底地执行 | 结尾段与路由触发句搬出上游正是这条的延伸 |
| `ce037679` 名字即可调用、不写路径；不系统区分用户与模型调用；唯一性与系统性、一张与实际同步的总图 | 保留 | 新形态不给技能写路径；不改变任何技能的触发方式（除三个搬走的）；「总图」= mode 路由表 + playbook，由 8.2 的 lint 保证同步 |
| `fe94802d` 平级调用、禁止嵌套、不改上游 frontmatter；否决用 `disable-model-invocation` 强制层级 | 前两条保留；「不改上游 frontmatter」与现有做法（已翻转六个技能）早就不一致，新形态把翻转减到四个并写明理由；「否决强制层级」正是本方案不照搬 pstack 的原因 | 需 owner 确认「翻转算必要改动」这个读法（U4） |
| `f4c3d378` 以技能为第一层编排 | 保留，读法更新 | 路由与编排在技能层做：mode 就是一个技能，playbook 住在它里面 |
| `c155ffc2` 调用方只给角色名与票号 | 保留 | 启动提示词点名 playbook（角色）与票号 |

---

## 9. Q7 扩展路径

### 9.1 从 pstack 或其他合集加东西

| 加什么 | 怎么进来 | 触碰的现有文字 |
|---|---|---|
| 能力技能 | 仓库有 subtree 的合集：`git subtree pull`（mattpocock、diagram-design、unlazy 的现有做法）。pstack 住在 `cursor/plugins` 仓库的 `pstack/` 子目录里，`git subtree` 直接拉的是整个仓库；做法二选一：在本地克隆上 `git subtree split --prefix pstack` 得到只含 pstack 的分支再 `subtree add`，或快照拷贝进 `mmw-v2/upstream-pstack/` 并在 merge-note 记源提交（快照为 `b0b9c7a0`，`plugin.json` 0.15.4）。按导入频率选：只拿几份文件用快照，要跟随更新用 split。pstack 是 MIT 许可（`LICENSE` 已核实） | `skills.txt` 一行；翻转 `disable-model-invocation`（pstack 46/47 个技能带它，L7 A.3）；按 9.2 替换 Cursor 专有机制；merge-note 一份 |
| 原则 | 正文照录进 `mmw/principles/<slug>.md`；pstack 的 description 改成首行 `Apply when …`；原则之间的相对链接 `../principle-x/SKILL.md` 改为 `x.md` | mode `## Principles` 加一行；merge-note 记来源与这两处改写 |
| 工作流（playbook） | 文件拷进 `mmw/playbooks/`；把 "Run **Opening a PR**" 换成 MMW 的交付结尾（Build 或 Small change 的结尾；MMW 的流水线不开 PR，由 orchestrator 落地，`implement` 第 8 步）；按 9.2 替换 Cursor 机制 | mode 路由表加一行。这就是「扩展只加不改」的落点：只动 mode 的一行 |
| 脚本 | 放进拥有它的技能的 `scripts/`，调用命令写在调用方正文（L7 A.6） | 调用方一步 |

**不能原样搬的：** pstack 的 Bug fix、Feature、Refactoring 等 playbook 都以开 PR 收尾、用 `architect`、`arena` 等 MMW 没有的技能、用 Cursor 的 `/loop` 与云代理；搬进来之前要先决定它在 MMW 里对应哪条路线（Small change 还是 Build 的一步）。这是产品范围决定（U5）。

### 9.2 Cursor 专有机制的替换（L7 E.2 逐行）

| pstack 机制 | MMW 替换 |
|---|---|
| `mode: true`、`reminder:` | `shared.md` 提醒行 + `mmw` description（3.3） |
| `disable-model-invocation: true` | 不用于可达的技能；只给确实只该人触发的技能（7 个现有的） |
| `paths:` | 无对应；按文件类型的规则写进 `CODING_STANDARDS.md`（review axis 读）或由 `code-checkers` 变成检查 |
| `.mdc` 加 `alwaysApply` 的模型角色配置 | `~/.mmw/models.json`，只管脚本启动的四个角色（`models.py` `ALLOWED_AGENTS`）；会话内的子代理跑在父会话的模型上（ADR 0015）。pstack 的面板角色（`arena runners` 列表决定扇出数）没有对应，导入 `arena` 类技能前要先定这件事 |
| `agents/*.md` + `subagent_type` | 宿主自带的通用 subagent，告诉它用哪个技能（ADR 0015） |
| `Task` 的 `model`、`run_in_background`、`readonly` | 写成能力（"where the host lets you choose the subagent's model"）；只读靠文字（PC15） |
| `/loop`、`/goal`、云代理、cloud-sleeper | relay 事件唤醒与 watchdog；不导入依赖云代理的 playbook |
| 运行中 `git show origin/main:` 重读组件 | 禁止（`AGENTS.md` `## Self-hosting boundary`） |
| 内置 `create-skill` | `writing-for-agents` 技能 |
| `AskQuestion` | 有人值守：直接问；无人值守：mode `## Autonomy` 与本 playbook 写明的去处 |
| `~/.cursor/projects/…/agent-transcripts/` | 不导入依赖它的内容；MMW 的重入读 tracker 与仓库 |
| `cursor-team-kit` 的 `control-ui`、`control-cli`、`deslop` | 按角色槽位写（L7 B.1）：浏览器与界面驱动对应 `playwright-cli`、`computer-use`、`ui-acceptance` 的 oracles；`deslop` 没有对应 |

### 9.3 项目私有组件（L7 A.11）在 MMW 里对应什么

| 组件 | 生成方 | 维护方 | 位置 |
|---|---|---|---|
| 产品答卷 `.mmw/target.json` 及 `harness/`、`journeys/`、`stories/` | `ui-acceptance` 的 `target_config.py` 与 contract ticket | 同左 | 消费仓库 `.mmw/` |
| screen contract | `write-screen-contract` | 同左（`Re-runs`） | `docs/specs/<effort>/screen-contract.yaml` |
| 仓库的 `AGENTS.md`、`CLAUDE.md`、`CODING_STANDARDS.md`、`TESTING.md` | `manage-agents-md` | 同左；`retro` 的 `repository-agents` 去处 | 消费仓库根 |
| 词表与 tracker 约定 `CONTEXT.md`、`docs/agents/*.md` | `setup-matt-pocock-skills`、`domain-modeling` | 同左 | 消费仓库 |
| 仓库专有的多步工作流 | `retro` 的 `repository-skill` 去处（`retro/SKILL.md` `## Prevention destinations`：「a repeated multi-step workflow specific to one repository, as a repository-local skill with a discovery test」） | 该仓库 | 仓库本地技能目录 |
| 模型角色 | `models.py config` | 同左 | `~/.mmw/models.json`（对应 pstack 的 `pstack-models.mdc`） |

mode 要为最后第二行写一条优先级：仓库本地的技能或 `AGENTS.md` 认领同一任务时，它们先于 mode 的路由表。不为仓库专有的 playbook 另开 `.mmw/playbooks/` 这样的槽位：现在没有任何仓库需要它（按用户要求第 2 条，不加没有价值的东西），`repository-skill` 已经是那个扩展点。宿主是否扫描仓库本地技能目录，各家行为未核实（第 15 节 T9）。

---

## 10. Q8 风险与验证

| # | 风险 | 最可能坏在哪里 | 怎样验证 |
|---|---|---|---|
| R1 | 头部衔接依赖 mode 在场 | 结尾段删掉后，一个直接用 `/to-spec` 进来、没加载 `mmw` 的会话写完 spec 不知道下一步是 `to-tickets`；Cursor 上没有提醒行 | T1、T4：新会话只给「我在这个仓库有个想法 X」和一张真实需求，看它开了哪些文件、在哪里猜、是否走到 `to-tickets` 发布；另起一个只打 `/to-spec` 的会话看结束时是否回到 mode |
| R2 | 夜间重入 | 被压缩的 orchestrator 收到 `#12 ticket.passed` 不回 `night.md`；`## On waking` 搬家后 worker 的 ack 与重跑行为变了 | T2：隔离测试 HOME（`AGENTS.md` 要求的 fake tracker、fake runner）里起一个 orchestrator，压缩上下文后投一条唤醒行，看它是否加载 `mmw` 并进入事实表第 3 行；worker 同样，看是否先重跑被打断的命令、再 ack |
| R3 | 冻结运行时 | 改造跨越 `skills.txt`、启动提示词、`RESUME:` 字样、技能目录搬家；只要装好的 checkout 在 watch 打开时被移动，旧 `dispatch.sh` 起的 worker 会读到新 playbook（或反之） | 发布规程：只在没有 watch 打开时做 `AGENTS.md` `## Gotchas` 的第三步；`install.sh` 需 owner 授权后跑一次（技能列表变了）；`--check` 为 0 才算完。兼容性：收尾步骤的编号与标题保持不变，使一张在旧版里停在 `needs-triage` 的票被新版 worker 接手时 `RESUME:` 仍指对步骤 |
| R4 | 多宿主 | Pi、Cursor 上按相对路径打开 `mmw/playbooks/*.md`、按「the X skill's file」打开跨技能文件是否可靠；Codex 是否读 `openai.yaml` 的 `policy` | T3：在隔离 HOME 下为每个宿主装开发版技能，起新会话，给 "Use the mmw skill's worker playbook on ticket #N"，看它打开的文件 |
| R5 | 上游拉取 | 上游改名、删掉或拆分 playbook 点名的技能；上游把 `to-spec` 等改回模型可触发或更进一步地改 frontmatter | 8.2 的 lint 在每个套件的 `run.sh` 开头跑，与 `check_module_paths.py` 同位置；拉取后先跑它 |
| R6 | mode 变胖 | mode 每个工程会话都读，worker 也读；内容一多就挤占 worker 的注意力 | T8：写成后计行数与词数，对比 pstack mode（143 行）；让一个 worker 真跑一张票，比较前后打开的文件与完成情况（`SKILL-SET-RULES.md` `## Verifying`） |
| R7 | description 恢复上游原文后自动选中变弱 | 不经过 mode 的会话少了 MMW 加的触发句 | 与 R1 同一组实测 |
| R8 | 事实表不完整 | 与 `night.md` 缺的那一行同类的遗漏，出现在新写的 `idea-to-tickets.md` 表里 | 对每张事实表，列出流程的每个持久状态，逐个确认有一行接住（这是一次读表检查，不是测试） |
| R9 | 原则成了第二份 | 原则 `**Why:**` 与调用方保留的理由句重复 | 规则：调用方只留本处的具体句与原则名；下一轮逐处 grep |

---

## 11. 偏离 pstack 的清单

| # | 偏离 | 原因（MMW 做不到 pstack 的什么） |
|---|---|---|
| D1 | mode 模型可触发，无 `mode`/`reminder` 键 | 没有 Cursor 的常驻机制；提醒行需要一个可加载的目标；被唤醒、被压缩的会话要能自己回来 |
| D2 | 能力技能保持模型可触发 | Claude Code 上关掉触发的技能对模型不可见（已核实），mode 点名够不到 |
| D3 | 原则是文件不是技能 | 同 D2；可触发的原则技能会常驻 description 且被自动触发 |
| D4 | mode 多一张入口表与 `## On waking` | 脚本启动的会话与事件唤醒，pstack 没有 |
| D5 | playbook 每步 `Done when`，可重入的 playbook 开头一张事实表 | 事件唤醒与 `RESUME:` 依赖可观察的完成判据；状态在 tracker 而不在 transcript |
| D6 | 没有 `session-pickup`、`pause-safely` playbook | MMW 的接续读 tracker 与仓库（事实表、`RESUME:`）；夜的暂停是 `dispatch.sh suspend`（`night.md` `## Suspending the night`） |
| D7 | 没有 agent 定义文件 | ADR 0015；agent 定义 = 启动提示词 + `models.json` 一行 |
| D8 | `## Non-negotiables` 只列 description 之外的触发 | description 是活的，重复即冲突 |
| D9 | 回复写法不在 mode | `shared.md` 是它的家 |
| D10 | 被中断的 worker 用 `dispatch.sh resume` 续跑，不照 pstack 的「重开一个新子代理」 | worker 会话持有票的上下文；`night.md` 已写明反复 `continue` 是缺陷。pstack 自己在这点上也不一致（L7 E.1 第 29 条） |
| D11 | 不从 trunk 重读组件 | Self-hosting boundary |

---

## 12. 每一次移动、拆分、新建的收益

收益类别按用户要求第 2 条：①去掉经 grep 核实的真重复；②给无处安放的内容一个家；③把 MMW 流程移出上游文本；④让内容被两个以上调用方复用；⑤以后加外来技能不必改现有文字；⑥消除已核实的断点或冲突。

| 动作 | 收益 | 证据 |
|---|---|---|
| 新建 `mmw` mode | ②（头部 Yes/No 与「谁来检查」、阶段边界、「不知道用哪个技能」三块内容，只在未安装的 `ask-matt` 里）；⑤（加 playbook 只动路由表一行）；⑥（B8、B9） | N10 B1、B3、B5、B8、B9，§10.1；本轮核实 `ask-matt` 原文 |
| 新建 `idea-to-tickets.md` | ②（`ask-matt` 主流程）；③（5 个上游技能的结尾段）；⑥（B2 `grilling` 无下一步、B4 `prototype` LOGIC/EXP 无下一步、B6 `diagnosing-bugs` 无交接） | N10 B2、B4、B6、§6 |
| `implement` 正文 → `worker.md` | ③（上游 `implement` 回到 15 行原文，特例条消失）；①（`dispatch` 与 `implement` 的 ack 重复 R6；`dispatch`、`ui-acceptance`、`verify-ticket` 三处 description 或表行各自声称 `implement` 的一步，R7、R8、B7） | N10 R6–R8、B7；上游原文已核实 |
| `night.md`、`one-ticket.md` 搬进 mode | ①（`dispatch` 的 description 与 `implement` 都声称「起 reviewer」这一时刻，R7；`retro` 第 186 行与 `night.md` 各写一次返回，N10 §9 列为一条边的两端）；⑤（夜类流程与其他 playbook 同处，路由一处） | N10 R7、§9 |
| `## On waking` 搬进 mode | ⑥（B9）；①（R6） | N10 B9、R6 |
| `inside-a-ticket.md` → `mmw/references/adopting-a-ticket.md` | 随 `worker.md` 走：它唯一的读者是 worker 的「自己接手」分支；不搬的话 `worker.md` 要跨技能跳到 `dispatch` 读它 | `implement` 第 12 行现在就是这一跳 |
| `writing-interface-code.md`、`saving-memory.md` 搬进 `mmw/references/` | 随 `worker.md` 走，唯一读者是 worker 的两个分支 | N3 §2.2、§2.3 |
| `code-review`、`to-tickets` 搬到 `mmw-v2/skills/` | ③（特例条消失，上游目录可原样拉取） | `merge-notes/README.md` 第 34–36 行 |
| 原则文件 | ①（理由句多处各写，N9 §9.3 末条）；②（阶段边界）；④（每条都有两个以上调用方，门槛第 4 条） | N9 §9.1 |
| mode `## Autonomy` 写层级 | ⑥（`NO_QUESTION` 与 `implement` 第 23 行给同一事件两种指令，已核实；`shared.md` 规则 11 与 `ui-acceptance` 规则 4、5 的张力，N9 §9.3） | `tool-guard.py` 76–80 行 |
| 8.2 的 lint | ⑥（让「总图与实际同步」成为可失败的检查，而不是文字要求） | Memory `ce037679`；N10 §8 注 |
| `night.md` 补重入表一行 | ⑥ | N1 §9.2 第 1 条，本轮核实 |

---

## 13. 不动清单

| 不动的 | 理由 |
|---|---|
| 全部脚本（`dispatch.sh`、`relay.py`、`watchdog.py`、`turn-guard.py`、`tool-guard.py`、`models.py`、`verify-ticket.py`、oracles、`lease.py`、`retro.py`、`pull_design.py` 等）的位置与行为 | 已在拥有它们的技能的 `scripts/` 下，与 pstack 相同；只改其中点名 `implement` 的字符串与 `NO_QUESTION` 文字 |
| `night.md` 的内容与结构 | 单一入口、单一任务（C.1 第 7 问）；C.4 的不拆理由全部成立；只改命令写法与补一行重入表 |
| `worker.md` 不再细分 | 同上；拆出的部分没有第二个调用方 |
| `code-review` 的 `references/session.md` 与四个 axis 文件 | 子代理提示模板属于它的能力（L7 A.5 第一行） |
| `ui-acceptance` 的 `## Five rules while the product is running` | 绑定它的 oracles 与 lease，是能力内部；`PRODUCT_RULES` 只是指针 |
| `verify-ticket` 的 `references/sub-issues.md`、`linting.md` | 能力内部 |
| `advisor` 的两个时刻 | 能力内部；ADR 0014 |
| `design-pages` 的四个时刻与 `edit-pages.md` → `pull.md` | 能力内部的完成方式 |
| 7 个用户触发技能 | 它们的理由与分层无关（`c9f4e5c7`） |
| `diagram-design`、`exe-release`、`code-checkers`、`manage-agents-md`、`research`、`wizard`、`codebase-design`、`domain-modeling`、`grilling`、`tdd`、`to-questionnaire`（描述恢复原文之外）、`writing-for-agents`（描述之外） | 自身完整的能力，description 已正确触发 |
| `shared.md` 除提醒行外的全部内容 | owner 的原话；是回复写法与决定权的家 |
| `CODING_STANDARDS.md`、`TESTING.md` | 本仓的规则，review axis 读；不是 MMW 的运行时原则 |
| `CONTEXT-MAP.md` 与 `docs/contexts/` | 词表；只随改名同步 |
| ADR 全部（新增一份，不改旧的正文） | 决定记录允许有历史（`shared.md` 规则 13 的例外） |
| `install.sh`、`render.py`、board、`migrations/` | 安装与运行设施；`install.sh` 的逻辑按 `skills.txt` 自动适应 |
| 消费仓库的 `.mmw/` 与票正文 | 票模板不点名 `implement`（已 grep `to-tickets` 与其 references）；推断不需要 downstream-note，历史票未查 |
| `night.md` 的规则簇（authority order、四步门槛、三条提交规则） | 绑定机制、单一调用方（C.2），不抽成原则 |
| N9 的 PC3、PC4、PC6、PC7、PC9、PC10、PC13–PC16 | 见 6.3 |
| 仓库专有 playbook 槽位 | 没有需求；`repository-skill` 已是扩展点 |
| `SKILL-SET-RULES.md` 的位置（在 `writing-for-agents` 目录下，是本仓加的文件） | 加在上游技能旁的文件不产生拉取冲突；读者（写技能的 agent）已经会加载它 |

---

## 14. C.6 形式拆散十一条自查

| # | 信号 | 本方案 |
|---|---|---|
| 1 | 新建前没确认已有组件不是归宿，或模式并不反复出现 | mode：已有组件里没有头部内容的家（`ask-matt` 未安装，已核实）；playbook：全部是现有文件搬家或已有内容的集中，只有 `idea-to-tickets.md` 是新文件，它收的是 `ask-matt` 主流程与 5 处结尾段；原则：只收两个以上调用方的 |
| 2 | 新增不改变未来代理的行为 | 入口表改变被唤醒 worker 的第一步（先重跑）；路由表改变头部的第一步；每条原则写明改变的决定 |
| 3 | 重复已有的、位置得当的指引 | mode 不复述 `shared.md`；`## Non-negotiables` 不复述 description；原则的调用方只留具体句 |
| 4 | 本可由机制强制的规则写成文字 | 「总图同步」做成 lint；PC6 不写成原则（已有钩子）；`RESUME:` 编号由测试钉 |
| 5 | 拆出的 playbook 只调用一个技能、没有门槛、所有权或交付物 | Small change、Foggy effort、Incoming issue、Hard bug 都只写路由行，不建 playbook |
| 6 | 拆出的 reference 每次都读、单一调用方、读者是本代理 | `## On waking` 放 mode 正文不单列；`adopting-a-ticket.md`、`writing-interface-code.md`、`saving-memory.md` 都只在分支读 |
| 7 | 原则说不出改变哪个决定，或只适用于一个流程的一步 | 6.3 按门槛排除了 PC4、PC6、PC15 等 |
| 8 | 调用方要按步骤编号引用被拆出的部分 | 唯一一处是现存的 `RESUME:`（不增加）；mode 与 playbook 之间只按标题引用 |
| 9 | 拆出的内容没有第二个调用方、也不减重复 | `night.md`、`one-ticket.md` 搬家的收益主要是①和⑤，其中①只有 R7 一处与 `retro` 返回句一处，是本方案里收益最薄的一步（如实记录）；若 owner 选 3.2 的降级方案 D，这一步是第一个可以不做的 |
| 10 | 单入口固定流程拆成三层 | `night.md`、`worker.md` 各一份；reviewer 一个能力技能 |
| 11 | 只在任务流程之间复用的内容做成能力技能 | worker 的顺序进 playbook 而不是保留为 `implement` 能力技能 |

---

## 15. 未确定与需要的实测

**需要实测（全部在隔离测试 HOME 里做，装开发版技能，不碰已安装的 checkout，符合 `AGENTS.md` `## Self-hosting boundary`）：**

| 编号 | 问题 | 实测 |
|---|---|---|
| T1 | Claude Code、Codex、Pi、Grok 是否遵从用户级提示里的提醒行去加载 `mmw` | 每个宿主新会话，只说「在这个仓库我想做 X」；记录第一个加载的技能 |
| T2 | 被压缩或清空上下文的会话收到 `#<n> <event>` 后是否回到 `mmw` 与对应 playbook 的事实表 | fake runner 投递唤醒行；orchestrator 与 worker 各一次 |
| T3 | 各宿主能否按相对路径打开 `mmw/playbooks/*.md`，按「the X skill's file」打开跨技能文件 | 启动提示词 "Use the mmw skill's worker playbook on ticket #N"，记录打开的文件；重点是 Pi 与 Cursor |
| T4 | 直接斜杠进入某个能力技能的会话，结束时是否回到 mode | `/to-spec` 起一个会话，看是否走到 `to-tickets` |
| T5 | Cursor 的补救渠道：用户规则手贴或 `~/.cursor/rules/*.mdc` 加 `alwaysApply` 是否生效 | Cursor 新会话看提醒是否在上下文 |
| T6 | 删掉 `AUTONOMOUS` 后半句的规则、只留事实，worker 行为是否不变 | 一张真实票，前后各跑一次 |
| T7 | 现有测试是否钉住 `verify-ticket.py` `RESUME:` 的步骤编号与 `implement` 收尾步骤的对应 | 读 `tests/verify-ticket/test_preflight.py`（本轮未读） |
| T8 | mode 写成后的篇幅与 worker 的注意力 | 行数、词数；一张真实票的前后对比 |
| T9 | 五个宿主是否扫描仓库本地技能目录 | 在消费仓库放一个本地技能，各宿主新会话看是否列出 |
| T10 | 可触发的 `mmw` description 与 `grilling`、`wayfinder`、`to-spec`、`dispatch` 的触发是否抢同一请求 | 按 `SKILL-SET-RULES.md` `### Descriptions` 第 2 条并排读，再用 T1 的会话验证 |

**需要 owner 决定（产品、范围或 owner 自己的文字）：**

| 编号 | 决定 | 建议 |
|---|---|---|
| U1 | `shared.md` 加一行提醒（它是 owner 以第一人称写的全局提示，所有会话常驻） | 加；文字见 3.3 |
| U2 | 采用忠实方案还是 N10 的模型 D（脚本会话不经过 mode） | 忠实方案；D 作为降级 |
| U3 | 是否还想在 MMW 之外使用上游原版 `code-review`（对任意分支或 PR 评审）、上游原版 `implement` | 现在不装；若要，需给 MMW 的评审技能改名，这是范围决定 |
| U4 | 「为让 mode 够得到而翻转上游 frontmatter」是否算 `fe94802d`「不改上游 frontmatter」的允许例外 | 算；今天已经翻转了六个，新方案减到四个 |
| U5 | 是否要把 pstack 的 Bug fix、Feature、Refactoring 类 playbook 引入 MMW，引入后对应 Small change 还是 Build | 暂不引入；先定对应关系 |

**未能核实的事实：**

- `install.sh` 头注释「每个 host 都读 `SKILL.md` 的 `disable-model-invocation`」：只在 Claude Code 上核实到它的效果（技能从模型列表消失）；Codex 按上游文档读 `openai.yaml`，未实测（N10 §11）。
- pstack `principle-separate-before-serializing-shared-state`、`principle-make-operations-idempotent` 的原文本轮未读，6.3 里「可直接导入」是推断。
- `design-pages/references/pull.md` `## A contract child answered by this pull` 的最终归属（`night.md` 的规则簇还是 `idea-to-tickets.md` 的入口）要看谁在什么会话里执行它，下一轮定。
- 历史票（消费仓库里已发布的票）是否在正文里点名 `implement` 的小节：只查了模板，没查历史票。
