# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create workspaces, and print the arguments for `create_agent`. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. The commands, their exit codes, and the two shapes that wake you are in `SKILL.md` next to this file. Resolve `<dispatch>` the same way that file does, and add its two `--tools` flags to every command here.

You sleep between the steps below. Every agent this pipeline starts says when it is done — a reviewer and a verifier wake the worker that started them, a worker wakes you — so there is nothing to poll and no reason to hold a turn open.

## 1. The user says the night starts

Run, in this checkout, on the branch the night merges into:

```bash
<dispatch> check <spec>
```

**Exit 0:** the machine is ready, and `check` has created the night's heartbeat — `mmw-night-<spec>`, at 7 and 47 minutes past each hour (40 minutes apart, then 20), prompt `land --sweep, then status <spec>, act per step 3`, id in `.git/mmw-heartbeat-<spec>`; `summary` and `suspend` delete it by that id, and it expires on its own after 16 hours in case neither ever runs — nothing lists heartbeats, so one whose id file is gone could otherwise fire for ever with no command able to reach it. It wakes and it sweeps; it never judges. A fire while you are busy is reported failed and simply fires next time. What the sweep covers is the one failure a working night cannot see: a ticket lands, and the message saying so never arrives — `notify_parent` writes one stderr line and gives up when there is no `PASEO_AGENT_ID`, when the parent is already archived, or when `paseo send` errors. The sweep asks Paseo what is here and the tracker what is finished, so it needs none of that to have worked. Then go to step 2. **Exit 2:** stderr is one line per failure (`install.sh --check`, a provider whose `status` is not `available`, a queued ticket with two worker-grade labels or a label `models.md` has no row for). Fix what the lines name, or tell the user if only they can, then run `check` again. Do not `advance` on 2.

## 2. First `advance`

Stay on this branch all night. Every `advance` merges into whatever `HEAD` is on.

```bash
<dispatch> advance <spec>
```

**Exit 0:** stdout is zero or more JSON lines, one per ticket on the frontier. For each line, call `create_agent` with every field except `fallback`. A `create_agent` that fails to start the provider is the `create_agent` failed to start the provider row of `SKILL.md`, not a second guess at the host. Then end your turn. **Exit 2:** nothing was touched; read stderr; if it is uncommitted changes, commit or set them aside and run `advance` again; if it is the `.git` lock, run `advance` again. **Exit 3:** a merge is in conflict, still in the tree. Resolve it with the `resolving-merge-conflicts` skill — never `--abort` — run this repository's own checks, commit the merge, then `advance` again.

What `advance` does inside that one command — merge, archive, give claims back, then dispatch — is the next section.

## `advance` merges, releases, then dispatches

`<dispatch> advance <spec>` merges the branch of every ticket that closed with `ALL MET` into the branch you are on at that moment, archives each merged ticket's workspace, gives back the claims whose workers are gone, then dispatches every ticket on the frontier. The branch you open the night on is the base branch, so stay on it all night: every `advance` merges into whatever `HEAD` is on, and `git config branch.issue-<n>.mmw-base-branch` is a record for readers, not something `advance` consults.

The four are one command because the order is the reason. A worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see; the frontier is read after the claims come off, so a ticket freed by this run starts in this run rather than the next one; and `advance` archives a ticket's workspace only after that ticket's branch is already in `HEAD`, releasing its lease first.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its closing comment opens `ALL MET`, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. The fourth is what makes the command safe to run at any time: a branch already merged is skipped, and an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

A ticket is claimed by being assigned to the account this pipeline is signed in as — `verify-ticket.py --preflight` does it — and the frontier takes only unassigned tickets, which is what keeps a second worker off a ticket somebody is already working. Three paths give a claim back: the closeout, the hand back to triage, and `land`. A session that ends any other way — a crash, a machine restart, a workspace archived from outside this pipeline — leaves the claim standing, and from then on the ticket is off every frontier for good, with an empty frontier as the only sign of it.

