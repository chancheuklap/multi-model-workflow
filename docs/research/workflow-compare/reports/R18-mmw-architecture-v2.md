# R18 MMW 升级后的架构（定稿）

本文是 MMW（`mmw-v2/`）这次架构升级的定稿。它以 R15（同构派）为底稿，并入 R16（导入优先）与 R17（夜间彻底派）各自最好的部分，处理了两轮评审：第一轮的结果在第 14 节，第二轮（41 条）逐条写在文末「审查记录」。凡评审指出的问题，都回原文或源码核实过。

**材料。**

- 准绳：`docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）。
- 底稿：`R13-pstack-design-essence.md`（精髓 E1–E12、接口 I-1–I-16）、`R14-mmw-layer-mixing-inventory.md`（任务顺序 T1–T38、原则候选 PC1–PC29、天然整体 W1–W7）。
- 三份设计：`R15-mmw-v2-isomorphic.md`、`R16-mmw-v2-import-first.md`、`R17-mmw-v2-night-thorough.md`。
- R4 V1–V17、R12 M1–M30 里「已核实」的事实直接引用编号，它们的结论不用；`N11-mmw-gaps.json` 列出的错误不用。
- pstack 快照在 `docs/research/code-landing-refs/pstack/`（`.cursor-plugin/plugin.json` `"version": "0.15.4"`）。下文以 `skills/`、`poteto-mode/`、`agents/`、`automations/` 开头的 pstack 路径都相对这个目录；MMW 路径不带前缀时相对 `mmw-v2/`。

**标注。** 「原文」＝文件里写着的；「已核实」＝本轮回到原文或跑命令看到的；「推断」＝由原文推出、原文没直接写的；需要实测的写进第 11 节，并写明怎么测。「新写」＝没有现成来源、由本文作为工程决定写下的文字，每处都注明依据并记入 ADR 0032。

**术语。** 本文把 `scripts/` 下的程序叫「脚本」，mode 目录下的叫「mode 的脚本」。不用 pstack 的 lever 一词指代脚本：L7 `### A.6 脚本` 首条说明 lever 在 pstack 里还包括「a skill your subagents follow」。

**硬约束**（任务给定，只有这些算约束）：

- **H1** 宿主不换（Claude Code、Codex、Grok、Pi、Cursor；runner 用 Orca、Paseo、herdr）；这些宿主没有 Cursor 的 `mode: true` / `reminder` 常驻机制。
- **H2** Claude Code 上，带 `disable-model-invocation: true` 的技能不在模型的技能列表里，模型按名也调不到（R4 V1）；description 在宿主启动时扫入，改动要新会话才生效。
- **H3** 会话内派出的子代理跑在本会话宿主的模型上；跨厂商只能另起会话（`docs/adr/0015-no-custom-subagents.md` `## Consequences`）。
- **H4** runner 把送进会话的文字当键盘输入，换行即提交，所以脚本送进会话的一条消息必须是一行（`skills/dispatch/scripts/watchdog.py` 第 813 行注释，R12 M1）。
- **H5** Self-hosting boundary（根 `AGENTS.md` `## Self-hosting boundary`）：一次 watch 期间冻结已安装版本；运行中的流程不读工作树里正在被改的版本。
- **H6** 夜里的会话屏幕前没人，不能向人提问。

另有一条任务给定的边界，记作 **S**：`mmw-v2/prompt/shared.md` 是用户的全局规则，对所有项目生效，MMW 不改写它。

**判据**（任务给定）：每段内容默认搬到它按类型该在的层；留在原处必须写明是 H1–H6 或 S 中的哪一条。第 9 节的「留（H#）」汇总是全部例外。这条判据同时写进 ADR 0032 与每张批次票的验收条件（第 10 节）。

---

## 0. 结论（先读这里）

### 0.1 升级后 MMW 长什么样

今天的 MMW 只有一种组件：技能。35 个技能里同时装着「一件事怎么做」「先做什么后做什么」「我被谁调用、下一步交给谁」「跨任务的判断」「流水线的状态」五类内容。升级后分成七种组件，各有自己的目录：

| 组件 | 回答什么问题 | 放在哪里 | 第 2 批后 | 全部批次后 |
|---|---|---|---|---|
| mode | 遇到什么情况用什么；任务走哪份 playbook；无人时能自己定什么；被唤醒后怎么接上 | `mmw-v2/skills/mmw/SKILL.md`，模型可调用的技能 | 1 | 1 |
| playbook | 一类任务从头到尾的步骤、谁拥有什么、交出什么 | `mmw/playbooks/`；仓库私有的在 `<仓库>/.mmw/playbooks/` | 18 份（MMW 16、pstack 2）＋本仓库私有 3 份 | 32 份（pstack 再进 14 份） |
| 原则 | 跨任务、能改变一个具体决定的判断 | `mmw/principles/` | 26 条（MMW 12、pstack 14） | 35 条（pstack 23 条全部） |
| 能力技能 | 一件事怎么做、交回什么；不知道是谁调用它 | `mmw-v2/skills/<name>/` 与三个上游子树 | 35 个 | 52 个（pstack 再进 17 个） |
| reference | 只在某一步才读的材料、交给子代理或另起会话的简报 | 所属技能的 `references/`；mode 自己的在 `mmw/references/`，外来的在 `mmw/references/ps/` | 位置重排 | 同左 |
| 脚本 | 每次结果都一样的状态读写、投递、检查 | 流水线的在 `mmw/scripts/`（外来的在 `mmw/scripts/ps/`）；能力自己的在能力目录 | 16 个文件进 `mmw/scripts/` | 同左加 pstack 的 `watch-pr/`、`worktree-audit.sh` |
| 角色与配置 | 哪个角色读哪份 playbook、用哪个模型、被什么事件叫醒到哪一步 | `mmw/roles.json` 与 `~/.mmw/models.json` | 6 个角色 | 同左；面板角色进 `models.json` |

### 0.2 与现在最大的不同

1. **「先后顺序」和「谁调用我」全部离开能力技能。** 今天能力技能结尾有 17 句「下一步用 X」（R14 第 2 节名单），任务顺序散在 38 处（R14 T1–T38）。升级后这些句子进 playbook；能力技能以「交回什么」结尾。连线检查（第 7.5 节 `check_wiring.py`）保证它们不回流。
2. **流水线的状态从能力技能里拿出来。**
   - `dispatch` 解散：路由进 mode；夜间、单票、接手一张票三份流程成为 playbook；改模型成为能力技能 `setup-mmw`；脚本整目录搬进 `mmw/scripts/`。
   - `verify-ticket` 拆开：事件词表（`events.py`）与写票状态的命令（认领、记录判据运行、决定、评审、`touched`、草稿、closeout、切子票）成为 mode 的脚本 `mmw/scripts/ticket.py`；`verify-ticket` 只留「跑一张票的判据、lint 票面、发布 spec 与票」。今天 mode 一侧的 `status.py`、`relay.py` 反过来按路径加载能力技能里的 `events.py`（`status.py` 第 40 行、`relay.py` 第 258 行，已核实），这个方向随之理顺。
   - `implement` 的 101 行拆开：worker 的流程进 `work-a-ticket.md`，通用写码规则进 mode 的 reference，Memory 的做法成为能力技能 `shared-experience`；`implement` 回到上游 15 行原文，不再安装。
   - `code-review` 回到上游 87 行的通用评审，任何分支都能用；票的评审流程成为 `review-a-ticket.md`。
3. **想知道「做一件事要走哪些步」，只读一个文件。** 例：做一张票读 `mmw/playbooks/work-a-ticket.md`，11 步从认领到关票；今天要在 `implement`、`verify-ticket`、`dispatch`、`code-review`、`ui-acceptance` 五个技能之间跳。
4. **跨任务的判断有了自己的层。** 今天 29 条这样的规则平均每条散在 6 处以上、措辞不一（R14 第 0 节第 2 条）；升级后是 `principles/` 一个目录，调用方只写名字加一句本地限定。
5. **pstack 的全部组件都判定了去处**（第 13 节全量清单，102 项）：导入 17 个能力技能、23 条原则、17 份 playbook 文件（`bug-fix` 以合并方式进入），另 2 份同名 playbook（`authoring-a-skill`、`prototype`）保留 MMW 版并吸收原文段落；导入 14 条 mode 触发行原文、mode 的 `## Comments` 一节、1 份 mode reference、2 组 mode 脚本、1 份 agent 简报；不导入的 16 项各写了理由。导入的实际改动按八种类型计（第 8.2 节）：
   - 一份 playbook 或原则：复制一个文件，mode 加一行，`imports.tsv` 加一行；原则另有「删开关行、改相对链接」两种机械改写。
   - 一个能力技能：`skills.txt` 加一行 `ps/<name>`；若它被 mode 或 playbook 点名，再在 `skills.txt` 该行加 `+model`，由 `install.sh` 在安装副本里去掉开关并生成 `agents/openai.yaml`（子树原文不动，第 4.3 节）；它点名的 mode 触发行按 mode-trigger 类型原文复制；它引用的 Cursor 专有名字在 `slots.md` 有一行。
   - 需要人判断的改动都单独计数，全部批次共 10 处（第 13.2 节），不再写「0 处」。
6. **夜里更稳。** 今天已核实的四处断点在 B0 修掉：worker 读不到唤醒后的第 1 步（N10 B9）；`MMW turn guard:` 找不到处理行（R4 V7）；八种 watchdog 告警只有一种有处理行（R12 M16）；`night.md` `### Exit codes of resume` 是空节（R4 V8；本轮读原文，第 102–104 行只有一段话，没有退出码）。另修两处本轮核实的静默失效：hook 找不到同伴模块时退出 1、在 Claude Code 上等于不拦（第 7.3 节）；`verify-ticket.py` 找不到 `dispatch.sh` 时静默少写两个字段（第 7.6 节）。

### 0.3 要做多少事

分六批（第 10 节），每批作为本仓库的票，由当时已安装的冻结版本跑（H5），每批完成后流水线照常能跑：

| 批 | 做什么 | 你要做的 |
|---|---|---|
| B0 地基 | hook 经固定位置的启动器调用；锚点表、角色表、连线检查（按类别分批转为失败）；`dispatch.sh where`；四处断点；探针实测 | 授权跑一次 `install.sh` |
| B1 mode 与白天 | mode、26 条原则、白天 11 份 playbook、pstack 子树与 2 份 pstack playbook；白天技能回原文；`retro` 的新去处与四条分拣规则 | 授权 `install.sh`；开新会话 |
| B2 夜间 | 夜间 5 份 playbook；`dispatch` 解散、脚本整目录搬进 `mmw/scripts/`；`verify-ticket` 拆出 `ticket.py`；`implement`、`code-review` 回原文 | 在没有夜在跑时授权 `install.sh`；开新会话；挑一个小 spec 跑一夜验收 |
| B3 pstack 核心 | 15 个能力技能、9 条原则、`dispatch.sh panel`、`figure-it-out` 接住「没有匹配」、6 份开发类 playbook 与 `bug-fix` 合并、11 条触发行、`## Comments` | 授权 `install.sh`；开新会话 |
| B4 PR 交付组 | `opening-a-pr`、`babysit`、`shipping`、`worktree-cleanup`；`bugbot-triage.md`；`watch-pr`（引入 bun） | 授权 `install.sh`；装 bun；说出哪些仓库用 PR 交付 |
| B5 诊断与验证组 | `runtime-forensics`、`trace-forensics`、`hillclimb`、`visual-parity`；`create-verification-skill`、`maintain-verification-skill` | 授权 `install.sh`；开新会话 |

量级（推断，落地后用 `wc -l` 实测）：新写的文件约 60 个，多数是把现有段落搬过去；改动约 80 个现有文件；随改的测试文件 14 个以上，分在 `board`、`dispatch`、`liveness`、`relay`、`verify-ticket`、`migrations` 六个套件（第 7.6 节，本轮 grep）。

### 0.4 风险在哪

- **B2 面最大。** 它同时改启动提示词、唤醒文字、hook、票状态脚本四个边界，拆开会有读者走到错的一步（R14 W1–W3）。缓解：B0 先让新旧两套定位并行；B2 发布前跑六个完整套件与新 `tests/mmw`，再在隔离环境里用假 tracker 跑一整夜；回退是把已安装 checkout 移回上一个提交并重跑 `install.sh`。
- **搬脚本的路径耦合。** 本轮 grep 到的全部调用点列在第 7.6 节；做法是整目录平移（`mmw/scripts/` 内部相对路径全部不变），外部调用点改从 `anchors.py` 取；连线检查第 10 类覆盖 Python 与 shell 两种写法，B0 起就让「指向不存在的目录」失败。
- **mode 在某些宿主上可能没被读到。** 脚本起的会话由启动提示词点名 mode，这条路径确定；人起的会话靠 description 与 hook，各宿主能否注入一行要实测（U-2）。有备用路径，结构不因实测结果缩小。
- **上游 `code-review` 回原文后，它的 description 可能与 reviewer 的 playbook 抢触发**（U-11），B2 验收夜会看到。

### 0.5 需要你决定的事

只有这些改变你看到的东西、改你的其他仓库、或不可撤销：

1. 是否往你各个消费仓库的 `AGENTS.md` 加一行「This repository uses MMW: the `mmw` skill」。它是人起的会话找到 mode 的备用路径，改的是你其他仓库的指令文件。
2. B2 的提升时机，以及用哪个小 spec 跑验收夜。
3. Cursor 收不到 `shared.md`（根 `AGENTS.md` `## Key Conventions`）。Cursor 应用里的用户规则是否补上同样内容。
4. 你的哪些消费仓库用 PR 收改动（`.mmw/target.json` 的 `delivery: pr`）。这决定 B4 的四份 playbook 在哪些仓库出现在路由表里；B4 本身照做。

我已自行做出的工程决定（理由与放弃的备选见各节）：

- `dispatch` 解散，脚本整目录搬进 `mmw/scripts/`，hook 与 `statedir.py`、`watchdog.py` 同层（第 1、7 节）。
- `verify-ticket` 拆出 mode 的脚本 `ticket.py` 与 `events.py`（第 4.1 节）。
- `implement` 回原文后不再安装；`exe-release` 保持完整的能力技能，路由表直接指向它，不设出包 playbook（第 3、4 节）。
- 调用开关不在上游子树里改：`install.sh` 按 `skills.txt` 的 `+model` 标记在安装副本里去掉（第 4.3 节）。
- 引入 bun，只供 `mmw/scripts/ps/` 下 pstack 的 TypeScript 脚本使用，写进根 `AGENTS.md` `## Package Manager`。理由：`watch-pr` 是多份 169–832 行的 TypeScript 文件，带 bun 测试（L7 A.6）；改写成 node 等于分叉一份会漂移的副本并丢掉测试。放弃的备选：node 重写；不导入 PR 组。
- `dispatch.sh check` 在 `install.sh --check` 失败时自动跑完整安装的行为改成只报告，让代码服从你已写下的规则「`install.sh` runs only when the user explicitly authorises it」（根 `AGENTS.md` `## Gotchas`；R12 M7）。代价：开夜时若安装不齐，要你授权后再开。
- hook 启动器找不到目标时按 hook 分别处理：`mode-hook`、`turn-guard` 放行；`tool-guard` 只对 `issue-<n>` 目录里的会话拒绝（第 7.3 节）。
- 优先级句（mode `## Autonomy` 第一条）是新写的，依据 L7 C.2「归置 MMW 时要显式写出优先级」，记入 ADR 0032。

---

## 0A. 改造前后一图看懂

### 0A.1 目录树对照

左边是现状，右边是第 2 批完成后。只列有变化的部分。

```
NOW  mmw-v2/                                   UPGRADED  mmw-v2/
skills/                                        skills/
├── dispatch/          (6 moments, 1 skill)    ├── mmw/                             MODE (new)
│   ├── SKILL.md                               │   ├── SKILL.md                     triggers / principles / autonomy / re-entry / playbooks
│   ├── hosts.json                             │   ├── roles.json                   role -> playbook -> models row -> wake steps
│   ├── references/                            │   ├── hosts.json                   <- dispatch/
│   │   ├── night.md        (orchestrator)     │   ├── imports.tsv                  every file brought in from pstack
│   │   ├── one-ticket.md   (orchestrator)     │   ├── playbooks/                   18 PLAYBOOKS
│   │   ├── inside-a-ticket.md (worker)        │   │   define-a-change  map-a-large-effort  design-an-interface
│   │   └── editing-models.md                  │   │   prototype  direct-change  bug-fix  triage-an-issue
│   └── scripts/  (12 files)                   │   │   research-a-question  onboard-a-repository  deliver-a-change
├── verify-ticket/                             │   │   authoring-a-skill  run-a-night  accept-the-night
│   ├── SKILL.md   (routes the worker)         │   │   run-one-ticket  work-a-ticket  review-a-ticket
│   └── scripts/verify-ticket.py (4253 lines:  │   │   session-pickup (pstack)  pause-safely (pstack)
│        criteria + claim + closeout + events) │   ├── principles/                  26 PRINCIPLES (12 MMW + 14 pstack)
│       events.py (dispatch+watchdog events)   │   ├── references/                  slots, subagent-brief, orchestrator-events,
├── ui-acceptance/ design-pages/               │   │                                writing-code, skill-set-rules, reviewing-a-skill-set,
├── write-screen-contract/ retro/ advisor/     │   │                                interface-and-remake, pipeline-issues,
├── exe-release/ code-checkers/                │   │                                tracker-additions, review-axes/{4 axes}, ps/
├── manage-agents-md/                          │   └── scripts/                     MODE SCRIPTS (flat; moved whole)
upstream/skills/engineering/                   │       dispatch.sh relay.py watchdog.py status.py statedir.py
├── implement/   (101 lines: worker flow)      │       ghlist.py models.py tool-guard.py turn-guard.py runners/
├── code-review/ (ticket review only)          │       events.py (<- verify-ticket)  ticket.py (split from verify-ticket.py)
├── to-spec/ to-tickets/ (MMW text inside)     │       anchors.py  mode-hook.py (new)   ps/ (pstack scripts, B4)
├── triage/ wayfinder/ prototype/ grilling/    ├── setup-mmw/                       CAPABILITY (new: models, runner, board)
│   ... (+1612/-358 lines of MMW edits)        ├── shared-experience/               CAPABILITY (new: Memory)
└── ask-matt/  (not installed, edited)         ├── to-spec/  to-tickets/            CAPABILITY (forked out of upstream/)
                                               ├── verify-ticket/                   criteria runner, lint, publish only
                                               ├── ui-acceptance/ (+writing-interface-code.md)
                                               ├── design-pages/  (+state-list-format.md)
                                               ├── write-screen-contract/ retro/ advisor/ exe-release/ ...
                                               upstream/skills/   back to upstream text (2 kinds of edits only)
(no playbooks, no principles, no mode)         upstream-pstack/                     new subtree (pstack source, untouched)
                                               mmw-hook.py                          new: fixed hook launcher
                                               import/import_component.py           new: brings pstack files in
                                               tests/lib/check_wiring.py            new: wiring lint
```

仓库根新增：`.mmw/playbooks/`（本仓库私有 playbook 3 份与索引）、`docs/adr/0032`–`0034`、`docs/skill-set.md`（一行指针）。`~/.mmw/` 新增 `bin/mmw-hook`、`skills/`（带 `+model` 标记的上游技能的安装副本）、`state/<repo>/prompts/`。

### 0A.2 按组件类型的数量对照

| 类型 | 现状 | B2 后 | 全部批次后 | 来源 |
|---|---|---|---|---|
| mode | 0 | 1 | 1 | 第 2 节 |
| playbook | 0 份正式的；约 6 份流程文件挂在技能名下（`implement` 正文、`code-review/references/session.md`、`dispatch/references/night.md`、`one-ticket.md`、`inside-a-ticket.md`、`triage/references/pipeline-issues.md`） | 18＋私有 3 | 32＋私有 3 | 第 3、13 节 |
| 能力技能 | 35 个技能，全部混装（已核实：`skills.txt` 35 行：mattpocock 24、本仓 10、diagram-design 1） | 35（MMW 自有 13、mattpocock 21、diagram-design 1）＋ mode | 52（加 pstack 17） | 第 4 节 |
| 原则 | 0；29 条规则散在各处（R14 PC1–PC29） | 26 | 35 | 第 5 节 |
| reference | 124 份 `.md`（其中 diagram-design 56 份） | 约 124，mode 自有 13 份 | 加导入技能的 reference 与 `ps/bugbot-triage.md` | 推断，落地后实测 |
| 脚本 | 45 个文件分布在 10 个技能里，其中 `dispatch` 12 个 | `mmw/scripts/` 16 个（dispatch 的 12 个、`events.py`、新 `ticket.py`、`anchors.py`、`mode-hook.py`）；仓库工具新增 `mmw-hook.py`、`import_component.py`、`check_wiring.py` | 加 `ps/watch-pr/`、`ps/worktree-audit.sh` | 第 7 节 |
| 角色定义 | 散在 `dispatch.sh` 提示词、`relay.py` `WAKES`、`dispatch/SKILL.md` 的表 | `mmw/roles.json` 一处，6 个角色 | 同左 | 第 7.1 节 |

---
## 1. 目标目录树与命名规则

**采用的决定。** 以 R15 的布局为底：`mmw-v2/skills/mmw/` 照 pstack `poteto-mode/` 的布局放 `SKILL.md`、`playbooks/`、`principles/`、`references/`、`scripts/`；`dispatch/scripts/` 整目录平移到 `mmw/scripts/`，hook 与其他脚本平放；`verify-ticket` 的状态部分进 `mmw/scripts/`；`dispatch` 解散。加入 R17 的 `roles.json` 与 `imports.tsv`，R16 的 `shared-experience` 与 `deliver-a-change`。新增 hook 启动器 `mmw-hook.py`。

**理由。** 用户要求目录结构、组件类型、每类内容的归属都看得出变化。pstack 的脚本放在 mode 下（`skills/poteto-mode/scripts/`，L7 A.6）；MMW 的 relay、watchdog、hook、事件词表只服务流水线，按类型属于 mode 的脚本。整目录平移让 `models.py` ↔ `runners/*.sh` ↔ `statedir.py`、`turn-guard.py` ↔ `watchdog.py` 这些双向的同目录相对路径全部不变（本轮核实：`runners/orca.sh` 第 313 行、`paseo.sh` 第 111 行、`herdr.sh` 第 124 行都用 `$(dirname "$HERE")/models.py`；`models.py` 第 23–30 行按同目录 `import statedir`、`RUNNERS_DIR = SKILL_DIR / "scripts" / "runners"`；`turn-guard.py` 第 135–139、224、231 行按 `HERE` 找 `statedir`、`watchdog.py`、`runners`；`tool-guard.py` 第 57–58 行 `_HERE.parents[1] / "ui-acceptance"` 在平放时仍解析到 `skills/ui-acceptance`）。

**放弃的备选。**
- R17：脚本留在 `dispatch` 能力技能里。它的理由「被多个 playbook 或用户直接调用」只对任务板和改模型成立；它也让 `roles.json` 变成能力脚本向上读 mode 的数据。
- 上一版本文：`models.py`、`hosts.json` 搬进 `setup-mmw/scripts/`、hook 搬进 `mmw/scripts/hooks/`。两者都会切断上面列的同目录相对路径：前者让 B2 之后每次起 worker、reviewer、advisor 都失败，后者让两个 hook 导入失败后在 Claude Code 上静默放行（第 7.3 节）。

### 1.1 `mmw-v2/`（到文件一级）

```
mmw-v2/
├── skills.txt                    self/mmw、self/setup-mmw、self/shared-experience、self/to-spec、self/to-tickets 新增；
│                                 self/dispatch、engineering/implement、engineering/to-spec、engineering/to-tickets 删除；
│                                 行尾可带 +model（第 4.3 节）；B3 起新增 ps/<name>
├── install.sh                    hook 经 ~/.mmw/bin/mmw-hook 登记；认 ps/ 前缀与 +model；--check 核对连线、开着的 watch、bun
├── mmw-hook.py                   新：hook 启动器源文件，install.sh 复制为 ~/.mmw/bin/mmw-hook（第 7.3 节）
├── import/
│   ├── import_component.py       新：按八种类型把 pstack 文件放进 mmw/，只做机械改写（第 8.5 节）
│   └── pstack.map                新：机械改写表
├── skills/
│   ├── mmw/                      ── mode（模型可调用，H2）
│   │   ├── SKILL.md              ## Non-negotiables / Principles / Autonomy / Re-entry / Subagents /
│   │   │                         Writing the reply / Playbooks；B3 起加 ## Comments（第 2 节）
│   │   ├── roles.json            角色 → playbook → models.json 行 → 启动命令 →（事件 → 唤醒步骤）
│   │   ├── hosts.json            ← dispatch/hosts.json（models.py 按 SKILL_DIR 找它，位置关系不变）
│   │   ├── imports.tsv           每个外来文件：类型、本地路径、来源路径、来源提交、机械改写、判断改动、批次
│   │   ├── playbooks/            18 份（第 3 节）
│   │   ├── principles/           principle-<slug>.md，26 份（第 5 节）
│   │   ├── references/
│   │   │   ├── slots.md                  槽位、别名与宿主工具映射（第 8.3 节）
│   │   │   ├── subagent-brief.md         派子代理的简报模板
│   │   │   ├── orchestrator-events.md    run-a-night 与 run-one-ticket 共用的唤醒表
│   │   │   ├── writing-code.md           direct-change 与 work-a-ticket 共用的写码规则
│   │   │   ├── skill-set-rules.md        ← writing-for-agents/SKILL-SET-RULES.md（随安装走）
│   │   │   ├── reviewing-a-skill-set.md  ← writing-for-agents/REVIEWING-A-SKILL-SET.md
│   │   │   ├── interface-and-remake.md   ← wayfinder/references/
│   │   │   ├── pipeline-issues.md        ← triage/references/
│   │   │   ├── tracker-additions.md      ← setup-matt-pocock-skills 里 MMW 加的流水线段落
│   │   │   ├── review-axes/{standards,spec,tests,ui}.md   ← code-review/references/ 四个 axis 文件
│   │   │   └── ps/                       导入的 mode 级 reference 与 agent 简报（B3、B4）
│   │   └── scripts/              ── mode 的脚本（只被 playbook 步骤、mode 触发行、hook 调用）
│   │       ├── dispatch.sh relay.py watchdog.py status.py statedir.py ghlist.py models.py
│   │       ├── tool-guard.py turn-guard.py runners/{orca,paseo,herdr}.sh   ← dispatch/scripts/ 整目录
│   │       ├── events.py                                                  ← verify-ticket/scripts/
│   │       ├── ticket.py                                                  ← 从 verify-ticket.py 拆出（第 4.1 节）
│   │       ├── mode-hook.py anchors.py                                    新（第 7.2、7.4 节）
│   │       └── ps/                                                        导入的 pstack 脚本（B4）
│   ├── setup-mmw/                能力：改 host、model、effort、runner；查一个角色的值；开任务板；按命令点名 mmw/scripts/models.py
│   ├── shared-experience/        能力：Memory 记录的打开、搜索、保存、更正、关闭决定
│   │   ├── SKILL.md              ← implement ## Shared experience while implementing 的方法部分、night.md ## 4 Memory 决定的写法
│   │   └── references/saving-memory.md   ← implement/references/
│   ├── to-spec/  to-tickets/     能力：从上游目录分出的 MMW 自有文本
│   ├── verify-ticket/            能力：跑判据（CHECK/EXPECT、gate-check）、lint 票面、发布 spec 与票；issue_tree.py
│   ├── ui-acceptance/            能力 + references/writing-interface-code.md（← implement）
│   ├── design-pages/             能力 + references/state-list-format.md（← prototype UI.md 第 6 步）
│   └── write-screen-contract/ retro/ advisor/ exe-release/ code-checkers/ manage-agents-md/
├── upstream/                     mattpocock squash subtree：只允许两类改动（第 4.3 节）
├── upstream-diagram-design/  upstream-unlazy/   不变
├── upstream-pstack/              新：pstack 的 squash subtree，原文不改（第 8.1 节）
├── merge-notes/                  新增 pstack.md；回原文的技能删掉对应条目
├── downstream-notes/             新增一份：启动提示词、技能名、脚本路径的变化对消费仓库的影响
├── prompt/                       不改（S）
├── board/                        四个文件的路径改从 anchors.py 取（第 7.6 节）
├── migrations/remove-verifier.py 第 16 行 DISPATCH_SCRIPTS 改到 mmw/scripts
└── tests/
    ├── lib/check_wiring.py       新：连线检查，每个套件先跑（第 7.5 节）
    ├── lib/check_own_skill_frontmatter.py   认 ps/ 前缀与 +model 标记
    ├── mmw/                      新套件：roles.json、anchors.py、where、ticket.py、mode-hook、mmw-hook、import_component
    ├── wiring/                   每类连线检查一个必须失败的反例
    └── 其余套件                  board、dispatch、liveness、relay、verify-ticket、migrations 的路径与断言随改
```

仓库根：

```
<本仓库根>/
├── AGENTS.md                     发布四步移到私有 playbook，这里留一行指针与 H5 那一句；
│                                 <important if … upstream …> 改成指向私有 playbook Pull an upstream；
│                                 ## Package Manager 加 bun 一行
├── .mmw/target.json              delivery: playbook:promote-a-change
├── .mmw/playbooks/
│   ├── INDEX.md                  一行一份，格式同 mode 路由表
│   ├── promote-a-change.md       ← 根 AGENTS.md ## Gotchas 第 1 条的四步
│   ├── pull-an-upstream.md       ← 根 AGENTS.md <important if … upstream …>、merge-notes/README.md
│   └── import-a-component.md     第 8.6 节
├── docs/skill-set.md             一行指针：技能集规则在 mmw 技能的 references/skill-set-rules.md
├── docs/adr/0032-the-set-is-layered.md、0033-wakes-carry-a-step-pointer.md、0034-pstack-enters-as-a-subtree.md
└── docs/contexts/toolbox/CONTEXT.md、night/CONTEXT.md   新词条：mode、playbook、principle、role、slot、step pointer、where line
```

### 1.2 消费仓库与 `~/.mmw/`

```
<消费仓库>/
├── AGENTS.md                     ## External References 里的 mmw 一行（待你决定，第 0.5 节第 1 条）
├── docs/agents/{issue-tracker,triage-labels,domain}.md   配置，onboard-a-repository 写入
├── .mmw/target.json              新增可选键 delivery（commit | pr | playbook:<slug>，缺省 commit）与 control（界面 → 技能）
├── .mmw/harness/ journeys/ stories/                     不变
├── .mmw/playbooks/               可选：该仓库私有 playbook，只在人在场的会话里读（H5：夜间角色不读）
├── docs/specs/<effort>/screen-contract.yaml  prototypes/<effort>/   不变
└── .worktrees/issue-<n>、merge-<branch>                  名字归流水线

~/.mmw/
├── installed-root                已安装 checkout 的路径（H5 的冻结点）
├── models.json                   角色 → host、model、effort；runner；B3 起加面板角色（值为列表）
├── boards.json
├── bin/mmw-hook                  新：hook 启动器（install.sh 复制，不是软链）
├── skills/<name>/                新：带 +model 标记的上游技能的安装副本（第 4.3 节）
└── state/<owner>__<name>/        watches.json（新增 kind 字段）、relay.lock、watchdog.lock；新增 prompts/、panels/
```

### 1.3 命名规则

