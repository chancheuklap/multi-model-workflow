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

**Outside check**:
An observation independent of the operator's or agent's judgment that would establish whether the requested result is right. The rewritten prompt names that check before the work begins. [Rewritten prompt](../skill-authoring/GLOSSARY.md#requests-replies-and-teaching).

[Investigation playbook](../../../skills/mmw-mode/playbooks/investigation.md) · [how](../../../skills/how/SKILL.md) · [why](../../../skills/why/SKILL.md) · [sharpen](../../../skills/sharpen/SKILL.md)

### Gaps in the record

**Null result**:
A recorded search of available evidence that returned no match. Its meaning depends on the query and the period the source covers. For example, a search of retained logs can establish that no entry matched that search.

**Evidence gap**:
A part of the question that the available records cannot answer. A missing chat permission or unavailable telemetry leaves a gap.

[why](../../../skills/why/SKILL.md) · [recall](../../../skills/recall/SKILL.md)

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

**Feedback loop**:
In bug diagnosis, one command that drives the reported symptom, has already run once, and can go red on this bug and green once it is fixed. It is tight when it is fast, deterministic, sharp enough to assert the exact symptom, and runnable by the agent unattended. For an intermittent bug the target is a high reproduction rate. The Skill authoring pattern of the same name is a different thing. [Skill authoring pattern](../skill-authoring/GLOSSARY.md)

**Minimized reproduction**:
The smallest scenario that still goes red. Every remaining element is load-bearing, so removing any one turns the feedback loop green.

**Debug tag**:
A unique prefix such as `[DEBUG-a4f2]` on every temporary log. One search for the prefix finds all of them, and an empty search shows the probes are withdrawn.

**Correct test seam**:
A [test seam](../product-verification/GLOSSARY.md) where a regression test exercises the real bug pattern as it occurs at the call site. A seam that is too shallow gives false confidence. When none exists, that absence is a finding about the architecture.

**Candidate hypothesis**:
A possible cause of the reproduced failure with a prediction that distinguishes it from other causes. Three to five are ranked before any is tested. Each diagnostic pass uses runtime evidence to eliminate candidates. A refuted hypothesis also invalidates the change it motivated.

**Root cause**:
The first place the system makes the wrong decision or fails to handle a legitimate state. The symptom is where the resulting fault becomes visible. Under *Fix Root Causes*, the bug diagnosis confirms the surviving mechanism in a running reproduction before a fix is planned.

[Bug fix playbook](../../../skills/mmw-mode/playbooks/bug-fix.md) · [Diagnosis loop](../../../skills/mmw-mode/references/bug-fix/diagnosis-loop.md) · [principle-fix-root-causes](../../../skills/principle-fix-root-causes/SKILL.md)

### Reconstructing recent work

**Recall**:
A reconstruction of the operator's recent work across chats in the named workspace and time window. With a named feature, file, subsystem, area, or bug, it also searches the shared record. A question about activity alone can use chat history and live state. The default window is the past seven days. Resuming one specific chat follows Session pickup. [Session pickup](../unattended-runs/GLOSSARY.md#pausing-and-resuming-work).

**Shared record**:
Evidence about the same work outside the operator's own chats, such as recurring reports, a reverted fix, or an error still occurring in production. Recall cites the shared source and checks the current state of the branches, pull requests, and issues it finds.

**Recall investigator**:
The delegate Recall starts for one source the topic touches, on the `reader` role when its tools can read the source, otherwise on the `judgment and prose` role with the required read access. It reads only, writes nothing, and holds the tools its source needs, such as git and `gh` for source control. It reports the current state, what was tried and did not hold, and what users still report. A source it cannot read is reported as unread, and an empty search is a finding. [Reader](../routing-and-delegation/GLOSSARY.md#model-assignments)

**Current-state brief**:
Recall's account of where the work stands. It opens with a *capsule* of at most five bullets, gives the status of each thread, names up to five recurring problems, and closes with one concrete next move. A full state capsule supplied by the operator can replace the search through past chats.

**Thread status**:
The single tag attached to each line of work in a recall brief. The tags are `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, and `[planned, not started]`. Chat findings cite a chat ID.

[recall](../../../skills/recall/SKILL.md)

### Reviewing a session

**Durable learning**:
A finding from a particular session that would change a future agent's decision and would still apply after paths, versions, or code details change. The agent running [reflect](../../../skills/reflect/SKILL.md) ties it to a specific moment in the active transcript and proposes a destination for it.

### Disposition of session findings

**Missed trigger**:
A skill was available and suited to the task but did not run. Its finding routes to the skill description. A body edit concerns a skill the transcript shows the agent used, for example by reading its instructions, naming it in a delegation brief, or running its documented commands.

**Accepted finding**:
A proposal for a specific edit, with its problem, proposed change, and destination. The operator chooses which accepted proposals to apply.

**Rejected finding**:
A proposal the agent drops with a reason, such as guidance the target skill already gives or a one-off that would not change a future decision.

**Backlog finding**:
A lesson better enforced by a mechanism such as a lint rule, script, metadata flag, or runtime check. The agent presents it under Backlog.

[reflect](../../../skills/reflect/SKILL.md)
