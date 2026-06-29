# Investigate · 查清现状(阶段操作指南)

> investigate 阶段:当场判断 + 跑命令。**红线:取证不判定**——只摆证据,不在这拍方案、选路线、下设计结论。

阶段目标:把现状查清(内部代码 / 外部方案),产出一份带引用的现状报告,喂 design / build 扎根。

## 1. 判断:查哪个方向 + 定 topics

两个方向各自一个 workflow,**分开跑**:

| 方向 | 查什么 | 跑哪个 workflow | 角度 skill(可选) |
|---|---|---|---|
| 内部(仓库现状) | 模块边界 / seam / 数据流 / 根因 | `investigate-internal` | `codebase-design` · `improve-codebase-architecture` · `diagnosing-bugs` |
| 外部(成熟方案,**非必做**) | 现有库 / 实现 / 最佳实践 | `investigate-external` | `deep-research` · `context7` |

- 只需查内部 → 只跑 internal;要对比外部方案 → 再跑 external;两个都要 → 先后各跑一次。
- 窄到一个点(一个函数 / 已知文件)→ 别起 workflow,自己 Read/grep 查完直接 handoff。
- 定 topics:**一个 topic 一个 agent**,按调查真实需要定几个(别凑没意义的 topic,也不设上限)。每个 `{ angle, question, skill? }`。

## 2. Checkpoint → 跑 workflow

**fire 前先把 topics 亮给用户**(方向 + 各 topic 的 angle/question,一句话或小表),等用户批 / 改再跑——别闷头烧 token。批了跑对应 workflow(scriptPath 固定,只填 topics):

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/investigate-internal.workflow.js",   // 外部则 investigate-external
  args: { topics: [ /* { angle, question, skill? } ... */ ] }
})
```

后台跑完通知。它每 topic 并行一个只读 agent、机械过滤无出处 / 低信心 claim、综合成带引用报告(`{ topics, report:{ markdown, open_questions, spinoff_candidates } }`)。

## 3. 收口(回主线程)

1. **亲验承重事实**:报告里的 `file:line` / `url`,自己 grep/Read/查证坐实。子代理是劳动力不是信源,验不过的不写进交付物。
2. **写 `docs/context`**:领域现状落领域文档 + 一份 research 笔记。
3. **旁路登记**:`report.spinoff_candidates` 里亲验为真的,逐条 `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,不顺手修。
4. **handoff**:
   - 够 design / build 用 → `mmw handoff --conclusion pass --produced docs/context/<...>`
   - `open_questions` 里有必须用户拍板才能继续的 → `--conclusion needs-context`

## 红线

- 两个方向分开跑、各自 workflow、不混;外部调查非必做。
- 全程只读;fan-out 期间不写状态平面,综合 + 亲验后主线程才写盘。
- workflow 断了同会话重跑;阶段级断点靠 `manifest.phases`。
