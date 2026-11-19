### Work through the map

**You own one ticket's resolution. Never resolve more than one ticket per session, with the exception of research tickets.**

The user gives a map (URL or number). A ticket is optional: without one, you pick the next decision, not the user. Read `../references/wayfinder.md` first. It holds the map body, the ticket format, and the ticket types every step below uses.

1. **Load the map**: the low-res view, not every ticket body. The map and its tickets are where the work stands (**principle-progress-is-what-the-record-says**). Done when you hold the map's frontier, blocked tickets and fog.
2. **Choose the ticket.** If the user named one, use it. Otherwise take the first frontier ticket in order. **Claim it**: assign it to yourself before any work. Done when it is assigned to you.
3. **Resolve it as the type its `wayfinder:<type>` label names**, per `## Ticket Types` in `../references/wayfinder.md`. Read the label, not just the body: the body never states the type. **Zoom as needed**: fetch the full body of any related or closed ticket on demand; use whichever skills the `## Notes` block names. If in doubt, the **grilling** skill and the **domain-modeling** skill. Done when the ticket's question has its answer.
4. **Record the resolution**: post the **resolution comment** the ticket's type names, **close** the issue, and **append a context pointer** to the map's Decisions-so-far, attaching each ticket it names as a child of the map as **Resolve** in `../references/github-issues.md` says. For a UI prototype ticket, name the winner prototype's commit in the resolution comment. Done when the ticket is closed with its comment and the map has its pointer.
5. **Add newly-surfaced tickets** (create-then-wire). When walking the API fake reveals a question that changes the interface, open a decision ticket on the map with the type that fits it. Graduate any fog the answer has made specifiable, clearing each graduated patch from **Not yet specified** so it lives only as its new ticket. If the answer reveals that a ticket (this one or another) sits beyond the destination, **rule it out of scope** rather than resolving it on the route. If the decision invalidates other parts of the map, update or delete those tickets. Done when the map shows every ticket and patch of fog the answer changed.

6. **Stop when the map is clear.** If no `wayfinder:` ticket of the map is still open and **Not yet specified** is empty, the map is clear; a spec already cut from it does not count. Stop and tell the user the next move: in a fresh session, run the To spec playbook (`playbooks/to-spec.md`) against this map, passing the map's full reference. Leave the map open: it stays this effort's index of decisions. Otherwise stop after this one ticket, and tell the user the next frontier ticket. Done when the user has the next move.

The user may run unblocked tickets in parallel, so expect other sessions to be editing the tracker concurrently.

**Reply:** the ticket resolved, by name, with its answer; the context pointer added; new tickets, graduated fog, and out-of-scope rulings, each by name; and, when the map is clear, the next move.
