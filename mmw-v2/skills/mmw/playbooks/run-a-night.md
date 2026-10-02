### Run a night

**You own the night's decisions, never a worker's code.**

The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a child, whether to `advance` again.

The night is read in the morning by the user, cold, from `NIGHT SUMMARY`, `NIGHT RETRO` and the tracker, with none of this session's context. So each decision you make leaves its reason where that reader will look: on the child, the ticket or the spec, in a comment that stands on its own. A reason that lives only in this session is lost when it ends. The night's output is a batch the user can accept in the morning, not a count of closed tickets. A ticket handed back with its reason on it is a good result; a criterion loosened, or a worker resumed again and again with `continue`, to make one close is a defect that lands under a green mark (**principle-silence-is-never-a-pass**).

Commands of this skill's `bash scripts/dispatch.sh` are named bare below.

**Entry.**
- **The user starts the night.** The user asks for a spec's whole batch to run, and the spec carries no `spec.opened`: start at **Check and open**.
- **Woken.** Go to the step the wake's pointer names, after mode `## Re-entry`.
- **Compacted, or unsure.** **Where you are.**
- **Suspended.** A night whose newest event is `spec.suspended` has no step to resume: `#### Suspending the night` says how the same batch is taken up again.

**Where you are.** Run `dispatch.sh where <spec>` and go to the step it prints.

#### Steps

1. **Check and open.** Run `dispatch.sh check <spec>`, then `open-night`, from a checkout on the night's base branch: the current checkout names it.
   **Exit 0:** the machine is ready; open the night. **Exit 2:** fix every condition stderr names and run `check` again; an invalid agent row is reported to the user.
   When `check` exits 0 and stderr carries a `dispatch: warning: install.sh --check still finds this` paragraph, show the user the lines under it and ask whether they authorise the install; run `open-night` only after they answer, with the install or without it.
   Then run `dispatch.sh open-night <spec>` from this session, the one the night's wakes must reach.
   **Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>; task board <url> · <step pointer>`, and this session is the night's orchestrator. **Exit 2:** fix stderr's named condition and run `open-night` again.
   Hand the user the task board URL from that line in your first message of the night. A board that did not start is one stderr line and holds nothing up; `bash scripts/dispatch.sh board` starts it later.
   Done when `open-night` has exited 0 and your first message of the night gives the user the task board URL, or the stderr line saying the board did not start.

2. **Lint the batch.** Run this once, before the first `advance`, on every spec, with the `verify-ticket` skill's `python3 scripts/verify-ticket.py <spec> --lint`.
   Exit 0: no `ERROR`. Exit 1: fix each `ERROR` on its ticket, except one saying the tracker could not answer (tagged `[parent-unreadable]` or `[sub-issues-unreadable]`, or a traceback from a `gh` call): nothing about the tickets was established, so run the same command again once the tracker answers. Exit 2: a criterion names an oracle this run cannot reach, and nothing was read.
   When the batch drives a screen contract, whether the consuming repository can be driven at all is a separate question, answered there by the `ui-acceptance` skill's `target_config.py --check`, which prints every `.mmw/target.json` field still to answer and exits 0 once the file is complete.
   Done when `--lint` on the spec exits 0, and, when the batch drives a screen contract, `target_config.py --check` exits 0 in the consuming repository.

3. **Advance, then end your turn.** Run `dispatch.sh advance <spec>`, then end your turn (**principle-agents-are-woken-not-polled**). The relay `open-night` started wakes you when a ticket of the batch gets an event that needs the orchestrator (**Handle each wake**), and the watchdog tells you when the tracker has gone silent where it should not; nothing else does, and no agent polls another.
   After `open-night` records `into`, `advance` may run from any checkout in this repository. It does not move that checkout or any local base branch.
   **Exit 0:** end your turn. **Exit 4:** a runner refused a start; stderr names each refusal, and none is retried. Fix what each names and run `advance` again; end your turn only while another worker of the night remains live, and if none does, tell the user which tickets were refused and why. **Exit 2:** fix what stderr names and run `advance` again (a night that is not open: `open-night <spec>` first); the rest of the batch was landed and started.
   Done when `advance` has exited 0 and you have ended your turn, or it exited 4 with no worker of the night live and you have told the user which tickets were refused and why.

4. **Handle each wake.** Take the wakes one at a time, in the order below: two tickets landing seconds apart are two wakes, and you get the second after you end your turn.
   - Do mode `## Re-entry` up to and including **Ack the wake**.
   - Run `bash scripts/dispatch.sh status <spec>`. Exit 0 prints the table; exit 2 means the tracker did not return the whole batch, so run it again when the tracker answers.
   - Take every row the table matches, not only the ticket named by the wake. Do what the Night orchestrator column of `references/orchestrator-wakes.md` says for each row.
   - Run `bash scripts/dispatch.sh advance <spec>` once. Its exit codes are under **Advance, then end your turn**.
   - When the `advance` you just ran left the frontier empty and no agent live (read `status` again), go to **Closing pass**; otherwise end your turn.

   A `contract` child is settled as `#### Contract children` says, and a decision nobody is there to make is recorded as `#### Unattended outlets` says.
   Done when every row `status` printed for this wake has been acted on, `advance` has run once after them, and you have ended your turn or gone to **Closing pass**.

