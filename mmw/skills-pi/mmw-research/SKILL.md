---
name: mmw-research
description: research 的共享入口。主 agent 在用户明确要求系统调查、`wayfinder:research` ticket、问题需要多个独立角度或多份一手来源，或者必须真实运行外部系统才能知道它在我们的负载和数据下的实际表现时使用；收到 research task 的 `investigator` 也使用本技能进入内部或外部取证方法。一个函数、一个已知文件、一个事实、文件计数、一条命令或一次直接查询能回答时，主 agent 自己处理。
---

本技能根据当前 agent 在这次 research 中的身份加载不同方法。只读取当前身份对应的 reference。

`investigator` 只完成 task 分配的一个角度，不再派发其他 agent。task 同时指定两个方向时，停止取证，请主 agent 把它们拆成两个独立角度。

## 按身份加载

| 当前身份 | 加载 |
| --- | --- |
| 你是接收用户请求或其他技能调用，并负责派发 `investigator`、综合和保存的主 agent | 完整读取 [MAIN.md](MAIN.md)；不读取 `INTERNAL.md` 或 `EXTERNAL.md`。`MAIN.md` 第 1 节会告诉你要不要转去 [EVIDENCE.md](EVIDENCE.md) |
| 你是 `investigator`，task 指定内部方向 | 完整读取 [INTERNAL.md](INTERNAL.md)，完成 task 后直接交回报告 |
| 你是 `investigator`，task 指定外部方向 | 完整读取 [EXTERNAL.md](EXTERNAL.md)，完成 task 后直接交回报告 |
| 你是 `investigator`，但 task 没有指定唯一方向 | 向主 agent 报告缺少唯一的取证方向，停止取证 |
| 当前上下文无法判断你承担哪一种身份 | 说明缺少主 agent 或 `investigator` 身份信息，不猜测执行路径 |
