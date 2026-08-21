---
name: ui-qa
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
| To operate the interface and give opinions | `prototype`. That is a walkthrough. Only the user can do it. UI QA does not judge "this version is good" |
| To decide whether an interface design should be this way | `grilling`. UI QA checks against agreed criteria. It does not make design decisions |
| To change the design system itself | The target repo. The design system is read-only to UI QA. An accepted rule break flows back as a usability criterion |
| To check that code is correct, or that the diff matches the artifact | `code-review`. UI QA does not read the diff |

## Context

| Material | How | Read for |
| --- | --- | --- |
| Domain docs | Read this run's range as `domain-modeling` specifies | Report and finding bodies use the project's canonical terms |
| ADR | If the repo has `docs/adr/`, read the ones about the interface | Interface decisions must not conflict with them |

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

- **Class A** (A1–A4) is deterministic. The result is a fact, a **violation**. Fix it. Do not spend the user's time.
- **Class B** (B1–B5) is model judgment. The result is a candidate, a **finding**. Report it. Wait for a verdict.

The split is the kind of judgment, not where the criterion lives.

Three more **report items**: coverage report, criterion self-check, declaration-vs-implementation mismatch. They are facts. They have no interface fix target, so they do not enter user verdicts and they do not drive edits.

## 1. Clean working tree

Run `git status --porcelain`. **If it prints anything, stop.** List the uncommitted files. Ask the user to commit, then invoke this skill again. After they commit they call you. This run ends here.

This step makes three later facts hold: scope is the latest commit (step 6), a bad edit rolls back with git (step 9), and this skill's edits can be one commit with none of the user's code mixed in.

Continue. Criteria and wiring paths have no name segment. The screen map and the report do not enter the repo. Behavior is the same from the main checkout or a task worktree.

## 2. Dependencies

This skill carries its own scripts, next to this file. Resolve their absolute paths once; every command below is written relative to the skill directory.

```bash
bash scripts/check-deps.sh
```

It prints one line per capability with the path it resolved to, and exits 0 when all four are there. **Use the paths it printed** — this skill installs nothing and hardcodes no location.

Where they come from is not this skill's business, and deliberately so: the browser automation, the accessibility engine, and the design-system linter come from wherever this machine keeps its Node CLIs; the design-system author is a skill the host has already loaded. Installing a private copy of any of them would make a second version of something another tool is also running, and two versions of a linter disagree about the same file only once the run is already half done.

On non-zero exit, install what it named, then switch on which capability is still missing:

| Missing capability | Name in `deps.json` | Action |
| --- | --- | --- |
| Browser automation | `browser` | **Stop.** It drives every check |
| Design-system author | `design-system-author` | **Stop.** Step 4 uses it when the design system is missing |
| Accessibility engine | `accessibility` | Degrade: skip A2. Run the other eight |
| Design-system linter | `design-lint` | Degrade: skip the criterion self-check in step 5. Mark the report header that criteria were not linted this run. Run all nine |

The first two stop: there is no fallback. The last two each affect only their own slice.

## 3. Product

Criteria and wiring are per product, so the product is first. **Four levels. Stop at the first hit:**

1. The free text in the argument hint names a product → use it. Do not ask.
2. No name, and there is one wiring file → use it. Do not ask. A single-app repo is never asked.
3. No name, and there are several wiring files → list them and let the user pick once. **List the `product` field, not the filename.**
4. **No wiring file** (first run on a new repo) → ask which product this run checks. Product id: lowercase letters, digits, hyphens.

The name from level 4 is the id used when creating files in the next step. Do not ask it again in the questionnaire.

**The four paths, relative to the target repo root:**

| Want | Path |
| --- | --- |
| This product's wiring file | `docs/ui-qa-wiring/<product-id>.json` |
| Threshold table (one per repo) | `docs/ui-criteria/thresholds.json` |
| This product's usability criteria | `docs/ui-criteria/products/<product-id>.md` |
| Design-system file | Wiring field `designSystem`. Repo-relative path. **The target repo owns that file**, so it does not live under either root above |

Levels 2 and 3 list existing products: list `docs/ui-qa-wiring/`, read each file's `product` field.

**Lint the wiring file before using anything in it:**

```bash
python3 scripts/wiring_lint.py docs/ui-qa-wiring/<product-id>.json
```

Non-zero exit: **stop**, and give the user its output as it stands. It also refuses a file whose name does not match its own `product` field — that check is what keeps a malformed product id from writing outside these roots.

