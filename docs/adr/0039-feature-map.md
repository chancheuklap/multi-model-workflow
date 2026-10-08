---
date: 2026-10-08
amends: []
---

# feature map 是按产品放的常驻文件，放在 `docs/features/<产品>/`，由 lint、同一提交和定期复核保持为真，night 里只有脚本是通过条件

白天讨论一个产品要改什么，以及 night 里一张票改到已有功能时，都要有一处写着这个产品现在能让用户做成什么、从哪里进、哪条检查守着每个行为。feature map 就是这一处。一个产品一个目录，一个功能一个文件。它在产品还在的时候都得为真。ADR 0038 收常驻文件的条件是有东西让它保持为真。这里是三样。lint 查格式、索引、出处和检查目标。改功能的 worker 在同一个提交里改对应的功能文件。定期复核把 `check: none:` 的行变成可执行的命令，这一项在本组的第 5 份 spec，不在这份决定里执行。night 里一张票过不过，只看会变红的脚本，也就是 criteria 和 pin。`## Driving it` 写怎么操作这个功能，给白天复现和定期复核用。

## Considered Options

- **放在 `.mmw/`。** 否决。那里装的是给脚本执行的东西。agent 常用的搜索默认跳过隐藏目录。ADR 0038 已经因此把设计包和屏幕契约留在搜索能看见的目录里。
- **跟 `CONTEXT.md` 放在一起。** 否决。context 按领域划分，不按产品。一个产品里的功能会散进好几个 context，agentflow 的 context 还是单个文件。
- **把 `## Driving it` 当作 night 的通过条件。** 否决。criterion 由命令判定，否则就不是 criterion。night 里没有东西能检验一段操作说明。把它当成通过条件，就是把 agent 自己的口头判定带回 night。

## Consequences

- 格式与规则只写在 `mmw-v3/skills/mmw-mode/references/feature-map.md`。写 spec、切票和改功能文件的步骤指向它，不另抄一份。
- 词汇在 `docs/contexts/tickets/CONTEXT.md`。spec 和票的各节定义在那个 context。
- `.mmw/target.json` 的 `checks` 还不调用 feature map 的 lint。调用它的脚本要先存在于已安装的 checkout，而一夜进行中那份 checkout 不更新。
