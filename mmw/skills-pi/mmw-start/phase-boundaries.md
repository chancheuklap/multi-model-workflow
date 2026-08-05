# 阶段边界

阶段是同一会话内的一段完整工作，例如 Grilling、spec 综合、实现或 QA。只有完成当前阶段、准备进入下一阶段时，才判断上下文如何处理。阶段中继续当前步骤；剩余工作可以按既有角色合同派 subagent 时，才把有边界的部分派出。

离开当前会话会把原始对话从 primary source 变成摘要或报告等 secondary source。信息会减少。每次按以下顺序判断，第一项成立就执行，不跳步。

## 1. Continue

先问当前会话能否继续。下一阶段需要本阶段的原始推理，或者当前会话仍能可靠容纳下一阶段时，继续当前会话。Continue 不损失信息，也不增加任务、文件或切换成本。

Grilling 到 spec、spec 到 ticket 拆分通常需要前一阶段的原始推理，应优先 Continue。MMW 的人工审批关卡仍按各技能执行；Continue 不能跳过确认。

## 2. 清空无关上下文

只有当前会话的探索、决定和死路对下一阶段全部无关时，才选择清空上下文。误清空相关上下文会丢失“为什么”，读取 diff 或文档不能恢复原始讨论。

## 3. Handoff

只有需要 portability 时使用 `/handoff`：

- 切换到另一个 harness。
- 切换到另一个目录或仓库。
- 交给另一位协作者。
- 阶段中途分出一条旁支，又不能打断当前工作。

同一任务、同一目录、同一主 agent 继续下一阶段时，不为“整理一下”制作 handoff。

## 4. AFK

下一阶段已有清楚边界，不需要用户中途决定，而且 MMW 已有合适角色和 task 合同时，可以派 subagent 或后台 Worktree 任务。角色、worktree、结果验证和报告验证仍按调用技能执行。

需要用户走查、共同理解、spec 定稿或 ticket 清单批准的阶段不是 AFK。不能为了节省当前上下文，让 subagent 代替用户完成 HITL 或人工审批关卡。

## 5. Compact

前四项都不成立、上下文仍相关、用户仍需留在循环中，而且宿主支持 compact 时，才压缩上下文。给 compact 的说明要写清下一阶段和必须保留的 primary source。

Compact 是最后选择。摘要可能压平决定、取舍和被否决方向，不能因为内容很多就提前使用。

## 宿主能力

Pi 没有由本 plugin 保证可调用的 clear 或 compact 动作。Continue 时留在当前会话；需要 portability 时调用 `/handoff`；AFK 工作按调用技能的原生 subagent 合同派发。不得声称已经清空或压缩上下文。

宿主动作没有实际执行时，不得声称已经 clear、compact、handoff 或派发。所选动作既无法由 agent 执行，也无法由用户触发时，回到 Continue 判断；Continue 仍安全就继续，否则报告宿主能力 blocker。
