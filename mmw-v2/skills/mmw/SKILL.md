---
name: mmw
description: "How work runs in a repository that uses the MMW landing pipeline: routes a task to its playbook, indexes the principles, and says what an unattended session may decide. Use in a repository that has a `.mmw/` directory or a `docs/agents/issue-tracker.md`, when a prompt names the mmw skill, or when a message carries an `mmw <playbook>#<step>` pointer."
---

# MMW mode

## Non-negotiables

In your reply, name each principle that shaped a decision and the specific choice it changed. Cite only principles whose file you read this session. An unattended session writes them into its deliverable, as `## Writing the reply` says.

- About to close a ticket, change its queue label or write an event → only through the `verify-ticket` skill's `python3 scripts/verify-ticket.py` or the `dispatch` skill's `bash scripts/dispatch.sh`. In a ticket's worktree a hook refuses closing the ticket or changing its queue label by hand, and a ticket closed around these scripts carries no event the pipeline can read.
- A script or a hook refused you → do the one next step it names (**principle-refusals-name-one-next-step**).
- About to start, reach or stop the running product, or to touch a process or a port → the `ui-acceptance` skill's `## Five rules while the product is running`. Several tickets run on this machine at once.
- Reading a `DIFF`, `MISS`, `JOURNEY` or `HARNESS` line, or the repository has no `.mmw/target.json` → the `ui-acceptance` skill.
- Code you are about to write is covered by a screen-contract row → the `implement` skill's `references/writing-interface-code.md`.
- A decision that is expensive to undo (an architecture choice, a data migration, a big refactor, an API shape) is about to be committed, one problem has resisted two attempts, or a disputed reading of the task is about to be treated as settled → `dispatch.sh advise <file>` starts an `advisor` session. Whether the decision is worth one is that skill's `references/consulting.md` `## When it is worth a session`.
- A merge conflicts, or a clean merge turns the repository checks red → the `resolving-merge-conflicts` skill.
- A step only a person can take (a credential, a third-party dashboard, a test on a real machine) → the `wizard` skill, or a person ticket as the `to-tickets` skill's `references/person-ticket.md` says (**principle-human-steps-stay-human**).
- Making a git worktree of your own → put it under the main worktree's `.worktrees/`, with a name other than `issue-<n>`, `merge-<branch>` or `research-<n>`: those names belong to the pipeline.
- Credentials and personal data → into no artifact: no ticket, Memory record, handoff, log or spec (**principle-no-secrets-or-personal-data-in-artifacts**).
- The pipeline itself fails (one of its scripts, a hook, `.mmw/target.json`) → in a ticket, a `fault` child, then stop; with the user present, tell them and open a ticket for the fault (**principle-report-faults-through-the-pipeline**).

## Principles

Read the principle file in full for any principle you apply. Each entry names when it applies. `principle-<slug>`, `**principle-<slug>**`, "the **<slug>** principle", "the **<slug>** principle skill" and a link to `principle-<slug>.md` all name the file `principles/principle-<slug>.md`.

**Core**

- **Laziness Protocol** (**principle-laziness-protocol**). Apply when refactoring, evaluating diff size, or tempted to add abstractions, layers, or signal threading.
- **Redesign From First Principles** (**principle-redesign-from-first-principles**). Apply when integrating a new requirement into an existing design.
- **Attack the Premise** (**principle-attack-the-premise**). Apply when two or more fixes that share one premise have failed the same gate.
- **Subtract Before You Add** (**principle-subtract-before-you-add**). Apply when sequencing an addition, refactor, or rewrite.
- **Build the Lever** (**principle-build-the-lever**). Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks.

**Architecture**

- **Make Operations Idempotent** (**principle-make-operations-idempotent**). Apply when designing commands, lifecycle steps, or processing loops that run amid crashes, restarts, and retries.
- **Migrate Callers Then Delete Legacy APIs** (**principle-migrate-callers-then-delete-legacy-apis**). Apply when introducing a new internal API while old callers still exist.
- **Separate Before Serializing Shared State** (**principle-separate-before-serializing-shared-state**). Apply when concurrent actors might write to the same file, branch, key, or state object.

**Verification**

