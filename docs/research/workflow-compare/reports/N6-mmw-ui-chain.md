# N6 — MMW 界面链单元清点：ui-acceptance + design-pages + write-screen-contract

本文只做事实清点，不做归置决定。单元范围：`mmw-v2/skills/ui-acceptance/`、`mmw-v2/skills/design-pages/`、`mmw-v2/skills/write-screen-contract/` 的全部受 git 跟踪文件（共 29 个，`git ls-files` 核实；工作树里另有 `__pycache__/*.pyc`，未被跟踪，不计入）；`docs/contexts/ui-acceptance/CONTEXT.md`；ADR 0002、0004、0011、0028、0029、0030；三份与本单元交接的 reference：`mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`、`mmw-v2/upstream/skills/engineering/implement/references/writing-interface-code.md`、`mmw-v2/upstream/skills/engineering/code-review/references/ui-reviewer.md`。

## 0. 读法与来源说明

- **完整读过的文本**：三个技能的 `SKILL.md` 与全部 reference（逐行）；`docs/contexts/ui-acceptance/CONTEXT.md`（417 行，全读）；六份 ADR（全读）；上面三份交接 reference（全读）；`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（176 行，全读）；`mmw-v2/merge-notes/README.md`（全读）；`mmw-v2/merge-notes/to-tickets.md` 第 82–182 行、`implement.md` 第 29–34、145–152、211–270 行、`code-review.md` 第 52–61、100–120、179–209 行（本单元相关各节全读，其余节只看了标题）。
- **脚本**：读了每个脚本的文件头注释、参数定义（`argparse` 或手写 `argv` 判断）、`main` 的分派与每个 `return <码>`，以及个别与本报告结论直接相关的函数（`pull_design.py` 的 `run`、`main`、`PullRefused`、`design_check_lines`、`refusal_text`；`boundary-check.py` 的 `main`/`_main`；`lease.py` 的模块注释、`judge_run`、`main` 的返回码；`target_config.py` 的 `FIELDS`；`harness-guard.py` 的 `main`；`journey.py` 的 `main`；`story-parity.py` 的参数与 `_load` 导入）。**没有逐行读实现**：`story-parity.py`（701 行）、`design_render.py`（627 行）、`pull_design.py`（1670 行）、`lease.py`（746 行）、`lint_screen_contract.py`（577 行）、`extract_skeleton.py`（244 行）的比较与渲染算法本体未读；凡涉及这些算法的描述来自其文件头或 reference，标「据文件头」。
- **没有运行任何脚本**（包括 `--help`）；只运行了只读的 `git log`、`git show`、`git ls-files`、`grep`、`nmem m search/show`。
- **线索材料**：`docs/research/workflow-compare/reports/` 的 M1、I1、I3、I5、T1、T3、C1、C3；`docs/reviews/2026-09-23-skill-set/汇总.md`；`docs/reviews/2026-09-28-lightweight/ui-acceptance.md`、`design-pages.md`、`write-screen-contract.md`（各读「定稿」一节）；`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`；`docs/research/mmw-structure/2026-09-06-handoff.md`（只 grep）。采用的每条结论都回原文核实过，核实结果列在第 9 节。
- **实地证据**：Nowledge Mem 的 retro 记忆 `mmw-retro-chancheuklap__multi-model-workflow-spec-444/445/446/447/555`（读了 `## Problems observed`）、用户裁定记忆 `415f96d0`、提案记忆 `5a337408`；相关提交说明用 `git show -s` 读。

「推断」表示我从原文推出而原文未写明；「未确定」表示读不到或读了也定不下。

---

## 1. 部件清单

### 1.1 ui-acceptance（`mmw-v2/skills.txt` 第 39 行 `self/ui-acceptance`：本仓自有技能，不在上游 subtree 中）

| 文件 | 行数 | 是什么 | 给谁用 |
| --- | --- | --- | --- |
| `SKILL.md` | 38 | 定义 **product under test** 与四个 **oracle**；`## Find your moment` 分派表；`## Five rules while the product is running` | 任何要启动、触达、观察运行中产品的 agent；`dispatch.sh` 第 109 行 `PRODUCT_RULES` 把这一节点名写进每个 worker 的启动 prompt（第 1949 行） |
| `references/story-parity.md` | 118 | story oracle 的产品侧约定（story 页、story adapter、`[data-story-root]`）、两侧读取的事实表、element parity 判定规则、`DIFF` 行格式、负控制 | 建 story service/adapter 的 worker（contract ticket、page ticket）；读 `DIFF` 行修产品的 worker |
| `references/boundary-check.md` | 38 | `boundary-check.py` 的两遍规则；`## Selecting one row's test`（按行选中唯一测试）；`## The four-column boundary test` | 写 boundary 判据的切票 agent（经 `cutting-interface-tickets.md` 指过来）；写四列测试、读 `MISS` / `GREEN WITHOUT INTERACTION` 的 worker |
| `references/journey.md` | 58 | journey 脚本的输入与要求、fault-injection switch、负控制、`JOURNEY FAILED` 怎么读 | 写 journey 脚本或故障开关的 worker（contract ticket、critical-flow ticket）；读 `JOURNEY …` 行的 worker |
| `references/harness-guard.md` | 33 | back door 允许存放的位置、`HARNESS LEAK` / `HARNESS DESIGN PAGE` 的修法 | 读这两行的 worker；实现 harness guard 的 contract ticket worker |
| `references/product-answers.md` | 96 | 每个 `.mmw/` 回答必须保证的不变要求；`start`/`stop`/`stories`/`journeys`/`harness_markers`/`checks` 各字段的理由；`.mmw/` 目录形状；真钥匙规则 | 填 `.mmw/target.json` 与 `.mmw/harness/` 的 agent（主要是 contract ticket worker） |
| `scripts/story-parity.py` | 701 | story oracle：按 `data-ui` id 比较产品 story 与设计页；`--render-only` 只出设计侧数值；PEP 723 依赖 Pillow、playwright、psutil、pyyaml | `CHECK:` 行（经 `verify-ticket.py`）；page ticket worker 手跑 `--render-only`；UI axis reviewer 手跑 `--out` |
| `scripts/boundary-check.py` | 148 | 把一条产品测试命令跑两遍，第二遍加 `MMW_NEGATIVE=1` 必须失败 | `CHECK:` 行 |
| `scripts/journey.py` | 311 | 在 lease 下起产品、跑 journey 脚本、停产品；`--break` 时第二遍只坏一个 operation | `CHECK:` 行 |
| `scripts/harness-guard.py` | 282 | 扫 git 跟踪（及将跟踪）的文件，找 `MMW_` 读取与 `harness_markers` 字串的越界位置 | `CHECK:` 行（批次最后一张票） |
| `scripts/target_config.py` | 287 | `.mmw/target.json` 的字段表 `FIELDS`（唯一定义处）、`--check`/`--validate`、`discover`、`command_env` | 填答案的 agent；`journey.py`、`story-parity.py` 导入；`to-spec` 与 `dispatch` 的 `night.md` 第 55 行引用 `--check` |
| `scripts/lease.py` | 746 | lease（每个 ticket worktree 一个 slot：端口段 + 数据目录）；动词 `claim`/`run`/`release`/`remove-instance`/`list`/`count` | `verify-ticket.py`（`load_lease`）、`dispatch.sh`（`release --stop`、`remove-instance`）、`journey.py`、`boundary-check.py`、`story-parity.py`；人或 agent 手起产品用 `lease.py run --` |
| `scripts/design_render.py` | 627 | 设计侧离线渲染库：baseline server、包装页、截图、`[data-ui]` 读取器；自己不判定 | `story-parity.py`、`write-screen-contract` 的 `extract_skeleton.py`、`design-pages` 的 `pull_design.py` 三处导入 |
| `scripts/pixel_diff.py` | 45 | 写像素差异图作证据；当命令运行时退出 2 并指向 `story-parity.py` | `story-parity.py` 导入 |
| `scripts/refusal.py` | 52 | 一条拒绝消息的三段结构（what / why / next step）与 `REPORT_BLOCKED` 句；256 字符上限 | 本技能各脚本；也被 `dispatch/scripts/tool-guard.py` 第 58–62 行、`retro/scripts/retro.py` 第 28、48 行、`pull_design.py` `refusal_text` 跨技能导入 |

### 1.2 design-pages（`skills.txt` 第 36 行 `self/design-pages`）

| 文件 | 行数 | 是什么 | 给谁用 |
| --- | --- | --- | --- |
| `SKILL.md` | 26 | 目的、`## Find your moment`、宿主能力门槛（须有 Claude Design MCP 工具）、`## The state list` 的定义 | 白天、有 Claude Design MCP 工具的会话；「a dispatched worker never runs it」 |
| `references/edit-pages.md` | 33 | 建项目（`## Create the project`）、design system 变更后刷新 `_ds/`、`task.md` 交接法、`## Sign-off`、`## Next` | 建 Claude Design 项目或接受定稿的会话 |
| `references/draw.md` | 13 | 处理排队评论；本会话画页的附加规则 | 用户把评论 Send to Claude 或要求本会话画页时 |
| `references/pull.md` | 49 | pull 的时机、四步、首次 pull 后拆原型脚手架、pull report 设计问题的处理、`## Reached from here` 分派、`contract` child 的收尾 | 用户定稿后，或处理点名本文件的 `contract` child 时 |
| `references/design-system.md` | 46 | design system 是什么、何时从什么建、由 Claude Design 内的 agent 建（五步）、已有产品迁入 | 被要求建 design system 或迁入已有产品时 |
| `references/template-project-claude-md.md` | 52 | 写进页项目根目录 `CLAUDE.md` 的整块模板：页名、`scene`、`## Page data`、`$preview`、`data-ui`、`task.md`、`## Files` | 本会话写入；**读者是 Claude Design 项目内的 agent**，每次对话都读 |
| `references/template-design-system-claude-md.md` | 45 | 写进 design system 项目 `CLAUDE.md` 的模板（三个待填字段） | 同上，读者是 design system 项目内的 agent |
| `scripts/pull_design.py` | 1670 | 把一个 Claude Design 项目拉成完整 design package；写 `scenes.json`、`design-manifest.json`、`README.md`、`pull-report.md`；原子替换目标目录 | pull 的第 2 步 |
| `scripts/check_editable_selectors.py` | 112 | 找出 Claude Design 编辑器点不中的 CSS 选择器；退出 1 有、0 无 | `pull_design.py` 以模块导入（第 1052–1054 行），结果进 pull report `设计检查` |

