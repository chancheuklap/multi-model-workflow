# 370-lease-held-per-ticket

## 改了什么

租约的语义有三处变化：

1. **槽按票持有。** 一张票在它第一次跑到"要产品"的判据时占一个槽，一直持有到这张票的工作结束（落地、交回、释放、挂起、撤回），而不是每次运行各占各的。worker 自己那一轮、verifier 的 reverify、closeout 的检查共用同一个槽。
2. **`instance.max` 按整个仓库计。** 计数覆盖这个仓库的每一个检出——票工作树、跑 reverify 的主检出、任何共享同一个 git 目录的检出——而不只是当前工作树。
3. **非票检出在判官结束时还槽。** 不在 `.worktrees/issue-<n>` 里的运行（主检出的 reverify、合并工作树、手动跑一次判官），判官结束就把它**自己占的**那个槽还掉；已经被别人占着的槽不动（mmw #373 补上的"别人的不动"这一条）。

## 哪些产物失效

- `.mmw/target.json` 的 `instance.max`：数值含义从"同时能起几套产品"变成"一晚最多几张票同时处于验收"。原来按前一种含义填的数字会让夜里的界面票排队。
- `.mmw/target.json` 的 `stop`：只停进程、不停容器的 `stop` 原来只是留下垃圾，现在会卡住下一个拿到这个槽的运行。
- ticket 的 `CHECK:`：自己起产品、不走 `start` 的判据，现在占的槽会一直留到票结束。

## 怎么迁

1. 按新含义重估 `instance.max`：问"一晚允许几张票同时在验收"，不是"机器能同时起几套"。story 判据不占槽（见 `373-truthful-ports-and-story-service.md`），不必为它留量。
2. 让 `stop` 真的停干净：`stop` 返回之后，本次租约的端口段（`MMW_PORT_BASE` 起 `MMW_PORT_COUNT` 个）上不许还有人监听，容器发布的端口也算。自查一条命令：

   ```
   python3 <drive-target scripts>/lease.py release <worktree> --stop
   ```

   还有监听者时它拒绝还槽，并点名端口、pid 和那个进程的目录。
3. 旅程脚本不许自己起任何东西，负控制那一遍尤其不许：`journey.py` 现在会在负控制之后再跑一次 `stop` 并检查端口，剩下的监听者让这次运行报 `JOURNEY LEFT THE PRODUCT UP`。
4. 手动起产品用 `lease.py run -- <start 命令>`，它的租约会留着；在同一个检出里跑判官不会再把它停掉。
