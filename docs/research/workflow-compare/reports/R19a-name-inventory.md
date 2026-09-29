# R19a MMW 命名清点（升级后 MMW 自有的全部名字）

本文给下一步写改名表（`R19-naming-table.md`，R18 第 17 节 D9）的人或 agent 用：升级后 MMW 自有的每个名字现在是什么、谁读它、在仓库里出现多少次、对人与 agent 是否清楚。本文只清点与判断，不提新名字。上游 mattpocock 与 pstack 的名字不改（R18 第 17 节 D9），这里只作对照列在第 16 节；分叉进来的 `to-spec`、`to-tickets` 列出，但注明是上游概念名。

## 0. 结论

1. **清点范围**：各表共 317 行，一行是一个名字或一组同类名字（例：`runners/orca.sh`、`paseo.sh`、`herdr.sh` 一行）；`slots.md`、`anchors.py`、`mmw-hook`、`--tools`、`models.json` 在两节各出现一次。判断：清楚 198 行、含糊 104 行、误导 15 行，分节统计在第 0.1 节。
2. **最大的问题是一词多义（第 15.1 节，19 组）**。最严重的四组：
   - `mmw` 同时指整套工具、仓库目录 `mmw-v2/`、消费仓库配置目录 `.mmw/`、label 前缀 `mmw:`、事件标记 `<!-- mmw {…} -->`（`events.py` 第 67 行 `MARK = "mmw"`），R18 再让它指 mode 技能、hook 启动器 `mmw-hook`、步骤指针前缀 `mmw <slug>#`、测试套件 `tests/mmw`。pstack 的 mode 叫 `poteto-mode`，名字里带组件类型。
   - 「slot」：产品槽位（`ui-acceptance/scripts/lease.py` 第 124 行「every slot file」、事件 `worker.queued`）与 R18 新建的 `slots.md`（pstack 名字的对应表）。R18 自己把两者都写成「槽位」（第 4.1 节「产品槽排队」、第 1.1 节 `slots.md`「槽位、别名与宿主工具映射」）。
   - 「check」有十种用法：`dispatch.sh check`、`install.sh --check`、`target_config.py --check`、票里的 `CHECK:` 行、事件 `ticket.checked`、`.mmw/target.json` 的 `checks` 键、`--check-only`、R18 新定的 `ticket.py --check`、技能 `code-checkers`、`check_wiring.py`。
   - 「effort」：`models.json` 的推理强度 `effort`、目录 `docs/specs/<effort>/`、playbook `map-a-large-effort`。
3. **同一个东西有几个名字（第 15.2 节，13 组）**。例：「角色」在 `roles.json` 叫 role、在 `models.py` 叫 agent（`ALLOWED_AGENTS`）、在 `models.json` 叫 row、在 R18 第 2.2 节叫 label（`models.py config get <label>`）；「子票」在事件里叫 child（`child.opened`、`mmw:child`），在开关与 reference 里叫 sub-issue（`--sub-issue`、`sub-issues.md`）；出包配置在 `exe-release` 里同时叫 key、release manifest、adapter（`references/key.md` 第 1–5 行）。
4. **名字让读者得出错的结论的，判为「误导」共 15 行、14 个名字**（`slots.md` 两节各计一次）。例：`dispatch.sh wait` 什么也不等（`dispatch.sh` 第 2284–2290 行注释「It waits for nothing」）；`--preflight` 不是只读预检，它认领票并写 `ticket.claimed`（`verify-ticket.py` 第 4143 行 help）；`spec.opened` 记的是一夜开始，不是 GitHub 上开了一个 spec；`edit-pages.md` 讲的是建项目与记签字，不是改页面；`fix_dispatch.py` 与 `dispatch` 技能毫无关系。
5. **写法不统一**：Python 文件 9 个用连字符、22 个用下划线（连字符的文件不能 `import`，只能按路径加载，`mmw-v2/tests/AGENTS.md` `## Key Conventions` 第 3 条「`verify-ticket.py` is no identifier」）；MMW 自有原则 12 条里只有 2 条是 pstack 式祈使句；MMW 自写 playbook slug 16 个里 14 个带冠词（`define-a-change`），pstack 23 个里只有 2 个带；MMW 加进上游目录的文件一半全大写（`SKILL-SET-RULES.md`），一半小写放进 `references/`。
6. **改名的代价按「谁读」分三档（第 15.4 节）**。只有人与 agent 读的（reference、playbook、原则、mode 节名）改名只动文字；程序按字面读、但只在本机的（脚本、状态文件、`roles.json`）改名要一起改调用点与测试；存在外部、长期保存的（事件名写在 GitHub 评论里并被每次 fold 重放、label 贴在各仓库的 issue 上、`.mmw/target.json` 的键与 `delivery` 值在消费仓库里）改名要迁移或别名表。`SKILL-SET-RULES.md` `### Vocabulary` 第 3 条：程序、tracker 或消费仓库读的名字「is copied verbatim and is not renamed for style」。

### 0.1 判断统计

| 类别（表行数） | 清楚 | 含糊 | 误导 |
|---|---|---|---|
| 技能名（第 2 节）（15） | 9 | 6 | 0 |
| reference（第 3 节）（43） | 25 | 14 | 4 |
| 脚本文件名（第 4 节）（41） | 21 | 19 | 1 |
| `dispatch.sh` 子命令与参数值（第 5.1 节）（30） | 18 | 10 | 2 |
| `verify-ticket.py` / `ticket.py` 开关（第 5.2 节）（19） | 11 | 7 | 1 |
| 其他脚本的子命令（第 5.3 节）（8） | 7 | 1 | 0 |
| playbook slug 与步骤名（第 6 节）（31） | 22 | 9 | 0 |
| 原则 slug（第 7 节）（12） | 8 | 4 | 0 |
| mode 节名与骨架标记（第 8 节）（16） | 14 | 2 | 0 |
| 配置文件与登记值（第 9 节）（26） | 14 | 10 | 2 |
| 事件名与字段值（第 10 节）（29） | 18 | 7 | 4 |
| tracker label（第 11 节）（3） | 3 | 0 | 0 |
| 状态目录与文件（第 12 节）（22） | 12 | 10 | 0 |
| `board/`（第 13 节）（11） | 8 | 3 | 0 |
| `tests/` 套件（第 14 节）（11） | 8 | 2 | 1 |
| 合计（317） | 198 | 104 | 15 |

（按本文各表的「判断」列逐行计得；第 5.3 节按每行判断的第一个词计。「新（R18）」的名字按它在 R18 里的含义判断。）

## 1. 方法

- **出现次数**：`rg --pcre2 --count-matches -e '<模式>' mmw-v2 docs AGENTS.md`，在仓库根运行（本轮，2026-09-29，工作树含未提交的研究报告）。「总」＝这三处全部；「现役」＝同样三处去掉 `docs/research/`（研究报告与 `code-landing-refs/` 下的第三方快照）。`rg` 按 `.gitignore` 跳过 `__pycache__/`、`.worktrees/`，并跳过隐藏目录（根 `.mmw/` 不计）。
- **模式**：默认是名字本身，前后不接字母、数字、`_`、`-`（`(?<![A-Za-z0-9_-])名字(?![A-Za-z0-9_-])`），所以 `verify-ticket` 的计数含 `verify-ticket.py` 与 `tests/verify-ticket`，技能名的计数都含同名脚本与测试目录。例外：`dispatch.sh` 子命令按 `dispatch.sh <子命令>` 计（正文里单写 `advance` 的不计）；`mmw`、`dispatch`、`retro`、`advisor` 这类常用词按「作为技能被提到」的形式计（`` `mmw` ``、`skills/mmw/`、`mmw skill`、`mmw/scripts` 等）；mode 节名按带 `#` 的整行文字计；事件名前后不接字母数字。计数是匹配次数，不是文件数。
- **新名字**：R18 新定、仓库里还没有的名字标「新（R18）」，它的「现役」次数是 0，「总」次数几乎全来自 R15–R18 等研究报告。
- **谁读**：「人」＝用户或维护者读文档与任务板；「agent」＝读技能文字、启动提示词、唤醒行、拒绝文字的会话；「程序」写出是哪个程序，「字面」＝程序源码里写着这个字符串，「锚点」＝R18 第 7.1、7.2 节之后改由 `roles.json` 或 `anchors.py` 登记、程序从那里取。
- **判断**：「清楚」＝只看名字能说对它是什么；「含糊」＝名字说不出它做什么、或与别的名字撞义、或是没定义过的自造词；「误导」＝名字让读者得出错的结论（做的事与名字相反，或名字指向另一个已有的概念）。理由写在同一行。

## 2. 技能名

| 现名 | 是什么（出处） | 谁读 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `mmw` | 新（R18）：mode 技能，任务路由、原则索引、无人时能定什么、重入（R18 第 2 节） | agent：启动提示词「Use the mmw skill」、`/mmw`；程序：`dispatch.sh` 启动提示词、唤醒指针前缀（锚点，R18 第 7.8 节）、`check_own_skill_frontmatter.py` | 847/2 | 含糊 | 同一个词已指整套工具（`MMW` 2814/463 次）、`.mmw/`（1008/470）、`mmw:` label、事件标记；「读 mmw」说不清是读技能还是读工具。pstack 的 mode 名是 `<品牌>-mode`（`poteto-mode`） |
| `setup-mmw` | 新（R18）：改角色的 host、model、effort、runner，查一个角色的值，读 `install.sh --check`，开任务板（R18 第 4.1 节） | agent（路由表直接行）；人（`/setup-mmw`） | 53/0 | 含糊 | 「setup」让人以为是首次安装；真正的安装是 `install.sh`，给仓库接入是 playbook `onboard-a-repository`，三者都像「设置」。开任务板不是设置 |
| `shared-experience` | 新（R18）：Nowledge Mem 里 Memory 记录的开、搜、存、改、关（R18 第 4.1 节） | agent（P12、P15 点名） | 52/1 | 含糊 | 名字取自 `implement` 的小节 `## Shared experience while implementing`（R18 第 1.3 节）；「experience」说不出 Memory。同一件事的其他名字都用 memory：`saving-memory.md`、`dispatch.sh memory-list`、`--memory-decisions` |
| `to-spec` | 分叉：把对话写成 spec 并发布（上游概念名） | agent、人（`/to-spec`）；程序：`install.sh` 按 `skills.txt` 查重 | 1533/359 | 清楚 | mattpocock 的 `to-<产物>` 句式；计数含上游同名目录 |
| `to-tickets` | 分叉：把 spec 切成票（上游概念名） | 同上 | 2478/439 | 清楚 | 同上 |
| `verify-ticket` | 升级后：跑一张票的判据、lint 票面、发布 spec 与票、`issue_tree.py`（R18 第 4.1 节） | agent；程序：`dispatch.sh` 按路径找 `verify-ticket.py`（第 4616 行）、`board_data.py` 按路径加载同目录脚本 | 3665/717 | 含糊 | 升级后它还发布 spec（`--publish --spec-body`）、lint 一整批草稿，名字只说「核对一张票」 |
| `ui-acceptance` | 界面验收：四个 oracle、产品答案、租约 | agent；程序：`verify-ticket.py` 把它的 `scripts/` 放上 `PATH`（第 4171–4175 行）、`tool-guard.py` 第 57 行按目录名找 | 1736/519 | 清楚 | 验收测试是通用术语 |
| `design-pages` | 在 Claude Design 与仓库之间搬设计 | agent、人 | 930/191 | 清楚 | — |
| `write-screen-contract` | 写 `docs/specs/<effort>/screen-contract.yaml` | agent、人 | 580/167 | 清楚 | 动词加宾语，与上游 `to-spec` 同类 |
| `exe-release` | 按当前分支出官方安装包 | agent、人（「ship」「package」） | 459/159 | 清楚 | 「exe」限定 Windows 可执行文件，现有模板只有 `release_templates/nuitka_electron.ps1.tmpl`，与内容相符 |
| `code-checkers` | 给仓库装 linter、formatter、类型检查与 git hook | agent、人 | 250/57 | 清楚 | — |
| `manage-agents-md` | 按固定格式建或重写 `AGENTS.md`、`CLAUDE.md` | agent、人 | 346/102 | 清楚 | — |
| `retro` | 复盘一个已完成的 spec 夜 | agent（P12 **Retro**）；程序：`retro.py` 写 `spec.retroed` | 509/113 | 含糊 | 名字不说对象是一夜；上游 mattpocock 另有同名技能 `skills/in-progress/retro/`（squash `5b1a4c51` 的目录树，`SKILL-SET-RULES.md` 第 169 行引它），pstack 的 `reflect` 复盘一个会话，两者会并列在路由表（R18 第 3.1 节） |
| `advisor` | 另起会话的第二意见 | agent；程序：`dispatch.sh advise` 启动提示词「Use the advisor skill.」（第 2049–2052 行注释） | 257/34 | 清楚 | 与角色名、`models.json` 行名一致 |
| `dispatch`（解散） | 现有：六个时刻的入口（`dispatch/SKILL.md` `## Find your moment`） | agent；程序：hook 路径 `~/.agents/skills/dispatch/scripts/*`（R18 第 7.3 节）、`board/` 四处路径 | 3474/328 | 含糊 | 六个时刻里只有「起会话」是 dispatch；解散后名字留在 `dispatch.sh`（第 5.1 节） |
| `implement`、`code-review` 等回原文的上游技能 | 上游名，不在本表判断 | — | — | — | 见第 16 节 |

