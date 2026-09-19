---
name: implement
description: Implement a piece of work based on a spec or set of tickets. Use when you were dispatched onto a ticket, or picked one up yourself, and are about to claim it, write the code, and work through the closing steps that post the result and close the ticket.
---

Implement the work described by the user in the spec or tickets.

First claim the ticket with the `verify-ticket` skill: its `--preflight` run, in that skill's `references/claiming.md`. It is first because nothing else in this pipeline claims a ticket, and step 8 below cannot close one you do not hold. If you picked the ticket up yourself rather than being started on it, run `<dispatch> adopt <n>` just before that claim, from the ticket's worktree on branch `issue-<n>` (the `dispatch` skill's `references/inside-a-ticket.md`): it records you as the ticket's worker and makes sure a relay watches the ticket. Without it no event names your session, so your reviewer's report would wake nobody, and `start <n> reviewer` would refuse.

The branch may already carry the commits of an earlier worker of this ticket whose session ended, among them a `wip(#<n>): uncommitted work of …` commit holding what it left uncommitted. They are this ticket's work: carry on from them.

Then check the ticket is coherent: its title and **What to build** describe the same vertical slice; every glob under **Owns** either matches an existing path or is marked `(new)`. An older ticket without **Owns** gets one derived from its **Seam** and the spec sections **Parent** names — post the derived list as a comment on the ticket, then continue.

Then read yourself in: the ticket in full, comments included, and its own open sub-issues (`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100 --jq '.[] | select(.state=="open")'`), as a supplement to **What to build** — whether you do them goes under `Decisions I made on my own`; then every item under its **Read first**, each through to its conclusion: the last section of a research file, an ADR's decision in the untitled paragraph under its title, a handoff package downloaded from Claude Design, a prototype's leaf `README.md` read to its verdict. A baseline in **Read first** is anything there that records a settled conclusion, and it is a contract, not a reference. A handoff package is copied exactly; a prototype is rewritten to production standard, keeping the shape its verdict settled on. Then follow **Parent** to the spec and read only the Implementation Decisions sections the ticket names, plus its Testing Decisions and Out of Scope — not the whole spec. Then the root CONTEXT.md: every term you write comes from it. A ticket without **Read first** is an older one: fall back to every item under the spec's **Sources**.

An interface ticket's **Read first** names the **target trees** of its design pages (`docs/specs/<effort>/targets/<page>.aria`, `<page>.classes`): every scene's tree of named nodes and its class set, produced by the same normaliser the judge reads. Write toward them — build the nodes and the classes they show, in that order and under those ancestors — and then run the judge; do not write blind and reverse the design out of `DIFF` lines. When a tree is not enough to see, the `ui-acceptance` skill's `story-parity.py --render-only` renders the design side of your scenes into a directory with no product at all; resolve `scripts/` from that skill's own SKILL.md, the way you resolve `<engine>` and `<dispatch>`.

Then say in one sentence which **seam** this ticket is tested at — copied from the ticket's **Seam**. If the ticket has no **Seam**, derive it from the spec's Testing Decisions and post it as a comment on the ticket before you start, so the ticket is complete for the next reader.

Commands of the `verify-ticket` skill are written `<engine> …` below; commands of the `dispatch` skill are written `<dispatch> …`. Resolve each from that skill's own SKILL.md. `start` starts the session and prints its id; each closing step names the command and the first line to read. Every `--sub-issue` run below is in the `verify-ticket` skill's `references/sub-issues.md`. A fault in the pipeline itself (`verify-ticket.py`, hook, driver, `.mmw/target.json`): `<engine> <n> --sub-issue fault <file>` — the file's body is the command you ran and the output you saw — then stop.

While writing code:

- The baseline is the contract. Copy the values, wording, states and interface shapes of every baseline in **Read first** from it rather than writing them again from memory. An interface ticket has two, each binding its own domain: the handoff package binds look and verbatim copy; the screen contract binds what each control calls, which field feeds each shown value, what state follows, what failure shows, and timing. A handoff statement about the second domain is a reference the contract has already adopted or overridden, so the two never compete. When something this ticket was told to follow does not hold, whether a baseline under **Read first**, a spec section named by **Parent**, or an acceptance criterion lacks a state, field, interaction or case or contradicts another such source, keep going and run `<engine> <n> --sub-issue contract <file>`. The child quotes what does not hold and states what in that same source still holds and must be preserved; a screen-contract row that does not fit also names the alignment ticket, since that is where the row is rewritten. Never quietly change a baseline, never quietly add around one. A check that will not pass is answered by fixing the code or abandoning the criterion, never by bending the baseline, the harness or the test.
- An interface has one code path: **no request path chooses its projection by whether a data source is present, by a query parameter, or by a build switch.** Data enters the view through the client generated from the API contract, or through the server's one render path from persistent state; a component takes its state from that data, never from a prop that poses it for a scene, never from a preview projection that stands in when the store is absent; fixture values live in the seed script that puts the product into a state, never in the view layer. On a server-rendered target this is what makes an `observe` line mean anything at all. The repository's static guard for this is one of the contract ticket's deliverables.
- Every surface component's root carries `data-screen="<mount>"`, the value the screen contract's `pages` declares for that design page — whoever builds the surface carries it; a top-level dialog renders inside that subtree or its scene names the page root. The value is unique in one render, and the guard checks that too. A worker who writes a surface component writes its story adapter and its boundary tests in the same pass.
- Put no question on the screen. Take the option the ticket, its baselines and the spec make most likely, write one line for it under **Decisions I made on my own**, and keep going. A question whose answer would change what the ticket delivers gets `<engine> <n> --sub-issue decision <file>` instead, and the rest of the work carries on.
- Before changing a function, grep every caller and fix the shared code once; before adding a branch or guard to an existing flow, name the branch or file it makes unnecessary and delete it in the same commit.
- Before writing a helper, search the repository and **Read first** for one that already exists.
- Before adding a file, a dependency or a configuration entry, say why the existing one is not enough.
- Never simplify away: security, error handling that prevents data loss, accessibility, or anything the ticket explicitly asks for — **What to build**, every acceptance criterion, the baseline, the interface under **Seam**.
- At the end, write `skipped: [X], add when [Y]`.
- For a file outside **Owns**: change it when a criterion cannot pass otherwise — it lands under `Outside Owns:` in the closing comment; when the change is merely convenient, leave it and run `<engine> <n> --sub-issue deferred <file>`.

## Shared experience while implementing

`dispatch` starts you with `NMEM_SPACE`, `NMEM_AGENT_ID=mmw-worker`,
`MMW_TASK_SCOPE`, `MMW_SPEC` and `MMW_TICKET`, and your first prompt carries two
indexes of Memory, one line per record with its `id`, `title`, first line (`applies`)
and `space`: Current task shared experience (the newest 30 records labelled
`MMW_TASK_SCOPE`) and Related experience (up to 15 `mmw-experience` records from this
repository and `mmw-toolbox`, found by searching each path under this ticket's
`## Owns` and the ticket, spec and map titles; a record that names one of those paths
comes first). Before working, read both indexes and open every record whose title or
first line bears on this ticket; skip the rest. A `truncated:` line means more
task records exist than are listed: search them with the task-scope command below.

```sh
nmem --json memories show "<id>" --space "<space from the index line>"
```

Current artifacts, verified evidence, the user's instructions, repository
instructions, the ticket, and its parent spec override Memory. Verify every Memory
against current repository evidence before acting on it.

When a command or tool behaves in a way that the ticket, repository authority, and
the records you opened do not explain, search the current task with the exact error,
command, and component before trying a workaround; if that has no answer, search
repository and approved toolbox experience. Keep the query to that error, command and
component, and keep `--` before it: Nowledge returns nothing for a query that names
something no record holds, which long prose always does, and reads a query that starts
with `-` as an option.

```sh
nmem --json memories search --space "$NMEM_SPACE" --label "$MMW_TASK_SCOPE" \
  --limit 10 -- "<exact error + command + component>"
nmem --json memories search --space "$NMEM_SPACE" --label mmw-experience \
  --limit 10 -- "<exact error + command + component>"
```

Save a Memory as soon as all three conditions hold: another ticket or later agent may
reuse the fact, a current command result or authority verifies it, and the ticket and
code do not already make it obvious. Evaluate the same trigger again at every
meaningful milestone or handoff. Save only while `MMW_TASK_SCOPE` is `mmw-map-<n>` or
`mmw-spec-<n>`; an empty value means routing failed and nothing is written. Store only
reusable engineering context that is safe for repository collaborators. Exclude
secrets, customer data, raw chat transcripts, private host paths and unverified
claims. Use unit type `learning`, or `procedure` for fixed steps. Take the labels from
the environment rather than reconstructing the numbers from prose: a map task adds its
map label, and a standalone spec's task label already is `mmw-spec-<spec>`. Give it a
title that names the component and the behaviour, and name in `证据` every repository
path the fact concerns: a later worker's Related experience ranks a record first when
it names a path that worker owns. Write this exact body:

```sh
label_args=(
  --label mmw-experience
  --label "mmw-spec-$MMW_SPEC"
  --label "mmw-ticket-$MMW_TICKET"
)
if [[ "$MMW_TASK_SCOPE" == mmw-map-* ]]; then
  label_args+=(--label "$MMW_TASK_SCOPE")
fi

nmem --json memories add --stdin \
  --space "$NMEM_SPACE" \
  --agent-id "$NMEM_AGENT_ID" \
  --unit-type learning \
  "${label_args[@]}" \
  --title "<searchable title>" <<'MEMORY'
适用条件：<环境、版本或前提>
问题：<已证实的非显然行为>
有效做法：<下一名 worker 可以直接执行的操作>
证据：<命令与输出首行，或 path:line>
发生位置：<repository、spec #n、ticket #n、日期>
MEMORY
```

Keep the id `nmem` returns and link the evidence in the ticket report. A failed Memory
write is reported as unsaved; continue the ticket work rather than treating Memory as
a prerequisite for implementation.

Correct only a record whose `space` (in an index line) or `space_id` (in a search or
show result) equals `NMEM_SPACE`; a toolbox record is context, not a record for this
worker to change. When current evidence verifies a replacement, save
the replacement first and supersede the old record with its id; when a record simply
no longer applies, deprecate it. Use one lifecycle command per old record, and do not
leave two active records that conflict:

```sh
nmem --json memories supersede "$OLD_ID" "$NEW_ID" \
  --space "$NMEM_SPACE" --reason "<current evidence for the replacement>"
nmem --json memories deprecate "$OLD_ID" \
  --space "$NMEM_SPACE" --reason "<current evidence that it no longer applies>"
```

The main agent's closing pass and the `retro` skill have their own script commands; a
worker does not write their Memory records or edit Working Memory here.

Finish by reporting the Memory records added, used, superseded, or deprecated, and the
evidence used to validate them. If none changed, say so.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the ticket asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files — roughly one focused test per stated behavior — and don't turn scratch checks into additional permanent test files. This is about extras only: implement every behavior the ticket asks for, completely.

Once done, commit your work to the current branch and work through the closing steps below. The tracker is closed by the closeout, never by hand.

A ticket that already carries a run of your own — a `ticket.checked` event whose `run` is `self` — or a `reviewer.reported`, `worker.decided`, or worker reverify event, is work you were prompted back into. Claim it again first — `<engine> <n> --preflight` — because `advance` takes the claim off a ticket it re-dispatches and step 8 refuses a ticket that is not yours. Then read the ticket's comments and find your row; each condition is an event the ticket itself carries, named in the trailing `<!-- mmw {...} -->` block of its comment, and the newest comment alone does not say where you are, because step 2 posts its comment in the middle and has a fix round after it.

| The ticket carries | Resume at |
| --- | --- |
| its newest result event is `ticket.bounced` | step 1, then step 4 and step 5 onward; integrate and run the worker criteria, do not start a second reviewer, then make the final full run and close out |
| no run of your own | step 1 |
| a run of your own, no `reviewer.reported`, and no `reviewer.started` or a `reviewer.lost` after the newest one | step 2, at its start: `<dispatch> start <n> reviewer` |
| a `reviewer.started` with no `reviewer.reported` and no `reviewer.lost` after it | step 2, asleep on the reviewer: end your turn, and you are woken when its report lands. Do not start a second reviewer |
| a `reviewer.reported`, and no run of your own newer than it | step 2, at its fix round: fix the in-ticket findings, then rerun step 1. Do not start a second reviewer |
| a run of your own newer than the `reviewer.reported`, no `worker.decided` | step 3 |
| a `worker.decided`, no worker reverify after it | step 4 |
| a worker reverify whose `commit` is `HEAD`, with nothing newer | step 5 |

These events are not steps and do not move you: `worker.touched`, which is another ticket's step 6 landing on this one; a `ticket.checked` whose `run` is `repo-checks` and whose result is `unmet`, which means step 8's draft was fine and the repository's own suite was not (fix the code and run `--closeout` again); a `worker.queued`, which means a run of the criteria found no product slot free (the `verify-ticket` skill's `references/running-criteria.md` under **A criterion that runs the product** says what to do); and `ticket.refused`, which means the ticket was never yours to start.

