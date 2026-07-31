---
name: plan-writer
description: 把一个切片写成实施计划的角色。派进任务工作树，探完代码再拆活，交付前自检必过。
runs-on: codex
model: gpt-5.6-sol
effort: high
sandbox: workspace-write
skill: mmw-plan-writer
writes: 只有自己那份计划与它对应的那个切片
---

登记的是派发参数，不是方法论。方法论在技能 `mmw-plan-writer`，派发前先确认那份技能已装进第二模型的技能根。

派发时另外交代：写哪个切片、设计文档在哪、切片文档在哪、工作树在哪。收工回结构化报告，主线程亲验。

## 施工单

- **来源**：`plugin/scripts/worker.sh` 的 `plan-dispatch`（模型与思考档在第 32-33 行的环境变量默认值里，可写边界由 `check_plan_boundary` 把关）
- **保留**：模型与思考档比落地档高一级；可写范围只有自己那份计划与对应切片，越界视为失败；派发前预检技能已装、传入的文档真实存在
- **删除**：环境变量当登记处——参数搬到这份文件，脚本读它

<!-- 派发时钉的围栏正文待填。 -->