## 3. reference 文件名

按所属技能分组。「新（R18）」的位置取自 R18 第 1.1 节目录树。

| 现名（所在处） | 是什么（出处） | 谁读 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `slots.md`（`mmw/references/`，新） | pstack 里的 Cursor 名字、槽位、别名在 MMW 读作什么（R18 第 8.3 节） | agent；程序：`import_component.py` 扫关键词逐个对它（R18 第 8.5 节）、`check_wiring.py` 第 2 类 | 60/0 | 误导 | 「slot」已指产品槽位（`lease.py` 第 124 行、`worker.queued`）；R18 中文两处都叫「槽位」。处理产品槽排队的 agent 会被指到这份文件 |
| `subagent-brief.md`（`mmw/references/`，新） | 派子代理的简报模板 | agent | 10/0 | 清楚 | — |
| `orchestrator-events.md`（`mmw/references/`，新） | P12、P14 共用的唤醒处理表 | agent；程序：`roles.json` 的 `*` 唤醒（R18 第 7.1 节）、`check_wiring.py` 第 6 类 | 20/0 | 含糊 | 表里还有八种 `watchdog:` 告警、`MMW turn guard:` 行、`resume` 退出码（R18 第 3.3 节 P12），都不是 `events.py` 的事件 |
| `writing-code.md`（`mmw/references/`，新） | P5、P15 共用的写码规则 | agent | 19/0 | 清楚 | — |
| `skill-set-rules.md`（`mmw/references/`，新；现为 `writing-for-agents/SKILL-SET-RULES.md`） | 技能集的写作与评审规则 | agent、人（根 `AGENTS.md` `## External References`） | 14/0（现名 357/90） | 清楚 | — |
| `reviewing-a-skill-set.md`（同上；现为 `REVIEWING-A-SKILL-SET.md`） | 走一遍技能集、报告并修 | agent | 3/0（现名 74/35） | 清楚 | — |
| `interface-and-remake.md`（`mmw/references/`；现在 `wayfinder/references/`） | 地图终点有界面或要翻新已有产品时的两类票 | agent（P2） | 110/31 | 含糊 | 「remake」不是常用词；文件标题是「Tickets for an interface or a remake」，名字漏了「票」 |
| `pipeline-issues.md`（`mmw/references/`；现在 `triage/references/`） | 流水线自己交回 `needs-triage` 的 issue 怎么处理 | agent（P13） | 158/53 | 清楚 | — |
| `tracker-additions.md`（`mmw/references/`，新） | MMW 加进 `docs/agents/issue-tracker.md` 的段落（三组 label 等，R18 第 3.3 节 P9） | agent（P9） | 5/0 | 含糊 | 名字说来历（「加的东西」），不说内容 |
| `review-axes/{standards,spec,tests,ui}.md`（`mmw/references/`，新；现为 `code-review/references/<axis>-reviewer.md`） | 四个评审 axis 的自足简报 | agent（axis 子代理）；程序：`dispatch.sh` 数据文件给绝对路径（R18 第 3.3 节 P16） | 24/0（现名 101/46、159/77、98/31、111/32） | 清楚 | R18 去掉了 `-reviewer` 后缀；pstack 的同类文件保留 `<角色>-reviewer.md`（`reflect/references/judgment-reviewer.md`） |
| `session.md`（`code-review/references/`，并入 P16） | reviewer 的整套流程 | agent；程序：`dispatch.sh` 第 1747–1751 行 Rules 包按字面点名 | 460/133 | 含糊 | 「session」是全仓最常用的词之一，说不出是评审流程 |
| `advising.md`（`advisor/references/`） | 被咨询一方怎样回答 | agent（advisor 会话）；程序：`roles.json` `brief`（R18 第 7.1 节） | 113/30 | 清楚 | 与 `consulting.md` 成对，一个是被问方，一个是提问方 |
| `consulting.md`（`advisor/references/`） | 提问方怎样写 brief、怎样对待回答 | agent；程序：`dispatch.sh` 第 2057 行拒绝文字按字面点名 | 135/41 | 清楚 | 同上 |
| `git-hooks.md`、`python.md`、`typescript.md`（`code-checkers/references/`） | commit 时跑检查器；两种语言的检查器配置 | agent | 52/30、32/23、18/9 | 清楚 | 三个都说出了对象 |
| `design-system.md`（`design-pages/references/`） | 在 Claude Design 里建设计系统 | agent（路由表直接行） | 131/46 | 清楚 | — |
| `draw.md`（`design-pages/references/`） | 标题「draw — act on comments, draw when asked」 | agent（P3 **Act on queued comments**） | 51/14 | 含糊 | 主体是处理排队的评论，名字只说画 |
| `edit-pages.md`（`design-pages/references/`） | 标题「edit pages — set up the project, record sign-off」 | agent（P3 第 1 步） | 188/59 | 误导 | 内容是建 Claude Design 项目与记录签字；改页面在 `draw.md` |
| `pull.md`（`design-pages/references/`） | 把签字的项目拉进仓库 | agent；`contract` 子票正文按字面点名（`pull.md` 第 3 行） | 292/78 | 清楚 | — |
| `template-design-system-claude-md.md`、`template-project-claude-md.md`（`design-pages/references/`） | 写进 Claude Design 项目的 `CLAUDE.md` 模板 | agent | 29/22、59/39 | 清楚 | 长，但说全了 |
| `state-list-format.md`（`design-pages/references/`，新；现为 `prototype/UI.md` 第 6 步） | 状态清单的格式 | agent；程序：`pull_design.py` 第 983 行按字面读 `## State list` 标题 | 43/0 | 清楚 | 与 `screen-contract-format.md`、上游 `*-FORMAT.md` 同一句式 |
| `driving.md`（`exe-release/references/`） | 标题「Drive one product」：按出包引擎的状态推进一个产品 | agent；程序：`release-flow.sh` 第 1338 行、`fix_dispatch.py` 第 4 行注释 | 150/85 | 含糊 | 「driving」是比喻，不说是出包循环 |
| `key.md`（`exe-release/references/`） | 标题「Write a release manifest」：写 `<product>.release-adapter.json` | agent | 139/91 | 误导 | 同一个文件在正文叫 release manifest、在文件名与 `--adapter` 开关叫 adapter（`key.md` 第 3–5 行）、在 `verify_key.py` 叫「钥匙」；在出包语境里「key」先让人想到签名密钥 |
| `new-product.md`（`exe-release/references/`） | 把一个产品接进出包系统 | agent | 64/25 | 清楚 | — |
| `create.md`、`rewrite.md`（`manage-agents-md/references/`） | 新建与重写两种情形 | agent；程序：`check.sh` 第 46 行点名 `rewrite.md` | 24/11、46/25 | 清楚 | 放在技能目录里时清楚；离开目录就说不出对象 |
| `boundary-check.md`（`ui-acceptance/references/`） | 一个控件的点击是否产生它那一行写的行为 | agent；程序：`boundary-check.py` 第 16 行 | 93/51 | 含糊 | 「boundary」指界面与后端的边界，名字本身不说 |
| `harness-guard.md`（`ui-acceptance/references/`） | 仓库为可驱动而加的名字是否只留在允许的地方 | agent | 44/25 | 含糊 | 「harness」是 MMW 对消费仓库 `.mmw/harness/` 的叫法，「guard」不说守什么 |
| `journey.md`（`ui-acceptance/references/`） | 一条端到端路径在真产品上是否还通 | agent；程序：`journey.py` 第 228、235 行拒绝文字 | 89/46 | 清楚 | user journey 是通用术语 |
| `product-answers.md`（`ui-acceptance/references/`） | `.mmw/` 里每个产品答案字段必须保证什么 | agent；程序：`target_config.py` 第 91 行 | 108/65 | 含糊 | 自造词；同一组字段在脚本里叫 target config（`target_config.py`、`.mmw/target.json`） |
| `story-parity.md`（`ui-acceptance/references/`） | story oracle 按 `data-ui` 元素比对设计页 | agent | 125/61 | 清楚 | — |
| `writing-interface-code.md`（`ui-acceptance/references/`，新位置；现在 `implement/references/`） | 按 screen contract 写界面代码 | agent（mode 触发行、P15） | 302/60 | 清楚 | — |
| `linting.md`（`verify-ticket/references/`） | 标题「Linting a batch」 | agent | 134/52 | 清楚 | — |
| `sub-issues.md`（`verify-ticket/references/`） | 标题「Cutting something out of a ticket」：五种子票 | agent | 184/58 | 含糊 | 同一概念在事件与 label 里叫 child（第 15.2 节） |
| `screen-contract-format.md`（`write-screen-contract/references/`） | screen contract 文件格式 | agent；程序：`lint_screen_contract.py` 第 139、350 行、`story-parity.py` 第 466、472 行拒绝文字 | 102/70 | 清楚 | — |
| `saving-memory.md`（`shared-experience/references/`，新位置） | 存一条 Memory 的条件 | agent | 74/16 | 清楚 | — |
| `revising-a-spec.md`、`several-specs.md`（`to-spec/references/`） | 改已发布的 spec；一份参考拆成几份 spec | agent | 117/38、50/20 | 清楚 | — |
| `ambiguity-scan.md`（`to-tickets/references/`） | 票切好后的歧义扫描 | agent（子代理） | 110/15 | 清楚 | — |
| `cutting-interface-tickets.md`（`to-tickets/references/`） | 标题「Tickets from a screen contract」 | agent | 352/112 | 含糊 | 名字说 interface，内容与标题说 screen contract |
| `person-ticket.md`（`to-tickets/references/`） | 只有人能做的事单开一张票 | agent | 100/47 | 清楚 | 词汇与 `ready-for-human`、`human-steps-stay-human` 不统一（第 15.2 节） |
| `night.md`（`dispatch/references/`，并入 P12、P13） | 夜的 orchestrator 流程 | agent；程序：`watchdog.py` 第 735、780 行告警文字按字面点名 | 1086/200 | 含糊 | 「night」是自造词，指任何时候的一次整批运行（第 15.1 节） |
| `one-ticket.md`（`dispatch/references/`，并入 P14） | 夜外起一个 worker 做一张票 | agent | 190/22 | 清楚 | — |
| `inside-a-ticket.md`（`dispatch/references/`，并入 P15） | 标题「A ticket you picked up yourself」 | agent | 160/22 | 误导 | 名字像是「在票里的会话都读」，内容只给自己拿起票的会话 |
| `editing-models.md`（`dispatch/references/`，并入 `setup-mmw`） | 改 host、model、effort、runner | agent | 128/42 | 含糊 | 只说 models，也改 host 与 runner |
| `ps/`（`mmw/references/ps/`，新） | 导入的 pstack mode reference 与 agent 简报 | agent；程序：`import_component.py` 机械改写 `../references/X` → `../references/ps/X`（R18 第 8.2 节） | 见第 9 节 `ps/` | 含糊 | 见第 9 节 |

## 4. 脚本文件名

