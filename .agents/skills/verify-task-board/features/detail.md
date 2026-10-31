# 详情
Route: /
Tests: issue-641.e2e.ts

右边一列，选中那张票的状态、阶段、用的 model、事件记录、子 issue，以及去 GitHub 的链接。

## Sub-features

- 详情头部显示选中 ticket 的当前阶段。
- Events 按阶段分块，review 结束、worker 再次认领后，最新一块表达 working。

## How to get to it (user POV)

打开看板就在。

## Driving it with e2e

`issue-641.e2e.ts` 点击 `#11 source ticket`，对比 `详情.status.phase` 和最新 `详情.event-block.phase`。

## Proof

reviewer 已交出结果且 worker 再次认领，卡片、详情头部和 Events 最新阶段均为 working。来源为 #641 的 C 和本轮原页面复现，不增加 UI 字段或改变早先 review 事件的含义。

## Gotchas

- 内容读自 GitHub 上的真实仓库，随时在变；测试要固定的数据时，用 `browser.route` 截 `GET /api/board`。
