# N8-mmw-substrate：install、prompts、hooks、board、tests、notes 的事实清点

本文只清点事实，给下一轮「拆不拆、放哪、值不值」提供证据，不做归置决定。凡标「推断」的是从读到的内容推出、没有直接原文的结论；凡来自线索材料的结论都回到原文核对过，结果列在第 10 节。

## 0. 范围与读法

完整读过（逐行）：

- `mmw-v2/prompt/shared.md`（51 行）、`mmw-v2/prompt/hosts/{claude,codex,grok,pi}.md`（claude/grok/pi 为 0 字节，codex 1 行）、`mmw-v2/prompt/README.md`、`mmw-v2/prompt/render.py`（全文 125 行）、`mmw-v2/prompt/tests/run.sh`
- `mmw-v2/skills.txt`
- `mmw-v2/skills/dispatch/scripts/tool-guard.py`（全文 289 行）、`mmw-v2/skills/dispatch/scripts/turn-guard.py`（全文 340 行）
- `mmw-v2/board/AGENTS.md`、`mmw-v2/board/CLAUDE.md`、`mmw-v2/board/supervisor.py`（全文）、`mmw-v2/board/gates.py`（全文）
- `mmw-v2/tests/AGENTS.md`、`mmw-v2/tests/CLAUDE.md`、`mmw-v2/tests/lib/` 五个文件的头注释、12 个 `mmw-v2/tests/<name>/run.sh` 的头注释
- 根 `AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`、`mmw-v2/merge-notes/README.md`、`mmw-v2/downstream-notes/README.md`
- `docs/adr/0003`、`0005`、`0006`、`0007`、`0015`（全文）；约束材料 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（全文 176 行）
- `mmw-v2/skills/dispatch/references/editing-models.md`（`models.py config` 的用法说明）

按需读过：

- `mmw-v2/install.sh`（1851 行）：头注释 1–44 行、技能安装主循环 143–230、retired 目录 232–307、hook 段注释与安装点表 309–460 与 580–760、Codex 信任 757–800、提示词段 899–1013、task board LaunchAgent 1015–1056、Paseo 段头与 reload 1058–1110 与 1230–1258、Orca 段注释 1260–1300、`MMW_USES` 自检注释 1404–1420 与末尾 1600–1625、Nowledge Mem 与 Cursor MCP 段 1625–1851。没有逐行读的：hook 的 `grouped`/`cursor`/`extension` 三个安装函数体（460–580）、Codex 信任写入函数体（800–895）、Paseo 与 Orca 的 Python 实现体（1110–1230、1300–1400）、`MMW_USES` 核对实现（1420–1600）。关于这些部分的结论只来自它们的注释，属推断。
- `mmw-v2/board/server.py`（前 60 行与 `main`）、`board_data.py`、`settings_api.py`、`codeversion.py` 的头部；`mmw-v2/board/page/` 只列了目录。
- `mmw-v2/migrations/remove-verifier.py`：头部 60 行与 `main`、`run` 的结构；`mmw-v2/skills/dispatch/scripts/models.py` 头注释与 `--help`。
- `~/.mmw/models.json` 只读取结构；`~/.mmw/state/*/guard.log` 只读统计。

运行过的只读命令：`python3 mmw-v2/prompt/render.py --check`（退出 0）、`bash mmw-v2/install.sh --check`（退出 0，交给 installed checkout `.worktrees/mmw-installed` 核对，打印 `HOOKS-INSTALLED`，「技能 2 处 × 35 个」，13 个 hook 安装点）、`models.py --help`、若干 `git log`/`git show`、`nmem --json m search`。

## 1. 部件清单

| 部件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `mmw-v2/prompt/shared.md` | 用户级提示词的共用正文：五条读者事实、15 条规则、完成标准 | Claude Code、Codex、Pi、Grok 的每一个会话，含脚本起的 worker 与 reviewer（见 §9.2） |
| `mmw-v2/prompt/hosts/codex.md` | Codex 专属一行：`Never interrupt subagents or other agents while they are working. Wait quietly until they complete.` | Codex 每个会话 |
| `mmw-v2/prompt/hosts/{claude,grok,pi}.md` | 空文件，占位 | 无内容 |
| `mmw-v2/prompt/render.py` | 把 `hosts/<host>.md` + `shared.md` 拼成 `~/.codex/AGENTS.md`、`~/.pi/agent/AGENTS.md`、`~/.grok/AGENTS.md`，首行写正文 sha256；检查 Grok `[compat.claude] agents` | `install.sh`、launchd 任务 `com.mmw.prompt-sync`、维护者 |
| `mmw-v2/prompt/README.md` | 哪个源文件经哪条路到哪个 host、生成文件形状、三条命令 | 改提示词的维护者（根 `AGENTS.md` `## External References` 指向它） |
| `mmw-v2/prompt/tests/` | `render.py` 的 unittest，用 `MMW_V2_HOME` 隔离 | 维护者手跑 |
| `mmw-v2/skills.txt` | 装哪些技能的唯一名单，35 行，四种前缀 `engineering/`、`productivity/`、`self/`、`dd/` | `install.sh`、`check_own_skill_frontmatter.py`、`SKILL-SET-RULES.md` 称其为 skill set 的范围 |
| `mmw-v2/install.sh` | 唯一安装入口，装九样（头注释 2–17 行），`--check` 只读；记录 `~/.mmw/installed-root` | 用户授权后手跑；`dispatch.sh check` 每夜前调用（见 §3） |
| `~/.mmw/models.json`（机器状态，不在仓库） | `{version, runner, rows:{junior-worker, senior-worker, reviewer, advisor: {host, model, effort}}}`；本机现值 `version 9`、`runner "orca"` | `dispatch.sh`（经 `models.py`）、task board 设置页、`install.sh` 首装 |
| `mmw-v2/skills/dispatch/scripts/models.py`（只读其头与用法） | `models.json` 的唯一读写者；子命令 `config show|runner|set`、`runner`、`paseo-args`、`row`、`bypass-argv`、`launch-line` | `dispatch.sh`、board `settings_api.py`、`install.sh` Paseo 段、用户经 agent |
| `mmw-v2/skills/dispatch/references/editing-models.md` | 改 host/model/effort/runner 的三条命令与一个 runner 差异提醒 | 用户要求换模型时的 agent（dispatch 技能分派到此） |
| `mmw-v2/skills/dispatch/scripts/tool-guard.py` | host hook：在 `issue-<n>` 工作树里拒绝结束进程、手动关票/挪出队列、弹屏提问 | 五个 host 在工具调用前调用它；被拒绝的是 worker 与 reviewer |
| `mmw-v2/skills/dispatch/scripts/turn-guard.py` | host hook：主 agent 回合结束时重新拉起 watchdog，并在有票被占且 watchdog 不健康时不让回合结束 | 五个 host 在回合结束时调用；只作用于中继登记的主 agent |
| `mmw-v2/board/supervisor.py` | 按 `~/.mmw/boards.json` 为每个仓库守一个 `server.py`；`--register`、`--ensure` | `com.mmw.board` LaunchAgent、`dispatch.sh board` |
| `mmw-v2/board/server.py` | 127.0.0.1 上的任务板 HTTP 服务，每次启动生成 page token | 用户的浏览器；根 `.mmw/` 的产品答卷 |
| `mmw-v2/board/board_data.py`、`settings_api.py`、`gates.py`、`codeversion.py`、`page/` | 只读 GitHub 索引；读写 `models.json`；写请求同源与 token 闸门；代码变更自重启；前端 | server 进程 |
| `mmw-v2/board/AGENTS.md`（+ `CLAUDE.md` 一行 `@AGENTS.md`） | board 目录的约定与陷阱 | 在 `mmw-v2/board/` 工作的 agent |
| `mmw-v2/migrations/remove-verifier.py` | 一次性迁移：删历史 `verifier.*` 事件的机器块与 `models.json` 旧 verifier 行；`--dry-run`；退出 0/2 | ADR 0026 点名的一次执行（是否已执行：本机 `models.json` 无 verifier 行，推断已执行，未核实） |
| `mmw-v2/tests/AGENTS.md`（+ `CLAUDE.md`） | 测试目录约定、隔离变量清单、陷阱、命令 | 在 `mmw-v2/tests/` 工作的 agent |
| `mmw-v2/tests/<name>/run.sh` × 12 | 各子系统测试入口；头注释说测什么、要什么运行时（`board/run.sh` 没有头注释，根 `AGENTS.md` 明写此例外） | 维护者手跑；reviewer 的 Tests axis |
| `mmw-v2/tests/lib/check_module_paths.py`、`check_upstream_em_dashes.py`、`check_own_skill_frontmatter.py` | 每个 `run.sh` 先跑的三个共用检查（toolbox `CONTEXT.md` 称 **shared lints**） | 所有套件 |
| `mmw-v2/tests/lib/parse_k.sh`、`run_unittests.py` | `-k` 解析与 unittest 判定（跳过数非 0 或运行数为 0 即失败） | 四个套件的 `run.sh` |
| 根 `AGENTS.md`（+ `CLAUDE.md` 一行 `@AGENTS.md`） | 本仓库的导航、Self-hosting boundary、命令、参考表、约定、陷阱 | 本仓库里每一个 agent 会话 |
| `CODING_STANDARDS.md` | 本仓库代码规则：技能与脚本、状态与配置 | code-review 的 Standards axis（`code-review/references/standards-reviewer.md` 第 9 行）；`to-tickets`、`to-spec` 把相关条目带进票与 spec |
| `TESTING.md` | 本仓库测试规则：测试证明什么、布局、改动要跑哪些套件 | code-review 的 Tests axis（`code-review/references/tests-reviewer.md` 第 31 行） |
| `mmw-v2/merge-notes/README.md` + 24 份说明 | 三个上游 subtree 被本仓改过的段落、理由、再拉上游时的取舍；`disable-model-invocation` 成对规则；host 中立 | 拉上游或改上游技能的人（根 `AGENTS.md` important-if 块）；`SKILL-SET-RULES.md` 引用它 |
| `mmw-v2/downstream-notes/README.md` + 19 份现行、7 份 archive | 本仓改动使消费仓库产物失效时的说明：三个固定标题 | 写的一方：本仓做出这类改动的 agent（根 `AGENTS.md` Key Conventions）；读的一方：维护消费仓库的人或 agent，没有任何技能点名它（grep 结果见 §4） |
| ADR 0003/0005/0006/0007/0015 | 安装形态、docs 层、技能安装位置、提示词源、不交付 subagent 的决定 | 维护者；票的 `Read first` 列出时的 worker |

