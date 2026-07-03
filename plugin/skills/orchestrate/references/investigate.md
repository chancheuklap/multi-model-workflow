# Investigate · 查清现状(阶段操作指南)

> investigate 阶段:当场判断 + 跑命令。**红线:取证不判定**——只摆证据,不在这拍方案、选路线、下设计结论。

阶段目标:把现状查清(内部代码 / 外部方案),产出一份带引用的现状报告,**存档 `docs/investigating/<slug>.md`**(命名同设计 / 计划文档),喂 design / build 扎根。

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

**fire 前必停,按下面固定格式把投查计划亮给用户**(别每次自创格式),等用户批 / 改再跑——别闷头烧 token:

```
投查方向:<内部 / 外部 / 两者>(外部非必做)
| # | angle | question | skill |
|---|---|---|---|
| 1 | <角度名> | <这一题要回答什么> | <角度 skill 或 —> |
| 2 | ... | ... | ... |
```
亮完跟一句:「批 / 改 / 增删 topic?批了跑 `investigate-<internal|external>`」。等用户回应再 fire,不擅自跑。

批了跑对应 workflow(scriptPath 固定,只填 topics):

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/investigate-internal.workflow.js",   // 外部则 investigate-external
  args: { repoRoot: "<任务 worktree 绝对路径>",   // internal 必传,钉死取证目标(external 无此参数)
          topics: [ /* { angle, question, skill? } ... */ ] }
})
```

后台跑完通知。它每 topic 并行一个只读 agent、机械过滤无出处 / 低信心 claim、综合成带引用报告(`{ topics, report:{ markdown, open_questions, spinoff_candidates } }`)。

## 3. 收口(回主线程)

1. **亲验承重事实**:报告里的 `file:line` / `url`,自己 grep/Read/查证坐实。子代理是劳动力不是信源,验不过的不写进交付物。
2. **旁路登记**:`report.spinoff_candidates` 里亲验为真的,逐条 `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,不顺手修。
3. **存档 + handoff**:把现状报告写进 `docs/investigating/<slug>.md`(prepare 已 scaffold 该目录),钉进接力单:
   - 够 design / build 用 → `mmw handoff --conclusion pass --produced docs/investigating/<slug>.md`
   - `open_questions` 里有必须用户拍板才能继续的 → `--conclusion needs-context`
   - **bug 查根因两种诚实收口**(查不动别假装查到):**无法重现** → `needs-context`,报告附**已试的重现路径**,请用户补重现步骤 / 环境;**无法定位根因**(重现了但定不到) → `needs-context`,报告附**已排除的假设(带证据)**,请用户给方向 / 补信息。别硬编个根因往下走。

> **investigate 不维护 `docs/context`**:领域文档(术语 / 对象关系 / 角色 / 状态,跨任务持久)由 **design 阶段的 `domain-modeling`** 在产出设计文档之后维护,investigate 别多管。现状报告存 `docs/investigating/`(本任务存档),不是领域文档,别往 `docs/context` 塞。

## 红线

- 两个方向分开跑、各自 workflow、不混;外部调查非必做。
- 全程只读;fan-out 期间不写状态平面,综合 + 亲验后主线程才写盘。
- workflow 断了同会话重跑;阶段级断点靠 `manifest.phases`。
