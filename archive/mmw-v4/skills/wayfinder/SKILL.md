---
name: wayfinder
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# wayfinder

| Work in hand | Read |
| --- | --- |
| A destination whose decisions exceed one session | [Chart the map](references/chart-the-map.md) |
| An existing map, with or without a named decision | [Work through the map](references/work-through-the-map.md) |

Chart a decision map or resolve its next decision. Each call returns the map or one resolution to its caller; keep the fresh-session boundary even when called from preparation. A cleared map returns its destination result, which may be only a decision.

A loose idea has arrived, too big for one agent session, and wrapped in fog: the way from here to the **destination** isn't visible yet. Wayfinding is about finding that way, not charging at the destination. Wayfinder charts the way as a **shared map** on the repo's issue tracker, then works its **decision tickets** (questions whose resolution is a decision, not slices of a build to execute) one at a time until the route is clear.

The destination varies per effort, and naming it is the first act of charting: it shapes every ticket. It might be a spec to hand off and iterate on, a decision to lock before planning starts, or a change made in place like a data-structure migration. The map is domain-agnostic: engineering work, course content, whatever fits the shape.

## Plan, don't do

Wayfinder is **planning** by default: each ticket resolves a decision, and the map is done when the way is clear, with nothing left to decide before someone goes and does the thing. The pull to just do the work is usually the signal you've reached the edge of the map and it's time to hand off. An effort can override this in its **Notes**, carrying execution into the map itself, but absent that, produce decisions, not deliverables.

## Refer by name

