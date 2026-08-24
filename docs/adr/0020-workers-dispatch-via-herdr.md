---
date: 2026-08-24
amends: []
---

# 跨宿主工人经 Herdr 面板派发，编排会话内的角色走 subagent

落地流水线要把角色派到不同宿主的不同模型上（角色到模型的映射见消费仓库的 `docs/agents/models.md`）。载体按「每个功能找最合适的载体」分配，而不是一刀切。

按最终的角色模型表，编排者、规划者、复验者、升级顾问全部落在 Claude Code 上，而编排者本身就是一个 Claude Code 会话——**会话内的角色用宿主原生的 subagent 承载**：规划者是一次性 subagent，结果直接返回编排者；复验者每票新起一个 subagent（独立性的实质是「非作者的新上下文」，新起即满足），同票第二轮复验用消息续用同一个 subagent（它记得第一轮 findings，只需核对修复是否命中——符合「需要继承上下文时复用已开好的 agent」的约定）；复验者卡住时以「被 X 挡住」的报告结束并返回，这本身就是停车信号；升级顾问就是现有的 advisor subagent，零改动。

**唯一做不成 subagent 的角色是两级工人**——初级在 Cursor CLI、高级在 Grok Build，必须跨宿主。工人经 Herdr 派发：编排者跑在 Herdr 会话里，每票用 `herdr worktree create` 建工作副本，开一个 pane 用 `agent start` 启动对应宿主的 agent，用 `agent prompt --wait` 递简报。选 Herdr 的理由有三。第一，`agent start --kind` 原生支持全部五个宿主的 CLI（实测 kinds 清单含 pi、claude、codex、cursor、grok）。第二，Herdr 内建 agent 生命周期识别（idle / working / blocked / done / unknown），其中 `blocked` 表示它识别出了审批或提问界面——这让编排者能发现「工人在问问题」，把问题停车成 issue 后继续，这正是参考项目 swarm-forge 里最脆弱的一环（用正则刮终端画面猜状态）的成品化解法。第三，agent 在 pane 里常驻且有名字，自动修一轮可以回到原工人（上下文还在）。

完成判定不读终端画面，只读硬状态：仓库里验收关卡的执行结果、票的关闭状态、分支上的 commit。终端画面只在 `blocked` 时读，用于把问题停车。工人若需经无头 CLI 一次性调用（应急降级），成败判定解析 JSON 输出，不信退出码——五个宿主 CLI 的 help 全文都没有退出码承诺（herdr 自身反而有约定：服务错误 exit 1、语法错误 exit 2）。

## Considered Options

- **全部走无头 CLI 一次性调用。** 否决。工人的活是长任务：无头模式下工人卡在提问界面只能挂死或超时，人无法旁观或干预，卡住的问题也无从停车。参考项目 ponytail 的 benchmark 用无头模式是因为它的单元是几分钟的封闭题，与过夜落地不同型。
- **复验者也走无头 CLI（本 ADR 首版的选择）。** 否决并修正。当初的理由里只有「非作者的新上下文」承重，而 subagent 新起同样满足；「JSON 好解析」不承重（判决反正写进票的评论）；「复验是短任务」判断有误（重跑全套关卡、UI 票还要起应用跑界面检查，是长任务）。无头进程跑完即灭，同票第二轮无从复用。
- **全部走 Herdr 面板（含 CC 内角色）。** 否决。规划者与复验者在编排者同一宿主内，subagent 结果直达、零 pane 管理成本；为它们开 pane 是纯开销。
- **宿主内 subagent 承载工人。** 否决。跨不了宿主，而初级、高级工人分别在 Cursor 与 Grok Build 的模型上。

## Consequences

- 启动无人值守前必须先进 Herdr 会话（编排技能在 `HERDR_ENV` 不为 1 时应报错退出，不降级硬跑）。
- 编排技能依赖 `herdr` CLI 的 agent / pane / worktree 子命令面；Herdr 尚在 0.x，升级改命令语法的风险高于成熟版本，会直接破坏流程，技能正文应遵守其技能文件的指引「以本机 `herdr --help` 为准」。
- 编排技能同时依赖所在宿主的 subagent 派发与续用能力；技能正文按能力描述（「宿主支持后台子任务与消息续用时……」），不点宿主名。
- 不在 Herdr 环境时的降级路径是工人走无头 CLI 串行跑，能力缩水（无 blocked 识别、无旁观），仅作应急。

来源：2026-08-24 与用户的设计对话（载体分配于次日经用户质询修正：复验者从无头 CLI 改为 subagent）；本机对 herdr 0.8.2（`herdr --help`、`herdr agent`、`herdr worktree`）与五个宿主 CLI 无头参数的实测；swarm-forge 与 ponytail 本地克隆的对照阅读。
