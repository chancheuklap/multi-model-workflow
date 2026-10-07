# 卡片与右栏详情 (#548)

## Question

一张卡片上写哪些字段？点开之后右栏按什么顺序讲清这张票的来龙去脉（事件、阻塞、子 issue）？

## Current conclusion

胜出方案是生产版任务板的界面，`mmw-v2/board/page/`，其中`canvas.mjs` 画卡片，`detail.mjs` 画右栏。试点 #541 规定设计决定取自生产版，所以本目录没有写变体代码，也没有 `?variant=` 切换条；决定的细节写在 #548 的解决评论里。

## Which parts the real code has taken

全部：胜出方案就是生产代码。它的状态清单与交给 Claude Design 的输入，合在 `prototypes/task-board/553/UI/README.md` 的 `## State list`。
