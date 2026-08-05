# 领域上下文与检索

这个 Context 定义 MMW 如何保存项目语言并验证结构关系。

## Language

**领域模型**：
项目特有概念、术语所有权和 bounded context 关系的长期语言模型。
_Avoid_: 数据模型、实现架构

**Context Map**：
多 bounded context 仓库的索引，登记 Context、leaf、所有权和关系。
_Avoid_: Wayfinding 的 map、架构图

**leaf**：
一个 bounded context 的 glossary，只定义该 Context 特有的术语。
_Avoid_: spec、流程文档、参考手册

**ADR**：
记录难以回退、会让未来读者意外且经过真实取舍的决定。
_Avoid_: plan、变更日志、普通说明

**权威引用**：
非拥有 leaf 指向术语拥有 leaf 的引用。
_Avoid_: 重复定义、同义转述

**canonical 术语**：
拥有术语的 leaf 规定的用词。
_Avoid_: `_Avoid_` 中列出的说法、自造同义词

**结构图谱**：
由 `mmw graph build` 构建的本机派生物。
_Avoid_: Context Map、Wayfinding 的 map

**结构候选**：
Serena 或 Graphify 返回、尚未回到当前源码验证的关系。
_Avoid_: 代码事实、已验证关系

**`mmw graph status`**：
报告结构图谱是 `FRESH`、`STALE` 还是 `MISSING` 的命令。
_Avoid_: 查询成功、文件修改时间
