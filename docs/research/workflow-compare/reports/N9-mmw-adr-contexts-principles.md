# N9 清点：ADR、词表（contexts）与原则候选

单元范围：`docs/adr/` 的 31 份 ADR 与 `docs/adr/README.md`；`CONTEXT-MAP.md` 与 `docs/contexts/*/CONTEXT.md`（7 份）；`CODING_STANDARDS.md`；`TESTING.md`；`mmw-v2/prompt/shared.md`。本轮只清点事实，不做归置决定。

## 0. 读法与核实标记

- **读了什么。** 31 份 ADR 全文（每份的 `# ` 标题、标题下一段、`## Considered Options`、`## Consequences`，以及 0003、0006、0014 标题上方的 `>` 注）；`docs/adr/README.md` 全文；`CONTEXT-MAP.md` 全文；7 份 `CONTEXT.md` 全文（toolbox 434 行、night 433 行、ticket-run 331 行、tickets 364 行、ui-acceptance 417 行、task-board 107 行、release 168 行）；`CODING_STANDARDS.md`、`TESTING.md`、`mmw-v2/prompt/shared.md` 全文。
- **为核对「在技能文本里出现在哪」读了什么。** 用 `mmw-v2/skills.txt` 列出的已安装技能（`diagram-design` 除外）的全部 102 个 `.md` 文件做 grep；命中处读了上下文段落。整段读过的技能文本：`implement/SKILL.md` 第 15–110 行、`dispatch/SKILL.md` 第 1–30 行、`dispatch/references/night.md` 第 1–12、104–140 行、`ui-acceptance/SKILL.md` 第 28–38 行、`advisor/SKILL.md` 与两份 reference 前段、`to-tickets/SKILL.md` 第 80–90 行、`code-review/references/session.md` 第 99–101 行、`verify-ticket/references/sub-issues.md` 第 1–20 行、`writing-for-agents/SKILL-SET-RULES.md` 全文。脚本只读了文件头注释与命中行（`dispatch.sh` 第 95–116 行的 start prompt 常量、`ui-acceptance/scripts/refusal.py` 第 1–30 行）。
- **未读。** `docs/contexts/night/how-it-works.md`（93 行，在 `docs/contexts/` 下但不是 `CONTEXT.md`，不在给定范围内）；`mmw-v2/prompt/README.md` 与 `render.py`。
- **标记。** 「已核实」= 本轮回到原文或运行只读命令确认；「未核实」= 只来自线索材料；「推断」= 由原文推出、原文没有写明。grep 次数是本轮在上述 102 个文件上的结果。

---

## 1. 部件清单

### 1.1 目录与规范文件

| 文件 | 是什么 | 给谁用、何时读 |
| --- | --- | --- |
| `docs/adr/README.md` | ADR 的写法（`## 一份 ADR 长什么样`：frontmatter `date`/`amends`，决定写在 `# ` 标题及其下一段，不写 `## Decision`，必有 `## Considered Options` 与 `## Consequences`）、31 行索引表（含「改写了哪几份 / 被哪几份改写」两列）、两代旧编号翻译表、删除批次记录 | 写 ADR 的人；在本仓干活、要判断某份 ADR 现行效力的 agent（`AGENTS.md` `## External References` 把「ADR shape, the index」指到这里，已核实） |
| `CONTEXT-MAP.md` | 词表总目：一个词汇、七个 bounded context；词条读法（粗体名、`_Avoid_`、`_Home_`，`_Home_` 与词条冲突时以 `_Home_` 为准）；写词条的规矩；7 个 context 的一句话范围与 7 条关系 | 改词汇前的人与 agent（`AGENTS.md` 要求先读）；`implement` 开工读入时（`implement/SKILL.md` 第 16 行「the `CONTEXT.md` of each context `CONTEXT-MAP.md` lists that this ticket touches」） |
| `docs/contexts/toolbox/CONTEXT.md` | 工具箱作为仓库与安装目标的词汇：host、subagent、安装位置、subtree、merge-note、`models.json`、`install.sh`、hooks、refusal、skill-set review 的 21 个术语、code-checkers 与 manage-agents-md 的术语 | 同上；`writing-for-agents` 的复审者（`SKILL-SET-RULES.md` `### Vocabulary` 末条：「In MMW the glossary is `CONTEXT-MAP.md` and `docs/contexts/<name>/CONTEXT.md`」） |
| `docs/contexts/night/CONTEXT.md` | 夜的词汇：orchestrator、runner/adapter、worktree 与分支、`dispatch.sh` 各动词、relay/watch/wake/ack、watchdog/turn guard、retro 词汇 | 同上 |
| `docs/contexts/ticket-run/CONTEXT.md` | 一张票从认领到关闭的词汇：worker/reviewer/advisor、Memory 索引、事件与 fold/hold、closing comment 固定行、code review 词汇、preflight 与 closeout | 同上 |
| `docs/contexts/tickets/CONTEXT.md` | spec 与 ticket 的写法词汇：worker grade、spec 各节、ticket 各节、acceptance criterion 各行、blocking edge/frontier、label 与 queue、lint | 同上 |
| `docs/contexts/ui-acceptance/CONTEXT.md` | 设计侧（Claude Design、design package、scene）、oracle（story/boundary/journey/harness guard）、screen contract、product answers、lease | 同上 |
| `docs/contexts/task-board/CONTEXT.md` | 本地任务板页面自己的词汇（lamp、phase pill、canvas edge、settings sheet 等；按提交 `3a0d813e`（2026-09-29 10:33，本轮读取之后）为准，左栏词条已由 **The Night** 改名 **Maps & specs**） | 同上 |
| `docs/contexts/release/CONTEXT.md` | `exe-release` 的词汇：release manifest、release engine/loop、`where` 状态、tier、circuit breaker、budget、stage、build hook | 同上 |
| `CODING_STANDARDS.md` | 本仓代码写法：`## Skills and scripts` 4 条、`## State and configuration` 5 条 | code-review 的 Standards axis 每次评审必读（`code-review/references/standards-reviewer.md` 第 9 行，已核实）；票的 `## Read first` 可点名其中几节（`to-tickets/SKILL.md` 第 174 行） |
| `TESTING.md` | 本仓测试规矩：`## What a test proves`、`## Layout`、`## Which suites a change needs` | Tests axis 每次评审必读（`tests-reviewer.md` 第 31 行，已核实）；写 MMW 自身测试的人 |
| `mmw-v2/prompt/shared.md` | 用户级提示词正文：读者的五个事实、一段「无人会话」前言、15 条规则（Who decides what 1–3，How to report 4–9，How to work 10–15）、结尾一段 | Claude Code（`~/.claude/CLAUDE.md` 软链到安装检出里的此文件，已用 `ls -la` 核实）、Codex、Pi、Grok（`render.py` 生成物）的每一个会话、每一回合常驻；Cursor 不在内（ADR 0007 正文：「Cursor 不在此列，它的用户级提示词只能在 app 里手动粘贴」） |

### 1.2 31 份 ADR

「现行」= 决定仍在约束当前代码；「部分改写」= 决定核心仍在，Consequences 里若干条被后续 ADR 改写；「作废」= 索引写明整份作废；「挂起」= 所依附的技能已退役。「活读者」= 运行时哪个 agent 在什么情况下会读它（大多数只由维护者读）。

