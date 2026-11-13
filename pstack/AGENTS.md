# Working on pstack

When working on pstack, follow the [pstack glossary map](docs/GLOSSARY-MAP.md) to the relevant definitions and use their terms.

Link a bundled skill by its exact name and the relative path to its `SKILL.md`. Instructions copied outside the bundle use the skill name available to the receiving agent.

## Bring v5 Cloud methods into pstack

Migrate one item at a time. Keep the v5 Cloud instructions that teach the work. Fit them into pstack's routing and delegation. Read the v5 prompt and the relevant pstack guide in full, then trace the calls to the agent that uses the result. Identify who makes each decision and what they need at that point. [v5 Cloud skills](../mmw-v5-cloud/skills/) · [Routing guide](docs/guide/02-poteto-mode.md) · [Design guide](docs/guide/04-design.md)

When the two editions share a source, compare the v5 wording with the pstack copy and the original passage. Keep the pstack passage when it already does the job. Bring over applicable v5 instructions verbatim. Adapt the lines whose role, inputs or handoff actually change. Follow a conflict into an existing caller or recipient only as far as it affects this migration. [pstack source](../upstream/pstack/) · [Matt Pocock's skills](../upstream/mattpocock/skills/)

## Decide where an instruction belongs

| Where | What the instruction decides |
| --- | --- |
| Mode | In **Non-negotiables**, name the trigger and the action, route or stop it requires of the main chat, including when two routes overlap. Use **Principles** for decisions a principle changes, **Autonomy** for authorization, **Subagents** for shared delegation rules, and **Writing the reply** and **Comments** for shared style. **Playbooks** indexes routes by the request they serve. |
| Playbook | How the main chat takes a class of task to its requested result. It owns the order, the condition for calling a method, and the decision to continue, switch paths, hand back or stop. |
| Skill | How to perform one method on given inputs and produce a result the caller can judge. Its name and description identify when to use it. It can run several steps, call another skill or direct its own subagents. |
| Plan or brief | The files, symbols, targets and commands for this particular assignment. Put a fixed command or format in a playbook when its runs depend on that exact form. |

When a prompt mixes workflow and method, split it where the method returns its result. Keep a short local action in the step that needs it. For example, the mode calls for a measurement check before reporting a speedup. **Perf issue** decides when to take the baseline and remeasure. The [benchmark-checklist](skills/benchmark-checklist/SKILL.md) skill checks whether failed requests made the run look faster. **Hillclimb** uses the same method before freezing its benchmark. [poteto-mode](skills/poteto-mode/SKILL.md) · [Perf issue](skills/poteto-mode/playbooks/perf-issue.md) · [Hillclimb](skills/poteto-mode/playbooks/hillclimb.md)

Several workflows reuse **Opening a PR**. Its handoff is the open PR. A request to follow that PR goes to **Babysit**. The [figure-it-out](skills/figure-it-out/SKILL.md) skill supplies a method for designing and running a playbook for one large or unmatched task. **Orchestrate** runs a standing program. [Opening a PR](skills/poteto-mode/playbooks/opening-a-pr.md) · [Babysit](skills/poteto-mode/playbooks/babysit.md) · [Orchestrate](skills/poteto-mode/playbooks/orchestrate.md)

## Write a playbook

Use the input and requested outcome to distinguish the route in the mode's Playbooks index. A request to diagnose a captured startup profile selects **Trace forensics**. A request to fix measured startup slowness selects **Perf issue**. Put the body in `skills/poteto-mode/playbooks/<title>.md` using a lowercase, hyphenated title. Name the file in the index if it differs. [Trace forensics](skills/poteto-mode/playbooks/trace-forensics.md) · [Perf issue](skills/poteto-mode/playbooks/perf-issue.md)

Write backward from the handoff. The main chat copies the numbered steps into its checklist and records a reason for a skipped step. Order the steps by the evidence each needs. At a skill call, name the input, the result needed and how the main chat uses it. In the reply, name the artifact, its evidence and anything still open. **Multi-phase plan** returns the checked plan and names the execution playbook. Implementation starts on the operator's go. [Multi-phase plan](skills/poteto-mode/playbooks/multi-phase-plan.md)

```markdown
### <Playbook name>

**You own <outcome>.** <Input or scope that distinguishes this route.>

1. <Obtain what the next decision needs.>
2. <Act on it. Call the relevant skill where its result is needed.>
3. <Check the result. State when to stop or hand it back.>

**Reply:** <Deliverable, evidence and open decisions.>
```

Write just enough to choose the next step and know when the work is done. **Trace forensics** maps a hot frame to a source location and marks a single capture's finding as a hypothesis. The parser depends on the capture. When a playbook builds on another, write the differences once. **Autopilot-stack** reuses **Autopilot-full** and specifies the stacking rules and the verified handoff to the operator. [Trace forensics](skills/poteto-mode/playbooks/trace-forensics.md) · [Autopilot-stack](skills/poteto-mode/playbooks/autopilot-stack.md)

## Choose the delegate by who defines the work

**Direct playbook delegation.** The main chat runs the playbook, scopes an implementation or helper assignment, and checks the result. Give the `poteto-agent` the goal, scope, completion condition and the absolute path to the mode in its environment. It reads the mode and carries out the assigned step. **Feature** uses this path for a scoped implementation and keeps design and verification with the main chat. [Feature](skills/poteto-mode/playbooks/feature.md) · [poteto-agent role](agents/poteto-agent.md)

**Delegation inside a skill.** The main chat reads the skill and follows its method. The skill defines each delegate's role, what it receives, what it returns and how the main chat judges the result. In **Feature**, competing implementations go through [arena](skills/arena/SKILL.md). For a contested design, [interrogate](skills/interrogate/SKILL.md) briefs its own reviewers and has the main chat rerun their commands before accepting findings.

Read access and model choice are separate from who gives the instructions. **Multi-phase plan** directly assigns a `poteto-agent` to look up files and test commands. For a plan review, [ambiguity-scan](skills/ambiguity-scan/SKILL.md) sends a fresh, read-only general-purpose reviewer the draft, sources and Plan brief. Select the model assigned to the work role in the operator's model rule. Give new work to a fresh subagent and resume one when the assignment needs state costly to transfer, such as its uncommitted changes. [Multi-phase plan](skills/poteto-mode/playbooks/multi-phase-plan.md) · [setup-pstack](skills/setup-pstack/SKILL.md#model-rule)