5. **Closing pass.** Give every open finding its `resolve-child` as `#### Closing pass` says, then run `dispatch.sh advance <spec>`.
   Loop: each `ticket.passed` wakes you at **Handle each wake**; when the frontier is empty again, this pass runs again. Continue until no open finding survives.
   Done when `dispatch.sh findings <spec>` prints no finding, and `status` shows an empty frontier and no live agent.

6. **Close the Memory records.** Once every finding has a route, close this spec's Memory records.
   Run `bash scripts/dispatch.sh prepare-memory-decisions <spec>` and save its output to a file: it computes the repository's Space id, pulls the spec's full `mmw-spec-<spec>` record set, and writes a `--memory-decisions` file skeleton with `total` and `returned` already filled in, one entry per record, or a ready-made `unchecked` object when the list could not be read or was truncated.
   Write the closing decision for each id in the file as the `memory-records` skill says. Keep the file for **Reverify and summarize**.
   Done when the file is finished as the `memory-records` skill's `## Close a spec's records` says.

7. **Reverify and summarize.** **Closing pass** left no open finding. From any checkout in this repository, run `dispatch.sh reverify <spec>`, then `dispatch.sh close-night <spec> --memory-decisions <file>`.

   `reverify` exit 0: every landed ticket is green. Exit 1: each red ticket is already reopened in `needs-triage`; do not close it. Exit 2: fix stderr's named condition and run `reverify` again.
   To recover a reopened ticket, repair the cause on the base branch, push it, and run `reverify <spec>` again; all met, `reverify` closes it itself. Still red, `close-night` refuses the night: tell the user which ticket stays red and why, and stop.
   When `close-night` refuses the `--memory-decisions` file, list the Memory records again, rewrite the file, and run `close-night` again; a rerun repeats no completed action.
   Tickets left for human acceptance, handed back to triage by their worker, or behind an open blocker are valid outcomes; `close-night` does not require every ticket to succeed.

   `close-night` exit 0: `NIGHT SUMMARY` is posted and the spec watch is closed. Exit 1: posted and closed, and a relay was left running; end the pid stderr names. Exit 2: nothing was posted; fix what stderr names and run `close-night` again. A refusal counting findings no `resolve-child` reached sends you back to **Closing pass**.
   Done when `close-night` has exited 0, or has exited 1 with `NIGHT SUMMARY` posted on the spec.

8. **Retro.** Immediately after `close-night` records `spec.closed` (exit 0, or exit 1 with the comment confirmed), invoke the `retro` skill in this same orchestrator session for this spec; `finish` needs its `spec.retroed` event, recorded.
   Done when the spec carries a `spec.retroed` event whose result is `recorded`.

9. **Hand the night to the user.** Tell the user the night finished, and point them at `NIGHT SUMMARY` and `NIGHT RETRO`.
   Once they answer, run **Accept the night** with them; until then, end your turn.
   Done when your reply names `NIGHT SUMMARY`, `NIGHT RETRO` and **Accept the night**.

#### Contract children

While a worker holds a ticket, its code is the worker's: you change what the worker works from (the spec, the ticket body, a criterion, a baseline, under the authority order below) and tell it through `resume`, never its worktree or branch. Your own fixes wait for the closing pass, on `origin/<into>`.

For a `contract` child, use this authority order exactly: **decision tickets and ADRs, then the spec, then the design package or the screen contract, each in its own domain, then domain documents, then the ticket body**. Fix it yourself when you can cite a written authority at that order: a higher authority, a more specific file within the same authority, a repository rule, or the artifact a baseline copied. Edit the tracker-owned spec, acceptance criterion, or ticket body directly; when a spec changes, leave the change-and-reason comment that the `to-spec` skill's `references/revising-a-spec.md` requires. Edit a repository-owned baseline through the normal `origin/<into>` commit and push procedure in `#### Closing pass`. Correct every not-yet-landed ticket derived from the same bad statement. Comment on the child with the authority used, every published item corrected, the source commit, and the tickets checked; run `bash scripts/dispatch.sh resolve-child <n> <child> fixed`, then resume the active worker with the exact correction, the commit it should integrate from, and `continue`.

