# 灯与药丸 (#547)

## Question

每张卡片用什么视觉元素回答要不要我出手和卡在哪一步？各有几种状态、各用什么颜色？

## Current conclusion

胜出方案是生产版任务板的界面，`mmw-v2/board/page/`，其中`shared.mjs`、`board-logic.mjs` 负责灯与药丸。试点 #541 规定设计决定取自生产版，所以本目录没有写变体代码，也没有 `?variant=` 切换条；决定的细节写在 #547 的解决评论里。

## Which parts the real code has taken

全部：胜出方案就是生产代码。它的状态清单与交给 Claude Design 的输入，合在 `prototypes/task-board/553/UI/README.md` 的 `## State list`。