| 组件 | 位置 | 命名 | 由什么核对 |
|---|---|---|---|
| mode | `skills/mmw/SKILL.md` | 技能名 `mmw`，全套只有这一个 mode | `check_own_skill_frontmatter.py` |
| playbook | `skills/mmw/playbooks/<slug>.md`；私有的在 `<仓库>/.mmw/playbooks/` | slug 小写连字符；与 pstack 同一任务类型时用 pstack 的文件名（`bug-fix`、`prototype`、`session-pickup`、`pause-safely`、`authoring-a-skill`），以后导入同名文件是合并，不是并存；首行 `### <Name>`，没有 frontmatter（L7 A.2） | 第 1、7 类 |
| 步骤 | MMW 自写 playbook 的编号步骤 `N. **<Title>.** …` | 标题就是锚点；跨文件只按标题引用 | 第 4 类 |
| 步骤指针 | 脚本文字、唤醒、启动提示词 | `mmw <slug>#<Step title>`，或 `mmw#<mode 小节名>`；只指向 MMW 自写的 playbook 与 mode | 第 1 类 |
| 原则 | `skills/mmw/principles/principle-<slug>.md` | 文件名等于 frontmatter 的 `name`；MMW 自有与 pstack 共用一个命名空间，同名时导入脚本拒绝 | 第 5 类 |
| 原则引用 | 任何文本 | MMW 自写的文字只用 `**principle-<slug>**`；导入的文字保留 pstack 的五种写法，由 mode 的解析规则接受 | 第 5 类 |
| mode 的 reference | `skills/mmw/references/`；外来的在 `references/ps/` | 被两份以上 playbook 共用、是子代理或另起会话的简报、是槽位表，或随安装分发给所有仓库的规则 | 第 2 类 |
| mode 的脚本 | `skills/mmw/scripts/`；外来的在 `scripts/ps/` | 平放，不分子目录（外来的除外） | 第 10 类 |
| 能力技能 | `skills/<name>/` 或 `upstream*/…/<name>/` | 新拆的取源文字里已有的名字（`shared-experience` 取自 `implement` `## Shared experience while implementing` 与 `dispatch.sh` 第 1729 行「Shared experience for ticket」；`setup-mmw` 对应 pstack `setup-pstack`） | `install.sh` 查重（第 163–164 行） |
| 角色 | `skills/mmw/roles.json` 的键 | `worker`、`self-picked-worker`、`reviewer`、`night-orchestrator`、`ticket-orchestrator`、`advisor` | 第 6 类 |
| 外来能力技能 | `upstream-pstack/skills/<name>/` | `skills.txt` 前缀 `ps/`；与已装技能重名时不导入 | `install.sh` 查重 |

### 1.4 角色的物理位置

| 角色 | 操作文件 | 模型绑定 | 启动方式 | 常驻纪律从哪来 |
|---|---|---|---|---|
| worker | `playbooks/work-a-ticket.md` | `models.json` 的 `junior-worker` / `senior-worker` | `dispatch.sh start <n> worker` | 启动提示词点名 mode |
| self-picked-worker | `playbooks/work-a-ticket.md` 的入口 **Picked up yourself** | 人起的会话 | `dispatch.sh adopt <n>` | 人起会话的四条到达路径 |
| reviewer | `playbooks/review-a-ticket.md` | `reviewer` | `dispatch.sh start <n> reviewer` | 启动提示词点名 mode |
| 评审 axis | `references/review-axes/<axis>.md`（自足的子代理简报） | 会话内，跑在 reviewer 的模型上（H3） | reviewer 派通用子代理 | 只读，不读 mode（第 3.3 节 P16） |
| 夜的 orchestrator | `playbooks/run-a-night.md` | 人起的会话 | 用户说「今晚跑 spec #N」 | mode description、hook；`open` 打印的指针 |
| 单票 orchestrator | `playbooks/run-one-ticket.md` | 人起的会话 | 用户要在夜外跑一张票 | 同上 |
| advisor | 能力技能 `advisor` 的 `references/advising.md`（例外，见下） | `advisor` | `dispatch.sh advise <file>` | 启动提示词点名 mode `## Autonomy` |

**advisor 的例外。** advisor 的操作文件留在能力技能的 reference 里，不写成 playbook。依据两条：L7 A.5 表第一行（原样交给另一个代理的简报放 reference，即使每次都用）；L7 C.6 信号 5（只调用一个技能、没有自己编排的 playbook 是形式拆散）。被咨询一方只做一件事：按 `advising.md` 回答一个决定，没有第二个组件可编排。第 12 节据此把「角色流程留在能力技能里」写成 1 个例外，不写 0。

---

## 2. mode：`mmw`

**采用的决定。** 一个模型可调用的技能 `mmw`，章节照 pstack mode，只放 MMW 独有的内容与导入的 pstack 触发行；四条到达路径叠加；启动提示词在所有 runner 上都是一行。

**理由。** H1 下没有 `mode: true`；H2 下带开关的 mode 按名调不到，脚本起的会话就无法「Use the mmw skill」。pstack `agents/poteto-agent.md` 的 description 写「Reads the `poteto-mode` skill's `SKILL.md` in full before any work」，执行者也在 mode 的纪律下工作。

**放弃的备选。** R16 的 `## Host tools` 整张表放进 mode 正文：它只在一步点名 Cursor 工具或槽位时才需要，按 L7 A.5 放 `references/slots.md`，mode 只留别名与一行触发。

### 2.1 frontmatter

```
---
name: mmw
description: How work runs in a repository that uses the MMW landing pipeline: routes a task to its playbook, indexes the principles, and says what an unattended session may decide. Use in a repository that has a `.mmw/` directory or a `docs/agents/issue-tracker.md`, when a prompt names the mmw skill, or when a message carries an `mmw <playbook>#<step>` pointer.
---
```

不带 `disable-model-invocation`（H2）；description 不写宿主名与 runner 名（`references/skill-set-rules.md` `### Descriptions`）；Codex 侧的 `agents/openai.yaml` 不写 `policy` 行。

### 2.2 正文逐节

**`## Non-negotiables`**

首段取自 pstack mode 第 15 行：「In your reply, name each principle that shaped a decision and the specific choice it changed. Cite only principles whose file you read this session.」（改动标注：原文「leaf SKILL.md」改为「file」，因为 MMW 的原则是文件。）无人会话把这一句写进交付物（第 6 节）。

MMW 触发行，每一行都从现有技能 description 或正文里「在某个时刻用我」的句子搬来：

| 条件 → 去处 | 来源 |
|---|---|
| 要关票、改队列 label、写事件 → 只经 `mmw/scripts/ticket.py` 或 `dispatch.sh`；hook 会拦别的写法 | `implement` 第 99 行；`tool-guard.py` `REFUSAL`；`CODING_STANDARDS.md` `## State and configuration` 第 3 条（R14 PC6） |
| 一个脚本或 hook 拒绝了你 → 照它点名的那一个下一步做（**principle-refusals-name-one-next-step**） | ADR 0008；R14 PC3 |
| 要启动、连上、停掉运行中的产品，碰进程或端口 → `ui-acceptance` 的 `## Five rules while the product is running` | `dispatch.sh` 第 109 行 `PRODUCT_RULES` |
| 要写的代码被 screen contract 的一行覆盖 → `ui-acceptance` 的 `references/writing-interface-code.md` | `ui-acceptance` description 末句；`implement` 第 16 行末句 |
| 撤销代价高的决定（架构、数据迁移、大重构、API 形状）落定之前；一个问题试了两次仍不行 → `advisor`（门槛见它的 `references/consulting.md` `## When it is worth a session`） | `advisor` description |
| 同一前提下两次修复都失败 → **principle-attack-the-premise** | pstack mode 第 46 行 |
| 合并冲突，或干净合并后仓库检查变红 → `resolving-merge-conflicts` | `implement` 第 78、99 行 |
| 只有人能做的一步（凭据、第三方控制台、装机实测）→ `wizard`，或按 `to-tickets` 的 `references/person-ticket.md` 开人工票（**principle-human-steps-stay-human**） | `wizard` description；`ui-acceptance` 规则 3 |
| 一个阶段结束 → **principle-decide-at-phase-boundaries** | 残留 `ask-matt/PHASE-BOUNDARIES.md` |
| 会话要交给另一个 agent 或宿主 → `handoff` | `handoff` description；N10 B5 |
| 问题出在用词 → `domain-modeling`、`codebase-design`；刚说的话没被理解 → `wait-what` | 残留 `ask-matt` `## Vocabulary underneath`、`## Standalone` |
| 要自建 git worktree → 放在主工作树的 `.worktrees/` 下，不用 `issue-<n>`、`merge-<branch>` | 根 `AGENTS.md` `## Key Conventions` |
| 在本仓库、有 watch 开着 → 不运行正在被改的 MMW，不移动已安装 checkout | 根 `AGENTS.md` `## Self-hosting boundary`（H5） |
| 改了 `mmw-v2/upstream*/` 的文本 → 写 merge-note；让消费仓库的产物失效 → 写 downstream-note | 根 `AGENTS.md` `## Key Conventions` |
| 凭据与私人数据 → 不进任何产物（**principle-no-secrets-in-artifacts**） | 第 5 节 |
| 一步点名 control、delivery、forge 槽位，或 Cursor、pstack 专有的名字 → `references/slots.md` | 第 8.3 节 |
| 流水线自身出错（脚本、hook、`.mmw/target.json`）→ 夜里：`fault` 子票后停；白天：告诉用户，另开票修，不就地绕过（**principle-route-faults-dont-bypass**） | `implement` 第 18 行；`night.md` 第 82 行 |
| 打开任务板、换 host/model/effort/runner → `setup-mmw` | `dispatch/SKILL.md` 表第 5、6 行 |
| 在票的工作树里，导入的文字写「rebase」→ 读作 `dispatch.sh integrate`，一次合并，不 rebase | `implement` 第 78 行；`slots.md` 同一行 |
| 英文产物（文档、提交信息、PR 描述）→ `unslop`；给用户的回复按 `shared.md` 规则 4–9 | pstack mode 第 26 行（改写，第 13 节判断改动 J3）；R13 I-16 |

`### Imported triggers`（B3 起）：pstack mode 第 19–35 行里被导入的触发行，原文逐行复制，每行在 `imports.tsv` 登记类型 `mode-trigger`。B3 进 11 行（第 19–25、27、29、30、35 行），B4 进 3 行（第 31–33 行）；第 26 行由上表最后一行的 MMW 版代替，第 28、34 行不导入（第 13 节）。这些行里的 Cursor 名字（`AskQuestion`、control skill、`/loop`、Writing the reply、Feature step 3）按 `slots.md` 与本节的别名读。

**`## Principles`**

- 首句取自 pstack mode 第 39 行：「Read the principle file in full for any principle you apply. Each entry names when it applies.」（改动标注：原文「leaf skill」改为「principle file」。）
- 解析规则一句：`principle-<slug>`、`**principle-<slug>**`、「the **<slug>** principle」「the **<slug>** principle skill」、相对链接 `principle-<slug>.md`，都指 `principles/principle-<slug>.md`。pstack 的引用写法（L7 E.1 第 1 条）因此不改就能解析。
- 索引分组照 pstack 的 Core、Architecture、Verification、Delegation、Meta，加一组 Pipeline 放 MMW 自有原则。每行 `**<Title>** (**principle-<slug>**). <何时适用>.`；「何时适用」等于原则文件 `description` 的第一句，导入时由脚本从 description 生成，由连线检查第 5 类核对。索引行不写规则句（R12 K-27）。
- 末段「User rules」：按编号列 `shared.md` 规则 1、6、10、11、13、14、15 的适用时机，不复述内容（S）。

**`## Autonomy`**

- **优先级**（新写，依据 L7 C.2「pstack 没有写明哪一层优先。归置 MMW 时要显式写出优先级」与 C.2 所引 `prototype.md`、`feature.md` 的限定句高于原则的实例；ADR 0032 记录）：`shared.md`（用户规则）> 本 mode > 所服务的 playbook（含它对原则的本地限定）> 原则。能力技能自带的人工闸门不在这条链里：人在场时照闸门停；无人会话里 mode 不覆盖它，而是走本角色的无人出路（下文），例如 `to-spec` 第 6 行的产品闸门在无人会话里变成一条 `decision` 子票。这与第 4.5 节「能力技能自带的闸门保留」一致。
- **人在场**：`shared.md` 规则 1–3 管「谁决定什么」，本节不复述（S）。可以撤销的流水线动作（`advance`、`route`、`resume`）直接做。总是先问的三件：把 project branch 合进默认分支（`night.md` 第 200 行「that remains the user's release decision」）；运行完整的 `install.sh`（根 `AGENTS.md` `## Gotchas`）；`finish` 只在用户验收之后（`night.md` `## 6`）。
- **无人**（启动提示词带 `Unattended`，或 `tool-guard.py` 拦下了一次提问）：屏幕上不放问题；取票、baseline、spec 里最可能的那个选项，写一行进本角色的决定记录，继续做（`implement` 第 23 行）。三个角色的唯一出路：
  - worker：写进 closeout 的 `Decisions I made on my own`；会改变交付内容的开 `decision` 子票并照默认继续（`implement` 第 23 行）；
  - reviewer：报告里在该条末尾写 `unverified: <what would settle it>`（`code-review/references/session.md` 第 89 行）；
  - advisor：写「Missing information gets named precisely」那一条（`advisor/references/advising.md` 第 18 行）。
- **产品事项清单抄一次**：什么是「只有用户能定的事」（顾客看到什么、钱怎么走、范围与先后、对外发布、难以撤销）。这是本 mode 唯一复述 `shared.md` 的一段（H1：Cursor 收不到 `shared.md`）。
- **导入原则的产品限定**：**principle-experience-first** 决定你给用户的建议，不替用户做产品取舍（`shared.md` 规则 1；第 5.3 节）。
- **`shared.md` 规则 11「redo it yourself」与「停下报告」的划界**：你自己的步骤失败了，照规则 11 重做；你代码之外的东西出故障（流水线、环境、够不到产品），`fault` 子票就是这一步的重做，不绕开它（`ui-acceptance` 规则 5「not yours to route around」）。这修掉 R14 PC18 列出的张力。
- 导入的原则与本节冲突时以本节为准。实例：pstack `principle-never-block-on-the-human` 的 `**Boundaries:**` 要求不可逆动作先确认，无人会话里没人可确认，按上一条由脚本承担或不做。
- 这一节接住 `dispatch.sh` 第 108 行 `AUTONOMOUS` 常量里的规则；常量删掉，启动提示词只留 `Unattended` 这个数据（`references/skill-set-rules.md` `### Prompts written for other agents` 第 1 条「Rules reach the agent through the skill it loads」与第 2 条「the prompt keeps the data」）。

**`## Re-entry`**（被唤醒、被压缩、被 `resume` 时）

1. 唤醒可能打断你正在跑的命令，先把它原样再跑一次（**principle-make-operations-idempotent**：流水线的命令都按可重跑写）。
2. 读唤醒点名的那张票；唤醒不带 tracker 之外的内容。
3. `dispatch.sh ack <n> <event>`，在任何长工作之前。`watchdog:` 开头的行和 `MMW turn guard:` 行不 ack。
4. 去唤醒那一行指针点名的步骤。没有指针时（会话被压缩，或收到的不是唤醒），跑 `dispatch.sh where`，照它印出的那一行做（**principle-the-tracker-is-the-state**；输出形式见第 7.7 节）。

本节所说的 `dispatch.sh` 是本技能目录下的 `scripts/dispatch.sh`，即宿主加载本技能的那个已安装 checkout 里的文件；数据文件与唤醒行给出它的绝对路径时用那个路径；不运行你所在工作树里的同名文件（H5）。

来源：`dispatch/SKILL.md` `## On waking` 第 1–4 步整体搬迁。它在 mode 里，每个角色都读得到，修掉 N10 B9。

**`## Subagents`**

- 用宿主自带的通用子代理（ADR 0015）。简报照 `references/subagent-brief.md`，首句「Read the `mmw` skill's `## Principles` and the playbook step you serve.」。例外：评审 axis 这类只读、自足的简报不加这一句（第 3.3 节 P16）。导入组件里的 `subagent_type: "poteto-agent"` 或 `generalPurpose` 一律读作「宿主的通用子代理，带这份简报」。
- 同一步的子代理在一条消息里一起发出，等全部回来（`code-review/references/session.md` 第 23、33 行；`to-tickets` 第 113、119 行；`wayfinder` 第 76、114 行）。报告写进文件，大块工作交给子代理（`session.md` 第 31 行；`manage-agents-md` 第 50 行）。
- 只读靠简报里一句「You are read-only: write nothing.」，宿主没有只读档（`advising.md` 第 23 行；四个 axis 文件第 3 行；R14 PC15）。
- 模型角色：会话内的子代理不指定模型，跑在本会话的模型上（H3，等于 pstack 的 `inherit-parent`）；需要另起会话的角色用 `setup-mmw` 所点名的 `models.py config get <label>` 查；面板角色经 `dispatch.sh panel` 另起会话（第 8.8 节）。
- 取自 pstack mode 第 95 行原文：「You own every subagent's work. Review the diff and write your own summary, don't pass through what it said.」「A second opinion is the same prompt against a different model. Agreement is high-signal.」

**`## Writing the reply`**

- 给用户的回复以 `shared.md` 规则 4–9 为准，本 mode 不复述（S）。
- 取自 pstack mode 第 109 行，删去半句：「Every playbook ends with a reply written this way. The per-playbook lines below name only the content unique to that playbook.」（改动标注：删去原文「, PR link as `https://github.com/<owner>/<repo>/pull/<number>`」，因为 MMW 默认交付不是 PR；B4 起 `delivery: pr` 的仓库由 **Opening a PR** 自己的 Reply 写 PR 链接。）
- 无人会话的「回复」是 playbook 的交付物（closeout、`REVIEW` 报告、spec 上的理由评论）。出处：`shared.md` 前言「what it reports goes in the formats its skills give」。
- pstack mode 第 101–107 行关于标点与句式的规则不管给用户的回复（R13 I-16）；它们经 `unslop` 管英文产物。

**`## Comments`**（B3 起，类型 `mode-section`）：pstack mode 第 111–113 行原文复制。导入的 `feature.md` 第 4 步写「Comments per **Comments**」，`no-comments` 同批导入。

**`## Playbooks`**

1. 执行协议（第 6 节），首段照抄 pstack mode 第 117 行。
2. 别名：「**Opening a PR** means **Deliver a change**」（B4 起，`delivery: pr` 的仓库里就是导入的 **Opening a PR**）；「the control skill means the control row of `references/slots.md`」；「a Cursor command, file or setting names its `references/slots.md` row」；「**poteto-mode** or `/poteto-mode` means this skill」；「**Writing the reply**, for a reply to the user, means `shared.md` rules 4–9」。
3. **没有匹配**。B3 起：「No playbook below fits, or the effort is large or cross-cutting and no playbook here covers it → the **figure-it-out** skill. It designs a bespoke, rigorous playbook for the task.」（取自 pstack mode 第 119 行；改动标注：删去 Orchestrate 一句与「work the user steps away from」一句，因为 MMW 里一份 spec 的整批票走 **Run a night**；判断改动 J2。）B1、B2 期间 `figure-it-out` 未装，这一条是：「No playbook below fits → say so, then open a todolist of the steps you will take, each naming the component it uses, before any work; the same `skip:` rule applies.」（来源：pstack mode 第 117 行的执行协议与 `figure-it-out` 第 9 行「When the task matches no playbook, design one. The deliverable before any code is the workflow itself」。B3 把它换成上一段。）
4. 路由表（第 3.1 节），每行 `- **<Name>.** <任务类型>. [用户原话]. [Distinct from …]. \`playbooks/<file>.md\`.`（L7 A.1）。
5. 一句：当前仓库 `.mmw/playbooks/INDEX.md` 列的私有 playbook 排在表后，只在人在场的会话里用（H5）。

**篇幅**：B2 后约 170 行，B4 后约 200 行（推断；pstack mode 143 行）。上下文成本见 U-5。

### 2.3 怎样被加载（H1、H2）

| 会话 | 到达路径 | 确定性与证据 |
|---|---|---|
| 脚本起的 worker、reviewer | 启动提示词，一行：`Use the mmw skill. Role worker, ticket #<n>, unattended: mmw work-a-ticket#Claim. Data: <文件的绝对路径>.`（reviewer 同形，加 base commit）。数据文件在 `~/.mmw/state/<repo>/prompts/<n>-<role>.md`：已安装 checkout 里这份 playbook 与 `dispatch.sh`、`ticket.py` 的绝对路径（取自 `~/.mmw/installed-root`）、Memory 索引、reviewer Rules 包 | 确定。**必须一行**：herdr 的第一条提示词经 `runners/herdr.sh` 第 204 行 `send` 调 `herdr_ agent prompt`（第 230 行）送进去，H4 管它；orca、paseo 以参数传入（`orca.sh` 第 25 行；`paseo.sh` 第 125 行）。今天 `dispatch.sh` 第 1949、1967、2072 行的提示词是多行的，在 herdr 上是否被拆成几条待测（U-9）。绝对路径保证读的是冻结版本（H5），由连线检查第 12 类核对 |
| advisor | 一行：`Use the advisor skill. Unattended per the mmw skill's ## Autonomy. Brief: <文件路径>.` | 同上 |
| 被唤醒（relay、watchdog、`resume`、turn guard） | 唤醒行同一行末尾接指针：`#<n> reviewer.reported · mmw work-a-ticket#Get reviewed`；由发出方按（收件角色，事件）从 `roles.json` 取；收件角色由 watch 的 `kind` 与票上的 `*.started` 定（第 7.1 节） | 确定（H4 满足）。`ack` 按收件人、票、事件名匹配，不解析文字（R4 V4） |
| 被压缩 | `mode-hook.py` 挂在会话开始事件上（Claude Code 的 `SessionStart`，来源为 compact 时；Codex 的 `SessionStart`）：先查当前仓库是否 MMW 仓库，再在本会话属于流水线时跑 `dispatch.sh where`，打印那一行 | 各宿主能否注入待测（U-2）。本轮核实 `install.sh` 第 774–775 行 `CODEX_CONTEXT_EVENTS` 只是 trust hash 里 `additionalContextLimit` 字段生效的事件集合；据此推出「Codex 这些事件能注入上下文」是**推断**，并入 U-2。没有注入事件的宿主：下一条唤醒自带指针，mode `## Re-entry` 第 4 步让会话自己跑 `where` |
| 会话内子代理 | `mode-hook.py` 挂 `SubagentStart`：在 MMW 仓库打印「Use the mmw skill: read its `## Principles` and the step you serve.」；另由简报首句保证 | Claude Code 的 `SubagentStart` 注入已观察到：本报告的写作会话开头就收到了一段「SubagentStart hook additional context」。其余宿主待测（U-2）。这是 pstack `poteto-agent` 的替代 |
| 人起的会话 | ① `mode-hook.py` 挂 prompt 提交事件：当前仓库是 MMW 仓库才打印一行，照 pstack `reminder` 原文改写：「New task here? Playbook match or rigor needed → apply the mmw skill. Casual turn or user opts out → don't.」；② mode description 模型可调用；③ 消费仓库 `AGENTS.md` 一行（待你决定）；④ `/mmw` | 各宿主能否注入待测（U-2）。只在 MMW 仓库打印，回应 ADR 0014 否决常驻规则的两条理由（R4 V16）。②④ 已有机制 |
| 夜或单票的 orchestrator | 同人起的会话；`dispatch.sh open`、`open-ticket` 打印的那一行末尾加 `· mmw run-a-night#Handle each wake`（单票为 `run-one-ticket`） | 确定 |

`mode-hook.py` 的范围（三种事件相同）：当前仓库没有 `.mmw/` 与 `docs/agents/issue-tracker.md` 时不输出、退出 0；只在工作目录名是 `issue-<n>`，或 `watches.json` 里某个 watch 的收件会话是本会话（`dispatch.sh self` 读 runner 的环境变量，不读 tracker）时才调用 `where`，其余只打印那一句提醒。失败时不输出、退出 0，头注释写明它是辅助路径、不是 ADR 0008 管的闸口；判断是不是 Cursor 在调用按 payload 字段，不按环境变量（根 `AGENTS.md` `## Gotchas` 第 4 条）。

### 2.4 各批次里 mode 的内容

连线检查第 2 类在每批发布前对 mode 跑一遍，必须干净：mode 在任何一批里只点名当时已经存在的组件。

| 批 | `## Re-entry` 与脚本路径 | 触发行 | 路由表 |
|---|---|---|---|
| B1 | 指向 `dispatch` 技能的 `scripts/dispatch.sh`（`ack` 已有，`where` 在 B0 加入） | 不含 `setup-mmw`、`orchestrator-events.md`、`ticket.py` 三行；关票一行写 `verify-ticket.py`；换模型一行指向 `dispatch` 技能 | 夜间五行指向 `dispatch` 技能的 `references/night.md`、`one-ticket.md`、`inside-a-ticket.md` 与 `implement`、`code-review` 技能；「没有匹配」用 B1、B2 版 |
| B2 | 改为 `mmw/scripts/dispatch.sh` | 加上三行，关票一行改为 `ticket.py` | 夜间五行指向 P12–P16 |
| B3 | 同 B2 | 加 `### Imported triggers` 11 行 | 加 6 份 playbook 行与 4 条直接能力行（第 3.1 节），「没有匹配」换成 `figure-it-out` |
| B4、B5 | 同 B2 | B4 加 3 行 | B4 加 4 行（其中 3 行只在 `delivery: pr` 的仓库出现），B5 加 4 行 |

---
## 3. playbook 总目录

**采用的决定。** B2 后 `mmw/playbooks/` 有 18 份：MMW 自有 16 份（白天 11 份、夜间与单票 5 份），pstack 原文 2 份（`session-pickup`、`pause-safely`，B1 导入）；本仓库私有 3 份在 `.mmw/playbooks/`。B3 至 B5 再导入 pstack 14 份，`bug-fix` 在 B3 合并（第 13 节）。

**判据。** 一类任务里多项能力的先后，有自己的门槛、所有权或交付物（R13 E1；L7 C.1 第 3 问）。只调用一个技能、内部步骤属于那项能力做法的请求，按 L7 C.3 与 C.6 信号 5 属于能力层，由路由表直接指向能力技能。据此：
- 出包不设 playbook。`exe-release` 第 1–5 步（先决条件、`git ls-files '*.release-adapter.json'` 挑产品、逐个驱动、同提交核对、交用户装机）是「怎样出包」本身，只编排它自己的引擎，按 C.3 的共同判据留在能力内。
- advisor 的被咨询一方不设 playbook（第 1.4 节）。

**放弃的备选。**
- R15 在 B1 先写 MMW 版 `session-pickup`、`pause-safely`：MMW 没有这两类白天会话的原文。改为 B1 连同子树直接导入。
- R16 在 B1 就用 pstack `bug-fix.md`：它依赖 `how`、`why`、`architect`，B3 才有。B1 用 MMW 自己的来源写，B3 合并（第 3.3 节 P6）。
- R15 的 `ticket-adoption` 单列：只多一步 `adopt`，作为 `work-a-ticket` 的入口变体。

### 3.1 路由表（mode `## Playbooks` 的内容）

| # | 名字 · 文件 | 任务类型与用户原话 | Distinct from | 入口 |
|---|---|---|---|---|
| P1 | **Define a change** · `define-a-change.md` | 一段对话、一个想法、一张清空的地图、一个判为可做的 issue、一个架构决定，要变成已发布的 spec 与通过 lint 的票（「把这个做成 spec」「切票」） | Map a large effort：终点还看不见；Direct change：小到用户当场检查 | 路由；P2、P3、P4、P6、P7 交过来的进 **Write the spec** |
| P2 | **Map a large effort** · `map-a-large-effort.md` | 一个会话装不下、路线看不清（全新项目、大功能） | Define a change：一次访谈加一份 spec 装得下（`wayfinder` description「Not for a well-scoped feature」） | 路由 |
| P3 | **Design an interface** · `design-an-interface.md` | 界面要设计或翻新；Claude Design 项目里有排队的评论；设计包已签字要拉回仓库；screen contract 要重写 | Prototype：还在比较草图；设计系统单独构建：直接能力行 | 路由；P4 的 UI 结论 |
| P4 | **Prototype** · `prototype.md` | 要靠做出来、跑起来才能定的问题：状态模型、界面长相、一个库或做法能不能行（「做个原型」「mock it up」「sketch it to decide」） | Define a change：问题在对话里就能答；Research a question：答案在文档里 | 路由；P1 **Settle runnable questions** |
| P5 | **Direct change** · `direct-change.md` | 小到用户会直接检查的改动，不开票、不跑夜 | Define a change：要多个会话、脚本判据与独立评审（残留 `ask-matt` 第 26 行）；B3 起另有 Feature、Refactoring | 路由；P1 **Decide who checks** |
| P6 | **Bug fix** · `bug-fix.md` | 有东西坏了、报错（「debug」「diagnose」） | Triage an issue：外来的、还没判断的 issue；B3 起 Perf issue：量得出的变慢 | 路由 |
| P7 | **Triage an issue** · `triage-an-issue.md` | 不是你建的 issue 或外部 PR 在等判断 | Accept the night：流水线自己交回的票 | 路由 |
| P8 | **Research a question** · `research-a-question.md` | 要一手来源回答一个问题，答案写成仓库里的文件（「查一下」「调研」） | B3 起 Investigation：只读回答代码怎么工作 | 路由；P2 的调研票 |
| P9 | **Onboard a repository** · `onboard-a-repository.md` | 给一个仓库接入 MMW | — | 路由 |
| P10 | **Deliver a change** · `deliver-a-change.md` | 按本仓库收改动的方式交出一个完成的改动 | — | 其他 playbook 的最后一步；别名 Opening a PR |
| P11 | **Authoring or modifying a skill** · `authoring-a-skill.md` | 写或改技能、playbook、原则、mode，或任何 agent 读的文字 | B3 起 Eval：量一处改动对 agent 行为的影响 | 路由；Import a component |
| P12 | **Run a night** · `run-a-night.md` | 「今晚跑 spec #N」：一份 spec 的整批票 | Run one ticket | 路由；`roles.json` `night-orchestrator` |
| P13 | **Accept the night** · `accept-the-night.md` | 夜跑完了：早上的队列、验收、`finish` | Triage an issue：单个外来 issue | 路由；P12 最后一步；`where` 在「`spec.retroed` 已记录、未合并」时指向这里 |
| P14 | **Run one ticket** · `run-one-ticket.md` | 在夜之外起一个 worker 做一张票 | Work a ticket：那里你就是 worker | 路由 |
| P15 | **Work a ticket** · `work-a-ticket.md` | 被 `start` 派到一张票上；或自己拿起一张票（入口 **Picked up yourself**） | Run one ticket | 启动提示词；路由 |
| P16 | **Review a ticket** · `review-a-ticket.md` | 被起为一张票的 reviewer | 能力技能 `code-review`：不绑票的评审 | 启动提示词 |
| P17 | **Session pickup** · `session-pickup.md`（pstack 原文） | 接手前一个 agent 没做完的工作（handoff 文件、会话记录、推上去的分支） | 绑票的会话被唤醒：mode `## Re-entry`；B3 起 `recall`：跨多个会话找回上下文 | 路由 |
| P18 | **Pause safely** · `pause-safely.md`（pstack 原文） | 显式暂停、换宿主、宿主重启、即将压缩 | Run a night 的 `#### Suspending the night` | 路由 |

**直接指向能力技能的行**（每行一句 Distinct from）：
- 顾问 → `advisor`（Distinct from `interrogate`：一个决定、一个更强的模型，不是多模型对抗评审）。
- 换模型、runner，开任务板 → `setup-mmw`。
- 出包、打安装包（「ship」「package」）→ `exe-release`（Distinct from Accept the night 的 `finish`：合进 project branch，不出包）。
- 设计系统（「搭一套设计系统」「要不要建设计系统」）→ `design-pages` 的 `references/design-system.md`（Distinct from Design an interface：不出页面，不写 screen contract）。
- 代码架构整理的普查 → 告诉用户运行 `/improve-codebase-architecture`（用户触发的技能），选定的决定进 **Define a change**（Distinct from B3 起的 Refactoring：执行一次已定的、不改行为的结构改动）。
- 不绑票的一次评审 → `code-review`；画图 → `diagram-design`；写 AGENTS.md → `manage-agents-md`；装检查器 → `code-checkers`；学一个概念 → `teach`；把刚说的讲简单 → `wait-what`；问卷 → `to-questionnaire`；只有人能做的步骤 → `wizard`；交接 → `handoff`；无仓库的访谈 → `grill-me`；重跑一次夜的复盘 → `retro`。
- B3 起：复盘这个会话（「reflect」）→ `reflect`（Distinct from `retro`：`retro` 复盘一夜的事件，`reflect` 复盘当前会话的记录）；找回最近的工作上下文（「catch me up」）→ `recall`；影响面（「what could this break」）→ `blast-radius`；技术文档 → `technical-writing`。

**本仓库私有**（`.mmw/playbooks/INDEX.md`）：**Promote a change**、**Pull an upstream**、**Import a component**。

