# pstack glossary map

Each context defines the words pstack uses to make a particular kind of decision. Start with the question you need to answer.

## Contexts

| Question | Context |
| --- | --- |
| Who selects a playbook, which model gets the brief, and how does a panel divide or compare the work? | [Routing and delegation](glossary/routing-and-delegation/GLOSSARY.md) |
| What lets a run continue without the operator, stop cleanly, or resume under another agent? | [Unattended runs](glossary/unattended-runs/GLOSSARY.md) |
| What questions remain on a map, what has been agreed, and which ticket can start? | [Planning and tickets](glossary/planning-and-tickets/GLOSSARY.md) |
| Which principle changes a design decision, what does a sketch settle, and what qualifies for a refactoring or comment removal? | [Engineering design](glossary/engineering-design/GLOSSARY.md) |
| What can an investigation establish about behavior, history, risk, or an earlier session? | [Investigation](glossary/investigation/GLOSSARY.md) |
| What can a benchmark, live process, or captured trace establish about a regression, leak, or stalled operation? | [Performance](glossary/performance/GLOSSARY.md) |
| Which artifact settles a visual question, catches the operator up, or sends an action to a bot? | [Design and presentation](glossary/design-and-presentation/GLOSSARY.md) |
| What claim did a check test, on which product path, and with what evidence? | [Product verification](glossary/product-verification/GLOSSARY.md) |
| Which property of the code was checked, under which bounds and assumptions? | [Formal verification](glossary/formal-verification/GLOSSARY.md) |
| How does a checked model become a reader's chart, and what can a marked state or loop show? | [Statechart](glossary/statechart/GLOSSARY.md) |
| Who owns the PR, what does its watcher report, and when is a stack or worktree ready for the next action? | [Pull request delivery](glossary/pull-request-delivery/GLOSSARY.md) |
| How are skills and personal modes written, how do task and teaching prompts differ, and what does a blind eval measure? | [Skill authoring](glossary/skill-authoring/GLOSSARY.md) |
| How does Benny route a report, establish who is fixing it, and verify a new or existing fix? | [Automation](glossary/automation/GLOSSARY.md) |

For a named principle, the [principles guide](guide/08-principles.md) lists the decision each rule changes and links to its instructions.

## Relationships

- The main chat selects a playbook and gives each [worker](glossary/routing-and-delegation/GLOSSARY.md#worker-assignments) a brief for its assignment. The model rule supplies the model for the role. A worker assigned as [PR owner](glossary/pull-request-delivery/GLOSSARY.md#the-pr-and-its-owner) owns that branch and PR. A replacement can take over both.
- A map issue is the parent of its decision tickets. Its decision frontier shows which questions a session can claim. A spec written from the map links to the recorded answers and approved prototypes. [Wayfinder decisions](glossary/planning-and-tickets/GLOSSARY.md#wayfinder-decisions)
- A spec issue is the direct parent of its [plan issue](glossary/planning-and-tickets/GLOSSARY.md#phases-and-decisions) and execution tickets. Tickets drawn from the plan link to it. Ticket splitting determines which outcomes can be assigned independently. During authorized implementation, a code ticket and its PR link to one another. The ticket frontier identifies work whose direct blockers are complete. The merge frontier identifies the lowest unmerged PR in a stack. [Ticket dependencies](glossary/planning-and-tickets/GLOSSARY.md#assignments-and-dependencies) · [PR stacks](glossary/pull-request-delivery/GLOSSARY.md#stacks-and-the-portion-that-can-land)
- A product spec states the agreed behavior. Its expected result becomes a ticket acceptance criterion. An approved prototype fixes the design question the operator settled. A proof artifact records what happened when the implementation was checked.
- A measurement baseline is a starting measurement. A visual parity baseline consists of frozen reference screenshots. A settled baseline records a decision the implementation must preserve. [Measurements](glossary/performance/GLOSSARY.md#benchmark-claims) · [Screenshot baselines](glossary/design-and-presentation/GLOSSARY.md#design-decisions-and-evidence) · [Settled decisions](glossary/engineering-design/GLOSSARY.md#engineering-decisions)
- A formal property states a promise about covered code. A TLC property is a formula configured for a model check. A counterexample trace records a path through the model. Replaying that path against the code tests whether the product has the defect. A captured performance trace records an actual execution. [Formal checks](glossary/formal-verification/GLOSSARY.md#verification-tools-and-evidence) · [Statechart rules](glossary/statechart/GLOSSARY.md#model-and-rules) · [Captured traces](glossary/performance/GLOSSARY.md#diagnosing-a-capture)
- The [arena](../skills/arena/SKILL.md) skill compares artifacts produced for the same task and picks one as the base for the result. A blind skill eval compares agent behavior to decide whether to promote a variant. A PR base is the branch a change targets.
- The decision trail records decisions across an unattended run. A hillclimb's decision log records the measurement for each attempt and whether the change was kept or reverted. [Decision trail](glossary/unattended-runs/GLOSSARY.md#the-decision-trail) · [Hillclimb experiments](glossary/performance/GLOSSARY.md#hillclimb-experiments)
- In a pstack run, a code ticket's PR opens ready for review. In Benny, a trusted bug or performance marker in the source thread makes a report eligible for reproduction. The automation can verify an existing fix or open a draft PR for a bounded fix of its own. [PR readiness](glossary/pull-request-delivery/GLOSSARY.md#the-pr-and-its-owner) · [Benny fixes](glossary/automation/GLOSSARY.md#existing-fixes-and-new-draft-fixes)

## What belongs in the glossary

Include a term when its pstack meaning changes a choice, responsibility, check, result, or handoff. A watcher verdict that occurs rarely belongs here if it determines what can happen to a PR. Give each sense one home. Record an alias where readers encounter it, and qualify a shared word when contexts use it differently.

Ordinary technical words keep their usual meanings. Filenames, commands, vendor names, and individual test cases belong with their source unless they name a distinct concept or state the reader needs to interpret.