| 编号 | 决定（`# ` 标题的意思） | Consequences 要点 | 状态（出处：README 索引与正文） | 活读者 |
| --- | --- | --- | --- | --- |
| 0001 | 同一内容在 tracker 与仓库两处时，权威副本在生产它的一侧；另一侧是写下那刻的快照；两侧都不单独作为行动依据 | decision ticket 结论评论是长期产物；tracker 正文被下游按位置读的节固定标题，生产方定字面、读取方引同一字面；spec 发布后原 issue 以链接评论关闭 | 现行 | 维护者；`relay.py` 注释引用（grep 已核实） |
| 0002 | 界面 QA 的 A3/B1 押在 DESIGN.md 格式规范上，不押在生成工具上 | 规范 alpha，爆炸半径只 A3/B1；校验器版本钉死一条被 0004 推翻 | 挂起（`deprecated/ui-qa`，README 表下注） | 无 |
| 0003 | MMW 不打包成插件，由 `install.sh` 散装 | 版本号闸门删除；插件命名空间消失；卸载由安装器按清单负责 | 决定现行，正文数字与交付面已过时（标题上 `>` 注指向 0006、0015） | 无（`install.sh` 实现） |
| 0004 | 设计系统文件可不可信由校验结果定（三档：拒收 / 只能参考 / 可用），不由来源定 | 爆炸半径加三档分级；依赖检查单独判 `SKILL.md` 在不在 | 挂起 | 无 |
| 0005 | docs 层过继到 v2：tracker 配置落地，ADR 编号取最大号 + 1，索引手工维护，不再调冻结区 CLI | 冻结区零调用；engineering 技能 tracker 前置检查成立；README 重建 | 现行；但「在根 AGENTS.md 落 `## Agent skills` 块」这条后果今已不成立（`AGENTS.md` 无此节，grep 已核实），没有后续 ADR 记录这一变化 | 维护者 |
| 0006 | 技能装进 `~/.agents/skills`，只为 Claude Code 再装 `~/.claude/skills` | 软链数；四个 host 私有 `skills/` 目录退役并由 `install.sh` 摘除；撞名规则 | 现行（正文三处 subagent 说法由 0015 作废，`>` 注写明） | `install.sh`；toolbox CONTEXT `~/.agents/skills` 的 `_Home_` |
| 0007 | 用户级提示词源放在仓库（`shared.md` + `hosts/<host>.md`），host 目录只放软链或生成物 | `--check` 比对生成物；首次 `--adopt`；手改生成物 `render.py` 退 2；Cowork 会话跳过软链 | 现行 | `install.sh`、`render.py` |
| 0008 | 流水线每道闸口：拒绝要点名事实、给唯一出路，且不许靠什么都不做通过 | 新增闸口要跑一遍失败路径；列出已按此改过的地方；测试套件自身也受此约束 | 现行；正文说消息三段结构「写在 `mmw-v2/skills/verify-ticket/scripts/refusal.py`」，该路径不存在，实际文件是 `mmw-v2/skills/ui-acceptance/scripts/refusal.py`（find 已核实）；正文列举的 `hook.py`、`board.py` 今已不在活层 | 被 5 个脚本注释引用（`relay.py:79`、`watchdog.py:10`、`journey.py:17`、`refusal.py:19`、`events.py:36`）；`CODING_STANDARDS.md` 引用 |
| 0009 | 夜间编排迁到 Paseo：脚本只做工具，判断归 main agent（今称 orchestrator） | 动词表；`install.sh` 摘上一代残留；`status.py` 只读 | 原则现行；Paseo 细节由 0010、0018、0019 改写 | 维护者 |
| 0010 | agent 之间靠事件互相叫醒，谁都不许轮询另一个 agent | 「状态落地与告诉需要知道的人在同一次脚本调用里」「agent 永远不轮询另一个会话」；`advance` 写成随时可重跑 | 核心现行；机制（`notifyOnFinish`、`notify_parent`）由 0020 改写 | merge-notes（code-review、implement）引用 |
| 0011 | 界面等价在组件级离线判定，整机只跑三到五条旅程 | 外观判据不起产品；消费仓库迁移；「半年后再发明……的人，读这一份」 | 部分改写（0028）；正文「比较原语留在 `visual-parity.py`」今不成立：该文件在活层与仓库中都不存在（find 已核实），无后续 ADR 记录 | 维护者 |
| 0012 | out-of-ticket review finding 按四步门槛（加第 0 步）路由，先匹配者胜，默认自己改 | 收口轮写在 `night.md` 第 4 步；自己改的守三条可审计规则；推翻证据是什么 | 现行（被 0023 改写落地位置）；正文引用的 `mmw-v2/skills/drive-target/scripts/refusal.py` 不存在 | 程序本体在 `night.md` §4（已核实与 ADR 同义） |
| 0013 | reviewer 的报告落地与报信是同一次脚本调用 | `#<n> REVIEW` 首行 | 整份作废（0020） | 无 |
| 0014 | advisor 只有一扇门：正文是技能，调用方与回答方共用 | 只读靠文字；advisor 在调用方 workspace 里跑 | 现行（第三条后果由 0015 作废，`>` 注写明） | 维护者 |
| 0015 | 工具箱不再交付 subagent，用 host 自带的通用 subagent | 三个 axis subagent 只读靠 reference 首句；`models.py` 跟技能走；各 host `agents/` 退役 | 现行（被 0016 改写一句） | 维护者；toolbox CONTEXT `subagent` 的 `_Home_` |
| 0016 | 会话怎么起写在本机活表 `~/.mmw/models.md` | —— | 整份作废（0024） | 无 |
| 0017 | 这一夜没有任何时钟（删 heartbeat 与 `land --sweep`） | 没人叫醒时夜停在原地，早上 `advance` 接着走 | 现行（叫醒来源由 0020 改写） | 维护者 |
| 0018 | runner 收进一条边界：三个动词（加 `stop`），一 runner 一适配器，选择是本机一行配置；起会话被拒就是终点，不重试、不换 host、不换 runner | 加 runner = 写适配器；0009、0016 的若干条改写 | 现行（被 0019、0020、0024、0026 改写部分后果） | 维护者；`CODING_STANDARDS.md` 第 3 条同义 |
| 0019 | 票的状态是其事件的 fold；评论首行不再是协议；谁在跑写在票上 | `status.py` 只读 tracker；verifier 判决经脚本（后被 0026 取消） | 现行 | `events.py`（代码本体）；ticket-run CONTEXT |
| 0020 | 唤醒从 board 发出：relay 读票上结果事件，经 runner 的 send 送到等它的会话；任何脚本都不再报信 | 0013 作废；0010 核心不变；runner 加 `self` 动词；代价（最多晚 30 秒等） | 现行（被 0021、0022、0026 改写） | merge-note implement 引用 |
| 0021 | 判活分三层（turn guard、watchdog、问沉默票的 runner），都不是 agent，`worker.lost` 只由 watchdog 写 | 实测表在 `turn-guard.py` 头；Codex `trusted_hash`；host 整个崩掉只有人能发现 | 现行（被 0022、0026 改写） | 维护者 |
| 0022 | 一个仓库一个 relay，同时看多个 watch，每个 watch 叫醒开它的 orchestrator；等槽位的 worker 也由 relay 叫醒 | `recipient.json` 删除；0021 改三处；升级要先停旧 relay | 现行 | 维护者 |
| 0023 | base branch 以 origin 为准：先合、再查、再 fast-forward 推送，合不进去交 triage | `ticket.landed` 只在 push 成功后写；`ticket.bounced` 保留 worktree；`MMW_BASE_REF` | 现行（被 0025、0027 改写） | 维护者；CODING_STANDARDS 第 4 条（State）同义 |
| 0024 | 会话配置只存进 `models.json`；runner 附加操作也只经适配器 | 0016 作废；写入加锁、版本比对、原子替换 | 现行（被 0026 改写角色数） | 维护者；CODING_STANDARDS 第 1 条（State）同义 |
| 0025 | 开夜记住并推送 project branch；用户验收后 `finish` 把 base branch 合回并清理 | `spec.merged` 是重跑边界；保留签出 base branch 的 worktree | 现行 | 维护者；`night.md` 第 192 行起的 `finish` |
| 0026 | 取消 verifier 会话；worker 在 review 后对最终 commit 跑全部 criteria，closeout 核验这次运行 | 每票少一会话；`--reverify --actor` 必填；迁移脚本 | 现行；「接受的风险」写明用户 2026-09-14 接受「worker 可在 final run 前改写 `CHECK:`」 | `implement` 第 4 步（final run） |
| 0027 | 同一夜第一次 landing conflict 交回 worker 队列，第二次才交 triage | `NIGHT SUMMARY` `Bounced:` 只列仍 `needs-triage` 的；一夜最多自动承担一次 integration | 现行 | `dispatch.sh` 注释引用；`night.md:87` |
| 0028 | 外观按 `data-ui` id 做 element parity；boundary test 断言四列；product answers 只写不变要求；judge 不遮不藏；journey 第二遍只弄坏一个接口 | 消费仓库迁移 downstream-notes 449–456；「半年后再发明……的人，读这一份」 | 现行 | 维护者 |
| 0029 | 设计的唯一源头是 Claude Design 项目，仓库里的 design package 只由 pull 写入 | 设计改动只在 Claude Design；DESIGN.md 不再是设计源头 | 现行（被 0030 改写）；正文说「设计时截图检查与 pull report 承担」，`design-pages` 各 reference 中没有 screenshot 检查（grep 已核实；README 表下注已改指 `pull.md` `## Design problems in the report` 与 `edit-pages.md` `## Sign-off`，这两个标题存在，已核实） | 维护者；ui-acceptance CONTEXT `DESIGN.md` 的 `_Home_` |
| 0030 | design system 由 Claude Design 里的 agent 从产品代码提炼，只装外观；设计页不加载产品代码 | `design-system.md` 改写；两脚本删除 | 现行 | 维护者；理由已部分写回 `design-pages`（见 §4 D13） |
| 0031 | worker 开工拿两份有上限的 Memory 索引；相关经验用 `## Owns` 路径与标题短查询搜出 | worker 写 Memory 必须在「证据」里写路径；运行中搜索也只用报错/命令/组件并放 `--` 后 | 现行（README 日期 2026-09-18 排在 0030 之后，编号与日期顺序不一致，属事实，不影响效力） | `implement` `## Shared experience while implementing`（第 38–60 行同义，已核实） |

**技能 `.md` 文本不引用本仓任何 ADR 编号**（grep `docs/adr/0` 与 `ADR 00` 于 102 个技能文件：零命中，`ADR-0007` 仅是上游示例文字）。引用本仓 ADR 的活文件只有：5 个脚本注释、`CODING_STANDARDS.md`、3 份 `CONTEXT.md` 的 `_Home_`、`install.sh`、4 份 merge-note、`docs/contexts/night/how-it-works.md`（已核实）。

---

## 2. 内容分类

本单元没有 `SKILL.md` 或 reference。所给七种类型之外自拟一种：**定义**（词条：一个名字是什么、与邻词区别在哪）。

### 2.1 ADR（31 份，结构统一）

| 段 | 类型 | 谁在何时读 | 每次运行都读？ |
| --- | --- | --- | --- |
| frontmatter `date`、`amends` | 命令与接口（索引用的元数据） | 维护者判断效力时 | 否 |
| 标题上方 `>` 注（0003、0006、0014） | 沉积（「现行读法见……」「正文写的是当时的状态」） | 维护者 | 否 |
| `# ` 标题 + 下一段 | 带理由的规则 / 目的与立场（这就是决定本身，README 规定别处引用时引这两样） | 维护者；票的 `## Read first` 列出某 ADR 时由 worker 读（`implement/SKILL.md:16`「an ADR's decision in the untitled paragraph under its title」）；夜里处理 `contract` 子票时按权威顺序读（`night.md:98`「decision tickets and ADRs, then the spec…」） | 否，只在被点名的分支 |
| 自由标题节（「要修的是什么」「这条规则是从哪一批故障里得出的」等） | 目的与立场 + 价值证据（事故、实测数字） | 维护者 | 否 |
| `## Considered Options` | 带理由的规则（否决项及理由；多处是日后能成为原则的句子，如 0008「给了选项的 agent 会自己发明第六个」、0018「一个自信的错误答案比『不知道』坏」、0029「禁令比正向做法更容易被读成该做的事」） | 维护者 | 否 |
| `## Consequences` | 混合：命令与接口（事件名、退出码、文件名）、带理由的规则、沉积（「改写了 0010 的第四条」「以前的夜建出来的 heartbeat……」） | 维护者 | 否 |

