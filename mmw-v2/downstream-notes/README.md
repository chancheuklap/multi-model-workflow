# downstream-notes

本仓库的改动让 consuming repository 里已有产物失效时，一次改动一份：改了什么、哪些产物因此失效、怎么迁。
方向与 merge-note 相反：merge-note 记的是 upstream 再动时本仓库怎么取舍；这里记的是本仓库改了之后 consuming repository 怎么跟上。

## 什么改动必须写一份

凡是改动会让 consuming repository 已有的 screen contract、ticket 的 `CHECK:` 或 `.mmw/target.json` 失效的。

## 一份写三样

每份说明固定这三个标题字面，按这个顺序：

- `## 改了什么`。
- `## 哪些产物失效`：consuming repository 里哪些产物因此失效，按 `## 什么改动必须写一份` 的三类点名。
- `## 怎么迁`：能一条命令说清的就给命令，说不清的给判断依据。

文件名是造成这次改动的 ticket 号加一个 slug（`158-drive-target-judges.md`）。现行说明的索引每行 `[<文件>](<文件>) — mmw #<n>`。

一份说明被后一份完全接住时，原文件移到 `archive/`，并从 `## 目前有说明的改动` 挪到 `## 已被取代`。那一节每行 `[<文件>](archive/<文件>) — mmw #<n>，由 [<新文件>](<新文件>) 取代`。

## 目前有说明的改动

- [255-journey-address-case.md](255-journey-address-case.md) — mmw #255
- [341-origin-base-branch.md](341-origin-base-branch.md) — mmw #341
- [359-landed-ticket-branch-deleted.md](359-landed-ticket-branch-deleted.md) — mmw #359
- [370-lease-held-per-ticket.md](370-lease-held-per-ticket.md) — mmw #370
- [373-truthful-ports-and-story-service.md](373-truthful-ports-and-story-service.md) — mmw #373
- [449-skill-renamed-ui-acceptance.md](449-skill-renamed-ui-acceptance.md) — mmw #449
- [450-target-config-check.md](450-target-config-check.md) — mmw #450
- [453-element-parity.md](453-element-parity.md) — mmw #453
- [454-story-inputs-and-refusals.md](454-story-inputs-and-refusals.md) — mmw #454
- [455-journey-break.md](455-journey-break.md) — mmw #455
- [456-harness-markers.md](456-harness-markers.md) — mmw #456
- [472-skill-renamed-design-pages.md](472-skill-renamed-design-pages.md) — mmw #472
- [473-handoff-package-by-pull.md](473-handoff-package-by-pull.md) — mmw #473
- [476-design-project-claude-md.md](476-design-project-claude-md.md) — mmw #476
- [491-skill-renamed-write-screen-contract.md](491-skill-renamed-write-screen-contract.md) — mmw #491
- [492-skeleton-by-data-ui-id.md](492-skeleton-by-data-ui-id.md) — mmw #492
- [494-screen-contract-format.md](494-screen-contract-format.md) — mmw #494
- [514-interface-tickets.md](514-interface-tickets.md) — mmw #514

## 已被取代

- [201-trigger-after.md](archive/201-trigger-after.md) — mmw #201，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
- [207-negative-control-per-row.md](archive/207-negative-control-per-row.md) — mmw #207，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
- [216-story-judges.md](archive/216-story-judges.md) — mmw #216，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
- [220-target-json-fields.md](archive/220-target-json-fields.md) — mmw #220，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
- [221-contract-format.md](archive/221-contract-format.md) — mmw #221，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
- [298-scene-data-from-the-page.md](archive/298-scene-data-from-the-page.md) — mmw #298，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
- [344-quoted-accessible-names.md](archive/344-quoted-accessible-names.md) — mmw #344，由 [514-interface-tickets.md](514-interface-tickets.md) 取代
