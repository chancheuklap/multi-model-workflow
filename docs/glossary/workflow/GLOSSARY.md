# Workflow

The language of a run: the spec, the tickets under it, the branches they land on, and the roles that hold them.

Do not invent a Chinese name for a term in this file, or for any MMW skill. Use the English name.

## Language

### Roles

**Coordinator**:
The role that owns an authorized spec or one ticket from the owner's execution Go through to the delivery PR. This role runs in a cloud agent and manages issues, Blocked by links, PR bodies, and merges.
_Avoid_: any invented Chinese name.

**Worker**:
The assigned role `worker`. A Worker pushes the issue-N branch, opens the PR for its ticket, and writes the ticket's result in that PR.
_Avoid_: Cloud Worker, native Cloud Worker, implementation worker, implementation agent, and any invented Chinese name.

**owner**:
The person who gives the execution Go, releases work out of `needs-triage`, and accepts a delivery PR. operator and human are this same person.
_Avoid_: operator, human, and any invented Chinese name.

**main reviewer**:
A name this workflow does not use. The three axes review one comparison.
_Avoid_: verifier, and any invented Chinese name.

**retro agent**:
The agent that reads a diff for retro and catches a repeated mistake. It is not the main reviewer.
_Avoid_: reviewer agent, review agent, and any invented Chinese name.

**candidate**:
A brief role. It produces one design for a question that is also given to other sessions of this role.
_Avoid_: ticket head, and any invented Chinese name.

**verifier**:
The role that runs `verify-<app>` on the commit it is given. It does not edit the drive script or the feature map.
_Avoid_: main reviewer, and any invented Chinese name.

### Work objects

**spec**:
An issue labelled `mmw:spec`, with no queue label and no worker grade. It is the text a person checks before agents build from it unattended, and it contains the tickets under it.
_Avoid_: any invented Chinese name.

**ticket**:
An issue labelled `mmw:ticket`. It is the execution object. It is not a container of tasks.
_Avoid_: 票, and any invented Chinese name.

**tracer bullet**:
A ticket that lands one narrow path through the stack on its own. vertical slice is the same shape, and both names stay.
_Avoid_: any invented Chinese name.

**vertical slice**:
A ticket that lands one narrow path through the stack on its own. tracer bullet is the same shape, and both names stay.
_Avoid_: any invented Chinese name.

**decision ticket**:
A sub-issue of a wayfinder map. It carries only a `wayfinder:<type>` label. It resolves a decision.
_Avoid_: any invented Chinese name.

**sub-issue**:
An issue the tracker nests under a parent issue.
_Avoid_: child, child issue, and any invented Chinese name.

**Blocked by**:
The tracker link that names the tickets one ticket waits on.
_Avoid_: blocking edge, blocker, dependency, native blocking, and any invented Chinese name.

**work report**:
The ticket PR. It records what the Worker did for its ticket.
_Avoid_: final work report, Worker report, final report, and any invented Chinese name.

**PR**:
The pull request a Worker opens for its ticket. Draft is a state of this PR. The Worker writes the result in the body and the Coordinator marks it ready.
_Avoid_: ticket PR, draft PR, and any invented Chinese name.

**delivery PR**:
The pull request from the night branch into the project branch. It is the handoff to the owner.
_Avoid_: delivery, delivery pull request, and any invented Chinese name.

**map**:
A single issue labelled `mmw:map`. It indexes decision tickets. The decision text stays on the ticket.
_Avoid_: any invented Chinese name.

**mmw:child**:
The label on an issue opened under a ticket when a problem needs a tracked decision or a repair. Promoting that issue to executable work replaces this label with `mmw:ticket`.
_Avoid_: any invented Chinese name.

**wide refactor**:
One mechanical change whose blast radius reaches so many call sites that a single ticket cannot land on its own.
_Avoid_: any invented Chinese name.

**expand-contract**:
The sequence used for a wide refactor: add the new form beside the old, migrate call sites in batches, then delete the old form when no caller remains. That last step is not a contract.
_Avoid_: any invented Chinese name.

**expected result**:
The sentence in a user story that states one observable result. A verification script copies that sentence unchanged.
_Avoid_: any invented Chinese name.

**code predecessor**:
A ticket whose result is already merged into the night branch. A new Worker for later work waits on that merge.
_Avoid_: any invented Chinese name.

**Agent ID**:
The identifier returned when a Worker, a review axis, or a verifier is started. The Coordinator keeps the Worker's Agent ID with its ticket. A verifier that does not pass is started again; that new start has its own Agent ID.
_Avoid_: any invented Chinese name.

**card**:
One assignment object in the `cards` array printed by `dispatch.sh spawn`. Its `description` labels the task, `model_row` supplies the model settings, and `prompt` contains the task text. The sender uses those settings to start a fresh subagent, with a new context that does not inherit the sender's conversation, and sends `prompt` unchanged. The card describes the assignment; starting the subagent returns its Agent ID.
_Avoid_: Worker as a name for the card, and any invented Chinese name.

**max_workers**:
A configuration key this workflow drops. A night dispatches every eligible ticket.
_Avoid_: any invented Chinese name.

**RUNTIME_COMMIT**:
The starting commit of this run. Model configuration is read at that commit. Board edits after it belong to the next run.
_Avoid_: any invented Chinese name.

**consuming repository**:
The project checkout the run works in. Commands run there.
_Avoid_: any invented Chinese name.

**MMW runtime**:
The installed skills and tools fixed for this run. In Cursor that copy is the project's `.cursor/`. In Codex it is the project's `.agents/`.
_Avoid_: any invented Chinese name.

**execution Go**:
The owner's authorization that starts the Coordinator on a spec or a ticket.
_Avoid_: any invented Chinese name.

