---
name: executor-capable
description: 落地一份计划的强档。计划自己标了高风险时用，模型更强、思考档更省。
runs-on: codex
model: gpt-5.6-sol
effort: medium
sandbox: workspace-write
skill: mmw-worker
writes: 计划声明的改动范围内的源码；文档目录禁碰
---

方法论与标准档同一份技能 `mmw-worker`，两档的差别只在这份登记的模型与思考档。

选档不由派活的人临时拍：计划文档自己在复杂度那一行标了要强档，脚本据此切。涉及计费、权限、数据迁移这类改错了代价高的活会这么标。

## 施工单

- **来源**：`plugin/scripts/worker.sh` 第 29-30 行的强档环境变量，以及第 344-347 行按计划复杂度自动切档的判断
- **保留**：选档由计划文档决定、不靠派活的人手传；两档共用同一份落地方法论
- **删除**：环境变量当登记处

<!-- 派发时钉的围栏正文待填。 -->