**B3 加的行**：**Feature**（`feature.md`；Distinct from Direct change：新行为，从一个命名的数据形状出发，委派实现）、**Investigation**（`investigation.md`；Distinct from Research a question：只读回答代码问题，不写调研文件）、**Refactoring**（`refactoring.md`；Distinct from Feature 与 Bug fix，原文）、**Perf issue**（`perf-issue.md`；Distinct from Bug fix）、**Autonomous run**（`autonomous-run.md`；Distinct from Run a night：一个任务跑到一个可检查的谓词成立，不是一批票）、**Eval**（`eval.md`；Distinct from Authoring or modifying a skill）。**B4**：**Opening a PR**、**Babysit**、**Shipping**（这三行只在 `delivery: pr` 的仓库出现）、**Worktree and simulator cleanup**。**B5**：**Runtime forensics**、**Trace forensics**、**Hillclimb**、**Visual parity**（Distinct from Design an interface：两套实现之间像素一致，不是设计到页面）。

### 3.2 统一骨架

照 pstack（L7 A.2），MMW 自写的 playbook 多两个可选段：

```
### <Name>

**You own <对象>. <动词>, <动词>.**                 所有权行（有出处才写）
<可选首段：本类任务的纪律、与相邻 playbook 的界线>
**Entry.** <多入口的 playbook：每个入口一行>          MMW 多出
**Where you are.** <读哪条脚本输出定位>               MMW 多出：跨会话、会被唤醒的 playbook（H6）

#### Steps                                            长 playbook 才写这一行；只有这些步骤抄进待办
1. **<Title>.** <祈使句>。点名一个能力技能、原则、脚本命令或别的 playbook；门槛与 Done when。
…

#### <规则簇>                                         常设规则，不进待办（pstack orchestrate.md，L7 D.1）

**Reply:** <本 playbook 独有的回复或交付物>
```

规则：步骤只点名组件，不复述做法（pstack `authoring-a-skill.md`「Delegate to other skills by path. Don't restate.」）；原则用括注点名，可加一句本地限定（L7 C.2）；引用别的组件按名字加意图或按标题，不按编号；每一步至少点名一个组件或标 `(judgement)`（连线检查第 7 类）。**所有权行只在有出处时写**，出处写在下文各份的「所有权」一项；找不到出处的只留骨架。导入的 pstack playbook 保持原文：步骤没有粗体标题，连线检查对它们只查 `### <Name>` 与 `**Reply:**`，脚本指针不以它们为目标（第 7.5 节）。

### 3.3 逐份

下面每份写：入口、所有权及其出处、步骤骨架（标题 + 点名的组件）、重入、交付物、原文来源。步骤正文从来源原文搬。

#### P1 Define a change

- **Entry**：一段对话或想法；`wayfinder` 地图清空；`triage` 判 `ready-for-agent`；`improve-codebase-architecture` 选定的决定；**Prototype** 的 LOGIC 或 EXP 结论（补 N10 B4）。
- **所有权**：You own the batch the night will build. The user owns every product call.（出处：`to-spec/SKILL.md` 第 6 行「A call on what the user sees, what happens to money, or what is in scope … is not yours」）
- **步骤**：
  1. **Interview.** `grilling` 与 `domain-modeling`（用户输入 `/grill-with-docs` 的会话就处在这一步）；仓库外的一手事实用 `research`（**principle-attack-the-premise**）。
  2. **Settle runnable questions.** 答案要靠运行才能知道的，走 **Prototype**；它的 UI 结论经 **Design an interface** 回到 **Write the spec**。
  3. **Ask the one who knows.** 缺的知识在别人脑子里：`to-questionnaire`，结束回合。
  4. **Decide who checks.** 要多个会话、脚本判据与独立评审 → 继续；小到用户直接检查 → **Direct change**，本 playbook 结束（残留 `ask-matt` 第 22–26 行；补 N10 B3）。
  5. **Write the spec.** `to-spec`；来源是已分诊 issue 时，发布后关掉它并链接 spec（ADR 0001；R12 K-15）。
  6. **Split into several specs when it is several.** 一份参考拆成几份 spec 时，把划分交给用户确认，写回地图 `## Specs` 或第一份 spec 的 `## Further Notes`，一次写一份并停下（`to-spec/references/several-specs.md` 全文：这份文件整份是一次多会话的先后，按类型属于 playbook；`to-spec` 留下「怎样判断划分」一句）。
  7. **Cut the tickets.** `to-tickets`；歧义扫描交给没写这批票的子代理（**principle-a-second-reader-judges**）。
  8. **Lint the batch.** `verify-ticket.py <spec> --lint`，直到没有 `ERROR`（**principle-silence-is-never-a-pass**）。
  9. **Hand to the night.** 什么时候开夜由用户定：**Run a night** 或 **Run one ticket**。
- **规则簇**：`#### Session boundaries`——从 **Interview** 到 **Cut the tickets** 在同一个未清空的上下文里，临界时按 **principle-decide-at-phase-boundaries**（残留 `ask-matt` `### Context hygiene`；`grill-with-docs` 第 7 行「in this same session」）。
- **Where you are**：九行事实表（R12 K-33），每行的事实都在 tracker 或仓库里（spec 已发布无票 → **Cut the tickets**；票已过 lint → **Hand to the night**；其余 → **Interview**）。
- **Reply**：spec 链接、票号与 worker 等级、lint 结果、留给用户的产品问题、`skip:` 的步骤。
- **来源**：`to-spec` `## Next`、第 1 步第 12 行、第 4 步；`to-tickets` 第 20、160 行；`grill-with-docs` 第 7 行末句；`improve-codebase-architecture` `### 4. Hand the decision on`；`verify-ticket/references/linting.md` 第 3 行；`several-specs.md`；残留 `ask-matt` 主流程（R14 T16–T18、T22–T24、T14、T36）。

#### P2 Map a large effort

- **所有权**：You own the map, not the build.（出处：上游 `wayfinder` `## Plan, don't do`）
- **步骤**：1 **Chart the map.** `wayfinder` 的 `### Chart the map`；终点有界面或翻新已有产品时读 `references/interface-and-remake.md`（本轮读全文：它规定对齐票、设计票与选择清单，只在地图有界面或翻新时读，属于分支才读的 reference）。2 **Resolve one decision ticket at a time.** `wayfinder` 的 `### Work through the map`；调研票 → **Research a question**；原型票 → **Prototype**；设计票与对齐票 → **Design an interface**。3 **Hand the clear map on.** 没有未关子票、「Not yet specified」为空时，告诉用户在新会话里对这张地图跑 **Define a change**。
- **Where you are**：地图在 tracker 上。**Reply**：已决与未决的票。
- **来源**：`wayfinder` 第 6 步第 126 行；`interface-and-remake.md`；残留 `ask-matt` 第 48 行「it hands off, it doesn't build」（R14 T21）。

#### P3 Design an interface

- **Entry**：**Prototype** 的 UI 胜出方案；Claude Design 项目里有排队的评论；用户说设计签字了；一份已拉回的设计包要重写 screen contract。
- **所有权**：The user owns how it looks.（出处：`design-pages/SKILL.md` 第 10 行「how they look is the user's call」）
- **步骤**：1 **Set up the Claude Design project.** `design-pages` 的 `references/edit-pages.md`；宿主没有 Claude Design 工具时，该技能自己的闸门停下，这时走 **Pause safely** 并告诉用户运行 `handoff` 换宿主（R12 K-43）。2 **Act on queued comments.** `design-pages` 的 `references/draw.md` `## Comments`。3 **Pull the signed-off design.** `design-pages` 的 `references/pull.md`；首次 pull 后拆掉原型脚手架（同文件 `## After the first pull`）。4 **Write the screen contract.** 按 `#### Change classes` 选分支；差距清单等用户回答。5 **Stop on unaligned rows.** 有未对齐的行：开对齐票，或走 `write-screen-contract` 的 `Reverse sweep`（`to-spec` 第 2 步第 22 行的闸门）。6 **Back to the spec.** 首次 → **Define a change** 的 **Write the spec**；spec 已发布 → `to-spec` 的 `references/revising-a-spec.md`。
- **规则簇**：`#### Change classes`（出处：`pull.md` `## Reached from here` 的三路：没有 screen contract → `write-screen-contract` 全量；`增删控件或改流转` → 它的 **Re-runs**；`只改外观或文案` → 不改 screen contract，`reverify <spec>`）；`#### A pull made for a wayfinder design ticket`（同节第一段：回到 **Map a large effort**）；`#### A contract child answered by a pull`（`pull.md` 同名段：评论 → `dispatch.sh route` → 挪票 → `resume`；`orchestrator-events.md` 的 contract 行指向它）。
- **原则**：**principle-the-baseline-is-a-contract**。**Reply**：设计包路径、screen contract 的行数与对齐状态。
- **来源**：`prototype/UI.md` 第 3 步第 83 行与 `## Next`；`edit-pages.md` `## Next`；`pull.md`；`draw.md`；`write-screen-contract` `## Next`（R14 T22、T25、T26）。

#### P4 Prototype

- **所有权**：You own the design decision, not the code.（出处：pstack `prototype.md` 所有权行前半句；后半句「The real build follows Feature」不取，MMW 的正式实现走 **Define a change** 或 **Direct change**。）
- **步骤**：1 **Scope the decision.** 说出原型要定的那个决定；「No decision means no prototype.」（pstack `prototype.md` 第 1 步原文。）2 **Pick the branch.** `prototype`：状态与逻辑 → LOGIC，界面长相 → UI，一个库、算法或集成能不能行 → EXP（`prototype/SKILL.md` 的分支表；判不准时按它的缺省规则）。3 **Build and observe it.** `prototype` 的该分支，放在 `prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/`（`prototype` 规则 1）。4 **Present the alternatives.** 选项、取舍与推荐（pstack `prototype.md` 第 6 步原文前两句）。5 **Hand the answer on.** 答案写进叶目录 `README.md`（`prototype` 规则 6）；UI 胜出 → **Design an interface**；LOGIC、EXP 的结论 → **Define a change** 的 **Write the spec**，或小到用户直接检查时 **Direct change**。
- **Reply**：取自 pstack `prototype.md` 的 Reply，删去「Say plainly that the prototype is throwaway」（MMW 的原型留在仓库作参考，`prototype` 规则 6「keep the prototype」）。
- **来源**：pstack `prototype.md`；`prototype/SKILL.md` 规则 1、6 与分支表；`prototype/UI.md` `## Next`；残留 `ask-matt` 第 19–21 行。`imports.tsv` 记为「合并：MMW 版，吸收 pstack 第 1、6 步与 Reply」，判断改动 J1。pstack 第 3 步「Build throwaway in an isolated scratch dir」与 `prototype` 规则 1 冲突，以能力技能的做法为准（第 2.2 节优先级：「这一步怎么做」以能力技能为准）。

#### P5 Direct change

- **所有权**：The user checks this change directly.（出处：残留 `ask-matt` 第 26 行「Take **No** only for a change small enough that the user will check it directly」）
- **步骤**：1 **Write it test-first.** `tdd`，在事先约定的 seam 上；写码规则按 `references/writing-code.md`。2 **Run the checks.** 定期跑类型检查与单个测试文件；结束时只跑仓库为这次改动点名的测试（`shared.md` 规则 15 高于上游原文「full test suite once at the end」）。3 **Get a second reading.** `code-review`，固定点是本次改动的起点（**principle-a-second-reader-judges**）。4 **Deliver.** **Deliver a change**。
- **Reply**：改了什么、怎么验证、为什么要新加文件或依赖（`writing-code.md` 那一句的本地出口）、请用户检查的点。
- **来源**：上游 `implement` 原文五行（squash `5b1a4c51`，本轮已读）；残留 `ask-matt` 第 24–26 行。

#### P6 Bug fix（B1–B2 为 MMW 版；B3 合并 pstack 原文）

B1–B2 的 MMW 版：
- **所有权**：You own this task. Plan, review, verify.（出处：pstack `bug-fix.md` 所有权行第一、二句。）
- **步骤**：1 **Build a red loop.** `diagnosing-bugs`，先建一个在这个 bug 上能变红的命令。2 **Find the root cause.** `diagnosing-bugs`（**principle-fix-root-causes**；两次修复失败 → **principle-attack-the-premise**）。3 **Choose the route.** 小修复且有 seam：本会话用 `tdd` 先写失败测试；没有能锁住 bug 的 seam：告诉用户运行 `/improve-codebase-architecture`；要多个会话：**Define a change**。4 **Verify on the same surface.** 原复现现在通过（**principle-prove-it-works**）。5 **Deliver.** **Deliver a change**。
- **Reply**（取自 pstack `bug-fix.md`）：what was broken, root cause, fix, how you verified；复现从红到绿的原样输出。
- **来源**：残留 `ask-matt` 第 44 行「Something's broken」；上游 `diagnosing-bugs`（零差异，R14 第 6 节）；补 N10 B6。

B3 合并：`playbooks/bug-fix.md` 换成 pstack 原文第 1–6 步，第 6 步「Run **Opening a PR**」之前插入一步 MMW 补充步，其余不改：
- 插入的一步：「**Choose the route.** A fix with no seam that can lock the bug down → tell the user to run `/improve-codebase-architecture`. A fix that needs several sessions → **Define a change**, and this playbook ends here.」（来源：B1 版第 3 步；判断改动 J4，记入 `imports.tsv` 与 `merge-notes/pstack.md`。）
- 与 `diagnosing-bugs` 的关系写进 `slots.md` 一行：pstack 第 2 步「Binary-search the cause」的做法就是 `diagnosing-bugs` 的反馈循环；循环难建时读它（来源：`diagnosing-bugs` description「Diagnosis loop for hard bugs」）。mode 不因此多触发行。
- 第 1 步「via the control skill (Non-negotiables)」→ `slots.md` control 行；第 2 步「Cursor's `/loop` command」→ `slots.md`；第 3 步「your configured bug-fix model」→ `slots.md`；第 5 步「the **tdd** skill」由 MMW 已装的 `tdd` 满足点名。

#### P7 Triage an issue

- **所有权**：The maintainer owns each outcome.（出处：`triage` 第 2 步「Tell the maintainer your category … Wait for direction.」）
- **步骤**：1 **Triage.** `triage` 的 `## Triage a specific issue or PR`，到它给出四种结果之一为止。2 **Route ready-for-agent work.** 写 agent brief，进 **Define a change** 的 **Write the spec**，以这个 issue 为来源。流水线交回的票不在这里判，转 **Accept the night**。
- **Reply**：每个 issue 的结论与理由。**来源**：`triage/SKILL.md` 第 70、82、94 行；残留 `ask-matt` 第 40–42 行（R14 T19）。

#### P8 Research a question

- **所有权**：不写（`research` 与相关原文没有所有权句）。
- **步骤**：1 **Name the decision it feeds.** 地图上的票、spec 的 `## Sources` 或一份 ADR。2 **Run the research.** `research`（后台代理，一手来源，写成仓库里的 Markdown 文件）。3 **Link it where the decision is.** 解答评论、spec `## Sources` 或 ADR 引用这个文件（**principle-clues-are-not-evidence**）。
- **来源**：`research` 三步；`wayfinder` 第 5 步；`to-spec` 模板 `## Sources`；根 `AGENTS.md` 开头「a spec may cite」。

#### P9 Onboard a repository

- **步骤**：1 **Set up the tracker.** `setup-matt-pocock-skills`，然后把 `references/tracker-additions.md` 写进 `docs/agents/issue-tracker.md`（内容是今天上游种子里 MMW 加的 `## Three label sets`、「In this toolbox the tracker is also the landing pipeline's store」与「keep the defaults」两段；本轮 `git diff` 核实）。2 **Write the agent files.** `manage-agents-md`（`mmw` 那一行待你决定）。3 **Install the checkers.** `code-checkers`，结果写进 `.mmw/target.json` 的 `checks`。4 **Answer the product questions.** 有界面的仓库：`ui-acceptance` 的 `target_config.py --check` 直到退出 0。5 **Say how it takes changes.** `.mmw/target.json` 的 `delivery`（第 1.2 节；问用户）。6 **Check the machine.** `bash mmw-v2/install.sh --check`（只读）。
- **交付物**：`.mmw/target.json` 完整，`--check` 退出 0。**来源**：`setup-matt-pocock-skills` 第 17、51、63 行与种子；`code-checkers` 第 6、8 步；`night.md` 第 54–56 行（R14 T32、T33）。

#### P10 Deliver a change

- **步骤**：1 **Find how this repository takes changes.** 在票的工作树里：交付就是 closeout，本 playbook 不适用（`implement` 第 99 行）。其余按 `.mmw/target.json` 的 `delivery`：`commit` 或缺省 → 提交到当前分支并告诉用户（上游 `implement` 末句「Commit your work to the current branch.」）；`pr` → **Opening a PR**（B4）；`playbook:<slug>` → 该仓库私有 playbook `<slug>`。2 **Deliver.** 照第 1 步选出的那一种做；改了技能 description 的，提醒用户开新会话（H2）。
- **Reply**：提交号、交付到了哪一步、还差什么。本仓库的 `delivery` 是 `playbook:promote-a-change`。

#### P11 Authoring or modifying a skill

- 与 pstack 同名。pstack 原文末段「Tell it to do the thing and skip the reason」与 `skill-set-rules.md` 事实 1「next to a rule, the reason for it」冲突，所以用 MMW 版；`imports.tsv` 记为「合并：MMW 版，吸收 pstack 第 2 步 Validate 与末段 When in doubt, delete 一句」（判断改动 J5）。
- **步骤**：1 **Place it.** 按 `references/skill-set-rules.md` 的 `## Layers of the set`（第 7.9 节）决定它是 mode 行、playbook、原则、reference 还是能力技能。2 **Write it.** `writing-for-agents`（**principle-one-home-per-meaning**、**principle-encode-lessons-in-structure**）。3 **Validate it.** frontmatter、引用的文件存在、跨技能链接可解析（pstack 第 2 步原文）；`check_wiring.py`。4 **Record what it changes elsewhere.** 改了上游 → merge-note；消费仓库产物失效 → downstream-note。5 **Run the smallest suites.** `TESTING.md` `## Which suites a change needs`（`shared.md` 规则 15）。6 **Walk a real task.**（`skill-set-rules.md` `## Verifying`；B3 起要量行为差异时走 **Eval**）7 **Deliver.** **Deliver a change**。
- **来源**：`SKILL-SET-RULES.md` `## Editing`、`## Verifying`；pstack `authoring-a-skill.md`（R14 T35、T38）。

#### P12 Run a night（night-orchestrator）

- **所有权**：You own the night's decisions, never a worker's code.（出处：`night.md` 第 3 行「Every decision is yours」、第 96 行「its code is the worker's」）首段：早上的读者是冷读，理由留在他会看的地方（`night.md` 第 5 行）；一夜的产出是一批可以验收的票（`night.md` 第 7 行，**principle-silence-is-never-a-pass**）。
- **Where you are**：`dispatch.sh where <spec>`（第 7.7 节的输出形式）。
- **`#### Steps`**：
  1. **Check and open.** `dispatch.sh check <spec>`、`open <spec>`，把任务板 URL 交给用户。
  2. **Lint the batch.** `verify-ticket.py <spec> --lint`；批次驱动 screen contract 时再跑 `target_config.py --check`。
  3. **Advance, then end your turn.** `dispatch.sh advance <spec>`（**principle-woken-not-polled**）。
  4. **Handle each wake.** mode `## Re-entry`（到 ack 为止）；`dispatch.sh status <spec>`；按 `references/orchestrator-events.md` 处理每一行；`advance` 一次；前沿空且没有活代理 → **Closing pass**，否则结束回合。
  5. **Closing pass.** 按 `#### Closing pass`：`findings`、`route`、新票 `--lint`、`advance`，循环到没有未路由的 finding。
  6. **Close the Memory records.** `dispatch.sh memory-list <spec>`；四种关闭决定的写法见 `shared-experience`。
  7. **Reverify and summarize.** `dispatch.sh reverify <spec>`；`summary <spec> --memory-decisions <file>`。
  8. **Retro.** 本会话里用 `retro`，直到 `spec.retroed`。
  9. **Hand the night to the user.** 告诉用户读 `NIGHT SUMMARY`、`NIGHT RETRO`，接受后走 **Accept the night**。
- **规则簇**：`#### Contract children`（`night.md` 第 96–100 行的权威顺序）；`#### Closing pass`（`night.md` `## 4` 整块，本轮读全文；理由句换成点名：第 126 行 Owns 并发 → **principle-separate-before-serializing-shared-state**；第 127 行 negative control → **principle-silence-is-never-a-pass**；第 131 行「run the affected tests」→ `shared.md` 规则 15；第 128 行「A name echoed through prose is not a coupling」等领域参数留在原处，L7 C.2）；`#### Suspending the night`（同名节）；`#### Unattended outlets`（`night.md` 第 100 行：没开始的票移到 `needs-triage`，在子票上评论，留给用户）。
- **reference `orchestrator-events.md`**（与 P14 共用）：`night.md` `## 3` 表全部 16 行（本轮读全文），另补齐三处：`MMW turn guard:` 一行（照消息里的命令做，R4 V7；`turn-guard.py` 第 306–311 行）；`watchdog.py` 第 94–109 行八种告警各一行（R12 M16）；`resume` 的退出码（本轮读 `dispatch.sh` `resume_one`：0 已送达；4 已交出、看不到回合开始，不再发；3 对方多半在回合中，结束回合、下次唤醒再发，若再得 3 且票上无新事件则 `start <n> worker` 替换；2 会话已不在，先 `retract <n>`；补 R4 V8 的空节）。
- **Reply**：`NIGHT SUMMARY` 与 `spec.retroed`；`skip:` 行写在 spec 的一条评论里。
- **来源**：`dispatch/references/night.md` 全文（210 行）；`retro/SKILL.md` 第 186 行（R14 T7、T27、T37）。

#### P13 Accept the night

- **所有权**：The user owns acceptance and the release decision.（出处：`night.md` 第 188 行「after they accept the result」、第 200 行「that remains the user's release decision」）
- **步骤**：1 **Read the night out.** 把 `NIGHT SUMMARY`、`NIGHT RETRO` 的要点说给用户（`shared.md` 规则 4、5）。2 **Work the needs-triage queue.** `docs/agents/issue-tracker.md` `## Morning queries` 第一条查询；每条用 `triage`，流水线产出的按 `references/pipeline-issues.md`（本轮读全文：它规定每条变成用户一句话能答的问题、`ready-for-agent` 的三个去处）；需要路由的用 `dispatch.sh route`。3 **Put the retro proposals to the user.** 批准的进 **Define a change** 或 **Authoring or modifying a skill**。4 **List what only the user can do.** 第二条查询 `ready-for-human`（**principle-human-steps-stay-human**）。5 **Merge the accepted night.** 只在用户验收之后：`dispatch.sh finish <spec>`；stderr 给出的删 worktree 命令交给用户。不把 project branch 合进默认分支。
- **交付物**：`finish` 退出 0。**来源**：`night.md` `## 5` 末段与 `## 6`；`pipeline-issues.md`；`triage/SKILL.md` 第 70、90 行（R14 T20、T34）。

#### P14 Run one ticket（ticket-orchestrator）

- **所有权**：You own one ticket's ending: `land <n>` is its whole ending.（出处：`one-ticket.md` 第 3 行「`land <n>` is its whole ending」）
- **步骤**：1 **Open the ticket's watch.** `dispatch.sh open-ticket <n>`，交任务板 URL。2 **Start the worker, then end your turn.** `dispatch.sh start <n> worker`（**principle-woken-not-polled**）。3 **Handle each wake.** mode `## Re-entry`；`references/orchestrator-events.md`（与 P12 共用，读票状态用 `ticket.py fold <n>` 代替 `status`）。4 **Land.** `dispatch.sh land <n>`，Done when 退出 0；`bounced` 时告诉用户哪张票、`ticket.bounced` 写了什么。
- **来源**：`dispatch/references/one-ticket.md`（14 行，本轮读全文）。

#### P15 Work a ticket（worker、self-picked-worker）

- **Entry**：`start` 起的 worker（启动提示词点名）；**Picked up yourself**（先 `dispatch.sh adopt <n> [--into <base>]`，`inside-a-ticket.md`）；被唤醒（指针）或被压缩（`where`）。
- **所有权**：You own this ticket's branch until its closeout. The orchestrator lands it.（出处：`implement` 第 99 行）票体、spec、判据、baseline 归 orchestrator 与用户。
- **Where you are**：`dispatch.sh where <n>`（第 7.7 节）。
- **`#### Steps`**（标题一一对应 `implement` 原文；第 4–8 步是今天 `resume_at` 返回的「step 1」到「step 5」）：
  1. **Claim.** `ticket.py <n> --preflight`；`NOT_READY` 就停；分支上前一个 worker 的 `wip(#<n>)` 提交接着做。
  2. **Read yourself in.** 票、开着的子 issue、**Read first**（**principle-the-baseline-is-a-contract**）、**Parent** 的 spec 小节、词表；有 screen contract → `ui-acceptance` 的 `references/writing-interface-code.md`；相关 Memory → `shared-experience`。
  3. **Write the code.** `tdd`，两句本地限定：seam 是票 `## Seam` 点名的那些；`CHECK:` 点名的用例就是第一条红测试（`tdd` 第 22 行本仓加句、`implement` 第 30 行）。`#### While writing code` 适用。
  4. **Integrate and run every criterion.** `dispatch.sh integrate <n>`；冲突或检查变红 → `resolving-merge-conflicts`（该技能第 2 步的票语句回到这里：先认出新合入的每张票，读它的票与 closeout 证据）；然后 `ticket.py <n> --check`。
  5. **Post the decisions.** `ticket.py <n> --decisions <file>`。
  6. **Get reviewed.** `dispatch.sh start <n> reviewer`，结束回合（**principle-a-second-reader-judges**、**principle-woken-not-polled**）。被 `reviewer.reported` 唤醒：票内问题修掉或写 `refuted:`；票外问题 `ticket.py <n> --sub-issue finding`；这一轮修复就是 `tdd` 的 refactor 轮（`tdd` 第 38 行本仓加句回到这里）。被 `reviewer.lost` 唤醒：另起一个 reviewer。
  7. **Run every criterion one final time.** `ticket.py <n> --check --reverify --actor worker`。
  8. **Audit against the ticket.**（**principle-prove-it-works**）
  9. **Tell the touched tickets.** `ticket.py <n> --touched`。
  10. **Draft the closing comment.** `ticket.py <n> --draft`。
  11. **Close out.** 只有人能答的判据写 `ABANDON: AC<n> decision …` 并开 `decision` 子票；`ticket.py <n> --closeout <draft>`。
- **规则簇**（不进待办）：
  - `#### While writing code`：`implement` 第 22–28 行的票相关部分——baseline 是合同，本地后果一句「a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on this one inherits it」（**principle-the-baseline-is-a-contract**、**principle-silence-is-never-a-pass**）；「keep intact」清单（绑定票的 **What to build**、**Seam**，L7 C.2）；Owns 两档（**principle-separate-before-serializing-shared-state**）；「Before adding a file, a dependency or a configuration entry, write under **Decisions I made on my own** why the existing one is not enough.」（`implement` 第 26 行原文，这一句绑定 worker 的 closeout，所以留在这里）；「a dispatched worker never runs `design-pages`」（`design-pages` 第 21 行后半句）；通用写码规则见 `references/writing-code.md`。
  - `#### Decisions I made on my own`：第 23 行的写法（写给 reviewer 与早上的用户），也是本角色的无人出路。
  - `#### ABANDON kinds`：第 76 行。
  - `#### While the product runs`：指向 `ui-acceptance` `## Five rules while the product is running`（替代 `PRODUCT_RULES` 提示词）；产品起不来就开 `fault` 子票后停（`ui-acceptance` 第 38 行）。
  - `#### Memory while working`：何时开、何时存 → `shared-experience`。
  - `#### When the orchestrator resumes you`：照 `resume` 送来的那句话做，再跑 `where`，从它印出的步骤继续（来源：`night.md` 第 81、104 行关于 `resume` 的话）。
  - `#### After the closeout, picked up yourself`：被 `ticket.passed` 或 `ticket.returned` 唤醒时，`ack` 后告诉用户票已关、`dispatch.sh land <n>` 合并它并停掉 relay；不在本会话跑 `land`（`inside-a-ticket.md` `## After the closeout` 原文）。
- **唤醒**：每个（角色，事件）只有一个处理处，登记在 `roles.json`（第 7.1 节）：`reviewer.reported`、`reviewer.lost` → **Get reviewed**；orchestrator 的 `resume` 文字 → `#### When the orchestrator resumes you`；self-picked-worker 收到的 `ticket.passed`、`ticket.returned` → `#### After the closeout, picked up yourself`。
- **交付物**：`--closeout` 退出 0 的收尾评论，它就是 worker 的回复。
- **来源**：`implement/SKILL.md` 第 8–101 行；`inside-a-ticket.md`；`verify-ticket/references/sub-issues.md` 第 11 行里属于 worker 的部分；`tdd` 第 22、38 行；`resolving-merge-conflicts` 第 2 步的票语句；`ui-acceptance` 第 38 行（R14 T1–T5、T9、T13、T15、T28、T29）。

#### P16 Review a ticket（reviewer）

- **Entry**：启动提示词点名票与 base commit；Rules 包在数据文件里。
- **所有权**：取自 `code-review/SKILL.md` 第 8 行：「This review is the first reading by anyone who did not write it: what it reports, the worker fixes before the ticket closes; what it misses ships.」You own the one review report; verify every finding, fix none.（后一句出处：`session.md` 第 3、49 行。）
- **步骤**：
  1. **Pin the diff.** 失败直接写成报告后停（`session.md` `## 1`）。
  2. **Run the axes.** 每个 axis 一个通用子代理，同一条消息发出；有 story criterion 的票才跑 UI axis（H3：都跑在本会话模型上）。每个子代理的提示是一行：「Read `<数据文件给出的 review-axes/<axis>.md 绝对路径>` and review ticket #<n> from base commit <base>, axis <Axis>.」简报自足：Standards 简报保留自带的 smell baseline 全文（`standards-reviewer.md` 第 13–39 行）。依据：上游 `code-review` 原文第 63 行「plus the smell baseline from step 3 pasted in full (the sub-agent has no other access to it)」，同一份内容给两类读者，按 L7 C.2「规则的读者读不到原则，只给指针会失效」与 C.5 可以接受。axis 子代理只读，不加 `subagent-brief.md` 的首句，也不读 mode。
  3. **Verify every finding.** Holds、`refuted`、Could not tell（**principle-clues-are-not-evidence**；`session.md` `## 3`）。
  4. **Sort in-ticket and out-of-ticket.**（`session.md` `## 4` 的六类依据）
  5. **Write the report.** `ticket.py <n> --review <file>`，它唤醒 worker。
- **规则簇**：`#### Report format`（`session.md` 第 73–95 行，它就是交付物，L7 C.4）；`#### Active Rules`（同名节）；`#### Unattended outlets`：拿不准时在该条末尾写 `unverified: <what would settle it>`。
- **重入**：一次性会话；前四步不写任何东西，重跑没有副作用；丢失时 watchdog 写 `reviewer.lost`，worker 在 **Get reviewed** 另起一个。
- **交付物**：`REVIEW <base>..<HEAD>` 评论与 `reviewer.reported` 事件。**来源**：`code-review/references/session.md` 全文（101 行，本轮读全文）；`code-review` `## Find your moment`（R14 T10、T11）。

#### P17 Session pickup、P18 Pause safely（pstack 原文，B1 导入）

原文不改（本轮读全文）。在 MMW 里的解析：`session-pickup` 第 1 步的 `agent-transcripts/` 与 cloud-agent URL → `slots.md` 的 transcript 行（宿主的会话记录、`handoff` 文件、推上去的分支、tracker 事件；各宿主位置待 U-8）；它点名的 **principle-guard-the-context-window**、**principle-prove-it-works** B1 同批导入；第 4 步「Route the remaining work to the matching playbook」按 MMW 路由表。`pause-safely` 没有宿主依赖；第 4 步「If a show-me-your-work trail exists」在 B3 前不适用。绑票的会话不走 P17，走 mode `## Re-entry`。

#### 私有 playbook（本仓库 `.mmw/playbooks/`）

