# 交付工作流

这个 Context 定义 MMW 从讨论到实现使用的产物和参与方式。

## Language

**prototype**：
回答一个只靠讨论定不下来的设计问题的粗糙可运行产物。
_Avoid_: MVP、正式实现、静态设计稿

**prototype 资产**：
用户走查过的可运行 prototype、完整界面变体、README 中的问题、逐轮用户走查结论和用户选中的路径。确实作为设计合同出处的证据也属于 prototype 资产。Prototype 资产保存在 `mmw path prototype` 返回的路径，供 spec、ticket、plan、审查和实现持续引用。
_Avoid_: 过程截图、DOM、console、录屏、临时探测输出、生成中间物、生产实现、只留结论

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
用户批准随 research 保存的 HTML、字段表、脚本或其它文件。research 索引必须说明每个文件的用途。
_Avoid_: research 资产、调查资产、配套资产

**research 目录**：
用户选择保存后才创建的目录。它只包含 research 索引、research 报告和用户批准的 research 配套文件。
_Avoid_: investigation 目录、artifact 目录、调查目录

**research 路径**：
research 目录的精确仓库相对路径。普通任务使用 `docs/research/<产物目录>/<research 主题>/`；Wayfinder 使用 `docs/research/<产物目录>/issue-<编号>/<research 主题>/`。
_Avoid_: worktree 路径、任务 slug 推导路径

**evidence**：
外部系统实测形成的测试计划、结论台账，以及不能低成本重建且直接支撑结论的最小原始证据。需要保留的原始证据必须脱敏。Evidence 保存在 `mmw path evidence` 返回的路径。
_Avoid_: 全部运行输出、未脱敏原始数据、可低成本重建的过程材料

**scratch**：
prototype、research 和外部系统实测产生的临时过程材料。过程截图、DOM、console、录屏、临时探测输出和生成中间物默认保存在 `mmw path scratch` 返回的路径，不进入 Git；任务结束时清理。
_Avoid_: prototype 资产、evidence、长期合同出处

**走查**：
用户使用 prototype 并给出接受、拒绝或修改意见。
_Avoid_: 审查、自动验收

**共同理解**：
`/mmw-grilling` 对已经谈定的问题、约束、决定、取舍和范围作出的总结。用户确认总结准确后，共同理解才成立。
_Avoid_: spec、讨论记录、单方面假设

**spec**：
把已经谈定的内容综合成的设计合同。
_Avoid_: plan、Wiki 页面、讨论草稿

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
