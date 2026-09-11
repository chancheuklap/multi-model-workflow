# 359-landed-ticket-branch-deleted

## 改了什么

一张票落地并归档 workspace 后，`dispatch.sh advance` 与 `dispatch.sh land` 会删除本机和 origin 上已经完全包含在 `origin/<base branch>` 里的 `issue-<n>`。

## 哪些产物失效

consuming repository 已有 ticket 的 `CHECK:` 如果把 `issue-<n>` 当作 git ref，落地后的 `reverify` 会找不到该 ref；判据因此失败，并可能让票记下 `ticket.regressed`。

## 怎么迁

把 `CHECK:` 中的 `issue-<n>` 换成不会随落地清理而消失的 ref：比较基线用运行时提供的 `$MMW_BASE_REF`，要核对已验收代码则用票上 `ticket.passed.commit` 的 commit id。
