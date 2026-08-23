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

## Package Manager

<one or two lines: package manager and runtime>

## Commands

| Command | What it does |
| --- | --- |
| `<command>` | <from entries of type command, filtered by the command rule below> |

## External References

| Need | File |
| --- | --- |
| <setup, architecture, API, security, release, policy> | `<repository-relative path, from entries of type reference>` |

## Key Conventions

- <one per bullet, from entries of type convention with no when line: how things are done here — generated files and the command that regenerates them, fixed orderings, which of two records wins, deliberate unconventional choices and their reason>

## Gotchas

- <one per bullet, from entries of type gotcha with no when line: what goes wrong — problems debugged more than once, differences between machines and environments, legacy areas>

<important if="<the when value: one kind of work>">
<the convention and gotcha entries that share this when value>
</important>

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
```

A fact that describes a practice is a convention; a fact that describes a consequence is a gotcha. "Generated files are not hand-edited; run `make gen`" is a convention; "hand edits under `gen/` are overwritten on the next build" is a gotcha.

The last line is written exactly as shown, in English whatever the file's language. Hosts that load nested files on their own lose nothing by it; hosts that stop at the working directory depend on it.

A root file carries only the sections above: no directory map, no environment variables, no list of installed skills, no commit attribution, no metadata header, no index of nested files. It is 150 lines at most; past that, rules that hold only in one directory move to that directory's file and documents get a row in External References instead of a summary.

## Nested template

```markdown
# <directory path>

<purpose: one sentence — what this directory owns and what it does not own, from the maintainer's nested-purpose answer>

## Key Conventions

- <from entries of type convention whose place is this directory>

## Gotchas

- <from entries of type gotcha whose place is this directory>

## Commands

| Command | What it does |
| --- | --- |
| `<only commands that apply here and the root does not list>` | |

## External References

| Need | File |
| --- | --- |
| <only documents that cover this directory and the root does not list> | `<path>` |
```

Every section after the purpose line appears only when it has rows. A nested file says only what differs from the root: keep narrower files shorter than root files. Nothing in it points back to the root, wraps in `<important if>`, names a skill, or carries a metadata header.

## Domain sections

A **domain section** is guidance that only matters for certain tasks — testing patterns, API conventions, state management, i18n — wrapped in an `<important if>` block with a targeted condition. In the survey list it is every entry that carries a `when` line; entries with the same `when` value share one block.

Not everything goes in a domain section. Context that is relevant to virtually every task — identity, package manager, commands, external references, key conventions, gotchas — is left as plain markdown at the top of the file. This is onboarding context the agent always needs. The rule: inline what every task needs, and wrap what only some tasks reach.

Conditions must be specific and targeted.

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

| Rule | Meaning |
| --- | --- |
| Concise | One line per concept. Dense, human-readable content; no verbose explanations |
| Actionable | Commands are copy-paste ready; paths are real; steps are concrete, not vague |
| Project-specific | Patterns unique to this project, not generic advice |
| Current | Every line reflects the codebase as it is now |
| Form | Headings, bullets, and tables; the identity lines are the one place prose is allowed. One rule per bullet. Commands in a table when there is more than one |
| Paths | Repo-relative, never "see docs". A path that stands for a whole class of files carries a `<name>` placeholder for the varying segment (`mmw-v2/skills/<name>/tests/run.sh`); `scripts/check.sh` skips a backticked token with `<…>` and checks every other slashed token against the disk |
| External References | Name the exact file for setup, architecture, API specs, security, release, and policy docs when they exist; reference them instead of copying them |
| Commands | Only commands whose meaning `--help` and the manifest's scripts do not give; file-scoped test, lint, and typecheck commands first, full builds only when no narrower command exists. On a rewrite every command in the old file passes through this rule: one whose meaning is discoverable stays in `inputs.md`, every other one is kept |
| Rationale | One kind only — the reason behind a deliberate unconventional choice, which stops the next agent from "fixing" it. No other reason is written |
| Phrasing | State each rule as the behaviour to perform. A prohibition stays only where no positive phrasing exists, and then sits next to the positive target |

## Pointers

An External References row and the subdirectory sentence are context pointers: their wording decides whether an agent reaches the file.

- **Front-load the leading word**: the pointer is where it does its triggering work.
- **One trigger per branch.** Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.
- **Cut identity the body already carries.**

Done when every pair from step 1 exists, every line in every file traces to one survey-list entry, and the root is within 150 lines.

Next: [prune.md](prune.md).