### 1.3 write-screen-contract（`skills.txt` 第 46 行 `self/write-screen-contract`）

| 文件 | 行数 | 是什么 | 给谁用 |
| --- | --- | --- | --- |
| `SKILL.md` | 121 | 目的；`## Inputs`；七步；`## Re-runs`；`## Done when`；`## Next` | design package 落地后写 spec 前的会话（wayfinder 的 alignment ticket 或普通对话）；`to-spec` 发现未对齐行时退回到它的 **Reverse sweep** |
| `references/screen-contract-format.md` | 138 | screen contract 文件格式：顶层键、`pages`/`scenes`/`viewports`/`locale`/`states`/`retired_ids` 规则表、行的两个示例、列规则表、cross-component row | 写合同的 agent（「Read it before step 2」）；文件第 3 行自称也被 `to-spec`、`to-tickets`、`implement`、`code-review`、story oracle、boundary check 与 lint 读 |
| `scripts/extract_skeleton.py` | 244 | 离线渲染 design package 每个 scene，写 skeleton（每个 (页, `data-ui` id) 一条） | 第 1 步 |
| `scripts/lint_screen_contract.py` | 577 | 按 skeleton 与可选 `openapi.json` lint 合同；每次先打印 `RETIRED` 行 | 第 7 步 |
| `scripts/dump_openapi.py` | 28 | 调 FastAPI app factory 写 OpenAPI 文档 | `## Inputs` 第三条，仓库没有自己导出器时 |

### 1.4 单元内其余文件

| 文件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `docs/contexts/ui-acceptance/CONTEXT.md` | 本界定上下文的术语表，97 条，六节：The design side / The oracles / Screen contract / Product answers and the scripts that read them / The lease / Refusals；其中 10 条 `_Home_` 指向上游 `prototype` 技能（prototype、leaf directory、effort、scaffolding、shell、experiment round 等） | 改词汇的维护者；`docs/agents/domain.md` 要求探索代码前先读 |
| `docs/adr/0002`、`0004` | 界面 QA 绑 DESIGN.md 格式、设计系统可信度由校验定 | 已挂起（`docs/adr/README.md` 第 54 行：技能在 `deprecated/ui-qa`） |
| `docs/adr/0011` | 界面等价在组件级离线判定，整机只跑少量旅程 | 维护者 |
| `docs/adr/0028` | element parity、App 页进 story、四列 boundary test、product answers 只写不变要求、judge 不遮不藏、journey 第二遍坏一个接口 | 维护者 |
| `docs/adr/0029` | Claude Design 是唯一设计源，仓库副本只由 pull 写入 | 维护者 |
| `docs/adr/0030` | design system 由 Claude Design 内的 agent 从产品代码提炼，只装外观；设计页不加载产品代码 | 维护者 |
| `to-tickets/references/cutting-interface-tickets.md` | 152 行；`# Tickets from a screen contract`：四种判据形状、Seam/Owns、五种票（design-system、contract、component page、app page、critical-flow）、共用 journey helper、reaction ticket | 有 screen contract 的 spec 切票时（`to-tickets/SKILL.md` 第 46 行与模板 `## Read first` 第 174 行两处指来） |
| `implement/references/writing-interface-code.md` | 57 行；page ticket 的两份基线、写码前取设计值、写产品、就地修、设计侧有缺陷时开 `contract` child、一条代码路径 | page ticket 的 worker（`implement/SKILL.md` 第 16 行：`## Read first` 列出 screen contract 时读） |
| `code-review/references/ui-reviewer.md` | 37 行；UI axis：看 story 截图找 element parity 覆盖不到的问题，三类 finding | UI axis 子 agent；`code-review/references/session.md` 第 21 行：票有 story criterion 时才跑 |

单元外但直接相关、我只读了相关行的：`mmw-v2/tests/ui-acceptance/`（9 个测试文件）、`mmw-v2/tests/design-pages/`（2 个）、`mmw-v2/tests/write-screen-contract/`（2 个）只列了目录，未读；`mmw-v2/downstream-notes/` 中 449、450、453–456、472、473、476、491、492、494、514 与本单元相关，只读了 453 的前 19 行。

---

## 2. 内容分类表

类型缩写：**顺** 顺序；**做** 做法；**理** 带理由的规则；**命** 命令与接口；**分** 重入与分派；**格** 格式与模板；**目** 目的与立场；**沉** 沉积。一段有两种性质时写「主 / 次」。

### 2.1 ui-acceptance

| 文件 · 段 | 类型 | 谁、何时读；每次还是分支 |
| --- | --- | --- |
| `SKILL.md` frontmatter `description` | 分 | 每个宿主启动时扫描进系统提示；触发词：填 `.mmw/target.json`、读 `DIFF`/`MISS`/`JOURNEY`/`HARNESS` 行、给 run 端口、写 page ticket 代码之前 |
| `SKILL.md` 第 8 行定义段（product under test、四个 oracle、`lease.py`） | 命 / 目 | 每次加载都读 |
| `SKILL.md` 第 10 行「During a night these oracles are the only eyes on a UI…never the check.」 | 目 / 理 | 每次加载都读；针对「红了就放宽判据」的诱惑 |
| `SKILL.md` 第 12 行「A criterion names an oracle bare; run one by hand as `scripts/<name>`.」 | 命 | 每次 |
| `SKILL.md` `## Find your moment`（8 行表） | 分 | 每次；把读者送到七个时刻，其中两行送出本技能（`implement` 的 `writing-interface-code.md`、`to-tickets` 的 `cutting-interface-tickets.md` **Criterion shapes**） |
| `SKILL.md` `## Five rules…` 引言（第 30 行） | 理 | 每个要碰产品的 worker；`PRODUCT_RULES` 让每个 worker 在碰产品前读 |
| 规则 1「Never end a process you did not start」 | 理 / 命 | 同上；「another run's product looks exactly like a stuck one」是理由；「Your shell refuses kill…」陈述 `tool-guard.py` 的 `ENDS_A_PROCESS`、`XARGS_KILL`（第 173–174 行，已核实） |
| 规则 2「Never start the product outside the lease」 | 理 / 命 | 同上；「The script refuses without a lease」指的是消费仓库自己的 `start`（`product-answers.md` `start` 条要求它这样做） |
| 规则 3「Never complete a human step by hand」 | 理 | 同上；理由「satisfying it makes a broken automation look healthy, and the next run has no person in it」 |
| 规则 4「When the product cannot be reached…」 | 理 | 同上；与 `refusal.py` 的 `REPORT_BLOCKED` 句同义（见第 4 节） |
| 规则 5「A fault in the pipeline itself…」 | 理 | 同上 |
| 第 38 行「Reporting blocked…goes through an event…A worker opens a `fault` child, as the `implement` skill says, and stops.」 | 理 / 命 | 同上；理由是 relay 只因事件唤醒人 |
| `story-parity.md` 第 3–7 行 | 分 | 两种读者各自一节：建 story 的读 **The story page the product serves**，修失败的读 **The DIFF line** |
| `## The story page the product serves` | 做 / 命 / 理 | contract ticket worker（其 **Read first** 点名此节）与每张 page ticket worker（`writing-interface-code.md` **Write the product** 指来）；分支读（只建 story 的时刻）。含 URL 形状 `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`、`[data-story-root]` 位置、scene data 与 `scenes.<name>.input`、「a scene stands for a state, so the clicked object needs no data of its own」 |
| `## The two sides` | 命（事实表） | page ticket worker 在 `--render-only` 后读 values JSON 时（`writing-interface-code.md` 第 15 行指来）；修 `DIFF` 的 worker |
| `## Element parity` | 命（判定规则） | 修 `DIFF` 的 worker；含 2 px 容差、`parent`/`position` 的判定条件及其理由（「does not report a later element merely pushed…」） |
| `## The DIFF line` | 格 / 做 / 理 | 读到 `DIFF` 行的 worker；「Fix the product component, not the story page…」 |
| `## Negative controls` | 命 | 读到 `NEGATIVE CONTROL FAILED` 的人 |
| `boundary-check.md` 第 3 行 | 命 | 复述脚本头（见第 4 节） |
| `## Selecting one row's test` | 做 / 理 / 顺 | 切票 agent 写 boundary 判据时（经指针）；worker 命名测试并跑一次 `--run` 时；两次手跑有先后（发布前改名跑一遍必须非零；写好测试后恰好跑一个） |
| `## The four-column boundary test` | 做 / 理 / 格 | 写四列测试的 page ticket worker、建 interaction helper 的 contract ticket worker；「Mocking the gateway is the allowed seam. Lower than the gateway…higher…」是理由；cross-component row 在整页组合处断言 |
| `harness-guard.md` 第 3–19 行 | 理 | 读到 `HARNESS …` 行或实现 guard 的人；「a back door opened for automated acceptance that ships to a customer's machine」；禁止拼接名字绕过（`process.env["MMW_" + "NEGATIVE"]`） |
| `## What it reads` | 命 | 同上 |
| `## Exit codes` | 命 / 做 | 读到退出码 1 的人；只保留退出 1 及修法 |
| `journey.md` 第 3–8 行 | 目 | 「There are few of them on purpose…money, sign-in, and one submit chain」 |
| 第 10–12 行 | 分 | 写脚本的读前两节，读输出的读后两节 |
| `## What the script gets, and what it must be` | 命 / 做 / 理 | 写 journey 脚本的 worker（contract ticket 的 smoke journey、critical-flow ticket）；「End by reading the result back from another page」带理由 |
| `## The fault-injection switch` | 命 / 理 | 实现开关的 worker（第一张 critical-flow ticket）；`BREAK ARMED <METHOD> <route>`；「The switch lives in the product because…」 |
| `## The negative control` | 理 / 命 | 同上与读输出者；`JOURNEY LEFT THE PRODUCT UP` |
| `## Exit codes` | 做 | 读到 `JOURNEY FAILED` 的人（一句） |
| `product-answers.md` 第 3–5 行 | 分 | 填答案的 agent |
| `## What every product answer must guarantee`（8 条） | 理（不变要求） | contract ticket worker（**Read first** 点名本文件）；ADR 0028「product answers 只写不变要求」的落点 |
| `## What the repository answers`：`start` | 命 / 理 | 同上；含幂等、`SO_REUSEADDR` 端口检查（理由：`TIME_WAIT`）、`MMW_DATA_DIR` 重定向、无 lease 拒绝 |
| 「Servers under a burst」 | 理 | 同上；至少 64 个待接连接 |
| `stop`、`stories`、`journeys`、`harness_markers`、`checks` | 命 / 理 | 同上；`checks` 的形状与 `MMW_BASE_REF` |
| `## .mmw/ directory` | 格 | 同上 |
| `## Rules`（真钥匙） | 理 | 同上；涉及钱与真实客户 |

