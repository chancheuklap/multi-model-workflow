---
date: 2026-10-19
amends: [0038, 0055]
---

# 研究答案、非界面原型的结论和工作记录只记在票的评论里

研究答案、LOGIC、EXP、SKETCH 原型的结论、修改技能的 findings、技能流程的 walk record，以及 Hillclimb 的尝试记录，都写在提出问题的票上，不另存仓库文件。这份决定采用 #1165 正文 What to build 第 14、15 条中主人的决定，改写 0038 的地图研究笔记位置和 0055 的非界面原型 README 约定。原型代码仍留在仓库，UI 原型的结论仍进 feature file，两份 ADR 的其他决定保持不变。

## 每种记录放在哪里

- 研究答案作为研究票的 resolution comment，原样保留研究会话的回答。
- LOGIC、EXP、SKETCH 的 verdict comment 写明问题、定下的答案和被否决的选项，building ticket 的 Read first 同时列出原型目录和结论评论，作为 baseline。
- 实验的每一轮各有一条评论，结论评论随实验结果更新，包含可复用部分。
- 修改技能的 findings 和 walk record 各作为票上的评论，后者从 PR 链接。
- Hillclimb 每次尝试各有一条 Attempt 评论，记录假设、改动、前后结果、测试及保留或撤回的结论，baseline 是 Attempt 0。

## Considered Options

- **在仓库和票里各留一份记录。** 否决。同一结论有两个位置，后续会话可能读到不同版本，且需要额外维护同步。
- **只删非界面原型的 README，研究笔记和工作日志仍进仓库。** 否决。主人在 #1165 第 14、15 条决定把这些记录一并放在票里。
- **改写 0038 和 0055 的原文。** 否决。ADR 是历史记录，后来的决定通过 amends 说明取代了哪些部分。

## Consequences

- `efforts/<effort>/research/` 不接收新的研究答案，LOGIC、EXP、SKETCH 的结论不另写 README，Hillclimb 不另写仓库内的尝试日志。
- spec 和 ticket 引用结论时给出评论链接，引用原型代码时给出仓库路径。无票原型的结论按 prototype 技能规则写在回复里。
- 原型代码、生成实验页面的程序和 UI 的 winner 仍进仓库。UI 的 feature-file 结论及其他验证资产的位置不变。
- 已有研究笔记和原型 README 保留其历史内容，不因这份决定迁移或删除。
