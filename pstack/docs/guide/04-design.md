# Design before you write code

One attempt at a hard design locks in the first shape the model thought of. [architect](../../skills/architect/SKILL.md) settles types and boundaries before implementation. [arena](../../skills/arena/SKILL.md) runs several attempts at the same brief and merges the best parts. [interrogate](../../skills/interrogate/SKILL.md) has other models try to break the result. When the job is coverage rather than design synthesis, [swarm](../../skills/swarm/SKILL.md) fans out slices or races and aggregates their results.

The two most common design mistakes are taking the agent's first design and polishing a plan that no code has tested. This page fixes both. You plan through code. Prototypes answer the open questions, a README or tutorial sets the target, and the written plan comes last.

![Three robots draft competing bridge models at their own tables under /architect, /arena, and /interrogate panels, while a judge robot with a clipboard inspects skeptically.](./images/design.jpg)

## Settle the shape with [architect](../../skills/architect/SKILL.md)

```text
/architect design the import pipeline before writing any code. i care most about how callers use it.
```

[architect](../../skills/architect/SKILL.md) grounds itself first, running [how](../../skills/how/SKILL.md) over the code the design touches and [why](../../skills/why/SKILL.md) when it moves ownership or layers. Then it runs [arena](../../skills/arena/SKILL.md) to produce competing design sketches, with the caller's usage written first in each, followed by types, signatures, and a module map.

By default it proceeds straight from the synthesized design into implementation. If you want to see the design first, say so:

```text
/architect with checkpoint. stop and show me before implementing.
```

The design isn't sacred once code starts. If implementation shows the same workaround in unrelated places, or types that only compile with `any` or forced casts, [architect](../../skills/architect/SKILL.md) treats that as proof the design is wrong. It scraps the sketch and starts over instead of patching around it.

## Fan out attempts with [arena](../../skills/arena/SKILL.md)

```text
/arena take my prompt to the arena verbatim. i want to compare their proposals with yours.
```

[arena](../../skills/arena/SKILL.md) is the general tool underneath. N subagents attempt the same design or code brief in parallel, each writing to its own worktree or directory. A read-only judge from a different model family scores every candidate against a rubric. When no model from another family can run, the coordinator skips the judge and picks the base itself. The coordinator reads each candidate end to end, picks a base, grafts in the best ideas from the losers, and verifies the result.

```mermaid
flowchart LR
    A[One task] --> B[Configured panel]
    B --> C[Candidate 1]
    B --> D[Candidate 2]
    B --> E[Candidate N]
    C --> F[Cross-judge]
    D --> F
    E --> F
    F --> G[Pick a base]
    G --> H[Graft the best parts]
    H --> I[Verify]
```

The panel comes from your [setup-pstack](../../skills/setup-pstack/SKILL.md) configuration, and you can adjust it per task. Ask for more candidates when the decision matters, fewer when it doesn't:

```text
/arena this, 5 candidates. the cache key format is expensive to change later.
```

## Cover slices and races with [swarm](../../skills/swarm/SKILL.md)

```text
/swarm check every package under packages/ against its check.sh. one worker per package. one report.
```

[swarm](../../skills/swarm/SKILL.md) fans N workers across independent slices, coverage matrices, gauntlet lanes, exploration partitions, or declared race arms. Each worker gets its own scope and check, then reports `PASS`, `ISSUES`, or `BLOCKED`. The parent waits for the workers and returns one compact report with any gaps or dropouts.

Reach for it when parallelism buys coverage or lets independent checks race. [arena](../../skills/arena/SKILL.md) gives every worker the same design or code brief, then picks a base and grafts the best parts. [swarm](../../skills/swarm/SKILL.md) covers slices or runs a race with a selection rule declared up front. It does not use the base-selection and grafting ceremony.

## Break it with [interrogate](../../skills/interrogate/SKILL.md)

```text
/interrogate the whole branch, but skeptically. no nitpicks unless it's an actual bug or regression.
```

[interrogate](../../skills/interrogate/SKILL.md) gives the change and its intent to adversaries on the configured models, and each tries to break it with a run against the real code. Adversaries find different failures. A finding survives only when rerunning its command shows a failure that breaks the intent. The report lists every verified finding with the adversaries that found it, then what each adversary dropped and why, and applies nothing.

Read the Dropped list too. You can override the verdict.

## Prototype instead of debating

Never take the first design. Ask for a few, and pick from evidence you can see:

```text
/poteto-mode prototype a few options for the new dropdown menu. take screenshots or videos for me to compare.
```