### 2.2 design-pages

| 文件 · 段 | 类型 | 谁、何时读；每次还是分支 |
| --- | --- | --- |
| `SKILL.md` `description` | 分 | 宿主启动扫描 |
| 标题行与第 8 行 | 目 | 每次；「The user designs in Claude Design, with the agent inside it」 |
| 第 10 行「What this skill pulls is copied exactly…how they look is the user's call.」 | 目 / 理 | 每次；划分：约定归本会话把关，好不好看归用户 |
| `## Find your moment`（4 行表） | 分 | 每次 |
| 第 21 行宿主能力门槛 | 理 | 每次；没有 Claude Design MCP 工具就停；dispatched worker 不运行 |
| `## The state list` | 格（定义） | 每次；定义「the state list」在哪两个位置，其余文件只写这个名字 |
| `edit-pages.md` `## Create the project` | 做 / 顺 | 建项目的分支；终态清单 + 一个 `finalize_plan` 让用户只批一次；`ui-ids.md` 收集法（「ids read from `scenes.json` alone miss elements that carry no text」是理由） |
| `### After the design system changes` | 顺 / 命 | design system 变更后的分支；`list_files`/`delete_files`/`copy_files` |
| `## Talking to the agent inside Claude Design` | 做 / 理 | 每次要让项目内 agent 干活时；`task.md` 机制，「So the user never composes instructions」 |
| `## Sign-off` | 理 | 定稿时；只由 pull 写 design package，不用「Handoff to Claude Code」导出 |
| `## Next` | 分 / 理 | 定稿后；「its report is the convention check」 |
| `draw.md` `## Comments` | 做 | 评论排队的分支 |
| `## When this session draws` | 做 / 理 | 用户要求本会话画页的分支；`if_match` 防覆盖用户刚在编辑器里的修改 |
| `pull.md` `## When` | 理 | pull 分支每次；「Do not replace the design package while a worker is running a ticket」 |
| `## Steps` 1–4 | 顺 / 命 | pull 分支每次；`MMW_DESIGN_PREVIEW_URL` 不打印不落盘；「the command exits 0 whatever the report finds」；`设计检查` 中哪些不是缺陷 |
| `## After the first pull` | 做 | 只有首次 pull |
| `## Design problems in the report` | 理 / 分 | 报告有问题时；两支：design ticket 还开着 / 已进入实现（开 `contract` child）；`覆盖` 与 `本地改过的说明` 也要处理 |
| `## Reached from here` | 分 | pull 分支每次；按「合同是否存在」再按 `改动分类` 三选一 |
| `## A contract child answered by this pull` | 顺 / 命 | 只有回答 `contract` child 的 pull；`dispatch.sh route … fixed`、票移回 `ready-for-agent`、`dispatch.sh resume` |
| 末句「Git is the design's version history; Claude Design keeps none.」 | 理 | 同上（事实兼理由） |
| `design-system.md` 开头 | 格（定义） | design system 分支 |
| `## What it is for` | 目 | 判断值不值得建时 |
| `## When, and from what`（3 行表） | 分 / 理 | 同上 |
| `## Who builds it` 1–5 | 顺 / 命 / 做 | 建 design system 分支；第 5 步验收标准 |
| `## After the design system changes` | 分（指针） | — |
| `## An existing product` 1–4 | 顺 | 已有产品迁入分支 |
| `template-project-claude-md.md` 第 1–3 行 | 做 | 本会话建项目时 |
| 围栏块（`# Page conventions` 及其 7 节） | 格 / 理 | 写进 Claude Design 项目后，**项目内 agent 每次对话都读**；`## Page data`、`## Files` 带理由（「would make acceptance compare the product with itself」） |
| `template-design-system-claude-md.md` 字段说明 | 做 | 本会话 |
| 围栏块（Sources / What it holds / Unification / `task.md` / Done when） | 格 / 理 | design system 项目内 agent 每次对话 |

### 2.3 write-screen-contract

| 文件 · 段 | 类型 | 谁、何时读；每次还是分支 |
| --- | --- | --- |
| `SKILL.md` `description` | 分 | 宿主启动扫描 |
| 第 8 行（两份基线的分工） | 目 | 每次 |
| 第 10 行「Every row becomes a requirement a ticket owns…do not fill in the plausible default…」 | 目 / 理 | 每次 |
| 第 12 行指针、第 14 行 `<scratch>` 与「Some hosts refuse `uv run … $VAR`」 | 分 / 做 | 每次 |
| `## Inputs` | 格 / 命 | 每次；`dump_openapi.py` 与手写 `openapi.json` 两条退路 |
| `## Steps` 引言（第 25 行） | 顺 / 理 | 每次；「Steps 2 to 5 are four passes over the same rows」，只有 1 在前、7 在后是真依赖 |
| `### 1.` | 顺 / 命 | 首跑与重跑；`extract_skeleton.py`、Chromium 安装命令 |
| `### 2.` | 做 / 理 | 每次；`mount` 是声明不是推导；一个控件按状态分行；禁用态是一行 |
| `### 3.` | 做（「the ones people get wrong」） | 每次；`shows`/`calls`/`source` 的易错点（与格式 reference 列规则重叠，见第 4 节） |
| `### 4.` | 理 / 做 | 每次（有 App 页时）；「the App row is the only place it gets an owner and a boundary test」 |
| `### 5. Reverse sweep` | 目 / 做 | 每次；`to-spec` 按此标题名回指 |
| `### 6.` | 做 / 理 | 每次；「this is the one judgement in this skill that is theirs…Expect a handful of entries, not dozens」 |
| `### 7.` | 命 | 每次 |
| `## Re-runs` | 分 / 理 | 重跑分支；按 `改动分类` 或 spec 决定变化分两支；「Row ids are never renumbered or reused」带理由 |
| `## Done when` | 做（完成标准） | 每次 |
| `## Next` | 分 | 每次；wayfinder / 首次 / 重跑三路 |
| `screen-contract-format.md` 第 3–7 行 | 目 / 格 | 写合同的 agent 每次；其他技能读格式时 |
| `## Top level`（YAML） | 格 | 同上 |
| `## Pages, scenes, viewports, locale, states, retired_ids`（表） | 格 / 理 | 同上；`viewports` 与 media-query 断点相等时「compares two reflows and verifies nothing」 |
| `## A row` 与两个示例 | 格 | 同上；示例用 notes app（符合 SKILL-SET-RULES `### Examples`） |
| `## Column rules`（表） | 格 / 理 | 同上；`source` 列「A user story … is an audit trail no worker ever reads」 |
| 第 115 行两句（页无行是错、反向扫 OpenAPI） | 命（lint 规则） | 同上 |
| `## A cross-component row` | 格 / 命 | 有 App 页时；region 的定义与 lint 的归属判定 |

### 2.4 三份交接 reference

| 文件 · 段 | 类型 | 谁、何时读 |
| --- | --- | --- |
| `cutting-interface-tickets.md` 第 3–5 行 | 格（定义 **page ticket**） | 切票 agent，spec 有 screen contract 时（分支） |
| `## Criterion shapes`（四种 `CHECK:`/`EXPECT:`） | 格 / 命 | 同上；也是 `ui-acceptance` `## Find your moment` 与 SKILL-SET-RULES `### Paths` 指向的唯一处 |
| 「A layer with no precedent yet」 | 顺 | 新产品：先切 contract ticket |
| `## Seam and Owns on these tickets` | 做 / 格 | 同上；按判据形状给出观察层；design page 永不进 **Owns** |
| `## design-system ticket` | 做 / 理 / 顺 | 有 `_ds/` 且产品缺这些样式时；「the second exception to vertical slicing」 |
| `## contract ticket` | 格（交付清单）/ 理 / 顺 | 同上；静态守卫与 harness guard 的判据放批次最后一张（理由：扫整棵树） |
| `## component page ticket` | 做 / 理 | 同上；`next` 是别页 scene 的行怎么断言 |
| `## app page ticket` | 做 | 同上；**Owns** 是 composition module |
| `## critical-flow ticket` | 做 / 理 | 同上；阻塞边从流程的行推导 |
| `## Shared journey helper` | 做 | 两张以上 journey 票时 |
| `## reaction ticket` | 理 | 同上；与 UI axis 按「render 看得见与否」分界 |
| `writing-interface-code.md` 第 3 行 | 理 | page ticket worker，每张 page ticket 都读 |
| `## Before the first line` | 顺 / 命 | 同上；`story-parity.py --render-only` |
| `## Write the product` | 顺 / 理 | 同上；story criterion 是 red-before-green 的声明例外（点名 `tdd`） |
| `## Fix in place` | 做 / 理 | 同上；先查设计值是否合理再抄 |
| `## When the design side is the defect` | 分 / 命 / 格 | 设计侧有缺陷的分支；`verify-ticket.py <n> --sub-issue contract <file>`；第二行固定中文句 |
| `## One code path` | 理 | 同上 |
| `ui-reviewer.md` 第 3 行 | 目 | UI axis 子 agent，仅票有 story criterion 时 |
| `## 1.` | 命 / 顺 | 同上 |
| `## 2.`（三类） | 格 / 理 | 同上 |
| `## 3. Report` | 格 | 同上；「Under 400 words」 |
| `## What is not yours` | 理 | 同上；与 story criterion、reaction ticket 分界 |

### 2.5 CONTEXT.md 与 ADR

| 文件 · 段 | 类型 | 谁读 |
| --- | --- | --- |
| `CONTEXT.md` 六节 97 条 | 格（定义），部分 `_Avoid_` 行记录旧名 | 维护者、改词汇者；worker 夜里一般不读（推断：无 prompt 或技能指 worker 读它） |
| ADR 0002、0004 | 沉（已挂起的决定） | 维护者 |
| ADR 0011、0028、0029、0030 | 决定记录（按用户 CLAUDE.md 第 13 条，决定类文件本就记录历史） | 维护者；技能正文不指向这几份 ADR（`grep` 核实：三个技能正文与 reference 中无 `docs/adr` 字样；`ADR` 一词只出现在 `write-screen-contract` 作为合同行 `source` 允许的出处形状 `ADR-<nnnn>` 与 `## Inputs` 的「Where a resolution names an ADR」），只有 `CONTEXT.md` 的 **`DESIGN.md`** 条 `_Home_` 指 ADR 0029 |

