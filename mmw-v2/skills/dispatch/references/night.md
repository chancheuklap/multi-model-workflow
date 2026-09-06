# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create workspaces, and print the arguments for `create_agent`. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. The commands, their exit codes, and the shape of a finish notification are in `SKILL.md` next to this file. Resolve `<dispatch>` the same way that file does, and add its two `--tools` flags to every command here.

## 1. The user says the night starts

Run, in this checkout, on the branch the night merges into:

```bash
<dispatch> check <spec>
```

**Exit 0:** create a heartbeat (`create_heartbeat`; CLI `paseo heartbeat create --cron '*/10 * * * *'`) with the fixed prompt `run status <spec>, act per step 3`. Write the heartbeat's id to `.git/mmw-heartbeat-<spec>` in this checkout — `suspend` deletes by that id. It only wakes; it never judges. A fire while you are busy is reported failed and simply fires next time. Then go to step 2. **Exit 2:** stderr is one line per failure (`install.sh --check`, a provider whose `status` is not `available`, a queued ticket with two worker-grade labels or a label `models.md` has no row for). Fix what the lines name, or tell the user if only they can, then run `check` again. Do not `advance` on 2.

## 2. First `advance`

Stay on this branch all night. Every `advance` merges into whatever `HEAD` is on.

```bash
<dispatch> advance <spec>
```

**Exit 0:** stdout is zero or more JSON lines, one per ticket on the frontier. For each line, call `create_agent` with that object and `notifyOnFinish: true`. Then wait. **Exit 2:** nothing was touched; read stderr; if it is uncommitted changes, commit or set them aside and run `advance` again; if it is the `.git` lock, run `advance` again. **Exit 3:** a merge is in conflict, still in the tree. Resolve it with the `resolving-merge-conflicts` skill — never `--abort` — run this repository's own checks, commit the merge, then `advance` again.

What `advance` does inside that one command — merge, archive, give claims back, then dispatch — is the next section.

## `advance` merges, releases, then dispatches

`<dispatch> advance <spec>` merges the branch of every ticket that closed with `ALL MET` into the branch you are on at that moment, archives each merged ticket's workspace, gives back the claims whose workers are gone, then dispatches every ticket on the frontier. The branch you open the night on is the base branch, so stay on it all night: every `advance` merges into whatever `HEAD` is on, and `git config branch.issue-<n>.mmw-base-branch` is a record for readers, not something `advance` consults.

The four are one command because the order is the reason. A worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see; the frontier is read after the claims come off, so a ticket freed by this run starts in this run rather than the next one; and `advance` archives a ticket's workspace only after that ticket's branch is already in `HEAD`, releasing its lease first.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its closing comment opens `ALL MET`, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. The fourth is what makes the command safe to run at any time: a branch already merged is skipped, and an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

A ticket is claimed by being assigned to the account this pipeline is signed in as — `verify-ticket.py --preflight` does it — and the frontier takes only unassigned tickets, which is what keeps a second worker off a ticket somebody is already working. Two paths give a claim back: the closeout, and the hand back to triage. A session that ends any other way — a crash, a machine restart, a workspace archived from outside this pipeline — leaves the claim standing, and from then on the ticket is off every frontier for good, with an empty frontier as the only sign of it.

So `advance` gives a claim back when four things hold at once: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and no live worker holds it — no Paseo agent listed for the ticket whose `status` is other than `closed`. The write is `gh issue edit <n> --remove-assignee @me`, so a ticket a person took for themselves is untouched and stays off the frontier, which is the right answer — somebody has it. Each release prints one line naming the ticket and saying why, and that line is not decoration: `paseo ls` answers for this machine and no other, so a worker of the same account running on a second machine reads from here as a claim whose owner is gone.

A standing workspace is not a run. Paseo owns every run this pipeline starts, so an agent it no longer lists, or lists as `closed`, is not working, whatever directory is still on disk; the workspace stays for `start` to reuse, and the next worker picks the branch up where the last one left it.

When nothing can start and the batch still holds open tickets in the agent queue, `advance` names each of those tickets on stderr with the condition holding it — claimed by somebody, blocked by a ticket still open, or already held by a live worker. An empty frontier and a finished batch print the same nothing otherwise, and the difference between them is not visible from outside the frontier's five conditions. The exit code is unchanged: this is an explanation, not a failure.

A product that cannot move its ports says so in `.mmw/target.json` as `"instance": {"max": <n>}`. `advance` then starts at most `max` minus the leases already counted under this checkout's workspaces, and holds the rest on the frontier for the next advance. Held is not a refusal and not a claim: the ticket keeps its label, stderr says how many and why.

## 3. Each finish notification

The notification's first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.` Title is `#<n> worker`, `#<n> reviewer` or `#<n> verifier`. One `create_agent` yields one terminal notification; a notification is not the ticket being done.

