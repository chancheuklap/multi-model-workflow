---
date: 2026-10-29
amends: [0048]
---

# 产品的 e2e 全套是 `scripts/check --all` 的一步 `e2e-<product>`，默认档从不选它

一个产品有了 `verify-<product>` 之后，它的整套 `product` target e2e 测试作为 `scripts/check` 里只属于 `--all` 的一步 `e2e-<product>` 运行：一晚收尾时由 `dispatch.sh summary`、单张票开 PR 前由 One ticket 第 4 步、接入时由 setup-mmw 各跑一次 `--all` 带上它。默认档从不选 `tests/e2e/`，所以落地时的检查不跑 e2e。e2e test 仍由白天写、夜里只读。主人的决定见 spec [#1407](https://github.com/chancheuklap/multi-model-workflow/issues/1407) 第 7 节（主人 2026-10-29 批准）。

## 要修的是什么

全套 e2e 原先靠 Run a night 第 5 步和 One ticket 第 4 步各一段手写命令。命令写死 `npx e2e`，在 e2e 装在 `tests/e2e/<product>/` 自己 package 里的仓库找不到它（#1405），跑完也不留记录。

## Considered Options

- 保留手写命令，只修好找不到 runner 的问题。否决：两段说明仍是脚本之外的第二条路，跑没跑没有记录（spec #1407 第 7 节）。
- 让默认档也选 e2e。否决：每次落地都跑整套 e2e，代价高，而 0048 定下的"夜里只读、票的 CHECK 只跑本票测试"不需要它。

## Consequences

- 0048 `## Consequences` 第 2 条"e2e test 归产品的验证系统，不进 `TESTING.md`、`scripts/check`、spec 的 Testing Decisions 或票的 Seam"不再全部成立：e2e test 进 `scripts/check --all` 的 `e2e-<product>` 一步，仍不进默认档、spec 的 Testing Decisions 和票的 Seam（`TESTING.md` 已由 0060 删除）。
- 0048 其余仍然成立：e2e test 和 feature map 白天写、主人要求时维护复核、夜里只读；Isolate 的两层不变。
- 一晚收尾时，只有 `e2e-<product>` 红、且这一晚还有未关闭的票其 `CHECK:` 点到 `tests/e2e/<product>/`，`summary` 照常收尾并列出它们，由编排者把红测试记在那张票下或当回归修。
