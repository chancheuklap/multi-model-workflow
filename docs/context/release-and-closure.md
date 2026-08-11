# 出包与收尾

这个 Context 定义 `/mmw-release` 与 `/mmw-closing` 使用的语言。

## Language

**产品**：
可以独立出成安装包的交付对象。
_Avoid_: 仓库、宿主、stage

**出包配置**：
一个产品的 `.release-adapter.json` 配置。
_Avoid_: 构建脚本、交付记录

**`mmw release`**：
持有出包状态机、失败分级、路径护栏和熔断的确定执行层。
_Avoid_: 发布 agent、第二个执行器

**stage**：
`mmw release` 状态机中的一个构建阶段。
_Avoid_: plan 阶段、Tracker 状态

**出包状态**：
一次出包过程在各 stage 与 attempt 之间持续存在的状态。
_Avoid_: stage、状态角色、出包阶段产物

**出包阶段产物**：
一个 stage 在一次 attempt 中产生的产物。
_Avoid_: 出包状态、交付记录

**交付记录**：
记录产品和出包时 commit 的持久文件。
_Avoid_: `mmw release receipt`、subagent 报告

**用户实测**：
用户安装实际安装包并确认能安装、能使用。
_Avoid_: 构建成功、浏览器验收

**对外发布**：
发送到外部系统的动作。
_Avoid_: 本地提交、Tracker 日常操作
