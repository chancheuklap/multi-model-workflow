# Routing and delegation

The main chat chooses how to carry out the operator's request. A delegate's brief sets its job, the model rule supplies its model, and the chosen method determines what comes back.

## Language

### People and instructions

**Operator**:
The person who directs the run, authorizes work, and decides product questions. A user story may describe someone else who uses the product.
_Avoid_: owner on its own when a PR owner could also be meant.

**Main chat**:
The conversation that receives the operator's request and runs the selected playbook. It owns the checklist and the delegations, checks what the agents produced, and reports to the operator.

**Invoker**:
The operator, playbook step, or skill that calls a skill and supplies its inputs. The skill returns its result to the invoker, who decides what happens next.
_Avoid_: caller for the invoker. A caller is code or a person that uses a module's interface.

**Skill**:
A named set of reusable instructions that an operator or another skill can invoke. A playbook can call a skill for one step.

**Playbook**:
A sequence of steps for a kind of task, such as an investigation or a bug fix. The operator can name the playbook inside the mode. The main chat copies its steps into the checklist and keeps a skipped step visible with its reason.

**Non-negotiable**:
A trigger in the mode that ties a condition to a required action, such as the throughput checkpoint for nontrivial multi-step work.

**Throughput checkpoint**:
A decision about how to divide work. It records what must finish first, which workstreams are independent, which writes would share state, and the smallest safe division. One worker can be the result.

**Subagent**:
An agent assigned a bounded part of the work. A routed skill can give it a role-specific brief. The parent remains responsible for the result. Under Guard the Context Window, a subagent that reads a large collection returns only its findings and their sources to its parent. [principle-guard-the-context-window](../../../skills/principle-guard-the-context-window/SKILL.md)

**poteto-agent**:
The delegate role that follows the installed mode for a playbook's code-writing and helper assignments. A skill can request it explicitly.

**Brief**:
The instructions one delegate receives. They state the operator's goal and the delegate's scope. For repository work, the brief identifies the assigned work issue, an existing PR when relevant, and the exact revision for a PR verifier. The brief received by the agent writing the code identifies its execution ticket and assigned change.

**Fresh subagent**:
A new agent session for an assignment. A replacement gets the original brief, later directives, and the previous agent's report and branch. Continuing with the same agent is reserved for work that needs its costly-to-transfer state, such as a running simulator.

[poteto-mode](../../../skills/poteto-mode/SKILL.md) · [poteto-help](../../../skills/poteto-help/SKILL.md) · [Feature playbook](../../../skills/poteto-mode/playbooks/feature.md) · [poteto-agent role](../../../agents/poteto-agent.md) · [ambiguity-scan](../../../skills/ambiguity-scan/SKILL.md)

### Worker assignments

**Worker**:
A subagent that carries out one assignment and returns a result its parent can inspect. For repository work, the worker's brief identifies its work issue and any existing PR it will work on. In Bug fix, a worker can return investigation findings with runtime evidence or implement the scoped fix. In Feature, a code delegate receives the file scope, named data shape, and success criteria. It produces the code change for the main chat to review and verify. [Bug fix playbook](../../../skills/poteto-mode/playbooks/bug-fix.md) · [Feature playbook](../../../skills/poteto-mode/playbooks/feature.md) · [poteto-mode](../../../skills/poteto-mode/SKILL.md)

In Orchestrate, a worker receives a kickoff with its goal, write boundaries, and the evidence it must produce. A worker also assigned as PR owner becomes the sole writer of that PR's branch. [Orchestrate playbook](../../../skills/poteto-mode/playbooks/orchestrate.md) · [PR owner](../pull-request-delivery/GLOSSARY.md#the-pr-and-its-owner)

A swarm worker receives one coverage slice or race arm and returns `PASS`, `ISSUES`, or `BLOCKED` with evidence for the coordinator's report. [swarm](../../../skills/swarm/SKILL.md)

**Execution playbook**:
The playbook that assigns authorized tickets and directs their delivery. It receives the `ready-for-agent` tickets whose direct blockers have cleared. A multi-phase plan names the execution playbook that determines who may merge and what the operator reserves for review. [to-tickets](../../../skills/to-tickets/SKILL.md) · [Multi-phase plan playbook](../../../skills/poteto-mode/playbooks/multi-phase-plan.md)

### Model assignments

**pstack model rule**:
The operator's saved assignments of models and settings to roles, normally in `~/.agents/pstack-models.md`. Nested delegates receive the same rule or the role lines they need. An assignment that cannot run leaves an unfilled role.

**Model role**:
A named kind of assignment in the model rule. Code assignments use `feature, refactoring`, `bug-fix`, `perf-issue`, or `hillclimb`. `hardest tasks` covers especially difficult work, and `judgment and prose` covers writing and judgment. A [research](../../../skills/research/SKILL.md) report and a factual lookup for [grilling](../../../skills/grilling/SKILL.md) both use `judgment and prose`. A single line can supply different briefs. For example, `reflect judgment, divergent, synthesizer` supplies two reviewers and a synthesizer.

