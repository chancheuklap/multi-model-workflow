---
date: 2026-09-05
amends: []
---

# 用户级提示词的源放在仓库里，host 目录只放软链或生成物

四个 host 的用户级提示词（Claude Code 的 `~/.claude/CLAUDE.md`，Codex 的 `~/.codex/AGENTS.md`，Pi 的 `~/.pi/agent/AGENTS.md`，Grok 的 `~/.grok/AGENTS.md`）原来是四份手工维持一致的拷贝，只有 Codex 那份多开头两行。现在源只有一处：`mmw-v2/prompt/shared.md` 是共用正文，`mmw-v2/prompt/hosts/<host>.md` 是只给那一家的补充。Claude Code 读软链，另外三家读 `mmw-v2/prompt/render.py` 拼出的文件；`install.sh` 装这一切并装一个 launchd 任务盯着源，改了就重拼。理由与技能、subagent 相同：源在仓库才有历史、能跨机器、能被 `--check` 查漂移。

Cursor 不在此列，它的用户级提示词只能在 app 里手动粘贴。

## 各家能读什么，决定了各家怎么装

2026-09-05 在本机查的：Claude Code 2.1.261 的二进制与官方 memory 文档，Codex 0.152.0 的二进制与官方 AGENTS.md 文档，pi-coding-agent 0.84.4 的 README 与 `dist/`，Grok 的 `~/.grok/docs/user-guide/12-project-rules.md`、`05-configuration.md` 与 `grok inspect` 实测。

- Claude Code 读 `~/.claude/CLAUDE.md` 与 `~/.claude/rules/*.md`，支持 `@路径` 引入，认软链；不读 `~/.claude/CLAUDE.local.md`，不读 AGENTS.md。
- Codex 读 `~/.codex/AGENTS.override.md`，没有才读 `~/.codex/AGENTS.md`，只取一个；没有引入语法；指令文件合计上限 32 KiB。
- Pi 读 `~/.pi/agent/AGENTS.md` 或 `CLAUDE.md`，`AGENTS.override.md` 存在则替换；没有引入语法；还会沿 cwd 向上读到 `~/AGENTS.md`。
- Grok 读 `~/.grok/AGENTS.md`、`~/.grok/rules/*.md`，还沿 cwd 向上读到 `~/AGENTS.md`；`[compat.claude] agents` 开着时另读 `~/.claude/` 下的 `CLAUDE.md`、`CLAUDE.local.md`、`AGENTS.md`、`Claude.md`、`AGENT.md`。本机这项当天是开的，`grok inspect` 显示同一份提示词被载入两次。

所以：Claude Code 用软链（`~/.claude/CLAUDE.md` 指 `shared.md`，`~/.claude/rules/mmw-claude.md` 指 `hosts/claude.md`），另外三家没有引入语法只能拼接，Grok 的 `[compat.claude] agents` 要关掉，`render.py` 见到没关就报。

## Considered Options

- **专属件放 `~/.config/agent-prompt/`，仓库外。** 否决。不在 git 里，没有历史，跨机器要另抄。
- **专属件按 host 放在各自目录，叫 `AGENTS.local.md` 之类。** 否决。各家都在兼容别家的文件名：Grok 会读 `~/.claude/CLAUDE.local.md`，Pi 会读 `CLAUDE.md`。放在 host 目录下、名字沾 CLAUDE 或 AGENTS 的文件，随时可能被第二家顺手读走。源放仓库里，host 目录只有生成物，没有这个问题。
- **主本留在 `~/.claude/CLAUDE.md`，只把专属件进仓库。** 否决。git 只管一半，主本仍在仓库外裸奔。Claude Code 认软链，主本进仓库对使用者没有代价：在 Claude Code 里改 CLAUDE.md，写进去的就是仓库文件。
- **让 Grok 继续走 `[compat.claude]` 直接读 `~/.claude/CLAUDE.md`，不为它生成。** 否决。省一份生成物，代价是 Grok 的加载依赖它的兼容开关，专属件的隔离也要跟着那个开关走；且 `~/.grok/AGENTS.md` 仍要存在放专属内容，等于两条路并行。三家一律生成，机制只有一种。
- **`render.py` 用状态文件记上次写了什么，来识别生成物有没有被人改。** 否决。`install.sh` 已经放弃过记账文件（`.mmw-skills`），理由是记录会被下一次安装重写。改为把正文哈希写进生成文件第一行的 HTML 注释：文件自己说明自己是不是原样，不需要旁边的记录。
- **不装 launchd，只靠 `install.sh` 与手跑。** 否决。使用者在 Claude Code 里改 CLAUDE.md 后不会想起要跑一次同步；launchd 是 macOS 自带的，按文件变化触发，不装任何东西。

## Consequences

- `install.sh` 装的东西从四样变五样；`install.sh --check` 顺带比对三份生成物与源、两条软链、launchd 任务。
- 每台机器首次装要跑一次 `python3 mmw-v2/prompt/render.py --adopt`：目标位置原有的文件不是生成物，`render.py` 不认，拒绝覆盖。
- 生成物被人直接改过时 `render.py` 退出 2 不覆盖，改动要搬回 `hosts/<host>.md` 或 `shared.md` 再 `--adopt`。
- launchd 的 WatchPaths 记的是本 checkout 的绝对路径；换 checkout 跑一次 `install.sh` 就重写。编辑器用「写新文件再改名」保存时 WatchPaths 是否每次触发未实测，`install.sh` 与手跑兜底。
- `~/.claude/CLAUDE.md` 是软链后，Claude Code 桌面版的 Cowork 会话会跳过它（官方文档写明）；终端与 IDE 不受影响。
- `~/AGENTS.md` 不在本决定范围内，Pi 与 Grok 照旧读它。

来源：2026-09-05 与用户的设计对话，及上述各家文档与实测。