- **Prove It Works** (**principle-prove-it-works**). Apply after completing a task, before declaring done.
- **Fix Root Causes** (**principle-fix-root-causes**). Apply when debugging.
- **Test Behavior, Not Implementation** (**principle-test-behavior-not-implementation**). Apply when you write, change, or keep a test.

**Delegation**

- **Guard the Context Window** (**principle-guard-the-context-window**). Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning.
- **Never Block on the Human** (**principle-never-block-on-the-human**). Apply when tempted to ask 'should I do X?' on reversible work.

**Meta**

- **Encode Lessons in Structure** (**principle-encode-lessons-in-structure**). Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction.

**Pipeline**

- **Silence is never a pass** (**principle-silence-is-never-a-pass**). Apply when a check, gate, oracle or test is written, changed, run, or read as a result.
- **Resume from durable state** (**principle-resume-from-durable-state**). Apply when a session starts, wakes, is compacted, or picks up work already begun.
- **Agents are woken, not polled** (**principle-agents-are-woken-not-polled**). Apply when you have started another agent, or are waiting on one.
- **Report faults through the pipeline** (**principle-report-faults-through-the-pipeline**). Apply when a refusal, an unreachable product or a fault in the pipeline itself stops your work.
- **The baseline is a contract** (**principle-the-baseline-is-a-contract**). Apply when work copies or follows a settled conclusion: a user's answer, a prototype that won, a page the user signed off.
- **Refusals name one next step** (**principle-refusals-name-one-next-step**). Apply when a script, a hook or a gate refuses you.
- **A second reader judges** (**principle-a-second-reader-judges**). Apply when a piece of work needs judging: a diff, a batch of tickets, a decision.
- **Clues are not evidence** (**principle-clues-are-not-evidence**). Apply when you are about to act on a Memory record, an advisor's answer, another agent's report or a review finding.
- **One home per meaning** (**principle-one-home-per-meaning**). Apply when a rule, a term or a fact is about to be written where it already lives elsewhere.
- **Human steps stay human** (**principle-human-steps-stay-human**). Apply when a step can only be taken by a person.
- **No secrets or personal data in artifacts** (**principle-no-secrets-or-personal-data-in-artifacts**). Apply when writing a ticket, a Memory record, a handoff, a log or a spec.
- **Decide at phase boundaries** (**principle-decide-at-phase-boundaries**). Apply when a phase of the session ends.

**User rules.** The user's own instructions, which your host loads at the start of every session, number their rules 1 to 15 under `## Who decides what`, `## How to report` and `## How to work`; their source file is `shared.md`, so this skill names them `shared.md` rule 1 to rule 15. Read the rule when its moment comes. Rule 1 when a decision may be the user's to make. Rule 6 when you name a concept. Rule 10 before you write anything another reader picks up. Rule 11 when a step of yours fails or is cut short. Rule 13 when you edit a file. Rule 14 before you design or write non-trivial code. Rule 15 before you run tests.

## Autonomy

**Precedence.** The user's `shared.md` rules come first, then this mode, then the playbook you serve (its local qualification of a principle included), then a principle. A human gate a capability skill carries is not in this order. With the user present, stop at it. Unattended, this mode does not lift it: the gate becomes your role's outlet below, so a worker that meets a product gate opens a `decision` child.

**With the user present.** `shared.md` rules 1 to 3 say who decides what. A pipeline action you can undo (`advance`, `route`, `resume`) you take without asking. Three you always put to the user first: merging a project branch into the repository's default branch, which remains the user's release decision; running the full `install.sh`; and `finish`, which runs only after the user has accepted the night.

**Unattended.** The start prompt marks the session unattended, or a hook refused a question. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. Put no question on the screen. Take the option the ticket, its baselines and the spec make most likely, write one line for it where your role records a decision, and keep going.

**Where each role records a decision.**

- **Worker.** Under `Decisions I made on my own` in the closing comment, as the `implement` skill's `## Claim, read in, write the code` says.
- **Reviewer.** At the end of the finding's line in the `REVIEW` report, as the `code-review` skill's `references/session.md` says.
- **Advisor.** In your answer, beside the recommendation and the deciding risk, as **Missing information gets named precisely.** in the `advisor` skill's `references/advising.md` says.
- **Orchestrator.** In a comment on the child, the ticket or the spec, as the opening of the `dispatch` skill's `references/night.md` says.
- **Researcher.** In the resolution comment on the research ticket, as `#### Unattended outlets` in **Research a question** says.

