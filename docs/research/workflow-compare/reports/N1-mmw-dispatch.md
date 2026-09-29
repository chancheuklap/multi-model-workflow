# N1 · MMW 单元清点：dispatch

本文只清点事实，供下一轮按「pstack 组件规范」判断拆不拆、放哪、值不值。不做归置决定。凡「推断」均已标明；凡采用线索材料的结论都标「已核实 / 未核实」。

## 0. 范围、读法与线索核实

### 0.1 读了什么

| 文件 | 读法 |
| --- | --- |
| `mmw-v2/skills/dispatch/SKILL.md`、`references/night.md`、`references/one-ticket.md`、`references/inside-a-ticket.md`、`references/editing-models.md`、`hosts.json` | 全文 |
| `docs/contexts/night/CONTEXT.md`、`docs/contexts/night/how-it-works.md` | 全文 |
| ADR 0009、0010、0016、0017、0018、0020、0021、0022、0023、0024、0025、0027 | 全文；另读了 0012 全文，0008、0026、0031 的标题与前两节，`docs/adr/README.md` 的索引表 |
| `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` | 全文 |
| `scripts/dispatch.sh`（4761 行） | 头注释（1–110 行）、`usage`、入口参数解析与 `case` 分派（4570–4761 行）；以下函数全文：relay 辅助函数与 `ensure_repository_memory`、`own_session`（407–660 行），`open_night`、`open_ticket`、`ack_wake`、`adopt_ticket`、`row_for_role`、`read_ticket`（850–1140 行），`start_session`、`worker_memory_packet`、`reviewer_rules_packet`、`start_one`、`advise_one`、`retract_one`、`resume_one`、`ended_worker_hold`、`wait_one`（1529–2315 行），`check_machine`、`integrate_ticket` 一组（2316–2575 行），`run_merge_checks`、`bounce_goes_to_triage`、`bounce_ticket`（2780–2895 行），`record_landed`、`advance`（3099–3272 行），`land_tickets` 末段，`summary_spec`，`finish_spec`；3280–4600 行其余部分只读了注释、`exit`/`return` 行和 `refuse` 行。**未逐行读**：工作区辅助函数（1137–1528 行）、merge worktree 与锁（2580–2780 行）、`land_one_via_origin`（2895–3098 行）、`suspend_night` 主体、`reverify_spec` 主体、`close_spec_memories` 主体、`route_child` 主体、`finish` 的清理函数 |
| `scripts/relay.py`（1823 行） | 模块文档（1–237 行，含退出码表）、常量与 `WAKES`、`wake_text`、argparse 子命令表 |
| `scripts/watchdog.py`（984 行） | 模块文档（含退出码表与告警原文）、`NEXT` 常量、每条告警的拼字代码、argparse 子命令表 |
| `scripts/turn-guard.py`（340 行）、`scripts/tool-guard.py`（289 行）、`scripts/ghlist.py`（176 行） | 全文 |
| `scripts/statedir.py`（212 行） | 模块文档与 `locked` 以前全部；末尾约 20 行未读 |
| `scripts/status.py`（932 行） | 模块文档、函数目录、`parse_args`、`main` |
| `scripts/models.py`（1275 行） | 模块文档、常量、`runner_name` 至 `main`（1120–1275 行） |
| `scripts/runners/paseo.sh`、`orca.sh`、`herdr.sh` | 头注释（含 `# MMW_USES:`）与动词分派；未读各动词实现 |

未运行任何会改状态的命令。运行过的只读命令：`git log`、`git show`、`git ls-files`、`gh issue view`、`gh search issues`、`nmem m search`、读取 `~/.mmw/state/*/watchdog.json` 与 `relay.log`。

### 0.2 线索材料的使用与核实

| 线索 | 采用的内容 | 状态 |
| --- | --- | --- |
| `docs/reviews/2026-09-28-lightweight/dispatch.md` | 当时 night.md 的删改清单 I1–I7、D1–D15；脚本死代码清单 | 已核实：提交 `61fd4fe6` 的说明写明"Applies … 定稿 in full"，现文件含 I1、I2、I3、I4、I5、I6、I7 原句，`findings`、`memory-list` 子命令与 `advance` 的第二次 frontier 计算都在。脚本清单第 1 条（`--json | --run` 拒绝）与第 5 条（`extra` 恒非空）**仍在** `dispatch.sh`，即脚本清理未做（已核实） |
| `docs/research/workflow-compare/reports/M2-mmw-night.md` | 阶段表、`finish_preflight` 要求同 base branch 的票全关 | 阶段表逐项对照 night.md 与 `dispatch.sh` 已核实；`finish_preflight` 内部条件只读到 stderr 文本（"no spec.retroed"、"open nights into"、"specs that used"），逐票关闭一条**未核实** |
| `I2-mmw-night-intent.json` | 各元素的意图与 ADR 出处 | 引用的 ADR 段落已逐条回原文核实；"reverify 的设计理由原文未写"一条同意（本次所读 ADR 中也没有） |
| `I5-mmw-field-evidence.json` | 故障与处置 | #406、#407、#296、#408、#507 标题已用 `gh issue view` 核实；提交 `2b560899`、`8b3f9395`、`0855d553`、`cae2de26` 已核实存在且说明相符；Memory 里的 retro 记录**未打开核实** |
| `T2-night.json` | 各组件的外部来源（mattpocock implement-spec、firstmate、unlazy） | 只核实了 implement-spec 原文与 `turn-guard.py` 自述的 firstmate 出处；其余来源链**未核实** |
| `docs/reviews/2026-09-23-skill-set/汇总.md`、`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` | how-it-works 移出技能、night.md 词数、词表决定 | 用作背景，未逐条核实 |
| `docs/research/mmw-structure/2026-09-06-handoff.md` | "技能按 agent 所处的时刻划分"的早期结论 | 未核实其是否仍是现行判断 |
| Nowledge Mem | 用户 2026-09-29 的两条决定（见 7.4） | 记录本身已读到；未对照原对话核实 |

## 1. 部件清单

词数用 `wc -w`，行数用 `wc -l`。`scripts/__pycache__/` 未被 git 跟踪（`.gitignore` 第 9 行），不计。

| 文件 | 规模 | 是什么 | 给谁用 |
| --- | --- | --- | --- |
| `SKILL.md` | 28 行 / 388 词 | 技能入口：`description`、按角色分到六个 moment 的表、所有被唤醒者共用的 `## On waking` | 每个 host 在会话开始时扫描 `description`；worker、自己拿票的会话、orchestrator、改模型配置的会话、开 task board 的会话都先读全文 |
| `references/night.md` | 210 行 / 3598 词 | 一夜的顺序：重入表、`check`/`open`、lint、`advance`、每次被唤醒的处理表、closing pass、`reverify`/`summary`/retro、`finish`、`suspend` | orchestrator，整夜每次被唤醒都读 |
| `references/one-ticket.md` | 14 行 / 349 词 | 夜外单票的四步：`open-ticket`、`start`、处理唤醒、`land` | 在夜外给一张票起 worker 的会话 |
| `references/inside-a-ticket.md` | 13 行 / 177 词 | 自己拿票的会话先跑 `adopt`；夜外 adopt 之后的收尾 | 没有 `start` 在背后的 worker 会话 |
| `references/editing-models.md` | 27 行 / 326 词 | 用 `models.py config set` / `config runner` 改角色与 runner；runner 能力差异要告诉用户 | 被用户要求改模型或 runner 的会话 |
| `hosts.json` | 61 行 | 首次安装的默认四行（`junior-worker` grok、`senior-worker` codex、`reviewer` claude `opus[1m]`、`advisor` claude `fable[1m]`）与每个 host 的 CLI 参数、Paseo settings | `models.py`（展开启动参数）、`install.sh`（首装默认值） |
| `scripts/dispatch.sh` | 4761 行 | 26 个子命令：开夜、推进、落地、起会话、送消息、撤回、挂起、复验、收夜、合回、路由 finding，以及拼启动提示词 | orchestrator、worker（`integrate`、`start … reviewer`、`wait`、`ack`、`adopt`）、reviewer 的 Spec axis（`integrated`）、advisor 调用方（`advise`）、`verify-ticket.py`（`self`） |
| `scripts/relay.py` | 1823 行 | 每仓库一个常驻进程：读被 watch 的票的评论，把 `WAKES` 里的事件翻成 `#<n> <event>`，经收件人的 runner `send` 送达，等 `ack` 出队 | `dispatch.sh`（`start`/`stop`/`watching`/`ack`）；维护者用 `queue` 排障 |
| `scripts/watchdog.py` | 984 行 | 判活第二、三层：查 relay 是否在跑、在读；问沉默票的 runner 会话是否还在；写 `worker.lost`/`reviewer.lost`；把告警直接发给 orchestrator | `turn-guard.py`（`arm`）；维护者（`status`） |
| `scripts/turn-guard.py` | 340 行 | 判活第一层：挂在五个 host 回合结束事件上的 hook，只对 orchestrator 生效，watchdog 不健康且有票被占时拦住回合 | host（由 `install.sh` 注册） |
| `scripts/tool-guard.py` | 289 行 | 在 `issue-<n>` 工作树里拒绝三件事：手工关票或改队列 label、弹出提问、结束进程 | host（由 `install.sh` 注册为 pretool 与 question hook）；受约束的是 worker 与 reviewer |
| `scripts/status.py` | 932 行 | 只读：从 tracker 与事件折叠算出表格、`advance`/`reverify`/`land` 的计划行、worker 分级、summary 正文、closeout 就绪判断、未路由 finding | `dispatch.sh` |
| `scripts/models.py` | 1275 行 | 读写 `~/.mmw/models.json`（锁、版本、原子替换）、扫描 host 目录、选 runner、拼 host 启动参数 | `dispatch.sh`、runner 适配器、`install.sh`、task board（`mmw-v2/board/settings_api.py`）、用户经 `config` 子命令 |
| `scripts/statedir.py` | 212 行 | 每仓库本机状态目录 `$MMW_HOME/state/<owner>__<name>/` 与带进程身份的文件锁 | `relay.py`、`watchdog.py`、`turn-guard.py`、`models.py`、`mmw-v2/board/supervisor.py`；`lease.py` 注释称它为 canonical reader |
| `scripts/ghlist.py` | 176 行 | 带 ETag 条件请求的 GitHub REST 分页读取 | `relay.py`；`mmw-v2/board/codeversion.py` 把它列为 board 依赖 |
| `scripts/runners/paseo.sh` / `orca.sh` / `herdr.sh` | 236 / 593 / 359 行 | runner 适配器：`start`、`send`、`liveness`、`stop`、`self`、`attach`、`open-url`（Paseo 另有 `catalog-status`、`catalog-models`、`diagnostic`）；头部 `# MMW_USES:` 供 `install.sh --check` 核对 CLI | `dispatch.sh`、`relay.py`、`watchdog.py`、`turn-guard.py` |
| `docs/contexts/night/CONTEXT.md` | 434 行 | night 语境的词表（Roles、Places、Branches、Dispatch、Models、命令、Liveness、Retro） | 改词汇或技能文本的维护者；不被夜里的 agent 加载（推断：技能文本不指向它） |
| `docs/contexts/night/how-it-works.md` | 93 行 | 命令底层机制的维护者说明 | 改 `dispatch.sh`、`relay.py`、`watchdog.py`、`status.py`、`turn-guard.py` 的人（首行原文） |
| ADR 0009、0010、0016、0017、0018、0020–0025、0027 | 20–39 行/篇 | 夜间编排、唤醒、判活、runner 边界、models.json、origin base branch、project branch、bounce 的决定与被否方案 | 维护者 |

