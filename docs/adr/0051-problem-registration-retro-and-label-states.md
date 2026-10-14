---
date: 2026-10-14
amends: [0035, 0039]
---

# 问题先登记并复盘，主人挑中和批准计划分两次，标签分种类与状态

MMW 用 `register-problem` 保存当场解决不了的问题和每次出现，用 Retrospective（`mmw-v4/skills/mmw-mode/playbooks/retrospective.md`）与 `retro` 技能归并、核实并提出方案。每个 MMW issue 恰好带一个种类标签，状态另记。主人先挑中问题，接手会话写计划和验收标准；主人再说 Go，原 issue 才变成 `mmw:ticket` 并交给 worker。复盘只读事件、issue 和 git，不读对话记录，也不写外部记忆。决定来自 spec #1033 `## Implementation Decisions` §1、§3、§14、§17。

## 种类说明问题是什么，状态说明下一步谁来推

- `mmw:lesson` 是判断、环境、流程上的做法问题，出生时待处理，由复盘处理。
- `mmw:problem` 是票外的产品问题，或 playbook 开的、计划未批的 issue。会话碰到的产品问题出生时等主人决定；playbook 开的计划出生时待处理。
- `mmw:child` 是 worker 在一张票里发现的范围外问题。`finding`、`contract`、`fault` 出生时只贴种类标签，机器还欠它一步；`decision`、`deferred` 出生时另贴 `needs-triage`，等主人决定。
- 待处理不贴状态标签。等主人决定贴 `needs-triage`，只有主人能让它离开。待做贴 `ready-for-agent` 加等级，或 `ready-for-human`。关闭用 GitHub 的关闭原因，主人否决的另贴 `wontfix`。地图与 spec 不走这套状态机。
- `needs-info` 只从标签表里删。已有仓库上的标签和带它的 issue 保留，迁移只打印编号供主人决定。

## 挑中不是批准施工

主人挑中一条登记后，接手会话按 `## Problem` 的 `Playbook:` 行写计划，保留原种类。`mmw-mode/references/ticket.md` `## Handing it back` 把写好的计划交回主人。Go 才原地改种类并派 worker；子 issue 经 `dispatch.sh route` 转换，连同父节点和路由记录一起处理。

能用脚本查出的重复错误交给 `correct`。它读登记及 `lesson.seen`，按层级写计划，不自己提交。验证在过去错误的提交上运行新检查，须因那次错误失败；在修好后的头上运行，须通过。两次输出都交给主人。`reflect` 退役到 `mmw-v4/docs/retired-skills/reflect/`，判断、环境、流程三个视角由复盘承担。

## Considered Options

- **主人只决定一次，挑中就派 worker。** 否决。spec #1033 §3 采纳 advisor 2026-10-14 的两次决定方案。挑中时只有问题和方案，计划与验收标准尚未写成；直接派 worker 会跳过主人对实际施工范围的批准。
- **复盘只读自己角色的登记。** 否决。判断、环境、流程三个视角需核对整次运行的登记与信号，否则跨角色的同一问题不能归并，未路由子 issue 和撤回提交也会漏掉。
- **继续用 v3 的外部记忆复盘。** 否决。主人要求问题进入能归并、核实、提出方案并批准落地的工作流。外部记忆不是这条 issue 队列；复盘也不读取私人对话记录。

## Consequences

- 每条问题保留一个编号，出现记录与落地计划在同一 issue 上，Go 前不会被当成已批准的票。
- `needs-triage` 只表示等主人决定，机器尚未处理的工作不混进主人的队列；暂缓不会自动过期。
- 复盘提议走现有的检查、技能文字、Bug fix 或 Feature 路线，不写进 `AGENTS.md`、`CLAUDE.md`、外部记忆或仓库自己的编码规范文件。
- 本决定改写 ADR 0035 的 Memory 收尾和 ADR 0039 的复盘提案写入 `CODING_STANDARDS.md` 两项。0035 的会话 Space 设置与 0039 的 `TESTING.md` 随改动更新不在本决定范围内。
- 复盘失败写明原因，不阻止合并。运行中的 MMW 保持冻结，新版本发布且没有监视开着时才迁移已有仓库的标签。
