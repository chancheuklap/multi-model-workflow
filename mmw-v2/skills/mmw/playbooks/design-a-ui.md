### Design a UI

**The user owns how it looks.**

A design package says what the UI looks like and what it says. The backend decisions, a wayfinder map's or a conversation's, say what the system does. Nothing in between says which control calls what, or which story page each design page is. This playbook takes a UI from its Claude Design project to a design package in the repository and a screen contract that ties the package to those decisions, and the spec and every worker of the night then copy the two as they stand (**principle-the-baseline-is-a-contract**). The temptation is to write the spec once the pages look right; a spec written around a row whose `gap` is not `aligned` has the night build a decision nobody has made.

**Entry.**
- **A UI to design.** A winning variant from **Prototype**, a design ticket on a map, or an existing product to redraw starts at **Set up the Claude Design project**.
- **Comments queued.** Comments the user sent to Claude on a Claude Design project start at **Act on queued comments**.
- **Signed off.** A design the user has signed off, or has changed in Claude Design after sign-off, starts at **Pull the signed-off design**.
- **A `contract` child.** A `contract` child whose body names the `design-pages` skill's `references/pull.md` starts at **Pull the signed-off design** and ends as `#### A contract child answered by a pull` says.
- **Screen contract to write.** A pulled design package with no screen contract yet, or an alignment ticket on a map, starts at **Write the screen contract**.
- **Unattended.** This playbook runs with the user present. An unattended session that reaches it records the product question where its role records a decision (mode `## Autonomy`) and stops.

#### Steps

1. **Set up the Claude Design project.** Create or check the project with the `design-pages` skill's `references/set-up-and-sign-off.md`. Only a session whose host has the Claude Design tools can do this work; when the `design-pages` skill stops because this host has none, tell the user to run `/handoff` to move the work to a host that has them, and stop.
   Done when the user has the project's link and has been told to say `开始` there, or has been told to run `/handoff`.
2. **Act on queued comments.** Act on the comments the user sent to Claude with the `design-pages` skill's `references/draw.md` `## Comments`, each time the user queues more, until the user says the design is signed off.
   Done when no comment on the project is still queued for Claude, and the user has said the design is signed off.
3. **Pull the signed-off design.** Pull the project into the repository with the `design-pages` skill's `references/pull.md`; a design fix the report names goes back to Claude Design as its **Design problems in the report** says. A pull is two tool calls and one command, and its report is the convention check: when you doubt the pages hold the conventions, pull and read the report rather than reading pages by hand. After the first pull, take the prototype's scaffolding down as its **After the first pull** says.
   Done when the design package and its `pull-report.md` are committed together, the report names no design fix, and nothing outside the leaf directories imports the prototype's variants.
4. **Write the screen contract.** Pick the branch by `#### Change classes`: it decides whether the `write-screen-contract` skill runs on this pull, and how. A pull made for a design ticket on a wayfinder map writes no screen contract: `#### A pull made for a wayfinder design ticket`.
   Done when the branch `#### Change classes` names has run to its end: the screen contract lints clean and the user has answered every entry of its gap list, or, for `只改外观或文案`, the commit is pushed where that branch says.
5. **Stop on unaligned rows.** Read the `gap` of every row of the screen contract before anything is written from it. Stop at any row whose `gap` is not `aligned`: on a wayfinder map, send the effort back to its alignment ticket; with no map, go back to the `write-screen-contract` skill's **Reverse sweep** and then **Write the gap list and stop for the user**, where the user settles each unaligned row.
   Done when every row's `gap` is `aligned`, or the effort is back at its alignment ticket.
6. **Back to the spec.** On a wayfinder map, `#### A pull made for a wayfinder design ticket` says where the session goes. Otherwise hand the aligned screen contract on by how this run wrote it:
   - A screen contract written for the first time: **Write the spec** in **Write a spec and tickets**, which writes the spec this effort does not have yet.
   - A screen contract changed by the `write-screen-contract` skill's **Re-runs**: the `to-spec` skill's `references/revising-a-spec.md`, with the tickets already cut corrected against the new text.
   Done when the screen contract is committed and the session has gone on to the step or reference its case names, or back to the map's ticket.

#### Change classes

For a pull not made for a wayfinder map's design ticket, whether the effort's screen contract `docs/specs/<effort>/screen-contract.yaml` exists, and then `改动分类` in the pull report, decide which skill this run hands to; there is no default:

- **No screen contract yet**, whatever `改动分类` says: the `write-screen-contract` skill, for the whole screen contract.
- **增删控件或改流转**: the `write-screen-contract` skill at its **Re-runs** section, which edits only the rows those controls belong to.
- **只改外观或文案**: the screen contract does not change, because no `data-ui` id did. An open ticket picks up the new package on its next run. Landed tickets are re-run by this skill's `bash scripts/dispatch.sh reverify <spec>` on `origin/<base branch>`, which reopens a red one into triage with `ticket.regressed`; that reopened ticket is the correction. Until the night's `finish`, push the commit to `origin/<base branch>`: while the night is open, its closing pass runs `reverify`; after its `close-night`, run `reverify <spec>` from this session. After `finish` the base branch is gone: push to the project branch the night merged into, and tell the user that the spec's landed tickets were not re-run against the new package.

#### A pull made for a wayfinder design ticket

A pull made for a wayfinder map's design ticket ends at that ticket: once the `design-pages` skill's `references/pull.md` **Design problems in the report** lets it close, return to **Resolve one decision ticket at a time** in **Map a large effort** to record the resolution. The screen contract is the alignment ticket's.

A screen contract written for a wayfinder map's alignment ticket resolves that ticket: return to **Resolve one decision ticket at a time** in **Map a large effort** to record the resolution; the spec is written once the map is clear, as **Hand the clear map on** in **Map a large effort** says.

#### A contract child answered by a pull

When the pull answered a `contract` child, finish it after the package is committed and pushed to `origin/<base branch>` and **Write the screen contract** has run, with this skill's `dispatch.sh`: comment on the child with the commit; `dispatch.sh resolve-child <n> <child> fixed`; move the not-yet-started tickets the night moved to `needs-triage` back to `ready-for-agent`; `dispatch.sh resume <n> "<the commit to integrate from>, then: continue"`. The worker then runs its criteria on the new package.

**Reply:** the design package's directory and the commit that holds it; the screen contract's row count and the rows whose `gap` is not `aligned`; the step, reference or map ticket the work went to next.
