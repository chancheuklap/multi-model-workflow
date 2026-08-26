# Disposition, fingerprints, report

The nine checks are listed in [SKILL.md](SKILL.md) under "Checks: two classes, nine kinds". This file is what happens after they run.

## The commits this run makes

**The working tree was clean at step 1 of [SKILL.md](SKILL.md).** That fact makes every line below hold. No home-grown rollback.

A run makes up to three commits, in this order. Each stands alone so the user can revert one without losing the others:

| # | Holds | When it happens |
| --- | --- | --- |
| 1 | The criteria and wiring files setup mode created | End of setup mode, before the app starts. First run for a product only |
| 2 | Class A edits | After all nine checks finish. Its SHA goes in report section 1 |
| 3 | Fixes for class B findings the user marked `accepted` | After the user returns verdicts, which is after the report. Only when at least one item came back `accepted` |

**Commit 2 holds interface fixes only.** Keeping the criteria in commit 1 is what makes "revert section 1's SHA" safe: it undoes this run's interface edits and leaves the criteria the next run needs.

**Commit 3 is a separate commit, not an amend of commit 2.** The report already gave the user commit 2's SHA. Rewriting that commit would leave them holding a SHA that no longer exists.

## Class A edit flow

1. **Run all nine checks, collect every result, then enter edits.**
2. **Edit one, verify one.** After each edit, re-run only the check that produced that violation. The test: that violation's criterion now holds.
3. **After all edits, re-run all four class A checks.** Per-item verify cannot see a new class A problem this edit introduced. All four are deterministic. The re-run needs no model, and does not re-walk the semantic layer.
4. **A bad edit rolls back with git.** If the full re-run finds a new class A violation, or a per-item verify fails, `git checkout` that file to undo that edit. That item degrades to a finding. Verification result is `reverted`.
5. **Edit only what you can edit in source.** A violation inside a third-party component or a dependency package becomes a finding.

**Class B is judged on the interface as it stood before the class A edits, and stays that way.** Say so in the report. Class A fixes thresholds, WCAG, tokens, and runtime errors; it leaves the flows and meaning class B cares about untouched.

**All class A edits this run go in one commit, not one commit per item.** The message says this is a UI QA edit and lists the violations. Report section 1 still lists each. To undo one item, the user edits on top of that commit.

## Where the five disposition marks go

Class B uses MMW's existing five disposition marks. Class B waits for a verdict; this skill edits nothing there on its own. "Criteria" means this product's usability-criteria file. Fields are in [CRITERIA.md](CRITERIA.md) under "Usability criteria".

| Verdict | Who fixes | Store in criteria? | Next run, fingerprint hits |
| --- | --- | --- | --- |
| `accepted` | **Main agent fixes after the verdict comes back**, in commit 3 | Yes, status `confirmed` | **Report again**, marked "accepted and fixed last time, present again" |
| `rejected` | No fix | Yes, status `rejected` | Suppress. Leave it out of the report |
| `waived` | No fix | Yes, status `waived` | Suppress. Leave it out of the report |
| `duplicate` | Follow the item it points at | Do not store on its own | n/a |
| `needs-evidence` | No fix | **Do not store** | n/a |

**`accepted` is a regression mark, not a suppress mark.** `rejected` and `waived` mean "not a problem", so a later hit is suppressed. `accepted` means "it was a problem, and it was fixed", so a later hit means **it came back**.

**`needs-evidence` stays out of criteria.** It means this finding's source was not verified in source, so it is not yet a standing judgment. It lives in this run's report only.

Class B fixes have no deterministic check to re-run. Verify is the next run: if the problem is gone, that finding does not appear; if not, report again per the table.

**Store every long-lived verdict, whatever the conclusion.** `accepted`, `rejected`, and `waived` all write into this product's usability criteria, distinguished by status. Storing only `accepted` would make ruled-out items repeat every run.

## Ownership default

When the interface and the criteria disagree, the criteria layer picks the default:

- Disagrees with the threshold table → **default: implementation is wrong**. An executable floor has no reasonable "intentionally smaller" case.
- Disagrees with a design-system rule or a usability criterion → **mark for a user verdict**. An intentional design change is normal.

## Fingerprint: which check + which location

Each class B verdict stores a fingerprint, two parts: check id, plus location. Location uses that check's natural grain. Four shapes. **This skill generates the fingerprint. The user does not.**

**Element grain (B1, B5)**

```
check: B1
criterion: DS-rule-3          ← which rule was broken
screen: main
state: default
element-role: button
element-name: Sync
```

`screen` and `state` come from ids already on the screen map ([SKILL.md](SKILL.md) step 4). `element-role` and `element-name` come from the accessibility snapshot ([CRITERIA.md](CRITERIA.md), "What the probe collects").

**`criterion` is required.** One element can break two different criteria — spacing in the design system, and a product usability criterion. Without which rule, the two findings share a fingerprint, and `rejected` on one suppresses the other. B1 takes the rule id from design-system prose. B5 takes the usability-criterion id (`U-001`).

**Location is a screen-and-element address, never a CSS selector.** Selectors carry class names and positional indexes, and a relayout changes all of them.

**Step grain (B2)**

```
check: B2
walkthrough: create sync task
step: 3
question: 2
```

`walkthrough` is the path pack `path-name`. `step` is that step's `index` (both in [SEMANTIC.md](SEMANTIC.md) "Path pack"). `question` is which of the four, 1–4. Failures of question 2 and question 4 on the same step are two things. Store them apart.

**Screen grain (B4)**

```
check: B4
screen: main
state: default
question: 5
```

`question` is which of the six, 1–6. B4 asks per step, but the fingerprint is screen plus state — two steps that stop on the same screen and state merge into one.