各 ADR 里「沉积」最重的：0003（整体是 2026-08-18 状态）、0006（数字过时）、0010、0017、0020（大段改写说明）、0015（逐条作废其他 ADR 的句子）。按 README 与 `shared.md` 规则 13，ADR 的主题就是决定与变更，所以这些记录是其主题，不算违规（`shared.md` 规则 13 明写 ADR 例外）。

### 2.2 `docs/adr/README.md`

| 节 | 类型 | 读者 |
| --- | --- | --- |
| 首句「手工维护……」 | 做法 | 写 ADR 的人 |
| `## 一份 ADR 长什么样` | 格式与模板 | 写 ADR 的人（`AGENTS.md` External References 指来；`docs/agents/domain.md` `## Flag ADR conflicts` 指来） |
| 索引表 | 命令与接口（编号、amends 关系） | 判断现行效力的人 |
| 表下注（0002/0004 挂起、0011 推翻的是 #115） | 沉积 + 重入与分派（告诉读者该改读哪里） | 同上 |
| `## 编号在本仓库以外仍会出现` | 重入与分派（旧编号翻译） | 读历史 issue/commit 的人 |
| `## 删过哪几批` | 沉积 | 维护者 |

### 2.3 `CONTEXT-MAP.md` 与 7 份 `CONTEXT.md`

| 段 | 类型 | 读者与时刻 |
| --- | --- | --- |
| `CONTEXT-MAP.md` 第 1–5 行（一个词汇七个 context；`_Home_` 为准；词条不重复 `_Home_` 能读到的东西；「只在用户定过或 `_Home_` 证实后才写定义」「只把真错的词放进 `_Avoid_`」） | 带理由的规则（理由原文：「specs and tickets take their wording from these entries, a night worker names code after them… every word listed there becomes a correction someone will make」） | 写词条的人；改词汇前的 agent |
| `## Contexts` | 重入与分派（找哪份） | 同上；`implement` 读入时选 context |
| `## Relationships` | 连线（context 之间谁读谁） | 同上 |
| 每份 `CONTEXT.md` 开头段 | 目的与立场（该 context 管什么；ticket-run 开头「Everything this part of the pipeline knows is written on the ticket, where the next session reads it with an empty context」是一条带理由的规则） | 同上 |
| 各 `### ` 分组下的词条 | 定义；词条的名字多为命令与接口（事件名、脚本名、字段名、输出行） | `implement` 读入（只读本票触及的 context）；Standards axis（`standards-reviewer.md:9` 的 domain glossary）；`domain-modeling`、`grill-with-docs`；writing-for-agents 的复审 |

词条里嵌着的**行为规则**（按 `SKILL-SET-RULES.md:80`「A behaviour rule found only in the glossary is evidence of intended behaviour」逐条查了它们在技能文本里是否也在）：

| 词条 | 嵌着的规则 | 技能文本里是否也有（grep） |
| --- | --- | --- |
| ticket-run **unreadable event** | 读不懂的事件块从不当散文，依 fold 决定的命令一律拒绝 | 脚本 `events.py:36` 实现并引 ADR 0008；技能文本无（不需要：脚本拒绝） |
| night **evidence_checked** | 缺的来源只缩小分析，从不当作「没发生」的证据 | 有：`retro/SKILL.md:47` |
| ui-acceptance **`harness_markers`** | `[]` 是合法答案，缺键不是默认值 | 有：`ui-acceptance/references/harness-guard.md:10-11` |
| ui-acceptance **`stop`** | 这是一次运行结束进程的唯一方式 | 有：`ui-acceptance/SKILL.md:32` 规则 1 |
| ui-acceptance **release** (lease) | 有监听者时拒绝，因为从活进程收回就是杀它 | 脚本 `lease.py`；技能文本规则 1 同义 |
| toolbox **permission mode** | 没有只读档，所以不能写的 agent 是被告知只读的 subagent | 有：code-review 四个 axis 文件第 3 行、`advisor/references/advising.md` `## What you never do` |
| ticket-run **reviewer Rules** | Rules 决定查什么，每条 finding 仍需当前来源 | 有：`code-review/references/session.md:101` |
| ticket-run **semantic-conflict angles** | 别票的 passed 结论是跑过什么的证据，不是组合正确的证明 | 有：`code-review/references/spec-reviewer.md:22` |
| night **retro problem** / **earlier occurrence** | 没有一手来源证明的问题不记录；同票两条事件算一次 | 有：`retro/SKILL.md` 第 60–70 行 |
| ticket-run **`Audit`** | 按用户读 closing comment 的方式核对；不自己算 `Counts:` | 有：`implement/SKILL.md` 第 5 步 |

未见「只在词表里、技能文本没有」的行为规则（在上表范围内；未对 400 余条词条逐条做此核对，见 §11）。

### 2.4 `CODING_STANDARDS.md`

| 段 | 类型 | 读者 |
| --- | --- | --- |
| 开头段 | 目的与立场（Standards axis 应用这些；票携带塑造它工作的几条） | Standards axis 每次；worker 仅当 `## Read first` 点名 |
| Skills and scripts 1（技能目录整个软链进各 host，只放 agent 读或跑的东西） | 带理由的规则 | 写技能/脚本的人 |
| Skills and scripts 2（脚本从自身位置找邻居；绝对路径只许固定用户级位置与 `mktemp`） | 做法（理由隐含：推断为「技能目录被软链、被拷走」） | 同上 |
| Skills and scripts 3（runner 命令只在适配器；`# MMW_USES:` 是权威清单） | 带理由的规则（理由在 ADR 0018，不在此文件） | 同上 |
| Skills and scripts 4（拒绝三段；查不了要说查不了；脚本头记实测不记文档声称） | 带理由的规则（引 ADR 0008） | 同上 |
| State and configuration 1–2（`models.json` 唯一写入口与锁；`~/.mmw` 另外两样；`MMW_HOME` 由 `statedir.py` `home()` 读） | 命令与接口 + 规则 | 同上 |
| State 3（fold；每个事件由脚本贴，模型一个不敲；靠 relay 互相叫醒，没人轮询，夜没有时钟） | 带理由的规则（理由在 ADR 0010/0017/0019/0020） | 同上 |
| State 4（在 `origin/<base branch>` 落地；冲突或红检查成 `ticket.bounced`；合回默认分支不是 MMW 的事） | 带理由的规则 | 同上 |
| State 5（`~/.cursor/mcp.json` 的 `nowledge-mem` 条目去掉 `type` 字段） | 做法 + 价值证据（症状：worker 静默没有 memory 工具） | `install.sh` 维护者 |

### 2.5 `TESTING.md`

| 段 | 类型 | 读者 |
| --- | --- | --- |
| 开头段 | 目的 | Tests axis 每次 |
| `## What a test proves` | 带理由的规则（理由：钉措辞让每次改好文字都要改测试，且绿测试什么都没证明） | Tests axis；写 MMW 测试的人 |
| `## Layout` | 做法 + 命令与接口（`mmw-v2/tests/<name>/`；gate-check 例外；`MMW_V2_HOME` 只是 `install.sh` 的测试缝） | 同上 |
| `## Which suites a change needs` | 做法（带理由：board 与 retro 按文件路径导入 verify-ticket/dispatch 的模块） | 同上 |

### 2.6 `mmw-v2/prompt/shared.md`

每个非 Cursor 会话每回合常驻，读者是所有 host 上的所有会话（含脚本起的 worker/reviewer）。

| 段 | 类型 |
| --- | --- |
| 开头「Five facts」与一句总括 | 目的与立场 |
| 「A session a script started with no person in it…」一段 | 重入与分派（无人会话如何套用这些规则：问题走技能的问题路由、报告用技能格式、票的既定方案即规则 14 的「已点名项目」；提交 `0b6d47e3` 说明理由：无法给脚本会话单独一份 host 提示词） |
| 规则 1（工程决定自己做，产品决定交人：顾客看到什么、钱、范围与顺序、对外发布、难撤销） | 带理由的规则 |
| 规则 2（讨论中的问题是问题；批准的计划是开工信号，不以「要继续吗」结束回合；夜里的工作早上冷读） | 带理由的规则 |
| 规则 3（异议是应尽的义务，不制造） | 带理由的规则 |
| 规则 4（可核查证据；「tests pass」「should work」不算；原因是找到的不是猜的） | 带理由的规则 |
| 规则 5（报告讲理由与后果，不讲代码；按改动大小定篇幅） | 格式与模板 + 带理由的规则 |
| 规则 6–8（标准术语、不用修辞、引用有锚点且照抄原名） | 带理由的规则（写作） |
| 规则 9（何时用列表） | 格式与模板 |
| 规则 10（先想清谁在哪里读） | 带理由的规则 |
| 规则 11（步骤失败自己重做，只把只有用户能做的交给用户） | 带理由的规则 |
| 规则 12（读够再下结论；没读的部分说是推断） | 做法 + 带理由的规则 |
| 规则 13（文件只写现状；ADR 等决策记录例外） | 带理由的规则 |
| 规则 14（先搜现成的：GitHub、包仓库、读一个实现文件；三选一） | 做法 + 带理由的规则（提交 `05db60ec`：综合自四个公开来源） |
| 规则 15（默认禁止全量测试；最小相关集；跑全量前说出具体风险） | 带理由的规则（提交 `398644f9`，提交说明为空） |
| 结尾「What this file looks like when it is working」 | 目的与立场（完成标准） |

