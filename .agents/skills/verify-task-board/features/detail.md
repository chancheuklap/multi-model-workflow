# 详情
Route: /
Tests: none

右边一列，选中那张票的状态、阶段、用的 model、事件记录、子 issue，以及去 GitHub 的链接。

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
