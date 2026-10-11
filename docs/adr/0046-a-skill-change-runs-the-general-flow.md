---
date: 2026-10-09
amends: [0040, 0043]
---

# 一次技能改动和别的项目一样走通用流程：先读技能集的标准，按大小走 Make a small change 或 Write a spec，最后证明一次

Authoring or modifying a skill 只有三步。第一步读技能集的标准：改动服务的设计意图，`SKILL-SET-COMPONENTS.md` 定每段放哪，`writing-for-agents` 的 `SKILL.md` 和 `SKILL-SET-RULES.md` 定怎么写，改了拷来的文件就在 `mmw-v3/imports.tsv` 记一条 J，编号取全表最大号加一。第二步按 Make a small change 第一步判断大小，文字和脚本一样对待：小的走 Make a small change，提交在 `dev` 或工作所在的分支上；大的走 Write a spec，spec 只点名这些标准，由 Cut tickets 抄进每张票的 Read first，能由命令判定的检查成为票的验收标准。第三步证明一次：从仓库根目录跑脚本检查，再由一个新 agent 在改后的文字上走一个真实任务。小改动在第二步之后证明；大改动在主人接受这一夜、`finish` 跑完、安装的副本移过去之后证明，夜里票已跑过的命令不再跑，只跑 `grep`。发布仍是主人的决定。

## 要修的是什么

0040 让一个会话做不完的改动经 Land it 交给 Write a spec：先把段落写好抄进草稿，再把文件恢复到上次提交，spec 逐字引用这些段落，最后一张票写 `imports.tsv`。同一段文字写了两遍，文件为了让夜里重写而恢复。检查、走查、提交又各占一步。2026-10-09 的走查发现，提交到哪个分支、命令在哪个目录跑、读 `writing-for-agents` 的哪几节、J 号怎么取都要 agent 自己猜（#970 至 #973）。

## Considered Options

- **保留 Land it，只补那几处含糊。** 否决。段落先写一遍再由票照抄一遍，两份迟早不一致，而且一次技能改动仍走一条别的产品不走的路。

## Consequences

- 0040 正文里的 Land it、Validate it、Deliver，0043 正文里的 Place it，现在分别是 Run the general flow by size、Prove it, once、Read the skill set's standards。
- Review the skill set 的 Fix every finding 跑这本 playbook 时，Prove it, once 只跑检查：审查的走查就是这些修改的走查。审查可以只针对点名的意图或文件，范围外的任务不走。