---

## 3. 连线

对外交接：本单元不产出事件；它产出的是**被读的文本**。ADR 由 `domain-modeling` 写（`domain-modeling/SKILL.md` `### Offer ADRs sparingly`），格式以 `docs/adr/README.md` 为准（`merge-notes/domain-modeling.md:5`，`docs/agents/domain.md:61`，已核实；`domain-modeling` 的三份文件与最近 squash 提交 `5b1a4c51` 逐字节相同，已用 `cmp` 核实，所以技能本身仍指向上游 `ADR-FORMAT.md`，本仓的格式经 `AGENTS.md` External References 与 `docs/agents/domain.md` 到达读者）。`CONTEXT.md` 由 `domain-modeling` 维护、由改词汇的复审批量修改（最近提交 `61f1065c`）。`CODING_STANDARDS.md` 与 `TESTING.md` 由 `manage-agents-md` 写入（`manage-agents-md/SKILL.md:155, 208, 289`，`references/rewrite.md:23`）。`shared.md` 由 `install.sh` 软链、`render.py` 拼接给各 host。

```edges
docs/adr/README.md -> docs/adr/0001..0031 : indexes (自拟：列出并记录 amends 关系)
docs/adr/0010 -> docs/adr/0009 : amends (自拟：ADR 改写 ADR)
docs/adr/0013 -> docs/adr/0010 : amends
docs/adr/0017 -> docs/adr/0010 : amends
docs/adr/0018 -> docs/adr/0009 : amends
docs/adr/0019 -> docs/adr/0018 : amends
docs/adr/0020 -> docs/adr/0013 : voids (自拟：整份作废)
docs/adr/0020 -> docs/adr/0010 : amends
docs/adr/0021 -> docs/adr/0020 : amends
docs/adr/0022 -> docs/adr/0021 : amends
docs/adr/0023 -> docs/adr/0012 : amends
docs/adr/0024 -> docs/adr/0016 : voids
docs/adr/0025 -> docs/adr/0023 : amends
docs/adr/0026 -> docs/adr/0018 : amends
docs/adr/0026 -> docs/adr/0024 : amends
docs/adr/0027 -> docs/adr/0023 : amends
docs/adr/0028 -> docs/adr/0011 : amends
docs/adr/0030 -> docs/adr/0029 : amends
docs/adr/0015 -> docs/adr/0014 : amends
docs/adr/0006 -> docs/adr/0003 : amends
docs/adr/0004 -> docs/adr/0002 : amends
docs/adr/0012 -> mmw-v2/skills/dispatch/references/night.md : cites (程序本体在 night.md §4)
mmw-v2/skills/dispatch/scripts/relay.py -> docs/adr/0008 : cites
mmw-v2/skills/dispatch/scripts/relay.py -> docs/adr/0001 : cites
mmw-v2/skills/dispatch/scripts/relay.py -> docs/adr/0009 : cites
mmw-v2/skills/dispatch/scripts/watchdog.py -> docs/adr/0008 : cites
mmw-v2/skills/ui-acceptance/scripts/journey.py -> docs/adr/0008 : cites
mmw-v2/skills/ui-acceptance/scripts/refusal.py -> docs/adr/0008 : cites
mmw-v2/skills/verify-ticket/scripts/events.py -> docs/adr/0008 : cites
mmw-v2/skills/dispatch/scripts/dispatch.sh -> docs/adr/0027 : cites
CODING_STANDARDS.md -> docs/adr/0008 : cites
CODING_STANDARDS.md -> CONTEXT-MAP.md : cites
TESTING.md -> AGENTS.md : cites
CONTEXT-MAP.md -> docs/contexts/*/CONTEXT.md : cites
docs/contexts/*/CONTEXT.md -> (each entry's _Home_ file) : cites
docs/contexts/toolbox/CONTEXT.md -> docs/adr/0006 : cites
docs/contexts/toolbox/CONTEXT.md -> docs/adr/0015 : cites
docs/contexts/ui-acceptance/CONTEXT.md -> docs/adr/0029 : cites
docs/contexts/toolbox/CONTEXT.md -> CODING_STANDARDS.md : cites
AGENTS.md -> CONTEXT-MAP.md : cites
AGENTS.md -> docs/adr/README.md : cites
AGENTS.md -> CODING_STANDARDS.md : cites
AGENTS.md -> TESTING.md : cites
docs/agents/domain.md -> docs/adr/README.md : cites
mmw-v2/merge-notes/domain-modeling.md -> docs/adr/README.md : cites
code-review(Standards axis) -> CODING_STANDARDS.md : reads
code-review(Standards axis) -> docs/contexts/*/CONTEXT.md : reads
code-review(Tests axis) -> TESTING.md : reads
implement -> CONTEXT-MAP.md : reads
implement -> docs/contexts/*/CONTEXT.md : reads
implement -> docs/adr/* : reads (仅当 ## Read first 列出)
dispatch(orchestrator, night.md §3 contract child) -> docs/adr/* : reads (权威顺序第一档)
to-spec -> docs/adr/* : cites (每条决定注明来源，可为 ADR id)
to-tickets -> CODING_STANDARDS.md : cites (## Read first)
to-tickets -> TESTING.md : cites (## Read first)
domain-modeling -> docs/adr/* : writes
domain-modeling -> docs/contexts/*/CONTEXT.md : writes
manage-agents-md -> CODING_STANDARDS.md : writes
manage-agents-md -> TESTING.md : writes
writing-for-agents(SKILL-SET-RULES) -> CODING_STANDARDS.md : cites (refusal)
writing-for-agents(SKILL-SET-RULES) -> CONTEXT-MAP.md : cites (MMW 的 glossary)
mmw-v2/install.sh -> mmw-v2/prompt/shared.md : writes (软链到 ~/.claude/CLAUDE.md)
mmw-v2/prompt/render.py -> mmw-v2/prompt/shared.md : reads
claude/codex/pi/grok sessions -> mmw-v2/prompt/shared.md : configured-by (每回合常驻)
mmw-v2/skills/dispatch/scripts/dispatch.sh -> worker/reviewer start prompt : writes (AUTONOMOUS 常量，与 shared.md 规则 2 同义)
```

---

## 4. 重复（grep 核实；区分真重复与同词）

### 4.1 真重复（同一意思两处以上）