- **Promote a change**（`promote-a-change.md`）：1 **Commit on dev.** 2 **Fast-forward main.** `git push . dev:main` 3 **Move the installed checkout.** `git -C .worktrees/mmw-installed checkout --detach main`，然后 `bash mmw-v2/install.sh --check`；任何 watch 开着时等（H5）；`skills.txt`、hook 或启动器变了的，请用户授权完整 `install.sh`。4 **Push both.** `git push origin dev main`。来源：根 `AGENTS.md` `## Gotchas` 第 1 条原文四步。根 `AGENTS.md` 那一条改成一行指针加「The third step waits while any watch is open」。
- **Pull an upstream**：1 **Pull the subtree.**（命令见 `merge-notes/README.md`）2 **Resolve by the merge-notes.** 3 **For unlazy, read every listed diff and run its suite.**（`bash mmw-v2/tests/verify-ticket/run.sh`）4 **Refresh imported pstack files.**（只对 `upstream-pstack`：`import_component.py --refresh`，读它列出的差异）5 **Check.**（`install.sh --check`、`check_wiring.py`）6 **Deliver.** **Deliver a change**。来源：根 `AGENTS.md` `<important if … upstream …>`；`merge-notes/README.md`。
- **Import a component**：第 8.6 节。

---
## 4. 能力技能总目录

**采用的决定。** 能力技能只讲一件事怎么做、交回什么；「下一步」「谁调用我」「worker」「night」这类句子与流水线状态的读写全部离开。上游技能回到 squash `5b1a4c51` 原文，只允许两类改动（第 4.3 节）；调用开关由 `install.sh` 在安装副本里处理。`implement` 回原文并不再安装；`code-review` 回原文并安装；`to-spec`、`to-tickets` 分叉为 MMW 自有；`verify-ticket` 拆出 mode 的脚本；新拆出 `setup-mmw`、`shared-experience`；`dispatch` 解散。

**理由。** 能力技能离开 MMW 的流水线、在没有 `.mmw/` 的仓库里还能用，才能被 mode、playbook、子代理、以后导入的 pstack 组件按名复用（R13 E3；L7 B.2 硬规律 3 的推断理由「为了能力技能能脱离 mode 使用」）。`code-review` 今天要求提示词里有票号，通用评审能力因此没有装在任何地方（残留 `ask-matt` 第 28 行「`code-review` has no use on a branch or PR without a ticket」）。

**放弃的备选。**
- R16 D5：保留开关、靠模型按路径读 `SKILL.md`。它把 H2 的解法押在未实测的行为上（U-1）。
- R17：`implement` 回原文后保留安装。它的「full test suite once at the end」「use /code-review」与 `shared.md` 规则 15、`review-a-ticket` 冲突，装着还会与 worker 的入口抢触发（U-11）。
- 上一版本文：`verify-ticket` 整体「本层」、`own_session()` 找不到 `dispatch.sh` 时拒绝。它让能力脚本向上依赖 mode 的脚本，缺了还拒绝，与 E3 相反（第 7.6 节）。

### 4.1 MMW 自有能力技能

| 技能 | 升级后只剩什么（纯能力） | 剥离了什么 → 去哪里 |
|---|---|---|
| `setup-mmw`（新） | 改角色的 host、model、effort 与 runner；查一个角色当前的值；读 `install.sh --check` 的输出；开任务板。按命令点名 mode 的脚本（`mmw/scripts/models.py config show/set/runner/get`、`dispatch.sh board`），不持有文件 | 来源：`dispatch/references/editing-models.md`（27 行）、`dispatch/SKILL.md` 表第 5、6 行。pstack 先例：`setup-pstack` 按 mode 的角色标签写配置（L7 B.2 表「能力技能 → mode：少见」） |
| `shared-experience`（新） | Memory 记录的打开、按错误搜索、保存三条件、更正与 deprecate、四种关闭决定（`retain`、`propose`、`deprecate`、`supersede`）的写法；`references/saving-memory.md` | 来源：`implement` 第 36–68 行的方法部分；`night.md` 第 151–157 行的写法部分。「何时用」留在 P12、P15 |
| `verify-ticket` | 跑一张票的判据：`CHECK`/`EXPECT` 怎样读与跑（把 `ui-acceptance` 的 `scripts/` 放上 `PATH`）、gate-check；lint 票面与草稿；发布 spec 与票（`--publish`，本轮核实它不写事件）；`issue_tree.py`（读 spec → 票 → 子票的树）；子票五种 kind 及判别问题（`sub-issues.md` 第 13–23 行，`design-pages/references/pull.md` 也开 `contract` 子票，是第二个调用方）。跑判据只打印结果，不写事件 | 事件词表 `events.py` 与写票状态的命令（`--preflight`、判据运行后的 `ticket.checked` 与产品槽排队的 `worker.queued`、`--decisions`、`--review`、`--touched`、`--draft`、`--closeout`、`--sub-issue`、`fold`、`resume_at`）→ mode 的脚本 `mmw/scripts/ticket.py`、`events.py`（本轮核实：`events.py` 第 143–169 行定义 `worker.started`、`worker.retracted`、`worker.replaced`，`"stage": "dispatch"`，及 watchdog 写的 `*.lost`；`verify-ticket.py` 第 1372–2599 行 11 处 `post_event`）；`own_session()` → 删，`ticket.py` 与 `dispatch.sh` 同目录直接调 `self`；description 的时机半句 → P1、P12；第 16 行「A worker's claim … are steps of the `implement` skill」→ 删；`## Reached from here` → mode 触发行；`sub-issues.md` 第 11 行「谁在何时读」→ 各角色的唤醒行；`linting.md` 第 3 行「何时 lint」→ P1、P12；第 10 行理由 → 点名 **principle-the-tracker-is-the-state**。`--lint` 是否读事件由 B2 票核实，读的话那部分随 `ticket.py` 走（推断） |
| `ui-acceptance` | 全部规则与四个 oracle、五份 reference、九个脚本（含 `refusal.py`、`lease.py`）；接收 `writing-interface-code.md`（三处「closing step 1」改为按名引用） | description 末句「before writing a page ticket's code」→ 改为「before writing code for a page a screen-contract row covers」，流水线时机进 mode 触发行；第 38 行 → P15；第 10 行与规则 3–5 的理由 → 点名 **principle-silence-is-never-a-pass**、**principle-human-steps-stay-human**、**principle-route-faults-dont-bypass** 加本地一句 |
| `design-pages` | pull、draw、edit、design-system 四个分支，两份模板，两个脚本，`references/state-list-format.md`，第 21 行前半句的宿主闸门 | `edit-pages.md` `## Next`、`pull.md` `## Reached from here` 与 `## A contract child answered by this pull` → P3；第 21 行后半句 → P15；第 25 行按编号引用「`UI.md` step 6」→ 同技能内的 `state-list-format.md` |
| `write-screen-contract` | 第 1–7 步、`Re-runs`、格式文件、三个脚本 | `## Next` → P3、P1；第 8–10 行理由 → **principle-the-baseline-is-a-contract** |
| `retro` | 第 1–13 步；`## Prevention destinations`，`retro.py` `DESTINATIONS` 加 `principle`、`playbook`、`mode`（第 31–32 行现有 8 个）；`## Decide` 加 pstack synthesizer 的四条分拣规则（Existing-skill-first、Decision-changing、Structural-mechanism check、Already-covered，`reflect/references/synthesizer.md` 原文，R13 E11）；读事件格式时经 `anchors.py` 的路径加载 mode 的 `events.py`（脚本之间的导入，L7 B.2 表「脚本 → 脚本：导入」；`retro` 的对象就是 MMW 的一夜） | description「right after the dispatch skill's `summary` records `spec.closed`」→ P12 **Retro**；第 186 行 → 删；第 16–35 行立场 → **principle-clues-are-not-evidence**、pstack 三条 |
| `advisor` | 发起方怎样写 brief、怎样对待回答（`consulting.md`）；被咨询方怎样回答（`advising.md`，另起会话的简报，第 1.4 节）；`## When it is worth a session` | `consulting.md` `## Start it` 的「Run the `dispatch` skill's `dispatch.sh advise <file>`」→ 改成「start the advisor session your environment provides」，mode 触发行写 `dispatch.sh advise`（本轮读全文：这是它唯一点名流水线的一句） |
| `exe-release` | `SKILL.md` 第 1–5 步全部、`key.md`、`new-product.md`、`driving.md`、引擎脚本 | 无流程句要搬；`driving.md` 第 5 行「Do not resume from session memory」→ 点名 **principle-the-tracker-is-the-state** 加本地一句「the release engine's state」 |
| `code-checkers` | 探测、配置、git hook | 第 6、8 步在接入流程里的先后 → P9；第 5 步探针理由 → **principle-silence-is-never-a-pass** |
| `manage-agents-md` | 其余全部 | 第 50 行子代理默认 → mode `## Subagents` |
| `to-spec`（分叉） | 上游 75 行加 MMW 的 spec 能力（seam、状态可达、模板的 API contract、visual acceptance、Critical flows、Sources）、`revising-a-spec.md`（本轮读全文：怎样改一份已发布的 spec，是这项能力的做法）；第 2 步只留「有未对齐的行就停」这道闸门；「怎样判断一份参考该拆成几份 spec」一句 | description 触发句 → 路由表；`## Next` → 删；`several-specs.md` 的「写一份、停下、下次再跑」循环 → P1 **Split into several specs**；退回路线 → P3；第 6 行 → 点名 `shared.md` 规则 1，自己的闸门保留（L7 A.3） |
| `to-tickets`（分叉） | 切片、五问、四行判据、blocking edges、Owns、`<issue-template>`（标题登记进 `anchors.py`，W4）、三份 reference | 第 20、160 行 → P1；第 113–119 行子代理段 → mode `## Subagents`；第 84、88 行理由 → 点名原则，已写的本地理由保留（R12 M25） |
| `dispatch` | — 解散 | description 与 `## Find your moment` → 路由表、`roles.json`、`setup-mmw`；`## On waking` → mode `## Re-entry`；`night.md` → P12、P13、`orchestrator-events.md`；`one-ticket.md` → P14；`inside-a-ticket.md` → P15；`editing-models.md` → `setup-mmw`；第 8 行前半句 → **principle-the-tracker-is-the-state**；`hosts.json`、`scripts/` → `mmw/` |

**为什么 `to-spec`、`to-tickets` 分叉而不是回原文**：它们的正文多数是 MMW 的能力，不是流程（`merge-notes/to-spec.md` 第 31 行自认「不到一半的行是上游的」，R4 V11；`merge-notes/README.md` 把 `to-tickets` 列为本仓自有正文的技能）。留在上游目录，每次拉上游都在这些段落冲突（R12 M5）。分叉后上游目录回原文、不安装（`install.sh` 第 163–164 行拒绝重名）。

### 4.2 上游（mattpocock）能力技能

「开关」一列：「模型」＝上游原文就模型可调用；「+model」＝上游带开关，被 mode 或 playbook 点名，`skills.txt` 该行加 `+model`，安装副本去掉开关（第 4.3 节）；「用户」＝保持上游开关，点名它的地方写「告诉用户运行 /x」。

| 技能 | 升级后 | 撤回的本仓改动 → 去处 | 保留的改动与类别 | 开关 |
|---|---|---|---|---|
| `implement` | 回原文 15 行，**不安装** | 全部 → P15、`writing-code.md`、`ui-acceptance`、`shared-experience` | 无 | 不装 |
| `code-review` | 回原文 87 行双轴评审，安装 | `## Find your moment`、`session.md` → P16；四个 axis → `mmw/references/review-axes/`；第 8 行 → **principle-a-second-reader-judges** | 无 | 模型 |
| `tdd` | 回原文 | 第 22、38 行票语句 → P15；「The agreement is something written down」一并撤回 | 「call the Skill tool」→ 读 `codebase-design` 的 `SKILL.md`：宿主中立（H1，本轮 `git diff` 核实） | 模型 |
| `grilling` | 回原文 | 第 28 行 → mode `## Autonomy`、`shared.md` 规则 1；第 30–44 行 → **principle-attack-the-premise**、**principle-redesign-from-first-principles**、**principle-fix-root-causes**、**principle-subtract-before-you-add**、**principle-laziness-protocol** | 无 | 模型 |
| `grill-with-docs` | 回原文 | 第 7 行末句 → P1 | 「Call the Skill tool」改为读 `SKILL.md`：宿主中立（H1） | 用户（P1 写「用户输入 /grill-with-docs」） |
| `triage` | 回原文 | description 触发句 → 路由表；第 70、90 行与 `pipeline-issues.md` → P13；第 82、94 行 → P7；`AGENT-BRIEF.md` 的定位句 → P7 | 无 | +model（上游带开关，P7 点名） |
| `wayfinder` | 回原文 | 第 6 步 → P2；`interface-and-remake.md` → `mmw/references/`；`mmw:map` 字面 → `docs/agents/issue-tracker.md` `## Three label sets` | 宿主中立的子代理措辞（H1） | +model（P2 点名） |
| `to-questionnaire` | 回原文 | description 触发句 → 路由表；「you」改「the user」一并撤回 | 无 | +model（P1 点名） |
| `prototype` | 回原文 + 能力改动 | 规则 6 的「之后做什么」、`UI.md` 第 3 步交接与 `## Next` → P4、P3；`## State list` 格式 → `design-pages/references/state-list-format.md`（W6） | EXP 分支（`EXP.md`、`evidence-page.md`）、`prototypes/<effort>/<issue>/` 叶目录与叶 `README.md`、「keep the prototype」：本轮读 `git diff`（5 个文件 +166/−23），都在改「原型怎样做、放哪、留不留」，能力改动 | 模型 |
| `improve-codebase-architecture` | 回原文 + 能力改动 | `### 4. Hand the decision on` → 路由行与 P1 入口 | `HTML-REPORT.md` 改用 `diagram-design` 画图（2 个文件 +36/−86）：能力改动 | 用户（路由行写「告诉用户运行」） |
| `resolving-merge-conflicts` | 回原文 + 能力改动 | 第 2 步「After a clean merge of `origin/<base branch>`, identify each ticket …」→ P15 | description 与第 1、3 步的「干净合并后检查变红」：能力改动 | 模型 |
| `codebase-design` | 回原文 + 能力改动 | 第 10 行「the task that brought you here decides what you do next」→ 删 | 第 16 行术语规则：能力改动 | 模型 |
| `setup-matt-pocock-skills` | 回原文 + 能力改动 | 「In this toolbox the tracker is also the landing pipeline's store …」「The night's scripts and the ticket skills write the default label strings verbatim … keep the defaults」、种子里的 `## Three label sets` 与第 17、51、63 行 → P9 与 `mmw/references/tracker-additions.md` | 写 `AGENTS.md` `## External References` 行而不是 `## Agent skills` 块、`CLAUDE.md` 只留 `@AGENTS.md`、「Every list read is a whole list」与 `--limit`/`--paginate`、已有文件只改本次答案改动的部分：本轮读 `git diff`（6 个文件 +55/−42），能力改动 | +model（P9 第 1 步由模型运行） |
| `writing-for-agents` | 回原文 | 第 8 行 → 删；`SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` → `mmw/references/`（随 mode 安装，P11 在任何仓库都读得到） | description 放宽为「any document an agent will consume」 | 模型 |
| `diagnosing-bugs`、`domain-modeling`、`research` | 就位（与上游零差异） | — | — | 模型 |
| `handoff`、`grill-me` | 就位 | 无流程句 | 「call the Skill tool」改掉：宿主中立（H1，本轮 `git diff`：各 1 行） | +model（mode 触发行、路由行点名） |
| `teach` | 就位 | 无流程句 | 工作区位置、`GLOSSARY.md`、经本地 HTTP 交付、自包含页面：本轮读 `git diff`（+11/−4），能力改动 | +model（路由行点名） |
| `wait-what` | 就位 | 无流程句 | `visual` 参数与 `VISUAL.md`：本轮读 `git diff`（3 个文件 +22/−1），能力改动 | +model（mode 触发行点名） |
| `wizard` | 就位 | 无流程句 | 点击路径写目的、bash 3.2 的 `${NAME}`：本轮读 `git diff`（+5/−5），能力改动 | 模型 |
| 残留 `ask-matt`（不安装） | 回原文 | 主流程 → P1、P4、P5；on-ramps → P2、P6、P7；`### Context hygiene` → P1；`## Phase boundaries` 与 `PHASE-BOUNDARIES.md` → **principle-decide-at-phase-boundaries** | — | — |
| `diagram-design`（第二个上游） | 就位 | — | merge-note 已有 | 模型 |

### 4.3 上游目录今后只允许两类改动；调用开关在安装时处理

写进 `merge-notes/README.md`，由连线检查第 3 类的「上游差异」一项核对：

1. **宿主中立**（H1）：上游写死 Claude Code 专有工具的句子（例如「call the Skill tool」）。
2. **能力改动**：改变这项能力本身怎么做，带 merge-note。本轮对上表每个「能力改动」都读了 `git diff`。

**调用开关（H2）不在子树里改。** `skills.txt` 的行尾标记 `+model` 表示「这个技能被 mode 或 playbook 点名，要模型可调用」。`install.sh` 对带标记的技能生成安装副本 `~/.mmw/skills/<name>/`：`SKILL.md` 是源文件去掉 `disable-model-invocation` 一行后的拷贝，`agents/openai.yaml` 按同一标记生成（不写 `policy`），其余文件软链回源目录；宿主的技能软链指向这个副本。`install.sh --check` 比对副本与源文件，源文件变了就报「副本过期」。这样 mattpocock 与 pstack 两个子树都保持原文，拉上游不会在开关行冲突；代价是带标记技能的 `SKILL.md` 改动要重跑 `install.sh` 才生效（其余文件照旧即改即生效），而上游 `SKILL.md` 只随子树拉取改变，拉取后本来就要跑 `--check`。宿主能否读取「真目录里放软链文件」的技能目录，并入 U-3 实测。连线检查第 9 类核对：被点名、要模型调用的技能都带 `+model`；带 `+model` 的副本里没有开关、`openai.yaml` 没有 `policy`。

流程句、原则句、配置字面都不进上游文本。

### 4.4 新拆出的内容

| 新位置 | 来源 | 为什么在这一层 |
|---|---|---|
| `mmw/references/writing-code.md` | `implement` 第 24–25 行两句的具体动作原样保留：「Before changing a function, grep every caller and fix the shared code once; when what you add supersedes an existing branch, guard or file, delete it in the same commit.」「Before writing a helper, search the repository and **Read first** for one that already exists.」（去掉 **Read first** 这个票的字眼，改为「and the files the task points at」）；每句后按第 5.4 节第 1 条加点名：前一句 **principle-subtract-before-you-add**，后一句 `shared.md` 规则 14 | P5、P15 两份 playbook 共用；不产出交付物，不是能力技能（L7 C.1 第 6 问）。第 26 行「write under **Decisions I made on my own**」绑定 worker 的 closeout，留在 P15 `#### While writing code`；P5 把同样的理由写在 Reply 里 |
| `ui-acceptance/references/writing-interface-code.md` | `implement/references/` | 按设计基准写界面的方法，属于持有 oracle 的能力；消掉 N10 B7 的来回跳转 |
| `design-pages/references/state-list-format.md` | `prototype/UI.md` 第 6 步 | `pull_design.py` 第 983 行按字面读它（R12 M21）；格式归读写双方里的能力一侧 |
| `mmw/scripts/ticket.py`、`events.py` | `verify-ticket.py` 的状态命令、`verify-ticket/scripts/events.py` | 流水线状态的读写（L7 A.6 情形 1「多个写者共享、需要跨会话存活的状态」），属于 mode 的脚本 |
| `shared-experience`、`setup-mmw` | 见 4.1 | 可以单独调用的能力 |

### 4.5 共同规则

- 以交付物结尾（pstack 的 `## Output Format`、`**Reply:**`，L7 A.3），不写「下一步」。
- 不出现「下一步」「谁调用我」两种句型：`## Next`、`## Reached from here`、「return to」后接技能名、任何 playbook slug、按编号引用别的文件里的步骤。角色名作为领域词可以出现（连线检查第 3 类，R17 第 7.4 节的判法）。
- 自带的人工闸门保留（L7 A.3）；无人会话里怎样处理见 mode `## Autonomy`。
- 能力技能的脚本不调用 mode 的命令（L7 B.2 硬规律 3 的推断理由：能力技能要能脱离 mode 使用）。唯一允许的跨目录引用是按 `anchors.py` 的路径导入 mode 持有的数据格式模块 `events.py`，只读（`retro.py`；任务板 `board/` 不是技能，同样经 `anchors.py`）。L7 B.2 表里「脚本 → 脚本」一格是「导入、测试」，硬规律 2「脚本不往上调用任何东西」管的是脚本调用文字层；上一版本文把 L7 B.2 引成「pstack 只禁止能力技能依赖 playbook」，漏了这一条，已改正。

---

## 5. 原则层

**采用的决定。** 原则是 `mmw/principles/principle-<slug>.md` 普通文件，格式与 pstack 原则相同。B1 建 26 条：MMW 自有 12 条，pstack 原文 14 条；B3 导入 pstack 其余 9 条，pstack 23 条全部落位。mode `## Principles` 是索引，由连线检查与原则文件的 `description` 核对。

**理由。** H2：pstack 的 23 条原则全带 `disable-model-invocation: true`（本轮对 `skills/principle-*` 逐一 grep：23 个文件，各 1 处），装成技能在 Claude Code 上按名调不到；装成模型可调用的技能，又会让二十多条 description 进每个会话的技能列表，与「只被点名、不被调用」相反（R13 E5）。门槛是 L7 A.4 的四条（短名；可观察的触发情境；能改变一个具体决定；跨任务），与「现在有几处引用」无关，所以不采用 R12 的「只建 2 条」。

**放弃的备选。** R16 保留导入原则 frontmatter 里的开关键（文件不是技能，这个键没有作用）；改为导入脚本机械删掉这一行，记在 `imports.tsv`。原则是复制进 `mmw/` 的文件，删行发生在复制出的文件上，子树原文不动。

### 5.1 存放、格式与引用（H2）

- **位置**：`mmw-v2/skills/mmw/principles/principle-<slug>.md`。文件名不是 `SKILL.md`，宿主扫描技能时不会把它当嵌套技能（U-3 探针核实）。
- **格式**：frontmatter 只有 `name: principle-<slug>` 与 `description: "Apply when … . <规则摘要>."`；正文 `# <Title>`、一到三句规则、`**Why:**`、`**Pattern:**`，可选 `**Boundaries:**`、`**Stop:**`、`**The test:**`、「Distinct from …」（L7 A.4）。
- **MMW 自有原则的写法约束**：规则与理由逐字取自下表「出处」列的原文；原文没有理由的不写 `**Why:**`（pstack 23 条里也只有 16 条有，L7 A.4）；出处（ADR 号、行号）写进 ADR 0032，不进原则文件（R12 K-19）。
- **引用**：MMW 自写的文字只用 `**principle-<slug>**`；导入的文字保留原样，由 mode 的解析规则接受；原则之间的相对链接 `../principle-x/SKILL.md` 由导入脚本机械改成 `principle-x.md`（`principle-build-the-lever` 3 处、`principle-attack-the-premise` 4 处，本轮 grep）。
- **读取**：mode 索引每个任务读；应用哪条读哪条全文；回复（无人时写在交付物里）点名改变了决定的那条。
- **方向**：原则只指向原则或能力技能，不指向 playbook、脚本、mode（L7 B.2 硬规律 1）。
- **调用方**：点名一次，加一句本地限定或本地后果（L7 C.2），不复述原则正文。上游技能正文不加引用，因为上游回到原文。

### 5.2 MMW 自有原则（12 条，索引组 Pipeline）

| slug | 规则（归并自现有原文） | 理由出处 | 被谁点名 | 吸收的 R14 编号 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 一道检查跑了却什么都没做、或绿灯可能来自产品正确之外的原因，就是失败；查不了就说查不了；检查红了改产品或开子票质疑来源，不弯 baseline、harness、测试；新建的检查先证明它会失败（negative control） | ADR 0008 第 8 行；`implement` 第 22 行末两句；`night.md` 第 7、127 行；`ui-acceptance` 第 10 行；`to-tickets` 第 84 行 | P1、P12、P15；`ui-acceptance`；`code-checkers`；`retro`；`CODING_STANDARDS.md` | PC1、PC2、PC22 |
| `the-tracker-is-the-state` | 你在哪一步由持久记录（票上的事件、tracker、提交、引擎状态）决定，会话记忆是会丢的副本；续跑读记录，不重做已做的 | `dispatch/SKILL.md` 第 8 行；`verify-ticket/SKILL.md` 第 10 行；`exe-release/references/driving.md` 第 5 行；ADR 0019 | mode `## Re-entry`；P1、P12、P15 的 `**Where you are.**`；`verify-ticket`；`exe-release` | PC5 |
| `woken-not-polled` | 谁都不轮询另一个 agent；起了别人就结束回合，由事件叫醒 | ADR 0010；`night.md` 第 11 行；`implement` 第 78、84 行；`one-ticket.md` 第 8 行 | P12、P14、P15 | PC4 |
| `route-faults-dont-bypass` | 拒绝、产品连不上、流水线自身故障，按流水线给的路由上报，不绕路、不写重试循环、不换 host 或 runner。`**Boundaries:**` 写与 `shared.md` 规则 11 的划界（第 2.2 节） | `dispatch/SKILL.md` 第 25 行；ADR 0010、0017、0018；`ui-acceptance` 规则 4、5；`implement` 第 18 行 | mode Non-negotiables 流水线故障行；P12 `fault` 行；P15 **Claim** | PC18 |
| `the-baseline-is-a-contract` | 基准（用户的回答、胜出的原型、签字的页面）是别人已经付过代价的决定；照抄，不凭记忆重写、不改进；不成立就开 `contract` 子票公开重开 | `implement` 第 22 行「A baseline is a decision someone already paid for …」 | P1、P3、P12 `#### Contract children`、P15；`design-pages` 第 10 行；`write-screen-contract` 第 18 行；`to-tickets` 第 174 行 | PC8 |
| `refusals-name-one-next-step` | 读拒绝的一侧：拒绝点名一个事实、说为什么、给唯一下一步；收到拒绝照那一步做，不即兴（写脚本的一侧留在 `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条） | ADR 0008；`SKILL-SET-RULES.md` 第 12、59 行；`night.md` 第 66 行 | mode Non-negotiables；P12 **Handle each wake**；`ui-acceptance` 第 26、35 行 | PC3 |
| `a-second-reader-judges` | 对一件工作的判断交给一个没写它的读者（另一个上下文或会话） | `code-review/SKILL.md` 第 8 行；`to-tickets` 第 63 行；`tdd` 第 38 行「judged with fresh eyes」；`consulting.md` 第 9、37 行 | P1 **Cut the tickets**、P5、P15 **Get reviewed**、P16；`advisor` | PC20 |
| `clues-are-not-evidence` | Memory、顾问的话、别人的报告、axis 的 finding 都是线索；行动前对当前仓库、tracker 与运行结果核实 | `implement` 第 47–49 行；`session.md` 第 89、101 行；`retro` 第 58、63–66 行；`advising.md` 第 15 行；`research` 第 10 行 | P8、P16 **Verify every finding**；`shared-experience`；`retro` | PC11 |
| `one-home-per-meaning` | 一个意思只有一个权威的家，别处按名指向它 | `writing-for-agents` 第 78 行；`SKILL-SET-RULES.md` 第 17、40 行；`design-pages` 第 6 行；`editing-models.md` 第 3 行 | P11、Import a component；`references/skill-set-rules.md`；连线检查的依据 | PC16 |
| `human-steps-stay-human` | 只有人能做的一步单列交给人，agent 不代做，也不报告成做了 | `ui-acceptance` 规则 3；`person-ticket.md` 第 3 行；`wizard` description；`exe-release` 第 5 步 | mode 触发行；P13；`exe-release` | PC29 |
| `no-secrets-in-artifacts` | 凭据与个人数据不进任何产物（票、Memory、handoff、日志、spec） | `diagnosing-bugs` `## Redact`；`saving-memory.md` 第 4–5 行；`handoff` 第 14 行；`product-answers.md` 第 96 行；根 `AGENTS.md` `## Gotchas` 末条 | mode Non-negotiables；`shared-experience`；P6、P17、P18 | PC28 |
| `decide-at-phase-boundaries` | 一个阶段结束时，在继续、清空、压缩、交接、派子代理五个选项里按判断树选一个 | 残留 `ask-matt/PHASE-BOUNDARIES.md` 的五个选项与判断树（上游原文，来源记在 `imports.tsv`） | mode 触发行；P1 `#### Session boundaries`；P3 | ask-matt `### Context hygiene` |

「被打断的命令原样重跑」不单独成原则：它是 mode `## Re-entry` 第 1 步的操作文字，点名 **principle-make-operations-idempotent**（R14 PC17 的设计一侧由这条 pstack 原则接住，使用一侧就是那一步）。

### 5.3 pstack 原则（23 条全部导入）

| pstack 原则 | 批 | 接住的 MMW 规则 | MMW 调用方留下什么 |
|---|---|---|---|
| `prove-it-works` | B1 | PC1 的「真物验证」、PC11、PC14 的「引用看到的那一行」 | P6、P15 **Audit against the ticket**、P17；本地一句「在票里，真物就是判据在 `HEAD` 上的运行」 |
| `fix-root-causes` | B1 | PC19 一部分 | P6；`retro` |
| `attack-the-premise`、`redesign-from-first-principles` | B1 | PC19（`grilling` 第 30–44 行、`retro` 第 30–35 行） | P1 **Interview**、P6、mode 触发行 |
| `laziness-protocol`、`subtract-before-you-add`、`migrate-callers-then-delete-legacy-apis` | B1 | PC21、PC24 一部分 | `references/writing-code.md`；Standards 简报 |
| `test-behavior-not-implementation` | B1 | PC23；PC2 的 negative control 一句 | P5、P15 **Write the code**；做法留在 `tdd` |
| `separate-before-serializing-shared-state` | B1 | PC12 | P12 `#### Closing pass`、P15 `#### While writing code`；`to-tickets` 保留 Owns 与 blocking edges 的领域规则 |
| `make-operations-idempotent` | B1 | PC17 | `CODING_STANDARDS.md` 一条；mode `## Re-entry` 第 1 步 |
| `encode-lessons-in-structure`、`build-the-lever` | B1 | PC25、PC7、PC6 一部分 | P11；`retro` `## Decide`；`CODING_STANDARDS.md` |
| `guard-the-context-window` | B1 | PC26 | mode `## Subagents`；P17 |
| `never-block-on-the-human` | B1 | PC9 的执行一侧 | mode `## Autonomy` |
| `sequence-verifiable-units` | B3 | — | 导入的 `bug-fix`、`feature`、`refactoring`、`perf-issue`；票里的「rebase」由 mode 触发行与 `slots.md` 解释为 `dispatch.sh integrate` |
| `model-the-domain`、`foundational-thinking`、`exhaust-the-design-space`、`outcome-oriented-execution`、`minimize-reader-load` | B3 | — | 导入的 `feature`、`refactoring`、`architect`、`figure-it-out` 点名 |
| `boundary-discipline`、`type-system-discipline` | B3 | — | 导入的 `typescript-best-practices` 点名；索引 Architecture 组 |
| `experience-first` | B3 | — | 索引 Core 组；mode `## Autonomy` 的产品限定句（它决定你给用户的建议，不替用户做产品取舍；`shared.md` 规则 1。判断改动 J6） |

**不建成原则的候选**（逐条去处）：PC6 → mode Non-negotiables 第一行，hook 强制（绑定机制，L7 C.2）；PC9 → `shared.md` 规则 1 加 mode `## Autonomy`；PC10 → `shared.md` 规则 10；PC13 → 规则 13；PC14 → 规则 15；PC15 → mode `## Subagents`（绑定 ADR 0015）；PC24 → 规则 1「Anything outside the scope I gave you is asked about, not done」加 `laziness-protocol`；PC25 的「两次独立发生」门槛 → 留在 `retro`（领域参数，L7 C.2）；PC27 → `shared.md` 规则 6、8。

### 5.4 与 MMW 已有规则重合时怎么办

按 pstack `reflect/references/synthesizer.md` 的四条（Existing-skill-first、Decision-changing、Structural-mechanism check、Already-covered）落成五条操作规则：

1. **同义**：用 pstack 原文；MMW 各处的复述换成「点名 + 一句本地后果」，不整句替换掉具体动作。例：PC12 → `separate-before-serializing-shared-state`，`implement` 第 28 行只留「one file has one writer at a time and the cut missed an edge」。
2. **部分覆盖**：两个都留，MMW 原则写「Distinct from」。例：`silence-is-never-a-pass`「Distinct from **principle-prove-it-works**, which says how to verify; this says what to report when a check did not run or did nothing.」
3. **冲突**：导入原文，冲突由 mode `## Autonomy` 或所服务 playbook 的限定句解决，不改原则原文。
4. **与 `shared.md` 同义**：MMW 自己不建原则，调用方点名规则号；pstack 的同义原则照样导入，冲突时 `shared.md` 高。
5. **能由 lint、脚本或 hook 低成本强制的**：不写成原则文字，转进 `CODING_STANDARDS.md` 或 `check_wiring.py`。

