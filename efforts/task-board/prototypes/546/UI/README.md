# 画布：四层结构怎么摆 (#546)

## Question

map、spec、ticket、子 issue 四层在画布上怎么摆，阻塞关系怎么画，画布怎么平移缩放？

## Current conclusion

胜出方案是生产版任务板的界面，`mmw-v2/board/page/`，其中`canvas.mjs`、`board-logic.mjs` 负责画布与排布。试点 #541 规定设计决定取自生产版，所以本目录没有写变体代码，也没有 `?variant=` 切换条；决定的细节写在 #546 的解决评论里。

## Which parts the real code has taken

全部：胜出方案就是生产代码。它的状态清单与交给 Claude Design 的输入，合在 `prototypes/task-board/553/UI/README.md` 的 `## State list`。
