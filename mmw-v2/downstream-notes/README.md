# downstream-notes

本仓库的改动让 consuming repository 里已有产物失效时，一次改动一份：改了什么、哪些产物因此失效、怎么迁。
方向与 merge-note 相反：merge-note 记的是 upstream 再动时本仓库怎么取舍；这里记的是本仓库改了之后 consuming repository 怎么跟上。

## 什么改动必须写一份

凡是改动会让 consuming repository 已有的 screen contract、ticket 的 `CHECK:` 或 `.mmw/target.json` 失效的。target trees 随 screen contract 一起点名。Done when：该不该写一份已经能从这一条判出来。

## 一份写三样

1. 改了什么。
2. consuming repository 里哪些产物因此失效：screen contract、ticket 的 `CHECK:`、`.mmw/target.json`、target trees，按类点名。
3. 怎么迁：能一条命令说清的就给命令，说不清的给判断依据。

不做迁移脚本框架，不做版本号协商。文件以改动命名，列进下面的索引。Done when：三样都有、索引有这一条。

## consuming repository 怎么用

1. 打开对应改动的说明。
2. 按「怎么迁」执行或判断。
3. 迁完：该改的 screen contract、`CHECK:`、`.mmw/target.json`、target trees 与说明里点名的类一致。

## 目前有说明的改动

尚无。下一份从本仓库下一次会让 consuming repository 产物失效的改动起写。
