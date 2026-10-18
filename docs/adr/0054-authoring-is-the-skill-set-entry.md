---
date: 2026-10-18
amends: [0040, 0046]
---

# Authoring or modifying a skill 是改进技能集的唯一入口，writing-for-agents 只在被点名时运行

改进 MMW 的技能、playbook、reference 或 principle，都由 `mmw-mode` 的 `references/owning-a-task.md` `## Playbooks` 送到 `playbooks/authoring-a-skill.md`。四种来源共用六步流程：主人的话、登记的问题或复盘提案、上游新版、对技能集某部分的怀疑。`writing-for-agents` 保留规则和参考资料，由 playbook、票或调用者点名读取，不再靠描述自行触发。它的描述统一为 `Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.`。

## 依据与流程

[#1126](https://github.com/chancheuklap/multi-model-workflow/issues/1126) 的审计记录了两处缺口。自 2026-10-11 起，没有会话按描述调用 `writing-for-agents`，另一 host 的 49 个会话却读了它的 `SKILL.md`，多数是技能工作之外的 worker 和 researcher。v4 的八张已关闭技能票，只有四张记录了设计意图，两张记录了走查。资料存在，不等于执行的 agent 在需要时读到它。

[#1134](https://github.com/chancheuklap/multi-model-workflow/issues/1134) 的 Implementation Decisions 第 4 节据此定下六步：Open the ticket、Gather the evidence、Judge it against the design、Plan the fix、Write the ticket, by size、Hand it back。取证先于规划，每条 finding 都有主人能打开的证据。票的 Read first 按段落点名文件和节，让 worker 与 reviewer 读同一份标准。

Prove it, once 保留在通用落地流程之后。脚本检查由 `scripts/check` 汇总，改脚本仍跑相关套件。改动改变 agent 做任务的行为时，由新 agent 走一项真实任务，记录提交在 `fix-<n>` 并从 pull request 链接。纯措辞修改不走查。缺少必需的记录不能算通过。

## Considered Options

- 保留四个分散入口。否决。登记与复盘提案、上游新版和怀疑技能无用都需要先取证再规划，分开会遗漏同一套标准。
- 继续让 `writing-for-agents` 靠描述自行触发。否决。审计中的两种读取行为不同，描述没有把标准送到执行改动的步骤。
- 每个措辞修改也走查。否决。主人选择只在改动改变任务行为时走查，避免让不能发现行为问题的检查占用一次运行。

## Consequences

- 0040 与 0046 的入口由六步流程承接，写作规则仍由 `writing-for-agents` 持有，实施仍交给 worker。
- 描述在新会话开始时生效。此改动不移动 installed checkout，不运行安装或发布。仓库 `AGENTS.md` `## Gotchas` 的主人发布决定与自托管边界保持不变。
