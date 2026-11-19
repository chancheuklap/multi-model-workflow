---
name: verify-notes
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Verify Notes

This example belongs at `.agents/skills/verify-notes/SKILL.md` in the illustrative
Notes product. It verifies Notes in Chromium against a fresh local instance.

## Read first

For writing, changing or diagnosing tests, use the **test-audit** skill.

Read `npx e2e guide <topic>` for `writing-tests`, `running`, or `debugging`.
Skip `agent`, `mcp`, and `explore`. The config is
`tests/e2e/notes/e2e.config.ts`, tests are in `tests/e2e/notes/`, and the feature
map is `features/` beside this skill. Each feature file opens with three lines:

```text
# <feature name>
Route: <route or entry>
Tests: <file>, <file>, …
```

## Launch

Apply **principle-clean-up-owned-resources** throughout the run.

The config calls the product environment tool:

```bash
bash scripts/dev/notes.sh serve --port {port} --temporary-data
```

The runner supplies a free port. The tool serves a production build, creates a
fresh data directory, and runs migrations before reporting ready. Ready means
`/notes` renders the note list and can create a note. Notes has no separate
back-end stack or accounts. Each run owns its data. Tests in one run share that
database, so the config sets `workers: 1` and disables retries.

`product` runs Notes. `design` uses the same command with `NOTES_PROTOTYPE=1`.
Its mount point renders the prototype at `/notes`. Run `design` when writing
new tests in the day, and only `product` at night. Once the mount point is
removed, `design` is unused and the test stays unchanged.

Notes uses npm and a root lockfile. A ticket copies this CHECK line, replacing
`<file>` with its acceptance file relative to `tests/e2e/notes/`:

```bash
npm ci --silent && npx e2e run <file> --config tests/e2e/notes/e2e.config.ts --target product --trace on --output .e2e/<test file name>
```

## Doctor

Run only to investigate a failure:

```bash
npx e2e list --config tests/e2e/notes/e2e.config.ts
npx e2e run smoke.e2e.ts --config tests/e2e/notes/e2e.config.ts --target product --trace on --output .e2e/doctor
```

`list` loads the config without starting anything. The smoke test opens `/notes`
and checks the `Notes` heading. Exit 0 proves launch, the browser engine, and the
landmark. Notes has no sign-in state to restore.

Known local failures:

| Symptom | Cause | Remedy |
| --- | --- | --- |
| `list` cannot load the config | A config error or missing dependency | Read its diagnostic and run `npm ci` if dependencies are missing |
| The engine cannot start Chromium | Chromium is not installed | Run `npx @e2e-dev/web install chromium` |
| The server exits before ready | The environment tool's build or migration failed | Read `tests/e2e/notes/.e2e/logs/product.log` and repair the reported prerequisite |
| The smoke test cannot find `Notes` | The app did not render its reachable home page | Read the smoke trace and inspect the page before driving further |
| Pinning fails on `product` while `design` passes | The prototype has pinning but the product does not | This is the expected base failure before the pinning ticket lands |

## Drive

`pin-note.e2e.ts` creates a note, then pins it with `Pin Release checklist`.
The feature recipe is `features/pin-note.md`. Notes starts with an empty
note list and needs no credentials.

## Evidence

The ticket's output is under `tests/e2e/notes/.e2e/<test file name>/`.
`report.json` records the run. `--trace on` keeps
`results/<test>/trace.md` for passing tests too. `app.screenshot('pinned-note')`
keeps the comparison frame in that test's attempt directory. A run clears its
own output, so use a separate output directory for proof that must survive it.

Storage is proven by the ticket's back-end tests.

## Cleanup

The runner stops the tool it started. The tool removes its instance and fresh data
directory on exit, including after a failed attempt. Evidence and target logs
live under `tests/e2e/notes/.e2e/`.

## Rules

- Use only the local Notes instance, never a production server.
- Keep test data separate from a user's Notes data.
- Do not change main-branch product code during verification.

## Helpers

None. Launch uses the product's environment tool. e2e is the test runner.
