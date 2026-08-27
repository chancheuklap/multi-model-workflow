# Herdr 派发模型：票怎么到 worker、worker 怎么被知道、产出怎么被读、verifier 在哪跑

`00-synthesis.md` §「第二轮之后的定案（2026-08-28）」首行定了：Worker 是 Herdr 拉起的独立会话，每票一个 worktree；verifier 是编排会话自己的只读子代理；「票即输入」= Herdr 启动 worker 时喂的提示词。本文只查这套安排在机制上是怎么成立的，给 `implement` / `to-tickets` 的设计当事实依据；不设计自动化。旧实现（回退提交 `ceb2c2a1` 之前的 `docs/adr/0020-workers-dispatch-via-herdr.md` 与 `docs/specs/landing-orchestrator/`）只当「当时怎么想的」引用，不复用。

名词：**Herdr** 是一个终端多路复用器，把终端组织成 workspace / tab / pane，并识别 pane 里跑着的 coding agent（`~/.claude/skills/herdr/SKILL.md:8`）。**编排会话** 指跑在 Herdr 某个 pane 里、负责派票的那个 agent 会话。**worker** 指被派去做一张票的 agent 会话。**verifier** 指在最终 commit 上重跑票的 `CHECK:` 并写 `VERDICT` 行的只读角色（`06-independent-verifier.md` §1）。**subagent / 子代理** 指宿主在同一进程内派出的、有自己上下文的子任务。

取证时间 2026-08-28，本机版本：herdr 0.8.2、claude 2.1.247、grok 1.0.5、codex 0.149.1、cursor-agent 2026.08.11、pi 0.84.3。`HERDR_ENV=1`，本会话本身在 Herdr pane 里，`herdr agent list` 与 `herdr api snapshot` 只读查看过；没有启动任何 agent、没有发任何 prompt。引用写法 `文件:行号`；`herdr <组>` 指运行该命令组不带子命令打印出的清单（`SKILL.md:26-40` 规定的发现方式，`--help` 对子命令一律只打顶层帮助，本机实测十个子命令均如此）。

## 1. Herdr 是什么、能做什么

### 1.1 启动 agent

| 事实 | 出处 |
| --- | --- |
| 命令：`herdr agent start <name> --kind KIND --pane ID [--timeout MS] [-- <agent-args...>]` | `herdr agent` 清单 |
| 可用 kind：`pi\|claude\|codex\|gemini\|cursor\|devin\|agy\|cline\|omp\|mastracode\|opencode\|copilot\|kimi\|kiro\|droid\|amp\|grok\|hermes\|kilo\|qodercli\|qwen\|maki`（22 种；本仓五个宿主全在） | `herdr agent` 清单末行 |
| 前提：pane 必须已存在且是空闲 shell（提示符、无前台命令）；`agent start` 不建、不拆、不移 pane | `SKILL.md:54`、`:108` |
| 建 pane：`herdr pane split --current --direction right --cwd "$PWD" --no-focus`，新 pane ID 在 `.result.pane.pane_id` | `SKILL.md:103-106` |
| 建 worktree：`herdr worktree create [--workspace ID \| --cwd PATH] [--branch NAME] [--base REF] [--path PATH] [--label TEXT]` | `herdr worktree` 清单 |
| `agent start` 成功返回的时机：Herdr 在同一 pane 里检测到预期 agent 并判断它能接收交互输入；启动期被挡返回 `agent_not_ready`，名字仍保留；默认 30 秒超时 | `SKILL.md:120` |
| `--` 之后是传给 agent 的原生参数 | `SKILL.md:114-118` |
| Herdr 怎么知道 pane 里是哪个 session：它给每个宿主装了一个 SessionStart hook，hook 通过 unix socket 调 `pane.report_agent_session` 上报 `agent_session_id`。本机 `herdr integration status`：claude / codex / pi 为 v8、cursor / grok 为 v1，五个宿主都装了 | `~/.claude/hooks/herdr-agent-state.sh`、`~/.codex/herdr-agent-state.sh`、`~/.cursor/herdr-agent-state.sh`、`~/.grok/hooks/herdr-agent-state.sh`、`~/.pi/agent/extensions/herdr-agent-state.ts` |
| Claude 的 hook 在 hook 输入带 `agent_id` 时直接退出，即**子代理不会出现在 Herdr 的 agent 列表里** | `~/.claude/hooks/herdr-agent-state.sh` 的 `is_subagent = bool(hook_input.get("agent_id"))` 一段 |

