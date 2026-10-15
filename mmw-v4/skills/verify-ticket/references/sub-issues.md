# Cutting something out of a ticket

## When something has to leave this ticket

```bash
python3 scripts/verify-ticket.py <n> --sub-issue <kind> <file>
```

`--sub-issue` takes a kind and a file whose first line is the child's title and whose rest is its body; it opens the child under this ticket and records it there.

Every child carries `mmw:child`. A `finding`, `contract` or `fault` opens with no status label, awaiting processing. A `decision` or `deferred` also carries `needs-triage`, awaiting the owner's decision.

The kind decides who reads the child and when. A `fault` or `contract` wakes the session that sent this ticket, the night's orchestrator or the One ticket session. That session handles the wake as Run a night's **3. Each time something wakes you** or One ticket's **Each wake** step says. A repaired environment fault is resumed and routed `fixed`. A fault in the running pipeline's own scripts goes to the owner with `## Problem`, `Playbook:` and `needs-triage`, keeping `mmw:child` and leaving it unrouted. A `finding` goes to the session that merges this ticket, in the night's closing pass or One ticket's **Open the pull request** step, including a fix ticket merged into an existing PR by Opening a PR's **Before merging, read its checks and comments** step. A `decision` or `deferred` reaches the owner in the night summary or the top half of this ticket's pull request description, while you carry on. None of these readers has seen your session, so the body stands on its own.

## Which kind it is

Ask **the kind questions** in order. The first yes decides the kind.

| Order | Question | Kind | Not this kind |
| --- | --- | --- | --- |
| 1 | Is the pipeline itself broken: `verify-ticket.py`, `dispatch.sh`, a hook, a `scripts/check` that cannot run (a missing tool, a broken script)? Or is the product unreachable, or waiting on a human step? | `fault` | A process you did not start that looks stuck: it is another run's, and you never end it. |
| 2 | Does something this ticket was told to follow fail to hold: a baseline, a `## Parent` spec section or an acceptance criterion lacks a state, field or case, or contradicts another such source? | `contract` | Those sources are clear and this ticket's implementation is wrong; fix it in this ticket. |
| 3 | Do the sources say nothing, while multiple defensible readings would produce observably different outcomes? | `decision`, with the default taken | An internal name or data structure whose alternatives have no observable difference; decide it and record it in `DECISIONS`. |
| 4 | Is it a defect from the review report outside this ticket's `## Owns`? | `finding` | It is inside `## Owns`; fix it in this ticket. |
| 5 | Is it a merely convenient product change outside `## Owns` that no criterion needs? | `deferred` | A way-of-working problem goes to the **register-problem** skill. A criterion needs the product change: make it, as the mmw-mode skill's Work a ticket playbook says for a file outside **Owns**. |
