---
name: mmw-wayfinder
description: Plan a huge chunk of work — more than one agent session can hold — as a shared map of decision tickets on the issue tracker. Use when charting a loose idea into a map, or when claiming and resolving one decision ticket on an existing map, until the way to the destination is clear.
argument-hint: "[map number, ticket number, or the loose idea]"
---

This turn's input: `$ARGUMENTS`

A loose idea has arrived — too big for one agent session, and wrapped in fog: the way from here to the **destination** isn't visible yet. Wayfinding is about finding that way, not charging at the destination. This skill charts the way as a **shared map** on the repo's issue tracker, then works its **decision tickets** — questions whose resolution is a decision, not slices of a build to execute — one at a time until the route is clear.

The destination varies per effort, and naming it is the first act of charting — it shapes every ticket. It might be a spec to hand off and iterate on, a decision to lock before planning starts, or a change made in place like a data-structure migration. The map is domain-agnostic — engineering work, course content, whatever fits the shape.

## Plan, don't do

Wayfinder is **planning** by default: each ticket resolves a decision, and the map is done when the way is clear — nothing left to decide before someone goes and does the thing. The pull to just do the work is usually the signal you've reached the edge of the map and it's time to hand off. An effort can override this in its **Notes** — carrying execution into the map itself — but absent that, produce decisions, not deliverables.

## Refer by name

Every map and ticket is an issue, so it has a **name** — its title. In everything the human reads — narration, the map's Decisions so far — refer to it by that name, never by a bare id, number, or slug. A wall of `#42, #43, #44` is illegible; names read at a glance. The id and URL don't vanish — a name wraps its link — but they ride _inside_ the name, never stand in for it.

## The Map

The map is a single issue on this repo's issue tracker, labelled `wayfinder:map` — the canonical artifact. Its tickets are child issues of the map.

The map is an **index**, not a store. It lists the decisions made and points at the tickets that hold their detail; a decision lives in exactly one place — its ticket — so the map never restates it, only gists it and links.

Create, link, claim, frontier-query, and append through `mmw issue` in the invocation steps. Do not consult a separate tracker-operations doc.

### The map body

The whole map at low resolution, loaded once per session. Open tickets are **not** listed — they are open child issues, found by query.

```markdown
## Destination

<what reaching the end of this map looks like — the spec, decision, or change this effort is finding its way to. One or two lines; every session orients to it before choosing a ticket.>

## Branch

<full branch name of the charting session. The name segment is the substring after the last `/` in this value. Do not change it after the map is created.>

## Notes

<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [<closed ticket title>](link) — <one-line gist of the answer>

## Not yet specified

<!-- see "Fog of war": in-scope fog you can't ticket yet; graduates as the frontier advances -->

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed, never graduates -->
```

### Tickets

Each ticket is a **child issue** of the map; the tracker's issue id is its identity. Its body is the question, sized to one agent session:

```markdown
## Question

<the decision or investigation this ticket resolves>

## Required materials

<one artifact ref per line: `category=<category> name=<name-segment> [issue=<number>] [sub=<subpath>]`. Include `issue=` and `sub=` only when that artifact has them. One resolution comment per line: `issue=<number> resolution comment` — the comment on that issue that starts with `<!-- mmw:conclusion -->`. Write `none` when there are none.>
```

The session that charts the map writes the materials already known. The session that claims the ticket adds materials produced since.

Resolve a line `category=<category> name=<name-segment> [issue=<number>] [sub=<subpath>]` by running `mmw artifact path <category> --name <name-segment>` plus `--issue` / `--sub` when those keys are present. The command prints a path; then read that path's index and the files the index lists. Resolve `issue=<number> resolution comment` by reading that issue's comment that starts with `<!-- mmw:conclusion -->`.

When this ticket writes or reads artifacts, every `mmw artifact path` takes `--name` from the substring after the last `/` in `## Branch`, and `--issue <this ticket's number>`. The scope segment is `issue-<this ticket's number>`.