### 1.2 命名规则

- 名字须匹配 `[a-z][a-z0-9_-]{0,31}`，在活着的 agent 里唯一；名字跟着 pane 里当前的占用者走，agent 退出、被 release 或被替换时清空（`SKILL.md:56`）。名字只存在于 Herdr 运行时，不进 Git 也不进 tracker（Nowledge Mem `feedback-herdr-agent-name-must-match-session`）。
- 同一条记忆要求 Herdr 的 name 与 agent 自己的 session 名用同一个字符串、启动时就给：Claude Code 走 `herdr agent start <name> --kind claude --pane <id> -- -n <name>`（`claude --help` 的 `-n, --name <name>  Set a display name for this session`；2026-08-11 实测通过）。pi 有同名参数 `--name, -n <name>  Set session display name`（`pi --help`）。Codex 没有启动命名参数（记忆；`codex --help` 亦无）。Grok `--help` 没有 `-n`，只有 `-r, --resume` 按「session titles」匹配，说明它有标题但本机没查到启动时设标题的参数。Cursor `--help` 没有命名参数。
- 名字取材：用仓库或领域文档已有的术语或直接用票号（同一条记忆「How to apply」段）。UUID 不能当 Herdr 名（36 位、可能以数字开头，不合上面的正则）。

### 1.3 发 prompt

- `herdr agent prompt <target> <text> [--wait] [--until STATUS]... [--timeout MS]`（`herdr agent` 清单）。发送方式是按 pane 的 bracketed-paste 模式贴文本，短暂延迟后送 Enter（`SKILL.md:128`）。
- 目标已停在审批或提问对话框时，不发任何字节，返回 `agent_blocked`（`SKILL.md:128`）。
- 从非 working 状态发出的 prompt 五秒内必须观察到生命周期变化，否则返回 `agent_prompt_stalled`（`SKILL.md:130`）。
- `--wait` 等的是第一个稳定态 `idle` / `done` / `blocked`；**它跟踪的是生命周期，不是某一个回合**，agent 已在 working 时当前回合结束就能满足它（`SKILL.md:128-130`）。`agent wait` 不带 `--until` 时同样的默认（`:138`）。
- `SKILL.md:120`：agent 启动后要等它 idle 再 prompt。

### 1.4 生命周期状态

`idle` = 准备好接收输入且它的 tab 在聚焦的 Herdr UI 里被看过；`done` = 同一个底层 idle，但是在没人看的后台工作结束之后；聚焦 tab 或用 focus 命令指向它才算「看过」，CLI 读取不算；`blocked` = Herdr 识别出审批或提问界面；`unknown` = 有 agent 但无法可靠分类，**不证明完成**（`SKILL.md:58`）。

### 1.5 读输出的三种来源与各自缺陷

| 来源 | 命令 / 位置 | 缺陷 | 出处 |
| --- | --- | --- | --- |
| 终端渲染 | `herdr agent read <target> --source visible\|recent\|recent-unwrapped\|detection --lines N`；日志和 transcript 优先 `recent-unwrapped` | 只有可见区 + 宿主 scrollback。agent 若在 alternate screen 上运行，滚出的行不进 scrollback，加大 `--lines` 也救不回；超过 pane 宽度的表格被截断 | `SKILL.md:174-183`；Nowledge Mem `1035efa2-1cc0-45d2-9938-bea8f6f1a7ba` |
| 让 agent 落文件 | 读失败后再要求 agent 把完整回复写成 Markdown 到临时目录、只回文件路径，然后直接读文件 | 只能作为读失败后的兜底，不能在首个 prompt 里就要求；依赖 agent 照办 | `SKILL.md:185` |
| 磁盘 transcript | `herdr agent list` 的 `agent_session.value` 就是宿主磁盘上的 session id；路径按宿主见 §4.2 | Herdr 只给 id 不给路径（本机 `agent list` 里 `agent_session` 只有 `agent / kind / source / value` 四个键；Claude 的 hook 虽把 `transcript_path` 当 `agent_session_path` 上报，list 输出里看不到；codex hook 只检查 `transcript_path` 存在不上报，cursor / grok hook 只报 id）；格式五家各异，要自己解析 | 本机 `herdr agent list` 输出；四个 hook 脚本；记忆 `1035efa2…` |

