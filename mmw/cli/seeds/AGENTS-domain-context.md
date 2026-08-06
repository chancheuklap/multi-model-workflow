<!-- MMW-DOMAIN-CONTEXT-START -->
## 领域上下文

开始 research、讨论、设计、写文档、写代码或审查前，运行 `mmw domain path`：

- 返回 `map`：先读 Map，再读本次涉及的全部 leaf。
- 返回 `single`：读命令返回的领域文档。
- 返回 `none`：直接继续，不报告缺失，也不创建领域文档。

运行 `mmw domain dirs`，读取 `adr` 路径下与本次范围相关的 ADR。

任何面向用户或写入仓库的内容，都使用 leaf 定义的 canonical 术语。代码标识符和测试名也适用。不得使用 `_Avoid_` 中列出的说法。

用户说法、leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得自行选择一个覆盖其他内容。

形成长期术语、关系或歧义结论时，使用 `/mmw-domain-modeling` 更新拥有该概念的 leaf。其他 leaf 只保留权威路径引用。

同一 agent 在任务范围不变时只需读取一次。任务进入新的 bounded context 后重新选路并读取。
<!-- MMW-DOMAIN-CONTEXT-END -->