## 2. 内容分类

本单元不含任何 `SKILL.md`。下表按节切的是会被 agent 读到的说明性文件与脚本头注释。「频率」一栏：每次＝该读者每次会话都载入；分支＝只有某个条件下才读。

### 2.1 `mmw-v2/prompt/shared.md`

读者与时刻（全部各节相同）：Claude Code 经 `~/.claude/CLAUDE.md` 软链、Codex/Pi/Grok 经生成的 `AGENTS.md`，在每个会话开始时整份载入系统上下文；包括脚本起的 worker、reviewer、advisor 会话（提交 `0b6d47e3` 说明无法按会话关掉，见 §9.2）。频率：每次。

| 段落 | 类型 | 备注 |
| --- | --- | --- |
| 第 1–9 行：`Five facts about that reader` 与一句话总结 | 目的与立场 | 规定读者是谁、为什么后面每条成立 |
| 第 11 行：`A session a script started with no person in it …` | 带理由的规则 + 分派 | 把「问我」改路由到技能的提问途径、「汇报」改用技能的格式、rule 14 的「已点名项目」读作票的既定方案。只对 dispatched 会话起作用 |
| `## Who decides what` rule 1 | 带理由的规则 | 工程决定自己做、产品决定问；列出只有 owner 能做的五类决定 |
| rule 2 | 带理由的规则 | 讨论中的问题只答不做；已批准计划是开工信号，不以「shall I continue?」结束回合；夜里的活早上冷读 |
| rule 3 | 带理由的规则 | 该反对就反对、不制造反对；正确性/安全/钱的确认流程 |
| `## How to report` rule 4 | 带理由的规则 | 可核对的证据；「should」「tests pass」不算；未核实要标 |
| rule 5 | 带理由的规则 + 格式 | 报原因与后果，不报代码；按改动大小定篇幅；删减时最后删警告、数字、前提 |
| rule 6、7 | 带理由的规则 | 术语用法；不用修辞 |
| rule 8 | 带理由的规则 + 格式 | 每个引用要锚定：路径 + 标题/标识符，原文照抄 |
| rule 9 | 格式与模板 | 何时用列表表格 |
| `## How to work` rule 10 | 做法 + 带理由的规则 | 写之前先点名读者、他们在做什么、能看到什么 |
| rule 11 | 带理由的规则 | 失败自己重做，只把只有 owner 能做的交回 |
| rule 12 | 做法 | 读多少文件；没读的部分得出的结论标推断 |
| rule 13 | 带理由的规则 | 文件只描述主题现状，决定类文件除外；外科式编辑 |
| rule 14 | 顺序 + 做法 | 先搜 GitHub 与包注册表，再网；读实现文件；三选一；回复里列出搜索与 URL |
| rule 15 | 带理由的规则 | 默认禁止全仓全量测试 |
| `## What this file looks like when it is working` | 目的与立场 | 整份文件的完成标准 |

沉积：无。MMW 专有词只出现在第 11 行（worker、reviewer、ticket）、rule 2（night）、rule 8（`CHECK:`、reviewer）、rule 13（ticket comment）（grep 计数）。

### 2.2 `mmw-v2/prompt/hosts/codex.md`

一行规则，无理由；Codex 每次载入。ADR 0007 `## Consequences` 末条记录来源：原 `~/AGENTS.md` 的一句，Pi 与 Grok 沿 cwd 向上也会读到，所以并入 Codex 专属件。类型：带理由的规则（理由只在 ADR 里）。

### 2.3 `mmw-v2/prompt/README.md` 与 `render.py` 头注释

| 段落 | 类型 | 读者·时刻 |
| --- | --- | --- |
| README 第 3 行与表格（文件 / 谁读 / 怎么到 host） | 命令与接口 | 改提示词的维护者；分支 |
| README 第 13 行（生成文件形状、哈希、退出 2） | 命令与接口 | 同上 |
| README 第 15 行（Grok `[compat.claude] agents` 必须 false） | 带理由的规则 | 同上 |
| README 第 17 行（Cursor 不在此列） | 带理由的规则 | 同上 |
| README 命令块、第 26 行 launchd | 命令与接口 | 同上 |
| `render.py` 头注释（三种状态 `ours`/`edited`/`foreign`、退出 0/1/2、`MMW_V2_HOME`） | 命令与接口 | 维护者、测试 |

### 2.4 `mmw-v2/install.sh` 注释

读者：修改或排查安装的维护者；运行者只看输出。频率：分支。

| 段落 | 类型 | 备注 |
| --- | --- | --- |
| 头注释 2–17 行：九样东西 | 命令与接口 | 与根 `AGENTS.md` Commands 行、toolbox `CONTEXT.md` **`install.sh`** 条目三处列同一清单（§4） |
| 19–20 行：上一代装过、这次摘掉的东西 | 沉积（但记录的是仍在执行的清理动作） | |
| 22–28 行：三个来源、软链不是拷贝、description 要重开会话 | 带理由的规则 | |
| 30–35 行：两种模式、`没查`/`不一致`、`HOOKS-INSTALLED` | 命令与接口 | |
| 37–43 行：技能装两处的理由 | 带理由的规则 | ADR 0006 的摘要 |
| 54–97 行：`ours_skill_target`、`stale_links` 注释（「ui-qa 从 skills.txt 拿掉之后八处软链留了一整天」） | 带理由的规则 + 沉积（事故来源） | |
| 125–129 行：`--check` 交给 installed checkout | 带理由的规则 | Self-hosting boundary 的唯一脚本化部分（§7） |
| 232–236、270–274 行：retired 位置 | 带理由的规则 + 实测记录 | 「实测里 Grok 取 `~/.grok/skills` 那份」 |
| 309–324 行：hook 段总述、Grok 环境变量守卫、合并不覆盖 | 带理由的规则 + 实测记录 | Grok 0.2.73 / 1.0 的变量差异 |
| 583–598 行：摘除本仓旧 hook 的理由与 `SWEPT` 清单 | 带理由的规则 | |
| 757–767 行：Codex `trusted_hash` | 实测记录 + 带理由的规则 | 2026-08-29、2026-09-10 实测 |
| 899–905 行：提示词段 | 带理由的规则 | ADR 0007 摘要 |
| 1015–1018 行：board LaunchAgent | 带理由的规则 | |
| 1058–1064、1236–1240 行：Paseo | 带理由的规则 | |
| 1260–1273 行：Orca | 带理由的规则 + 实测记录（Orca 1.4.199 源文件） | |
| 1404–1415 行：`MMW_USES` 自检 | 带理由的规则 | 「什么都没核的检查不许读起来像通过」＝ADR 0008 |
| 1624–1625、1756–1761 行：Nowledge Mem、Cursor MCP | 带理由的规则 | 与 `CODING_STANDARDS.md` 最后一条重复（§4） |

`SKILL-SET-RULES.md` `### Redundancy and bloat` 的 Sediment 表规定「a dated measurement, "tested on"」的归宿是 script header，所以这些实测记录放在这里是该规则指定的位置。

### 2.5 `tool-guard.py` 头注释与文字

读者：修改 hook 的维护者读头注释；被拦下的 worker/reviewer 只读拒绝串（host 把它作为 deny reason 送回模型）。

| 段落 | 类型 | 读者·频率 |
| --- | --- | --- |
| 第 2–20 行：三件事与各自理由（`gh issue close` 跳过 closeout；屏幕上的问题没人答；别人的进程和卡死的进程分不清） | 目的与立场 + 带理由的规则 | 维护者；分支 |
| 22–26 行：用法与 `<host>` | 命令与接口 | 同上 |
| 28–31 行：「It refuses rather than checks」 | 带理由的规则 | 同上 |
| 33–37 行：受管判定＝工作目录 basename `issue-<n>` | 带理由的规则 | 同上 |
| 39–46 行：Cursor 导入 Claude hook，只读 payload 的 `cursor_version` | 带理由的规则 + 实测 | 同上 |
| `REFUSAL`、`NO_QUESTION`、`no_kill()` 三段拒绝文字 | 格式与模板（agent 读的出路） | 被拦下的 worker/reviewer；只在被拦时 |
| `governed_ticket` docstring（Cursor 2026-09-06 实测）、`runs` docstring（2026-08-30 worker 撞上）、`no_kill` docstring（2026-09-05 三个 agent 三种错答） | 沉积（事故与实测来源），也是保留设计的理由 | 维护者 |

