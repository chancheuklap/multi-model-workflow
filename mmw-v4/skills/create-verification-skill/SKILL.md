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
Skip the `agent`, `mcp`, and `explore` material.
Do not install the e2e skill in the product repository or on a host, or use
e2e's `init` command. Its description invites automatic selection at worker
and reviewer startup, and its body promotes model-driven actions, remote
control, and exploratory testing. MMW keeps a read-only copy of it at
`upstream/e2e/` for comparison; no host loads that copy.

## 1. Interview the repo, not the user

Answer these from the codebase and ask the user only what you cannot
observe.

| Question | Where the answer is | What it decides |
| --- | --- | --- |
| Surface | What a user touches. A web UI, an iOS or Android app, an API | One skill per primary surface; name the others for a later run. Web goes through `@e2e-dev/web`, iOS and Android through `@e2e-dev/mobile`. An API with no UI still gets a `web()` target with `app.url` and `app.command` so the runner starts it, and its tests take only `app` and use `fetch` (topic `writing-tests`). For Electron, use the browser provider described below. A non-Electron native desktop app has no e2e engine yet. A CLI, library, batch job, or desktop frontend whose browser output is only a native-runtime notice also has no supported drivable surface. Stop during this interview, before writing anything. Name the entry point, the engine that cannot drive it, and that no skill was generated |
| Run | The documented dev command, its ports, env vars, seed data, auth | The target's `app.command` (topic `setup`). A dev server that compiles a route on first visit reads as broken to an agent, so prefer a production build command when the repo has one |
| e2e state | `tests/e2e/<product>/e2e.config.ts`, the `tests` glob, `e2e` in `package.json`, and any Playwright or Cypress suite | Install the packages and write the config as below. An existing Playwright or Cypress suite is the best source of locators, data setup, and sign-in steps; read it. Configure no model. A config with no model runs the deterministic steps, and nothing else |
| Observe | The trace page, screenshots, the report, and the action and result visible to the user | The evidence to keep. Storage is proven by the ticket's back-end tests |
| Isolate | Can each run have its own port and data directory, and each checkout its own back-end stack? | Both layers are required in Launch, as below. If either cannot hold, register the prerequisite before this product gets UI tickets |
| Name | The package name or the repo name; if `verify-<x>` exists, use x | `<product>` in `verify-<product>`, lowercase, no scope. |

For a new project without code, use `references/tests-from-prototype.md`; the
product launch is proved by the first night's smoke ticket. For an existing
product:

If the checkout does not build or start as-is, fix that first or report it
precisely before generating. A skill written against a broken base teaches
wrong steps. An irrelevant missing asset (a static dir the API never
serves, a sample config) may be created by the generated skill, marked as
verification scaffolding and removed in Cleanup.

An existing `verify-<product>/` is read before anything is written. Keep its
SKILL.md and feature files, add the features the map lacks, and change an
existing file only where the app contradicts it.

## 2. Generate the skill

Before writing, record the checkout's existing changes with `git status` and
`git diff`. Preserve those changes throughout generation and commit only this
run's changes, using selective staging when a file already had edits.

Install any missing `e2e` and `@e2e-dev/web` packages in the product repository's `devDependencies`
with its package manager. When the repository has no package manager, put them
in `tests/e2e/<product>/package.json` with its lockfile. Use
`npm ci --prefix tests/e2e/<product>` and
`npm exec --prefix tests/e2e/<product> --` in CHECK lines, and exclude
`tests/e2e/` from the repository's own unified checks.
The CHECK installs dependencies in an empty checkout;
the repository's lockfile pins the versions, and collaborators without MMW can
run them. The packages have no post-install script. Write
`tests/e2e/<product>/e2e.config.ts` yourself when absent; read an existing
config and change only what the product or these requirements contradict.
Add `.e2e/` to the root `.gitignore` only when missing,
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
against its real local back end; `design` runs the same launch command with an
environment variable that enables the prototype mount points at the final routes.
This applies to Electron too. For a new project without code, `design` launches
the standalone prototype page with the effort's chosen stack.
Run `design` while writing tests in the day. At night run only `product`.
After the mount points are removed, `design` is unused and tests stay unchanged.