记忆 `e44b6cfb-379b-43cc-b0b5-cfa6981e95f3` 的教训适用于这里：终端快照是渲染层，磁盘文件才是数据源。

### 1.6 `herdr api snapshot` 的字段

`herdr api snapshot` 返回 `.result.snapshot`，本机（protocol 20、version 0.8.2）结构：

- `agents[]`：`agent`（kind 名）、`agent_session{agent, kind, source, value}`（`source` 形如 `herdr:claude`，`kind` 为 `id`，`value` 是 session id）、`agent_status`、`cwd`、`focused`、`foreground_cwd`、`pane_id`、`revision`、`state_change_seq`、`tab_id`、`terminal_id`、`terminal_title`、`terminal_title_stripped`、`tokens{}`、`workspace_id`。
- `panes[]`：同上再加 `scroll{}`。
- `tabs[]`：`agent_status`、`focused`、`label`、`number`、`pane_count`、`tab_id`、`workspace_id`。
- `workspaces[]`：`active_tab_id`、`agent_status`、`focused`、`label`、`number`、`pane_count`、`tab_count`、`tokens{}`、`workspace_id`。
- `layouts[]`：`area`、`focused_pane_id`、`panes`、`splits`、`tab_id`、`workspace_id`、`zoomed`。
- 顶层：`focused_pane_id`、`focused_tab_id`、`focused_workspace_id`、`protocol`、`version`。

本次读取时五个活 agent 都没有用 `agent start` 命名，所以没有观察到 `name` 字段；记忆 `feedback-herdr-agent-name-must-match-session` 说命名后 snapshot 里 `name` 与 `terminal_title_stripped` 对得上，本文未复核。`agent list` 是同一份数据的 `agents[]` 子集。

`terminal_title_stripped` 的来源是宿主设的终端标题（Claude 的 `-n` 写进终端标题，`claude --help`），是 snapshot 里唯一能反映宿主侧会话名的字段。

## 2. 票怎么到 worker 手里

### 2.1 Herdr 能喂什么

Herdr 只有两条把文字送进 agent 的路：`agent start ... -- <agent-args>` 里的原生参数，和 `agent start` 返回后的 `agent prompt`（§1.1、§1.3）。五个宿主的 CLI 都接受位置参数作为首个 prompt（`claude --help` 的 `prompt`、`grok --help` 的 `[PROMPT]`、`codex --help` 的 `[PROMPT]`、`cursor-agent --help` 的 `prompt`、`pi --help` 的 `[messages...]`），但 `SKILL.md:120` 的 `agent start` 是等到 agent「ready for interactive input」才返回，带初始 prompt 启动会让 agent 一开机就 working，这与就绪检测怎么相处本文没有实测（§7）。已核实的路径是：`agent start` → 等 idle → `agent prompt <name> "<text>" --wait`。

所以「票即输入 = Herdr 启动 worker 时喂的提示词」在机制上是：`agent prompt` 送进去的那一段文字。

### 2.2 最小形态是不是 `implement #<n>` 一句

`implement/SKILL.md`（`mmw-v2/upstream/skills/engineering/implement/SKILL.md`）的第 6 行说它实现「the spec or tickets」，第 8-10 行规定它自己去做的事：核对票在 frontier 上、读票全文含评论、读 `Read first` 每一项、沿 `Parent` 读 spec 指名的小节。也就是说票号一到手，读票是技能的事，不是派发词的事。派发词只需要让技能被触发并带上票号。

技能怎么被触发，按能力分两种：

