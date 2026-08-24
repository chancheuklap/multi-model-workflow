# 五宿主 hook 能力矩阵（本机取证记录）

> discipline-hooks spec 的附件。2026-08-24 在本机取证，取证会话的原始报告收敛于此；实现前如宿主升级，按下表「取证对象」列的路径重验。宿主版本：Claude Code 2.1.241、Codex 0.149.1、cursor-agent 2026.08.11-e8db854、Grok Build 1.0.5、pi 0.84.2。ponytail 克隆 = https://github.com/DietrichGebert/ponytail @ 2ed6c52。

## ① 会话开始注入（SessionStart 等价物）

| 宿主 | 有/无 | 机制 | 输出形状要点 | 取证对象 |
|---|---|---|---|---|
| Claude Code | 有 | `SessionStart`（matcher `startup\|resume\|clear\|compact`） | 裸 stdout 即上下文，不需 JSON | ponytail `hooks/claude-codex-hooks.json`、`hooks/ponytail-runtime.js` 尾注 |
| Codex | 有 | `SessionStart` / 线上名 `session_start` | 必须 JSON：`{systemMessage, hookSpecificOutput:{hookEventName, additionalContext}}` | 同一份 hooks JSON 经 `.codex-plugin/plugin.json` 引用；codex 二进制含 `SessionStartHookSpecificOutputWire` |
| Cursor | 有 | `sessionStart`；发现路径 `~/.cursor/hooks.json`、项目 `.cursor/hooks.json` | 响应接受 `additional_context`（string）与 `env` | cursor-agent bundle 校验器；本机 `~/.cursor/hooks.json` 已有 herdr 的活条目 |
| Grok Build | 有事件、无注入 | `SessionStart` 被动 | 只有 `PreToolUse`/`Stop`/`SubagentStop` 是 blocking，「every other event is passive」 | `~/.grok/docs/user-guide/10-hooks.md` |
| pi | 事件有、注入在别处 | 扩展事件 `session_start`（进程内回调） | 无 JSON 协议；真正注入在 `before_agent_start` | pi 包内 `docs/extensions.md`；ponytail `pi-extension/index.js` |

## ② 每轮 prompt 注入

| 宿主 | 机制 | 要点 |
|---|---|---|
| Claude Code | `UserPromptSubmit` | stdin 收 `{prompt}`；支持 `hookSpecificOutput.additionalContext` |
| Codex | `user_prompt_submit` | JSON 同①；exit 2 + stderr = 阻断理由 |
| Cursor | `beforeSubmitPrompt` | 响应 `{continue, user_message, additional_context}`——可注入、可改写、可中断 |
| Grok Build | 被动 | 「`UserPromptSubmit` is observe-only」 |
| pi | `before_agent_start` | 返回 `{systemPrompt}` 直接**替换**本轮系统提示（多扩展链式叠加）——五家里最强的注入口 |

## ③ subagent 启动注入

| 宿主 | 机制 | 要点 |
|---|---|---|
| Claude Code | `SubagentStart` | **必须** `hookSpecificOutput` JSON 形式，否则上下文被丢弃；stdin 给 `agent_type` 可做作用域过滤 |
| Codex | `subagent_start` | `SubagentStartHookSpecificOutputWire`；本机 `~/.codex/config.toml` 已有 ponytail 注册痕迹 |
| Cursor | `subagentStart` | 响应含 `permission?/user_message/additional_context`；输入含 `subagent_type`、`is_parallel_worker` |
| Grok Build | 被动 | matcher 可测 subagent type，但输出不进模型 |
| pi | 无独立事件 | `before_agent_start` 对 subagent 同样触发并可改其可见系统提示（本机扩展测试证实）——盲区不存在，缺的是独立控制粒度 |

## ④ 会话结束拦截（Stop 等价物）

| 宿主 | 机制 | 输出形状 |
|---|---|---|
| Claude Code | `Stop` / `SubagentStop` / `SessionEnd` | `{decision:"block", reason}` 惯例 |
| Codex | 同上 | `StopCommandOutputWire`；exit 2 + stderr = 续跑提示（错误串原文可证） |
| Cursor | `stop` / `subagentStop` | 响应 `{followup_message}`——只能追加后续消息，无 decision 字段 |
| Grok Build | `Stop` / `SubagentStop`（唯一注入口） | 三形状：`{"decision":"block","reason"}` ／ `hookSpecificOutput.additionalContext` ／ `{"continue":false,"stopReason"}`；默认 timeout 600s，每轮最多 8 次续跑 |
| pi | 无拦截 | `agent_end` 等只读；可 `pi.sendUserMessage` 推送但非门控 |

## ⑤ 常驻规则文件（降级层）

| 宿主 | 路径 | 形状 |
|---|---|---|
| Claude Code | `CLAUDE.md` / `AGENTS.md` | 纯 Markdown |
| Codex | 仓库根或 `~/.codex/AGENTS.md`（本机已存在） | 纯 Markdown |
| Cursor | `.cursor/rules/*.mdc` | **必须** YAML frontmatter（`alwaysApply: true`）；用户级全局目录本机为空——常驻规则只能逐仓库落 |
| Grok Build | `$GROK_HOME/rules/*.md`（默认 `~/.grok/rules/`）；派发时另有 `--rules` 参数追加 | 直接 append 到系统提示 |
| pi | `AGENTS.md`/`CLAUDE.md` 自动发现（`-nc` 可关） | `--append-system-prompt` 文本或文件路径通吃 |

## 分流层要点

- 一份 hook JSON 喂 Claude+Codex；Grok 明文「skips unrecognized event names so a shared Claude or Cursor settings file still loads」，且默认扫描 `~/.claude/settings.json` 与 `~/.cursor/hooks.json`（`[compat.<vendor>] hooks` 可关；本机当前两项为 false）。
- 输出形状不统一：ponytail `writeHookOutput`（39 行；hooks 目录合计约 670 行零依赖 Node）枚举了 Copilot / Codex / Qoder / Claude（SubagentStart 单列）四家；Cursor / Grok / pi 三家按上表补。
- 宿主判定靠环境变量：`PLUGIN_DATA`（Codex）、`COPILOT_PLUGIN_DATA`、`CLAUDE_PLUGIN_ROOT`、`QODER_SESSION_ID`。
- 全部脚本 fail-open + 超时 + stdin 容错（ponytail issue #443 的 Windows 冻死事故）。