**Screen grain or path grain (B3)**

```
check: B3
screen: [main]
state: [default]
```

`screen` and `state` are arrays. Length 1 for a single "very confused" step. Length 2 for the two-step "somewhat confused" item, in walk order.

**Class A stores no fingerprint.** It edits. There is no verdict to remember.

## Two-level match

Each run compares every class B finding fingerprint this run to stored verdicts in this product's usability criteria.

| Level | Condition | Result |
| --- | --- | --- |
| Level 1 · exact | Every fingerprint field matches | Same thing. Follow the stored verdict. Leave it out of the report |
| Level 2 · near | Same check, **exactly one** location field differs | Maybe the same thing. Report, attach the previous verdict, ask if it is the same thing |
| Neither | Different check, or two or more location fields differ | New problem. Report as usual |

"Exactly one field differs" is deterministic. Same input, same result. No model. **`check` is not a location field** — it must match, or the item falls through to "neither". Four examples:

| What changed | Which field | Level |
| --- | --- | --- |
| Button copy "Sync" → "Sync now" | element-name | Level 2 |
| State `default` split into `default` and `syncing` | state | Level 2 |
| A step inserted in the walkthrough; old step 3 is now 4 | step | Level 2 |
| Button moved screen and renamed | screen + element-name | New problem |

The last row is intended: a new screen and a new name is not the old thing. Ask again.

B3 `screen` and `state` are arrays. Compare **the whole array as one field**: identical contents means that field matches.

**After a level 2 hit.** User says "yes": update that verdict's fingerprint to this run's values, then follow the verdict. User says "no": treat as new; the user judges again; criteria gain an item.

**Location miss ends the match at level 2, which asks.** A relayout can reshuffle the whole screen, so falling back to comparing content would suppress far too often.

## Stale verdicts: list them, keep them

At the end of each run, inspect verdict items in this product's usability criteria. **Only items whose fingerprint falls in this run's scope:** the fingerprint's screen was checked this run, and neither match level hit. Those go in the report's last section.

**Verdicts outside scope never enter the stale test.** Default level is this-change (three levels in [SKILL.md](SKILL.md) step 5). Most screens were not checked this run, so they will not hit — listing them as "maybe dead" treats "not checked" as "checked and absent", and invites deleting criteria that still hold. B2 fingerprints locate by walkthrough; same rule: only walkthroughs actually walked this run.

So only the `full` level runs a complete stale check across every verdict.

**List them, keep them, and let the run pass.** If the user wants one gone, they say so. This line is how criteria stop rotting: verdicts only grow, and would keep suppressing problems that no longer exist.

## Report shape: five sections

Order is "what the user must do":

| Section | Content | User does |
| --- | --- | --- |
| 1 · Class A edits | One line per item: violation id, file and location, before, after, verification. End with commit 2's SHA | Nothing required. Look. To undo the whole run, revert that SHA |
| 2 · Class B new findings | Neither match level hit. Class A items whose verification is `reverted` also degrade into this section | Per-item verdict |
| 3 · Class B near matches | Level 2 hits, each with the previous verdict | Per item: "same / not the same" |
| 4 · Report items | The three defined in [SKILL.md](SKILL.md) under "Checks: two classes, nine kinds" | Nothing required. They may say one line |
| 5 · Stale verdicts | Fingerprint in this run's scope, no matching check result | Nothing required. To delete, they say so |

Sections 2 and 3 stay apart: section 3 only wants "same / not". Mixing them makes every item feel like a full verdict. Section 4 is **this run's boundary**. Section 5 is **existing criteria that may need cleaning**. Keep them apart.

Section 1 "verification" takes two values: `verified` (per-item re-run of that check passed, and the full class A re-run after all edits introduced no new class A violation) or `reverted` (any step failed, the edit was undone). **The whole report uses only these two words.**

**Five fixed header lines, before the five sections:**

```
Scope: this-change (no tag, default)
Covered: 3 screens / 7 states
Uncovered: 12 screens / 31 states
Criteria: thresholds v1 · Duck usability 14 confirmed · design system read and linted
Skipped this run: none
```

Where each line comes from:

| Line | Value |
| --- | --- |
| Scope | The level name from [SKILL.md](SKILL.md) step 5. After a degrade: "this-change → this-task (this-change did not touch interface files)", with the reason |
| Covered | Screens and states actually checked this run, counted from in-scope nodes on the screen map |
| Uncovered | Screen-map totals minus the previous line. Includes unreached states from the coverage report |
| Criteria | Three parts: threshold-table `version`; count of `confirmed` items in this product's usability criteria; design-system handling, one of "read and linted", "read, not linted", "missing" — matching [SKILL.md](SKILL.md) step 3 |
| Skipped this run | Check ids skipped this run, plus why. Missing design-system file: "A3, B1 (no design-system file)". A degraded dependency: the `degrade_note` from the preflight JSON. Semantic layer returned nothing: "B2, B3, B4 (semantic evaluation returned nothing)". Windows capability self-check missing items: name them. None skipped: "none" |

## Where verdicts flow back

**An accepted B1 flows into usability criteria, not into the design system.** The design system is read-only. An accepted design-system rule break becomes one item in this product's usability criteria. The body records which design-system rule it specializes for this product. Source points at that rule.

**A threshold-shaped verdict enters the threshold table.** For example the user confirms a min size for a class of elements: add an item in the four-field shape in [CRITERIA.md](CRITERIA.md) "Threshold table". The next run judges it as A1.

Every flow-back names this UI QA run and the date as source. Fields and format for both files are in [CRITERIA.md](CRITERIA.md) under "The three cross-boundary files".