- 用户显式调用：Claude Code 是 `/implement`（本会话技能列表里 `implement` 就是这样列出的）；Grok Build 用 `/name`，且默认扫 `.claude/skills`、`.agents/skills`、`.cursor/skills`（`docs/research/grok-build-vs-claude-code.html` 「技能 Skills」一节）；Codex、Cursor、pi 的斜杠语法本文没查（§7）。
- 模型按 `description` 自动调：`implement` 的 description 是 `Implement a piece of work based on a spec or set of tickets.`（`SKILL.md:3`），一句 `implement #<n>` 或 `实现 #<n>` 能命中。`mmw-v2/install.sh:15-17` 说明 Codex、Cursor、Grok、Pi 原生扫 `~/.agents/skills`，Claude Code 只认 `~/.claude/skills`，两处都装了同一批软链；本机 `ls ~/.agents/skills` 里有 `implement`。

结论：最小形态可以是一句带票号的话；但它成立有三个前提，都不在那句话里：

1. worker 的 cwd 在票的 worktree 里（`implement` 读票靠 `gh`，而 `gh` 的仓库来自 cwd；`docs/agents/issue-tracker.md:8` 「`gh issue view <number> --comments`」）。
2. worker 进程里 `gh` 已登录。
3. worker 的权限模式允许它不问人就改文件、跑命令——各家参数不同（`claude --permission-mode`、`grok --permission-mode` / `--always-approve`、`codex -a never -s workspace-write`、`cursor-agent --force`、pi `--approve`），这些通过 `agent start -- <args>` 传，本文不定取值。

### 2.3 worker 到位后会读到什么

| 东西 | 各宿主 | 出处 |
| --- | --- | --- |
| 仓库指令 `AGENTS.md` / `CLAUDE.md` | Claude Code 读 `CLAUDE.md`（本仓 `CLAUDE.md` 只有一行 `@AGENTS.md`）；Grok 每个目录按 `Agents.md / Claude.md / CLAUDE.md / CLAUDE.local.md / AGENT.md / AGENTS.md` 顺序读，另扫 `.grok/rules/`、`.claude/rules/`；pi 读 `AGENTS.md` 与 `CLAUDE.md`（`pi --help` 的 `--no-context-files  Disable AGENTS.md and CLAUDE.md discovery`）；Codex、Cursor 本文未核（§7） | `grok-build-vs-claude-code.html` 「项目规则：AGENTS.md / CLAUDE.md」一节；`pi --help` |
| 本仓 `AGENTS.md` 里给技能的配置：tracker 走 `gh`（§「Issue tracker」）、五个 triage 标签（§「Triage labels」） | 随上一行到达。`to-tickets/SKILL.md:10` 「The issue tracker and triage label vocabulary should have been provided to you」指的就是这个 | `AGENTS.md` §「Agent skills」 |
| 技能软链 | 见 §2.2 第二点 | `mmw-v2/install.sh:15-17`、`:41-49` |
| subagent 成品 | 六个安装点：`~/.claude/agents`、`~/.codex/agents`、`~/.pi/agent/agents`、`~/.cursor/agents`、`~/.grok/agents`、`~/.grok/roles` | `mmw-v2/install.sh:222-229` |
| 宿主全局指令 | `~/.claude/CLAUDE.md`、`~/.grok/AGENTS.md`、`~/.codex/AGENTS.md`、`~/.pi/agent/AGENTS.md` 本机都存在（`ls` 结果） | 本机目录 |

worktree 是仓库的完整副本，根目录的 `AGENTS.md` 和 `docs/agents/` 都在，所以把 cwd 设到 worktree 就够。

## 3. worker 做完怎么被知道

### 3.1 Herdr 有没有完成信号

没有「任务完成」信号，只有 §1.4 的生命周期状态。能拿到的最接近的东西：

