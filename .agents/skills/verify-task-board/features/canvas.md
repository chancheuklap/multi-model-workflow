# 画布
Route: /
Tests: none

中间的画布，一张卡片一张票，按依赖排开，可缩放；点卡片打开详情。

## Sub-features

- 还没有逐项登记；第一次有票改到这里时，照代码补全，并写这一部分的测试。

## How to get to it (user POV)

打开看板就在。

## Driving it with e2e

还没有测试。

## Proof

还没有测试。

## Gotchas

- 内容读自 GitHub 上的真实仓库，随时在变；测试要固定的数据时，用 `browser.route` 截 `GET /api/board`。
