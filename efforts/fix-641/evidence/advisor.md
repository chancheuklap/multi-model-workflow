Recommend a GitHub-backed monitor implemented inside the existing board process, with one derived presentation model and shared refresh work. Keep relay delivery and authoritative workflow decisions independent of the board. Your overall direction is sound, but settle the night-phase evidence and refresh contract before presenting the architecture as complete.

The deciding risk is false confidence: a fast page saying “running”, “landed” or “finished” when its evidence is stale, incomplete or belongs to another run. Fewer requests are valuable only within a stated freshness and completeness contract.

1. Make the board one interpretation of evidence, not one scalar status.

Keep tracker closure, acceptance result, landing, dependency release, ownership, current phase and attention as separate facts. Derive their display together once, then let cards, counts, edges and detail consume that result. Reuse events.py's domain rules. Do not change dependency semantics to make a red edge agree cosmetically with a landed card. A genuinely reopened landed issue can require attention and block successors.

Replay phase transitions into spans and derive the current phase from the final span. Remove the separate PHASE_OF_EVENT and sticky-claim classification. Preserve events that finish a phase as boundary evidence, while opening the next span even when it has no later event. Record when a phase became evidenced, and distinguish that from actual operation start when only completion records exist. Do not infer activity or a hang from a held session or elapsed silence.

2. Include minimum phase-entry evidence in the recommended scope.

“Awaiting evidence” is necessary for historical or interrupted runs, but it cannot be the normal answer for new runs if #641 promises to show closeout, reverify and retrospective while they happen. Current spec.opened, spec.closed and spec.retroed record milestones. Ticket checks record results. Those records cannot establish every long operation's beginning.

Recommend the smallest canonical phase-entry record through the existing event mechanism, written where the operation actually begins. No heartbeat, new daemon or new command family. Exact names and transition placement belong to the subsequent design and implementation investigation. Existing completion events close spans. A failed or interrupted phase retains its last recorded state with stale or failure evidence rather than pretending it finished.

The night is not a straight progression through all-landed, closeout, reverify and retro. Run a night step 4 can create tickets and return to execution; step 5 can repair and repeat checks; summary can close a night with handed-back or blocked tickets. Model those loops and outcomes. spec.closed ends the watch before retrospective and delivery. It does not mean the entire owner-facing delivery is finished. Preserve that distinction through spec.retroed and eventual spec.merged without expanding this work into a PR dashboard.

Use the latest spec.opened comment identity as the run boundary. Do not use the current fold's historical booleans as a latest-run state. Do not discard earlier ticket evidence merely because a resumed spec has a later opening: standing ticket work can carry forward. Default selection uses the active run, preserves explicit selection, and has a stable tie-break when several nights are active. Keep the selected completed run visible. Closed-root discovery after a board restart must be specified; retaining an object only in memory does not solve that case.

3. Put refresh ownership in the existing BoardStore.

A warm page should receive the last successful board result promptly while one refresh runs. Coalesce concurrent refreshes, and reuse a sufficiently recent result across staggered tabs as well. In-flight coalescing alone does not stop two tabs whose requests never overlap from doubling GitHub traffic. Keep GitHub I/O outside the lock needed to serve a published result, then publish the completed generation together. No additional service is needed.

The visible tab requests refresh on return. Manual refresh waits for, or explicitly tracks, a refresh covering every source its promise includes. A weaker automatic refresh cannot satisfy a stronger manual request merely because it was already running. During failure or rate pause, retain the last successful content and show its age and the next eligible retry. Hidden tabs do not create routine reads.

Do not promise an atomic GitHub snapshot. Publish one internally consistent interpretation with source validation times. Tracker metadata, comments and relationships must each have a declared maximum age. A fresh comment stream with ten-minute-old blocking relationships still leaves #641 incomplete. Structure reconciliation must cover external dependency edits, not only MMW child events.

