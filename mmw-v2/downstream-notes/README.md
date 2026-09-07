# downstream-notes

本仓库的改动让 consuming repository 里已有产物失效时，一次改动一份：改了什么、哪些产物因此失效、怎么迁。
方向与 merge-note 相反：merge-note 记的是 upstream 再动时本仓库怎么取舍；这里记的是本仓库改了之后 consuming repository 怎么跟上。

## 什么改动必须写一份

凡是改动会让 consuming repository 已有的 screen contract、ticket 的 `CHECK:` 或 `.mmw/target.json` 失效的。

## 一份写三样

每份说明固定这三个标题字面，按这个顺序：

- `## 改了什么`。
- `## 哪些产物失效`：consuming repository 里哪些产物因此失效，按 `## 什么改动必须写一份` 的三类点名；target trees 随 screen contract 一起。
- `## 怎么迁`：能一条命令说清的就给命令，说不清的给判断依据。

文件名是造成这次改动的 ticket 号加一个 slug（`158-drive-target-judges.md`）。索引每行 `[<文件>](<文件>) — mmw #<n>`。

## 目前有说明的改动

- [201-trigger-after.md](201-trigger-after.md) — mmw #201
- [207-negative-control-per-row.md](207-negative-control-per-row.md) — mmw #207
- [216-story-judges.md](216-story-judges.md) — mmw #216
- [220-target-json-fields.md](220-target-json-fields.md) — mmw #220
- [221-contract-format.md](221-contract-format.md) — mmw #221
- [255-journey-address-case.md](255-journey-address-case.md) — mmw #255

