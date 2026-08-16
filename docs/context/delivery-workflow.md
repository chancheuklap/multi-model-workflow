# 交付工作流

这个 Context 定义 MMW 从讨论到实现使用的产物和参与方式。

## Language

**prototype**：
在真实代码落地前，用持续迭代的可运行资产回答只靠讨论无法判定的问题。初版可以粗糙；后续轮次原地修改同一份 prototype，直到走查回答当前问题。Throwaway 说的是写法：没有测试、错误处理最少。文件留在仓库里。
_Avoid_: MVP、静态设计稿、用完即丢的一次性文件、把外壳提升成正式实现

**prototype 资产**：
走查过的可运行 prototype、变体、README 中的问题与走查结论、用户选中的产物，以及作为长期证据保留的文件。路径由 `mmw artifact path prototype` 给出。下游点名 `README.md`，并读它列出的文件。
_Avoid_: 过程截图、DOM、console、录屏、scratch、把未完成工作接入生产路由、没有可运行文件的结论

**prototype 索引**：
该目录里的 `README.md`。它记录问题、怎么运行、走查结论、选中的产物、否决的约束和长期证据。它不是可运行的 prototype。
_Avoid_: 资产索引、capture.md、五项交接

**解释 HTML**：
把用户点名内容重新说明为普通 HTML 可视化的文档。
_Avoid_: prototype、Logic HTML

**research**：
`/mmw-research` 保存在一个 research 目录下的 findings。每个 Explore agent 写一份 findings 文件。`wayfinder:research` ticket 保存时不问用户；其余情况由用户决定。保存不代表下游必须引用。
_Avoid_: investigation、artifact、调查资产、调查结果、主 agent 综合

**research 索引**：
该目录里的 `README.md`。由主 agent 写。它记录问题，并列出目录中的文件。下游点名这份文件，并读它列出的文件。它不是 findings。
_Avoid_: 资产索引、调查索引、research 报告、章节指引

**research 目录**：
保存之后才创建的目录。它包含 research 索引，以及 Explore 写出的 findings 文件。
_Avoid_: investigation 目录、artifact 目录、调查目录

**research 路径**：
research 目录的精确仓库相对路径。它按[路径形状](./artifact-location.md)确定，类别内细分是 research 主题。
_Avoid_: worktree 路径、任务分支名推导路径

**点名**：
上游在自己的产物中写下一条产物引用，指定下游必须读的那件产物。下游只读被点名的产物，以及该产物的索引显式列出的文件。
_Avoid_: 引用、传路径、递归读取

**evidence**：
直接支撑结论、而且不能低成本重建的最小原始证据。外部系统实测的 evidence 经脱敏后保存在对应 research 目录的 `raw/`；界面 evidence 保存在 scratch 中，用户要求长期保留时由用户指定位置。
_Avoid_: 全部运行输出、未脱敏原始数据、可低成本重建的过程材料

**scratch**：
prototype、research、外部系统实测和 `/mmw-grilling` 产生的临时过程材料。过程截图、DOM、console、录屏、临时探测输出、生成中间物和 shared-understanding record 的位置按[路径形状](./artifact-location.md)确定，类别根是 scratch 根。scratch 不进入 Git，并在任务结束时清理。
_Avoid_: prototype 资产、evidence、长期合同出处

**走查**：
用户使用 prototype 并给出接受、拒绝或修改意见。
_Avoid_: 审查、自动验收

**shared understanding**：
`/mmw-grilling` 对已经谈定的问题、约束、决定、取舍和范围作出的总结。用户确认总结准确后，shared understanding 才成立。
_Avoid_: spec、讨论记录、单方面假设、共同理解

**shared-understanding record**：
`/mmw-grilling` 为一次访谈写下的文件，位置按[路径形状](./artifact-location.md)确定，类别根是 scratch 根，文件名是 `understanding.md`。它含 Round Q&A 原样、Shared understanding 和 Supporting materials 三段。
_Avoid_: shared understanding、讨论记录、审查记录、共同理解记录

**spec**：
把已经谈定的内容综合成的设计合同。spec 文件的位置按[路径形状](./artifact-location.md)确定，类别根是 `docs/specs/`，文件名是 `spec.md`。
_Avoid_: plan、Wiki 页面、讨论草稿

**spec issue**：
一份已批准并发布的 spec 在 Tracker 中的父项，也是其 tracer bullet ticket 的父项。
_Avoid_: spec、tracer bullet ticket、agent brief

**spec 索引**：
全部 spec 元数据的清单，由一条 CLI 命令扫描各份 spec 的元数据块当场算出。agent 读命令输出。`docs/specs/README.md` 是同一次运行写下的副本，供不运行命令的读者阅读，不是权威。plan 没有对应的索引。
_Avoid_: research 索引、tracker 索引、spec、重建索引

**tracer bullet ticket**：
从 spec 拆出的端到端垂直切片，声明 blocking edge，并交给一名 `worker` 实现。
_Avoid_: decision ticket、任务包、横向层任务

**plan**：
一张 tracer bullet ticket 的实施计划。现在 spec 里已经有事实的票一起写；只能等上游代码的票，等 `/mmw-implement` 关票后再写。
_Avoid_: spec、tracer bullet ticket、路线图

**批次**：
某一时刻还没有 `ready-for-agent` 标签、而且现在就写得出 plan 的那些 open tracer bullet ticket。现在写不写得出，看写它的 plan 要知道的合同形状、字段名和精确值，在 spec 的 `## Contract Boundaries`、`## Implementation Decisions` 或 ticket 验收里找不找得到。只有等上游代码做出来才知道的，先不写。阻塞关系不参与判定，它决定谁先实现。
_Avoid_: frontier、全部 ticket、plan 清单、`## Cross-Plan Contract Anchors`

**人工审批关卡**：
必须取得用户明确确认才能继续的关卡。`/mmw-grilling` 的关卡确认 shared understanding；`/mmw-to-spec` 的关卡确认 spec 定稿；`/mmw-to-tickets` 的关卡确认 ticket 粒度、blocking edge、合并和拆分。三者不能互相替代。
_Avoid_: 人闸、人工门禁

**HITL**：
human in the loop。少了人在对话中的回答，工作就没有答案。
_Avoid_: `ready-for-human`、人工审批关卡

**AFK**：
away from keyboard。agent 可以独立完成，用户回来只需要看结果。
_Avoid_: `ready-for-agent`、人工审批关卡

**路径形状**：
(authoritative: [路径形状](./artifact-location.md))

**产物引用**：
(authoritative: [产物引用](./artifact-location.md))