Write `.agents/skills/verify-<product>/SKILL.md` with YAML frontmatter.
`name: verify-<product>` and `description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.`
Without frontmatter the skill never registers. When
the project has `.claude/skills/`, link it the way `e2e init` does, a
relative symlink `.claude/skills/verify-<product>` to
`../../.agents/skills/verify-<product>`. Every section says what the interview
found, no placeholders.

When writing e2e tests, use `references/tests-from-prototype.md`. It holds the
test-writing rules for both existing behavior and features present only in the
prototype. Read `references/example/verify-notes.SKILL.md` for a complete generated
skill, alongside the config, test, and feature file in that directory.

Read every entry in `references/known-issues.md` during generation. Copy each
applicable entry into the generated skill or product environment tool at the
place the entry names.

| Section | Holds |
| --- | --- |
| Read first | Name `npx e2e guide <topic>` with `agent`, `mcp`, and `explore` skipped, config `tests/e2e/<product>/e2e.config.ts`, tests `tests/e2e/<product>/`, and `features/`. Show the feature header format: `# <feature name>`, `Route: <route or entry>`, `Tests: <file>, <file>, …` on three lines |
| Launch | The exact invocation of the product environment tool and how readiness shows. Launch only calls that tool. If the product has none, build it in the product repository during generation, as below. Launch must reach a usable state from an empty data dir, including any migrations. Ready means usable, not just that a process answers. Say which ports and env the command needs. The product target uses the real local back end. Include both isolation layers and the complete CHECK line described below |
| Doctor | One read-only check that answers "is this instance worth driving?". For a Docker Compose back end, first check that Docker is running and the stack is reachable. `npx e2e list --config tests/e2e/<product>/e2e.config.ts` loads the config and prints every test-target pair without starting anything, so a config error or unsupported Node version shows here first. Then run the smoke test, a model-free test that opens the app and pins one landmark, on `--target product` with the same config. Exit `0` means the app starts, the engine runs, and the landmark renders. No smoke test in the project: write `tests/e2e/<product>/smoke.e2e.ts` now. For a signed-in app, use an ordinary signed-in smoke test that consumes a named session with saved login state. Selecting it runs setup and checks that the session restores and a signed-in landmark renders. Running a setup file alone selects no test and exits `NO_TESTS`. Include a known local failures table with symptom, cause, and remedy. Lines that work around a product defect name its product ticket and are removed when it is fixed. Run Doctor only to investigate a failure |
| Drive | Scripted: a test under `tests/e2e/<product>/`, using `screen` to find elements by roles, visible names, and labels (topic `writing-tests`). Name the credentials and sessions a signed-in drive starts from. If an existing feature lacks accessible names, open a prerequisite ticket to add them before writing its test. Check locators by running the smoke test or this test and reading its `trace.md`; test against `design` when writing in the day. During maintenance, walk a feature without tests with the control-ui skill |
| Evidence | What a proof keeps and where. Every run writes `.e2e/report.json`; a failed test gets `.e2e/results/<test>/trace.md`, `--trace on` gives one to passing tests too (topic `running`), `app.screenshot('<name>')` saves a named frame (topic `writing-tests`). The next run clears `.e2e/results/`, Doctor included, so a proof that must outlive it runs with `--output .e2e/proof/<name>` or its attempt directory is copied out before anything else runs. State the proof standards (below) |
| Cleanup | What to tear down. The runner stops the app it started; a server the user started stays theirs. Never kill by process name; stop what you started. Cleanup removes instances and scratch state (test accounts, scaffolding), never the evidence; name where the evidence is |
| Rules | Do not connect to production servers, including SSH just to read files. Do not change main-branch code. Use test accounts, test licenses, local test servers and databases, and PC test machines wherever needed. Name credentials here, never passwords. External paid APIs are tested features too; call them. Set `workers: 1` when tests in one run share writable state, such as a configuration file or database |
| Helpers | Any script the skill ships is executable and its invocation is in the skill body. A helper the reader has to reverse-engineer is not a helper. Most projects need none; the e2e CLI is the helper |

