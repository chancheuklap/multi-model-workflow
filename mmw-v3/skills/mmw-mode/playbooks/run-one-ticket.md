### Run one ticket

**You own one written ticket outside a night, as its orchestrator, from `open-ticket` to `land`; its worker is dispatched from here.** A ticket outside a night belongs to no spec, so no `advance` ever collects it: `land` is its whole ending. Distinct from Run a night, which runs a spec's batch from `open` to `finish`.

Commands of the `dispatch` skill's `dispatch.sh` are named bare below.

1. **Open the watch.** Run `dispatch.sh open-ticket <n>`. This session becomes the ticket's orchestrator; when the line it prints names a task board, hand its URL to the owner.
   Done when `open-ticket` exited 0.
2. **Start the worker.** From a checkout of the branch this ticket will merge into, which must exist on origin, run `dispatch.sh start <n> worker`, then end your turn.
   Done when `start` exited 0 and your turn has ended.
3. **Each time something wakes you,** do the `dispatch` skill's `## On waking`, then act on the event:
   - `#<n> ticket.passed` or `#<n> ticket.returned`: go to step 4.
   - `#<n> worker.lost`: the worker's session stopped. `dispatch.sh start <n> worker` starts another in the same workspace; it first commits tracked edits and pushes the ticket branch to origin.
   - `#<n> ticket.refused`: the worker refused to claim the ticket, and the event's `reason` says why. Fix that, then `dispatch.sh start <n> worker` again.
   - `#<n> child.opened`: a `fault` stopped the worker; fix what the child names, then `dispatch.sh resume <n> "<what you fixed>, then: continue"`. A `decision` is for the owner, and the worker carries on. A `contract` child is settled as Run a night's **Settling a contract child** says.
   - `relay.recovered since <time>`: nothing; later wakes carry the recovered events.
   - A `watchdog:` line or an `MMW turn guard:` line: act as Run a night's step 5 table says for it, reading the `verify-ticket` skill's `events.py fold <n>` where it says `status`.

   Done when the wake is acked and acted on, and your turn has ended unless step 4 is next.
4. **Land the ticket.** Once it passed or came back, run `dispatch.sh land <n>` from any checkout of this repository. It lands the ticket, closes the watch and prints what it did; stderr names anything it left standing. A merge conflict or red repository checks count as `bounced` on its summary line, and without an open night `land` leaves that ticket in `needs-triage`: tell the owner which ticket and what the `ticket.bounced` event names.
   Done when `land` exits 0.

**Reply:** what `land` did, and anything its stderr left standing.
