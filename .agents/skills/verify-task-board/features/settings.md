# 本机配置
Route: / → 顶栏齿轮「本机配置」
Tests: settings.e2e.ts

在看板上看、改这台机器上每个 agent 跑在哪个 host、model、effort，以及会话派子代理时用哪个 model、effort，保存到本机的 `models.json`。分三个页签：「会话角色」「子代理」「型号目录」，共用底部一个状态栏和一个「保存」。

## Sub-features

- 「会话角色」：runner（用什么起 session），和「一个 agent 一行」：每个会话角色一行，host、model、effort 三个下拉框。
- 「子代理」：`review-axis`、`reader`、`default` 三行，各写一句用途；每行在 claude、codex 上各有 model、effort 两个下拉框。「跟叫它的会话一样」就是用派它的那个会话自己的 model 或 effort。Claude 的 model 可选 sonnet、opus、haiku、fable，effort 可选 low 到 max；Codex 的 model 来自它的型号目录，effort 随所选 model 变；Codex 选「跟叫它的会话一样」时，effort 只列每个 Codex model 都支持的档位。
- 「型号目录」：每个 host 问到了几个 model、目录是什么时候读到的、现在可选哪些；最近一次读取失败时，写出失败种类和详情，并说明仍在用哪一次读到的那份；「重新扫描」再问一次。下面列出所有「存的型号已不在目录里」的格子，写明存的名字和现在可选的名字，「跳到这一格」把焦点放到那一格。
- 一个型号在整页只有一种名字，和「会话角色」那一列的写法相同。
- 页签名后标出这一页的情况：几处不对、改了几处、读取失败、几格旧型号。
- 底部状态栏写改了几处、为什么不能保存、已保存；有格子不对时「保存」不可用。「保存」一次写回整份配置，子代理也在里面。
- 打开之后配置被别处改过，保存被拒，「重新读取」换成现在保存着的内容。

## How to get to it (user POV)

打开看板，点右上角齿轮「本机配置」，再点页签。不需要账号。

## Driving it with e2e

`settings.e2e.ts` 改 `reviewer 的 effort`，看底部「改了 1 处」，点「保存」看「已保存」，关掉再打开，读回新值。下拉框都按「<agent> 的 host / model / effort」的可访问名字找；关闭按钮是「关闭本机配置」。

## Proof

改过的格子在关掉、重新打开本机配置后仍是新值，底部写「已保存 · <时刻>」。

## Gotchas

- 每次运行的 `MMW_HOME` 是新的，从 `scripts/dev/board-fixtures/` 起步：`reviewer` 是 claude、sonnet、high。型号目录来自 `host-catalog.json`，不问本机的 claude、codex。
- 「重新扫描」在测试里读的是同一份目录，看不出目录变化；目录读失败、存的型号不在目录里，这两个状态本机造不出来，用 `browser.route` 截 `GET /api/settings`。
