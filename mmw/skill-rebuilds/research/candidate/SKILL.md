---
name: mmw-research
description: research 的共享入口。主 agent 在用户明确要求系统调查、`wayfinder:research` ticket，或者问题需要多个独立角度或多份一手来源时使用；收到 research task 的 `investigator` 也使用本技能进入内部或外部取证方法。一个函数、一个已知文件、一个事实、文件计数、一条命令或一次直接查询能回答时，主 agent 自己处理。
---

本技能根据当前 agent 在这次 research 中的身份加载不同方法。只读取当前身份对应的 reference。

## 下一步

| 当前身份 | 下一步 |
| --- | --- |
| 你是接收用户请求或其他技能调用，并负责派发 `investigator`、验证、综合和保存的主 agent | **自己继续**：完整读取 [MAIN.md](MAIN.md)；不读取 `INVESTIGATOR.md`、`INTERNAL.md` 或 `EXTERNAL.md` |
| 你是主 agent 派出的 `investigator`，task 要求你完成一个 research 角度 | **自己继续**：完整读取 [INVESTIGATOR.md](INVESTIGATOR.md)；task 会指定内部或外部方向 |
| 当前上下文无法判断你承担哪一种身份 | **停**：说明缺少主 agent 或 `investigator` 身份信息，不猜测执行路径 |