The [Prototype playbook](../../skills/poteto-mode/playbooks/prototype.md) builds throwaway sketches in a scratch directory, puts the variants behind one switcher, drives each one, and captures screenshots or timings. It also works for behavior and algorithms, not just UI. Prototypes are planning with code. They let the agent answer its own open questions by running something instead of asking you, and they leave room for an option you wouldn't have thought of.

The same idea scales up to a real design. Pair [architect](../../skills/architect/SKILL.md) with prototypes and keep a review gate:

```text
/poteto-mode we need rate limiting for external webhooks. /architect it first, and answer open questions with prototypes. let me review before proceeding.
```

Don't spend adversaries on an abstract plan. [interrogate](../../skills/interrogate/SKILL.md) drops every finding a run does not prove, so a plan with no code behind it gives them little to break. Let prototypes settle the questions, then review what got built.

## Write the README first for shared code

For a package or API that other code will use, start with the doc a user would read:

```text
/poteto-mode write a tutorial for how i would use the new config package first. then /teach me why it beats the current one.
```

Writing the tutorial first forces the caller's view. You describe the API to a hypothetical user and work back to the implementation. The doc also becomes a concrete target the agent checks its own work against. Name [technical-writing](../../skills/technical-writing/SKILL.md) when the doc itself matters, so a tutorial stays a tutorial instead of drifting into reference and explanation at once.

## Plan after the design settles

Use [to-spec](../../skills/to-spec/SKILL.md) to record the agreed behavior on the work issue. To turn the spec into a multi-phase plan, give the main chat the work issue or the reviewed draft.

```text
/poteto-mode turn this design into a plan. show the outcome of each phase, what it depends on, and how to verify it.
```

The [Multi-phase plan playbook](../../skills/poteto-mode/playbooks/multi-phase-plan.md) compares the spec's user stories with the current product. The plan records evidence for behavior that already works. For the remaining work, it describes the approach, outcomes, dependencies and checks across phases. It carries forward the test seams, approved prototypes and scope boundaries. The main chat publishes the checked plan in its own issue under the spec issue.

When you request tickets, [to-tickets](../../skills/to-tickets/SKILL.md#split) splits the remaining plan into independently assignable outcomes. Each execution ticket is a direct child of the spec issue. It links the plan issue, names the relevant phase or outcomes, states its acceptance criteria and names its direct blockers. A standalone problem with one deliverable uses the original issue as its ticket. Once you authorize execution, the agent writing the code receives the ticket and its assignment. Each code ticket links to its corresponding PR and the PR links back. A human action or an investigation can finish with evidence on the issue.

You can also ask [to-tickets](../../skills/to-tickets/SKILL.md#issue-template) to draft tickets directly from a settled discussion or spec. If the approach, dependencies or checks across phases still need planning, the main chat runs the planning playbook first.

For a migration, state the bar in the prompt:

```text
/poteto-mode plan the migration of our ui library to the new styling system. include visual regression checks for each phase. the result must match the original exactly, bugs included.
```

"bugs included" keeps the migration from quietly fixing things on the way, which would make the old and new output impossible to compare. For a project that spans many days, you can commit the plan to the repo for a while so other agents see the work in progress. Delete it when the work lands.

## How much design work does a task deserve?

You might be wondering whether every change needs this. No. Most changes need none of it. A rough ladder:

- A small, finished change you're unsure about needs [interrogate](../../skills/interrogate/SKILL.md) alone.
- A change that crosses function boundaries or moves ownership earns [architect](../../skills/architect/SKILL.md), which brings [arena](../../skills/arena/SKILL.md) with it.
- A standalone decision where independent attempts would help, like naming, formats, or an algorithm, is [arena](../../skills/arena/SKILL.md) directly.
- A coverage matrix, set of parallel checks, or race with declared arms is [swarm](../../skills/swarm/SKILL.md).
- An open question you could answer by running something, like a layout, a timing, or an approach, gets a prototype, not a debate.
- A contested design that's expensive to reverse gets [architect](../../skills/architect/SKILL.md), then [interrogate](../../skills/interrogate/SKILL.md) before shipping.
- Work that spans several phases gets a plan, written after the design settles.

[poteto-mode](../../skills/poteto-mode/SKILL.md) already applies this ladder. Boundary-crossing work triggers [architect](../../skills/architect/SKILL.md) on its own, so you reach for these directly mainly when you want more or less scrutiny than the default.

Next: [Build and clean the change](./05-build-and-clean.md).
