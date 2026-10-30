# Development

Preparing a selected change through evidence, discussion and design, or returning a requested diagnosis or architecture report. This context distinguishes the reusable methods from the records in Tickets and the execution in Ticket run and Night.

## Language

### Preparation

**Develop a change**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/develop-a-change.md) for supplying the missing evidence, decisions and plan of one selected code change, ending with an independent ticket or spec batch. It reuses completed preparation and is distinct from mmw-mode routing and ticket execution.

**preparation**:
The evidence, settled decisions and executable plan still needed before implementation. Its result can be one independent ticket; a long investigation alone does not make a spec necessary.

**execution Go**:
The owner's authority to execute the recorded scope, distinct from selecting a problem for preparation or approving a batch breakdown alone. A prior Go remains attached to its agreed scope.

**owner acceptance**:
The owner's judgment after running and inspecting the prepared product result. Automated verification supplies evidence for this judgment; it does not substitute for acceptance.

**Design a UI**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/design-a-ui.md) supplying a confirmed UI design to a development preparation or returning it as a directly requested result. It does not take over Develop a change's planning or the execution flows.

### Discussion and investigation

**Grill with docs**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/grill-with-docs.md) for sharpening a design through discussion while recording settled terms and important decisions. It combines grilling with domain-modeling and returns the decisions to its caller.

**Investigation**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/investigation.md) for a cited read-only answer or recommendation. A diagnosis can use a specialist method without preparing or implementing a fix.

**Runtime forensics**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/runtime-forensics.md) for diagnosing a live runtime symptom using instrumentation. It is distinct from Trace forensics, which starts with an existing capture.

**Trace forensics**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/trace-forensics.md) for a diagnosis supported by an existing profile, trace or heap capture. It returns what that capture supports without starting a repair.

**`how`**:
The [skill](../../../mmw-v4/skills/how/SKILL.md) for a working explanation of how the current code is organized and behaves. It is distinct from why, which investigates the forces behind that shape.

**`why`**:
The [skill](../../../mmw-v4/skills/why/SKILL.md) for investigating the evidence behind a design's motivation and history. Its conclusions separate recorded intent from inference.

**`research`**:
The [skill](../../../mmw-v4/skills/research/SKILL.md) for returning a cited answer to one question from primary sources. The answer is a result for its caller rather than an implementation plan.

**`teach`**:
The [skill](../../../mmw-v4/skills/teach/SKILL.md) for explaining what a thing is, how it works and why it was built that way at the owner's pace.

**`grilling`**:
The [skill](../../../mmw-v4/skills/grilling/SKILL.md) for resolving a design tree of dependent decisions with the owner. Observable facts are evidence inputs rather than decisions the owner must supply.

**`domain-modeling`**:
The [skill](../../../mmw-v4/skills/domain-modeling/SKILL.md) for settling a project's domain language and recording glossary terms and qualifying architecture decisions. Reading an existing glossary alone is not this modeling work.

**`sharpen`**:
The [skill](../../../mmw-v4/skills/sharpen/SKILL.md) for assessing the expert approach, actual goal, useful constraints and independent proof of a task. It returns those conclusions to its caller.

**`wait-what`**:
The [skill](../../../mmw-v4/skills/wait-what/SKILL.md) for re-explaining a reply, visually re-pitching it, catching up on changes or restating the goal before dependent work. It is a user-invoked communication component.

**`diagram-design`**:
The [skill](../../../mmw-v4/skills/diagram-design/SKILL.md) for self-contained diagrams and pages that explain a system or decision to a person. Its source-named elements and adjacent explanations describe the thing being considered.

### Methods

**`bug-fix`**:
The [skill](../../../mmw-v4/skills/bug-fix/SKILL.md) for diagnosing a defect, preparing its focused repair, implementing the prepared repair or verifying the original scenario. Each entry returns evidence within its caller's authority.

**`perf-issue`**:
The [skill](../../../mmw-v4/skills/perf-issue/SKILL.md) for diagnosing a measured slowdown, preparing one performance change and comparing the result against the same baseline. Sustained metric improvement belongs to hillclimb.

