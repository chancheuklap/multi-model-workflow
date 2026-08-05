# 交付工作流

这个上下文定义 MMW 把一项需求变成可验证交付结果时使用的正式产物和流程控制概念。

## Language

**MMW 任务**：
围绕一个用户目标建立的交付单元。一个 MMW 任务拥有自己的任务 worktree 和任务分支。
_Avoid_: 会话、聊天、主线程

**slug**：
MMW 任务在分支名和产物路径中使用的稳定短名。
_Avoid_: issue 编号、任务标题

**任务 worktree**：
承载一项 MMW 任务全部正式改动的隔离工作目录。
_Avoid_: 结果 worktree、主仓库目录

**prototype**：
为回答一个尚不能只靠讨论决定的问题而制作的粗糙可运行产物。prototype 提供设计证据，不是生产实现。
_Avoid_: MVP、正式实现、静态设计稿

**走查**：
用户根据 prototype 的真实运行结果接受、拒绝或要求修改当前方案的活动。
_Avoid_: 自动验收、审查

**spec**：
记录目标行为、实现决定、合同边界和测试决定的定稿设计合同。
_Avoid_: 需求草稿、plan、Wiki 页面

**tracer bullet ticket**：
由一名 `worker` 独立实现并提交验证证据的一条端到端交付切片。主 agent 负责验收和结果验证。
_Avoid_: decision ticket、任务包、横向层任务

**plan**：
一张 tracer bullet ticket 的可执行实施合同。一张 tracer bullet ticket 恰好对应一份 plan。
_Avoid_: spec、tracer bullet ticket 正文、路线图

**任务包**：
plan 内可以独立实现、独立验证并值得单独审查的最小交付单元。
_Avoid_: tracer bullet ticket、阶段、代码层

**人工审批关卡**：
主 agent 必须取得用户对指定产物或动作的明确批准，才能执行下一次流程转换的关卡。各技能可以定义不同实例，但不得改名或改变这项批准责任。
_Avoid_: 人闸、人工门禁、用户决策点、人工参与点

**HITL**：
必须有人在对话中参与才能完成的工作属性。HITL 描述参与方式，不自动表示存在人工审批关卡。
_Avoid_: `ready-for-human`、人工审批关卡

**AFK**：
agent 可以在用户不在场时独立完成的工作属性。AFK 不包含对外发布或其他受控动作的授权。
_Avoid_: 全自动发布、免审批

**浏览器验收**：
主 agent 在真实界面中验证黄金路径和相关边界状态的交付证据。
_Avoid_: 人工审批关卡、自动回归测试
