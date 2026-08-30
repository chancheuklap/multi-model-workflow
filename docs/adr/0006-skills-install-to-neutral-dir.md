---
date: 2026-08-26
amends: [0003]
---

> 正文里的数目写的是 2026-08-26 当时的值。现在装几个技能见 `mmw-v2/skills.txt`，安装器里还有几处按宿主名写死的表见 `mmw-v2/install.sh`。

# 技能装进一个各家通用的位置，只为 Claude Code 单独再装一份

技能原来按宿主各装一份，五个用户级目录各 30 条软链。现在改为装两处：`~/.agents/skills` 和 `~/.claude/skills`，两处都直接指向仓库源目录。理由是 `~/.agents/skills` 不属于任何一家，而 Codex、Cursor、Grok、Pi 四家都扫它，其中 Cursor 和 Grok 扫它不受任何兼容开关控制；只有 Claude Code 不扫，所以那一处单独再装一份同样的软链。subagent 不走这条，仍按宿主各装一份——各家的模型字段写法不同，同一份正文必须换壳。

四家读 `~/.agents/skills` 是当天在本机逐个实测的：把一个探针技能放进 `~/.agents/skills/`，再用全新进程问每一家看不看得到。Grok 由 `grok inspect --json` 报出 `source.path`，Codex、Pi、Cursor 各起一个非交互进程原样贴出探针的 description。把探针换成指向仓库外的软链重测，四家同样认得。其中三家另有独立佐证：Grok 的用户文档写明它在每一层都扫 `.agents/skills/`，Pi 的 README 把 `~/.agents/skills/` 列进技能放置位置，Cursor 的 bundle 里这一条无条件加入用户级根目录列表。Codex 只有探针实测支撑，它的二进制里没有一处能直接读出用户级根目录清单。

Claude Code 在同一条件下答「没有」，它的二进制里 `.agents/skills` 零命中，技能根目录全部落在 `.claude` 体系内。能追加技能目录的设置键也搜不到——`skillDirs`、`extraSkill`、`additionalSkill` 三个都零命中。插件可以从别处带技能进来，但 ADR `0003` 已经否掉了插件这条路。

## Considered Options

- **维持五处各装一份。** 否决。五处装的是同一批软链，冗余本身不换来任何东西，而每加一个宿主就要在 `install.sh` 里多一行。更麻烦的是同名技能落在多处时各家的取舍不一致：实测中 Cursor 取 `~/.claude/skills` 那份，Codex 取 `~/.agents/skills` 那份，Grok 在把 `[compat.claude] skills` 临时置为 `true` 之后也取 `~/.agents/skills` 那份。三家都不报错也不提示。位置越多，撞名时越难判断哪一份在生效。
- **统一装进 `~/.claude/skills`，让别家从那里读。** 否决。别家读 Claude 的目录都要过一道兼容开关：Grok 有 `[compat.claude] skills`，默认 `true` 而本机当时是 `false`；Cursor 的 bundle 里 `.claude/skills` 与 `.codex/skills` 只在第三方兼容打开时才进用户级根目录列表，`.agents/skills` 与 `.cursor/skills` 则是无条件进的。把统一位置放在某一家的私有目录，等于把另外几家的可用性押在那家的兼容开关上。`~/.agents/skills` 没有这层依赖。
- **只装 `~/.agents/skills`，Claude Code 那份也省掉。** 否决。Claude Code 不扫通用位置，省掉那一份它就一个技能都看不见。
- **`~/.claude/skills/<名>` 软链到 `~/.agents/skills/<名>`，而不是各自直接指仓库。** 否决。两级软链没有验证过，而且 `install.sh` 判断一条链是不是自己装的，靠的是 `readlink` 的结果落不落在三个技能源目录里；桥指向 `~/.agents` 会让这条判断失效，冲突检测和退役清理整套逻辑都要跟着改写。两处各自直接指仓库，现有逻辑一行不用动。

## Consequences

- 软链从 150 条降到 60 条（`skills.txt` 30 条 × 位置数，前提是两处的宿主主目录都在）。
- 技能正文和用户触发开关照旧不按宿主分支。安装器里剩下的按宿主分支只有两处：Claude Code 那一个额外目标目录，和四个写死的退役目录。
- 再加一个扫 `~/.agents/skills` 的宿主时，技能那半边不用改 `install.sh`。subagent 那半边仍要加一行安装点和一份成品壳。
- `~/.agents/skills` 不属于任何宿主，无条件创建，不套用「宿主主目录不存在就跳过」那条规则。`~/.claude/skills` 照旧跳过。
- `~/.codex/skills`、`~/.pi/agent/skills`、`~/.cursor/skills`、`~/.grok/skills` 退役。它们不再是安装目标，主循环也不会走到，但各自的宿主仍在扫它们——残留的是上一轮名单里的旧版本，跟通用位置的那份撞名。实测里 Grok 取 `~/.grok/skills` 那份，把通用位置的盖住，不报错也不提示。因此 `install.sh` 每次运行都按各自的 `.mmw-skills` 摘一遍，`--check` 见到残留报「残留」并退出 1。
- `~/.claude/skills` 里除了 `install.sh` 装的那份，不能再有同名的东西，否则在 Cursor 那边会盖掉通用位置的版本。
- ADR `0003` 的「五个宿主由 `install.sh` 统一散装」对 subagent 仍然成立，对技能不再成立。0003 取消插件打包、由安装器散装这个决定本身没有变。

来源：2026-08-26 与用户的设计对话；当天在本机对 Grok 1.0.5、Codex 0.149.1、Cursor CLI 2026.08.11-e8db854、Claude Code 2.1.246、pi-coding-agent 0.84.3 所做的探针实测（探针测完已清理，磁盘上不可复核；撞名那一组在 Cursor 上复测两次并对调过标记文字）；以及 `~/.grok/docs/user-guide/08-skills.md`、`~/.grok/docs/user-guide/05-configuration.md`、`~/.grok/config.toml`、pi-coding-agent 的 `README.md`、Cursor CLI bundle 与 Claude Code 二进制里的技能发现代码。
