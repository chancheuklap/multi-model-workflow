# Generate and prove

When you need e2e instructions, run `npx e2e guide <topic>`: `writing-tests`
for writing tests, `running` and `debugging` for running and reading results.
It prints the same text from the version installed in this repository.
Skip the `agent`, `mcp`, and `explore` material.
Do not install the e2e skill in the product repository or on a host, or use
e2e's `init` command. Its description invites automatic selection at worker
and reviewer startup, and its body promotes model-driven actions, remote
control, and exploratory testing. MMW keeps a read-only copy of it at
`upstream/e2e/` for comparison; no host loads that copy.

Use the existing product or settled standalone prototype and the caller's scope, branch and authority. Reuse the caller's environment and matching proof. When runtime tools are missing, read this skill's `references/prepare-environment.md`, complete that method, then resume the interview. Follow the steps below; missing prototype code returns to the design caller instead of being treated as a completed proof.

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

For a new project without code, read the **prepare-ui-acceptance** skill's `references/new-design.md` for its standalone launch and pending product proof; the product launch is proved by the first implementation smoke ticket. For an existing
product:

If the checkout does not build or start as-is, fix that first or report it
precisely before generating. A skill written against a broken base teaches
wrong steps. An irrelevant missing asset (a static dir the API never
serves, a sample config) may be created by the generated skill, marked as
verification scaffolding and removed in Cleanup.

An existing `verify-<product>/` is read before anything is written. Keep its
SKILL.md and feature files, add the features the map lacks, and change an
existing file only where the app contradicts it.

## 2. Build the recipe and feature map

Before writing, record the checkout's existing changes with `git status` and
`git diff`. Preserve those changes throughout generation and commit only this
run's changes, using selective staging when a file already had edits.

Install any missing `e2e` and `@e2e-dev/web` packages in the product repository's `devDependencies`
with its package manager. When the repository has no package manager, put them
in `tests/e2e/<product>/package.json` with its lockfile. Use
`npm ci --prefix tests/e2e/<product>` and
`npm exec --prefix tests/e2e/<product> --` in CHECK lines. The default tier of
`scripts/check` never selects `tests/e2e/`; only its `--all` step
`e2e-<product>` runs those tests.
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

Read `references/example/verify-notes.SKILL.md` for a complete generated
skill, alongside the config, test, and feature file in that directory.

Read every entry in `references/known-issues.md` during generation. Copy each
applicable entry into the generated skill or product environment tool at the
place the entry names.

| Section | Holds |
| --- | --- |
| Read first | Name `npx e2e guide <topic>` with `agent`, `mcp`, and `explore` skipped, config `tests/e2e/<product>/e2e.config.ts`, tests `tests/e2e/<product>/`, and `features/`. Show the feature header format: `# <feature name>`, `Route: <route or entry>`, `Tests: <file>, <file>, …` on three lines |
| Launch | Call **principle-clean-up-owned-resources** before starting resources. The exact invocation of the product environment tool and how readiness shows. Launch only calls that tool. Use the environment tool returned by Prepare environment when the product lacked one. Launch must reach a usable state from an empty data dir, including any migrations. Ready means usable, not just that a process answers. Say which ports and env the command needs. The product target uses the real local back end. Include both isolation layers and the complete CHECK line described below |
| Doctor | One read-only check that answers "is this instance worth driving?". For a Docker Compose back end, first check that Docker is running and the stack is reachable. `npx e2e list --config tests/e2e/<product>/e2e.config.ts` loads the config and prints every test-target pair without starting anything, so a config error or unsupported Node version shows here first. Then run the smoke test, a model-free test that opens the app and pins one landmark, on `--target product` with the same config. Exit `0` means the app starts, the engine runs, and the landmark renders. No smoke test in the project: write `tests/e2e/<product>/smoke.e2e.ts` now. For a signed-in app, use an ordinary signed-in smoke test that consumes a named session with saved login state. Selecting it runs setup and checks that the session restores and a signed-in landmark renders. Running a setup file alone selects no test and exits `NO_TESTS`. Include a known local failures table with symptom, cause, and remedy. Lines that work around a product defect name its product ticket and are removed when it is fixed. Run Doctor only to investigate a failure |
| Drive | Scripted: name the test under `tests/e2e/<product>/` and the credentials and sessions a signed-in drive starts from. For writing or changing tests, name the test-audit skill rather than copying its rules. Check locators by running the smoke test or this test and reading its `trace.md`; test against `design` when writing in the day. During maintenance, walk a feature without tests with the control-ui skill |
| Evidence | What a proof keeps and where. Every run writes `.e2e/report.json`; a failed test gets `.e2e/results/<test>/trace.md`, `--trace on` gives one to passing tests too (topic `running`), `app.screenshot('<name>')` saves a named frame (topic `writing-tests`). The next run clears `.e2e/results/`, Doctor included, so a proof that must outlive it runs with `--output .e2e/proof/<name>` or its attempt directory is copied out before anything else runs. State the product-specific evidence locations |
| Cleanup | State that the e2e runner stops the app it started; name any remaining teardown commands, disposable state (test accounts, scaffolding), and evidence paths |
| Rules | Do not connect to production servers, including SSH just to read files. Do not change main-branch code. Use test accounts, test licenses, local test servers and databases, and PC test machines wherever needed. Name credentials here, never passwords. External paid APIs are tested features too; call them |
| Helpers | Any script the skill ships is executable and its invocation is in the skill body. A helper the reader has to reverse-engineer is not a helper. Most projects need none; the e2e CLI is the helper |

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

