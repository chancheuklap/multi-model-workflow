# Unattended runs

A single task can run to a checkable finish condition. A standing program has a coordinator, a PR queue has explicit merge authority, and a handoff preserves verified progress for the next agent.

## Language

### One task or a program

**Overnight contract**:
The operator's handoff for work that continues while they are away. It names the goal, the check for completion, the permissions for the run, and what to do at a genuine dead end. [Overnight guide](../../guide/07-overnight.md)

**Bespoke playbook**:
A sequence of phases designed for one ambitious or unusual task, including work the operator will review after stepping away. Its first deliverable is the phase list, sized to the work and ordered around its riskiest unknowns. [figure-it-out](../../../skills/figure-it-out/SKILL.md)

**Rigor level**:
The checks and artifacts a bespoke playbook requires for the stakes of a decision. Each unit has a hypothesis and a check against the real artifact. Its verdict is `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`. [figure-it-out](../../../skills/figure-it-out/SKILL.md) · [Claims and verdicts](../product-verification/GLOSSARY.md#claims-and-verdicts)

**Autonomous run**:
A playbook that drives one task to its exit condition. Each iteration checks the work, keeps or discards the change according to the evidence, and records whether the result advanced. A genuine dead end comes back to the operator. [Autonomous run playbook](../../../skills/poteto-mode/playbooks/autonomous-run.md)

**Exit condition**:
The checkable predicate that defines completion before an autonomous run starts, such as zero remaining callers of an old API. A plateau calls for a change of approach. The original condition still determines success. [Autonomous run playbook](../../../skills/poteto-mode/playbooks/autonomous-run.md)

**Watcher**:
A subagent that wakes the coordinator when a named event occurs, such as a PR merge. A **heartbeat** is the timed check that backs up a watcher or supplies the next check when there is no event to watch. Continued work after disconnection requires a wake-up that survives it. [Autonomous run playbook](../../../skills/poteto-mode/playbooks/autonomous-run.md)

**Orchestrate**:
The playbook for a standing project that spans many assignments and outlasts one agent's session. One coordinator assigns the work and checks the results. An independent verifier from a different model family in the operator's cross-judge pool checks each PR at its current head. [Orchestrate playbook](../../../skills/poteto-mode/playbooks/orchestrate.md)

**Autopilot-full**:
The playbook for a queue of independent PRs built from trunk. The root coordinator owns the independent verification. Within the operator's grant, each PR owner carries its change through merge once the required verdict and checks hold. [Autopilot-full playbook](../../../skills/poteto-mode/playbooks/autopilot-full.md)

**Autopilot-stack**:
The playbook that hands verified PRs, green at their current heads, to the operator to land. A PR builds on another branch only when it depends on that PR. After handoff, further pushes need the operator's go. [Autopilot-stack playbook](../../../skills/poteto-mode/playbooks/autopilot-stack.md)

### Authority and supervision

**Session override**:
An instruction such as "keep going" that tells the agent to continue through the operator's absence. The operator can still reserve decisions or explicitly pause the work.

**Full-autonomy grant**:
The operator's permission to make decisions and carry out the agreed work without waiting between steps. An Autopilot grant covers the named queue. For a preference left open, the agent explains its default and how the operator can change it. Reserved gates and Always pause actions, such as a deploy or a customer message, still require the operator.

**Operator gate**:
A decision or action the operator reserves, such as landing a particular PR. The operator's **go** authorizes execution of the stated program. Under Never Block on the Human, independent, reversible work continues while a required decision waits. [principle-never-block-on-the-human](../../../skills/principle-never-block-on-the-human/SKILL.md)

**Root coordinator**:
The chat responsible for the whole program. In Orchestrate it assigns work and checks what landed. In Autopilot it owns the verification verdicts and supervises the queue. Each PR owner writes its branch. [Pull request delivery](../pull-request-delivery/GLOSSARY.md)

**Sub-coordinator**:
An optional Orchestrate role between the root coordinator and the workers in an area with many parallel assignments. It owns those assignments and sends the root one **rollup**, a consolidated report.

**Kickoff**:
The assignment that gives an Orchestrate worker its goal, write boundaries, prohibited actions, and the evidence that proves completion. It includes the upstream reports that the worker needs, even when those reports came from sibling agents.

**Shared artifact store**:
The coordinator's location for records and outputs that other agents can read. An Autopilot kickoff identifies where the owner's decision trail lives so a replacement can recover it after a worker environment disappears.

**Audit tick**:
One scheduled check of an active Autopilot queue. The coordinator rereads the execution playbook, probes progress through every worker's observable actions, and corrects missing records. Ticks are hourly when the host can wake the coordinator.

**Stuck-after runtime**:
The expected time to observable progress, drawn from earlier runs of the same kind. An agent with no new effects past that time qualifies for replacement. An owner that has neither pushed nor logged a decision by the first audit also qualifies. An agent waiting for a decision needs an answer.

**Countersign**:
The root coordinator's fresh approval of a proposed relaxation of a check, after an independent verifier supplies proof. It counts as approval only when the operator's grant covers it. A forge-enforced approval still comes through the forge.

**Hold**:
The operator's zero-writes order to every Autopilot owner. Owners report their state and retain their briefs until release. A stop also cancels pending audits.

[poteto-mode](../../../skills/poteto-mode/SKILL.md) · [Autopilot-full playbook](../../../skills/poteto-mode/playbooks/autopilot-full.md) · [Multi-phase plan playbook](../../../skills/poteto-mode/playbooks/multi-phase-plan.md) · [Orchestrate playbook](../../../skills/poteto-mode/playbooks/orchestrate.md)

### The decision trail

**Decision trail**:
The append-only decision log the operator can audit after a run. Each row names its time, phase, decision, reason, evidence pointer, and result. A correction adds a row that supersedes the original. A hillclimb uses an attempt log with measured results. [Hillclimb experiments](../performance/GLOSSARY.md#hillclimb-experiments)

**Run (decision trail)**:
One agent conversation, including later turns and context summaries. A replacement agent, a pickup, or a new chat starts a new run, even when the same task and decision trail continue.

**Start row**:
A decision-trail row with phase `start` that marks where a run adds to an existing log or resumes after another run wrote to it. Its evidence identifies the current run, and it names the preceding timestamp range written by others.

**Trail audit**:
A comparison of a run's decision rows with its transcript and the evidence each row points to. Missing decisions and unsupported claims get new rows. If the execution record is unavailable, the audit identifies the claims it could not check.

**Attention**:
The closing section of a report for a run that produced a decision trail. A reviewer from a different model family checks the log and transcript for weak evidence, skipped verification, or risky choices. The section identifies the reviewer and its flags, records no flags, or says the cross-model review could not run.

[show-me-your-work](../../../skills/show-me-your-work/SKILL.md) · [Decision log header](../../../skills/show-me-your-work/references/decision-log-template.tsv)

### Pausing and resuming work

**Pause safely**:
An explicit suspension of in-flight work at an atomic boundary. The agent finishes or backs out the current unit, records pending edits in a work-in-progress commit, and leaves a note a fresh agent can read.

**Resume note**:
A record kept outside the chat context that tells the next agent the goal, verified progress, current state, next steps, important files, and known problems. It points to an existing decision trail when one exists.

**Session pickup**:
Taking over work from a specific transcript, remote run, or pushed branch. The prior record establishes the decisions already made. The new agent checks inherited claims against the original goal on the real artifact and routes the remaining work.

**Resume point**:
Where the next agent can continue after comparing the original plan with what actually landed. The pickup may also yield a finished recommendation, a decision to ratify or override a prior conclusion, or a postmortem of a failed run.

[Pause safely playbook](../../../skills/poteto-mode/playbooks/pause-safely.md) · [Session pickup playbook](../../../skills/poteto-mode/playbooks/session-pickup.md)
