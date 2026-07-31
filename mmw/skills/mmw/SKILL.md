---
name: mmw
description: 报当前任务现状：在哪一格、盘上产物说到哪、上次为什么停。新会话接续先用它。
---

合读三个来源报一遍现状：状态文件、阶段产物、提交流水。只读盘，不读会话记忆，不改任何状态。

## 施工单

- **来源**：`plugin/commands/progress.md`、`plugin/commands/reassess.md`、`plugin/scripts/progress.sh`、`flow.sh` 的 where
- **保留**：读盘不读记忆；报「在哪一格 / 产物说到哪 / 上次为什么停」三样
- **删除**：进度板渲染器与它的投影层；where 的 load/do/then 指令面——不再由引擎指路

<!-- 方法论正文待填。填之前先读「来源」里的旧文件全文，按保留与删除两列取舍。 -->
