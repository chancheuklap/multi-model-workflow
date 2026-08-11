# 交付工作流

这个 Context 定义 MMW 从讨论到实现使用的产物和参与方式。

## Language

**prototype**：
在真实代码落地前，用持续迭代的可运行资产回答只靠讨论无法判定的问题。初版可以粗糙；后续轮次原地修改，直到它接近可以真实落地的状态。符合项目技术与质量要求的可移植内容可以被正式实现直接复用。
_Avoid_: MVP、静态设计稿、用完即丢的临时代码、把 prototype 外壳直接当成正式实现

**prototype 资产**：
用户走查过的可运行 prototype、完整界面变体、README 中的问题、逐轮用户走查结论、用户选中的产物和被提升为长期证据的文件。它的位置按[路径形状](./artifact-location.md)确定。spec、ticket、plan、审查和实现按精确路径持续引用。达到项目技术与质量要求的组件、纯逻辑、接口合同和后端脚本可以直接复用；调试外壳、切换器和落选变体继续作为 prototype 资产保存。
_Avoid_: 过程截图、DOM、console、录屏、临时探测输出、生成中间物、把未达到项目质量要求的内容接入生产路由、只留结论

**research**：
`/mmw-research` 中由主 agent 验证并综合的事实。每次 research 完成后，用户决定是否保存。用户选择不保存时，不创建 research 目录或文件。保存不代表下游必须引用。
_Avoid_: investigation、artifact、调查资产、调查结果

**research 索引**：
已保存 research 的 `README.md`。它记录问题、范围快照、结论摘要、文件索引、下游用途和未查清项。
_Avoid_: 资产索引、调查索引

**research 报告**：
已保存 research 的 `report.md`。它只包含主 agent 验证后的完整结论和逐条出处。
_Avoid_: investigation report、调查报告、subagent 原始报告

**research 配套文件**：
用户批准随 research 保存的 HTML、字段表、脚本或其他文件。research 索引必须说明每个文件的用途。
_Avoid_: research 资产、调查资产、配套资产

**research 目录**：
用户选择保存后才创建的目录。它只包含 research 索引、research 报告和用户批准的 research 配套文件。
_Avoid_: investigation 目录、artifact 目录、调查目录

**research 路径**：
research 目录的精确仓库相对路径。它按[路径形状](./artifact-location.md)确定，类别内细分是 research 主题。
_Avoid_: worktree 路径、任务 slug 推导路径

**evidence**：
直接支撑结论、而且不能低成本重建的最小原始证据。外部系统实测的 evidence 经脱敏后保存在对应 research 目录的 `raw/`；界面 evidence 保存在 scratch 中，用户要求长期保留时由用户指定位置。
_Avoid_: 全部运行输出、未脱敏原始数据、可低成本重建的过程材料

**scratch**：
prototype、research、外部系统实测和 `/mmw-grilling` 产生的临时过程材料。过程截图、DOM、console、录屏、临时探测输出、生成中间物和共同理解记录的位置按[路径形状](./artifact-location.md)确定，类别根是 scratch 根。scratch 不进入 Git，并在任务结束时清理。
_Avoid_: prototype 资产、evidence、长期合同出处

**走查**：
用户使用 prototype 并给出接受、拒绝或修改意见。
_Avoid_: 审查、自动验收

**共同理解**：
`/mmw-grilling` 对已经谈定的问题、约束、决定、取舍和范围作出的总结。用户确认总结准确后，共同理解才成立。
_Avoid_: spec、讨论记录、单方面假设

**共同理解记录**：
`/mmw-grilling` 为一次访谈写下的文件，位置按[路径形状](./artifact-location.md)确定，类别根是 scratch 根，文件名是 `understanding.md`。它含逐轮问答原样、共同理解和支持材料三段。
_Avoid_: 共同理解、讨论记录、审查记录

**spec**：
把已经谈定的内容综合成的设计合同。spec 文件的位置按[路径形状](./artifact-location.md)确定，类别根是 `docs/specs/`，文件名是 `spec.md`。
_Avoid_: plan、Wiki 页面、讨论草稿

**spec 索引**：
仓库中一份自动生成的文件，收录全部 spec 的元数据，位于 `docs/specs/README.md`。它由一条 CLI 命令全量重建。
_Avoid_: research 索引、tracker 索引、spec

**tracer bullet ticket**：
从 spec 拆出的端到端垂直切片，声明 blocking edge，并交给一名 `worker` 实现。
_Avoid_: decision ticket、任务包、横向层任务

**plan**：
一张 tracer bullet ticket 的实施计划。
_Avoid_: spec、tracer bullet ticket、路线图

**任务包**：
plan 内能携带自身测试周期、值得一名新审查者单独检查的最小单位。
_Avoid_: tracer bullet ticket、阶段、代码层

**人工审批关卡**：
必须取得用户明确确认才能继续的关卡。`/mmw-grilling` 的关卡确认共同理解；`/mmw-to-spec` 的关卡确认 spec 定稿；`/mmw-to-tickets` 的关卡确认 ticket 粒度、blocking edge、合并和拆分。三者不能互相替代。
_Avoid_: 人闸、人工门禁

**HITL**：
human in the loop。少了人在对话中的回答，工作就没有答案。
_Avoid_: `ready-for-human`、人工审批关卡

**AFK**：
away from keyboard。agent 可以独立完成，用户回来只需要看结果。
_Avoid_: `ready-for-agent`、人工审批关卡

**路径形状**：
(authoritative: [路径形状](./artifact-location.md))