Add an `e2e-<product>` step to the repository's `scripts/check`, selected only
by `--all`, never by changed paths in the default tier. Use Launch's dependency
install and preparation that `app.command` does not perform, including a build
when needed. Then run every e2e test against `product`, without a file filter:

- Root e2e package: `npx e2e run --config tests/e2e/<product>/e2e.config.ts --target product`.
- Nested e2e package: `npm exec --prefix tests/e2e/<product> -- e2e run --config tests/e2e/<product>/e2e.config.ts --target product`.

In the generated skill, name the **test-audit** skill at the entry for writing,
changing or diagnosing tests. Keep common testing rules there rather than
copying them into each product's Rules or Evidence section.

Read `references/feature-map.md` and write or reuse the mapped feature's description and Proof now. Finish the usable product skill and config before preparing its test. The recipe, config and Proof are inputs to the next step, not files the caller must already have.

## 3. Prepare the first test

Reuse a matching prepared test and its baseline evidence. For a missing mapped UI test, call the **prepare-ui-acceptance** skill with the actual current behavior or settled design, the draft product skill, config and feature Proof. It uses those drafts to prepare this generation's proving test and returns here. For an API without a UI, write the fixed HTTP test with the **test-audit** skill and the installed e2e writing guide.

Use a settled repair requirement and its reproduction, current behavior for a pin, or the confirmed winner and final interface contract for a new design. Update the API fake to that contract before tests. An unresolved UI decision returns to the design caller. Generation of an existing product's stable behavior does not wait for a separate new design.

Done when a mapped feature has its fixed-step test, registration, complete command and evidence appropriate to that baseline. The generated method remains a draft until the next step proves it.

## 4. Prove the generated skill before handing it over

Apply **principle-clean-up-owned-resources** throughout the proof run. Read the complete generated SKILL.md and follow its instructions end to end once, from a shell in the project. Reuse this generation's matching execution evidence where it already proves a step.

1. Install the browser, then Doctor: the `npx e2e list` call the skill names,
   then the smoke test; both include the product's config and exit `0`.
   For a new project without code, run list and smoke against `design`;
   record the first implementation smoke ticket as the pending proof of the product
   launch.
2. Drive one mapped feature through its test file. One is enough; the map
   exists so later runs cover the rest. Use the prepared test from the previous step, checking its actual result and `trace.md`.
   For a feature present only in the prototype, run the same test against both targets:
   design passes and product fails for the missing feature. Without product
   code, prove this feature on design and record the pending product proof.
3. Run and measure the entire Launch CHECK line once in a fresh checkout,
   including dependency install, preparation, cold back-end startup, and tests.
   Write `TIMEOUT:` only when that total exceeds 600 seconds. Without product
   code, measure the design CHECK and leave the product CHECK to the smoke ticket.
4. Cleanup, then confirm the evidence still exists at the named location.
   A cleanup that eats the proof fails this step.

For the measurement above, use the product CHECK when implementation exists, or the design CHECK when product code does not yet exist. Measure the entire line in a fresh checkout: dependency install,
preparation, cold back-end startup, and the test run together. Only when it
exceeds 600 seconds, write `TIMEOUT: <seconds>` from that measured time, in
the format of the **to-tickets** skill's `references/ticket-format.md`. TIMEOUT governs
the whole CHECK, including cold back-end startup in a new checkout.

Fix a broken launch, config or recipe. Judge the target behavior against its declared baseline: a smoke test that passes and a repair test that reproduces the agreed bug can prove the method works. A missing-feature product failure is likewise expected when design passes. Keep that failure as evidence for implementation, rather than fixing the product or weakening the test to make generation green. A generated skill that was never executed is a draft, not a deliverable.
If you proved it in a stand-in for the real target (a container in place of a
fresh VM, a local stack in place of a remote one, Mac development mode in place
of the shipped app), list every setup step the stand-in did that the target
will not. Those steps stay unverified until a run on the real target covers them.

Commit the generated skill, feature map, the relative
`.claude/skills/verify-<product>` link when created, root `.gitignore` line, tests and
config under `tests/e2e/`, dependency manifest and lockfile changes, and the
`e2e-<product>` step in `scripts/check`. When
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
at night. Run a whole-product maintain-verification-skill pass only when the owner requests it; an affected-feature lookup returns its list without maintenance. Keep verification assets read-only during a night. For a new feature, use **prepare-ui-acceptance** to update its description and tests. Run this method only for a missing reusable product skill or required launch and drive capability; the interview says how an existing map is treated. Return matching prepared acceptance to the caller so it is not written or proved again. Name any isolation prerequisite, the first
implementation smoke ticket proving a new project's product launch and reachable home
page, and the setup steps still unverified on the real target.

## Rules

- Generate from what you observed. A section that could apply to any app
  is not finished.
- One sentence from the e2e skill beats a paragraph of your own. Link the
  topic.
- Never put a secret in the generated skill or the map. Name the
  credential (topic `setup`).
