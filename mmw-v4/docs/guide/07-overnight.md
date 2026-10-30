# Run work while you sleep

A night runs a spec's published tickets while nobody watches. One session, the orchestrator, sends a worker to each ticket that is ready, lands each ticket that passes, fixes or files what the reviewers found, and delivers the whole batch as one pull request. You read that pull request in the morning, with none of the night's context.

The playbook is [Run a night](../../skills/mmw-mode/playbooks/run-a-night.md). A day ticket takes the shorter path of the [One ticket](../../skills/mmw-mode/playbooks/one-ticket.md) playbook. Every command below is the `dispatch` skill's `scripts/dispatch.sh` ([dispatch](../../skills/dispatch/SKILL.md)), unless it names the `verify-ticket` skill ([verify-ticket](../../skills/verify-ticket/SKILL.md)).


## What a night needs before it starts

A night runs only on work that is already decided. The planning playbooks produce it:

1. Grill with docs, or a wayfinder map (Chart the map, then Work through the map), settles the decisions.
2. To spec records them in a spec, published as a GitHub issue.
3. To tickets cuts the spec into tickets with acceptance criteria and blocking edges, published as sub-issues of the spec.

Each acceptance criterion carries a `CHECK:` command and the output it must show under `EXPECT:`. That pair is what lets a worker prove its ticket without you, so a criterion that cannot fail proves nothing. Before the first worker starts, the night lints every ticket for what the batch cannot be run on.

The night's base branch is cut from a project branch. A night never lands on the repository's default branch; merging the project branch into the default branch stays your release decision.

## Who does the work

The orchestrator is the session you tell that the night starts. It decides; the scripts merge, archive, create worktrees and start sessions. Every decision it makes leaves its reason on the ticket, the child issue or the spec, where the morning reader looks.

The dispatched roles are the rows of [`roles.json`](../../skills/dispatch/roles.json):

| Role | Sent with | What it does |
| --- | --- | --- |
| `junior-worker` | a ticket | Works one ticket to closed: writes the code, runs the criteria, starts its reviewer |
| `senior-worker` | a ticket | The worker of a ticket labelled `senior-worker` |
| `reviewer` | a ticket | Reviews one ticket's diff on the four axes of the `code-review` skill |
| `researcher` | a brief | Reads one source or angle and hands back cited findings |
| `candidate` | a brief | Designs one of several candidate answers to the same brief |
| `advisor` | a brief | Gives a second opinion on one decision |

Each role's host, model and reasoning effort is a row of `~/.mmw/models.json`. Change a row with `python3 mmw-v4/skills/dispatch/scripts/models.py config set <role> <host> <model> <level>`; [editing-models.md](../../skills/dispatch/references/editing-models.md) has the details and the runner choice.

A worker follows the Work a ticket playbook ([work-a-ticket.md](../../skills/mmw-mode/playbooks/work-a-ticket.md)). It claims the ticket, writes the code test-first, merges the base branch in, runs every criterion, posts its decisions, sends a reviewer, fixes what the review found inside the ticket, runs the criteria a final time and closes the ticket with `verify-ticket.py --closeout`. It asks nobody: a question only you can answer becomes a child issue of the ticket, and the worker takes a written default and carries on. A worker never opens a pull request; the orchestrator lands its ticket.

## How the orchestrator is woken

Between steps the orchestrator ends its turn. Nothing polls. Three processes bring it back:

- **The relay** (`relay.py`) watches the tracker. When a watched ticket gets an event that needs someone, it wakes the waiting session through its runner. `ticket.passed`, `ticket.returned`, `ticket.refused`, `worker.lost`, and a `child.opened` of kind `contract`, `fault` or `decision` wake the orchestrator. `reviewer.reported` and `reviewer.lost` wake the ticket's worker. The relay never writes to GitHub and decides nothing.
- **The watchdog** (`watchdog.py`) notices silence. A worker that dies writes nothing, and on the tracker that looks like work in progress. The watchdog asks the runner whether a silent ticket's worker is still there, and sends a `watchdog:` line when it is not.
- **The turn guard** (`turn-guard.py`) is a hook on every turn end. It re-arms the watchdog when a watch is open and the watchdog has stopped.

A woken session first follows the dispatch skill's `## On waking`: it reads what the wake names on the ticket, then acknowledges it with `dispatch.sh ack <n> <event>`, so the relay stops sending the same wake.

## The night, step by step

The orchestrator finds its place from the record, not from memory: the first row of the playbook's table whose fact holds on the tracker says which step comes next.

