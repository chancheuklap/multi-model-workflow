# Investigation

An investigation can explain how code runs, why a decision was made, what a change could break, or where earlier work stands.

## Language

### Questions about behavior

**Read-only investigation**:
A task whose result is a cited explanation or, for a choice between alternatives, a recommendation with trade-offs. The Investigation playbook uses the current code to explain behavior and adds a historical search when the question concerns motivation.

**Research report**:
A dated answer to a specific question with each claim tied to a primary source. It identifies what remains unverified and gives the caller access to its supporting attachments. A research ticket links the report so a later session can use the evidence. [research](../../../skills/research/SKILL.md) · [Wayfinder decisions](../planning-and-tickets/GLOSSARY.md#wayfinder-decisions)

**Mechanics**:
What the code does now, including the trigger, the path through the code, the data passed between components, and the outcome. Under *Read Before You Conclude*, the investigator reads the relevant passage and its callers before describing the behavior. When a rule spans agents, that path includes their handoffs. If the conclusion depends on an unread part, the account identifies what the investigator observed and what they inferred. [principle-read-before-you-conclude](../../../skills/principle-read-before-you-conclude/SKILL.md)

**Motivation**:
The reason a person or team chose a particular behavior. A contemporaneous statement can establish intent. The behavior of the code alone leaves that intent open.

**Exploration angle**:
One distinct part of a subsystem that a read-only explorer traces for a larger question. The explorer gives the explainer the components, execution flow, files read, boundaries, surprises, and unresolved questions for that part.

**How explorer**:
The delegate who investigates one exploration angle. A question spanning several files or services can use two to four explorers in parallel. A narrow question goes directly to the explainer.

**How explainer**:
The delegate who writes the architectural explanation. For a narrow question the explainer reads the code directly. For a larger question the explainer reconciles the explorers' findings, checking disagreements against the code.

**Outside check**:
An observation independent of the operator's or agent's judgment that would establish whether the requested result is right. The rewritten prompt names that check before the work begins. [Rewritten prompt](../skill-authoring/GLOSSARY.md#requests-replies-and-teaching).

[Investigation playbook](../../../skills/poteto-mode/playbooks/investigation.md) · [how](../../../skills/how/SKILL.md) · [why](../../../skills/why/SKILL.md) · [Explorer brief](../../../skills/how/references/explorer-prompt.md) · [Explainer brief](../../../skills/how/references/explainer-prompt.md) · [sharpen](../../../skills/sharpen/SKILL.md)

### Historical sources

**Code anchor**:
The files and lines, symbols, recent commits, pull requests, and linked tickets that identify the target of a historical question. The investigators and the synthesizer receive the same anchor.

**Evidence category**:
One of seven kinds of record in a historical investigation. Each available source belongs to the category that best describes its evidence. A source playbook describes what to look for in that category.

| Category | What the record can establish |
| --- | --- |
| Source control history | The change and the rationale recorded in its commits, reviews, tests, or comments. [Code archaeology](../../../skills/why/references/sources/code-archaeology.md) |
| Issue or ticket tracker | The product need, external constraint, or later change of scope. A parent issue can explain why a smaller task existed. [Ticket records](../../../skills/why/references/sources/linear.md) |
| Long-form documents | The options and rationale in design documents, meeting notes, and decision records. A draft records the plan at its date. [Document records](../../../skills/why/references/sources/notion.md) |
| Real-time team chat | Deliberation that stayed in a conversation. The thread supplies context for a quoted message. [Chat records](../../../skills/why/references/sources/slack.md) |
| Infrastructure observability | Runtime conditions recorded in metrics, monitors, traces, logs, or incidents around the change. [Telemetry records](../../../skills/why/references/sources/datadog.md) |
| Error or exception tracking | The exception, affected releases, frequency, and path through the target code in an actual event. [Error history](../../../skills/why/references/sources/sentry.md) |
| Product analytics warehouse | Feature use, experiment exposures, usage costs, or the distribution behind a threshold. [Analytics records](../../../skills/why/references/sources/databricks.md) |

**Why investigator**:
The read-only delegate who searches one assigned source in an accessible evidence category. The investigator returns the queries, citations, contradictions, gaps, and leads for other sources. An incident or postmortem search supplements that source's usual search when the target looks defensive, such as a newly added retry.

**Additional lead**:
A reference in one source that points to another, such as a pull request that links to a chat thread. The investigator records the reference for the investigator who owns the other source or for a follow-up search.

**Coverage map**:
The account of what was actually searched, published as *Sources Consulted*. Each category records its search or the reason for skipping it, such as inaccessible evidence or a demonstrably irrelevant category.

**Null result**:
A recorded search of available evidence that returned no match. Its meaning depends on the query and the period the source covers. For example, a search of retained logs can establish that no entry matched that search.

**Evidence gap**:
A part of the question that the available records cannot answer. A missing chat permission or unavailable telemetry leaves a gap.

**Retention cliff**:
The limit on how far back the source has records. When the change predates that limit, an empty query leaves the historical activity unknown.

[why](../../../skills/why/SKILL.md) · [Source playbooks](../../../skills/why/references/source-playbook.md) · [Investigator brief](../../../skills/why/references/investigator-prompt.md) · [Incident and postmortem context](../../../skills/why/references/sources/incident-postmortem.md) · [Synthesizer brief](../../../skills/why/references/synthesizer-prompt.md)

### Reading historical records

**Co-change signal**:
Another file changed in the same commit as the target. The association identifies related code or tests to examine for an explanation.

**Author-bounded search**:
A search of chat messages from the change's author around the merge date. It can locate a deliberation whose wording never appears in the code or ticket.

**Error trajectory**:
The first and last recorded occurrences, frequency, and affected releases of an exception relative to the change. The actual event and its stack establish whether the error reached the target code. An automated root-cause suggestion supplies a hypothesis.

**Event usage trajectory**:
The change in recorded product events around a release. A rise after a merge can support a launch hypothesis. A change to instrumentation can produce the same rise even if usage stayed constant.

**Experiment exposure**:
A warehouse record that connects a feature-flag variant to the people or events included in an experiment. Counts by variant near a merge date and a recorded ship decision bear on whether the experiment informed the change.

**Refresh lag**:
The interval during which a newly recorded event can appear in the raw data before a scheduled update includes it in a typed, deduplicated analytics table. Evidence from that interval can come from raw events deduplicated by event ID.

**Temporal correlation**:
An event, error, or metric changes near the date the code shipped. The timing can support an explanation. Other changes shipped in the same window can account for the observation.

[Code archaeology](../../../skills/why/references/sources/code-archaeology.md) · [Chat records](../../../skills/why/references/sources/slack.md) · [Error history](../../../skills/why/references/sources/sentry.md) · [Analytics records](../../../skills/why/references/sources/databricks.md) · [Telemetry records](../../../skills/why/references/sources/datadog.md)

### Confidence in a historical claim

**Why synthesizer**:
The delegate who weighs investigator findings against the original question, verifies doubtful citations, and assigns a confidence tier to each claim. Conflicting sources retain both citations. The confidence language survives later edits and teaching.

**Circumstantial evidence**:
A record that bears on the question without directly stating the reason. The investigator identifies the inference the record could support and any other reading that would fit it.

**Direct**:
The confidence tier for a claim that a cited author explicitly states. A sentence recording why a retry limit changed can establish the author's rationale.

**Supported**:
The confidence tier for a conclusion supported by several converging pieces of indirect evidence. The account cites the items and identifies what each contributes.

**Inferred**:
The confidence tier for a reasonable interpretation of the context. The account identifies the observations, shows the step from observation to interpretation, and signals uncertainty.

**Speculative**:
The confidence tier for a possibility with little evidence when other explanations fit equally well. The account presents it as a hypothesis.

**Unknown**:
The confidence tier for a question the search did not answer. The account identifies the specific searches and missing evidence.

**Competing hypotheses**:
Plausible explanations that remain open in a historical investigation. Each has its own supporting evidence, counterevidence, or missing observation. A suggestion embedded in the operator's question also enters the investigation as a hypothesis.

**Preserve / Change / Avoid / Risk**:
The constraint set for planning a change after an investigation into its history. It records what the historical findings imply about behavior to preserve, intended changes, choices to avoid, and remaining risks.

[Synthesizer brief](../../../skills/why/references/synthesizer-prompt.md) · [teach](../../../skills/teach/SKILL.md) · [Investigator brief](../../../skills/why/references/investigator-prompt.md) · [Confidence tiers](../../../skills/why/references/epistemics.md) · [why](../../../skills/why/SKILL.md)

### Blast radius

**Blast radius**:
The effects a change can have outside the edited code. The investigation includes consumers that a symbol search can miss, such as another program reading the same wire format or a callback that runs during teardown.

**Safety fact**:
A specific fact on which the change's safety depends. The blast-radius report gives the strongest level of evidence reached and labels a fact that remains unproved as *unproven*.

| Level | Evidence for the safety fact |
| --- | --- |
| 1 | The reviewer asserted it. |
| 2 | The reviewer cited the relevant source line. |
| 3 | Tracing the failure step by step showed that the bad case was unreachable. |
| 4 | A script or test exercised the actual code and checked the claim. |
| 5 | The reviewer reproduced the behavior in the running app. |

**Cleared risk**:
A suspected failure that the investigation checked and ruled out, with the reason recorded under *Cleared*. A confirmed risk instead carries the failure mechanism, source location, likelihood, impact, and a way to check it.

[blast-radius](../../../skills/blast-radius/SKILL.md)

### Bug diagnosis

**Reproduction**:
A repeatable trigger that produces the reported symptom on the affected product surface. The original reproduction supplies the before-and-after check for a fix. The report includes its failing output and its output after the fix. *Repro* is the short form. [Product surface](../product-verification/GLOSSARY.md#evidence-and-observation).

**Candidate hypothesis**:
A possible cause of the reproduced failure with a prediction that distinguishes it from other causes. Each diagnostic pass uses runtime evidence to eliminate candidates. A refuted hypothesis also invalidates the change it motivated.

**Root cause**:
The first place the system makes the wrong decision or fails to handle a legitimate state. The symptom is where the resulting fault becomes visible. Under *Fix Root Causes*, the bug diagnosis confirms the surviving mechanism in a running reproduction before a fix is planned.

[Bug fix playbook](../../../skills/poteto-mode/playbooks/bug-fix.md) · [principle-fix-root-causes](../../../skills/principle-fix-root-causes/SKILL.md)

### Reconstructing recent work

**Recall**:
A reconstruction of the operator's recent work across chats in the named workspace and time window. With a named feature, file, subsystem, area, or bug, it also searches the shared record. A question about activity alone can use chat history and live state. The default window is the past seven days. Resuming one specific chat follows Session pickup. [Session pickup](../unattended-runs/GLOSSARY.md#pausing-and-resuming-work).

**Shared record**:
Evidence about the same work outside the operator's own chats, such as recurring reports, a reverted fix, or an error still occurring in production. Recall cites the shared source and checks the current state of the branches, pull requests, and issues it finds.

**Current-state brief**:
Recall's account of where the work stands. It opens with a *capsule* of at most five bullets, gives the status of each thread, names up to five recurring problems, and closes with one concrete next move. A full state capsule supplied by the operator can replace the search through past chats.

**Thread status**:
The single tag attached to each line of work in a recall brief. The tags are `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, and `[planned, not started]`. Chat findings cite a chat ID.

[recall](../../../skills/recall/SKILL.md)

### Reviewing a session

**Durable learning**:
A finding from a particular session that would change a future agent's decision and would still apply after paths, versions, or code details change. The reviewer ties it to a specific moment in the active transcript and proposes a destination for it.

**Judgment reviewer**:
The reviewer who examines decisions, corrections, preferences, and friction for a principle that applies to future work.

**Tooling reviewer**:
The reviewer who identifies durable facts about a tool or workflow, including occasions when the operator had to supply context the agent could have fetched.

**Divergent reviewer**:
The reviewer who examines missed checks, second-order effects, and alternative explanations for a successful or failed decision.

[reflect](../../../skills/reflect/SKILL.md) · [Review criteria](../../../skills/reflect/references/synthesizer.md) · [Judgment reviewer brief](../../../skills/reflect/references/judgment-reviewer.md) · [Tooling reviewer brief](../../../skills/reflect/references/tooling-reviewer.md) · [Divergent reviewer brief](../../../skills/reflect/references/divergent-reviewer.md)

### Disposition of session findings

**Reflect synthesizer**:
The delegate who combines the three reviewers' findings, checks the evidence and the target skill, and assigns each finding to Accepted, Rejected, or Backlog.

**Convergence**:
Agreement between at least two session reviewers on a finding. It raises confidence in that finding. A finding from a single reviewer needs stronger support from the other criteria, such as whether it changes a future decision.

**Missed trigger**:
A skill was available and suited to the task but did not run. Its finding routes to the skill description. A body edit concerns a skill the transcript shows the agent used, for example by reading its instructions, naming it in a delegation brief, or running its documented commands.

**Accepted finding**:
A proposal for a specific edit, with its problem, proposed change, and destination. The operator chooses which accepted proposals to apply. A new skill is an eligible destination for a recurring pattern only when no existing skill fits.

**Rejected finding**:
A proposal the synthesizer drops with a reason. For example, `already-covered` means clear guidance already exists in the right place. `skill-not-used` means the proposed destination was neither used nor a missed trigger.

**Backlog finding**:
A lesson better enforced by a mechanism such as a lint rule, script, metadata flag, or runtime check. The tracker item records the pattern and the proposed mechanism. The parent files it directly.

[Review criteria](../../../skills/reflect/references/synthesizer.md) · [Reviewer scope](../../../skills/reflect/references/judgment-reviewer.md) · [reflect](../../../skills/reflect/SKILL.md)
