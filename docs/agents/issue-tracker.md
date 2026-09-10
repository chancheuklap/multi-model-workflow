# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- **Every list read is a whole list.** `gh issue list` stops at 30 without `-L`, and a `gh api` list
  endpoint returns only its first page without `--paginate`. Both truncate in silence: the output
  carries no marker, so a half-read set reads exactly like a complete one. A spec's tickets, a map's
  children, a frontier and a morning queue are sets, and acting on part of a set is not a short answer
  but a wrong one — an agent that cannot see a ticket treats it as absent. Pass `-L <n>` above any count
  this repository can reach, or `--paginate` with `?per_page=100`, on every one of them. The tree
  under a map or a spec is the one set not read list by list: see **Reading a tree** below.
- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --limit 500 --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`
- **Re-parent**: `gh issue edit <number> --parent <parent>` attaches issue `<number>` under parent `<parent>`; `gh issue edit <number> --remove-parent` detaches it.
- **Transfer**: `gh issue transfer <number> <owner>/<repo>` moves the issue to another repository. The parent–child link breaks.

Infer the repo from `git remote -v` — `gh` does this automatically when run inside a clone.

## Reading a tree

The work is four layers deep — a map, its specs, each spec's tickets, each ticket's children —
joined by GitHub's sub-issue link. Read over REST that is one request per issue per layer, and a
page left unread raises no error. So the tree below an issue is read in one GraphQL query, by
`scripts/tree.py` of the `verify-ticket` skill (`python3 <that script> <issue> --root map|spec|ticket`,
default `spec`), which `status.py` and `verify-ticket.py --lint` use too. Each layer is read at a fixed
page size wherever the tree is entered: 50 specs under a map, 100 tickets under a spec (GitHub's own cap
on one issue's children), 50 children under a ticket; each issue comes back with its number, title and
state, and each issue with a layer below it with GitHub's `total` / `completed` count of that layer.
Entered at a map, that is 255,050 possible nodes against GitHub's limit of 500,000 per query; a
fourth list at 100 would ask for a million and GitHub refuses the query outright. `tree.py` exits 2,
and answers nothing, when any list comes back shorter than the count GitHub gives for it, or the
answer carries `errors`.

## Three label sets

Three sets, each answering one question, none standing in for another:

| Set | Answers | Labels |
| --- | --- | --- |
| Layer | which layer of the tree this issue is | `mmw:map` · `mmw:spec` · `mmw:ticket` · `mmw:child` |
| Queue | who it is waiting on | `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix` ([triage-labels.md](triage-labels.md)) |
| Grade | which worker row starts it | `junior-worker` · `senior-worker` |

The layer labels, with the colour and description a repository that lacks one creates it with
(`gh label create <name> --color <colour> --description "<description>"`):

| Label | Colour | Description | Put on by |
| --- | --- | --- | --- |
| `mmw:map` | `5319e7` | MMW layer: the map one discussion opened | the wayfinder skill, creating the map |
| `mmw:spec` | `1d76db` | MMW layer: a spec, the container of one batch of tickets | the to-spec skill, publishing the spec |
| `mmw:ticket` | `0e8a16` | MMW layer: a ticket, one unit of work | the to-tickets skill, publishing each ticket; `dispatch.sh route … became-ticket` |
| `mmw:child` | `c5def5` | MMW layer: a child issue a ticket opened | `verify-ticket.py --sub-issue` |

A layer label puts an issue in no queue. The layer label tells a board which layer an issue is; the
parent link tells the scripts which spec a ticket sits under — `verify-ticket.py` takes a ticket's
spec to be its direct parent and never walks further up. So a child that becomes a ticket changes
both: its label goes from `mmw:child` to `mmw:ticket`, and its parent moves from the ticket it came
from to that ticket's spec (`dispatch.sh route <child> became-ticket <ticket>` does both). Where it
came from stays on the record as the `child.closed` event on the original ticket.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; the triage skill reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either — resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding operations

Used by the wayfinder skill. The **map** is a single issue whose children are **decision tickets**.

- **Map**: a single issue labelled `wayfinder:map` and `mmw:map`, holding the Destination / Notes / Decisions-so-far / Not yet specified body. `gh issue create --label wayfinder:map --label mmw:map`.
- **Decision ticket**: an issue linked to the map as a GitHub sub-issue (`gh api --paginate repos/<owner>/<repo>/issues/<map>/sub_issues?per_page=100`). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child's body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket carries an assignee.
- **Blocking link**: GitHub's **native issue dependencies** — the canonical, UI-visible representation. Add one with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only — the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the blocked ticket's body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh issue list --state open --limit 500`, scoped to the map's sub-issues / task list read with `--paginate`), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins. This query serves the wayfinder skill's maps; the night's frontier is a different one, defined in `mmw-v2/skills/dispatch/scripts/status.py`.
- **Claim**: `gh issue edit <n> --add-assignee @me` — the session's first write.
- **Resolution**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.

## Morning queries

Two lists, in this order:

- `gh issue list --state open --limit 500 --label needs-triage` — what fell over in the night. Run the triage skill over it before anything else.
- `gh issue list --state open --limit 500 --label ready-for-human` — what only the user can do.
