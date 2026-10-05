### Resolve a map ticket

**You own one decision ticket of a map: claimed first, resolved by its type, recorded on the map, and the fog its answer clears turned into tickets.** One ticket per session: each ticket is sized to one session, and the map, not this session, is what the next session reads. The exception is research tickets, which a researcher session answers. What a map, a ticket, the fog and the out of scope are is the `wayfinder` skill; read it before step 1. Other sessions may be working other tickets of the same map at the same time, so read the map body fresh before every edit of it. Distinct from Chart a map, which creates the map, and from Work a ticket, which builds a ticket of a spec.

1. **Load the map.** Read the map body: the low-resolution view, not every ticket body. Read the `SKILL.md` of each skill its **Notes** names.
   Done when you know the destination, the decisions so far and the fog.
2. **Choose the ticket and claim it.** Take the ticket the owner named; otherwise the first ticket of the frontier query in the repository's `docs/agents/issue-tracker.md` `## Wayfinding operations`. Claim it before any other work: `gh issue edit <n> --add-assignee @me`.
   Done when the ticket carries your assignee.
3. **Resolve it by its type,** as the `wayfinder` skill's `## Ticket Types` says. Zoom as needed: fetch the full body of any related or closed ticket. For a `grilling` ticket, read the `grilling` and `domain-modeling` skills' `SKILL.md` and grill the owner; for a `prototype` ticket, read the `prototype` skill's `SKILL.md` and follow it, and the owner reacts to what it builds; for a `task` ticket, do the work, or hand the owner a precise checklist for what only they can do. A HITL ticket resolves only through the owner's own answers; never answer for them. For a `research` ticket, brief one researcher with `dispatch.sh brief researcher <file>`, the brief written from the `mmw-mode` skill's `references/map-research-brief.md`, and save, record and close it as Chart a map step 5 says when the wake comes; a research ticket does not count as this session's one ticket.
   Done when the ticket has its answer: the decision, the facts, or the work done.
4. **Record the resolution.** Post the answer as the ticket's resolution comment, close it, and append a context pointer (the ticket's name, linked, and a one-line gist) to the map's **Decisions so far**. A prototype's resolution names its leaf directory; a decision the owner made says so.
   Done when the ticket is closed with its resolution comment and its pointer is on the map.
5. **Move the frontier.** Create the tickets the answer has made statable, as child issues with their type labels, then wire their blocking edges; clear each patch of fog that graduated from **Not yet specified**. A ticket the answer shows to sit beyond the destination is ruled out of scope as the `wayfinder` skill's `## Out of scope` says, not resolved. A ticket the decision invalidated is updated or closed with a comment saying why.
   Done when the map's tickets, fog and out-of-scope lines all agree with the answer.
6. **Check whether the map is clear,** as the `wayfinder` skill's `## A clear map` says. When it is, the next move is a fresh session running Write a spec with this map as its reference; leave the map open.
   Done when you know whether the map is clear.

**Reply:** the ticket's name and its answer; the tickets it opened, closed or ruled out of scope, by name; the frontier now; and, when the map is clear, that the next move is Write a spec on this map in a fresh session.