**沉积检查**：三个技能正文与 reference 中没有找到带日期的实测、历史或「no longer」类语句（逐行读过）。沉积全部在脚本头：`lease.py` 第 28–36 行「On 2026-09-05 five workers shared three fixed ports」、`refusal.py`「On 2026-09-05 three workers…」「Grok Build clips a deny reason at 256 characters…(2026-08-29)」、`target_config.py` `command_env` 文档串、`journey.py` 头部引用 ADR 0008——SKILL-SET-RULES `### Redundancy and bloat` 的 Sediment 表把「a dated measurement」的归宿定为 script header，所以这些是合规位置。

---

## 3. 连线

### 3.1 对外交接（产出 → 读者）

| 本单元产出 | 位置 | 谁读 | 出处 |
| --- | --- | --- | --- |
| Claude Design 项目 `CLAUDE.md`、`task.md`、`state-list.md`、`ui-ids.md`、`_ds/` 副本 | Claude Design 服务端 | 项目内 agent；用户说 `开始` / `继续` | `edit-pages.md` `## Create the project`、`## Talking to the agent…` |
| design package：页面与依赖、`scenes.json`、`design-manifest.json`、`README.md`、`pull-report.md` | `prototypes/<effort>/claude-design/`，与报告一起提交 | `write-screen-contract`（baseline）、`story-parity.py`（设计侧）、`extract_skeleton.py`、page ticket worker（**Read first** 基线）、UI axis、`contract ticket` 的 design-system 票（`_ds/`） | `pull.md` `## Steps`；`pull_design.py` `run` |
| `pull-report.md` 的 `改动分类` | 同上 | 本会话决定下一个技能；`to-spec` 的 `references/revising-a-spec.md` 第 9 行 | `pull.md` `## Reached from here` |
| `contract` child 的收尾：`child.closed`（经 `dispatch.sh route … fixed`）、`dispatch.sh resume` | tracker 事件；worker 会话 | 夜里被挂住的 worker | `pull.md` `## A contract child answered by this pull` |
| screen contract | `docs/specs/<effort>/screen-contract.yaml` | `to-spec`（第 2 步整份读，未对齐即停）、`to-tickets`（`rows:` 行、`pages.<page>.component`）、`verify-ticket.py --lint`（`lint_screen_contract()` 函数，第 3409 行）、`story-parity.py`（`--contract`）、page ticket worker、`code-review` Spec axis | `screen-contract-format.md` 第 3 行；`to-spec/SKILL.md` 第 22 行 |
| gap list | `<scratch>/gap-list.md`（临时） | 用户（grilling） | `SKILL.md` `### 6.` |
| 四种 oracle 输出行（`STORY OK`/`DIFF`/`NEGATIVE CONTROL FAILED`；`BOUNDARY OK`/`MISS`/`GREEN WITHOUT INTERACTION`；`JOURNEY …`；`HARNESS …`） | stdout | `verify-ticket.py` 按 `EXPECT:` 判；worker 读修法 | 各脚本头 |
| `--render-only` 的 values JSON 与截图 | `--out/values/<mount>/<scene>-<W>x<H>.json`、`--out/media` | page ticket worker | `story-parity.py` 头；`writing-interface-code.md` |
| lease 注册与六个 `MMW_` 变量 | `MMW_HOME/leases` | `.mmw/target.json` 声明的每条命令 | `lease.py` 头 |
| `worker.queued` 事件（由 `verify-ticket.py` 在 `lease.Full` 时写，不由本单元脚本直接写） | ticket 评论 | relay 唤醒等槽位的 worker | `verify-ticket.py` 第 1758–1808 行（已核实） |

### 3.2 点名调用的技能

- `ui-acceptance` → `implement`（`## Find your moment` 第 1 行、第 38 行开 `fault` child）、`to-tickets`（第 3 行）、`dispatch`（第 38 行提到 relay）。
- `design-pages` → `prototype`（`## The state list`、`pull.md` 第 2 步 `<effort>` 定义、`## After the first pull`）、`write-screen-contract`、`dispatch`（`reverify`、`route`、`resume`）、`verify-ticket`（`--sub-issue contract`）、`wayfinder`。
- `write-screen-contract` → `design-pages`（输入）、`wayfinder`、`to-spec`、`to-spec` 的 `references/revising-a-spec.md`、`ui-acceptance`（格式 reference `on_failure` 列提到四列 boundary test）。
- 反向点名本单元的：`prototype/UI.md` 第 121 行、`ask-matt/SKILL.md` 第 21 行、`wayfinder/references/interface-and-remake.md` 第 7–9 行、`to-spec/SKILL.md` 第 22、82、94 行、`to-spec/references/revising-a-spec.md` 第 9 行、`verify-ticket/SKILL.md` 第 12、25 行、`verify-ticket/references/sub-issues.md` 第 19 行、`implement/SKILL.md` 第 76 行、`dispatch/references/night.md` 第 55、84、210 行、`docs/contexts/night/how-it-works.md` 第 17 行。

### 3.3 脚本之间的导入（本单元内与跨技能）

- `story-parity.py` 用 `_load` 导入 `design_render.py`、`lease.py`、`target_config.py`、`pixel_diff.py`、`refusal.py`（第 62–67 行）。
- `journey.py` 导入 `target_config`、`lease`；`boundary-check.py` 导入 `refusal`、`lease.judge_run`（第 142–143 行：整个检查包在 `judge_run(Path.cwd(), stop=True)` 里）；`harness-guard.py` 导入 `lease.read_target_json`、`refusal`；`target_config.py` 导入 `lease`。
- 跨技能：`extract_skeleton.py` 从兄弟目录 `../ui-acceptance/scripts/design_render.py` 加载（`SIBLING_UA`，可用 `--tools` 覆盖）；`pull_design.py` 经 `tool_scripts(tools)` 加载 `design_render.py` 与 `refusal.py`；`tool-guard.py`、`retro.py` 加载 `refusal.py`；`verify-ticket.py` 加载 `lease.py` 并把 `ui-acceptance/scripts` 放进 `CHECK:` 的 `PATH`（第 2856–2875、4168–4175 行）；`dispatch.sh` 第 4615 行定位 `lease.py`。

```edges
prototype/UI.md -> design-pages : hands-off-to
ask-matt -> design-pages : cites
ask-matt -> write-screen-contract : cites
wayfinder/interface-and-remake.md(design ticket) -> design-pages : hands-off-to
wayfinder/interface-and-remake.md(alignment ticket) -> write-screen-contract : hands-off-to
design-pages/SKILL.md -> design-pages/references/edit-pages.md : re-enters-at
design-pages/SKILL.md -> design-pages/references/draw.md : re-enters-at
design-pages/SKILL.md -> design-pages/references/pull.md : re-enters-at
design-pages/SKILL.md -> design-pages/references/design-system.md : re-enters-at
design-pages/references/edit-pages.md -> design-pages/references/template-project-claude-md.md : reads
design-pages/references/design-system.md -> design-pages/references/template-design-system-claude-md.md : reads
design-pages/references/edit-pages.md -> ClaudeDesign:page-project/CLAUDE.md,task.md,state-list.md,ui-ids.md : writes
design-pages/references/design-system.md -> ClaudeDesign:design-system/CLAUDE.md,task.md : writes
ClaudeDesign:agent -> ClaudeDesign:page-project/CLAUDE.md : reads
design-pages/references/pull.md -> design-pages/scripts/pull_design.py : runs-script
design-pages/scripts/pull_design.py -> ui-acceptance/scripts/design_render.py : imports
design-pages/scripts/pull_design.py -> ui-acceptance/scripts/refusal.py : imports
design-pages/scripts/pull_design.py -> design-pages/scripts/check_editable_selectors.py : imports
design-pages/scripts/pull_design.py -> prototypes/<effort>/claude-design/(scenes.json,pull-report.md) : writes
design-pages/references/pull.md -> write-screen-contract : hands-off-to
design-pages/references/pull.md -> write-screen-contract#Re-runs : re-enters-at
design-pages/references/pull.md -> wayfinder : hands-off-to
design-pages/references/pull.md -> dispatch.sh reverify : runs-script
design-pages/references/pull.md -> dispatch.sh route/resume : runs-script
design-pages/references/pull.md -> verify-ticket.py --sub-issue contract : runs-script
dispatch.sh resume -> worker : wakes
dispatch/references/night.md(contract child row) -> design-pages/references/pull.md : hands-off-to
write-screen-contract/SKILL.md -> write-screen-contract/references/screen-contract-format.md : reads
write-screen-contract/SKILL.md -> write-screen-contract/scripts/extract_skeleton.py : runs-script
write-screen-contract/SKILL.md -> write-screen-contract/scripts/lint_screen_contract.py : runs-script
write-screen-contract/SKILL.md -> write-screen-contract/scripts/dump_openapi.py : runs-script
write-screen-contract/scripts/extract_skeleton.py -> ui-acceptance/scripts/design_render.py : imports
write-screen-contract/SKILL.md -> prototypes/<effort>/claude-design/ : reads
write-screen-contract/SKILL.md -> docs/specs/<effort>/screen-contract.yaml : writes
write-screen-contract/SKILL.md -> to-spec : hands-off-to
write-screen-contract/SKILL.md -> to-spec/references/revising-a-spec.md : hands-off-to
write-screen-contract/SKILL.md -> wayfinder : hands-off-to
to-spec -> write-screen-contract#Reverse sweep : re-enters-at
to-spec -> docs/specs/<effort>/screen-contract.yaml : reads
to-spec -> ui-acceptance/scripts/target_config.py --check : cites
to-tickets/SKILL.md -> to-tickets/references/cutting-interface-tickets.md : reads
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/boundary-check.md#Selecting one row's test : cites
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/story-parity.md,journey.md,product-answers.md : cites
to-tickets/references/cutting-interface-tickets.md -> ticket:CHECK(story-parity.py,boundary-check.py,journey.py,harness-guard.py) : writes
ui-acceptance/SKILL.md -> to-tickets/references/cutting-interface-tickets.md#Criterion shapes : re-enters-at
ui-acceptance/SKILL.md -> implement/references/writing-interface-code.md#Before the first line : re-enters-at
ui-acceptance/SKILL.md -> ui-acceptance/references/story-parity.md : re-enters-at
ui-acceptance/SKILL.md -> ui-acceptance/references/boundary-check.md : re-enters-at
ui-acceptance/SKILL.md -> ui-acceptance/references/journey.md : re-enters-at
ui-acceptance/SKILL.md -> ui-acceptance/references/product-answers.md : re-enters-at
ui-acceptance/SKILL.md -> ui-acceptance/references/harness-guard.md : re-enters-at
ui-acceptance/SKILL.md -> implement : hands-off-to
implement/SKILL.md -> implement/references/writing-interface-code.md : reads
implement/references/writing-interface-code.md -> ui-acceptance/scripts/story-parity.py(--render-only) : runs-script
implement/references/writing-interface-code.md -> ui-acceptance/references/story-parity.md : cites
implement/references/writing-interface-code.md -> ui-acceptance/references/boundary-check.md#Selecting one row's test : cites
implement/references/writing-interface-code.md -> tdd : cites
implement/references/writing-interface-code.md -> verify-ticket.py --sub-issue contract : runs-script
implement/references/writing-interface-code.md -> design-pages/references/pull.md : cites
dispatch.sh(start worker PRODUCT_RULES) -> ui-acceptance/SKILL.md#Five rules while the product is running : cites
verify-ticket/SKILL.md -> ui-acceptance : hands-off-to
verify-ticket/references/sub-issues.md -> ui-acceptance/SKILL.md#Five rules while the product is running : cites
verify-ticket.py -> ui-acceptance/scripts/(PATH for CHECK) : runs-script
verify-ticket.py -> ui-acceptance/scripts/lease.py : imports
verify-ticket.py -> worker.queued : writes-event
relay -> worker : wakes
verify-ticket.py(--lint) -> docs/specs/<effort>/screen-contract.yaml : reads
dispatch.sh -> ui-acceptance/scripts/lease.py(release --stop, remove-instance) : runs-script
dispatch/scripts/tool-guard.py -> ui-acceptance/scripts/refusal.py : imports
retro/scripts/retro.py -> ui-acceptance/scripts/refusal.py : imports
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/design_render.py : imports
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/pixel_diff.py : imports
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/lease.py : imports
ui-acceptance/scripts/story-parity.py -> ui-acceptance/scripts/target_config.py : imports
ui-acceptance/scripts/story-parity.py -> .mmw/target.json(stories) : configured-by
ui-acceptance/scripts/journey.py -> .mmw/target.json(start,discover,stop,journeys) : configured-by
ui-acceptance/scripts/journey.py -> ui-acceptance/scripts/target_config.py : imports
ui-acceptance/scripts/journey.py -> ui-acceptance/scripts/lease.py : imports
ui-acceptance/scripts/boundary-check.py -> ui-acceptance/scripts/lease.py(judge_run) : imports
ui-acceptance/scripts/harness-guard.py -> .mmw/target.json(harness_markers,leaves_machine,stories) : configured-by
ui-acceptance/scripts/target_config.py -> .mmw/target.json : reads
ui-acceptance/scripts/lease.py -> .mmw/target.json(instance.max, stop) : configured-by
ui-acceptance/scripts/lease.py -> MMW_HOME/leases : writes
code-review/references/session.md -> code-review/references/ui-reviewer.md : calls
code-review/references/ui-reviewer.md -> ui-acceptance/scripts/story-parity.py(--out) : runs-script
code-review/references/spec-reviewer.md -> docs/specs/<effort>/screen-contract.yaml : reads
```

