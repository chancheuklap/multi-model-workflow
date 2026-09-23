# Cutting something out of a ticket

`<engine>` is resolved in this skill's `SKILL.md`.

## When something has to leave this ticket

```bash
<engine> <n> --sub-issue <kind> <file>
```

`--sub-issue` takes a kind and a file whose first line is the child's title and whose rest is its body; it opens the child under this ticket and records it there.

## Which kind it is

Ask these questions in order. The first yes decides the kind.

| Order | Question | Kind | Not this kind |
| --- | --- | --- | --- |
| 1 | Is the pipeline itself broken: `verify-ticket.py`, `dispatch.sh`, a judge script, `lease.py`, a hook, `.mmw/target.json`? Or is the product unreachable, or waiting on a human step (rules 3 and 4 of the `ui-acceptance` skill's **Five rules while the product is running**)? | `fault` | A process you did not start that looks stuck: it is another run's, and you never end it (rule 1). |
| 2 | Does something this ticket was told to follow fail to hold: a baseline, a `## Parent` spec section or an acceptance criterion lacks a state, field or case, or contradicts another such source? | `contract` | Those sources are clear and this ticket's implementation is wrong; fix it in this ticket. |
| 3 | Do the sources say nothing, while multiple defensible readings would produce observably different outcomes? | `decision`, with the default taken | An internal name or data structure whose alternatives have no observable difference; decide it and record it in `DECISIONS`. |
| 4 | Is it a defect from the review report outside this ticket's `## Owns`? | `finding` | It is inside `## Owns`; fix it in this ticket. |
| 5 | Is it a merely convenient change outside `## Owns` that no criterion needs? | `deferred` | A criterion needs the change: make it, under the `implement` skill's bullet "For a file outside **Owns**" in `## Claim, read in, write the code`. |

## Exit codes

`0` the sub-issue is open and recorded. `1` the sub-issue is open and its `child.opened` event could not be written; stderr names it — do not open it again. `2` a refusal, with the reason on stderr.
