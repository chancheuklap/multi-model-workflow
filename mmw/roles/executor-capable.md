---
name: executor-capable
description: 落地一份计划的强档。计划自己在复杂度那一行标了要强档时用，模型更强、思考档更省。
model: gpt-5.6-sol
effort: medium
skills:
  - mmw-worker
sandbox: workspace-write
deny-paths:
  - docs/
---

方法论、可写范围、开工要拿到的东西与 `executor` 完全相同，差别只有模型与思考档。

**选档不由派活的人临时拍**：读计划文档复杂度那一行。涉及计费、权限、数据迁移这类改错了代价高的活会标强档。

## 施工单

- **来源**：`plugin/scripts/worker.sh` 第 29-30 行的强档环境变量，以及第 344-347 行按计划复杂度自动切档的判断
- **保留**：选档由计划文档决定、不靠派活的人手传；两档共用同一份落地方法论
- **删除**：模型档只存在于脚本环境变量里

<!-- 角色提示词正文待填。 -->