自拟关系：`imports`（一个脚本以模块方式加载另一个脚本的代码）；`writes`（产出一个文件或工件，区别于只写事件的 `writes-event`）。

---

## 4. 重复

`grep` 范围：`mmw-v2/`、`docs/`（排除 `docs/research/`、`docs/reviews/`）、`AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`。merge-notes、downstream-notes、ADR 是变更记录，引用旧文本属其本职，下表单列不计。

| # | 内容 | 出现位置 | 判断 |
| --- | --- | --- | --- |
| R1 | 两份基线分工：design package 管外观与逐字文案，screen contract 管 `calls`/`shows`/`next`/`on_failure` | `write-screen-contract/SKILL.md` 第 8 行；`screen-contract-format.md` 第 15 行 `baselines.precedence`；`writing-interface-code.md` 第 3 行；`to-spec/SKILL.md` 第 22 行；`cutting-interface-tickets.md` 第 122–123 行；`CONTEXT.md` 第 323 行 | **真重复**（同一意思，五处技能文本，读者分别是写合同、写 spec、切票、写码的 agent）。每处都是该读者在其时刻读的文件，属 SKILL-SET-RULES「Keep the copy the acting agent loads」的多读者情形；是否合一未定 |
| R2 | story 页约定：`[data-story-root]` 在组件自身根上、带设计页根的 `data-ui` id | `story-parity.md` 第 23–28 行（定义处）；`product-answers.md` 第 18–20 行（指针）；`writing-interface-code.md` 第 21 行（指针）；`cutting-interface-tickets.md` 第 92 行（contract ticket 交付项复述一遍）；`spec-reviewer.md` 第 37 行（审查规则）；`story-parity.py` 头第 16 行与第 625 行拒绝文本 | 定义只一处；`cutting-interface-tickets.md` 第 92 行与 `spec-reviewer.md` 是**部分重复**（复述要点给第二读者）。2026-09-23 汇总第 109 行记「story 页面的要求原来写了三份，现在只留一份」（已核实为当前状态：只有 `story-parity.md` 有完整规则） |
| R3 | `data-ui` id 只在列表的重复部分重复 | `template-project-claude-md.md` 第 37 行（给 Claude Design agent）；`product-answers.md` 第 21–24 行（给 contract ticket）；`cutting-interface-tickets.md` 第 93 行（静态守卫）；`docs/contexts/tickets/CONTEXT.md` 第 142 行；`boundary-check.md` 第 32 行与 `story-parity.md` 第 57 行（`<id>#<n>` 命名） | **同一规则四种读者**：设计侧 agent、产品答案、切票、测试助手。设计侧那份读者读不到仓库（`template-project-claude-md.md` 第 3 行），不能合并；其余三处是真重复 |
| R4 | 六个 lease 变量清单 | `lease.py` 头第 13–19 行；`journey.md` 第 22–23 行；`product-answers.md` 第 44–45 行；`CONTEXT.md` 第 409 行 | **真重复**（同一清单）。SKILL-SET-RULES `### Redundancy and bloat` Duplication 条把脚本头也算作一份 |
| R5 | 「journey 脚本自己什么都不启动」 | `journey.md` 第 34–36 行；`product-answers.md` 第 30–31 行 | **真重复**，同一技能两份 reference；两者都被 contract ticket 的 **Read first** 点名（`cutting-interface-tickets.md` 第 106 行），同一读者读两遍 |
| R6 | story service 不取 lease、用机器分配的端口 | `story-parity.md` 第 15–18 行；`product-answers.md` 第 62–70 行；`CONTEXT.md` **story** 条 | **真重复**，同上情形（contract ticket 两份都读） |
| R7 | 无 lease 时 `start` 拒绝并打印 `lease.py run --` 命令 | `ui-acceptance/SKILL.md` 规则 2；`product-answers.md` `start` 条第 49–50 行 | 同一事实、两种读者：规则 2 告诉 worker 会发生什么，`product-answers.md` 要求写 `start` 的人让它发生。**部分重复** |
| R8 | 「报告 blocked 并停：不等、不重试、不改环境、不碰别的 run」 | `ui-acceptance/SKILL.md` 规则 4；`refusal.py` `REPORT_BLOCKED`（被各脚本拒绝文本使用）；`CONTEXT.md` **`REPORT_BLOCKED`** 条 | **真重复**：文本一份、脚本拒绝一份。SKILL-SET-RULES 把 refusal 文本也计为一份 |
| R9 | 像素差异图是证据不是裁决 | `story-parity.md` 第 92–94、108–109 行；`story-parity.py` 头第 18–19 行；`pixel_diff.py` 头；`writing-interface-code.md` 第 35 行 | 真重复；`writing-interface-code.md` 那句带 #548 的教训（见 `merge-notes/implement.md` `## Where a failing story-parity.py criterion is read`） |
| R10 | 禁止 stub `fetch`/msw/nock/fetch-mock，mock 放在 gateway | `boundary-check.md` 第 34 行；`verify-ticket.py` 第 2843 行正则与第 3425 行文档串 | 文本 + 脚本检查，互补（lint 只查 `CHECK:` 行，文本管测试文件）；`boundary-check.md` 自己写明 lint 管不到测试文件 |
| R11 | 设计侧缺陷 → `contract` child，由 design-pages 的 pull 处理 | `writing-interface-code.md` `## When the design side is the defect`（worker）；`pull.md` `## Design problems in the report` 第二支（design-pages 会话）；`dispatch/references/night.md` 第 84 行（夜里的 orchestrator：移票到 `needs-triage` 留给白天）；`pull.md` `## A contract child answered…`（白天的收尾，把票移回） | 同一机制的**四个时刻、四种角色**，不是重复，是一条交接链的各端。`pull.md` 第二支与 `writing-interface-code.md` 用同一命令形状（`--sub-issue contract`），命令形状重复 |
| R12 | 行 id 不重排不复用 | `write-screen-contract/SKILL.md` `## Re-runs`（带理由）；`screen-contract-format.md` `id` 列与 `retired_ids` 行；`CONTEXT.md` **`retired_ids`** | 真重复（同一读者：写合同的 agent 两份都读） |
| R13 | `shows` 只写字段、不写值；`calls` 的写法；`source` 的优先级 | `SKILL.md` `### 3.` 三条；`screen-contract-format.md` `## Column rules` 的 `shows`/`calls`/`source` 列 | 真重复，同一读者。2026-09-28 lightweight review 的「不采纳」A10 明确保留：「它列在 the ones people get wrong 之下，是 agent 填这一列时正要读的提醒」（已核实原文） |
| R14 | `task.md` 的约定 | `edit-pages.md` `## Talking to the agent…`（本会话怎么写）；两份模板的 `## task.md`（项目内 agent 怎么做）；`design-system.md` 第 4–5 步 | 本会话一份、两类 Claude Design 项目各一份。两份模板同句（「It never overrides the rules/conventions in this file」只差一词），因为两个项目的 agent 互相读不到，属**必要的平行副本** |
| R15 | pull 只由 `pull.md` 写 design package；不用「Handoff to Claude Code」 | `edit-pages.md` `## Sign-off`；`writing-interface-code.md` 第 51 行；`night.md` 第 84 行；ADR 0029 | 各自读者不同（design-pages 会话、worker、orchestrator）；「Handoff to Claude Code」只在 `edit-pages.md` 出现一次（`grep` 核实） |
| R16 | `改动分类` 决定下一步 | `pull.md` `## Reached from here`；`write-screen-contract/SKILL.md` `## Re-runs` 第一条；`to-spec/references/revising-a-spec.md` 第 9 行；`CONTEXT.md` **pull report** | 同一分类值、三个接收端各管一段（交接链），不是真重复 |
| R17 | 判据形状 `CHECK:`/`EXPECT:` | 只在 `cutting-interface-tickets.md` `## Criterion shapes`；`ui-acceptance` 四份 reference 中已无（`grep "The criterion"` 在 reference 中 0 处，核实） | 已归一。但 `merge-notes/to-tickets.md` 第 93 行仍写「每种 criterion 的形状只点名 `ui-acceptance` 的 … 各自的 **The criterion** 一节」，与同文件第 91 行「原样从 `ui-acceptance` 的四份 reference 搬来」矛盾（见第 5 节） |
| R18 | 「选中一行测试」的锚定规则 | 只在 `boundary-check.md` `## Selecting one row's test`；`cutting-interface-tickets.md` 第 32 行与 `writing-interface-code.md` 第 23 行只放指针 | 已归一（`merge-notes/to-tickets.md` 第 91 行说明理由：worker 不读 `to-tickets`） |
| R19 | 「The pipeline scripts…report blocked」的「管线故障」清单 | `ui-acceptance/SKILL.md` 规则 5；`verify-ticket/references/sub-issues.md` 第 19 行第 1 问 | 部分重复：`sub-issues.md` 引用规则编号并复述脚本清单 |
| R20 | 术语表对规则的复述 | `CONTEXT.md` 97 条中多条（**boundary criterion**、**journey criterion**、**harness guard criterion**、**fault-injection switch**、**lease** 等）重述行为规则 | 术语表的本职是定义；但见第 9 节「术语表 `_Home_` 与现状不符」 |

