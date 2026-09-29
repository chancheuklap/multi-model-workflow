# N2 单元清点：verify-ticket

日期：2026-09-29。本文只做事实清点，不做归置决定。

## 0. 阅读范围与方法

完整读过（逐行）：

- `mmw-v2/skills/verify-ticket/SKILL.md`（25 行）、`references/linting.md`（11 行）、`references/sub-issues.md`（23 行）
- `mmw-v2/merge-notes/unlazy.md`（79 行）
- `docs/contexts/ticket-run/CONTEXT.md`（331 行，读到 `### Writing interface code` 标题为止即文件末）、`docs/contexts/tickets/CONTEXT.md`（364 行）
- `docs/adr/0008-silence-is-never-a-pass.md`、`0012-review-finding-routing.md`、`0013-a-report-and-its-message-are-one-call.md`、`0019-ticket-state-is-a-fold-of-events.md`、`0026-no-verifier.md`；另读了 `docs/adr/README.md` 的索引表与 `0020-wakes-come-from-the-board.md` 开头两段（为确认 0013 被谁作废）
- `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（176 行）

脚本（按规矩读头注释、`--help`、分派、退出码，另读了下列函数体）：

- `scripts/verify-ticket.py`（4253 行）：模块 docstring 与常量区（1–140 行）、`python3 verify-ticket.py --help` 全文、`main()`（4115–4253）、全部函数与类的 docstring（用 `ast` 抽出，逐条读过）；函数体完整读过的有 `post_event`、`ticket_spec`、`own_session`、`close_ticket`、`_run_checks`/`run_checks`、`refusals`、`resume_at`、`run_preflight`、`run_baseline_if_needed`、`blocker_fold`、`_run_closeout`/`run_closeout`、`draft_problems`、`verified_problems`、`run_draft`、`run_decisions`、`run_review`、`run_touched`、`run_sub_issue`、`lint_criteria`、`reads_as_spec`、`run_lint`、`require_judges` docstring、`PIPELINE_SCRIPTS`/`JUDGES`/`TOOLS` 常量。未逐行读：screen contract 相关 lint（`lint_screen_contract` 及其 20 余个辅助函数，约 3000–3650 行）、`run_publish_drafts`/`run_publish_spec` 函数体、`ticket_entries` 以下图算法函数体、`hold_slot` 函数体后半。
- `scripts/events.py`（955 行）：模块 docstring、词汇表（`SUBJECTS` 至 `RESULTS`，55–245 行）、`main()`（870–955）、全部函数 docstring。未读 `apply()` 函数体。
- `scripts/issue_tree.py`（285 行）：模块 docstring 与函数 docstring。
- `mmw-v2/upstream-unlazy/scripts/gate-check.mjs`：头注释与 `HELP`、选项常量、函数清单与 `process.exit` 位置；`gate-lint.mjs`：头注释与 `HELP`；`scripts/lib/gates.mjs`：头注释与导出函数清单。三者与上游的差异逐行读过（见第 5 节）。
- 对照读过的外部文件：`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 1–40 行与 `## Closing steps` 全段、`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 7、8 步、`mmw-v2/skills/dispatch/references/night.md` 40–56、76–96、108–124、140–150 行、`mmw-v2/skills/dispatch/scripts/relay.py` `WAKES`、`dispatch.sh` 调用 `$VERIFY`/`$EVENTS` 的几段、`tool-guard.py` 模块 docstring、`status.py` `Sub-issues opened tonight` 一段、`mmw-v2/merge-notes/implement.md` 中含 verify-ticket 的行、`mmw-v2/tests/verify-ticket/run.sh` 头注释。

线索材料的使用：`docs/reviews/2026-09-28-lightweight/verify-ticket.md`（全文读过）、`docs/reviews/2026-09-28-lightweight/汇总.md` 与 `docs/reviews/2026-09-23-skill-set/汇总.md`（grep 相关行）、`docs/research/workflow-compare/reports/M3-mmw-ticket.md`（grep 相关行）、`I3-mmw-ticket-intent.json`、`I5-mmw-field-evidence.json`（抽取相关条目）、`T3-ticket.json`、`C3-ticket-ui-down.json`（只确认其节点指向）、`docs/research/mmw-structure/2026-09-06-handoff.md`（grep）、`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`（前 80 行）。下文凡采用线索里的结论，都标「已核实」（回到代码、git 或原文确认过）或「未核实」。

没有运行任何会改状态的命令；运行过的只有 `verify-ticket.py --help`、只读 git 命令、grep。

## 1. 部件清单

### 1.1 技能目录 `mmw-v2/skills/verify-ticket/`

| 部件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `SKILL.md` | 技能入口：一句说它跑判据并把结果作为事件贴回票；「票是唯一状态」一段；oracle 靠 `PATH` 找到的一句；`## Find your moment` 两行表；`## Reached from here` 一条指向 `ui-acceptance`。description：`Run one ticket's acceptance criteria, and close the ticket when they pass. Use when something has to be cut out of a ticket, and when a batch is about to be published.` | 任何按 description 加载本技能的 agent：主要是要开子票的 worker、要发布或 lint 一批票的写票 agent 与夜的 orchestrator。worker 的 claim、跑判据与关票不经本文件（`SKILL.md` 第 16 行原文：`A worker's claim, criteria runs and closeout are steps of the implement skill.`） |
| `references/linting.md` | 三条 `--lint` 命令（草稿、一张票、一个 spec）、图取自 tracker 的 blocking edge、批次就绪的判据 | `to-tickets` 第 7/8 步的写票 agent；开夜前的 orchestrator（`night.md` `## 1b`） |
| `references/sub-issues.md` | `--sub-issue <kind> <file>` 命令、文件形状、五种 kind 各由谁在何时读、**the kind questions** 五级有序表（带「Not this kind」对照列） | worker（`implement` `SKILL.md` 第 18 行：`Every --sub-issue run below is in the verify-ticket skill's references/sub-issues.md`）；`design-pages` 的 `references/pull.md` 开 `contract` 子票的 agent |
| `scripts/verify-ticket.py` | 4253 行主脚本，一个入口十一种工作（`main()` 中互斥）：默认跑判据、`--reverify --actor worker\|main`、`--preflight`、`--closeout [--check-only]`、`--decisions`、`--touched`、`--draft`、`--sub-issue`、`--review`、`--lint [--drafts]`、`--publish (--spec-body\|--drafts)`。还定义三组 label（`CLASS_LABELS`、`QUEUE_LABELS`、`GRADE_LABELS`）与 `ensure_label` | worker、reviewer、写 spec/写票 agent、orchestrator；`dispatch.sh` 直接 import 它的 `run_target_json_checks` 与 `ensure_label` |
| `scripts/events.py` | 流水线的事件词汇表（`EVENTS`、`SUBJECTS`、`REFUSALS`、`CHILD_KINDS`、`CHECK_RUNS`、hold 规则 `ENDS_EVERY_HOLD`/`ENDS_ONE_HOLD`/`SLOT_ENDS` 等）与 fold；CLI：`emit`、`fold`、`session`、`sessions`、`result`、`checked`、`live`、`child`；退出码 0/2/3 | 全流水线的库：`verify-ticket.py`、`dispatch.sh`（`emit`/`fold`）、`relay.py`、`status.py`、`watchdog.py`（经 relay）、`retro.py`、`mmw-v2/board/board_data.py`、`codeversion.py`；orchestrator 按 `night.md` 手工跑 `events.py fold <n>` |
| `scripts/issue_tree.py` | 一次 GraphQL 读 map/spec/ticket/child 四层树，列表短于计数就拒答（exit 2）；先用 1 点的计数查询定页大小 | `verify-ticket.py`（lint、`--touched`、`--draft`）、`status.py`、`board_data.py`、`codeversion.py`；CLI 入口留作诊断 |
| `scripts/gate-check/gate-check.mjs`、`gate-lint.mjs`、`lib` | 三个相对 symlink，指向 `../../../../upstream-unlazy/scripts/…`（`ls -la` 已核实） | `verify-ticket.py` 以 `node` 调用 |
| `scripts/__pycache__/`（未入库） | 本地缓存，含已删脚本的 `.pyc`（`refusal`、`lease`、`hook`、`screen_driver`、`visual-parity`、`tree`） | 无人；`git ls-files` 不含它（已核实） |

