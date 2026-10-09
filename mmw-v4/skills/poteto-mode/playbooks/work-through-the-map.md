### Work through the map

**You own one ticket's resolution. Never resolve more than one ticket per session, with the exception of research tickets.**

The user gives a map (URL or number). A ticket is optional: without one, you pick the next decision, not the user. Read `../references/wayfinder.md` first. It holds the map body, the ticket format, and the ticket types every step below uses.

1. **Load the map**: the low-res view, not every ticket body.
2. **Choose the ticket.** If the user named one, use it. Otherwise take the first frontier ticket in order. **Claim it**: assign it to yourself before any work.
3. **Resolve it as the type its `wayfinder:<type>` label names**, per `## Ticket Types` in `../references/wayfinder.md`. Read the label, not just the body: the body never states the type. **Zoom as needed**: fetch the full body of any related or closed ticket on demand; use whichever skills the `## Notes` block names. If in doubt, the **grilling** skill and the **domain-modeling** skill.
4. **Record the resolution**: post the answer as a **resolution comment**, **close** the issue, and **append a context pointer** to the map's Decisions-so-far.
5. **Add newly-surfaced tickets** (create-then-wire); graduate any fog the answer has made specifiable, clearing each graduated patch from **Not yet specified** so it lives only as its new ticket. If the answer reveals that a ticket (this one or another) sits beyond the destination, **rule it out of scope** rather than resolving it on the route. If the decision invalidates other parts of the map, update or delete those tickets.

6. **Stop when the map is clear.** If no child ticket of the map is still open and **Not yet specified** is empty, the map is clear. Stop and tell the user the next move: in a fresh session, run the To spec playbook (`playbooks/to-spec.md`) against this map, passing the map's full reference. Leave the map open: it stays this effort's index of decisions.

The user may run unblocked tickets in parallel, so expect other sessions to be editing the tracker concurrently.

**Reply:** the ticket resolved, by name, with its answer; the context pointer added; new tickets, graduated fog, and out-of-scope rulings, each by name; and, when the map is clear, the next move.
