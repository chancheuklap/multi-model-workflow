# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repository root, or
- **`CONTEXT-MAP.md`** at the repository root if it exists — it points at one `CONTEXT.md` per context. Read each one relevant to the topic. In this repository the map is the root `CONTEXT-MAP.md` and the contexts it points at are `docs/contexts/<name>/CONTEXT.md`.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in. In multi-context repos, also check for context-scoped ADRs beside each context's `CONTEXT.md`; this repository keeps every ADR system-wide in `docs/adr/`.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The domain-modeling skill (reached via grill-with-docs and improve-codebase-architecture) creates them lazily when terms or decisions actually get resolved.

## File structure

Single-context repo (most repos):

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

Multi-context repo (presence of `CONTEXT-MAP.md` at the root): the map names the contexts and how they relate, and each context has its own `CONTEXT.md`. Where a context's code sits in one directory, its `CONTEXT.md` usually sits there too, with context-scoped ADRs beside it.

This repository is multi-context, and its context files sit apart from the code they describe:

```
/
├── CONTEXT-MAP.md                     ← the map: six contexts and how they relate
├── docs/
│   ├── adr/                           ← every ADR, all of them system-wide
│   └── contexts/
│       ├── toolbox/CONTEXT.md         ← MMW as a repository and install target
│       ├── tickets/CONTEXT.md         ← what a spec and a ticket are
│       ├── ticket-run/CONTEXT.md      ← one ticket from claim to close
│       ├── night/CONTEXT.md           ← dispatching sessions onto tickets
│       ├── ui-acceptance/CONTEXT.md   ← design side, screen contract, judges
│       └── task-board/CONTEXT.md      ← the local browser board
└── mmw-v2/
```

The contexts live under `docs/contexts/` rather than beside their code because the code of most of them is a skill directory, and a skill directory is symlinked whole into every host: it holds only what the agent holding the skill reads or runs. A `CONTEXT.md` placed beside that code would ship to every host with the skill and be read by agents who never asked for it. `docs/adr/` stays system-wide: there are no context-scoped ADR directories here.

## Use the vocabulary in `CONTEXT.md`

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to the synonyms listed on its `_Avoid_` lines.

A definition in `CONTEXT.md` that disagrees with the file its `_Home_` line names is wrong: fix `CONTEXT.md`.

An attribute that can be had by reading the `_Home_` file itself — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated in `CONTEXT.md`: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest. So an entry saying less than its `_Home_` is not a defect; saying more is.

Updating a `CONTEXT.md` systematically is that rule applied entry by entry: open each entry's `_Home_` and rewrite the entry from what that file says now, never from memory of what the term used to mean; a term whose `_Home_` no longer defines it moves to the file that does, or is dropped.

If the concept you need isn't in `CONTEXT.md` yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for the domain-modeling skill).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