## 2. 内容分类表

类型缩写：**顺序**、**做法**、**规则+理由**、**命令接口**、**重入分派**、**格式模板**、**目的立场**、**沉积**。"读者/时刻"说明谁在什么时候读、每次还是某分支。

### 2.1 `SKILL.md`

| 段 | 内容摘要（原文开头） | 类型 | 读者/时刻 |
| --- | --- | --- | --- |
| frontmatter `description` | "Start a reviewer from inside a ticket, run a night as its orchestrator, run one ticket outside a night, change the host, model, reasoning effort or runner, or open the local task board." | 重入分派（触发条件） | 所有 host 在每个会话开始时扫描 |
| 第 8 行 | "Choose the moment that matches your role. Where you are is what the ticket's events say, not what this session remembers. `bash scripts/dispatch.sh` finds the scripts … so no path is ever passed to it." | 重入分派 + 规则+理由（以票上事件定位，不凭会话记忆）+ 命令接口 | 每个读者，每次 |
| 第 12 行 | "A **night** is one run of a spec's published tickets under one orchestrator, from `open` to `summary`, at any hour." | 目的立场（定义） | 每个读者 |
| `## Find your moment` 表 | 六行：1 worker（去 `implement` 的 `## Closing steps`）、2 自拿票、3 orchestrator、4 夜外单票、5 改模型/runner、6 开 task board（行内给命令与退出码） | 重入分派；第 6 行含命令接口 | 每个读者，每次 |
| `## On waking` 1–4 | 重跑被打断的命令 → 读票 → `ack`（"Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked."）→ 按本 moment 的文件行动 | 顺序 + 规则+理由 + 命令接口 | 每次被唤醒的 worker、orchestrator、自拿票会话 |

### 2.2 `references/inside-a-ticket.md`

| 段 | 摘要 | 类型 | 读者/时刻 |
| --- | --- | --- | --- |
| 开头两段 | 先跑 `adopt <n>`；"Without it no event names your session, so your reviewer's report would wake nobody, and `start <n> reviewer` would refuse." | 顺序 + 规则+理由 | moment 2，一次，claim 之前（由 `implement` 开工段指来） |
| `## Exit codes` | `adopt <n> [--into <branch>]` 从哪个工作树跑、夜外加 `--into`；exit 2 | 命令接口 | 同上 |
| `## After the closeout` | 夜外 adopt 的票没有 orchestrator：ack 自己的 `ticket.passed`/`ticket.returned`，告诉用户跑 `land`；"Do not run `land` from this worker session: it stops every session the ticket's events name, including this one." | 顺序 + 规则+理由 | 只在"夜外 adopt"这一分支，关票之后 |

### 2.3 `references/one-ticket.md`

| 段 | 摘要 | 类型 | 读者/时刻 |
| --- | --- | --- | --- |
| 第 3 行 | "A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending." 唤醒处理见 SKILL.md | 目的立场 + 指针 | moment 4，每次 |
| 步 1–2 | `open-ticket <n>`（交出 board URL）→ `start <n> worker`（从目标分支的 checkout，分支须在 origin），结束回合 | 顺序 + 命令接口 | 同上，开头一次 |
| 步 3 | 被唤醒的四种事件各自怎么做：`worker.lost`、`ticket.refused`、`child.opened`（fault / decision）；`contract`、`watchdog:`、`MMW turn guard:` 按 night.md 第 3 节处理，把其中的 `status` 换成 `events.py fold <n>` | 重入分派 + 做法；最后一条是跳到 night.md 的指针 | 每次被唤醒 |
| 步 4 | `land <n>`；"Done when `land` exits 0"；夜外 bounce 直接进 `needs-triage`，告诉用户 | 顺序 + 命令接口 + 完成判据 | 结尾一次 |

### 2.4 `references/editing-models.md`

| 段 | 摘要 | 类型 | 读者/时刻 |
| --- | --- | --- | --- |
| 开头 | 只在用户下令时读；"Change it only through the commands below." | 重入分派 + 规则（禁止手改） | moment 5 |
| `## Change one role` | `models.py config set <role> <host> <model> <level>`；四个角色；把档位放进模型名的 host（model-and-level pair）、`fast` 属于模型名、只有开关的 thinking option | 命令接口 + 做法 | 同上 |
| `## Change the runner` | `config runner <runner>`、`config show`；下次 `start` 生效 | 命令接口 | 同上 |
| 最后一段 | 不能观察会话内程序的 runner 对每次 `resume` 和唤醒都答 exit 4；"tell the user of it when the runner changes" | 规则+理由（转告用户） | 只在改 runner 分支 |

### 2.5 `references/night.md`（按小节，括号内为本节词数）