| # | 意思 | 位置 | 备注 |
| --- | --- | --- | --- |
| D1 | 只有改变顾客所见、钱、范围、对外、难撤销的决定交给用户；其余自己定并写理由 | `shared.md` 规则 1；`writing-for-agents/REVIEWING-A-SKILL-SET.md:28`（几乎逐项同列）；`advisor/references/consulting.md:19`（「what the customer sees, scope, anything hard to undo」）；`grilling/SKILL.md:28`；`implement/SKILL.md:23` | 读者不同：`shared.md` 给所有会话；其余各给本技能的 agent |
| D2 | 不以「要我……吗 / Shall I」结束回合，否则停工 | `shared.md` 规则 2；`dispatch.sh:108` 常量 `AUTONOMOUS`（进 worker/reviewer start prompt） | 有意的重复：Cursor 收不到 `shared.md`（ADR 0007），start prompt 覆盖所有 host（推断为此理由；原文未写明为何两处都有） |
| D3 | 用领域既有术语，否则用词典词，最后才自造并当场定义；照抄程序读的名字；不用修辞 | `shared.md` 规则 6、7、8；`SKILL-SET-RULES.md:75-77`；`CONTEXT-MAP.md` 词条读法 | `shared.md` 管回复与文档，`SKILL-SET-RULES` 管技能文本 |
| D4 | 文件只写现状，变更与理由进 commit message | `shared.md` 规则 13；`SKILL-SET-RULES.md:51`、`:145`；`to-spec/references/revising-a-spec.md:11`；`docs/research/mmw-structure/2026-09-06-handoff.md` §五第 5 条（用户判据原文） | |
| D5 | 报测试结果要引看到的那一行，不写「测试通过」 | `shared.md` 规则 4；`night.md:135`（「`ran 188 skipped 0`, not "the tests pass"」）；ADR 0012 Consequences 规则 3 | ADR 是记录，night.md 是执行处 |
| D6 | 只跑受影响/最小相关的测试集 | `shared.md` 规则 15；`implement/SKILL.md:32`；`night.md:131, 135`；`SKILL-SET-RULES.md:152`；`TESTING.md` `## Which suites a change needs`（本仓特例） | |
| D7 | 拒绝三段：发生了什么（带可查事实）、为什么、下一步 | ADR 0008 正文末段；`CODING_STANDARDS.md` Skills and scripts 4；toolbox CONTEXT **refusal**；`ui-acceptance/scripts/refusal.py` 文件头；`SKILL-SET-RULES.md:12` | toolbox 词条复述了三段，而 `CONTEXT-MAP.md` 自己说词条「does not repeat what can be read there」 |
| D8 | 没人轮询；靠 relay 把事件变成唤醒；夜没有时钟 | ADR 0010、0017、0020、0022；`CODING_STANDARDS.md` State 3；`night.md:11`；night CONTEXT **relay**/**wake** | |
| D9 | 票的状态是事件的 fold；每个事件由脚本贴 | ADR 0019；`CODING_STANDARDS.md` State 3；ticket-run CONTEXT **event**/**fold**/**issue comment** | |
| D10 | 在 `origin/<base branch>` 合并—检查—快进推送，冲突成 `ticket.bounced` | ADR 0023；`CODING_STANDARDS.md` State 4；night CONTEXT **base branch**/**merge lock** | |
| D11 | `models.json` 是唯一配置，只经 `models.py config` 与任务板写 | ADR 0024；`CODING_STANDARDS.md` State 1；toolbox CONTEXT **`models.json`**/**`models.py`**；`AGENTS.md` `## Commands` 末行；`dispatch/references/editing-models.md:3` | |
| D12 | 收口轮四步门槛与三条可审计规则 | ADR 0012 正文；`night.md` §4（已逐条对照，同义） | ADR 自述程序本体在 night.md，ADR 只留否决理由；实际 ADR 仍完整复述了步骤 |
| D13 | 设计页不加载产品代码的理由；design system 的用途 | ADR 0030；`design-pages/references/template-project-claude-md.md:51`；`design-pages/references/design-system.md:7` | 2026-09-28 复审提议写回，今已写回（已核实两句都在），推翻了 2026-09-21 的「理由只放 ADR」（Memory `415f96d0`）在这两处的适用 |
| D14 | 词条与 `_Home_` 冲突时以 `_Home_` 为准；词条事实要对 `_Home_` 核 | `CONTEXT-MAP.md` 第 3 行；`SKILL-SET-RULES.md:80` | |
| D15 | self-hosting boundary 的内容 | `AGENTS.md` `## Self-hosting boundary`；toolbox CONTEXT **self-hosting boundary**、**installed checkout** | 词条是定义，与规则正文同义 |
| D16 | 不制造异议 | `shared.md` 规则 3；`advisor/references/advising.md:17`（「Do not manufacture objections」） | |
| D17 | 写给没有你上下文的读者 | `shared.md` 规则 2 末句、规则 10；`SKILL-SET-RULES.md:33-34`；`night.md:5`；`verify-ticket/references/sub-issues.md:11`；`grilling/SKILL.md:28` | |

### 4.2 只是同词（词表已分开）

「baseline」（tickets **baseline** / toolbox **checker baseline** / ticket-run **baseline run**）；「hook」（**host hook** / **git hook** / release **build hook**）；「finding」（**review finding** / **skill-set-review finding** / **release finding** / night **alert** 的 `_Avoid_`）；「release」（lease **release** / `ticket.released` / `RELEASE` plan line / `exe-release`）；「effort」（`models.json` **`effort`** / ui-acceptance **effort**）；「round」（tickets **round** / **experiment round** / release **fix round**）；「phase」（night **phase** / 任务板 **phase pill** / 事件 `stage`）；「retired」（toolbox **retired** / tickets **retiring line** / `retired_ids`）；「hold / held / `HOLD`」。另：merge worktree 的名字 `CODING_STANDARDS.md` 与 `AGENTS.md` 写 `merge-<branch>`，night CONTEXT **worktree** 写 `merge-<slug>`（`/` 换成 `-`）——同一物两种写法，后者更准确（已核实原文）。

---

## 5. 上游差异

不适用：本单元不含上游技能。唯一相关的上游文件是 `domain-modeling` 的 `ADR-FORMAT.md`（与上游逐字节相同，已核实），它给的 ADR 模板（一段即可，`Status` 等节可选）与本仓 `docs/adr/README.md` 的格式（`amends` frontmatter、两节必需、不写 status）不同；连接做在上游文本之外（`docs/agents/domain.md:61`、`AGENTS.md` External References），符合 `SKILL-SET-RULES.md` `### Upstream skills`「Connect outside the upstream text first」。

---

## 6. 价值证据

| 部件 | 防的失败 | 实地证据 | 核实 |
| --- | --- | --- | --- |
| ADR 0008 | 闸口既没干活也没出声，读起来像通过 | ADR 正文「这条规则是从哪一批故障里得出的」：2026-09-05 一夜五处（批次读错、`advance` 一张没派却打印同一行总结、类型检查红三天、测试写进真租约表、失联应用占地址） | 已核实原文；事故本身未另核 |
| 拒绝三段（`refusal.py`） | 只说错不说下一步，agent 即兴 | `refusal.py` 头：2026-09-05 三个 worker 对同一条「端口被占」各自发明了等、重试循环、杀进程 | 已核实原文 |
| ADR 0010 | worker 轮询与 main 定时查表 | 各 host shell 工具时限实测（Cursor 30 s，Grok Build/Claude Code 120 s）；用户 2026-09-06 原话 | 已核实原文 |
| ADR 0011 / 0028 | 整机驱动把流水线缺陷乘开；像素面积稀释差异 | 变色龙 S3：7 张界面票关 1 张，25 张子票 22 张是流水线自己的；#640 worker 为过判官改产品；spec #444：13px 对 26px 只占截图 2.7% 被放行 | 已核实原文 |
| ADR 0012 | review 子票无限循环 | #216 一夜：三代每票约 3 张，38 张中 27 张（71%）落在本票 Owns 内，9 张（24%）已不成立 | 已核实原文 |
| ADR 0017 | 定时器 | 「它在本机一次都没有救过一夜」 | 已核实原文（无外部数据） |
| ADR 0018 | runner 知识散在四个脚本 | 分支 `spec-300-herdr-night` 合不回，收成 tag；Herdr 对已挪走会话仍报 `idle`（2026-09-10 实测） | 已核实原文 |
| ADR 0019 | 首行协议易碎；runner 只答一台机器导致派第二个 worker | 正文「要修的是什么」四条 | 已核实原文 |
| ADR 0022 | 被拒登记不撤回 | 「已复现」 | 已核实原文 |
| ADR 0026 | verifier 重复运行 | 用户 2026-09-14 接受「worker 可在 final run 前改写 `CHECK:`」的风险 | 已核实原文 |
| ADR 0027 | 第一次冲突就交 triage 浪费保留的工作 | 无事故编号；I5-P8 记外部 agentflow #915 首次 bounce 后 78 秒才重启 | ADR 原文已核实；I5 未核实 |
| ADR 0029 / 0030 | 两个设计源头各改各的；design system 做成产品副本 | 工作监控与变色龙；任务板试点 46 个 React 组件、44 个场景全过却改不动 | 已核实原文 |
| ADR 0031 | Memory 长查询返回 0 条 | `--explain` 报 `unsupported_specific_anchor`；无关票同样得 0.78 分 | 已核实原文 |
| 「summary 在有未路由 finding 时拒绝」（PC1 在夜里的实例） | 收口漏路由 | I5-P5：外部 #407 漏 43/57 条；提交 `2b560899`（2026-09-13） | 提交已核实；issue 未核实 |
| closeout 重跑安全（PC17） | 重跑写重复事件 | I5-P7：#414、#440；提交 `0855d553`（2026-09-16） | 提交已核实；issue 未核实 |
| 一个文件同时一个写者（PC12） | 并发票合并冲突 | I5-P4：外部 #408 三张界面票 bounce；本仓 #447 一夜 22 条 finding 21 条收口修 | 未核实（取自 I5） |
| `TESTING.md` `## What a test proves` | 测试钉措辞 | 提交 `e2dab1d7`（2026-09-29）「remove wording assertions from every remaining suite」 | 提交已核实 |
| `shared.md` 规则 14 | 重复造轮子 | 提交 `05db60ec`：综合自四个公开来源；未见事故 | 已核实提交说明；无事故证据 |
| `shared.md` 规则 15 | 默认跑全量测试 | 提交 `398644f9`，说明为空 | 无证据 |
| `shared.md` 规则 12 | —— | 提交 `b1df3138`：删掉依赖不存在 hook 的假设 | 已核实 |
| `shared.md` 无人会话前言 | 脚本起的会话误读「问我」的规则 | 提交 `0b6d47e3` 说明 | 已核实 |
| `CODING_STANDARDS.md` State 5 | worker 静默没有 memory 工具 | 原文写了症状，未给事故编号 | 部分 |
| `CONTEXT-MAP.md` 与 7 份词表 | 同一概念多名、名实不符 | 2026-09-23 复审 441 条发现、162 条第一轮后仍成立（I5-P9 引 `docs/reviews/2026-09-23-skill-set/汇总.md` §七）；2026-09-29 词汇复核（`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`）新增 29 条、改正多条与 `_Home_` 不符的词条 | 汇总数字未核实；DECISIONS 已读 |
| 其余 ADR（0001、0003、0005、0006、0007、0009、0014、0015、0021、0023、0024、0025） | 见各自「要修的是什么」 | 多为设计推理与当日实测；无夜的事故编号 | 无独立实地证据（仅 ADR 自述） |

---

## 7. 约束

| 约束 | 出处 | 对本单元形态的作用 |
| --- | --- | --- |
| ADR 的形状（决定在标题+首段，`amends`，两节必需） | `docs/adr/README.md` `## 一份 ADR 长什么样` | 31 份 ADR 都照此写 |
| 执行指令住在执行它的技能里，ADR 只留决策与否决 | ADR 0012 `## Considered Options` 第 2 条（夜跑在 consuming repository，读不到本仓 `docs/adr/`） | 技能文本不引用 ADR；0012 的步骤搬进 `night.md` |
| 维护者规则不进 `SKILL.md` | ADR 0008 `## Considered Options` 第 1 条 | 0008 只在脚本注释与 `CODING_STANDARDS.md` 被引用 |
| 规则写在必须遵守它的 agent 读的文本里；ADR/词表/merge-note 只能向维护者解释 | `SKILL-SET-RULES.md` `### Load and disclosure` 第 8 条（第 32 行） | 原则若只放 ADR 或词表，到不了执行 agent |
| 技能交出理由（事实 1）；每样东西一个家（事实 7）；技能靠名字互相调用（事实 6） | `SKILL-SET-RULES.md` `## What skill text is for` | 原则层「每条只写一处」与「理由贴在规则旁」之间要取舍 |
| 维护者的设计理由属 ADR（沉积表第 2 行） | `SKILL-SET-RULES.md:50` | ADR 是理由的家 |
| `shared.md` 到不了 Cursor；技能装进 `~/.agents/skills` 五家都扫 | ADR 0007 正文；ADR 0014 `## Considered Options` 第 2 条 | 只写在 `shared.md` 的原则，Cursor 上的会话读不到 |
| 词条写法：只在定下或 `_Home_` 证实后写；`_Avoid_` 只放真错的词 | `CONTEXT-MAP.md` 第 5 行 | 词表不是规则的家 |
| 改词汇前先读 map | `AGENTS.md` External References 第 1 行 | |
| 用户判据（2026-09-06）：技能是交付物；需要读的在技能里安排时刻；拒绝的出路是可执行动作；求根本解；文件只写现状 | `docs/research/mmw-structure/2026-09-06-handoff.md` §五 | 线索材料；前 4 条今在 `SKILL-SET-RULES.md` 与 `refusal.py` 中有同义表述（已核实），「求根本解」未在现行规范里找到对应句 |
| 界面技能正文只留可执行规则，理由放 ADR 0029/0030 | Memory `415f96d0`（2026-09-21，source 为 agent） | 已被 2026-09-28 复审在两处推翻（写回已核实） |
| 不需要 agent 判断的事交给脚本，技能文字不再描述 | `docs/reviews/2026-09-28-lightweight/汇总.md` 第三节第 2 小节（记为「你定的原则」） | 与 ADR 0009、`SKILL-SET-RULES` 事实 2 一致；与 ADR 0004「这一段不写成代码」有张力（0004 已挂起） |
| 原则层：写为什么、何时用，每条只写一处 | Memory `8ec53374`（2026-09-29，用户确认的改造方向） | 本报告 §9 的判据 |
| 旧规则（`SKILL-SET-RULES.md`、ADR、既往写法决定）在这次重构中是审视对象而非约束；但不许为匹配新架构而形式拆散或硬塞 | Memory `756fc056`（2026-09-29） | 本节所列约束都只是「现在为什么是这个样子」，不是下一轮不可改的条件 |

---

## 8. 天然整体

| 整体 | 为什么不可拆 |
| --- | --- |
| 每一份 ADR（标题+首段、Considered Options、Consequences） | 否决项是决定的一半：拆开后「为什么不是 X」与「定了 Y」分居两处，后来者会重提被否的方案（0011、0028 末条明写「半年后再发明……的人，读这一份」） |
| 夜的 ADR 链 0009→0010→0013→0017→0018→0019→0020→0021→0022→0026 | 每份只说改了前一份哪句；现行机制只有顺着 `amends` 与 README 索引读完一条链才能拼出。单抽一份会读到已作废的机制（如 0013） |
| ADR 0008 的三个条件 | 三条（点名事实、唯一出路、不许不作为而通过）是同一次故障归纳出的同一形状；ADR 自己已把「消息三段」与「闸口行为」分给 `refusal.py` 与本 ADR 两处，再拆会失去「为何要有这道闸」 |
| `shared.md` 全文 | 规则按编号互引（规则 2 引规则 1，规则 12 引规则 4，前言引规则 14，规则 10 被开头「rule 10」引）；五个事实是全部规则的理由来源。抽出单条会丢掉它的理由（多数规则的理由写在「Five facts」而不在规则本身） |
| `CONTEXT-MAP.md` + 7 份 `CONTEXT.md` | 词条之间靠 `Distinct from` 跨 context 互指（如 **hold**/`blocker_hold`/`HOLD` 三处），一个概念只在一处定义；map 是唯一目录 |
| `CODING_STANDARDS.md`、`TESTING.md` | 各被一个 axis 整份读；拆开只给该 axis 增加跳转 |
| `night.md` §4（第 0 步 + 四步 + 三条提交规则 + `route` 命令） | 执行者（orchestrator）在同一时刻用完；ADR 0012 只是它的理由记录 |

