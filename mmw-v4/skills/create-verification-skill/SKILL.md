---
name: create-verification-skill
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Create a verification skill

A coding agent that changes an app should be able to prove the change the
way a user would see it. This skill writes that proof recipe for one
project as a skill, `.agents/skills/verify-<product>/`, built on e2e. The
config launches the app, fixed-step tests pin what must hold, and
`.e2e/` keeps the evidence. Write
the output for the next agent, not for a human. It will be read cold,
mid-task, by an agent that has never seen the app.

When you need e2e instructions, run `npx e2e guide <topic>`: `writing-tests`
for writing tests, `running` and `debugging` for running and reading results.
It prints the same text from the version installed in this repository.
Do not copy the e2e skill into the product repository or MMW, or use e2e's
`init` command. Its description invites automatic selection at worker and
reviewer startup, and its body promotes model-driven actions, remote
control, and exploratory testing.

## 1. Interview the repo, not the user

Answer these from the codebase and ask the user only what you cannot
observe.

| Question | Where the answer is | What it decides |
| --- | --- | --- |
| Surface | What a user touches. A web UI, an iOS or Android app, an API | One skill per primary surface; name the others for a later run. Web goes through `@e2e-dev/web`, iOS and Android through `@e2e-dev/mobile`. An API with no UI still gets a `web()` target with `app.url` and `app.command` so the runner starts it, and its tests take only `app` and use `fetch` (topic `writing-tests`). For Electron, use the browser provider described below. A non-Electron native desktop app has no e2e engine yet, say so and stop |
| Run | The documented dev command, its ports, env vars, seed data, auth | The target's `app.command` (topic `setup`). A dev server that compiles a route on first visit reads as broken to an agent, so prefer a production build command when the repo has one |
| e2e state | `tests/e2e/<product>/e2e.config.ts`, the `tests` glob, `e2e` in `package.json`, and any Playwright or Cypress suite | Install the packages and write the config as below. An existing Playwright or Cypress suite is the best source of locators, data setup, and sign-in steps; read it. Configure no model. A config with no model runs the deterministic steps, and nothing else |
| Observe | The trace page, screenshots, the report, and what the app leaves behind in files, rows, sent messages, logs | The side-effect stores the Evidence section names. Find them now |
| Isolate | Can each run have its own port and data directory, and each checkout its own back-end stack? | Both layers are required in Launch, as below. If either cannot hold, open a prerequisite ticket before this product gets UI tickets |
| Name | The package name or the repo name; if `design/<x>/` or `verify-<x>` exists, use x | `<product>` in `verify-<product>`, lowercase, no scope. A name mismatch makes setup-mmw report a missing `verify-<x>` |

If the checkout does not build or start as-is, fix that first or report it
precisely before generating. A skill written against a broken base teaches
wrong steps. An irrelevant missing asset (a static dir the API never
serves, a sample config) may be created by the generated skill, marked as
verification scaffolding and removed in Cleanup.

An existing `verify-<product>/` is read before anything is written. Keep its
SKILL.md and feature files, add the features the map lacks, and change an
existing file only where the app contradicts it.

## 2. Generate the skill

Install `e2e` and `@e2e-dev/web` in the product repository's `devDependencies`
with its package manager. The CHECK installs dependencies in an empty checkout;
the repository's lockfile pins the versions, and collaborators without MMW can
run them. The packages have no post-install script. Write
`tests/e2e/<product>/e2e.config.ts` yourself, add `.e2e/` to the root `.gitignore`
without a leading slash so it covers every depth, and run
`npx @e2e-dev/web install chromium` once per machine. Otherwise the first test
run downloads the browser and spends the check's time on it.

Keep each product's config, `*.e2e.ts`, `*-snapshots/`, and `helpers/` under
`tests/e2e/<product>/`, even in a one-product repository. Shared helpers go
under `tests/e2e/helpers/`. e2e uses the config directory as its project root;
test paths and `.e2e/` resolve there. Every project command therefore includes
`--config tests/e2e/<product>/e2e.config.ts`. Without it, the config is not found;
it does not select another product. Both targets set `command.cwd` back to the
product root because the launch working directory also defaults to the config
directory.

Define two targets with no model configuration: `product` runs the real product
against its real local back end; `design` serves `design/<product>/` through a
local static server on port 0, not a local-file URL. Run `--target design` only
when writing tests in the day or maintaining them. At night run only
`--target product`, so a design edit not yet pulled cannot fail the night on
the design instead of the product.

Write `.agents/skills/verify-<product>/SKILL.md` with YAML frontmatter.
`name: verify-<product>` and `description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.`
Without frontmatter the skill never registers. When the project has
`.claude/skills/`, link it with a relative symlink `.claude/skills/verify-<product>`
to `../../.agents/skills/verify-<product>`. Every section says what the interview
found, no placeholders.

