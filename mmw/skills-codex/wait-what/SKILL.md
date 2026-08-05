---
name: wait-what
description: 停一下，上一条没有说明白；补齐必要上下文并用更简单的语言重述。
disable-model-invocation: true
---

重新说明上一条消息。先补齐读者缺少的必要上下文，再使用 ASD-STE100 简化技术英语（Simplified Technical English）的原则写短句。

在仓库任务中，先遵守目标仓库 `AGENTS.md` 的领域上下文规则，通过 `mmw domain path` 读取相关 leaf，并使用 canonical 术语。没有领域文档时使用行业标准术语。

只重述当前结论、原因和下一步。不要扩展新方向，也不要假定读者已经理解先前使用的缩写或代码标识符。