### 2.6 `turn-guard.py` 头注释与文字

| 段落 | 类型 | 读者·频率 |
| --- | --- | --- |
| 第 2–14 行：「The worst way a night dies…」与两件事 | 目的与立场 | 维护者 |
| **Whose turn**（16–27 行） | 带理由的规则 | 维护者 |
| **The predicate**（29–34 行） | 带理由的规则（判据） | 维护者 |
| **What each host can do at a turn end** 表（36–57 行） | 命令与接口（各 host 的退出码/输出形状） | 维护者 |
| **Three lessons …** copied from firstmate（59–77 行） | 带理由的规则 + 沉积（来源） | 维护者 |
| **It never breaks a host**（79–83 行） | 带理由的规则 + 命令与接口（退出 0/1/2） | 维护者 |
| **Checked against the real hosts** 2026-09-10（85–123 行） | 实测记录（归宿即脚本头） | 维护者；「每次新 host 或升级都要重跑」 |
| `guard()` 里拼出的 `MMW turn guard: …` 文字 | 格式与模板（主 agent 读到的唯一处理说明） | 主 agent；只在被拦时。`dispatch/references/night.md` 第 19 行把 `MMW turn guard:` 路由到 `## 3. Each time something wakes you`，但该节没有针对它的行，处理步骤全在这条消息里（已核实） |

### 2.7 根 `AGENTS.md`

读者：本仓库里起的每一个 agent 会话（Claude 经 `CLAUDE.md` 的 `@AGENTS.md`，其余 host 原生读 `AGENTS.md`）。频率：每次；important-if 块只在条件成立时适用。

| 段落 | 类型 |
| --- | --- |
| 开头三段（MMW 是什么；`mmw-v2/` 才是活的；本仓也是自己流水线的消费仓库；「The skills in this repository are deliverables, not the working instructions of an agent working on it.」） | 目的与立场 |
| `## Self-hosting boundary` 四条 | 带理由的规则（只在本仓消费自己流水线时适用） |
| `## Package Manager` | 命令与接口 |
| `## Commands` 表 | 命令与接口 |
| `## External References` 表（Need → File） | 重入与分派（按需求把读者送到文件） |
| `## Key Conventions` | 带理由的规则 + 命令与接口 |
| `## Gotchas` 第一条（四个 promotion 步骤） | 顺序 |
| `## Gotchas` 其余四条 | 做法 / 带理由的规则（沙箱与 hook、Codex 信任、hook 不读环境、凭据写入技能目录的后果） |
| important-if 两块 | 分派（条件适用的规则） |
| 末行「Before working in a subdirectory, search it for an `AGENTS.md`」 | 做法 |

### 2.8 `mmw-v2/board/AGENTS.md`、`mmw-v2/tests/AGENTS.md`

读者：在该子目录工作的 agent（根 `AGENTS.md` 末行要求先读）。频率：分支。

- `board/AGENTS.md`：首段＝目的（「It is a second store for nothing」）；Key Conventions 四条＝命令与接口 + 带理由的规则；Gotchas 三条＝做法。
- `tests/AGENTS.md`：首段＝目的；Key Conventions 八条＝做法 + 带理由的规则（隔离变量清单、`MMW_HOME` 隔离、fake 二进制、`set -e` 例外）；Gotchas 八条＝做法；Commands 表＝命令与接口。

### 2.9 `CODING_STANDARDS.md`、`TESTING.md`

读者：code-review 的 Standards axis 与 Tests axis，在审一张票时读（分支）；`to-spec` 第 117 行、`to-tickets` 第 174 行把相关小节列进 spec/票的来源。

- `CODING_STANDARDS.md` `## Skills and scripts` 四条：带理由的规则（技能目录只放 agent 读或跑的东西；脚本按自身位置找邻居；runner 命令只在适配器；拒绝三段式 + 实测写进脚本头）。`## State and configuration` 五条：带理由的规则 + 命令与接口（`models.json` 只经 `models.py config`；`~/.mmw` 布局；票状态是事件折叠；landing 在 `origin/<base branch>`；Cursor MCP 条目）。
- `TESTING.md` `## What a test proves`：带理由的规则（可成为原则的候选：测试证明脚本行为，不钉文字）。`## Layout`：做法。`## Which suites a change needs`：带理由的规则。

### 2.10 `merge-notes/README.md`、`downstream-notes/README.md`

读者：merge-notes——拉上游 subtree 或改上游技能的人（根 `AGENTS.md` important-if 块要求先读），以及按 `SKILL-SET-RULES.md` `### Upstream skills` 做 diff 的审查者；downstream-notes——在本仓做出使消费仓库产物失效改动的 agent（写）。频率：分支。

| 段落 | 类型 |
| --- | --- |
| merge-notes 开头三行（给意图不给 diff；diff 命令；与 downstream 的方向） | 目的 + 命令与接口 |
| `## 上游更新时怎么用` 1–4 | 顺序 |
| `## disable-model-invocation` | 带理由的规则（七个技能名单已核实，§5） |
| `## host 中立` 第一、二段 | 带理由的规则（规则本体在 `SKILL-SET-RULES.md` `### Hand-offs` 与 `### Paths and host neutrality`） |
| `## host 中立` 第三段（`ready-for-afk` 已知偏差，不修不加守卫） | 沉积性质的决定记录；按 shared.md rule 13，merge-note 的主题就是决定，属允许 |
| `## 本仓自有正文的技能` | 带理由的规则 |
| `## 目前有说明的技能` | 分派（索引） |
| downstream-notes 开头两行 | 目的 |
| `## 什么改动必须写一份` | 带理由的规则 |
| `## 一份写三样`、文件名、索引行、archive 规则 | 格式与模板 + 顺序 |
| 两个索引节 | 分派（索引） |

### 2.11 `editing-models.md`（`models.py config` 用法）

读者：用户要求换 host/model/effort/runner 时的 agent；分支。`## Change one role`＝命令与接口 + 做法（level 与 host 的关系）；`## Change the runner`＝命令与接口 + 带理由的规则（不能观察会话内程序的 runner 对 `resume` 与 wake 答 exit 4，要告诉用户）。

### 2.12 测试入口与 `tests/lib/`

`run.sh` 头注释：命令与接口 + 做法（要什么运行时、缺了就失败不静默跳过），读者是跑测试的维护者与 Tests axis。`tests/lib/` 三个检查脚本的 docstring：带理由的规则（为什么这个检查存在）+ 沉积（`check_own_skill_frontmatter.py` 记录 advisor 与 ui-acceptance 冒号事故，修于 `d37a6048`）。

### 2.13 ADR

每份 ADR 是决定记录，类型天然是「带理由的规则 + 沉积（被取代说明）」。0003、0006、0014 标题上方有 `>` 注，指回 0006/0015 说明哪些句子已不成立。读者：维护者；票的 `Read first` 列出时的 worker。

## 3. 连线

### 3.1 对外交接

- `install.sh` 产出：`~/.agents/skills/*` 与 `~/.claude/skills/*` 软链 → 五个 host 启动时扫描；各 host 的 hook 配置（`~/.claude/settings.json`、`~/.codex/hooks.json` + `config.toml` 的 `trusted_hash`、`~/.cursor/hooks.json`、`~/.grok/hooks/mmw-verify-ticket.json`、`~/.grok/hooks/mmw-turn-guard.json`、`~/.pi/agent/extensions/mmw-verify-ticket.ts`、`mmw-turn-guard.ts`）→ host 调 hook；`~/.claude/CLAUDE.md`、`~/.claude/rules/mmw-claude.md` 软链与三份生成的 `AGENTS.md` → host 载入提示词；`com.mmw.prompt-sync`、`com.mmw.board` 两个 LaunchAgent；`~/.paseo/config.json`、`~/.local/bin/paseo`；Orca setup；Nowledge Mem 的 `mmw-toolbox` Space 与 `mmw-worker`/`mmw-reviewer` Identity；`~/.cursor/mcp.json` 的 `nowledge-mem`；`~/.mmw/models.json`（仅缺席时）；`~/.mmw/installed-root`。
- `dispatch.sh check`（`dispatch.sh` 2344–2360 行）先跑 `install.sh --check`；不齐且本 checkout 就是 installed checkout 时直接跑完整 `install.sh` 修复，剩余问题只作警告，不挡夜（已核实）。
- `dispatch.sh board`/`open` 调 `supervisor.py --ensure`（`dispatch.sh` 97、409–418 行）。
- `tool-guard.py` 产出：拒绝 JSON（按 host 形状）→ host 把理由送回模型。
- `turn-guard.py` 产出：exit 2 + stderr（claude/codex/grok/pi 扩展）或 `followup_message`（cursor）→ 主 agent；写 `$MMW_HOME/state/<owner>__<name>/guard.log`；调用 `watchdog.arm` 拉起 `watchdog.py`；调用每个 runner 适配器的 `self`。
- board 读 GitHub（经 verify-ticket 的 `events.py`、`issue_tree.py` 与 dispatch 的 `ghlist.py`），读写 `models.json`（经 `models.py`），读 `boards.json`。
- `CODING_STANDARDS.md`/`TESTING.md` → code-review 两个 axis。
- merge-notes → 拉上游的人、`SKILL-SET-RULES.md` 的审查。
- downstream-notes → 消费仓库维护者（无技能点名）。
- `shared.md` → 四个 host 的每一个会话。

