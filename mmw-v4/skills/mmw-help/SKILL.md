---
name: mmw-help
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# MMW help

Answer the user's question about MMW, hand them a prompt they can send, and link the file the answer came from. For a help question, don't start the work. The user asked how, and a run spends real tokens, so let them send the prompt.

A message that asks for work, such as "fix this bug", is not a help question: do the work.

This file maps questions to the skills and guide pages that hold the answers. Those files own the details. Read the file you route to before you quote it, and trust it when it disagrees with this map. Give the user each file's path in the toolbox checkout, the directory above the one `~/.mmw/installed-root` names.

## Find out what they need

Infer the need from the message and the conversation. A named situation, such as "which skill reviews a diff?", goes straight to its section. If the need is still unclear, ask one multiple-choice question with these options, then answer only the section they pick:

- Get set up
- Start a task
- Pick a skill
- Fix a run that went wrong
- Make MMW my own

Check the state that changes the answer, and mention it only when it does:

- No `~/.mmw/models.json` means install has not run on this machine, so no dispatched role can start.
- No `verify-*` skill or other app harness in the project means agents have no scripted way to drive the app. Mention the **create-verification-skill** skill when the question is about proving a change works.

## Get set up

1. Install from the toolbox checkout: `bash mmw-v4/install.sh`. It links every skill for each host, registers the hooks, links the user-level prompt, writes `~/.mmw/models.json` when absent, and records the checkout in `~/.mmw/installed-root`. Installing changes what every session on the machine reads, so it is the owner's decision; `bash mmw-v4/install.sh --check` only reports, and `bash mmw-v4/install.sh --back` returns the machine to v3. The script's header comment lists every item.
2. Pick the host, model and reasoning effort of each dispatched role: `python3 mmw-v4/skills/dispatch/scripts/models.py config show`, then `config set`. The **dispatch** skill's `references/editing-models.md` has the usage. A change takes effect at the next start.
3. In each repository MMW is to work in, run the **setup-mmw** skill once: it creates the pipeline's labels, ignores its directories and gives it its `scripts/check`.
4. Start a real task in a session, with a goal and a check that can pass or fail.

Guide page 1 (`mmw-v4/docs/guide/01-setup.md`) has the details. Offer to word their first prompt with them, per [`references/prompting.md`](references/prompting.md).

If cost is the worry, say where the tokens go: dispatched workers and reviewers, the four review subagents each reviewer sends, and the candidates of `arena`. The four review axes use the `review-axis` subagent row, so you can change their model separately from the reviewer session. A cheaper model or a lower effort on a role's row of `~/.mmw/models.json` spends fewer.

## Start a task

Every session reads the **mmw-mode** skill in full before anything else; its description says so. The mode matches the task to a playbook in the `## Playbooks` of its `references/handling-a-request.md`, works through the playbook's steps, and runs the other skills as the steps need them. A good prompt states the goal and how to tell it's done. It doesn't list skills, because a hand-written sequence tends to drop or reorder steps the playbook would keep. Read [`references/prompting.md`](references/prompting.md) before you help word one. Guide page 2 (`mmw-v4/docs/guide/02-mmw-mode.md`) has examples.

Mid-session, starting a message with "new task" tells the session to match a fresh playbook.

## Pick a skill

The default answer is to describe the task and let the mode route it. Name a skill directly when the user wants more or less of something than the playbook gives. Read the skill before you recommend it, and give one example prompt.