The product environment tool belongs in its development scripts directory, with
an operating skill for manual use, debugging, diagnosis, and verification. It
provides one command to start the whole local product and one to create test
accounts. Launch calls it rather than shipping environment scripts as Helpers.

It provides both isolation layers: each product run owns port 0 and a fresh data
directory, and each checkout owns its back-end stack and database. `workers`
limits tests inside one run, not two tickets' runs. For a separate back-end
repository, overlay that repository's Compose files. Allocate ports dynamically
and record them in the checkout. Label containers with the checkout path,
collect stacks of deleted checkouts on the next start, and limit the number of
stacks running at once. Reuse this checkout's reachable stack and start it only
when unreachable. Use the stack's existing idempotent lifecycle command so
overlapping calls converge on one stack. If the stack runs checkout code,
readiness must establish that its code is current, not just that a port answers.

If ports or data directories are fixed, or the stack cannot be separated by
checkout, register the prerequisite with the **register-problem** skill. This
product gets no UI ticket until that prerequisite lands.
Record the prerequisite in Hand over.

For desktop Electron, the product target uses e2e's browser provider with
`scope: 'attempt'`. Start a fresh Electron for each test with debugging port 0
and a temporary user data directory. Read the debugging port from that
directory's `DevToolsActivePort`, and close that Electron after the test.
Electron cannot open a new browser context, so e2e rejects passing the same
Electron to a second test. When the Electron main process starts the back end,
put its database in this run's own directory, shared throughout the run.
The design target uses the same Electron launch command with the prototype
environment variable. Native behavior is tested only on `product`.

Launch gives the entire CHECK line for a ticket to copy. For example:

```bash
pnpm install --frozen-lockfile --silent && npx e2e run <file> --config tests/e2e/<product>/e2e.config.ts --target product --trace on --output .e2e/<test file name>
```

Use the repository's own dependency install first: any `CHECK:` may run in a
new checkout with nothing installed. Add any preparation the target's
`app.command` does not perform, such as a build, between install and e2e.
Write `<file>` relative to `tests/e2e/<product>/`, for example `search.e2e.ts`.
Writing `tests/e2e/<product>/search.e2e.ts` there selects no test. Put the file
before `--trace`, whose optional value is greedy. `--trace on` leaves a trace
for every run, which Work a ticket's Audit reads without another run.
Each criterion needs its own output: e2e clears the previous results on every
run. `--output .e2e/<test file name>` puts its trace under
`tests/e2e/<product>/.e2e/<test file name>/results/<test>/trace.md`.

Measure the entire CHECK line in a fresh checkout: dependency install,
preparation, cold back-end startup, and the test run together. Only when it
exceeds 600 seconds, write `TIMEOUT: <seconds>` from that measured time, in
the format of the mmw-mode skill's `references/ticket.md`. TIMEOUT governs
the whole CHECK, including cold back-end startup in a new checkout.

Proof standards, for the Evidence section: exercise the real user path,
not internal setters or test-only endpoints; capture the action and the
resulting state the user sees, not only the final screen. Storage is proven
by the ticket's back-end tests. For request interception, follow
`references/tests-from-prototype.md`. When the safe path is a dry run or a test mode, verify what it
skips by watching files, network, and refs rather than trusting its name.

## 3. Seed the feature map

