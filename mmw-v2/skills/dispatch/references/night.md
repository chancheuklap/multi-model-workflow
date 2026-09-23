# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. How a wake reaches you and what you do on one is in the skill's [../SKILL.md](../SKILL.md), and `<dispatch>`, `<engine>`, `<events.py>`, `<lease.py>` and `<ui-acceptance scripts>` are resolved in its `## Resolve `<dispatch>` once` section.

Between the steps below you end your turn. The relay you start in step 1 wakes you when a ticket of the batch gets an event that needs the main agent (step 3), and the watchdog tells you when the tracker has gone silent where it should not; nothing else does, and no agent polls another.

Find where you are by the first row whose fact holds:

| The fact | Go to |
| --- | --- |
| The user has said the night starts, and the spec carries no `spec.opened` | [1. The user says the night starts](#1-the-user-says-the-night-starts), then 1b and 2 |
| The spec's newest night event is `spec.suspended`, or you are deciding to stop the night because the fault is in the pipeline | [Suspending the night](#suspending-the-night) |
| A wake arrived: `#<n> <event>`, `relay.recovered since <time>`, a line of `watchdog:` findings, or `MMW turn guard:` | [3. Each time something wakes you](#3-each-time-something-wakes-you) |
| `<dispatch> status <spec>` shows an empty frontier and no live agent, and the spec carries no `spec.closed` | [4. The closing pass](#4-the-closing-pass) |
| The spec carries `spec.closed` and no later `spec.retroed` whose result is `recorded` | [5. The night is over](#5-the-night-is-over), from the paragraph that invokes the `retro` skill |
| The spec carries `spec.closed` and a later `spec.retroed` whose result is `recorded`, and the user has accepted the result | [6. Merge the accepted night](#6-merge-the-accepted-night) |

## 1. The user says the night starts

Run `check` and `open` from a checkout on the night's base branch: the current checkout names it.

```bash
<dispatch> check <spec>
```

**Exit 0:** the machine is ready; open the night. **Exit 2:** fix every condition stderr names and run `check` again; an invalid agent row is reported to the user.

Then, from this session — the one the night's wakes must reach:

```bash
<dispatch> open <spec>
```

**Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>; task board <url>`, and this session is the night's main agent. **Exit 2:** fix stderr's named condition and run `open` again.

Hand the user the task board URL from that line in your first message of the night. A board that did not start is one stderr line and holds nothing up; `<dispatch> board` starts it later.

## 1b. Before the batch: what the batch cannot be run on

Run this once, before the first `advance`, on every spec:

```bash
<engine> <spec> --lint
```

It starts nothing and runs no product. It reads every ticket of the batch and prints one finding per line; a `WARN` (a ticket with no worker-grade label starts on the default row) does not change the exit code, and a closed ticket's findings do not count.

Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2: a criterion names a judge this run cannot reach, and nothing was read.

When the batch drives a screen contract, whether the consuming repository can be driven
at all is a separate question, answered there by `python3 <ui-acceptance scripts>/target_config.py --check`, which prints
every `.mmw/target.json` field still to answer and exits 0 once the file is complete.

## 2. First `advance`

After `open` records `into`, `advance` may run from any checkout in this repository. It does not move that checkout or any local base branch.

```bash
<dispatch> advance <spec>
```

**Exit 0:** end your turn. **Exit 4:** a runner refused a start; stderr names each refusal, and none is retried. Fix what each names and run `advance` again; end your turn only while another worker of the night remains live, and if none does, tell the user which tickets were refused and why. **Exit 2:** fix what stderr names and run `advance` again (a night that is not open: `open <spec>` first); the rest of the batch was landed and started.

## 3. Each time something wakes you

A `watchdog:` line is not a queued wake: it is not acked.

On `MMW turn guard:`, run the named `watchdog.py arm` command. Exit 0 means it runs; on exit 1, fix stderr's reason or open a `fault` child on any held ticket with that command and output, then end your turn.

Handle each wake in this order, one wake at a time — two tickets landing seconds apart are two wakes, and you get the second after you end your turn:

1. Do steps 1-3 of `## On waking` in [../SKILL.md](../SKILL.md), which end with the ack.
2. Run `<dispatch> status <spec>`. Exit 0 prints the table; exit 2 means the tracker did not return the whole batch, so run it again when the tracker answers.
3. Take every row the table matches, not only the ticket named by the wake.
4. Run `<dispatch> advance <spec>` once. Its exit codes are under [**2. First `advance`**](#2-first-advance).
5. When the `advance` you just ran left the frontier empty and no agent live (read `status` again), go to [4. The closing pass](#4-the-closing-pass); otherwise end your turn.

| What you see | What you do |
| --- | --- |
| `ticket.passed`, or a `ready` frontier row | Step 4's `advance` handles it |
| A live worker should continue | `<dispatch> resume <n> "<what you settled, then: continue>"`; act on exit 0, 4, 3 or 2 as [Exit codes of `resume`](#exit-codes-of-resume) below says |
| `child.opened` of kind `fault` | Read `python3 <events.py> fold <n>`, fix the child, then `<dispatch> resume <n> "… continue"` |
| `child.opened` of kind `contract` | Read the child and the authority it cites. Apply the authority order below; then either correct the source the child names and every unlanded derived ticket, close the child and resume its worker, or move the affected not-yet-started tickets to `needs-triage` and leave the child open |
| `child.opened` of kind `contract` naming a Claude Design page | The design package is written only by the `design-pages` skill's `references/pull.md`, so there is nothing to correct in this night. Move the affected not-yet-started tickets to `needs-triage`, comment on the child with the pages it names, the ticket numbers moved, and that it needs a session whose host has the Claude Design MCP tools, and leave it open for the user |
| `child.opened` of kind `decision` | Nothing; the worker took the default |
| `ticket.returned` | Leave its workspace for triage; step 4 continues the batch |
| The `advance` summary has `bounced` | Nothing: `advance` starts a worker once more in the ticket's **standing workspace** (its worktree `.worktrees/issue-<n>` and branch, kept after its session ends) after its first bounce of the night, and leaves it in `needs-triage` after the second |
| `ticket.refused` | Fix the event's `reason`; step 4 starts it if the frontier permits |
| `worker.lost` | Step 4 gives back the claim and starts another worker in the standing workspace |
| `relay.recovered since <time>` | Nothing; later wakes carry the recovered events |
| `watchdog: relay down (…)` | Nothing is relaying: `<dispatch> advance <spec>` starts it again for the recorded main agent; `open-ticket <n>` for one ticket |
| `watchdog: relay not reading (…)` | Nothing; it clears itself with the first read that works. When it repeats without clearing, tell the user the relay cannot read the tracker (network or credential) |
| `watchdog: #<n> liveness unknown: …` | `<dispatch> resume <n> "Say in one line where you are, then continue"`, and act on its exit as [Exit codes of `resume`](#exit-codes-of-resume) says |
| `watchdog: #<n> is held with no session to ask, …` | Read `status`; when nothing works the ticket, `<dispatch> retract <n>` |
| `watchdog: cannot read the tracker since <time>: …` | Run `gh issue view <n>` for the ticket the finding names; wait for tracker or network recovery, or leave credential repair to the user |
| `watchdog: #<n> events unreadable` | Leave the named comment for the user |
| A worker whose session is gone while its worktree, slot or claim still stand (`advance` says "if the worker … is gone, retract it") | `<dispatch> retract <n>`; a `0` on its summary line is something it could not release, and the line above says why. Step 4 starts the replacement |
| `watchdog: #<n> silent since <time> with nothing to wait on: …` | When `python3 <events.py> fold <n>` lists an open `contract` child, the worker is waiting on you: settle it by the `child.opened` of kind `contract` row. Otherwise resume it with the message under [Exit codes of `resume`](#exit-codes-of-resume) below |
| Any other live worker | Nothing; its result wakes you or its worker |
| The ticket needs the other worker grade | Give it exactly one of the `junior-worker` / `senior-worker` labels (none starts it as `junior-worker`; both, or a grade `models.json` has no row for, is refused); the next `start` reads it |

For a `contract` child, use this authority order exactly: **decision tickets and ADRs, then the spec, then the design package or the screen contract, each in its own domain, then domain documents, then the ticket body**. Fix it yourself when you can cite a written authority at that order: a higher authority, a more specific file within the same authority, a repository rule, or the artifact a baseline copied. Edit the tracker-owned spec, acceptance criterion, or ticket body directly; when a spec changes, leave the change-and-reason comment that the `to-spec` skill's `references/revising-a-spec.md` requires. Edit a repository-owned baseline through the normal `origin/<into>` commit and push procedure in `## 4. The closing pass` — never the design package, which is written only by the `design-pages` skill's `references/pull.md`. Correct every not-yet-landed ticket derived from the same bad statement. Comment on the child with the authority used, every published item corrected, the source commit, and the tickets checked; run `<dispatch> route <n> <child> fixed`, then resume the active worker with the exact correction, the commit it should integrate from, and `continue`.

When no authority settles the correction, or the proposed correction would overturn the user's decision or expand the spec, leave the choice to the user. Find every not-yet-started ticket derived from the same Parent decision, move each from `ready-for-agent` to `needs-triage`, and comment on the child with the unresolved options, your recommendation, and the ticket numbers moved. Leave the child open for the user. A ticket already being worked stays held at the contract question; do not rewrite its delivery while the authority is unresolved.

### Exit codes of `resume`

`resume` prints the next step of every exit on stderr; act on it. Exit 2 sent nothing: read `status` and do not send again. Exit 4 is the ordinary answer on a runner that cannot observe its sessions: the text went in, so do not send it again, and let the ticket's next event say whether the worker read it. When you run `resume` again after exit 3, word it so a worker that receives both messages reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`.

For `watchdog: #<n> silent since <time> with nothing to wait on: …`, run `<dispatch> resume <n> "You ended your turn with no result on the ticket. Carry on from where its events say you are. If something outside your code stops you, open a fault sub-issue saying what you ran and what you saw, then stop; if only a person can settle it, open a decision sub-issue, take the default and carry on."` Change no label.

## 4. The closing pass

The frontier is empty and `status` shows no live agent. If this spec's tickets still hold open findings — the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `python3 <events.py> fold <n>`, open until a `child.closed` on the ticket gives their `resolution` — route **exactly those**. If there are none, close this spec's Memory records as the end of this pass says ("Once every finding has a route"), then go to step 5.

**Read every ticket of the batch, not the ones you heard about.** A `child.opened` of kind `finding` wakes nobody: the three kinds that wake you are `contract`, `fault` and `decision`. So the findings you were woken for during the night are no measure of the findings that exist, and a pass built on your wakes reads a fraction of them. Take the ticket list from `<dispatch> status <spec>` — every row of that table is a ticket of this batch — and run the `fold` above on each one, one ticket at a time.

Every route is carried out by one command, run once per finding, and it is the only way a finding leaves this pass:

```bash
<dispatch> route <n> <child> fixed
<dispatch> route <n> <child> stale <invalid|fixed-elsewhere>
<dispatch> route <n> <child> became-ticket <new ticket>
```

`<n>` is the ticket the finding came from, the one whose `fold` lists it under `children`. `became-ticket <child>` makes the finding itself the ticket; `became-ticket <other issue>` closes the finding as that issue's duplicate. `route` writes the `child.closed` event that the night summary counts. Exit 1: run the same command again; it repeats no step. Exit 2: nothing was done, and stderr says why.

Judge each one by the four steps below, **in order, first match wins**, after the check that comes before them.

**Step 0, before you classify at all.** Check the condition the finding's own body states against the current `HEAD`. If it never held, run `<dispatch> route <n> <child> stale invalid` and do nothing else. If it held but a later ticket of the same batch or a closing-pass fix already resolved it, run `<dispatch> route <n> <child> stale fixed-elsewhere` and do nothing else. A judge's claim disproved by current evidence is `invalid`; a valid claim satisfied somewhere else is `fixed-elsewhere`. `fixed-elsewhere` is not a reviewer false positive.

1. **Does it fall inside another still-open ticket's `## Owns`?** → a ticket, `Blocked by` that open one. Not a question of size: the constraint is concurrency. Fixing it yourself in the origin-tracking checkout makes the next `advance` conflict when that ticket's branch merges.
2. **Is it a gap in the criteria themselves** — a `CHECK:` that is already green while the thing it names is broken or never reached? → a ticket, `senior-worker`, and it asks for a negative control.
3. **How many files does the fix touch?** One → fix it yourself. Two or more **with a design coupling between them** — how you fix one decides how you fix the other, and neither can be written until both are settled → a ticket, `senior-worker`. Counting files is not counting effort; it is asking whether the change has a cross-file shape somebody should look at. **A name echoed through prose is not a coupling**: renaming a thing along with its restatements in a domain doc, a `SKILL.md` and a reference file is mechanical, `grep` proves you got them all, and it stays with you.
4. **Nothing matched** → fix it yourself. **The default is to fix it, not to open a ticket.**

The ones you fix: use a checkout that tracks `origin/<into>`. Fetch before each fix, commit it there, run the affected tests, and fast-forward push it to `origin/<into>`. If that push is rejected, fetch, merge the new `origin/<into>` into the commit, run the affected tests again, and retry the fast-forward push. Then `<dispatch> route <n> <child> fixed` for each, after its commit and push. The commits follow these three rules:

1. One commit per finding, or per group of findings with one cause; the commit message names them by number.
2. It touches only the files that finding names.
3. It runs the affected test suites, and the commit message quotes the line it saw (`ran 188 skipped 0`, not "the tests pass").

A fix that exceeds those three is a ticket after all.

The ones that become tickets: open as few tickets as possible. A ticket whose files sit in another live ticket's `## Owns` is `Blocked by` that live ticket. A finding that is a ticket on its own becomes one in place — rewrite its body into a ticket, label it for the agent queue, then `<dispatch> route <n> <child> became-ticket <child>`; findings folded into one new ticket each get `<dispatch> route <n> <child> became-ticket <that ticket>`.

A ticket you write here is dispatched in this night, and it has had none of the reading the published batch had. Write it to the `<issue-template>` of the `to-tickets` skill's `SKILL.md`, with every criterion in the four-line shape that file's **4. Write each acceptance criterion** gives, and only what its five questions admit as a criterion. Two shapes come back from a night's findings and neither is a criterion: prose that states a rule with no command under it, and the repository's own whole-tree checker — a `lint.sh`, a full type-check — put in a `CHECK:`, which fails on files this ticket never touched and blocks it on somebody else's work.

Then lint each ticket you wrote or rewrote, before you dispatch it:

```bash
<engine> <n> --lint
```

Read its exit as in 1b; fix every `ERROR` and lint again.

Once every finding has a route, close this spec's Memory records before leaving the pass.
List the repository space by the exact `mmw-spec-<spec>` label with a limit large enough
to return the whole set, and inspect every returned record. Get the Space id from the
tracker repository rather than from this session's `NMEM_SPACE`:

```sh
mmw_closeout_space="$(gh repo view --json nameWithOwner -q .nameWithOwner |
  tr '[:upper:]' '[:lower:]' | sed 's|/|__|')"
nmem --json memories list --space "$mmw_closeout_space" \
  --label "mmw-spec-<spec>" --limit 1000
```

If `gh repo view` did not give `owner/name`, run it again once the tracker answers;
never read Default as this repository.

For each id decide exactly
one of `retain`, `propose`, `deprecate` or `supersede`: `retain` remains useful as it is;
`propose` is a candidate for the later retro and does not change the Memory here;
`deprecate` is no longer valid; `supersede` names the existing `replacement_id` that
replaces it. A `propose` decision's `evidence` is exactly one event comment URL
(`https://github.com/<owner>/<name>/issues/<n>#issuecomment-<id>`) or commit URL
(`https://github.com/<owner>/<name>/commit/<40-hex sha>`): the retro counts the
proposal only when that string is one of its problem's sources, and `summary` refuses
any other value. Write the result as one UTF-8 JSON object:

```json
{"status":"complete","total":2,"returned":2,"decisions":[{"memory_id":"<id>","decision":"retain","reason":"<why>","evidence":"<where that was established>"},{"memory_id":"<old id>","decision":"supersede","reason":"<why>","evidence":"<where that was established>","replacement_id":"<existing id>"}]}
```

The ids must be the exact, duplicate-free set from the fresh complete list, and
`total` must equal `returned`. When Nowledge Mem cannot return a readable list, or says
it returned fewer rows than its total, do not infer an empty set and do no lifecycle
work: write `status` `unchecked` with its `reason`, and `summary` names the other fields
it requires. Keep this object for step 5. Done when the decisions object names one
decision for every id of the fresh list, or is an `unchecked` object with its reason.

Then:

```bash
<dispatch> advance <spec>
```

Loop: each `ticket.passed` wakes you at step 3; when the frontier is empty again, this pass runs again. Continue until no open finding survives. Then go to step 5.

## 5. The night is over

Step 4 left no open finding. From any checkout in this repository:

```bash
<dispatch> reverify <spec>
<dispatch> summary <spec> --memory-decisions <file>
```

`reverify` exit 0: every landed ticket is green. Exit 1: each red ticket is already reopened in `needs-triage`; do not close it. Exit 2: fix stderr's named condition and run `reverify` again.

To recover a reopened ticket, repair the cause on the base branch, push it, and run `reverify <spec>` again; all met, `reverify` closes it itself. Still red, `summary` refuses the night: tell the user which ticket stays red and why, and stop.

When `summary` refuses the decisions file, list the Memory records again, rewrite the file, and run `summary` again; a rerun repeats no completed action.

Tickets left for human acceptance, handed back to triage by their worker, or behind an open blocker are valid outcomes; `summary` does not require every ticket to succeed.

`summary` exit 0: `NIGHT SUMMARY` is posted and the spec watch is closed. Exit 1: posted and closed, and a relay was left running; end the pid stderr names. Exit 2: nothing was posted; fix what stderr names and run `summary` again. A refusal counting findings no route reached sends you back to step 4.

Immediately after `summary` records `spec.closed` (exit 0, or exit 1 with the comment confirmed), invoke the `retro` skill in this same main-agent session for this spec; `finish` needs its `recorded` receipt.

Then tell the user the night finished, point them at `NIGHT SUMMARY` and `NIGHT RETRO`, and say that after they accept the result the main agent will run `finish` to merge it into the project branch.

## 6. Merge the accepted night

Only after the user has accepted the result, the main agent runs:

```bash
<dispatch> finish <spec>
```

`finish` checks its own preconditions and names on stderr any that is missing. It merges `origin/<base branch>` into `origin/<project branch>`, records `spec.merged`, and deletes the base branch wherever that is safe. A worktree that has the base branch checked out, usually the one this session runs in, is kept: stderr gives the commands that remove it, for the user to run once this session is done, and `finish` needs no second run.

Exit 0: the merge is recorded. Exit 1: the merge conflicted or the repository checks failed, and nothing was pushed or deleted. Exit 2: fix what stderr names and run `finish` again. Do not merge the project branch into the repository default branch here; that remains the user's release decision.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> suspend <spec>` is that decision carried out.

It stops every session still holding a ticket of the batch, commits and pushes each stopped ticket branch, and gives back its claim and slot; a ticket it cannot stop or push keeps everything, and nothing is force-pushed. The spec's watch closes: a suspended night wakes nobody.

Workspaces and branches stay, with the interrupted tickets' commits present on origin. The same batch is taken up again with `<dispatch> open <spec>` and then `<dispatch> advance <spec>` once whatever stopped the night is fixed: `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

Exit 0: the night is stopped. Exit 1: stderr names, one line each, what was left. For a slot a process still listens on (`lease.py` names the port and the pid), stop that process where it was started and run `python3 <lease.py> release <its worktree>`; tell the user every other line. Exit 2: nothing was touched; fix what stderr names and run `suspend` again. Done when `suspend` exits 0, or exits 1 and you have told the user each line stderr left.
