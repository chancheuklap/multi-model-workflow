---
date: 2026-10-27
amends: [0054]
---

# 一张票装得下的技能文字由 Authoring 会话自己写，新 agent 的试走当裁判；脚本仍交 worker

Authoring or modifying a skill 的会话在 `fix-<n>` 上直接写一张票装得下的技能文字，提交推送后，有行为改变的就派一个新 agent 走一项真实任务，再把写的原句和试走结果交给主人，主人说行就从 `fix-<n>` 开 PR。文字不再交给 worker 照抄，也不再派审查员。脚本照旧由 worker 写、审查员审，它旁边的技能文字由会话先写在 `fix-<n>` 上，不进票的 Owns。试走对本次写的句子猜错了，会话当场改，再走一次；第二次仍发现的交给主人。票通过以后主人再决定改一两句，会话在 `fix-<n>` 上改，不重开票、不派 worker。

## 要修的是什么

0054 让文字和脚本一样交给 worker，Prove it, once 排在票通过之后。会话为了让 worker 写对，把原句一字一句写进票，worker 照抄，审查员审，试走一发现问题就加一条验收、重开票，换新 worker 和新审查员重来。这个循环没有上限。

- [#1268](https://github.com/chancheuklap/multi-model-workflow/issues/1268) 派了 5 个 worker、5 个审查员，前后 2 小时 50 分，其中一次只为撤回一条验收。
- [#1165](https://github.com/chancheuklap/multi-model-workflow/issues/1165) 派了 4 个 worker、4 个审查员，试走连续 3 次不过；票里写死的原句和别处冲突，worker 开了 4 张 contract 子票。
- [#1271](https://github.com/chancheuklap/multi-model-workflow/issues/1271) 通过后试走要补一句，worker 因票已关闭拒绝认领（[#1273](https://github.com/chancheuklap/multi-model-workflow/issues/1273)）。

两张票上审查员一共找出 4 处问题，都是旧说法还留在别的文件里，写之前搜一遍就能找到。设计意图第 18 条本来就规定技能文字由试走证明，测试只证明脚本。

## Considered Options

- **保留 worker，只给回头次数设上限。** 否决。文字仍要写两遍，冻结的原句仍会引出 contract 子票，每一圈仍要一个新 worker 和一个新审查员。
- **会话写文字，再派一次审查员。** 否决。审查员和试走查的是同一件事，试走用真实任务查得更准。
- **会话写文字，新 agent 试走当裁判。** 采用。写的人不当裁判仍然成立，裁判是没见过这些字的 agent。

## Consequences

- 恢复了 `DESIGN-INTENTS.md` `## Departures` P21 拿掉的一半：一个 agent 能做完的技能文字由会话写，但仍开票、仍等主人说行，脚本仍交 worker。
- `mmw-mode` 的 `references/owning-a-task.md` `## Playbooks` 把这两种情况列为 worker 规则的例外。
- 主人的话来源于 [#1291](https://github.com/chancheuklap/multi-model-workflow/issues/1291)。
