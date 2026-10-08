---
name: manage-agents-md
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Manage AGENTS.md

An `AGENTS.md` is loaded into every session of every agent that works in this repository, on every host, and each line is obeyed as fact: a wrong or stale line misleads every agent after you, and a line the code already says only thins attention. So the file holds what an agent working here cannot find out by itself before it does damage: what this project is and what is at stake, what must not be touched, what must happen in order, what looks wrong but is deliberate, and where the documents are.

This skill keeps the format those files are written to, and `scripts/check.sh`, which checks what a machine can: the root file's line count, the `CLAUDE.md` beside each `AGENTS.md`, path references, `<important if>` tag balance, the subdirectory sentence, and any `AGENTS.override.md` left behind. The Write AGENTS.md playbook writes the files to it, from a **survey list**: one entry per fact, each with its evidence, a place (`root` or a directory path), a type (command, convention, gotcha, reference, defect, purpose, identity) and, for a fact that matters to one kind of work alone, a `when` value. Other skills and playbooks add rows to a file in this format by its headings.

```bash
bash scripts/check.sh [repo-root]          # run the checks; prints ok, or one line per failure
bash scripts/check.sh --limit              # print the root file's line limit
bash scripts/check.sh --list [repo-root]   # print every AGENTS.md, CLAUDE.md and AGENTS.override.md the checks scan
```

## What NOT to Add

Each rule, then what it catches.

1. **Obvious code info** — what the code already says. Bad: `The UserService class handles user operations.` The class name already tells us this.
2. **Discoverable from code** — cut any instruction the agent can discover from existing code patterns. LLMs are in-context learners — if your codebase consistently uses a pattern, the agent will follow it after a few searches. Bad: `Use named exports.` Every file in `src/` already does.
3. **Generic best practices** — universal advice, quality slogans, "follow best practices". Bad: `Always write tests for new features.` `Use meaningful variable names.`
4. **One-off fixes** — won't recur; clutters the file. Bad: `We fixed a bug in commit abc123 where the login button didn't work.`
5. **Verbose explanations** — verbose explanations when a one-liner suffices. Bad: `The authentication system uses JWT tokens. JWT (JSON Web Tokens) are an open standard (RFC 7519) that defines a compact and self-contained way for securely transmitting information between parties as a JSON object. In our implementation, we use the HS256 algorithm which...` Good: `Auth: JWT with HS256, tokens in `Authorization: Bearer <token>` header.`
6. **Linter territory** — anything a linter, formatter, typechecker, or pre-commit hook can enforce. When you cut one, suggest in the report wiring it as a pre-commit hook with the Set up code checkers playbook. Bad: `Use camelCase for variables, PascalCase for components.`
7. **Code snippets** — cut code snippets. They go stale and bloat the file. Use file path references instead (e.g., "see `src/utils/example.ts` for the pattern"). Bad: a ten-line example handler.
8. **Copies of other documents** — content that `README.md`, `CONTRIBUTING.md`, or a policy doc already holds. Reference it instead. Bad: the setup steps from `CONTRIBUTING.md` pasted in.
9. **Installed skills and plugins** — a list of what is installed. Bad: `Available skills: tdd, research, ...`
10. **Welcome text** — welcome text, intros, conclusions, or pleasantries.
    Bad: `Welcome! This file helps you work effectively in our codebase.`
11. **Prose about why** — long prose explaining why instructions matter.
    Bad: a paragraph on how following these rules keeps the team productive.
12. **Nested repeats** — nested `AGENTS.md` files that repeat root instructions.
    Bad: a nested file that restates the root's commit rule.

## Language

Write in the language the repository's existing instruction files use; in a repository that has none, the language the owner answered in. Other skills and playbooks add rows under `## Commands`, `## External References` and `## Key Conventions` by those headings, so the headings stay in English as written; the lines under them are in the repository's language. Keep the subdirectory sentence in English as shown, because `scripts/check.sh` looks for it by its English words.

## Root template

Write the file in this shape. A section with no entries is left out, heading included.

