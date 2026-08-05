# Knowledge and Domain

这个上下文定义 MMW 如何取得可信事实，以及项目特有术语如何获得唯一所有权。

## Language

**内部调查**：
对当前仓库实现、调用关系、数据流、seam 或影响面的只读调查。每条结论以当前源码的 `文件:行号` 为出处。
_Avoid_: 代码审查、实现建议

**外部调查**：
对仓库之外的库、接口或规范进行的一手来源调查。每条结论以拥有该事实的官方来源或可复现命令输出为出处。
_Avoid_: 二手文章、原型实验

**结构候选**：
符号检索或图查询返回、尚未由当前源码验证的可能关系。候选不能直接进入 spec、plan 或用户结论。
_Avoid_: 代码事实、已验证关系

**检索图**：
由源码内容构建的结构关系图。它可能缺失、过期或新鲜；Markdown 和空提交不改变其新鲜度。
_Avoid_: Context Map、Wayfinder map

**领域模型**：
项目特有概念、术语所有权和 bounded context 关系的长期语言模型。
_Avoid_: 数据模型、实现架构

**bounded context**：
一组内部词义一致、并对这些词拥有明确责任的领域语言边界。
_Avoid_: seam、代码目录

**Context Map**：
多 bounded context 仓库的领域索引，登记每个 context 的 leaf、所有权和跨 context 关系。
_Avoid_: Wayfinder map、架构图

**leaf**：
一个 bounded context 的权威 glossary，只定义项目特有术语。leaf 不记录流程步骤、实现细节或临时决定。
_Avoid_: spec、参考文档、分支 context

**权威引用**：
非拥有 leaf 指向术语拥有 leaf 的固定引用。共享术语只在一个 leaf 中定义。
_Avoid_: 重复定义、同义转述

**ADR**：
记录难以回退、会让未来读者意外、并来自真实取舍的长期架构决定。ADR 不承担 glossary 或实施计划职责。
_Avoid_: 决策草稿、变更日志
