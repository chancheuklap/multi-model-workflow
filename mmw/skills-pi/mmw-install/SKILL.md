---
name: mmw-install
description: 把 MMW 装到这台电脑、把这个仓库配好。用于新电脑第一次装、新仓库第一次配、用户说「配一下这个仓库」或「装一下 MMW」、`mmw` 命令找不到，或者升级 MMW 之后重装。日常开发不使用。
---

一句话交代这件事的全貌：**MMW 装一次管这台电脑的所有宿主，仓库配一次管这个仓库的所有语言。**两件事分开，第一次上手两件都要做，之后换仓库只做第二件。

四步，按顺序走完。每一步都幂等，已经做过就跳过，重跑无害。

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

这一条覆盖 Claude Code、Codex、Pi、Cursor、Grok 五个宿主：技能、agent、MCP 服务器、编辑后诊断的 hook 与扩展、`mmw` 命令本身，还有 Claude Code 的两个语言服务器插件（装用户级，所有仓库都有）。Grok 的技能、角色和 Stop hook 打散到 `~/.grok/`。

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

## 配好之后是什么样

- 五个宿主都能用 MMW 的技能和 agent
- 改完一个文件，宿主立刻报这个文件的诊断——判据同一份。Claude Code 走 LSP 插件加 hook，Codex 走 hook，Pi 走扩展，Grok 走 Stop hook
- 持续集成跑的判据和本地这一批是同一份规则表、同一批检查器

诊断和持续集成为什么能对得上、规则表怎么改、谁拥有哪份配置，跑 `mmw toolchain` 看用法，再读规则表 `config/toolchain-rules.json` 的文件头。