1. **`check` and `open`.** `dispatch.sh check <spec>` confirms the machine is ready; what `install.sh --check` finds it shows as a warning the night does not wait on. `dispatch.sh open <spec>` opens the night's watch on the relay and makes this session the orchestrator.
2. **Lint the batch.** `verify-ticket.py <spec> --lint` reports every ticket the night cannot run on. Each `ERROR` is fixed on its ticket before any worker starts.
3. **`advance`.** `dispatch.sh advance <spec>` lands every passed ticket, deletes its local and origin ticket branch copies when cleanup permits it, and starts a worker on each ticket whose blockers are cleared, up to `max_workers` tickets held at once (3 unless `~/.mmw/models.json` sets it); it names each ticket left waiting for room. The orchestrator then ends its turn.
4. **Each wake.** The orchestrator runs `dispatch.sh status <spec>`, handles every row the table matches, then runs `advance` once. It can tell a live worker to continue with `dispatch.sh resume <n> "<text>"`, release a worker whose session is gone with `dispatch.sh retract <n>`, fix a `fault` in this repository's environment, or settle a `contract` child by the authority order the playbook gives: decision tickets and ADRs, then the spec, then the winner prototype, then domain documents, then the ticket body. A correction no written authority settles goes back to you. The worker hands back the ticket already being worked, and it moves to `needs-triage` along with the not-yet-started tickets that depend on the correction.
5. **The closing pass.** When no ticket is left to start and no agent is live, `dispatch.sh findings <spec>` lists the open findings the reviewers filed. Each one leaves through `dispatch.sh route`: `fixed`, `stale invalid`, `stale fixed-elsewhere`, or `became-ticket`. The default is to fix it on the night's branch; it becomes a ticket only when another open ticket owns its files, when it shows a gap in the criteria, or when the fix couples two or more files by design.
6. **`reverify` and `summary`.** `dispatch.sh reverify <spec>` runs every landed ticket's criteria again on the base branch and reopens any that went red. `dispatch.sh summary <spec>` posts the `NIGHT SUMMARY` on the spec and closes the watch.
7. **The pull request.** The orchestrator opens one pull request from the night's branch to the project branch, titled `Night #<spec>: <the spec's title>`. Its first line opens your visual page, with decisions and recommendations, before and after, affected product parts, evidence, unfinished work, retrospective counts and links. The body is a short record with ticket verdicts and evidence links, check summaries and the verbatim `NIGHT SUMMARY`.
8. **`finish`.** Only after you accept the pull request, `dispatch.sh finish <spec>` merges it into the project branch and closes the spec issue as completed. It retains the local night branch and removes its origin copy when cleanup permits it. It creates or fast-forwards the local project branch to the fetched origin tip, including in a clean project worktree. Uncommitted changes or local commits outside origin leave the project branch unchanged, with the reason on stderr. A worktree on the night branch and its branch stay unchanged; stderr gives a removal command for a linked worktree or a detach command for the main worktree, for after the session ends. If cleanup or closing the spec fails, `finish` exits 2 and leaves the spec open. Run `finish` again to complete cleanup and close the spec without merging again. It refuses while a check is red or still running, or while a review thread is open; the orchestrator settles each and runs `finish` again.

A ticket handed back to triage with its reason, or one waiting on your decision, is a valid outcome of the night. A criterion loosened to make a ticket close is a defect, because it lands broken behaviour under a green mark.

### Suspending a night

When the fault is in the pipeline rather than in a ticket, workers left running only produce failures that say nothing about the work. `dispatch.sh suspend <spec>` stops the night: it closes the watch and leaves the workspaces, branches and pushed commits in place. Once the cause is fixed, `dispatch.sh open <spec>` and then `dispatch.sh advance <spec>` take the same batch up again.

## One ticket: a day ticket

Every change outside a night is one ticket. The playbook of its kind opens the ticket and its `fix-<n>`, writes the plan into it and hands it back to you; on your go, [One ticket](../../skills/mmw-mode/playbooks/one-ticket.md) runs. There is no spec and no batch, so no `advance` ever collects the ticket.

1. The ticket gets `ready-for-agent` and a worker label, and passes `verify-ticket.py --lint`.
2. `dispatch.sh send worker <n>`, run from `fix-<n>`, starts the worker and makes this session the ticket's orchestrator.
3. Each wake is read, acknowledged and acted on, and the session tells you what happened, because you are there.
4. Once the ticket passes, the session checks it the way the playbook that wrote it says, such as the original reproduction for a bug.
5. It merges the latest project branch into `fix-<n>` and runs `dispatch.sh land <n>`. A ticket that cannot merge goes to `needs-triage` and is sent again from step 1 when you pick it.
6. It runs [Opening a PR](../../skills/mmw-mode/playbooks/opening-a-pr.md): one pull request from `fix-<n>` to the project branch, merged with `gh pr merge` when you say yes.

## What to say

To start a night, name the spec and say it starts:

```text
the tickets of spec #212 are published and linted. run the night on them. i'm going to bed.
```

"I'm going to bed" is a session override in the mode's `## Autonomy`: the session keeps going and asks nothing it can decide itself. The pull request link is what you get in the morning.

To stop a night on purpose:

```text
the relay keeps failing on every wake. suspend the night on #212.
```

**Pitfall:** a night is not a way to make decisions. A spec with open questions produces tickets whose workers each guess the answer differently. Settle the decisions first with Grill with docs or a wayfinder map, then publish.

Next: [Shared principles and automatic loading](./08-principles.md).