### 3.2 边

```edges
mmw-v2/install.sh -> mmw-v2/skills.txt : reads
mmw-v2/install.sh -> ~/.agents/skills : writes (symlinks)
mmw-v2/install.sh -> ~/.claude/skills : writes (symlinks)
mmw-v2/install.sh -> mmw-v2/prompt/render.py : runs-script
mmw-v2/install.sh -> ~/.claude/CLAUDE.md : writes (symlink to mmw-v2/prompt/shared.md)
mmw-v2/install.sh -> ~/.claude/rules/mmw-claude.md : writes (symlink to mmw-v2/prompt/hosts/claude.md)
mmw-v2/install.sh -> com.mmw.prompt-sync : writes (LaunchAgent)
mmw-v2/install.sh -> com.mmw.board : writes (LaunchAgent)
mmw-v2/install.sh -> host hook configs : writes (registers tool-guard.py pretool/question, turn-guard.py stop)
mmw-v2/install.sh -> ~/.codex/config.toml : writes (trusted_hash)
mmw-v2/install.sh -> mmw-v2/skills/dispatch/scripts/models.py : runs-script (imports by path, first-install defaults)
mmw-v2/install.sh -> mmw-v2/skills/dispatch/hosts.json : reads (via models.py)
mmw-v2/install.sh -> ~/.mmw/models.json : writes (only when absent)
mmw-v2/install.sh -> ~/.paseo/config.json : writes
mmw-v2/install.sh -> mmw-v2/skills/dispatch/scripts/runners/*.sh : reads (# MMW_USES:, --check only)
mmw-v2/install.sh -> Nowledge Mem : writes (Space, Identities)
mmw-v2/install.sh -> ~/.cursor/mcp.json : writes
mmw-v2/install.sh -> ~/.mmw/installed-root : writes
mmw-v2/install.sh -> <installed checkout>/install.sh : hands-off-to (--check from another checkout)
com.mmw.prompt-sync -> mmw-v2/prompt/render.py : runs-script (on WatchPaths change)
mmw-v2/prompt/render.py -> mmw-v2/prompt/shared.md : reads
mmw-v2/prompt/render.py -> mmw-v2/prompt/hosts/*.md : reads
mmw-v2/prompt/render.py -> ~/.codex/AGENTS.md : writes
mmw-v2/prompt/render.py -> ~/.pi/agent/AGENTS.md : writes
mmw-v2/prompt/render.py -> ~/.grok/AGENTS.md : writes
mmw-v2/prompt/render.py -> ~/.grok/config.toml : reads ([compat.claude] agents)
host session -> mmw-v2/prompt/shared.md : reads (every session, four hosts)
host (claude|codex|grok|cursor|pi) -> mmw-v2/skills/dispatch/scripts/tool-guard.py : calls (pretool; question on claude|grok|codex only)
host (claude|codex|grok|cursor|pi) -> mmw-v2/skills/dispatch/scripts/turn-guard.py : calls (turn end)
mmw-v2/skills/dispatch/scripts/tool-guard.py -> mmw-v2/skills/ui-acceptance/scripts/refusal.py : runs-script (imports)
mmw-v2/skills/dispatch/scripts/tool-guard.py -> worker/reviewer session : writes-event (deny reason; custom: refuses)
mmw-v2/skills/dispatch/scripts/tool-guard.py -> mmw-v2/skills/verify-ticket/scripts/verify-ticket.py : hands-off-to (refusal names --closeout)
mmw-v2/skills/dispatch/scripts/turn-guard.py -> mmw-v2/skills/dispatch/scripts/watchdog.py : runs-script (arm)
mmw-v2/skills/dispatch/scripts/turn-guard.py -> mmw-v2/skills/dispatch/scripts/statedir.py : reads
mmw-v2/skills/dispatch/scripts/turn-guard.py -> mmw-v2/skills/dispatch/scripts/runners/*.sh : runs-script (self)
mmw-v2/skills/dispatch/scripts/turn-guard.py -> $MMW_HOME/state/<repo>/watches.json : reads
mmw-v2/skills/dispatch/scripts/turn-guard.py -> $MMW_HOME/state/<repo>/guard.log : writes
mmw-v2/skills/dispatch/scripts/turn-guard.py -> main agent : wakes (holds the turn / followup_message)
mmw-v2/skills/dispatch/references/night.md -> MMW turn guard line : re-enters-at (## 3. Each time something wakes you)
mmw-v2/skills/dispatch/scripts/dispatch.sh -> mmw-v2/install.sh : runs-script (check; full install when this checkout is installed)
mmw-v2/skills/dispatch/scripts/dispatch.sh -> mmw-v2/board/supervisor.py : runs-script (--ensure)
com.mmw.board -> mmw-v2/board/supervisor.py : runs-script (KeepAlive)
mmw-v2/board/supervisor.py -> ~/.mmw/boards.json : reads/writes
mmw-v2/board/supervisor.py -> mmw-v2/board/server.py : runs-script
mmw-v2/board/supervisor.py -> mmw-v2/skills/dispatch/scripts/statedir.py : reads (imports)
mmw-v2/board/board_data.py -> mmw-v2/skills/verify-ticket/scripts/events.py : reads (loads by path)
mmw-v2/board/board_data.py -> mmw-v2/skills/verify-ticket/scripts/issue_tree.py : reads (loads by path)
mmw-v2/board/board_data.py -> mmw-v2/skills/dispatch/scripts/ghlist.py : reads (loads by path)
mmw-v2/board/settings_api.py -> mmw-v2/skills/dispatch/scripts/models.py : reads (imports)
mmw-v2/board/settings_api.py -> ~/.mmw/models.json : writes (via models.py)
mmw-v2/board/codeversion.py -> mmw-v2/board/*.py + LOADED five scripts : reads (fingerprint)
.mmw/ (root product answers) -> mmw-v2/board/page/index.html : reads (mmw-page-token meta)
mmw-v2/skills/dispatch/scripts/dispatch.sh -> ~/.mmw/models.json : configured-by (via models.py)
mmw-v2/skills/dispatch/references/editing-models.md -> mmw-v2/skills/dispatch/scripts/models.py : cites (config set|runner|show)
mmw-v2/tests/<name>/run.sh -> mmw-v2/tests/lib/check_module_paths.py : runs-script
mmw-v2/tests/<name>/run.sh -> mmw-v2/tests/lib/check_upstream_em_dashes.py : runs-script
mmw-v2/tests/<name>/run.sh -> mmw-v2/tests/lib/check_own_skill_frontmatter.py : runs-script
mmw-v2/tests/lib/check_own_skill_frontmatter.py -> mmw-v2/skills.txt : reads
mmw-v2/tests/dispatch/test_dispatch.sh -> mmw-v2/install.sh : runs-script (scenario_install*, under MMW_V2_HOME)
mmw-v2/tests/dispatch/test_tool_guard.py -> mmw-v2/skills/dispatch/scripts/tool-guard.py : runs-script
mmw-v2/tests/liveness/test_guard.sh -> mmw-v2/skills/dispatch/scripts/turn-guard.py : runs-script
mmw-v2/prompt/tests/test_render.py -> mmw-v2/prompt/render.py : runs-script
mmw-v2/migrations/remove-verifier.py -> mmw-v2/skills/dispatch/scripts/models.py : runs-script (imports)
mmw-v2/migrations/remove-verifier.py -> GitHub issue comments : writes (edits comments)
code-review Standards axis -> CODING_STANDARDS.md : reads
code-review Tests axis -> TESTING.md : reads
to-spec -> CODING_STANDARDS.md : cites
to-tickets -> CODING_STANDARDS.md : cites
SKILL-SET-RULES.md -> mmw-v2/merge-notes/README.md : cites (squash diff command; disable-model-invocation)
SKILL-SET-RULES.md -> CODING_STANDARDS.md : cites (refusal shape)
mmw-v2/merge-notes/README.md -> SKILL-SET-RULES.md : cites (### Hand-offs, ### Paths and host neutrality, ### Descriptions)
mmw-v2/merge-notes/README.md -> mmw-v2/downstream-notes/README.md : cites
AGENTS.md -> mmw-v2/merge-notes/README.md : cites (important-if block)
AGENTS.md -> mmw-v2/downstream-notes/README.md : cites
AGENTS.md -> CODING_STANDARDS.md : cites
AGENTS.md -> TESTING.md : cites
AGENTS.md -> mmw-v2/prompt/README.md : cites
mmw-v2/board/AGENTS.md -> mmw-v2/skills/verify-ticket/scripts/events.py : cites
mmw-v2/tests/AGENTS.md -> mmw-v2/skills/dispatch/scripts/turn-guard.py : cites (header records the manual host check)
retro -> AGENTS.md : writes (prevention destination repository-agents; custom: proposes)
```

