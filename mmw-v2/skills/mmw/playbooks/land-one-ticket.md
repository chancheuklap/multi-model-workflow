### Land one ticket

**You own one ticket's ending: `land <n>` is its whole ending.**

You are starting one worker on one ticket, with no batch behind it. A ticket outside a night belongs to no spec, so no `advance` will ever collect it. While the worker holds the ticket, its code is the worker's: you change what it works from and tell it through `resume`, never its worktree or branch.

Commands of this skill's `bash scripts/dispatch.sh` are named bare below.

**Entry.**
- **Asked for one ticket.** The user asks for one worker on one ticket, outside any night: start at **Open the ticket's watch**.
- **Woken.** Go to the step the wake's pointer names, after mode `## Re-entry`.
- **Compacted, or unsure.** **Where you are.**

**Where you are.** Run `dispatch.sh where <n>` and go to the step it prints.

#### Steps

1. **Open the ticket's watch.** `bash scripts/dispatch.sh open-ticket-watch <n>`: this session becomes the ticket's orchestrator, and the line it prints carries the task board's URL; hand it to the user.
   Done when `open-ticket-watch` has exited 0 and the user has the task board URL, or the stderr line saying the board did not start.

2. **Start the worker, then end your turn.** `bash scripts/dispatch.sh start <n> worker`, from a checkout of the branch this ticket will merge into, which must exist on origin. Then end your turn (**principle-agents-are-woken-not-polled**).
   Done when `start` has exited 0 and you have ended your turn.

3. **Handle each wake.** You are woken with `#<n> ticket.passed` or `#<n> ticket.returned`, or with another wake. Do mode `## Re-entry` up to and including **Ack the wake**, then do what the One-ticket orchestrator column of `references/orchestrator-wakes.md` says for the wake. On `ticket.passed` or `ticket.returned` go to **Land**; after any other wake, end your turn. A decision nobody is there to make is recorded as `#### Unattended outlets` says.
   Done when the wake is handled and you have gone to **Land** or ended your turn.

4. **Land.** Once the ticket passed or came back, run `bash scripts/dispatch.sh land <n>` from any checkout of this repository. It lands the ticket, closes the watch and prints what it did; stderr names anything it left standing. A merge conflict or red repository checks count as `bounced` on its summary line, and without an open night `land` leaves that ticket in `needs-triage`: tell the user which ticket and what the `ticket.bounced` event names.
   Done when `land` exits 0.

#### Unattended outlets

With nobody to ask, write each decision you take, each `skip:` line of your todolist and each principle that changed a decision into one comment on this ticket: a ticket outside a night has no spec of this run, and the ticket is where the morning reader will look.

**Reply:** `land` exiting 0 and the line it printed, naming the ticket it landed and the watch it closed, with anything stderr named that it left standing.
