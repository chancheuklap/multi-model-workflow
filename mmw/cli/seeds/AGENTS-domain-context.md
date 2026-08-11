<!-- MMW-DOMAIN-CONTEXT-START -->
## 领域上下文

开始 research、讨论、设计、写文档、写代码或审查前，先读领域文档。看仓库根有什么，形态就定了：

- 根上有 `CONTEXT-MAP.md`：它是索引。先读它，再读它列出的、本次涉及的全部 leaf（leaf 在 `docs/context/` 下）。
- 根上只有 `CONTEXT.md`：直接读它。
- 两个都没有：直接继续，不报告缺失，也不创建领域文档。

先运行 `mmw artifact index adr` 取得 ADR 索引，再读其中与本次范围相关的那几份。

任何面向用户或写入仓库的内容，都使用 leaf 定义的 canonical 术语。代码标识符和测试名也适用。不得使用 `_Avoid_` 中列出的说法。

用户说法、leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得自行选择一个覆盖其他内容。

形成长期术语、关系或歧义结论时，使用 `/mmw-domain-modeling` 更新拥有该概念的 leaf。其他 leaf 只保留权威路径引用。

同一 agent 在任务范围不变时只需读取一次。任务进入新的 bounded context 后重新选路并读取。
<!-- MMW-DOMAIN-CONTEXT-END -->