#### Unattended outlets

A decision about one child or one ticket leaves its reason in a comment on that child or ticket. Every other decision you take with nobody to ask, each `skip:` line of your todolist and each principle that changed a decision go into one comment on the spec, which the user reads beside `NIGHT SUMMARY`.

When no authority settles a `contract` child's correction, or the proposed correction would overturn the user's decision or expand the spec, leave the choice to the user. Find every not-yet-started ticket derived from the same Parent decision, move each from `ready-for-agent` to `needs-triage`, and comment on the child with the unresolved options, your recommendation, and the ticket numbers moved. Leave the child open for the user. A ticket already being worked stays held at the contract question; do not rewrite its delivery while the authority is unresolved.

#### Closing pass

The frontier is empty and `status` shows no live agent. If this spec's tickets still hold open findings (the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `events.py fold <n>`, open until a `child.closed` on the ticket gives their `resolution`), route **exactly those**.

List the open findings with `dispatch.sh findings <spec>`. A finding wakes nobody, so the ones you were woken about are no measure of what exists.

Every route is carried out by one command, run once per finding, and it is the only way a finding leaves this pass:

```bash
bash scripts/dispatch.sh resolve-child <n> <child> fixed
bash scripts/dispatch.sh resolve-child <n> <child> stale <invalid|fixed-elsewhere>
bash scripts/dispatch.sh resolve-child <n> <child> became-ticket <new ticket>
```

`<n>` is the ticket the finding came from, the one whose `fold` lists it under `children`. `became-ticket <child>` makes the finding itself the ticket; `became-ticket <other issue>` closes the finding as that issue's duplicate. `resolve-child` writes the `child.closed` event that the night summary counts. Exit 1: run the same command again; it repeats no step. Exit 2: nothing was done, and stderr says why.

Judge each one by the four steps below, **in order, first match wins**, after the check that comes before them.

**Step 0, before you classify at all.** Check the condition the finding's own body states against the current `HEAD`. If it never held, run `bash scripts/dispatch.sh resolve-child <n> <child> stale invalid` and do nothing else. If it held but a later ticket of the same batch or a closing-pass fix already resolved it, run `bash scripts/dispatch.sh resolve-child <n> <child> stale fixed-elsewhere` and do nothing else. A finding's claim disproved by current evidence is `invalid`; a valid claim satisfied somewhere else is `fixed-elsewhere`. `fixed-elsewhere` is not a reviewer false positive.