---

## 9. 原则候选（主任务）

判据：一条规则同时满足「带理由」与「跨多个步骤或多个技能适用」才列为候选。「出现」只算已安装技能的 `.md` 文本（102 个文件，grep 核实）；`shared.md`、ADR、`CODING_STANDARDS.md`、词表、脚本另列。「次数」= 位置数 / 文件数 / 技能数。本表不做归置决定。

### 9.1 候选

| # | 规则一句话 | 理由出处 | 技能文本中的位置（grep 核实） | 次数 | 适用时刻 |
| --- | --- | --- | --- | --- | --- |
| PC1 | 假通过比诚实失败更坏：一道检查、一次交付不许因为什么都没做而读起来像通过；查不了就说查不了 | ADR 0008 全文；`CODING_STANDARDS.md` Skills and scripts 4；词条 **refusal**、**unreadable event**、**evidence_checked**；`implement/SKILL.md:22` 自带理由（「An honest `HANDOFF REQUIRED` costs them one look… a false `ALL MET` lands broken behaviour under a green mark」） | `implement/SKILL.md:22`；`dispatch/references/night.md:7`；`ui-acceptance/SKILL.md:34`（规则 3）、`:36`（规则 5）；`ui-acceptance/references/harness-guard.md:10-11`；`code-checkers/SKILL.md:58`；`code-checkers/references/git-hooks.md:42`；`retro/SKILL.md:47`、`:58`；`code-review/references/session.md:89`（`unverified:`）；`SKILL-SET-RULES.md:62`、`:89` | 12 / 9 / 7（implement、dispatch、ui-acceptance、code-checkers、retro、code-review、writing-for-agents）；另 5 个脚本注释引 ADR 0008 | worker 收尾写 closing comment；orchestrator 判 finding 与接受结果；写/配检查器；retro 判证据；写任何闸口 |
| PC2 | 一个检查要证明自己能失败（negative control / probe），不能失败的检查什么都没证明 | ADR 0011（#640）、0012 第 2 步（#253「跳过十个用例还打印 all passed」）、0028（停产品让弱断言同样失败）；词条 **negative control**、**probe**；`to-tickets/SKILL.md:84` 自带理由（「`ok`, `passed` or `done` on their own also appear in failing output」） | `to-tickets/SKILL.md:84`、`:88`；`to-tickets/references/cutting-interface-tickets.md:43-46`；`to-spec/SKILL.md:95`；`implement/SKILL.md:30`；`ui-acceptance/references/story-parity.md:114-117`、`journey.md:42-53`、`boundary-check.md:15`；`dispatch/references/night.md:127`（第 2 步）；`code-checkers/SKILL.md:58`、`references/git-hooks.md:72`；`SKILL-SET-RULES.md:62` | 12 / 11 / 7（to-tickets、to-spec、implement、ui-acceptance、dispatch、code-checkers、writing-for-agents） | 写 `CHECK:`/`EXPECT:`；TDD 的第一个红；配 oracle；配检查器；收口路由 |
| PC3 | 拒绝要点名一个可查事实、说为什么、给唯一一条可直接执行的下一步；收到拒绝的 agent 照做，不即兴 | ADR 0008 条件 1、2（「给了选项的 agent 会自己发明第六个」）；`refusal.py` 头；`CODING_STANDARDS.md` Skills and scripts 4；2026-09-06 handoff §五第 3 条 | `SKILL-SET-RULES.md:12`、`:59`、`:134-136`；`ui-acceptance/SKILL.md:26`、`:35`；`dispatch/references/night.md:66`；`advisor/references/consulting.md:13` | 7 / 4 / 4；实现在脚本：`refusal.py` 被 `tool-guard.py`、`lease.py`、`journey.py`、`boundary-check.py`、`harness-guard.py` 导入；`verify-ticket.py` 与 `dispatch.sh` 各有自己的 `refuse`（是否三段未核实） | 写脚本；任何 agent 读到拒绝时 |
| PC4 | 谁都不轮询另一个 agent：起了别人就结束回合，由票上事件经 relay 叫醒；会话内部阻塞式等待不算轮询 | ADR 0010（host 时限实测、用户原话）、0017、0020、0022（排队 worker 每 90 秒花一回合）；`CODING_STANDARDS.md` State 3 | `dispatch/references/night.md:11`（「no agent polls another」）、`:66`、`:70`；`dispatch/SKILL.md:25-28`；`dispatch/references/one-ticket.md:8`；`inside-a-ticket.md:5`；`implement/SKILL.md:22`、`:78`、`:84`；`ui-acceptance/SKILL.md:38`；`verify-ticket/references/sub-issues.md:11`；`SKILL-SET-RULES.md:90`；反例（会话内等 subagent）`code-review/references/session.md:33` | 13 / 9 / 6 | 起 reviewer 后；等槽位（exit 3）；开 `contract`/`fault` 子票后；orchestrator 每步之间 |
| PC5 | 进度与状态读自持久记录（票上的事件、release engine 状态），不读会话记忆；会话里的理由随会话消失 | ADR 0019；ticket-run CONTEXT 开头段；release CONTEXT **release engine**；`night.md:5` 自带理由 | `dispatch/SKILL.md:7`（「Where you are is what the ticket's events say, not what this session remembers」）、`:26`；`dispatch/references/night.md:5`；`implement/SKILL.md:74`（`RESUME:`）、`:86`（「a session's state never is」）；`exe-release/references/driving.md:5`（「Do not resume from session memory」）；`verify-ticket/references/sub-issues.md:11`；`SKILL-SET-RULES.md:33` | 8 / 7 / 5 | 被唤醒；重入一张票；续跑出包；写子票正文 |
| PC6 | 协议状态只由脚本写（事件、关票、改 label、交付记录），模型不手敲 | ADR 0019（手敲 `VERDICT` 关不了票）、ADR 0010「为什么通知那一步在脚本里」；`CODING_STANDARDS.md` State 3（「a model types none」）；词条 **event**、**issue comment** | `implement/SKILL.md:99`（「Never close the ticket or swap its labels yourself: a hook blocks the command」）；`ui-acceptance/SKILL.md:38`（普通评论不带事件）；`dispatch/references/night.md:113-120`（`route` 是 finding 离开的唯一方式）；`exe-release/references/driving.md:44` | 4 / 4 / 4；另由 `tool-guard.py` 机械拦截 | worker 关票；报告 blocked；收口路由；出包收尾 |
| PC7 | 确定性工作由脚本做，文本只写判断；判断属于 agent，不藏进无模型的状态机 | ADR 0009；`SKILL-SET-RULES.md` 事实 2；2026-09-28 用户决定（汇总第三节 2）；张力：ADR 0004「这一段不写成代码」 | `SKILL-SET-RULES.md:12`、`:59-63`；`dispatch/references/night.md:3`；`exe-release/references/driving.md:5`；`wizard/SKILL.md:10`（上游原文） | 5 / 4 / 4 | 写技能与脚本；orchestrator 每个决定；驱动出包 |
| PC8 | 基线即合同：已定的结论照抄不重写；不成立时经 `contract` 子票在决定者看得见处重开，从不悄悄改或绕开 | `implement/SKILL.md:22` 自带理由（「A baseline is a decision someone already paid for… reopens that decision where nobody who made it can see」）；tickets CONTEXT **baseline**（IEEE 610.12 change control）；ADR 0029 | `implement/SKILL.md:16`、`:22`、`:27`、`:96`；`implement/references/writing-interface-code.md:3`、`:41`；`design-pages/SKILL.md:10`；`design-pages/references/pull.md:5`、`:31`、`:45-47`；`dispatch/references/night.md:92`、`:98`；`triage/references/pipeline-issues.md:5`；`to-tickets/SKILL.md:174`；`write-screen-contract/SKILL.md:18` | 15 / 9 / 7 | worker 读入与写码；设计定稿后；orchestrator 处理 `contract`；triage |
| PC9 | 用户只决定产品事项（顾客所见、钱、范围与顺序、对外、难撤销）；其余工程决定自己做、写一行理由、继续 | `shared.md` 规则 1、2；`dispatch.sh:108` `AUTONOMOUS`；ticket-run **child kind** 的 `decision` | `implement/SKILL.md:23`、`:96`；`grilling/SKILL.md:26-28`；`REVIEWING-A-SKILL-SET.md:28`；`advisor/references/consulting.md:7`、`:19`；`manage-agents-md/SKILL.md:76`；`verify-ticket/references/sub-issues.md`（`decision` 行）；`to-tickets/references/person-ticket.md:3`；`triage/SKILL.md:36` | 11 / 9 / 8 | 写码遇到选择；grilling；咨询 advisor 后；切出子票；复审 |
| PC10 | 写给看不到你上下文的读者：早上冷读的用户、空上下文的下一个 agent、只见首行的 shell | `shared.md` 规则 2 末句、8、10；ticket-run CONTEXT 开头；`SKILL-SET-RULES.md:33-34` | `dispatch/references/night.md:5`；`implement/SKILL.md:23`；`verify-ticket/references/sub-issues.md:11`；`grilling/SKILL.md:28`；`to-tickets/references/ambiguity-scan.md:73`；`advisor/references/advising.md:19`；`SKILL-SET-RULES.md:33-34`、`:100-102`、`:135` | 10 / 7 / 7 | 写子票、closing comment、决定行、问题、start prompt、脚本输出 |
| PC11 | 线索不是证据：Memory、reviewer Rule、别票的通过结论、brief、相似标题只决定去看什么，结论要当前的一手来源 | `shared.md` 规则 4（「A cause is something you found, not something you guessed」）、12；词条 **reviewer Rules**、**semantic-conflict angles**、**earlier occurrence** | `implement/SKILL.md:48-49`；`code-review/references/session.md:89`、`:101`；`code-review/references/spec-reviewer.md:22`；`retro/SKILL.md:58`、`:63-66`；`advisor/references/advising.md:15`；`research/SKILL.md:10`（上游原文） | 8 / 6 / 5 | 读 Memory 后；评审出 finding；retro 定原因；advisor 回答 |
| PC12 | 同一文件同一时刻只有一个写者：能并行的票不写同一个文件；共享入口要么归一张票，要么加 Blocked by | `implement/SKILL.md:28` 自带理由（「one file has one writer at a time and the cut missed an edge」）；`to-tickets/SKILL.md:107`；ADR 0012 第 1 步（「并发约束不是工作量」）；I5-P4（未核实） | `to-tickets/SKILL.md:44`、`:90`、`:107`、`:182-184`；`implement/SKILL.md:28`、`:78`；`dispatch/references/night.md:127`（第 1 步）、`:140` | 8 / 3 / 3 | 切票；worker 改 Owns 外文件；集成冲突；收口开票 |
| PC13 | 文件只写现状；改了什么、为什么进 commit message、评论或决策记录 | `shared.md` 规则 13；`SKILL-SET-RULES.md` 沉积表；2026-09-06 handoff §五第 5 条 | `SKILL-SET-RULES.md:51`、`:145`；`to-spec/references/revising-a-spec.md:11`；`manage-agents-md/references/rewrite.md:36` | 4 / 3 / 3 | 任何写文件；修订已发布 spec；重写 AGENTS.md |
| PC14 | 只跑证明本次改动的最小测试集，并引用看到的那一行 | `shared.md` 规则 4、15；`TESTING.md` `## Which suites a change needs`；ADR 0012 规则 3 | `implement/SKILL.md:32`；`dispatch/references/night.md:131`、`:135`；`SKILL-SET-RULES.md:152` | 4 / 3 / 3 | worker 收尾前；orchestrator 自己改 finding；技能改完 |
| PC15 | 只读靠写进文本、由 agent 自守，而不是靠权限档（host 没有只读档） | ADR 0014 `## Consequences` 第 1 条、0015 第 1 条；toolbox **permission mode** | `advisor/references/advising.md:25`（「this is a rule you keep, not one that keeps you」）；`advisor/references/consulting.md:5`；`code-review/references/standards-reviewer.md:3`、`spec-reviewer.md:3`、`tests-reviewer.md:3`、`ui-reviewer.md:3`；`code-review/references/session.md:31` | 7 / 7 / 2 | advisor 与四个 axis 开工时 |
| PC16 | 一个意思、一份配置、一个设计只有一个权威的家；第二份迟早与第一份矛盾 | ADR 0001、0007、0024（两个写者互相覆盖）、0029（两源各改各的）、0030；`SKILL-SET-RULES.md` 事实 7；`CONTEXT-MAP.md` 第 3 行；Memory `8ec53374` | `writing-for-agents/SKILL.md:78`；`SKILL-SET-RULES.md:17`、`:40`；`design-pages/SKILL.md:6`；`design-pages/references/pull.md:49`；`dispatch/references/editing-models.md:3`；`exe-release/references/new-product.md:97` | 7 / 6 / 4 | 设计配置与源；写技能；改 host/model；迁移出包方式 |
| PC17 | 有副作用的命令被打断后原样重跑能接上、不重复副作用；给出的下一步可以照写直接跑 | ADR 0010 Consequences（`advance` 写成随时可重跑）、0017（早上 `advance` 从原地接）、0025（`spec.merged` 是重跑边界）；I5-P7 与提交 `0855d553` | `dispatch/SKILL.md:25`；`dispatch/references/night.md:120`、`:180`；`implement/SKILL.md:74`；`SKILL-SET-RULES.md:136` | 5 / 4 / 3 | 被唤醒打断命令后；route 退 1；summary 拒绝后；重入票 |
| PC18 | 拒绝要响，替换是静默的：起不来就停并报告，不重试、不换 host/runner、不绕过、不改环境 | ADR 0018 `## Considered Options` 第 3、4 条（用户 2026-09-10）；`refusal.py` 头的 2026-09-05 事故；`ui-acceptance/SKILL.md:36` 自带理由（「A workaround built instead hides it from every ticket after yours」） | `dispatch/references/night.md:66`（「none is retried」）；`ui-acceptance/SKILL.md:35`（规则 4）、`:36`（规则 5）；`implement/SKILL.md:18`、`:78`（fault 后 stop） | 5 / 3 / 3 | 起会话被拒；产品连不上；流水线自身故障 |