### 5.5 与 `mmw-v2/prompt/shared.md` 的关系（S）

- `shared.md` 是用户写给所有项目的全局规则，经 `install.sh` 发给 Claude Code、Codex、Pi、Grok；Cursor 的用户级提示词在应用里维护（根 `AGENTS.md` `## Key Conventions`）。MMW 不改写它。
- **划界**：`shared.md` 管「谁决定什么、怎么汇报、怎么工作」；mode 管 MMW 独有的触发、无人会话的出路、重入；原则层管跨任务的工程判断。
- **引用**：mode 索引的「User rules」段只写规则号与适用时机；技能里今天的翻版（R14 第 5.5 节；N9 D1、D4、D5、D6、D16、D17）改成点名规则号。
- **优先级**：`shared.md` 最高。给用户的回复与导入的 pstack 写作规则冲突时（例：pstack「No long-dash character anywhere」，`shared.md` 自己用 em dash），以 `shared.md` 为准。
- **唯一的复制**：mode `## Autonomy` 抄一次产品事项清单（H1：Cursor 收不到 `shared.md`）。

---

## 6. 执行协议

**采用的决定。** 人在场：照抄 pstack 的执行协议。无人：`skip:` 行与点名原则写进本 playbook 的交付物；位置由脚本从事件算。`--closeout` 加一项核对：P15 的每个 `#### Steps` 标题要么在事件里有痕迹、要么有 `skip:` 行；B2 只报告，B3 起不通过就拒绝。

**理由。** 模型最常见的失败是自己排顺序、悄悄漏步（pstack `docs/guide/02-poteto-mode.md` Pitfall）；「跳过」变成可见的决定，与 ADR 0008「它跑了一遍却什么都没做，有人会发现吗」是同一个问题。H6 下待办屏幕没人看，压缩后待办可能丢，早上的读者读的是票。上一版把核对推迟的依据是 `SKILL-SET-RULES.md` 的「加机制要指名它会阻止的那次失败」：这是可以重新审视的旧规则，不是 H1–H6；而它要的那次失败本来就能指名——无人会话漏掉 **Audit against the ticket** 或 **Tell the touched tickets**，今天没有任何痕迹。

**人在场的会话。** mode `## Playbooks` 首段照抄 pstack mode 第 117 行：「Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to a playbook below, open its file, and copy its steps in verbatim.」只有编号步骤（长 playbook 是 `#### Steps` 下的）进待办，规则簇与模板不进（L7 D.1）。`feature.md` 式的 `n/a: <reason>` 与「Mandatory: no skip-with-reason escape」照原文保留。宿主没有待办工具时（U-4），在回复开头列出步骤标题与 skip 行。

**无人的会话（H6）。**

| 角色 | `skip:` 行与原则点名写在哪 | 依据 |
|---|---|---|
| worker | closeout 的 `## Decisions I made on my own`，每行 `skip: <步骤标题>: <reason>`，原则名写进决定行 | `implement` 第 23 行；`--closeout` 已做格式检查（是否接受这种行见 U-12） |
| reviewer | `REVIEW` 报告末尾 | `session.md` 第 73–95 行的报告格式 |
| orchestrator | spec 上的一条评论 | `night.md` 第 5 行「leaves its reason where that reader will look」 |

票上的事件就是 pstack `show-me-your-work` 的等价物，只写一处（R13 E7）。**`--closeout` 的步骤核对**：第 7.7 节的「事件 → 步骤」表给出每个有事件的步骤该留下的事件；没有事件的步骤（**Read yourself in**、**Write the code**、**Audit against the ticket**、**Draft the closing comment**）由收尾评论里的对应段落作痕迹（`--closeout` 已检查的 `Evidence`、`Outside Owns:` 等段；`--touched` 在别的票上留 `worker.touched`）；两者都没有、也没有 `skip:` 行的步骤，B2 在收尾评论下列出，B3 起拒绝 closeout 并点名缺哪一步。

---
## 7. 脚本与 hook

**采用的决定。** 流水线脚本整目录进 `mmw/scripts/`，hook 平放；票状态的命令与事件词表进 `mmw/scripts/`；角色与（角色，事件）的唤醒步骤登记在 `roles.json`，文字锚点与跨目录路径登记在 `anchors.py`；「现在在哪一步」由 `dispatch.sh where` 从事件算，输出区分「在某步」「在两步之间」「全新」「无法判定」；hook 经 `~/.mmw/bin/mmw-hook` 启动器调用，失败行为按 hook 分别定；连线检查按类别分批转为失败。

**放弃的备选。** R16、R17 把 `resume_at` 留在 `verify-ticket.py`：能力脚本仍然知道 worker 的步骤。R17「回退不需要重装」：B1、B2 改了 `skills.txt`，回退必须重跑 `install.sh`。上一版本文：启动器找不到目标时一律退出 2；hook 放进 `hooks/` 子目录；`models.py` 进 `setup-mmw`（第 1 节）。

### 7.1 `mmw/roles.json`：角色定义层

```json
{
  "worker":              {"playbook": "work-a-ticket",   "models_row": ["junior-worker", "senior-worker"],
                          "started_by": "dispatch.sh start <n> worker",
                          "wakes": {"reviewer.reported": "Get reviewed", "reviewer.lost": "Get reviewed",
                                    "resume": "When the orchestrator resumes you"}},
  "self-picked-worker":  {"playbook": "work-a-ticket",   "started_by": "dispatch.sh adopt <n>",
                          "wakes": {"reviewer.reported": "Get reviewed", "reviewer.lost": "Get reviewed",
                                    "ticket.passed": "After the closeout, picked up yourself",
                                    "ticket.returned": "After the closeout, picked up yourself"}},
  "reviewer":            {"playbook": "review-a-ticket", "models_row": ["reviewer"],
                          "started_by": "dispatch.sh start <n> reviewer", "wakes": {}},
  "night-orchestrator":  {"playbook": "run-a-night",     "started_by": "dispatch.sh open <spec>",
                          "wakes": {"*": "Handle each wake"}},
  "ticket-orchestrator": {"playbook": "run-one-ticket",  "started_by": "dispatch.sh open-ticket <n>",
                          "wakes": {"*": "Handle each wake"}},
  "advisor":             {"skill": "advisor", "brief": "references/advising.md", "models_row": ["advisor"],
                          "started_by": "dispatch.sh advise <file>", "wakes": {}}
}
```

- 「`*`」＝发给这个角色的所有唤醒：relay 的 `WAKES` 里 `to: MAIN` 的事件（`ticket.passed`、`ticket.returned`、`ticket.refused`、`child.opened`、`worker.lost`，`relay.py` 第 291–299 行，本轮核实）、`relay.recovered`、八种 `watchdog:` 告警、`MMW turn guard:` 行。
- **收件角色怎样定**：relay、watchdog、turn guard 按 watch 的 `kind` 取角色，不按 watch 所属的 playbook 取。`watches.json` 的每个 watch 新增 `kind` 字段，由开它的命令写：`open` → `night`，`open-ticket` → `ticket`，`adopt` → `adopt`。`kind: adopt` 的 watch 里 relay 以 MAIN 身份叫醒的就是 worker 自己（`inside-a-ticket.md` `## After the closeout`「where `adopt` started a relay with you as the session it wakes」），角色取 `self-picked-worker`。`to: WORKER` 的事件按票上 `worker.started` 的 `adopted` 字段（`dispatch.sh` 第 1017 行 `--json-field adopted=true`）区分 `worker` 与 `self-picked-worker`。单票 orchestrator 收到的 watchdog 告警因此指向 `run-one-ticket#Handle each wake`，不再被送进夜的 playbook。
- `resume` 不是事件：`dispatch.sh resume` 把 orchestrator 的那句话原样送进去，末尾接 `· mmw work-a-ticket#When the orchestrator resumes you`。
- 读者：`dispatch.sh`（启动提示词、`where`、`resume`）、`relay.py`、`watchdog.py`、`turn-guard.py`、`check_wiring.py`。它们都在 `mmw/` 里，读同一技能目录下的数据；从已安装 checkout 读，watch 期间冻结（H5）。缺失即安装残缺，读它的脚本拒绝并指向 `install.sh --check`（ADR 0008）。这落实了用户在 Memory 里定下的「agent 定义（读哪个 playbook + models.json 一行）」方向（R17 第 1.1 节引 Memory `8ec53374`）。

### 7.2 `mmw/scripts/anchors.py`：文字锚点与跨目录路径的唯一登记处

不导入任何模块（R12 K-2）。登记：
- playbook 文件名与步骤标题（例 `WORK_GET_REVIEWED = ("work-a-ticket", "Get reviewed")`）、mode 小节名（`## Re-entry`、`## Autonomy`）、`## Five rules while the product is running`；
- 启动提示词数据文件里的小节指针：`shared-experience` 的 `SKILL.md`、`review-a-ticket#Active Rules`（替代 `dispatch.sh` 第 1741 行「the implement skill's `## Shared experience while implementing` says how to use them」与第 1747–1751 行「code-review skill's `references/session.md` under `## Active Rules`」这两处 Python f-string 里的字面）；
- 票模板标题（`## Parent`、`## Owns`、`## Read first`、`## Seam`、`## Acceptance criteria`，W4）、`## State list`（W6）、`EXPECT` 成功标记（`STORY OK`、`BOUNDARY OK`、`JOURNEY OK`、`HARNESS OK`，W5）；
- 跨技能目录的路径：`EVENTS_PY`、`UI_ACCEPTANCE_SCRIPTS`（`tool-guard.py` 的 `refusal.py`）、`VERIFY_TICKET_PY`、`ISSUE_TREE_PY`，以及 `board/`、`retro.py`、`install.sh`、`migrations/` 用到的 `mmw/scripts` 路径。

「脚本按字面点名文字或别的技能目录」从此只有这一处；连线检查核对每个锚点在目标文件里存在。

### 7.3 hook 启动器 `mmw-hook`

- **问题（已核实）**：`~/.claude/settings.json` 第 43、53、85 行的 hook 命令写死 `~/.agents/skills/dispatch/scripts/tool-guard.py`、`turn-guard.py`。移动已安装 checkout 之后、`install.sh` 跑完之前，这些文件不在，`python3` 以 exit 2 退出，Claude Code 把 PreToolUse 的 exit 2 当作拦截，本机每个会话的每条命令都会被拦。反方向的失效同样存在：两个 hook 在模块顶层导入同伴（`tool-guard.py` 第 62 行 `from refusal import refusal`，`turn-guard.py` 第 139 行 `import statedir`），导入失败时 Python 退出 1，Claude Code 把 exit 1 当作不拦截的错误，拦截就被静默关掉（推断，依据 Claude Code 对 exit 1 与 exit 2 的区分；`turn-guard.py` 第 330 行注释「an import's SystemExit(2) must not block」说明作者已按这一区分处理 `main` 内的导入）。
- **做法**：B0 由 `install.sh` 把 `mmw-v2/mmw-hook.py` 复制成 `~/.mmw/bin/mmw-hook`（复制，不是软链），五个宿主的 hook 命令改成 `exec python3 ~/.mmw/bin/mmw-hook <tool-guard|turn-guard|mode-hook> <args>`；Claude Code 的命令保留今天的前缀 `[ -z "${GROK_AGENT:-}${GROK_HOOK_EVENT:-}" ] || exit 0;`（第 43、53、85 行现有）。启动器读 `~/.mmw/installed-root`，按候选相对路径依次找目标：`mmw-v2/skills/mmw/scripts/<name>.py`，再找 `mmw-v2/skills/dispatch/scripts/<name>.py`（B3 删掉第二个候选）。
- **找不到目标时，按 hook 分别处理**：

  | hook | 事件 | 行为 | 理由 |
  |---|---|---|---|
  | `mode-hook` | 会话开始、子代理开始、prompt 提交 | 不输出，退出 0 | 辅助路径（第 2.3 节）；在 `UserPromptSubmit` 上退出 2 会拦掉用户的提示词 |
  | `turn-guard` | Stop | 往 stderr 打印一行「MMW hook turn-guard not found under <root>: run bash mmw-v2/install.sh --check」，退出 0 | Stop 上的 exit 2 让会话无法结束回合，会重现全机故障；放行的代价是这段时间 watchdog 不健康不被提醒 |
  | `tool-guard` | pretool、question | 启动器自己按 `tool-guard.py` 的判法（工作目录或 `PASEO_AGENT_CWD` 的末段是 `issue-<n>`）判断是否受管：受管会话退出 2 并打印同样一行；其余会话退出 0 | 受管会话屏幕前没人（H6），放行会让 `gh issue close` 与提问失去拦截；拒绝让这个会话停下，watchdog 以 `silent since` 报出来。非受管会话放行，避免全机被拦。代价：启动器里有一份与 `tool-guard.py` 相同的正则，登记在 `anchors.py`，由 `tests/mmw` 核对两处一致 |

- **效果**：B2 移动脚本时 hook 命令不变，切换窗口消失；Codex 的 `trusted_hash` 按命令字符串算（`install.sh` 第 764–800 行），命令不再变，B2 以后不必重算。
- **验收**（B0、B2 各一次）：在隔离 home 里经启动器调用两个 hook，断言 `gh issue close` 与提问在 `issue-<n>` 目录里确实被拒、在别的目录放行；把目标文件挪走再调一次，断言上表的行为；另断言两个 hook 能导入全部同伴模块（`tests/liveness` 加一条）。

### 7.4 `mmw/scripts/mode-hook.py`（B1 新建）

三种事件：会话开始（含压缩后）跑 `dispatch.sh where` 并打印那一行；`SubagentStart` 打印读 mode 的一句；prompt 提交时打印 pstack `reminder` 的改写句。范围与失败处理见第 2.3 节末段。各宿主登记哪些事件按 U-2 的实测结果；B1 只登记 B0 探针证实能注入的事件。

### 7.5 连线检查 `mmw-v2/tests/lib/check_wiring.py`

与 `check_module_paths.py` 同类，每个套件的 `run.sh` 先跑。每一类在它所查的对象建成的那一批转为「不通过就失败」，之前只报告；`tests/wiring/` 为每一类放一个必须失败的反例（R12 X-5）。

| 类 | 检查 | 防的是 | 转为失败 |
|---|---|---|---|
| 1 指针 | 每个 `mmw <slug>#<title>` 或 `mmw#<section>` 字面（脚本、文本、`roles.json`、`anchors.py`）都对到一份 MMW 自写 playbook 里带粗体标题的步骤、`####` 小节，或 mode 的小节；指向导入 playbook 即失败 | 指针对不上 | B0 |
| 2 可解析 | 路由表每行的文件存在；每步点名的技能在 `skills.txt`；点名的 reference、脚本子命令、原则文件存在；导入文件里未映射的名字都在 `slots.md` 有一行；mode 只点名当时存在的组件 | 某一跳找不到下一步；pstack 缺依赖检查（L7 E.1 第 27 条） | B1（每批发布前对 mode 跑一遍） |
| 3 方向与纯度 | 能力技能文本没有「下一步」「谁调用我」两种句型；原则只指向原则或能力技能；能力技能的脚本不调用 mode 的命令，只可按 `anchors.py` 导入 `events.py`；脚本里的文字锚点与跨目录路径只来自 `anchors.py`；上游技能与 squash 原文的差异只能是 merge-note 登记过的两类 | L7 B.2 三条方向规律；混层回潮 | B2 末 |
| 4 不按编号 | MMW 自写的文字跨文件出现 `step \d`、`closing step`、`Phase X`、`## N` 即失败；`imports.tsv` 登记的导入文字不查 | L7 E.1 第 2 条；R12 M13、M30 | B2 末 |
| 5 原则索引 | mode 索引每行对应一个原则文件，「何时适用」等于其 `description` 第一句；MMW 自写的原则引用只用一种写法 | L7 E.1 第 1、14 条 | B1 |
| 6 事件覆盖 | `roles.json` 的每个（角色，事件）↔ `relay.py` `WAKES` 与 `relay.recovered` ↔ `watchdog.py` 的八种告警前缀 ↔ `MMW turn guard:` ↔ `resume`：每个（角色，事件）恰好有一个处理处，在该角色的 playbook 或 `orchestrator-events.md` 里 | R14 W1；R12 K-30；`SKILL-SET-RULES.md` `### Hand-offs`「Each event gets one instruction across the set」 | B2 末 |
| 7 骨架 | MMW 自写 playbook 有 `### <Name>`、带粗体标题的编号步骤、`**Reply:**`，每步点名一个组件或标 `(judgement)`；`imports.tsv` 登记的导入 playbook 只查 `### <Name>` 与 `**Reply:**`（`opening-a-pr.md` 连 `**Reply:**` 也没有，L7 C.6 信号 5 所记的例外，登记在 `imports.tsv`）；路由表每份 playbook 恰好一行；`.mmw/playbooks/INDEX.md` 同理 | L7 A.2 | B1 |
| 8 一行 | 所有送进活会话的模板（唤醒、告警、`resume`、启动提示词）不含换行 | H4 | B0 |
| 9 开关 | 被 mode 或 playbook 点名、要模型调用的上游技能在 `skills.txt` 带 `+model`；安装副本里没有开关、`openai.yaml` 没有 `policy`；本仓自有技能不带开关 | H2；`merge-notes/README.md` 的配对规则 | B1 |
| 10 路径字面 | Python 与 shell 文件里指向技能目录的字面（`"skills" / "<name>"`、`skills/<name>/scripts`、`HERE.parents[N] / "<name>"`、`$(dirname "$HERE")/<file>`、`$SKILL_ROOT/scripts/<file>`）指向的目录与文件存在 | `check_module_paths.py` 只查模块名，抓不到 `board/` 的四处、`runners/*.sh` 的三处与 `install.sh` 第 1428 行 | 存在性 B0；「只经 `anchors.py`」B2 末 |
| 11 孤立脚本命令 | 每个 `dispatch.sh`、`ticket.py` 子命令至少被一个 playbook 步骤、mode 触发行或别的脚本点名 | R15 第 7.4 节 | B2 末 |
| 12 冻结路径 | 启动提示词与数据文件里写出的 MMW 文件路径都在 `~/.mmw/installed-root` 所指的 checkout 下，不在任何 `.worktrees/issue-<n>` 下 | H5 | B2 |
| `--graph` | 由以上数据生成一张连线总图 | 用户在 Memory 里要的「一张与实际同步的总图」（R17 引 `ce037679`） | — |

`install.sh --check` 对已安装 checkout 跑第 2、6、7 类的只读部分，并列出开着的 watch 与活着的 relay、watchdog 锁（R12 K-32）。

### 7.6 要改的脚本与调用点（本轮 grep 到的全部）

| 位置 | 改动 | 为什么 |
|---|---|---|
| `dispatch/scripts/` 整目录 → `mmw/scripts/`；`dispatch/hosts.json` → `mmw/hosts.json` | 平移，内部文件名与相对位置不变 | `models.py` ↔ `runners/*.sh` ↔ `statedir.py`、`turn-guard.py` ↔ `watchdog.py`、`runners/`、`tool-guard.py` → `skills/ui-acceptance` 的相对路径全部保持（第 1 节） |
| `dispatch.sh` 第 108–109 行 | 删 `AUTONOMOUS`、`PRODUCT_RULES` | 规则的家是 mode `## Autonomy` 与 P15 规则簇；没有测试钉这两句（R12 M19） |
| `dispatch.sh` 第 1741、1747–1751 行 | Memory 索引与 Rules 包正文里的小节名改从 `anchors.py` 取，指向 `shared-experience` 与 `review-a-ticket#Active Rules` | 这两处 f-string 里写死了旧技能的小节名 |
| `dispatch.sh` 第 1949、1967、2072 行 | 启动提示词改为一行，取值来自 `roles.json`；Memory 索引、Rules 包、advisor 简报与已安装 checkout 的绝对路径写进 `~/.mmw/state/<repo>/prompts/` | W2；H4；H5；`test_dispatch.sh` 第 2830、6984、7199 行随改（R12 M19） |
| `dispatch.sh` 新动词 `where [<spec>|<n>]` | 第 7.7 节 | 被压缩的会话不必记住自己是谁（R12 K-3） |
| `dispatch.sh` `open`、`open-ticket`、`adopt` | 写 `watches.json` 时加 `kind` | 第 7.1 节 |
| `dispatch.sh` `resume_one`（第 2190 行起） | 送出的文字末尾接指针 | 第 7.1 节 |
| `dispatch.sh` 第 99 行 `MODELS_PY="$SKILL_ROOT/scripts/models.py"` | 不变（平移后仍成立） | — |
| `dispatch.sh` 第 2344–2360 行 | `check` 失败时不再自动跑完整 `install.sh`，只报告缺什么 | 服从根 `AGENTS.md` 规则（R12 M7） |
| `dispatch.sh` 新动词 `panel`、`panel-wait`（B3） | 第 8.8 节 | H3 |
| `status.py` | 新增 `--where`（第 7.7 节）；`_load` 的缺省路径改为同目录的 `events.py`；`issue_tree.py` 经 `anchors.py` 从 `verify-ticket` 导入 | 位置是 mode 的事；R4 V6、V10；R12 M17、M18 |
| `relay.py` 第 258 行 `_load_events`、第 385 行 `wake_text` | 事件词表改为同目录；唤醒文字同一行末尾接 ` · mmw <playbook>#<step>`，按第 7.1 节取；`WAKES` 不变 | H4；R12 K-1；`test_relay.py` 相等断言随改（R4 V5） |
| `watchdog.py` 第 735、780 行等 | 「night.md's Exit codes of resume」改为按收件角色取的指针；八种告警都带指针，仍是一行 | R4 V2；H4 |
| `turn-guard.py` 第 306 行起 | 保留命令，末尾接指针 | R4 V7 |
| `tool-guard.py` 第 57–58 行 | `_UI_ACCEPTANCE_SCRIPTS` 改从 `anchors.py` 取 | 平放时原写法仍成立，改从锚点取是为了第 10 类 |
| `tool-guard.py` 第 68 行 `REFUSAL` | 关票命令改为 `ticket.py {n} --closeout <draft>`，加一句指向 `mmw work-a-ticket#Close out` | 命令搬家；**principle-refusals-name-one-next-step** |
| `tool-guard.py` 第 76 行 `NO_QUESTION` | 分三种：环境变量 `MMW_ROLE`（`dispatch.sh start` 写进会话环境，与今天的 `MMW_TICKET` 同处，第 1957 行）为 `worker` 时给 worker 的出路（今天的原句）；为 `reviewer` 时给「write `unverified: <what would settle it>` at the end of that finding's line in your report」；读不到时两条都给。每条不超过 `REASON_LIMIT`（`test_tool_guard.py` 第 450 行）。只管 `issue-<n>` 目录里的会话，advisor 不在其中（文件头注释与 `governed_ticket()`，本轮核实）；hook 进程能否读到 `MMW_ROLE` 待测（U-17） | V9；`test_tool_guard.py` 第 442–447 行的三条断言改为按角色断言 |
| `verify-ticket/scripts/verify-ticket.py` | 拆：状态命令进 `mmw/scripts/ticket.py`；留下判据运行（只打印结果）、lint、发布；`own_session()`（第 250–257 行）删除；`resume_at`（第 2148–2182 行）进 `status.py`；第 831、844、1986 行点名 `dispatch.sh start … worker` 的拒绝文字随状态命令进 `ticket.py` | 第 4.1 节 |
| `verify-ticket/scripts/events.py` → `mmw/scripts/events.py` | 平移 | 事件词表是流水线状态 |
| `retro/scripts/retro.py` | `events.py` 经 `anchors.py` 的路径加载；`DESTINATIONS` 加 `principle`、`playbook`、`mode`（B1） | 第 4.5 节；R13 E11 |
| `board/board_data.py` 第 15 行、`codeversion.py` 第 20–23 行、`settings_api.py` 第 10 行、`supervisor.py` 第 18 行 | 路径改从 `anchors.py` 取（`mmw/scripts/`；`events.py`、`issue_tree.py` 的新位置） | 四处写死 `skills/dispatch/scripts`（本轮核实）；`supervisor.py` 在导入时绑定，由 LaunchAgent `com.mmw.board` 常驻 |
| `install.sh` 第 326、331–332 行 | hook 源路径改为 `mmw/scripts/`；hook 经启动器登记 | 本轮 grep |
| `install.sh` 第 1088 行 `MMW_MODELS_PY` | 改为 `mmw/scripts/models.py` | 同上 |
| `install.sh` 第 1428 行 `runners = root / "skills" / "dispatch" / "scripts" / "runners"`、第 1604 行提示文字 | 改为 `mmw/scripts/runners` | `--check` 扫描 `MMW_USES` 用 |
| `install.sh` 第 150–153 行 | 认 `ps/` 前缀（→ `upstream-pstack/skills/`）与行尾 `+model`；生成安装副本（第 4.3 节） | 今天只有 `self/*`、`dd/*` 两种前缀 |
| `install.sh` 第 940–955 行 | 已安装 checkout 的脚本位置变化时，对 `com.mmw.board` 做 bootout 再 bootstrap | `supervisor.py` 在导入时绑定旧路径；今天只在 plist 变化或任务没在跑时 bootstrap |
| `install.sh` `--check` | 加连线核对、开着的 watch、带 `+model` 的副本是否过期、`delivery: pr` 的仓库在时 `bun` 是否在 `PATH` | 第 4.3、8 节 |
| `tests/lib/check_own_skill_frontmatter.py` 第 56–62 行 | 认 `ps/` 前缀与 `+model` 标记；加一个 `ps/` 反例测试 | 今天不认识的前缀一律解析成 `upstream/skills/<line>`，B3 起每个套件都会红 |
| `migrations/remove-verifier.py` 第 16–22 行 | `DISPATCH_SCRIPTS` 改从 `anchors.py` 取 | 它导入 `models`、`statedir` |
| 测试（14 个文件，本轮 grep） | `tests/board/test_settings_api.py`、`test_supervisor.py`；`tests/dispatch/test_dispatch.sh`、`test_local_config.py`、`test_profiles.py`、`test_runner_pick.py`、`test_status.py`、`test_tool_guard.py`；`tests/liveness/test_guard.sh`、`test_liveness.py`；`tests/relay/test_ghlist.py`、`test_relay.py`、`test_relay.sh`；`tests/verify-ticket/test_events.py`；另 `tests/migrations/test_remove_verifier.py` 间接依赖；`tests/verify-ticket/` 里测状态命令的（`test_closeout.py`、`test_draft.py`、`test_preflight.py` 等）随 `ticket.py` 搬到 `tests/mmw/` | 路径与断言随改 |
| 仓库文档 | 14 个文件里 118 处 `dispatch/scripts` 或 `skills/dispatch`（`docs/adr`、`docs/contexts`、根 `AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`），加上点名 `verify-ticket.py --closeout` 等状态命令的地方 | 字面引用，照判据一起改 |

### 7.7 `dispatch.sh where`：事件 → 步骤

`where` 用 `dispatch.sh self` 取当前会话的 runner 与会话号，对比票上 `*.started` 事件与 `watches.json` 定角色，再由 `status.py --where` 按下表从事件算位置。输出只有四种形式，一行：

- `AT <role> #<n> · mmw <playbook>#<step>`：记录能唯一定出一步；
- `BETWEEN <role> #<n> · mmw <playbook>#<step A> .. #<step B>`：两步之间的步骤不留事件，读票与工作树确认从哪一步继续；
- `FRESH <role> #<n> · mmw <playbook>#<first step>`：本角色在这张票或这份 spec 上还没有任何事件；
- `UNKNOWN <reason>`：事件读不到、认不出本会话、或事件组合不在表里；照 `<reason>` 做，不猜。

今天 `verify-ticket.py` 的 `resume_at` 在两种情形都返回 `None`（全新认领与第 5 步之后，本轮读第 2148–2182 行），上一版规定「没有记录就从 Claim 开始」会把做到第 8–10 步的 worker 送回 **Claim**；上面的 `FRESH` 与 `BETWEEN` 把这两种情形分开。

| 角色 | 票或 spec 上的最新记录 | 输出 |
|---|---|---|
| worker | 没有本会话之后的 `ticket.claimed` | `FRESH` → **Claim** |
| worker | `ticket.claimed`，没有本人的判据运行 | `BETWEEN` **Read yourself in** .. **Integrate and run every criterion** |
| worker | 本人的 `ticket.checked`（run `self`），没有 `worker.decided` | `AT` **Post the decisions** |
| worker | `worker.decided`，没有 `reviewer.started` | `AT` **Get reviewed** |
| worker | `reviewer.started` 活着、没有 `reviewer.reported` | `AT` **Get reviewed**（等待中，结束回合） |
| worker | `reviewer.reported` 之后没有本人的判据运行 | `AT` **Get reviewed**（修复轮） |
| worker | `reviewer.reported` 之后有本人的判据运行，没有 worker 的 reverify | `AT` **Run every criterion one final time** |
| worker | worker 的 reverify 在 `HEAD` 上且是最新事件 | `BETWEEN` **Audit against the ticket** .. **Close out** |
| worker | `ticket.returned` 或 `ticket.bounced` 之后 | `AT` **Claim**，然后从 **Integrate and run every criterion** 起 |
| reviewer | `reviewer.started` 是本会话、没有 `reviewer.reported` | `FRESH` → **Pin the diff**（前四步不写东西，重跑无副作用） |
| night-orchestrator | spec 没有 `spec.opened` | `FRESH` → **Check and open** |
| night-orchestrator | `spec.opened`，批次里没有任何 `worker.started` | `BETWEEN` **Lint the batch** .. **Advance, then end your turn**（`--lint` 可重跑） |
| night-orchestrator | 有活代理或非空前沿 | `AT` **Handle each wake** |
| night-orchestrator | 前沿空、没有活代理、有开着的 finding | `AT` **Closing pass** |
| night-orchestrator | 没有开着的 finding，没有 `spec.closed` | `BETWEEN` **Close the Memory records** .. **Reverify and summarize**（`memory-list` 可重跑） |
| night-orchestrator | `spec.closed`，没有 `result=recorded` 的 `spec.retroed` | `AT` **Retro** |
| night-orchestrator | `spec.retroed` 已记录，没有 `spec.merged` | `AT` `mmw accept-the-night#Read the night out` |
| ticket-orchestrator | 按 `one-ticket.md` 的四步同理：没有 `worker.started` → **Start the worker**；有活 worker → **Handle each wake**；`ticket.passed` 或 `ticket.returned` → **Land** | 同上 |

不新增事件：不留事件的步骤（**Lint the batch**、**Close the Memory records**、worker 的 **Read yourself in**、**Audit**、**Draft**）都可重跑，`BETWEEN` 让会话读票确认（**principle-make-operations-idempotent**）。这张表登记进 `anchors.py`；「`where` 对每个角色、每一行的正确率」是 U-16 的实测项。

### 7.8 脚本怎样点名 playbook 与步骤

- 只按 `mmw <slug>#<Step title>`，取自 `anchors.py` 或 `roles.json`，不写编号；技能内路径随已安装 checkout 冻结（H5），启动提示词的数据文件另给绝对路径。
- 送进活会话的一切都是一行（H4）。
- 脚本不做判断：`where` 只报告位置，下一步由 playbook 的步骤决定。

### 7.9 仓库文档随之改的规则

