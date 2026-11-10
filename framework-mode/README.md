# poteto-mode 的骨架

[框架技能](SKILL.md) 保留 pstack 的行为指令和七节原有顺序。`⟦…⟧` 标出采用者要填写的内容，包括哪些请求进哪条流程、哪些行动须经用户确认、每种工作用什么模型。配套的[子代理定义](agents/framework-agent.md)保留委派的另一端。两份文件都是源模板。

## 一条真实路由：修复已测出的性能退化

```text
用户要求修复已测出的性能退化
└─ 主对话选中 Perf issue playbook，将原步骤逐项写入待办
   ├─ 步骤 1　采集基线 → 调 benchmark-checklist 检验测量
   ├─ 步骤 3　根据 trace 制定方案 → 委派实现
   │          ├─ 主对话按 perf-issue 角色选模型，传入 mode 路径
   │          ├─ 子代理读 mode → 完成实现 → 交回改动
   │          └─ 主对话检查改动，采集修复后的 trace
   └─ 最终报告给出基线、修复后数值、差值和证据路径
```

**怎么区分 playbook 和 skill？** 上图的 Perf issue 持有整项任务，从第一次测量一直管到交付。benchmark-checklist 只回答“这次测量能不能信”，在 Perf issue 和 Hillclimb 中都用得上。主对话可以自己读这个 skill。只有流程明确委派实现时，才发生图里的子代理调用。[Perf issue 原文](../upstream/pstack/skills/poteto-mode/playbooks/perf-issue.md) · [benchmark-checklist 原文](../upstream/pstack/skills/benchmark-checklist/SKILL.md)

**怎么区分两种委派？** playbook 把某一步直接交给 poteto-agent，父对话传入 mode 的绝对路径，子代理先读它。若步骤调用的 skill 自己组织子代理，则由该 skill 指定类型。例如 swarm 直接指定 generalPurpose，并分别给每个 worker 划定工作范围。类型决定子代理从哪份指引开始工作，角色配置决定这次用哪个模型。[poteto-agent 定义](../upstream/pstack/agents/poteto-agent.md) · [swarm 的派发指令](../upstream/pstack/skills/swarm/SKILL.md#phase-b-fan-out) · [模型配置](../upstream/pstack/skills/setup-pstack/SKILL.md)

## 对照原文填写

| 框架中的位置 | 填什么 | pstack 的原例 |
| --- | --- | --- |
| Non-negotiables | 当前情境触发的动作，以及两个入口都匹配时选谁 | 用户问 PR 状态就进入 Babysit，由它的第一步决定如何跟进。单纯创建 PR 不触发 |
| Principles | 哪个判断需要哪项原则，完整准则放进对应的 skill | 要报告加速比时，读 Explain the Number，找出限制性能的因素 |
| Autonomy | 默认可执行的事、必须暂停的事、本次授权能改变什么 | 可逆操作可直接进行，部署须暂停。用户点名的确认环节仍然有效 |
| Subagents | 直接委派类型、专用 skill 的例外、角色与模型的对应关系 | Perf issue 的实现读 perf-issue 角色配置。父对话检查改动、自己报告 |
| Writing the reply / Comments | 所有流程共用的回复与注释规则 | 回复中的结论就地给证据。性能数字等专有交付项写在对应 playbook |
| Playbooks | 各类任务的匹配条件、流程文件以及优先路由 | 普通任务匹配既有流程。大型单次任务或无匹配时由 figure-it-out 设计流程。持续的项目级工作进 Orchestrate |

基线为仓库快照 pstack 0.15.36。[mode 原文](../upstream/pstack/skills/poteto-mode/SKILL.md) · [路由指南](../upstream/pstack/docs/guide/02-poteto-mode.md) · [原则指南](../upstream/pstack/docs/guide/08-principles.md) · [定制指南](../upstream/pstack/docs/guide/09-make-it-yours.md)
