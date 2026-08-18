---
name: mmw-prototype
description: Build a prototype to answer a design question. Use when talk cannot decide how something should look or behave, a `wayfinder:prototype` ticket arrives, or the user wants to sanity-check a state model, data shape, or UI.
---

# Prototype

A prototype is a **running asset that answers a question**. The question decides the shape. Write it without tests, extra error handling, or abstractions. The files stay in the repo as a prototype asset, edited in place across rounds, until a walkthrough answers the current question.

`mmw domain path` prints the domain docs to read. Use those terms.

If the question is an external system as it actually behaves under our load, data, or account, invoke `$mmw:mmw-research`. If the question cannot be made concrete enough to walk through, invoke `$mmw:mmw-grilling`, then return.

One question this round. Later rounds edit the same prototype. Do not start a new prototype for a new question. Stop this direction only when a walkthrough shows the whole direction is wrong.

`mmw artifact path prototype --sub README.md` prints the index path. The directory that contains it is this prototype. Add `--name` and `--issue` when the caller passed them. Each other file: `mmw artifact path prototype --sub <path>`. Process shots: `mmw artifact path scratch --sub evidence`.

## Pick a branch

Identify which question this round answers — from the user's prompt, the surrounding code, the existing prototype, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file — free-play buttons plus tabbed guided walkthroughs — that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.
- **Looking at one output is enough** — a payload, a contract, a transform. Write the smallest runnable script, contract sample, or sample data in this prototype. Hand the input and the output to the user. Cover the failures, empty values, and edges the question cares about, not only the happy path.

The branches produce very different artifacts — getting this wrong wastes the round. If two branches fit and the user can answer, ask which this round. If the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic or a script; a page or component → UI) and state the assumption at the top of the prototype and in `README.md`.

## Rules that apply to both

1. **Clearly marked as a prototype.** Write the files where `mmw artifact path prototype` prints. Thin wiring may sit next to the real page or module so context is obvious — but name every file, title, and route so a casual reader can see it's a prototype, not production. For UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure. Keep each host file's wiring to one site, and list every site under `## Mounted wiring` in `README.md`: that list is the only record that this prototype reached production code.
2. **Trivial to run.** A UI prototype starts from one command in the project's task runner — `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it. Write that command or path in `README.md`.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
6. **Capture it when done.** `README.md` is the index of this prototype: the question, how to run it, the walkthrough conclusions in the user's words, the chosen artifacts, rejected constraints, the mounted wiring, and any long-lived evidence. It is not the running prototype. Downstream names `README.md` and reads the files it lists. Write `none` for a field that has none. Reuse is the idea, not engineering completeness — say that above any reusable path. This skill does not fold the prototype into production.

## Walkthrough

The user operates the running prototype and accepts, rejects, or asks for a change. Do not click, choose, or declare the round done for them. Open each page in its own view so they can compare. Wait.

If they ask for a change, edit the same prototype and walk through again.

## After capture

Commit the prototype files and `README.md` this round wrote. Do not commit scratch. Do not create an empty commit.

After a UI round is committed, run `$mmw:mmw-ui-qa`. It does not replace the walkthrough. If it cannot run, continue and say so.

When `$mmw:mmw-wayfinder` or another skill invoked this, return the README path. When the user invoked this, report that path and ask: write a spec, or stop here. If the whole direction is wrong, the README still holds that fact; return the path.
