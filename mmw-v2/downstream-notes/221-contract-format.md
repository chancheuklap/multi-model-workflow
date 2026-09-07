# 221-contract-format

## 改了什么

screen contract 不再写到达路径、定位钉和读回断言。`scenes.<name>` 只留 `page`；`pages` 每页留 `mount` 与 `component`，只有 `App · ` 页可写 `route`；行只留 `id`、`component`、`trigger`、`precondition`、`scenes`、`calls`、`shows`、`next`、`on_failure`、`source`、`gap`。`retired_ids`、`volatile_values`（含 `after`）、`readme_dispositions`、`backend_without_ui`、`proposed_operations`、`viewports`、`target.kind` 原样。lint 对出现的已删字段点名报 error；合同目录下最近一次 `story-parity.py --out` 清单若漏了某个非 App 页的场景，报警告。

## 哪些产物失效

- screen contract：仍写行上 `observe` / `after` / `route`、非 App 页的 `route`、`scenes` 上除 `page` 以外的键、或顶层机制表的，lint 从绿变红。
- ticket 的 `CHECK:`：`wiring-check.py` 所依赖的行字段不再存在；界面票的外观判据改为 `story-parity.py --pages <mount,…>`，接线判据改为 `boundary-check.py --run …`。
- target trees 不因此失效；哈希检查照旧。

## 怎么迁

打开 `docs/specs/<effort>/screen-contract.yaml`，删掉上一节点名的键，给每个 `Component · ` 页留下 `mount` 与 `component`。用本仓库的 `lint_contract.py --tools <drive-target scripts>` 对着现有 skeleton 跑到零 error。界面票的 `CHECK:` 按第二份 spec 改写，不在本仓改消费仓库的票。
