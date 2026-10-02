### Map a large effort

**You own the map, not the build.**

This playbook carries the `wayfinder` skill across sessions for a destination one session cannot hold, while research tickets run in sessions of their own. When the map clears, **it hands off, it doesn't build**: the next move is **Write a spec and tickets**, which collapses the map's linked decisions into a buildable plan. Building straight from the map skips that collapse and throws the linked detail away, so go straight to **Make a small change** only when the effort turned out genuinely small.

**Entry.**
- **Routed from mode `## Playbooks`.** Start where **Where you are** says.
- **Unattended.** This playbook runs with the user present. An unattended session that reaches it records the product question where its role records a decision (mode `## Autonomy`) and stops.

**Where you are.** Take the first line whose fact holds. Read each fact from the tracker, the repository and the user's message, never from this session's memory (**principle-resume-from-durable-state**).
- A closed `research` ticket of the map has no context pointer in Decisions-so-far → **Collect finished research**.
- The user's message names no map, and the tracker has no map for this effort → **Chart the map**.
- The map has an open child ticket, and every open child ticket of the map is a `research` ticket that already has a `research/<n>` branch → **Resolve one decision ticket at a time**.
- The map has an open child ticket, or **Not yet specified** is not empty → **Resolve one decision ticket at a time**.
- The map has no open child ticket and **Not yet specified** is empty → **Hand the clear map on**.
- Anything else → **Collect finished research**.

#### Steps

1. **Collect finished research.** Append a context pointer for each closed `research` ticket that Decisions-so-far does not list yet; research sessions close their tickets without editing the map, so their pointers are added here. Each pointer links the report file on the ticket's `research/<n>` branch, where its research session pushed it. Every session that advances the map does this first, so the map body keeps one writer (**principle-separate-before-serializing-shared-state**). Merging a `research/<n>` branch into the base branch waits for the user's command; this playbook merges none. Then go on at the step **Where you are** names; with every pointer appended, its first line no longer holds.
   Done when every closed `research` ticket of the map has a context pointer in Decisions-so-far that links its report file.

2. **Chart the map.** Chart the map with the `wayfinder` skill's `### Chart the map`. A destination with a UI, or one that remakes an existing product, adds tickets: read `references/ui-and-remake-tickets.md`. Assign each `research` ticket you just created to the dev driving the map, so a session working through the map skips it while its research session runs. For each `research` ticket you just created, run this skill's `bash scripts/dispatch.sh research <n>`: it starts a separate session that resolves the ticket with the `research` skill. This step is done once every `research` ticket has a session started; do not wait for any of them to report back. Charting ends the session, as the last step of that section says; the next session finds its place through **Where you are**.
   Done when the map is on the tracker with its Destination, its Notes and its wired tickets, and every `research` ticket it created has a research session started.

3. **Resolve one decision ticket at a time.** Work through the map with the `wayfinder` skill's `### Work through the map`. When the map has no open child ticket but **Not yet specified** is not empty, first graduate into tickets what you can now state precisely, as the `wayfinder` skill's `## Fog of war` says. Skip each open `research` ticket that already has a `research/<n>` branch: its research session has started, and this skill's `bash scripts/dispatch.sh research <n>` would start a second session on the same ticket rather than refuse. When the ticket you claimed is a `research` ticket, run this skill's `bash scripts/dispatch.sh research <n>` for it and stop there without recording a resolution: its research session posts the resolution comment and closes the ticket, and a later session appends its context pointer. If the frontier is empty while `research` tickets assigned to the dev driving the map are still open, stop and tell the user their names: each research session may still be running or may have stopped without closing its ticket, and once one has stopped, this skill's `bash scripts/dispatch.sh research <n>` starts it again. A design or alignment ticket goes through **Design a UI**, and any other `prototype` ticket through **Prototype**.
   Done when the ticket you claimed is closed with its resolution comment and its context pointer, or its research session has started, or you have told the user the names of the open `research` tickets.

4. **Hand the clear map on.** If no child ticket of the map is still open and **Not yet specified** is empty, the map is clear. Stop and tell the user the next move: in a fresh session, run **Write a spec and tickets** against this map, passing the map's full reference. Leave the map open: it stays this effort's index of decisions.
   Done when the user has the map's full reference and the next move, and the map is still open.

**Reply:** the map's decided and undecided tickets, by name; the `research` tickets whose sessions are still running; the `research/<n>` branches not yet merged into the base branch.