### 1.2 `mmw-v2/upstream-unlazy/` 中被用到的部分

| 部件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `scripts/gate-check.mjs`（769 行） | 判定引擎：按 ledger 逐条跑 `CHECK:`，exit 0 且输出匹配 `EXPECT:` 才勾选，写 `EVIDENCE:`，打印 `ALL MET` / `UNMET:` / `HANDOFF REQUIRED:` 汇总行；退出码 0/1/2/3（3 为 lease 冲突，本仓不用）。仍含上游的 scope、lease、`--claim`/`--release`/`--log`/`--bind` 代码 | `verify-ticket.py` `_run_checks`（传 `--cwd`、可选 `--reverify`、`--timeout`、ledger 文件）与 `run_baseline` |
| `scripts/gate-lint.mjs`（250 行） | 判据写法 lint，不执行 `CHECK:`；退出码 0/1/2 | `verify-ticket.py` `lint_criteria`（不加 `--strict`） |
| `scripts/lib/`（`gates.mjs` 999 行、`check-supervisor.mjs`、`regex-worker.mjs`、`process-tree.mjs`、`dispatch.mjs`） | ledger 解析 `parseGates`、状态 `gateState`、定义摘要、原子写、锁、lease；其余四个与上游逐字相同 | 上两个脚本 import |
| `tests/run-tests.mjs`、`tests/lint-tests.mjs` | 引擎自己的测试（25 条、29 条） | `mmw-v2/tests/verify-ticket/run.sh` 与 `AGENTS.md` Commands 表 |
| 其余（`SKILL.md`、`references/`、`templates/`、`stop-hook.mjs`、`install-hooks.mjs`、`dispatch-check.mjs`、其余测试） | 上游原样保留，不接进技能目录 | 无运行时读者（`mmw-v2/merge-notes/README.md` 第 65 行：`verify-ticket 的判定引擎 gate-check，不是装进 host 的技能`） |

### 1.3 文档

| 部件 | 是什么 | 给谁用 |
| --- | --- | --- |
| `mmw-v2/merge-notes/unlazy.md` | subtree 拉取命令、symlink 约定、`## 总原则`（按改动落在判定/审批/scope 等哪层决定收或弃上游）、逐文件逐段意图、`## 审批为什么删` | 拉上游 subtree 的维护 agent |
| `docs/contexts/ticket-run/CONTEXT.md` | ticket-run 限界上下文词汇表；本单元相关词条约 40 条（event、fold、hold、child kind、the kind questions、ledger、gate-check、preflight、closeout、final run 等），多数 `_Home_` 指向本单元文件 | 改词汇的维护者；按 `implement` 读入步骤读 glossary 的 worker |
| `docs/contexts/tickets/CONTEXT.md` | tickets 上下文：acceptance criterion 各行、`met/unmet/abandoned`、`ABANDON:`、blocking edge、labels、lint、lint rule ID、`ERROR`/`WARN` | 同上；写票 agent |
| ADR 0008 / 0012 / 0013 / 0019 / 0026 | 见第 7 节 | 维护者 |
| `mmw-v2/tests/verify-ticket/`（范围外，只列） | 26 个 unittest 文件 + `run.sh`（同时跑 unlazy 两份 node 测试） | 维护者 |

## 2. 内容分类表

「谁在何时读」一列中的「每次」指该读者每次进入这一时刻都读；「分支」指只有进入该分支才读。

### 2.1 `SKILL.md`

| 段 | 内容 | 类型 | 谁、何时读 |
| --- | --- | --- | --- |
| frontmatter `description` | 做什么 + 两个触发分支（开子票；批次即将发布） | 重入与分派（触发） | 每个 host 启动时扫进系统提示，每次 |
| 第 8 行 `Each acceptance criterion … This skill runs them and posts the outcome on the ticket as an event.` | 技能做什么 | 目的与立场（只说了「做什么」，未说谁依赖、做浅的代价） | 加载本技能的 agent，每次 |
| 第 10 行 `The ticket is the only state. Every run reads it fresh… which is the only part any program reads.` | 票是唯一状态；每条评论是事件；首行给人、`<!-- mmw {...} -->` 块给程序 | 带理由的规则 + 命令与接口（事件格式） | 同上，每次；轻量复审把它列为「保留，勿删」（`docs/reviews/2026-09-28-lightweight/verify-ticket.md` `### 保留，勿删` 第一条，已核实原文在） |
| 第 12 行 `A criterion names an oracle by its bare name…` | oracle 为何能裸名调用；手工复现需把目录放上 `PATH` | 做法 + 命令与接口 | 同上，每次读；只在手工重跑 `CHECK:` 的分支用上 |
| `## Find your moment` 第 16 行 | worker 的 claim、跑判据、关票属于 `implement` | 重入与分派 | 每次 |
| `## Find your moment` 表两行 | 开子票 → `sub-issues.md`；发布/已发布/开夜 → `linting.md` | 重入与分派 | 每次 |
| `## Reached from here` | 碰产品、读 `DIFF`/`MISS`/`JOURNEY`/`HARNESS`、无 `.mmw/target.json`、动进程或端口 → `ui-acceptance`，其五条规则约束本技能每次运行 | 重入与分派 + 带理由的规则（约束来源） | 每次读；只在该分支跳转 |

### 2.2 `references/linting.md`

| 段 | 内容 | 类型 | 谁、何时读 |
| --- | --- | --- | --- |
| 第 3 行 | 读者所处时刻 | 重入与分派 | 写票 agent（发布前后）、orchestrator（开夜），进入该分支时 |
| 第 5–9 行代码块 | 三条 `--lint` 命令及各自范围 | 命令与接口 | 同上 |
| 第 11 行第一句 | 图就是 tracker 的 blocking edge，与 `--preflight`、`advance` 用的是同一份，所以边在 tracker 上改，不在票正文改 | 带理由的规则 | 同上；只在 lint 报图问题时用上 |
| 第 11 行第二句 | 批次就绪：`ERROR` 为零，每个 `WARN` 看过并修掉或有意保留 | 做法（完成判据） | 同上 |

### 2.3 `references/sub-issues.md`