| 现名（升级后位置） | 是什么（出处） | 谁读 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `dispatch.sh`（`mmw/scripts/`） | 流水线的命令行：24 个子命令（`dispatch.sh` 第 368–395 行 usage） | agent（playbook 步骤）；人；程序：`advance` 调 `start`、`install.sh`、测试 `test_dispatch.sh`、R18 的启动器与数据文件给绝对路径 | 2960/746 | 含糊 | 子命令里只有 `start`、`advise` 是 dispatch；`dispatch` 技能解散后，名字不再对应任何技能 |
| `relay.py`（同上） | tracker 上的事件进、给等候会话的唤醒出（第 1 行） | 程序：`dispatch.sh`、`watchdog.py`、`board_data.py`；人（排障） | 571/126 | 清楚 | relay 是通用词，文件首行说清了 |
| `watchdog.py`（同上） | 活性的第二、三层：查会话是否还活着（第 1 行） | 程序：`turn-guard.py`、`dispatch.sh`；agent 读它的 `watchdog:` 告警 | 310/82 | 清楚 | 通用术语 |
| `status.py`（同上） | 一张 spec 的只读视图；另算 `--advance-plan`、`--land-plan`、`--reverify-plan`，R18 加 `--where`（第 4–10 行） | 程序：`dispatch.sh` | 393/131 | 含糊 | 一半功能是「算计划」与「算位置」，不是状态 |
| `statedir.py`（同上） | 每个仓库的状态目录与锁 | 程序：`relay.py`、`watchdog.py`、`turn-guard.py`、`models.py` | 64/22 | 清楚 | — |
| `ghlist.py`（同上） | 按页读完一个 GitHub REST 列表 | 程序：`relay.py`、`board_data.py` | 33/4 | 清楚 | — |
| `models.py`（同上） | 读 `models.json`、扫宿主模型目录、按 `hosts.json` 展开启动参数、选 runner、改配置（第 1–2 行；第 1203–1233 行） | 程序：`dispatch.sh` 第 99 行、`runners/*.sh`、`board/settings_api.py`、`install.sh` 第 1088 行；人（`config show/set/runner`） | 521/114 | 含糊 | 它管的是角色的 host、model、effort 与 runner，名字只说 models |
| `tool-guard.py`（同上） | 拦三件事：手动关票、屏幕上提问、结束进程（第 1–2 行） | 程序：宿主 hook（`~/.claude/settings.json` 第 43、53、85 行，R18 第 7.3 节） | 323/44 | 含糊 | 按宿主 hook 事件（PreToolUse）起名，不说拦什么 |
| `turn-guard.py`（同上） | orchestrator 结束回合时的检查（第 1 行） | 程序：宿主 Stop hook | 234/60 | 清楚 | 「守住回合结束」与内容一致 |
| `runners/orca.sh`、`paseo.sh`、`herdr.sh`（同上） | 每个 runner 的适配器 | 程序：`dispatch.sh`、`models.py`（`RUNNERS_DIR`）、`install.sh` 第 1428 行 | 80/37、87/43、63/28 | 清楚 | — |
| `events.py`（`mmw/scripts/`；现在 `verify-ticket/scripts/`） | 事件词表与 fold | 程序：`dispatch.sh`、`status.py` 第 40 行、`relay.py` 第 258 行、`retro.py`、`board_data.py`（均按路径加载，R18 后经 `anchors.py`） | 509/118 | 清楚 | — |
| `ticket.py`（`mmw/scripts/`，新） | 从 `verify-ticket.py` 拆出的写票状态命令（R18 第 4.1 节） | agent（P15 各步）；程序：`tool-guard.py` `REFUSAL`（R18 第 7.6 节） | 35/0 | 含糊 | 与 `verify-ticket.py` 都「操作一张票」，名字不区分「写票的状态」与「跑票的判据」 |
| `anchors.py`（`mmw/scripts/`，新） | 文字锚点、跨目录路径、`where` 表的唯一登记处（R18 第 7.2、7.7 节） | 程序：`dispatch.sh`、`relay.py`、`board/`、`retro.py`、`install.sh`、`check_wiring.py` | 92/0 | 含糊 | 「anchor」指文中标题，登记的却还有文件路径与事件到步骤的表 |
| `mode-hook.py`（`mmw/scripts/`，新） | 会话开始、子代理开始、提交提示词时打印一行（R18 第 7.4 节） | 程序：`mmw-hook` 启动器 | 26/0 | 清楚 | — |
| `mmw-hook.py` → `~/.mmw/bin/mmw-hook`（`mmw-v2/`，新） | hook 启动器，按名字找三个 hook（R18 第 7.3 节） | 程序：五个宿主的 hook 配置 | 5/0、20/0 | 含糊 | 读作「MMW 的 hook」，它其实是启动所有 hook 的启动器；与 `mode-hook.py` 并列时分不清 |
| `import_component.py`（`mmw-v2/import/`，新） | 按八种类型把 pstack 文件放进 `mmw/` | agent（私有 playbook **Import a component**） | 25/0 | 清楚 | — |
| `pstack.map`（`mmw-v2/import/`，新） | 机械改写表 | 程序：`import_component.py` | 4/0 | 含糊 | 「map」已指 wayfinder 的地图（`mmw:map`、`--map N`） |
| `check_wiring.py`（`tests/lib/`，新） | 12 类连线检查（R18 第 7.5 节） | 程序：每个套件的 `run.sh`、`install.sh --check` | 166/0 | 含糊 | 「wiring」是比喻；12 类里有指针、可解析、方向、编号、原则索引、事件覆盖、骨架、一行、开关、路径、孤立命令、冻结路径 |
| `verify-ticket.py`（`verify-ticket/scripts/`） | 升级后：跑判据、lint、发布（第 4120–4169 行） | agent；程序：`dispatch.sh`、测试 `_load.py` | 1707/382 | 含糊 | 同第 2 节 `verify-ticket`；连字符文件名不能 `import`（`tests/AGENTS.md`） |
| `issue_tree.py`（同上） | 一个 issue 之下的树 | 程序：`status.py`、`board_data.py` | 88/40 | 清楚 | — |
| `boundary-check.py`（`ui-acceptance/scripts/`） | 同 `boundary-check.md` | agent（`CHECK:` 行按名字写，`to-tickets` 的 `cutting-interface-tickets.md`） | 138/73 | 含糊 | 同 `boundary-check.md` |
| `design_render.py`（同上） | 离线渲染设计包 | 程序：`story-parity.py`、`extract_skeleton.py` 导入 | 89/33 | 清楚 | — |
| `harness-guard.py`（同上） | 同 `harness-guard.md` | agent（`CHECK:` 行） | 96/44 | 含糊 | 同上 |
| `journey.py`（同上） | 在真产品上跑一条命名路径并证明它会失败 | agent（`CHECK:` 行）；程序：`verify-ticket.py` 第 88 行 `PRODUCT_JUDGES` | 177/96 | 清楚 | — |
| `lease.py`（同上） | 一个票工作树占用本机的一个产品槽位 | 程序：`dispatch.sh`、`verify-ticket.py` | 316/166 | 含糊 | 同一件事在事件与文档里叫 slot（`lease.py` 第 124 行「every slot file」放在 `leases/` 下） |
| `pixel_diff.py`、`refusal.py`、`story-parity.py`（同上） | 像素差图；所有拒绝的统一形状；story oracle | 程序、agent | 39/7、149/33、324/125 | 清楚 | — |
| `target_config.py`（同上） | 读并检查 `.mmw/target.json` | agent（`--check` 直到退出 0）；程序 | 241/65 | 含糊 | 「target」说不出这是产品答案（`product-answers.md`） |
| `check_editable_selectors.py`、`pull_design.py`（`design-pages/scripts/`） | 找 Claude Design 编辑器不能直接改的选择器；拉取设计包 | agent | 21/13、170/53 | 清楚 | — |
| `builders/nuitka.py`（`exe-release/scripts/`） | 生成 Nuitka 编译命令 | 程序 | 21/11 | 清楚 | — |
| `diagnose_core.py`（同上） | 把出包失败现场翻译成带等级与指纹的 finding（第 1 行） | 程序：`release-flow.sh` | 36/27 | 含糊 | 「core」没有说明 |
| `fix_dispatch.py`（同上） | P1 失败时写修复简报交给驱动出包的 agent（第 1 行） | 程序：`release-flow.sh` | 39/27 | 误导 | 「dispatch」是流水线技能与脚本的名字，也是事件的 stage 值；这里指「分派修复」 |
| `release_contracts.py`（同上） | 三份数据结构：ReleaseAdapterManifest、ReleaseFinding、ReleaseLoopEvent（第 1–2 行） | 程序 | 57/44 | 含糊 | 「contract」已指 screen contract 与 `contract` 子票 |
| `release_script_assembler.py`、`release_templates/nuitka_electron.ps1.tmpl`、`release-flow.sh`（同上） | 装配构建机输入；PowerShell 模板；出包引擎 | 程序、agent | 35/18、13/7、208/146 | 清楚 | — |
| `verify_key.py`（同上） | 出包前把「钥匙」对着仓库核一遍 | agent（`exe-release` 步骤） | 32/19 | 含糊 | 「key」＝release manifest，见 `key.md` |
| `check.sh`（`manage-agents-md/scripts/`） | 对 `AGENTS.md`、`CLAUDE.md` 做机械检查 | agent | 95/58 | 含糊 | 名字只说「检查」；仓库里还有 `check_wiring.py`、`check_module_paths.py` 等 |
| `retro.py`（`retro/scripts/`） | 盘点、搜索、写 `spec.retroed`（第 1–2 行） | agent | 248/71 | 清楚 | — |
| `dump_openapi.py`、`lint_screen_contract.py`（`write-screen-contract/scripts/`） | 导出 OpenAPI；lint screen contract | agent | 20/13、89/40 | 清楚 | — |
| `extract_skeleton.py`（同上） | 渲染设计包的场景并写出行清单（第 1 行） | agent | 107/57 | 含糊 | 「skeleton」是比喻，产物是 row inventory |
| `check_module_paths.py`、`check_own_skill_frontmatter.py`、`check_upstream_em_dashes.py`、`parse_k.sh`、`run_unittests.py`（`tests/lib/`） | 各套件先跑的检查；`-k` 解析；unittest 裁决 | 程序：各 `run.sh`；人 | 43/19、67/16、51/27、18/13、13/5 | 清楚 | — |
| `remove-verifier.py`（`migrations/`） | 一次性迁移 | 程序、人 | 19/3 | 清楚 | — |
| `install.sh`、`prompt/render.py` | 安装器；生成宿主用户级 `AGENTS.md` | 人、agent；程序：`dispatch.sh` 第 96 行 `INSTALLER` | 983/200、178/39 | 清楚 | — |

## 5. 子命令与开关

### 5.1 `dispatch.sh`

子命令列表取自 `dispatch.sh` 第 368–395 行 usage 与第 4628–4760 行分派表；含义取自各函数前的注释。

