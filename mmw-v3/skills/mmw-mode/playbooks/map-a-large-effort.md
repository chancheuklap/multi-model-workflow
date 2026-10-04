### Map a large effort

**You own the map, not the build.**

This playbook carries the `wayfinder` skill across sessions for a destination one session cannot hold, while research tickets run in sessions of their own. When the map clears, **it hands off, it doesn't build**: the next move is `playbooks/write-a-spec-and-tickets.md`, which collapses the map's linked decisions into a buildable plan. Building straight from the map skips that collapse and throws the linked detail away, so go straight to `playbooks/make-a-small-change.md` only when the effort turned out genuinely small.

**Where you are.** Take the first line whose fact holds. Read each fact from the tracker, the repository and the user's message, never from this session's memory.
- A closed `research` ticket of the map has no context pointer in Decisions-so-far → **Collect finished research**.
- The user's message names no map, and the tracker has no map for this effort → **Chart the map**.
- The map has an open child ticket, or **Not yet specified** is not empty → **Resolve one decision ticket at a time**.
- The map has no open child ticket and **Not yet specified** is empty → **Hand the clear map on**.
- Anything else → **Collect finished research**.

#### Steps

1. **Collect finished research.** Append a context pointer for each closed `research` ticket that Decisions-so-far does not list yet; research sessions close their tickets without editing the map, so their pointers are added here. Each pointer links the report file on the ticket's `research/<n>` branch, where its research session pushed it. Every session that advances the map does this first, so the map body keeps one writer. Merging a `research/<n>` branch into the base branch waits for the user's command; this playbook merges none. Then go on at the step **Where you are** names; with every pointer appended, its first line no longer holds.
   Done when every closed `research` ticket of the map has a context pointer in Decisions-so-far that links its report file.

2. **Chart the map.** Chart the map with the `wayfinder` skill's `### Chart the map`. A destination with a UI, or one that remakes an existing product, adds tickets: read `references/ui-and-remake-tickets.md`. Start a research session for each `research` ticket you just created, as `#### Research tickets` says; do not wait for any of them to report back. Charting ends the session, as the last step of that section says; the next session finds its place by **Where you are**.
   Done when the map is on the tracker with its Destination, its Notes and its wired tickets, and every `research` ticket it created has a research session started.

3. **Resolve one decision ticket at a time.** Work through the map with the `wayfinder` skill's `### Work through the map`. When the map has no open child ticket but **Not yet specified** is not empty, first graduate into tickets what you can now state precisely, as the `wayfinder` skill's `## Fog of war` says. First start a research session, as `#### Research tickets` says, for each open `research` ticket on the frontier: research tickets are not held to one at a time, and each session posts its own resolution comment and closes its ticket, and a later session appends its context pointer. Then claim one ticket of another type and resolve it. If the frontier is empty while `research` tickets assigned to the dev driving the map are still open, stop and tell the user their names, as `#### Research tickets` says. A ticket whose opening line names a skill (a design or an alignment ticket) is worked with that skill, as the map's `## Notes` say; any other `prototype` ticket, with the `prototype` skill.
   Done when every open `research` ticket on the frontier has a research session started, and the ticket you claimed is closed with its resolution comment and its context pointer, or no ticket of another type is on the frontier, or you have told the user the names of the open `research` tickets.

4. **Hand the clear map on.** If no child ticket of the map is still open and **Not yet specified** is empty, the map is clear. Stop and tell the user the next move: in a fresh session, run `playbooks/write-a-spec-and-tickets.md` against this map, passing the map's full reference. Leave the map open: it stays this effort's index of decisions.
   Done when the user has the map's full reference and the next move, and the map is still open.

#### Research tickets

A `research` ticket is resolved in a session of its own. Assign the ticket to the dev driving the map, so a session working through the map skips it, then run this skill's `bash scripts/dispatch.sh research <n>`. It starts a separate session in the worktree `.worktrees/research-<n>`, on the branch `research/<n>`, that resolves the ticket by `playbooks/research-a-question.md`: it pushes the report to that branch, posts the resolution comment and closes the ticket. Nothing wakes this session when it ends; **Collect finished research** picks up what it left.

A ticket that already has a `research/<n>` branch has had its session started, and running the command again starts a second session on the same ticket rather than refusing. So when the frontier is empty and `research` tickets assigned to the dev driving the map are still open, tell the user their names instead: each session may still be running, or may have stopped without closing its ticket. Once the user says one has stopped, running the command again starts it again on the same branch.

**Reply:** the map's decided and undecided tickets, by name; the open `research` tickets whose sessions have been started; the `research/<n>` branches not yet merged into the base branch.
