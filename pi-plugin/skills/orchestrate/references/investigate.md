# Investigate · 查清现状(阶段操作指南)

> investigate 阶段:当场判断 + 跑命令。**红线:取证不判定**——只摆证据,不在这拍方案、选路线、下设计结论。

阶段目标:把现状查清(内部代码 / 外部方案),产出一份带引用的现状报告,**存档 `docs/investigating/<slug>.md`**(命名同设计 / 计划文档),喂 design / build 扎根。

## 1. 判断:查哪个方向 + 定 topics

内部与外部调查分开定义 topics，由已安装的 pi-dynamic-workflows saved workflow 并行启动隔离 agent：

| 方向 | 查什么 | 派发 | 角度 skill(可选) |
|---|---|---|---|
| 内部(仓库现状) | 模块边界 / seam / 数据流 / 根因 | `/investigate-internal` | `codebase-design` · `diagnosing-bugs` |
| 外部(成熟方案,**非必做**) | 现有库 / 实现 / 最佳实践 | `/investigate-external` | `deep-research` · `context7` |

- 只需查内部 → 只跑 internal；要对比外部方案 → 再跑 external；两个都要 → 两个 workflow 可并行。
- 窄到一个点(一个函数 / 已知文件)→ 别起 fan-out，自己用 read/grep 查完直接 handoff。
- 只有一个聚焦问题,但要跨多个文件追模块边界 / 调用链 / 数据流 → 调用一次 `Agent({subagent_type:"Explore", prompt:"<原问题 + repoRoot + 必须核验的边界>"})`；主线程亲验返回后直接收口，不为单 topic 起完整 workflow。
- 定 topics:**一个 topic 一个 agent**，按调查真实需要定几个。每个 `{ angle, question, skill? }`。

## 2. Checkpoint → 跑调查编排器

**fire 前按下面固定格式把投查计划亮给用户**(别每次自创格式)。等不等回应看值守档:`attended`(develop 讨论态)等用户批 / 改再跑——方向错了白烧 token;`afk`(bug / small-change 起步档,或用户已放权)亮出即跑,不阻塞等回应,用户看到有异议随时插话追加或掉头:

```
投查方向:<内部 / 外部 / 两者>(外部非必做)
| # | angle | question | skill |
|---|---|---|---|
| 1 | <角度名> | <这一题要回答什么> | <角度 skill 或 —> |
| 2 | ... | ... | ... |
```
`attended` 亮完跟一句:「批 / 改 / 增删 topic?」等回应再 fire;`afk` 亮完直接 fire,不问。

批了以后把 topics 压成无空格 JSON，连同目标仓库绝对路径传给 saved workflow：

```text
/investigate-internal topics=[{"angle":"<角度>","question":"<问题>","skill":"<可选>"}] repoRoot=/绝对/仓库路径
/investigate-external topics=[{"angle":"<角度>","question":"<问题>","skill":"<可选>"}]
```

这两个命令由 `@quintinshaw/pi-dynamic-workflows` 注册。workflow 为每个 topic 启动隔离 agent，强制 JSON Schema 结构化结果，过滤无 locator / low confidence 结论，再由独立 synthesizer 综合；运行状态、失败详情、暂停与恢复统一从 `/workflows` 面板查看和控制。

## 3. 收口(回主线程)

1. **亲验承重事实**:报告里的 `file:line` / `url`,自己 grep/read/查证坐实。子代理是劳动力不是信源,验不过的不写进交付物。
2. **旁路登记**:`report.spinoff_candidates` 里亲验为真的,逐条 `mmw spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`,不顺手修。
3. **存档 + handoff**:把现状报告写进 `docs/investigating/<slug>.md`(prepare 已 scaffold 该目录),钉进接力单:
 - 够 design / build 用 → `mmw handoff --conclusion pass --produced docs/investigating/<slug>.md`
 - `open_questions` 里有必须用户拍板才能继续的 → `--conclusion needs-context`
 - **bug 查根因两种诚实收口**(查不动别假装查到):**无法重现** → `needs-context`,报告附**已试的重现路径**,请用户补重现步骤 / 环境;**无法定位根因**(重现了但定不到) → `needs-context`,报告附**已排除的假设(带证据)**,请用户给方向 / 补信息。别硬编个根因往下走。

> 领域文档(`docs/context`)归 design 阶段的 `domain-modeling` 维护;investigate 只写 `docs/investigating/`,不碰 `docs/context`。

## 红线

- 调查 pi 全程只读；脚本只写状态平面的 run 账本、prompt、原始结果和综合报告。
- workflow 级断点靠 pi-dynamic-workflows journal；阶段级断点靠 `manifest.phases`。
