# 910-migrate-products

## 改了什么

一个仓库可以有几个产品。每个产品的 `target.json`、`harness/`、`stories/` 和 `journeys/` 放在 `.mmw/<产品名>/`。根 `.mmw/target.json` 保留 `checks`。文件里已经有的 `needs` 留在根上。`products` 写成这次命令收到的那一个产品名。`.mmw/AGENTS.md` 和 `.mmw/CLAUDE.md` 仍在根上。

`efforts/*/screen-contract.yaml` 增加顶层键 `product`。`docs/features/` 里的 `journey.py run <flow>` 写成 `journey.py run <产品名>/<flow>`。

## 哪些产物失效

- 根 `.mmw/target.json` 仍带着 `start` 这类产品键的旧布局。新版 MMW 装上以后，这样的仓库开 night 会被旧布局拒绝，直到跑下面的迁移命令。拒绝的下一步就是这条命令。
- journey 名字。critical flow、feature map 和 ticket 的 `CHECK:` 里，`journey.py run <flow>` 要写成 `journey.py run <产品名>/<flow>`。这条命令只改仓库里 `docs/features/` 下的文件，不改 tracker 上的 ticket。
- 缺顶层键 `product` 的 screen contract。值是产品名。

## 怎么迁

在消费仓库的 clone 里，切到要迁的分支，再运行。`<产品名>` 只含小写字母、数字和连字符。

```
python3 ~/.agents/skills/setup-mmw/scripts/migrate_products.py <产品名>
```

命令用 `git mv` 移动 `harness/`、`stories/` 和 `journeys/`，改写根 `target.json`、各产品的 `target.json`、screen contract 和 `docs/features/` 里的 journey 名字。它只暂存，不提交。成功时最后一行是 `PRODUCTS MIGRATED <n> changes`。没有旧布局时打印 `PRODUCTS OK`。两种情况都退出 0。

`.mmw/<产品名>/` 已经存在，而根上仍是旧布局时，命令退出 2，工作区没有任何改动。

`CLIMBS <n>` 列出的是移动后仍靠数父目录找仓库根的文件，例如 `parents[2]` 或 `../..`。这些文件比原来深了一层，原来的层数会指错一层。命令不改这些文件。按列出的路径自己改。

`STILL NAMED <n>` 后面的 `git grep` 列出仍写着旧路径的被跟踪行。一份历史文件保留它写成时的路径。一条仍会执行的命令改成新路径。
