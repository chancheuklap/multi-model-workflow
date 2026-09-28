# Vocabulary decisions (2026-09-28)

This round rechooses the names of MMW's own concepts so that each one recruits what a model already knows (a **leading word**, upstream `writing-for-agents` `## Leading words`), and completes the glossary (`CONTEXT-MAP.md`, `docs/contexts/*/CONTEXT.md`). The inventories behind it list every term the skills use, where, and whether the glossary has it: `docs/reviews/2026-09-28-lightweight/vocabulary-inventory/*.md`.

## Scope

- **Concept names change; machine identifiers do not.** An identifier is a string a program, the tracker or a consuming repository reads: an event name (`ticket.bounced`), a label, a `.mmw/target.json` key, a CLI verb or flag (`lease.py claim`, `--break`), an environment variable, an output token (`BREAK ARMED`, `ALL MET`), a file or directory name, a code constant (`JUDGES`). Where the prose names a concept by its identifier (the `contract` child, the `finding` child), that identifier stays its only name: introducing a second prose name would give one concept two names.
- **Upstream's own vocabulary stays upstream's.** A term an upstream skill uses in upstream's sense (wayfinder's fog of war, destination, HITL/AFK; to-tickets' expand-contract, blast radius; code-review's smell names) is defined in that skill and in `mmw-v2/upstream/CONTEXT.md`, not in MMW's glossary. MMW's glossary records a term an upstream skill uses when this repository gives it a meaning of its own.

## Renames

Each row: the concept, its old prose name, its new name, the source of the new name, and why it fits exactly. "Everywhere" means every skill, reference, merge-note, glossary entry, `AGENTS.md`, the text scripts print or build for an agent, and the tests that assert that text.

| # | Concept | Old name | New name | Source | Why it fits |
| --- | --- | --- | --- | --- | --- |
| R1 | The session that runs a night: opens it, dispatches the frontier, lands, routes findings, writes the summary | main agent | **orchestrator** | Anthropic, "Building effective agents": the orchestrator-workers pattern, a central model that breaks work down, delegates it to workers and integrates their results | The pattern's prior is the behaviour MMW asks for: the orchestrator delegates and integrates, and does not do a worker's work. `worker` is already the other half of the pattern. The relay's `to` value `main` is an identifier and stays |
| R2 | What a caller hands the advisor | question packet, the packet | **brief** (advisor brief where the owner is not obvious) | the ordinary sense of a brief; the same word MMW already uses for triage's **agent brief** and exe-release's **fix brief** | One word for one family: a document written so a reader with no other context can act. The `advise <packet file>` argument name in the usage line changes with it; the command does not |
| R3 | A script an acceptance criterion names bare, which decides pass or fail (`story-parity.py`, `boundary-check.py`, `journey.py`, `harness-guard.py`) | judge; story judge | **oracle** (test oracle); **story oracle** | software testing: a test oracle is the mechanism that decides whether a test passed | "Judge" now carries the prior of LLM-as-a-judge, a model making a subjective call; these are deterministic scripts. The constant `JUDGES` and file names stay |
| R4 | Making the product itself fail one named interface on a journey's second start, to prove the journey notices | break switch | **fault-injection switch**; the practice is **fault injection** | fault injection (chaos engineering, reliability testing) | Exact: a deliberate, controlled failure to show the system under test detects it. `--break`, `MMW_BREAK`, `BREAK ARMED` stay |
| R5 | The product module that makes outbound calls, which a four-column boundary test replaces with a mock | outbound call module | **gateway** | Fowler, *Patterns of Enterprise Application Architecture*: Gateway, an object that encapsulates access to an external system | Exact, and the standard seam for substituting a test double |
| R6 | Registering a worktree's slot in the lease registry | claim (a lease) | **acquire** (a lease); release stays | lease vocabulary of distributed systems: a lease is acquired, renewed, released | Frees "claim" for its one pipeline meaning (a worker claiming a ticket). `lease.py claim` stays |
| R7 | One thing the watchdog's second or third layer reports as a `watchdog:` line | finding | **alert** | monitoring | "Finding" already names a review finding and the `finding` child; an alert is what a watchdog raises |
| R8 | The tracker-native dependency between two tickets | blocking link; native issue dependencies | **blocking edge** | graph vocabulary; upstream `to-tickets` step 5's own word | Upstream's word and the graph prior (edges, a frontier, a cycle) the linter and `status.py` already reason with. GitHub's feature name "issue dependencies" is named once, as the mechanism |
| R9 | The closing-comment skeleton `--draft` writes; a ticket body written but not yet published | draft (both) | **closing-comment draft**; **ticket draft** | plain words | Disambiguates one word used for two artifacts inside `verify-ticket`. `--draft`, `--drafts` stay |
| R10 | An event that shows a night stalled (`worker.queued`, `ticket.returned`, a `fault` child, a `handoff` result) | blocking event | **stall event** | ordinary sense (a stalled job) | "Blocking" is the ticket-graph word (R8) |
| R11 | The Spec axis's angle on persistent or process-wide state shared by integrated tickets | Shared state | **Shared-state ownership** | plain words | Separates it from the lint problem tag `shared-state`, a different concept |
| R12 | `verify-ticket`'s ordered questions that pick a child's kind | the five questions | **the kind questions** | plain words | "The five questions" is `to-tickets`' criterion ladder |

