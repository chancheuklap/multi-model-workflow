# 341-origin-base-branch

## 改了什么

`advance`、`land` 与 `reverify` 不再以调用者 checkout 里的本机 base branch 为准。它们取回 `origin/<base branch>`，在每条 base branch 的常驻 detached merge worktree 里合并或重新验收；repository checks 收到 `MMW_BASE_REF=origin/<base branch>`。落地只 fast-forward 推送，冲突或红检查把票作为 `ticket.bounced` 交给 triage。

同时退役了两个 git config：`dispatch` 不再写 `branch.issue-<n>.mmw-base`（派发那一刻的 base commit）和 `branch.issue-<n>.mmw-base-branch`（base branch 名）。

## 哪些产物失效

- `.mmw/target.json` 的 `checks` 中写死本机 branch 名的命令失效：合并检查在 detached HEAD 上运行，本机同名 branch 可能落后 origin。
- ticket 的 `CHECK:` 中写死本机 branch 名的命令失效：worker worktree、merge worktree 与新 clone 不共享那条本机 branch 的位置或进度。
- ticket 的 `CHECK:` 中读 `branch.issue-<n>.mmw-base` 或 `branch.issue-<n>.mmw-base-branch` 的命令失效，而且是**假绿**：`git config --get` 什么都不打印并退出 1，命令退化成一条比较不了东西的命令——`git diff --name-only $(git config branch.issue-713.mmw-base)..HEAD -- <目录>` 变成 `git diff ..HEAD`，恒报没有改动，判据照样通过。`verify-ticket.py --lint` 现在对读这两个键的 `CHECK:` 报 ERROR（标记 `[retired-base]`）。

## 怎么迁

1. 把 `.mmw/target.json` 的 `checks` 与 ticket 的 `CHECK:` 中作为比较基线的本机 branch 名换成 `$MMW_BASE_REF`；流水线在需要它的 repository checks 与 reverify 中提供 `origin/<base branch>`。读 `mmw-base` 的写法一并换掉，diff 写成 `$MMW_BASE_REF...HEAD`。
2. 切换之前，把本机领先的 base branch 推到 GitHub；origin 从切换起成为唯一集成基线。
3. 用旧版 `advance` 把已经通过、尚未落地的票全部合掉，再安装或启用这次改动。
4. 确认每台会跑 worker 的电脑都有向这个 repository 推送 ticket branch 的权限。
5. 只在没有 open night 的时刻切换，避免同一批票一半走本机基线、一半走 origin 基线。
6. 切换时仍在运行的票，若其事件或 worktree 仍按旧基线建立，在切换后重新 `start`，让它从 origin 重新取得上下文。
