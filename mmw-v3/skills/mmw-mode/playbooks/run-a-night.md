### Run a night

**You own one night: a spec's published tickets, from `open` to `finish`, as their orchestrator; every worker is dispatched from here.** The scripts merge, archive, create worktrees and start the sessions; every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again. The owner's acceptance in the morning comes back to this session, which runs `finish`. Distinct from Run one ticket, which runs one ticket outside any night.

Commands of the `dispatch` skill's `dispatch.sh` and the `verify-ticket` skill's `verify-ticket.py` are named bare below. Between the steps you end your turn. The relay that `open` starts wakes you when a ticket of the batch gets an event that needs you (step 5), and the watchdog tells you when the tracker has gone silent where it should not; nothing else does, and no agent polls another.

<!--
Shell. The stance for the whole night comes here: who reads the night in the morning and
where each decision leaves its reason, and why a ticket handed back beats one closed under
a loosened criterion. Source in MMW v2 at 9df1ab67d:
mmw-v2/skills/dispatch/references/night.md, its opening paragraphs. A lesson on how the
orchestrator works writes it.
-->

1. **Find your step.** Run `dispatch.sh status <spec>` and read the spec's own events; take the first row whose fact holds.

   | The fact | Go to |
   | --- | --- |
   | The owner has said the night starts, and the spec carries no `spec.opened` | step 2 |
   | The spec's newest night event is `spec.suspended`, or the fault is in the pipeline and the night must stop | step 6 |
   | A wake arrived: `#<n> <event>`, `relay.recovered since <time>`, a line of `watchdog:` alerts, or `MMW turn guard:` | step 5 |
   | `status` shows an empty frontier and no live agent, and the spec carries no `spec.closed` | the closing pass, below |
   | The spec carries `spec.closed` | the end of the night, below |

   Done when you are at the step the first matching row names.
2. **Check and open.** From a checkout on the night's base branch, run `dispatch.sh check <spec>`. Exit 2: fix every condition stderr names and run it again; report an invalid agent row to the owner. Exit 0: from this session, the one the night's wakes must reach, run `dispatch.sh open <spec>`. Exit 0 prints `opened #<spec>: wake-ups go to <runner> session <session>`, and this session is the night's orchestrator; when the line goes on to name a task board, hand its URL to the owner. Exit 2: fix the condition stderr names and run `open` again.
   Done when `open` exited 0.

<!--
Shell. Linting the batch before the first `advance` comes here, by the `verify-ticket`
skill's `references/linting.md`. Source in MMW v2 at 9df1ab67d: night.md `## 1b. Before
the batch: what the batch cannot be run on`. A lesson on how the orchestrator works
writes it.
-->

3. **Advance.** Run `dispatch.sh advance <spec>`. It lands every passed ticket and starts a worker on every ticket the frontier frees; after `open` it may run from any checkout of this repository. Exit 0: end your turn. Exit 4: a runner refused a start; stderr names each refusal and none is retried; fix what each names and run `advance` again, and end your turn only while another worker of the night is live; when none is, tell the owner which tickets were refused and why. Exit 2: fix what stderr names and run `advance` again (a night that is not open: `open <spec>` first); the rest of the batch was landed and started.
   Done when `advance` exited 0 and your turn has ended, or the owner has heard which tickets were refused.
4. **Keep each worker on its ticket.** While a worker holds a ticket, its code is the worker's: you change what it works from (the spec, the ticket body, a criterion, a baseline) and tell it through `dispatch.sh resume <n> "<what you settled, then: continue>"`, never its worktree or branch. Exit 3 from `resume`: word the next `resume` so a worker that receives both reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`.
   Done when every instruction you gave a worker went through `resume`.