1. Integrate `origin/<base branch>` first: `<dispatch> integrate <n>`, from this ticket's worktree. Exit 0 merged it or it was already contained. Exit 3 leaves a conflicted merge in the tree with the numbers, titles and files of the tickets merged into the base branch on stderr: use the `resolving-merge-conflicts` skill, run the checks affected by those tickets, commit the merge, then run `<dispatch> integrate <n>` again. A clean merge that makes repository checks red also uses that skill, which reads the merged tickets and their closeout evidence before repairing the interaction. Exit 2 names the condition that prevented integration; a pipeline failure becomes a `fault` sub-issue, then stop. Never rebase, abort or push from this integration command. Then run every criterion yourself, with the `verify-ticket` skill: `<engine> <n>`, the run for a worker who has finished writing code, in that skill's `references/running-criteria.md`. Handle exit 3 as that file's **A criterion that runs the product** section says. Exit 4 means the criteria ran and their result could not be written on the ticket: run it again. A criterion whose `CHECK` is `story-parity.py` prints one `DIFF` line and nothing that explains it; the `ui-acceptance` skill is where the line is read. Fix only what that line names — the tree lines under it, the elements after `around:`, the console error — and run once more; do not chase the pixel share by changing fonts, line heights or renderer flags. How many rounds a criterion gets is your judgement: keep fixing while a fix is in sight, and when none is, write `ABANDON: AC<n> failed <what each round tried>` and carry on with the rest — the closeout counts no rounds, so that line is the whole record of the trying.
2. Start the reviewer: `<dispatch> start <n> reviewer`, then end your turn. You are woken with `#<n> reviewer.reported` once its report is on the ticket. Then read the report, the comment on the ticket that carries that event (`<dispatch> wait <n> reviewer` prints the event with the two commits it read), and `<dispatch> ack <n> reviewer.reported`. Start exits 2: the reviewer row of the `dispatch` skill, which you read in that skill's own `SKILL.md`. Do not start a second reviewer. Done means the review comment is on the ticket, never a session's state, and this step ends only with that comment. The in-ticket round is first: fix the in-ticket findings once, under the writing rules that governed the first write, and rerun step 1. An in-ticket finding you do not fix is `refuted:` — you checked, and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count. Then, for each out-of-ticket review finding whose body the in-ticket round has not made untrue, run `<engine> <n> --sub-issue finding <file>`. No re-review.

