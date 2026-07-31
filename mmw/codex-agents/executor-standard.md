---
name: executor-standard
description: 落地一份计划的标准档。派进自己的工作树，逐个 Task Pack 测试先行，每个 Pack 一次提交。
runs-on: codex
model: gpt-5.6-terra
effort: high
sandbox: workspace-write
skill: mmw-worker
writes: 计划声明的改动范围内的源码；文档目录禁碰
---

登记的是派发参数，不是方法论。方法论在技能 `mmw-worker`，派发前先确认那份技能已装进第二模型的技能根。

多数计划走这一档。计划自己标了高风险时改派强档，见 `executor-capable`。

派发时另外交代：落哪份计划、设计文档在哪、切片文档在哪、工作树在哪、从哪个提交起算。收工回结构化报告，主线程用跑测试与读 diff 验收，不吃自述。

## 施工单

- **来源**：`plugin/scripts/worker.sh` 的 `dispatch`（模型与思考档在第 26-27 行的环境变量默认值里，文档禁区由 `check_docs_boundary` 把关）
- **保留**：默认档跑速度型模型、思考档拉满；文档目录越界当场判失败；派发前预检技能已装、传入的文档真实存在；额外放行主仓库的 git 公共目录，否则工作树里跑不了 git
- **删除**：环境变量当登记处；派发即建工作树的耦合

<!-- 派发时钉的围栏正文待填。 -->
