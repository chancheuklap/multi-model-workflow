# resolving-merge-conflicts

源目录：`mmw-v2/upstream/skills/engineering/resolving-merge-conflicts/`

## 逐段意图

### SKILL.md

下表登记 `SKILL.md` 与上游原文不同的所有段落；表外的段落是上游原文。

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` 与第 1 步 | #340 扩大 trigger：除了有 conflict markers 的 merge/rebase，还包括一次 clean merge 让 repository checks 由绿转红。上游改 trigger → 收上游措辞，这个 clean-merge case 保留 |
| 第 2、3 步 | 保留的是第 2 步的「or failing interaction」、第 3 步的标题「Resolve each hunk or interaction」与「With no conflict markers, trace the failing path across the merged tickets rather than treating either side in isolation.」一句。第 2 步原来的末句「After a clean merge of `origin/<base branch>`, identify each ticket …」→ `mmw-v2/skills/mmw/playbooks/work-a-ticket.md` `#### Integrating`（spec #597 第 6 节）。上游改 primary-source 或 resolve 步骤 → 收上游措辞，这三处保留 |

### docs page

`mmw-v2/upstream/docs/engineering/resolving-merge-conflicts.md` 的 `What it does`、
`When to reach for it`、primary-source 段与 `It's working if` 同步说明 `origin/<base branch>`
clean merge 的红检查路径。上游改这些段 → 收上游说明，并保留 ticket、closeout、merge
commits 三类 primary source。