| 现名 | 是什么 | 谁读 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `check <spec>` | 开夜前检查本机与安装（`check_machine`） | agent（P12 **Check and open**） | 81/19 | 含糊 | 「check」十种用法之一（第 15.1 节） |
| `open <spec>` | 开一夜：relay 以本会话为 orchestrator 看住这个 spec，写 `spec.opened`（第 850–853 行） | agent | 30/22 | 含糊 | 与 GitHub 的 open issue 同词；不说开的是「夜」 |
| `open-ticket <n>` | 夜外为一张票开 watch（第 891–896 行） | agent | 17/7 | 含糊 | 读作「开一张票（issue）」 |
| `board` | 开任务板 | agent、人 | 21/12 | 清楚 | — |
| `adopt <n> [--into <branch>]` | 让自己拿起票的会话成为这张票的 worker（第 925–932 行） | agent | 22/10 | 含糊 | 同一概念另有 `self-picked-worker`、**Picked up yourself**、`adopted` 字段三个名字 |
| `self` | 打印本进程所在的 runner 与会话（第 4570 行） | 程序：`mode-hook.py`、`where`（R18 第 7.7 节） | 18/10 | 清楚 | — |
| `advance <spec>` | 把通过的票合进 project branch，再起前沿上的下一批（`night.md` `## 2`） | agent | 66/28 | 含糊 | 不说「合并」也不说「起下一批」 |
| `integrate <n>` | 把 `origin/<base>` 合进这张票的分支（第 2526–2528 行） | agent（P15） | 40/17 | 清楚 | 持续集成的通用词 |
| `integrated <n>` | 列出本票开始后合进 base 的兄弟票，给 Spec axis 交叉核对（第 2480–2483 行） | agent（reviewer） | 20/11 | 误导 | 读作「是否已集成」的状态查询；实际是一份票号清单 |
| `land <n>` | 夜外合并一张票并收掉它的会话、工作树、槽位（第 3262–3272 行） | agent（P14） | 19/11 | 清楚 | 「land a change」是通用说法；与 `advance`、`finish` 三个合并动词并存见第 15.1 节 |
| `start <n> worker\|reviewer` | 起会话并写 `*.started` | agent、程序（`advance`） | 124/46 | 清楚 | — |
| `advise <file>` | 起 advisor 会话 | agent | 52/14 | 清楚 | — |
| `retract <n>` | 会话已不在时撤回 `start` 留下的东西（第 2084–2088 行） | agent | 10/8 | 清楚 | — |
| `wait <n> worker\|reviewer` | 打印票上最新一条结果事件（第 2284–2290 行） | agent | 17/10 | 误导 | 注释原文「It waits for nothing」 |
| `ack <n> <event>` | 确认已处理一条唤醒 | agent（mode `## Re-entry`） | 22/14 | 清楚 | — |
| `resume <n> "<text>"` | 把 orchestrator 的一句话送进 worker 会话 | agent | 46/22 | 清楚 | — |
| `status <spec>` | 打印一张状态表（`status.py --table`） | agent | 34/11 | 清楚 | — |
| `findings <spec>` | 列出开着的 finding | agent | 14/11 | 清楚 | — |
| `memory-list <spec>` | 打印 `--memory-decisions` 文件的骨架（第 3705–3711 行） | agent | 10/7 | 含糊 | 名字说「列出」，产物是待填的决定文件 |
| `reverify <spec>` | 在 base 上重跑已落地票的判据 | agent | 26/16 | 清楚 | — |
| `summary <spec> --memory-decisions <file>` | 发 `NIGHT SUMMARY`、关 spec 的 watch、写 `spec.closed`（`night.md` 第 184–186 行） | agent | 15/10 | 含糊 | 它还关掉一夜；`status.py --summary` 同名却只打印 |
| `finish <spec>` | 用户验收后把一夜合进 project branch，写 `spec.merged`（`night.md` 第 188、200 行） | agent（P13） | 28/13 | 含糊 | 不说合并；`advance`、`land`、`finish` 三个动词都做合并 |
| `suspend <spec>` | 暂停一夜 | agent | 14/8 | 清楚 | — |
| `route <ticket> <child> …` | 记录一个子票的结局：`fixed`、`stale`、`became-ticket`（第 4455–4475 行） | agent（P12 **Closing pass**） | 58/28 | 含糊 | 「route」让人以为是转发；做的是结案登记 |
| `where [<spec>\|<n>]` | 新（R18）：从事件算出本会话在哪一步 | agent、程序（`mode-hook.py`） | 31/0 | 清楚 | — |
| `panel`、`panel-wait` | 新（R18，D7 按需）：跨厂商面板 | agent | 12/0、1/0 | 清楚 | — |
| `research <n>` | 新（R18 第 16 节）：起 `researcher` 会话 | agent（P2） | 6/0 | 清楚 | — |
| `--into <branch>`、`--memory-decisions <file>` | `adopt` 的 base 分支；关 Memory 记录的决定文件 | agent | 32/23、50/45 | 清楚 | — |
| `--tools <dir>` | 别的技能的脚本目录（`verify-ticket.py` 第 4167 行 help 同义） | 程序、测试 | 104/69 | 含糊 | 「tools」说不出是「其他技能的 scripts 目录」 |
| `became-ticket`、`fixed-elsewhere` | `route` 的结局值 | agent；程序：`events.py` `CHILD_RESOLUTIONS`、`STALE_REASONS` | 85/63、40/35 | 清楚 | — |

### 5.2 `verify-ticket.py` 与 `ticket.py` 的开关

开关取自 `verify-ticket.py` 第 4120–4169 行；R18 第 4.1 节把 `--preflight`、`--decisions`、`--review`、`--touched`、`--draft`、`--closeout`、`--sub-issue` 与 fold 移到 `ticket.py`。

| 现名 | 是什么 | 谁读 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `--reverify` | 重跑全部判据 | agent；程序：`dispatch.sh reverify` | 213/75 | 清楚 | — |
| `--lint` | 审判据的写法，不跑 `CHECK` | agent | 356/126 | 清楚 | — |
| `--drafts <dir>` | 未发布的票草稿目录 | agent | 104/37 | 含糊 | 与 `--draft`（收尾评论草稿）只差一个字母，意思不同 |
| `--publish`、`--spec-body`、`--title`、`--map N` | 发布 spec 或一批草稿 | agent（`to-spec`、`to-tickets`） | 76/44、25/20、62/57、17/15 | 清楚 | `--map` 与 `pstack.map` 撞词见第 15.1 节 |
| `--preflight` | 认领这张票，或在票上写明为何拒绝（help 原文） | agent（P15 **Claim**） | 187/60 | 误导 | preflight 通常指只读的预检；它写 `ticket.claimed` 或 `ticket.refused` |
| `--closeout <draft>` | 核对收尾评论后发出并关票 | agent；程序：`tool-guard.py` 第 68 行 `REFUSAL` | 293/105 | 清楚 | closeout 在 `docs/contexts/` 有定义 |
| `--check-only` | 与 `--closeout` 同用：只核对 | agent | 48/14 | 清楚 | — |
| `--decisions <file>` | 发 DECISIONS 评论 | agent | 70/16 | 清楚 | — |
| `--touched` | 在 `## Owns` 覆盖了本次改动文件的兄弟票上发 `worker.touched` | agent | 86/25 | 含糊 | 不说是「通知被碰到的票」 |
| `--draft [out]` | 写收尾评论草稿 | agent | 90/21 | 含糊 | 见 `--drafts` |
| `--sub-issue <kind> <file>` | 在本票下开一个 `needs-triage` 子票 | agent | 158/53 | 含糊 | 子票在事件与 label 里叫 child |
| `--actor worker\|main` | `--reverify` 必带：worker 的最后一次，或 orchestrator 在 base 上重跑 | agent | 92/33 | 含糊 | `main` 指 orchestrator（help 写「the main agent」），与 main 分支同词 |
| `--review <file>` | 发评审报告 | agent（P16） | 113/41 | 清楚 | — |
| `--tools <dir>` | 同第 5.1 节 | 程序 | 104/69 | 含糊 | 同第 5.1 节 |
| `ticket.py <n> --check` | 新（R18 P15 第 4 步）：跑判据 | agent | 4/0 | 含糊 | 今天跑判据是不带开关的默认调用；`--check` 与 `--check-only`、`install.sh --check` 同词 |
| `fold`（`events.py fold`，R18 写作 `ticket.py fold <n>`） | 把票的全部事件重放成当前状态 | agent（P14）；程序 | 29/11 | 清楚 | 函数式编程的通用词，`events.py` 首段有定义 |
| `resume_at` | 今天在 `verify-ticket.py` 第 2148–2182 行；R18 移进 `status.py --where` | 程序 | 84/5 | 清楚 | 随 R18 删除 |
| `--where`（`status.py`，新） | 算出位置 | 程序：`dispatch.sh where` | 4/0 | 清楚 | — |
| `own_session()` | 今天在 `verify-ticket.py` 第 250–257 行；R18 删除 | 程序 | 27/12 | 清楚 | 随 R18 删除 |

### 5.3 其他脚本的子命令（不计次数）

| 脚本 | 子命令（出处） | 判断 |
|---|---|---|
| `relay.py` | `start`、`add`、`stop`、`watching`、`run`、`ack`、`queue`（第 3–9 行） | 清楚；`queue` 与 label 组 Queue 同词（第 15.1 节） |
| `watchdog.py` | `run`、`arm`、`status`（第 4–6 行） | 清楚 |
| `turn-guard.py`、`tool-guard.py` | `stop <host>`；`pretool <host>`、`question <host>`（各自第 4、22–23 行） | 清楚：按宿主 hook 事件命名，读者是程序 |
| `models.py` | `config show`、`config set`、`config runner`、`runner`，R18 加 `config get`（第 1203–1233 行） | 含糊：`runner` 是读当前 runner，`config runner` 是改，两者只差前缀 |
| `status.py` | `--table`、`--advance-plan`、`--reverify-plan`、`--worker-grades`、`--summary`、`--findings`、`--land-plan`（第 4–10 行） | 清楚；`--summary` 与 `dispatch.sh summary` 同名不同事 |
| `events.py` | `emit`、`fold`、`session`、`sessions`、`result`、`checked`、`live`、`child`（第 5–12 行） | 清楚 |
| `retro.py` | `gather`、`search`、`finalize`（第 2 行） | 清楚 |
| `lease.py` | `claim`、`release`、`count` 等（第 5–11 行） | 清楚 |

## 6. playbook slug 与被程序点名的步骤名

「谁读」对全部 MMW 自写 playbook 相同，不逐行重复：agent 从 mode 路由表与启动提示词读；程序经 `roles.json` 的 `playbook` 字段（R18 第 7.1 节）把 slug 写进启动提示词、唤醒行尾的指针 `mmw <slug>#<Step>`、`where` 的输出（R18 第 7.7 节）、`tool-guard.py` 的 `REFUSAL`（R18 第 7.6 节）；`check_wiring.py` 第 1、2、7 类核对。私有 playbook 的 slug 还被消费仓库的 `.mmw/target.json` 按字面读（`delivery: playbook:<slug>`，R18 第 3.3 节 P10）。

| 现名 · 标题（R18 第 3.1 节） | 是什么 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `define-a-change` · **Define a change** | 对话或想法 → 已发布的 spec 与过了 lint 的票 | 31/0 | 含糊 | 名字不提 spec 与票；「change」同时出现在 `direct-change`、`deliver-a-change`、`promote-a-change`，四处指的东西不同 |
| `map-a-large-effort` · **Map a large effort** | 一个会话装不下、路线看不清的工作 | 17/0 | 含糊 | 「effort」另指推理强度与 `docs/specs/<effort>/` |
| `design-an-interface` · **Design an interface** | 界面设计、拉设计包、写 screen contract | 25/4 | 清楚 | — |
| `prototype` · **Prototype** | pstack 同名，MMW 版 | 133/13（`prototype.md`） | 清楚 | pstack 名 |
| `direct-change` · **Direct change** | 小到用户直接检查、不开票的改动 | 6/0 | 含糊 | 「direct」可读成「直接动手改」；真正的判据是「由用户直接检查」（R18 P5 所有权行） |
| `bug-fix` · **Bug fix** | pstack 同名 | 171/0 | 清楚 | pstack 名 |
| `triage-an-issue` · **Triage an issue** | 判外来 issue 与 PR | 17/0 | 清楚 | — |
| `research-a-question` · **Research a question** | 一手来源回答一个问题，写成仓库文件 | 11/0 | 清楚 | — |
| `onboard-a-repository` · **Onboard a repository** | 给仓库接入 MMW | 19/0 | 清楚 | — |
| `deliver-a-change` · **Deliver a change** | 按仓库的 `delivery` 交出改动 | 8/0 | 清楚 | — |
| `authoring-a-skill` · **Authoring or modifying a skill** | pstack 同名，MMW 版 | 79/0 | 清楚 | pstack 名 |
| `run-a-night` · **Run a night** | 一份 spec 的整批票 | 48/0 | 含糊 | 「night」是自造词，指任何时候的一次整批运行（`dispatch/SKILL.md` 第 12 行「at any hour」） |
| `accept-the-night` · **Accept the night** | 早上的队列、验收、`finish` | 23/0 | 含糊 | 同上 |
| `run-one-ticket` · **Run one ticket** | 夜外为一张票起 worker 并落地 | 29/0 | 含糊 | 与 `work-a-ticket` 只差动词，run 是「编排」、work 是「亲手做」，名字不说 |
| `work-a-ticket` · **Work a ticket** | worker 从认领到关票 | 68/0 | 含糊 | 同上 |
| `review-a-ticket` · **Review a ticket** | reviewer 的流程 | 32/0 | 清楚 | — |
| `session-pickup` · **Session pickup** | pstack 原文（D6 推迟到按需） | 127/0 | 清楚 | pstack 名 |
| `pause-safely` · **Pause safely** | pstack 原文（D6 推迟到按需） | 77/0 | 清楚 | pstack 名 |
| `promote-a-change` · **Promote a change** | 本仓库私有：dev → main → 已安装 checkout → push | 6/0 | 清楚 | promote 是发布工程的通用词 |
| `pull-an-upstream` · **Pull an upstream** | 本仓库私有：拉上游子树 | 8/0 | 清楚 | — |
| `import-a-component` · **Import a component** | 本仓库私有：导入 pstack 组件 | 10/0 | 清楚 | — |
| `INDEX.md`（`.mmw/playbooks/`） | 私有 playbook 索引 | 7/0 | 清楚 | — |

