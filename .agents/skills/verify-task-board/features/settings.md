# 本机配置
Route: / → 顶栏齿轮「本机配置」
Tests: settings.e2e.ts

在看板上看、改这台机器上每个 agent 跑在哪个 host、model、effort，保存到本机的 `models.json`。

## Sub-features

- 「本机的 host」：每个 host 问到了几个 model，或者为什么没问到；「重新扫描」再问一次。
- runner：用什么起 session。
- 「一个 agent 一行」：每个会话角色一行，host、model、effort 三个下拉框；start 会拒绝的格子带斜线，下面写哪里不对。
- 底部状态写改了几处、为什么不能保存、已保存；「保存」一次写回整份配置。
- 打开之后配置被别处改过，保存被拒，「重新读取」换成现在保存着的内容。

## How to get to it (user POV)

打开看板，点右上角齿轮「本机配置」。不需要账号。

## Driving it with e2e

`settings.e2e.ts` 改 `reviewer 的 effort`，看底部「改了 1 处」，点「保存」看「已保存」，关掉再打开，读回新值。下拉框都按「<agent> 的 host / model / effort」的可访问名字找；关闭按钮是「关闭本机配置」。

## Proof

改过的格子在关掉、重新打开本机配置后仍是新值，底部写「已保存 · <时刻>」。

## Gotchas

- 每次运行的 `MMW_HOME` 是新的，从 `scripts/dev/board-fixtures/` 起步：`reviewer` 是 claude、sonnet、high。型号目录来自 `host-catalog.json`，不问本机的 claude、codex。
- 「重新扫描」在测试里读的是同一份目录，看不出目录变化；目录读失败、存的型号不在目录里，这两个状态本机造不出来，用 `browser.route` 截 `GET /api/settings`。
