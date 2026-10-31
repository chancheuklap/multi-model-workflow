# Handle independent ticket results while another worker continues

This is an acceptance design, not an executed result. The coordinator must handle each ticket result without waiting for all workers to finish. The coordinator may stay active throughout.

## Prepare the observation

Use an isolated test repository, MMW_HOME, and recorded App sessions. Use the frozen runtime selected for the run. Do not install or run the product under test as the controller of a live watch.

Prepare one watch covering independent tickets #101, #102, #103, and #104. Record coordinator C as its `codex-app` recipient. Give each ticket an existing worker W101 through W104. Record each worker identity in its ticket's `worker.started` event. No session starts during this scenario.

Keep W104 running behind a completion barrier. Allow W104 to write progress before and after each coordinator action. Release a result from W101, W102, or W103 only at the step that names that worker. Observe the tracker comments, relay queue, adapter receipts, coordinator actions, and W104's continuing progress. Record event comment IDs and relay sequence numbers rather than assuming ticket-number order.

Use the real App adapter and tool executor for transport acceptance. A fake tracker or controlled worker may supply valid result events. A fake adapter response does not prove App delivery. Record a finite timeout for each observation before running the scenario. A timeout fails acceptance rather than implying success or authorizing a worker restart.

## Exercise staggered results and a queued burst

| Observable action | Expected source records and coordinator behavior |
| --- | --- |
| C enters the shared `dispatch.sh wait-wake` operation through the calling runner's tool executor. Keep C's turn active. W104 writes progress. | The existing watch still names C. Waiting creates no replacement coordinator, worker, or watch. W104 retains its original session and worktree. |
| W101 records `ticket.passed` on #101. Keep W102, W103, and W104 unfinished. | The relay reads the valid tracker event and queues `#101 ticket.passed` to C. The row identifies #101, `ticket.passed`, `to=main`, the existing watch, and C's runner and session. The adapter's real delivery receipt precedes any claim of delivery. |
| Observe C's first wait return before allowing W102 or W103 to finish. | C receives #101's wake while W104 remains running. C reads #101's authoritative ticket result, then acknowledges `#101 ticket.passed` before long handling. C handles only the result the tracker proves. A pass wake alone does not prove landing. |
| While C handles #101, W103 records `ticket.refused`, then W102 records `ticket.returned`. Keep C active. | Both events acquire separate queue rows for C, ordered by their tracker comment IDs. Neither event overwrites #101 or merges with the other ticket. Already accepted App delivery stays delivered until acknowledged. An unsent wake stays queued for retry. |
| During the pending C results, record `reviewer.reported` on #104 after W104's `worker.started`. | The relay addresses `#104 reviewer.reported` to W104's recorded runner and session, not C. Delivery to W104 can proceed while C's recipient has pending rows. W104 consumes its reviewer result and continues its existing work. |
| C finishes its bounded handling of #101 and re-enters active wait as needed. | C receives #103's refusal and #102's return in relay sequence order. C reads each named ticket and acknowledges each wake in that order before starting long handling. Ack-through semantics must not erase an earlier unread result. Each result gets its own tracker-based disposition. |
| After all three ticket results are read and acknowledged, C waits again. Keep #104 without a terminal result and let W104 write further progress. Observe another relay cycle over the same comments. | C's three handled result rows are absent. W104's independently addressed rows are unaffected by C's acknowledgments. The repeated tracker read produces no second handling of the same comment. The watch remains open and W104 continues in its original session. |

## Return conditions

A successful wait returns an actionable existing wake for the calling recipient. It does not wait for the watched set to finish, for C to become idle, or for any worker's final chat message. Several pending wakes may require several wait calls. Preserve relay ordering and the rule that a recipient receives at most one new wake per delivery pass.

The scenario passes when C has handled the pass, refusal, and return from their tracker records, acknowledged the corresponding rows, and returned to waiting while W104 still progresses. It does not require W104 to finish or the watch to close. End observation before ordinary worker completion cleanup.

## What must not happen

- No interrupt, cancellation, archival, replacement, repeated assignment, or duplicate implementation of a continuing child occurs to make waiting return.
- C does not wait for a batch-complete signal. Independent ticket results are not a brief batch.
- C does not infer ticket success from a wake, an App receipt, an empty queue, or a completed chat turn.
- Pending results do not disappear because C is active. A delivered but unacknowledged wake does not cause repeated message injection each relay cycle.
- A refusal or return does not become a pass. Reviewer results do not go to the coordinator.
- The relay does not decide dispositions or write ticket outcomes. Shared workflow instructions do not acquire App-native tool names or parameters.

## Contract sources

[ADR 0067](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/docs/adr/0067-native-tools-stay-behind-runner-adapters.md) places native operations inside runner adapters and requires real receipts. [relay.py](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py) supplies `WAKES`, watch ownership, worker routing, recipient ordering, delivery retention, and acknowledgment semantics. The frozen dispatch skill supplies the proposed active-wait entry and read-before-ack workflow. This scenario does not establish that active waiting is already implemented.