- `agent prompt --wait` / `agent wait` 在第一个稳定态返回。`implement` 是一个长回合，回合结束就 idle / done，`--wait` 会在那时返回；但回合也可能提前结束——agent 在正文里问了问题就停（idle，不是 blocked）、agent 崩了、宿主自己中断——这些同样是「稳定态」。
- `blocked` 能区分「停在审批 / 提问对话框」；`unknown` 什么都不证明（`SKILL.md:58`）。
- CLI 没有推送机制（`herdr notification show` 是给人看的桌面通知）；socket API 的 `events.subscribe` 能实时推送 `pane.agent_status_changed`（§7 实测），是唯一的推送通道，但推的仍是生命周期状态。

### 3.2 靠什么判断

| 手段 | 怎么读 | 可靠性 |
| --- | --- | --- |
| 票状态 | `gh issue view <n> --json state,stateReason,comments`；`gh` 2.96.0 支持 `stateReason`（`gh issue view --help` 的 JSON 字段列表；`00-synthesis.md` §「第二轮核实的事实」第 3 条） | 最可靠的「完成」定义：`implement/SKILL.md:20-24` 要求 worker 收尾时评论证据、push、开 PR、关票；`00-synthesis.md` 定案「失败词汇」行定了 `ALL MET` 关票、`HANDOFF REQUIRED` 不关票并换标签。票关了或首行 `HANDOFF REQUIRED` 的评论出现，就是 worker 按契约收了尾。缺陷：worker 没走到收尾（崩、停、放弃）时票不动，单看票分不清「还在做」和「死了」，要和 Herdr 状态合看 |
| Herdr 状态 + 票状态 | `herdr agent get <name>` 为 idle / done 且票未变 → worker 停了但没收尾 | 旧 `ADR 0020:14` 的原则「完成判定不读终端画面，只读硬状态……终端画面只在 `blocked` 时读」在机制上仍然成立 |
| `herdr agent read` | 读最近输出看它最后说了什么 | 只能在 idle 后当补充证据，缺陷见 §1.5；alternate screen 的宿主（`grok --help` 与 `codex --help` 都有 `--no-alt-screen`，说明默认在 alt screen）尤其不可靠 |
| 磁盘 transcript | 按 §4.2 路径读最后一条 assistant 消息 | 完整，但要按宿主解析；适合事后取证，不适合当轮询信号 |
| git | `git -C <worktree> log <base>..HEAD`、`git status --porcelain` | 有 commit 说明写了东西，不说明做完 |

## 4. 产出怎么被读

### 4.1 收尾评论是不是唯一可靠通道

是。理由：

- 它是契约的一部分：`implement/SKILL.md:22` 要求评论里给分支、commit、每条验收标准的证据；`00-synthesis.md` 定案的 `EVIDENCE:`、`Outside Owns:`、`skipped: [X], add when [Y]`、`ALL MET` / `HANDOFF REQUIRED`、`VERDICT` 行全部落在这条评论上（`06-independent-verifier.md` §7.1 的理由：本仓票在 GitHub Issues，任何宿主任何会话都读得到）。
- 其他通道都有寿命或格式问题：Herdr 名字随 agent 退出消失（§1.2）；终端输出会滚丢（§1.5）；transcript 五家格式不同，且只对本机可见。

### 4.2 transcript 路径按宿主

下表每行都在本机 `ls` / `find` 核实过一个真实文件。

| 宿主 | 路径 | 说明 |
| --- | --- | --- |
| Claude Code | `~/.claude/projects/<cwd 把 / 换成 ->/<session-id>.jsonl` | 本会话 `~/.claude/projects/-Users-cheuklapchan-multi-model-workflow/32175e9b-….jsonl`，与 `herdr agent list` 里本 pane 的 `agent_session.value` 一致 |
| Codex | `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-<时间戳>-<thread-id>.jsonl` | 按日期分目录，不按 cwd |
| Cursor | `~/.cursor/projects/<cwd 去掉首个 / 再把 / 换成 ->/agent-transcripts/<session-id>/<session-id>.jsonl` | 与记忆 `1035efa2…` 一致 |
| Grok Build | `~/.grok/sessions/<cwd 做 URL 编码>/<session-id>/` 目录，内含 `chat_history.jsonl`、`updates.jsonl`、`events.jsonl`、`system_prompt.txt`、`summary.json` 等 | 与记忆 `1035efa2…` 一致；`grok export` 子命令能把会话导出成 Markdown（`grok --help`） |
| pi | `~/.pi/agent/sessions/--<cwd 把 / 换成 ->--/<时间戳>_<session-id>.jsonl` | 首尾各多两个 `-` |