### Branches

**night**:
One unattended run.
_Avoid_: night branch, NIGHT, and any invented Chinese name.

**night branch**:
The branch named `night/spec-N` for one spec, or `night/ticket-N` for one ticket. N is that issue's number.
_Avoid_: night, NIGHT, and any invented Chinese name.

**issue-N branch**:
The branch named `ticket/issue-N` for ticket N. N is that ticket's issue number.
_Avoid_: any invented Chinese name.

**project branch**:
The branch named `project/<project name>`, cut from the dev branch. A delivery PR merges into it.
_Avoid_: dev, dev branch, PROJECT, and any invented Chinese name.

**dev branch**:
The branch named `dev`. A finished project branch merges into it for testing.
_Avoid_: project branch, the dev, and any invented Chinese name.

**main branch**:
The branch named `main`. The dev branch merges into it for deployment.
_Avoid_: any invented Chinese name.

### Labels

**ready-for-agent**:
The queue label on a ticket an agent may take. It excludes `ready-for-human` and `needs-triage`.
_Avoid_: any invented Chinese name.

**ready-for-human**:
The queue label on a ticket only a person can do. That ticket has no worker grade.
_Avoid_: any invented Chinese name.

**needs-triage**:
The queue label for work that waits until the owner releases it. It is not frontier work.
_Avoid_: any invented Chinese name.

**junior-worker**:
The default worker grade on a ticket an agent works.
_Avoid_: any invented Chinese name.

**senior-worker**:
The worker grade for a ticket where a silent wrong result matters: money that must reach a terminal state, recovery after a crash, a contract an installed base already reads, or a security default.
_Avoid_: any invented Chinese name.

**worker grade**:
The label `junior-worker` or `senior-worker`. An agent ticket has exactly one.
_Avoid_: any invented Chinese name.

**queue label**:
One of `ready-for-agent`, `ready-for-human`, and `needs-triage`. A ticket has one of them.
_Avoid_: any invented Chinese name.

### Wayfinding

**destination**:
What reaching the end of a wayfinder map looks like: the spec, the decision, or the change that effort is finding its way to.
_Avoid_: any invented Chinese name.

**frontier**:
Work that can be taken now because every ticket in its Blocked by list is done. On a wayfinder map the frontier is also unclaimed. Human tickets and `needs-triage` tickets are outside it.
_Avoid_: any invented Chinese name.

**fog of war**:
In-scope questions on a wayfinder map that are not sharp enough to be tickets yet. They sit in the map section Not yet specified.
_Avoid_: any invented Chinese name.

**claim**:
The assignee on a decision ticket: a person on a HITL ticket, an agent on an AFK ticket. An open decision ticket with no assignee is unclaimed.
_Avoid_: the dev, and any invented Chinese name.

**HITL**:
A decision ticket worked with a human who speaks for themselves. The agent does not answer that human's side.
_Avoid_: any invented Chinese name.

**AFK**:
A decision ticket the agent drives alone.
_Avoid_: any invented Chinese name.

**wayfinder:research**:
A decision-ticket type for a fact the decision waits on. It is resolved by the research skill.
_Avoid_: any invented Chinese name.

**wayfinder:prototype**:
A decision-ticket type for a cheap concrete artifact to react to. It is resolved by the prototype skill. It is not Prototype, the fidelity mode of html-prototype, and it is not a logic demo or a UI prototype.
_Avoid_: any invented Chinese name.

**wayfinder:grilling**:
A decision-ticket type for a conversation. It is resolved by the grilling skill and the domain-modeling skill.
_Avoid_: any invented Chinese name.

**wayfinder:task**:
A decision-ticket type for manual work that must happen before a decision can be made.
_Avoid_: any invented Chinese name.

### Review

**Standards**:
The review axis that checks the diff against this repo's documented coding standards.
_Avoid_: any invented Chinese name.

**Spec**:
A review axis. It checks the diff against the originating issue or spec. The issue labelled `mmw:spec` is the work object **spec**.
_Avoid_: any invented Chinese name.

**Tests**:
The review axis that checks whether the tests are trustworthy, proportionate proof of the assigned change.
_Avoid_: any invented Chinese name.

**pinned comparison**:
The commit a review or a Worker measures a change against.
_Avoid_: fixed point, and any invented Chinese name.

**ticket head**:
The current commit on the issue-N branch for one ticket. Review measures it against the pinned comparison, land merges it into the night branch, and a `--head` value names it.
_Avoid_: candidate, and any invented Chinese name.

### Baselines

**smell baseline**:
The fixed list of code smells the Standards axis applies even when a repo documents no standard.
_Avoid_: baseline alone, and any invented Chinese name.

**accepted baseline**:
A conclusion already recorded on a spec or a ticket. A Worker does not reopen it.
_Avoid_: baseline alone, and any invented Chinese name.

**settled baseline**:
A conclusion already chosen in material the work was told to follow. It is followed as written.
_Avoid_: baseline alone, contract, and any invented Chinese name.

**measurement baseline**:
The measurement a later number is compared with.
_Avoid_: baseline alone, and any invented Chinese name.

### Checks

**pre-commit hook**:
The check that runs on a commit. It covers format, lint, types, and the static parameter rules.
_Avoid_: guardrail, commit hook, and any invented Chinese name.

**scripts/check**:
The executable check at the repository root that `land` runs on a merge. `MMW_BASE_REF` is the branch being merged into. A missing file, a red result, or a check this machine cannot run leaves the night branch unchanged.
_Avoid_: any invented Chinese name.

**land**:
The dispatch operation that merges a Worker's PR into the night branch after `scripts/check` passes for that head.
_Avoid_: any invented Chinese name.