## 4. 重复

用 `grep -rniE` 扫了 `mmw-v2/`、`docs/`（排除 `archive/`、`deprecated/`、`code-landing-refs/`、`workflow-compare/`、`reviews/`）、根 `AGENTS.md`、`TESTING.md`、`CODING_STANDARDS.md`、`CONTEXT-MAP.md`。

| 规则 / 定义 / 命令 | 出现位置 | 判定 |
| --- | --- | --- |
| `install.sh` 装的九样 | `install.sh` 头注释 2–17 行；根 `AGENTS.md` `## Commands` 第一行；`docs/contexts/toolbox/CONTEXT.md` **`install.sh`**（只说「nine items its header comment lists」）；`docs/research/.../C5-toolbox.json` | 真重复：`AGENTS.md` 那一行把九样逐项复述；`CONTEXT.md` 只指向头注释，不是重复 |
| 提示词的路由（哪个源到哪个 host） | `prompt/README.md` 表；`install.sh` 899–905 行；根 `AGENTS.md` `## Key Conventions` 第三条；ADR 0007 | 真重复（三处现行描述 + ADR 决定记录） |
| Grok `[compat.claude] agents` 要 false | `prompt/README.md` 第 15 行；`render.py` `grok_compat_on`；ADR 0007；根 `AGENTS.md` `## External References`「Grok's `[compat.claude]` requirement」只是指针 | 真重复（README 与 ADR），代码是执行处 |
| 「hook 只从 payload 判断，不读环境变量」 | 根 `AGENTS.md` `## Gotchas` 第四条；`install.sh` 316–321 行；`tool-guard.py` 头 39–46 行；`turn-guard.py` 头 59–77 行；ADR 0021 `## Consequences` | 真重复，五处 |
| Grok 两个环境变量 `GROK_AGENT`/`GROK_HOOK_EVENT`、不判 `GROK_SESSION_ID` | `install.sh` 318–320 行与 `GROK_GUARD`；`turn-guard.py` 65–77 行与 `stands_down`；ADR 0021 | 真重复（注释两处 + ADR）；实现两处（安装的 shell 前缀与 turn-guard 自身判断，属两层防护，不是文字重复） |
| 四个 promotion 步骤 | 根 `AGENTS.md` `## Gotchas` 第一条；`docs/contexts/toolbox/CONTEXT.md` **the four promotion steps** | 真重复（glossary 定义复述步骤） |
| Self-hosting boundary | 根 `AGENTS.md` `## Self-hosting boundary`；toolbox `CONTEXT.md` **self-hosting boundary**、**installed checkout**；`to-tickets/references/person-ticket.md` 第 11 行与 merge-note `to-tickets.md` 153 行、`teach.md` 28 行引用它 | glossary 为定义性复述；技能里是引用，不是重复 |
| `models.json` 只经 `models.py config` 修改 | 根 `AGENTS.md` `## Commands` 最后一行（「The only way to change」）；`CODING_STANDARDS.md` `## State and configuration` 第一条；`editing-models.md` 第 3 行；`models.py` 头注释；toolbox `CONTEXT.md` **`models.py`** | 真重复，五处 |
| `MMW_V2_HOME` 只给测试、`MMW_HOME` 给运行时 | `TESTING.md` `## Layout` 第二条；`install.sh` 100、905、1017、1064 行；`render.py` 头；`tests/AGENTS.md` Gotchas 末条；toolbox `CONTEXT.md` **`MMW_V2_HOME`** | 真重复 |
| 拒绝三段式 | `CODING_STANDARDS.md` 第 10 行；`refusal.py` 第 10 行起；toolbox `CONTEXT.md` **refusal**；`SKILL-SET-RULES.md` 第 134 行（引用） | `CODING_STANDARDS.md` 与 `CONTEXT.md` 真重复；`refusal.py` 是实现 |
| board 依赖哪些脚本 | `board/AGENTS.md` Key Conventions 第一条（「those four scripts」）与第三条（「the five scripts」）；`TESTING.md` `## Which suites` 列四个；`codeversion.py` `LOADED` 列五个（多 `statedir.py`）；task-board `CONTEXT.md` 第 26 行 | 真重复且不一致：`statedir.py` 被 board 载入（`supervisor.py` 第 21 行、`LOADED`），但 `TESTING.md` 没把它列进「改了要跑 board 套件」的清单；relay 与 liveness 的 `run.sh` 头注释列了 `statedir.py` |
| `disable-model-invocation` 成对 | `merge-notes/README.md` `## disable-model-invocation`；toolbox `CONTEXT.md` 条目；各 merge-note 只写自己站哪边（`to-spec.md` 41、`triage.md` 36、`to-tickets.md` 50、`implement.md` 24 各复述「两处必须同增同删」半句） | README 与 CONTEXT 真重复；四份 merge-note 各带半句复述 |
| downstream-note 的触发条件 | `downstream-notes/README.md` `## 什么改动必须写一份`；根 `AGENTS.md` Key Conventions 末条与 important-if 块第三条；toolbox `CONTEXT.md` **downstream-note** | 真重复，四处 |
| 共用 lint 三件 | 根 `AGENTS.md` `## Commands` 第五行；toolbox `CONTEXT.md` **shared lints**；各检查脚本 docstring | 真重复（AGENTS 与 CONTEXT）；`tests/AGENTS.md` 首段与 Key Conventions 第二条说 `lib/` 放 `-k` 解析与 unittest 判定，没提这三个检查（遗漏，不是重复） |
| 「never end a process you did not start」 | `tool-guard.py` 头 15–20 行与 `no_kill()`；`ui-acceptance/SKILL.md` `## Five rules while the product is running` rule 1（并写「Your shell refuses `kill`…」）；提交 `0beb2906` 说「The four standing rules are in the launch prompt and in SKILL.md」 | 一条规则的两个载体：hook 强制 + 技能文字，属同义（真重复，但一个是强制一个是说明，见 §9.3） |
| 「关票只经 `--closeout`」 | `tool-guard.py` 头 5–8 行与 `REFUSAL`；`implement/SKILL.md` 第 99 行 step 8「Never close the ticket or swap its labels yourself: a hook blocks the command.」；`merge-notes/README.md` 第 32 行 | 同上 |
| 「屏幕上不放问题」 | `tool-guard.py` 头 10–13 行与 `NO_QUESTION`；`implement/SKILL.md` 第 23 行「Put no question on the screen…」；`shared.md` 第 11 行（「what it would ask me goes where its skills route questions」） | 三处同义；`NO_QUESTION` 与 `implement` 第 23 行给的出路基本一致（`Decisions I made on my own` / `ABANDON: AC<n> decision` + sub-issue） |
| rule 15「默认不跑全量」 | `shared.md` rule 15；`merge-notes/implement.md` 第 19 行把它作为改动理由；`implement/SKILL.md` 第 32 行（「the tests the repository's own instructions name」） | 同义（implement 那句是 rule 15 在票里的落地） |
| rule 13「文件只写现状」 | `shared.md` rule 13；`SKILL-SET-RULES.md` Sediment 表与 `## Editing` 末条（「The file states what is true now; what changed and why goes to the commit message」） | 同义：一条对所有文件、一条对技能文本 |
| rule 8「引用锚定、原文照抄」 | `shared.md` rule 8；`SKILL-SET-RULES.md` `### Vocabulary`「copied verbatim」 | 只是同词：shared.md 管回复里的引用，SKILL-SET-RULES 管程序读的名字 |
| rule 2「讨论中的问题 vs 开工信号」 | 仅 `shared.md` | 无重复 |
| rule 14「先找现成实现」 | 仅 `shared.md`（第 11 行对 worker 的改读也在同文件） | 无重复 |
| 「nobody polls, the night has no clock」 | `CODING_STANDARDS.md` 第 16 行；ADR 0010、0017；night `CONTEXT.md` | 真重复（标准文件复述 ADR 决定） |
| landing 在 `origin/<base branch>` | `CODING_STANDARDS.md` 第 17 行；ADR 0023、0025；night `CONTEXT.md`；`night.md` | 真重复 |
| Cursor MCP 去掉 `type` 字段 | `CODING_STANDARDS.md` 第 18 行；`install.sh` 1756–1761 行 | 真重复 |

## 5. 上游差异

本单元不含上游技能正文。与上游有关的三点事实：

- `install.sh` 的技能软链做法来自 mattpocock 上游 `scripts/link-skills.sh`：最近一次 squash 提交 `5b1a4c51`（2026-09-18，「Squashed 'mmw-v2/upstream/' changes from 6654f6b6..c55ee460」）里该脚本 `DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills")`，注释「Each entry is a symlink into this repo」（已核实，`git show 5b1a4c51:scripts/link-skills.sh`）。MMW 在此之上加了名单文件、残留摘除、`--check` 与另外八样安装。上游脚本注明「dev-only script … not a supported installer」。
- `merge-notes/README.md` `## disable-model-invocation` 的七个保留成对设置的技能（`setup-matt-pocock-skills`、`grill-me`、`grill-with-docs`、`handoff`、`teach`、`improve-codebase-architecture`、`wait-what`）与本仓现状一致：`skills.txt` 所列上游技能里，恰好这七个同时有 `disable-model-invocation: true` 与 `allow_implicit_invocation: false`（已核实，grep 两类文件）。
- `skills.txt` 里没有 merge-note 的两个上游技能 `engineering/diagnosing-bugs`、`engineering/research` 与 squash 提交完全相同（`git diff --stat` 为空，已核实），与「没 merge-note 就没改」一致。
- `check_upstream_em_dashes.py` 依据的「上游禁止 em-dash」规则在 `mmw-v2/upstream/AGENTS.md` 第 25 行（已核实）。

