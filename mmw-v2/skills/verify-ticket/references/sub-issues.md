# Cutting something out of a ticket

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## When something has to leave this ticket

```bash
<engine> <n> --sub-issue <kind> <file>
```

`--sub-issue` takes a kind and a file whose first line is the title. It opens a new issue labelled `needs-triage` and `mmw:child` (the layer label; the repository's first child creates it), parented to this ticket, whose body opens with the line ``A `<kind>` child of #<n>.``, and posts a `child.opened` event on this ticket naming the new issue and its kind — the ticket's events are where its children are counted.

## Which kind it is

Ask these questions in order. The first yes decides the kind.

| Order | Question | Kind | Not this kind |
| --- | --- | --- | --- |
| 1 | Is the pipeline itself broken: a script, hook, driver or the target contract? | `fault` | A stale product process occupies a port and can be removed as an environment repair. |
| 2 | Does something this ticket was told to follow fail to hold: a baseline, a `## Parent` spec section or an acceptance criterion lacks a state, field or case, or contradicts another such source? | `contract` | Those sources are clear and this ticket's implementation is wrong; fix it in this ticket. |
| 3 | Do the sources say nothing, while multiple defensible readings would produce observably different outcomes? | `decision`, with the default taken | An internal name or data structure whose alternatives have no observable difference; decide it and record it in `DECISIONS`. |
| 4 | Is it a defect from the review report outside this ticket's `## Owns`? | `finding` | It is inside `## Owns`; fix it in this ticket. |
| 5 | Is it a merely convenient change outside `## Owns` that no criterion needs? | `deferred` | A criterion cannot pass without it; make the change and list it under `Outside Owns`, unless the file is in the `## Owns` of a ticket that can run beside this one: then it is `contract`, and the file is left alone. |

A file outside `## Owns` follows one rule, the one the `to-tickets` skill's step 5 cuts a batch by: no two tickets that can run at the same time write the same file. Two tickets can run at the same time when neither blocks the other, directly or down a chain. A shared file several tickets need, a shared stylesheet for one, is owned by one ticket, and every other ticket that needs it is blocked by that one. So a file owned by a ticket this one waits on, or by one that waits on this one, may be changed when a criterion needs it; `--touched` tells its owner. A file owned by a ticket that can run beside this one is the batch's cut missing an edge: open a `contract` child that names the file and the criterion that needs it, and do not edit the file.

A kind is named for who can answer the child, not for where it came from:

| Kind | Who opens it | What it records | Where it goes next |
| --- | --- | --- | --- |
| `finding` | the worker, from the review comment | the review found a defect that does not fall inside this ticket's scope | the closing pass of the night: fixed by the main agent, closed as no longer true, or made a ticket |
| `contract` | the worker | something this ticket was told to follow does not hold: a baseline under `## Read first`, a spec section named by `## Parent`, or an acceptance criterion lacks a state, field or case, or contradicts another such source; or a criterion needs a file that a ticket able to run beside this one owns. Its body quotes what does not hold and states what in the same source still holds and must be preserved | back to whoever wrote the failing layer; never changed quietly and worked on |
| `deferred` | the worker | work outside `## Owns` seen here that was merely convenient to change, and left alone on purpose | a later ticket. A change a criterion cannot pass without is made and listed under `Outside Owns`, not opened here, unless a ticket that can run beside this one owns the file (question 5) |
| `decision` | the worker | a choice only a person can make; the worker carries on with the default | the user |
| `fault` | the worker or the main agent | the pipeline itself is broken — a script, a hook, the driver, the target contract | the user, to fix the pipeline. The agent that opens it stops where it is |

An empty file, or a kind that is not one of the five, is refused and nothing is opened. A repository that lacks the `mmw:child` label and will not let it be created is refused the same way. `fault` is the one kind that brings the ticket to rest. This run tells nobody: the relay of the `dispatch` skill reads the `child.opened` on the ticket and wakes the main agent with `#<n> child.opened` for a `contract`, `fault` or `decision`.

A reviewer opens no `fault`. The worker that started it is asleep until its report lands on the ticket, and a `child.opened` wakes only the main agent, so a reviewer that stopped after opening one would leave that worker asleep. It reports the failure through its review report, which wakes the worker.

## Exit codes

`0` the sub-issue is open and recorded. `1` the sub-issue is open and its `child.opened` event could not be written; stderr names it — do not open it again. `2` a refusal, with the reason on stderr.
