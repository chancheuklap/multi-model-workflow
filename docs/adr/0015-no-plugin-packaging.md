---
date: 2026-08-18
amends: []
---

> 现行读法见 ADR 0018：技能改装 `~/.agents/skills` 与 `~/.claude/skills` 两处，本篇「五个宿主各装一份」只对 subagent 仍然成立。取消插件打包、由安装器散装这个决定本身没有变。
>
> 下面正文写的是 2026-08-18 当时的状态。安装入口现在是 `mmw-v2/install.sh`；正文里的 `mmw/install.sh` 已进 `archive/`，**不要跑它**，它会把活的安装整个换成上一代。九个交付面现在只剩技能与 subagent 两面，其余七面连同 `mmw` CLI 一起退役。

# MMW 不打包成插件，五个宿主由 `install.sh` 统一散装

MMW 由九个交付面组成：CLI 与 runtime、技能、角色、hooks、MCP、权限、UI QA 依赖、Cursor 隔离包装、语言服务器插件。插件格式最多装得下其中四面，而且只在两个宿主上——Claude Code 与 Codex。实际行为几乎全在 CLI 里（`mmw launch`、`mmw artifact path`、`mmw worktree`、`mmw dispatch`、图谱、出包），没有任何插件格式装得下它，2026-08-06 发布的 Agent Plugins 1.0 也明确不定义安装机制。半个插件加半个安装器，等于两条安装路径都要维护，而任何一条都不完整。

因此取消打包：删掉 `mmw/.claude-plugin/`、`mmw/.codex-plugin/`、根 `.claude-plugin/marketplace.json`、根 `.agents/plugins/marketplace.json`，全部九面由 `mmw/install.sh` 装进各宿主自己的用户级目录。

## Considered Options

- **保留插件，缺的那几面继续由 install.sh 补。** 否决。这正是取消之前的状态：两条路径并存，而版本号闸门（`install.sh` 的 `require_version_bump` 与 AGENTS.md 的五处版本号同步）整套机制都只为了对付插件缓存不刷新。九面里插件盖住四面，省不掉安装器，却多出一套缓存语义和一处必须手工同步的版本号。
- **改用 Agent Plugins 1.0 这个中立标准打包。** 否决。实测 Codex 0.147.0 装得下只有 `.claude-plugin/` 清单的插件，Claude Code 2.1.234 装得下清单在根的插件，Grok 1.0.4 两种都验证通过——互认不是问题。问题是那个标准只管技能与 MCP 两面，角色、hooks、权限、CLI 都不在里面，换成它反而把盖住的面从四个减到两个。
- **只保留 Codex 那一份，为了 App 插件界面里的条目。** 否决。`interface` 块只换来一个图标，代价是 Codex 这一个宿主保留整套打包语义：`.codex-plugin/plugin.json`、marketplace、插件缓存、版本号闸门、`installed_plugin_root()` 那一串校验。技能与 hook 照样得由 install.sh 装。

## Consequences

- 版本号闸门与「五处版本号同步」一起删除。改完跑一次 `mmw/install.sh`，宿主读到的就是新内容。
- 别人安装从「给一个 marketplace 地址」变成 `git clone` 加一条 `bash mmw/install.sh`。MMW 不再出现在 Codex App 的 Plugins 界面里。
- 插件命名空间随之消失：Claude Code 的 subagent 从 `mmw:mmw-reviewer` 变成 `mmw-reviewer-claude`，Codex 的技能引用从 `$mmw:mmw-reviewer` 变成 `mmw-reviewer`，检索工具名从 `mcp__plugin_mmw_<服务器>__` 变成 `mcp__<服务器>__`。
- `mmw mcp serve` 与 `mmw/mcp/serve.py` 删除。它们是 Codex 插件的 stdio 进程入口；Codex 现在从 `~/.codex/config.toml` 直接读真实命令。`runtime.py check-mcp-config` 同理删除——它要求 MCP 配置写成 `mmw mcp serve <名>`，那条护栏现在拦的是正确配置。
- 技能物化随之作废。物化曾经展开派发动作，派发改成运行期查表（`cli/host-actions.json`）之后只剩 Codex 的技能引用语法一条改写；Codex 认 `/mmw-review`，那条也没有了。五份技能产物删除，五个宿主软链同一份 `mmw/skills-src/`。
- 卸载改由安装器负责：每个目标目录留一份 `.mmw-skills` 或 `.mmw-agents` 清单，装之前按它清理退役的条目。目录里同名的东西不是 MMW 装的就不动，报冲突并非零退出。

来源：2026-08-18 与用户的设计对话，以及当天在本机对 Codex 0.147.0、Claude Code 2.1.234、Grok 1.0.4 三家插件清单互认所做的实测（测完已还原）。
