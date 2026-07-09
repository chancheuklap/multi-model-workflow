---
description: 展示当前 multi-model-workflow 任务进度板(投影,从磁盘真相源重建)
argument-hint: ""
---

## 现状(动态注入)

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/mmw.sh" progress render --stdout 2>&1`

## 指令

上面是刚从 task.json / loop-state.json 重渲染的进度板。

1. 若上面是 `NO-ACTIVE-RUN`:明确告诉用户当前不在在管任务 worktree、无板可展示,停止,不伪造进度。
2. 有板:把板面内容原样转述给用户(路线/阶段/值守模式/进度度量/计划进度/阻塞/计划外项)。
3. 只汇报板面 + 一个「若需你拍板」的问题(仅当板里有待决项);不自动续跑、不加板外推断。
