Question: Trace GitHub reads outside the board, their overlap, costs and reuse opportunities.

### Components Found
- `/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/ghlist.py:88`: ConditionalListReader caches REST list pages and validators per exact address in one process.
- `/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py:479`: Board wraps comment reads and paginated sub-issue reads. Relay polls watches and tracks event marks.
- `/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/verify-ticket/scripts/issue_tree.py:245`: read gets a complete bounded sub-issue tree by GraphQL, including labels and blockers.
- `/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/verify-ticket/scripts/events.py:865`: read_comments loads issue comments or consumes an already fetched list; fold computes event state.
- `/Users/cheuklapchan/.codex/worktrees/c66b/multi-model-workflow/mmw-v4/skills/dispatch/scripts/status.py:96`: status gets tree plus individual issue views for fields and event folds.

### Flow
1. Relay creates one Board and reader per repository process (relay.py:1424-1440); each poll resolves each spec watch via unconditional paginated REST sub-issues, deduplicates ticket numbers, then reads each watched ticket's comments (relay.py:950-992, 507-513). Brief watches cause no tracker read (relay.py:60-62, 955-957).
2. On first successful read or restart it reads full comments; later it uses the latest updated timestamp minus two minutes, and deduplicates event IDs (relay.py:64-73, 985-1021). When the since URL changes, Board discards the old address cache (relay.py:493-503). Consequently a change generally causes a new unconditional read after the mark changes, then stable URL pages become conditional. Empty marks continue to use the full URL. This is a logical sequence, not a measurement.
3. Reader requests each page, following Link; 304 reuses body and stored next link. A cached last page exactly 100 entries is fetched unconditionally so an appended next page is discoverable even if the body ETag has not changed. Missing cache on 304, malformed JSON, bad status, command failure and 120 second aggregate timeout fail the read. Cached addresses are in memory; clone deep copies; discard removes an address (ghlist.py:88-176). The read counters count 200 and 304, not a complete account of all attempted calls or actual server charges.
4. A failed relay ticket read retains the prior mark and makes the cycle unsuccessful; it retries next cycle (relay.py:1120-1140). The main loop sleeps after a cycle, so 30 seconds is a minimum wait plus work time, not a fixed 30-second cadence (relay.py:1445-1453). No explicit rate-limit backoff is visible in these paths.
5. For S spec watches and unique watched tickets i with P_i comment pages, a stable poll makes sum(P_i) comment HTTP requests plus sum(Q_j) spec sub-issue pages; Q_j is the number returned by gh pagination. Stable conditional pages may produce 304; a full terminal page is unconditional. Newly changed marks, first reads and missing ETags can produce 200s and altered page counts. Counts do not include other actions or retries by gh. At most the nominal cadence is 120 cycles/hour at the 30 second default; duration reduces this. Source-derived, not measured.
6. issue_tree.read computes max query cost and for cost >10 makes a sizing GraphQL query before a sized tree query. If counts changed and the tree comes back short, it retries at maximum pages; still-short lists fail rather than silently truncate (issue_tree.py:145-156, 203-215, 245-263). Structural pages cap at 50 specs, 100 tickets, 50 children, metadata at 10; over-cap structure fails rather than paginates (issue_tree.py:25-35, 50-60). The maximum map cost model in the code is 152 points; this is not a measured current charge. GraphQL points and REST requests are distinct measures.
7. status summary reads the tree once, then reads each ticket; batch_children receives the same tree but reads every ticket again, plus each distinct child (status.py:842-883). Thus for N distinct tickets and C distinct discovered children, print_summary invokes 2N+C gh issue views and one tree.read, which may issue one, two, or three GraphQL calls depending on sizing and retry. This is a directly observable redundant read; reuse the first ticket map if freshness requirements permit. Other status invocations must be assessed independently.
8. events.read_comments runs gh issue view unless a caller passes comments-file; passing already-fetched comments is an existing way to avoid repeated fetches (events.py:865-886). verify-ticket separately fetches comments for its decision paths (verify-ticket.py:172-182). Different processes do not share the relay reader, so board, relay and status can read the same issue independently. Their different purposes and freshness requirements do not establish that a read can safely be removed.

### Files Read
Relevant portions of relay.py, status.py, events.py, verify-ticket.py; complete ghlist.py and issue_tree.py. Paths above identify their directories. Also searched mmw-v4/skills for nested AGENTS.md and found none.

### Boundaries
Each relay is isolated by repository state and process; REST list addresses include repository, issue, query and page. Code does not establish that rate budgets are per repository: gh authenticates using its configured identity, and repositories using the same identity may share an upstream budget. Exact account, credential scope, GitHub's current quota rules and actual budgets were not inspected. No token was inspected. Source code alone cannot prove effective server billing.

### Non-Obvious Things
- Reusing ConditionalListReader is already supported and avoids rebuilding pagination and validation. Board already imports it, per `mmw-v4/board/AGENTS.md:7`; investigate board's existing lifetime and cache behavior before proposing another cache.
- The relay's exact-URL cache is independent from the board's and cannot be assumed a complete issue snapshot: after reconciliation it requests only comments since a moving mark. Sharing that delta as an entire issue history would lose events.
- Reusing ticket views inside the status summary is a concrete candidate to remove duplicate work. Changing relay polling or sharing snapshots across processes requires proving freshness and event recovery, including restarts and concurrent changes. Treating successful reads as proof a tracker write completed is invalid: write correctness and idempotence need their own evidence.
- Failure handling differs: ghlist and tree raise on invalid response; status gh_json falls back to an empty object but normalise_ticket marks unread_raw (status.py:65-75, 145-147). Exact downstream treatment of every failure was not fully traced.

### Open Questions
- Issue #641's original statements were not retrieved in this assigned slice; cannot say which specific claims are resolved.
- No live traffic, benchmarks, configured authentication identity, effective rate limits, or third-party gh internal pagination were measured. The formula for gh issue view counts invocations, not internal HTTP requests.
- Full dispatch command tree and write paths were not traced; no claim that all duplicate reads are identified. A cross-repository budget coordinator is not established by the source examined.

## Problems
None