So `advance` gives a claim back when four things hold at once: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and nothing holds it. That last one is read off the tracker, not off Paseo. An agent that has finished stops at `idle`, and so does one asleep on a subagent; on 2026-09-07 this machine listed 43 agents that had run to completion and not one of them was `closed`. A ticket is held while it is open and carries no verdict either way, and it is a ticket the tracker says is closed or handed back that nothing holds any more. The write is `gh issue edit <n> --remove-assignee @me`, so a ticket a person took for themselves is untouched and stays off the frontier, which is the right answer — somebody has it. Each release prints one line naming the ticket and saying why, and that line is not decoration: `paseo ls` answers for this machine and no other, so a worker of the same account running on a second machine reads from here as a claim whose owner is gone.

A standing workspace is not a run. Paseo owns every run this pipeline starts, so an agent it no longer lists, or lists as `closed`, is not working, whatever directory is still on disk; the workspace stays for `start` to reuse, and the next worker picks the branch up where the last one left it.

When nothing can start and the batch still holds open tickets in the agent queue, `advance` names each of those tickets on stderr with the condition holding it — claimed by somebody, blocked by a ticket still open, or already held by a live worker. An empty frontier and a finished batch print the same nothing otherwise, and the difference between them is not visible from outside the frontier's five conditions. The exit code is unchanged: this is an explanation, not a failure.

A product that cannot move its ports says so in `.mmw/target.json` as `"instance": {"max": <n>}`. `advance` then starts at most `max` minus the leases already counted under this checkout's workspaces, and holds the rest on the frontier for the next advance. Held is not a refusal and not a claim: the ticket keeps its label, stderr says how many and why.

## 3. Each time something wakes you

Two things wake you, and both end here: a **ticket message** whose first line is `#<n> ALL MET`, `#<n> HANDOFF REQUIRED`, `#<n> NOT_READY` or `#<n> SUB-ISSUE pipeline`, sent by `verify-ticket.py` the moment that ticket came to rest; or a **heartbeat fire**, which says nothing at all. No finish notification reaches you: the only agent you start is the worker, and it is started with `notifyOnFinish: false` so that its middle states — asleep on a verifier, asleep on a reviewer — do not reach you as news.

1. Were you running a command when it arrived? A ticket message interrupts, and the command reports being interrupted rather than finishing. Run that command again before anything else — `advance` in particular is written to be run again at any time, and picks up whatever the interrupted run left behind.
2. Run `<dispatch> status <spec>`. The table's `note` column is `needs permission`, `ready`, `waiting on #<m>`, `closed: archive it` (Paseo still lists the agent but it is not running), the newest comment, or empty while a worker is live.
3. Any row noting `needs permission`: `list_pending_permissions` then `respond_to_permission` (CLI: `paseo permit`). This is not a stop, and the table is the only place it shows — a worker started with `notifyOnFinish: false` does not announce it, so the heartbeat is what brings this row to your eye when nothing else does.
4. Take every row the table matches, not only the ticket you were woken about. What woke you says one thing happened; the table says what is true, and two tickets landing seconds apart wake you once.

| What you see | What you do |
| --- | --- |
| A ticket just closed `ALL MET`, or the frontier has `ready` rows and no live worker on them | `<dispatch> advance <spec>`, then `create_agent` on each new line (every field except `fallback`; a failure to start the provider is the `SKILL.md` row of that name) |
| The worker is live and the work should continue | `<dispatch> resume <n> "<what you settled, then: continue>"`. Exit 3 means it is in a turn and did not take the message: wait and run the same command again, do not go looking for another way to reach it |
| `resume` has exited 3 several times and you cannot tell whether it is working or stuck | Ask `get_agent_status` for that agent. An `activeTurn` naming a turn means it is working. An `activeTurn` of null while the send still fails means the session is stuck: a rejected send left `lastError` set, the send path reads that field, and it will take no message again. Archive it and `<dispatch> start <n> worker` — the workspace and branch are reused, the commits are all there, and what the worker was told in that session is not |
| The worker has stopped and the ticket has a new child whose first line is `SUB-ISSUE pipeline` | Read that sub-issue (`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100`). Fix the cause it names. Then `<dispatch> resume <n> "… continue"` |
| `status` shows the ticket still `OPEN`, and `paseo ls --label mmw.ticket=<n>` shows a live child labelled `mmw.kind=reviewer` or `mmw.kind=verifier` | Not a stop: the worker is asleep on that child and wakes when it finishes. Do nothing |
| The message reads `#<n> NOT_READY` | The ticket refused to be claimed and `--preflight` said why in a comment on it. Fix what that comment names, then `<dispatch> advance <spec>` |
| A row whose `note` ends in `· land it`: the ticket has come to rest and its agents are still listed | `<dispatch> land <n>`. It merges, archives the workspace with its agents, and gives the slot and the claim back. `advance` does the same for the whole batch, so either ends this row |
| `status` notes `closed: archive it`, or `paseo logs <id>` shows only the prompt with no output (an agent created before the daemon restarted answers this way) | `paseo archive <id>`, then `<dispatch> advance <spec>`: with no agent on the ticket and its claim given back, the ticket is on the frontier again and `start` reuses its standing workspace and branch |
| The ticket has no closing comment, the worker is not running, and `paseo logs <id>` shows what stopped it | Fix that — a file it could not find, a command it needs, a baseline it read wrong — then `resume` with that plus `continue`. A question only a person can settle: `resume` telling the worker to open it with `verify-ticket.py <n> --sub-issue decision <file>`, take the default meanwhile, and record it under `Decisions I made on my own`. Change no label |
| The worker is live and nothing is wrong | Do not `resume`. End your turn |
| `status` shows an empty frontier and no live agent of this spec | Go to step 4 |

