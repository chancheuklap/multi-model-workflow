# AGENTS.md

MMW 是用户跨 host、跨 repository、跨电脑共用的工作流 toolbox：交付技能和 subagent。个人使用，没有 CI，测试手工跑。
只有 `mmw-v2/` 是活的。`archive/` 装的是 MMW 早先那一代，`deprecated/` 是 MMW v2 自己 retired 的技能与 subagent：两者都不改、不当事实，`archive/` 里的安装脚本一个都不要跑。
仓库里的技能是交付物，不是你的工作指南。

## 命令

没有包管理器和构建步骤。运行时只有 bash、`python3` 标准库和按需的 `uv`。

| 命令 | 干什么 |
| --- | --- |
| `bash mmw-v2/install.sh` | MMW 的全部安装都经这里，装五样：技能 symlink 进 `~/.agents/skills` 和 `~/.claude/skills`，assembled subagent file symlink 进各 host，hook 写进各 host 自己的配置，agent detection rule 拷进 `~/.config/herdr/agent-detection/`，用户级提示词（`~/.claude/CLAUDE.md` 软链到 `mmw-v2/prompt/shared.md`，Codex、Pi、Grok 各一份由 `mmw-v2/prompt/render.py` 拼出的 AGENTS.md，加一个盯着源的 launchd 任务） |
| `bash mmw-v2/install.sh --check` | 只查不写：齐了回 0，缺东西或有 stale link 回 1 |
| `python3 mmw-v2/agents/assemble.py --check` | 校验 `mmw-v2/agents/<名>/out/` 的 assembled subagent file 与源一致。`install.sh --check` 已内含它；单跑用于只验这一样 |
| `python3 mmw-v2/prompt/render.py --adopt` | 每台机器首次装提示词时跑一次：目标位置原有的 AGENTS.md 不是生成物，`render.py` 默认拒绝覆盖 |
| `bash mmw-v2/prompt/tests/run.sh` | `render.py` 的测试 |
| `bash mmw-v2/skills/<名>/tests/run.sh` | 单个技能的测试 |
| `bash mmw-v2/hooks/tests/run.sh` | `rule-at-moment.py` 的测试 |

## 约定

- `SKILL.md` 对所有 host 是同一份：不把任何 host 当默认或首选，不按 host 名分支；能力差异用按能力判断的自然语言写。
- 装哪些技能只改 `mmw-v2/skills.txt`。host 上的 symlink 直接指向 source directory，改完下一次调用即生效；只有 frontmatter 的 `description` 是 host 启动时扫进去的，改它要重开会话。
- 技能自带的脚本，由拿着这份技能的 agent 从它的 `SKILL.md` 就地解析 `scripts/…`；caller 只点技能名与要做的事，不写安装路径。装了技能就是拿到脚本，两者不会各自漂移，路径在五个 host 上都对。唯一的例外是写进 ticket 的那条 `CHECK:`——它由 shell 执行，中间没有 agent，所以路径写全，形状与理由在 `mmw-v2/skills/verify-ticket/references/ui-parity.md`。
- 每个 agent 用哪个 host、哪个 model、哪档 effort、什么 launch arguments，只改 `mmw-v2/skills/dispatch/models.md`。它跟着技能的 symlink 走，是这台机器的一份，consuming repository 里不放。
- 用户级提示词只改 `mmw-v2/prompt/shared.md`（四家共用）和 `mmw-v2/prompt/hosts/<host>.md`（只给那一家）。`~/.codex/AGENTS.md`、`~/.pi/agent/AGENTS.md`、`~/.grok/AGENTS.md` 是生成物，直接改会被 `render.py` 拒绝覆盖。Cursor 不参与，它的用户级提示词在 app 里手动维护。
- `mmw-v2/upstream/` 是 mattpocock/skills 的 git subtree（squash），`mmw-v2/upstream-diagram-design/` 是 cathrynlavery/diagram-design 的另一个。两者都可编辑；upstream 自带的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动——`mmw-v2/upstream/CONTEXT.md` 是 upstream 自己的 vocabulary，本仓的 vocabulary 只有根 `CONTEXT.md`。拉 upstream 和解冲突见 `mmw-v2/merge-notes/README.md`；改了 upstream 的技能就写或更新它的 merge-note。
- 两个 subtree 之外还有一份从 unlazy 抄进来的脚本：`mmw-v2/skills/verify-ticket/scripts/gate-check/`。它没有 subtree，`git subtree pull` 和 merge-note 都不管它，来源、commit 与改过哪几行记在 `mmw-v2/skills/verify-ticket/scripts/gate-check/UPSTREAM.md`。

## Agent skills

### Issue tracker

本仓的 issue tracker 在 GitHub，全部操作走 `gh` CLI。See `docs/agents/issue-tracker.md`.

### Triage labels

五个 triage role 用默认 label（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）。See `docs/agents/triage-labels.md`.

### Domain docs

本仓的 Domain docs 是一份 `CONTEXT.md`（在 repository root，landing pipeline 的全部固定词，改 vocabulary 先读它）加 `docs/adr/`。See `docs/agents/domain.md`.

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