只是同词、不是重复的：`contract`（W2：`contract` child 指票被要求遵守的东西；screen contract；**contract ticket**——DECISIONS.md「Rejected」表说 contract ticket 这个名字的缺陷成立但没有更好候选）；`part`（W9：design system 的 part 与 `data-ui` 的 `<element>`）；`effort`（CONTEXT 第 139 行明写与 `models.json` 的 `effort` 不同）；`scratch`（CONTEXT 第 165 行：evidence scratch directory 与 `<scratch>` 不同）；`story` 与 user story（CONTEXT 第 191–193 行）。

---

## 5. 上游差异

**三个技能本身不是上游技能**：`mmw-v2/skills.txt` 第 36、39、46 行以 `self/` 登记；最近一次 squash 提交 `5b1a4c51`（「Squashed 'mmw-v2/upstream/' changes from 6654f6b6..c55ee460」，2026-09-18）的树里没有任何 design、screen、ui-acceptance 路径（`git ls-tree` 核实）。上游 `to-tickets/SKILL.md` 唯一与界面有关的句子是第 31 行「(schema, API, UI, tests): vertical, NOT a horizontal slice」；上游 `implement`、`code-review` 的 `SKILL.md` 中没有 UI、design、screen、story 字样（`git show` + `grep` 核实）。

三份交接 reference 都在上游 subtree 目录里，但都是本仓新增文件：

| 文件 | 上游行数 | 现状行数 | merge-note | 性质 |
| --- | --- | --- | --- | --- |
| `to-tickets/references/cutting-interface-tickets.md` | 0（squash 树中不存在） | 152 | `merge-notes/to-tickets.md` `## 界面 ticket 的规则 cutting-interface-tickets.md`、`## 一个概念一个名字…`、`## 界面 ticket 接回模板的 Seam、Owns 与五问`、`## contract ticket 已有产品一支的条件`、`## contract ticket 的「缺什么」…`、`## 任务板试点 #541 出 #555 那批票时补的规则`、`## 走真实流程补的四处缺口`、`## cutting-interface-tickets.md 只写切票那一刻用得上的话` | **改变能力**：新增五种票、四种判据形状、Seam/Owns 按判据形状的填法、批次末票放全树扫描判据。全部是 MMW 流程写入 |
| `implement/references/writing-interface-code.md` | 0 | 57 | `merge-notes/implement.md` `## writing-interface-code.md`、`## Where a failing story-parity.py criterion is read`、`## Two baselines…and one code path`、`## The story criterion is a declared exception to red before green`、`## A DIFF value is checked before it is copied` | **改变能力**：给 `tdd` 的 red-before-green 声明一个例外；新增「设计值先查后抄」的顺序；新增 `contract` child 出口。全部是 MMW 流程写入 |
| `code-review/references/ui-reviewer.md` | 0 | 37 | `merge-notes/code-review.md` `## UI axis（试点）`、`## The UI axis and the reaction ticket divide appearance…` | **改变能力**：第四个 review axis（试点状态只写在 merge-note，不写在 `session.md`） |

这三个 reference 所属技能的 `SKILL.md` 也被本仓改写到多半不是上游原文：`to-tickets` 上游 105 行 / 现状 206 行；`implement` 上游 15 行 / 现状 101 行；`code-review` 上游 87 行 / 现状 15 行（`git show` 与 `wc -l` 核实）。`mmw-v2/merge-notes/README.md` `## 本仓自有正文的技能`（第 36 行）规定：拉上游时这三个技能不合并上游改动，冲突取本仓；它们的 merge-note 记本仓各段意图而非与上游的差异。SKILL-SET-RULES `### Upstream skills` 末条：「When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text.」

指向这三份 reference 的上游文件改动（不在本单元文件范围，只列位置）：`to-tickets/SKILL.md` 第 46 行与第 174 行（模板 `## Read first`）；`implement/SKILL.md` 第 16 行末句；`code-review/SKILL.md` 第 3 行 description（「Standards, Spec, Tests and UI axes」）与第 15 行入口表；`code-review/references/session.md` 第 19–21、79–85 行。

**merge-note 与现状的一处不一致（已核实）**：`merge-notes/to-tickets.md` 第 93 行（`五种 ticket` 行）末句写「每种 criterion 的形状只点名 `ui-acceptance` 的 `references/story-parity.md`、`boundary-check.md`、`journey.md` 各自的 **The criterion** 一节」；而同文件第 91 行写判据形状已「原样从 `ui-acceptance` 的四份 reference 搬来」，`ui-acceptance` 的 reference 里也已没有 **The criterion** 小节（2026-09-28 lightweight review D1 删除，`grep` 核实）。SKILL-SET-RULES `### Upstream skills` 第 2 条：「An entry that still states a replaced rule is a finding: the next upstream pull would restore that rule.」

---

## 6. 价值证据