1. If it is `needs permission`: `list_pending_permissions` then `respond_to_permission` (CLI: `paseo permit`). Then go to 2. This is not a stop.
2. Run `<dispatch> status <spec>`. The table's `note` column is `needs permission`, `ready`, `waiting on #<m>`, `closed: archive it` (Paseo still lists the agent but it is not running), the newest comment, or empty while a worker is live.
3. Decide, using the table and the notification:

| What you see | What you do |
| --- | --- |
| A ticket just closed `ALL MET`, or the frontier has `ready` rows and no live worker on them | `<dispatch> advance <spec>`, then `create_agent` on each new line |
| The worker is live and the work should continue | `<dispatch> resume <n> "<what you settled, then: continue>"` |
| The worker has stopped and the ticket has a new child whose first line is `SUB-ISSUE pipeline` | Read that sub-issue (`gh api repos/{owner}/{repo}/issues/<n>/sub_issues`). Fix the cause it names. Then `<dispatch> resume <n> "… continue"` |
| The notification is `finished`, `status` shows the ticket still `OPEN`, and `paseo ls --label mmw.ticket=<n>` shows a live child labelled `mmw.kind=reviewer` or `mmw.kind=verifier` | Not a stop: the worker is blocking on `paseo wait` for that child and will carry on when it returns. Its one finish notification is spent; the heartbeat from step 1 runs `status` again within ten minutes. Do nothing. No live child and no closing comment: take the next matching row |
| The worker `was closed`, or `errored` and `paseo logs <id>` shows only the prompt with no output (an agent created before the daemon restarted answers this way) | `paseo archive <id>`, then `<dispatch> advance <spec>`: with no agent on the ticket and its claim given back, the ticket is on the frontier again and `start` reuses its standing workspace and branch |
| The worker `errored` short of a closing comment and `paseo logs <id>` shows what stopped it | Fix that — a file it could not find, a command it needs, a baseline it read wrong — then `resume` with that plus `continue`. A question only a person can settle: `resume` telling the worker to open it with `verify-ticket.py <n> --sub-issue decision <file>`, take the default meanwhile, and record it under `Decisions I made on my own`. Change no label |
| The worker is live and nothing is wrong | Do not `resume`. Wait for the next notification |
| `status` shows an empty frontier and no live agent of this spec | Go to step 4 |

Then wait for the next notification. Most notifications that close a ticket are followed by another `advance`. The heartbeat from step 1 only wakes; it does not judge.

## 4. The night is over

The frontier is empty and `status` shows no live agent. Then, still on this branch:

```bash
<dispatch> reverify <spec>
<dispatch> summary <spec>
```

`reverify` re-runs every closed `ALL MET` ticket's criteria against this `HEAD`. Exit 0: all green. Exit 1: each red ticket is already reopened, labelled `needs-triage`, unassigned, and commented with the failing `AC<n>` — that is the morning's triage queue; do not close those tickets.

`summary` posts a comment on the spec whose first line is `NIGHT SUMMARY <date>`, with the four lines `Closed:`, `Handed back to needs-triage:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:`. If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended.

Delete the heartbeat from step 1 (`paseo heartbeat delete <id>`), and remove `.git/mmw-heartbeat-<spec>`.

Tell the user the night finished, and point them at that comment.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> suspend <spec>` is that decision carried out.

It archives every live worker of the batch with `paseo archive <id>`: the worker is interrupted and taken off the agent list, its reviewer and verifier with it, and the workspace and the branch stay. Then every ticket still in the agent queue gets one comment opening `NIGHT SUSPENDED #<spec>`, with the time and whether a worker was interrupted on it, and its claim is given back. Without the comment the morning reader finds a row of tickets with no verdict and no way to tell them from work in progress; without the claim given back, `advance` never takes the ticket up again. A ticket a worker handed back to triage during the night already carries its own verdict, so it is left alone.

Workspaces and branches stay, and the same batch is taken up again with `<dispatch> advance <spec>` once whatever stopped the night is fixed: each ticket is unclaimed and held by no agent, so it is on the frontier, and `start` reuses its standing workspace. That is the reason to suspend a night rather than let it run: the fix is carried on with the same worktrees, and a batch dispatched again from scratch would throw the night's work away along with the night.

The slots are given back for every ticket of the batch, handed back ones included, because the gate in `advance` counts claims rather than sessions and the next night would otherwise read the machine as fuller than it is. `lease.py` refuses a slot something still listens on and names the port and the pid; `suspend` reports that and exits 1 rather than forcing it, because taking a slot off a live process is the same act as ending it.

It then deletes the main agent's heartbeat (`paseo heartbeat delete`) when `.git/mmw-heartbeat-<spec>` names one; a night that never wrote that file has no heartbeat to delete. After that, `advance` can run again.