## 6. 价值证据

| 部件或段落 | 防的是什么失败 | 实地证据 |
| --- | --- | --- |
| `tool-guard.py` 关票闸门 | worker 手敲 `gh issue close` 或摘 `ready-for-agent`，票被关却没有收尾评论 | 提交 `f872c99f`（2026-08-29）给出设计理由，未点名具体事故；`cd3ae680`（2026-08-30）与 `runs()` docstring 记录一个 worker 在草稿正文里写「我没有直接关票」被误拦，说明闸门在真实运行中触发过；`38b932cc` 记录拒绝串被 Grok 截断出路。Memory「hook.py 作为工具调用前闸门的职责与生效条件」（2026-09-05）。未找到「worker 真的手动关票」的事故记录：无证据 |
| `tool-guard.py` 结束进程闸门 | 一个 run 杀掉邻居的应用 | 提交 `0beb2906` 正文：2026-09-05 五个 worker 共用三个端口，「one ended another's application to take its ports」；三个 worker 对同一条正确错误信息给出三种错答（`no_kill` docstring） |
| `tool-guard.py` 提问闸门 | 无人值守的会话弹出表单，没人回答，会话停住 | 提交 `563b5e3f`（2026-09-02）加入；未找到具体事故编号：无证据。另见 §9.3：cursor 与 pi 没有注册提问闸门 |
| `tool-guard.py` 的 `PASEO_AGENT_CWD` 回退 | Cursor 从 `~/.cursor` 跑 hook，闸门对所有命令放行 | `governed_ticket` docstring：2026-09-06 实测 cursor-agent 2026.08.25 |
| `turn-guard.py` | 主 agent 回合结束后无人再启动它，同时 watchdog 已死 | `guard.log`（只读统计）：`chancheuklap__multi-model-workflow` 77 行、1 次 `block`（2026-09-15T05:46:27Z，codex，watchdog 因 GitHub TLS 超时超过容差未读全 board）；`agentflow-hq__agentflow` 186 行、0 次 `block`。即至今在两个仓库里触发 263 次，真正拦住 1 次。ADR 0021 第一段与提交 `d7149255`（#317） |
| `install.sh` 残留摘除（`stale_links`、retired 目录） | 旧版软链与新版撞名，host 静默取旧版 | 头注释 83–85 行「ui-qa 从 skills.txt 拿掉之后八处软链留了一整天」；ADR 0006 实测 Grok 取 `~/.grok/skills` 那份 |
| `install.sh` Codex `trusted_hash` | 装了的 hook 在 Codex 里 Active 为 0 | 757–767 行：2026-08-29 实测，2026-09-10 用本机 16 条处理器核对算法；`turn-guard.py` 头 codex 0.153.4 行：移走 config.toml 后 hook 不运行 |
| `install.sh` Cursor MCP 去 `type` | worker 静默没有 memory 工具 | `install.sh` 1756–1761 行与 `CODING_STANDARDS.md` 描述症状；未找到事故编号：无证据（有症状描述，无记录的发生时间） |
| `install.sh --check` 交给 installed checkout | 改造工具箱的那夜用新脚本核对旧安装 | I5 working_well「冻结运行时跨夜不换版」：#424 夜 #431 在冻结运行时里经两次 tracker 失败后落地（已核实该条出处在 I5，原 issue 未重开核对：未核实） |
| `render.py` 哈希头 | 有人直接改生成文件，改动被下次渲染覆盖 | ADR 0007 否决状态文件的理由；未找到覆盖事故：无证据 |
| Grok `[compat.claude] agents` 检查 | 同一份提示词进上下文两次 | ADR 0007：2026-09-05 `grok inspect` 显示载入两次 |
| `shared.md` rule 12 现文 | 模型等待一个不存在的文件大小提醒 | 提交 `b1df3138`（2026-09-28）：`rule-at-moment.py` 从未注册，Codex/Pi/Grok 本就没有这个提醒 |
| `shared.md` 第 11 行 | 脚本起的会话把「问 owner」读成弹屏提问、把 rule 14 读成重新选型 | 提交 `0b6d47e3`（2026-09-23）描述为「removes the misreadings」；未找到具体夜的事故：无证据 |
| `shared.md` rule 14 | 自造已有的东西 | 提交 `05db60ec` 只说明来源（四个外部规则合并）；无事故证据 |
| `shared.md` rule 15 | 无理由跑全量测试 | Memory「MMW 四宿主默认禁止全仓全量测试」（2026-09-15）只记录决定；提交 `398644f9` 无正文；无事故证据 |
| `shared.md` rule 8 | 自创叫法让 owner 读不懂 | Memory「沟通须用源文件真名并先讲意图」：用户要求把 `turn-guard.py`、`watchdog.py` 用真名而非「回合结束检查」「看门进程」——证明规则在场但被违反过，不证明规则有效 |
| board `codeversion.py` 自重启 | 挪 installed checkout 后 board 仍跑旧代码到下次登录 | 提交 `af24f8cf`（2026-09-18）正文 |
| board `gates.py` | 本机其它网页跨站写 `models.json` | 设计理由（`board/AGENTS.md` Gotchas 第二条）；无事故证据 |
| board 整体 | 人早上看夜的状态 | I5 nights 表 #555「任务板界面」夜；M2 引 task-board `CONTEXT.md` `### What the page shows`。使用频率无记录：无证据 |
| `check_module_paths.py` | 改名漏改按路径加载的调用方 | I5-P9：#555 的 `tree.py` 改名漏改 `retro.py`，retro gather 停止；#587 加此检查（已核实 I5 条目，提交 `812a2141` 标 #587） |
| `check_own_skill_frontmatter.py` | description 含未加引号的冒号，严格 YAML 解析失败 | docstring：advisor 与 ui-acceptance 实际出过，修于 `d37a6048`（2026-09-23 复审） |
| `check_upstream_em_dashes.py` | 本仓在上游 subtree 里写入 em-dash | 提交 `0b00edcb`（2026-09-23 审计）；docstring 说明规则来源；无事故证据以外的记录 |
| `run_unittests.py` 的零跳过规则 | 半个套件通过读起来像全过 | ADR 0008 原则；`MMW_FORCE_SKIP=1` 自证；无事故编号 |
| `merge-notes/` | 下次拉上游把已删规则恢复回来 | 2026-09-23 汇总 `### 6. merge-note 与其他文档`：改写多份仍写着已被取代规则的条目（已核实该段原文） |
| `downstream-notes/` | 消费仓库的产物静默失效 | 19 份现行说明；2026-09-28 汇总第 73 行要求为 release 字段删除写一份（已核实）；读的一方没有机制送达：消费仓库是否读过无记录，无证据 |
| `CODING_STANDARDS.md`/`TESTING.md` 拆分 | 规则多处、reviewer 读不到 | 提交 `2cbd0279`（「One home per rule」）；2026-09-23 汇总 `## 八` 的「规则的唯一出处」（已核实）；汇总写明「没有让新 agent 按新文本跑过一张真实的票」 |
| `remove-verifier.py` | 旧 `verifier.*` 事件与 `models.json` 旧行在 verifier 取消后残留 | ADR 0026 第 14 行；一次性，执行记录未核实 |
| Self-hosting boundary（文字） | 正在跑的夜被它自己改的版本接管 | I5 working_well 同上；Memory「夜未收完时不要安装 mmw，只挪冻结工作树」；没有任何脚本拒绝从非 installed checkout 运行 `dispatch.sh`（grep dispatch 与 verify-ticket 脚本，只找到 `check` 里的 `installed-root` 比较） |

## 7. 约束

