---
name: mmw-install
description: 把 MMW 装到这台电脑、把这个仓库配好。用于新电脑第一次装、新仓库第一次配、用户说「配一下这个仓库」或「装一下 MMW」、`mmw` 命令找不到，或者升级 MMW 之后重装。日常开发不使用。
---

一句话交代这件事的全貌：**MMW 装一次管这台电脑的所有宿主，仓库配一次管这个仓库的所有语言。**两件事分开，第一次上手两件都要做，之后换仓库只做第二件。

五步，按顺序走完。每一步都幂等，已经做过就跳过，重跑无害。

## 1. MMW 装到这台电脑

先看装没装：

```bash
command -v mmw && mmw --version
```

找得到就跳到第 2 步。找不到，从 MMW 源码仓库装：

```bash
cd <MMW 源码仓库>
bash mmw/install.sh
```

这一条覆盖 Claude Code、Codex、Pi、Cursor 四个宿主：技能、agent、MCP 服务器、编辑后诊断的 hook 与扩展、`mmw` 命令本身，Cursor 的隔离包装 `mmw-cursor-agent`，还有 Claude Code 的两个语言服务器插件（装用户级，所有仓库都有）。Cursor 不把整棵 `mmw/` 装成 plugin，而是散装到 `~/.cursor/skills`、`~/.cursor/agents`、`~/.cursor/mcp.json`、`~/.cursor/hooks.json` 和 PATH。

装完宿主要重启，或者开一个新会话，新装的东西才加载。

**前置**：`git`、`python3`、`jq`、`node`。缺哪个装哪个，install.sh 会报。

## 2. 仓库配好

在目标仓库里跑：

```bash
mmw init
```

这一条做完仓库该有的全部配置，并把它们提交进当前分支。工具链那一部分按仓库实际用的语言产出——有 Python 就配 Python 的，有 TypeScript 就配 TypeScript 的，没有的语言不产出任何东西。

产出物和判据都来自 MMW 的规则表与模板，不是每个仓库各写一份。所以换个仓库、换台电脑，跑这一条就回来了。

## 3. 缺的工具装上

配置写好了不等于工具在。看缺什么：

```bash
mmw toolchain detect
```

报「缺」的条目，末尾一行就是装它的命令。要 MMW 代跑：

```bash
mmw toolchain install          # 只列不装，先看清楚
mmw toolchain install --yes    # 确认之后真装
```

**装之前把清单给用户看，等他点头再加 `--yes`。**这些命令会往全局或工作区装东西。

装完再 `mmw toolchain detect` 确认一遍，「待办」那行应该是「无」。

## 4. Codex 的 hook 要用户确认一次

Codex 不会自动信任插件带来的 hook。它在**交互式**会话里弹确认，`codex exec` 不弹也不跑 hook。

告诉用户：开一个交互式 Codex 会话，看到 MMW 的 hook 确认提示时同意一次。

**每次 MMW 升版都要重来一次**——Codex 的信任哈希把展开后的插件路径算进去，路径里含版本号。

这一步只有用户能做，你做不了，也不要试着改 `~/.codex/config.toml` 里的 `trusted_hash`。

## 5. Cursor 要用户做的三件事

这台机器装了 Cursor 时才做。这三件只有用户能做：

1. 在 App 设置里关闭 Include third-party Plugins, Skills, and other configs。关掉之后，Agents Window 的主 agent 只加载 Cursor 自己的技能和 MCP，不再加载用户级 `~/.codex/skills` 与 `~/.claude/skills`。CLI worker 由 `mmw-cursor-agent` 隔离，不靠这一项。
2. 把 `cursor.worktreeMaxCount` 调到大于默认 25。Cursor 会回收 `~/.cursor/worktrees/` 里的树；数量太低时，还没结束的任务树会被清掉。
3. 把 Agents Window 的编排模型选成 grok，与已安装 runtime 的 orchestrator 一致。CLI worker 的模型由 `mmw-cursor-agent --mmw-role` 注入，不要去改 `cli-config.json` 里用户自己的默认模型。

## 配好之后是什么样

- 四个宿主都能用 MMW 的技能和 agent
- 改完一个文件，宿主立刻报这个文件的诊断——四个宿主看到的是同一批，判据同一份
- 持续集成跑的判据和本地这一批是同一份规则表、同一批检查器

诊断和持续集成为什么能对得上、规则表怎么改、谁拥有哪份配置，跑 `mmw toolchain` 看用法，再读规则表 `config/toolchain-rules.json` 的文件头。
