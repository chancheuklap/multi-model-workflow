# resolving-merge-conflicts

源目录：`mmw-v2/upstream/skills/engineering/resolving-merge-conflicts/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` 与第 1 步 | #340 扩大 trigger：除了有 conflict markers 的 merge/rebase，还包括一次 clean merge 让 repository checks 由绿转红。上游改 trigger → 收上游措辞，这个 clean-merge case 保留 |
| 第 2、3 步 | `origin/<base branch>` 的 clean merge 没有 hunk 可读：从 first-parent merge commits 找这次合进来的 tickets，读 ticket、closeout 与 commit，再沿失败路径找交互；不要把任一边孤立处理。上游改 primary-source 或 resolve 步骤 → 收上游措辞，这条无 markers 的路径保留；原有的 `check the PRs` 保留 |

### docs page

`mmw-v2/upstream/docs/engineering/resolving-merge-conflicts.md` 的 `What it does`、
`When to reach for it`、primary-source 段与 `It's working if` 同步说明 `origin/<base branch>`
clean merge 的红检查路径。上游改这些段 → 收上游说明，并保留 ticket、closeout、merge
commits 三类 primary source。
