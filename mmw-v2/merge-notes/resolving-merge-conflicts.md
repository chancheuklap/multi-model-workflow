# resolving-merge-conflicts

源目录：`mmw-v2/upstream/skills/engineering/resolving-merge-conflicts/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 值外面那对引号去掉。这个值里没有「冒号加空格」，`yaml.safe_load` 验过去掉引号后解析结果逐字不变，而不带引号是本仓 `description` 的常态。上游改这一行的内容 → 收上游，不带引号这一点保留，除非新值里含冒号加空格——那种值必须带引号，否则 YAML 把它当成一个 mapping，整份 frontmatter 解析失败 |
| frontmatter 的 `description` 与第 1 步 | #340 扩大 trigger：除了有 conflict markers 的 merge/rebase，还包括 ticket-base merge 干净完成、但 repository checks 由绿转红。上游改 trigger → 收上游措辞，这个 clean-merge case 保留 |
| 第 2、3 步 | clean merge 没有 hunk 可读：从新进 base 的 first-parent merge commits 找 sibling tickets，读 ticket、closeout 与 commit，再沿失败路径找交互；不要把任一边孤立处理。上游改 primary-source 或 resolve 步骤 → 收上游措辞，这条无 markers 的路径保留 |

### docs page

`mmw-v2/upstream/docs/engineering/resolving-merge-conflicts.md` 的 `What it does`、
`When to reach for it`、primary-source 段与 `It's working if` 同步说明 clean ticket-base
merge 的红检查路径。上游改这些段 → 收上游说明，并保留 ticket、closeout、merge
commits 三类 primary source。
