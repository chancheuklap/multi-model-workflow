# One ticket, outside a night

You are starting one worker on one ticket, with no batch behind it. A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending. Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md); what you do on a wake is `## On waking` there.

Four steps:

1. `<dispatch> open-ticket <n>`: this session becomes the ticket's main agent, and the line it prints ends with the task board's URL; hand it to the user.
2. `<dispatch> start <n> worker`, from a checkout of the branch this ticket will merge into, which must exist on origin. Then end your turn.
3. You are woken with `#<n> ticket.passed` or `#<n> ticket.returned`, or with one of the four below. Read that event on the ticket and `<dispatch> ack <n> <that event>`, then act on it.
   - `#<n> worker.lost`: the worker's session stopped. `<dispatch> start <n> worker` starts another in the same workspace; it first commits tracked edits and pushes the ticket branch to origin.
   - `#<n> ticket.refused`: the worker refused to claim the ticket, and the event's `reason` says why. Fix that, then `<dispatch> start <n> worker` again.
   - `#<n> child.opened`: a `fault` stopped the worker — fix what the child names, then `<dispatch> resume <n> "<what you fixed>, then: continue"`; a `decision` is for the user, and the worker carries on.
   - `#<n> child.opened` of kind `contract`, a `watchdog:` line, or an `MMW turn guard:` line: act as [night.md](night.md) under **3. Each time something wakes you** says for it, reading `python3 <events.py> fold <n>` where it says `status`. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Once the ticket passed or came back, run `<dispatch> land <n>` from any checkout of this repository. It lands the ticket, closes the watch and prints what it did; stderr names anything it left standing. Done when `land` exits 0. A merge conflict or red repository checks count as `bounced` on its summary line, and without an open night `land` leaves that ticket in `needs-triage`: tell the user which ticket and what the `ticket.bounced` event names.