| 段 | 摘要 | 类型 | 读者/时刻 |
| --- | --- | --- | --- |
| 开头第 1 段（开头五段与重入表共 439 词） | "You are the orchestrator. … The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: …" | 目的立场 | orchestrator，每次进入 |
| 第 2 段 | 早上用户冷读 `NIGHT SUMMARY`、`NIGHT RETRO` 与 tracker，所以每个决定的理由写进 child、票或 spec 上能独立读懂的评论 | 目的立场 + 规则+理由 | 同上 |
| 第 3 段 | "The night's output is a batch the user can accept in the morning, not a count of closed tickets. … a criterion loosened, or a worker resumed again and again with `continue`, to make one close is a defect that lands under a green mark." | 目的立场（点名诱惑） | 同上 |
| 第 4 段 | 本文件是夜的顺序；唤醒怎么到、到了怎么办在 SKILL.md | 指针 | 同上 |
| 第 5 段 | "Between the steps below you end your turn. … nothing else does, and no agent polls another." | 规则+理由 | 同上 |
| "Find where you are" 表 | 六行，以 spec 上的事件（`spec.opened`、`spec.suspended`、`spec.closed`、`spec.retroed`）与 `status` 输出判定从哪一节进 | 重入分派 | 每次进入 |
| `## 1.`（139） | 从 base branch 的 checkout 跑 `check`、`open`；两者退出码；第一条消息交出 board URL | 顺序 + 命令接口 + 做法 | 开夜一次 |
| `## 1b.`（126） | `verify-ticket.py <spec> --lint` 的退出码；tracker 没回答（`[parent-unreadable]` 等）要重跑而不是改票；UI 批次另跑 `ui-acceptance` 的 `target_config.py --check` | 命令接口 + 做法；最后一段只在 UI 批次分支 | 开夜一次 |
| `## 2.`（111） | `advance` 的退出码 0 / 4 / 2 及各自下一步 | 命令接口 | 第一次 advance；第 3 节借用 |
| `## 3.` 步 1–5 | ack → `status` → 处理表匹配的每一行 → `advance` 一次 → frontier 空且无活 agent 则进第 4 节 | 顺序 | 每次被唤醒 |
| `## 3.` 表（15 行） | `ticket.passed`、继续 worker（`resume`）、`fault`（本仓环境自己修；流水线脚本不在夜里修补，告诉用户，必要时 suspend）、`contract`、`contract` 指向 Claude Design 页面、`decision`、`ticket.returned`、bounce、`ticket.refused`、`worker.lost`、`relay.recovered`、会话没了但资源还占着（`retract`）、`watchdog: #<n> silent since …`（先查开着的 contract child）、其他活 worker、换 worker 分级 | 重入分派 + 做法；`fault` 行含理由 | 每次被唤醒，按行匹配 |
| "While a worker holds a ticket …" | 票被 worker 占着时代码归 worker；orchestrator 只改 worker 的依据并用 `resume` 告知；自己的修复等到 closing pass | 规则+理由 | 每次被唤醒 |
| contract 权威顺序段 | "decision tickets and ADRs, then the spec, then the design package or the screen contract, …, then domain documents, then the ticket body"；能引到更高权威时自己改、要留的评论内容、`route … fixed`、`resume` 附修正 | 规则+理由 + 做法 + 格式（child 评论要写的四项） | 只在 `contract` 分支 |
| "When no authority settles …" | 推翻用户决定或扩 spec 时，把未开始的派生票移到 `needs-triage`，在 child 上写选项、建议与移动的票号 | 规则+理由 + 做法 | 只在 `contract` 无权威分支 |
| `### Exit codes of resume`（51） | exit 3 后再发要让两条消息读成一条；替换的 worker 没有旧会话里的指示，要重发 | 做法 | 只在 `resume` 分支 |
| `## 4.` 开头两段（本节共 1197 词） | frontier 空、无活 agent 时路由 `finding`；用 `findings <spec>` 列出，"A finding wakes nobody, so the ones you were woken about are no measure of what exists." | 顺序 + 规则+理由 | closing pass，每轮 |
| `route` 三种写法与退出码 | `fixed` / `stale <invalid|fixed-elsewhere>` / `became-ticket <n>`；exit 1 重跑、exit 2 什么都没做 | 命令接口 | 同上 |
| Step 0 与四步判据 | 先对当前 `HEAD` 核 finding 的条件；再按"在另一张开着的票的 `## Owns` 里 → 票""判据本身的缺口 → senior 票加 negative control""两个以上文件且有设计咬合 → senior 票"与"默认自己改"判；每步带理由（"Not a question of size: the constraint is concurrency"、"Counting files is not counting effort"、"A name echoed through prose is not a coupling"） | 规则+理由（先匹配者胜的判定程序） | 同上，每条 finding |
| 自己修的做法 + 三条提交规则 | 用跟踪 `origin/<into>` 的 checkout、fetch、提交、跑测试、fast-forward push，被拒则合并重试；一个提交一条或一组同源 finding；只动原因需要的与证明它的测试；commit message 引用看到的测试行（`ran 188 skipped 0`） | 做法 + 格式模板（commit message） | 同上，"自己改"分支 |
| 变成票的做法 | 票尽量少；落在活票 `## Owns` 的要 `Blocked by`；原地改写成票或合并进新票各用哪种 `route` | 做法 | "开票"分支 |
| 新票的写法 | 按 `to-tickets` 的 `<issue-template>` 与四行判据；"Two shapes come back from a night's findings and neither is a criterion"（无命令的规则散文；全仓检查器放进 `CHECK:`） | 规则+理由 + 格式模板（指向 `to-tickets`） | "开票"分支 |
| lint 新票 | `verify-ticket.py <n> --lint`，退出码同 1b | 命令接口 | "开票"分支 |
| Memory 收口的目的段 | 这些记录经 `mmw-experience` 标签进入后来 worker 的开工提示；夜中为真的记录落地后可能变假；对照落地结果判 | 目的立场 | closing pass 末尾，每夜一次 |
| `memory-list` 与四种决定 | 跑 `memory-list <spec>` 存文件；`retain`/`propose`/`deprecate`/`supersede` 的含义；`propose` 的 `evidence` 只能是一条事件评论 URL 或 commit URL（retro 只在它等于问题来源时计入，`summary` 拒绝其他值） | 命令接口 + 格式模板 + 规则+理由 | 同上 |
| "Keep the file for step 5. Done when …" | 完成判据 | 格式（完成判据） | 同上 |
| 循环段 | 再跑 `advance`；每个 `ticket.passed` 回到第 3 节；frontier 再空时重来，直到没有 open finding | 顺序 | 同上 |
| `## 5.`（272） | `reverify` → `summary --memory-decisions`，各自退出码；修复重开的票后再 `reverify`；`summary` 拒绝 Memory 文件时重列重写；"Tickets left for human acceptance … are valid outcomes"；`spec.closed` 后立即在同一会话调用 `retro` 技能；然后告诉用户 | 顺序 + 命令接口 + 规则+理由 + 交接 | 夜末一次 |
| `## 6.`（108） | 用户验收后才跑 `finish`；保留签出 base branch 的工作树并给出删除命令；退出码；"Do not merge the project branch into the repository default branch here; that remains the user's release decision." | 命令接口 + 规则+理由 | 验收后一次 |
| `## Suspending the night`（195） | 何时值得挂起（故障在流水线而不在票）；挂起后不再唤醒任何人、工作区与分支保留；怎么恢复；退出码与 `lease.py release` 的处理；Done when | 规则+理由 + 命令接口 + 完成判据 | 只在挂起分支 |

**沉积**：技能文本（SKILL.md 与四个 reference）里没有找到。`grep` "no longer / used to / now / 2026 / #三位数" 只命中 `deprecate` 的定义"is no longer valid"（定义本身）。沉积在脚本与维护者文档里：`dispatch.sh` 入口的 `--json | --run) refuse "$1 is no longer a flag"`；`turn-guard.py` 头部 2026-09-10 的五个 host 实测记录（`CODING_STANDARDS.md` 要求脚本头记录这类实测，按 `SKILL-SET-RULES.md` Sediment 表也属合法归宿）；`how-it-works.md` `## How advance processes a batch` 里的"(ADR 0027)"。

### 2.6 维护者文档（粗分）

| 文件与小节 | 类型 |
| --- | --- |
| `how-it-works.md` `## Starting a session`、`## Events and holds`、`## Results, watches and wakes`、`## The watchdog and turn guard`、`## Opening a night`、`## How advance processes a batch`、`## Interpreting a night`、`## Reverify and summary` | 命令接口（行为规格）为主，夹带规则+理由（如"A start the runner refuses is refused once … no retry and no other host or runner"） |
| `CONTEXT.md` 各词条 | 定义；个别词条含行为规则（如 **wake**"which is not acked"） |
| ADR 各篇 | 规则+理由 + 被否方案 + 沉积（它们的主题就是决定与变更，按用户规则 13 属合法） |

### 2.7 各类型的分布（技能文本，按上表段数，推断性质的粗计）

- night.md 约 3600 词中，命令接口与重入分派（重入表、第 3 节表、各退出码段）约占一半；规则+理由集中在开头四段、第 3 节表下三段、第 4 节判据与新票写法、第 5 节"valid outcomes"、第 6 节末句、挂起判据。
- 顺序只有四处真正依赖先后：`## On waking` 1–4、第 3 节步 1–5、第 5 节 `reverify → summary → retro → 告诉用户 → finish`、one-ticket 的 `open-ticket → start → 唤醒 → land`。

## 3. 连线

### 3.1 本单元产出的工件与事件，谁读