- `SKILL-SET-RULES.md` 与 `REVIEWING-A-SKILL-SET.md` 搬到 `mmw/references/skill-set-rules.md`、`reviewing-a-skill-set.md`，随 mode 安装，P11 在任何仓库都读得到；`docs/skill-set.md` 留一行指针；根 `AGENTS.md` `## External References` 那一行改指新位置。文件加 `## Layers of the set`（本文第 0.1 节的层与判据）。事实 7「A skill's place follows from its own text … its closing section says what comes next」与 `### Hand-offs` 第 5 条改为「一个技能的位置由 mode 路由表与 playbook 决定；能力技能以它交回什么结尾」。原句防的两件事——第二份副本漂移、某一跳找不到下一步（#538）——由「顺序只有一个家」加连线检查第 2、7 类防住。
- `CODING_STANDARDS.md`：加「脚本的文字锚点与跨技能路径只经 `anchors.py`」「可重跑（**principle-make-operations-idempotent**）」；跨任务立场改为点名原则。
- `TESTING.md`：加连线检查一句；写明锚点表改动要跑哪些套件。
- 根 `AGENTS.md`：`## Package Manager` 加「`bun` runs only the imported pstack scripts under `mmw/scripts/ps/`」；`## Gotchas` 第 1 条改为指向私有 playbook **Promote a change** 的一行加「The third step waits while any watch is open」。
- ADR 0032（分层；`dispatch` 解散；`verify-ticket` 拆分；取代事实 7；本文的判据与优先级句）、0033（唤醒带步骤指针，修订 0020；启动提示词一行、数据进文件，修订 0031 的投递方式；watch 加 `kind`）、0034（pstack 以子树引入；导入的八种类型；开关在安装时处理）。
- `CONTEXT-MAP.md`、`docs/contexts/toolbox/CONTEXT.md`、`night/CONTEXT.md`、`ticket-run`、`tickets` 的 `CONTEXT.md`：新词条 mode、playbook、principle、role、slot、step pointer、where line；`RESUME:` 词条改为 where line；`_Home_` 随搬家改。

---

## 8. pstack 导入接口

**采用的决定。** pstack 以 squash subtree 引入 `mmw-v2/upstream-pstack/`，原文不改。组件按八种类型落位（第 8.2 节），每个外来文件登记在 `imports.tsv`；Cursor 专有机制、PR、forge、control、模型角色由 `mmw/references/slots.md` 解析；跨厂商面板由 `dispatch.sh panel` 另起会话，与依赖它的能力技能同在 B3。

**理由。** 用户以后要把 pstack 里有用的东西搬进来，新架构必须让改动只是加文件、加登记行；需要判断的改动单独计数（第 13 节）。

### 8.1 来源与安装

- `cursor/plugins` 仓库的 `pstack/` 子目录：先在临时克隆里 `git subtree split --prefix=pstack`，再对切出的分支 `git subtree add --squash` 到 `mmw-v2/upstream-pstack/`（推断，U-13）。命令与提交记进 `merge-notes/pstack.md`；`LICENSE`（MIT）随子树保留。
- 能力技能：`skills.txt` 加 `ps/<name>`（必要时加 `+model`），`install.sh` 从 `upstream-pstack/skills/<name>` 装软链或安装副本。
- 其余类型复制进 `mmw/`。不用软链，因为 pstack 文件里的相对链接按读者打开的路径解析，软链会让它们指错；拉更新后 `import_component.py --refresh` 列出差异。

### 8.2 八种导入类型

| 类型 | 落位 | 登记 | 机械改写 |
|---|---|---|---|
| `playbook` | `mmw/playbooks/<file>` | 路由表一行（带 Distinct from）；`imports.tsv` | `../references/X` → `../references/ps/X`；`scripts/X` → `scripts/ps/X` |
| `principle` | `mmw/principles/principle-<slug>.md` | mode 索引一行（由 description 生成）；`imports.tsv` | 删开关行；`../principle-x/SKILL.md` → `principle-x.md` |
| `skill` | 不复制；`skills.txt` 一行 `ps/<name>` | `skills.txt`；`imports.tsv` | 无（开关在安装副本里处理，第 4.3 节） |
| `mode-trigger` | mode `## Non-negotiables` 的 `### Imported triggers`，原文一行 | `imports.tsv`（行号与来源行号） | 无 |
| `mode-section` | mode 里一个同名小节，原文复制 | `imports.tsv` | 无（目前只有 `## Comments`） |
| `mode-reference` | `mmw/references/ps/<file>` | `imports.tsv` | 无 |
| `mode-script` | `mmw/scripts/ps/<path>`，连同它导入的同目录文件 | `imports.tsv`；运行时依赖写进根 `AGENTS.md` `## Package Manager` | 无 |
| `agent` | `mmw/references/ps/agents/<name>.md`，作为通用子代理的简报 | `slots.md` 一行（「Spawn <Agent>」读作「宿主通用子代理，带这份简报」）；`imports.tsv` | 删 frontmatter 的 `is_background` 等宿主字段 |

外来的 reference 与脚本放 `ps/` 子目录，与 MMW 自有文件分开命名空间：MMW 的 `mmw/scripts/` 是流水线的状态脚本，不混入 bun 的 `package.json`、`bun.lock`。playbook 与原则不分命名空间：同名就是同一任务类型或同一条规则，按第 8.5 节冲突规则合并。

### 8.3 `mmw/references/slots.md`

| pstack 里写的 | 在 MMW 读作 | 依据 |
|---|---|---|
| `mode: true`、`reminder` | `mmw` 技能 + `mode-hook.py` + 启动提示词 | H1；第 2.3 节 |
| **poteto-mode**、`/poteto-mode` | `mmw` 技能 | 第 2.2 节别名 |
| 「your configured <label> model (default …)」；`~/.cursor/rules/pstack-models.mdc` 的 `<label>` 行 | 会话内子代理：不指定模型，跑在本会话模型上（H3）；需要另起会话的：`models.py config get "<label>"` | R13 I-5 |
| 面板角色 `arena runners`、`architect runners`、`interrogate reviewers`、`arena cross-judge pool`、reflect 的 judgment、tooling 两种模型 | `dispatch.sh panel <label> <brief>`，列表取自 `models.json` 该面板角色 | H3；第 8.8 节 |
| `Task` 的 `model`、`run_in_background`、`readonly` | 不指定模型；后台按宿主（U-4）；只读靠简报一句 | ADR 0015 |
| `subagent_type: "poteto-agent"` / `generalPurpose` | 宿主通用子代理 + `references/subagent-brief.md` + `SubagentStart` 注入 | 第 2.3 节 |
| 「Spawn Comment Sicko」 | 宿主通用子代理，简报 `references/ps/agents/comment-sicko.md` | `agent` 类型 |
| `AskQuestion` | 人在场：在对话里问（`shared.md` 规则 1）；无人：mode `## Autonomy` | H6 |
| Cursor's `/loop`、`/goal` | 宿主自带的循环命令（如有，U-4）；夜里是 relay 唤醒与 watchdog | ADR 0010、0020 |
| cloud agent | `dispatch.sh start` 或 `panel` 另起的会话 | — |
| `agent-transcripts/`、`~/.cursor/projects/` | 各宿主的会话记录位置，一行一个（U-8）；另有 `handoff` 文件、推上去的分支、tracker 事件 | R13 I-14 |
| 「the MCPs from the Cursor environment」「the `mcps/` directory」 | 你的宿主列出的 MCP 工具 | `why` 第 62 行 |
| `create-skill` | `writing-for-agents` | — |
| `automate-me` | 没有对应物：用户的工作方式写在 `shared.md`（S） | 第 13 节 |
| control 槽位（「the matching control skill」、`control-ui`、`control-cli`） | 浏览器与 Web → `playwright-cli` 或 `ui-acceptance` 的 oracle；本机原生窗口 → `computer-use`；Orca 内置浏览器 → `orca-cli`；CLI → 直接跑命令；`.mmw/target.json` `control` 可覆盖；B5 起可由 `create-verification-skill` 生成仓库自己的一个；找不到就停下并说出缺什么（ADR 0008） | R13 I-8 |
| delivery 槽位（「Run **Opening a PR**」） | **Deliver a change**（P10）；`delivery: pr` 的仓库里就是导入的 **Opening a PR** | R13 I-10 |
| forge 槽位（`gh`、`command -v origin`、`gt`） | `docs/agents/issue-tracker.md`；导入文件里的 `gh` 默认与它相容，不改 | R13 I-11 |
| audit trail（「the **show-me-your-work** skill」） | 绑票的会话：票上的事件与 `Decisions I made on my own`；其余会话：B3 起导入的技能，B3 前写在回复里 | R13 E7 |
| `/deslop`（cursor-team-kit） | 没有对应物，写 `skip:` 行 | L7 E.1 第 27 条 |
| brain note | `shared-experience` 保存的一条 Memory 记录 | — |
| 「Rebase」「rebase onto clean trunk」 | 在票的工作树里读作 `dispatch.sh integrate`（一次合并）；其余会话照原文 | `implement` 第 78 行 |
| 「Binary-search the cause」的做法 | 反馈循环难建时读 `diagnosing-bugs` | 第 3.3 节 P6 |
| worktree 约定 | `.worktrees/` 下，避开 `issue-<n>`、`merge-<branch>`；`worktree-cleanup` 不删这两类，任何 watch 开着时不删本仓库的 worktree | 根 `AGENTS.md` `## Key Conventions`；H5 |
| 运行中从 trunk 重读 playbook（`autopilot-full.md` 第 6 步、`multi-phase-plan.md` 模板） | 禁止（H5）。这两份不导入（第 13 节） | L7 B.1 |

### 8.4 PR 与 MMW 落地方式的对应

| 情形 | pstack | MMW |
|---|---|---|
| 夜里一张票 | —（pstack 没有） | closeout；orchestrator `advance` 合进 project branch（ADR 0025） |
| 一夜的结果 | 一个 stack 经 babysit、shipping 落地；或 Autopilot、Orchestrate | `summary` → 用户验收 → `finish`（P12、P13） |
| 白天在本仓库 | Opening a PR | 私有 playbook **Promote a change**（`delivery: playbook:promote-a-change`） |
| 白天在用 PR 的仓库 | Opening a PR、Babysit、Shipping | 同左，B4 导入 |
| 其他仓库 | — | 提交到当前分支并告诉用户（`delivery: commit`） |

`shipping.md` 九步在 MMW 里逐条都有对应物（R16 第 9.3 节表）：独立 verdict ↔ reviewer 与判据运行；只落地从根开始连续的已验证段 ↔ `advance` 按阻塞边合并；patch-id 核对 ↔ 收口轮 `reverify` 与 worker 在 `HEAD` 上的最终运行；一次一个 ↔ `advance` 一次合并一张（ADR 0027）；不把自动合并当就绪 ↔ 就绪只看票事件；每次合并后重算 ↔ ADR 0019；`watch-pr` 与 `/loop` ↔ relay、watchdog；停在天花板 ↔ `NIGHT SUMMARY`。所以它不替换 MMW 的夜，只服务用 PR 交付的仓库的白天改动。

### 8.5 `import/import_component.py`

**做的（全是机械的）**：按八种类型复制文件并登记 `imports.tsv`；做第 8.2 节表里的机械改写；`principle` 类型从 description 生成 mode 索引行；`skill` 类型在它被 mode 或 playbook 点名时给 `skills.txt` 那一行加 `+model`；带出依赖闭包（被导入文件点名的技能、原则、playbook、mode reference、mode 脚本）；扫出槽位关键词（control skill、Opening a PR、`gh`/`origin`/`gt`、`subagent_type`、configured … model、`pstack-models.mdc`、`AskQuestion`、`/loop`、`/goal`、cloud、`agent-transcripts`、`git show origin/main:`、Spawn <Agent>）并逐个对 `slots.md`，有未映射的就以非 0 退出；遇到同名 playbook、同名技能、同名原则、悬空依赖就拒绝并点名；`--refresh` 对比子树新版本列出差异。

**不做的**：改写需要判断的句子。这些由跑 **Import a component** 的 agent 处理：加一行 `slots.md`，或做一处判断改动并在 `imports.tsv` 的「判断改动」列与 `merge-notes/pstack.md` 各记一条（L7 C.1 第 1 问）。

**冲突规则**：
- 同名能力技能不导入，MMW 的同名技能满足点名（`tdd`、`teach`）；用户要 pstack 版时以 `pstack-<name>` 改名导入。
- 同名 playbook：按「导入原文 + 附加步骤」合并，附加步骤算判断改动（`bug-fix`）；原文与 MMW 规则冲突、不能靠附加步骤解决的，保留 MMW 版并吸收可用的原文段落（`authoring-a-skill`、`prototype`）。三种处理都记在 `imports.tsv`。
- 原则重合按第 5.4 节。本地闸门与上层授权冲突按 mode 优先级句。运行中从 trunk 重读：不导入该文件，或删那一句并算判断改动（H5）。

### 8.6 私有 playbook **Import a component**（`.mmw/playbooks/import-a-component.md`）

1. **Pull the source.** 按 **Pull an upstream** 拉 `upstream-pstack/`。
2. **Pass the entry questions.**（取自 R4 D7.3 与 R13 第 4 节末）①它产出一个能叫出名字的交付物、能脱离 mode 被调用吗？否则它是 playbook。②它依赖的每个槽位在 `slots.md` 都有一行吗？③依赖 PR 吗？是就只路由给 `delivery: pr` 的仓库。④依赖跨厂商面板吗？`panel` 在就用，否则在路由行写明降级。⑤运行中从 trunk 重读自己吗？不导入，或删那一句。⑥与 MMW 同名吗？按冲突规则。
3. **Run the importer.** `python3 mmw-v2/import/import_component.py <type> <name>`，带出依赖闭包。
4. **Register it.** 路由表一行（带 Distinct from）、原则索引一行、`skills.txt` 一行 `ps/<name>`、触发行一行；需要时加 `slots.md` 一行。
5. **Prove the wiring.** `check_wiring.py`；`install.sh --check`。
6. **Deliver.** **Deliver a change**（技能列表变了：请用户授权 `install.sh`，开新会话）。

### 8.7 bun

B4 起 `mmw/scripts/ps/watch-pr/`、`bootstrap.ts`、`package.json`、`bun.lock` 需要 bun（L7 A.6：`bootstrap.ts` 首次运行时自举依赖）。它们只被 `babysit.md`、`shipping.md` 点名，这两份只在 `delivery: pr` 的仓库出现在路由表里；`install.sh --check` 只在本机登记了 `delivery: pr` 的仓库时要求 bun。`worktree-audit.sh` 是 bash，不需要 bun。

### 8.8 多模型面板（H3，B3）

H3 下跨厂商面板只能是多个另起的会话。`dispatch.sh panel <label> <brief>`：按 `models.json` 里该面板角色的列表逐项另起会话（照 `dispatch.sh` 第 2053–2080 行 `advise_one` 的做法），每个成员拿同一份简报（pstack `interrogate` 第 57 行「The same filled template goes to all reviewers」），答案写进 `~/.mmw/state/<repo>/panels/<id>/<member>.md`；`panel-wait <id>` 阻塞到全部到齐或某个会话消失（「一条会阻塞到对方完成的命令」是 `skill-set-rules.md` `### Hand-offs` 第 3 条认可的完成信号）。成员要写答案文件，与 `advising.md`「writing nothing」不同，在面板简报里写明这一例外。`arena`、`architect`、`interrogate`、`reflect`、`eval` 与它同批，价值来自模型多样性（pstack `interrogate` 第 9 行「The adversarial signal comes from model diversity」），不以降级方式导入。U-6 只量耗时、费用与夜里收齐的可靠性，不作为建不建的闸门。

---
## 9. 改造前后对照表（N1–N10 的每个部件）

动作词：**搬**（整体换位置）、**拆**（分给几处）、**删**（内容已有别处的家）、**回原文**、**改写**（原位改文字）、**新建**、**本层**（按类型本来就在这一层，位置不动，内容可能改；不属于「留在原处」）、**留（H#）**（按类型本该搬走，因硬约束留下）、**留（S）**。

### 9.1 N1 `dispatch` 与夜

| 部件 | 升级后 | 动作 |
|---|---|---|
| `dispatch/SKILL.md` description、`## Find your moment` | mode 路由表、`roles.json`、`setup-mmw` | 拆；技能解散 |
| 第 8 行 | 前半句 → **principle-the-tracker-is-the-state**；后半句 → `mmw/scripts/` 头注释 | 拆 |
| `## On waking` | mode `## Re-entry` | 搬 |
| `references/night.md` | P12；`## 3` 表与 `### Exit codes of resume` → `orchestrator-events.md`；`## 5` 末段与 `## 6` → P13；Memory 决定写法 → `shared-experience` | 拆、搬；补 R4 V6–V8、R12 M16 |
| `references/one-ticket.md`、`inside-a-ticket.md` | P14；P15 **Entry** 与 `#### After the closeout, picked up yourself` | 搬 |
| `references/editing-models.md` | `setup-mmw` | 搬 |
| `hosts.json`、`scripts/` 全部 12 个文件 | `mmw/hosts.json`、`mmw/scripts/`（平移） | 搬 + 第 7.6 节改写 |
| `tool-guard.py`、`turn-guard.py` 的拦截登记 | 各宿主 hook 配置，经 `~/.mmw/bin/mmw-hook` | 改写；登记位置 **留（H1、H6）**：结构性拦截只能在宿主 hook 上做 |
| `AUTONOMOUS`、`PRODUCT_RULES` | mode `## Autonomy`；P15 `#### While the product runs` | 删 |
| 三条启动提示词 | 一行，点名 mode、playbook、票号、`Unattended`、数据文件 | 改写。提示词里的 mode 名与 playbook 名 **留（H1）** |
| 唤醒、告警、`resume` 文字的一行形状 | 每行接指针 | 形状 **留（H4）**，内容照改 |
| `dispatch.sh check` 自动重装 | 只报告 | 改写 |
| `anchors.py`、`roles.json`、`mode-hook.py`、`where`、`mmw-hook`、`watches.json` 的 `kind` | 第 7 节 | 新建 |
| `docs/contexts/night/CONTEXT.md`、`how-it-works.md`；ADR 0009、0010、0016–0018、0020–0025、0027 | 仓库文档 | 本层；改路径、加词条；0033 修订 0020 |

### 9.2 N2 `verify-ticket`

| 部件 | 升级后 | 动作 |
|---|---|---|
| `SKILL.md` 第 8–12 行 | 能力正文（只讲跑判据、lint、发布）；第 10 行理由换点名原则 | 改写 |
| description 的时机半句；第 16 行；`## Reached from here` | P1、P12；删；mode 触发行 | 拆、删 |
| `## Find your moment` 表 | 能力内部分支（切子票、lint） | 本层 |
| `references/linting.md`、`sub-issues.md` | 命令与 kind 表本层；「何时」→ P1、P12；第 11 行 → 各角色唤醒行 | 拆 |
| `verify-ticket.py` 判据运行、lint、发布 | 能力脚本；判据运行只打印结果 | 本层，改写 |
| `verify-ticket.py` 状态命令、`resume_at`、`own_session()` | `mmw/scripts/ticket.py`；`status.py --where`；删 | 拆、搬、删 |
| `events.py` | `mmw/scripts/events.py` | 搬 |
| `issue_tree.py`、`gate-check/`、`upstream-unlazy/`、`merge-notes/unlazy.md` | 能力、外来组件、仓库文档 | 本层 |
| `docs/contexts/ticket-run`、`tickets` 的 `CONTEXT.md` | `RESUME:` 词条改为 where line | 改写 |
| `tests/verify-ticket/` 测状态命令的文件；`test_preflight.py` 第 450–517 行的 `RESUME:` 断言 | `tests/mmw/`；`where` 场景 | 搬、改写 |

### 9.3 N3 `implement`、`code-review`、`tdd`

| 部件 | 升级后 | 动作 |
|---|---|---|
| `implement/SKILL.md` 第 1–101 行 | P15、`references/writing-code.md`、原则、`shared-experience`、`ui-acceptance` | 拆；回原文，不安装 |
| `implement/references/writing-interface-code.md`、`saving-memory.md` | `ui-acceptance/references/`、`shared-experience/references/` | 搬 |
| `code-review/SKILL.md` | 上游 87 行，安装 | 回原文 |
| `code-review/references/session.md` | P16；第 23–33 行 → mode `## Subagents` | 搬、拆 |
| 四个 axis 文件 | `mmw/references/review-axes/`，内容不变，Standards 保留自带的 smell baseline | 搬 |
| `tdd/SKILL.md` 第 22、38 行 | P15 限定句；其余回原文（宿主中立一处 H1） | 搬 |
| `merge-notes/implement.md`、`code-review.md`、`tdd.md` | 记「回原文、内容去了哪里」 | 改写 |

### 9.4 N4 `to-spec`、`to-tickets`、`triage`

| 部件 | 升级后 | 动作 |
|---|---|---|
| `to-spec`、`to-tickets` 全目录 | `mmw-v2/skills/` 下分叉；流程句 → P1、P3；子代理段 → mode `## Subagents`；上游目录回原文不装 | 搬（分叉）、拆 |
| `several-specs.md` | 循环 → P1 **Split into several specs**；判断一句留 `to-spec` | 拆 |
| `revising-a-spec.md`、`<issue-template>` 与三份 reference | 能力 | 本层 |
| `triage/SKILL.md`、`AGENT-BRIEF.md` | 流水线句 → P7、P13；其余回原文；开关 `+model` | 拆、回原文 |
| `triage/references/pipeline-issues.md` | `mmw/references/pipeline-issues.md` | 搬 |
| `docs/agents/issue-tracker.md`、`triage-labels.md`、`domain.md` | 配置；`## Morning queries` 的先后 → P13 | 本层 |

### 9.5 N5 其他上游技能

| 部件 | 升级后 | 动作 |
|---|---|---|
| `prototype` 规则 6 后半、`UI.md` `## Next`、脚手架时机 | P4、P3 | 拆 |
| `prototype` EXP 分支、叶目录、「keep the prototype」 | 能力改动 | 本层 |
| `prototype` `UI.md` state list 段 | `design-pages/references/state-list-format.md` | 搬（W6） |
| `wayfinder` 第 6 步、`mmw:map`、`interface-and-remake.md` | P2；`issue-tracker.md`；`mmw/references/` | 拆、搬 |
| `grilling` 第 28–44 行；`grill-with-docs` 第 7 行末句 | mode `## Autonomy`、pstack 五条原则；P1 | 拆、搬；回原文 |
| `improve-codebase-architecture` `### 4` | 路由行与 P1 入口 | 搬；画图改动本层 |
| `codebase-design` 第 10 行；`resolving-merge-conflicts` 第 2 步票语句 | 删；P15 | 删、搬 |
| `setup-matt-pocock-skills` 的流水线段落 | P9、`tracker-additions.md` | 搬；格式与分页改动本层 |
| `writing-for-agents` 第 8 行；`SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` | 删；`mmw/references/`，改写事实 7 | 回原文、搬 |
| `triage`、`wayfinder`、`to-questionnaire`、`setup-matt-pocock-skills`、`handoff`、`grill-me`、`teach`、`wait-what` 的开关 | 子树原文不动，安装副本去掉（`+model`） | **留（H2）**：只在安装副本里 |
| 残留 `ask-matt` | P1、P2、P4、P5、P6、P7、mode、**principle-decide-at-phase-boundaries**；目录回原文，不装 | 拆、回原文 |

### 9.6 N6 界面链

| 部件 | 升级后 | 动作 |
|---|---|---|
| `ui-acceptance` description 末句、表第 1 行、第 38 行 | mode 触发行；本技能 reference 行；P15 | 拆 |
| `ui-acceptance` 规则 1、2、五份 reference、九个脚本 | 能力 | 本层 |
| 规则 3–5 | 点名原则 + 本地机制 | 改写 |
| `design-pages` 交接段、第 21 行后半句、第 25 行 | P3、P12 contract 行、P15；同技能 reference | 拆 |
| `write-screen-contract` `## Next`、第 8–10 行 | P3、P1；原则 | 拆 |
| `code-review/references/ui-reviewer.md` | `mmw/references/review-axes/ui.md` | 搬 |
| `docs/contexts/ui-acceptance/CONTEXT.md`、ADR 0002、0004、0011、0028–0030 | 仓库文档 | 本层，改写 |

### 9.7 N7 独立技能

| 部件 | 升级后 | 动作 |
|---|---|---|
| `retro` description 触发、第 186 行 | P12 **Retro** | 搬、删 |
| `retro` 第 16–35 行；`## Decide` | 点名原则；加四条分拣规则 | 改写 |
| `retro.py` | `DESTINATIONS` 加三项；`events.py` 路径经 `anchors.py` | 改写 |
| `advisor` 三份 | 能力；`## Start it` 一句去掉 `dispatch` 名 | 本层，改写 |
| `exe-release` 全部 | 能力；路由表直接指向 | 本层；`driving.md` 第 5 行点名原则 |
| `code-checkers` 第 6、8 步的顺序；`manage-agents-md` 第 50 行 | P9；mode `## Subagents` | 拆、搬 |

### 9.8 N8 底座

| 部件 | 升级后 | 动作 |
|---|---|---|
| `prompt/shared.md` | 用户层 | **留（S）**；mode 与原则按规则号引用 |
| `prompt/hosts/*.md`、`render.py` | 宿主提示词的生成与分发 | 本层 |
| `skills.txt`、`install.sh` | 登记层与安装器；`ps/`、`+model`、启动器、安装副本、`com.mmw.board` 重载 | 改写 |
| 已安装 checkout 与 `~/.mmw/installed-root` | 原处 | **留（H5）** |
| `~/.mmw/models.json` | 配置；B3 加面板角色 | 本层 |
| `board/` 四个文件、`migrations/remove-verifier.py` | 路径改从 `anchors.py` 取 | 本层，改写 |
| `tests/lib/` | 加 `check_wiring.py`；`check_own_skill_frontmatter.py` 认 `ps/` 与 `+model`；`tests/mmw/`、`tests/wiring/` 新建 | 新建、改写 |
| 根 `AGENTS.md` | 发布四步 → 私有 playbook **Promote a change**，留指针与 H5 一句；`<important if … upstream …>` → **Pull an upstream** 的指针；`## Package Manager` 加 bun；Commands 与 External References 加 mode 行 | 拆、改写 |
| `CODING_STANDARDS.md`、`TESTING.md`、`merge-notes/`、`downstream-notes/` | 仓库文档 | 本层，改写 |

### 9.9 N9、N10

| 部件 | 升级后 | 动作 |
|---|---|---|
| 31 份 ADR、`CONTEXT-MAP.md`、七份 `CONTEXT.md` | 仓库文档；新增 ADR 0032–0034；新词条 | 本层；只住在词表里的行为规则待查（U-15） |
| PC1–PC29 | 第 5.2、5.3 节与「不建成原则的候选」一段 | 新建、搬、删复述 |
| 35 份 frontmatter | description 只写「是什么、直接调用时怎么说」；流水线时机进 mode；回原文的恢复上游 description | 改写 |
| 24 份 `agents/openai.yaml` | 带 `+model` 的由安装副本生成；分叉的自有技能不带 | 改写 |
| 五张 `## Find your moment` 表 | `dispatch`、`verify-ticket` 第 16 行、`code-review` 的路由内容 → mode 与 playbook；`design-pages`、`ui-acceptance`、`advisor` 的是能力内部分支 | 拆 / 本层 |
| 结尾段 17 句「下一步」 | playbook | 删 |
| 八种到达机制（N10 §3.1） | 四条到达路径（第 2.3 节） | 改写 |
| 提交 `06163a0f` 的决定（移除 ask-matt） | 路由职能由 mode 承担，ask-matt 仍不安装 | 本层 |

**「留（H#）」与「留（S）」汇总**（全部例外）：

1. 唤醒、告警、`resume` 文字必须一行——H4（形状，内容照改）。
2. 启动提示词里的 mode 名、playbook 名——H1。
3. hook 的拦截登记在宿主配置里——H1、H6。
4. 被 mode 或 playbook 点名的上游与 pstack 技能要模型可调用：`triage`、`wayfinder`、`to-questionnaire`、`setup-matt-pocock-skills`、`handoff`、`grill-me`、`teach`、`wait-what`，以及 B3 起 `skills.txt` 带 `+model` 的全部 `ps/` 技能——H2。只在安装副本里改，子树原文不动。
5. mode `## Autonomy` 抄一次产品事项清单——H1（Cursor 收不到 `shared.md`）。
6. 已安装 checkout 与 `installed-root`——H5。
7. `shared.md` 不改——S。

另有两个用户触发的上游技能保持开关，点名它们的地方写「告诉用户运行」：`improve-codebase-architecture`（路由行、P6）、`grill-with-docs`（P1 第 1 步）。这是上游原文，不是留在原处。

---

## 10. 迁移批次（H5 下分批，每批后流水线仍能跑）

**采用的决定。** 六批。每批是本仓库的票，由当时已安装的冻结版本跑；变更自己的测试只在隔离的测试 home 里、对假 tracker 与假 runner 跑（`TESTING.md`）；发布走私有 playbook **Promote a change**。**凡是改了 `skills.txt`、hook 或启动器的批，「移动已安装 checkout」与「运行 `install.sh`」写成一条命令序列一起做**，只在 `install.sh --check` 报告没有开着的 watch、没有活着的 relay 与 watchdog 锁时执行；回退是把已安装 checkout 移回上一个 `main` 提交**并重跑 `install.sh`**。

**每张批次票的验收条件**（照 ADR 0032 的判据）：
1. 这一批涉及的每个文件，每一段要么搬到按类型该在的层，要么在票的 closeout 里写明留下它的是 H1–H6 或 S 中的哪一条；「没有收益」「现在能跑」「改动面大」不作理由。
2. 连线检查里在这一批或更早转为失败的类别全部通过；第 3 类的「只报告」输出里，属于本批文件的条目为零。
3. 本批列出的完整套件通过，并按 `shared.md` 规则 15 在开跑前写明理由。

| 批 | 内容 | 为什么这时流水线仍能跑 | 你要做的 |
|---|---|---|---|
| **B0 地基** | `mmw-hook` 启动器与 hook 改登记（第 7.3 节）；`anchors.py`、`roles.json`（只登记）；`check_wiring.py`（第 1、8、10 类存在性转为失败，其余只报告）；`dispatch.sh where` 与 `--preflight` 的 `RESUME:` 并存；`dispatch.sh check` 改为只报告；在今天的 `night.md` 与脚本文字上补四处断点（V6 accept 行、V7 turn guard 行、V8 退出码、V9 `NO_QUESTION`）；ADR 0032；在隔离 home 跑 U-1、U-2、U-3、U-9、U-17 探针 | 只加不删；hook 命令变了但指向同一批脚本 | 授权 `install.sh`（hook 登记方式变了）；读 ADR 0032 |
| **B1 mode 与白天** | `skills/mmw/`：`SKILL.md`（B1 版，第 2.4 节）、12+14 条原则、`references/`（`slots.md`、`subagent-brief.md`、`writing-code.md`、`skill-set-rules.md`、`reviewing-a-skill-set.md`、`interface-and-remake.md`、`tracker-additions.md`）、`mode-hook.py`（只登记 B0 探针证实能注入的事件）；白天 11 份 playbook（P1–P11）；`upstream-pstack/` 子树、`import_component.py`、导入 `session-pickup`、`pause-safely`；私有 `.mmw/playbooks/` 三份，根 `AGENTS.md` 相应改指针；白天技能回原文（`grilling`、`grill-with-docs`、`codebase-design`、`improve-codebase-architecture`、`setup-matt-pocock-skills`、`writing-for-agents`、`wayfinder`、`prototype`、`triage` 的白天部分、`to-questionnaire`、`handoff`、`grill-me`、残留 `ask-matt`）；`to-spec`、`to-tickets` 分叉；`skills.txt` 的 `+model` 与安装副本；`design-pages/references/state-list-format.md`；`retro` 的四条分拣规则与 `DESTINATIONS` 三项；连线检查第 2、5、7、9 类转为失败 | 夜间角色的文件与提示词都没动：worker 仍读 `implement`，orchestrator 仍读 `night.md`；`to-tickets` 分叉后名字与标题不变，`night.md` 第 141 行的引用照样有效；mode 只点名 B1 时存在的组件 | 授权 `install.sh`（`skills.txt` 变了）；开新会话（H2） |
| **B2 夜间**（同一发布窗口，W1–W3 天然整体） | 票 a：P12–P16、`orchestrator-events.md`、`review-axes/`、`pipeline-issues.md`、`shared-experience`、`setup-mmw`；启动提示词一行与数据文件；唤醒指针、watch 的 `kind`、watchdog、turn guard、`NO_QUESTION`、`REFUSAL`；`resume_at` 删除、`where` 成为唯一；`implement`、`code-review`、`tdd`、`resolving-merge-conflicts` 回原文；`verify-ticket`、`ui-acceptance`、`design-pages`、`advisor`、`exe-release` 剥离；closeout 步骤核对（只报告）。票 b：`dispatch/` 整目录搬进 `mmw/`；`verify-ticket.py` 拆出 `ticket.py`，`events.py` 搬家；`dispatch` 解散；`models.py config get`；第 7.6 节全部调用点；mode 改为 B2 版；连线检查第 3、4、6、11 类与第 10 类「只经 `anchors.py`」转为失败，第 12 类启用 | 启动器按新旧两处路径找 hook 目标，搬家时 hook 不断；两张票同一窗口提升，中间状态不发布。**跑完整套件的理由**（`shared.md` 规则 15）：这批跨启动提示词、relay、hook、票状态脚本四个边界，定向测试覆盖不到「某事件在新 playbook 没有处理行」「某指针对不上」「某个调用点仍指旧路径」三类风险，所以跑 `dispatch`（`test_dispatch.sh all`）、`relay`、`verify-ticket`、`liveness`、`board`、`migrations` 六个完整套件与新 `tests/mmw`，再在隔离 home 用假 tracker 跑一整夜 | 在没有夜在跑时授权「移动 checkout + `install.sh`」（它会重载 `com.mmw.board`）；开新会话（`dispatch`、`implement` 的 description 消失，`code-review` 的 description 改回上游）；挑一个小 spec 跑第一个真实夜并验收；读 downstream-note |
| **B3 pstack 核心** | 能力技能 15 个：`how`、`why`、`architect`、`arena`、`interrogate`、`swarm`、`show-me-your-work`、`unslop`、`figure-it-out`、`no-comments`（及 `agents/comment-sicko.md` 简报）、`technical-writing`、`recall`、`reflect`、`blast-radius`、`typescript-best-practices`；原则 9 条；`dispatch.sh panel`、`panel-wait` 与面板角色；playbook `feature`、`investigation`、`refactoring`、`perf-issue`、`autonomous-run`、`eval`，`bug-fix` 合并；mode `### Imported triggers` 11 行、`## Comments`、「没有匹配」换成 `figure-it-out`；`slots.md` 补行；启动器删旧路径候选；closeout 步骤核对转为拒绝 | 只加组件、路由行与检查 | 授权 `install.sh`（`skills.txt` 与启动器变了）；开新会话 |
| **B4 PR 交付组** | playbook `opening-a-pr`、`babysit`、`shipping`、`worktree-cleanup`；mode reference `bugbot-triage.md`；mode 脚本 `watch-pr/`、`bootstrap.ts`、`package.json`、`bun.lock`、`worktree-audit.sh`；触发行 3 行；根 `AGENTS.md` `## Package Manager` 加 bun | 只加；前三份只在 `delivery: pr` 的仓库出现 | 授权 `install.sh`；装 bun；说出哪些仓库用 PR 交付（第 0.5 节第 4 条） |
| **B5 诊断与验证组** | playbook `runtime-forensics`、`trace-forensics`、`hillclimb`、`visual-parity`；能力技能 `create-verification-skill`、`maintain-verification-skill`；`slots.md` 的 control 行加「仓库自己的验证技能」 | 只加 | 授权 `install.sh`；开新会话 |