| 段 | 内容 | 类型 | 谁、何时读 |
| --- | --- | --- | --- |
| `## When something has to leave this ticket` 命令块 | `--sub-issue <kind> <file>` | 命令与接口 | worker（及 `design-pages` 的 agent），每次开子票 |
| 第 9 行 | 文件首行是子票标题、其余是正文；开在本票下并记录 | 格式与模板 + 命令与接口 | 同上 |
| 第 11 行 `The kind decides who reads the child and when…` | 五种 kind 各在何时由谁读；读者没见过你的会话，所以正文要自足 | 目的与立场 + 带理由的规则 | 同上；2026-09-28 轻量复审定稿 I1 加入（已核实：`docs/reviews/2026-09-28-lightweight/verify-ticket.md` `### 增加` I1 与现文一致，仅 "main agent" 已被 2026-09-29 词汇复查改为 "orchestrator"） |
| `## Which kind it is` 首句 | 按序问 **the kind questions**，第一个 yes 定 kind | 顺序（有序判定） | 同上 |
| 表格（五行 × Question / Kind / Not this kind） | 五级判定梯；每行附反例，反例指回本票该怎么做（修、记 `DECISIONS`、按 `implement` 某条改） | 做法 + 带理由的规则（对照例） | 同上，每次开子票都读全表 |

### 2.4 脚本中给 agent 读的文字（输出、拒绝、`--help`）

这些不是技能文本，但 agent 在运行时读到，归类供下一轮参考：

| 位置 | 类型 |
| --- | --- |
| `verify-ticket.py` `EXIT_CODES`（`--help` 末尾，每种工作的退出码） | 命令与接口 |
| `--preflight` 打印的 `NOT_READY:`/`READY:`/`RESUME: step <k> (<event>)`/`CARRIED:`（`refusals`、`resume_at`、`run_preflight`） | 重入与分派（`RESUME:` 直接给出 `implement` `## Closing steps` 的步号）+ 带理由的规则（每条 `NOT_READY` 带「stop」与原因） |
| `--draft` 写出的收尾评论骨架（`run_draft`：首行、`Branch: … Commit: … PR: none`、每条判据块、`Outside Owns:`、`Review findings:`、`skipped: <fill>`、`Green before work:`、`Sub-issues opened:`、`Counts:`、`Decisions I made on my own`） | 格式与模板 |
| `--closeout` 拒绝时的首行（总数 + `--check-only` 看其余）与 `also:` 行（`_run_closeout`） | 做法 + 命令与接口 |
| `--lint` 的 `ERROR`/`WARN … [<lint rule ID>]` 与 `LINT OK`/`LINT FINDINGS:` 行（`lint_criteria`），`--drafts` 末尾 `DRAFTS_NOT_CHECKED` 两行 | 命令与接口 + 带理由的规则（每条 finding 自带原因与改法；轻量复审据此删掉了 `linting.md` 的规则复述，未逐条核实每条消息都带改法） |

## 3. 连线

### 3.1 本单元产出什么、谁读

| 命令 | 写到 tracker 的东西 | 谁读、读后做什么 |
| --- | --- | --- |
| `--preflight` | assignee；`ticket.claimed` 或 `ticket.refused`（`reason` ∈ `REFUSALS`）；claim 后在 `worker.started.base` 跑不需要产品槽位的判据，写 `ticket.checked` run `baseline` | relay 把 `ticket.refused` 送给 orchestrator（`relay.py` `WAKES`，已核实）；`--draft` 的 `Green before work:` 读 baseline（`green_before_work_block`）；worker 读 stdout 的 `RESUME:` |
| 默认运行 / `--reverify --actor worker` | `ticket.checked` run `self`/`reverify`，含 `counts`、`criteria`、`failed`、`shape`、`slot`、`outside_owns`；无槽位时 `worker.queued` 并 exit 3 | `--decisions` 核对 `Outside Owns`；`--draft` 取 evidence；`--closeout` 的 `verified_problems` 只认 actor worker、commit = HEAD、shape 一致的最新 reverify；relay 在槽位归还时唤醒 `worker.queued` 的 worker |
| `--reverify --actor main` | `ticket.checked` run `reverify`，stage `regress` | `dispatch.sh` reverify（3641 行调用）决定 `ticket.regressed`/`ticket.recovered` |
| `--decisions` | `worker.decided`（`DECISIONS` 评论，两节固定标题） | reviewer 的 Spec axis 逐行判 `reasonable`/`should not`；`--touched`、`--draft` 取句子 |
| `--review`（reviewer 调） | `reviewer.reported`（首行 `REVIEW <base>..<head>`） | relay 唤醒 worker（`WAKES`）；`--draft` 生成 `Review findings:`；`--closeout` 的 `review_finding_problems` 要求每条 `## In-ticket` 行有处理 |
| `--touched` | 在兄弟票上贴 `worker.touched` | 那张票的 worker |
| `--sub-issue` | 新 issue（`needs-triage` + `mmw:child`，native sub-issue）；本票 `child.opened`（`kind`） | `fault`/`contract`/`decision` 经 relay 唤醒 orchestrator（`decision` 按 `night.md` 表格「Nothing; the worker took the default」）；`finding` 由 `dispatch.sh findings` 在收口轮读；`deferred`、`decision` 出现在 `NIGHT SUMMARY` 的 `Sub-issues opened tonight:`（`status.py` 573–602 行，已核实） |
| `--draft` | 本地文件（仓库外），stdout `DRAFT: wrote <path>` | worker 填 `<fill>` |
| `--closeout` | 先按 `.mmw/target.json` `checks` 跑并写 `ticket.checked` run `repo-checks`；push `origin/issue-<n>`；关票或交回 `needs-triage`；交回时先还槽位；最后 `ticket.passed`/`ticket.returned` | relay 唤醒 orchestrator；`advance` 以 `ticket.passed` 合并；`status.py`/board/retro 读 fold |
| `--lint` | 不写任何东西，只打印 | 写票 agent、orchestrator 修票 |
| `--publish --spec-body` / `--drafts` | 新 spec（`mmw:spec`，可挂 map）/ 一批票（native sub-issue、labels、blocking edge），再对发布结果跑一次 lint | `to-spec`、`to-tickets` 的 agent；之后 `dispatch` |

### 3.2 点名的技能、跑的脚本、引用的文档

- 本单元技能文本点名：`implement`（`SKILL.md` 第 16 行；`sub-issues.md` 第 5 行问题的反例列）、`ui-acceptance`（`SKILL.md` `## Reached from here`；`sub-issues.md` 第 1 行问题引其 rules 1、3、4）。
- `verify-ticket.py` 运行：`node gate-check.mjs`、`node gate-lint.mjs`、`gh`（issue view/comment/edit/close/create、api、GraphQL 经 `issue_tree.py`）、`git`、`bash dispatch.sh self`（`own_session`，给 `ticket.refused` 填 session）、`ui-acceptance` 的 `lease.py`（`load_lease` import，`hold_slot`、`judge_run`、`give_slot_back`）、`.mmw/target.json` 的 `checks`、throwaway worktree（`run_baseline`）。`CHECK:` 的 shell 的 `PATH` 前置 `ui-acceptance/scripts`（`main()` 中 `TOOLS` 默认值，`--tools` 覆盖）。
- 反向依赖（别的技能与脚本调用本单元）：见下方 edges。