**One product per run.** A second product is a second invocation.

## 4. Criteria and wiring; create what is missing

If all four files from the previous step exist, skip this step and go to step 5.

If any is missing, enter **setup mode**: **read [SETUP.md](SETUP.md) in full now**, create the missing files, then return to step 5 and continue this run.

## 5. Lint the criteria first

Once the files exist, lint the design-system file:

```bash
design.md lint <design-system file from the previous step>
```

The file argument is required. Without it the linter reads whatever `DESIGN.md` happens to sit in the working directory, and that is not necessarily the file wiring `designSystem` points at. The linter checks format, cross-token WCAG contrast, and reference integrity. It does not start the app. It prints JSON. Each item has `severity` `error` or `warning`.

Do not skip this step. A3 and B1 treat the design system as criteria.

| Lint result | Action |
| --- | --- |
| No findings | Continue. Criterion self-check says "linted, no issues" |
| Any `error` | **Stop.** The file will not parse. A3 and B1 cannot run |
| Only `warning` | Continue. List each in the report. **Mark them as criteria problems, not interface problems** |
| Command fails, or output is not JSON | Continue. Mark the report header that criteria were not linted this run |
| Step 4 did not create a design system (user refused) | Skip this step. Report header: "A3, B1 (no design-system file)" |

Lint results go in the report's **criterion self-check**. They **are not one of the nine checks**. No interface fix target. No user verdict.

## 6. Build the screen map

**Read [CRITERIA.md](CRITERIA.md) in full now.** This step starts the app from wiring fields. Step 8 judges the nine checks from that file.

The map records screens, states per screen, and jumps between screens. The next step maps changed files to screens from it. Step 8's cognitive walkthrough builds paths from it. **It is built in-process. It is not a file. Discard it after the run.**

**Start the app, then attach to it.** Run wiring `launch` (command, working directory, env) with a remote-debugging-port argument on the end, using `launch.debugPort` or `9222`. Secrets are `env:<name>` or `keychain:<name>`; resolve by prefix. Then point the browser automation's attach entry at that port and recognize the main window from `mainWindow` `titlePattern` or `urlPattern`. If `prepare.steps` exists, run them in order for login and test data.

Attaching is what makes an Electron app and a web app the same job here, and it is why [WINDOWS.md](WINDOWS.md) is short: over there the user presses start instead of you, and everything after the attach is identical.

**A successful attach is not four working capabilities.** Attaching to a running instance yields less than owning one from the start, and which parts survive depends on how the app was built. Right after you have the main window, prove each by doing it once:

| # | Capability | How | Pass |
| --- | --- | --- | --- |
| 1 | Accessibility-tree snapshot | One snapshot of the main window | Non-empty, and at least one element with an accessible name |
| 2 | Batch computed style | One `eval` reading `document.body`'s computed style | Non-empty `font-family` |
| 3 | Cropped screenshot | One shot of any visible element | Non-empty bytes |
| 4 | Inject the accessibility engine | Inject its whole file, at the path step 2 printed | The engine's window global is readable afterwards |

| Missing | Effect |
| --- | --- |
| 1 Snapshot | **Stop.** No element location. None of the nine can run |
| 2 Computed style | Skip A1 and A3. Run the other seven |
| 3 Screenshot | Skip no check. B2 question 2 judges from the structured visual-salience numbers alone, and that finding notes there was no screenshot |
| 4 Accessibility engine | Skip A2. Run the other eight |

Skipped check ids go in the report header "Skipped this run". **A missing capability makes a partial QA, and the report says so.**

Three sources merge into one map. Union, not exclusive:

| Source | How | Contributes |
| --- | --- | --- |
| Code extract | Read routes, state machines, conditional-render branches | Baseline screens and jumps. **Record each file path you read into that screen node's `source-files` array** — the next step uses it |
| Runtime probe | Walk reachable paths from the main window | Jumps code does not show, and reachability |
| Usability criteria | States named in this product's usability criteria | States the probe cannot reach without special conditions |

The same state from several sources becomes one node, recording which sources hit it. **Reachability is runtime probe only:** probed states are reached; states only in the other two sources are unreached. Keep unreached states in the map. Do not delete them.

**What you can reach depends on the wiring file.** Empty, loading, error, and permission states enter the check when `prepare.steps` can reach them. What it cannot declare (fault injection, several permission identities, resetting data mid-check) becomes one coverage-report line — that is the product's own test-fixture work.

