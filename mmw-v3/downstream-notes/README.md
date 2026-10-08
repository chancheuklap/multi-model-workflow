# downstream-notes

本仓库的改动让 consuming repository 里已有产物失效时，一次改动一份。一份说明写三件事：改了什么、哪些产物因此失效、怎么迁。

方向与 merge-note 相反。merge-note 记的是 upstream 再动时本仓库怎么取舍。这里记的是本仓库改了之后，consuming repository 怎么跟上。

## 什么改动必须写一份

改动会让 consuming repository 已有的 screen contract、ticket 的 `CHECK:`、`.mmw/target.json`，或某个技能让它生成的文件失效时，写一份。技能改了它要求生成的文件该做什么，已经生成出去的文件不会自己跟上，所以同样要写。

## 一份写三样

每份说明按这个顺序使用这三个标题。

- `## 改了什么`
- `## 哪些产物失效`。点名 screen contract、ticket 的 `CHECK:`、`.mmw/target.json`，或技能生成的文件里因此失效的那几类。
- `## 怎么迁`。能一条命令说清的就给命令。说不清的给判断依据。

文件名是造成这次改动的 ticket 号加一个 slug，例如 `910-migrate-products.md`。

现行说明的索引每行是 `[<文件>](<文件>) — mmw #<n>`。

一份说明被后一份完全接住时，把原文件移到 `archive/`，并从 `## 目前有说明的改动` 挪到 `## 已被取代`。`## 已被取代` 每行是 `[<文件>](archive/<文件>) — mmw #<n>，由 [<新文件>](<新文件>) 取代`。

## 目前有说明的改动

- [910-migrate-products.md](910-migrate-products.md) — mmw #910