### 9.2 家族关系（事实，不是归并决定）

- PC1、PC2、PC3、PC18 都以 ADR 0008 为理由源：PC1 是闸口的结果不能伪装，PC2 是检查本身要能失败，PC3 是拒绝的形状，PC18 是拒绝之后不做静默替代。
- PC4、PC5、PC6 都以 ADR 0019/0020 为理由源：状态在票上（PC5），只有脚本写它（PC6），所以谁都靠读它被叫醒、不必轮询（PC4）。
- PC9、PC10、PC11 主要来自 `shared.md`，技能里是各自场景的翻版。
- 与 pstack 的近似（取自 `G2-pstack-principles.md` 的术语表，本轮**未核实** pstack 原文）：PC2/PC14 近 `Prove It Works`；PC9 近 `Never Block on the Human`；PC12 近 `Separate Before Serializing Shared State`；PC17 近 `Make Operations Idempotent`；PC7 与「不需要判断的交给脚本」近 `Encode Lessons in Structure`。G2 表中这几条的 MMW 列多写「无」，而本表显示 MMW 有同义规则分散在多个技能里。

### 9.3 张力（原文之间，未裁决）

- `shared.md` 规则 11（「When a step fails or is interrupted, redo it yourself」）与 `ui-acceptance/SKILL.md` 规则 4、5 及 `implement` 的「fault 子票后 stop」方向相反。`shared.md` 的无人会话前言（「applies these rules through its ticket」）是唯一的调和句；原文没有点名这一对。
- `SKILL-SET-RULES.md:61`（「A rule a script could check exactly becomes a check」）与 ADR 0004「三档是一条判断规则；写成脚本只是把一条规则藏进一个没人会去读的文件」。0004 已挂起，但它的理由是一般性的。
- 原则「每条只写一处」（Memory `8ec53374`）与两条放置约束：`shared.md` 到不了 Cursor（ADR 0007）；consuming repository 读不到本仓 `docs/adr/`（ADR 0012）。目前同一原则在 `shared.md`、`CODING_STANDARDS.md`、多个技能里各有一份，部分正是为了到达不同读者（D2 为例）。
- `SKILL-SET-RULES.md` 事实 1 要求理由贴在规则旁；PC1 的理由在 ADR 0008，技能里各处各写一句本场景的理由（`implement:22`、`night.md:7`、`ui-acceptance:34`），理由文字彼此不同。