被 `roles.json` 的 `wakes` 或 `where` 表按字面点名的步骤名（R18 第 7.1、7.7 节；程序经锚点读，agent 从唤醒行读）：

| 步骤名 | 所在 playbook | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| **Claim** | `work-a-ticket` | 284/51 | 清楚 | 对应的开关叫 `--preflight`，两个名字（第 15.2 节） |
| **Get reviewed** | `work-a-ticket` | 17/0 | 清楚 | — |
| **Close out** | `work-a-ticket` | 15/0 | 清楚 | — |
| **Handle each wake** | `run-a-night`、`run-one-ticket` | 18/2 | 清楚 | — |
| **Closing pass** | `run-a-night` | 22/0 | 清楚 | — |
| `#### When the orchestrator resumes you` | `work-a-ticket` | 4/0 | 清楚 | — |
| `#### After the closeout, picked up yourself` | `work-a-ticket` | 5/0 | 含糊 | 逗号连起两个短语；不说这是 `ticket.passed`、`ticket.returned` 的处理处 |
| **Picked up yourself**（入口） | `work-a-ticket` | 7/0 | 含糊 | 与 `adopt`、`self-picked-worker` 是同一概念的三个名字 |
| **Active Rules**（`review-a-ticket#Active Rules`） | `review-a-ticket` | 39/15 | 清楚 | — |

## 7. 原则 slug（MMW 自有 12 条）

文件名 `mmw/principles/principle-<slug>.md`（R18 第 5.1 节）。谁读：agent（mode `## Principles` 索引、playbook 括注、回复里点名，mode `## Non-negotiables` 首段）；人（回复与交付物里的点名）；程序：`check_wiring.py` 第 5 类（索引行对原则文件）、`import_component.py` 同名拒绝（R18 第 8.5 节）、`retro.py` `DESTINATIONS` 加 `principle`（R18 第 4.1 节）。次数按不带 `principle-` 前缀的 slug 计。

| slug | 规则（R18 第 5.2 节） | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 检查没真跑或绿灯另有原因就是失败 | 136/17 | 清楚 | 与 ADR `0008-silence-is-never-a-pass.md` 同名，五个脚本的文件头引它（`events.py` 第 36 行等） |
| `the-tracker-is-the-state` | 位置由持久记录决定，不由会话记忆决定 | 88/0 | 含糊 | 规则还管提交与出包引擎的状态（`exe-release/references/driving.md` 第 5 行），名字只说 tracker |
| `woken-not-polled` | 不轮询别的 agent，起了就结束回合 | 16/3 | 清楚 | — |
| `route-faults-dont-bypass` | 故障按流水线的路由上报，不绕路 | 4/0 | 含糊 | `dont` 缺撇号，读不出是一句还是两句；「route」已是 `dispatch.sh route`（登记子票结局）的名字 |
| `the-baseline-is-a-contract` | 基准照抄，不成立就开 `contract` 子票 | 14/0 | 含糊 | 「contract」同时指 screen contract；与 `contract` 子票的关联是有意的，与 screen contract 的重合不是 |
| `refusals-name-one-next-step` | 收到拒绝照它点名的一步做 | 5/0 | 清楚 | — |
| `a-second-reader-judges` | 判断交给没写它的读者 | 9/0 | 清楚 | — |
| `clues-are-not-evidence` | Memory、顾问、报告都是线索，行动前核实 | 17/0 | 清楚 | — |
| `one-home-per-meaning` | 一个意思只有一个权威的家 | 5/0 | 清楚 | 与词表的 `_Home_` 字段同词 |
| `human-steps-stay-human` | 只有人能做的一步交给人 | 13/0 | 清楚 | — |
| `no-secrets-in-artifacts` | 凭据与个人数据不进任何产物 | 3/0 | 含糊 | 规则也管个人数据，名字只说 secrets |
| `decide-at-phase-boundaries` | 阶段结束时在五个选项里选一个 | 10/0 | 清楚 | 取自上游 `ask-matt/PHASE-BOUNDARIES.md` |

句式：12 条里只有 `decide-at-phase-boundaries`、`route-faults-dont-bypass` 是祈使句；其余是陈述句（`clues-are-not-evidence`）、分词（`woken-not-polled`）或名词短语（`one-home-per-meaning`）。pstack 23 条里 17 条是祈使句（第 16.2 节）。

## 8. mode 的节名与 playbook 骨架标记

谁读：agent（每个会话读 mode）；程序：`anchors.py` 登记 `## Re-entry`、`## Autonomy`（R18 第 7.2 节），advisor 的启动提示词按字面写「per the mmw skill's ## Autonomy」（R18 第 2.3 节），指针 `mmw#<节名>` 由 `check_wiring.py` 第 1 类核对。

| 现名 | 是什么（R18 第 2.2 节） | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `## Non-negotiables` | 常设触发行 | 47/0 | 清楚 | pstack 节名 |
| `### Imported triggers` | 按原文复制的 pstack 触发行（D6 后按需） | 7/0 | 含糊 | 说的是来历（导入的），不是作用；读者要在两张触发表里找 |
| `## Principles` | 原则索引 | 97/5 | 清楚 | pstack 节名 |
| `## Autonomy` | 优先级、人在场、无人时的出路 | 97/0 | 清楚 | pstack 节名 |
| `## Re-entry` | 被唤醒、被压缩、被 `resume` 后怎样接上 | 42/0 | 清楚 | — |
| `## Subagents` | 子代理的简报与模型 | 80/0 | 清楚 | pstack 节名 |
| `## Writing the reply` | 回复以 `shared.md` 为准 | 34/0 | 清楚 | pstack 节名 |
| `## Comments` | pstack 原文（B3，D6 后按需） | 31/6 | 清楚 | pstack 节名 |
| `## Playbooks` | 执行协议、别名、路由表 | 50/0 | 清楚 | pstack 节名 |
| `**Entry.**` | playbook 骨架：多入口时每个入口一行（MMW 多出） | 4/0 | 清楚 | — |
| `**Where you are.**` | playbook 骨架：读哪条脚本输出定位（MMW 多出） | 18/0 | 清楚 | — |
| `#### Steps` | 长 playbook 里进待办的步骤 | 24/0 | 清楚 | — |
| `**Reply:**` | 本 playbook 独有的交付物 | 98/0 | 清楚 | pstack 标记 |
| `## On waking`（去掉，并入 `## Re-entry`） | 现在 `dispatch/SKILL.md` 的四步 | 155/13 | 清楚 | 现名 |
| `## Find your moment`（去掉） | 现在五个技能的时刻表 | 97/22 | 含糊 | 「moment」是 MMW 的自造分类词 |
| `## Next`、`## Reached from here`（去掉） | 现在能力技能里「下一步」「谁调用我」的小节 | 209/17、68/8 | 清楚 | 现名；R18 第 4.5 节禁止 |

## 9. `mmw/` 下的配置文件与登记值

| 现名 | 是什么（出处） | 谁读 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `roles.json`（新） | 角色 → playbook → `models.json` 行 → 启动命令 → 唤醒步骤（R18 第 7.1 节） | 程序：`dispatch.sh`、`relay.py`、`watchdog.py`、`turn-guard.py`、`check_wiring.py`（字面文件名） | 51/0 | 清楚 | — |
| `anchors.py`（新） | 见第 4 节 | 程序 | 92/0 | 含糊 | 见第 4 节 |
| `imports.tsv`（新） | 每个外来文件的类型、路径、来源提交、改动、批次 | 程序：`import_component.py`、`check_wiring.py` 第 4、7 类；人 | 38/0 | 清楚 | — |
| `slots.md`（新） | 见第 3 节 | agent、程序 | 60/0 | 误导 | 见第 3 节 |
| `hosts.json`（现在 `dispatch/`） | 两个键：`hosts`（每个宿主怎样起）与 `defaults`（首次安装时四个角色的默认行） | 程序：`models.py`（按 `SKILL_DIR` 找） | 136/40 | 含糊 | 角色默认值也放在这里，名字只说 hosts |
| `~/.mmw/models.json` | 角色 → host、model、effort，加 `runner` | 程序：`models.py`（要求恰好四行，第 139–143 行）、`dispatch.sh` 第 85 行、`board/settings_api.py`、`page/local-config.mjs`；人（任务板设置页） | 438/159 | 含糊 | 内容是角色配置；`settings_api.py` 第 1 行叫它「agent configuration」，`board/AGENTS.md` 第 3 行叫「model configuration」 |
| `skills.txt` | 装进各宿主的技能名单 | 程序：`install.sh`、`check_own_skill_frontmatter.py` | 236/34 | 清楚 | — |
| `+model`（`skills.txt` 行尾标记，新） | 这个上游技能被点名，安装副本去掉 `disable-model-invocation`（R18 第 4.3 节） | 程序：`install.sh`、`check_wiring.py` 第 9 类 | 51/0 | 误导 | 旁边的 `models.json`、`models.py` 里「model」都指 LLM；读作「加一个模型」 |
| `ps/`（`skills.txt` 前缀与 `references/ps/`、`scripts/ps/`，新） | pstack 来源 | 程序：`install.sh`、`check_own_skill_frontmatter.py`、`import_component.py` | 47/0 | 含糊 | 缩写；与 Unix `ps`、`exe-release` 的 PowerShell 文件（`tests/exe-release/ps-syntax-check.ps1`）同形 |
| `upstream-pstack/`（新） | pstack 的 squash subtree | 程序：`install.sh`；人 | 34/0 | 清楚 | 与 `upstream-unlazy/`、`upstream-diagram-design/` 同句式；mattpocock 的目录却叫 `upstream/`，无后缀 |
| 角色 `worker` | 被 `start` 派到票上的写码会话 | 程序：`roles.json`、`tool-guard.py`（R18 `MMW_ROLE`）；agent | — | 清楚 | 通用词 |
| 角色 `self-picked-worker`（新） | 自己拿起票的 worker | 程序：`roles.json`、`relay.py` 取角色 | 8/0 | 含糊 | 同一概念另叫 `adopt`、**Picked up yourself**、`adopted` |
| 角色 `reviewer`、`advisor` | 评审、顾问 | 同上；`models.json` 同名行 | — | 清楚 | 与技能、`models.json` 行同名 |
| 角色 `night-orchestrator`（新） | 夜的 orchestrator | 程序：`roles.json`；事件 actor 写作 `main` | 16/0 | 含糊 | 「night」自造；同一角色在事件里叫 `main`、在 `relay.py` 叫 `MAIN` |
| 角色 `ticket-orchestrator`（新） | 夜外单票的 orchestrator | 同上 | 8/0 | 含糊 | 夜的 orchestrator 也处理票；名字不说「一张票、夜外」 |
| 角色 `researcher`（新，R18 第 16 节） | 另起会话做调研 | 程序：`roles.json`、`models.py` `ALLOWED_AGENTS`、`local-config.mjs` | 19/0 | 清楚 | — |
| 行 `junior-worker`、`senior-worker` | worker 的两档，同时是 label | 程序：`models.py`、`dispatch.sh`（按票的 `*-worker` label 选行）、`verify-ticket.py` `GRADE_LABELS` | 165/117、142/87 | 清楚 | — |
| `roles.json` 键 `playbook`、`models_row`、`started_by`、`wakes`、`brief`、`skill` | R18 第 7.1 节 | 程序 | `models_row` 8/0、`started_by` 12/0 | 清楚 | — |
| `where` 输出 `AT`、`BETWEEN`、`FRESH`、`UNKNOWN`（新） | 四种位置（R18 第 7.7 节） | agent；程序：`mode-hook.py` | 各 1/0 | 清楚 | — |
| watch 的 `kind`：`night`、`ticket`、`adopt`（新） | 由 `open`、`open-ticket`、`adopt` 写（R18 第 7.1 节） | 程序：`relay.py`、`watchdog.py`、`turn-guard.py` | 0/0 | 含糊 | 两个名词加一个动词；`adopt` 借用命令名 |
| 导入类型 `playbook`、`principle`、`skill`、`mode-trigger`、`mode-section`、`mode-reference`、`mode-script`、`agent`（新） | R18 第 8.2 节 | 程序：`import_component.py`、`imports.tsv` | 7/0、5/0、3/0、4/0（mode-* 四个） | 清楚 | — |
| `.mmw/target.json` 键 `delivery`，值 `commit`、`playbook:<slug>`（新；D2 删去 `pr`） | 这个仓库怎样收改动 | 程序：P10 的 agent 按字面读；`install.sh --check` | 29/0 | 清楚 | — |
| 步骤指针 `mmw <slug>#<Step title>`、`mmw#<节名>`（新） | 脚本送进会话的定位（R18 第 1.3、7.8 节） | agent；程序：`relay.py`、`watchdog.py`、`turn-guard.py`、`dispatch.sh`、`check_wiring.py` 第 1 类 | 13/0 | 清楚 | 前缀 `mmw` 的多义见第 15.1 节 |
| `ALLOWED_AGENTS`（`models.py` 第 31 行） | 允许的角色行 | 程序 | 25/13 | 含糊 | 角色在这里叫 agent |
| `.mmw/target.json`（消费仓库） | 产品答案 | 程序：`target_config.py`、`verify-ticket.py`、`dispatch.sh` | 536/286 | 含糊 | 「target」不说是产品答案；文档叫 product answers |
| `.mmw/playbooks/`（消费仓库，新） | 仓库私有 playbook | agent（只在人在场时） | — | 清楚 | — |