Then end your turn. Most tickets that land are followed by another `advance`. The heartbeat from step 1 only wakes; it does not judge.

## 4. The night is over

The frontier is empty and `status` shows no live agent. Then, still on this branch:

```bash
<dispatch> reverify <spec>
<dispatch> summary <spec>
```

`reverify` re-runs every closed `ALL MET` ticket's criteria against this `HEAD`. Exit 0: all green. Exit 1: each red ticket is already reopened, labelled `needs-triage`, unassigned, and commented with the failing `AC<n>` — that is the morning's triage queue; do not close those tickets.

`summary` posts a comment on the spec whose first line is `NIGHT SUMMARY <date>`, with the four lines `Closed:`, `Handed back to needs-triage:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:`. If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended.

`summary` also deletes the heartbeat `check` created and removes `.git/mmw-heartbeat-<spec>`.

Tell the user the night finished, and point them at that comment.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> suspend <spec>` is that decision carried out.

It archives every live worker of the batch with `paseo archive --force <id>`: the worker is interrupted and taken off the agent list, its reviewer and verifier with it, and the workspace and the branch stay. `--force` is the part that matters — plain `paseo archive` refuses a running agent, and a worker in the middle of a turn is the whole reason to suspend a night. A worker that survives the archive anyway keeps its slot rather than having its product stopped underneath it: a live worker starts the product again, and the `stop` in between tears up the record of what it started, leaving processes that `stop` can no longer reach. Then every ticket still in the agent queue gets one comment opening `NIGHT SUSPENDED #<spec>`, with the time and whether a worker was interrupted on it, and its claim is given back. Without the comment the morning reader finds a row of tickets with no verdict and no way to tell them from work in progress; without the claim given back, `advance` never takes the ticket up again. A ticket a worker handed back to triage during the night already carries its own verdict, so it is left alone.

Workspaces and branches stay, and the same batch is taken up again with `<dispatch> advance <spec>` once whatever stopped the night is fixed: each ticket is unclaimed and held by no agent, so it is on the frontier, and `start` reuses its standing workspace. That is the reason to suspend a night rather than let it run: the fix is carried on with the same worktrees, and a batch dispatched again from scratch would throw the night's work away along with the night.

The slots are given back for every ticket of the batch, handed back ones included, because the gate in `advance` counts claims rather than sessions and the next night would otherwise read the machine as fuller than it is. Each one is given back the way every slot is: the product's own `stop`, run from that worktree, then the release. `lease.py` refuses a slot something still listens on after that and names the port and the pid; `suspend` reports that and exits 1 rather than forcing it, because taking a slot off a live process is the same act as ending it.

It then deletes the main agent's heartbeat (`paseo heartbeat delete`) when `.git/mmw-heartbeat-<spec>` names one; a night that never wrote that file has no heartbeat to delete. After that, `advance` can run again.