补充：Claude（`--session-id <uuid>`）、Grok（`-s, --session-id`，新会话专用）、pi（`--session-id <id>`）允许启动时指定 session id，即启动前就能算出 transcript 路径；Codex 没有；Cursor 有 `create-chat` 返回 ID，能否 `--resume` 进空 chat 未验（§7）。

## 5. verifier 在哪跑

### 5.1 事实

- 定案：verifier 是编排会话自己的只读子代理，只审一次（`00-synthesis.md` 定案表「Worker 与 verifier 是谁」「verifier 次数」两行）。做法：第四个 subagent `mmw-v2/agents/verifier/`（`06-independent-verifier.md` §8.3）。
- 装到哪：`install.sh:222-229` 的六个安装点，五个宿主都装；现有三个 agent（advisor、claim-checker、ui-evaluator）本机六处软链齐全（`ls` 结果）。所以 verifier 做成第四个目录后，无论 worker 跑在哪个宿主，那个宿主都有 verifier 定义可派。
- 子代理对 Herdr 不可见（§1.1 末行），它的审批提示会出现在父会话里，被 Herdr 当父会话的 `blocked`。
- `implement` 的收尾（`implement/SKILL.md:20-24`）由 worker 自己做到关票为止；定案「verifier 次数」行写的顺序是 worker 自跑 → verifier 一次 → 没过的 worker 修并自跑填证据 → 关票，也就是 verifier 在关票之前。

### 5.2 两种场景

**(a) 白天用户手工开一个会话做一张票。** 没有编排会话。会话里只有 worker 一个主体，以及它能派的子代理。

**(b) 编排会话经 Herdr 派 worker。** 编排会话与 worker 是两个进程；编排会话看得到 worker 的 Herdr 状态和票，看不到 worker 的上下文；worker 看不到编排会话。

### 5.3 场景 (a) 里 verifier 由谁派：三种可能与后果

| 可能 | 机制 | 后果 |
| --- | --- | --- |
| 1. worker 自己派子代理 | `implement` 收尾第 2 步「派 verifier subagent」（`06` §8.1）；brief 按 `06` §8.2 只给验收标准原文、SHA、Seam、FORBIDDEN、REPORT | 满足「判的不是写的那个」（新上下文、没有写码记忆，`06` §6 表第二行）；同宿主，模型由 `agent.json` 按宿主选，是否跨家族取决于宿主（`06` §3.3）。brief 由 worker 拼，worker 有漏抄标准的空间——缓解是「原样粘贴」而不是转述（`06` §8.2 要点一）。顺序自然：verifier 在关票前。与定案首行的差异只在父是谁 |
| 2. 用户手工触发 | 用户在另一个会话里派 verifier，或把 `VERDICT` 自己写上 | 独立性最强；但多一步人的动作，且本仓没有单独的「验这张票」入口（`mmw-v2/skills.txt` 里没有）；worker 关票前得停下等，`implement` 的收尾流程要拆成两段 |
| 3. `implement` 按能力判断「能派子代理就派」 | 就是 `06` §6 的三层降级：能派且能选模型 → 派并换模型；能派不能选 → 同模型也派；不能派 → 自己从干净 shell 重跑，`by self-reported` | 在 (a) 里等于可能 1 加一条兜底；在 (b) 里 worker 也会走同一步——于是 (b) 有两个候选 verifier：worker 的子代理和编排会话的子代理。定案要求只审一次，就得规定其中一个不派 |

### 5.4 场景 (b) 里若按定案由编排会话派