## 10. 事件名

事件词表在 `events.py` 第 106 行起的 `EVENTS`。谁读，对全部事件相同：程序按字面读——`events.py`（定义与 fold）、写者（`verify-ticket.py`/`ticket.py`、`dispatch.sh` 经 `events.py emit`、`watchdog.py` 写 `*.lost`）、读者（`status.py`、`relay.py` 的 `WAKES`、`retro.py`、`board_data.py`、`dispatch.sh` 的 `ticket_events`），R18 后还有 `roles.json` 的 `wakes`；agent 在唤醒行 `#<n> reviewer.reported` 与 `ack <n> <event>` 里读到事件名；人读的是同一条评论的第一行文字，事件名藏在 HTML 注释里（`events.py` 第 21–27 行）。事件永久写在 GitHub 评论里，每次 fold 从头重放，读不懂的块列为 `unreadable`，调用方拒绝判断（`events.py` 第 33–36 行），所以改名要带别名（推断，依据这两段原文）。

| 现名 | 是什么（`events.py`） | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `spec.opened` | 一夜在这个 spec 上开始（`dispatch.sh` 第 850–853 行） | 163/119 | 误导 | 读作「GitHub 上开了一个 spec」；记的是夜的开始 |
| `spec.suspended` | 一夜被暂停 | 74/48 | 清楚 | 「暂停」只可能是夜 |
| `spec.closed` | `summary` 写：一夜结束（`night.md` 第 186 行） | 174/95 | 误导 | 读作 spec issue 被关闭；`summary` 不关 spec issue（`dispatch.sh` `summary_spec` 里没有关 issue 的调用，推断），之后还要 `retro` 与 `finish` |
| `spec.retroed` | `retro` 已记录或未记录 | 190/107 | 含糊 | 自造动词 |
| `spec.merged` | `finish` 把一夜合进 project branch | 66/34 | 清楚 | — |
| `ticket.claimed` | worker 认领 | 124/85 | 清楚 | 写它的开关叫 `--preflight`（第 15.2 节） |
| `ticket.refused` | 认领被拒（六种原因） | 114/60 | 清楚 | — |
| `ticket.passed` | 收尾通过、关票 | 359/240 | 清楚 | — |
| `ticket.returned` | 收尾未通过、交回 | 231/126 | 清楚 | — |
| `ticket.released` | 认领被放回（`landed`、`suspended`、`worker-lost`） | 88/59 | 含糊 | 「released」先让人想到发布（`exe-release`） |
| `ticket.landed` | 通过的提交已进 base | 158/125 | 清楚 | — |
| `ticket.regressed`、`ticket.recovered` | 落地后重跑变红；修好后恢复 | 80/48、39/15 | 清楚 | — |
| `ticket.bounced` | 合并失败（`conflict`、`checks`） | 168/90 | 含糊 | 俚语，不说是合并失败 |
| `ticket.checked` | 一次判据或仓库检查的运行及结果 | 292/173 | 含糊 | 不说结果；与「check」一族同词 |
| `worker.started`、`worker.resumed`、`worker.retracted`、`worker.replaced` | 起、续、撤、换 | 274/212、50/28、66/36、28/24 | 清楚 | — |
| `worker.decided` | 发了 DECISIONS | 59/43 | 清楚 | — |
| `worker.queued` | 等产品槽位 | 167/90 | 清楚 | — |
| `worker.touched` | 发在票 A 上：票 B 改了票 A `## Owns` 覆盖的文件（`events.py` 第 163–166 行注释） | 27/17 | 误导 | 主语是 worker，读作「本票的 worker 碰了什么」；实际是「别的票碰了本票的文件」 |
| `worker.lost`、`reviewer.lost` | watchdog 判定会话已停 | 98/57、93/41 | 清楚 | actor 值 `judge` 见下 |
| `reviewer.started`、`reviewer.reported` | 起评审；报告已发 | 83/40、257/133 | 清楚 | — |
| `child.opened`、`child.closed` | 开子票；子票结局登记 | 188/102、101/63 | 清楚 | 与 sub-issue 两名见第 15.2 节 |
| `relay.recovered` | relay 恢复读取后的唤醒（不在 `events.py`） | 96/48 | 清楚 | — |
| 告警前缀 `watchdog:` | 八种告警（`watchdog.py` 第 94–109 行） | 51/39 | 清楚 | — |
| 行首 `MMW turn guard:` | turn guard 的提醒（`turn-guard.py` 第 306 行） | 70/13 | 清楚 | — |
| actor 值 `main` | orchestrator 写的事件 | 23（现役，精确形式） | 含糊 | 同一角色另叫 orchestrator、`MAIN`（`relay.py` `WAKES`）；与 main 分支同词 |
| actor 值 `judge` | `worker.lost`、`reviewer.lost` 的写者，即 watchdog（第 170、178 行） | 37/8 | 误导 | `judge` 在 `verify-ticket.py` 第 88 行 `PRODUCT_JUDGES` 指 oracle 脚本，在 `MMW_JUDGE_LEASE_OWNER` 指 oracle 的租约 |
| stage 值 `dispatch` | `worker.started`、`worker.retracted`、`worker.replaced` 的阶段 | — | 含糊 | 与技能、脚本同名；技能解散后仍可读作动词「派出」，但读者会先想到那个技能 |
| 子票 kind `finding`、`deferred`、`decision`、`fault` | `events.py` `CHILD_KINDS` | 90/65、38/25、109/65、106/50 | 清楚 | — |
| 子票 kind `contract` | 基准不成立 | 228/115 | 含糊 | 与 screen contract 同词 |

## 11. tracker label

定义在 `verify-ticket.py` 第 59–82 行，文档在 `docs/agents/issue-tracker.md` `## Three label sets`。谁读：人（GitHub、任务板）；程序：`verify-ticket.py`（`ensure_label` 创建、`--lint` 读 `mmw:spec`）、`dispatch.sh` 按 `WORKER_LABEL_RE`（第 113 行）读 `*-worker`、`board_data.py`；agent：`triage` 技能与 `issue-tracker.md` 的两条早上查询。label 贴在各仓库已有的 issue 上。

| 现名 | 是什么 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `mmw:map`、`mmw:spec`、`mmw:ticket`、`mmw:child` | 层级 label | 109/54、89/52、96/70、68/53 | 清楚 | 代码里的常量叫 `CLASS_LABELS`（第 59 行），文档叫 Layer；`mmw:child` 与 sub-issue 两名 |
| `needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix` | 队列 label（mattpocock 的名字，`docs/agents/triage-labels.md`） | 384/226、50/36、569/232、196/95、84/44 | 清楚 | 上游名；`ready-for-human` 在本仓库收窄为「只有人能做的一件事，kind 为 `reaction` 或 `reach`」 |
| `junior-worker`、`senior-worker` | worker 档位 label，同时是 `models.json` 行名 | 见第 9 节 | 清楚 | — |

## 12. 状态目录与文件

目录布局取自 `statedir.py` 第 1–30 行、`relay.py` 第 170–200 行、`watchdog.py` 第 111–145 行、`lease.py` 第 115–130 行、本机 `ls ~/.mmw`。谁读：程序按字面读，除特别写明外是 `relay.py`、`watchdog.py`、`turn-guard.py`、`statedir.py`、`dispatch.sh`；人在排障时读；agent 在拒绝文字里读到路径。

| 现名 | 是什么 | 谁读（特别的） | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|---|
| `~/.mmw/`（`MMW_HOME`） | 本机 MMW 根目录 | `lease.py`、`board/`、`install.sh` | `MMW_HOME` 169/148 | 清楚 | — |
| `installed-root` | 已安装 checkout 的路径（H5 冻结点） | `dispatch.sh`、`install.sh`、R18 的启动器 | 85/20 | 清楚 | — |
| `models.json`、`models.lock` | 角色配置与它的锁 | `models.py` | 见第 9 节、7/5 | 含糊 | 见第 9 节（`models.lock` 随它） |
| `boards.json`、`boards.json.lock`、`board.log` | 任务板登记、锁、日志 | `board/supervisor.py`、`install.sh` | 51/27、—、3/3 | 清楚 | — |
| `bin/mmw-hook`（新） | hook 启动器副本 | 宿主 hook 配置 | 20/0 | 含糊 | 见第 4 节 |
| `skills/<name>/`（新） | 带 `+model` 的上游技能的安装副本（R18 第 4.3 节） | 宿主技能软链 | — | 含糊 | 与 `~/.agents/skills`、`~/.claude/skills` 并存，名字不说是「安装副本」 |
| `state/<owner>__<name>/` | 每个仓库的状态目录 | 全部状态脚本 | 21/4 | 清楚 | — |
| `watches.json` | 开着的 watch | R18 起加 `kind` | 104/68 | 清楚 | — |
| `relay.lock`、`relay.log` | relay 的锁与日志 | — | 50/40、12/9 | 清楚 | — |
| `relay.json` | 运行中 relay 的 pid、身份、间隔（`relay.py` 第 185 行） | `watchdog.py` | 35/34 | 含糊 | 名字只说 relay；它是进程记录 |
| `beat.json` | relay 的心跳：最后一次成功读取（`relay.py` 第 188 行） | `watchdog.py` | 53/51 | 含糊 | watchdog 的心跳叫 `watchdog.json`，两个心跳两种起名法 |
| `gap.json` | 最近一次宣布的无人值守空档（`relay.py` 第 195 行） | — | 15/14 | 含糊 | 「gap」说不出是什么空档 |
| `seen.json` | 每张票已翻译过的（评论，事件）对 | — | 11/10 | 清楚 | — |
| `queue.jsonl`、`queue.seq`、`queue.lock` | 唤醒队列、序号、锁 | — | 15/13、7/7、4/4 | 含糊 | 「queue」在 label 里指「等谁」一组（`issue-tracker.md` 第 39 行）；这里是唤醒队列 |
| `watchdog.lock`、`watchdog.log` | watchdog 的锁与日志 | — | 33/25、8/8 | 清楚 | — |
| `watchdog.json` | watchdog 的心跳 | `turn-guard.py` | 34/30 | 含糊 | 见 `beat.json` |
| `guard.log` | turn guard 对每个 orchestrator 的决定（`turn-guard.py` 第 82 行） | — | 20/15 | 含糊 | 有两个 guard，名字不说是哪个 |
| `merge-<branch>.lock` | 每个合并目标一把锁 | `dispatch.sh` | 43/6 | 清楚 | — |
| `prompts/`、`panels/`（新） | 启动提示词的数据文件；面板答案 | `dispatch.sh` | 10/1、7/0 | 清楚 | — |
| `leases/`、`instances/` | 产品槽位登记；每次运行的数据目录（`lease.py` 第 122–129 行） | `lease.py` | 77/46、3/3 | 含糊 | `leases/` 里放的是「slot file」（第 124 行注释），一义两名 |
| `logs/`、`worktrees/`、`memory-backups/`、`secrets.env`、`chameleon-data/`、`host-config-backup-*`、`removed-hook-leftovers-*.tar.gz`（本机 `~/.mmw/` 下） | 在 `mmw-v2/` 的脚本里 grep 不到写者 | 不明 | `memory-backups` 0/0、`secrets.env` 1/0 | 清楚 | 名字本身说得清；来历不明（推断：别的工具或手工留下），不属于 MMW 的命名范围，列出供改名表核对 |
| `.worktrees/issue-<n>`、`merge-<branch>`、`research-<n>`（新）、`mmw-installed` | 流水线的工作树 | `tool-guard.py` 按目录名 `issue-<n>` 判定受管会话（R18 第 7.3 节） | 166/75、—、1/0、37/15 | 清楚 | — |

