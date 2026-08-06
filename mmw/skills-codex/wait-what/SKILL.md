---
name: wait-what
description: 停一下，刚才的内容没有说明白；用更简单的文字或可视化重新说明。
disable-model-invocation: true
---

重新说明用户没有看懂的内容；用户没有另行指出时，就是上一条消息。先补齐读者缺少的必要上下文，再使用 ASD-STE100 简化技术英语（Simplified Technical English）的原则写短句。

在仓库任务中，先遵守目标仓库 `AGENTS.md` 的领域上下文规则，通过 `mmw domain path` 读取相关 leaf，并使用 canonical 术语。没有领域文档时使用行业标准术语。

只重新说明这份内容，不引入新方向。根据读者缺少的上下文解释必要的缩写和代码标识符。

用户要求可视化解释时，完整读取并执行 [VISUAL.md](VISUAL.md)。