- ADR 0003：不打包成插件，由 `install.sh` 散装。现行读法见 0006 与 0015。
- ADR 0005：docs 层（ADR 编号、索引、`docs/agents/`）由 v2 手工维护，不调用冻结区。
- ADR 0006：技能只装 `~/.agents/skills` 与 `~/.claude/skills` 两处，各自直接指仓库；四个旧位置退役；两级软链被否决（会破坏 `install.sh` 的归属判断）。
- ADR 0007：提示词源在仓库；Claude 用软链，Codex/Pi/Grok 用 `render.py` 拼接；Grok 兼容开关必须关；Cursor 只能在 app 内手贴；否决「状态文件记账」而用首行哈希；否决「不装 launchd」。
- ADR 0014 `## Considered Options` 第二条：否决把 advisor 的 caller 侧规则写进用户级提示词，两个理由——`shared.md` 到不了 Cursor；「为一件偶尔发生的事付每回合的常驻 context」。这是对 `shared.md` 该放什么的现成约束。
- ADR 0015：不交付 subagent；六个 `agents/` 目录退役由 `install.sh` 清理；`models.py` 接管 `models.md` 的解析。
- ADR 0008（silence is never a pass）：`install.sh` 的 `没查`、`run_unittests.py` 的零跳过、`turn-guard.py` 对「没心跳」不当作「没占用」都受它约束。
- ADR 0021：turn guard 的三层判活设计、只守主 agent、各 host 能力表、Codex 信任。
- ADR 0024（未通读，只从 T4 线索与 `CODING_STANDARDS.md` 引用得知）：`models.json` 与 runner 扩展边界。
- 根 `AGENTS.md` `## Self-hosting boundary`：夜开着时不动 installed checkout、不跑 `install.sh`、不用新版本的脚本控制旧夜。
- 根 `AGENTS.md` `## Gotchas`：`install.sh` 只在用户明确授权时运行，`--check` 例外。与之并存的事实：`dispatch.sh check` 在本 checkout 即 installed checkout 时会自动跑完整 `install.sh` 修复（`## Commands` 同一表格里写明「repairs from the installed checkout」）。两句都在同一文件，未见说明二者关系的文字。
- `SKILL-SET-RULES.md` 事实 2「Scripts carry what is deterministic; text carries judgement」与 `### Scripts and judgement`「A rule a script could check exactly becomes a check … not a sentence」：hook 与三个 lint 属于此类落地。
- `SKILL-SET-RULES.md` `### Load and disclosure`「A rule sits in the text of the agent that must follow it … in a script's comment, in the glossary, in a merge-note … reaches no worker」：因此 hook 头注释里的理由到不了 worker，worker 读到的只有拒绝串与技能文字。
- `SKILL-SET-RULES.md` Sediment 表：日期实测的归宿是脚本头，维护者理由的归宿是 ADR——本单元的 `install.sh`、`turn-guard.py` 头注释正是按此放置。
- `SKILL-SET-RULES.md` `### Descriptions`：本仓自研技能 frontmatter 只有 `name` 与 `description`，由 `check_own_skill_frontmatter.py` 检查。
- `SKILL-SET-RULES.md` 事实 7：「this is why MMW ships no router skill, since every description is already in the agent's runtime」——对「mode 入口与路由」有直接约束（原文已核实）。
- `TESTING.md` `## What a test proves`：测试不钉文字。
- 记录在案的用户决定：提交 `0b6d47e3`——worker/reviewer 无法另配一份 host 提示词（要搬各 host 的凭据目录；claude 的 `--bare`/`--setting-sources` 会连 MMW hook 一起丢），所以 `shared.md` 对它们照常载入，用第 11 行改读。Memory「MMW 四宿主默认禁止全仓全量测试」记录 rule 15 是 owner 的决定。
- 2026-09-06 handoff（`docs/research/mmw-structure/2026-09-06-handoff.md`）里 advisor 建议新增 `mmw-v2/runtime/` 交付面，把 hook 等「不属于任何时刻」的东西从技能下搬走；现状核对：`mmw-v2/runtime/` 不存在，两个 hook 仍在 `mmw-v2/skills/dispatch/scripts/`（`tool-guard.py` 的历史是 `verify-ticket/scripts/hook.py` → `drive-target/scripts/hook.py` → 现址，`git log --follow` 已核实）。这是未执行的建议，不是决定。

## 8. 天然整体

- `install.sh` 的「装」与「`--check`」：同一段代码的两个模式，每一段都同时定义「怎么装」与「怎么认出装齐了/残留」（例如 `grouped()` 返回 `install`、`installed` 一对）。拆开等于两份归属判据要保持一致。
- 技能软链、retired 目录清理、hook 残留清理共用一个归属判据（命令或软链目标落在本仓库 source directory 下，`ours_skill_target`、`MARK`）。注释 585–593 行明说「与软链那边同构」。拆开后判据会漂移。
- `render.py` + `shared.md`/`hosts/*.md` + launchd 任务 + `install.sh` 提示词段：同一条发布路径；首行哈希只有 `render.py` 写、只有 `render.py` 认。
- `tool-guard.py` 的两个闸门共用受管判定 `governed_ticket()`（提交 `5265254a`：「the question gate governs every session in a ticket worktree」）与按 host 的输出形状 `refuse()`。三件拒绝在同一个 PreToolUse 调用里判定，拆成多个 hook 意味着每个 host 多注册几条、多几次进程启动（推断）。
- `turn-guard.py` 与 `watchdog.py`、`relay.py` 的 `read_watches`/`main_of`、`statedir.py`：turn guard 直接加载 `watchdog.py` 并用它的 `read_health`、`arm`、`night_open`（ADR 0021 定义三层为一个设计）。turn guard 单独存在没有意义。
- hook 脚本与 `install.sh` hook 段：hook 的调用形状（`pretool <host>`、`stop <host>`）、超时、Grok 前缀、Cursor `loop_limit`、Pi 扩展文本都写在 `install.sh` 里；改一边必须改另一边，liveness 与 dispatch 套件同时测两边。
- board 的 `supervisor.py` + `server.py` + `codeversion.py` + LaunchAgent：守护、服务、自重启是一个运行单元；`codeversion.LOADED` 把 board 与它加载的五个技能脚本绑成一个版本单位。
- `refusal.py` 与所有拒绝串：拒绝格式的唯一实现，被 `tool-guard.py`、`remove-verifier.py`、ui-acceptance 脚本共用（位置在 ui-acceptance 技能下，`tool-guard.py` 第 57–62 行跨技能加载）。
- `shared.md` 本身：五条读者事实是后面 15 条规则的理由（第 1 行「Five facts about that reader drive every rule below」），拆开会失去理由。第 11 行依赖 rule 14 的原文。
- merge-note 与它所说明的上游技能：一对一，README 规定每份只写该技能改了哪几段。
- `CODING_STANDARDS.md`/`TESTING.md` 与 code-review 的两个 axis：文件名是 axis reference 里写死的读取对象，拆分或改名要同时改 `standards-reviewer.md`、`tests-reviewer.md` 与 `manage-agents-md`。

## 9. 重点问题的事实依据

### 9.1 这些非技能部件各自是什么（候选归类，只列证据，不做决定）

| 部件 | 它现在做的事（事实） | 可对应的新架构层（候选） | 依据 |
| --- | --- | --- | --- |
| `shared.md` | 所有项目、所有会话常驻；规则面向 owner，第 11 行改读给无人会话 | 宿主级提示（host-level prompt），不是 MMW 的 mode 常驻规则 | 它是 owner 的全局提示（本会话系统提示把 `~/.claude/CLAUDE.md` 标为「global instructions for all projects」）；MMW 专有词只在 4 处；Cursor 不载入 |
| `hosts/codex.md` | Codex 一句 | 宿主级提示 | ADR 0007 |
| `render.py`、launchd、`install.sh` 全体 | 把技能、hook、提示词、外部工具配置装到本机 | 安装机制 | `install.sh` 头注释 |
| `skills.txt` | 发布名单 | 安装机制的配置；`SKILL-SET-RULES.md` 定义 skill set 的范围 | 第 3 行 |
| `models.json` 一行 | 角色 → host/model/effort | 「角色 = playbook + models.json 一行」里的那一行 | `models.py` `ALLOWED_AGENTS`；`editing-models.md` |
| `models.py config` | 唯一写入口 | lever | `CODING_STANDARDS.md` 第 14 行 |
| `tool-guard.py` | 在 host 层拒绝三类命令 | lever（强制型），其规则文字属原则/做法层 | §9.3 |
| `turn-guard.py` | 在 host 层维持主 agent 回合、拉起 watchdog | lever（夜的运行机制），与 watchdog/relay 同层 | ADR 0021 |
| board | 人看夜的状态、改模型配置 | 独立产品/工具（非技能），读流水线事件；settings 页是 `models.py` 的另一个写入口 | `board/AGENTS.md` 首段 |
| `migrations/` | 一次性状态迁移 | lever（一次性） | ADR 0026 |
| `tests/`、`tests/lib/` | 测试与三个共用 lint | 仓库开发设施；lint 是「规则变检查」的落地 | `SKILL-SET-RULES.md` `### Scripts and judgement` |
| 根 `AGENTS.md`、`board/AGENTS.md`、`tests/AGENTS.md` | 在本仓工作的 agent 的常驻导航与约定 | 仓库文档（本仓作为被改造的产品）；不是 MMW 的 mode | 根 `AGENTS.md`「The skills in this repository are deliverables, not the working instructions of an agent working on it」 |
| `CODING_STANDARDS.md`、`TESTING.md` | 本仓的代码与测试规则，由 review axis 读 | 仓库文档（消费仓库也各有一份，由 `manage-agents-md` 生成） | `manage-agents-md/SKILL.md` 第 208 行 |
| merge-notes、downstream-notes | 维护记录 | 仓库文档（决定类，允许有历史） | `shared.md` rule 13 例外 |

### 9.2 `shared.md` 与未来 mode 常驻规则的分工：现有事实

