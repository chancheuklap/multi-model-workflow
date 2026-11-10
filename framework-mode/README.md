# 从 poteto-mode 抽出的骨架

使用入口是 [SKILL.md](SKILL.md)。可以在对话里明确要求 agent 读取它，或用支持该技能格式的宿主加载本目录。正文是给执行者的指令。本页供填写框架的人阅读。

    用户目标与授权 → 主对话选 playbook → 在当前步骤调用方法或委派
                          ↑                        │
                          └──── 检查返回的证据 ────┘
                         达到该流程终点 → 交回用户

## 内容应该放在哪里

| 如果这段内容决定…… | 放在哪里 | 本包中的落点 |
| --- | --- | --- |
| 哪种请求走哪条路、由谁接回结果 | mode 入口 | 「选路」中的一行，写用户要的产物，指向唯一流程 |
| 一类任务从哪里开始、下一步怎样选、在哪里结束 | playbook | 调查与制定计划。同一问题按所要求的交付物分流 |
| 当前一步要怎样取得一项可验收的专业结果，别处也能独立调用 | 专业 skill | 由步骤按需调用所在环境中的 skill。仅被一处使用且几句话说得清的动作留在该步骤 |
| 多条流程在同一条件下都要改变一个判断 | 原则及其触发条件 | mode 写“何时读”，核对证据的正文只写一处 |
| 某次委派做什么、交回什么 | 本次任务说明 | 父对话在委派发生时填写。通用工作准则由 mode 提供，专业子代理遵从其调用 skill 的约定 |
| 某种工作用什么模型、允许什么工具 | 宿主配置及具体授权 | 由派出方采用。框架不内置模型名 |
| 可查阅的格式、定义或确定性操作 | reference 或命令 | 需要它的步骤引用。能返回结果的命令直接运行 |

**填写的例子。** 若要加入“修复故障”，路由索引只需写入“交付已验证的修复”及其 playbook 位置。复现、定位、修复、在同一场景复验的顺序属于该 playbook。若“分析一次采样”也会被调查或性能优化独立调用，它才值得有自己的 skill。仅增加一个路由关键词，不会把调查所得的修复建议变成实施授权。

## 与上游的对应关系

上游基线为 pstack 0.15.36。以下链接固定到所读快照。

- [poteto-mode](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/SKILL.md) 把目标、触发条件、原则索引、授权、委派及 playbook 路由接在同一入口。这里保留这些关系，移出作者个人文风、代码约定、模型名和特定产品的交付动作。
- [poteto-agent](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/agents/poteto-agent.md) 要求直接受派者读取同一份 mode，主对话主持流程。这个包以任务说明传入技能位置，未注册宿主专属 agent 类型。
- [Investigation](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/playbooks/investigation.md) 和 [Multi-phase plan](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md) 展示不同的交付终点。包内两份流程是缩写后的独立样例。
- [figure-it-out](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/figure-it-out/SKILL.md) 与 [Orchestrate](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/playbooks/orchestrate.md) 区分临时设计的一次流程与持续运作的项目。这里保留按规模选择及可接手的要求；长期调度、唤醒、托管状态属于采用框架的环境。
