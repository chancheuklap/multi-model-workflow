# Codex App live workflow acceptance

Candidate: `5e621872d6ad87a8375581bd0065c5f99f174a7f`.

The owner requested a demonstration in the actual MMW repository, without installing the candidate. The coordinating chat used a frozen copy of the candidate scripts and an isolated MMW_HOME. No installed skills, hooks, live model configuration or installed checkout were changed.

## Actual workflow

The original coordinating chat ran `dispatch.sh send worker` for three independent tickets. Each worker ran the unchanged Work a ticket playbook, committed only its identity evidence and used `dispatch.sh send reviewer`. Each independent reviewer shared its worker's ticket worktree, ran the four review axes and posted reviewer.reported. The existing relay queued that report to the worker; a new worker turn consumed it and closed the ticket through verify-ticket.

| Ticket | Worker chat | Reviewer chat | Branch | Result |
|---|---|---|---|---|
| [#1471](https://github.com/chancheuklap/multi-model-workflow/issues/1471#issuecomment-6539977077) | `01a19093-aac0-7b42-8e55-5c75fc742870` | `01a19097-11d8-7cd0-8d8f-96e3de52bc58` | `issue-1471` | CLOSED, ticket.passed |
| [#1472](https://github.com/chancheuklap/multi-model-workflow/issues/1472#issuecomment-6539989448) | `01a19094-1270-7141-84f2-867fa0f0615f` | `01a19097-ccdc-73a3-9346-5d15366ea3d3` | `issue-1472` | CLOSED, ticket.passed |
| [#1473](https://github.com/chancheuklap/multi-model-workflow/issues/1473#issuecomment-6539967207) | `01a19094-851e-7800-a91c-e3691d76ac5d` | `01a19096-5608-7e10-aef9-5a1735bf088d` | `issue-1473` | CLOSED, ticket.passed |

Each ticket worktree is `/Users/cheuklapchan/multi-model-workflow/.worktrees/issue-<ticket>`. The worker and reviewer identities are distinct; all three ticket worktrees and branches are distinct. The six chats remain visible in the Codex sidebar section `MMW 正式演示 · Workers 与 Reviewers`.

## Notification evidence

While the coordinating turn remained active, notifications accumulated in the App's pending-message queue. Reading another chat's status did not consume those notifications. After the coordinating turn ended, this chat received `#1471 child.opened` in a new App turn. That child had already been resolved, so the wake required no repeated work. The relay log separately records reviewer.reported delivery to each worker and ticket.passed delivery to the coordinating chat.

The first two workers found a missing closing quote in their ticket CHECK. The coordinator corrected the ticket source, resolved contract children #1474 and #1475 through dispatch route, and resumed the same workers. Neither the frozen runtime nor the workers' identities were replaced.

## Checks and limits

- `CHECK PASS default: 10 steps in 450s` on the candidate runtime code.
- App adapter unit suite: 15 tests passed. The codexappdispatch isolated integration scenario passed.
- Real App: three worker starts, three worker-dispatched independent reviewer starts, reviewer reports, worker automatic continuation and three ticket.passed closeouts.
- All files in the frozen runtime matched its recorded hashes after the run.
- The review reports cover the workers' identity evidence, not an independent review of all adapter source.
- No candidate installation, promotion to dev/main or release. Installed App hooks and App restart recovery were not accepted by this demonstration.
- Chats, worktrees and ticket branches remain available for inspection; evidence tasks were not landed into the product branch.

The frozen runtime was `/tmp/mmw-app-demo-20261031-1540/toolbox/mmw-v4`; its isolated coordination home was `/tmp/mmw-app-demo-20261031-1540/home`. Local raw evidence is in that run's `evidence/`, including the tracker responses and formal-acceptance.json.

## Full brief-role run and waiting behavior

The later frozen run used `/tmp/mmw-app-final-20261031/runtime/mmw-v4` and its own `/tmp/mmw-app-final-20261031/home`. The current coordinating chat remained the parent. Six independent App chats received assignments through the normal `dispatch.sh send` commands: two researchers, one advisor, two candidates, and one retro-analyst. They changed no product code. The researchers' persisted findings are under `efforts/fix-1464/research/1470-app-role-acceptance/`; the role-return evidence and acceptance designs are in [roles](roles/).

The two researchers reported at 07:08:44 and 07:09:08 UTC. The relay recorded one completion wake at 07:09:37 UTC. After the coordinator ended its turn, the App started parent turn `01a190cb-617c-7eb1-8902-690a1575db3b` with `brief 20261031-070807-aa6d done`. The parent read both answers before acknowledging the batch. [Parent-return evidence](roles/parent-return.json) records the report times, single wake, and new parent turn.

The coordinator also received the candidate, retro-analyst, and advisor batch notices through the adapter-owned native waiting path while its turn was active. It read their complete answers before acknowledging. The candidate artifacts are proposed acceptance scenarios, not evidence that those scenarios executed. The two paths preserve the same brief-batch completion and acknowledgment protocol. Ending the turn and receiving a background wake remains preferred; native active waiting is an allowed alternative rather than a replacement for that path.

The advisor's first report omitted the isolated `MMW_HOME` and therefore looked in the wrong state directory. The same chat submitted its existing answer successfully after receiving the exact command with the correct environment; it did not repeat its investigation. The generated brief footer now includes `MMW_HOME` directly in its report command. The `briefreport` regression executes that generated command with an unrelated inherited home: it failed before the correction and passed afterwards.

After the six chats had completed their turns, the parent closed all four batches through the frozen runtime. Native archival and subsequent state inspection confirmed that all six sessions stopped. The final watch table and MMW wake queue were empty. [Closeout evidence](roles/closeout.json) and [command receipts](roles/close-results.json) retain those results. The runtime's recorded source hashes remained unchanged throughout the run.

## Task-board runner and model selection

The current checkout's task-board server ran in an isolated `MMW_HOME` on a temporary port. Selecting `codex-app` changed all seven session-role hosts to Codex and restricted their host/model choices accordingly. The subagent and model-catalog tabs showed only supported hosts, preserving the hidden Claude subagent settings for a runner that supports them. A compatible model and effort survive the switch; incompatible choices are reconciled after the new catalog arrives.

The coordinator selected `gpt 6 luna`, `high` for advisor in the actual settings UI, saved, closed the dialog, and reopened it. The saved choices remained. That isolated configuration was then used by the formal advisor dispatch. The App-owned archived turn contexts independently record `gpt-6-luna` with `high` in both advisor turns, as retained in [actual model evidence](roles/advisor-model.json). The local browser used a stored host-catalog fixture; the subsequent independent App chat is the actual runner-start evidence. [Subagent settings screenshot](roles/codex-subagents.png) records the rendered page.

## Management coverage and limits

The App dispatch integration fixture now also exercises resuming the recorded App worker after the configured default changes to Paseo, without starting a replacement chat. It merges a passing worker commit, preserves the ticket worktree and branch when native stop fails, then confirms stop and removes the owned worktree and branch on retry. This is isolated integration evidence with fake runner receipts and tracker data, not a live App landing run. Shared suspend, finish, and cleanup behavior remains covered by the existing dispatch suite.

Native foreground stop rechecks the App even when a previous observation says stopped. A stopped observation alone cannot authorize foreground cleanup after a chat has been reopened. Background observations still distinguish unknown state from confirmed stop.

No candidate installation, hook-trust change, promotion, or release was performed. Candidate hook wiring and payload handling are covered by isolated checks; the new hooks were not deployed into the running desktop App. This run manually invoked the frozen turn guard to arm its existing watchdog. It does not count as a real installed Stop-hook acceptance. No automatic coordinator-host crash resurrection or exactly-once transport guarantee is claimed. Ticket events, brief reports, and read-before-ACK remain authoritative.

## Final candidate checks

`scripts/check` passed the default tier's ten steps on the final runtime changes, including board, dispatch, installer, liveness and relay suites. The App adapter suite passed 18 cases. The targeted `briefreport`, `sendbrief`, `sendinto`, and extended `codexappdispatch` integration scenarios also passed. Source wiring and host-neutrality checks passed. Windows-only PowerShell checks were not run on macOS.

The role-return reports and candidate acceptance designs do not imply an extra implementation delegation. All product changes and the final evidence synthesis were performed by the original coordinator.
