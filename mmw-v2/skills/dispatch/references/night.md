# Running a night

You are the orchestrator. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

The night is read in the morning by the user, cold, from `NIGHT SUMMARY`, `NIGHT RETRO` and the tracker, with none of this session's context. So each decision you make leaves its reason where that reader will look: on the child, the ticket or the spec, in a comment that stands on its own. A reason that lives only in this session is lost when it ends.

The night's output is a batch the user can accept in the morning, not a count of closed tickets. A ticket handed back with its reason on it is a good result; a criterion loosened, or a worker resumed again and again with `continue`, to make one close is a defect that lands under a green mark.

This file is the order of the night. How a wake reaches you and what you do on one is in the skill's [../SKILL.md](../SKILL.md).

Between the steps below you end your turn. The relay you start in step 1 wakes you when a ticket of the batch gets an event that needs the orchestrator (step 3), and the watchdog tells you when the tracker has gone silent where it should not; nothing else does, and no agent polls another.

Find where you are by the first row whose fact holds:

| The fact | Go to |
| --- | --- |
| The user has said the night starts, and the spec carries no `spec.opened` | [1. The user says the night starts](#1-the-user-says-the-night-starts), then 1b and 2 |
| The spec's newest night event is `spec.suspended`, or you are deciding to stop the night because the fault is in the pipeline | [Suspending the night](#suspending-the-night) |
| A wake arrived: `#<n> <event>`, `relay.recovered since <time>`, a line of `watchdog:` alerts, or `MMW turn guard:` | [3. Each time something wakes you](#3-each-time-something-wakes-you) |
| `bash scripts/dispatch.sh status <spec>` shows an empty frontier and no live agent, and the spec carries no `spec.closed` | [4. The closing pass](#4-the-closing-pass) |
| The spec carries `spec.closed` and no later `spec.retroed` whose result is `recorded` | [5. The night is over](#5-the-night-is-over), from the paragraph that invokes the `retro` skill |
| The spec carries `spec.closed` and a later `spec.retroed` whose result is `recorded`, and the user has not accepted the result yet | Tell the user the night's result waits for their acceptance, pointing at `NIGHT SUMMARY` and `NIGHT RETRO`, then end your turn |
| The spec carries `spec.closed` and a later `spec.retroed` whose result is `recorded`, and the user has accepted the result | [6. Merge the accepted night](#6-merge-the-accepted-night) |

## 1. The user says the night starts

Run `check` and `open` from a checkout on the night's base branch: the current checkout names it.

```bash
bash scripts/dispatch.sh check <spec>
```

**Exit 0:** the machine is ready; open the night. **Exit 2:** fix every condition stderr names and run `check` again; an invalid agent row is reported to the user.

When `check` exits 0 and stderr carries a `dispatch: warning: install.sh --check still finds this` paragraph, show the user the lines under it and ask whether they authorise the install; run `open` only after they answer, with the install or without it.

Then, from this session — the one the night's wakes must reach:

```bash
bash scripts/dispatch.sh open <spec>
```

**Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>; task board <url>`, and this session is the night's orchestrator. **Exit 2:** fix stderr's named condition and run `open` again.

Hand the user the task board URL from that line in your first message of the night. A board that did not start is one stderr line and holds nothing up; `bash scripts/dispatch.sh board` starts it later.

## 1b. Before the batch: what the batch cannot be run on

Run this once, before the first `advance`, on every spec, with the `verify-ticket` skill's `verify-ticket.py`:

```bash
verify-ticket.py <spec> --lint
```

Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2: a criterion names an oracle this run cannot reach, and nothing was read.

When the batch drives a screen contract, whether the consuming repository can be driven
at all is a separate question, answered there by the `ui-acceptance` skill's `target_config.py --check`, which prints
every `.mmw/target.json` field still to answer and exits 0 once the file is complete.

## 2. First `advance`

After `open` records `into`, `advance` may run from any checkout in this repository. It does not move that checkout or any local base branch.

```bash
bash scripts/dispatch.sh advance <spec>
```

**Exit 0:** end your turn. **Exit 4:** a runner refused a start; stderr names each refusal, and none is retried. Fix what each names and run `advance` again; end your turn only while another worker of the night remains live, and if none does, tell the user which tickets were refused and why. **Exit 2:** fix what stderr names and run `advance` again (a night that is not open: `open <spec>` first); the rest of the batch was landed and started.

## 3. Each time something wakes you

Handle each wake in this order, one wake at a time — two tickets landing seconds apart are two wakes, and you get the second after you end your turn:

1. Do steps 1-3 of `## On waking` in [../SKILL.md](../SKILL.md), which end with the ack.
2. Run `bash scripts/dispatch.sh status <spec>`. Exit 0 prints the table; exit 2 means the tracker did not return the whole batch, so run it again when the tracker answers.
3. Take every row the table matches, not only the ticket named by the wake.
4. Run `bash scripts/dispatch.sh advance <spec>` once. Its exit codes are under [**2. First `advance`**](#2-first-advance).
5. When the `advance` you just ran left the frontier empty and no agent live (read `status` again), go to [4. The closing pass](#4-the-closing-pass); otherwise end your turn.

| What you see | What you do |
| --- | --- |
| `ticket.passed`, or a `ready` frontier row | Step 4's `advance` handles it |
| A live worker should continue | `bash scripts/dispatch.sh resume <n> "<what you settled, then: continue>"`; act on exit 0, 4, 3 or 2 as [Exit codes of `resume`](#exit-codes-of-resume) below says |
| `child.opened` of kind `fault` | Read the `verify-ticket` skill's `events.py fold <n>`. A `fault` in this repository's environment (a credential, a service, `.mmw/target.json`) you fix, then `bash scripts/dispatch.sh resume <n> "… continue"`. A `fault` in the pipeline's own scripts you do not patch while they run the night: tell the user what failed, and suspend when the rest of the batch would hit it too |
| `child.opened` of kind `contract` | Read the child and the authority it cites. Apply the authority order below; then either correct the source the child names and every unlanded derived ticket, close the child and resume its worker, or move the affected not-yet-started tickets to `needs-triage` and leave the child open |
| `child.opened` of kind `contract` naming a Claude Design page | The design package is written only by the `design-pages` skill's `references/pull.md`, so there is nothing to correct in this night. Move the affected not-yet-started tickets to `needs-triage`, comment on the child with the pages it names, the ticket numbers moved, and that it needs a session whose host has the Claude Design MCP tools, and leave it open for the user |
| `child.opened` of kind `decision` | Nothing; the worker took the default |
| `ticket.returned` | Leave its workspace for triage; step 4 continues the batch |
| The `advance` summary has `bounced` | After the second bounce the ticket stays in `needs-triage` |
| `ticket.refused` | Fix the event's `reason`; step 4 starts it if the frontier permits |
| `worker.lost` | Step 4 gives back the claim and starts another worker in the standing workspace |
| `relay.recovered since <time>` | Nothing; later wakes carry the recovered events |
| A worker whose session is gone while its worktree, slot or claim still stand (`advance` says "if the worker … is gone, retract it") | `bash scripts/dispatch.sh retract <n>`; a `0` on its summary line is something it could not release, and the line above says why. Step 4 starts the replacement |
| `watchdog: #<n> silent since …` | When `events.py fold <n>` lists an open `contract` child, the worker is waiting on you; settle that child first |
| Any other `watchdog:` alert | Do what the alert itself says to do, and act on the exit of a `resume` it names as [Exit codes of `resume`](#exit-codes-of-resume) below says; the line is not acked |
| An `MMW turn guard:` line | Do what the line says: run the `watchdog.py arm` command it names, act on what that prints, and when it exits non-zero open a `fault` child on a held ticket with that command and its output; the line is not acked |
| Any other live worker | Nothing; its result wakes you or its worker |
| The ticket needs the other worker grade | Give it exactly one of the `junior-worker` / `senior-worker` labels; the next `start` reads it |

While a worker holds a ticket, its code is the worker's: you change what the worker works from (the spec, the ticket body, a criterion, a baseline, under the authority order below) and tell it through `resume`, never its worktree or branch. Your own fixes wait for the closing pass, on `origin/<into>`.

For a `contract` child, use this authority order exactly: **decision tickets and ADRs, then the spec, then the design package or the screen contract, each in its own domain, then domain documents, then the ticket body**. Fix it yourself when you can cite a written authority at that order: a higher authority, a more specific file within the same authority, a repository rule, or the artifact a baseline copied. Edit the tracker-owned spec, acceptance criterion, or ticket body directly; when a spec changes, leave the change-and-reason comment that the `to-spec` skill's `references/revising-a-spec.md` requires. Edit a repository-owned baseline through the normal `origin/<into>` commit and push procedure in `## 4. The closing pass`. Correct every not-yet-landed ticket derived from the same bad statement. Comment on the child with the authority used, every published item corrected, the source commit, and the tickets checked; run `bash scripts/dispatch.sh route <n> <child> fixed`, then resume the active worker with the exact correction, the commit it should integrate from, and `continue`.

When no authority settles the correction, or the proposed correction would overturn the user's decision or expand the spec, leave the choice to the user. Find every not-yet-started ticket derived from the same Parent decision, move each from `ready-for-agent` to `needs-triage`, and comment on the child with the unresolved options, your recommendation, and the ticket numbers moved. Leave the child open for the user. A ticket already being worked stays held at the contract question; do not rewrite its delivery while the authority is unresolved.

### Exit codes of `resume`

- Exit 0: the worker took the message and a turn started on it; its result wakes you, and `worker.resumed` is on the ticket unless stderr says it was not written.
- Exit 4: the runner was handed the message but cannot show a turn starting on it; the text is in the session, so do not send it again.
- Exit 3: the worker did not take the message and is most likely in a turn; end your turn and run `resume` again on the next wake or `watchdog:` alert about the ticket. When `resume` exits 3 again with no ticket event in between, `bash scripts/dispatch.sh start <n> worker` replaces the worker, stopping it through its runner first.
- Exit 2: nothing was sent, and stderr names why and what to run. When stderr says the worker is not on its runner any more, run `bash scripts/dispatch.sh retract <n>`, then `bash scripts/dispatch.sh advance <spec>` inside a night or `bash scripts/dispatch.sh start <n> worker` outside one; when `retract` cannot tell whether the session stopped, tell the user.

When you run `resume` again after exit 3, word it so a worker that receives both messages reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`.

## 4. The closing pass

The frontier is empty and `status` shows no live agent. If this spec's tickets still hold open findings — the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `events.py fold <n>`, open until a `child.closed` on the ticket gives their `resolution` — route **exactly those**. If there are none, close this spec's Memory records as the end of this pass says ("Once every finding has a route"), then go to step 5.

List the open findings with `bash scripts/dispatch.sh findings <spec>` and route exactly those. A finding wakes nobody, so the ones you were woken about are no measure of what exists.

Every route is carried out by one command, run once per finding, and it is the only way a finding leaves this pass:

```bash
bash scripts/dispatch.sh route <n> <child> fixed
bash scripts/dispatch.sh route <n> <child> stale <invalid|fixed-elsewhere>
bash scripts/dispatch.sh route <n> <child> became-ticket <new ticket>
```

`<n>` is the ticket the finding came from, the one whose `fold` lists it under `children`. `became-ticket <child>` makes the finding itself the ticket; `became-ticket <other issue>` closes the finding as that issue's duplicate. `route` writes the `child.closed` event that the night summary counts. Exit 1: run the same command again; it repeats no step. Exit 2: nothing was done, and stderr says why.

Judge each one by the four steps below, **in order, first match wins**, after the check that comes before them.

**Step 0, before you classify at all.** Check the condition the finding's own body states against the current `HEAD`. If it never held, run `bash scripts/dispatch.sh route <n> <child> stale invalid` and do nothing else. If it held but a later ticket of the same batch or a closing-pass fix already resolved it, run `bash scripts/dispatch.sh route <n> <child> stale fixed-elsewhere` and do nothing else. A finding's claim disproved by current evidence is `invalid`; a valid claim satisfied somewhere else is `fixed-elsewhere`. `fixed-elsewhere` is not a reviewer false positive.

1. **Does it fall inside another still-open ticket's `## Owns`?** → a ticket, `Blocked by` that open one. Not a question of size: the constraint is concurrency. Fixing it yourself in the origin-tracking checkout makes the next `advance` conflict when that ticket's branch merges.
2. **Is it a gap in the criteria themselves** — a `CHECK:` that is already green while the thing it names is broken or never reached? → a ticket, `senior-worker`, and it asks for a negative control.
3. **How many files does the fix touch?** One → fix it yourself. Two or more **with a design coupling between them** — how you fix one decides how you fix the other, and neither can be written until both are settled → a ticket, `senior-worker`. Counting files is not counting effort; it is asking whether the change has a cross-file shape somebody should look at. **A name echoed through prose is not a coupling**: renaming a thing along with its restatements in a domain doc, a `SKILL.md` and a reference file is mechanical, `grep` proves you got them all, and it stays with you.
4. **Nothing matched** → fix it yourself. **The default is to fix it, not to open a ticket.**

The ones you fix: use a checkout that tracks `origin/<into>`. Fetch before each fix, commit it there, run the affected tests, and fast-forward push it to `origin/<into>`. If that push is rejected, fetch, merge the new `origin/<into>` into the commit, run the affected tests again, and retry the fast-forward push. Then `bash scripts/dispatch.sh route <n> <child> fixed` for each, after its commit and push. The commits follow these three rules:

1. One commit per finding, or per group of findings with one cause; the commit message names them by number.
2. It touches only what the finding's cause requires, and the tests that prove it; anything more is a ticket after all.
3. It runs the affected test suites, and the commit message quotes the line it saw (`ran 188 skipped 0`, not "the tests pass").

A fix that exceeds those three is a ticket after all.

The ones that become tickets: open as few tickets as possible. A ticket whose files sit in another live ticket's `## Owns` is `Blocked by` that live ticket. A finding that is a ticket on its own becomes one in place — rewrite its body into a ticket, label it for the agent queue, then `bash scripts/dispatch.sh route <n> <child> became-ticket <child>`; findings folded into one new ticket each get `bash scripts/dispatch.sh route <n> <child> became-ticket <that ticket>`.

A ticket you write here is dispatched in this night, and it has had none of the reading the published batch had. Write it to the `<issue-template>` of the `to-tickets` skill's `SKILL.md`, with every criterion in the four-line shape that file's **4. Write each acceptance criterion** gives, and only what its five questions admit as a criterion. Two shapes come back from a night's findings and neither is a criterion: prose that states a rule with no command under it, and the repository's own whole-tree checker — a `lint.sh`, a full type-check — put in a `CHECK:`, which fails on files this ticket never touched and blocks it on somebody else's work.

Then lint each ticket you wrote or rewrote, before you dispatch it:

```bash
verify-ticket.py <n> --lint
```

Read its exit as in 1b; fix every `ERROR` and lint again.

Once every finding has a route, close this spec's Memory records before leaving the pass. These records are what this spec's workers left for the workers after them: each carries the `mmw-experience` label, so later workers in this repository see it in their start prompt and act on it before reading any code. A record that was true mid-night can be wrong once the batch has landed. Judge each against what landed: keep what still holds, deprecate or supersede what the batch made untrue, and propose to the retro what should change how the pipeline works.

Run `bash scripts/dispatch.sh memory-list <spec>` and save its output to a file: it computes the repository's Space id, pulls the spec's full `mmw-spec-<spec>` record set, and writes a `--memory-decisions` file skeleton with `total` and `returned` already filled in, one entry per record, or a ready-made `unchecked` object when the list could not be read or was truncated.

For each id in the file decide exactly one of `retain`, `propose`, `deprecate` or `supersede`: `retain` remains useful as it is; `propose` is a candidate for the later retro and does not change the Memory here; `deprecate` is no longer valid; `supersede` names the existing `replacement_id` that replaces it. A `propose` decision's `evidence` is exactly one event comment URL (`https://github.com/<owner>/<name>/issues/<n>#issuecomment-<id>`) or commit URL (`https://github.com/<owner>/<name>/commit/<40-hex sha>`): the retro counts the proposal only when that string is one of its problem's sources, and `summary` refuses any other value.

Keep the file for step 5. Done when every id in it has a decision, or it is the `unchecked` object `memory-list` wrote.

Then:

```bash
bash scripts/dispatch.sh advance <spec>
```

Loop: each `ticket.passed` wakes you at step 3; when the frontier is empty again, this pass runs again. Continue until no open finding survives. Then go to step 5.

## 5. The night is over

Step 4 left no open finding. From any checkout in this repository:

```bash
bash scripts/dispatch.sh reverify <spec>
bash scripts/dispatch.sh summary <spec> --memory-decisions <file>
```

`reverify` exit 0: every landed ticket is green. Exit 1: each red ticket is already reopened in `needs-triage`; do not close it. Exit 2: fix stderr's named condition and run `reverify` again.

To recover a reopened ticket, repair the cause on the base branch, push it, and run `reverify <spec>` again; all met, `reverify` closes it itself. Still red, `summary` refuses the night: tell the user which ticket stays red and why, and stop.

When `summary` refuses the `--memory-decisions` file, list the Memory records again, rewrite the file, and run `summary` again; a rerun repeats no completed action.

Tickets left for human acceptance, handed back to triage by their worker, or behind an open blocker are valid outcomes; `summary` does not require every ticket to succeed.

`summary` exit 0: `NIGHT SUMMARY` is posted and the spec watch is closed. Exit 1: posted and closed, and a relay was left running; end the pid stderr names. Exit 2: nothing was posted; fix what stderr names and run `summary` again. A refusal counting findings no route reached sends you back to step 4.

Immediately after `summary` records `spec.closed` (exit 0, or exit 1 with the comment confirmed), invoke the `retro` skill in this same orchestrator session for this spec; `finish` needs its `spec.retroed` event, recorded.

Then tell the user the night finished, point them at `NIGHT SUMMARY` and `NIGHT RETRO`, and say that after they accept the result the orchestrator will run `finish` to merge it into the project branch.

## 6. Merge the accepted night

Only after the user has accepted the result, the orchestrator runs:

```bash
bash scripts/dispatch.sh finish <spec>
```

A worktree that has the base branch checked out, usually the one this session runs in, is kept: stderr gives the commands that remove it, for the user to run once this session is done, and `finish` needs no second run.

Exit 0: the merge is recorded. Exit 1: the merge conflicted or the repository checks failed, and nothing was pushed or deleted. Exit 2: fix what stderr names and run `finish` again. Do not merge the project branch into the repository default branch here; that remains the user's release decision.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `bash scripts/dispatch.sh suspend <spec>` is that decision carried out.

A suspended night wakes nobody: its watch is closed, and its workspaces, branches and pushed commits stay for `open` and `advance` to take up.

Workspaces and branches stay, with the interrupted tickets' commits present on origin. The same batch is taken up again with `bash scripts/dispatch.sh open <spec>` and then `bash scripts/dispatch.sh advance <spec>` once whatever stopped the night is fixed: `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

Exit 0: the night is stopped. Exit 1: stderr names, one line each, what was left. For a slot a process still listens on (`lease.py` names the port and the pid), stop that process where it was started and run `lease.py release <its worktree>`; tell the user every other line. Exit 2: nothing was touched; fix what stderr names and run `suspend` again. Done when `suspend` exits 0, or exits 1 and you have told the user each line stderr left.
