# poteto-mode 的框架技能

**Playbook 组织任务的推进与交付，skill 提供完成某项工作的具体方法。直接委派由主对话划定任务，skill 内部委派由该 skill 规定分工。** 这两组区别决定一段提示词放在哪里，以及派出的 agent 应该按什么指引工作。[框架技能](SKILL.md) · [playbook 写作指南](playbooks/README.md)

## 区分 playbook 和 skill

| | Playbook | Skill |
| --- | --- | --- |
| 负责的决定 | 一类任务先做什么、后做什么、何时调用哪种方法、满足什么条件才继续或结束 | 给定材料和目标后，具体怎样分析、设计、实施或验证，产出什么结果 |
| 使用的上下文 | 在 mode 的共同规则下推进任务，衔接各步骤和交付要求 | 为自己的方法规定所需材料、操作步骤与结果，供用户或其他流程调用 |
| 撰写边界 | 写到下一步能接手、任务能正确结束 | 写到调用者能得到并判断这项方法的结果 |

分类时看提示词在决定什么。**决定任务怎样推进的内容放进 playbook，决定一种方法怎样执行的内容放进 skill。** 如果两类决定混在一起，就把方法抽成 skill，在 playbook 里保留何时调用、传入什么，以及拿到结果后怎样继续。

skill 可以有多步流程、调用其他 skill、派出子代理，也可以直接响应用户。playbook 可以被其他 playbook 复用。步骤多少、能否复用和是否派人，都不能单独决定分类。这是对 pstack 现有组织方式的归纳。[mode 的流程入口](../upstream/pstack/skills/poteto-mode/SKILL.md#playbooks) · [设计指南](../upstream/pstack/docs/guide/04-design.md)

## 区分两种委派

**区别在于子代理的工作指引由谁规定。**

| | 主对话直接委派 | Skill 内部委派 |
| --- | --- | --- |
| 任务怎样产生 | 主对话把当前步骤划出一项具体工作，给定范围、目标和完成条件 | 主对话执行一个 skill，该 skill 为完成其方法规定需要哪些角色、各做什么 |
| 子代理按什么工作 | `poteto-agent` 先读完整 mode，再按本次任务说明执行。框架模板中的名字是 `framework-agent` | 子代理类型、专用指令、材料和返回要求由 skill 指定，遵从该 skill 的安排 |
| 主对话怎样处理结果 | 检查指定工作是否完成，再继续 playbook | 按 skill 规定的方法核实、选择或汇总结果，取得这个 skill 的产出后继续任务 |

**选择时先看这次派人是否属于正在执行的 skill 所规定的方法。** 属于，就沿用那个 skill 的角色和派发要求。当前步骤直接需要一个实现者或助手，就由主对话划定范围，派出读取 mode 的子代理。[poteto-mode 的 Subagents](../upstream/pstack/skills/poteto-mode/SKILL.md#subagents) · [poteto-agent 原定义](../upstream/pstack/agents/poteto-agent.md) · [skill 内部派发指令](../upstream/pstack/skills/interrogate/SKILL.md#fan-out)

直接委派让受派者沿用同一套工作准则，也让主对话保留设计和验收职责。skill 内部委派把分工、角色限制和结果处理一并封装进方法，调用者可以复用整套做法。两条路径都要求派出方检查结果。模型按工作角色读取配置，读写权限按任务设置，它们与这两种委派方式分别决定。[Feature 的委派理由](../upstream/pstack/skills/poteto-mode/playbooks/feature.md) · [interrogate 的核实步骤](../upstream/pstack/skills/interrogate/SKILL.md#verify) · [模型配置](../upstream/pstack/skills/setup-pstack/SKILL.md)

新任务默认派新子代理，并给出完整要求。恢复已有子代理的条件仍按 mode 中的 Fresh subagents by default 执行。[框架的 Subagents](SKILL.md#subagents) · [框架的子代理定义](agents/framework-agent.md)

## 对照原文填写

| 模板位置 | 采用者填写的内容 |
| --- | --- |
| Non-negotiables | 哪些事件触发哪项动作，以及容易混淆时选哪一条。例如用户请求跟进 PR 状态时进入 Babysit |
| Principles | 何时读哪项原则，读后会改变什么决定 |
| Autonomy | 哪些动作默认可执行，哪些须等用户确认，本次授权能改变什么 |
| Subagents | 专门规定委派方式的 skill 名单，以及各类任务使用的模型配置 |
| Writing the reply / Comments | 读者、文风和注释约定。各流程独有的交付内容留在自己的 playbook |
| Playbooks | 能区分任务的路由条件和对应文件。pstack 遇到大型单次任务或没有合适的 playbook 时调用 `figure-it-out`，由它为这次工作设计步骤。持续的项目级工作进入 `Orchestrate` |

来源为仓库中的 pstack 0.15.36。[路由指南](../upstream/pstack/docs/guide/02-poteto-mode.md) · [figure-it-out](../upstream/pstack/skills/figure-it-out/SKILL.md) · [Orchestrate](../upstream/pstack/skills/poteto-mode/playbooks/orchestrate.md)
