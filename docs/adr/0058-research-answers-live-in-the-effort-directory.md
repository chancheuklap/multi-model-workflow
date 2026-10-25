---
date: 2026-10-25
amends: [0056]
---

# Effort 内的研究答案原样保存在每个问题的目录，由派出会话提交，票的 resolution comment 指向答案文件

一个 effort 内，每位 researcher 的完整回答原样保存在 `efforts/<effort>/research/<ticket number>-<slug>/brief-<n>.md`，为这份回答制作或保存的来源、图片、数据和脚本放在同目录的 `brief-<n>/`。派出会话用 `send researcher --into` 指定目录，读完回答后在 effort branch 上提交并推送，再关闭 brief batch。只有一位 researcher 时，`brief-1.md` 就是答案；有多位时，派出会话另写 `answer.md`，引用各份回答。研究票的 resolution comment 是答案的 `## Answer` 和答案文件路径。本决定只改写 0056 中研究答案的位置，其余记录仍按 0056 放在票的评论里。

## 要修的是什么

- #1268 的 findings 调查了 MMW 使用的五个仓库。研究票的回答中有五份超过 GitHub 单条评论 65,536 字符的上限，十张票靠会话自行分段保存答案。
- 一个问题可能由多位 researcher 回答，一份回答也可能带保存的网页、截图、脚本和数据。每个问题一个目录，每位 researcher 一份回答和一个附件目录，保留彼此的边界。
- 后续票、spec 和地图已经引用研究文件路径。brief batch 的 state 目录会被清理，不能作为后续工作取用答案的位置。
- 0057 已让 brief 会话在派出会话的 worktree 写文件，由派出会话提交在 effort branch，只经主人接受的 PR 进 project branch。研究答案沿用这条提交路径。

## Considered Options

- **完整答案放在票的评论里。** 否决。评论长度限制不能容纳已有的长答案，且回答与后续决定、测试记录混在同一个评论串中。
- **拆成多条评论。** 否决。分段和重组依赖会话自行处理，也不能把回答的附件放在一起。
- **每个问题一个 secret gist。** 否决。答案离开产品仓库和 effort branch，后续工作要在另一处寻找答案和附件。
- **每个问题一个目录，内含各位 researcher 的回答文件。** 采用。回答不受评论长度限制，附件与回答放在一起，研究票只留下摘要和路径。

## Consequences

- `map-<n>` 和 `fix-<n>` 上的 `send researcher` 必须指定符合布局的 `--into`，脚本创建目录并把每份回答和附件的路径写进 brief。
- report 命令、batch 记录和 wake 协议不变。派出会话负责提交，不由 researcher 跑 git 写命令。
- 已提交在五种旧布局中的研究文件留在原处，不迁移、不删除。已有引用继续可用。
- effort 外单独的 Investigation 仍按 0057 `## 边界` 不提交文件，其回答可保存在系统临时目录。
