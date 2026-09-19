---
date: 2026-09-20
amends: []
---

# 设计的唯一源头是 Claude Design 项目，仓库里的 handoff package 只由 pull 写入

界面在 Claude Design 里定稿。仓库里的 handoff package 只由 design-pages 的 pull 入口写入：两次 MCP 调用加上 `pull_design.py`，连同 pull report 一起提交。设计改动回 Claude Design 去做；下一次 pull 覆盖仓库里的副本。没有钩子拦截本地编辑，pull report 会写明 pull 前包被改过。git 是设计的版本历史，因为 Claude Design 目前没有。

证据是工作监控与变色龙：handoff package 旁边留着 port 的生成源，两次设计改动只改了本地，Claude Design 落后；两边各自在改时谁也说不清哪份是对的。ADR 0002、0004 设想的设计质量检查（A3、B1）所挂的界面 QA 技能已退役；设计时截图检查与 pull report 承担「页面有没有画对、选择器编辑器点不点得中」。

## Considered Options

- **拦截仓库里对 handoff package 的本地编辑。** 否决。正向指引已经够：下一次 pull 覆盖它，报告写明发生过本地改动。加一道钩子会把「设计不在这里改」做成禁令，而禁令比正向做法更容易被读成该做的事。
- **继续把 port 的生成源留在 handoff package 旁边，改完再上传。** 否决。那是第二条源头，也是两次只改本地、Claude Design 落后的原因。
- **用 Claude Design 的「Handoff to Claude Code」导出。** 否决。那条路让网页里的 agent 把设计改写成一份 README，这份 README 不随之后的设计更新，会变成设计页和 screen contract 之外的第三份说法。
- **两份并排，靠同步脚本对齐。** 否决。同步失败时仍然是两份源头，只是多了一个会静默过期的步骤。

## Consequences

- 设计改动的位置只有 Claude Design 项目；仓库里的 handoff package 是它的拉取结果，不是编辑面。
- 消费仓库不再把一份 `DESIGN.md` 当作设计源头；design system 在 Claude Design 里，从已经能运行的代码建立。
- ADR 0002、0004 正文不动；索引里它们的注记改指设计时截图检查与 pull report。
