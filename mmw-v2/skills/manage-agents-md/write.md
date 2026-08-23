# Write

Branches **create** and **rewrite**. You have `survey-list.md`, with the maintainer's answers appended. You now write the files, root first, one at a time, from that list alone. Each line you write comes from one entry; an idea with no entry is not written.

## Steps

1. **List the nested directories**: the directories that earned a pair in [ask.md](ask.md). One entry was enough.
2. **Write the root `AGENTS.md`** on the root template below, from the entries whose place is `root`.
3. **Write the root `CLAUDE.md`**: the line `@AGENTS.md`, plus any other `@` line listed under `## Imports found in old CLAUDE.md files` in `inputs.md` that came from the root `CLAUDE.md`. Nothing else.
4. **Write each nested pair** on the nested template, from the entries whose place is that directory. The `CLAUDE.md` beside it holds the one line `@AGENTS.md`, replacing whatever was there.

## Root template

Write the file in this shape. A section with no entries is left out, heading included.

```markdown
# AGENTS.md

<identity: one to four lines, from the entries of type identity — who it serves and what it solves; what stage it is at and whether real users, data, or money run through it; what this repository is not (split-out repositories, frozen directories); how an agent should treat the repository's contents. The tech stack is not identity.>

## Package manager and runtime

<one or two lines>

## Commands

| Command | What it does |
| --- | --- |
| `<command>` | <from entries of type command whose meaning --help and the manifest do not give; file-scoped test, lint, and typecheck commands first> |

## References

| Need | File |
| --- | --- |
| <setup, architecture, API, security, release, policy> | `<repository-relative path, from entries of type reference>` |

## Conventions and pitfalls

- <one rule per bullet, from entries of type convention or pitfall that have no when line>

<important if="<the when value: one kind of work>">
<the entries that share this when value>
</important>

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
```

The last line is written exactly as shown. Hosts that load nested files on their own lose nothing by it; hosts that stop at the working directory depend on it.

A root file carries only the sections above: no directory map, no environment variables, no list of installed skills, no commit attribution, no metadata header, no index of nested files. It is 150 lines at most; past that, rules that hold only in one directory move to that directory's file and documents get a row in References instead of a summary.

## Nested template

```markdown
# <directory path>

<scope: one sentence — what this directory owns and what it does not own, from the maintainer's nested-scope answer>

- <one rule per bullet, requirements and prohibitions mixed, from entries whose place is this directory>

## Commands

| Command | What it does |
| --- | --- |
| `<only commands that apply here and the root does not list>` | |

## References

| Need | File |
| --- | --- |
| <only documents that cover this directory and the root does not list> | `<path>` |
```

Commands and References appear only when they have rows. A nested file says only what differs from the root: keep narrower files shorter than root files. Nothing in it points back to the root, wraps in `<important if>`, names a skill, or carries a metadata header.

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

A References row and the subdirectory sentence are context pointers: their wording decides whether an agent reaches the file.

- **Front-load the leading word**: the pointer is where it does its triggering work.
- **One trigger per branch.** Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.
- **Cut identity the body already carries.**

Done when every pair from step 1 exists, every line in every file traces to one survey-list entry, and the root is within 150 lines.

Next: [prune.md](prune.md).
