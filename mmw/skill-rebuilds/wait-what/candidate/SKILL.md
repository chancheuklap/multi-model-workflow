---
name: wait-what
description: 停一下，刚才的内容没有说明白；补齐必要上下文，并用更简单的文字或可视化重新说明。
disable-model-invocation: true
---

用户手动调用本技能。重新说明用户没有看懂的内容；用户没有另行指出时，就是上一条消息。

<!-- upstream: vendor/mattpocock-skills/skills/productivity/wait-what/SKILL.md:7 -->

等一下——我不明白你现在讲到哪一步了。换一种方式重新说明：补一点上下文，使用 ASD-STE100 简化技术英语（Simplified Technical English），并采用领域上下文中的通用语言。

在仓库任务中，先遵守目标仓库 `AGENTS.md` 的领域上下文规则。使用领域上下文中的 canonical 术语；没有领域文档时使用行业标准术语。

只重新说明用户点名的内容，不引入新方向。根据读者缺少的上下文解释必要的缩写和代码标识符。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 用户需要用更简单的文字重新说明 | **自己继续**：补齐理解当前内容所需的上下文，再用短句重新说明 |
| 用户需要把方案、文档或回复做成普通 HTML 可视化解释 | **自己继续**：完整读取 [VISUAL.md](VISUAL.md) |
| 用户需要用按钮驱动业务逻辑、状态转移或数据形状 | **自己继续**：完整读取 [LOGIC.md](LOGIC.md) |