In these steps you never wait on the reviewer, and never ask whether it is done: after `start` you end your turn, and the relay of the `dispatch` skill wakes you when its result event lands on the ticket. The wake names the ticket and the event and nothing else; the event on the ticket is the answer, never a session's state.

3. Post the decisions comment, once: `<engine> <n> --decisions <file>`, in the `verify-ticket` skill's `references/closeout.md`. The file is two sections: `Decisions I made on my own` — every line written so far, one per line, in the shape the closing comment uses — and `Outside Owns` — the `Outside Owns:` line of your newest run (its `ticket.checked` event, run `self`), followed by one sentence per file saying which criterion could not pass without it; `None` when that line is `None`. It is posted here, before the final run, and once: a later fix round adds nothing to it, and the closing comment carries the final version.
4. Run every criterion one final time: `<engine> <n> --reverify --actor worker`. It runs after the last step that writes a commit, including the review fix, and includes criteria earlier runs already ticked. If anything still fails, write `ABANDON: AC<n> failed` for each failure and close out `HANDOFF REQUIRED`; this final run gets no fix round because the earlier own run and review fix were the repair rounds.
5. Audit: re-read the whole ticket and every item under **Read first**, trace every criterion to its latest `EVIDENCE:`, recount `Counts:`.
6. Tell the tickets whose files you changed: `<engine> <n> --touched`. It sits after step 2 because it reads the review comment, and a run before that is refused: step 2 is then the one to finish first.
7. Cut loose what only a person can settle, then write the closing comment to a draft file. A criterion that waits only on one sentence from a person: write `ABANDON: AC<n> decision <question, options, and the default if nobody answers>` **and** run `<engine> <n> --sub-issue decision <file>`, then keep working the rest — the ticket does not stop. Then `<engine> <n> --draft`, which prints the path it wrote as `DRAFT: wrote <path>`, and fill in every `<fill>` the skeleton leaves you. Give that run no path of your own: the skeleton names every file the ticket names, step 8 runs the repository's own checks over the working tree, and a draft inside that tree is one more file those checks read.
8. Close the ticket with the `verify-ticket` skill: `<engine> <n> --closeout <draft>`, in that skill's `references/closeout.md`, which is also where the conditions it reads the draft against are written. The closeout pushes the ticket branch before it closes the ticket and never force-pushes. It does not archive any agent: landing is a separate act, run by the main agent (`land <n>`, or `advance` for a batch), and it takes the whole workspace with the agents inside it. Never close the ticket or swap its labels yourself — a hook blocks the command. Open no pull request. The main agent fetches and merges `origin/issue-<n>` once the ticket is closed, with `dispatch.sh land <n>` for a ticket dispatched on its own or `dispatch.sh advance` for a batch, into the base branch named by `worker.started.into`. Nothing in this pipeline reads a pull request: code review takes its diff from git, and the final run reads the ticket and the worktree. A ticket you adopted outside a night, where `adopt` started a relay with you as the session it wakes, has no main agent to land it: you are woken with `#<n> ticket.passed` or `#<n> ticket.returned`; `<dispatch> ack <n> <that event>`, then tell the user the ticket is closed and that `<dispatch> land <n>` merges it and stops that relay. Do not run `land` from this worker session: it stops every session the ticket's events name, including this one.

Three `ABANDON` kinds, and the machine branches on each. `failed`: it ran and did not pass — after as many rounds in step 1 as you judged worth spending, or still failing after the review fix or final run; the reason says what each round tried. `stuck`: it will not start, or cannot be done within the task — a `CHECK` that will not run, a missing credential or device; the reason names the routes tried or points at the sub-issue that records them. Neither is held to a round count; giving up on the first round is allowed for both. `decision`: both options are legal and neither the ticket nor the spec says — write the question, the options, and the default when nobody answers; a UI difference never goes here. Any `failed` or `stuck` turns the whole ticket into `HANDOFF REQUIRED`; `decision` does not — its sub-issue is already open, and the rest all passing is still `ALL MET`.
