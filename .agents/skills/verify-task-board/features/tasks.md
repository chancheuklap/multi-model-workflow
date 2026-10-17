# 任务列表
Route: /
Tests: none

左边一列，按地图列出任务；点一个任务，画布换成它的票。

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