| 产出 | 写者 | 读者 |
| --- | --- | --- |
| 事件 `spec.opened`（runner、session、`into`、`project`） | `dispatch.sh open` | `status.py`、`dispatch.sh`（`resolve_into`、`revive_night_watch`、`finish`）、`retro.py`（night's base commit）、night.md 重入表 |
| `worker.started` / `reviewer.started`（session、runner、machine、host、model、effort、grade、worktree、branch、base、into；adopt 另加 `adopted=true`） | `start`、`adopt` | `events.py` fold；`relay.py`（worker 身份）；`watchdog.py`（问哪个 runner、哪台机器）；`resume`/`retract`/`land`/`suspend`；code-review 的 Spec axis 经 `integrated` 读 base |
| `worker.replaced`、`worker.retracted`、`worker.resumed` | `start`、`retract`、`resume` | fold（结束或恢复 hold） |
| `ticket.released`（reason `worker-lost` / `suspended` / `landed`） | `advance`、`suspend`、`land` | fold |
| `ticket.landed`（commit、merge、base、compare 链接）、`ticket.bounced`（files 或 commands） | `advance`、`land` | fold；阻塞票的 frontier；`summary` 的 `Bounced:` 行；triage |
| `ticket.regressed`、`ticket.recovered` | `reverify` | fold；`summary`；triage |
| `child.closed`（resolution、reason、became） | `route` | `summary` 的 `Findings routed:`；retro |
| `spec.suspended`、`spec.closed`（`NIGHT SUMMARY`、`memory_closing`）、`spec.merged` | `suspend`、`summary`、`finish` | 早上的用户；`retro`（需要 `spec.closed`）；`finish`（需要 `spec.retroed`） |
| `worker.lost`、`reviewer.lost` | `watchdog.py`（唯一写者） | relay → orchestrator / worker |
| 标签与指派：`needs-triage`/`ready-for-agent` 互换、`mmw:ticket`、去掉 `@me` 指派、reopen/close | `bounce_ticket`、`reverify`、`route`、`advance`、`suspend` | tracker 队列；triage；frontier |
| 唤醒 `#<n> <event>`、`relay.recovered since <time>` | `relay.py` | worker 或 orchestrator 的会话（经 runner `send`） |
| 告警 `watchdog: …`、`MMW turn guard: …` | `watchdog.py`、`turn-guard.py` | orchestrator |
| 本机文件：`.worktrees/issue-<n>`、`.worktrees/merge-<slug>`、`merge-<slug>.lock`、`<git common dir>/mmw-reverify-<spec>`、状态目录下 `watches.json`、`queue.jsonl`、`seen.json`、`beat.json`、`gap.json`、`watchdog.json`、`guard.log` 等 | `dispatch.sh`、relay、watchdog、turn guard | 同组脚本；`summary`（reverify receipt）；task board（`mmw-v2/board/` 引入 `models.py`、`statedir.py`、`ghlist.py`） |
| `~/.mmw/models.json` | `models.py config`（及 board、install） | `dispatch.sh start`、`advise`、`check`；board |
| Memory：repository Space `<owner>__<name>` 的创建或修复；Memory 记录的 `deprecate`/`supersede` | `ensure_repository_memory`、`close_spec_memories` | 后来 worker 的开工提示；retro |

### 3.2 `dispatch.sh` 拼出的启动提示词与发给 orchestrator 的文本（摘录原文）

**worker**（`start_one`，`case "$kind"` 的 `worker)` 分支；标题 `#<n> worker`；环境变量 `NMEM_SPACE=<space>`、`NMEM_AGENT_ID=mmw-worker`、`MMW_TASK_SCOPE=<scope 或空>`、`MMW_SPEC`、`MMW_TICKET`）：

```
Use the implement skill to work ticket #<n>. You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. Several tickets run on this machine at once. Before you start, reach or stop the product, read 'Five rules while the product is running' in the ui-acceptance skill.

Shared experience for ticket #<n>.

MMW repository Space: <space>
MMW task root: <map #m | standalone spec #s | unavailable: …>
MMW task scope: <mmw-map-m | mmw-spec-s | unavailable: …>

Current task shared experience:
<最多 30 行索引 | none | unavailable: …>

Related experience:
<最多 15 行索引 | none | unavailable: … | partial: …>

These are indexes, not the records; the implement skill's `## Shared experience while implementing` says how to use them.
```

两句常量在 `dispatch.sh` 第 108–109 行：`AUTONOMOUS` 与 `PRODUCT_RULES`。Memory 部分由 `worker_memory_packet` 生成：按 task scope label 列 30 条；对 `## Owns` 前 8 条路径与票、spec、map 标题各做一次 `mmw-experience` 搜索（每次 10 条），合并取 15 条；每行是 `{"id","title","applies"(正文首行，截 200 字),"space"}`。Nowledge 失败写进提示词，不阻止开工（ADR 0031）。

**reviewer**（`reviewer)` 分支；标题 `#<n> reviewer`；环境变量 `NMEM_SPACE`、`NMEM_AGENT_ID=mmw-reviewer`）：

```
Use the code-review skill to review ticket #<n> from base commit <base>. You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work.

Active reviewer Rules approved for this review:
<每条 {"id","title","body","scope","source"} 一行 | none | unavailable: <reason>>
```

Rules 由 `reviewer_rules_packet` 从 `nmem context read --agent-id mmw-reviewer` 的 `rule_stack`（global/owner/space/agent）读出；怎么用只写在 `code-review` 的 `references/session.md` `## Active Rules`（函数注释与 `mmw-v2/merge-notes/code-review.md` 第 155 行都这么说）。

**advisor**（`advise_one`；标题 `advisor <pid>`；不写事件）：

```
Use the advisor skill.
<brief 文件全文>
```

**orchestrator**：`dispatch.sh` 不启动 orchestrator（用户启动它，CONTEXT **orchestrator**）。它从脚本收到的文本是：
- `open` 的 stdout：`opened #<spec>: wake-ups go to <runner> session <session>; task board <url>`
- relay 的唤醒：`#<n> <event>` 或 `relay.recovered since <time>`（`relay.py` `wake_text`）
- watchdog 告警，每条以 `watchdog:` 开头并带下一步，例如 idle 告警末尾附一整句要 `resume` 的文字："You ended your turn with no result on the ticket. Carry on from where its events say you are. If something outside your code stops you, open a fault sub-issue …"；liveness unknown 告警写 "dispatch.sh resume <n> \"Say in one line where you are, then continue\", and act on its exit as night.md's Exit codes of resume says"
- turn guard 的拦截文字："MMW turn guard: the night on <repo> has held tickets (…) and its watchdog is not healthy: … Run `python3 …/watchdog.py arm --repo <repo>`, act on what it prints; if it exits non-zero, open a `fault` child on any held ticket with that command and its output. Then end your turn."
- 每个子命令的 stderr 拒绝（"Every refusal names its next step on stderr"，`dispatch.sh` 头注释）

### 3.3 点名调用的技能、运行的脚本、引用的文档

- 技能文本点名的技能：`implement`（SKILL.md moment 1）、`verify-ticket`（night.md 1b、第 3、4 节的 `--lint` 与 `events.py fold`）、`ui-acceptance`（`target_config.py --check`；`lease.py release`）、`design-pages`（`references/pull.md`）、`to-spec`（`references/revising-a-spec.md`）、`to-tickets`（`<issue-template>` 与第 4 步判据形状）、`retro`（第 5 节）。
- 脚本输出点名的技能：`resolving-merge-conflicts`（`integrate_conflict_report`）、`implement`、`code-review`、`advisor`（启动提示词）、`ui-acceptance`（`PRODUCT_RULES`）。
- 反向：点名 dispatch 的技能：`implement`（`integrate`、`start … reviewer`、`wait`、`ack`、`inside-a-ticket.md`）、`code-review` 的 `references/spec-reviewer.md`（`integrated`）、`to-tickets` 结尾（交给 dispatch 开夜）、`retro`（由 `summary` 触发，结束后回到 night.md `## 5`）、`triage`（`route`、`advance`、单票路径）、`design-pages` `references/pull.md`（`reverify`、`route`、`resume`）、`advisor` `references/consulting.md`（`advise`）、`ui-acceptance` SKILL.md（relay 只为事件唤醒）、`setup-matt-pocock-skills` 的 `issue-tracker-github.md`（`route`）、`ask-matt`（未列入 `mmw-v2/skills.txt`，不安装）。
- 脚本层的外部调用：`verify-ticket.py` 调 `dispatch.sh self`（其 `own_session` docstring 与第 254 行）；`install.sh` 注册两个 hook、导入 `models.py` 写 `models.json`；`mmw-v2/board/` 导入 `models.py`、`statedir.py`、`ghlist.py`。

### 3.4 edges

