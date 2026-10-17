# 顶栏
Route: /
Tests: smoke.e2e.ts

看板最上面一条：这是哪个仓库的看板，四种状态各有几张票，立刻重读 GitHub，打开本机配置。

## Sub-features

- 仓库名 `chancheuklap/multi-model-workflow`。
- needs you、running、queued、done 四个计数；点 needs you 跳到下一张要你处理的票。
- 「立刻重读 GitHub」：页面开着时每分钟自动读一次，这个按钮立刻读。
- 齿轮「本机配置」。

## How to get to it (user POV)

打开看板就在。

## Driving it with e2e

`smoke.e2e.ts` 看仓库名，点「本机配置」。

## Proof

仓库名可见；点齿轮后本机配置打开，标题「这台机器上，每个 agent 跑在哪」。

## Gotchas

- 票的状态读自 GitHub 上的真实仓库（本机的 `gh`，只读），计数随时在变，测试不断言具体数字。
