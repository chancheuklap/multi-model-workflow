# Children and decisions

Use the current ticket's native child issues to preserve matters that cannot be settled within its assigned work. The child body is written for a receiver who has seen none of your session: state the problem, evidence, affected requirement, what you tried and what decision or repair is needed.

Choose the first matching kind:

| Question | Kind and receiver |
| --- | --- |
| Is an unavailable environment or broken pipeline preventing work? | `fault`; notifies coordinator. Preserve the command, error and unfinished work. |
| Does a required baseline, spec decision or acceptance requirement fail to hold or contradict another source? | `contract`; notifies coordinator. Cite the actual conflict and what would settle it. |
| Do the sources leave observably different product outcomes open? | `decision`, with the default taken; notifies coordinator and adds `needs-triage`. Take the option the ticket, its baselines and the spec make most likely, record the alternatives and default, and carry on. Keep established decisions and the authorized scope intact. |
| Is a supported defect outside the assigned repair? | `finding`; no immediate notification. Coordinator handles it in the closing pass. |
| Is it an optional product change the task does not require? | `deferred`; adds `needs-triage`, with no immediate notification. |

An implementation mistake within this ticket is repaired here. An internal engineering choice with no unresolved product promise is yours to make and explain. A change necessary for assigned behavior does not become optional because it touches another file.

Write a UTF-8 file with the child's title on the first line and its explanation below, then run `python3 verify-ticket.py N --sub-issue KIND FILE`. The whole file becomes the body. If child creation succeeded but its event failed, use the error's `--existing CHILD` retry with the same report; do not create a duplicate.

For a contract or fault that blocks further work, retain the work and wait for the coordinator through the shared dispatch method. Continue unaffected work when it can proceed. If the coordinator says the blocker will not be resolved in this run, go directly to [Worker: Verify the final output and return it](worker.md#5-verify-the-final-output-and-return-it) and close out as `incomplete`, naming the child and the work or proof not performed. Creating a child does not automatically suspend a session or grant permission to change the agreed behavior.

## Coordinator resolution

Read the actual evidence and authoritative source before deciding. Record the correction or unresolved alternatives on the child. Resolve with `dispatch.sh route N CHILD RESOLUTION --report FILE`:

- `fixed`: the matter was actually repaired. For a repository repair, include `--commit SHA` naming the actual committed repair after its checks and push. For environment-only or tracker-only repairs, state exactly what changed in the report; no unrelated commit is a repair receipt.
- `stale --reason invalid`: the asserted problem did not hold.
- `stale --reason fixed-elsewhere`: it held but was repaired elsewhere.
- `became-ticket --became TARGET`: prepare the actual executable-ticket destination as [Coordinator: Close the remaining findings](coordinator.md#4-close-the-remaining-findings) says, then route it. The route reclassifies and links, but does not write the task for you.

Closing a child records its disposition; it does not wake its worker. If the worker should continue, explicitly `resume N MESSAGE` with the correction, its source and any commit to integrate. An unresolved owner choice remains visible in triage and the delivery. Do not route it as repaired.
