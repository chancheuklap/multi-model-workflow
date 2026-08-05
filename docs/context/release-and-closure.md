# Release and Closure

这个上下文把通过 final 终审的代码产出为一致安装包，并把已落地设计转入 Wiki。

## Language

**产品**：
由一份 release adapter 登记、可以独立构建和交付的安装对象。一次任务可能影响多个产品。
_Avoid_: package、仓库、宿主

**release adapter**：
仓库为一个产品登记构建目标、资产范围与出包阶段的配置合同。
_Avoid_: 构建脚本、release engine

**release engine**：
`mmw release` 提供的确定执行层，拥有状态机、失败分级、路径护栏和熔断。主 agent 只解释状态并处理引擎无法判断的暂停。
_Avoid_: 发布 agent、第二套执行器

**release stage**：
release engine 状态机中的一个可运行构建阶段。阶段结果写入 release receipt。
_Avoid_: plan 阶段、任务状态

**release receipt**：
记录一次出包已经执行的动作、日志、finding 和当前状态的权威账本。
_Avoid_: subagent 报告、安装包清单

**交付记录**：
记录某个产品安装包路径和 `source_commit` 的持久文件。一次多产品交付要求所有记录指向同一个最终提交。
_Avoid_: release receipt、终审报告

**安装包实测**：
用户在真实安装环境中确认包可以安装并完成目标行为的人工验收。它是发布验收，不是 spec 的人工审批关卡。
_Avoid_: 人工审批关卡、自动构建成功

**任务收尾**：
final 终审和必要出包完成后，把 spec 与 plan 归档到 Wiki、验证远端一致并清理任务分支文档的阶段。
_Avoid_: release、分支集成

**Wiki spec 页面**：
一份已落地 spec 及其 plan 的长期唯一事实来源。Wayfinder map、审查记录和终审报告不进入该页面。
_Avoid_: 本地 spec 副本、审查归档