```edges
host -> dispatch/SKILL.md : reads (description 扫描)
dispatch/SKILL.md -> implement : hands-off-to (moment 1 读 implement ## Closing steps)
dispatch/SKILL.md -> references/inside-a-ticket.md : re-enters-at (moment 2)
dispatch/SKILL.md -> references/night.md : re-enters-at (moment 3)
dispatch/SKILL.md -> references/one-ticket.md : re-enters-at (moment 4)
dispatch/SKILL.md -> references/editing-models.md : re-enters-at (moment 5)
dispatch/SKILL.md -> dispatch.sh board : runs-script (moment 6)
references/night.md -> dispatch/SKILL.md#On waking : cites
references/one-ticket.md -> dispatch/SKILL.md#On waking : cites
references/one-ticket.md -> references/night.md#3 : cites (contract、watchdog、turn guard 三类)
references/night.md -> dispatch.sh check/open/advance/status/resume/retract/findings/route/memory-list/reverify/summary/finish/suspend : runs-script
references/night.md -> verify-ticket : calls (--lint；events.py fold)
references/night.md -> ui-acceptance : calls (target_config.py --check；lease.py release)
references/night.md -> to-tickets : cites (<issue-template>、判据形状)
references/night.md -> to-spec : cites (references/revising-a-spec.md)
references/night.md -> design-pages : cites (references/pull.md)
references/night.md -> retro : calls
retro -> references/night.md#5 : hands-off-to (返回)
references/one-ticket.md -> dispatch.sh open-ticket/start/resume/land/ack : runs-script
references/inside-a-ticket.md -> dispatch.sh adopt/ack : runs-script
references/editing-models.md -> models.py config : runs-script
implement -> references/inside-a-ticket.md : cites
implement -> dispatch.sh integrate/start reviewer/wait/ack : runs-script
code-review -> dispatch.sh integrated : runs-script
to-tickets -> dispatch : hands-off-to (开夜)
triage -> dispatch.sh route/advance : runs-script
design-pages -> dispatch.sh reverify/route/resume : runs-script
advisor -> dispatch.sh advise : runs-script
verify-ticket.py -> dispatch.sh self : runs-script
dispatch.sh -> runners/<runner>.sh : runs-script (start/send/liveness/stop/self/attach/open-url；paseo 另有 catalog-*/diagnostic)
dispatch.sh -> models.py : runs-script (runner、row_tsv、worker_role_names)
dispatch.sh -> status.py : runs-script (--table/--advance-plan/--reverify-plan/--land-plan/--worker-grades/--summary/--closeout-ready/--findings)
dispatch.sh -> relay.py : runs-script (start/stop/watching/ack)
dispatch.sh -> verify-ticket/events.py : runs-script (emit、fold、session、result、checked)
dispatch.sh -> verify-ticket/verify-ticket.py : runs-script (--reverify --actor main；run_target_json_checks；标签表)
dispatch.sh -> ui-acceptance/lease.py : runs-script
dispatch.sh -> install.sh : runs-script (check 时 --check，必要时修复)
dispatch.sh -> board/supervisor.py : runs-script (--ensure)
dispatch.sh -> nmem : runs-script (spaces、memories list/search、context read、生命周期修改)
dispatch.sh -> tracker : writes-event (spec.opened、worker.started、reviewer.started、worker.replaced、worker.retracted、worker.resumed、ticket.released、ticket.landed、ticket.bounced、ticket.regressed、ticket.recovered、child.closed、spec.suspended、spec.closed、spec.merged)
dispatch.sh -> worker session : calls (启动提示词 "Use the implement skill …")
dispatch.sh -> reviewer session : calls (启动提示词 "Use the code-review skill …")
dispatch.sh -> advisor session : calls (启动提示词 "Use the advisor skill.")
dispatch.sh -> resolving-merge-conflicts : cites (integrate 冲突报告)
dispatch.sh -> ui-acceptance : cites (PRODUCT_RULES 指向 "Five rules while the product is running")
relay.py -> tracker : reads (gh api 评论、sub-issues，ETag)
relay.py -> runners/<runner>.sh : runs-script (send、liveness)
relay.py -> worker session : wakes (reviewer.reported、reviewer.lost、worker.queued)
relay.py -> orchestrator session : wakes (ticket.passed、ticket.returned、ticket.refused、child.opened contract/fault/decision、worker.lost、relay.recovered)
relay.py -> statedir.py : imports
relay.py -> ghlist.py : imports
relay.py -> verify-ticket/events.py : imports
watchdog.py -> relay.py : imports
watchdog.py -> tracker : reads
watchdog.py -> runners/<runner>.sh : runs-script (liveness、send)
watchdog.py -> tracker : writes-event (worker.lost、reviewer.lost)
watchdog.py -> orchestrator session : wakes (watchdog: 告警，不经队列)
watchdog.py -> references/night.md#Exit codes of resume : cites (告警文本)
turn-guard.py -> watchdog.py : runs-script (arm；读心跳)
turn-guard.py -> runners/<runner>.sh : runs-script (self)
turn-guard.py -> orchestrator session : wakes (拦住回合或 followup_message)
turn-guard.py -> install.sh : configured-by
tool-guard.py -> ui-acceptance/refusal.py : imports
tool-guard.py -> install.sh : configured-by
models.py -> hosts.json : reads
models.py -> ~/.mmw/models.json : reads/writes
models.py -> runners/paseo.sh : runs-script (catalog)
models.py -> statedir.py : imports
status.py -> verify-ticket/events.py : imports
status.py -> verify-ticket/issue_tree.py : imports
status.py -> tracker : reads
board -> models.py : imports
board -> statedir.py : imports
board -> ghlist.py : imports
install.sh -> models.py : runs-script (首装写 models.json)
dispatch.sh -> ~/.mmw/models.json : configured-by
dispatch.sh -> hosts.json : configured-by
how-it-works.md -> references/night.md#Exit codes of resume : cites (已失效，见 9.1)
ADR 0012 -> references/night.md#4 : cites (程序本体放 night.md)
```

## 4. 重复

用 `grep -rn -F` 在 `mmw-v2/`、`docs/`（排除 `docs/research/`、`docs/reviews/`）、`AGENTS.md`、`CODING_STANDARDS.md` 里核对。"真重复"指同一意思；"同读者"指两份都被同一个 agent 在同一时刻读到。

| # | 规则/定义 | 出现位置 | 判定 |
| --- | --- | --- | --- |
| R1 | night 的定义 | `SKILL.md` 第 12 行；`CONTEXT.md` **night** | 真重复（CONTEXT 多一句"read the way a nightly build is"）；读者不同（agent / 维护者） |
| R2 | `watchdog:` 与 `MMW turn guard:` 行不 ack | `SKILL.md` `## On waking` 第 3 步；`CONTEXT.md` **wake**、**alert**；`how-it-works.md` "These are not wake-queue rows and are not acked"；`watchdog.py` 文档"no queue row, so no ack" | 真重复；技能文本只有一份 |
| R3 | 不轮询、起了会话就结束回合 | `night.md` 开头第 5 段；`implement` SKILL.md 第 3 步（worker 一侧）；`how-it-works.md` `## Results, watches and wakes`；`CODING_STANDARDS.md` `## State and configuration`；ADR 0010、0017、0020 | 同一规则、不同执行者：night.md 管 orchestrator，implement 管 worker（`SKILL-SET-RULES.md` Load and disclosure："A rule sits in the text of the agent that must follow it"），维护者文档另有三份 |
| R4 | closing pass 的四步判据与三条提交规则 | `night.md` `## 4.`；ADR 0012 `## Consequences` 与正文 | 真重复，ADR 0012 明说"程序本身写在 night.md 第 4 步"、ADR 只记理由；**已分歧**：提交规则第 2 条 night.md 为"It touches only what the finding's cause requires, and the tests that prove it"，ADR 0012 仍为"只动那张子票点名的文件" |
| R5 | 不把 project branch 合进默认分支 | `night.md` `## 6.` 末句；ADR 0025；`CODING_STANDARDS.md`（"Merging into the repository's default branch is not MMW's job"）；`CONTEXT.md` **`dispatch.sh finish`**（未明写，只写合进 project branch） | 真重复 |
| R6 | bounce 的去向 | `night.md` `## 3.` 表 bounce 行；`how-it-works.md` advance 小节；ADR 0027；`dispatch.sh` `advance` 注释；`CODING_STANDARDS.md`（"a conflict or a red check becomes `ticket.bounced` for triage"） | 真重复；`CODING_STANDARDS.md` 那句与 ADR 0027 **矛盾**（它没写第一次回 worker 队列） |
| R7 | human acceptance、triage、blocked 都是合法结果 | `night.md` `## 5.`；`how-it-works.md` `## Reverify and summary` 末句 | 真重复 |
| R8 | `resume` 各退出码的含义 | `dispatch.sh` `resume_one` 注释与 stderr；`editing-models.md` 最后一段（exit 4）；`relay.py` 文档（`send` 的 0/2/3/4）；`CONTEXT.md` **unconfirmed**；ADR 0020；night.md 表行与 watchdog 告警都指向 night.md `### Exit codes of resume`，但该节现只剩两句 | 部分重复 + 失效指针（见 9.1） |
| R9 | runner 的选择顺序（`MMW_RUNNER` → models.json → 本进程所在 runner → `orca`） | `how-it-works.md` `## Starting a session`；`dispatch.sh` 头注释；`models.py` `runner_name` docstring；`CONTEXT.md` **runner**（只说 `models.py runner` 选）；`CODING_STANDARDS.md`；ADR 0018、0024 | 真重复（均为维护者读物） |
| R10 | 哪个事件唤醒谁 | `relay.py` 文档与 `WAKES` 字典；`how-it-works.md`；`CONTEXT.md` **recipient**；ADR 0020、0022；`night.md` `## 3.` 表（orchestrator 一侧的行） | 维护者文档间真重复；night.md 表是执行者那一份 |
| R11 | watchdog 告警清单 | `watchdog.py` 文档（原文逐条）；`how-it-works.md` `## The watchdog and turn guard` 第 3 段；`CONTEXT.md` **alert** | 真重复 |
| R12 | 心跳容差 `max(300, poll + margin)` | `watchdog.py` 文档；`turn-guard.py` 文档；`CONTEXT.md` **tolerance**；ADR 0021 | 真重复 |
| R13 | models.json 只经 `models.py config` 改 | `editing-models.md`；`AGENTS.md` Commands 表；`CODING_STANDARDS.md`；ADR 0024 | 真重复（执行者只读 editing-models.md） |
| R14 | 不在屏幕上提问 | `implement` SKILL.md 第 23 行"Put no question on the screen …"；`dispatch.sh` `AUTONOMOUS`（进 worker 与 reviewer 的启动提示词）；`tool-guard.py` `NO_QUESTION`（hook 拒绝文字） | 同一意图三处；worker 同一时刻读到前两处（技能与提示词），按 `SKILL-SET-RULES.md` `### Prompts written for other agents`"A rule stated both in a skill and in a prompt a script builds is duplication"属重复；hook 那份是事发时刻的拒绝，读者时刻不同 |
| R15 | 不手工关票 | `tool-guard.py` `REFUSAL`；`implement` 第 8 步"Never close the ticket or swap its labels yourself: a hook blocks the command" | 同一规则，事前（技能）与事发（hook） |
| R16 | worker 会话里跑 `land` 会停掉自己 | `inside-a-ticket.md` `## After the closeout`；`implement` 第 8 步 | 同一理由，不同分支（adopt 的与被 start 的 worker） |
| R17 | `route` 的退出码 | `night.md` `## 4.`；`dispatch.sh` `route_child` 注释 | 真重复 |
| R18 | 没有 relay watch 时 `start`/`advance` 拒绝 | `how-it-works.md`；`dispatch.sh` 头注释与 `start_one` 注释；ADR 0020 | 真重复（维护者） |
| R19 | 一次拒绝就是终点，不重试、不换 host 或 runner | `how-it-works.md`；`dispatch.sh` 头注释与 `advise_one` 注释；ADR 0018 | 真重复（维护者） |
| R20 | ack 的语义与"只有 ack 删行" | `SKILL.md` `## On waking`；`relay.py` 文档；`CONTEXT.md` **ack**、**wake queue**；`implement` 第 1、3 步（ack `worker.queued`、`reviewer.reported`） | 执行者一侧：SKILL.md 与 implement 两处，都被 worker 读到（worker 为解析 `dispatch.sh` 路径也读 dispatch SKILL.md，lightweight review"与其他技能的重复"第 2 条也指出此点，未核实 worker 实际是否读） |

