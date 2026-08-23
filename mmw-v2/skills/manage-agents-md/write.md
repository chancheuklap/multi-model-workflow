# Write

One format for every `AGENTS.md` this skill produces. You write from the merged survey list and the maintainer's answers, one file at a time, root first.

## Root files

`AGENTS.md` is the only body, 150 lines at most. `CLAUDE.md` beside it is a bridge: the line `@AGENTS.md`, plus any other `@import` lines the repository already had. No symlinks.

Sections, in this order. Use only the ones that have content; a section with nothing to say is left out, not left empty.

1. **Identity** — one to four lines, from the maintainer's answers, not from the manifest: who it serves and what it solves; what stage it is at and whether real users, data, or money run through it; what this repository is not (split-out repositories, frozen directories); how an agent should treat the repository's contents. The tech stack is not identity.
2. **Package manager and runtime** — one or two lines.
3. **Commands** — only commands whose meaning `--help` and the manifest's scripts do not give; prefer file-scoped test, lint, and typecheck commands. A table when there is more than one.
4. **References** — two columns, "Need" and "File", repository-relative paths to documents that already exist: setup, architecture, API, security, release, policy.
5. **Conventions and pitfalls** — one rule per bullet: generated files and the command that regenerates them; fixed orderings; which of two records wins; problems debugged more than once; deliberate unconventional choices and why; differences between machines and environments; legacy areas. Rationale only where it prevents a likely mistake.
6. **Task-scoped sections** — guidance that matters only for one kind of work, each wrapped in `<important if="...">` (below).
7. **The subdirectory sentence**, verbatim:
   ```
   Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
   ```
   Hosts that load nested files on their own lose nothing; hosts that stop at the working directory depend on it.

Not in a root file: a directory map, environment variables, the list of installed skills, commit attribution, metadata headers, an index of nested files.

## Nested files

`AGENTS.md` with the body, `CLAUDE.md` with `@AGENTS.md`. The body file is always named `AGENTS.md`.

A directory gets a nested pair when the survey or the maintainer gives one rule that holds only there and the root does not carry. One rule is enough.

Sections: a scope sentence (what the directory owns and does not own); rules, one per bullet, requirements and prohibitions mixed; then only if present, commands that apply only here and references to documents that cover only here.

Not in a nested file: a line pointing back to the root, `<important if>` blocks, skill ownership, metadata headers.

Keep narrower files shorter than root files; a nested file says only what differs from the root.

## Wrapping in `<important if>`

### Foundational context stays bare, domain guidance gets wrapped

Not everything should be in an `<important if>` block. Context that is relevant to virtually every task — identity, runtime, commands, references, conventions — should be left as plain markdown at the top of the file. This is onboarding context the agent always needs.

Domain-specific guidance that only matters for certain tasks — testing patterns, API conventions, state management, i18n — gets wrapped in `<important if>` blocks with targeted conditions.

The rule: inline what every task needs, and wrap what only some tasks reach.

### Conditions must be specific and targeted

Bad — overly broad conditions that match everything:
```
<important if="you are writing or modifying any code">
- Use absolute imports
- Use functional components
- Use camelCase filenames
</important>
```

Good — each rule has its own narrow trigger:
```
<important if="you are adding or modifying imports">
- Use `@/` absolute imports (see tsconfig.json for path aliases)
- Avoid default exports except in route files
</important>

<important if="you are creating new components">
- Use functional components with explicit prop interfaces
</important>

<important if="you are creating new files or directories">
- Use camelCase for file and directory names
</important>
```

The tag acts on a host whose own system prompt uses this XML pattern; a host without it reads the tag as text, which costs a line and changes nothing.

## Writing rules

- Use headings, bullets, and tables; avoid paragraphs.
- Use repo-relative paths; avoid vague references like "see docs".
- Reference existing docs/specs/policies instead of copying them.
- List exact external files for setup, architecture, API specs, security, release, and policy docs when they exist.
- Prefer file-scoped test/lint/typecheck commands; include full builds only when no narrower command exists.
- Put commands in tables when there is more than one.
- Keep one rule per bullet.
- Keep rationale out unless it prevents a likely mistake.
- Do not restate linter, formatter, or typechecker config.
- Do not list installed skills or plugins.
- Do not include generic quality slogans.

State each rule as the behaviour to perform. A prohibition stays only where no positive phrasing exists, and then sits next to the positive target.

## Pointers

A reference-table row and the subdirectory sentence are context pointers: the wording decides whether the agent reaches the file.

- **Front-load the leading word**: the pointer is where it does its triggering work.
- **One trigger per branch.** Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.
- **Cut identity the body already carries.**

## Output structure

```
# AGENTS.md

[identity, one to four lines]

## Package manager and runtime
[one or two lines]

## Commands
[table]

## References
| Need | File |
|---|---|

## Conventions and pitfalls
- [one rule]

<important if="<specific trigger for domain area 1>">
[guidance]
</important>

... more domain sections ...

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
```

Done when every file named in the survey list's "place" column exists with its bridge, every line in it traces to a survey entry or a maintainer answer, and the root is within 150 lines.