## Leading words added, not renamed

| # | Where | Text | Source |
| --- | --- | --- | --- |
| L1 | glossary **baseline** entry | the configuration-management sense: a reviewed and agreed item that serves as the basis for further work and changes only through change control, which here is a `contract` child | IEEE Std 610.12 |
| L2 | `retro` `SKILL.md` opening, the sentence that says causes are addressed to the environment | name the practice: a **blameless postmortem** | Google, *Site Reliability Engineering*, ch. 15 |
| L3 | glossary **night** entry | a night is read the way a **nightly build** is: unattended, its result read the next morning | build engineering |

## Kept, with the reason

- **night**: short, already the user's own word, and the nightly-build prior fits (L3).
- **baseline**: the configuration-management term, used in exactly that sense (L1). The other uses stay qualified: `baseline` run (the claim-time run, an identifier), checker baseline (the tool's own term), smell baseline (upstream code-review's term).
- **element parity**, **story**, **scene**, **story adapter**, **negative control**, **lease**, **slot**, **frontier**, **fold**, **closeout**, **heartbeat**, **watchdog**, **turn guard**, **relay**, **wake**, **harness**: each is the established term of its field, used in its sense.
- **four-column boundary test**, **product answers**, **closing pass**, **Memory closing**: plain descriptive names with no established term of the same meaning; "visual regression test", "contract test" and "test harness" were considered and rejected as false friends (they would bring in screenshot approval, consumer-driven contracts, and the `.mmw/harness/` directory respectively).
- **hook**: three mechanisms share the bare word; the glossary and the text qualify each: host hook, build hook, git hook.

## Glossary completion

The glossary records every concept of this repository's own text that an agent reasons with, one entry each, under the context whose skills use it most, in the existing entry shape (bold name, one or two sentences, `_Avoid_` where a wrong name is in use, `_Home_`). Two shapes are not one entry per string:

- A **family of identifiers** (plan lines `MERGE`/`DISPATCH`/`RELEASE`/`REVERIFY`/`RECOVER`/`ARCHIVE`/`HOLD`/`NOTHING`; the release engine's `where` states; an oracle's output lines; `--preflight`'s and `--closeout`'s output lines; the lint problem tags; the screen-contract row columns; the closing-comment headings) gets one entry naming the family, what it is for, and its `_Home_`, which lists the members.
- A term whose meaning is only its field's ordinary one (a Fowler smell, exit code, worktree) gets no entry.

Stale entries found by the inventory are corrected against their `_Home_` (the `Audit` entry describes a closing step that no longer recounts `Counts:` or traces `EVIDENCE:`). Every "same concept, several names" and "same name, several concepts" case in the inventories is resolved by the renames above or by qualifying the name in the text and the glossary.

## Second pass: candidates from the glossary completion

The glossary agents name-checked every entry they added or touched and listed candidates in `vocabulary-candidates/<context>.md`, without renaming. The decisions:

| # | Concept | Old name | Decision | Reason |
| --- | --- | --- | --- | --- |
| S1 | The relay absorbing an event into a wake already queued and unacked | folded (the relay's log line and prose) | **coalesced** | the established term of event-driven systems for merging duplicate events; "folded" sits beside **fold**, a different concept. The code variable `folded` stays |
| S2 | The confirmation `dispatch.sh finish` checks before merging | receipt, Retro receipt | the **`spec.retroed` event** (its identifier, its one name) | the concept already has an identifier; "receipt" also names the reverify receipt |
| S3 | The product module the compiled exe imports before serving, to catch a missing dependency | self-check module | **smoke module** | smoke test is exact, and the release manifest's field is already `smoke` |
| S4 | The fixed order that takes a toolbox change from `dev` to every host | the four release steps | **the four promotion steps** | promotion is release engineering's word for moving a build through ordered gates; "release" is `exe-release`'s domain |
| S5 | The session that runs `code-review` on a ticket | reviewer session | **reviewer** | the name every caller and event already use |
| S6 | The screen contract, in `code-review`'s `references/spec-reviewer.md` | the contract | **the screen contract** | "contract" alone is the `contract` child |
| S7 | `to-spec`'s fixed Implementation Decisions subsection for cross-component rows | `App · ` 页组合 | **cross-component composition** | skill text is English; no program reads the Chinese title |
| S8 | The screen contract's `rows` | control axis | **`rows`** (the identifier as its one name) | "axis" calls up a paired row/column sense that does not hold |

Not adopted: renaming the task board's edge state `done`, its `closeout` field and the UI axis category `design-page` (identifiers; the glossary tells them apart); prose names for the two senses of "decision" (each already has an identifier or a heading as its one name); `signature` → fingerprint (not the same mechanism); "cache" (upstream `writing-for-agents`' own term, used in its sense); "visual acceptance" (no term found whose meaning matches exactly).