**只是同词**（已核实各自出处）：

| 词 | 含义 A | 含义 B |
| --- | --- | --- |
| `self` | runner 适配器动词与 `dispatch.sh self` | `ticket.checked` 的 run 值 `self`（`docs/reviews/2026-09-29-vocabulary-recheck/verify/d.md` 第 29 行判为 TOLD APART） |
| round | watchdog 的一轮 | worker 修复重跑的一轮（词表决定 W3） |
| phase | `status` 表的 `phase` 列 | task board 的 phase pill（`CONTEXT.md` **phase**） |
| held / holder | fold 的占用事实 | `status.py` 的 holder（`CONTEXT.md` **holder**） |
| layer | liveness layer | test layer（`CONTEXT.md` **liveness layer** 的 `_Avoid_`） |
| finding | review finding / `finding` child | watchdog 的 alert（`CONTEXT.md` **alert** 的 `_Avoid_`） |
| status | `dispatch.sh status` | `watchdog.py status`、`status.py` 程序名 |
| dispatch | 本技能名与动词"派发" | `mmw-v2/upstream-unlazy/references/dispatch.md`（unlazy 的派发说明） |
| night | 一个 spec 的一次运行 | task board 左栏标题 The Night（词表 DECISIONS 第 105 行） |

## 5. 上游差异

**不适用。** dispatch 是本仓自写技能：`mmw-v2/skills.txt` 列为 `self/dispatch`；`mmw-v2/merge-notes/` 没有 `dispatch.md`。

供下一轮参考的相邻事实：

- 最近一次上游 squash 提交为 `5b1a4c513d027a598a277aa45892a6823381f9a9`。其中 `skills/in-progress/implement-spec/SKILL.md` 共 35 行，含 "frontier"、每个 implementer "in its own worktree"、"merger subagent"、最后 `/code-review` 与清理 worktree。`skills.txt` 不安装任何 `in-progress/` 技能。`T2-night.json` 称 MMW 的 frontier、逐票 worktree 与合并骨架由它改编而来；概念重合已核实，逐段借用无法核对（dispatch 文本与它没有共同句子，推断）。
- 为了接上 dispatch，上游技能被改了的段落记在别的 merge-note 里（已核实行号）：`implement.md` 第 13、22、186、190 行（`--preflight`、八步收尾、`wip(#<n>)` 提交、`inside-a-ticket.md`）；`code-review.md` 第 29、93、133、155 行（reviewer 自称、启动句、`dispatch.sh integrated`、Active Rules）；`to-tickets.md` 第 23、24、28、29、33、37、88 行（发布命令、不写 frontier、交给 dispatch、`## Owns`、分级只在 label、只发到 tracker）。这些是"把 MMW 流程写进上游"的改动，不是 dispatch 自身。

## 6. 价值证据

"事故/实测"列只写本次核实到的来源；标"无证据"的是本次所读材料里没有找到防过这种失败的记录。

| 部件或段落 | 防的失败 | 证据 | 核实 |
| --- | --- | --- | --- |
| relay 与 `ack`（ADR 0020） | 结果落在票上却没人被叫醒；脚本报信在进程死于写票与报信之间时静默丢失 | ADR 0020"要修的是什么"；本机 `relay.log` 里 `relay.recovered` 出现 18 行（本仓）与 50 行（agentflow） | 已核实（日志计数由本次 `grep -c` 得出） |
| relay 每仓库一个进程、多个 watch（ADR 0022） | 被拒的 `open-ticket`/`adopt` 把整夜收件人改走；同仓只能一夜；排队 worker 每 90 秒花一回合；orchestrator 关掉后每小时几千次请求 | ADR 0022"已复现"一句 | ADR 原文已核实；复现记录未另找 |
| watchdog 分"relay down"与"relay not reading" | 一轮瞬时网络失败被判成 relay down，处方是无谓重开夜 | #406 标题"一夜五次误报"；本机 `watchdog.json` 的 `reported` 里 relay 类 9 次（本仓）与 5 次（agentflow），另有 `idle`、`unheld`、`read` | 已核实 |
| watchdog 的 `worker.lost`/`reviewer.lost` | 会话死了不写事件，沉默与工作中一样 | ADR 0021；`gh search` 本仓 8 / 9 个 issue、agentflow 1 / 0 个 issue 的评论含这两个事件名 | 搜索计数已得；本仓计数含讨论这些名字的 spec，偏高；GitHub 是否索引 `<!-- mmw -->` 块内文字未确认 |
| turn guard | orchestrator 自己停下、watchdog 死了没人发现 | `turn-guard.py` 头部 2026-09-10 五个 host 实测；firstmate 记录 Grok 在守卫失灵时同步跑满 28800 秒 | 头部原文已核实；firstmate 原文未核实 |
| `tool-guard.py` 拒绝 `gh issue close` 只看以 `gh` 开头的片段 | 关票评论里提到"没有手工关票"被误拦 | `runs` docstring："2026-08-30: a worker hit exactly this on the first unconstrained run of this hook" | 注释原文已核实 |
| `tool-guard.py` 读 `PASEO_AGENT_CWD` | Cursor 在 `~/.cursor` 运行 hook，门对所有命令敞开 | `governed_ticket` docstring："measured 2026-09-06, cursor-agent 2026.08.25" | 注释原文已核实 |
| `tool-guard.py` 拒绝 `kill` 并给唯一出路 | 自主 agent 各自发明错误做法 | `no_kill` docstring："on 2026-09-05 three of them improvised three different wrong answers" | 注释原文已核实 |
| `resume` 区分 exit 2 与 exit 3 | 把"在回合中"当"会话不存在"，永久放弃一个 worker | `resume_one` 注释 #211："a five-hour session with 16 commits on its branch had to be killed"；#211 标题已查 | 已核实 |
| `resume` 只送给 hold 未结束的 worker | 往已结束 hold 的会话打字，`worker.resumed` 让旧 hold 复活 | `resume_one` 注释"On agentflow #754 the watchdog found no session to ask and `resume` found one" | 注释原文已核实；agentflow #754 未打开 |
| `read_ticket` 只认原生 parent 链接 | 从 `## Parent` 散文里取错 spec 号 | 注释引 #193 原文"无 spec；本仓自建票。收口 #188 的评审票外" | 注释原文已核实 |
| `require_runner` 在每个命令开头检查适配器 | 适配器缺失时 `retract` 归档了运行中 worker 的工作区并 exit 0 | 函数注释 | 注释原文已核实；无票号或日期 |
| `start` 写不了 `*.started` 就停掉会话 | 一个没有记录的会话在跑，旁边再起一个 worker | `start_one` 注释 | 无事故证据（设计推理） |
| `advance` 第二次 frontier 计算重启首次 bounce | 唯一活票首次 bounce 后没有唤醒，夜静默停下 | 提交 `cae2de26` 说明：agentflow #915（spec #914，2026-09-15）78 秒后才被第二次 `advance` 重启；`61fd4fe6` 把它挪进 `advance` 内部 | 提交说明已核实 |
| bounce 第一次回 worker、第二次 triage（ADR 0027） | 通常一次集成就能解决的冲突被留到早上；无限重试 | ADR 0027 理由；`gh search` agentflow 有 5 个 issue 含 `ticket.bounced` | ADR 已核实；计数口径同上 |
| `summary` 拒绝仍有未路由 finding | closing pass 漏掉 finding 后 watch 已关，无人能处理 | #407 标题"漏掉 43 条"；提交 `2b560899` | 已核实 |
| `findings` 子命令 | 逐票手工 fold 找 finding 的枚举工作 | lightweight review A8；#407 | 已核实 |
| `reverify` 的 `RECOVER` 路径 | 回归票修好后不会再被选中，`finish` 被挡 | #507 标题；提交 `8b3f9395` | 已核实 |
| `reverify` 本身 | 后来的票或收尾使已落地的早票变红 | I5：#445 的 #472、#446 的 #491 | 未核实（Memory retro 记录未打开） |
| closing pass 四步判据（ADR 0012） | review 子票每票约 3 张、三代不收敛；71% 的修复落在本票 `## Owns` 内 | ADR 0012 的 #216 数据表 | ADR 原文已核实 |
| 新票先 lint、四行判据形状 | closing pass 写的新票让 worker 卡住 | I5 引 #409 | #409 未打开，未核实 |
| `finish` 需要 `spec.retroed recorded` | `finish` 早于 retro | I5：#424 | 未核实 |
| `check` 刷新 Paseo provider 诊断 | 开夜时 host 看似可用，几小时后逐票失败 | `check_machine` 注释（各 host 诊断耗时实测数） | 注释原文已核实；无事故票号 |
| `models.py` 对 `opus[1m]` 去后缀匹配 | reviewer 与 advisor 行解析不出，reviewer 起不来 | lightweight review "修复"一节；提交 `61fd4fe6`、`f4e41c7f` | 提交已核实 |
| `ensure_repository_memory` 只把 404 当作缺失 | Nowledge 不可用时误建 Space | 函数注释 | 无证据（设计推理） |
| Memory 收口（retain/propose/deprecate/supersede） | 夜中写下、落地后变假的记录误导后来的 worker | night.md 目的段 | 无证据（未找到一次被错误记录误导的运行） |
| contract 权威顺序 | 无权威可引时 orchestrator 即兴改 spec 或推翻用户决定 | I5 夜表列出 spec #415"main agent 当夜处理 contract"为来源 | 无事故证据；#415 未打开 |
| `retract` | 会话没了，工作区、slot、claim 仍占着 | `gh search` 两仓 `worker.retracted` 均 0 | 计数已得（口径同上）；可能从未真实执行 |
| `suspend` | 流水线故障时 worker 继续产生无意义失败 | `gh search` 本仓 11 个 issue、agentflow 0 | 计数已得（口径同上） |
| `worker.replaced`（替换活 worker） | 两个 worker 在同一工作树互相覆盖 | `gh search` 本仓 4、agentflow 0 | 计数已得（口径同上） |
| `wait` | 被叫醒但结果评论尚未可读 | ADR 0010 Consequences | 无事故证据 |
| `advise` | 调用方把自己的结论伪装成第二意见 | ADR 0014（经 I2 转述） | ADR 0014 未读，未核实 |

