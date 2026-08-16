# Wayfinding

This context defines the map and decision ticket used by `/mmw-wayfinder`.

## Language

**effort**:
Work that does not fit in one agent session, and whose route from here to the destination is not yet clear. Whether the destination is a spec does not change the entry test.
_Avoid_: big ticket, big spec

**destination**:
The end state the wayfinding map is finding its way to. The destination fixes the effort's scope.
_Avoid_: goal list, delivery checklist

**map**:
The shared index of one effort on the issue tracker, labelled `wayfinder:map`. Its body records the map branch; the name segment for this effort's artifacts is computed from that branch and does not change after the map is created.
_Avoid_: Context Map, plan, repository

**decision ticket**:
A child issue under the map that clears one decision or a blocker in front of one, labelled `wayfinder:<type>`. Artifact name segment inherits the map branch slug; the scope segment is `issue-<ticket number>`. Git checkout and merge of ticket work sit outside this skill.
_Avoid_: tracer bullet ticket, 任务包

**Required materials**:
The section of a decision ticket body that lists what this ticket must read. The session that creates the ticket writes what is known then; the session that claims it adds materials produced since.
_Avoid_: consumes, 必读清单, supporting materials, 必读材料声明

**fog of war**:
In-scope work that is visible enough to notice but not yet sharp enough to write as a decision ticket, kept in `Not yet specified`.
_Avoid_: decision ticket, Out of scope

**resolution comment**:
The comment posted before a decision ticket is closed. It records the decision, the artifact refs this ticket used or produced, and Materials used. It is the authoritative copy of the decision and remains after the issue is closed.
_Avoid_: handback comment, shared-understanding record, scratch, 结论评论

**Materials used**:
The section of the resolution comment that accounts for every Required materials entry: used or not, and why if not.
_Avoid_: supporting materials, 材料使用记录

**路径形状**:
(authoritative: [路径形状](./artifact-location.md))

**名字段**:
(authoritative: [名字段](./artifact-location.md))

**范围段**:
(authoritative: [范围段](./artifact-location.md))

**权威副本**:
(authoritative: [权威副本](./tracker.md))

**frontier**:
(authoritative: [frontier](./tracker.md))

**HITL**:
(authoritative: [HITL](./delivery-workflow.md))

**AFK**:
(authoritative: [AFK](./delivery-workflow.md))

**shared understanding**:
(authoritative: [shared understanding](./delivery-workflow.md))

**`wayfinder:grilling`**:
A HITL decision ticket that uses `/mmw-grilling` to turn the `Question` into a shared understanding. How questions are asked is owned by `/mmw-grilling`.

**`wayfinder:prototype`**:
A HITL decision ticket that uses `/mmw-prototype` to iterate a running artifact and answer the question through a user walkthrough.

**`wayfinder:research`**:
An AFK decision ticket that uses `/mmw-research` to surface a fact a decision waits on. The fact may come from this repo's source, or from docs, third-party APIs, or official specs. Use when investigation yields the fact without a human discussion.

**`wayfinder:task`**:
Manual work that must happen before a decision can be formed. It may be HITL or AFK.

## Session boundary

One session resolves one decision ticket. A charting session may fire several `wayfinder:research` tickets in parallel, but each research invocation still resolves one ticket.
