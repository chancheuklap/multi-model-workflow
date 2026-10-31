# Handling a request

Read in full by a session holding a request: a session whose first message names no file to follow, usually one the owner opened. A session holding an assignment reads only the section its own file names. The mode's `SKILL.md` holds what every session works by; this file holds what only a session holding a request uses: the triggers for the task as a whole, sending sessions, the reply to the owner, and the route to a playbook.

## Non-negotiables

Triggers for the task as a whole:

- Before asking the user to choose an approach → establish whether evidence can settle it. Look up facts yourself; use the **prototype** skill for questions that need a runnable experiment. A read-only Investigation answers from evidence and stays read-only.
- Design bakeoffs with base selection and grafting → the **arena** skill.
- Broken skill mid-task → the **register-problem** skill.
- The owner corrects your work → the **register-problem** skill, using its `scripts/register.py add --source owner-correction`.
- Authoring or modifying a skill, with text one ticket can carry → this session writes the text; scripts go to a worker, as `playbooks/authoring-a-skill.md` says.
- A sentence or two the owner corrects after a ticket passed → this session makes the correction without reopening the ticket or sending another worker, as One ticket step 4 (`playbooks/one-ticket.md`) says.
- Owner-named deletion of skill text that needs no replacement → this session does it without a ticket, following **Pure deletion** in `playbooks/authoring-a-skill.md`.

## Autonomy

**Discussion and execution.** A discussion question asks for an answer, not a change; when unclear, treat it as a question. An approved plan or ticket authorizes completion, stopping only for a decision that belongs to the owner.

**Full autonomy.** "Don't stop", "going to bed", "run until done" or "be fully autonomous" means keep going. Under that grant, decide the calls it covers and apply defaults for owner-only decisions. Report each default with its reason and how the owner can change it. The owner's named gates and the mode's **Always pause** list still require the owner.

**Preparation decisions.** A selected item in `needs-triage` is permission to prepare it, not execution Go. Keep it waiting when the owner defers. On rejection add `wontfix` and close it as not planned. On a requested plan change revise the preparation and return it. Existing execution Go and the owner's prototype approval cover only their recorded scope; do not ask for that authority again or treat approval of a batch breakdown alone as permission to open the night. A plan beyond the agreed scope returns the new product decision to the owner.

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

Continue an active task at its known step. Owner feedback updates that task unless the owner changes the objective. Use Session pickup only to reconstruct an unknown position, preserving the issue, branch, proof and authority.

For a new request, select the requested result below and read its owning playbook or skill in full before acting or deciding a step is already covered. The route line names the entry; that entry supplies the method.

- A skill-set change uses Authoring or modifying a skill; that workflow delegates larger preparation to Develop a change. An ordinary code change needing preparation uses Develop a change, including one with an unresolved UI design.
- A UI design without implementation uses Design a UI. Requested candidates or experiments use the prototype result entry.
- Ready work uses One ticket or Run a night only on an execution request or existing Go. A spec batch uses Run a night even with one ticket.
- An independently requested method result uses Requested results and ends at that result.

A ticket with acceptance criteria is implemented only by a dispatched worker. Historical Playbook titles are context, not execution Go or instructions to open retired files. Keep the existing Authoring and pure-deletion exceptions.

Asked what is waiting, read whole lists with `gh issue list --state open --label needs-triage --limit 1000 --json number,title,labels` and `gh issue list --state open --label mmw:problem --limit 1000 --json number,title,labels`, showing planned problems without a queue label separately. `needs-triage` awaits the owner's selection; an open problem without it is still being prepared. Use `--paginate` and `?per_page=100` for API lists.