```edges
skill:verify-ticket/SKILL.md -> ref:verify-ticket/references/sub-issues.md : cites
skill:verify-ticket/SKILL.md -> ref:verify-ticket/references/linting.md : cites
skill:verify-ticket/SKILL.md -> skill:implement : hands-off-to
skill:verify-ticket/SKILL.md -> skill:ui-acceptance : hands-off-to
ref:verify-ticket/references/sub-issues.md -> script:verify-ticket.py#--sub-issue : runs-script
ref:verify-ticket/references/sub-issues.md -> skill:ui-acceptance#Five rules while the product is running : cites
ref:verify-ticket/references/sub-issues.md -> skill:implement#Claim, read in, write the code : cites
ref:verify-ticket/references/linting.md -> script:verify-ticket.py#--lint : runs-script
skill:implement -> script:verify-ticket.py#--preflight : runs-script
skill:implement -> script:verify-ticket.py#(criteria run) : runs-script
skill:implement -> script:verify-ticket.py#--decisions : runs-script
skill:implement -> script:verify-ticket.py#--reverify --actor worker : runs-script
skill:implement -> script:verify-ticket.py#--touched : runs-script
skill:implement -> script:verify-ticket.py#--draft : runs-script
skill:implement -> script:verify-ticket.py#--closeout : runs-script
skill:implement -> script:verify-ticket.py#--sub-issue : runs-script
skill:implement -> ref:verify-ticket/references/sub-issues.md : cites
skill:code-review#session.md -> script:verify-ticket.py#--review : runs-script
skill:to-tickets -> script:verify-ticket.py#--lint --drafts : runs-script
skill:to-tickets -> script:verify-ticket.py#--publish --drafts : runs-script
skill:to-tickets -> script:verify-ticket.py#--lint : runs-script
skill:to-spec -> script:verify-ticket.py#--publish --spec-body : runs-script
skill:dispatch#night.md 1b -> script:verify-ticket.py#--lint : runs-script
skill:dispatch#night.md closing pass -> script:verify-ticket.py#--lint : runs-script
skill:dispatch#night.md -> script:events.py#fold : runs-script
skill:design-pages#pull.md -> script:verify-ticket.py#--sub-issue contract : runs-script
script:dispatch.sh#reverify -> script:verify-ticket.py#--reverify --actor main : runs-script
script:dispatch.sh#run_merge_checks -> script:verify-ticket.py#run_target_json_checks : imports
script:dispatch.sh#ensure_label -> script:verify-ticket.py#ensure_label : imports
script:dispatch.sh -> script:events.py#emit : runs-script
script:dispatch.sh -> script:events.py#fold : runs-script
script:relay.py -> script:events.py : imports
script:status.py -> script:events.py : imports
script:status.py -> script:issue_tree.py : imports
script:watchdog.py -> script:relay.py : imports
script:retro.py -> script:events.py : imports
board:board_data.py -> script:events.py : imports
board:board_data.py -> script:issue_tree.py : imports
board:codeversion.py -> script:events.py : reads
board:codeversion.py -> script:issue_tree.py : reads
script:tool-guard.py -> script:verify-ticket.py#--closeout : cites
script:verify-ticket.py -> script:events.py : imports
script:verify-ticket.py -> script:issue_tree.py : imports
script:verify-ticket.py -> script:gate-check.mjs : runs-script
script:verify-ticket.py#--lint -> script:gate-lint.mjs : runs-script
script:gate-check.mjs -> lib:gates.mjs : imports
script:gate-lint.mjs -> lib:gates.mjs : imports
script:verify-ticket.py -> script:ui-acceptance/lease.py : imports
script:verify-ticket.py -> script:dispatch.sh#self : runs-script
script:verify-ticket.py -> config:.mmw/target.json#checks : configured-by
script:verify-ticket.py -> dir:ui-acceptance/scripts (oracles on CHECK PATH) : configured-by
script:verify-ticket.py#--preflight -> event:ticket.claimed : writes-event
script:verify-ticket.py#--preflight -> event:ticket.refused : writes-event
script:verify-ticket.py#--preflight -> event:ticket.checked(baseline) : writes-event
script:verify-ticket.py#(criteria run) -> event:ticket.checked(self|reverify) : writes-event
script:verify-ticket.py#(criteria run) -> event:worker.queued : writes-event
script:verify-ticket.py#--decisions -> event:worker.decided : writes-event
script:verify-ticket.py#--review -> event:reviewer.reported : writes-event
script:verify-ticket.py#--touched -> event:worker.touched : writes-event
script:verify-ticket.py#--sub-issue -> issue:child (needs-triage, mmw:child) : creates-issue
script:verify-ticket.py#--sub-issue -> event:child.opened : writes-event
script:verify-ticket.py#--closeout -> event:ticket.checked(repo-checks) : writes-event
script:verify-ticket.py#--closeout -> event:ticket.passed : writes-event
script:verify-ticket.py#--closeout -> event:ticket.returned : writes-event
script:verify-ticket.py#--publish -> issue:spec / tickets : creates-issue
event:reviewer.reported -> role:worker : wakes
event:ticket.passed -> role:orchestrator : wakes
event:ticket.returned -> role:orchestrator : wakes
event:ticket.refused -> role:orchestrator : wakes
event:child.opened(fault|contract|decision) -> role:orchestrator : wakes
event:worker.queued -> role:worker : wakes
script:verify-ticket.py#--preflight -> skill:implement#Closing steps : re-enters-at
script:dispatch.sh#advance -> event:ticket.passed : reads
tests:verify-ticket/run.sh -> tests:upstream-unlazy/run-tests.mjs, lint-tests.mjs : runs-script
doc:merge-notes/unlazy.md -> dir:upstream-unlazy : cites
doc:adr/0008 -> script:verify-ticket/scripts/refusal.py : cites
```

自拟关系：`imports` = 以模块方式加载对方文件（Python `spec_from_file_location` 或 JS `import`），比 `reads` 更强，改对方的函数签名会直接坏；`creates-issue` = 在 tracker 上新建 issue。`event:worker.queued -> role:worker : wakes` 的真实触发是槽位归还后 relay 发唤醒（`relay.py` `QUEUED` 常量注释），不是事件本身落地时。最后一条 ADR 0008 的引用是断的，见第 4.2 节。

## 4. 重复

### 4.1 同一意思在全仓出现多处（真重复）

用 grep 在 `mmw-v2/`、`docs/contexts/`、`docs/agents/`、`docs/adr/`、`AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`、`CONTEXT-MAP.md` 查（排除测试与 unlazy 未用文件）。

