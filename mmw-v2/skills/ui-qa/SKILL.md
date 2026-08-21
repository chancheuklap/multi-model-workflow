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
bash scripts/install-deps.sh --check
```

It prints package name, required version, and actual version for the npm dependencies, and whether the external skill is installed. Exit 0 when all four capabilities are present.

**Where each capability lives**, once installed. Names and versions come from `scripts/deps.json`; read the entry, then build its path:

| Capability | Path |
| --- | --- |
| A `command` entry | `scripts/deps/node_modules/.bin/` plus its **bin** field |
| A `source` entry | `scripts/deps/node_modules/` plus its **package** field, then its **source** field |
| The module root, to `require` from a Node script | `scripts/deps` |
| An `external-skill` entry | The host already loaded it. Invoke its **skill** field as a skill |
| A `shared-npx` entry | Run its **invoke** field as written. It is deliberately unpinned — another skill runs the same line, and the two resolving to one copy matters more here than pinning a version |

On non-zero `--check`, install what is missing: `bash scripts/install-deps.sh` for the npm ones, and for the external skill the command its `installedBy` field prints. Then switch on which capability is still missing:

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
npx @google/design.md lint <design-system file from the previous step>
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

Start the app from wiring `launch` (command, working directory, env). Secrets are `env:<name>` or `keychain:<name>`; resolve by prefix. Recognize the main window from `mainWindow` `titlePattern` or `urlPattern`. If `prepare.steps` exists, run them in order for login and test data.

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

| Input | How | Feeds |
| --- | --- | --- |
| Accessibility-tree snapshot | ARIA snapshot from the browser automation | Element location; all of class B |
| Computed style and layout box | Batch `getComputedStyle` and `getBoundingClientRect` on candidates | A1, A3 |
| Runtime CSS custom properties | `getComputedStyle(document.documentElement)` | A3 implementation-layer compare |
| Renderer console | Listen for console and page error | A4 |

The accessibility snapshot has roles and accessible names only. No class, test id, wrapper, or inline style. The same method covers native DOM, React, and web apps. No per-framework adapter.

**A2:** inject the accessibility engine's whole script file (step 2 says where it lives), call its analyze entry, and each violation is one A2.

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