编排会话要拿到最终 SHA、分支、worktree 才能写 brief（`06` §8.2 的 `SHA` 行）。这些在 worker 的收尾评论里，而 `implement/SKILL.md:22-24` 是评论之后紧接着 push、开 PR、关票。要让 verifier 落在关票之前，worker 必须在评论后停下等裁决、编排会话读评论 → 派 verifier → 把裁决 `agent prompt` 回同一个 worker（pane 常驻、上下文还在，`ADR 0020:12` 第三个理由；`SKILL.md:56` 名字跟 pane 走）→ worker 修、自跑、关票。这要求 worker 在 (b) 里的收尾和 (a) 里不同（多一个「等」），而技能正文对所有宿主是同一份（`AGENTS.md` §「约定」第 2 条）——不是按宿主分支，但是按「有没有人在外面等」分支，`implement` 得知道自己处在哪个场景，而这个信息只能来自派发词。

## 6. 与 `00-synthesis.md` 定案的冲突或需补充处

1. **verifier 的父会话**。定案「verifier 是编排会话自己的只读子代理」在场景 (a) 没有对象；在场景 (b) 要求 §5.4 的握手，且 `implement` 得按场景分支。可能 1 / 3（verifier 是运行 `implement` 的那个会话的子代理，编排会话只读评论里的 `VERDICT` 行）在两个场景里是同一条流程、同一份技能正文。这是要用户裁决的取舍：独立性（编排会话派，父与 worker 不是同一进程）对流程单一（worker 派）。
2. **「Herdr 启动 worker 时喂的提示词」的时机**。已核实的做法是 `agent start` 返回并 idle 后再 `agent prompt`（§2.1），不是启动参数。派发词的内容能压到「技能名 + 票号」，但 §2.2 的三个前提（cwd、`gh` 登录、权限参数）得在 `agent start` 的 `--cwd` 与 `-- <args>` 里给。
3. **命名**。定案没提 Herdr 名字。记忆要求两边一致、用票号；只有 Claude 与 pi 能在启动时设宿主侧名字（§1.2），其余宿主只能设 Herdr 一侧并如实说明。
4. **完成的定义**。Herdr 没有完成信号（§3.1），「做完」得定义成票状态（关票或 `HANDOFF REQUIRED`）加 Herdr idle / done；票不动而 agent 已 idle 是「停了没收尾」，需要一个处置（本文不设计）。
5. **verifier 对 Herdr 不可见**（§1.1 末行）。verifier 的 `blocked` 只会以父会话的 `blocked` 出现；编排会话若自己派 verifier，它自己的 pane 会 blocked，等于编排会话卡住。
6. **`herdr agent start` 依赖宿主的 Herdr integration**（§1.1 倒数第二行）。没装 hook 的宿主 `agent_session` 为空，§4.2 的 transcript 路径就接不上。换机器时要 `herdr integration install <kind>`。
7. **`--wait` 的语义**。旧 spec `landing-orchestrator.md:81` 的「Further Notes」已指出 `agent prompt --wait` 等的是稳定态而非单轮完成；本文 §3.1 复核仍成立。凡是把 `--wait` 返回当「做完」的设计都要改成 §3.2 的合看。

## 7. 实测（2026-08-28，herdr 0.8.2，本会话所在的 Herdr 会话）

实验：在本 tab 右侧分一个 pane，`herdr agent start probe1 --kind claude --pane <id> -- -n probe1 --model haiku`；另用 `herdr worktree create --cwd "$PWD" --branch probe-herdr-wt --no-focus` 开一个 worktree 工作区，在其根 pane 用带初始 prompt 的参数启动 `probe2`；用 python 直连 `$HERDR_SOCKET_PATH` 订阅 `pane.agent_status_changed`。做完后 `/exit` 两个 agent、`pane close`、`worktree remove`、删分支，全部清理。

