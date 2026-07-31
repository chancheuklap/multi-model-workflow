---
name: plan-writer
description: 把一个切片写成实施计划。
model: gpt-5.6-sol
effort: high
skills:
  - mmw-plan-writer
  - mmw-task-pack
  - mmw-testing
  - mmw-retrieval
write: true
allow-paths:
  - docs/plans/
  - docs/issues/
---

你写的是自己那份计划与它对应的那个切片，别的文档不动。源码只读不改。

开工要拿到：写哪个切片、设计文档在哪、切片文档在哪、工作树在哪、计划写进哪个文件。

收工回一份报告，四样齐：计划落在哪个文件、拆成几个 Task Pack、交付前自检逐条的结果、拿不准而留给主线程定的地方。

---

## 线下 · 不是技能内容

**模型为什么比落地档高一级**：拆活拆错了后面全跟着错。

### 施工单

- **来源**：`plugin/scripts/worker.sh` 的 `plan-dispatch`（模型与思考档在第 32-33 行的环境变量默认值里，可写边界由 `check_plan_boundary` 把关）
- **保留**：模型与思考档比落地档高一级；可写范围只有自己那份计划与对应切片，越界视为失败；开工前确认方法论技能已装、传入的文档真实存在
- **删除**：模型档只存在于脚本环境变量里；引擎回执与步账

<!-- 角色提示词正文待填。 -->
