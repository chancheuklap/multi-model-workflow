---
date: 2026-10-06
amends: [0019, 0023]
---

# 夜里每个事实只从记下它的那一条事件读：base branch 读写它的事件，reverify 的结果读 `ticket.checked`；事件在写时按表校验，读时只拒读不懂的

一个问题只有一个出处，没有逐级回退。票落地到哪个 base branch，读它最新 `ticket.passed` 的 `into`（和通过的那个提交记在一起）；票的工作树、合并、归档要的 base branch，读它最新 `worker.started` 的 `into`；一夜的 base branch（`reverify`、`summary`）读这一夜 `spec.opened` 的 `into`。只有 `start` 要在记录出现之前定下它：票还没有 `worker.started` 时，取开着的这一夜的 `into`，夜外取运行 `start` 的那个分支，再把它写进新的 `worker.started`，此后这张票都读那一条。reverify 的结果就是它自己发的 `ticket.checked`（`run=reverify`，带它跑的那个提交）：`summary` 用 `status.py --closeout-ready <spec> --at origin/<into>` 核对每张已落地或被重开的票，最新一次 reverify 是不是在那个提交上全绿，不再读某个 clone 本地的回执文件。事件的字段在写的时候由 `events.py` 的 `build` 按表校验；读的时候 `parse` 只拒绝不是 JSON、版本不对、或词表里没有的事件，字段一律当作可能缺省来读。

## 要修的是什么

- `resolve_into` 先读票、读不到再读这一夜第一张票、再读别处：同一个问题三处答案，哪一处答的要看当时有什么，出错时说不清是哪一处错了。
- reverify 的回执是 `reverify` 写在本地 git 目录里的文件，`summary` 只认同一个 clone 里的那一份：换个 checkout 跑 `summary` 就拒绝，而 reverify 的结果早已作为事件在票上。
- 读事件时也按写入的规则全套校验：以后每给某个事件加一个必填字段，之前写的票就整张读不了。

## Considered Options

- **保留回退链，只在日志里写明用了哪一处。** 否决。回退链的问题是它掩盖缺失：该有的记录不在，应该拒绝并说缺的是哪一条，而不是换一处凑一个答案。
- **reverify 回执改成写在票上的另一条事件。** 否决。`ticket.checked` 已经带着运行种类、提交和结果，再写一条是同一个事实的第二份。
- **读时继续全套校验，加字段时同时迁移旧票。** 否决。迁移就是改 GitHub 上已经写下的评论，是对外写；读时宽容、写时严格，加字段就不用碰旧票。

## Consequences

- 0019「票的状态是事件折叠出来的」照旧；变的是折叠时不再按写入规则判一条事件无效，只有读不懂的那一条让整张票被拒。
- 0023 的落地路径照旧，合并、检查、fast-forward 推送都在 `origin/<base branch>` 上；`advance`、`land`、`integrate` 读 base branch 的出处按上面分开，缺了就拒绝并点名缺的那条事件。
- 2026-10-06 只读扫描了两个接入仓库的开着的票（agentflow 49 张，本仓库 7 张）：带事件的 3 张都能被 v3 读懂，`spec.opened` 都带 `into` 与 `project`，没有一张要改。
