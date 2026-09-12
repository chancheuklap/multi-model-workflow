# Task board · the ticket's right-hand column

## The question

The 事件 list in the board's detail column is unreadable to a person: it prints the
pipeline's own event names (`worker.touched`, `ticket.checked`), the payload fields behind
them (`run=self result=met`, `term_e9f36d97-196b-417d-b596-69aca3f70b00`,
`5d2026a..d810a10`, `login=chancheuklap`), and 22 rows of equal weight with nothing tying
them to the `working` / `review` / `verify` pills the ticket's own card carries. What
should that column look like instead?

Three variants, on the real page, over the real board payload of ticket #729 of
`agentflow-hq/agentflow` — the ticket in the screenshot that opened the question.

## Run it

```
python3 prototypes/board-orchestration/sidebar-events/UI/serve.py
```

It prints one URL per variant and serves `mmw-v2/board/page/` as it is, with `/api/board`
answered from `fixture.json` beside this file. The fixture is one answer of the live
agentflow board, read once from `127.0.0.1:47101` at first start and kept out of git
(`--refetch` reads it again, `--board-port` picks another repository's board): the payload
has to be frozen, or three variants are compared against three different sets of events.
`←` `→` or the bar at the bottom switch variants; `?sel=<n>` opens another ticket.

## What all three share

The naming is one decision, made once in `vocab.mjs` and used by all three, so what the
variants are being judged on is the layout. Three rules:

1. **Every event has an English name a person can read.** No dots, no payload values in
   the name.
2. **Every event carries the step pill its ticket card would have shown while that event
   was the newest one on the ticket** — the same six words the canvas card uses:
   `queued` `working` `waiting` `review` `verify` `landed`. A refusal, a release, a
   retraction and a lost session all leave nothing running, so all four read `queued`.
3. **Backend fields are moved, not deleted.** Session ids, runners, machines, worktrees,
   commits, per-criterion evidence and the raw comment line are one click behind each
   event, in the payload's own field names.

| event | name it shows | pill |
| --- | --- | --- |
| `child.closed` | Sub-issue closed · Finding became a ticket | `landed` |
| `child.opened` | Finding raised · Your decision needed · MMW itself broke · Spec does not hold · Left for a later ticket | `working` |
| `reviewer.lost` | Reviewer session lost | `queued` |
| `reviewer.reported` | Review posted | `review` |
| `reviewer.started` | Reviewer started | `review` |
| `spec.closed` | Night closed | `queued` |
| `spec.merged` | Night's branch merged | `landed` |
| `spec.opened` | Night opened | `queued` |
| `spec.suspended` | Night suspended | `queued` |
| `ticket.bounced` | Merge bounced | `verify` |
| `ticket.checked` run=`repo-checks` | Repository checks | `verify` |
| `ticket.checked` run=`reverify` | Criteria re-run · Criteria re-run after landing | `verify` · `landed` |
| `ticket.checked` run=`self` | Criteria run | `working` |
| `ticket.claimed` | Ticket claimed | `working` |
| `ticket.landed` | Landed | `landed` |
| `ticket.passed` | Ticket passed | `verify` |
| `ticket.refused` | Pick-up refused | `queued` |
| `ticket.regressed` | Regressed after landing | `landed` |
| `ticket.released` | Claim released | `queued` |
| `ticket.returned` | Ticket handed back | `verify` |
| `verifier.failed` | Verification failed | `verify` |
| `verifier.lost` | Verifier session lost | `queued` |
| `verifier.passed` | Verification passed | `verify` |
| `verifier.started` | Verifier started | `verify` |
| `worker.decided` | Decisions recorded | `working` |
| `worker.lost` | Worker session lost | `queued` |
| `worker.queued` | Waiting for a slot | `waiting` |
| `worker.replaced` | Worker replaced | `queued` |
| `worker.resumed` | Worker resumed | `working` |
| `worker.retracted` | Worker retracted | `queued` |
| `worker.started` | Worker started | `working` |
| `worker.touched` | Another ticket touched its files | `working` |

A `ticket.claimed` never opens a block or a group of its own: `dispatch.sh` starts the
session and the worker claims the ticket a minute later, and a person reads those two as
one act.

## The three variants

**A · Phase blocks** (`variant-a.mjs`) — **the one that won**. The list becomes one block
per step the ticket passed through, headed by that step's pill and by the event of the
block worth opening it for. Only the last block and any block that went wrong are open, so
#729 opens at six lines instead of twenty-two; a click opens a block, a click on an event
opens its fields.

Its column reads, top to bottom: what this is and the way out to GitHub · title · `#729 ·
spec · map` · lamp, status word, step pill, duration · where it ran · what needs a person
(orange) · 前置 · 后续 · 进程 · 子 issue. What a person decides on — is anything holding
this ticket, does anything wait on it — is above the history, not under it.

**B · Plain-language feed** (`variant-b.mjs`). Keeps the chronological list and fixes the
reading instead of the structure: one Chinese sentence at the top says how the whole
ticket went, every event is a name over a line of plain English, and the pill appears only
on the row where the step actually changed. Longest of the three — it hides nothing.

**C · Run cards** (`variant-c.mjs`). Drops the flat list. A ticket's life is a small number
of attempts, and each attempt is a card: which steps it reached, who ran it (worker,
reviewer, verifier and their models), what came out of it. Only the lines that carry an
outcome are on the card; the rest is behind one count. Shortest of the three, and the only
one that shows at a glance that #729 was started twice.

## Where it is wired

`mmw-v2/board/page/app.mjs` carries a scaffolding block, marked `PROTOTYPE scaffolding`:
`?variant=` hands the detail column to `mount.mjs` here, `?sel=` opens a card on load.
Nothing runs without the parameter, and `serve.py` is the only server that serves this
directory under `/proto/`. Both come down when a winner is folded into
`page/detail.mjs` and `page/styles/board.css`.

## Two more rules the column is held to

**A related issue is shown the way its own card is shown.** Its lamp, and the same step
pill — `#728 landed`, `#731 queued`. The lists are split into 前置 (what it waited for) and
后续 (what waits on it), and whichever row still holds is sorted to the top and marked
`挡着`, in the orange the board keeps for "needs you". That word is the only thing a
blocking list is opened to find out; a landed blocker is noise and sinks.

**No sentence is used where a word will do.** A section title is a noun (`进程`, `前置`,
`后续`, `子 issue`), never a phrase about itself; a count is a number; an empty section is
`还没有事件`, not an explanation of what would go there; the duration slot holds `1h44m`
and nothing else, because the status word and the pill beside it already say how it ended.
The pipeline's own long strings are cut on the way in: `跑了 1h02m 后交回` → `1h02m`,
`等收口那一轮` → `等收口`, `在 GitHub 打开 #729 ↗` → `GitHub ↗`.

## The answer

**A wins**, and is still being refined against real tickets. B and C stay as reference:
B's opening sentence and C's per-run cards are both worth stealing from if A's blocks turn
out to hide too much. Nothing has been folded into `page/detail.mjs` yet.