```markdown
# AGENTS.md

<identity: one to four lines, from the entries of type identity — who it serves and what it solves; what stage it is at and whether real users, data, or money run through it; what this repository is not (split-out repositories, frozen directories); how an agent should treat the repository's contents. The tech stack is not identity. An agent decides what kind of task it is on, and how careful to be, from these lines.>

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

Hosts that load nested files on their own lose nothing by the last line; hosts that stop at the working directory depend on it.

A root file carries only the sections above, plus one section of its own for a class of facts every task needs that no section above holds: no directory map, no environment variables, no list of installed skills, no commit attribution, no metadata header, no index of nested files. It stays within the limit `check.sh` sets — `bash scripts/check.sh --limit` prints it; past that, rules that hold only in one directory move to that directory's file and documents get a row in External References instead of a summary.

## Code and test rules

No `AGENTS.md` carries a rule about how code or tests are written here: every session loads that file, and the author of a change is the agent with the least context to spare. Each such entry has one home, chosen by who reads it:

- How the tests run here (where they live, how one is run, which layers there are, which external boundaries are stubbed and how, how a test puts the system into a state): `TESTING.md` at the root. Whoever writes a spec or a ticket reads it, and so does the review's Tests axis.
- A judgement about how code or tests are written that holds only in this repository: a row of the root `CODING_STANDARDS.md`. The `setup-mmw` skill writes that file from its template, and after that a row is added, changed or removed only through a retro proposal the owner approved. Only the review reads it. A rule with a fixed shape is linter territory (`## What NOT to Add`), not a row.

A worker gets what it needs from either file through the spec and the ticket. The root's External References names each of the two files that exists. An entry is written into its file, which is created when absent. A command, test commands included, stays a row of `## Commands`.

## Nested template

```markdown
# <directory path>

<purpose: one sentence — what this directory owns and what it does not own, from the owner's nested-purpose answer>

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

Every section after the purpose line appears only when it has rows. An entry whose place is this directory and which carries a `when` line goes in bare under its type: the nested file is already scoped, so it carries no `<important if>` blocks. A nested file says only what differs from the root: keep narrower files shorter than root files. Nothing in it points back to the root, wraps in `<important if>`, names a skill, or carries a metadata header.

## `<important if>` blocks

### 1. Foundational context stays bare, task-specific guidance gets wrapped

Not everything goes in an `<important if>` block. What every task needs (identity, package manager, commands, external references, key conventions, gotchas) stays as plain markdown; wrap only what some tasks reach.

Guidance that only matters for certain tasks — releasing, deploying, editing translations — gets wrapped in **`<important if>` blocks** with targeted conditions. In the survey list such a block is every entry that carries a `when` line, and entries with the same `when` value share one block.

### 2. Conditions must be specific and targeted

Bad — overly broad conditions that match everything:
```
<important if="you are changing anything">
- Run `make release-check` before tagging a release
- Regenerate `docs/api.md` after changing a route
- Ask before changing anything under `infra/`
</important>
```

Good — each rule has its own narrow trigger:
```
<important if="you are tagging a release">
- Run `make release-check` first
</important>

<important if="you are adding or changing a route">
- Regenerate `docs/api.md` afterwards
</important>

<important if="you are changing anything under infra/">
- Ask the user first
</important>
```

## Writing rules

Write the smallest useful file. Use only sections that add non-obvious value.

- Use headings, bullets, and tables; avoid paragraphs outside the identity lines.
- Use repository-relative paths; avoid vague references like "see docs". A path that stands for a whole class of files carries a `<name>` placeholder for the varying segment (`packages/<name>/package.json`); `scripts/check.sh` skips a backticked token with `<…>` and checks every other slashed token against the disk.
- Prefer file-scoped lint and typecheck commands; include full builds only when no narrower command exists. The **command rule**: write only commands whose meaning `--help` and the manifest's scripts do not give.
- Keep one rule per bullet.
- Keep rationale out unless it prevents a likely mistake. The one rationale that does is the reason behind a deliberate unconventional choice: it stops the next agent from "fixing" it.
- State each rule as the behaviour to perform. A prohibition stays only where no positive phrasing exists, and then sits next to the positive target.

## Pointers

An External References row and the subdirectory sentence are context pointers: their wording, not the file behind them, decides whether an agent reaches the file. Write the Need column as the situation that should send an agent there, leading with the word that situation is named by, one row per distinct situation.
