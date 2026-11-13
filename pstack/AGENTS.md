# Working on pstack

When working on pstack, follow the [pstack glossary map](docs/GLOSSARY-MAP.md) to the relevant definitions and use their terms.

## Bring v5 Cloud methods into pstack

Use this repository's `pstack/` as the base. Migrate one v5 Cloud method at a time into pstack's routing, playbooks and delegation.

1. Read the v5 skill, its pstack counterpart if one exists, and the relevant guide in full. Trace the calls to the agent that uses the result. Distinguish source requirements, agent judgment and operator decisions. Say where the source leaves a choice open. [v5 Cloud skills](../mmw-v5-cloud/skills/) · [Routing guide](docs/guide/02-poteto-mode.md) · [Design guide](docs/guide/04-design.md)
2. For a shared upstream, compare the v5 wording, the pstack copy and the original passage. Separate the reusable method from the old v5 routing. Keep pstack wording that already does the job. Decide what to supplement, replace or split, and carry applicable v5 instructions over verbatim. [pstack source](../upstream/pstack/) · [Matt Pocock's skills](../upstream/mattpocock/skills/)
3. Change only the lines whose responsibility, inputs, route or handoff change. Revisit a previous import or another pstack prompt only for a conflict in this call chain. Reuse an existing step when it already covers the requirement.

For an investigation-only request, report findings. In a proposal, state the decision rule, illustrate it with a distinguishing example and identify what is proposed or already implemented. Honor requests to leave edits uncommitted.

## Write instructions for agents

Write English prompts with the host's installed `writing-for-agents`. Use pstack's authoring guidance for skills and custom modes. Keep one operation's steps together. Use a separate reference for a branch that other callers can skip in full. [Customization guide](docs/guide/09-make-it-yours.md)

Keep a v5 term for a distinct concept. If both editions name the same concept, choose the clearer term for that context. Record each meaning in its domain glossary, qualifying a word that has different meanings across contexts. [pstack glossary map](docs/GLOSSARY-MAP.md)

Use the canonical English names for issues and ticket types in every language, including replies and diagrams. Record discarded translations under `_Avoid_` beside the term they referred to. [Planning and tickets](docs/glossary/planning-and-tickets/GLOSSARY.md)

Link a bundled skill by its exact name and the relative path to its `SKILL.md`. Instructions copied outside the bundle use the skill name available to the receiving agent.

Use one set of instructions across hosts. Specify who acts, the trigger and the required result. Each host uses its available tools. Replace imported `loop` or `automate` calls with the required capability, such as a scheduled wake with the original cadence and stop condition. [Unattended runs](docs/guide/07-overnight.md)

## Decide where an instruction belongs

| Where | What the instruction decides |
| --- | --- |
| Mode | **Non-negotiables** gives the main chat the trigger and required action, route or stop, including which route takes precedence. **Principles** names decisions a principle changes, **Autonomy** sets authorization, **Subagents** governs delegation, and **Writing the reply** and **Comments** set shared style. **Playbooks** indexes tasks by requested outcome. |
| Playbook | How the main chat advances a class of task to delivery. It owns step order, when to call a method and what lets the chat continue, switch, stop or hand off. |
| Skill | How one method turns given inputs into a result the caller can judge. Its name and description identify when to use it. It can call other skills or direct its own subagents. |
| Plan or brief | The files, symbols, targets and commands for this particular assignment. Put a fixed command or format in a playbook when its runs depend on that exact form. |

Split a mixed prompt where the method returns its result. Keep a short local action in its step. Before reporting a speedup, the mode requires a measurement check. **Perf issue** applies it to the baseline. **Hillclimb** applies it before freezing a benchmark. The skill checks whether failed requests made the run look faster. [benchmark-checklist](skills/benchmark-checklist/SKILL.md) · [Perf issue](skills/poteto-mode/playbooks/perf-issue.md) · [Hillclimb](skills/poteto-mode/playbooks/hillclimb.md)

Read each principle you change in full. Compare the mode index entries and skill descriptions across pstack's principles. Match both styles. Each entry should let an agent recognize when the principle changes a decision, even without an explicit call from another skill. [poteto-mode](skills/poteto-mode/SKILL.md#principles) · [Principles guide](docs/guide/08-principles.md)

## Write a playbook

Route by input and requested outcome. **Trace forensics** diagnoses a captured startup profile. **Perf issue** fixes measured startup slowness. Put the playbook in `skills/poteto-mode/playbooks/<title>.md` using a lowercase, hyphenated title. Give the path in the mode index when the filename differs from that title. [Trace forensics](skills/poteto-mode/playbooks/trace-forensics.md)

Write backward from the handoff. The main chat uses the numbered steps as its checklist and records reasons for skips. Order steps by the evidence each needs. At a skill call, give the input, the required result and how the main chat uses it.

```markdown
### <Playbook name>

**You own <outcome>.** <Input or scope that distinguishes this route.>

1. <Obtain what the next decision needs.>
2. <Act on it. Call the relevant skill where its result is needed.>
3. <Check the result. State when to stop or hand it back.>

**Reply:** <Deliverable, evidence and open decisions.>
```

Write just enough to choose the next step and recognize completion. **Opening a PR** returns the open PR. **Babysit** follows it. When a playbook builds on another, write only the differences, as **Autopilot-stack** does for stacking and handoff. [Opening a PR](skills/poteto-mode/playbooks/opening-a-pr.md) · [Babysit](skills/poteto-mode/playbooks/babysit.md) · [Autopilot-stack](skills/poteto-mode/playbooks/autopilot-stack.md)

## Choose the delegate by who defines the work

**Direct playbook delegation.** The main chat owns the playbook, defines the assignment and checks the result. Give the `poteto-agent` its goal, scope, completion condition and the absolute path to the mode it must read. **Feature** delegates scoped implementation this way. **Multi-phase plan** delegates read-only lookup the same way. [Feature](skills/poteto-mode/playbooks/feature.md) · [poteto-agent role](agents/poteto-agent.md)

**Delegation inside a skill.** The skill defines each role, its inputs, its result and how the main chat judges it. **Feature** uses [arena](skills/arena/SKILL.md) for competing implementations. For Spec, Plan or Ticket review, [ambiguity-scan](skills/ambiguity-scan/SKILL.md) briefs one fresh, read-only general-purpose reviewer. It checks the draft against its sources and the stage's writing requirements. It reviews a ticket batch as a whole.

In pstack delegation prompts, assign new work to a fresh subagent. Resume one when the assignment needs state costly to transfer, such as uncommitted changes. Name the work role in the prompt. Use only the model assigned to that role in the operator's model rule, including an explicit choice to inherit. [poteto-mode](skills/poteto-mode/SKILL.md#subagents) · [setup-pstack](skills/setup-pstack/SKILL.md#model-rule)

## Connect a new workflow to the existing skills

- **Work issues.** Route new repository tasks, including read-only work and directly named skills, through [to-tickets](skills/to-tickets/SKILL.md). **Open** creates or reuses the GitHub work issue before work starts. **Update** records evidence, decisions, handoffs and results. **Split** drafts independently verifiable tickets with direct blockers. This skill owns the labels and the shared template's **Must have** and **Optional** fields.
- **Planning.** [Wayfinder](skills/poteto-mode/playbooks/wayfinder.md) records cross-session decisions on a map. A spec drawn from that map links back to it. [to-spec](skills/to-spec/SKILL.md) records agreed behavior. Use [Multi-phase plan](skills/poteto-mode/playbooks/multi-phase-plan.md) when requested or when the approach, dependencies or checks need planning across phases. The spec issue is the direct parent of the plan issue and execution tickets drawn from that scope. Each ticket drawn from the plan links to the plan issue and names its phase or outcome. A standalone problem with one deliverable becomes a ticket on the original issue. [Ticket splitting](skills/to-tickets/references/split.md)
- **Code delivery.** On authorized execution, open or reuse one PR per code ticket and link them both ways. Pass the ticket URL, scope, acceptance criteria and any existing PR URL through each handoff to the agent writing the code.
- **Visualization.** Replace imported `visualize` or `canvas` calls with the HTML skills. For visual explanations, including the whole spec, use [big-pics-little-words](skills/big-pics-little-words/SKILL.md) with [html](skills/html/SKILL.md).
- **App verification.** Route the caller to the project's `verify-<app>` for the target app and surface. Only when none matches, use [verify-this](skills/verify-this/SKILL.md). Keep its internal calls to [control-cli](skills/control-cli/SKILL.md) for terminals and [control-ui](skills/control-ui/SKILL.md) for graphical interfaces.
