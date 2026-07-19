# Investigate · 查清现状(阶段操作指南)

> investigate 阶段:当场判断 + 跑命令。**红线:取证不判定**——只摆证据,不在这拍方案、选路线、下设计结论。

阶段目标:把现状查清(内部代码 / 外部方案),产出一份带引用的现状报告,**存档 `docs/design/<slug>/investigating.md`**(设计文件夹的讨论态正式成员,随设计入 git),喂 design / build 扎根。

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

**fire 前按下面固定格式把投查计划亮给用户**(别每次自创格式)。等不等回应看值守档:`attended`(develop 讨论态)等用户批 / 改再跑——方向错了白烧 token;`afk`(bug / small-change 起步档,或用户已放权)亮出即跑,不阻塞等回应,用户看到有异议随时插话追加或掉头:

```
投查方向:<内部 / 外部 / 两者>(外部非必做)
| # | angle | question | skill |
|---|---|---|---|
| 1 | <角度名> | <这一题要回答什么> | <角度 skill 或 —> |
| 2 | ... | ... | ... |
```
`attended` 亮完跟一句:「批 / 改 / 增删 topic?」等回应再 fire;`afk` 亮完直接 fire,不问。

批了用 Workflow fan-out(每个 topic 一个工人,可并行):

```
Workflow({
 scriptPath: "<插件根>/workflows/investigate-internal.workflow.js", // 插件根一行算出:PLUGIN_ROOT="${MMW%/scripts/mmw.sh}";外部则 investigate-external
 args: { repoRoot: "<任务 worktree 绝对路径>", topics: [ /* { angle, question, skill? } */ ] }
})
```

全部收回后主线程综合成一份报告。

## 3. 收口(回主线程)

1. **亲验承重事实**:报告里的 `file:line` / `url`,自己 grep/Read/查证坐实。子代理是劳动力不是信源,验不过的不写进交付物。
2. **旁路登记**:`report.spinoff_candidates` 里亲验为真的,逐条 `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,不顺手修。
3. **存档 + handoff**:把现状报告写进 `docs/design/<slug>/investigating.md`(设计文件夹;目录不存在就建),钉进接力单:
 - 够 design / build 用 → `mmw handoff --conclusion pass --produced docs/design/<slug>/investigating.md`
 - `open_questions` 里有必须用户拍板才能继续的 → `--conclusion needs-context`
 - **bug 查根因两种诚实收口**(查不动别假装查到):**无法重现** → `needs-context`,报告附**已试的重现路径**,请用户补重现步骤 / 环境;**无法定位根因**(重现了但定不到) → `needs-context`,报告附**已排除的假设(带证据)**,请用户给方向 / 补信息。别硬编个根因往下走。

> 领域文档(`docs/context`)归 design 阶段的 `domain-modeling` 维护;investigate 只写设计文件夹的 `investigating.md`,不碰 `docs/context`。

## 红线

- 全程只读;fan-out 期间不写状态平面,综合 + 亲验后主线程才写盘。
- workflow 断了同会话重跑;阶段级断点靠 `manifest.phases`。
