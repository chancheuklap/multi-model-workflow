# AGENTS.md

MMW 是用户跨 host、跨 repository、跨电脑共用的工作流 toolbox：交付技能。个人使用，没有 CI，测试手工跑。
只有 `mmw-v2/` 是活的。`archive/` 装的是 MMW 早先那一代，`deprecated/` 是 MMW v2 自己 retired 的技能与 subagent：两者都不改、不当事实，`archive/` 里的安装脚本一个都不要跑。
仓库里的技能是交付物，不是你的工作指南。

## 命令

没有包管理器和构建步骤。运行时只有 bash、`python3` 标准库和按需的 `uv`。

| 命令 | 干什么 |
| --- | --- |
| `bash mmw-v2/install.sh` | MMW 的全部安装都经这里，装七样：技能 symlink 进 `~/.agents/skills` 和 `~/.claude/skills`，hook 写进各 host 自己的配置（drive-target 的 `hook.py`、dispatch 的回合守卫 `turn-guard.py`；Codex 那几条的信任哈希一并写进 `~/.codex/config.toml`），用户级提示词（`~/.claude/CLAUDE.md` 软链到 `mmw-v2/prompt/shared.md`，Codex、Pi、Grok 各一份由 `mmw-v2/prompt/render.py` 拼出的 AGENTS.md），一个盯着源的 launchd 任务，Paseo 侧配置（`~/.local/bin/paseo` 软链、`~/.paseo/config.json` 里 grok/cursor 两条 provider、`worktrees.root`；不写 Agent profile；第一次把活表拷进 `~/.mmw/models.md`，之后不覆盖），Orca 侧工作树配置（有 orca 时每个 setup 的 `worktree-base-path` 为 `.worktrees`，`--check` 另核每个仓库的外部工作树可见性为 `show`），Cursor 的 Nowledge Mem MCP（`~/.cursor/mcp.json` 里 `mcpServers.nowledge-mem` 一条） |
| `bash mmw-v2/install.sh --check` | 只查不写：齐了回 0，缺东西或有 stale link 回 1。从别的 checkout 跑时按 `~/.mmw/installed-root` 记下的那个 checkout 核对，只核对不接管 |
| `python3 mmw-v2/prompt/render.py --adopt` | 每台机器首次装提示词时跑一次：目标位置原有的 AGENTS.md 不是生成物，`render.py` 默认拒绝覆盖 |
| `bash mmw-v2/prompt/tests/run.sh` | `render.py` 的测试 |
| `bash mmw-v2/tests/<名>/run.sh` | 单个技能的测试（`verify-ticket`、`drive-target`、`align-screens`、`dispatch`、`exe-release`、`manage-agents-md` 各有一份；dispatch 技能的 `relay.py` 另有一份 `relay`） |
| `bash mmw-v2/tests/claude-design-blocks/run.sh` | 交接包每个场景的数据导出（`export_scene_data.py`）、`mk.py` 生成页的语法、`selector_check.py` 的判据、`deadsweep.py` 的清扫范围：迷你夹具，Node 跑页自己的 logic class，无浏览器 |
| `bash mmw-v2/tests/board/run.sh` | task board 的本地进程、story page、API client 替身与交互 helper 的测试 |
| `bash mmw-v2/tests/liveness/run.sh` | 判活三层的测试：`turn-guard.py` 的守卫谓词与五个 host 的 payload（含三条撞车对策）、`watchdog.py` 的心跳、容差、锁身份、问 runner 的三种答案；假 board、假 runner，不起 host |
| `bash mmw-v2/hooks/tests/run.sh` | `rule-at-moment.py` 的测试 |

## 约定

