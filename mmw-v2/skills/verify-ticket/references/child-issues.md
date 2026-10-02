# Cutting something out of a ticket

## Which kind it is

Ask **the kind questions** in order. The first yes decides the kind.

| Order | Question | Kind | Not this kind |
| --- | --- | --- | --- |
| 1 | Is the pipeline itself broken: `verify-ticket.py`, `dispatch.sh`, an oracle script, `lease.py`, a hook, `.mmw/target.json`? Or is the product unreachable, or waiting on a human step (the `ui-acceptance` skill's `## Five rules while the product is running`)? | `fault` | A process you did not start that looks stuck: it is another run's, and you never end it. |
| 2 | Does something this ticket was told to follow fail to hold: a baseline, a `## Parent` spec section or an acceptance criterion lacks a state, field or case, or contradicts another such source? | `contract` | Those sources are clear and this ticket's implementation is wrong; fix it in this ticket. |
| 3 | Do the sources say nothing, while multiple defensible readings would produce observably different outcomes? | `decision`, with the default taken | An internal name or data structure whose alternatives have no observable difference; decide it and record it in `DECISIONS`. |
| 4 | Is it a defect from the review report outside this ticket's `## Owns`? | `finding` | It is inside `## Owns`; fix it in this ticket. |
| 5 | Is it a merely convenient change outside `## Owns` that no criterion needs? | `deferred` | A criterion needs the change: make it, and it lands under `Outside Owns:` in the closing comment. |