| # | 内容 | 出现位置 | 判断 |
| --- | --- | --- | --- |
| R1 | 事件 = 首行给人 + 末尾 `<!-- mmw {...} -->` 块是程序唯一读的部分 | `SKILL.md` 第 10 行；`events.py` 模块 docstring；`docs/contexts/ticket-run/CONTEXT.md` **event**；`docs/contexts/night/how-it-works.md` 第 21 行；`dispatch.sh` 第 38 行注释；ADR 0019 正文 | 真重复。技能文本只有 `SKILL.md` 这一份；其余是脚本注释、glossary、ADR |
| R2 | 票是唯一状态、每次现读、不留文件 | `SKILL.md` 第 10 行；`verify-ticket.py` 模块 docstring 第 3–7 行 | 真重复（技能文本与脚本头注释） |
| R3 | oracle 裸名调用，因为 `verify-ticket.py` 把 `ui-acceptance/scripts` 放上 `CHECK:` 的 `PATH` | `SKILL.md` 第 12 行；`SKILL-SET-RULES.md` 第 117 行；`docs/contexts/toolbox/CONTEXT.md` **`--tools`**；`verify-ticket.py` `TOOLS` 注释；`ui-acceptance/SKILL.md` 第 8 行与 `to-tickets/references/cutting-interface-tickets.md` 第 5 行只说「named bare」不说机制 | 前四处真重复；后两处同一事实的另一半，读者不同（写判据的人） |
| R4 | 「流水线本身坏了」的部件清单：`verify-ticket.py`、`dispatch.sh`、oracle script、`lease.py`、hook、`.mmw/target.json` | `sub-issues.md` 表第 1 行；`ui-acceptance/SKILL.md` 第 36 行 rule 5；`ticket-run/CONTEXT.md` **child kind**；`implement/SKILL.md` 第 18 行（短版：`the pipeline's own scripts, a hook, or .mmw/target.json`） | 真重复（轻量复审已指出「五处副本」，现数四处：`events.py` `CHILD_KINDS` 注释只写 `fault, the pipeline itself broken`，不再列部件，已核实） |
| R5 | `contract` 的定义：票被告知要遵守的 baseline、`## Parent` spec 小节或判据缺状态/字段/用例或互相矛盾 | `sub-issues.md` 表第 2 行；`implement/SKILL.md` 第 22 行（多 "interaction"，并说正文写什么、何时结束回合）；`ticket-run/CONTEXT.md` **child kind**；`events.py` `CHILD_KINDS` 注释（短） | 真重复 |
| R6 | `decision` 的定义 | `sub-issues.md` 表第 3 行（`multiple defensible readings would produce observably different outcomes`）；`implement/SKILL.md` 第 23 行（`A question whose answer would change what the ticket delivers`）与 `## Closing steps` 的 `decision` ABANDON 段；`ticket-run/CONTEXT.md` | 同一意思、措辞不同（真重复；两处措辞不一，存在判不同的可能，推断） |
| R7 | `deferred` 的定义（Owns 外、仅为方便的改动） | `sub-issues.md` 表第 5 行；`implement/SKILL.md` 第 28 行；`ticket-run/CONTEXT.md` | 真重复；表第 5 行的反例列又指回 `implement` 该条 |
| R8 | `finding` = review 报告中 Owns 外的缺陷 | `sub-issues.md` 表第 4 行；`implement/SKILL.md` `## Closing steps` 第 3 步末句；`code-review/references/session.md` 分拣；`ticket-run/CONTEXT.md` **review finding** | 真重复（定义）；分拣本身在 `code-review` |
| R9 | kind 决定谁何时读（fault/contract 今晚叫醒 orchestrator 等） | `sub-issues.md` 第 11 行；`ticket-run/CONTEXT.md` **child kind** 末句；执行侧 `relay.py` `WAKES` 与 `night.md` `## 3` 表格 | 前两处真重复；`night.md` 是 orchestrator 自己的动作说明，不算重复 |
| R10 | 「不要结束不是你启动的进程」 | `sub-issues.md` 表第 1 行反例列；`ui-acceptance/SKILL.md` rule 1；`tool-guard.py` 模块 docstring | 真重复（技能文本两处，脚本注释一处） |
| R11 | 三条 `--lint` 命令 | `linting.md` 第 6–8 行；`to-tickets/SKILL.md` 第 7 步（`--lint` + `--drafts`）、第 8 步（spec 号）；`night.md` 第 49 行、第 146 行 | 真重复：每个调用方已写了自己那条命令；`linting.md` 是三者合在一处 |
| R12 | 批次就绪：零 `ERROR`、每个 `WARN` 看过并修或有意保留 | `linting.md` 第 11 行；`to-tickets/SKILL.md` 第 8 步第 157 行 | 真重复，措辞几乎一致 |
| R13 | 图 = tracker blocking edge，与 `--preflight`、`advance` 同源 | `linting.md` 第 11 行；`verify-ticket.py` `ticket_entries` 与 `cross_batch_findings` docstring；`docs/agents/issue-tracker.md`（blocking edge 为「every script reads」的一份，见 tickets CONTEXT **blocking edge** `_Home_`） | 真重复 |
| R14 | `--lint` 退出码 | `verify-ticket.py` `EXIT_CODES`；`night.md` `## 1b` | 部分重复：`night.md` 多一条判断（tracker 读不出时重跑，不改票） |
| R15 | final run 的四个条件（actor worker、commit = HEAD、result、shape） | `verified_problems`；ADR 0026 `## Consequences`；`implement` 第 4 步（只写后两者的一部分）；`ticket-run/CONTEXT.md` **final run** | 真重复（ADR 与 glossary 为维护者副本） |
| R16 | 收尾评论固定行 | `run_draft`（生成）；`draft_problems`（检查）；`ticket-run/CONTEXT.md` 该词条；`implement` 第 7 步（怎么填） | 生成与检查同在脚本；CONTEXT 为 glossary 副本；`implement` 讲填法，不算重复 |
| R17 | ledger 语法解析 | JS `gates.mjs` `parseGates`；Python `verify-ticket.py` `parse_criteria` 与 `ledger_with_results` | 实现层真重复：两份解析器。`parse_criteria` docstring 自述「Three readers… a ticket with a fenced CHECK: could not close」。轻量复审把「用 node 调 `gates.mjs` 统一」列为设计选项、未做（已核实仍为两份） |
| R18 | `GH_ENV`（去掉 `CLICOLOR_FORCE`/`CLICOLOR`） | `events.py` 第 806 行；`issue_tree.py` 第 62 行（`verify-ticket.py` 已改为引用 `events.GH_ENV`） | 真重复，两份（轻量复审时为三份，`bbf19b9f` 减到两份，已核实） |
| R19 | 三组 label 的颜色与说明 | 只在 `verify-ticket.py`（`CLASS_LABELS`/`QUEUE_LABELS`/`GRADE_LABELS`）；`dispatch.sh` `ensure_label` import 它；`docs/agents/issue-tracker.md` 说定义在此 | 不是重复（已合成一份，commit `97b12fb4`） |

### 4.2 只是同词、或引用已失效

- `ALL MET`：收尾评论首行与 gate-check 汇总行同词；`ticket-run/CONTEXT.md` **`ALL MET`** 已写明两者同词。不同物。
- `baseline`（`## Read first` 的已定结论）与 **baseline run**（`ticket.checked` run `baseline`）：`ticket-run/CONTEXT.md` **baseline run** 已声明区分。同词。
- `hold`（事件占用）、`blocker_hold`、night 的 `HOLD` plan line：`ticket-run/CONTEXT.md` **hold** 已声明区分。同词。
- **the kind questions**（本单元）与 `to-tickets` 的 **the five questions**：`ticket-run/CONTEXT.md` `_Avoid_` 已区分。同词相近。
- `lease`：gate-check 内的 OWNS lease（本仓不用）与 `ui-acceptance` 的产品槽位 `lease.py`：同词不同物，本单元文本未混用（推断：agent 读 gate-check 帮助时可能混淆，无证据）。
- 引用失效（非重复，但属同一类「一处写、他处已变」）：
  - ADR 0008 第 16、32 行指向 `mmw-v2/skills/verify-ticket/scripts/refusal.py`，文件现在在 `mmw-v2/skills/ui-acceptance/scripts/refusal.py`（`ls` 已核实；随 `f74eb4f8` 2026-09-06 移出）。轻量复审已报，至今未改。
  - `verify-ticket.py` `resume_at` docstring 说对应 `implement` `## Closing steps` 里「the paragraph starting "A ticket that already carries a run of your own"」；全仓 grep 这句只剩该 docstring 自己，`implement` 现为第 74 行一句「carry on at the step its `RESUME:` line names」。步号 1–5 与现行 `implement` 编号一致（已核实）。
  - `docs/contexts/tickets/CONTEXT.md` **`ERROR`, `WARN`** 说「Only an `ERROR` affects `--lint`'s exit code」，`_Home_` 为 `linting.md`，但 `linting.md` 现文不含这句；事实在 `EXIT_CODES` 与 `lint_criteria`。**lint** 词条 `_Home_` 同为 `linting.md`，所述「gate-lint plus the ticket-graph, worker-label and screen-contract checks」`linting.md` 也不再写。按 `SKILL-SET-RULES.md` `### Vocabulary`「An entry citing a file that does not hold those facts is a finding」。
  - `docs/contexts/toolbox/CONTEXT.md` **`--tools`** `_Home_` 为 `verify-ticket/SKILL.md`，而 `SKILL.md` 不提 `--tools`（它只说 `PATH`）。
  - ADR 0020 正文写 `child.opened`（kind `pipeline` 或 `decision`）唤醒 main；现行 kind 名已改为 `fault`/`contract`，`relay.py` `WAKES` 为 `("contract", "fault", "decision")`。ADR 为决策记录，不算错，只记。

