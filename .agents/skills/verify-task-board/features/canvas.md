# 画布
Route: /
Tests: issue-641.e2e.ts

中间的画布，一张卡片一张票，按依赖排开，可缩放；点卡片打开详情。

## Sub-features

- ticket 卡片显示阶段，点击后打开该票详情。
- block line 显示依赖是否仍被上游阻塞。

## How to get to it (user POV)

打开看板就在。

## Driving it with e2e

`issue-641.e2e.ts` 操作原刷新按钮和 `#11 source ticket` 卡片；在 GitHub I/O 边界给出关闭和合入，检查 `.e-block.blocked`。

## Proof

上游已关闭且合入，手动刷新后卡片为 landed，出边不再显示 blocked。来源为 #641 的原现象和主人要求修正现有状态的一致性。

## Gotchas

- 内容读自 GitHub 上的真实仓库，随时在变；测试要固定的数据时，用 `browser.route` 截 `GET /api/board`。
- #641 的读取缺陷必须经过真实后端，`issue-641.e2e.ts` 因此使用现有 fake gh 和独立 MMW_HOME，不能用固定的 `/api/board` 回答替代待测后端。
