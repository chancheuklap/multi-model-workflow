# Issue tracker pipeline sections

For a repository whose tracker is GitHub Issues, once the `setup-matt-pocock-skills` skill has written its `docs/agents/issue-tracker.md`: what the landing pipeline needs in that file beyond what the skill's seed writes. Add `## Three label sets` below to that file, after its `## Conventions` section. In that file's `## Wayfinding operations`, replace the **Map** and **Frontier query** lines with the two lines under the same heading below.

## Three label sets

Three sets, each answering one question, none standing in for another:

| Set | Answers | Labels |
| --- | --- | --- |
| Layer | which layer of the tree this issue is | `mmw:map` · `mmw:spec` · `mmw:ticket` · `mmw:child` |
| Queue | who it is waiting on | `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix` (`triage-labels.md`) |
| Grade | which worker row starts it | `junior-worker` · `senior-worker` |

The layer labels, put on by:

| Label | Put on by |
| --- | --- |
| `mmw:map` | the wayfinder skill, creating the map |
| `mmw:spec` | the to-spec skill, publishing the spec |
| `mmw:ticket` | the to-tickets skill, publishing each ticket; `dispatch.sh route … became-ticket` |
| `mmw:child` | `verify-ticket.py --sub-issue` |

A repository missing one of the labels above, or a queue or grade label, has it created the first time the `verify-ticket` skill's `--publish` or `--sub-issue` needs it; the colour and description for all three sets are defined once, in `verify-ticket.py`.

A layer label puts an issue in no queue.

## Wayfinding operations

- **Map**: a single issue labelled `wayfinder:map` and `mmw:map`, holding the map body the `wayfinder` skill writes. `gh issue create --label wayfinder:map --label mmw:map`.
- **Frontier query**: list the map's open children (`gh issue list --state open --limit 500`, scoped to the map's sub-issues / task list read with `--paginate`), drop any carrying `mmw:spec`, any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