## 5. 上游差异

本单元只有 unlazy 一个上游（`verify-ticket` 本身是本仓自写技能，`mmw-v2/skills.txt` 第 38 行 `self/verify-ticket`）。上游 squash 提交：`c0faf4d7`（2026-09-18，`Squashed 'mmw-v2/upstream-unlazy/' content from commit 16671491`）。`git diff c0faf4d7^{tree} HEAD:mmw-v2/upstream-unlazy --stat` 显示只有 5 个文件不同，其余与上游逐字相同。

| 文件 | 上游行数 | 现行数 | 改了什么 | 性质 | 对应 merge-note（`mmw-v2/merge-notes/unlazy.md`） | 改能力还是写入 MMW 规则 |
| --- | --- | --- | --- | --- | --- | --- |
| `scripts/gate-check.mjs` | 960 | 769 | 删审批：`--approve`、`~/.unlazy/approved`、`approvalExists`/`recordApproval`/`printOracle`、`APPROVAL REQUIRED`/`NOT RUN` 路径、reverify 时「reverify not run」的补记；HELP 改为 `A CHECK runs as written…`；`approvalOracleSignature` 改名 `oracleSignature`（保留：运行中定义被改则丢弃结果） | 删除一项能力（安全边界） | `### scripts/gate-check.mjs` 第一行 + `## 审批为什么删` | 改能力。理由是 MMW 语境：`CHECK:` 由主 agent 写在用户自己的 tracker 上，每次都传 `--approve`，记录以临时 ledger 绝对路径为键从不复用 |
| 同上 | | | 新增 `failureEvidenceFor`；删除 `mustWriteFailure` 条件，失败一律写 evidence（不写 `pending`，不带 `automatic-evidence` 前缀） | 改输出 | 第三行「写回循环里失败的那一支」 | 改能力。依据 2026-09-10 实测 #320、#327（merge-note 原文；commit `e0e92d78` 2026-09-10 `fix(verify-ticket): a failed criterion records why it failed`，已核实提交存在；#320/#327 本身未打开核实） |
| 同上 | | | `insertOrUpdateEvidence` 改用 `gate.attrEnd` 插入 | 随下一行 | 第二行 | 改能力（配合多行 `CHECK:`） |
| `scripts/lib/gates.mjs` | 953 | 999 | `parseGates`：紧跟 `CHECK:` 的围栏代码块是命令；`CHECK:` 下接裸文本报错；同时有值和围栏报错；记 `attrEnd` | 改语法 | `### scripts/lib/gates.mjs` | 改能力（上游多行命令会悄悄截断，merge-note 原文） |
| `scripts/gate-lint.mjs` | 245 | 250 | `tautological-check` 按行拆开判断 | 改判定精度 | `### scripts/gate-lint.mjs` `tautological-check` | 改能力 |
| 同上 | | | `manual-gate` 由 warning 改 error，消息改为「move it to code review… or to its own ready-for-human ticket」 | 改级别与消息 | 同节 `manual-gate` | 把 MMW 规则写进引擎：「验收标准只收机器判得了的事」（commit `1938ec66` `Merge issue-68: 验收标准只收机器判得了的事`，已核实提交存在） |
| `tests/run-tests.mjs` | 659（34 条） | 510（25 条） | 删 15 条 hook/install 测试与审批注入；加 2 条失败 evidence 测试；从 `hardening-tests.mjs` 移入 4 条（去审批） | 测试跟随 | `### tests/run-tests.mjs`（「上游 34 条里留 19 条，加上面 6 条，共 25 条」——条数已用 `grep -c test(` 核实） | 跟随 |
| `tests/lint-tests.mjs` | 398（29 条） | 413（29 条） | 删模板尺寸测试；三条「只是建议」改断言报错；四条补 `CHECK:`/`EXPECT:` | 测试跟随 | `### tests/lint-tests.mjs`（29 条，已核实） | 跟随 |

merge-note 与现码一致性：逐段对照 diff，五个文件的每处改动都有 merge-note 条目，未见无条目的段落（已核实）。merge-note 说 `stop-hook.mjs`、`install-hooks.mjs`、`dispatch-check.mjs` 不接进技能目录：symlink 只有三个（已核实）；但 `lib/` 整目录接入，其中 `dispatch.mjs` 被 `gate-check.mjs` import（`dispatchStatus`），gate-check 自身的 scope/lease/`--claim` 代码也仍在，只是 `verify-ticket.py` 只传显式 ledger 文件、从不传这些选项（推断其不可达，未运行验证）。

merge-note 本身的内容类型：`## 总原则` 与每条「我们的意图」是带理由的规则（给维护者）；`## 审批为什么删` 是带理由的规则；拉取命令与测试入口是命令与接口；`## 未改` 是清单。读者只有拉上游的维护 agent，按分支读（`AGENTS.md` `<important if="you are pulling an upstream subtree…">`）。

## 6. 价值证据

「证据」列：提交号均用 `git log -1` 核实存在；issue 号来自提交说明、代码注释或线索材料，未打开 GitHub 核实的标「issue 未打开」。

