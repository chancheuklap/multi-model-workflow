# Two researcher reports produce one wake for an active App parent

This acceptance scenario protects batch completion through the App adapter. Researcher A reports first. Researcher B continues working. The active parent receives one batch wake after both reports exist and then reads both answers.

## Setup and evidence

Use a fresh isolated test home, a test repository, and the frozen runtime chosen before the run. Exercise the actual App adapter and its tool executor. Do not run repository-local changed scripts to control an existing watch.

Start one parent App chat P and one researcher batch B containing exactly two independent chats, A and B2. Use the normal dispatch path when executing this scenario. Give each researcher a distinct answer marker. Arrange an observable hold in researcher B2's assignment so A can report while B2 remains at work. Release the hold through the agreed test input, without messaging B2 to change its task or interrupting its turn.

Record the following evidence before cleanup. Let S name the test repository's state directory beneath the isolated MMW_HOME.

- The native start receipts identify P, A, and B2 as distinct chats. Record their original identities throughout the scenario.
- `S/briefs/B/batch.json` identifies the researcher role, count 2, and parent runner `codex-app` and session P. Each child's `started.json` identifies its original chat.
- `S/watches.json` contains `briefs:B` addressed to `codex-app` and P.
- Retain timestamped snapshots of child result records, `S/queue.jsonl`, `S/queue.seq`, `S/briefs/B/woken.json`, and relay cycle evidence in `beat.json` and `relay.log`.
- Retain the parent's active-wait invocation, return receipt, and continuation transcript. Adapter receipts must identify the recipient and wake text. A status observation alone does not prove delivery.

## Exercise the batch

1. In P, invoke `dispatch.sh wait-wake` through the runtime's tool executor while the parent turn is active. Record that the invocation is outstanding before either report. Neither child is stopped or restarted to make the parent idle.
2. Allow A to report through `dispatch.sh report`. Observe `S/briefs/B/1/result.md` with A's marker and its subsequent `reported.json`. Confirm that B2 has neither `reported.json` nor `lost.json` and retains its original chat identity.
3. Keep B2's hold in place until the relay has completed at least two cycles after A's report. Use cycle timestamps and logs rather than a fixed sleep as the evidence of this interval. Across both cycles, the parent wait has no batch-completion return. There is no `brief.done` queue row for B, no `woken.json` for B, and no native delivery of `brief B done` to P.
4. Release B2's hold. Allow B2 to report through its original session. Observe `S/briefs/B/2/result.md` with B2's marker and its subsequent `reported.json`. Both answers now exist before the relay qualifies B as complete.
5. Observe the relay's next successful processing of B. Exactly one queue row for B has event `brief.done`, batch B, ticket null, destination `main`, watch `briefs:B`, runner `codex-app`, and session P. The relay creates `woken.json`. The wake text is exactly `brief B done`.
6. Let the active-wait call return through the adapter. Require a receipt for B's existing relay notification to P. The parent continues in its existing chat, reads `brief show B`, and opens both result files. Confirm both distinct answer markers in the evidence. A generic host notification or a queued-message receipt without the parent's return is insufficient.
7. After reading both answers, have P acknowledge `ack brief B` through dispatch. Confirm removal of B's row. Preserve the batch and observe at least two further relay cycles. The same batch creates no second queue row or parent completion wake. Only then close B and clean up resources owned by this test.

## Return and failure conditions

The batch-completion return is permitted only after both `reported.json` records exist and the relay has produced B's single wake. Queue acceptance, delivery, parent receipt, answer reading, and acknowledgement are separate observations. A delivered queue row remains until acknowledgement, so its continued presence before acknowledgement is expected.

Use a declared execution deadline for the test. If a bounded wait returns before B is complete, its return must identify timeout or a diagnostic, never batch completion. Continue waiting through the supported path without restarting children. If no batch wake reaches the active parent by the deadline after B2's report, fail with the queue, delivery, and wait receipts. Do not make the test pass by ending the parent turn, sending a manual wake, or guessing completion from child status.

Fail for a wake after only A's report, two per-child wakes, duplicate batch wakes, an incorrect recipient, missing answer markers, premature acknowledgement or cleanup, or any stopped, interrupted, replaced, or repeated child assignment. This scenario covers two successful reports. It does not prove the separate lost-child completion path.
