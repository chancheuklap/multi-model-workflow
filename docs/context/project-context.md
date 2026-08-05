# 项目上下文

这个上下文定义 MMW 如何保存项目特有语言，并把结构检索结果转换为可验证的代码事实。

## Language

**领域模型**：
项目特有概念、术语所有权和 bounded context 关系的长期语言模型。
_Avoid_: 数据模型、实现架构

**Context Map**：
多 bounded context 仓库的领域索引，登记每个 context 的 leaf、所有权和跨 context 关系。
_Avoid_: Wayfinding 的 map、架构图

**leaf**：
一个 bounded context 的权威 glossary，只定义项目特有术语。
_Avoid_: spec、流程文档、参考手册

**权威引用**：
非拥有 leaf 指向术语拥有 leaf 的固定引用。共享术语只在一个 leaf 中定义。
_Avoid_: 重复定义、同义转述

**检索图**：
由当前源码构建、供结构查询使用的关系图。
_Avoid_: Context Map、Wayfinding 的 map

**结构候选**：
检索图或符号查询返回、尚未由当前源码验证的可能关系。
_Avoid_: 代码事实、已验证关系

**图新鲜度**：
检索图相对当前源码提交的同步状态，正式取值为 `FRESH`、`STALE` 或 `MISSING`。
_Avoid_: 查询成功、Markdown 改动时间
