### Chart the map

**You own the map, not the answers. Charting resolves no ticket by hand.**

A loose idea too big for one agent session, with the way to the destination not yet visible. Read `../references/wayfinder.md` first. It holds the map body, the ticket format, and the ticket types every step below uses. Never resolve more than one ticket per session, with the exception of research tickets.

1. **Name the destination.** Use the **grilling** skill and the **domain-modeling** skill to pin down what this map is finding its way to: the spec, decision, or change. The destination fixes the scope, so it is settled with the user before you go on.
2. **Map the frontier.** Grill again, **breadth-first** this time: fan out across the whole space rather than deep on any one thread, surfacing the open decisions and the first steps takeable now. **If this surfaces no fog** (the way to the destination is already clear, the whole journey small enough for one session), you don't need a map. Stop and ask the user how they'd like to proceed.
3. **Create the map** (label `wayfinder:map`): Destination and Notes filled in, Decisions-so-far empty, the fog sketched into **Not yet specified**.
4. **Create the tickets you can specify now** as child issues of the map, then wire blocking edges in a **second pass** (issues need ids before they can reference each other). Write cross-references in that pass too, with real ids: a placeholder `#<n>` auto-links to an unrelated issue. Wiring sorts them into the frontier and the blocked; everything you can't yet specify stays in the fog: the **Not yet specified** section.
5. **Fire the research subagents.** For each `research` ticket you just created, spin up one subagent that runs the Investigation playbook (`playbooks/investigation.md`) to resolve it, in parallel. Not the **swarm** skill: each ticket keeps its own answer. Each subagent records its answer per Investigation's Research-ticket rule, comments on its own ticket, and closes it. Wait for all of them, then append their context pointers to the map's Decisions-so-far one at a time.
6. **Stop.** Charting is one session's work; it hand-resolves nothing.

**Reply:** the map and every ticket by name, which tickets sit on the frontier and which are blocked, the research tickets resolved with their gists, and what stays in Not yet specified.
