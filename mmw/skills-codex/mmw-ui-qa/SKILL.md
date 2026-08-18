---
name: mmw-ui-qa
description: UI QA: check the interface against agreed criteria, and produce violations and findings. Use to check the piece just finished during prototype iteration, or to run a full flow after the app has landed. Do not use when the user operates the interface and gives opinions — that is a walkthrough.
argument-hint: "[this-task|full] [product name; omit to auto-detect]"
---

# UI QA

UI QA checks the interface itself. It **is not any of the review gates**. It can run during prototype, when review is not in play. It is interactive. The normal flow stops to ask the user.

**The main case is the piece just finished.** Default scope is the latest commit. Say nothing extra for a daily run. Tag `full` for a full-flow check, on first landing and on the Windows pass. The first run for a product builds its criteria and wiring, then continues.

**If the user tagged a scope, use that tag. Do not infer.**

UI QA does not take these:

| The user wants | Hand to |
| --- | --- |
| To operate the interface and give opinions | `$mmw:mmw-prototype`. That is a walkthrough. Only the user can do it. UI QA does not judge "this version is good" |
| To decide whether an interface design should be this way | `$mmw:mmw-grilling`. UI QA checks against agreed criteria. It does not make design decisions |
| To change the design system itself | The target repo. The design system is read-only to UI QA. An accepted rule break flows back as a usability criterion |
| To check that code is correct, or that the diff matches the artifact | `$mmw:mmw-review`. UI QA does not read the diff |

## Context

| Material | How | Read for |
| --- | --- | --- |
| Domain docs | Read this run's range as `$mmw:mmw-domain-modeling` specifies | Report and finding bodies use the project's canonical terms |
| ADR | Run `mmw artifact index adr`, then read the ones about the interface | Interface decisions must not conflict with them |

## Checks: two classes, nine kinds

Each run executes nine **checks**. The set is closed. This skill does not invent a tenth. Later steps name them by number.

| ID | Judges | Criteria from |
| --- | --- | --- |
| **A1** | A number crosses a threshold min or max | Threshold table |
| **A2** | The accessibility engine reports a violation | The engine's own rules |
| **A3** | An element's token is outside the design system's **declared** set | The machine-readable part of the design system |
| **A4** | A runtime error in the renderer console | None. The error is the fact |
| **B1** | A named rule in the design-system prose | The prose part of the design system |
| **B2** | Any of the four cognitive-walkthrough questions unanswered | This skill, in [SEMANTIC.md](SEMANTIC.md) |
| **B3** | Confusion score high | This skill, in [SEMANTIC.md](SEMANTIC.md) |
| **B4** | Any of the six Trunk Test questions unanswered | This skill, in [SEMANTIC.md](SEMANTIC.md) |
| **B5** | A break of this product's usability criteria | Usability criteria |

**What a failing check produces has a different name per class:**

- **Class A** (A1–A4) is deterministic. The result is a fact, a **violation**. Fix it without asking.
- **Class B** (B1–B5) is model judgment. The result is a candidate, a **finding**. Report it. Wait for a verdict.

The split is the kind of judgment, not where the criterion lives.

**Report items are the third thing, and this is their only definition.** Three of them: coverage report, criterion self-check, declaration-vs-implementation mismatch. They are facts about this run, not problems in the interface. They have no interface fix target, so they drive no edits and take no user verdict. Later steps say "report item" and mean exactly this.

## 1. Preflight

Run `mmw-ui-qa preflight`. It prints one JSON: working tree, the four dependencies, and the products this repo already wired.

| Fact in the JSON | Action |
| --- | --- |
| `git.clean` is false | **Stop.** List `git.uncommitted`. Ask the user to commit, then invoke this skill again. This run ends here |
| `deps.stopMissing` is not empty | **Stop.** Name those capabilities and ask the user to run the MMW install entry |
| `deps.skipChecks` is not empty | Continue. Those check ids go in the report header "Skipped this run" |
| A degraded capability carries `degrade_note` | Write the report header the way that note says |
| The command is missing from `PATH` | **Stop.** Ask the user to run the MMW install entry |

`deps` comes from the runtime dependency declaration, which also owns what a missing capability costs. Read the costs from the JSON.

**A clean working tree makes three later facts hold:** scope is the latest commit (step 5), a bad edit rolls back with git (step 7), and this run's edits land in commits that hold none of the user's code.

## 2. Product

Criteria and wiring are per product, so the product is next. `criteria.products` in the preflight JSON lists what this repo already has, each with its `product` field. **Four levels. Stop at the first hit:**

1. The free text in the argument hint names a product → use it. Do not ask.
2. One product in the list → use it. A single-app repo is never asked.
3. Several products → list them and let the user pick once. **List the `product` field, not the filename.**
4. Empty list (first run on a new repo) → ask which product this run checks. Product id: lowercase letters, digits, hyphens.

The name from level 4 is the id used when creating files in the next step. Do not ask it again in the questionnaire.

**One product per run.** A second product is a second invocation.

Now run `mmw-ui-qa preflight <product-id>`. The JSON gains `criteria.selected` (the three per-product files and their paths), `wiringLint`, and `designSystem`.

## 3. Criteria and wiring

**If any of `criteria.selected` does not exist, enter setup mode: read [SETUP.md](SETUP.md) in full now**, create the missing files, then re-run `mmw-ui-qa preflight <product-id>` and continue down this table.