---

## 11. 风险与需要的实测

### 11.1 实测（都在隔离的测试 home 里做，不碰已安装 checkout）

| # | 问题 | 为什么重要 | 怎么测 |
|---|---|---|---|
| U-1 | 启动提示词「Use the mmw skill … mmw work-a-ticket#Claim. Data: …」能否让五个宿主的新会话读到 `playbooks/` 下的文件 | 夜间主路径 | 照 ADR 0006 的探针办法：探针 `mmw` 技能带 `playbooks/probe.md`（内含随机标记），各宿主非交互进程发这条提示词，看回复是否出现标记。数据文件已给绝对路径，读不到技能内路径时仍有一条路 |
| U-2 | 各宿主有没有「会话开始（含压缩后）」「子代理开始」「prompt 提交」事件、能否注入一行 | 第 2.3 节的 hook 路径 | 每宿主装只打印标记的探针 hook（经 `mmw-hook`），在有、无 `.mmw/` 的目录各提交一次、压缩一次、派一个子代理，看模型能否复述标记。Codex 能注入是由 `CODEX_CONTEXT_EVENTS` 推出的，一并实测；Claude Code 的 `SubagentStart` 已观察到 |
| U-3 | `mmw/playbooks/*.md`、`principles/*.md` 会不会被某宿主当成技能扫入；「真目录里放软链文件」的安装副本能否被各宿主正常读取 | 原则与 playbook 不进技能列表；第 4.3 节的开关处理 | 探针技能目录下放带 frontmatter 的嵌套 `.md`，另做一个安装副本式目录，看各宿主技能列表（Grok `grok inspect --json`） |
| U-4 | 五个宿主是否都有待办工具与后台子代理 | 执行协议；`slots.md` | 各宿主非交互进程列出可用工具 |
| U-5 | worker、reviewer 每次启动读 mode（约 170–200 行）加 playbook 的上下文成本 | 常驻纪律的代价（R4 曾以此否决 R2） | B1 后量字节；隔离 home 跑一张测试票，比较首个动作前的上下文用量 |
| U-6 | `panel` 起 3 个会话的耗时、费用、夜里收齐的可靠性 | 面板的成本数字（不作为建不建的闸门） | 用 `advise_one` 的机制起 3 个会话，量到齐时间与费用；故意杀掉一个，看 `panel-wait` 报告而不挂住 |
| U-7 | description 数量变化后人起的会话能否找到正确入口 | 头部入口（N10 B1） | 取 N10 第 3.2 节的起点语句各一句，在五个宿主的新会话里看加载了什么，升级前后各一次 |
| U-8 | 各宿主会话记录的位置与格式；Nowledge Mem 的会话记录能否作为来源 | `session-pickup`、`show-me-your-work`、`reflect`、`recall`、`eval` 的 transcript 行 | 各宿主跑短会话找记录文件；`nmem t search` 查同一会话 |
| U-9 | herdr 的 `agent prompt` 收到多行文字时是否按换行拆成几次提交 | 结果决定今天的 herdr 夜是否已有隐患；升级后不依赖它 | 隔离 home 用 herdr 起一个会话送两行文字，看收到一次还是两次提交 |
| U-11 | 启动提示词点名 playbook 后，reviewer 会不会改去加载回到原文的上游 `code-review` | 两者的 description 竞争 | 隔离 home 用假 tracker 跑一张票，看 reviewer 打开了哪些文件；竞争时由 mode 触发行写明「被起为 reviewer 时读 playbook」 |
| U-12 | `--closeout`、`--review` 是否接受 `skip:` 行 | 第 6 节 | 读 `run_closeout`，跑一次 `--closeout --check-only` |
| U-13 | 能否从 `cursor/plugins` 的 `pstack/` 干净切出子树 | 第 8.1 节 | 临时克隆里 `git subtree split --prefix=pstack`，比较切出的树与研究快照 |
| U-15 | 七份 `CONTEXT.md` 里有没有只住在词表里的行为规则 | 这类规则也要按类型搬 | 逐份读 `docs/contexts/*/CONTEXT.md`，对每条词条的 `_Home_` 核对 |
| U-16 | `dispatch.sh where` 在三种 runner、六个角色上每一行的正确率 | 被压缩会话的回路 | 对第 7.7 节表的每一行在假 tracker 上造出事件组合，三种 runner 各跑一次，比对输出 |
| U-17 | hook 进程是否继承 runner 用 `--env` 设的环境变量（`MMW_ROLE`） | `NO_QUESTION` 按角色分句；`mode-hook.py` 少调 `where` | 探针 hook 打印环境变量；不继承就用两条都给的那一句 |

上一版的 U-10（closeout 要不要核对步骤）改为直接建（第 6 节）；U-14（smell baseline 是否重复）已有结论：两份内容相同、读者不同，上游自己也这样写（第 3.3 节 P16）。

### 11.2 风险

- **B2 面大。** 缓解：B0 把启动器、锚点、`where`、连线检查先做成并行实现；W1–W3 同一窗口；六个完整套件加一整夜假 tracker；回退可完全撤销（移回 checkout + 重跑 `install.sh`）。
- **mode 没被读到。** 四条到达路径叠加；B0 先实测；脚本起的会话走确定路径。
- **导入的 pstack 文字与 `shared.md` 冲突。** 优先级句已写；导入时按第 5.4 节判。
- **原则层变长后成了摆设。** 靠点名义务与 `retro`、`reflect` 的 `principle` 去处，让原则被用、被修。
- **偏离 pstack 的五处**，各有理由：原则是文件不是技能（H2）；playbook 多 `**Where you are.**`、`**Entry.**`（H6）；脚本送进会话的指针（H4、H6）；hook 启动器（修已核实的切换窗口）；开关在安装副本里处理（H2，保持子树原文）。
- **你以前的要求「不许过度设计过度防御」**（R17 引 Memory `ce037679`）。本架构新增的机制是九项：`roles.json`、`anchors.py`、`where`、步骤指针、`mode-hook.py`、`mmw-hook` 启动器、`check_wiring.py`、`import_component.py`、`panel`；每项都指名了它修的已核实断点或它满足的导入需求。其余是把现有文字搬到对的层。落地后用 `wc -l` 实测新旧总行数，写进 B2 与 B5 的报告。

---

## 12. 自查：与第一版草图的最低范围逐项对照

| 草图项 | 结果 | 依据 |
|---|---|---|
| 一个 mode：常驻规则 | 超出 | `## Non-negotiables`（含导入触发行）、`## Autonomy`、`## Re-entry`、`## Subagents`；四条到达路径 |
| mode：原则索引 | 达到 | 26 条，B3 后 35 条（pstack 23 条全部），由连线检查与原则文件核对 |
| mode：playbook 路由表 | 达到 | B2 后 18 行，全部批次后 32 行，每行带 Distinct from；另有直接能力行与私有索引 |
| 白天定义 | 超出 | P1，另拆出 P2 地图、P3 界面、P4 原型、P5 直接改动 |
| 夜间编排、做一张票、评审一轮、单票、早上验收与 finish | 达到 | P12、P15、P16、P14、P13 |
| 修 bug | 达到 | P6（B3 合并 pstack 原文） |
| 出包 | 达到（按类型是能力技能） | `exe-release` 的第 1–5 步就是出包的做法，路由表直接指向它（第 3 节判据）；上一版的 P9 只编排它一个能力，按 L7 C.6 信号 5 是形式拆散 |
| 分诊、调研、给仓库接入 MMW、写技能 | 达到 | P7、P8、P9、P11；另有私有 Promote a change、Pull an upstream、Import a component |
| 其他工作流 | 超出 | P10、P17、P18；B3–B5 再进 14 份 |
| 没有匹配的任务 | 达到 | B1–B2 为执行协议加「先列步骤」；B3 起 `figure-it-out` |
| 能力技能只讲一步怎么做、不知道被谁调用 | 达到 | 17 句「下一步」与全部角色句离开；流水线状态离开 `verify-ticket`；连线检查第 3 类强制 |
| 原则层是真正的层，并能承接 pstack 原则 | 超出 | 12 条 MMW 自有 + pstack 23 条全部，同一格式、同一命名空间 |
| 脚本由 playbook 步骤调用 | 达到 | 流水线脚本进 `mmw/scripts/`；位置计算与票状态从能力脚本移到 mode 的脚本；第 11 类查孤立命令 |
| 外来组件直接落位 | 达到 | 八种导入类型；第 13 节全量清单：每个 pstack 组件都有层级、落位、依赖、冲突处理与批次，或不导入的理由；需要判断的改动单独计数 |
| 执行协议 | 达到 | 人在场照抄；无人写进交付物；closeout 核对步骤痕迹 |
| 角色流程留在能力技能里 | 1 个例外 | advisor 的被咨询方，依据 L7 A.5 表第一行与 C.6 信号 5（第 1.4 节）；worker、reviewer、两个 orchestrator 都是 playbook |
| 不小于第一版草图，不重复 R4、R12 的收缩 | 超出 | R4、R12：1 份头部 playbook、5 个角色流程留在能力技能里、2 条原则。本文：B2 后 18 份、全部批次后 32 份 playbook；1 个角色例外；35 条原则；`dispatch` 解散，`verify-ticket` 拆分 |

依赖实测的两项（U-2 hook 注入、U-4 待办工具）都有不依赖实测的备用路径，结构不因实测结果缩小。执行时的缩水由第 10 节的批次验收条件拦住：一段内容留在原处而没有写明 H1–H6 或 S，这张批次票就不能关。

---
## 13. pstack 全量清单与导入核算

### 13.1 全量清单

`docs/research/code-landing-refs/pstack/` 下共 102 项：`skills/` 47 个目录（原则 23、`poteto-mode` 1、其余能力技能 23）、`poteto-mode/playbooks/` 23 份、`poteto-mode/SKILL.md` 按节与触发行拆成 25 项、`poteto-mode/references/` 1 份、`poteto-mode/scripts/` 4 组、`agents/` 2 份、`automations/benny` 1 个（本轮 `ls` 与逐个读 frontmatter、grep 依赖）。「依赖」列只列被点名的组件；槽位一律经 `slots.md`，不再逐行重复。

**mode（`poteto-mode/SKILL.md`）**

| 项 | 层 · 落位 | 冲突与处理 | 批 |
|---|---|---|---|
| frontmatter `mode: true`、`reminder` | mode · `mmw` 技能 + `mode-hook.py` | H1：没有常驻机制 | B1 |
| 第 15 行（点名原则） | mode 首段 | 「leaf SKILL.md」→「file」（J7） | B1 |
| 第 19、20、21、22、23、24、25、27、29、30、35 行触发 | `mode-trigger` · `### Imported triggers` | 第 20 行的 `AskQuestion` 与第 30 行的 control skill 经 `slots.md` | B3 |
| 第 26 行（prose → unslop，回复按 Writing the reply） | MMW 触发行代替 | 给用户的回复归 `shared.md`（S；R13 I-16）（J3） | B3 |
| 第 28 行（`/deslop`） | 不导入 | cursor-team-kit 在 MMW 没有对应物（L7 E.1 第 27 条） | — |
| 第 31、32、33 行（Babysit、Shipping、Bugbot） | `mode-trigger` | 只在 `delivery: pr` 的仓库有意义 | B4 |
| 第 34 行（Broken skill → fix it in its own PR） | 不导入 | 与 H5、H6 冲突：夜里不能改运行中的版本，也没人可问；MMW 触发行「流水线自身出错」已覆盖（synthesizer Already-covered） | — |
| `## Principles` 索引 | mode 索引，逐行由原则 description 生成 | — | B1、B3 |
| `## Autonomy` | 映射到 MMW `## Autonomy`，不复制原文 | 「external actions proceed without asking」与 `shared.md` 规则 1 的「what goes out to the public」冲突，`shared.md` 高（S） | B1 |
| `## Subagents` | 映射到 MMW `## Subagents` 与 `slots.md`；第 95 行两句原文采用 | `poteto-agent`、显式模型 → H3、ADR 0015 | B1 |
| `## Writing the reply` | 第 109 行采用（删半句，J9）；第 101–107 行经 `unslop` 只管英文产物 | S | B1 |
| `## Comments` | `mode-section` | 无 | B3 |
| `## Playbooks` 第 117 行 | 原文采用 | 无 | B1 |
| `## Playbooks` 第 119 行（figure-it-out、Orchestrate） | 改写采用（J2） | Orchestrate 不导入；「steps away」一类由 Run a night 承担 | B3 |
| `references/bugbot-triage.md` | `mode-reference` · `mmw/references/ps/` | 无 | B4 |
| `scripts/watch-pr/`、`bootstrap.ts`、`package.json`、`bun.lock` | `mode-script` · `mmw/scripts/ps/` | 需要 bun（第 8.7 节） | B4 |
| `scripts/worktree-audit.sh` | `mode-script` | 无 | B4 |
| `scripts/check-plan.mjs` | 不导入 | 只服务 `multi-phase-plan.md` | — |
| `scripts/orch/` | 不导入 | 只服务 `orchestrate.md`；它的 store 与 tracker 事件重复 | — |

**能力技能（23）**

| 技能 | 层 · 落位 | 依赖 | 冲突与处理 | 批 |
|---|---|---|---|---|
| `how` | 能力 · `ps/how` +model | 无 | 无 | B3 |
| `why` | 能力 · `ps/why` +model | 无 | 第 62 行 MCP 目录 → `slots.md` | B3 |
| `architect` | 能力 · `ps/architect` +model | `arena`、`how`、`why`、`interrogate`；6 条原则 | 面板角色 → `panel` | B3 |
| `arena` | 能力 · `ps/arena` +model | 无 | 面板与 cross-judge → `panel` | B3 |
| `interrogate` | 能力 · `ps/interrogate` +model | 无 | 面板 → `panel` | B3 |
| `swarm` | 能力 · `ps/swarm` +model | 无 | `pstack-models` → `slots.md` | B3 |
| `show-me-your-work` | 能力 · `ps/show-me-your-work` +model | `encode-lessons-in-structure`、`unslop` | 绑票的会话用票上的事件（`slots.md`） | B3 |
| `unslop` | 能力 · `ps/unslop` +model | 无 | 只管英文产物（S） | B3 |
| `figure-it-out` | 能力 · `ps/figure-it-out` +model | `show-me-your-work`、`architect`、`arena`；7 条原则 | 「poteto-mode 的 Principles」→ 别名读作 `mmw` | B3 |
| `no-comments` | 能力 · `ps/no-comments` +model | `how`、`why`、`architect`；Comment Sicko | Comment Sicko → `agent` 类型 | B3 |
| `technical-writing` | 能力 · `ps/technical-writing` +model | `unslop` | 只管英文文档；回复归 `shared.md` | B3 |
| `recall` | 能力 · `ps/recall` +model | `why`、`session-pickup` | 第 1 步点名 `automate-me` → `slots.md`「没有对应物」；transcript → U-8 | B3 |
| `reflect` | 能力 · `ps/reflect` +model | `encode-lessons-in-structure`；`create-skill` | 与 `retro` 分工见路由行；`create-skill` → `writing-for-agents`；三个 reviewer 的模型 → `panel` | B3 |
| `blast-radius` | 能力 · `ps/blast-radius` +model | 无（本轮 grep） | 无 | B3 |
| `typescript-best-practices` | 能力 · `ps/typescript-best-practices` | `boundary-discipline`、`type-system-discipline` | frontmatter 的 `paths:` 是 Cursor 键；不被点名，不加 `+model`，由用户或按路径触发（U-3 看各宿主是否认 `paths:`） | B3 |
| `create-verification-skill` | 能力 · `ps/create-verification-skill` +model | `maintain-verification-skill` | 生成的技能落到消费仓库，填 `slots.md` 的 control 槽位 | B5 |
| `maintain-verification-skill` | 能力 · `ps/maintain-verification-skill` | `create-verification-skill` | 无 | B5 |
| `tdd` | 不导入 | — | 与 MMW `tdd` 同名；pstack 文字点名 `tdd` 由 MMW 版满足；需要时以 `pstack-tdd` 改名导入 | — |
| `teach` | 不导入 | — | 与 MMW `teach` 同名；它的职能（用 `how`、`why` 解释一块工作）由 `how`、`why`、`wait-what` 覆盖 | — |
| `bro` | 不导入 | — | 职能与 `wait-what` 相同 | — |
| `setup-pstack` | 不导入 | — | 职能由 `setup-mmw` 承担 | — |
| `automate-me` | 不导入 | — | 它把用户的工作方式写成个人 mode 技能；MMW 里这是 `shared.md`，由用户维护（S） | — |
| `make-bot-ui` | 不导入 | — | 对象是 Grok Bot 的 webhook 页面，MMW 没有这个入口；无依赖，需要时按能力技能单独导入 | — |

**原则（23）**：B1 导入 14 条（`prove-it-works`、`fix-root-causes`、`attack-the-premise`、`redesign-from-first-principles`、`laziness-protocol`、`subtract-before-you-add`、`migrate-callers-then-delete-legacy-apis`、`test-behavior-not-implementation`、`separate-before-serializing-shared-state`、`make-operations-idempotent`、`encode-lessons-in-structure`、`build-the-lever`、`guard-the-context-window`、`never-block-on-the-human`）；B3 导入 9 条（`sequence-verifiable-units`、`model-the-domain`、`foundational-thinking`、`exhaust-the-design-space`、`outcome-oriented-execution`、`minimize-reader-load`、`boundary-discipline`、`type-system-discipline`、`experience-first`）。落位 `mmw/principles/`；每条机械改动为删开关行一处加相对链接改写（`build-the-lever` 3 处、`attack-the-premise` 4 处）；冲突：`never-block-on-the-human` 的 `**Boundaries:**` 由 mode 优先级句处理，`experience-first` 由 mode 的产品限定句处理（J6），其余与 MMW 规则的重合按第 5.4 节。原则之间的依赖（`build-the-lever` → `encode-lessons-in-structure`、`laziness-protocol`、`prove-it-works`，均 B1）不跨批悬空。

**playbook（23）**

| playbook | 层 · 落位 | 依赖 | 冲突与处理 | 批 |
|---|---|---|---|---|
| `session-pickup` | playbook · 原文 | 2 条原则 | transcript → `slots.md` | B1 |
| `pause-safely` | playbook · 原文 | 无 | 无 | B1 |
| `authoring-a-skill` | 合并，MMW 版 | `create-skill`、`encode-lessons-in-structure` | 「skip the reason」与 `skill-set-rules.md` 事实 1 冲突（J5） | B1 |
| `prototype` | 合并，MMW 版 | `exhaust-the-design-space`（B3 前是悬空点名，所以 B1 的 MMW 版不点名它） | 第 3 步 scratch 目录与 `prototype` 规则 1 冲突；「Hand to Feature」改为 MMW 的去处（J1） | B1 |
| `bug-fix` | 合并：原文 + 补充步 | `how`、`why`、`architect`、`tdd`、`sequence-verifiable-units` | 同名；MMW 的选路进补充步（J4） | B3 |
| `feature` | playbook · 原文 | `how`、`architect`、`arena`、`interrogate`；3 条原则；`## Comments` | 第 6 步 rebase → `slots.md`；「Laziness Protocol」按解析规则 | B3 |
| `investigation` | playbook · 原文 | `how`、`why`、`unslop` | 无 | B3 |
| `refactoring` | playbook · 原文 | `how`、`architect`、`figure-it-out`；9 条原则 | 与「代码架构整理的普查」路由行分工（普查找候选，Refactoring 执行一次） | B3 |
| `perf-issue` | playbook · 原文 | control、`how`、`architect`、`sequence-verifiable-units` | 与 `diagnosing-bugs` 分工：`diagnosing-bugs` description 含 performance regressions；Perf issue 是有基线数字的改进，反馈循环难建时读 `diagnosing-bugs`（`slots.md`） | B3 |
| `autonomous-run` | playbook · 原文 | `sequence-verifiable-units`、`show-me-your-work` | 第 4 步「via poteto-mode」按别名；与 Run a night 分工见路由行；本仓库 watch 期间受 H5 触发行约束 | B3 |
| `eval` | playbook · 原文 | `arena`（Phase B、C） | 候选跑在不同模型上 → `panel`；transcript → `slots.md` | B3 |
| `opening-a-pr` | playbook · 原文 | `interrogate`、`no-comments`、`technical-writing`、`unslop` | 没有所有权行与 `**Reply:**`（L7 C.6 信号 5 所记的例外）；`/deslop`、`gt` → `slots.md` | B4 |
| `babysit` | playbook · 原文 | `bugbot-triage.md`、`watch-pr`、`shipping` | 需要 bun | B4 |
| `shipping` | playbook · 原文 | `watch-pr`、`babysit`、control | cloud agent → `slots.md`；不替换夜的落地（第 8.4 节） | B4 |
| `worktree-cleanup` | playbook · 原文 | `worktree-audit.sh`；4 条原则 | 不删 `issue-<n>`、`merge-<branch>`，watch 开着时不删本仓库的 worktree（`slots.md` worktree 行，J10） | B4 |
| `runtime-forensics` | playbook · 原文 | control、`guard-the-context-window` | 与 `diagnosing-bugs` 分工：交付物是诊断，不是修复 | B5 |
| `trace-forensics` | playbook · 原文 | `guard-the-context-window` | 无 | B5 |
| `hillclimb` | playbook · 原文 | `how`、`show-me-your-work`；6 条原则 | 与 Perf issue 分工（原文 Distinct from） | B5 |
| `visual-parity` | playbook · 原文 | control、`separate-before-serializing-shared-state` | 与 Design an interface、`ui-acceptance` 的 story parity 分工：两套实现之间的像素一致 | B5 |
| `autopilot-full` | 不导入 | — | 同一任务类型由 Run a night 原生承担（一票一 worker、orchestrator 裁决）；依赖 cloud agent 与 PR 合并；第 6 步运行中从 trunk 重读自己，与 H5 冲突 | — |
| `autopilot-stack` | 不导入 | — | 同上；它按编号引用 `autopilot-full` | — |
| `orchestrate` | 不导入 | — | 多日项目由 Map a large effort 加逐份 spec 的夜承担；`orch` store 与 tracker 事件是两份状态 | — |
| `multi-phase-plan` | 不导入 | — | 「计划是逐框执行的清单」在 MMW 是已发布的 spec 与带 `CHECK` 的票（Define a change）；模板要求每个 tick 从 trunk 重读，与 H5 冲突 | — |

**agent 与 automation**

| 项 | 处理 | 批 |
|---|---|---|
| `agents/poteto-agent.md` | 不导入：它的内容是「先读 mode」，由 `SubagentStart` 注入与简报首句在五个宿主上覆盖；自定义 agent 文件只在部分宿主存在 | — |
| `agents/comment-sicko.md` | `agent` 类型 · `mmw/references/ps/agents/comment-sicko.md` | B3 |
| `automations/benny` | 不导入：入口是 Slack 频道里的新报告，出口是 draft PR；MMW 的对应入口是 Triage an issue 与夜。若将来有 Slack 入口，按 L7 C.1 第 7 问作为单入口自动化导入，它的 control-adapter 契约是 `slots.md` control 行的参照 | — |
| `docs/guide/` | pstack 的使用说明，不是组件；作为 ADR 0034 的来源 | — |

**合计**：导入能力技能 17、原则 23、playbook 文件 17（其中 `bug-fix` 以合并方式进入）、另 2 份同名 playbook 并入 MMW 版、mode 触发行原文 14、mode 小节 1、mode reference 1、mode 脚本 2 组、agent 简报 1；映射到 MMW 对应小节的 mode 项 8；不导入 16 项（能力技能 6、playbook 4、触发行 2、mode 脚本 2、agent 1、automation 1），每项理由在表里。

### 13.2 需要判断的改动（全部）

| # | 位置 | 改动 | 批 |
|---|---|---|---|
| J1 | `playbooks/prototype.md` | MMW 版，吸收 pstack 第 1、6 步与 Reply，去掉「throwaway」与「Hand to Feature」 | B1 |
| J2 | mode `## Playbooks` 没有匹配 | pstack 第 119 行去掉 Orchestrate 与「steps away」两句 | B3 |
| J3 | mode 触发行 | 用 MMW 的「英文产物 → unslop」代替 pstack 第 26 行 | B3 |
| J4 | `playbooks/bug-fix.md` | 原文第 6 步前插入 **Choose the route** | B3 |
| J5 | `playbooks/authoring-a-skill.md` | 保留 MMW 版，吸收 pstack 第 2 步与末段一句 | B1 |
| J6 | mode `## Autonomy` | `experience-first` 的产品限定句 | B3 |
| J7 | mode `## Non-negotiables` 首段 | 「leaf SKILL.md」→「file」 | B1 |
| J8 | mode `## Principles` 首句 | 「leaf skill」→「principle file」 | B1 |
| J9 | mode `## Writing the reply` | 删「PR link as …」半句 | B1 |
| J10 | `slots.md` worktree 行 | `worktree-cleanup` 不删流水线的 worktree | B4 |

共 10 处，每处记入 `imports.tsv` 的「判断改动」列与 `merge-notes/pstack.md`。机械改动（删开关行、改相对链接、`ps/` 路径改写、由 description 生成索引行）由 `import_component.py` 做，不计在内。

### 13.3 每批导入实际要改的文件（B3 为例）

| 类型 | 数量 | 要改或新增的文件 |
|---|---|---|
| `skill` | 15 | `skills.txt` 15 行（13 行带 `+model`）；`imports.tsv` 15 行；安装副本由 `install.sh` 生成 |
| `principle` | 9 | `mmw/principles/` 9 个新文件；mode 索引 9 行；`imports.tsv` 9 行 |
| `playbook` | 6 新 + 1 合并 | `mmw/playbooks/` 6 个新文件、`bug-fix.md` 替换；路由表 6 行；`imports.tsv` 7 行；`merge-notes/pstack.md` 一条（J4） |
| `mode-trigger` | 11 | mode `### Imported triggers` 11 行；`imports.tsv` 11 行 |
| `mode-section` | 1 | mode `## Comments`；`imports.tsv` 1 行 |
| `agent` | 1 | `mmw/references/ps/agents/comment-sicko.md`；`slots.md` 1 行 |
| MMW 自己的改动 | — | mode「没有匹配」一条（J2）、unslop 触发行（J3）、`## Autonomy` 一句（J6）；直接能力行 4 条；`slots.md` 约 10 行（面板角色、`pstack-models.mdc`、`mcps/`、`automate-me`、rebase、`Binary-search`、Comment Sicko、`create-skill`、transcript、`/deslop`）；`dispatch.sh` 的 `panel`、`panel-wait`；`models.json` 面板角色 |

依据的原文：本轮读了 `bug-fix`、`feature`、`prototype`、`refactoring`、`perf-issue`、`visual-parity`、`investigation`、`session-pickup`、`pause-safely`、`authoring-a-skill`、`autonomous-run`、`eval` 全文，`figure-it-out`、`reflect`、`recall`、`teach`、`tdd` 全文，其余组件读了 frontmatter、开头几行与依赖 grep（第 15 节）。B4、B5 的计数是按依赖 grep 推断的，各批的 **Import a component** 第 2 步逐文件核实。

---

## 14. 第一轮评审的处理（摘要）

| 评审 | 条目 | 处理 |
|---|---|---|
| 1 / R15 | 批 1 发布的 playbook 点名批 4 才建的原则 | 12 条 MMW 原则与 14 条 pstack 原则、mode 索引都在 B1 |
| 1 / R15 | B1 先写 MMW 版 `session-pickup`、`pause-safely` | B1 连同子树直接导入 pstack 原文 |
| 1 / R15 | 上游保留的「能力扩展」只按标签留下 | 本轮对表中每一项都读了 `git diff`（第 4.2 节） |
| 2 / R15 | 任务板四个文件写死 `skills/dispatch/scripts` | 第 7.6 节列全，改从 `anchors.py` 取 |
| 2 / R15 | hook 路径切换窗口会拦住本机每条命令 | B0 的 `mmw-hook` 启动器 |
| 2 / R15 | U-9 推断方向错了 | herdr 经 `send` → `agent prompt` 送第一条提示词；启动提示词一律一行 |
| 1 / R16 | D5 押在未实测的 U-1 上；原则文件照留开关 | 不采用；开关在安装副本里处理，原则文件删开关行 |
| 2 / R16 | B2 就转失败，B2–B3 间套件全红 | 连线检查按类别在各自对象建成那一批转为失败 |
| 2 / R16 | orchestrator 轨迹写进 TSV 是新格式 | 写在 spec 的评论里 |
| 1、2 / R17 | `dispatch` 原名原位；`roles.json` 被能力脚本向上读 | 解散；读 `roles.json` 的脚本都在 `mmw/` 里 |
| 2 / R17 | Codex `PostCompact` 被当成可注入事件 | 不登记；各宿主能否注入统一由 U-2 实测 |
| 2 / R17 | 「回退不需要重装」；`roles.json` 缺失时的行为没定 | 回退重跑 `install.sh`；缺失即拒绝并指向 `install.sh --check` |
| 2 / R15 | `own_session()` 找不到就静默返回 `None` | 第二轮改为：随 `verify-ticket` 拆分删除，`ticket.py` 与 `dispatch.sh` 同目录（第 7.6 节） |

---

## 15. 本轮读了什么、没读什么

**本轮回到原文或源码核实的**：