When the design package has a feature the product does not yet have, including
all features of a new project without code, open
`references/tests-from-design.md` to write its feature file and tests.

| Section | Holds |
| --- | --- |
| Read first | One line naming `npx e2e guide <topic>`, config `tests/e2e/<product>/e2e.config.ts`, and test directory `tests/e2e/<product>/` |
| Launch | The exact command that starts the app for verification and how readiness shows. Launch must reach a usable state from an empty data dir, including any migrations. Ready means usable, not just that a process answers. The product target uses the real local back end. Include both isolation layers and the complete CHECK line described below |
| Doctor | One read-only check that answers "is this instance worth driving?". For a Docker Compose back end, first check that Docker is running and the stack is reachable. `npx e2e list --config tests/e2e/<product>/e2e.config.ts` loads the config and prints every test-target pair without starting anything, so a config error or unsupported Node version shows here first. Then run the smoke test on `--target product` with the same config. Exit `0` means the app starts, the engine runs, and the landmark renders. No smoke test in the project: write `tests/e2e/<product>/smoke.e2e.ts` now. A signed-in app's auth doctor is its session setup test. Run Doctor only to investigate a failure |
| Drive | Scripted: a test under `tests/e2e/<product>/`, using `screen` to find elements by roles, visible names, and labels (topic `writing-tests`). Name the credentials and sessions a signed-in drive starts from. Check locators by running the smoke test or this test and reading its `trace.md`; test against `design` when writing in the day. During maintenance, walk a feature without tests with the control-ui skill |
| Evidence | What a proof keeps and where. Every run writes `.e2e/report.json`; a failed test gets `.e2e/results/<test>/trace.md`, `--trace on` gives one to passing tests too (topic `running`), `app.screenshot('<name>')` saves a named frame (topic `writing-tests`). The next run clears `.e2e/results/`, Doctor included, so a proof that must outlive it runs with `--output .e2e/proof/<name>` or its attempt directory is copied out before anything else runs. State the proof standards (below) |
| Cleanup | What to tear down. The runner stops the app it started. Never kill by process name; stop what you started. Cleanup removes instances and scratch state (test accounts, scaffolding), never the evidence; name where the evidence is |
| Rules | Do not connect to production servers, including SSH just to read files. Do not change main-branch code. Use test accounts, test licenses, local test servers and databases, and PC test machines wherever needed. Name credentials here, never passwords. External paid APIs are tested features too; call them. For desktop products set `workers: 1` |
| Helpers | Any script the skill ships is executable and its invocation is in the skill body. A helper the reader has to reverse-engineer is not a helper. Most projects need none; the e2e CLI is the helper |

Launch has two hard isolation layers. Each product run owns port 0 and a fresh
data directory. `workers` limits tests inside one run, not two tickets' runs.
Each checkout owns its back-end stack. The launch command calls an ensure
script: first remove stacks whose checkout no longer exists, then check this
checkout's stack, reuse it when reachable, and start it only when unreachable.
Runs in the same checkout share that stack; the next ensure call from any
checkout collects stacks of deleted checkouts. This is not a registry or a
lease, just separate stacks per checkout. Show the ensure script's invocation
in Launch and ship it as a Helper.

If ports or data directories are fixed, or the stack cannot be separated by
checkout, open a prerequisite ticket with only `## Problem`, labelled
`needs-triage`, as the mmw-mode skill's `references/ticket.md` `## Opening a ticket`
step 1 says. This product gets no UI ticket until that prerequisite lands.
Record the prerequisite in Hand over.

For desktop Electron, the product target uses e2e's browser provider with
`scope: 'attempt'`. Start a fresh Electron for each test with debugging port 0
and a temporary user data directory. Read the debugging port from that
directory's `DevToolsActivePort`, and close that Electron after the test.
Electron cannot open a new browser context, so e2e rejects passing the same
Electron to a second test. When the Electron main process starts the back end,
put its database in this run's own directory, shared throughout the run.
The design target remains a static server and browser, without Electron.

Launch gives the entire CHECK line for a ticket to copy. For example:

```bash
pnpm install --frozen-lockfile --silent && npx e2e run <file> --config tests/e2e/<product>/e2e.config.ts --target product --trace on --output .e2e/<test file name>
```

Use the repository's own dependency install first: claim-time checks run in a
new checkout with nothing installed. Add any preparation the target's
`app.command` does not perform, such as a build, between install and e2e.
Write `<file>` relative to `tests/e2e/<product>/`, for example `search.e2e.ts`.
Writing `tests/e2e/<product>/search.e2e.ts` there selects no test. Put the file
before `--trace`, whose optional value is greedy. `--trace on` leaves a trace
for every run, which Work a ticket's Audit reads without another run.
Each criterion needs its own output: e2e clears the previous results on every
run. `--output .e2e/<test file name>` puts its trace under
`tests/e2e/<product>/.e2e/<test file name>/results/<test>/trace.md`.