Each ticket carries a `wayfinder:<type>` label — one of `research`, `prototype`, `grilling`, `task` (see [Ticket Types](#ticket-types)).

A session **claims** a ticket **first**, before any work, so concurrent sessions skip it. Claim with `mmw issue claim <number>` — it assigns the ticket to the current tracker user. An open, unassigned ticket is unclaimed.

Blocking uses the tracker's **native** dependency relationship — essential because it renders the frontier _visually_ in the tracker's own UI, so the human sees what's takeable without opening the map. Wire it with `mmw issue link <blocked> --blocked-by <blocker>`. A ticket is **unblocked** when every ticket blocking it is closed; the **frontier** is the open, unblocked, unclaimed children — the edge of the known. Query it with `mmw issue frontier <map number> --label-prefix wayfinder:`.

The answer isn't part of the body — it's recorded on resolution (see [Work through the map](#work-through-the-map)). Put new artifacts in the [resolution comment](#resolution-comment) Artifact refs; do not paste their contents into the ticket body.

### Resolution comment

Later sessions do not have this conversation, so the resolution comment is the record they will read. `mmw artifact path` prints a path; write the comment body there, then post that file:

```bash
mmw artifact path scratch --name <map-branch-slug> --issue <number> --sub outbox/answer.md
```

`<map-branch-slug>` is the substring after the last `/` in `## Branch`. `<number>` is this ticket's id.

First line: `<!-- mmw:conclusion -->`. Then:

```markdown
## Answer

<every conclusion from this ticket, with reasons and figures. For a grilling ticket, transcribe the `## Shared understanding` section of the file `$mmw:mmw-grilling` just wrote via `mmw artifact path scratch --sub understanding.md`. For a research ticket, read the README `$mmw:mmw-research` returned, then the findings files it lists; write the conclusions from those files. For a prototype ticket, read the README `$mmw:mmw-prototype` returned, then the files it lists; write the walkthrough conclusions and the chosen artifact.>

## Artifact refs

<same lines as Required materials, for artifacts this ticket produced. `none` if none.>

## Materials used

<one line per Required materials entry: used or not, and why if not.>
```

Then post with GitHub CLI `gh`: `gh issue comment <number> --body-file <the path just printed>`, `gh issue close <number>`, and `mmw issue append <map number> --section "Decisions so far" --line "<ticket title wrapped around its issue URL> — <one-line gist>"`. `<map number>` is the map issue id (from create output when charting, or from the map you loaded when walking).

If `$mmw:mmw-domain-modeling` writes an ADR in this session, keep the filename `draft-<ticket-number>-<short-english-slug>.md` that it uses. Do not assign a numeric ADR id here.

## Ticket Types

Every ticket is either **HITL** — human in the loop, worked _with_ a human who speaks for themselves — or **AFK**, driven by the agent alone. A HITL ticket only resolves through that live exchange; the agent never stands in for the human's side of it (a grilling agent that answers its own questions has broken this).

- **Research** (AFK): Surface a fact a decision waits on — from this repo's source, or from docs, third-party APIs, or official specs. Resolved by `$mmw:mmw-research`. Use when the fact can be obtained by investigation without a human discussion. Invoke it with the ticket's Question, the map-branch slug as the name segment, and `issue-<number>` as the scope segment. A `wayfinder:research` ticket is the user's approval to save: `$mmw:mmw-research` saves without asking.
- **Prototype** (HITL): Raise the fidelity of the discussion by making a cheap, rough, concrete running artifact to react to, via `$mmw:mmw-prototype`. The first cut can be rough; the user walks it and iterates until the idea is sharp. Link the prototype as an asset. Use when "how should it look" or "how should it behave" is the key question, and talk alone cannot decide it.
- **Grilling** (HITL): Conversation. The default case. Invoke `$mmw:mmw-grilling`. It applies `$mmw:mmw-domain-modeling` in the same discussion.
- **Task** (HITL or AFK): Manual work that must happen before a _decision_ can be made — nothing to decide, prototype, or research, but the discussion is blocked until it's done. Signing up for a service so its API can be judged, provisioning access, moving data so its shape can be seen. This is the one type that _does_ rather than decides — and it earns its place by unblocking a decision, not by delivering the destination. The agent drives it alone where it can (AFK); otherwise it hands the human a precise checklist (HITL). Resolved when the work is done; the answer records what was done and any resulting facts (credentials location, new URLs, row counts) later tickets depend on.

## Fog of war

The map is _deliberately_ incomplete: don't chart what you can't yet see. Beyond the live tickets lies the **fog of war** — the dim view of decisions and investigations you can tell are coming but can't yet pin down, because they hang on questions still open. Resolving a ticket clears the fog ahead of it, graduating whatever's now specifiable into fresh tickets — one at a time, until the way to the destination is clear and no tickets remain.

The map's **Not yet specified** section is where that dim view is written down: the suspected question, the area to revisit later. It's the undiscovered frontier _toward_ the destination — everything here is in scope, just not sharp enough to ticket. Write as loosely or as fully as the view allows; it doubles as a signpost for collaborators reading where the effort is headed.

**Fog or ticket?** The test is whether you can state the question precisely now — _not_ whether you can answer it now.

- **Ticket when** the question is already sharp — even if it's blocked and you can't act on it yet.
- **Not yet specified when** you can't yet phrase it that sharply. Don't pre-slice the fog into ticket-sized pieces: it's coarser than a ticket, and one patch may graduate into several tickets, or none, once the frontier reaches it.

**Not yet specified** excludes what's already decided (Decisions so far), what's already a live ticket, and what's out of scope (the next section).

## Out of scope

Fog only ever gathers _toward_ the destination. The destination fixes the scope, so work beyond it is **out of scope** — it isn't fog, and it doesn't belong in **Not yet specified**. It gets its own **Out of scope** section on the map: work you've consciously ruled out of _this_ effort. Scope, not sharpness, lands it here.

Out-of-scope work never graduates — the frontier stops at the destination — so it returns only if the destination is redrawn, and then as a fresh effort, not a resumption.

Ruling something out of scope is a scoping act, not a step on the route. When a ticket that already exists turns out to sit past the destination — mis-scoped in while charting, or exposed by a resolution — **close it** (a closed ticket is unambiguously off the frontier) and leave one line in the **Out of scope** section: the gist plus why it's out of scope, linking the closed ticket. It stays out of **Decisions so far**, which records the route actually walked — a scope boundary isn't a step on it.

## Invocation

Two modes. Either way, **never resolve more than one ticket per session** — with the exception of research tickets during charting.

### Chart the map

User invokes with a loose idea. This session creates the map and fires research. It does not resolve HITL tickets.

Name this effort's task branch.

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>` with the task-branch name decided above |
| Task branch already there | None of the above holds | Use the current branch |


1. **Name the destination.** Run a `$mmw:mmw-grilling` session to pin down what this map is finding its way to — the spec, decision, or change. `$mmw:mmw-grilling` applies `$mmw:mmw-domain-modeling` in the same discussion. The destination fixes the scope, so it's settled first.
2. **Map the frontier.** Grill again, **breadth-first** this time: fan out across the whole space rather than deep on any one thread, surfacing the open decisions and the first steps takeable now. This round surfaces questions and fog; it does not settle answers. Stop when the space is fanned out. Do not chase the frontier empty. **If this surfaces no fog** — the way to the destination is already clear, the whole journey small enough for one session — you don't need a map. Stop and ask the user how they'd like to proceed.
3. **Create the map** (label `wayfinder:map`): Destination, Branch (this session's full task-branch name), and Notes filled in; Decisions so far empty; the fog sketched into **Not yet specified**. `mmw artifact path scratch --sub outbox/map-body.md` prints a path; write the body there. The map name is the issue title, taken from this effort. Then:

   ```bash
   mmw issue create --title "<map name>" --body-file <that path> --label wayfinder:map
   ```

   Keep the new issue id as `<map number>`.

4. **Create the tickets you can specify now** as child issues of the map — then wire blocking edges in a **second pass** (issues need ids before they can reference each other). Everything you can't yet specify stays in **Not yet specified**. Each body has `## Question` and `## Required materials`. For each ticket, `mmw artifact path scratch --sub outbox/ticket-<n>.md` prints a path (`<n>` is 1, 2, 3… in this pass); write the body there. The ticket name is the issue title, taken from that question. Then:

   ```bash
   mmw issue create --title "<ticket name>" --body-file <that path> \
     --parent <map number> --label wayfinder:<type>
   ```

   Keep each new id. Then one link per edge, using those ids:

   ```bash
   mmw issue link <blocked> --blocked-by <blocker>
   ```

5. **Fire research.** For each `wayfinder:research` ticket you just created, `mmw issue claim <number>`. Skip a ticket if that command exits non-zero. Invoke `$mmw:mmw-research` on each claimed ticket in the same turn: tell it this is a `wayfinder:research` ticket, and pass the Question, the name segment from `## Branch`, and `issue-<number>`. Each returns a README path. Wait until they all return, then record each as a [resolution comment](#resolution-comment). If a result makes fog specifiable, create those tickets (create-then-wire).
6. Stop — charting is one session's work; it hand-resolves nothing except the research tickets in step 5. Commit files this session wrote. Do not create an empty commit. Report the destination, the map name, the Branch value, and the names of the frontier tickets. Do not claim those tickets.

### Work through the map

User invokes with a map (URL or number). A ticket is **optional** — without one, you pick the next decision, not the user. This session resolves one decision ticket.

1. Load the **map** — the low-res view, not every ticket body. `gh issue view <map number>`. Note the title, `## Branch`, and skills named in Notes. Then `mmw issue frontier <map number> --label-prefix wayfinder:`.

   If the user named a ticket, `gh issue view <number> --json state,assignees,labels` and `mmw issue children <map number>`. Continue only when it is an open, unassigned, unblocked child of this map with a `wayfinder:` label. Otherwise report its actual state and stop.

   If the user named no ticket and the frontier is empty, the way is clear — stop. Do not resolve another ticket.

2. Choose the ticket. If the user named one, use it. Otherwise take the first line `mmw issue frontier` printed. **Claim it**: `mmw issue claim <number>` before any work. If that command exits non-zero, take the next frontier line. If every frontier ticket fails claim, report that and stop.

3. Resolve it. `gh issue view <number>` for the Question. Resolve [Required materials](#tickets). **Zoom as needed**: fetch the full body of any related or closed ticket on demand; invoke the skills the `## Notes` block names. Handle the ticket by its type under [Ticket Types](#ticket-types). If in doubt, use `$mmw:mmw-grilling`.

   After `$mmw:mmw-research` or `$mmw:mmw-prototype` returns, invoke `$mmw:mmw-domain-modeling` only when this result produced terms, bounded contexts, or an ADR-worthy decision. `$mmw:mmw-grilling` already applied it.

   A HITL `wayfinder:task` that needs the user: give the checklist and stop this step. Continue the same ticket when they return.

4. Record the resolution as a [resolution comment](#resolution-comment).
5. Add newly-surfaced tickets (create-then-wire); graduate any fog the answer has made specifiable, clearing each graduated patch from **Not yet specified** so it lives only as its new ticket. If an open ticket already asks that question, comment the newly-sharp part on that ticket instead of creating another, and do not claim it. If the answer reveals a ticket — this one or another — sits beyond the destination, **rule it out of scope** rather than resolving it on the route. If the decision invalidates other parts of the map, update or delete those tickets.

Commit files this session wrote. Do not create an empty commit.

The user may run unblocked tickets in parallel, so expect other sessions to be editing the tracker concurrently.