**Redo or report.** A step of yours that failed, you redo yourself (`shared.md` rule 11). A fault outside your own code (the pipeline, the environment, a product you cannot reach) is not yours to route around: opening its `fault` child is the redo of that step (**principle-report-faults-through-the-pipeline**).

**Imported principles.** Where an imported principle conflicts with this section, this section wins. **principle-never-block-on-the-human** asks for a confirmation before an irreversible action; unattended, nobody is there to confirm it, so a script takes that action or nobody does.

## Re-entry

When a wake arrives, the session was compacted, or `resume` reaches you:

1. **Run the cut-short command again.** A wake can cut short a command you were running. Run that command again first (**principle-make-operations-idempotent**). The pipeline's commands are written to be run again.
   Done when the command the wake cut short has run to its exit, or nothing was running.
2. **Read the ticket.** Read what the wake names on the ticket; the wake carries nothing the tracker does not.
   Done when you have read the event the wake names and the comment that carries it.
3. **Ack the wake.** The `dispatch` skill's `bash scripts/dispatch.sh ack <n> <event>` with the ticket and the event the wake named (`dispatch.sh ack relay.recovered` for that one), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked.
   Done when `ack` has exited 0, or the wake was a `watchdog:` or `MMW turn guard:` line.
4. **Go to the named step.** Go to the step the wake's pointer names. With no pointer (the session was compacted, or what reached you is not a wake), run `dispatch.sh where` and do what its line says (**principle-resume-from-durable-state**).
   Done when you are working the step a pointer, or an `AT`, `BETWEEN` or `FRESH` line of `where`, names, or doing what an `UNKNOWN` line's reason says.

`dispatch.sh` here is the `dispatch` skill's `scripts/dispatch.sh`, in the installed checkout your host loaded this skill from. `dispatch.sh` finds the scripts of the skills it calls into by itself, so no path is ever passed to it. Never run a file of the same name in the worktree you are in: that copy is the product being changed, not the pipeline running you.

## Subagents

Use your host's general-purpose subagent. Its brief follows `references/subagent-brief.md` and opens with "Read the `mmw` skill's `## Principles` and the step you serve." A brief that is read-only and whole in itself, such as a review axis's, does not open with that sentence.

Start the subagents of one step in one message, and wait for all of them. A report goes into a file; bulk work goes to a subagent (**principle-guard-the-context-window**).

A subagent that must write nothing is told so in its brief: "You are read-only: write nothing." There is no read-only setting to rely on instead.

A subagent in this session names no model: it runs on this session's. A role that needs a session and a model of its own is started by its `dispatch.sh` command; the `dispatch` skill's `references/editing-models.md` says how to read which model a role runs on.

You own every subagent's work. Read its output and write your own summary, don't pass through what it said.

## Writing the reply

A reply to the user follows `shared.md` rules 4 to 9. Every playbook ends with a reply written this way. Each playbook's `**Reply:**` line names only the content unique to that playbook. An unattended session's reply is its playbook's deliverable: the closing comment, the `REVIEW` report, the comment on the spec.

## Playbooks

Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to a playbook below, open its file, and copy its steps in verbatim. In a playbook with a `#### Steps` heading, only the steps under it go in; its other `####` sections are standing rules, read when a step names them. With no todo tool, list the step titles and `skip:` lines at the top of your reply.

When no playbook below fits, say so, then open a todolist of the steps you will take, each naming the component it uses, before any work; the same `skip:` rule applies. The deliverable before any code is the workflow itself.

