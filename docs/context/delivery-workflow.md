# 交付工作流

这个 Context 定义 MMW 从讨论到实现使用的产物和参与方式。

## Language

**prototype**：
回答一个只靠讨论定不下来的设计问题的粗糙可运行产物。
_Avoid_: MVP、正式实现、静态设计稿

**走查**：
用户使用 prototype 并给出接受、拒绝或修改意见。
_Avoid_: 审查、自动验收

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
必须取得用户明确确认才能继续的关卡。不同技能可以要求用户确认不同产物或动作，这个词的含义不变。
_Avoid_: 人闸、人工门禁

**HITL**：
human in the loop。少了人在对话中的回答，工作就没有答案。
_Avoid_: `ready-for-human`、人工审批关卡

**AFK**：
away from keyboard。agent 可以独立完成，用户回来只需要看结果。
_Avoid_: `ready-for-agent`、人工审批关卡