A ticket's acceptance tests go in a new test file of their own under tests/e2e/<product>/, and its CHECK line runs only that file.
Register it on the feature file's `Tests:` line. Sharing another ticket's pin
file makes that pin fail for an unrelated reason; two criteria running the
same file overwrite its output. Keep one CHECK for that acceptance file.
Write `TIMEOUT: <seconds>` from the measured cold-start time, in the format of
the mmw-mode skill's `references/ticket.md`: preflight starts a cold back-end
stack in a new checkout.

Proof standards, for the Evidence section: exercise the real user path,
not internal setters or test-only endpoints; capture the action and the
resulting state, not only the final screen; verify side effects (files
written, rows inserted, messages sent) in the stores the interview found;
mock only where a production boundary already isolates the external
system. When the safe path is a dry run or a test mode, verify what it
skips by watching files, network, and refs rather than trusting its name.

## 3. Seed the feature map

Create one file per user-facing feature under
`.agents/skills/verify-<product>/features/`, the top three to five first, from
routes, navigation, commands, or docs. Each file starts with these three lines:

```text
# <feature name>
Route: <route or entry>
Tests: <file>, <file>, …
```

`Tests:` lists the covering files under `tests/e2e/<product>/`, separated by
commas. Each ticket changing this feature adds its own file. A feature without
a test has `Tests: none`. There is no hand-written index or status field:
the header shows test coverage, and unfinished product work belongs only on
tickets. Two branches adding features add separate files, avoiding an index
merge conflict. The opening paragraph and `Sub-features` say what the product
can do. Each feature file has these H2s, from the user's point of view.

| H2 | Holds |
| --- | --- |
| `Sub-features` | What the feature is made of, one line each |
| `How to get to it (user POV)` | Route, navigation, the account it needs |
| `Driving it with e2e` | The test files that pin it and the locators that matter |
| `Proof` | The observable end state that means it works, on screen and in the side-effect store |
| `Gotchas` | What reads as broken but is not; what the local app cannot do |

If the test lacks a precondition that it needs, the test reports a failure and
the reason goes in that feature's `Gotchas`. Never weaken the test to make it pass.

The map is the project's maintained verification source. A proof that drives
one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once, from a shell in the project.

1. Install the browser, then Doctor: the `npx e2e list` call the skill names,
   then the smoke test; both include the product's config and exit `0`.
   For a new project without code, record the first night's smoke ticket as
   the pending proof of the product launch.
2. Drive one mapped feature through its test file. One is enough; the map
   exists so later runs cover the rest. A missing test: write it now from
   the feature file, checking locators by running it and reading `trace.md`.
   For the design-package branch, run the same test against both targets:
   design passes and product fails for the missing feature.
3. Measure cold startup for `TIMEOUT:` and run the entire Launch CHECK line
   once, including its dependency install and preparation.
4. Cleanup, then confirm the evidence still exists at the named location.
   A cleanup that eats the proof fails this step.

Fix what fails, and run Cleanup after every failed iteration too, so
broken attempts do not strand ports and processes. A generated skill that
was never executed is a draft, not a deliverable.
If you proved it in a stand-in for the real target (a container in place of a
fresh VM, a local stack in place of a remote one, Mac development mode in place
of the shipped app), list every setup step the stand-in did that the target
will not. Those steps stay unverified until a run on the real target covers them.

Commit the generated skill, feature map, root `.gitignore` line, tests and
config under `tests/e2e/`, and `package.json` and lockfile changes directly on
the current checkout's project branch, without a ticket. Commit and push before the next
`dispatch.sh open`: ticket checkouts start from `origin`, so local-only files
are unavailable to workers. The `.gitignore` line keeps `.e2e/` output out of
the commit.

## 5. Hand over

Tell the user what landed. The skill path, the features mapped and which
have tests, what the proof run showed, and the evidence paths. Feature files
and e2e tests are written in the day by the ticket-writing steps and read-only
at night. Review them only when the owner names the maintain-verification-skill
skill. Rerun this skill when the app grows a feature the map lacks; section 1
says how an existing map is treated. Name any isolation prerequisite, the first
night's smoke ticket proving a new project's product launch and reachable home
page, and the setup steps still unverified on the real target.

## Rules

- Generate from what you observed. A section that could apply to any app
  is not finished.
- One sentence from the e2e skill beats a paragraph of your own. Link the
  topic.
- Never put a secret in the generated skill or the map. Name the
  credential (topic `setup`).