| 问题 | 结果 |
| --- | --- |
| `agent start` 返回什么 | 3.97 秒返回 `type: agent_started`，`.result.agent` 含 `name: "probe1"`、`interactive_ready: true`、`agent_status: idle`、`agent_session.value`（session id）、`terminal_title_stripped: "probe1"`（`-n` 生效）、`argv`（Herdr 实际执行的命令行） |
| `agent list` 有没有 `name` | 有：`agent start` 命名的 agent 在 `agent list` / `agent get` 里带 `name` 字段；手工启动的没有该字段 |
| 带初始 prompt 启动 | `herdr agent start probe2 … -- -n probe2 --model haiku "<prompt>"` 4.8 秒返回 `idle`，argv 里带着 prompt；agent 已把回复做完（transcript 里最后一条 assistant 文本是 `PONG2`）。可用，但 `agent start` 的返回不等回复完成 |
| `agent prompt --wait` 返回什么 | 3.1 秒返回 `type: agent_prompted`，`.result.agent.agent_status: "done"`，`.result.wait: null`。因为 pane 没被看过，是 `done` 不是 `idle` |
| 事件订阅 | `events.subscribe` 订 `{"type":"pane.agent_status_changed","pane_id":…}` 后，每次状态变化实时推一行：`working`（发 prompt 后 2 秒）→ `done`（再 2 秒）；提问时 `working` → `blocked` → 按 esc 后 `done`；agent 退出后 `agent_status: "unknown"` 且无 `agent` 字段。**这是 CLI 没暴露的推送通道**，一个订阅进程能同时盯多个 pane |
| 正文里提问（不用工具）后停下 | `--wait` 照样返回 `done`；只有读屏能看到 `⏺ Which colour do you prefer?`。证实 §3.1：`done` 不等于做完 |
| `blocked` | `AskUserQuestion` 弹出后 `agent wait --until blocked` 3 秒命中；`agent explain` 给出规则 `live_blocked_form`；此时 `agent prompt` 被拒 `agent_blocked`；`send-keys esc` 后回到 `done` |
| 读回复 | `agent read --source recent-unwrapped --lines 40` 只看到提示框（alt-screen）；`--lines 200` 触发滚动读取，能读到 `❯ prompt` / `⏺ PONG` / `✻ … done`。probe2 同样参数读不到它的初始回复（启动即回答，历史被压到更早），改从磁盘 transcript 读到 `PONG2` |
| transcript 路径 | 按 §4.2 公式推算的两个路径都存在：主仓 cwd → `~/.claude/projects/-Users-cheuklapchan-multi-model-workflow/<id>.jsonl`；worktree cwd → `~/.claude/projects/-Users-cheuklapchan--herdr-worktrees-multi-model-workflow-probe-herdr-wt/<id>.jsonl` |
| `worktree create` 返回 | `type: worktree_created`，含新 `workspace`（带 `worktree` 出处：`checkout_path`、`repo_root`、`is_linked_worktree`）、`tab`、`root_pane`（`pane_id` 可直接给 `agent start`）、`worktree`（`branch`、`path`、`open_workspace_id`）。默认路径 `~/.herdr/worktrees/<repo>/<branch>`，分支从当前 HEAD 建。`worktree remove --workspace <id>` 返回 `worktree_removed`，不删分支 |
| 完成信号 | 没有"任务完成"事件；能拿到的最细粒度是 `pane.agent_status_changed` 推送 + `terminal_title` 变化（`◐` working / `✳` idle 是 Claude 的 OSC 标题，`agent explain` 的 `osc_title_working` 规则用它） |

## 8. 未读、未确定

- 未测：Grok、Cursor、Codex 能否在启动时设宿主侧会话名；这三家 `agent start` 的就绪检测与 `--wait` 表现（本次只测了 Claude Code）。
- 未测：`done` → `idle` 的"被看过"转换（`agent focus` 会抢用户焦点，没做）。
- 未确定：Codex、Cursor、pi 里用户显式调用技能的语法；Codex 与 Cursor 是否读仓库根 `AGENTS.md`。
- 未确定：`pane process-info --pane <id>` 对 agent pane 返回了 `shell_pid: null`、空 `foreground_processes`，原因未查。
- 未读：`terminal session observe`（只读实时帧流）能否替代 alt-screen 读取；`herdr.dev/llms-full.txt`。
- 旧 `headless-cli-matrix.md` 的无头参数在当前版本仍存在，但与本文无关：定案是 Herdr 拉起的交互会话；`ADR 0020:18` 当时否决无头的理由（卡在提问界面只能挂死）在机制上仍成立。
