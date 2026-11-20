# Working on mmwstack

When working on mmwstack, follow the [mmwstack glossary map](mmwstack/docs/GLOSSARY-MAP.md) to the relevant definitions and use their terms.

## How mmwstack works with the Home Repo

**Respect the Home Repo boundary.** Every agent session starts in the Home Repo, which holds owner instructions, the model rule, native host adapters, and the installed skill library. `mmwstack` is the portable skill-pack source installed into it. Keep host-specific wiring in the Home Repo's adapters and setup docs. Keep host-specific subagent dispatch in [host-dispatch.md](mmwstack/skills/mmw-mode/references/host-dispatch.md) rather than inside general playbooks or skill bodies.

**Trace prompt loading across work stages.** Before editing a prompt, trace what is already in context at that stage: persistent instructions, [mmw-mode](mmwstack/skills/mmw-mode/SKILL.md) when active, the selected playbook, the invoked skill, and any disclosed references. Keep direct skill calls working when the operator skips `mmw-mode` by routing delegation through [Subagents](mmwstack/skills/mmw-mode/SKILL.md#subagents) instead of repeating mode rules in each skill.

**Protect upstream prompt craft and glossary unity.** Most `mmwstack` prompts are adapted from [pstack](upstream/pstack/) and [Matt Pocock's skills](upstream/mattpocock/skills/). Their wording carries each method's intent, so edit surgically instead of rewriting or paraphrasing freely. Reuse existing terms from the [mmwstack glossary map](mmwstack/docs/GLOSSARY-MAP.md) and the Home Repo glossary rather than coining new terms or synonyms, so every agent moving across skills shares one vocabulary and mental model.

## Bring upstream changes into mmwstack

**[pstack](upstream/pstack/) updates.** Diff the upstream snapshots first. Compare each changed method with its mmwstack counterpart, accounting for renamed skills and playbooks. Apply the upstream change where it fits; preserve mmwstack's routing, model choices and handoffs.

**[Matt Pocock's skills](upstream/mattpocock/skills/).** Read the source method and find the mmwstack step that needs its result. Extend that step if it already owns the decision. Add a separate skill only when a caller needs a distinct method and can judge its result.

For either source, trace the changed method from its trigger to the caller that uses its result.

For investigations, report findings. For proposals, state the decision rule and give an example that distinguishes the proposed behavior from the current one.

## Write instructions for agents

Write English prompts with the host's installed `writing-for-agents`. Use mmwstack's authoring guidance for skills and custom modes. Keep one operation's steps together. Use a separate reference for a branch that other callers can skip in full. [Customization guide](mmwstack/docs/guide/09-make-it-yours.md)

Record each meaning in its domain glossary, qualifying a word that has different meanings across contexts. [mmwstack glossary map](mmwstack/docs/GLOSSARY-MAP.md)

Use the canonical English names for issues and ticket types in every language, including replies and diagrams. Record discarded translations under `_Avoid_` beside the term they referred to. [Planning and tickets](mmwstack/docs/glossary/planning-and-tickets/GLOSSARY.md)

Link a bundled skill by its exact name and the relative path to its `SKILL.md`. Instructions copied outside the bundle use the skill name available to the receiving agent.

Use one set of instructions across hosts. Specify who acts, the trigger and the required result. Each host uses its available tools. Replace imported `loop` or `automate` calls with the required capability, such as a scheduled wake with the original cadence and stop condition. [Unattended runs](mmwstack/docs/guide/07-overnight.md)

## Decide where an instruction belongs

| Where | What the instruction decides |
| --- | --- |
| Mode | **Non-negotiables** gives the main chat the trigger and required action, route or stop, including which route takes precedence. **Principles** names decisions a principle changes, **Autonomy** sets authorization, **Subagents** governs delegation, and **Writing the reply** sets shared style. **Playbooks** indexes tasks by requested outcome. |
| Playbook | How the main chat advances a class of task to delivery. It owns step order, when to call a method and what lets the chat continue, switch, stop or hand off. |
| Skill | How one method turns given inputs into a result the caller can judge. Its name and description identify when to use it. It can call other skills or direct its own subagents. |
| Plan or brief | The files, symbols, targets and commands for this particular assignment. Put a fixed command or format in a playbook when its runs depend on that exact form. |

Split a mixed prompt where the method returns its result. Keep a short local action in its step. Before reporting a speedup, the mode requires a measurement check. **Perf issue** applies it to the baseline. **Hillclimb** applies it before freezing a benchmark. The skill checks whether failed requests made the run look faster. [benchmark-checklist](mmwstack/skills/benchmark-checklist/SKILL.md) · [Perf issue](mmwstack/skills/mmw-mode/playbooks/perf-issue.md) · [Hillclimb](mmwstack/skills/mmw-mode/playbooks/hillclimb.md)

Read each principle you change in full. Compare the mode index entries and skill descriptions across mmwstack's principles. Match both styles. Each entry should let an agent recognize when the principle changes a decision, even without an explicit call from another skill. [mmw-mode](mmwstack/skills/mmw-mode/SKILL.md#principles) · [Principles guide](mmwstack/docs/guide/08-principles.md)

## Write a playbook

Route by input and requested outcome. **Trace forensics** diagnoses a captured startup profile. **Perf issue** fixes measured startup slowness. Put the playbook in `mmwstack/skills/mmw-mode/playbooks/<title>.md` using a lowercase, hyphenated title. Give the path in the mode index when the filename differs from that title. [Trace forensics](mmwstack/skills/mmw-mode/playbooks/trace-forensics.md)

Write backward from the handoff. The main chat uses the numbered steps as its checklist. Order steps by the evidence each needs. At a skill call, give the input, the required result and how the main chat uses it.

```markdown
### <Playbook name>

**You own <outcome>.** <Input or scope that distinguishes this route.>

1. <Obtain what the next decision needs.>
2. <Act on it. Call the relevant skill where its result is needed.>
3. <Check the result. State when to stop or hand it back.>

**Reply:** <Deliverable, evidence and open decisions.>
```

Write just enough to choose the next step and recognize completion. **Opening a PR** returns the open PR. **Babysit** follows it. When a playbook builds on another, write only the differences, as **Autopilot-stack** does for stacking and handoff. [Opening a PR](mmwstack/skills/mmw-mode/playbooks/opening-a-pr.md) · [Babysit](mmwstack/skills/mmw-mode/playbooks/babysit.md) · [Autopilot-stack](mmwstack/skills/mmw-mode/playbooks/autopilot-stack.md)

## Choose the delegate by who defines the work

**Direct playbook delegation.** The main chat owns the playbook, defines the assignment and checks the result. Give the `mmw-agent` its goal, scope and completion condition. **Feature** delegates scoped implementation this way. [Feature](mmwstack/skills/mmw-mode/playbooks/feature.md) · [mmw-agent role](mmwstack/agents/mmw-agent.md)

**Delegation inside a skill.** The skill defines each role, its inputs, its result and how the main chat judges it. **Feature** uses [arena](mmwstack/skills/arena/SKILL.md) for competing implementations. For Spec, Plan or Ticket review, [ambiguity-scan](mmwstack/skills/ambiguity-scan/SKILL.md) briefs one fresh, read-only general-purpose reviewer. It checks the draft against its sources and the stage's writing requirements. It reviews a ticket batch as a whole.

In mmwstack delegation prompts, assign new work to a fresh subagent. Resume one when the assignment needs state costly to transfer, such as uncommitted changes. Keep delegation within the assignment and follow the skill's fallback when the host cannot spawn. Name the work role in the prompt. Use only the model assigned to that role in the operator's model rule, including an explicit choice to inherit. [mmw-mode](mmwstack/skills/mmw-mode/SKILL.md#subagents)

## Connect a new workflow to the existing skills

- **Work issues.** Route new repository tasks, including read-only work and directly named skills, through [to-tickets](mmwstack/skills/to-tickets/SKILL.md). **Open** creates or reuses the GitHub work issue before work starts. **Update** records evidence, decisions, handoffs and results. **Split** drafts independently verifiable tickets with direct blockers. This skill owns the labels and the shared template's **Must have** and **Optional** fields.
- **Planning.** [Wayfinder](mmwstack/skills/mmw-mode/playbooks/wayfinder.md) records cross-session decisions on a map. A spec drawn from that map links back to it. [to-spec](mmwstack/skills/to-spec/SKILL.md) records agreed behavior. Use [Multi-phase plan](mmwstack/skills/mmw-mode/playbooks/multi-phase-plan.md) when requested or when the approach, dependencies or checks need planning across phases. The spec issue is the direct parent of the plan issue and execution tickets drawn from that scope. Each ticket drawn from the plan links to the plan issue and names its phase or outcome. A standalone problem with one deliverable becomes a ticket on the original issue. [Ticket splitting](mmwstack/skills/to-tickets/references/split.md)
- **Code delivery.** On authorized execution, open or reuse one PR per code ticket and link them both ways. Pass the ticket URL, scope, acceptance criteria and any existing PR URL through each handoff to the agent writing the code.
- **Visualization.** Replace imported `visualize` or `canvas` calls with the HTML skills. For visual explanations, including the whole spec, use [big-pics-little-words](mmwstack/skills/big-pics-little-words/SKILL.md) with [html](mmwstack/skills/html/SKILL.md).
- **App verification.** Route the caller to the project's `verify-<app>` for the target app and surface. Only when none matches, use [verify-this](mmwstack/skills/verify-this/SKILL.md). Keep its internal calls to [control-cli](mmwstack/skills/control-cli/SKILL.md) for terminals and [control-ui](mmwstack/skills/control-ui/SKILL.md) for graphical interfaces.
