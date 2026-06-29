# Investigate · 查清现状(阶段操作指南)

> investigate 阶段操作指南:当场的判断 + 调用命令。

阶段目标:把"现状查清"——内部代码现状 / 外部已有方案——产出一份带引用的现状报告,喂给后面 design(选 A/B、扎根提问)或 build(定点修)。
**红线:取证不判定。** 这阶段只摆证据,不在这里拍方案、不选路线、不下设计结论。

---

## 1. 先判:要不要 fan out

| 情况 | 怎么做 |
|---|---|
| 问题窄 / 单点(一个函数、一个已知文件) | 别起 Workflow,自己 Read/grep 查完直接 handoff |
| 问题宽 / 多专题(跨模块、要对比外部方案、根因不明) | 跑下面的自建 Workflow 并行投查 |

判据是**广度和难度**,不是"反正有工具就铺一堆 agent"。

## 2. 定 topics(你的判断,不脚本化)

进阶段先评估任务,定**哪些角度 + 几个 agent**:简单 1–2 个,复杂 4–6 个,**不堆无数个**。每个 topic 一个对象:

```
{ angle: "短角度名", skill: "<运行时该 agent 加载的角度 skill>", mode: "internal|external", question: "这一题要回答什么" }
```

角度 → skill 对照(方法论由 upstream 维护,我们只引用名字):

| mode | 查什么 | skill 选项 |
|---|---|---|
| `internal` | 现状 / 模块边界 / seam / 根因 | `codebase-design` · `improve-codebase-architecture` · `diagnosing-bugs`(skill 留空则纯 Explore 式只读查) |
| `external` | 现有方案 / 库 / 最佳实践 | `deep-research`(网搜) · `context7`(库文档,留空走通用网搜) |

## 3. 跑 Workflow(一条命令)

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/investigate.workflow.js",
  args: { topics: [ /* 上面定好的 topic 列表 */ ] }
})
```

后台跑完会通知。它每 topic 并行一个只读 agent(运行时 invoke 角度 skill)、机械过滤无出处/低信心的 claim(取证非判定)、再综合成报告。返回:

```
{ topics: [{ topic, mode, findings:[{claim, locator, confidence}], summary, gaps, dropped:[...] }],
  report: { markdown, open_questions, spinoff_candidates:[{tag, finding}] } }
```

## 4. 收口(回到主线程)

1. **亲验承重事实**:报告里的 file:line / 存在性,自己 grep/Read 坐实。**子代理是劳动力不是信源**,验不过的不写进交付物。
2. **写 `docs/context`**:把查清的领域现状落领域文档(跨任务共享),外加一份 research 笔记。
3. **旁路登记**:`report.spinoff_candidates` 里亲验为真的,逐条
   ```bash
   mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"
   ```
   不顺手在这阶段修。
4. **handoff**:
   - 查清了、够 design/build 用 → `mmw handoff --conclusion pass --produced docs/context/<...>`
   - `open_questions` 里有必须用户拍板才能继续的 → `--conclusion needs-context`

## 5. 守住的红线

- Workflow 内对抗过滤是**取证**(丢无凭据 claim),不是审查判定——审归后面 Codex 设计审 loop,不在这。
- 全程只读;fan-out 期间不写状态平面,综合 + 亲验后主线程才写盘。
- fan-out 断了就重跑(同会话);阶段级断点靠 `manifest.phases`,在 Workflow 之外。