1. **Does it fall inside another still-open ticket's `## Owns`?** → a ticket, `Blocked by` that open one. Not a question of size: the constraint is concurrency. Fixing it yourself in the origin-tracking checkout makes the next `advance` conflict when that ticket's branch merges (**principle-separate-before-serializing-shared-state**).
2. **Is it a gap in the criteria themselves** (a `CHECK:` that is already green while the thing it names is broken or never reached)? → a ticket, `senior-worker`, and it asks for a negative control (**principle-silence-is-never-a-pass**).
3. **How many files does the fix touch?** One → fix it yourself. Two or more **with a design coupling between them** (how you fix one decides how you fix the other, and neither can be written until both are settled) → a ticket, `senior-worker`. Counting files is not counting effort; it is asking whether the change has a cross-file shape somebody should look at. **A name echoed through prose is not a coupling**: renaming a thing along with its restatements in a domain doc, a `SKILL.md` and a reference file is mechanical, `grep` proves you got them all, and it stays with you.
4. **Nothing matched** → fix it yourself. **The default is to fix it, not to open a ticket.**

The ones you fix: use a checkout that tracks `origin/<into>`. Fetch before each fix, commit it there, run the affected tests (`shared.md` rule 15), and fast-forward push it to `origin/<into>`. If that push is rejected, fetch, merge the new `origin/<into>` into the commit, run the affected tests again, and retry the fast-forward push. Then `bash scripts/dispatch.sh resolve-child <n> <child> fixed` for each, after its commit and push. The commits follow these three rules:

1. One commit per finding, or per group of findings with one cause; the commit message names them by number.
2. It touches only what the finding's cause requires, and the tests that prove it; anything more is a ticket after all.
3. It runs the affected test suites, and the commit message quotes the line it saw (`ran 188 skipped 0`, not "the tests pass").

The ones that become tickets: open as few tickets as possible. A ticket whose files sit in another live ticket's `## Owns` is `Blocked by` that live ticket. A finding that is a ticket on its own becomes one in place: rewrite its body into a ticket, label it for the agent queue, then `bash scripts/dispatch.sh resolve-child <n> <child> became-ticket <child>`; findings folded into one new ticket each get `bash scripts/dispatch.sh resolve-child <n> <child> became-ticket <that ticket>`.

A ticket you write here is dispatched in this night, and it has had none of the reading the published batch had. Write it to the `<issue-template>` of the `to-tickets` skill's `SKILL.md`, with every criterion in the four-line shape that file's **4. Write each acceptance criterion** gives, and only what its five questions admit as a criterion. Two shapes come back from a night's findings and neither is a criterion: prose that states a rule with no command under it, and the repository's own whole-tree checker (a `lint.sh`, a full type-check) put in a `CHECK:`, which fails on files this ticket never touched and blocks it on somebody else's work.

Then lint each ticket you wrote or rewrote, before you dispatch it:

```bash
verify-ticket.py <n> --lint
```

Read its exit as in **Lint the batch**; fix every `ERROR` and lint again.

Gather every `## Manifest notes` line of the night's `REVIEW` reports into one comment on the spec, one line per sentence with its ticket and the proposed change; the user marks the sentences a later batch rewrites.

#### Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `bash scripts/dispatch.sh suspend <spec>` is that decision carried out.

A suspended night wakes nobody: its watch is closed. Its workspaces and branches stay, with the interrupted tickets' commits on origin; once whatever stopped the night is fixed, `open-night <spec>` and then `advance <spec>` take the batch up again, and `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

Exit 0: the night is stopped. Exit 1: stderr names, one line each, what was left. For a slot a process still listens on (`lease.py` names the port and the pid), stop that process where it was started and run `lease.py release <its worktree>`; tell the user every other line. Exit 2: nothing was touched; fix what stderr names and run `suspend` again. Done when `suspend` exits 0, or exits 1 and you have told the user each line stderr left.

**Reply:** `NIGHT SUMMARY` and the `spec.retroed` event, and the comment on the spec that carries this session's `skip:` lines and the principles that changed a decision.