## 7. 约束

**先说明一条用户决定**：Memory 记录 `756fc056`（2026-09-29）写明，这次按 pstack 分层重构时，`SKILL-SET-RULES.md`、ADR 与之前记下的写法决定"都不是约束，而是被审视的对象"：对每条旧规则只问它原本防什么问题、新架构能否更好地解决。下面列出的是**现在的形态由哪些条款决定**，供审视，不是不可动的前提。

### 7.1 ADR

| ADR | 约束了什么 |
| --- | --- |
| 0009 | 脚本只做工具，判断归 orchestrator；没有无模型的守夜状态机（night.md 开头"Every decision is yours"） |
| 0010 | agent 之间靠事件互相叫醒，谁都不轮询；唤醒会打断正在跑的命令（`## On waking` 第 1 步；lightweight review 记下 Orca 下是否仍打断未验证） |
| 0012 | closing pass 的四步判据与三条提交规则的**操作文本必须放在 night.md**，因为夜在 consuming repository 跑、读不到 `docs/adr/` |
| 0016 | 已被 0024 整份作废；仍留下的是"`editing-models.md` 只在用户下令时读"的定位 |
| 0017 | 夜里没有唤醒 agent 的定时器 |
| 0018 | runner 只经适配器；工作树由协议用 git 切；起会话被拒就是终点；`description` 不写 runner 前置条件；`hosts.json` 保留 host × runner 的交叉参数 |
| 0020 | 唤醒由 relay 从票上发出；orchestrator 必须跑在适配器读得出 `self` 的 runner 会话里；没有 watch 的票不起会话；`adopt` 的存在理由 |
| 0021 | 判活三层都不是 agent；`*.lost` 只由 watchdog 写；只问本机起的会话；告警不进队列、不 ack |
| 0022 | 一仓一 relay、多 watch、watch 不共票；排队 worker 由释放槽位的事件唤醒 |
| 0023 | 落地以 `origin/<base branch>` 为准，在常驻 detached merge worktree 里合并 `ticket.passed.commit`、跑 checks、fast-forward push；不开 PR |
| 0024 | `models.json` 是唯一持久配置；附加操作（`attach`、catalog）也只经适配器 |
| 0025 | `open` 记录并推送 project branch；`finish` 只在用户验收与 retro 收据之后；不碰默认分支；不删签出 base branch 的工作树 |
| 0026 | 没有 verifier；角色只剩 worker、reviewer（加 advisor） |
| 0027 | 同一夜首次 bounce 回 worker 队列、第二次进 triage；记录 bounce 的计算不得同时重启该票（实现现状与其"下一次 advance"措辞有出入，见 9.1） |
| 0031 | worker 开工提示里的 Memory 是两份有上限的索引，查询用 `## Owns` 路径与标题 |
| 0008 | 每道闸口拒绝时点名事实、给唯一出路、不靠沉默通过（全体拒绝文字与"unreadable 不等于零"的写法） |

### 7.2 `SKILL-SET-RULES.md` 条款

- 事实 2"Scripts carry what is deterministic; text carries judgement"与 `### Scripts and judgement`：lightweight review 把 watchdog 映射表、bounce 重跑、逐票找 finding、Memory JSON 移进脚本的依据。
- 事实 5 与 `### Load and disclosure`："A file earns its own pointer when a given run can skip it"——四个 reference 各对应一个 moment；"The table that finds the reader's moment sits before any step with side effects"——SKILL.md 与 night.md 的两张重入表。
- `### Load and disclosure`"A rule sits in the text of the agent that must follow it"——worker 的规则不写在 dispatch，而由 SKILL.md moment 1 交给 `implement`。
- 事实 6、7 与 `### Hand-offs`："Invoking another skill … name the skill and the job, never an install path"——文本写 `bash scripts/dispatch.sh` 与"the `verify-ticket` skill's …"。
- `### Descriptions` 与 `### Paths and host neutrality`：`description` 不写 host 与 runner；技能文本里不出现 `orca`/`herdr`/`paseo` 与 host 名（本次 `grep` 已核实，只有产品名 Claude Design）。
- `### Prompts written for other agents`："A start prompt carries only what is known when the agent is started"；"A rule stated both in a skill and in a prompt a script builds is duplication; the prompt keeps the data"——`reviewer_rules_packet` 只放 Rule 行、用法写在 code-review 的依据（`dispatch.sh` 注释原文）。
- `### Redundancy and bloat` Sediment 表：日期实测放脚本头。
- `### Rules and completion criteria`："a step without a completion criterion is a finding … on a line beginning `Done when`"——dispatch 文本只有三处 `Done when`（night.md Memory 收口、`## Suspending the night`；one-ticket 步 4）。

### 7.3 仓库规则

- `AGENTS.md` `## Self-hosting boundary`：本仓自用流水线时，watch 开着期间运行的是 `~/.mmw/installed-root` 记录的冻结版本，不得用正在修改的副本控制本次运行——night.md `## 3.` 表 `fault` 行"A `fault` in the pipeline's own scripts you do not patch while they run the night"的依据（lightweight review I4 原文如此说明）。
- `AGENTS.md` `## Gotchas`：skill 目录是整机共享的一个 symlink；改动要经四步发布才生效。
- `CODING_STANDARDS.md` `## Skills and scripts`：脚本从自身位置找邻居；runner 命令只在适配器；拒绝三段式；脚本头记录实测。`## State and configuration`：models.json、状态目录、事件折叠、落地在 origin。

### 7.4 已记录的用户决定