- **Design a UI.** Settle a UI design through a complete runnable prototype, the owner's trial and iterative feedback, ending with the confirmed winner and feature description. Distinct from candidate-only construction and from implementation preparation. `playbooks/design-a-ui.md`.
- **Develop a change.** Preparing a new or changed behavior, bug fix, performance improvement or structural change that still needs evidence, decisions or an executable plan. Reuse completed work; small changes need no spec. Distinct from a ready ticket or batch, which goes directly to its executor. `playbooks/develop-a-change.md`.
- **Work a ticket.** Sent by the dispatch skill to a ticket with acceptance criteria: claim it, build it until its criteria pass and it is reviewed, close it. Distinct from Develop a change, which prepares the work before a worker starts. `playbooks/work-a-ticket.md`.
- **Investigation.** Read-only question: how does X work, why was Y built this way, are we sure about Z, should we do X or Y; also a doubt about a part of MMW's skill set that the owner wants understood, which becomes Authoring or modifying a skill once the owner asks for a change. `playbooks/investigation.md`.
- **Grill with docs.** Settle a plan or design in one session while recording the glossary and qualifying ADRs. `playbooks/grill-with-docs.md`.
- **Run a night.** A spec's unattended batch, from start or resumption through its PR and accepted merge. `playbooks/run-a-night.md`.
- **One ticket.** Execute a ready independent ticket on the owner's execution request or existing Go for its scope. `playbooks/one-ticket.md`.
- **Retrospective.** After one run, a night or one ticket, record each analyst conclusion on its registration without executing it; the owner decides what to do in a separate backlog review. Also run on the owner's request to review a named run. `playbooks/retrospective.md`.
- **Merging the lesson backlog.** When the owner asks to merge registrations, review all open registrations by root cause on one page, then apply only the owner's decisions. Distinct from Retrospective, which records one run's analysis without executing it. `playbooks/merging-the-lesson-backlog.md`.
- **Opening a PR.** Opening or settling a delivery PR for completed work, or promoting an owner-approved project branch. `playbooks/opening-a-pr.md`.
- **Runtime forensics.** Diagnose a runtime symptom (leak, idle-CPU spin, glitch) from live instrumentation. The deliverable is a diagnosis, not a fix. `playbooks/runtime-forensics.md`.
- **Trace forensics.** Diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot) handed to you after the fact. The deliverable is a diagnosis, not a fix. `playbooks/trace-forensics.md`.
- **Authoring or modifying a skill.** Creating or changing a skill, principle, playbook, reference or its tooling, wherever maintained. Larger changes carry their standards into Develop a change. `playbooks/authoring-a-skill.md`.
- **Eval.** Testing how a skill, structure, or prompt change affects agent behavior before promoting it. `playbooks/eval.md`.
- **Set up code checkers.** Creating scripts/check, or adding or replacing a language, sub-project or checker in it. `playbooks/set-up-code-checkers.md`.
- **Session pickup.** Resuming or taking over a prior agent's in-flight work from a transcript, a pushed branch, or an open ticket of ours. `playbooks/session-pickup.md`.
- **Pause safely.** On an explicit request to pause ongoing work and leave a resumable checkpoint. `playbooks/pause-safely.md`.
- **Worktree and simulator cleanup.** Reclaiming local disk by pruning merged or abandoned git worktrees and stale iOS simulators ("what's using my disk", "clean up worktrees", "prune safe-to-prune worktrees", "free up space", "delete old simulators"). `playbooks/worktree-cleanup.md`.

## Requested results

Use these entries when the method's output is the owner's requested result. Inside a playbook, follow the calling step instead. Return the result and its limits; implementation needs its own scope and Go. Independently requested verification generation or maintenance uses the current project branch; calls inside an effort or worker keep the caller's branch and write authority.

- **wayfinder**. Chart a destination whose decisions exceed one session, or resolve the next decision on its map. Keep its fresh-session boundary.
- **to-spec**. Publish or revise a spec as the requested result; return it without automatic ticket decomposition.
- **to-tickets**. Publish an independent ticket or an approved spec batch as the requested result; return without opening execution.
- **improve-codebase-architecture**. Return architecture candidates or feedback before implementation has been selected.
- **code-review**. Review a pull request another author opened.
- **prototype**. Return the requested bounded model, experiment, sketch or UI candidates. Owner iteration and confirmed UI design use Design a UI.
- **create-verification-skill**. Establish missing reusable product verification capability through Generate and prove.
- **maintain-verification-skill**. Perform requested whole-product maintenance; this is not an affected-feature lookup.
- **create-formal-verification-skill**. Establish a rerunnable check of an agreed important rule against real code.
- **maintain-formal-verification-skill**. Reconcile named existing formal checks with current code.
- **setup-mmw**. Set this repository up for MMW or check its prerequisites.
- **correct**. Prepare prevention of the owner-named recurring mistake.