| 部件或段落 | 防的失败 | 实地证据 |
| --- | --- | --- |
| `SKILL.md` 第 10 行（票是唯一状态、首行不被程序读） | agent 本地存状态、手敲事件评论、改首行措辞弄坏协议 | ADR 0019 `## 要修的是什么`（首行曾是协议、五种形状）；轻量复审列为保留。无单独事故号 |
| `SKILL.md` 第 12 行（oracle 在 `PATH`） | 手工复现 `CHECK:` 时 `command not found` 不知原因 | 相邻脚本机制 `require_judges` 有证据：docstring 记 2026-09-08 `dispatch.sh reverify` 未传 `--tools`，会把整批票重开交回（已读原文）。这句技能文本本身无独立证据 |
| `SKILL.md` `## Reached from here` | 碰产品、端口、进程时绕过 `ui-acceptance` 五条规则 | 无本单元内证据（ADR 0008 `## 这条规则是从哪一批故障里得出的` 列有租约、端口事故，属 `ui-acceptance`） |
| `sub-issues.md` 第 11 行（kind 决定谁读） | 在 `contract`/`decision` 之间选错；子票正文依赖会话上下文 | 轻量复审定稿 I1，依据是 `night.md` 表格与 `status.py` 代码（已核实代码一致）。无事故号，属「目的」文字 |
| `sub-issues.md` kind 表与顺序 | 一个坏 oracle 同时像 contract 与 fault；把不影响结果的小事开成 decision；杀别人的进程 | 轻量复审 `### 保留，勿删` 的推理；I5-P1（#444–#447 夜 worker 因不可满足的 `CHECK:` 正确停工开子票，未打开 issue）。「杀别人进程」对照例：无本单元事故号 |
| `linting.md` 与 `--lint` | 已发布票的 `CHECK:` 不可满足/判不了，worker 卡住 | I5-P1：#444、#445、#446、#447 连续四夜（证据指 Nowledge retro 记忆与 #409、#490，未打开）；commit `ed4739f7` `fix(#490): --lint refuses the two CHECK shapes that cannot decide their own criterion`；`e5cdd22e` `fix(#541): lint ticket drafts before publishing`；I5-P5：#409 收口新票缺 lint 卡住两轮；`d223b2a1` 夜 1b 对每个 spec 跑 lint |
| `lint_check_effects`（`[shared-state]` WARN） | 一条 `CHECK:` 改分支/票，影响后面的判据 | 无证据（轻量复审「没查到的」同结论；引入提交 `b69d201f` 2026-08-29） |
| `lint_expectations`（`$` 无 `m` 标志） | 永远过不了的 `EXPECT:` 正则 | 引入提交 `b69d201f`；无事故号 |
| `--preflight` 六条拒绝 | 在错分支、别人的票、未就绪或被阻塞的票上开工 | ADR 0008 把 preflight 列为闸口；`e20f546d` blocker 落地才放行；`6810802e` 被叫回的 worker 不再被自己的未提交改动判 dirty-tree。事故号未见 |
| baseline run | 分不清开工前已绿与本票实现的绿 | `8e598d89` `feat(#419): … baseline run`；I3 条目 1 注明「原文未单句陈述」其目的。无事故号 |
| `RESUME:` | 被叫回的 worker 重复已做的步骤 | `ef33c378`（2026-09-28）；`merge-notes/implement.md` 第 137 行：由轻量复审从 `implement` 的 333 词表格移入脚本，理由是阅读负担，不是事故 |
| 失败也写 `EVIDENCE:` | reverify 跑红一次不复现就无从解释 | merge-note 引 #320、#327（2026-09-10 实测，issue 未打开）；`e0e92d78` |
| `TrackerReadError` 与各处捕获 | 网络读失败出 traceback；拒绝信息说错已写入的东西 | I5-P7：#438、#439、#440（issue 未打开）；`0855d553` `fix(#414,#440): make closeout retry safe`；`bbf19b9f` 修三处异常类型（轻量复审 D4，已核实 `ticket_spec`、`blocker_fold`、`run_baseline_if_needed` 现捕 `TrackerReadError`） |
| `closeout_lock`、`completed_closeout`、`unannounced_change` | closeout 被截断后重跑写出重复 `ticket.passed` | I5-P7：#414（外部 #754）；`0855d553`；`6908f2fa` `fix(closeout): a rerun posts the event a closeout could not post after its change` |
| closeout 先还槽再写 `ticket.returned` | 交回后槽位不释放，夜的并行度下降 | I5-P8：#296（25 分钟调查）；`9757e945` |
| `verified_problems`（只认 worker 在 HEAD 上的最新 reverify，shape 一致） | 关票凭旧运行或改过的判据 | ADR 0026；`26924884` `feat(#416): remove verifier from ticket closeout`。「worker 可在 final run 前改写 `CHECK:`」是用户 2026-09-14 接受的残余风险（ADR 0026 原文） |
| `review_finding_problems` | in-ticket finding 被悄悄略过 | `aa9c84b0` `fix(#436)`；`3ddccf17` `fix(#925)`；`af278a55` |
| `run_target_json_checks` | 关票时仓库自己的检查没跑 | `target_config.py` 注释；本仓无 `checks` key（`AGENTS.md` 原文）。无事故号 |
| `--draft` 默认写仓库外 | 草稿进工作树被 `checks` 扫到、挡住关票 | `ebcf6c5f`；`merge-notes/implement.md` 第 37 行 |
| `--decisions` 放在 review 前、`Outside Owns` 需与运行一致 | reviewer 看不到决定 | `e6b932bd`；无事故号 |
| `--touched` | 越界改动没人告诉兄弟票 | 无事故号（`2fd95446` #413 相关的是 Outside Owns 计算） |
| `--sub-issue` 失败后的「do not open it again」 | 重开重复子票 | 轻量复审「不采纳 D3」：重复打开从未发生；唯一诱因随 D4 修复消失（已核实代码） |
| `--publish` | 手工逐张建票出错 | 轻量复审 `汇总.md` 第 122 行：「真实出过 8 张票标题整体错位一格」（未打开原始记录）；`e6a8e5d9` |
| 三组 label 定义一处、缺则建 | 新仓库第一次发票失败 | 轻量复审 `汇总.md` 第 93 行（xiaohuangya 缺 label）；`97b12fb4` |
| `events.py` fold 与 unreadable 拒绝 | 读错票的阶段；runner 只知本机导致重复派工 | ADR 0019 `## 要修的是什么` 四条；ADR 0008 第 3 条 |
| `issue_tree.py` 一次读整树、短页拒答 | 分页未读完读起来像子票更少 | 模块 docstring 的推理与代价计算；`67b25ef9`。无事故号 |
| gate-lint `manual-gate` 升 error | 无 `CHECK:` 的判据只有作者能判 | `1938ec66`（issue-68）；merge-note 理由 |
| gate-check 审批删除 | 每个 host 沙箱都要为仓库外目录放宽；审批从未被人读 | merge-note `## 审批为什么删` 的推理；无事故号 |

## 7. 约束