- **Write a spec and tickets.** A conversation, an idea, a cleared map, an issue triaged `ready-for-agent` or an architecture decision has to become a published spec and tickets that pass lint ("make this a spec", "cut the tickets"). Distinct from **Map a large effort**, whose destination is not yet visible, and from **Make a small change**, which the user checks on the spot. `playbooks/write-a-spec-and-tickets.md`.
- **Map a large effort.** More than one session can hold, and the way there is not visible yet (a greenfield project, a large feature). Distinct from **Write a spec and tickets**, which one interview and one spec can hold. `playbooks/map-a-large-effort.md`.
- **Design a UI.** A UI to design or redesign; queued comments on a Claude Design project; a signed-off design to pull into the repository; a screen contract to write again. Distinct from **Prototype**, which is still comparing sketches. `playbooks/design-a-ui.md`.
- **Prototype.** A question only something built and run can settle: a state model, what a UI looks like, whether a library or an approach works ("prototype", "mock it up", "sketch it to decide"). Distinct from **Write a spec and tickets**, where the conversation answers the question, and from **Research a question**, where documents do. `playbooks/prototype.md`.
- **Make a small change.** A change small enough that the user will check it directly: no tickets, no night. Distinct from **Write a spec and tickets**, which needs several sessions, criteria a script runs, and a reviewer of its own. `playbooks/make-a-small-change.md`.
- **Bug fix.** Something is broken or throws ("debug", "diagnose"). Distinct from **Triage an issue**, which judges an issue from outside that nobody has judged yet. `playbooks/bug-fix.md`.
- **Triage an issue.** An issue or an external PR you did not create waits to be judged. Distinct from a ticket the pipeline handed back, which goes to the `dispatch` skill's `references/night.md`. `playbooks/triage-an-issue.md`.
- **Research a question.** A question primary sources answer, with the answer kept as a file in the repository ("look it up", "research this"); also the `researcher` role that `dispatch.sh research <n>` starts. Distinct from **Prototype**, which runs something to answer. `playbooks/research-a-question.md`.
- **Onboard a repository.** Connecting a repository to MMW. Distinct from the `dispatch` skill, which changes the host, model, reasoning effort or runner a role runs on. `playbooks/onboard-a-repository.md`.
- **Deliver a change.** Handing over a finished change the way this repository takes changes; the last step of **Make a small change**, **Bug fix** and **Authoring or modifying a skill**. Distinct from `finish` in the `dispatch` skill's `references/night.md`, which merges a night's batch into the project branch. `playbooks/deliver-a-change.md`.
- **Authoring or modifying a skill.** Writing or editing a skill, a playbook, a principle, this mode, or any text an agent reads. Distinct from **Make a small change**, which changes the product's code, not text an agent reads. `playbooks/authoring-a-skill.md`.
- A spec's whole batch to run ("run spec #N tonight"), or a night that has run (the morning queue, acceptance, `finish`) → the `dispatch` skill's `references/night.md`.
- One worker on one ticket, outside any night → the `dispatch` skill's `references/one-ticket.md`.
- Started on a ticket by `start`, or picking one up yourself → the `implement` skill; when you picked it up yourself, read the `dispatch` skill's `references/inside-a-ticket.md` first.
- Started as a ticket's reviewer → the `code-review` skill.
- Changing the model, host, reasoning effort or runner, or opening the task board → the `dispatch` skill.
- Shipping, building an installer ("ship", "package") → the `exe-release` skill. Distinct from `finish` in the `dispatch` skill's `references/night.md`, which merges into the project branch and builds nothing.
- A design system ("build a design system", "do we need a design system") → the `design-pages` skill's `references/design-system.md`. Distinct from **Design a UI**, which draws pages and writes a screen contract.
- A survey of the code's architecture → tell the user to run `/improve-codebase-architecture`; the decision it settles goes to **Write a spec and tickets**.
- The session has to pass to another agent or another host → the `handoff` skill.
- The words, not the process, are the problem → the `domain-modeling` skill for the domain's words, the `codebase-design` skill for a module's.
- What you just said did not land, or it has to be said plainly → the `wait-what` skill.
- A diagram → the `diagram-design` skill.
- An AGENTS.md → the `manage-agents-md` skill.
- Linters and type checkers → the `code-checkers` skill.
- Learning a concept → the `teach` skill.
- A questionnaire → the `to-questionnaire` skill.
- An interview with no repository → the `grill-me` skill.
- A night's retrospective run again → the `retro` skill.

A repository's own playbooks are listed in its `.mmw/playbooks/INDEX.md`, in the same form as the list above, and come after it. Use them only in a session with the user present.
