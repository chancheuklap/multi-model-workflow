# Cutting something out of a ticket

## Resolve `<engine>` once

`<engine>` is `scripts/verify-ticket.py`, resolved from this skill's own `SKILL.md` the way its **Resolve `<engine>` once** section says.

## When something has to leave this ticket

```bash
<engine> <n> --sub-issue <kind> <file>
```

`--sub-issue` takes a kind and a file whose first line is the title. It opens a new issue labelled `needs-triage` and `mmw:child` (the layer label; the repository's first child creates it), parented to this ticket, whose body opens with the line ``A `<kind>` child of #<n>.``, and posts a `child.opened` event on this ticket naming the new issue and its kind — the ticket's events are where its children are counted.

A kind is named for who can answer the child, not for where it came from:

| Kind | Who opens it | What it records | Where it goes next |
| --- | --- | --- | --- |
| `finding` | the worker, from the review comment | the review found a defect that does not fall inside this ticket's scope | the closing pass of the night: fixed by the main agent, closed as no longer true, or made a ticket |
| `contract` | the worker | a baseline under `## Read first` this ticket was told to follow does not hold — a missing state, field or case, or two baselines that contradict each other | back to whoever wrote the spec or the baseline; never changed quietly and worked on |
| `deferred` | the worker | work outside `## Owns` seen here that was merely convenient to change, and left alone on purpose | a later ticket. A change a criterion cannot pass without is made and listed under `Outside Owns`, not opened here |
| `decision` | the worker | a choice only a person can make; the worker carries on with the default | the user |
| `fault` | the worker or the main agent | the pipeline itself is broken — a script, a hook, the driver, the target contract | the user, to fix the pipeline. The agent that opens it stops where it is |

An empty file, or a kind that is not one of the five, is refused and nothing is opened. A repository that lacks the `mmw:child` label and will not let it be created is refused the same way. `fault` is the one kind that brings the ticket to rest. This run tells nobody: the relay of the `dispatch` skill reads the `child.opened` on the ticket and wakes the main agent with `#<n> child.opened` for a `fault` or a `decision`.

A reviewer or a verifier opens no `fault`. The worker that started it is asleep until its result lands on the ticket, and a `child.opened` wakes only the main agent, so a reviewer or verifier that stopped after opening one would leave that worker asleep for good. It reports the failure through its result instead, which wakes the worker: the reviewer's review report says which failure it hit, and the verifier writes `--verdict "could not start: <what it ran and what it saw>"`.

## Exit codes

`0` the sub-issue is open and recorded. `1` the sub-issue is open and its `child.opened` event could not be written; stderr names it — do not open it again. `2` a refusal, with the reason on stderr.