| 部件或段落 | 防什么失败 | 实地证据 | 核实 |
| --- | --- | --- | --- |
| 组件级离线 story + 少量 journey（ADR 0011，整个 story-parity 设计） | 「真状态加真容器」的整机驱动把管线自身缺陷乘开，worker 被逼改产品迁就判据 | ADR 0011 第 10 行：变色龙 S3 2026-09-03 至 09-07，七张界面票关一张；25 张子票中 22 张是管线自己的；#640 的 worker 把 mount 挪到空 wrapper、塞隐藏节点 | ADR 原文已核实；原始 issue 未读 |
| element parity 取代树+像素、判官不遮不藏（ADR 0028） | 字号颜色位置差异被面积阈值放过；`volatile_values` 让差异消失 | ADR 0028 第 10 行：spec #444「工作监控指标 13px 对 26px 只占截图 2.7% 被像素阈值放行」 | ADR 已核实 |
| 四列 boundary test + `MMW_NEGATIVE` | 测试只证明了 `calls`；断言不依赖点击 | ADR 0028 第 10 行「boundary 只证明了 `calls`」 | ADR 已核实 |
| journey `--break` 只坏一个 operation；从另一页读回结果 | 停掉产品的负控制让弱断言（只看标题）也失败而通过 | ADR 0028 第 10、16 行 | ADR 已核实 |
| `SKILL.md` 第 10 行「only eyes…never the check」 | 红了就改判据 | ADR 0011 #640（挪 mount、塞隐藏节点）；lightweight review I1 标明为立场句 | 已核实 |
| Five rules 与 lease | 多个 run 抢端口、互杀、各自发明应对 | `lease.py` 头第 32–33 行「On 2026-09-05 five workers shared three fixed ports and a night produced one worker's worth of work」；`refusal.py` 头「three workers each got a correct, honest "port held by another checkout" and each invented a different response: one waited indefinitely, one built a retry loop, one killed the incumbent」；ADR 0008 第 20–26 行同一夜清单 | 脚本头与 ADR 已核实 |
| 规则 3、规则 5 的理由句 | 手动完成人类步骤、绕开坏脚本 | 无具体事故记录；lightweight review I2/I3 只说恢复被 `cb45a515` 删掉的句子 | **无证据**（只有立场，无事故） |
| 规则 1 的 `kill` 拦截 | 杀掉别人的产品 | `tool-guard.py` 第 170–171 行注释举 `lsof -ti:5173 \| xargs kill -9`；`refusal.py` 头「one killed the incumbent」 | 已核实 |
| `worker.queued` + relay 唤醒（lease 满时） | worker 轮询或占别人进程 | `verify-ticket.py` 第 1758–1808 行；外部 #296「一次交回使 max=2 的并行度变 1」（I5-P8，来自 I5 转述） | 代码已核实；#296 未核实（只读 I5） |
| `product-answers.md` 端口检查用 `SO_REUSEADDR` | 刚停的产品留下 `TIME_WAIT`，break 那遍 `start` 误拒 | 提交 `a546cfa1`「Found accepting #563…」 | 提交说明已核实 |
| 「Servers under a burst」≥64 待接连接 | 页面并发请求被重置、渲染为空 | 提交 `dd3584d9`：board suite 间歇失败，6 并行复现，128 时 24/24 通过 | 已核实 |
| `## Selecting one row's test` | 子串选中两条测试，判错行 | 提交 `e5cdd22e`（#541 为 #555 出票）列出「anchored test selection per row」；具体事故行未见 | 提交已核实；事故细节**未确定** |
| `writing-interface-code.md` **Fix in place**（只改点名的 id 与属性） | 按像素差反复调字体行高 | `merge-notes/implement.md` 第 147 行：变色龙 #548 一个 worker 跑 16 次 parity 调字体行高渲染参数后放弃 | merge-note 已核实；原 issue 未读 |
| **One code path** | 产品有一条只喂 fixtures 的 `scenario` 路径，判据在用户不走的路上变绿 | `merge-notes/implement.md` 第 151 行：变色龙渲染器 `scenario` 与 `live` 两条路径 | merge-note 已核实 |
| **Two baselines** 与 Spec axis 读 screen contract | 「desktop never talks to the backend」却 `ALL MET` 关票 | `merge-notes/code-review.md` 第 102 行：变色龙 #549 | merge-note 已核实 |
| design-pages：pull 为唯一写入者（ADR 0029） | 本地与 Claude Design 两份各改，说不清哪份对 | ADR 0029 第 10 行：工作监控与变色龙两次只改本地 | ADR 已核实 |
| design system 由 Claude Design agent 建、只装外观；页面不加载产品代码（ADR 0030、模板 `## Files`） | design system 成为产品前端副本，element parity 拿产品比产品，44 个 scene 全过 | ADR 0030 第 12 行：任务板试点，46 个 React 组件、两次返工 | ADR 已核实 |
| `template-project-claude-md.md` `## Files` 理由句 | 抄生产 CSS 带来编辑器点不中的选择器 | lightweight review design-pages I4：spec #445 第三个问题，18 条选择器，一条把指标缩成 13px 灰字 | 转述自 review；#445 原文未读，**未核实** |
| pull report `设计检查` 的「样式表里没有的类名」「写死的数值不在 design system 的变量里」 | 页面偏离 design system，worker 以 `contract` child 发现 | Mem retro spec-555：「The redrawn design pages carried class names the bound design system does not define…pull's design check reports neither」；落地提交 `61690429`；`pull_design.py` `design_check_lines` 已含两行 | 已核实 |
| 模板 `## Page data` 第二句（有交互的页面也加载后端形状数据） | story 无法运行产品的设置逻辑 | Mem retro spec-555（#569）；提交 `630aa812` | 已核实 |
| 模板 `App · ` 页区域填满槽位、覆盖层无背景 | App 页区域用 `100vh`、设置层不透明遮住看板 | Mem retro spec-555（#570）；提交 `670f07a8` | 已核实 |
| `story-parity.md`「after a click…draws that scene's own input」 | 点击后状态无 scene 数据，#568 被交回 | Mem retro spec-555（#568）；提交 `670f07a8` | 已核实 |
| `pull.md` `## Reached from here` 按合同是否存在分派 | 修完设计再 pull 一次，脚本不再标「首次」，合同一直没人写 | 2026-09-23 汇总第 42 行 | 已核实现状文本 |
| `pull.md` `覆盖` 与 `本地改过的说明` 必读 | 状态漏画要到 design ticket 关后才被 lint 拦；本地改动被覆盖无人告知 | lightweight review design-pages I2（依据是脚本行为：`handoff_page_errors`、`prepare_staging`/`install` 删除备份） | 脚本行为据 review 转述，`handoff_page_errors` 存在于 `lint_screen_contract.py` 第 201 行（核实）；实地事故**无证据** |
| `write-screen-contract` 第 10 行（不填看似合理的默认值） | 无决定支撑的 `on_failure` 被原样建出 | lightweight review 引 `docs/specs/task-board/screen-contract.yaml` 的 `conversation 2026-09-21` 为正面例子 | 未打开该 yaml，**未核实**；事故**无证据** |
| `### 4.` cross-component row | 联动没人建 | ADR 0028「组件联动写成 cross-component row」；`cutting-interface-tickets.md` app page ticket 的 composition module 理由（`merge-notes/to-tickets.md` 第 86 行：story 页自己接线会让漏接也全绿） | 已核实（理由为推演，未见事故） |
| `cutting-interface-tickets.md` 静态守卫与 harness guard 放末票 | 早票的全树判据被后票弄红、reverify 重开 | Mem retro spec-445（#472 AC4）、spec-446（#491 AC5）；I5-P2 | 已核实 |
| critical-flow ticket 阻塞边从行推导 | 后端不存在时派出最贵的票 | `merge-notes/to-tickets.md` 第 37 行：推演，未列事故 | **无证据**（推演） |
| reaction ticket 与 UI axis 分界 | 早上请用户看 UI axis 已报过的东西 | `merge-notes/code-review.md` 第 196–203 行；#539 | merge-note 已核实；事故**无证据** |
| UI axis（试点） | element parity 覆盖不到的装饰、整体观感、设计页画错 | 无运行记录（`merge-notes/code-review.md` 标为试点） | **无证据** |
| `harness-guard.py` | back door 随发布到客户机器 | ADR 0028 Consequences 要求 `harness_markers`；未见泄漏事故记录 | **无证据**（预防性） |
| Spec reviewer 与 `shows` 定义对齐 | reviewer 按错误规则报合规的行 | Mem retro spec-555（#566、#569）；提交 `4b8ed56a`、`564e1626` | 已核实 |

---

## 7. 约束

**ADR**

- ADR 0011：组件级离线判定；外观判据不起产品、不 seed、不走路由；整机只跑三到五条 journey（「半年后再发明『必须把整个产品摆进每个设计场景』的人，读这一份」）。
- ADR 0028（amends 0011）：`data-ui` id 配对的 element parity；App 页进 story；四列 boundary test 替换产品仓库指名的对外调用层；product answers 只写不变要求、不按产品类型给做法；judge 不遮不藏，拒绝 `volatile_values` 与带 `trigger` 的 `retired_ids`；`--break` 只坏一个接口；删 `target.kind`。「半年后再发明『按截图面积判外观』或『按产品类型写验收做法』的人，读这一份」。
- ADR 0029：Claude Design 为唯一设计源；仓库副本只由 pull 写；不用 Handoff 导出；不设钩子拦本地编辑（正向指引优先于禁令）；git 是设计历史。
- ADR 0030（amends 0029）：design system 由 Claude Design 内 agent 建，MMW 只写 `CLAUDE.md`、指源、事后检查；只装外观；设计页不加载产品代码；`check_design_system.py` 与 `build_ds_bundle.py` 已删。
- ADR 0008：每道闸口点名事实、给唯一出路、不许静默通过——本单元所有拒绝走 `refusal.py`，每个 oracle 带负控制（harness guard 除外，`CONTEXT.md` **negative control** 条写明）。ADR 0008 第 12 行仍说 `refusal.py` 在 `mmw-v2/skills/verify-ticket/scripts/`，现已在 `ui-acceptance/scripts/`（ADR 为决定记录，不改正文；属过时路径）。
- ADR 0026：不另起 verifier；新检查要么是脚本、要么是一个 reviewer axis——UI axis 据此成为 axis（`merge-notes/code-review.md` 第 54 行）。
- ADR 0002、0004：已挂起（`docs/adr/README.md` 第 54 行），不约束现状。

**SKILL-SET-RULES 条款**

- 事实 2「Scripts carry what is deterministic; text carries judgement」+ `### Scripts and judgement`：`pull.md` 第 3 步「the command exits 0 whatever the report finds」，把判断留给文本；`write-screen-contract` 删掉格式 reference 的 `Lint` 列（lightweight review D2）。
- 事实 5 与 `### Load and disclosure`「A reference that every run of the task opens is a fragment」：`screen-contract-format.md` 被写合同的每次运行打开，按此条应内联，但它同时是 `to-spec`、`to-tickets`、`implement`、`code-review` 引用的格式唯一处——现状保留独立文件（未见记录的裁定，**未确定**是否被视为例外）。
- 事实 6、7「never restates another skill's rules」「Everything has one home」：判据形状只住 `cutting-interface-tickets.md`；「选中一行测试」只住 `boundary-check.md`；story 页规则只住 `story-parity.md`。
- `### Load and disclosure`「A rule sits in the text of the agent that must follow it」：Five rules 放在 `ui-acceptance`，由 `dispatch.sh` 启动 prompt 点名章节名（「规则编号和标题不动：三个文件和 worker 的启动 prompt 逐字引用」，lightweight review D9）。
- `### Vocabulary` 第 2 条点名 **oracle**、**Gateway**、**fault injection**、**baseline** 为应优先采用的既有术语——本单元的 oracle、gateway、fault-injection switch、baseline 均按此命名（2026-09-28/29 词汇轮次把 judge、outbound call module、break switch 改掉；DECISIONS.md T26–T28、W1、W2）。
- `### Vocabulary`「Skill text is English. Another language appears only inside a name the program uses」：`pull.md` 的 `设计检查`、`覆盖`、`改动分类`、`本地改过的说明`、`编辑器点不中的选择器`、`未核对`、`增删控件或改流转`、`只改外观或文案` 都是 `pull_design.py` 写出的标题或值（第 1292、1310、1452–1455 行核实）；`design-system.md` 的 `开始`/`继续` 是用户在 Claude Design 里说的话。
- `### Paths and host neutrality`：`CHECK:` 不写路径、oracle 裸名（第 117 行原文点名本单元）。
- `### Examples`：示例用 notes app（`screen-contract-format.md`、`cutting-interface-tickets.md` 均为 notes）。
- `### Descriptions`：description 只写触发条件（三个 description 均为「Use when…」；2026-09-23 汇总第 30 行记用户定过此规则）。
- `### Upstream skills` 末条（少于一半上游行数即按自有文本审）：适用于三份交接 reference 所属技能。

**已记录的用户决定**

- Nowledge Mem `415f96d0`「界面技能正文只留可执行规则并保留防误用表述」：带日期实测、维护者理由、历史不写回技能；理由已在 ADR 0029/0030 的不必写回。lightweight review（design-pages「与你之前裁定的冲突」）建议恢复 I3、I4 两句理由并请用户确认——两句现已在文本中（`design-system.md` `## What it is for`、模板 `## Files`），推断用户已同意；**未找到用户确认的原话**。
- `docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`：T14 **page ticket**、T15 **critical-flow ticket**、T22 UI 类别名、T26 **Component page**、T27 **product under test**、T28 删 **boundary** 元条；Rejected：contract ticket 改名（缺陷成立、无候选）。
- `mmw-v2/merge-notes/README.md` `## 本仓自有正文的技能`：`code-review`、`implement`、`to-tickets` 拉上游时取本仓。
- 提交 `f74eb4f8`（2026-09-06）「the driver, the judges, the lease and the hook move into one skill; no script leaves its own directory」：一个技能拥有「怎么够到产品」的全部代码——这是 `lease.py`、`refusal.py` 住在 `ui-acceptance/scripts/` 的来由（当时技能名 drive-target，2026-09-19 改名 ui-acceptance）。同期另有提案（Mem `5a337408`，2026-09-05）主张新建 `mmw-v2/runtime/` 承接 lease、hook 等基础设施；现状没有 `mmw-v2/runtime/` 目录（`ls mmw-v2/` 核实），推断该提案未被采纳，**未找到否决的原话**。
- `AGENTS.md` `## Self-hosting boundary` 与 `to-tickets/references/person-ticket.md` 第 11 行：自托管仓库里 reaction ticket 经 `ui-acceptance` 的 lease 起产品。

