# 207-negative-control-per-row

## 改了什么

接线负控制（`wiring-check.py --negative`）拆写路径的时刻从「整次运行之前」改成「这一行自己的触发之前」。场景的 `reach` 与 `open` 链、以及该行的 `drive.open` 在写路径正常时跑；拆掉之后只跑该行的触发与 `observe`；下一行的 `reach` 之前再恢复。一行到不了（mount 没出现、控件不在）不再让整次停跑：其余行仍被评到，但只要有任何一行没被评到，整条判据仍退 2，并列出那些行。

## 哪些产物失效

- ticket 的 `CHECK:`：consuming repository 里 `wiring-check.py --rows … --negative`、原先因为到达画面要写入而整次退 2 的判据。那些行现在会被评到。其中 `observe` 在没有持久化时仍成立的，会印 `GREEN WITHOUT TRANSPORT <row>` 并退 1——那是这道门要抓的假绿，不是回归。`EXPECT: WIRING NEGATIVE OK <n>/<n>` 的形状不变。
- screen contract 与 `.mmw/target.json` 不因此失效：`transport_off` / `transport_on` 仍是仓库答的那两条命令；行的 `observe` 与 `reach` 不用改。

## 怎么迁

把原先退 2 的负控制判据再跑一遍。`WIRING NEGATIVE OK` 表示点名的每一行都评到了 `observe`，并且都在断言上 MISS；原先因到达要写入而整次退 2 的行，现在能被评到。`GREEN WITHOUT TRANSPORT` 是读表面不是从持久化状态喂的，改产品的读路径，不要为了让画面在写路径断开时也能到达去改报价方法或控件的出现条件。仍退 2 的，报错里列的是哪几行没被评到。
