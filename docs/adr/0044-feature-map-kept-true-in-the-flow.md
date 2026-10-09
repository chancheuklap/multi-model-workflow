---
date: 2026-10-09
amends: [0041]
---

# feature map 靠流程里的环节保持为真：lint、同一提交、Spec 轴读 Owns 里的功能文件、读到不对当场处理、retro 的 `feature-fact`，改「产品能做什么」之前先经主人确认；复核只在主人要求时做

ADR 0041 的标题说 feature map 由 lint、同一提交和定期复核保持为真，正文还把定期复核排给本组第 5 份 spec。主人的规则是常驻文件在改变它的流程里当场更新，不靠定期复核；`mmw-mode` 的触发行也已经是主人要求时才复核。这份决定改写 0041 的那一句：功能文件靠下面六样保持为真，复核不再是其中一样。

1. `feature_map.py lint` 查格式、索引、出处和检查目标。
2. 改功能的人在同一个提交里改对应的功能文件。
3. 审查的 Spec 轴读票 `## Owns` 里那几个功能文件被审那次提交的版本。
4. 读到功能文件不对时当场处理：白天的会话按 `mmw-v3/skills/mmw-mode/references/feature-map.md` 的 `## Using it in a task` 在它的提交里改正；脚本起的会话不拥有这个文件时，记一个 `deferred` 子票，写明那一行和产品实际怎样。
5. retro 的去向有 `feature-fact`：一夜里查出功能文件缺的或错的一行，作为补功能事实的去向记下。
6. 功能文件里「产品能做什么」的部分（开头一段、`## Sub-features` 的句子、`## How to get to it (user POV)`、README 的 `Features` 行）写进或改动之前，先在对话里列给主人确认；夜里只写 spec 的 `## Feature map changes` 已列出、已确认的。`## Driving it`、`## Gotchas`、`source`、`check` 是工程事实，agent 自己写。

## 要修的是什么

审查 `docs/reviews/2026-10-09-verification/README.md` 问题 29：以后读 ADR 的 agent 会照 0041 去安排定期复核，和主人的规则相反。同一审查的问题 27 补上了第 3、5 两样，问题 32 定了第 6 样。ADR 写完不改正文（ADR 0038），所以另写这一份。

## Considered Options

- **保留定期复核，作为第七样。** 否决。按期复核意味着功能文件在两次复核之间可以是错的；上面每一样都在改变事实的那一步当场写，复核留给主人点名的时候。
- **直接改 0041 的标题。** 否决。ADR 写完不改正文，勘误只改路径。

## Consequences

- 维护功能地图的复核（maintain-verification-skill）只在主人要求时进入，不排期。
- 本仓库根 `.mmw/target.json` 的 `checks` 调用 feature map 的 lint，0041 最后一条「`checks` 还不调用」对本仓库不再成立；它要等装着的 checkout 移到含 `feature_map.py` 的提交之后才在合并时跑得起来。
