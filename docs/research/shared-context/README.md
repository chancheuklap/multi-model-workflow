# 多 agent 共享上下文与降返工调研

调研日期 2026-09-13。问题：Cursor Projects 的 Project Context 与同类产品、开源实现怎样在 agent 之间组织、流转、更新共享上下文；Nowledge Mem 能否作为 MMW 的共享上下文载体；参考对象里哪些机制能让 MMW 的产出更忠于设计意图、返工更少。

每份报告带英文原文引语、URL 或固定 commit 链接，以及读取状态（全文、只读摘要、抓取失败）；"推断"表示调研者推出、来源未直接陈述。报告正文里的 MMW 事实以写作当日的工作树 `0f438594` 为准。

## 文件

| 文件 | 内容 |
| --- | --- |
| [report.html](report.html) | 汇总：MMW 现状对照、参考对象要点、Nowledge Mem 定位、四阶段方案、不采纳的做法、衡量指标、待定决策 |
| [research-1-cursor.md](research-1-cursor.md) | Cursor Projects：官方博客与 changelog、本机 Cursor 3.20.17 客户端代码里的默认提示词与同步逻辑、论坛 |
| [research-2-commercial.md](research-2-commercial.md) | Claude Code、Codex、Devin、Factory、Copilot、Jules/Conductor/Antigravity、Kiro 等 13 家的共享上下文设计与横向对比 |
| [research-3-opensource.md](research-3-opensource.md) | 22 个开源实现（beads、gastown、overstory、mcp_agent_mail、spec-kit、BMAD 等）的读写与并发机制 |
| [research-4-theory.md](research-4-theory.md) | Anthropic、Cognition、Manus、LangChain、OpenAI 与相关论文：原则、失败模式、谁写谁读的建议 |
| [research-5-nowledge-mem.md](research-5-nowledge-mem.md) | Nowledge Mem 数据模型、读写路径、五个 host 的接入、局限，以及与 MMW 四层 context 的映射 |
| [research-6-factory.md](research-6-factory.md) | Factory Missions 全生命周期、验收契约、validator、handoff，与 MMW 逐项对照 |
| [research-7-bmad-anthropic-pwf.md](research-7-bmad-anthropic-pwf.md) | BMAD-METHOD v6、Anthropic 长时任务文章、planning-with-files 的机制与 MMW 对照 |
| [research-8-monomind-devin-augment.md](research-8-monomind-devin-augment.md) | monomind project-context 与 project-hub、Devin、Augment 的知识采集、提升、检索、防陈旧 |
| [research-9-rework.md](research-9-rework.md) | 按返工成因分类的机制：Copilot、OpenAI、Kiro、Claude Code、25 篇论文与一线实践 |
| [notes/devin-notes.md](notes/devin-notes.md) | research-8 引用的 Devin 完整笔记与 URL 清单 |
| [notes/augment-notes.md](notes/augment-notes.md) | research-8 引用的 Augment 完整笔记与 URL 清单 |
| [notes/mmw-brief.md](notes/mmw-brief.md) | 交给第二轮调研 agent 的 MMW 背景说明 |

## 未收录的材料

报告里写作 `scratchpad/...` 的路径指调研时的临时目录，没有进仓库：

- `scratchpad/nm/`：Nowledge Mem 只读命令的原始输出与本机 server 的 `openapi.json`。其中含个人记忆库内容，不入库。
- `scratchpad/r7.*`、`scratchpad/r8mono.*`、`repos.*` 等：第三方仓库的浅克隆。报告已给出固定 commit 链接，可从 GitHub 重新取得。

## 读法

- 先读 `report.html`，再按需打开对应报告。
- `report.html` 第 10 节列出早期版本里被更正的三处说法。
- research-5 与 research-8 对 Nowledge Mem 的描述，前者基于命令实测，后者只读了 help 文本；两者不一致时以 research-5 为准。
