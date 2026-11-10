# poteto-mode 的框架技能

主对话收到用户的目标，在 mode 里选一份 playbook，把它的步骤写进待办。执行某一步时，主对话可以自己做、直接委派，或调用一个有专门做法的 skill。`⟦…⟧` 标出采用者要填写的内容，其余提示词保留在模板里。[框架技能](SKILL.md) · [编写 playbook](playbooks/README.md)

## 同一份 Feature playbook 里的两种委派

```text
主对话负责交付 Feature
│
├─ 第 4 步，已有明确的实现方式
│  主对话把目标、改动范围、验收条件和 mode 路径交给 poteto-agent
│  └─ poteto-agent 读 mode，完成指定改动 → 主对话检查改动，验证功能
│
└─ 第 7 步，设计仍有争议
   主对话调用 interrogate，把变更和设计意图交给它
   ├─ interrogate 规定每个 generalPurpose reviewer 在自己的工作区验证问题
   └─ 主对话按 interrogate 重跑命令，只采纳能复现且违背设计意图的发现
```

**直接委派时，主对话已经知道需要别人替它完成哪件事。** 在 `Feature` 第 4 步，主对话指定要改的文件、数据结构和成功条件。`poteto-agent` 先读同一份 mode，因此任务说明只需交代这一次的工作，共用的行为准则有固定出处。`Feature` 明确把这次委派的收益写成实现与复核分开。子代理写出改动，保留设计上下文的主对话检查改动并验证功能。新任务默认派新子代理，把原始要求和后续指示一起交给它。只有后续工作确实依赖难以转移的状态，例如尚未提交的改动，才恢复原子代理。[Feature](../upstream/pstack/skills/poteto-mode/playbooks/feature.md) · [poteto-agent 原定义](../upstream/pstack/agents/poteto-agent.md) · [框架中的子代理定义](agents/framework-agent.md)

**调用会派人的 skill 时，怎样分工本身就是方法的一部分。** `interrogate` 的目的是查出设计在哪些情形下会失败。它在派发指令里给 `generalPurpose` reviewer 写明设计意图、工作区和判断标准，要求交回命令、实际输出和预期输出。执行这个 skill 的主对话重跑每条命令，合并同一根因的发现，并记录其余发现被排除的理由。reviewer 的任务到可复现的发现为止。主对话因此可以拿原来的变更逐条核实，再由调用流程决定怎样处理。调用 skill 是主对话读取并执行它的指令，真正新开的 agent 是其中明确要求派出的 reviewer。[interrogate](../upstream/pstack/skills/interrogate/SKILL.md) · [设计指南](../upstream/pstack/docs/guide/04-design.md)

**决定委派方式的是谁规定工作做法。** `Multi-phase plan` 可以直接派 `poteto-agent` 只读查证，交回文件位置和测试命令。`Feature` 遇到多种可行实现时也会调用 `arena`，让候选者分别写代码，再比较和综合。读写权限、子代理类型和模型是不同选择。例如 `interrogate` 指定类型为 `generalPurpose`，模型则取自 `interrogate reviewers` 配置。两条路径最终都由主对话检查结果。[Multi-phase plan](../upstream/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md) · [arena](../upstream/pstack/skills/arena/SKILL.md) · [模型配置](../upstream/pstack/skills/setup-pstack/SKILL.md)

## 填写 mode 时怎样区分 playbook 和 skill

看谁需要知道一项决定。`Feature` 需要知道**何时**检查有争议的设计，以及检查完能否交付，这两件事写进 playbook。`interrogate` 的每个调用者都需要可信的发现。怎样派 reviewer、什么证据能使一条发现成立，写在 skill 里。以后改变复核方法，只需改 `interrogate`。若改变的是 `Feature` 在什么条件下进入复核，就改这个流程的触发条件，并核对 mode 中相应的共用规则。[playbook 写作指南与可填写样例](playbooks/README.md) · [pstack 的 mode 原文](../upstream/pstack/skills/poteto-mode/SKILL.md)

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