### 9.4 只在一处适用、应留在原处的规则（对照）

| 规则 | 出处 | 唯一读者 / 位置 | 判定 |
| --- | --- | --- | --- |
| out-of-ticket finding 四步门槛与三条可审计提交规则 | ADR 0012 | orchestrator，`night.md` §4 | 留在原处 |
| 同一夜第一次 bounce 交回 worker，第二次交 triage | ADR 0027 | `dispatch.sh advance`（`night.md:87` 一行提示） | 留在原处 |
| 在 origin 合并—检查—快进；`finish` 只在用户验收后 | ADR 0023、0025 | `dispatch.sh`；`night.md:192` | 留在原处（其中「用户验收才合回」是 PC9 的一个实例） |
| Memory 查询只用路径、标题、报错等短标识，放 `--` 后 | ADR 0031 | worker，`implement` `## Shared experience while implementing` | 留在原处 |
| product answers 只写必须保证什么，不按产品类型给做法 | ADR 0028 | 写 contract ticket 的 worker，`ui-acceptance/references/product-answers.md` | 留在原处 |
| brief 只带决定与证据，不带结论 | ADR 0014 | advisor 两扇门都在 `advisor` 技能内 | 留在原处 |
| worker 的 final run 在最后一次写 commit 之后 | ADR 0026 | `implement` 第 4 步 | 留在原处 |
| 判活容差、沉默阈值、idle 阈值 | ADR 0021、0022 | `watchdog.py`、`relay.py`、`turn-guard.py` 头部 | 留在原处（脚本） |
| `models.json` 加锁、比对版本、原子替换 | ADR 0024 | `models.py`；`editing-models.md` | 留在原处 |
| 安装位置、提示词分发、不交付 subagent | ADR 0003、0006、0007、0015 | `install.sh`、`render.py` | 留在原处 |
| fold 按 comment id 顺序全量重放 | ADR 0019 Considered Options | `events.py` | 留在原处 |
| board 与 retro 按路径导入模块，改它们要连跑三套件 | `TESTING.md` `## Which suites a change needs` | MMW 维护者 | 留在原处 |
| 测试证明行为不钉措辞 | `TESTING.md` `## What a test proves` | Tests axis 与写 MMW 测试的人；技能中只有 `SKILL-SET-RULES.md:63`、`:149` 近义 | 留在原处（本仓规则，已有唯一家） |
| 脚本头记带日期、钉版本的实测而非文档声称 | `CODING_STANDARDS.md` Skills and scripts 4 第二句；ADR 0006/0007/0021 的实测做法 | 写脚本的人；`SKILL-SET-RULES.md:44`、`:49` 近义 | 留在原处 |
| host/runner 中立（文本不按名字分支，差异写成能力） | ADR 0018；`SKILL-SET-RULES.md:69`、`:118-120`；`CODING_STANDARDS.md` 第 3 条 | 写技能与脚本的人（技能里是遵守而不是复述，如 `code-review/references/session.md:23-33`） | 留在原处（写作规则，已有两处各管文本与代码） |
| `~/.cursor/mcp.json` 去掉 `type` | `CODING_STANDARDS.md` State 5 | `install.sh` | 留在原处 |
| 以正向指引代替禁令 | ADR 0029 Considered Options 第 1 条；`writing-for-agents/SKILL.md:74` **Negation** | 写技能的人 | 留在原处 |
| 规则写在遵守它的 agent 读的文本里 | `SKILL-SET-RULES.md:32`；ADR 0008、0012 的否决项 | 写技能的人 | 留在原处 |
| 词条只在定下或 `_Home_` 证实后写；`_Avoid_` 只放真错的词 | `CONTEXT-MAP.md` 第 5 行；`SKILL-SET-RULES.md:79-80` 近义 | 写词条的人 | 留在原处 |
| 设计系统文件按校验三档决定可信度 | ADR 0004 | 已挂起，无读者 | 留在原处（无活读者） |
| `shared.md` 规则 9（何时用列表）、规则 5 的篇幅规矩 | `shared.md` | 所有会话回复用户时 | 留在原处（只管对用户的回复） |

---

## 10. 本轮发现的不一致（事实，未修改任何文件）

1. `AGENTS.md` External References 第 1 行写「split into six bounded contexts」，`CONTEXT-MAP.md` 第 3 行写「seven bounded contexts」并列出 7 个（已核实）。
2. `docs/contexts/ticket-run/CONTEXT.md` 第 330 行 `### Writing interface code` 是空节，下面没有词条（已核实）。
3. ADR 0008 正文把消息三段结构指到 `mmw-v2/skills/verify-ticket/scripts/refusal.py`，实际文件在 `mmw-v2/skills/ui-acceptance/scripts/refusal.py`；ADR 0012 正文指到 `mmw-v2/skills/drive-target/scripts/refusal.py`，该目录不存在（find 已核实）。toolbox CONTEXT **refusal** 的 `_Home_` 写对了。
4. ADR 0011 说比较原语「留在 `visual-parity.py`」；该文件不存在（find 已核实），没有后续 ADR 记录其删除。
5. ADR 0029 正文说「设计时截图检查与 pull report 承担」；`design-pages` 各 reference 中无 screenshot 检查（grep 已核实）。README 表下注已改对。
6. ADR 0005 后果①「在根 AGENTS.md 落 `## Agent skills` 块」今不成立（`AGENTS.md` 无此节），无后续 ADR。
7. merge worktree 名：`CODING_STANDARDS.md` State 4 与 `AGENTS.md` 写 `merge-<branch>`，night CONTEXT **worktree** 写 `merge-<slug>`。
8. toolbox CONTEXT **refusal** 复述了三段结构，与 `CONTEXT-MAP.md`「an entry does not repeat what can be read there」不符（轻微）。

---

## 11. 未确定

- 400 余条词条中嵌着的行为规则，只按 §2.3 所列 10 条核对了技能文本是否也有；其余未逐条核对。
- `verify-ticket.py` 的 `refuse()`/`refusals()` 与 `dispatch.sh` 的 `refuse()` 是否都给出三段（尤其「唯一下一步」）：只读到函数名，未读实现。
- `docs/contexts/night/how-it-works.md` 未读；它引用 ADR 0027，可能还有其他原则性表述。
- I5 中的 GitHub issue 链接与 Nowledge retro 记录（#406、#407、#408、#414、#447、spec-444/445/446/555 retro）未打开核实；只核实了其中 5 个提交哈希与标题。
- 2026-09-23 复审「441 条、162 条仍成立」的数字未回到 `汇总.md` 原文核实。
- G2 中 pstack 各原则的原文未读，§9.2 的近似关系只作线索。
- `dispatch.sh` 的 `AUTONOMOUS` 与 `shared.md` 规则 2 并存的原因（为 Cursor 还是为无人会话）原文未写明，§4 D2 的理由是推断。
- `shared.md` 规则 15 的触发事件：提交 `398644f9` 无说明，未查到事故。

## 12. 线索材料的使用与核实状态

| 材料 | 用了什么 | 状态 |
| --- | --- | --- |
| `I5-mmw-field-evidence.json` | PC1、PC12、PC17 的实地证据；夜次清单 | 5 个提交已核实；issue 与 Memory 未核实 |
| `G2-pstack-principles.md` | §9.2 的 pstack 近似 | 未核实 |
| `docs/reviews/2026-09-28-lightweight/汇总.md` | 两处理由写回、「不需要判断的交给脚本」的用户决定 | 写回的两句已在文件中核实；用户决定的原话未另找 Memory 核实 |
| `docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` | README 第 23、25、54 行的截图检查问题 | README 已改对（已核实）；ADR 0029 正文仍有此说法（已核实） |
| `docs/research/mmw-structure/2026-09-06-handoff.md` | 用户判据 5 条 | 原文已读；是否仍被用户认可未核实 |
| `M1`–`M3`、`I1`–`I3`、`T1`–`T4`、`C1`–`C5` | 仅扫读 M1–M3 中的「原则/ADR」字样 | 未采用其中结论 |
| Nowledge Mem | `8ec53374`、`756fc056`、`9040c9cf`、`415f96d0` | 已用 `nmem` 读到原文；`415f96d0` 的 source 为 agent |