5. **Each time something wakes you,** one wake at a time (two tickets landing seconds apart are two wakes, and the second comes after you end your turn): do the `dispatch` skill's `## On waking`, run `dispatch.sh status <spec>` (exit 2: the tracker did not return the whole batch; run it again when it answers), act on every row the table below matches, not only the ticket the wake named, then run step 3's `advance` once. When that `advance` left the frontier empty and no agent live (read `status` again), go to the closing pass; otherwise end your turn.

   | What you see | What you do |
   | --- | --- |
   | `#<n> ticket.passed`, or a `ready` frontier row | The `advance` handles it |
   | A live worker should continue | `dispatch.sh resume <n> "<what you settled, then: continue>"`, as step 4 says |
   | `#<n> child.opened` of kind `fault` | Read the `verify-ticket` skill's `events.py fold <n>`. A `fault` in this repository's environment (a credential, a service, `.mmw/target.json`) you fix, then `resume` the worker. A `fault` in the pipeline's own scripts you do not patch while they run the night: tell the owner what failed, and suspend (step 6) when the rest of the batch would hit it too |
   | `#<n> child.opened` of kind `contract` | Settle it as **Settling a contract child** below says |
   | `#<n> child.opened` of kind `decision` | Nothing; the worker took the default |
   | `#<n> ticket.returned` | Leave its workspace for triage; the `advance` continues the batch |
   | The `advance` summary has `bounced` | After the second bounce the ticket stays in `needs-triage` |
   | `#<n> ticket.refused` | Fix what the event's `reason` names; the `advance` starts it again when the frontier permits |
   | `#<n> worker.lost` | The `advance` gives back the claim and starts another worker in the standing workspace |
   | `relay.recovered since <time>` | Nothing; later wakes carry the recovered events |
   | A worker whose session is gone while its worktree, slot or claim still stand (`advance` says "if the worker … is gone, retract it") | `dispatch.sh retract <n>`; a `0` on its summary line is something it could not release, and the line above says why. The `advance` starts the replacement |
   | `watchdog: #<n> silent since …` | When `events.py fold <n>` lists an open `contract` child, the worker is waiting on you; settle that child first |
   | Any other live worker | Nothing; its result wakes you or its worker |
   | The ticket needs the other worker grade | Give it exactly one of the `junior-worker` / `senior-worker` labels; the next `start` reads it |

   Done when the wake is acked, every matching row is acted on, and `advance` ran once.
6. **Suspend the night** when the fault is in the pipeline rather than in a ticket: workers left running against it produce failures that say nothing about the work. Run `dispatch.sh suspend <spec>`. A suspended night wakes nobody: its watch is closed, and its workspaces, branches and pushed commits stay for `open` and `advance` to take up once the fault is fixed. Exit 1: stderr names, one line each, what was left; for a slot a process still listens on (the `ui-acceptance` skill's `lease.py` names the port and the pid), stop that process where it was started and run `lease.py release <its worktree>`, and tell the owner every other line. Exit 2: nothing was touched; fix what stderr names and run `suspend` again.
   Done when `suspend` exits 0, or exits 1 and the owner has heard each line stderr left.

**Settling a contract child.**

<!--
Shell. How a `contract` child is settled comes here: the authority order, fixing the
source and every unlanded derived ticket, `dispatch.sh route <n> <child> fixed`, resuming
the worker, and leaving the choice to the owner when no authority settles it, including a
child naming a Claude Design page. Source in MMW v2 at 9df1ab67d: night.md `## 3. Each
time something wakes you`, the two `contract` rows and the three paragraphs after the
table. A lesson on how the orchestrator works writes it.
-->

**The closing pass and the end of the night.**

<!--
Shell. Routing every open finding, closing the spec's Memory records, `reverify`,
`summary`, the `retro` skill, and `finish` once the owner has accepted the result come
here. Source in MMW v2 at 9df1ab67d: night.md `## 4. The closing pass`, `## 5. The night
is over` and `## 6. Merge the accepted night`. A lesson on how the orchestrator works
writes them.
-->

**Reply:** <!-- Shell: what the owner reads in the morning, from night.md `## 5`. -->
