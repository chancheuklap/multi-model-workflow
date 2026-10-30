# GitHub issues

Maps, specs and tickets live as GitHub issues. Use the `gh` CLI for all operations. The To spec (`../playbooks/to-spec.md`), Revising a spec (`../playbooks/revising-a-spec.md`), To tickets (`../playbooks/to-tickets.md`), Chart the map (`../playbooks/chart-the-map.md`) and Work through the map (`../playbooks/work-through-the-map.md`) playbooks take their `gh` commands from here.

## Conventions

- **Every list read is a whole list.** `gh issue list` stops at 30 without `--limit`, and a `gh api` list endpoint returns only its first page without `--paginate`. Both truncate in silence: the output carries no marker, so a half-read set reads exactly like a complete one. A spec's tickets, a map's children, a frontier and the `needs-triage` queue are sets, and an agent that cannot see a ticket treats it as absent. Pass `--limit 1000` to every `gh issue list`, and `--paginate` with `?per_page=100` to every `gh api` list.
- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**: `gh issue list --state open --limit 1000 --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Make an issue a sub-issue of a parent**: `gh issue create --parent <parent> ...`, or `gh issue edit <parent> --add-sub-issue <child>` afterwards (`gh` 2.94+). Older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>` (database id, as in **Blocking** below).
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). An issue is unblocked when every blocker is closed.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v`; `gh` does this automatically when run inside a clone.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

- **Rewrite an issue body**: `gh issue edit <number> --body-file <file>`.
- **List a parent's sub-issues**: `gh api --paginate "repos/<owner>/<repo>/issues/<parent>/sub_issues?per_page=100" --jq '.[] | {number, title, labels: [.labels[].name]}'`.
- **List an issue's open blockers**: `gh api --paginate "repos/<owner>/<repo>/issues/<n>/dependencies/blocked_by?per_page=100" --jq '.[] | select(.state == "open") | .number'`.

## Three label sets

Three sets, each answering one question, none standing in for another:

| Set | Answers | Labels |
| --- | --- | --- |
| Kind | what this issue is | `mmw:map` · `mmw:spec` · `mmw:ticket` · `mmw:child` · `mmw:lesson` · `mmw:problem` |
| Status | who owes the next step | no status label · `needs-triage` · `ready-for-agent` · `ready-for-human` · closed, with `wontfix` when the owner rejects it |
| Grade | which worker starts it | `junior-worker` · `senior-worker` |

Every MMW issue carries exactly one kind label. A `wayfinder:<type>` decision ticket carries none. Maps and specs use only open and closed, not the status labels.

A kind label puts an issue in no status. An open issue with no status label awaits processing by the machine. `needs-triage` means awaiting the owner's decision, and only the owner lets it leave. `ready-for-agent` with one grade label, or `ready-for-human`, means ready for work. An assignee marks work in progress. Closed ends the work, with `wontfix` when the owner rejects it.

Issues enter `needs-triage` when a session records a product problem, a worker opens a `decision` or `deferred` child, a retrospective proposes work, or a playbook hands back its plan. Tickets enter it when a worker hands them back, they bounce twice at night or once outside a night, `reverify` reopens them, or `land` cannot merge them. An orchestrator also puts a `contract` child there when no written authority settles it. A repaired problem that recurs enters it too. The owner's deferral leaves it there without expiry. The owner picks one, and the Session pickup playbook (`../playbooks/session-pickup.md`) takes it up. List them with `gh issue list --state open --label needs-triage --limit 1000 --json number,title,labels`.

The colour and description of every label are `LABELS` in the `verify-ticket` skill's `scripts/verify-ticket.py`, which creates a label the repository lacks the first time it puts one on. Before a `gh issue create --label` of your own, create a missing label from that table with `gh label create <name> --color <colour> --description "<description>"`. `gh issue create` fails outright on a missing label. Leave a label that already exists as it is.

## When a playbook says "publish"

Create a GitHub issue.

- **A spec**: `verify-ticket.py --publish --spec-body <file> --title "<title>"` of the `verify-ticket` skill, with `--map <map>` when the spec comes from a wayfinder map. It gives the spec `mmw:spec`, and with `--map` it publishes the spec as a sub-issue of the map; it prints the spec's number.
- **The tickets of a spec**: drafts, linted, then `verify-ticket.py <spec> --publish --drafts <dir>`, as the To tickets playbook (`../playbooks/to-tickets.md`) says.
- **A problem outside any spec**: opened by the first step of the playbook of its kind, as `ticket.md` `## Opening a ticket` says, with `mmw:problem` as its kind until the owner's Go. The ones whose plan is still being written or not yet handed back carry `mmw:problem` without `needs-triage`. List them with `gh issue list --state open --label mmw:problem --limit 1000 --json number,title,labels --jq '[.[] | select([.labels[].name] | any(. == "needs-triage") | not)]'`.

## When a playbook says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map` and `mmw:map`, its body in the shape of **The map body** in `wayfinder.md`. `gh issue create --label wayfinder:map --label mmw:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (see **Make an issue a sub-issue of a parent**). Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: as in **Blocking** above. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (**List a parent's sub-issues**, open only), drop any carrying `mmw:spec`, any with an open blocker (`issue_dependencies_summary.blocked_by > 0`) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far, then `gh issue edit <map> --add-sub-issue <t>` for each closed ticket `<t>` that pointer names whose `gh issue view <t> --json state,parent` shows no parent. A ticket with a parent keeps it, and an open ticket is not attached, so the map's frontier stays its own.