| Fact in the JSON | Action |
| --- | --- |
| `wiringLint.ok` is false | **Stop.** Give the user `wiringLint.output` as it stands. The app cannot start from a wiring file that does not parse |
| `designSystem.declared` is null | Continue. Skip A3 and B1. Report header: "A3, B1 (no design-system file)" |
| `designSystem.exists` is false | **Stop.** Wiring points at a design system that is not there |
| `designSystem.errors` above zero | **Stop.** List them. A3 and B1 have no criteria to judge against |
| `designSystem.warnings` above zero | Continue. List each in the report. **Mark them as criteria problems, not interface problems** |
| `designSystem.linted` is false | Continue. Mark the report header that criteria were not linted this run |

Design-system lint results are the **criterion self-check** report item. Field-level wiring rules live in the wiring schema next to the linter, so this file keeps only what the linter cannot decide: the flow above.

## 4. Build the screen map

**Read [CRITERIA.md](CRITERIA.md) in full now.** This step starts the app from wiring fields. Step 6 judges the nine checks from that file.

The map records screens, states per screen, and jumps between screens. The next step maps changed files to screens from it. Step 6's cognitive walkthrough builds paths from it. **It is built in-process. It is not a file. Discard it after the run.**

Start the app from wiring `launch` (command, working directory, env). Secrets are `env:<name>` or `keychain:<name>`; resolve by prefix. Recognize the main window from `mainWindow` `titlePattern` or `urlPattern`. If `prepare.steps` exists, run them in order for login and test data.

Three sources merge into one map. Union, not exclusive:

| Source | How | Contributes |
| --- | --- | --- |
| Code extract | Read routes, state machines, conditional-render branches | Baseline screens and jumps. **Record each file path you read into that screen node's `source-files` array** — the next step uses it |
| Runtime probe | Walk reachable paths from the main window | Jumps code does not show, and reachability |
| Usability criteria | States named in this product's usability criteria | States the probe cannot reach without special conditions |

The same state from several sources becomes one node, recording which sources hit it. **Reachability is runtime probe only:** probed states are reached; states only in the other two sources are unreached. Keep unreached states in the map.

**What you can reach depends on the wiring file.** Empty, loading, error, and permission states enter the check when `prepare.steps` can reach them. What it cannot declare (fault injection, several permission identities, resetting data mid-check) becomes one coverage-report line — that is the product's own test-fixture work.

Unreached states go in the **coverage report** report item, one line per state name and why.

## 5. Scope

**Three levels. The user's tag picks the level. No tag is the default.**

| Level | Tag | How scope is computed | When |
| --- | --- | --- | --- |
| **this-change** | none (default) | `git diff HEAD~1...HEAD --name-only` | Just committed; a quick check |
| **this-task** | `this-task` | `git diff $(git merge-base HEAD <parent>)...HEAD --name-only` | A task has landed; before handoff |
| **full** | `full` | Every screen and state in the map. Ignore git | First landing, or before Windows |

`<parent>` is the branch this branch was created from. Several long-lived branches: ask once. One main branch: use it.

**Changed files become screens.** File F maps to every screen node whose `source-files` contains F. That is a lookup in the map from the previous step, not another code scan.

**Degrade changes scope only. It does not drop checks.**

| Case | Degrade to | Report first line |
| --- | --- | --- |
| At least one screen | No degrade | The level name |
| Zero screens (backend, config, or docs) | this-task | this-change → this-task (this-change did not touch interface files) |
| this-task also maps to zero screens | Smallest set: the `mainWindow` screen plus its direct children in the map | this-task → main window and next level (this-task did not touch interface files) |
| `HEAD~1` does not exist (first commit on the branch) | this-task | Write "this-task". No extra note |

**All nine checks run at every level.** The level only chooses which screens they act on.

## 6. Run the checks

**Run all nine, collect every result, then go to step 7.** Fixing while checking would break the report: an A3 token edit changes what B1 sees, and the report would no longer match the interface the user opens.

Per-check rules, the four probe inputs, and the five numeric fields are in [CRITERIA.md](CRITERIA.md). Method and dispatch for B2, B3, B4 are in [SEMANTIC.md](SEMANTIC.md). Read that file in full before those three.

**Primary input is structured data, not screenshots.** All of it comes from a browser session driven by `mmw-ui-qa browser`. The accessibility snapshot carries roles and accessible names only — no class, test id, wrapper, or inline style — so the same method covers native DOM, React, and web apps with no per-framework adapter.

Screenshots only in two cases, **cropped to the relevant region, never full screen**: cognitive-walkthrough question 2, and when you must show the user evidence.

## 7. Dispose and report

Class A produces violations: **edit and commit them alone**. Class B produces findings: **report only, wait for a verdict**.

**Read [VERDICTS.md](VERDICTS.md) in full now.**

| Case | Action |
| --- | --- |
| Report given to the user; sections 2 and 3 have items to judge or answer | Wait for per-item verdicts and the "same thing?" answers in section 3. After they finish, write verdicts into usability criteria as [VERDICTS.md](VERDICTS.md) specifies, then report the final result once more |
| Report given to the user; sections 2 and 3 are empty | Nothing for them this run. The report ends the run |
| Called by `$mmw:mmw-prototype` or `$mmw:mmw-review`, and the user already judged | Hand the report back to the caller |

## Platform

The seven steps above are the Mac side: the skill starts the app and runs the whole flow.

**On Windows, read [WINDOWS.md](WINDOWS.md) in full first.** The user must be present and start the app once. Step 4's start becomes a connect to the debug port they opened. The other six steps stay the same.