| 约束 | 出处 | 约束了什么 |
| --- | --- | --- |
| 闸口拒绝要点名事实、给唯一出路、不许静默通过 | ADR 0008 第 10–14 行（点名 `verify-ticket.py` 的 preflight 与 closeout） | `refusals` 每条带原因与「stop」；`_run_closeout` 一次列全部问题；`NOT_RECORDED = 4`（写不进事件不算红）；`require_judges` exit 2 |
| 票状态是事件的 fold；首行不是协议；读不懂的块让决策命令拒绝 | ADR 0019 | `SKILL.md` 第 10 行；`events.py` 全部；`event_problems` 进 closeout |
| 唤醒来自 relay 读票，任何脚本不报信 | ADR 0020（作废 0013 全文，`docs/adr/README.md` 索引「0020（整份作废）」） | `run_review` docstring「Nothing here tells the worker」；ADR 0013 所述 `--review` 发消息已不成立 |
| 取消 verifier；worker final run；`--actor` 必填 | ADR 0026；用户 2026-09-14 接受残余风险 | `main()` 的 `--reverify requires --actor worker\|main`；`verified_problems` |
| out-of-ticket finding 的路由门槛在 `night.md` 第 4 步 | ADR 0012（被 0023 修订） | `sub-issues.md` 中 `finding` 只写「waits for the night's closing pass」，不写路由 |
| 技能文本七条事实 | `SKILL-SET-RULES.md` `## What skill text is for` | 事实 2（脚本做确定性工作，文字只管判断）：三份参考文件被缩到只剩判断，退出码进 `--help`；事实 5（按分支加载）：`linting.md`、`sub-issues.md` 各为一个分支；事实 6、7（一处一家）：R4–R12 属这条下的 finding 候选 |
| `### Load and disclosure`「A rule sits in the text of the agent that must follow it」 | 同上 | worker 的 claim/run/closeout 步骤已全部移入 `implement`（`9308ec7c` 删 `claiming.md`、`closeout.md`、`running-criteria.md`，已核实） |
| `### Paths and host neutrality`「A ticket's `CHECK:` line names no path」 | 同上第 117 行 | `SKILL.md` 第 12 行、`TOOLS` 机制 |
| `### Redundancy and bloat` Over-defense 四问 | 同上 | 轻量复审删 `lint_retired_base`、`review_problems`、`PIPELINE_SCRIPTS[...]["retired"]`、`--timeout`、`IN_TICKET_ITEM_RE`（已核实均已不在代码中；`ROW_ID_RE` 仍在，改作 screen contract 用途，第 3527 行） |
| `### Upstream skills`：改动须有 merge-note | 同上 | `merge-notes/unlazy.md` 的逐段意图表 |
| 拒绝三段结构 | `CODING_STANDARDS.md` 第 10 行（`refusal.py` 在 `ui-acceptance`） | 全部 `refuse()` 文案 |
| Self-hosting boundary | `AGENTS.md` `## Self-hosting boundary` 点名 `verify-ticket.py`、`events.py` | 本仓自跑夜时，不得用仓内改动中的 `verify-ticket.py` 控制当夜运行 |
| label 三组只在一处定义 | `docs/agents/issue-tracker.md`（`verify-ticket.py` 为定义处）；轻量复审 `汇总.md` 第 93 行 | `CLASS_LABELS` 等常量位置 |
| 轻量复审定稿中「不采纳」的用户/主 agent 决定 | `docs/reviews/2026-09-28-lightweight/verify-ticket.md` `### 不采纳` | 不给 `--sub-issue` 加同名去重；不加「Nobody watches…」段；不统一 JS/Python 解析器（本轮） |

## 8. 天然整体

| 整体 | 组成 | 为什么不可分 |
| --- | --- | --- |
| **the kind questions** 表 | `sub-issues.md` 第 11 行 + 第 15 行顺序句 + 五行表（含「Not this kind」列） | 顺序本身是判据（第一个 yes 定 kind，重叠情况靠顺序化解）；反例列是每行的边界。拆行或去掉顺序句，判定变成无序匹配 |
| closeout 事务 | `run_closeout`/`_run_closeout`：锁 → 读票与草稿 → `draft_problems`/`verified_problems`/`review_finding_problems`/`event_problems`/`git_problems` → repo checks → push → 改 tracker → 还槽 → 写事件；`completed_closeout` 与 `unannounced_change` 处理重跑 | 顺序即正确性：事件必须在 tracker 变化之后（docstring 原文「the event … must never stand on a ticket the tracker did not close」）；锁与补写针对 #414/#440。拆成多个命令会重新打开这两个故障 |
| 收尾草稿格式 | `run_draft`（生成骨架）+ `draft_summary`/`rewrite_summary`（首行与 `Counts:` 由脚本算）+ `draft_problems`（检查 `<fill>`、`ABANDON:`） | 同一格式的生产者与检查者在同一文件；拆开需在两处维护同一模板 |
| preflight | `refusals` + claim + `ticket.claimed` + `run_baseline_if_needed` + `resume_at` + `CARRIED:` | 同一次读票与 fold；`dirty-tree` 是否拒绝取决于 claim 是否已归本人，拒绝与 claim 共用状态 |
| 事件词汇与 fold | `events.py` 的 `EVENTS` 表、hold 规则、`fold`/`apply` | fold 的正确性依赖词汇表的每个字段与 hold 规则；它是 dispatch、relay、status、board、retro 共用的库，放在 verify-ticket 目录下是位置问题，不是内容可分（位置本身：轻量复审「只做记录」） |
| 判据运行链 | `write_ledger`（去掉 `TIMEOUT:`）→ `gate-check.mjs`（`parseGates`、`runCheck`、evidence 写回）→ `parse_criteria`/`tally` → `ticket.checked` | ledger 语法、evidence 格式、met 判定（勾选为准、evidence 不能通过）横跨 Python 与 JS 两侧；已有两份解析器（R17），再拆会多一个读者 |
| 产品槽位生命周期 | `verify-ticket.py` `hold_slot`/`give_slot_back`/`worker.queued` + `events.py` `SLOT_ENDS` + `relay.py` `QUEUED` + `ui-acceptance` `lease.py` | 跨三个技能的一条状态机：占槽在首次需要产品的运行，释放在 `SLOT_ENDS` 事件，唤醒在 relay。任何一环单独移动都要改另外两环 |
| `RESUME:` 与 `implement` `## Closing steps` 步号 | `resume_at` 硬编码「step 1…5」 | 脚本输出直接引用另一技能的步号；两者必须同步。这是跨技能耦合，不是一个文件内的整体（`resume_at` docstring 已与 `implement` 现文脱节，见 4.2） |
| unlazy 改动与 merge-note | 五个改动文件 + `merge-notes/unlazy.md` 逐段意图 + `tests/verify-ticket/run.sh` 只跑两份测试 | 下一次 subtree pull 的冲突按 merge-note 解；三者分开会让上游悄悄撤回改动（`merge-notes/README.md` 第 15 行原文） |

不属于天然整体、下一轮可单独判断的：`linting.md` 全文（三条命令各有调用方已写，见 R11/R12，剩下独有的只有第 11 行第一句「边在 tracker 上改」）；`--publish` 与三组 label 定义（能力上属于「发布 spec/票」，不属于「验收」，放在 `verify-ticket.py` 是历史位置，推断）；`issue_tree.py`（被多个技能 import 的读树工具）。

## 未确定

- #320、#327、#414、#438–#440、#296、#409、#444–#447、#490、#541、issue-68 的 GitHub 原文未打开；相关结论只核实到提交说明、代码注释与线索材料。
- `lint_screen_contract` 等约 650 行 screen contract lint、`run_publish_drafts`、`events.apply` 的函数体未读；这些部分的价值证据与重复情况未评估。
- `DRAFTS_NOT_CHECKED` 之外，lint 每条消息是否都带改法（轻量复审删 `linting.md` 的依据）未逐条核实。
- gate-check 的 scope/lease/`--claim` 代码在 `verify-ticket.py` 调用方式下是否确实不可达：只从调用参数推断，未运行验证。
- `mmw-v2/install.sh` 给 pi 写的扩展文件名为 `extensions/mmw-verify-ticket.ts`，而挂的是 dispatch 的 hook（`tool-guard.py`）：只读了 `point(...)` 那一行，文件内容未查，名字是否只是沉积未确定。
- worker 在 `implement` 流程中是否会加载 `verify-ticket` 的 `SKILL.md`（从而读到第 10、12 行）：`implement` 只点名脚本与 `references/sub-issues.md`，是否加载 `SKILL.md` 取决于 host 与模型，未观察到运行记录。