**`hillclimb`**:
The [skill](../../../mmw-v4/skills/hillclimb/SKILL.md) for sustained improvement of one metric against a frozen harness, target and attempt floor. Its measured attempts are kept or reverted with a recorded verdict.

**`refactoring`**:
The [skill](../../../mmw-v4/skills/refactoring/SKILL.md) for a structural change preserving a pinned behavioral contract. It supplies preparation, implementation and verification methods rather than a separate delivery workflow.

**`improve-codebase-architecture`**:
The [skill](../../../mmw-v4/skills/improve-codebase-architecture/SKILL.md) for finding and ranking module-deepening opportunities or recording a rejected candidate. Its requested result is an architecture report or feedback, not implementation.

**`codebase-design`**:
The [skill](../../../mmw-v4/skills/codebase-design/SKILL.md) holding the module-design vocabulary and judgments about depth, interfaces and seams. Its native glossary defines Module, Interface, Implementation, Depth, Seam, Adapter, Leverage and Locality.

**`blast-radius`**:
The [skill](../../../mmw-v4/skills/blast-radius/SKILL.md) for identifying and proving risks a change creates outside its immediate diff. It is distinct from how and why explanations.

**`benchmark-checklist`**:
The [skill](../../../mmw-v4/skills/benchmark-checklist/SKILL.md) for establishing what a performance measurement ran, its limiter and the scope its number supports.

**`arena`**:
The [skill](../../../mmw-v4/skills/arena/SKILL.md) for comparing designs of the same task, choosing a base and integrating selected ideas into one verified result. It is distinct from Eval's blinded behavioral comparison.

**`no-comments`**:
The [skill](../../../mmw-v4/skills/no-comments/SKILL.md) for independent comment review and accepted in-scope cleanup, including workaround and suppression findings. Its named reviewer is Comment Sicko.

**`typescript-best-practices`**:
The [skill](../../../mmw-v4/skills/typescript-best-practices/SKILL.md) holding TypeScript-specific modeling and typing guidance. It applies principle-type-system-discipline to `.ts` and `.tsx` work.

### Method results

**Attempt**:
A hillclimb ticket's measured attempt record, including its hypothesis, change, before/after result and kept-or-reverted verdict. Attempt 0 is its prepared measurement baseline.

**architecture candidate**:
A proposed module-deepening opportunity in an improve-codebase-architecture report. An owner rejection is recorded as feedback rather than silently re-proposed by a later report.

**measurement baseline**:
The workload, harness and initial result used for a performance comparison. It is distinct from a settled decision baseline in a ticket's Read first.

**design tree**:
The dependency structure of decisions examined by grilling. Its frontier consists of the decisions whose prerequisites are already settled, distinct from an implementation frontier.

**research file**:
The Markdown file, citing each claim's source, that a researcher reports as its answer. Inside an effort, the unchanged file lives in the question's directory `efforts/<effort>/research/<ticket number>-<slug>/`; a research ticket's resolution comment points at the answer file.

### Decision maps

**`wayfinder`**:
The [skill](../../../mmw-v4/skills/wayfinder/SKILL.md) for charting a map when decisions exceed one session and resolving one decision at a time. A map call retains its fresh-session hand-back even when invoked by Develop a change.

**destination**:
The wayfinder map's stated end result, which fixes the effort's scope. A destination can be a decision or a spec rather than a code delivery.

**fog of war**:
In-scope decisions a wayfinder map anticipates but cannot yet phrase precisely. The map's Not yet specified section holds this uncertainty, distinct from Out of scope.

**map frontier**:
The open, unblocked and unclaimed decision tickets of a wayfinder map. It is distinct from the implementation frontier computed for a spec batch.

**HITL and AFK**:
The wayfinder distinction between a decision ticket requiring live human participation and one an agent can resolve alone. These classify how a decision is reached, not a ticket's implementation worker grade.
