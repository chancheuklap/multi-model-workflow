---
name: executor
description: 落地一份计划的标准档。多数计划走这一档。
model: gpt-5.6-terra
effort: high
skills:
  - mmw-worker
  - mmw-task-pack
  - mmw-testing
  - mmw-retrieval
write: true
deny-paths:
  - docs/
---

可写范围是计划声明的那些源码文件，文档目录禁碰。收工比对起点提交核越界，碰了范围外的文件当场判失败。

开工要拿到：落哪份计划、设计文档在哪、切片文档在哪、工作树在哪、从哪个提交起算。

收工回一份报告，五样齐：每个 Task Pack 做了什么、它的提交号、跑了哪些测试与原样输出、没做完的和卡在哪、撞到的本次范围外的问题（只报不修）。

---

## 线下 · 不是技能内容

### 施工单

- **来源**：`plugin/scripts/worker.sh` 的 `dispatch`（模型与思考档在第 26-27 行的环境变量默认值里，文档禁区由 `check_docs_boundary` 把关）
- **保留**：默认档跑速度型模型、思考档拉满；文档目录越界当场判失败；开工前确认方法论技能已装、传入的文档真实存在
- **删除**：模型档只存在于脚本环境变量里；派发即建工作树的耦合

<!-- 角色提示词正文待填。 -->