- `SKILL.md` 对所有 host、所有 runner 是同一份：不把任何 host 当默认或首选，不按 host 名或 runner 名分支；能力差异用按能力判断的自然语言写。今晚用哪个 runner 由 `models.py runner` 选（最后一级是默认值），正文照写这个选法，不替它假定。某个 runner 自己的命令只写在它的适配器 `mmw-v2/skills/dispatch/scripts/runners/<runner>.sh` 里。frontmatter 的 `description` 不写任何 runner 的名字：它被扫进各 host 的系统提示，写一个就把整份技能锁在那个 runner 上；选定的 runner 起不来时，拒绝是脚本运行时 stderr 上的一行，不是 `description` 里的前置条件。
- 装哪些技能只改 `mmw-v2/skills.txt`。host 上的 symlink 直接指向 source directory，改完下一次调用即生效；只有 frontmatter 的 `description` 是 host 启动时扫进去的，改它要重开会话。
- `mmw-v2/skills/<名>/` 整个目录被软链进各 host，所以它只装拿着这份技能的 agent 要读要跑的东西：`SKILL.md`、reference 文件、`scripts/`。技能的测试在 `mmw-v2/tests/<名>/`，只存在于本仓库的 checkout 里；它从 `mmw-v2/tests/<名>/` 数两级回到 `mmw-v2/`，再进 `skills/<名>/scripts/` 找被测的脚本。
- 技能自带的脚本，由拿着这份技能的 agent 从它的 `SKILL.md` 就地解析 `scripts/…`；caller 只点技能名与要做的事，不写安装路径。装了技能就是拿到脚本，两者不会各自漂移，路径在五个 host 上都对。写进 ticket 的那条 `CHECK:` 也不写路径：它由 shell 执行、中间没有 agent，所以由跑它的 `verify-ticket.py` 把 drive-target 技能的 `scripts/` 放上那个 shell 的 `PATH`（`--tools`），判官按裸名调用；形状在 `mmw-v2/skills/drive-target/references/boundary-check.md` 与 `story-parity.md`。
- 一份技能指自己或兄弟技能的脚本，只用一种写法：开一节定义一个贯穿全文的记号，节名统一成 `` ## Resolve `<记号>` once ``，节里说这个记号在下文每条命令里展开成什么、并且从这份文件自己的位置解析一次。正文里不再出现裸相对路径，也不出现全文没有定义的记号。一个记号在整个工具箱里只解析出一个可执行文件——一个 agent 一次拿着好几份技能，把所有技能的词汇当成一套。
- 散文与命令里的绝对路径只有三类是合法的：(a) 本机用户级的固定位置（`~/.mmw/models.md`、`~/.agents/skills`、`~/.claude/skills` 这一类，它们就是那台机器上的地址，没有相对写法）；(b) 一个记号在运行时展开成的绝对路径（`` `<dispatch>` `` 展开成 `bash <absolute path to scripts/dispatch.sh>` 这一类——写在正文里的是记号，绝对路径只在执行时才有）；(c) 一次运行自己造出来的临时路径（`mktemp` 派生的，不是 `/tmp` 下的固定名）。这三类之外出现的绝对路径是缺陷。
- 本仓自写的技能不带 `agents/openai.yaml` 之类的 host 侧清单文件：一份技能的名字与描述只有 `SKILL.md` 的 frontmatter 一处权威。
- 每个 agent 用哪个 host、哪个 model、哪档 effort，只改本机 `~/.mmw/models.md`。第一次 `install.sh` 把默认行拷进去，之后不覆盖。仓里的 `hosts.json` 只记各 host 怎么起，不记今晚谁用谁。consuming repository 里不放。`dispatch.sh` 拿 `models.py` 解析这一行，再交给今晚的 runner 适配器（`mmw-v2/skills/dispatch/scripts/runners/<runner>.sh`）起会话。
- 用户级提示词只改 `mmw-v2/prompt/shared.md`（四家共用）和 `mmw-v2/prompt/hosts/<host>.md`（只给那一家）。`~/.codex/AGENTS.md`、`~/.pi/agent/AGENTS.md`、`~/.grok/AGENTS.md` 是生成物，直接改会被 `render.py` 拒绝覆盖。Cursor 不参与，它的用户级提示词在 app 里手动维护。
- `~/.cursor/mcp.json` 里的 `nowledge-mem` 一条由 `install.sh` 管：内容问本机 `nmem config mcp show --host cursor` 要，写进去之前摘掉它给的 `type` 字段——`cursor-agent` 只认 `url` 与 `headers`，带上 `type` 它把整条 server 跳过，症状是 worker 静默地没有 memory 工具。同一份文件里别的 server 不动；手改这一条，下次 `install.sh` 会覆盖，`--check` 会先报出来。
- `mmw-v2/upstream/` 是 mattpocock/skills 的 git subtree（squash），`mmw-v2/upstream-diagram-design/` 是 cathrynlavery/diagram-design 的另一个。两者都可编辑；upstream 自带的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动——`mmw-v2/upstream/CONTEXT.md` 是 upstream 自己的 vocabulary，本仓的 vocabulary 只有根 `CONTEXT.md`。拉 upstream 和解冲突见 `mmw-v2/merge-notes/README.md`；改了 upstream 的技能就写或更新它的 merge-note。
- 本仓库改动作废了 consuming repository 已有的产物，就写一份 downstream-note，判据与写法见 `mmw-v2/downstream-notes/README.md`。
- 两个 subtree 之外还有一份从 unlazy 抄进来的脚本：`mmw-v2/skills/verify-ticket/scripts/gate-check/`。它没有 subtree，`git subtree pull` 和 merge-note 都不管它，来源、commit 与改过哪几行记在 `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`。这份 `UPSTREAM.md` 是「技能目录只装拿着这份技能的 agent 要读要跑的东西」那条约定的唯一例外：它记的是这个目录里这几个文件的来源与本地改动，读它的人是下一次去 unlazy 那边比对的人，而他手上唯一的线索就是这个目录本身；挪出去，`scripts/` 里就剩一批看不出出处的第三方文件。

## Agent skills

### Issue tracker

本仓的 issue tracker 在 GitHub，全部操作走 `gh` CLI。See `docs/agents/issue-tracker.md`.

### Triage labels

五个 triage role 用默认 label（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）。See `docs/agents/triage-labels.md`.

### Domain docs

本仓的 Domain docs 是一份 `CONTEXT.md`（在 repository root，landing pipeline 的全部固定词，改 vocabulary 先读它）加 `docs/adr/`。See `docs/agents/domain.md`.

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
