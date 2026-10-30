## Notes example

Read the **create-verification-skill** skill's `references/example/e2e.config.ts`, `references/example/pin-note.e2e.ts`,
`references/example/pin-note.md`, and `references/example/verify-notes.SKILL.md`
together. They illustrate a Notes app that already creates notes at `/notes`;
pinning is the new feature.

The product's environment tool runs as `bash scripts/dev/notes.sh`. Its `serve` command
accepts `--port` and `--temporary-data`, creates a fresh data directory, runs
migrations, and removes its instance and scratch data on exit. It serves a
production build. `NOTES_PROTOTYPE=1` selects the prototype at `/notes` through
the same command, including the real backend for existing note creation. The
prototype's new pin interface uses an API fake seeded from the environment tool.
This example has no external back-end stack and no accounts.

Both targets create `Release checklist`, pin it, check the visible result, and
capture `pinned-note`. The config disables retries because data is fresh per
run, not per attempt. Rerun the CHECK for fresh data after a failure. These are
illustrative files, not a runnable Notes product shipped with this skill.