1. 覆盖面：`shared.md` 在 Claude、Codex、Pi、Grok 的每一个会话里载入，不分项目、不分角色；Cursor 不载入（ADR 0007；`prompt/README.md` 第 17 行）。本机 `models.json` 现在四个角色都落在 grok/codex/claude，所以派出的会话全部载入它。
2. 无法按会话关掉：提交 `0b6d47e3` 写明，给脚本起的会话另配提示词需要搬各 host 的凭据目录，claude 的 `--bare`/`--setting-sources` 会连 MMW hook 一起丢，所以选择「规则照常载入，加第 11 行改读」。
3. 读者设定：全文以 owner 为读者（第 1 行）。对无人会话，它把三件事改路由到「skills」：提问去技能的提问途径、汇报用技能的格式、rule 14 的既定项目读作票的方案（第 11 行）。也就是说它已经假定存在一个比它更具体的层来承接「怎么问、怎么报、按什么做」。
4. ADR 0014 已否决把偶发场景的规则写进用户级提示词（每回合常驻成本 + 到不了 Cursor）。
5. pstack 对照（只作事实）：`docs/research/code-landing-refs/pstack/skills/poteto-mode/SKILL.md` frontmatter 为 `disable-model-invocation: true`、`mode: true`、`reminder: New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't.`；其 `## Autonomy`（Just do it / Always pause / No is an acceptable answer）与 `## Writing the reply`（每个结论带证据或标签、影响先讲给使用者）在内容上与 `shared.md` rule 1–5 有重叠。区别是 pstack 把它们放在按对话启用的 mode 里，MMW 放在所有会话常驻的宿主级提示里。pstack 的 `plugin.json` 只声明 `skills` 与 `agents`，没有 hook（已核实）。
6. `shared.md` 的规则类型分布（§2.1）：几乎全部是「带理由的规则」，没有步骤顺序、没有命令、没有流水线事件。rule 14、15 与第 11 行是仅有的直接影响派工行为的条款。
7. 冲突面：rule 2「An approved plan or ticket … is the go signal」与 rule 1「When you reach one of those, … then ask」对无人会话由第 11 行改读；`tool-guard.py` 的提问闸门在 claude/grok/codex 上把「ask」在机械层面拦下，改道到 `implement` 给的两条出路。

### 9.3 hook 强制的规则与文字规则的关系

| 规则 | hook 强制（哪个 host） | worker 读到的文字 | 规则理由所在 |
| --- | --- | --- | --- |
| 不手动关票、不摘 `ready-for-agent`、不加 `needs-triage`/`ready-for-human` | `tool-guard.py pretool`：claude、codex、grok（JSON 注册），cursor（`beforeShellExecution`），pi（扩展，只拦 `bash` 工具） | `implement/SKILL.md` 第 99 行 step 8；拒绝串 `REFUSAL` | `tool-guard.py` 头 5–8、28–31 行；提交 `f872c99f` |
| 不结束进程（`kill`/`pkill`/`killall`/`killall5`/`xargs … kill`） | 同上 | `ui-acceptance/SKILL.md` `## Five rules while the product is running` rule 1；拒绝串 `no_kill()` | `tool-guard.py` 头 15–20 行；提交 `0beb2906` |
| 不弹屏提问 | `tool-guard.py question`：只在 claude（`AskUserQuestion`）、grok（`ask_user_question`）、codex（`request_user_input`）注册（`install.sh` 第 455 行）；`tool-guard.py` 自己的 `QUESTION_TOOLS` 还列了 cursor `AskQuestion` 与 pi `ask_user_question`，但没有注册点调用它们 | `implement/SKILL.md` 第 23 行；`shared.md` 第 11 行；拒绝串 `NO_QUESTION` | `tool-guard.py` 头 10–13 行；提交 `563b5e3f` |
| 主 agent 在有票被占而 watchdog 不健康时不得结束回合 | `turn-guard.py stop`：claude/codex/grok 真拦（exit 2），pi 与 cursor 只能塞一条 follow-up | 没有对应的技能文字要求「别结束回合」；主 agent 只在被拦时读到 `MMW turn guard:` 消息，`night.md` 第 19 行把它路由到第 3 节 | `turn-guard.py` 头；ADR 0021 |

事实归纳：

- 被强制的三条都有文字对应物，而且文字写在执行者的技能里（`implement`、`ui-acceptance`），符合 `SKILL-SET-RULES.md`「A rule sits in the text of the agent that must follow it」。文字还明说有 hook（`implement` 第 99 行「a hook blocks the command」、`ui-acceptance` rule 1「Your shell refuses …」）。
- hook 只是「拒绝」，不做检查（`tool-guard.py` 头 28–31 行）；出路由拒绝串给出，与技能文字一致。拒绝串属于 `SKILL-SET-RULES.md` 所说「counting a script's `--help`, its refusal text」的一份副本，即同一规则在技能文字与拒绝串里各一份。
- 管辖范围只按工作目录名 `issue-<n>` 判断；orchestrator、人工会话、ticket 工作树外的任何会话都不受 `tool-guard.py` 约束。`turn-guard.py` 反过来只管主 agent。
- 覆盖缺口：cursor 与 pi 上没有提问闸门，文字是唯一约束（本机当前角色没有落在这两个 host，推断当前不可达）；pi 的命令闸门只拦 `bash` 工具。
- hook 的理由写在脚本头和 ADR 里，worker 读不到；按 `SKILL-SET-RULES.md` 这是允许的，因为 worker 需要的规则句已在技能里。

## 10. 线索材料核实表

| 采用的线索 | 出处 | 结果 |
| --- | --- | --- |
| T4 `skill_install`：技能软链改编自 mattpocock `scripts/link-skills.sh#DESTS` | `T4-toolbox.json` | 已核实（squash `5b1a4c51` 原文） |
| T4 `installer`、`frozen_install`、`adapter_uses`、`models`、`board` 标为 MMW 原创 | `T4-toolbox.json` | 未核实其搜索范围；本轮没有重复外部搜索 |
| T4 `host_hooks`：阻断策略由 MMW 自己实现，依赖宿主事件；Codex `trusted_hash` 依赖 codex-rs | `T4-toolbox.json` | 部分核实：`install.sh` 757–767 行原文一致；codex-rs 源码未打开 |
| C5 边 `command:install.sh#install -> config:skills.txt : writes` | `C5-toolbox.json` edges 第 1 条 | 与原文不符：`install.sh` 读 `skills.txt`（143–157 行），不写 |
| I5-P9：模块改名漏改导致 retro 停止，#587 加检查 | `I5-mmw-field-evidence.json` | 已核实到 `check_module_paths.py` 与提交 `812a2141` 标 #587；#555 retro Memory 原文未打开 |
| I5 working_well「冻结运行时跨夜不换版」 | 同上 | 条目存在已核实；#424/#431 原 issue 未打开，未核实 |
| 2026-09-23 汇总：规则唯一出处拆到 `CODING_STANDARDS.md`/`TESTING.md`；新文本未经真实票验证 | `docs/reviews/2026-09-23-skill-set/汇总.md` `## 八` | 已核实原文；与提交 `2cbd0279` 一致 |
| 2026-09-23 汇总：merge-note 过时条目会在下次拉上游恢复旧规则 | 同上 `### 6.` | 已核实原文 |
| 2026-09-06 handoff：建议 `mmw-v2/runtime/`，hook 不属于任何时刻 | `docs/research/mmw-structure/2026-09-06-handoff.md` 第 78–120 行 | 已核实原文；已核实该建议未执行 |
| M2：turn guard 在 watchdog 不健康时挡住主 agent 回合 | `M2-mmw-night.md` 第 89、115 行 | 已核实（`turn-guard.py` 原文） |
| G1：pstack plugin 无 hook | `G1-pstack-core-terms.md` 第 101 行 | 已核实（`plugin.json` 原文） |
| 2026-09-28 汇总第 73 行：release 字段删除需写 downstream-note | `docs/reviews/2026-09-28-lightweight/汇总.md` | 已核实原文；对应 `release-self-heal-removed.md` 已在索引里 |

`docs/reviews/2026-09-29-vocabulary-recheck/` 只 grep 到 `DECISIONS.md`、`VERIFY-BRIEF.md`、`APPLY-BRIEF.md` 中出现本单元文件名，未逐份读，没有采用其中结论。

## 11. 未确定

- `install.sh` 460–580、800–895、1110–1230、1300–1400、1420–1600 行的实现体未逐行读；有关这些段落行为的描述来自注释，属推断。
- `remove-verifier.py` 是否已在本机执行过：`models.json` 无 verifier 行，但也可能从未有过，未核实。
- `tool-guard.py` 关票闸门与提问闸门是否在真实夜里拦下过真实的违规（而不是误拦）：没有找到日志或事故记录；hook 不写日志（`tool-guard.py` 无写文件代码），所以这一点目前无从统计。
- `downstream-notes` 是否被任何消费仓库读过、是否在 agentflow/xiaohuangya 执行过迁移：本仓无记录。
- board 被人实际使用的频率：无记录。
- `shared.md` 各条规则的实际效果：只有 rule 8 有一条「在场但被违反」的 Memory，其余无运行证据。
- ADR 0024 未通读；关于 `models.json` 与 runner 边界的约束只来自 `CODING_STANDARDS.md` 与 T4 的转述。
- Cursor 上用户级提示词的现状（app 内手贴的内容是否与 `shared.md` 一致）：无法从仓库读到。
- `tool-guard.py` `QUESTION_TOOLS` 里 cursor 与 pi 两项没有注册点，是有意留着还是遗漏，仓库里没有说明。
