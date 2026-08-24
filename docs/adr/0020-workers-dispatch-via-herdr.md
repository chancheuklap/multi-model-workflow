---
date: 2026-08-24
amends: []
---

# 落地工人经 Herdr 面板派发，短判定任务走无头 CLI

落地流水线要把工人派到不同宿主的不同模型上（角色到模型的映射见消费仓库的 `docs/agents/models.md`）。派发面有三个候选：宿主内 subagent、无头 CLI 一次性调用、Herdr 管理的终端面板。宿主内 subagent 无法跨宿主，首先出局。

选 Herdr 作为工人的派发面：编排者跑在 Herdr 会话里，每票用 `herdr worktree create` 建工作副本，开一个 pane 用 `agent start` 启动对应宿主的 agent，用 `agent prompt --wait` 递简报。理由有三。第一，`agent start --kind` 原生支持全部五个宿主的 CLI（实测 kinds 清单含 pi、claude、codex、cursor、grok）。第二，Herdr 内建 agent 生命周期识别（idle / working / blocked / done / unknown），其中 `blocked` 表示它识别出了审批或提问界面——这让编排者能发现「工人在问问题」，把问题停车成 issue 后继续，这正是参考项目 swarm-forge 里最脆弱的一环（用正则刮终端画面猜状态）的成品化解法。第三，agent 在 pane 里常驻且有名字，自动修一轮可以回到原工人（上下文还在），符合「需要继承上下文时复用已开好的 agent、不随意开新 agent」的约定。

完成判定不读终端画面，只读硬状态：仓库里验收关卡的执行结果、票的关闭状态、分支上的 commit。终端画面只在 `blocked` 时读，用于把问题停车。

复验、分诊这类一问一答的短判定任务走无头 CLI 一次性调用（五个 CLI 均有无头模式，实测参数详见落地 spec）：结构化 JSON 输出便于机器消费，独立进程天然保证复验者没看过实现过程。成败判定解析 JSON 输出，不信退出码——五个宿主 CLI 的 help 全文都没有退出码承诺（herdr 自身反而有约定：服务错误 exit 1、语法错误 exit 2）。

## Considered Options

- **全部走无头 CLI 一次性调用。** 否决。工人的活是长任务：无头模式下工人卡在提问界面只能挂死或超时，人无法旁观或干预，卡住的问题也无从停车。参考项目 ponytail 的 benchmark 用无头模式是因为它的单元是几分钟的封闭题，与过夜落地不同型。
- **全部走 Herdr 面板。** 否决。复验者的价值在「没看过实现过程」，常驻 pane 反而引入上下文残留的风险；短任务用面板还要付出读屏解析的成本，无头 JSON 更干净。
- **宿主内 subagent。** 否决。跨不了宿主，而角色到模型的映射要求初级工人、高级工人、复验者各在不同宿主的模型上。

## Consequences

- 启动无人值守前必须先进 Herdr 会话（编排技能在 `HERDR_ENV` 不为 1 时应报错退出，不降级硬跑）。
- 编排技能依赖 `herdr` CLI 的 agent / pane / worktree 子命令面；Herdr 尚在 0.x，升级改命令语法的风险高于成熟版本，会直接破坏流程，技能正文应遵守其技能文件的指引「以本机 `herdr --help` 为准」。
- 不在 Herdr 环境时的降级路径是无头 CLI 串行跑，能力缩水（无 blocked 识别、无旁观），仅作应急。

来源：2026-08-24 与用户的设计对话；本机对 herdr 0.8.2（`herdr --help`、`herdr agent`、`herdr worktree`）与五个宿主 CLI 无头参数的实测；swarm-forge 与 ponytail 本地克隆的对照阅读。
