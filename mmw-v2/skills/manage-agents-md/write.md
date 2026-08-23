# Write

Branches **create** and **rewrite**. You have `survey-list.md`, with the maintainer's answers appended. You now write the files, root first, one at a time, from that list alone. Each line you write comes from one entry; an idea with no entry is not written. Entries of type defect are never written; they go to the report.

## Language

Write in the language the repository's existing instruction files use; on the create branch, the language the maintainer answered in. Translate the section headings of the templates; keep the subdirectory sentence in English as shown, because `scripts/check.sh` looks for it by its English words.

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

The last line is written exactly as shown, in English whatever the file's language. Hosts that load nested files on their own lose nothing by it; hosts that stop at the working directory depend on it.

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

### Core Problem

Claude Code injects a system reminder with every CLAUDE.md that says:

> "this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task."

This means Claude will ignore parts of your CLAUDE.md it deems irrelevant. The more content that isn't applicable to the current task, the more likely Claude is to ignore everything — including the parts that matter.

### Solution: `<important if="condition">` Blocks

Wrap conditionally-relevant sections of the CLAUDE.md in `<important if="condition">` XML tags. This exploits the same XML tag pattern used in Claude Code's own system prompt, giving the model an explicit relevance signal that cuts through the "may or may not be relevant" framing.

The problem and the mechanism above are Claude Code's. A host whose system prompt uses this XML pattern acts on the tag; a host without it reads the tag as text, which costs a line and changes nothing. The format keeps the tag because it costs the other hosts nothing.

### 1. Foundational context stays bare, domain guidance gets wrapped

Not everything should be in an `<important if>` block. Context that is relevant to virtually every task — identity, runtime, commands, references, conventions — should be left as plain markdown at the top of the file. This is onboarding context the agent always needs.

Domain-specific guidance that only matters for certain tasks — testing patterns, API conventions, state management, i18n — gets wrapped in `<important if>` blocks with targeted conditions.

The rule: inline what every task needs, and wrap what only some tasks reach.

### 2. Conditions must be specific and targeted

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

## Writing rules

Write the smallest useful file. Use only sections that add non-obvious value.

- **Concise**: Dense, human-readable content; one line per concept when possible
- **Actionable**: Commands should be copy-paste ready
- **Project-specific**: Document patterns unique to this project, not generic advice
- **Current**: All info should reflect actual codebase state

- Use headings, bullets, and tables; avoid paragraphs.
- Use repo-relative paths; avoid vague references like "see docs".
- A path that stands for a whole class of files carries a `<name>` placeholder for the varying segment (`mmw-v2/skills/<name>/tests/run.sh`); `scripts/check.sh` skips a backticked token with `<…>` and checks every other slashed token against the disk.
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

Where the rules above meet this format:

- The identity lines are the one place prose is allowed; every other section is headings, bullets, and tables.
- "Keep rationale out unless it prevents a likely mistake" and "cache the reason behind a choice" agree: the reason behind a deliberate unconventional choice is what stops the next agent from "fixing" it, so that reason stays; any other reason goes.
- Commands that the old file held are all kept (see [migrate.md](migrate.md)); commands the survey newly found are filtered by the file-scoped rule above and by the cache test in [prune.md](prune.md).

## Pointers

A References row and the subdirectory sentence are context pointers: their wording decides whether an agent reaches the file.

- **Front-load the leading word**: the pointer is where it does its triggering work.
- **One trigger per branch.** Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.
- **Cut identity the body already carries.**

Done when every pair from step 1 exists, every line in every file traces to one survey-list entry, and the root is within 150 lines.

Next: [prune.md](prune.md).