- MMW：`skills.txt`；`dispatch/SKILL.md`、`references/night.md`（全文 210 行）、`one-ticket.md`、`inside-a-ticket.md`；`dispatch.sh` 第 95–112、1720–1760、1935–2005、2185–2220 行与 `self`、`adopt` 相关行；三个 runner 的 `self_` 与调 `models.py` 的行；`models.py` 第 18–34 行；`status.py` 第 1–60 行与全部函数名；`relay.py` 第 250–302、380–390 行；`watchdog.py` 第 90–112、805–816 行；`tool-guard.py` 第 1–80、136–156 行；`turn-guard.py` 第 125–145、218–236、300–340 行；`verify-ticket.py` 第 245–260、825–848、1980–1990、2140–2200、4100–4253 行与全部 `post_event` 位置；`events.py` 第 100–175 行；`verify-ticket/SKILL.md`；`code-review/references/session.md` 与四个 axis 文件；squash `5b1a4c51` 的 `code-review`、`implement` 原文；`advisor` 三份；`pipeline-issues.md`、`interface-and-remake.md`、`several-specs.md`、`revising-a-spec.md`；`exe-release/SKILL.md` 与 `driving.md` 第 1–20 行；`triage/SKILL.md` 第 60–100 行；`design-pages/SKILL.md` 与 `pull.md`、`draw.md`、`edit-pages.md` 的小节；`retro/SKILL.md` `## Decide`；残留 `ask-matt/SKILL.md` 第 1–60 行；`research/SKILL.md` 开头；`SKILL-SET-RULES.md` 的小节表与第 95–105 行；`prototype`、`setup-matt-pocock-skills`、`teach`、`wait-what`、`wizard`、`grill-me`、`handoff` 与 squash 原文的 `git diff`；24 个上游技能在 squash 原文与现状中的开关计数；`install.sh` 第 145–170、760–800、935–960、1420–1432 行与全部 `dispatch/scripts` 字面；`board/` 四个文件、`migrations/remove-verifier.py`、`tests/lib/check_own_skill_frontmatter.py` 第 50–66 行；`tests/` 下引用 `dispatch/scripts` 的 14 个文件与 `test_tool_guard.py` 第 435–450 行；`~/.claude/settings.json` 第 38–90 行。
- pstack：`poteto-mode/SKILL.md` 全文；12 份 playbook 全文（见第 13.3 节），其余 11 份的开头与依赖 grep；`figure-it-out`、`reflect`（含 `synthesizer.md` 开头）、`recall`、`teach`、`tdd` 全文；47 个技能目录的 frontmatter、文件列表与开关计数；`agents/` 两份；`automations/benny` 的 `README.md` 与 `FOR_AGENTS.md`。
- 报告：L7 `### A.5`、`### A.6`、`### B.2`、`## C`；R13 E11 与 I-6。

**没有读全文、结论据此标为推断的**：`status.py` 的函数体（`--where` 的实现细节）；`driving.md` 第 20 行以后、`key.md`、`new-product.md`（它们都留在 `exe-release`，不影响归属）；pstack 的 `autopilot-full`、`autopilot-stack`、`babysit`、`shipping`、`opening-a-pr`、`orchestrate`、`multi-phase-plan`、`hillclimb`、`runtime-forensics`、`trace-forensics`、`worktree-cleanup` 的全文，以及 `architect`、`arena`、`interrogate`、`how`、`why`、`swarm`、`show-me-your-work`、`unslop`、`no-comments`、`technical-writing`、`blast-radius`、两个 verification 技能的全文（`how` 至 `unslop` 七个的依赖另见 R16 的阅读）。B4、B5 的判断改动数与 B3 的 `slots.md` 行数依赖这些文件，各批的 **Import a component** 第 2 步逐文件核实；按第 10 节的验收条件，核实中发现的内容只能落到某一层，不能不带理由地留下。

---

## 16. 纳入 issue #591：调研由 `researcher` 角色另起会话完成

**问题（issue #591 原文，已读）。** `wayfinder` 的 `### Chart the map` 第 5 步把调研票派给宿主自带的通用子代理（今天的 `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 第 76、114 行）。2026-09-29 在 agentflow map #1000 上，4 个调研子代理都在 Write 一步被 Claude Code 拒绝（`Subagents should return findings as text, not write report files.`），主会话代写了报告、评论与关票。同时，按角色选宿主（issue 要求调研跑在 Codex 上）这一层在 2026-08-19 重新接入上游时丢了。`research` 技能第 6 行「Spin up a **background agent** to do the research」还会让被派出的 agent 再派一层（上游 mattpocock/skills #530）。

**这件事在新架构里的位置。** 它正好是新架构要消除的三种混层：一项能力（`research`）自己决定谁来执行；一个能力技能（`wayfinder`）写着流水线怎样派会话；角色（调研者）没有 `roles.json` 行与 `models.json` 行。修法因此不是给 `wayfinder` 打补丁，而是按层落位：

| 层 | 改动 | 依据 |
|---|---|---|
| 角色 | `mmw/roles.json` 加 `researcher`：`playbook: research-a-question`，`models_row: researcher`，`started_by: dispatch.sh research <n>`，`wakes: {}`（一次性会话，同 reviewer）。`hosts.json` `defaults` 加一行 `researcher`：codex、`gpt 6 sol`、`high`（照今天 `senior-worker` 行，issue #591 A 节）。`models.py` `ALLOWED_AGENTS` 加 `researcher` | 第 7.1 节「角色 = playbook + `models.json` 一行」；H3：要跨厂商只能另起会话 |
| 脚本 | `dispatch.sh research <n>`：照 `advise_one` 的写法（`use_runner`、`use_catalog_of`、`row_for_role researcher`、`start_session`），启动提示词一行：`Use the mmw skill. Role researcher, ticket #<n>, unattended: mmw research-a-question#Name the decision. Data: <文件路径>.`（第 2.3 节的形状；H4）。打印会话 id，不写票的事件（同 advisor）。**工作树**：用 `ensure_workspace` 一类函数建在 `.worktrees/research-<n>`，分支 `research/<n>`。不用 `issue-<n>`：`tool-guard.py` 按目录名 `issue-<n>` 生效（第 34、136–139 行，已核实），会拦下调研会话自己关票；每张调研票一个工作树，并行的调研会话与画 map 的会话互不共用工作区 | issue #591 D 节第 1 条的建议，并按 `tool-guard.py` 的目录判定选定目录名 |
| playbook P8 **Research a question** | 两个入口。人在场：本会话自己跑 `research`，不另开会话。`researcher` 角色：启动提示词点名。步骤：1 **Name the decision it feeds.**（地图上的票、spec `## Sources` 或 ADR）2 **Run the research.** `research` 能力，在本会话里读一手来源（**principle-clues-are-not-evidence**）。3 **Commit the report.** 报告写进仓库的调研目录，提交到 `research/<n>` 并推送。4 **Answer on the ticket.** resolution comment 给出分支上的文件链接与三句结论，然后关票。5 **Leave the map alone.** 不改 map 正文（**principle-separate-before-serializing-shared-state**：map 正文只有一个写者，#35 两次丢行是并发写的实例）。**Reply / 交付物**：推送的报告、resolution comment、关闭的票 | issue #591 C、D 节；`research` 三步；#35 |
| playbook P2 **Map a large effort** | 第 2 步 **Resolve one decision ticket at a time** 中「调研票 → **Research a question**」改为：每张调研票跑一次 `dispatch.sh research <n>`，派完不等回报，结束这一步。新增第 0 步 **Collect finished research.**（每次推进地图的会话开头做）：已关闭、但 Decisions-so-far 里还没有指针的调研票，逐条补上指向报告的指针。这是 map 正文唯一的写者 | issue #591 D 节第 2 条；**principle-separate-before-serializing-shared-state** |
| 能力 `research`（上游） | 删第 6 行「Spin up a **background agent** …」；第 8 行「Its job:」改成不指代 agent 的引导语；三步正文与 description 不动。记入新 merge-note `merge-notes/research.md`：要不要另开上下文由调用方决定（第 4.5 节「能力技能不写谁来执行」），并避免上游 #530 的嵌套派发 | 第 4.3 节第 2 类（能力改动，带 merge-note） |
| 能力 `wayfinder`（上游） | 回原文时，第 5 步与 `## Ticket Types` 的 Research 一条保留一处宿主中立改写：「Hand each research ticket to a separate session that can commit files and close the ticket; a subagent that must return findings as text cannot.」不点名 `dispatch`、不点名宿主。`merge-notes/wayfinder.md` 记：这是对上游 #763（改由画 map 的会话派子代理）的有意偏离，理由是 Claude Code 子代理不能在项目里新建报告文件（#591 现场）与按角色选宿主 | 第 4.3 节第 1 类（宿主中立，H1）；第 4.5 节 |
| 任务板 | `mmw-v2/board/page/local-config.mjs` 的 `agents` 列表加 `researcher`；核对 `docs/specs/task-board/screen-contract.yaml` 与 `prototypes/task-board/` 的设置页场景是否要加这一行，要加就补 downstream-note | issue #591 A 节 |
| 测试 | `tests/dispatch/test_dispatch.sh` 照 `scenario_advise` 加 `scenario_research`（起会话、打印 id；缺 `researcher` 行时拒绝并说明怎么补；工作树名不是 `issue-<n>`）；`test_local_config.py`、`test_profiles.py`、`tests/board/test_settings_api.py` 中按角色全集断言的地方加 `researcher`；`tests/mmw` 的 `roles.json` 一致性检查覆盖新角色 | issue #591 A 节；第 7.5 节 |
| 词表 | `docs/contexts/night/CONTEXT.md` 第 10 行「pipeline 启动的 agent」加 researcher，照第 106 行 `dispatch.sh advise` 的写法给 `dispatch.sh research <n>` 一条词条 | issue #591 A 节 |

**放进哪一批。** #591 是正在发生的故障（map #1000），不等 B2：

- **B0** 加角色与脚本：`researcher` 的 `hosts.json` 默认行、`ALLOWED_AGENTS`、`roles.json` 登记、`dispatch.sh research <n>`（此时在 `dispatch/scripts/`，B2 随整目录搬家）、任务板与测试、词表。
- **B1** 写 P2、P8 的新步骤；`research`、`wayfinder` 回原文时带上上表两处改动与两份 merge-note。B0 到 B1 之间，`wayfinder` 第 5 步的现有文字把「spin up your host's own general-purpose subagent」改成「run `dispatch.sh research <n>`」作为过渡（一处替换，B1 回原文时被上表的宿主中立句取代）。
- 发布后本机 `~/.mmw/models.json` 不会自动补新行：需要你授权跑一次 `models.py config set researcher codex "gpt 6 sol" high`，或在任务板设置页加这一行。

**验证。** `bash mmw-v2/tests/dispatch/run.sh`、`bash mmw-v2/tests/board/run.sh`；文字按 `references/skill-set-rules.md` `## Verifying` 走一遍：一个新会话只拿到一张真实调研票与「推进这张地图」的请求，看它能否起会话、写报告、推分支、发评论、关票，下一次推进地图时补上指针，中途不需要猜。

## 17. 用户的决定（2026-09-29，布置图页面上的六条备注）

以下决定优先于本文前面各节的对应写法；写 spec 时以本节为准。

| # | 问题 | 决定 | 对本文的影响 |
|---|---|---|---|
| D1 | B0 发布后给 `~/.mmw/models.json` 加 `researcher` 一行 | 加 | 第 16 节照做；发布步骤里执行 `models.py config set researcher codex "gpt 6 sol" high` |
| D2 | 是否有仓库改用 PR 交付 | 不用。MMW 现行交付（closeout → `advance` 合进 project branch → 用户验收 → `finish`）已覆盖 pstack `shipping.md` 九步的意图（第 8.4 节对照），单人、无 CI 的仓库用 PR 只多一层 | 删去 `delivery: pr` 取值与 `opening-a-pr`、`babysit`、`shipping` 三份导入、`bugbot-triage.md`、`watch-pr/`、bun（第 8.4、8.7 节，第 10 节 B4）；`deliver-a-change` 只保留 `commit` 与 `playbook:<slug>`；`slots.md` 的 delivery 行写「Opening a PR → **Deliver a change**」；`worktree-cleanup` 改为按需导入 |
| D3 | Cursor | 不考虑。现役宿主以 `~/.mmw/models.json` 为准：Claude Code（reviewer、advisor）、Codex（senior-worker）、Grok（junior-worker），runner 是 Orca | H1 的宿主清单收窄为这三个；删去 mode `## Autonomy` 里「为 Cursor 抄一次产品事项清单」一条（第 2.2、5.5 节），mode 只点名 `shared.md` 规则号；`mode-hook.py` 的「判断是不是 Cursor」一句删去；探针 U-1–U-4 只测这三个宿主 |
| D4 | 消费仓库 `AGENTS.md` 是否加一行指向 `mmw` | 不加。人起的会话用 `/mmw`，或由 `mmw` 的 description 被加载 | 删去第 2.3 节人起会话的第 ③ 条路径、第 1.2 节消费仓库 `AGENTS.md` 那一行、`dispatch.sh check` 的缺行提示；`onboard-a-repository` 第 2 步不写这一行 |
| D5 | B2 的发布时机与验收 | 不需要用户选择。B2 只在没有 watch 开着时发布；发布前在隔离 home 用假 tracker 跑一整夜（第 10 节已有）；发布后用户照常跑的下一个 spec 就是验收夜 | 第 0.5 节第 2 条删去 |
| D6 | pstack 导入 | 按需，先不要让 pstack 的东西过多进入 | B3–B5 全部改为按需，每次由用户点名要导入的组件，走私有 playbook **Import a component**；B1 只导入被 MMW 自写 playbook 或能力技能点名的 pstack 原则（第 5.3 节 B1 行里「MMW 调用方」一列非空的那些），`session-pickup`、`pause-safely` 两份 playbook 推迟到按需；`upstream-pstack/` 子树、`import_component.py`、`slots.md` 照建，它们是按需导入的前提 |
| D7 | pstack 的扩展工具箱（`reflect`、`eval`、`figure-it-out`、`automate-me`、`show-me-your-work`、`create-verification-skill`、`maintain-verification-skill`）与多模型面板 `dispatch.sh panel` 是否提进核心批次 | 不提，全部保持按需，不让这次改造过于复杂 | 核心批次只到 B0–B2；`dispatch.sh panel`、`panel-wait` 与 `models.json` 面板角色随第一个需要它的组件按需加入；`slots.md` 的 `automate-me` 一行保持「按需时再定对应物」 |
| D8 | 任务面板（`mmw-v2/board/`）怎样读 MMW | 面板只经稳定接口读 MMW：跨目录的路径从 `anchors.py` 取，「一张票现在在哪一步」从 `dispatch.sh where` 取，角色从 `roles.json` 取；不写死技能目录里的文件位置 | 第 7.6 节 `board/` 四处改路径时按此写；面板以后可以直接显示的新信息（角色与模型、每张票当前在 playbook 的哪一步、原则索引、`imports.tsv`）不在本次范围，另开 spec |
| D9 | 技能文本的写作与命名 | 技能文本同时遵守 pstack 的文本结构与 mattpocock 的写作方式，由写 spec 之前定稿的写作规范（`R20-writing-style-guide.md`）与范本（`docs/research/workflow-compare/exemplars/`）作票的基准；搬运的句子逐字保留，由逐字搬运检查与结构 lint 强制（`R21-text-integrity-checks.md`，进 B0）。MMW 自有的技能、reference、脚本趁这次系统改名，按用户过目的改名表（`R19-naming-table.md`）执行；上游 mattpocock 与 pstack 的名字不改 | 所有搬文字的票都带搬运清单与这两道检查；改名在搬家的同一张票里做 |
| D10 | mode 技能的名字 | `mmw`（用户在 2026-09-29 夜间授权 Claude 自行完成剩余决定，此项由 Claude 代定，待用户复核）。理由：用户在设计评审里对 D4 的问题写过「我直接调用新建的 mmw 技能不就可以了吗」，D4 也已写「人起的会话用 `/mmw`」；R20 第 5.1 节与 R21 的示例已经用 `skills/mmw/` 与指针前缀 `mmw <slug>#<Step title>`，命令也更短。放弃 R19 建议的 `mmw-mode`，它的理由与留下的代价写在 R19「用户过目」一节 | R19 第 4.1、4.9、7 节与「用户过目」一节按 `mmw` 写：目录 `skills/mmw/`，套件 `tests/mmw`，指针前缀 `mmw <slug>#<Step title>` |

R19、R20、R21 定稿后，与本文不同之处以它们为准：

- 改名以 R19 为准（例：`anchors.py`→`locations.py`、`ticket.py`→`ticket_state.py`、`mmw-hook`→`hook-launcher`、`shared-experience`→`memory-records`、`slots.md`→`pstack-names.md`、`ps/`→`pstack/`、`+model`→`+model-invoked`、playbook `define-a-change`→`write-a-spec-and-tickets` 等，全表见 R19 第 4 节）。
- 连线检查第 3 类的句型部分、第 4 类、第 7 类的逐文件部分改由结构 lint `check_component_structure.py` 实现，B0 起失败并靠例外表过渡（R21 第 4.4 节）。
- 三道文字检查共用套件 `tests/skill-text`，不另开 `tests/wiring`（R21 第 6 节）。
- 评审简报保留现名 `<axis>-reviewer.md`，不改为 `review-axes/`（R19 第 4.5 节）。

## 审查记录

第二轮审查共 41 条，逐条回原文核实。

1. **导入接口没有 mode 本身的落位**——采纳。第 8.2 节改为八种类型，新增 `mode-trigger`（`### Imported triggers`）、`mode-section`、`mode-reference`（`mmw/references/ps/`）、`mode-script`（`mmw/scripts/ps/`）、`agent`。核实：pstack mode 第 19–35 行的触发、`babysit.md` 等引 `../references/bugbot-triage.md`、`worktree-cleanup.md` 引 `scripts/worktree-audit.sh`，属实。第 13 节按类型重算，判断改动如实计为 10 处。
2. **只演示了部分 pstack 组件**——采纳。第 13.1 节全量清单 102 项，每项有层级、落位、依赖、冲突处理与批次，或不导入的理由；审查列出的同名与职能冲突（`tdd`、`teach`、`prototype`、`refactoring`、`perf-issue`、`visual-parity`、`reflect`、`opening-a-pr`）逐个处理；`benny` 判定为不导入并写明理由。
3. **没有学到 figure-it-out**——采纳。核实 pstack mode 第 119 行原文属实。B3 导入 `figure-it-out`，mode「没有匹配」路由到它（J2）；B1、B2 期间用执行协议加「先列步骤」一句（来源：pstack mode 第 117 行与 `figure-it-out` 第 9 行），失去逐步纪律的空档消除。
4. **多模型面板推迟到 B5**——采纳。核实 H3 只要求另起会话，`advise_one` 已有先例，没有硬约束支持推迟。`panel` 并进 B3，与 `arena`、`interrogate`、`architect`、`reflect`、`eval` 同批；U-6 只量耗时、费用与可靠性。
5. **`verify-ticket` 标为「本层」未经重判**——采纳。核实 `events.py` 第 143–169 行定义 dispatch 阶段与 watchdog 事件，`status.py` 第 40 行、`relay.py` 第 258 行按路径加载它，属实。拆出 `mmw/scripts/ticket.py` 与 `events.py`；`verify-ticket` 留跑判据、lint、发布与 `issue_tree.py`。与审查建议的差别：发布留在能力里（本轮核实 `run_publish_*` 不写事件，`to-spec`、`to-tickets` 调用它）；`--lint` 是否读事件由 B2 票核实。
6. **hook 搬进 `hooks/` 后相对导入会断**——采纳。核实 `tool-guard.py` 第 57–62 行、`turn-guard.py` 第 135–139、224、231 行属实。hook 与其他脚本平放在 `mmw/scripts/`；连线检查第 10 类存在性在 B0 就失败；验收加「两个 hook 能导入全部同伴模块」。
7. **把「读原文后再定去处」推迟到批次票**——采纳。本轮读完审查列出的文件（`night.md` 全文、四个 axis 文件、`advising.md`、`consulting.md`、`pipeline-issues.md`、`interface-and-remake.md`、`several-specs.md`、`revising-a-spec.md`，`prototype`、`setup-matt-pocock-skills`、`teach`、`wait-what`、`wizard` 的 diff），据此改了 `several-specs.md`（循环进 P1）、`consulting.md`（去掉 `dispatch` 一句）、P3 的来源（`改动分类` 在 `pull.md`，不在 `edit-pages.md`）、`setup-matt-pocock-skills` 的去处。`status.py` 函数体与 `driving.md` 后半没有读全，第 15 节写明；判据同时写进 ADR 0032 与第 10 节每张批次票的验收条件。
8. **调用开关没有一致执行**——采纳。核实 `setup-matt-pocock-skills`、`handoff`、`wait-what`、`grill-me`、`teach` 现状都带开关，属实。它们都被点名要模型调用，一律加 `+model`；只有 `improve-codebase-architecture`、`grill-with-docs` 保持用户触发，点名处写「告诉用户运行」。第 9 节汇总逐个列出。
9. **advisor 的操作文件留在能力技能里**——部分采纳。采用审查给的第二种办法：列为 1 个例外，依据 L7 A.5 表第一行（交给另一个代理的简报放 reference）与 C.6 信号 5（只编排一个能力的 playbook 是形式拆散），第 12 节不再写「0」。不写 `advise-a-decision.md`：它只会复述 `advising.md`，与第 35 条撤掉 P9 的理由相同。
10. **`bug-fix` 替换与 `sequence-verifiable-units` 的本地限定**——采纳。(1) 选路作为合并时插入原文的一步（J4），不进 mode；(2) 数字前后不一已随之消失；(3) rebase 的读法写进 `slots.md` 与 mode 触发行，每个读导入文字的会话都读得到。人在场的会话里 rebase 自己的未推送提交不受影响，限定只在票的工作树里生效。
11. **发布四步留在 AGENTS.md**——采纳。四步搬进 `.mmw/playbooks/promote-a-change.md`；P10 只按 `delivery` 分支，取值 `commit | pr | playbook:<slug>`（审查建议的 `promote` 泛化成「指名一份私有 playbook」，其他仓库也能用）；根 `AGENTS.md` 留一行指针与 H5 那一句。
12. **`SKILL-SET-RULES.md` 搬出技能后在其他仓库读不到**——采纳。核实 P11 第 1 步点名它、`writing-for-agents` 第 8 行按相对路径指向它，属实。放到 `mmw/references/skill-set-rules.md`，`docs/skill-set.md` 留指针。
13. **E11 只学了一半**——采纳。核实 `retro/SKILL.md` `## Decide`（第 117 行起）只有 MMW 的门槛。B1 把四条分拣规则写进 `## Decide`；`reflect` 在 B3 导入，路由表加「复盘这个会话」一行。
14. **U-10 推迟**——采纳。推迟依据是可重审的旧规则，不是 H1–H6。closeout 的步骤核对 B2 只报告，B3 起拒绝（第 6 节）。
15. **bun 交给用户决定**——采纳。改为工程决定：引入 bun，只供 `mmw/scripts/ps/`；放弃 node 重写（分叉、丢测试）。用户只需装 bun。
16. **事实与表述误差**——采纳。(1) 核实 pstack 原则 23 条、各带 1 处开关，已改；(2) 第 0.2 节写全导入一个能力技能的实际改动；(3) 开关改在 `install.sh` 生成的安装副本里去掉，子树原文不动（第 4.3 节）；(4) `models.py` 留在 `mmw/scripts/`，文件数改为 16。
17. **路由表漏了几类工作流**——采纳。核实 `design-pages` description 含「comments are queued」「a design system is to be built」。新增 P4 **Prototype**（分 LOGIC、UI、EXP 三个去处）；设计系统为直接能力行；排队的评论作为 P3 的入口与第 2 步。
18. **`models.py`、`hosts.json` 搬进 `setup-mmw` 会让起会话全部失败**——采纳。核实三个 runner 的 `$(dirname "$HERE")/models.py`、`models.py` 第 23–30 行、`migrations/remove-verifier.py` 第 16–22 行属实。`models.py`、`hosts.json` 与 runner、`statedir.py` 一起平移到 `mmw/`；`setup-mmw` 按命令点名；第 10 类加 shell 的 `dirname` 与 `$SKILL_ROOT` 写法。
19. **两个 hook 搬进子目录会静默失效**——采纳。同第 6 条；B0、B2 的验收加「在隔离 home 经启动器调用两个 hook，确认 `gh issue close` 与提问确实被拒」。
20. **启动器找不到目标时一律退出 2**——采纳。核实 `~/.claude/settings.json` 第 43、53、85 行的 Grok 前缀属实。改为按 hook 分别处理：`mode-hook`、`turn-guard` 放行；`tool-guard` 只对 `issue-<n>` 会话拒绝，写明取舍；登记新命令时保留 Grok 前缀。
21. **`own_session()` 改为拒绝**——部分采纳。采纳「去掉向上调用」：`own_session()` 随 `verify-ticket` 拆分删除，`ticket.py` 与 `dispatch.sh` 同目录。不采纳「由 `dispatch.sh start` 写 `MMW_SESSION`」：本轮核实会话号是 runner 起会话后才有的（`orca.sh` 读 `ORCA_TERMINAL_HANDLE`，`paseo.sh` 读 `PASEO_AGENT_ID`，`herdr.sh` 读 `HERDR_PANE_ID`，都由 runner 设置），`start` 在起会话前写不出来。L7 引用已改正；另注明 L7 B.2 表里「脚本 → 脚本」是「导入、测试」，决定这一条的是 E3，不是硬规律 2。
22. **`where` 答不出若干步**——采纳。核实 `resume_at` 在全新与第 5 步之后都返回 `None`、spec 级事件只有五种、`status.py` 只有六种形式，属实。第 7.7 节写出「事件 → 步骤」表，输出分 `AT`、`BETWEEN`、`FRESH`、`UNKNOWN`；不新增事件，不留事件的步骤都可重跑；表登记进 `anchors.py`；U-16 实测正确率。
23. **B1 的 mode 点名 B2 才建的组件**——采纳。第 2.4 节写出各批 mode 的内容：B1 的 `## Re-entry` 与触发行指向 `dispatch` 技能里当时真实存在的脚本与文件；连线检查第 2 类在每批发布前对 mode 跑一遍。
24. **唤醒与告警的指针前后不一**——采纳。核实 `one-ticket.md` 第 3 步、`inside-a-ticket.md` `## After the closeout`、`relay.py` `WAKES` 属实。`roles.json` 改为按（角色，事件）登记；watch 加 `kind`；新增角色 `self-picked-worker`；第 6 类检查核对每个（角色，事件）恰好一个处理处。
25. **`ps/` 前缀会让全部套件变红**——采纳。核实 `check_own_skill_frontmatter.py` 第 56–62 行、`install.sh` 第 150–153 行属实。两处同批（B1 引入子树时）认 `ps/` 与 `+model`，加反例测试。
26. **测试与迁移的改动面少算**——采纳，数字有出入。本轮 grep 到 14 个测试文件（审查写 13，多出 `tests/board/test_supervisor.py`），分在 5 个套件，加 `migrations` 套件间接依赖；`install.sh` 第 1428 行已列。B2 完整套件改为六个，并按规则 15 写明理由。
27. **自托管时冻结版本可能被绕过**——采纳。数据文件写出已安装 checkout 里 playbook 与脚本的绝对路径；mode `## Re-entry` 写明不用工作树里的同名文件；连线检查第 12 类核对。
28. **`NO_QUESTION` 覆盖 advisor 的说法不对**——部分采纳。核实 `tool-guard.py` 只管 `issue-<n>` 目录的会话，属实，已去掉「覆盖 advisor」。不采纳「按工作目录区分 worker 与 reviewer」：`governed_ticket()` 的 docstring 写明「Reviewer and worker share that directory」，工作目录区分不了。改为按 `dispatch.sh start` 写进会话环境的 `MMW_ROLE` 分句，读不到时两条都给（U-17）；`test_tool_guard.py` 第 442–447 行的断言列进 B2。
29. **出处与标注的准确性**——部分采纳。(1)(2) 改引文并加改动标注；(3) 同第 16 条；(5) Codex 能注入改标「推断」，并入 U-2；(6) 全文不再用 lever 指脚本；(7) 同第 16 条。(4) 驳回其结论、采纳其补充：「the prompt keeps the data」原文在 `### Prompts written for other agents` 第 2 条，上一版引第 2 条没错；第 1 条的「Rules reach the agent through the skill it loads」同样支持，现在两条都引。
30. **启动提示词数据里写死旧小节名**——采纳。核实 `dispatch.sh` 第 1741、1747–1751 行属实。列进第 7.6 节，改从 `anchors.py` 取，指向 `shared-experience` 与 `review-a-ticket#Active Rules`。
31. **`mode-hook.py` 的触发范围**——采纳。三种事件都先查 MMW 仓库标记；`where` 只在 `issue-<n>` 目录或 `watches.json` 有本会话时调用（第 2.3 节末段）。
32. **「你要做的」一列漏项**——采纳。核实 `supervisor.py` 第 18 行在导入时绑定、`install.sh` 第 940–955 行只在 plist 变化或任务没在跑时 bootstrap，属实。B2 加「开新会话」，由 `install.sh` 重载 `com.mmw.board`；B3 改为必须授权 `install.sh`（启动器是复制的文件）。
33. **导入的 pstack playbook 过不了自己的骨架检查**——采纳。核实 pstack `bug-fix.md` 等步骤没有粗体标题属实。第 7 类对 `imports.tsv` 登记的导入 playbook 只查 `### <Name>` 与 `**Reply:**`；指针只指 MMW 自写的 playbook 与 mode；第 4 类不查导入文字；「0 处」改为如实计数。
34. **axis 子代理简报被拆散**——采纳。核实上游 `code-review` 原文第 63 行「pasted in full (the sub-agent has no other access to it)」、`session.md` 第 25–29 行属实。Standards 简报保留自带的 smell baseline；P16 第 2 步写出新的一行提示；axis 子代理不加 `subagent-brief.md` 首句。
35. **P9 是空壳**——采纳。核实 `exe-release` 第 1–5 步是出包的做法本身。P9 删除，路由表改为直接指向 `exe-release`；playbook 重新编号：新增 P4 Prototype，原 P4–P8 顺延为 P5–P9，P10 起编号不变。
36. **`bug-fix` 的选路被拆进 mode 触发行**——采纳。同第 10 条：选路是合并时插入的一步；`diagnosing-bugs` 与 pstack 第 2 步的关系写进 `slots.md`（它是第 2 步反馈循环的做法）。
37. **`rerun-dont-reroute` 两个家、说法矛盾**——采纳。改名 `route-faults-dont-bypass`，只留「故障按路由上报、不绕路」与 `shared.md` 规则 11 的划界；「原样重跑」是 mode `## Re-entry` 第 1 步的操作文字，点名 `make-operations-idempotent`；第 5.2 节删掉「PC17（使用一侧）」。
38. **P15 的 `reviewer.reported` 有两个处理处**——采纳。删掉 `#### When something wakes you` 规则簇；`roles.json` 按（角色，事件）登记，`reviewer.reported`、`reviewer.lost` 只由 **Get reviewed** 处理；第 2.3 节示例与之一致。
39. **步骤正文按编号引用别的文件**——采纳。P6（原 P5）改为「`diagnosing-bugs`，先建一个能变红的命令」；P7（原 P6）合为一步，按标题引用 `## Triage a specific issue or PR`；P12 改为「mode `## Re-entry`（到 ack 为止）」。
40. **优先级句与所有权行没有来源**——采纳。优先级句注明是新写的工程决定，依据 L7 C.2，记入 ADR 0032，并加「能力技能的人工闸门在无人会话里走本角色的无人出路」，消除与第 4.5 节的冲突。所有权行逐条补出处：P5 取残留 `ask-matt` 第 26 行，P6 取 pstack `bug-fix.md`，P7 取 `triage` 第 2 步，P13 取 `night.md` 第 188、200 行，P14 取 `one-ticket.md` 第 3 行；P8 找不到出处，不写。
41. **`writing-code.md` 的来源句绑定 worker 的 closeout**——采纳。核实 `implement` 第 24–26 行属实。第 24、25 行的具体动作原样保留，按第 5.4 节第 1 条加点名；第 26 行留在 P15 `#### While writing code`，P5 把同样的理由写在 Reply 里。
42. **定稿对齐（不是审查意见）**：按 R21 第 7 节第 1 行，第 17 节表后加一段，写明 R19、R20、R21 与本文不同之处以它们为准，其中连线检查第 3、4、7 类与结构 lint 的分工以 R21 第 4.4 节为准；第 7.5 节与第 50 行的正文没有改，读者按那一段读。第 17 节另加 D10（mode 技能名 `mmw`），由 Claude 在用户授权下代定，待用户复核。
