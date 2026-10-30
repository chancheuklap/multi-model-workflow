# Handling a request

Read in full by a session holding a request: a session whose first message names no file to follow, usually one the owner opened. A session holding an assignment reads only the section its own file names. The mode's `SKILL.md` holds what every session works by; this file holds what only a session holding a request uses: the triggers for the task as a whole, sending sessions, the reply to the owner, and the route to a playbook.

## Non-negotiables

Triggers for the task as a whole:

- Nontrivial change, architecture decision, or "are we sure?" → the **how** skill.
- Before asking the user to choose an approach → establish whether evidence can settle it. Look up facts yourself; use the **prototype** skill for questions that need a runnable experiment. A read-only Investigation answers from evidence and stays read-only.
- Design bakeoffs with base selection and grafting → the **arena** skill.
- Broken skill mid-task → the **register-problem** skill.
- The owner corrects your work → the **register-problem** skill, using its `scripts/register.py add --source owner-correction`.
- Authoring or modifying a skill, with text one ticket can carry → this session writes the text; scripts go to a worker, as `playbooks/authoring-a-skill.md` says.
- A sentence or two the owner corrects after a ticket passed → this session makes the correction without reopening the ticket or sending another worker, as One ticket step 4 (`playbooks/one-ticket.md`) says.
- Owner-named deletion of skill text that needs no replacement → this session does it without a ticket, following **Pure deletion** in `playbooks/authoring-a-skill.md`.
- Generating or maintaining verification assets outside an effort → the **create-verification-skill** or **maintain-verification-skill** skill commits directly on the project branch without a ticket.

## Autonomy

**Discussion and execution.** A discussion question asks for an answer, not a change; when unclear, treat it as a question. An approved plan or ticket authorizes completion, stopping only for a decision that belongs to the owner.

**Full autonomy.** "Don't stop", "going to bed", "run until done" or "be fully autonomous" means keep going. Under that grant, decide the calls it covers and apply defaults for owner-only decisions. Report each default with its reason and how the owner can change it. The owner's named gates and the mode's **Always pause** list still require the owner.

## Subagents

**Send a session with the dispatch skill:** `dispatch.sh send worker|reviewer <ticket number>`, or `dispatch.sh send <role> --follow "<the file it works by>" <brief file>...` for a role its `roles.json` sends with a brief; each runs on the model `~/.mmw/models.json` gives its role. A brief is a file with `## Task`, `## Known` and `## For`, written for a reader that sees none of this conversation (**principle-write-for-where-it-is-read**); the step that sends it says what goes in each. End your turn after sending. When the relay wakes you, follow the dispatch skill's `## On waking` first, then the step that sent it.

**A second opinion is a session: `send advisor --follow "the advisor skill" <brief>`.** Ask for one before an architecture choice, a data migration, a big refactor or an API shape is committed, when one problem has resisted two attempts, or before a disputed reading of the task is treated as settled; not for what reading the code can settle. The brief carries the decision, not a narrowed question: the recent exchange quoted, your understanding, the constraints, the options and which way you lean, the paths you think matter. Leave out what to check and the conclusion you expect. For a problem that resisted two attempts, each attempt and what it produced is the core of the evidence. A choice you could reverse in minutes is not worth a session. The answer is advice: take it, or set it aside with a reason; its section for the owner goes to the owner as it stands. Do not ask again to get a different answer. A second consultation is for a new decision, or for the evidence the advisor said would change its answer.

## Writing the reply

Write for the owner per **principle-write-for-where-it-is-read**. Explain the problem, the choice and its reason, the effect on the product, and the limits. Use source names and make each reference understandable where it stands, per **principle-anchor-every-reference**.

- **Size the account to the task.** A small change gets a sentence or two; a design choice, an incident or a walkthrough gets the detail the owner needs. Keep every item the playbook's reply requires, including warnings, numbers and preconditions.
- **Use established terms and plain words.** Explain a technical term once when it enters the conversation.
- **A decision for the owner.** Explain what raised it, the product effect of each option, and your recommendation with its reason. Let the owner answer in their own words, without a shorthand token.
- **Use lists and tables when they help.** Follow the owner's formatting preference.
- **Give checkable evidence.** Apply **principle-calibrate-claims-to-evidence**. Show the command, flow, stored value, screenshot or failing line that supports the conclusion. Link only artifacts you read or produced. Run a check yourself when you can.
- **State the limits.** Say what you did not touch or check, because the owner cannot inspect the diff.

Each playbook's `**Reply:**` names the content unique to it. Work a ticket reports through its closing comment. Link a pull request as `https://github.com/<owner>/<repo>/pull/<number>` when one exists.

## Playbooks

Match the task to a playbook below and open its file.

A ticket with acceptance criteria is worked only by a worker the dispatch skill sends. Given one with no `Playbook:` line under its `## Problem`, run One ticket (`playbooks/one-ticket.md`) on it and tell the owner. An open ticket of ours given to this session, one whose `## Problem` has a `Playbook:` line, is picked up as Session pickup says. Asked what is waiting, list the `needs-triage` queue and the tickets waiting for the owner's go, both as `references/github-issues.md` `## When a playbook says "publish"` and `## Three label sets` give them.

Outside a night, a change normally goes through its playbook's ticket and the owner's go, then One ticket.