Every map and ticket is an issue, so it has a **name**: its title. In everything the human reads (narration, the map's Decisions-so-far), refer to it by that name, never by a bare id, number, or slug. A wall of `#42, #43, #44` is illegible; names read at a glance. The id and URL don't vanish; a name wraps its link, but they ride _inside_ the name, never stand in for it.

## The Map

The map is a single issue on this repo's issue tracker, labelled `wayfinder:map` and `mmw:map`, the canonical artifact. Its tickets are child issues of the map.

The map is an **index**, not a store. It lists the decisions made and points at the tickets that hold their detail; a decision lives in exactly one place, its ticket, so the map never restates it, only gists it and links.

The map, its child tickets, blocking, and frontier queries live on GitHub. Use the **GitHub operations** below for native relationships and whole-list reads.

### The map body

The whole map at low resolution, loaded once per session. Open tickets are **not** listed: they are open child issues, found by query.

```markdown
## Destination

<what reaching the end of this map looks like: the spec, decision, or change this effort is finding its way to. One or two lines; every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for this effort; the effort's directory name under `efforts/`>

## Decisions so far

<!-- the index: one line per closed ticket, enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [<closed ticket title>](link): <one-line gist of the answer>

## Not yet specified

<!-- see "Fog of war": in-scope fog you can't ticket yet; graduates as the frontier advances -->

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed, never graduates -->
```

### Tickets

Each ticket is a **child issue** of the map; the tracker's issue id is its identity. Its body is the question, sized to one 100K token agent session:

```markdown
## Question

<the decision or investigation this ticket resolves>
```

Each ticket carries a `wayfinder:<type>` label, one of `research`, `prototype`, `grilling`, `task` (see [Ticket Types](#ticket-types)). Besides the map's `mmw:map`, `wayfinder:` labels are the only labels a map and its tickets carry, never a triage label like `ready-for-agent`: they are decisions, not implementation work.

A session **claims** a ticket by assigning it to the dev driving the map, **first**, before any work, so concurrent sessions skip it. That assignee _is_ the claim: an open, unassigned ticket is unclaimed.

Blocking uses the tracker's **native** dependency relationship: essential because it renders the frontier _visually_ in the tracker's own UI, so the human sees what's takeable without opening the map. Only a tracker that lacks native blocking falls back to a body convention. A ticket is **unblocked** when every ticket blocking it is closed; the **frontier** is the open, unblocked, unclaimed children, the edge of the known.

The answer isn't part of the body; it's recorded on resolution (see `references/work-through-the-map.md`). Assets created while resolving a ticket are linked from the issue, not pasted in.

## Ticket Types

Every ticket is either **HITL** (human in the loop, worked _with_ a human who speaks for themselves) or **AFK**, driven by the agent alone. A HITL ticket only resolves through that live exchange; the agent never stands in for the human's side of it (a grilling agent that answers its own questions has broken this).

- **Research** (AFK): Reading the repo's code and history, documentation, third-party APIs, or local resources like knowledge bases to surface a fact a decision waits on. Resolved through the **Investigation** playbook: the ticket's question is its question, the map's destination and what its Decisions-so-far already settle are what you know, and the ticket's directory `efforts/<effort>/research/<ticket number>-<slug>/` (`<slug>` the question in a few lowercase English words joined by `-`) on the map's effort branch, which later sessions read with nothing else of this run, is where the researchers' answers are kept: send them `--into` it. The resolution comment is, with one researcher, its answer's `## Answer` and the path of its `brief-1.md`; with several, the `## Answer` you draw from theirs and the path of each `brief-<n>.md`; with none, your answer itself. Use when a decision waits on a fact, inside the repo or outside it.
- **Prototype** (HITL for the logic and UI branches, AFK for the experiment and sketch branches): Raise the fidelity of the discussion by making a cheap, rough, concrete artifact to react to (an outline, a rough take, a stub, or UI/logic code) with the **prototype** skill. Links the prototype as an asset. For a UI question, use the prototype skill's local UI branch through design freeze. Use when "how should it look" or "how should it behave" is the key question. When the question is how something should be implemented (which behavior, timing, or approach holds up), the prototype skill's experiment branch runs it against a bar set first, and the result decides, without the human. When the question is what shape the code should take, the prototype skill's sketch branch settles it by comparing candidate sketches, without the human.
- **Grilling** (HITL): Conversation. Run the Grill with docs playbook of the **mmw-mode** skill (`playbooks/grill-with-docs.md`). The resolution comment lists each decision the interview settled, one line each, and names every glossary term and ADR it wrote.
- **Task** (HITL or AFK): Manual work that must happen before a _decision_ can be made: nothing to decide, prototype, or research, but the discussion is blocked until it's done. Signing up for a service so its API can be judged, provisioning access, moving data so its shape can be seen. This is the one type that _does_ rather than decides, and it earns its place by unblocking a decision, not by delivering the destination. The agent drives it alone where it can (AFK); otherwise it hands the human a precise checklist (HITL). Resolved when the work is done; the answer records what was done and any resulting facts (credentials location, new URLs, row counts) later tickets depend on.

## Fog of war

The map is _deliberately_ incomplete: don't chart what you can't yet see. Beyond the live tickets lies the **fog of war**: the dim view of decisions and investigations you can tell are coming but can't yet pin down, because they hang on questions still open. Resolving a ticket clears the fog ahead of it, graduating whatever's now specifiable into fresh tickets, one at a time, until the way to the destination is clear and no tickets remain.

The map's **Not yet specified** section is where that dim view is written down: the suspected question, the area to revisit later. It's the undiscovered frontier _toward_ the destination: everything here is in scope, just not sharp enough to ticket. Write as loosely or as fully as the view allows; it doubles as a signpost for collaborators reading where the effort is headed.

**Fog or ticket?** The test is whether you can state the question precisely now, _not_ whether you can answer it now.

- **Ticket when** the question is already sharp, even if it's blocked and you can't act on it yet.
- **Not yet specified when** you can't yet phrase it that sharply. Don't pre-slice the fog into ticket-sized pieces: it's coarser than a ticket, and one patch may graduate into several tickets, or none, once the frontier reaches it.

**Not yet specified** excludes what's already decided (Decisions so far), what's already a live ticket, and what's out of scope (the next section).

## Out of scope

Fog only ever gathers _toward_ the destination. The destination fixes the scope, so work beyond it is **out of scope**: it isn't fog, and it doesn't belong in **Not yet specified**. It gets its own **Out of scope** section on the map: work you've consciously ruled out of _this_ effort. Scope, not sharpness, lands it here.

Out-of-scope work never graduates (the frontier stops at the destination), so it returns only if the destination is redrawn, and then as a fresh effort, not a resumption.

Ruling something out of scope is a scoping act, not a step on the route. When a ticket that already exists turns out to sit past the destination (mis-scoped in while charting, or exposed by a resolution), **close it** (a closed ticket is unambiguously off the frontier) and leave one line in the **Out of scope** section: the gist plus why it's out of scope, linking the closed ticket. It stays out of **Decisions so far**, which records the route actually walked; a scope boundary isn't a step on it.


## GitHub operations

- **Every list read is a whole list.** `gh issue list` stops at 30 without `--limit`, and a `gh api` list endpoint returns only its first page without `--paginate`. Both truncate in silence: the output carries no marker, so a half-read set reads exactly like a complete one. A spec's tickets, a map's children, a frontier and the `needs-triage` queue are sets, and an agent that cannot see a ticket treats it as absent. Pass `--limit 1000` to every `gh issue list`, and `--paginate` with `?per_page=100` to every `gh api` list.

The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map` and `mmw:map`, its body in the shape of **The map body** above. `gh issue create --label wayfinder:map --label mmw:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue using `gh issue create --parent <map>` or `gh issue edit <map> --add-sub-issue <child>`. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, using the blocker's database `id`, not its issue number. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh api --paginate "repos/<owner>/<repo>/issues/<map>/sub_issues?per_page=100"`, open only), drop any carrying `mmw:spec`, any with an open blocker (`issue_dependencies_summary.blocked_by > 0`) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far, then `gh issue edit <map> --add-sub-issue <t>` for each closed ticket `<t>` that pointer names whose `gh issue view <t> --json state,parent` shows no parent. A ticket with a parent keeps it, and an open ticket is not attached, so the map's frontier stays its own.

Read a referenced issue with its full body and comments. Create missing labels from the **verify-ticket** skill's `LABELS` table in `scripts/verify-ticket.py`; keep existing labels unchanged.