## 13. `board/` 文件名

谁读：程序——LaunchAgent `com.mmw.board`（`install.sh` 写路径）起 `supervisor.py`；`server.py` 按裸名导入 `board_data`、`codeversion`、`gates`、`settings_api`（`board/AGENTS.md` `## Gotchas` 第 1 条）；`codeversion.LOADED` 按文件名登记指纹；`page/index.html` 加载各 `.mjs`；`tests/board/` 的同名测试。人：维护者。

| 现名 | 是什么（出处） | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `board_data.py` | `GET /api/board` 背后的只读 GitHub 索引（第 1 行） | 64/16 | 清楚 | — |
| `codeversion.py` | 发现已加载的 Python 文件在磁盘上变了（第 1 行） | 30/10 | 清楚 | — |
| `gates.py` | 写请求的同源与 token 检查（第 1 行） | 12/8 | 含糊 | `verify-ticket` 用的 unlazy 检查叫 gate-check（132 次现役） |
| `server.py`、`supervisor.py`、`settings_api.py` | 服务一个仓库的板；保持每个仓库一个；读写 `models.json` | 58/17、71/17、40/2 | 清楚 | — |
| `page/api.mjs`、`app.mjs`、`shared.mjs` | 请求封装；页面布局；DOM 小工具 | 3/3、17/13、6/6 | 清楚 | 前端惯用名 |
| `page/board-feed.mjs` | 定时刷新 | 6/6 | 清楚 | — |
| `page/board-logic.mjs` | 票的两条轴：phase 与 lamp（第 1–3 行） | 30/30 | 含糊 | 「logic」不说是哪条逻辑 |
| `page/canvas.mjs`、`detail.mjs`、`tasks.mjs`、`topbar.mjs`、`settings.mjs` | 页面各区 | 25/25、35/35、13/13、19/19、52/36 | 清楚 | — |
| `page/local-config.mjs` | `models.json` 的角色、宿主、runner 目录（第 3–8 行 `CATALOG`） | 7/6 | 含糊 | 与 `settings.mjs` 分不清；内容是角色配置，这里又叫 agents |
| `page/index.html`、`page/styles/*.css`、`AGENTS.md`、`CLAUDE.md` | 页面入口、样式、目录说明 | — | 清楚 | — |
| `com.mmw.board` | LaunchAgent 标签 | 35/12 | 清楚 | — |

## 14. `tests/` 套件名

套件清单取自根 `AGENTS.md` `## Commands` 与 `mmw-v2/tests/`。谁读：人与 agent（根 `AGENTS.md`、`TESTING.md` 写明哪些改动跑哪个套件）；程序：各自的 `run.sh`。

| 现名 | 测什么 | 次数 总/现役 | 判断 | 理由 |
|---|---|---|---|---|
| `tests/verify-ticket` | `verify-ticket.py`、`events.py`，另跑 gate-check 的两个 node 套件 | 50/23 | 清楚 | R18 把测状态命令的文件搬到 `tests/mmw`（第 7.6 节） |
| `tests/ui-acceptance`、`write-screen-contract`、`retro`、`exe-release`、`manage-agents-md`、`design-pages` | 同名技能 | 10/6、5/3、5/3、9/3、7/3、6/3 | 清楚 | — |
| `tests/dispatch` | `dispatch.sh`、`models.py`、`status.py`、`tool-guard.py` 等 | 76/39 | 误导 | B2 后 `dispatch` 技能不存在，套件名指向一个没有的东西 |
| `tests/board` | 任务板 | 13/8 | 清楚 | — |
| `tests/liveness` | turn guard 与 watchdog | 13/5 | 清楚 | 取自 `watchdog.py` 第 1 行「layers of liveness」 |
| `tests/relay` | `relay.py`、`ghlist.py` | 27/11 | 清楚 | — |
| `tests/migrations` | 迁移脚本 | 1/0 | 清楚 | — |
| `tests/lib` | 不是套件：共用的检查与 `-k` 解析（`mmw-v2/tests/AGENTS.md` `## Key Conventions` 第 2 条） | 111/18 | 清楚 | — |
| `tests/mmw`（新） | `roles.json`、`anchors.py`、`where`、`ticket.py`、`mode-hook`、`mmw-hook`、`import_component`（R18 第 1.1 节） | 8/0 | 含糊 | 「mmw」多义（第 15.1 节）；内容是 mode 的脚本 |
| `tests/wiring`（新） | 每类连线检查一个必须失败的反例 | 4/0 | 含糊 | 继承 `check_wiring.py` 的比喻 |
| `prompt/tests/` | `render.py` | — | 清楚 | — |

## 15. 跨类别汇总

### 15.1 一词多义（同一个词指不同的东西）

| 词 | 各处的意思（出处） |
|---|---|
| `mmw` / MMW | 整套工具（根 `AGENTS.md` 首段）；`mmw-v2/`；消费仓库 `.mmw/`；label 前缀 `mmw:`；事件标记 `<!-- mmw {…} -->`（`events.py` 第 67 行）；R18 的 mode 技能、`mmw-hook`、步骤指针前缀、`tests/mmw` |
| slot / 槽位 | 产品槽位（`lease.py` 第 124 行、`worker.queued`）；R18 的 `slots.md`（pstack 名字对应表） |
| check | `dispatch.sh check`；`install.sh --check`；`target_config.py --check`；`CHECK:` 行；`ticket.checked`；`.mmw/target.json` 的 `checks`；`--check-only`；R18 `ticket.py --check`；`code-checkers`；`check.sh`、`check_wiring.py` |
| effort | `models.json` 的推理强度；`docs/specs/<effort>/`、`prototypes/<effort>/`；`map-a-large-effort` |
| contract | screen contract；子票 kind `contract`；原则 `the-baseline-is-a-contract`；`release_contracts.py` 的数据结构 |
| map | wayfinder 的地图与 `mmw:map`；`--map N`；`pstack.map` 改写表 |
| dispatch | 技能 `dispatch`；`dispatch.sh`；事件 stage 值 `dispatch`；`fix_dispatch.py` |
| gate | `board/gates.py`；unlazy 的 gate-check |
| judge | 事件 actor `judge`＝watchdog；`PRODUCT_JUDGES`＝oracle 脚本（`verify-ticket.py` 第 88 行）；`MMW_JUDGE_LEASE_OWNER` |
| main | 事件 actor `main`＝orchestrator；`relay.py` 的 `MAIN`；main 分支；`--actor main` 的「main agent」 |
| release | 事件 `ticket.released`（放回认领）；技能 `exe-release`、release manifest |
| change | `define-a-change`（一批票）、`direct-change`（小改动）、`deliver-a-change`（交付）、`promote-a-change`（发布到已安装 checkout） |
| run / work | `run-a-night`、`run-one-ticket`（编排）；`work-a-ticket`（亲手做）；`--run self\|reverify`（判据的一次运行）；`relay.py run`、`watchdog.py run` |
| queue | label 组 Queue（等谁，`issue-tracker.md` 第 39 行）；relay 的唤醒队列 `queue.jsonl` |
| summary | `dispatch.sh summary`（发布并关掉一夜）；`status.py --summary`（只打印） |
| ps | pstack 来源前缀；PowerShell `.ps1`；Unix `ps` |
| draft / drafts | `--draft`（收尾评论草稿）；`--drafts`（票草稿目录） |
| open | `dispatch.sh open`（开夜）、`open-ticket`（开单票 watch）、`spec.opened`（夜开始）；GitHub 的 open issue |
| night | 一次整批运行，「at any hour」（`dispatch/SKILL.md` 第 12 行）；日常词义是夜间。出现 2775/1123 次，是全套最核心的自造词 |

### 15.2 一义多名（同一个东西有几个名字）

| 东西 | 各处的名字 |
|---|---|
| 角色 | role（`roles.json`）；agent（`models.py` `ALLOWED_AGENTS`、`hosts.json` 的 `agent` 键、`local-config.mjs` 的 `agents`）；row（`models.json` `rows`、`models_row`）；label（R18 第 2.2 节 `config get <label>`）；grade（`junior-worker`、`senior-worker`） |
| orchestrator | orchestrator；actor `main`；`MAIN`；「main agent」 |
| 自己拿起的票 | `adopt`；`self-picked-worker`；**Picked up yourself**；`adopted` 字段（`dispatch.sh` 第 1017 行）；`inside-a-ticket.md` |
| 子票 | child（`child.opened`、`mmw:child`、`CHILD_KINDS`）；sub-issue（`--sub-issue`、`sub-issues.md`、GitHub 原名） |
| 产品槽位 | slot；lease（`lease.py`、`leases/`） |
| 只有人能做的事 | human（`ready-for-human`、`human-steps-stay-human`）；person（`person-ticket.md`、`triage-labels.md`「a person」） |
| 出包配置文件 | key（`key.md`、`verify_key.py`）；release manifest（正文）；adapter（`<product>.release-adapter.json`、`--adapter`） |
| 认领 | 步骤 **Claim**、事件 `ticket.claimed`；开关 `--preflight` |
| 产品答案 | product answers（`product-answers.md`）；target（`.mmw/target.json`、`target_config.py`） |
| 心跳 | `beat.json`（relay）；`watchdog.json`（watchdog） |
| Memory | Memory；shared experience（R18 新技能名） |
| 夜 | night（技能文字、`NIGHT SUMMARY`）；spec（事件 `spec.*` 的主语，stage 值 `night`） |
| 角色配置文件 | `models.json`；「agent configuration」（`settings_api.py` 第 1 行）；「model configuration」（`board/AGENTS.md` 第 3 行）；`local-config.mjs`；设置页 `settings.mjs` |

### 15.3 写法不统一