Create one file per user-facing feature under
`.agents/skills/verify-<product>/features/`, the top three to five first, from
routes, navigation, or docs. Follow
`references/example/pin-note.md` for the feature file. Each file starts with these three lines:

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
merge conflict. Write what the product can do first: the heading, `Route:`, opening paragraph,
`Sub-features`, and `How to get to it (user POV)`. For a UI prototype, write this
before design freeze and commit it before tests on the effort branch or
`fix-<n>`. Take sentences only from the winner prototype, closed decisions, and
`CONTEXT.md`. Each sentence has an identifiable source and describes something
the prototype can demonstrate. Write sentences in the product UI's language;
keep the prescribed headings in English. Do not ask the owner to confirm the
sentences. The owner confirms only the prototype.

When those sources disagree, decisions govern rules, the glossary governs names,
and the prototype governs appearance and interaction. Update a prototype that
lags behind decisions or names. A missing decision that changes the UI goes
through the `prototype` skill's `UI.md` iteration rules, and its answer updates
the prototype. For existing behavior without a new prototype, describe the
current product. Until the feature lands, the project branch's feature map
contains only what the product currently does.

Write `Proof` before tests. Write `Tests:` and `Driving it with e2e` with their
tests in the same commit. Record `Gotchas` when generation, bug fixing, or
maintenance discovers them. All feature files are read-only at night.
Each feature file has these H2s, from the user's point of view.

| H2 | Holds |
| --- | --- |
| `Sub-features` | What the feature is made of, one line each |
| `How to get to it (user POV)` | Route, navigation, the account it needs |
| `Driving it with e2e` | The test files that pin it and the locators that matter |
| `Proof` | What the user sees and can accomplish |
| `Gotchas` | What reads as broken but is not; what the local app cannot do |

If the test lacks a precondition that it needs, the test reports a failure and
the reason goes in that feature's `Gotchas`. Never weaken the test to make it pass.

The map is the project's maintained verification source. A proof that drives
one convenient entry point is incomplete when the map lists others.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once, from a shell in the project.

1. Install the browser, then Doctor: the `npx e2e list` call the skill names,
   then the smoke test; both include the product's config and exit `0`.
   For a new project without code, run list and smoke against `design`;
   record the first night's smoke ticket as the pending proof of the product
   launch.
2. Drive one mapped feature through its test file. One is enough; the map
   exists so later runs cover the rest. A missing test: write it now from
   the feature file, checking locators by running it and reading `trace.md`.
   For a feature present only in the prototype, run the same test against both targets:
   design passes and product fails for the missing feature. Without product
   code, prove this feature on design and record the pending product proof.
3. Run and measure the entire Launch CHECK line once in a fresh checkout,
   including dependency install, preparation, cold back-end startup, and tests.
   Write `TIMEOUT:` only when that total exceeds 600 seconds. Without product
   code, measure the design CHECK and leave the product CHECK to the smoke ticket.
4. Cleanup, then confirm the evidence still exists at the named location.
   A cleanup that eats the proof fails this step.

Fix what fails, and run Cleanup after every failed iteration too, so
broken attempts do not strand ports and processes. A generated skill that
was never executed is a draft, not a deliverable.
If you proved it in a stand-in for the real target (a container in place of a
fresh VM, a local stack in place of a remote one, Mac development mode in place
of the shipped app), list every setup step the stand-in did that the target
will not. Those steps stay unverified until a run on the real target covers them.

Commit the generated skill, feature map, the relative
`.claude/skills/verify-<product>` link when created, root `.gitignore` line, tests and
config under `tests/e2e/`, and dependency manifest and lockfile changes. When
generation is part of a prototype effort, commit these and the product
environment tool on the effort branch so they merge with its PR. Outside an
effort, commit directly on the current checkout's project branch without a
ticket. Commit and push before the next
`dispatch.sh open`: ticket checkouts start from `origin`, so local-only files
are unavailable to workers. The `.gitignore` line keeps `.e2e/` output out of
the commit.

## 5. Hand over

For an unsupported surface, report what you observed and that nothing was written.

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