**Reasoning budget**:
The operator's target reasoning level. The targets for `unlimited`, `large`, `medium`, and `small` are `max`, `xhigh`, `high`, and `medium`, respectively. Setup uses the highest supported level at or below the target. A fixed effort or speed for a role takes precedence over adjustments for an assignment.

**Speed (model role)**:
The choice of standard or fast execution for a delegate. Unless the operator fixed the role's speed, fast is reserved for failing CI, a broken trunk, or a person waiting on the result to proceed.

**Inherited model**:
The operator's explicit choice of `inherit-parent` or `auto`. Both values run the delegate on the parent's model with its inherited settings.

**Panel role**:
An assignment with one seat per entry in `arena runners`, `architect runners`, or `interrogate reviewers`. Two entries naming the same model supply two independent agents. Inherited entries also occupy seats. Arena can add runners for multiple design directions using the configured models. Architect applies Arena's runner rules to its own list. [setup-pstack](../../../skills/setup-pstack/SKILL.md) · [arena](../../../skills/arena/SKILL.md) · [architect](../../../skills/architect/SKILL.md)

**Arena cross-judge pool**:
The operator's ordered list of models from which one read-only judge is selected. Arena takes the first available model from a different family than the parent's. If the parent's family is unknown, Arena can use an explicitly named model and reports that it could not check the family. Inherited entries cannot judge.

**Second opinion**:
An independent answer to the same prompt from a different model.

[setup-pstack](../../../skills/setup-pstack/SKILL.md) · [reflect](../../../skills/reflect/SKILL.md) · [poteto-mode](../../../skills/poteto-mode/SKILL.md) · [arena](../../../skills/arena/SKILL.md)

### Swarm coverage and races

**Swarm**:
Parallel workers assigned independent portions of a task, the same task in a race, or a mixture of both. The `swarm workers` role supplies the worker model. The coordinator returns one report with the results, proved issues, and gaps.

**Coverage slice**:
The part of a swarm that one worker must check, such as one package in a repository. Coverage is complete when every required slice has a result.

**Race arm**:
One independent attempt at the same brief. A model race identifies the model for each arm up front. The predeclared selection rule takes the first passing result (`first pass`), ranks the results (`rank all`), or selects the best result (`best-of`).

**Swarm worker result**:
A worker's evidence and its status for the assigned check. `PASS` records a successful check, `ISSUES` records all defects the worker can prove, and `BLOCKED` records a check the worker could not complete. A measurement result identifies the requested revisions and method.

**Coverage gap**:
A required slice with no usable result. A **dropout** is a worker that returns no output. A worker can also leave a gap by returning results twice without the revisions or method its brief required.

[swarm](../../../skills/swarm/SKILL.md)

### Arena candidates and synthesis

**Arena**:
A comparison of independent attempts at one artifact. Each runner receives the same task. A task that assigns each runner a design direction differs between runners only in that direction. The parent chooses one candidate as the base, incorporates selected parts of others, and verifies the combined artifact.

**Runner**:
The agent that produces one independent answer to the Arena brief. Its **candidate** is the artifact it submits with a short rationale explaining alternatives it considered and rejected. An architect runner submits a design package under the same arrangement.

**Design direction**:
A distinct approach to the same brief, such as a different structure or trade-off. By default every runner receives the same brief and chooses its own direction. When the task asks for alternative interfaces to one module, each runner is assigned one of architect's [interface directions](../../../skills/architect/references/interface-directions.md) and the rest of its prompt stays identical. Arena adds runners when the task spans several directions. The wireframe sense is [layout direction](../design-and-presentation/GLOSSARY.md#visual-and-interaction-design).
_Avoid_: direction for a constraint that every runner receives.

**Arena rubric**:
Three to six criteria specific to the task, set before the runners start. The parent and the cross-judge score each candidate against these criteria. The runners see the task.

**Cross-judge**:
A read-only reviewer who scores completed candidates by path label and recommends a base with reasons. The parent reads every candidate and makes the final selection. If no eligible judge runs, the synthesis records that fact.

**Base (Arena)**:
The candidate the parent selects as the starting artifact for synthesis. A **graft** is a selected part of another candidate adapted to fit that base. When the candidates converge on the same design, the consensus can stand without a graft.

**Synthesis note**:
The record accompanying the verified Arena artifact. It identifies the base and why it won, the judge's verdict or absence, each graft and its source, rejected alternatives, any convergence or dropouts, and the verification result.

[arena](../../../skills/arena/SKILL.md) · [architect](../../../skills/architect/SKILL.md) · [Architect runner brief](../../../skills/architect/references/runner-prompt.md)

### Adversarial review

**Interrogate**:
A review in which independent adversaries try to break a change or design against its stated intent. The output reports the findings the parent can reproduce and what it dropped. Fixes are a separate assignment.

**Adversary**:
A reviewer given the scope, the intended behavior, and its own worktree. It reports the command it ran, the output it saw, and the output the intent required. For a design, the run can be a prototype or a probe of the current code.

**Verified finding (Interrogate)**:
A failure the parent reproduces by rerunning the adversary's command and can show violates the intent. The report combines findings with the same root cause, credits the adversaries that found them, and counts each adversary's dropped findings with reasons. A review can end with no verified findings.

[interrogate](../../../skills/interrogate/SKILL.md)
