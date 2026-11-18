# Routing and delegation

The main chat chooses how to carry out the operator's request. A delegate's brief sets its job, the model rule supplies its model, and the chosen method determines what comes back.

## Language

### People and instructions

**Operator**:
The person who directs the run, authorizes work, and decides product questions. A user story may describe someone else who uses the product.
_Avoid_: owner on its own when a PR owner could also be meant.

**Main chat**:
The conversation that receives the operator's request and runs the selected playbook. It owns the checklist and the delegations, checks what the agents produced, and reports to the operator.

**Execution environment**:
Where the host assigned the main chat's workspace for the task. Its value is `local` when the workspace runs on the operator's computer and `cloud` when it runs in a cloud workspace. Subagents inherit this value through their briefs, including when a replacement starts a new [run](../unattended-runs/GLOSSARY.md#the-decision-trail). [mmw-mode](../../../skills/mmw-mode/SKILL.md#subagents)

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

**Delegate**:
A subagent carrying out a scoped assignment. Code delegates, helpers, readers, investigators, runners, judges and reviewers are delegates.

**Needs reply**:
A delegate's reply `needs: <skill or step, and the inputs it needs>`, sent when a required step exceeds its tools and the skill has no applicable fallback. The parent supplies missing inputs, performs a step it is eligible to perform, or assigns an eligible agent in the task's execution environment. If the required step still cannot run, the parent reports it as blocked. [mmw-mode](../../../skills/mmw-mode/SKILL.md#subagents)

**Owner session**:
An agent session that carries an assignment as its own and starts delegates itself. A PR owner can take this role.
_Avoid_: delegate for an owner session, owner alone for the operator.

**mmw-agent**:
The delegate role that follows the installed mode for a playbook's code-writing and helper assignments. A skill can request it explicitly.

**Brief**:
The instructions one delegate receives. They state the task's execution environment, the operator's goal and the delegate's scope. For repository work, the brief identifies the assigned work issue, an existing PR when relevant, and the exact revision for a PR verifier. The brief received by the agent writing the code identifies its execution ticket and assigned change.

**Fresh subagent**:
A new agent session for an assignment. A replacement gets the original brief, later directives, and the previous agent's report and branch. Continuing with the same agent is reserved for work that needs its costly-to-transfer state, such as a running simulator.

[mmw-mode](../../../skills/mmw-mode/SKILL.md) · [mmw-help](../../../skills/mmw-help/SKILL.md) · [Feature playbook](../../../skills/mmw-mode/playbooks/feature.md) · [mmw-agent role](../../../agents/mmw-agent.md) · [ambiguity-scan](../../../skills/ambiguity-scan/SKILL.md)

### Worker assignments

**Worker**:
A subagent that carries out one assignment and returns a result its parent can inspect. For repository work, the worker's brief identifies its work issue and any existing PR it will work on. In Bug fix, a worker can return investigation findings with runtime evidence or implement the scoped fix. In Feature, a code delegate receives the file scope, named data shape, and success criteria. It produces the code change for the main chat to review and verify. [Bug fix playbook](../../../skills/mmw-mode/playbooks/bug-fix.md) · [Feature playbook](../../../skills/mmw-mode/playbooks/feature.md) · [mmw-mode](../../../skills/mmw-mode/SKILL.md)

The worker's kickoff names its goal, write boundaries and completion evidence. A worker assigned as [PR owner](../pull-request-delivery/GLOSSARY.md#the-pr-and-its-owner) is the sole writer of that PR's branch.

**Execution playbook**:
The playbook that assigns authorized tickets and directs their delivery. It receives the `ready-for-agent` tickets whose direct blockers have cleared. A multi-phase plan names the execution playbook that determines who may merge and what the operator reserves for review. [to-tickets](../../../skills/to-tickets/SKILL.md) · [Multi-phase plan playbook](../../../skills/mmw-mode/playbooks/multi-phase-plan.md)

### Model assignments

**mmwstack model rule**:
The operator's saved assignments of models and settings to roles, normally in `~/.agents/mmwstack-models.md`. Each host has its own section. A subagent that will delegate receives that section or the role lines it needs. An assignment that cannot run leaves an unfilled role.

**Model role**:
A named kind of assignment in the model rule. Autopilot starts its PR owner on `coder`. Autopilot and Shipping assign independent PR checks to `verifier`. Scoped code assignments use `feature, refactoring`, `bug-fix`, `perf-issue`, or `hillclimb`. `judgment and prose` covers writing and judgment, `advisor` covers consults of the advisor, `reader` covers a read-only assignment to read and report, and `code review` covers finished project-branch reviews. A single-agent [research](../../../skills/research/SKILL.md) report and a factual lookup for [grilling](../../../skills/grilling/SKILL.md) both use `judgment and prose`.

**Reasoning budget**:
The operator's target reasoning level. The targets for `unlimited`, `large`, `medium`, and `small` are `max`, `xhigh`, `high`, and `medium`, respectively. Setup uses the highest supported level at or below the target. A fixed effort or speed for a role takes precedence over adjustments for an assignment.

**Speed (model role)**:
The choice of standard or fast execution for a delegate. Unless the operator fixed the role's speed, fast is reserved for failing CI, a broken trunk, or a person waiting on the result to proceed.

**Inherited model**:
The operator's explicit choice of `inherit-parent` or `auto`. Both values run the delegate on the parent's model with its inherited settings.

**Panel role**:
An assignment with one seat per entry in `arena runners` or `architect runners`. Two entries naming the same model supply two independent agents. Inherited entries also occupy seats. Arena can add runners for multiple design directions using the configured models. Architect applies Arena's runner rules to its own list. [setup-mmwstack](../../../skills/setup-mmwstack/SKILL.md) · [arena](../../../skills/arena/SKILL.md) · [architect](../../../skills/architect/SKILL.md)

**Arena cross-judge pool**:
The operator's ordered list for one independent read-only judge. Arena uses the first available entry, including an explicitly inherited model. A candidate author cannot judge the submissions.

**Second opinion**:
An answer from a fresh agent given the same question.

**Advisor**:
The independent agent a decision owner consults at a major decision, when stuck, or when the operator asks. It reads the brief and the repository, returns a verdict, and edits nothing. The `advisor` role supplies its model. **Advisor mode** is the operator's instruction to consult it at those checkpoints for the rest of one conversation. [advisor](../../../skills/advisor/SKILL.md)

**Reader**:
The delegate role for an assignment that reads and reports, such as a large artifact, a chat transcript, or an event to watch, when no playbook or skill names a role for it. A reader is read-only and returns its findings with their sources. The `reader` role supplies its model. A **source reader** is one reader that a verification skill's [source wave](../product-verification/GLOSSARY.md#verification-skill-maintenance) assigns a single feature. A delegate that judges or writes uses `judgment and prose`. A person who reads a document, as in [reader load](../engineering-design/GLOSSARY.md#the-design-seen-by-its-callers), is a different sense. [mmw-mode](../../../skills/mmw-mode/SKILL.md#subagents)

[setup-mmwstack](../../../skills/setup-mmwstack/SKILL.md) · [mmw-mode](../../../skills/mmw-mode/SKILL.md) · [arena](../../../skills/arena/SKILL.md)

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

[arena](../../../skills/arena/SKILL.md) · [architect](../../../skills/architect/SKILL.md) · [Architect interface directions](../../../skills/architect/references/interface-directions.md)