- **Python 文件名**：连字符 9 个（`verify-ticket.py`、`tool-guard.py`、`turn-guard.py`、`boundary-check.py`、`harness-guard.py`、`story-parity.py`、`remove-verifier.py`，R18 新增 `mode-hook.py`、`mmw-hook.py`），下划线 22 个（`issue_tree.py`、`target_config.py`、`pull_design.py`、`board_data.py`、`import_component.py`、`check_wiring.py` 等）。连字符的文件不能 `import`，测试要经 `importlib` 按路径加载（`mmw-v2/tests/AGENTS.md` `## Key Conventions`）。pstack 与 mattpocock 的脚本全部用连字符，但它们没有 Python 模块（第 16 节）。
- **MMW 加进上游目录的文件**：全大写放在技能根（`SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md`、`prototype/EXP.md`，仿 mattpocock），小写放在 `references/`（`to-spec/references/`、`code-review/references/` 等，仿 pstack），小写放在技能根（`prototype/evidence-page.md`）。squash `5b1a4c51` 的上游原文里没有任何 `references/` 目录（`git ls-tree`，本轮）。
- **原则 slug 句式**：MMW 12 条里 2 条祈使句；pstack 23 条里 17 条（第 7、16.2 节）。
- **playbook slug 句式**：MMW 自写 16 个里 14 个是「动词 + 冠词 + 名词」（`define-a-change`、`run-a-night`），pstack 23 个里只有 `authoring-a-skill`、`opening-a-pr` 带冠词，多数是任务类型名词（`bug-fix`、`feature`、`investigation`）。标题同理：MMW「Define a change」是祈使句，pstack「Bug fix」「Feature」是名词。
- **评审简报后缀**：R18 把 `<axis>-reviewer.md` 改成 `review-axes/<axis>.md`；pstack 的同类文件保留 `-reviewer` 后缀（`reflect/references/judgment-reviewer.md`）。
- **子树目录**：`upstream-pstack/`、`upstream-unlazy/`、`upstream-diagram-design/` 带来源后缀，mattpocock 的是 `upstream/`。

### 15.4 改名的代价（按谁读）

| 档 | 名字 | 改名要动什么 |
|---|---|---|
| 只有人与 agent 读 | reference、playbook 标题、原则 slug、mode 节名、技能名（除 `+model` 相关） | 文字与指针；`check_wiring.py` 第 1、2、5 类核对；技能名改动要新会话才生效（R18 H2） |
| 程序按字面读、只在本机 | 脚本文件名、`roles.json` 键、`anchors.py` 登记、`dispatch.sh` 子命令、开关、`board/` 文件、测试套件名、状态文件名 | 调用点、测试、`install.sh`；状态文件只能在没有 watch 开着时改（H5）；`models.json` 的角色键由 `models.py` 第 139–143 行要求恰好四行，改名要迁移本机文件；hook 命令字符串变了 Codex 要重算 `trusted_hash`（根 `AGENTS.md` `## Gotchas` 第 3 条） |
| 外部、长期保存 | 事件名与字段值（GitHub 评论）、label（各仓库 issue）、`.mmw/target.json` 的键与 `delivery` 值、工作树名 `issue-<n>`、子票 kind 写在子票正文首行（`pipeline-issues.md` 第 3 行 ``A `<kind>` child of #<n>.``） | 事件要在 `events.py` 加旧名到新名的别名，否则旧票全部变成 `unreadable`（推断，第 10 节）；label 要逐仓库改；消费仓库要 downstream-note（根 `AGENTS.md` `## Key Conventions` 第 5 条）。`SKILL-SET-RULES.md` `### Vocabulary` 第 3 条：这类名字「is copied verbatim and is not renamed for style」 |

## 16. 上游的命名习惯（供统一句式参考；上游名字不改）

### 16.1 mattpocock（squash `5b1a4c51`，`git ls-tree`，本轮）

- **技能名**：小写连字符，说出一个动作或一个产物，无品牌前缀（唯一例外 `setup-matt-pocock-skills`）。四种句式：
  - `to-<产物>`：`to-spec`、`to-tickets`、`to-questionnaire`；
  - 动名词短语：`diagnosing-bugs`、`resolving-merge-conflicts`、`writing-for-agents`、`grilling`、`domain-modeling`；
  - 祈使动词（加宾语）：`implement`、`triage`、`research`、`teach`、`prototype`、`improve-codebase-architecture`、`grill-me`、`grill-with-docs`；
  - 名词：`code-review`、`codebase-design`、`wayfinder`、`wizard`、`handoff`；口语：`wait-what`。
- **reference**：没有 `references/` 目录；放在技能根，全大写连字符 `.md`，名字说出它承载的分支或产物：`LOGIC.md`、`UI.md`（`prototype` 的两个分支）、`DEEPENING.md`、`DESIGN-IT-TWICE.md`（`codebase-design`）、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`（`triage`）、`HTML-REPORT.md`、`PHASE-BOUNDARIES.md`、`SKILL-MECHANICS.md`。格式文件用 `-FORMAT` 后缀：`ADR-FORMAT.md`、`CONTEXT-FORMAT.md`、`teach` 的 `GLOSSARY-FORMAT.md` 等四份。小写的例外有两类：`tdd` 的 `mocking.md`、`tests.md`；`setup-matt-pocock-skills` 里要原样写进用户仓库的模板（`domain.md`、`triage-labels.md`、`issue-tracker-github.md`），文件名等于它写出的文件名。
- **脚本**：小写连字符，多以动词开头：`diagnosing-bugs/scripts/hitl-loop.template.sh`、`wizard/template.sh`、`misc/git-guardrails-claude-code/scripts/block-dangerous-git.sh`；仓库级 `scripts/link-skills.sh`、`list-skills.sh`、`sync-plugin-version.mjs`。
- **playbook、原则**：没有这两种组件；最接近原则的是 `ask-matt/PHASE-BOUNDARIES.md`。
- **词汇规则**：`SKILL-SET-RULES.md` `### Vocabulary` 第 2 条定的起名顺序——先用领域里意思完全相符的既有术语（baseline、oracle、orchestrator），其次用字典里的普通词，最后才自造词并在首次出现处用一句粗体定义；借来的术语若意思不同（false friend）比自造词更糟。

### 16.2 pstack（`docs/research/code-landing-refs/pstack/`，`plugin.json` 0.15.4）

- **技能名**：短，多为一个词或一句口语：`how`、`why`、`arena`、`swarm`、`recall`、`reflect`、`unslop`、`bro`、`teach`、`tdd`、`architect`、`interrogate`；短语：`figure-it-out`、`show-me-your-work`、`automate-me`、`no-comments`、`blast-radius`；动词加宾语：`create-verification-skill`、`maintain-verification-skill`、`make-bot-ui`；领域：`technical-writing`、`typescript-best-practices`；配置：`setup-pstack`；mode：`poteto-mode`（`<品牌>-mode`，H1「# Poteto mode」）。frontmatter `name` 等于目录名（唯一例外 `make-bot-ui` 的 `name: Make Bot UI`，L7 第 196 行）。
- **playbook**：`playbooks/<slug>.md`，slug 是任务类型名的小写连字符，首行 `### <Name>`，Name 只有首词大写。多数是名词：`bug-fix`、`feature`、`investigation`、`refactoring`、`perf-issue`、`runtime-forensics`、`trace-forensics`、`visual-parity`、`eval`、`hillclimb`、`shipping`、`session-pickup`、`worktree-cleanup`；动名词：`authoring-a-skill`、`opening-a-pr`；祈使：`orchestrate`、`babysit`、`pause-safely`。slug 可以比标题短：`worktree-cleanup` ←「Worktree and simulator cleanup」，`multi-phase-plan` ←「Multi-phase or multi-PR plan」，`authoring-a-skill` ←「Authoring or modifying a skill」。
- **原则**：目录 `principle-<slug>`，23 条 frontmatter 同构，description 全部以「Apply」开头（L7 第 246 行）。slug 17 条是祈使动词短语：`attack-the-premise`、`build-the-lever`、`encode-lessons-in-structure`、`exhaust-the-design-space`、`fix-root-causes`、`guard-the-context-window`、`make-operations-idempotent`、`migrate-callers-then-delete-legacy-apis`、`minimize-reader-load`、`model-the-domain`、`never-block-on-the-human`、`prove-it-works`、`redesign-from-first-principles`、`separate-before-serializing-shared-state`、`sequence-verifiable-units`、`subtract-before-you-add`、`test-behavior-not-implementation`；6 条是名词短语：`boundary-discipline`、`type-system-discipline`、`laziness-protocol`、`foundational-thinking`、`experience-first`、`outcome-oriented-execution`。索引里的显示名每词首字母大写（「**Prove It Works** (**principle-prove-it-works**)」，mode 第 65 行）。
- **reference**：`references/` 下小写连字符，名字说出读者或用途。交给子代理的提示用 `<角色>-prompt.md`：`architect/references/runner-prompt.md`、`interrogate/references/reviewer-prompt.md`、`why/references/investigator-prompt.md`、`synthesizer-prompt.md`、`how/references/explorer-prompt.md`、`explainer-prompt.md`；评审者用 `<角色>-reviewer.md`：`reflect/references/judgment-reviewer.md`、`tooling-reviewer.md`、`divergent-reviewer.md`；模板用 `-template`：`architect/references/rationale-template.md`、`show-me-your-work/references/decision-log-template.tsv`；主题名：`rubric.md`、`epistemics.md`、`design-red-flags.md`、`patterns.md`、`lead-judgment.md`、`synthesizer.md`；按来源分的子目录：`why/references/sources/<来源>.md`；mode 级：`poteto-mode/references/bugbot-triage.md`。
- **脚本**：小写连字符（`poteto-mode/scripts/worktree-audit.sh`、`check-plan.mjs`、`bootstrap.ts`、`show-me-your-work/scripts/log.sh`）；多文件工具一个目录，按职责分文件（`watch-pr/cli.ts`、`policy.ts`、`github.ts`、`render.ts`、`types.ts`，测试 `*.test.ts`；`orch/orch.ts`、`store.ts`）。
- **agent**：`agents/<名字>.md`：`comment-sicko.md`、`poteto-agent.md`。
- **mode 节名**：`## Non-negotiables`、`## Principles`、`## Autonomy`、`## Subagents`、`## Writing the reply`、`## Comments`、`## Playbooks`（`poteto-mode/SKILL.md` 第 13–115 行）。

### 16.3 两家的共同点与 MMW 现状的差距（推断，由上面两节归纳）

- 两家的名字都说出「做什么」或「产出什么」，或说出读者（`*-prompt`、`*-reviewer`）；MMW 名字里说来历（`tracker-additions.md`、`### Imported triggers`）、说比喻（`check_wiring.py`、`driving.md`、`gap.json`）、说宿主机制（`tool-guard.py`）的，都判为含糊。
- 两家的脚本全部连字符；MMW 的 Python 需要能 `import` 的名字，这与照搬连字符冲突，要由改名表定一条。
- pstack 的 playbook 是任务类型名词，MMW 的是祈使短语；pstack 原则多为祈使句，MMW 多为陈述句。改名表要在「照 pstack」与「保留 MMW 现有句式」之间选一种，并对全部 MMW 自写的名字一次统一。

## 17. 本轮读了什么、没读什么

- **读全文或相关段落的**：R18 全文（第 0–17 节与审查记录前 12 条）；`dispatch.sh` 第 1–100、150–200、360–420、4570–4761 行与 22 个子命令函数前的注释；`events.py` 第 1–200、860–900 行；`verify-ticket.py` 第 55–115、4110–4175 行；`statedir.py` 第 1–85 行；`relay.py`、`watchdog.py`、`turn-guard.py` 状态文件与告警的段落；`models.py` 第 25–35、135–145、1200–1235 行；`hosts.json`；本机 `~/.mmw/` 与 `~/.mmw/models.json` 的列表；全部 MMW 自有与 MMW 加进上游目录的 reference 的前三行；全部 MMW 脚本的文件头；`board/page/*.mjs` 的开头；`mmw-v2/tests/AGENTS.md`、`mmw-v2/board/AGENTS.md`；`docs/agents/triage-labels.md`、`issue-tracker.md` `## Three label sets`；`SKILL-SET-RULES.md` 中含「name / vocabulary / term」的段落；mattpocock squash `5b1a4c51` 的文件树；pstack 的目录树、23 份 playbook 的首行、mode 的节名与路由表；L7 与 R13 中关于命名的行；R20a、R20b 中关于命名的行。
- **没有读全文的**：多数 reference 与脚本只读了开头，「是什么」一列据此写，个别判断（如 `harness-guard`、`extract_skeleton`）依据文件首段；`docs/contexts/*/CONTEXT.md` 的词条没有逐条核对，某个名字若在词表里已有定义，「自造词」的判断要以词表为准；次数的模式说明见第 1 节，常用词的计数只是量级。