| The user wants to | Skill |
|---|---|
| Know how code works now, or where new code should live | `how` |
| Know why code is shaped this way, or where a number came from | `why` |
| Understand a change or subsystem, explained plainly | `teach` |
| Have a question investigated against primary sources | `research` |
| Know what a small diff could break outside itself | `blast-radius` |
| Use the shared words for module design: depth, seam, adapter | `codebase-design` |
| Get several designs of one brief, merged into the best one | `arena` |
| Answer a logic, UI, implementation or code-shape question by building code that answers it | `prototype` |
| Examine the expert approach, your real goal, constraints and an outside check, with conclusions returned for your decision | `sharpen` |
| Have a plan stress-tested one question at a time | `grilling` |
| Settle the project's terms or record a decision | `domain-modeling` |
| Have a diff read on four axes by eyes that did not write it | `code-review` |
| Get a second opinion on one decision, on a stronger model | `advisor` |
| Send a worker to a ticket, run a night, or change a role's model | `dispatch` |
| Run one ticket's acceptance criteria and close it | `verify-ticket` |
| Resolve a merge or rebase conflict | `resolving-merge-conflicts` |
| Fix a bug test-first when a cheap local test exists | `tdd` |
| Apply TypeScript rules to `.ts` or `.tsx` work | `typescript-best-practices` |
| Strip comments before review, using a reviewer that didn't write them | `no-comments` |
| Clean AI tells out of prose | `unslop` |
| Write docs, a README, a PR description, or a commit message to a standard | `technical-writing` |
| Re-pitch the last reply in words or with `visual` as one page; catch up with `ketchup`; align on your goal with `in-your-own-words`, then wait for confirmation | `wait-what` |
| Draw a diagram or a page that explains something | `diagram-design` |
| Build an install package from the current branch | `exe-release` |
| Drive and inspect a CLI or TUI to prove a change | `control-cli` |
| Drive and inspect a browser, Electron or web UI to prove a change | `control-ui` |
| Give agents a scripted way to drive the app and prove behavior | `create-verification-skill` |
| Bring a verification skill and its feature map back in line with the app | `maintain-verification-skill` |
| Vet a performance number before reporting or acting on it | `benchmark-checklist` |
| Write or edit a skill, a playbook or a reference to the set's standards | the Authoring or modifying a skill playbook |
| Register a problem that cannot be fixed in the current work | `register-problem` |
| Gather and sort a run's problems into proposals for the owner | `retro` |
| Stop agents from repeating the same mistakes in this repo | `correct` |
| Find their way around MMW | `mmw-help` |

If a skill directory next to this one is missing from the table, read its frontmatter and its opening lines. The `principle-*` directories are covered under principles below.

Close calls:

- `how` explains what the code does. `why` explains the reasons. `teach` runs one or both and explains the result plainly.
- The **prototype** skill's sketch branch stops at the sketch and hands it back. It writes no implementation.
- `code-review` reviews the diff. `blast-radius` looks for breakage outside the diff and proves the one fact that makes the change safe.

## Playbooks and principles

Playbooks are step lists inside the **mmw-mode** skill, not skills. Describing the task picks one; the `## Playbooks` of the mode's `references/handling-a-request.md` is the one list of which task goes to which playbook, so read it there rather than answering from memory. Guide page 5 (`mmw-v4/docs/guide/05-build-and-clean.md`), page 6 (`mmw-v4/docs/guide/06-verify-and-ship.md`) and page 7 (`mmw-v4/docs/guide/07-overnight.md`) show how a change is built, delivered as one pull request, and run unattended overnight.

Planning here is a spec and its tickets, because the owner checks those, not code. Grill with docs or a wayfinder map settles the decisions, To spec records them, To tickets cuts the spec into tickets the owner approves. For a design question, the **prototype** skill settles it in code first.

Principles are one-rule skills that the mode indexes in its `## Principles` and applies when their conditions arise. The user rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output." Guide page 8 (`mmw-v4/docs/guide/08-principles.md`) lists them.

## Fix a run that went wrong

| Symptom | Fix |
|---|---|
| A question got treated as the next step of the last task | Say "new task". |
| A new model choice had no effect | `models.py config set` takes effect at the next start of that role; a session already running keeps its model. |
| A skill's new description had no effect | A host reads descriptions at session start. Start a new session. |
| Runs cost more than expected | See the cost paragraph under Get set up. |
| Parallel agents overwrote each other | Give each agent its own worktree. |
| A night moved but closed no ticket | Each ticket needs criteria a command decides. See guide page 7 (`mmw-v4/docs/guide/07-overnight.md`). |
| The reply claims success from a green build | Ask for the real command, flow, stored value, or profile. That's the prove-it-works principle. |

For a run that drifts, [`references/prompting.md`](references/prompting.md) has one-line steers. Guide page 10 (`mmw-v4/docs/guide/10-recipes-and-pitfalls.md`) has more pitfalls and the recipes worth copying.

## Make MMW my own

- After a run, Retrospective sorts registered problems into proposals the owner picks before planning and implementation.
- Changing the set from your words, a registered problem or retrospective proposal, an upstream release or a doubt about a part of the set runs the Authoring or modifying a skill playbook. The Eval playbook tests a skill change blind.
- Fix a misbehaving skill in its own change, not inside the feature work where it went wrong.

Guide page 9 (`mmw-v4/docs/guide/09-make-it-yours.md`) covers each of these.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