Unreached states go in the **coverage report**, one line per state name and why. They do not drive edits. They do not enter user verdicts.

## 7. Scope

**Three levels. The user's tag picks the level. No tag is the default.**

| Level | Tag | How scope is computed | When |
| --- | --- | --- | --- |
| **this-change** | none (default) | `git diff HEAD~1...HEAD --name-only` | Just committed; a quick check |
| **this-task** | `this-task` | `git diff $(git merge-base HEAD <parent>)...HEAD --name-only` | A task has landed; before handoff |
| **full** | `full` | Every screen and state in the map. Ignore git | First landing, or before Windows |

`<parent>` is the branch this branch was created from. Several long-lived branches: ask once. Do not guess. One main branch: use it.

**Changed files become screens.** File F maps to every screen node whose `source-files` contains F. That is a lookup in the map from the previous step, not another code scan.

**If the scope maps to zero screens, say so and stop.** "This commit touched no interface files. Tag `this-task` or `full` and call me again." Someone who did not touch the interface did not arrive here by accident — ask which scope they meant, rather than picking one for them.

`HEAD~1` missing (first commit on the branch) is the same answer: say it, ask for a tag.

**All nine checks run at every level.** The level only chooses which screens they act on.

## 8. Run the checks

**Run all nine, collect every result, then go to step 9.** Do not fix while checking: an A3 token edit would change what B1 sees, and the report would not match the interface the user opens.

Per-check rules are in [CRITERIA.md](CRITERIA.md). Method and dispatch for B2, B3, B4 are in [SEMANTIC.md](SEMANTIC.md). Read that file in full before those three.

**Primary input is structured data, not screenshots.** Four sources, all from a browser session driven by the browser automation (step 2 says where it lives):

| Input | Command | Feeds |
| --- | --- | --- |
| Accessibility-tree snapshot | `snapshot` | Element location; all of class B |
| Computed style and layout box | `eval` returning JSON for a batch of elements at once | A1, A3 |
| Runtime CSS custom properties | `eval` over `document.documentElement`'s computed style | A3 implementation-layer compare |
| Renderer console | `console` | A4 |

**Add `--raw` to anything you parse.** Without it the output carries page status and a snapshot section, and the JSON you meant to read is buried in prose.

The accessibility snapshot has roles and accessible names only. No class, test id, wrapper, or inline style. Elements come back as refs (`e5`), and every later command takes that ref. The same method covers native DOM, React, and web apps. No per-framework adapter.

**Batch, do not loop.** One `eval` that returns an array for every candidate costs one round trip; one `eval` per element costs hundreds, and a screen full of elements is where a run stops being worth waiting for.

**A2:** run a page script that injects the accessibility engine's whole file (step 2 printed its path) and calls its analyze entry. Each violation is one A2. The browser automation's run-code entry takes a file, which is how the injection and the call travel together.

**Five numeric fields** (used by `interactive elements` and B2 question 2):

| Field | How |
| --- | --- |
| In first screen | Element `getBoundingClientRect` intersects the viewport |
| Size | `getBoundingClientRect` width and height, px |
| Contrast | WCAG contrast of foreground against actual background |
| Occluded | `elementFromPoint` at the element's center is not the element and not a descendant |
| Stacking | `z-index` of the first ancestor that forms a stacking context |

Screenshots only in two cases, **cropped to the relevant region, never full screen**: cognitive-walkthrough question 2, and when you must show the user evidence.

## 9. Dispose and report

Class A produces violations: **edit and commit them alone**. Class B produces findings: **report only, wait for a verdict**.

**Read [VERDICTS.md](VERDICTS.md) in full now.**

| Case | Action |
| --- | --- |
| Report given to the user; sections 2 and 3 have items to judge or answer | Wait for per-item verdicts and the "same thing?" answers in section 3. After they finish, write verdicts into usability criteria as [VERDICTS.md](VERDICTS.md) specifies, then report the final result once more |
| Report given to the user; sections 2 and 3 are empty | Nothing for them this run. The report ends the run |
| Called by `prototype` or `code-review`, and the user already judged | Hand the report back to the caller |

## Platform

The nine steps above are the Mac side: the skill starts the app and runs the whole flow.

**On Windows, read [WINDOWS.md](WINDOWS.md) in full first.** The user must be present and start the app once. Step 6's start becomes a connect to the debug port they opened. The other eight steps stay the same.