---

## 8. 天然整体

| 整体 | 组成 | 为什么拆开会失去意义或增加跳转 |
| --- | --- | --- |
| 设计侧离线渲染 | `design_render.py` 被 `story-parity.py`、`extract_skeleton.py`、`pull_design.py` 三处导入 | 三处必须用同一个渲染器、同一个暂停时钟（`SETTLE_VIRTUAL_MS`、`CLOCK_EPOCH_MS`）、同一个 `[data-ui]` 读取器，skeleton 的控件清单、pull 报告的覆盖、story 比较才指向同一批元素。分成三份会让三方对「设计页上有哪些元素」各执一词（推断，依据 `design_render.py` 头「`story-parity.py` and `extract_skeleton.py` import the baseline server, the wrapper page, capture, and the `[data-ui]` reader」） |
| `data-ui` id 这一条身份链 | 模板 `## data-ui`（设计侧画上）→ `pull_design.py` 写进 `scenes.json` → skeleton → screen contract `trigger` → story adapter / `[data-story-root]` → element parity 配对 → interaction helper 按 id 点击 | 每一环都用同一字符串作主键；任何一环换名，后面全部配对失败。ADR 0028 把「行按 `data-ui` id 识别」「story 按 id 比较」写成同一决定并否决拆成两份 ADR（「拆开会让『合同怎么指认控件』与『judge 按什么比』分成两份决定」） |
| 一个 oracle 与它的负控制 | `story-parity.py` 负控制、`boundary-check.py` 第二遍、`journey.py` 的 `--break`/产品停机遍 | ADR 0008「不许靠什么都不做通过」：没有负控制的 oracle 读起来和通过一样；负控制写在同一脚本同一次运行里 |
| lease 与 `.mmw/target.json` 的 `start`/`stop` 契约 | `lease.py`（分配）+ `product-answers.md` `start`/`stop`（消费仓库要保证的行为）+ Five rules（agent 的行为） | lease 只分配端口段；真正不越界靠 `start` 在 lease 内选端口、`stop` 只停自己的——三者缺一即回到 2026-09-05 的状态。`lease.py release` 拒绝仍在监听的 slot，也依赖 `stop` 真能停干净 |
| Five rules 这一节 | `SKILL.md` 第 28–38 行 | 标题和编号被 `dispatch.sh` 的 `PRODUCT_RULES`、`verify-ticket/references/sub-issues.md` 第 19 行、`implement/SKILL.md` 第 76 行逐字引用（lightweight review D9 已核实此约束） |
| pull 的「两次 MCP 调用 + 一条命令 + 读报告 + 提交」 | `pull.md` `## Steps` 1–4 | `MMW_DESIGN_PREVIEW_URL` 约一小时有效且不得落盘，必须在同一会话里接着跑命令；包与报告一起提交；报告的 `改动分类` 立即决定下一步。拆开会丢失预览地址或让报告与包分离 |
| 页项目 `CLAUDE.md` 模板整块 | `template-project-claude-md.md` 围栏块 | 它是写给另一个 agent 的完整指令文件，那个 agent 读不到仓库，也读不到本技能其他文件（第 3 行原文）；每条约定都是仓库之后要读回的东西，缺一条 pull 或 oracle 就无从读回 |
| screen contract 的 `rows` 与 `pages`/`scenes` 声明 | `screen-contract-format.md` 第 5 行 | 原文：「`rows` and these declarations cannot be derived from each other…so both are written, and the lint holds them to each other」 |
| write-screen-contract 第 2–5 步 | `SKILL.md` `## Steps` 引言 | 原文：「Steps 2 to 5 are four passes over the same rows; go back and forth between them」，是同一批行的往返填写，不是可分派给不同角色的独立步骤 |
| `contract` child 的四端 | `writing-interface-code.md`（开）→ `night.md` 第 84 行（夜里挂起、移票）→ `pull.md`（白天在 Claude Design 修、pull）→ `pull.md` `## A contract child answered…`（route、移回票、resume） | 这是跨角色、跨夜/日的一条回路；只看任何一端都看不到票如何回到 `ready-for-agent`。它本身分布在三个技能是因为读者不同（worker、orchestrator、design-pages 会话），不是可随意合并的重复 |
| page ticket 的 story criterion 例外与 boundary test 的 red-green | `writing-interface-code.md` `## Write the product` | 两者在同一遍写代码里交错：组件先按设计值写（例外），每行 boundary test 仍各自 red→green；拆到两个文件会让 worker 在 `tdd` 与本文件之间无从取舍（`merge-notes/implement.md` 第 224–243 行记录这正是 #539 前的问题） |

---

## 9. 未确定与线索核实

### 9.1 未确定

- `story-parity.py`、`design_render.py`、`pull_design.py`、`lint_screen_contract.py`、`extract_skeleton.py`、`lease.py` 的算法本体未逐行读；涉及其行为的描述均来自文件头或 reference。
- `writing-interface-code.md` 第 49 行的中文固定句「由 design-pages 技能的 references/pull.md 处理：…」：`grep` 全仓只在此处出现，没有脚本读它；它是否属于 SKILL-SET-RULES「a name the program uses」的例外，未确定。`merge-notes/implement.md` 第 31 行解释这句的用意（child 只能在白天由接了 Claude Design 的会话处理），但未说明为何用中文。
- `screen-contract-format.md` 第 3 行把「the boundary check」列为读者；`boundary-check.py` 全文不含 `contract`（`grep -c` 为 0），它只跑一条测试命令。推断此处指四列测试语义上遵循列规则，而非脚本读文件。
- `docs/contexts/ui-acceptance/CONTEXT.md` 的 **boundary criterion**、**journey criterion**、**harness guard criterion** 三条 `_Home_` 分别指 `boundary-check.md`、`journey.md`、`harness-guard.md`，但这三份文件已不含 `boundary-check.py --run`、`journey.py run`、`HARNESS OK`（`grep -c` 均为 0）；判据形状现住 `cutting-interface-tickets.md` `## Criterion shapes`。SKILL-SET-RULES `### Vocabulary`：「an entry citing a file that does not hold those facts is a finding」。
- `writing-interface-code.md` 与 `ui-reviewer.md` 写 `uv run story-parity.py …`（裸名），`ui-acceptance/SKILL.md` 第 12 行写「run one by hand as `scripts/<name>`」，`verify-ticket/SKILL.md` 第 12 行说手跑需把目录放上 `PATH`。三种说法对「手跑时怎么找到脚本」不完全一致；实际是否造成过失败，无记录。
- `CONTEXT.md` 中 10 条 `_Home_` 在上游 `prototype` 技能（experiment round、evidence page 等）的词条是否属于本界定上下文，未确定。
- 用户对 lightweight review design-pages I3/I4「与你之前裁定的冲突」的确认原话未找到。
- 只有一个真实使用本链全程的批次在本仓：任务板 #541 map → spec #555（Mem retro spec-555）；外部仓库（变色龙、工作监控、agentflow）的证据只经 ADR 与 merge-note 转述，原 issue 未读。

### 9.2 线索材料采用与核实

| 线索 | 采用的结论 | 状态 |
| --- | --- | --- |
| M1 §6「`pull_design.py` 的 `main` 仅在 `PullRefused`／异常时非零」 | 同 | 已核实（`main` 第 1647–1666 行） |
| M1 §6「lint 有 ERROR 返回 1、无 ERROR 返回 0」 | 同 | 已核实（文件头第 7 行、`main` 第 573 行） |
| M1 阶段表第 9 行把一种票叫「acceptance」 | 不采用 | 已过时：现名 **critical-flow ticket**（DECISIONS.md T15；`cutting-interface-tickets.md` `## critical-flow ticket`） |
| M1 标题「# Cutting interface tickets」 | 不采用 | 已过时：现标题 `# Tickets from a screen contract` |
| I1 `dual-baseline`、`claude-design-source` 的机制描述 | 采用 | 已核实（`write-screen-contract/SKILL.md` 第 8 行；ADR 0029） |
| I3「lease 满时写 `worker.queued`、relay 唤醒」 | 采用 | 已核实（`verify-ticket.py` 第 1758–1808 行） |
| I3「有 story criterion 才加 UI axis」 | 采用 | 已核实（`session.md` 第 21 行） |
| I3 称 `journey.md` 有 `## The break switch` 一节 | 不采用 | 已过时：现为 `## The fault-injection switch` |
| I5-P2（早票全仓判据被后票弄红） | 采用 | 已核实（Mem retro spec-445、spec-446 `## Problems observed`） |
| I5-P8（外部 #296 slot 未释放） | 仅作线索列出 | 未核实（未读 #296） |
| 2026-09-23 汇总第 42 行（pull 按合同是否存在决定下一步） | 采用 | 已核实（`pull.md` `## Reached from here` 第一条） |
| 2026-09-23 汇总第 109 行（story 页要求只留一份） | 采用 | 已核实（见第 4 节 R2） |
| lightweight review ui-acceptance I1–I7、design-pages I1–I5、write-screen-contract I1–I6 已落地 | 采用 | 已核实：逐条在现文本中找到对应句子（例：`SKILL.md` 第 10 行、`boundary-check.md` 第 34 行、`journey.md` 第 40 行末句、`product-answers.md` `## Rules`、`story-parity.md` 第 109–111 行、`pull.md` 第 30 行、`write-screen-contract/SKILL.md` 第 10、25、65、73、104–106、111 行） |
| lightweight review design-pages I4 转述 spec #445 第三个问题（18 条选择器） | 仅作证据转述 | 未核实（未读 #445） |
| 2026-09-06 handoff（align-screens、`screen_driver.py`、`target.adapter`） | 不采用为现状 | 沉积：所述文件已被 ADR 0011 删除或改名；只用来理解 `lease.py` 为何在本技能（与提交 `f74eb4f8` 对读，已核实） |
| T1/T3「element parity、break switch、四列规则为 MMW 原创；Playwright 只是依赖」 | 采用 | 部分核实：上游 squash 树无相关内容（已核实）；是否另有外部来源，未做 GitHub 搜索，**未核实** |
