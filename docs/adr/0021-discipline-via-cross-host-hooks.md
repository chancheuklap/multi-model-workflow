---
date: 2026-08-24
amends: []
---

# 执行纪律经跨宿主 hook 层送达，注入能力缺口按宿主降级

落地流水线的执行纪律（先读后写、反偷懒、反作弊、账本未清不许收工）必须到达实际写代码的 agent。只写在技能正文或主会话里送不到位：在 Claude Code 上，会话级注入的上下文不进 Task 派生的 subagent（参考项目 ponytail 为此专门写了 SubagentStart hook，其注释点名 issue #252）；纯 prompt 约束也没有「会话想结束时被拦下」的兜底。

选 hook 层，应抄尽抄 ponytail 的实现。本机实测的能力矩阵支撑其可行性：Claude、Codex、Grok 三家的 hook 配置是同一套 schema（ponytail 用一份 `claude-codex-hooks.json` 同时喂 Claude 与 Codex；Grok 文档明确跳过不认识的事件名，且默认扫描 `~/.claude/settings.json`）；本机 cursor-agent 2026.08 版的 hook 枚举含 sessionStart、subagentStart、stop 全套，且 `~/.cursor/hooks.json` 已有在运行的 hook；pi 无 hook JSON，但其扩展机制的 `before_agent_start` 能直接替换系统提示，注入反而最强。输出 JSON 形状各家不统一。ponytail 的分流函数 `writeHookOutput`（39 行；所在 hooks 目录合计约 670 行、零第三方依赖的 Node）枚举了它自己接的四家——Copilot、Codex、Qoder、Claude（Claude 的 SubagentStart 单列一支）；本仓要接的 Cursor、Grok、pi 三家不在其内，形状已在本机取证，分流层需照样补齐。

v1 装三类事件：开场纪律注入（SessionStart 等价物）、subagent 启动注入（支持的宿主顺手带上）、完成拦截（Stop 等价物：票的验收关卡未清、会话想结束就顶回去——思想来自参考项目 unlazy 的 Stop hook）。已知缺口按宿主降级：Grok 的开场类事件全部被动，本 v1 所用的三类事件里唯一能把文字送回模型的是 Stop/SubagentStop 拦截，开场纪律走 `$GROK_HOME/rules/` 下的规则文件（默认 `~/.grok/rules/`）或派发时 `--rules`；pi 无 subagent 生命周期事件、无结束拦截，只做开场注入。所有 hook 脚本失败一律 fail-open（照常放行），不许把会话卡死——这是 ponytail 用 Windows 冻死会话的事故（其 issue #443）换来的规则。

## Considered Options

- **不建 hook 层，纪律只靠票内简报与派发 prompt。** 否决。这是本次设计过程中顾问给过的初始裁决，被用户推翻，推翻有据：hook 是唯一不依赖 agent 自觉的送达与兜底通道，而ponytail 覆盖约 24 个宿主，其中经 hook JSON 注入的是 Claude、Codex、Qoder、Copilot 四家，其余走规则文件层——本决定采用的正是这套「hook 有则用、无则按宿主降级」的分层结构，其成本（一份 JSON + 薄分流 + 降级文件）远低于当初估计。
- **只在 Claude Code 装 hook。** 否决。违反「技能与其配套对五个宿主同一份、能力差异用按能力判断的语言写」的仓库约定；且实测表明 Codex、Cursor 的 hook 面同样齐全，放弃是白丢能力。
- **等各宿主 hook 标准统一再做。** 否决。要处理的输出形状差异有限且已可枚举（ponytail 枚举了它那四家，其余三家本机已取证）；等待没有确定的终点。

## Consequences

- MMW 新增第三类交付物：hook 层（一份共享 JSON、三个注入脚本、一个分流 runtime、一个 pi 扩展、Grok 的 `rules/` 降级文件），`install.sh` 要学会安装它——这是 install.sh 首次接触技能与 subagent 之外的产物形态。
- 纪律文本进入「一份正文、多处送达」的状态，承重句必须钉进机械校验（承重句不变量清单），防止改写时静默漂移——手法抄 ponytail 的 `check-rule-copies.js`。
- Cursor 的 hook 用户级路径与本机既有的 herdr hook 共存于 `~/.cursor/hooks.json`，安装时必须合并不得覆盖。

来源：2026-08-24 与用户的设计对话；本机五宿主 hook 能力实测（ponytail 本地克隆的适配器与分流层逐文件阅读、各宿主二进制与配置目录取证）。