4. Recommend an incremental repository read path, conditional on one bounded proof.

The concrete candidate is repository issue metadata plus a separate repository comment update feed, backed by complete bootstrap and periodic full reconciliation of the relevant sources. Merge comments by stable identity, replace edited content, and replay the normalized complete history. Include spec comments and landed tickets. Discover new relevant issues before relying on their incremental history. Use overlap, complete pagination and cursors advanced only after successful ingestion. Reconciliation handles deletion and coverage gaps. Manual refresh performs the promised full revalidation.

This is a candidate to replace routine per-ticket scans, not an extra permanent layer alongside them. Do not use issue updated_at as the sole comment-change detector, and do not treat relay's delta output as full history. The documented repository comment endpoint supports updated-time filtering and sorting; it is not a deletion log. See GitHub's [comment API](https://docs.github.com/en/rest/issues/comments#list-issue-comments-for-a-repository).

The fact that decides transport is measured workload: relevant ticket count and history size, unrelated repository comment traffic, reconciliation cost, and achieved freshness. Compare the candidate against corrected per-issue conditional reads under the same workload and correctness requirements. If repository-wide traffic costs more or cannot meet the agreed age bounds, retain the corrected per-issue reader. Do not ship an automatic policy selector or both permanent mechanisms merely to avoid this decision. No current measurements establish the winner.

5. Make MMW-wide API scope concrete without making the board an authority.

Remove duplicate reads within status and summary invocations, beginning with print_summary reading tickets that batch_children reads again. Reuse complete results only within a defined operation and invalidate or re-read after writes that affect its decision. Extend existing read helpers for complete pagination, conditional validation and rate-limit errors; adopt them at the actual repeated read paths. Preserve fresh evidence before claims, routing and landing.

Relay keeps ownership of wake delivery, deduplication and restart recovery. Reusing read code is justified; making relay depend on an open board or sharing a mutable cross-process cache is not yet justified. Multiple repositories can share authentication limits. Propagate server-directed pauses to the actual callers, including manual refresh, instead of creating a global quota service. Authenticated 304 responses avoid primary quota but still involve a request. GitHub recommends serial requests and obeying rate-limit response headers. See [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api).

6. Present the complete plan in this order.

On the requested single page, draw the current and proposed whole flow side by side. Include ordinary ticket work, the return from closing findings to more work, reverify and recovery, watch closure, retrospective and owner acceptance. Beneath that flow show how GitHub evidence reaches one board representation, with relay and commands alongside it. This prevents the API optimization from displacing the owner's monitoring objective again.

State proposed freshness, warm-page response and manual-refresh targets as product targets, not measured facts. Choose the targets before comparing transports. Validate the full flow, multi-tab traffic, restart discovery, same-second edits, pagination changes, deletions and rate pauses. Report page responsiveness, evidence age and API cost separately. Do not spend the first optimization effort on rendering based on historical timings.

Then obtain the required UI acceptance, settle transport using the bounded comparison, prepare the executable specification and verification, and implement the complete scope. Verify the October prerequisite's release and accepted-night status before implementation; a changed source layout is not proof that the prerequisite was accepted. Keep the installed runtime frozen throughout any watch. This advisory task authorizes no installation, tracker change or release.

Evidence checked directly: #641 and its October 1 decision; current board_data.py, board-feed.mjs and board-logic.mjs; ghlist.py; Run a night; the relevant event schema and fold transitions; relay's comment reader; status.py's batch_children and print_summary. The existing evidence report supplies broader call-path context. I did not benchmark or reproduce the running UI, and make no measured performance claim.

## For the owner

建议把这次工作定为“能从开夜一直看到交付的实时任务板”，并把读取提速和减少 GitHub 请求一起完成。页面会明确区分当前阶段、最近记录和数据是否过期。下一步先看同一页上的现状与完整方案；任务板新增显示仍由你验收，发布也仍由你决定。

## Problems

None