- **Work a ticket.** Sent by the dispatch skill to a ticket with acceptance criteria: claim it, build it until its criteria pass and it is reviewed, close it. Distinct from Feature, Bug fix, Perf issue and Hillclimb, which take a problem still open and decide how to build. `playbooks/work-a-ticket.md`.
- **Code review.** Reviewing a pull request another author opened. The **code-review** skill.
- **Investigation.** Read-only question: how does X work, why was Y built this way, are we sure about Z, should we do X or Y; also a doubt about a part of MMW's skill set that the owner wants understood, which becomes Authoring or modifying a skill once the owner asks for a change. `playbooks/investigation.md`.
- **Chart the map.** A loose idea too big for one agent session, with the way to the destination not yet visible ("wayfinder"). Charts it as a shared map of decision tickets on GitHub issues. `playbooks/chart-the-map.md`.
- **Work through the map.** An existing wayfinder map, given by URL or number, with or without a ticket. Resolves its next decision ticket, one per session. `playbooks/work-through-the-map.md`.
- **Grill with docs.** A plan or design to sharpen in one session, through a relentless interview that writes the glossary and ADRs as it goes. Distinct from Chart the map, which takes an idea too big for one session. `playbooks/grill-with-docs.md`.
- **To spec.** Recording settled decisions from a conversation, cleared map or supplied reference as a spec when one ticket cannot carry the change. `playbooks/to-spec.md`.
- **Revising a spec.** A section of a published spec has to change: the user asks, or To tickets sends a choice back to a spec decision. Edits the spec in place, never publishes a new one. `playbooks/revising-a-spec.md`.
- **To tickets.** Break a spec, plan, or conversation into tracer-bullet tickets with blocking edges, published as GitHub issues. `playbooks/to-tickets.md`.
- **Run a night.** A spec's unattended batch, from start or resumption through its PR and accepted merge. `playbooks/run-a-night.md`.
- **One ticket.** An owner-approved ticket outside a spec, or an owner-supplied ticket with acceptance criteria and no `Playbook:` line. `playbooks/one-ticket.md`.
- **Retrospective.** After one run, a night or one ticket, record each analyst conclusion on its registration without executing it; the owner decides what to do in a separate backlog review. Also run on the owner's request to review a named run. `playbooks/retrospective.md`.
- **Merging the lesson backlog.** When the owner asks to merge registrations, review all open registrations by root cause on one page, then apply only the owner's decisions. Distinct from Retrospective, which records one run's analysis without executing it. `playbooks/merging-the-lesson-backlog.md`.
- **Opening a PR.** Opening or settling a delivery PR for completed work, or promoting an owner-approved project branch. `playbooks/opening-a-pr.md`.
- **Bug fix.** A reported defect to reproduce, root-cause, and fix with runtime evidence. `playbooks/bug-fix.md`.
- **Perf issue.** A reported slowness to measure, trace and improve against a baseline. `playbooks/perf-issue.md`.
- **Hillclimb.** Sustained, scientific improvement of one metric against a target: loop hypotheses with before/after measurement, a decision log, and one commit per accepted win. Distinct from Perf issue, which is a one-off fix. `playbooks/hillclimb.md`.
- **Runtime forensics.** Diagnose a runtime symptom (leak, idle-CPU spin, glitch) from live instrumentation. The deliverable is a diagnosis, not a fix. `playbooks/runtime-forensics.md`.
- **Trace forensics.** Diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot) handed to you after the fact. The deliverable is a diagnosis, not a fix. `playbooks/trace-forensics.md`.
- **Feature.** New or changed behavior, built from a named data shape. `playbooks/feature.md`.
- **Refactoring.** A behavior-preserving change to structure or shape (rename, extract, inline, dedupe, move). This session pins the contract and plans the target shape into one ticket; a worker moves the code. `playbooks/refactoring.md`.
- **Improve the architecture.** Finding module-deepening opportunities before a particular refactor has been chosen. `playbooks/improve-the-architecture.md`.
- **Prototype.** A prototype kept in the repo to make a design or behavioral decision cheaply, or to settle an empirical fork by observing it instead of asking the human ("prototype", "mock it up", "try this layout", "sketch it to decide"). The **prototype** skill.
- **Authoring or modifying a skill.** Creating or changing a skill, principle, playbook, reference or its tooling, wherever maintained. Larger changes go to To spec. `playbooks/authoring-a-skill.md`.
- **Eval.** Testing how a skill, structure, or prompt change affects agent behavior before promoting it. `playbooks/eval.md`.
- **Set up a repository.** A repository MMW has not worked in yet, or a check-up of one ("set up MMW here", "is this repo ready for a night"): its labels, ignored directories and `scripts/check`. The **setup-mmw** skill.
- **Set up code checkers.** Creating scripts/check, or adding or replacing a language, sub-project or checker in it. `playbooks/set-up-code-checkers.md`.
- **Stop a repeated mistake.** On the owner's request, preventing a recurring agent mistake. The **correct** skill chooses the mechanism.
- **Session pickup.** Resuming or taking over a prior agent's in-flight work from a transcript, a pushed branch, or an open ticket of ours. `playbooks/session-pickup.md`.
- **Pause safely.** On an explicit request to pause ongoing work and leave a resumable checkpoint. `playbooks/pause-safely.md`.
- **Worktree and simulator cleanup.** Reclaiming local disk by pruning merged or abandoned git worktrees and stale iOS simulators ("what's using my disk", "clean up worktrees", "prune safe-to-prune worktrees", "free up space", "delete old simulators"). `playbooks/worktree-cleanup.md`.
