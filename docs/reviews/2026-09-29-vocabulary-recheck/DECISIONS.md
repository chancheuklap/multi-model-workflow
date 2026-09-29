# Vocabulary recheck decisions (2026-09-29)

This round examined every entry of the glossary (`CONTEXT-MAP.md`, `docs/contexts/*/CONTEXT.md`), 492 in all, to the standard of `docs/reviews/2026-09-28-lightweight/vocabulary.md` (naming order and false friends: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `### Vocabulary`). Twelve slice reviewers gave each entry one verdict (`candidates/<slice>.md`, one row per entry; `BRIEF.md`). Four verifiers then checked every proposal against the files and the cited sources, and merged the cross-context lists (`verify/a.md` to `verify/d.md`; `VERIFY-BRIEF.md`). This file is the result. Evidence, line numbers and the full list of places each change touches are in the `verify/` row named in each table; an agent applying a row reads that row first.

The same scope as 2026-09-28 holds: machine identifiers (CLI verbs and flags, event names, JSON fields, output tokens and columns, labels, file names, headings a program finds) stay byte for byte, and upstream's own terms keep upstream's sense.

## Verdicts on the 492 entries

| verdict | count |
| --- | --- |
| IDENTIFIER (a program reads the name; it stays) | 225 |
| KEEP-ESTABLISHED (already the field's term) | 101 |
| KEEP-PLAIN (plain words; established terms checked and rejected) | 103 |
| UPSTREAM | 22 |
| RENAME proposed | 25 |
| FIX-NAME (defect, no replacement found) | 15 |
| UNSURE | 1 |

(Counts from the reviewers' final messages; `candidates/*.md` hold the rows.)

## Renames adopted

| # | concept (context) | old name | new name | source | verify row |
| --- | --- | --- | --- | --- | --- |
| T1 | a (model, reasoning effort) choice a host offers (night) | pair | **model-and-level pair**; drop `_Avoid_: offering` | `editing-models.md`'s own wording | a 1 |
| T2 | the family of lines `release-flow.sh where` prints (release) | verdict | **`where` state** | state machine; `driving.md` "State table" | a 4 |
| T3 | the attempt history `release-flow.sh receipt` prints (release) | receipt | **release receipt** | the command's own heading | a 5 |
| T4 | one product's run of the release engine, `init` to `close`/`abort` (release, new entry) | round, loop, build loop | **release loop**; "round" keeps only the `.round` counter | identifiers `NO-LOOP`, `RELEASE_LOOP_DIR` | a 7 |
| T5 | a skill's or subsystem's test suite (toolbox) | `tests/run.sh` | **`mmw-v2/tests/<name>/run.sh`** | the literal in `AGENTS.md` | a 8 |
| T6 | the one setting a dispatched session starts with (toolbox) | permissions | **permission mode** | Claude Code, "Choose a permission mode" | a 9 |
| T7 | the checkout host symlinks point at (toolbox) | frozen checkout, installed worktree, frozen worktree | **installed checkout** | `AGENTS.md`'s majority wording | a 10 |
| T8 | the three checks every suite runs first (toolbox) | shared preflight checks | **shared lints** | lint (static analysis) | a 11 |
| T9 | `manage-agents-md`'s conditional block (toolbox) | domain section | **`<important if>` block** | the skill's and HumanLayer's own name | b 1 |
| T10 | `/wait-what visual` (toolbox) | `visual` tag, routing flag | **`visual` argument** | Claude Code `argument-hint` | b 2 |
| T11 | wizard's dim hint line (toolbox) | stage note | **`note`** (wizard) | `template.sh` `note()` | b 3 |
| T12 | the one command that runs a repository's checkers (toolbox) | the one command, entry point, manual entry point | **checker command** | plain words; **checker** | b 5 |
| T13 | to-spec's judgement that one source needs several specs (tickets) | several specs | **spec division** | the skill's own noun | b 7 |
| T14 | component page and app page tickets together (tickets) | interface ticket, UI ticket | **page ticket** | `cutting-interface-tickets.md` "every later page ticket" | b 8 |
| T15 | the ticket cut from one Critical flows line (tickets) | acceptance ticket | **critical-flow ticket** | the spec bullet; `CRITICAL_FLOWS_RE` | b 9 |
| T16 | the bracketed string naming the lint check that fired (tickets) | problem tag | **lint rule ID** (always qualified) | ESLint `ruleId`, SARIF `ruleId` | b 13 |
| T17 | the three conditions for saving a Memory (ticket-run) | capture gate | **save conditions** | `implement`'s own wording | c 1 |
| T18 | a comment on a tracker issue, ticket or spec (ticket-run) | ticket comment | **issue comment** | GitHub, `gh issue comment` | c 2 |
| T19 | the reviewer's one posted report (ticket-run) | review comment | **review report** | IEEE 1028; `--review` help text | c 3 |
| T20 | the reviewer's conclusion on one finding (ticket-run) | finding verdict | **Holds / `refuted` / Could not tell** (named by its members) | `session.md` step 3 | c 4 |
| T21 | the Spec axis's four angles on integrated tickets (ticket-run) | four angles | **semantic-conflict angles** | Fowler, SemanticConflict | c 5 |
| T22 | UI review categories (ticket-run) | `undecorated`, `design-page` | **`unpaired-decoration`**, **`design-page-wrong`**; `overall-look` stays | plain words; no program reads them (verified) | c 6 |
| T23 | `implement`'s rules while writing code (ticket-run) | writing rules | **code-writing rules** | plain words | c 7 |
| T24 | the readable name the board shows for an event (task board) | event name | **event display name** | plain words | c 9 |
| T25 | the board's 60-second re-read (task board) | board feed | **board polling** | polling | c 10 |
| T26 | a `Component · ` design page (ui-acceptance) | component | **Component page** | sibling **App page** | c 12 |
| T27 | the application the oracles test (ui-acceptance) | target | **product under test** ("the product" as short form) | Meszaros, system under test | c 13 |
| T28 | (ui-acceptance) | **boundary** meta-entry | delete it; **boundary criterion** and **four-column boundary test** carry the word | — | c 14 |

## One word, one meaning: senses split across contexts

From `verify/d.md` part 1. The bare word keeps the sense named; the other senses take the name given.

| # | word | bare word keeps | other senses become | d row |
| --- | --- | --- | --- | --- |
| W1 | interface | a module's interface (upstream `codebase-design`) | one `<METHOD> <route>`: **operation** (OpenAPI; the screen contract's word); the user interface: **UI** | 2 |
| W2 | contract | what a ticket was told to follow (the `contract` child) | 36 bare uses meaning the screen contract: **screen contract**; `.mmw/target.json` by its path | 3 |
| W3 | round | the tickets fix-and-rerun pass | release: T4; `EXP.md`: **experiment round**; the watchdog's: "the watchdog's round" | 1 |
| W4 | run | one execution | definitions using "run" for a product copy, an event stretch or a worktree reworded | 4 |
| W5 | hold / holder | a hold on a ticket | the lock's: **lock holder** | 5 |
| W6 | effort | reasoning effort | "reasoning level" becomes **reasoning effort** | 9 |
| W7 | gate | Continuous Delivery's gate | "closing gate", "closeout gate": **closeout** | 12 |
| W8 | category | the retro's category | the review's: **review category** | 33 |
| W9 | part | a design-system part | the `data-ui` half of the project template: `<element>` | 52 |
| W10 | example data | the real product data | the project template's heading: `## Page data` | 55 |
| W11 | runtime | MMW's running scripts | "acceptance runtime" is **product answers** (7 places) | 58 |
| W12 | generation | the relay's integer counter | the timestamp is named by its field, `since` | 32 |

Smaller single-line rewordings (d rows 6, 10, 13, 20, 22, 23, 26, 34, 38, 41, 50) are applied as that table states.

## Definitions corrected, names kept

From the verify files; each row states the new wording.

- `wait` does not block (a 2); **fix round** is the P2 `derive` counter, and **budget** lists three caps (a 6); **stale link** covers hook registrations and Paseo profiles (a 12); **stance** "is not a bare attitude" (b 4); **probe** covers both directions and is distinct from **negative control** (b 6); **seam** takes `codebase-design`'s whole definition (b 10); **retiring line** bolded at its source (b 14); **edit pages** describes set-up and sign-off (c 11); **back door** names Test Logic in Production (c 15); **lease** has no term and is per worktree (c 16).
- **suspend** pauses a night: `dispatch/references/night.md` `## Suspending the night` says workspaces, branches and pushed commits stay for `open` and `advance` to take up. `candidates/night-b.md` is right; `verify/d.md` Notes, which says it cannot be resumed, is wrong.
- The slice reviewers recorded further entries whose facts differ from their `_Home_` (for example **slot given back**, **generation**, **repository Space**, **closing pass**, **budget**, **surface**, **composition module**, **shell**, **triage role**). These sit in the reason column of `candidates/*.md` and were not re-verified by a second agent, except the ones the verify files name; each is checked against its `_Home_` when applied.

## New entries

`verify/d.md` part 2: 29 concepts get an entry (among them **design page**, **batch**, **hold**, **retro problem**, **final run**, **runner adapter**, **main worktree**, **archive** as plan line `ARCHIVE`, **skill set**, **`Done when` line**, **reverse sweep**, **agent inside Claude Design**) and 12 are named inside an existing entry; the context and name for each are in that table.

## Leftovers of the 2026-09-28 renames

`verify/d.md` part 3: 20 remaining prose occurrences of old names (main agent, packet, judge, "that module", claim a lease, shared state, self-check, reviewer session, the `页组合` `_Avoid_` line, handoff package), each with path, line and replacement. Change records (merge-notes quoting old text, downstream-notes) keep the old names.

## Rejected

| proposal | reason | row |
| --- | --- | --- |
| `phase` column → event | an output column a test asserts and a JSON key; the entry already states its meaning | a 3 |
| agent brief → investigation record | `## Agent Brief` is a heading posted in issue comments that `to-spec` finds; renaming breaks existing comments and every upstream merge | b 12 |
| contract ticket → any name | the defect stands (none of the set's contracts), but no candidate matches; "product-answers ticket" is the nearest, for a later round | b 11 |
| `drawn-wrong` | reads as a product defect; the category says the design page is wrong | c 6 |
| UI ticket | would include the design-system ticket, which is outside the set | b 8 |

## For the owner

Text the owner reads on the task board page:

1. **The Night** (the board's left-column title) shares "night" with "Night opened / Night closed", which mean one run of one spec (c 8).
2. **released** for a blocker that no longer blocks, on the same page as "Claim released" for a claim given back (d part 1 row 7).
3. **Reviewer session lost**, the display name for `reviewer.lost`, keeps the name S5 retired elsewhere (d part 3 row 23).

## Found on the way, not vocabulary

- `release-flow.sh`: the comment at lines 133-135 says the budget counts every repair round, but only the P2 commit (line 331) increments `fix_rounds`; a P1 fix or a `transient:` re-run is never counted (a Notes).
- `docs/adr/README.md` lines 23, 25, 54 credit `design-pages` `references/edit-pages.md` with a design-time screenshot check it does not contain (c Notes).
