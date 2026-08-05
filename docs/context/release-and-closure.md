# 发布与收尾

这个上下文定义通过 final 终审的交付结果如何形成安装包、交付记录和长期 Wiki 页面。

## Language

**产品**：
由一份 release adapter 登记、可以独立构建和交付的安装对象。一次任务可能影响多个产品。
_Avoid_: package、仓库、宿主

**release adapter**：
仓库为一个产品登记 `build_target`、`asset_roots` 与 release stage 的配置合同。
_Avoid_: 构建脚本、release engine

**release engine**：
`mmw release` 提供的确定执行层，拥有状态机、失败分级、路径护栏和熔断。主 agent 只解释状态并处理 release engine 无法判断的暂停。
_Avoid_: 发布 agent、第二套执行器

**release stage**：
release engine 状态机中的一个可运行构建阶段。release stage 结果写入 release receipt。
_Avoid_: plan 阶段、任务状态

**release receipt**：
记录一次出包已经执行的动作、日志与 ReleaseFinding 产物引用、暂停原因和当前状态的权威账本。
_Avoid_: subagent 报告、安装包清单

**ReleaseFinding**：
release engine 对一个产品检查结果使用的结构化对象，正式字段包括 `status`、`tier`、`root_cause_fingerprint`、`locator` 和 `remediation`。ReleaseFinding 由 release engine 分类，不使用审查 finding 的五种处置标记。
_Avoid_: finding、审查 finding、已采信缺陷

**交付记录**：
记录 `product`、`source_commit` 和 `closed_at` 的持久文件。一次多产品交付要求所有记录指向同一个最终提交；安装包路径只从 release engine 状态输出读取。
_Avoid_: release receipt、终审报告

**安装包实测**：
用户在真实安装环境中确认安装包可以安装并完成目标行为的验收活动。用户明确批准安装包及其对应 commit，是安装包实测人工审批关卡的通过凭据。
_Avoid_: 自动构建成功、浏览器验收

**人工审批关卡**：
(authoritative: [人工审批关卡](./delivery-workflow.md))

**对外发布**：
把分支、代码、安装包、部署结果或正式文档发送到仓库之外的动作。对外发布必须经过人工审批关卡。
_Avoid_: 本地提交、tracker 日常操作、实测写入

**任务收尾**：
final 终审和必要出包完成后，把 spec 与 plan 归档到 Wiki、验证远端一致并清理任务分支文档的阶段。
_Avoid_: release、分支集成

**Wiki spec 页面**：
一份已落地 spec 及其 plan 的长期唯一事实来源。Wayfinding 的 map、审查记录和终审报告不进入该页面。
_Avoid_: 本地 spec 副本、审查归档
