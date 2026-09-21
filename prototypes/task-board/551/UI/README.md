# 本机配置页 (#551)

## Question

本机配置页长什么样：怎么打开、怎么显示每个 host 在本机的状态、坏值怎么标、保存前怎么看改了哪几处？

## Current conclusion

胜出方案是生产版任务板的界面，`mmw-v2/board/page/`，其中`settings.mjs`、`local-config.mjs` 负责本机配置页。试点 #541 规定设计决定取自生产版，所以本目录没有写变体代码，也没有 `?variant=` 切换条；决定的细节写在 #551 的解决评论里。

## Which parts the real code has taken

全部：胜出方案就是生产代码。它的状态清单与交给 Claude Design 的输入，合在 `prototypes/task-board/553/UI/README.md` 的 `## State list`。
