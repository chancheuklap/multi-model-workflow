---
date: 2026-08-11
amends: [3]
---

# 历史产物人工处理，不做迁移命令

ADR 0003 换掉了全部 MMW 产物的路径形状，并留下一条 Consequence：历史产物由一条可重复执行的 CLI 迁移命令处理。取证之后我们不做这条命令，历史产物改为人工处理。理由是实际对象数量少：本机两个已装 MMW 的仓库里，只有 `agentflow` 的 `.dispatch/investigator-probe-brief.md` 这一个文件落在新合同已经取消的类别根下。

## Considered Options

**做一条可重复执行的 CLI 迁移命令**（否决）。它是 ADR 0003 原来写下的做法，否决理由有两条。

第一条是对象太少。`multi-model-workflow` 的 `docs/research/` 已经符合新路径形状，`docs/adr/` 与 `docs/context/` 是仓库级产物、没有名字段，零个对象。`agentflow` 当前没有 `docs/specs/` 文件（全历史出现过 45 个，被 `/mmw-closing` 删除了），所以 spec 改名这一项没有对象；`docs/plans/` 的类别根不变，只有名字段的取值可能过时。

第二条是识别不可靠。`agentflow` 的 `docs/plans/` 里既有 MMW 产的 plan，也有更早的其他工作流产的文档，没有任何标记能分开：早期目录里的文件名是 `2026-05-17-ai-review-batch-completion-progress-plan.md`，晚期是 `001-memory-snapshot-version-swap.md`。一条会移动 Git 跟踪文件的命令，靠这种规则圈定对象并不安全。

## Consequences

- `mmw doctor` 增加一项只读报告，报仓库里存在的、新合同下不该存在的路径，不动文件。它把「要人工处理什么」变成一条随时能跑出来的清单。
- 报三项，判据是这条路径在新合同下不该存在，机器能直接判定：`docs/evidence/` 存在（ADR 0003 取消了这个类别根）；`.dispatch/` 存在（ADR 0004 决定四栏 task 与角色报告不落盘）；`docs/specs/<X>/<X>.md` 存在（新的 spec 文件名是 `spec.md`）。
- 不报 `docs/plans/` 与 `docs/research/` 下名字段的取值。机器判定不了某个目录名是旧的任务 slug 还是新的工作名，报它就是用列表形状伪装成机械校验。也不报过程材料与审查记录内部的细分差异：这两个类别根仍然存在，而且它们的内容本来就在任务结束时清理。
- 这三项检查不改变 `mmw doctor` 的退出码。一个装好的 MMW，在有历史产物的仓库里仍然是装好的；让它因为历史产物而失败，会让人为了让它通过去删东西。ADR 0006 已经要求 `mmw doctor` 报告 `.mmw.json` 里的五项遗留配置，形态与本项相同，两者的退出码行为一致。
- 下面几项归入人工处理，MMW 不做任何机械动作：map 正文的 `## 产物目录` 一节改名为 `## 工作名`；`agentflow` 的 50 个 plan 目录保留旧的名字段取值；历史 spec 不补写 ADR 0001 决定的 YAML 元数据块；被移动文件的旧路径引用；本仓库现有的六份 ADR 补写元数据块。最后一项的对象真实存在——`docs/adr/` 现有 `0001` 到 `0006` 六份且都在使用中，而 ADR 索引取自元数据块，不补写就生成不出内容。它由 spec 阶段的实现一次补齐，来源是 Wayfinder decision ticket #23「读取产物的技能怎么找到它需要的产物」在本 ticket 上留下的补充。
- 取舍是明确的：用 `agentflow` 那 50 个 plan 目录的名字段不一致，换掉一条命令。风险随之而来——那 50 个目录里如果还有没交付完的任务，恢复它时 `mmw/skills-src/mmw-start/resuming.md:24` 会按 `docs/plans/<工作名>/` 去找，目录名对不上就会判定 plan 没写。用户已知情并接受。
- `.mmw.json` 的配置迁移不受影响，仍由 `mmw init` 处理（`mmw/cli/lib/init.sh:52-63`）。这一条来自 ADR 0006。

来源：Wayfinder decision ticket #25「历史产物迁移命令的形态与边界」，map #18「MMW 产物归纳与接线合同」。