- Memory `8ec53374`（2026-09-29）：MMW 改造为 pstack 分层（mode / playbook / 能力技能 / 原则 / lever 脚本 / agent 定义 = 读哪个 playbook + models.json 一行）；"宿主不换，夜间脚本保留作 lever"；目的是修改只动一处、扩展只加不改。
- Memory `756fc056`（2026-09-29）：旧规则是审视对象；同时避免形式上拆散与硬塞无价值内容。
- Memory `9040c9cf`：比较以意图为中心；MMW 最常用的只有 spec → ticket → 一夜派发 → 关票 → 验收合并这一条。
- ADR 0018"否决…"一条注明"用户 2026-09-10"否决重试与 fallback host；ADR 0026 注明用户 2026-09-14 接受 worker 自证最终运行的风险；ADR 0023 注明"用户已经决定不设 branch protection 或 ruleset"；ADR 0009 引用用户 2026-09-05"主 agent 整夜在线、按通知逐次工作并不是坏事"；ADR 0010 引用用户 2026-09-06 反对把轮询搬到 main。

## 8. 天然整体

| 整体 | 为什么不可分（或拆开的代价） |
| --- | --- |
| `SKILL.md` `## On waking` 四步 | 顺序本身就是内容：先重跑被打断的命令、再读票、再 `ack`、再长时间工作；`ack` 必须在读之后、长工作之前，因为 relay 重启时重发未 ack 的行。四个 moment 共用，拆到各 reference 会变成四份 |
| night.md 的重入表 + 各节标题 | 表的每一行指向一个锚点；重入判定依赖 spec 上的事件序列（`spec.opened` → `spec.closed` → `spec.retroed` → 验收）。拆开会让重入者先跳文件才能知道自己在哪 |
| night.md `## 3.` 的五步 + 处理表 + "While a worker holds" + 两段 contract 权威 | 每次唤醒都走同一条"ack → status → 处理所有匹配行 → advance 一次"；contract 的两段是同一个判断的两个分支（有权威可引 / 没有）。表的行与步 3 互相引用 |
| night.md `## 4.` 的 Step 0 + 四步判据 + 自己修的三条规则 + 开票规则 + lint | "按顺序、先匹配者胜"：拆开会丢失顺序；三条提交规则是第 3、4 步"自己修"的边界（ADR 0012"逃生口"），与判据一起才有意义 |
| Memory 收口与 `summary --memory-decisions` | 收口结果只有 `summary` 读，`summary` 拒绝不合格文件；`memory-list` 写骨架。它与 finding 路由目的不同（推断：可以从 closing pass 分离，但必须与 `summary` 连在一起） |
| `## 5.` 的 `reverify → summary → retro → 告诉用户` 与 `## 6.` `finish` | 每步要上一步的收据：`summary` 要 reverify receipt（且 commit 等于最新 origin），`finish` 要 `spec.retroed recorded` |
| relay + watchdog + turn guard + statedir | 共享状态目录里的文件：watchdog 读 relay 的 `relay.lock`、`beat.json`、`watches.json`；turn guard 读 watchdog 的心跳并调用 `arm`；三者都用 statedir 的锁与进程身份。任一独立搬走，其余两个的判断依据跟着断 |
| runner 适配器 + `models.py` + `hosts.json` | `models.py` 按选中的 runner 选目录（`MMW_CATALOG_MODE`），`hosts.json` 同时装 CLI 参数与 Paseo settings（ADR 0018 明写这是 host × runner 的交叉，留在 `hosts.json`） |
| `status.py` + `events.py` fold + `dispatch.sh` | 计划行（`MERGE`/`RELEASE`/`DISPATCH`/`REVERIFY`/`RECOVER`/`ARCHIVE`/`HOLD`/`NOTHING`）只有 `dispatch.sh` 读（`CONTEXT.md` **plan line**）；三者对"占用"与"frontier"用同一个折叠 |
| `start_one` + `worker_memory_packet` + `reviewer_rules_packet` + `AUTONOMOUS`/`PRODUCT_RULES` | 启动提示词在一次 `start` 里拼成，环境变量（`NMEM_SPACE`、`MMW_TASK_SCOPE`）与提示词内容一一对应；`MMW_TASK_SCOPE` 空值的含义由提示词里的"unavailable"同时说明 |
| `dispatch.sh` 各子命令 | 推断：子命令共用 merge worktree、merge lock、事件读写、`resolve_into` 等辅助函数；按命令拆成多个脚本会复制这些辅助函数或另建一个库。本次 `grep` 得 36 处 `python3 -c` 或内嵌 heredoc（lightweight review 当时计 26 处加 9 段），这是 bash 调 Python 的结构代价 |

可以单独存在、不依赖其余部分的（供对照，不是建议）：`references/editing-models.md`（只在用户下令时读）、moment 6 的 `board`、`advise`（只有 advisor 技能的调用方用）、`tool-guard.py`（只看工作树目录名，不读任何状态文件）。

## 9. 已核实的不一致与缺口

### 9.1 文本之间或文本与代码之间

1. **失效指针**：`how-it-works.md` `## Interpreting a night` 第 2 段说 `resume` 的退出码和给沉默 worker 的消息"are in the dispatch skill's `references/night.md` under **Exit codes of `resume`**"。现在该节只有两句（51 词），不含退出码表，沉默 worker 的消息已移进 `watchdog.py` 的 idle 告警（提交 `61fd4fe6`）。
2. 同一指向：night.md `## 3.` 表"A live worker should continue"行写"act on exit 0, 4, 3 or 2 as [Exit codes of `resume`] below says"；`watchdog.py` 两条 liveness unknown 告警写"act on its exit as night.md's Exit codes of resume says"。该节不再列这四个退出码；`resume` 自己的 stderr 覆盖 2、3、4，exit 0 无输出。
3. **ADR 0027 与实现**：ADR 0027 写"下一次 `advance` 才从 standing workspace 启动一个 worker"，并否决"第一次 bounce 后在同一次 `advance` 立即重启"。`dispatch.sh` `advance` 现在在同一次调用里做第二次 frontier 计算来重启（注释称这是 ADR 0027 要求的"later restart"）。ADR 0027 无后续修订（`docs/adr/README.md` 索引"被修订"列为"无"）。提交 `cae2de26` 曾以同一 ADR 为由拒绝过同次重启。
4. **ADR 0012 与 night.md**：提交规则第 2 条已分歧（见 R4）。
5. **`CODING_STANDARDS.md`**："a conflict or a red check becomes `ticket.bounced` for triage"没有反映 ADR 0027 的首次回队列。
6. `status.py` 文档写"One program, six forms"，文档列出 7 行，argparse 实有 8 种形式（多 `--closeout-ready`）。
7. `dispatch.sh` 头注释的子命令列表缺 `integrated`、`findings`、`memory-list`，`adopt` 未写 `[--into]`；`usage` 是全的。
8. `CONTEXT.md` **runner adapter** 说 `catalog-*` 读取"each answering with the same exit codes on every runner"；只有 `paseo.sh` 实现 `catalog-status`、`catalog-models`、`diagnostic`，`orca.sh`、`herdr.sh` 对它们走 `usage`。
9. `finish_spec` 在 `.mmw/target.json` 没有 `checks` 时打印中文 stderr"没有检查：.mmw/target.json 没声明 checks"，其余拒绝文字均为英文。
10. lightweight review 列出的脚本清理未做：`--json | --run` 拒绝与 `summary_spec` 中恒真的 `if [ -n "$extra" ]` 仍在。

### 9.2 流程缺口（推断，未在真实运行中观察）

1. night.md 的重入表没有"`spec.retroed recorded` 之后、用户尚未验收"这一行。retro 技能结尾明确说回到 night.md `## 5`，所以按 retro 走的 orchestrator 不受影响；中途重入（例如会话被压缩后）的 orchestrator 找不到匹配行。
2. 完成判据：night.md 的步 1、2、3、5、6 与 SKILL.md、`inside-a-ticket.md`、`editing-models.md` 都没有 `Done when` 行（`SKILL-SET-RULES.md` `### Rules and completion criteria` 视为 finding）。

## 10. 未确定

- `suspend_night`、`reverify_spec`、`close_spec_memories`、`route_child`、`land_one_via_origin` 与工作区辅助函数的主体未逐行读；对它们的描述来自头注释、退出行与 `how-it-works.md`。
- `finish_preflight` 是否要求"同 base branch 的所有票都已关闭"（M2 的说法）：只读到其 stderr 片段，未核实。
- relay、watchdog 的实现只读了文档与告警拼字，文档所述行为（ETag、覆盖两分钟、每 10 轮问 orchestrator 死活等）未对照实现。
- runner 适配器的 `start`/`send`/`liveness` 实现未读；`## On waking` 第 1 步"A wake can cut short a command you were running"在 Orca、Herdr 下是否成立未验证（lightweight review 同样未验证）。
- `gh search` 的事件计数：不确定 GitHub 搜索是否索引评论里 `<!-- mmw {...} -->` 块内的文字；本仓的计数包含讨论事件名的 spec 与 ticket，偏高。
- `worker.retracted` 两仓均为 0，可能从未真实执行；是否在未被搜索覆盖的仓库里执行过，未知。
- I5 所引 Memory retro 记录（spec 444–447、555）与 #409、#424、#415、agentflow #754、#915 未打开。
- ADR 0014（advisor 单入口）未读。
- `CONTEXT.md` 是否被夜里的任何 agent 加载：技能文本不指向它（推断其读者只有维护者），未在真实运行中观察。
