---
name: manage-agents-md
description: Create or rewrite a repository's AGENTS.md and CLAUDE.md to one fixed format. Use when asked to create AGENTS.md or CLAUDE.md, or to rewrite or migrate existing agent instruction files (root, nested, or AGENTS.override.md).
---

# Manage AGENTS.md

Two situations share one flow: set up in the situation's file, then the sections below in order; the situation's file says where its own step joins.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location: the path differs by machine and by host.

## Find your situation

From the repository root, list what exists:

```bash
bash <scripts>/check.sh --list .
```

| What you see | Your situation | Open |
| --- | --- | --- |
| Nothing | **create** | [references/create.md](references/create.md) |
| Any file, and the user asked you (to rewrite, migrate, redo, or change these files) | **rewrite** | [references/rewrite.md](references/rewrite.md) |

## The scratch directory

`inputs.md` in the scratch directory has three headings, each followed by one line per item or the word `none`:

```markdown
## Other tools' instruction files
<path>

## Commands found in old files
`<command>` — <file>:<line>

## Imports found in old CLAUDE.md files
<@line> — <file>:<line>
```

## Survey

You are collecting the facts the `AGENTS.md` files will be written from. Everything that ends up in a file traces back to an entry in the **survey list** you build here, or to the user's answer later. So the survey covers the whole repository.

### Groups

Two kinds of group. Each gets the prompt template below with its own **assignment**.

Topic groups, always these four, feeding the root file:

| Group | Assignment |
| --- | --- |
| toolchain | manifests, lock files, `Makefile`, task runners, `scripts/`, CI workflows: which package manager and runtime; which commands exist; which of them a reader cannot understand from `--help` or the manifest alone; which are file-scoped |
| documents | `README.md`, `CONTRIBUTING.md`, `docs/`, `specs/`, `SECURITY.md`, `.github/`, and every file listed in `inputs.md`: which documents cover setup, architecture, API, security, release, policy; where they disagree with each other or with the code |
| history | commit history: the busiest directories (command below); directories untouched for a year; committed files that a command generates; areas that look legacy |
| patterns | the code: test layout and how one test file is run; generated files and their generators; ordering dependencies between modules; anything two parts of the code do differently |

The history group finds the busiest directories with `git log --since='1 year ago' --name-only --format= | cut -d/ -f1-2 | sort | uniq -c | sort -rn`.

Directory groups: one per top-level directory holding code, tests, scripts, or deployment files (dependency, build-output, and VCS directories get none). Directories the user's instruction files or their own READMEs mark as frozen, retired, or archived share one group, and that group samples — top two levels, READMEs, script and test entry points — and says in each evidence field what it sampled. Assignment: everything under that directory, looking for rules that hold only there — what the directory owns and does not own (reported as one entry of type purpose), what must never be hand-edited there, what breaks if done in the wrong order, which commands apply only there. A rule that holds only in a deeper subdirectory is reported with that subdirectory's path.

### Dispatch

When the host can run subagents, dispatch every group at once, one subagent each: your host's general-purpose subagent, with no model named. When it cannot, run the groups yourself one after another with the same template, writing each report to the scratch directory before starting the next, so no report depends on your memory of an earlier one.

Prompt template — fill `<ROOT>` and `<ASSIGNMENT>`, send the rest as written:

```
You are surveying a repository so that another agent can write its AGENTS.md. You report facts with evidence; you do not write the AGENTS.md and you do not judge style.

Repository root: <ROOT>
Assignment: <ASSIGNMENT>

Read everything in your assignment. Then report every fact that an agent working in this repository would need and could not learn by reading the obvious file (a manifest, a config, a README). Leave out what those files already say plainly.

Cross-reference with the actual codebase: run the documented commands, check that referenced files exist, and verify architecture descriptions against the code.

Report format, one entry per fact, nothing else:

- fact: one sentence
  evidence: <file>:<line>, or the command you ran and its output
  place: root | <directory path> | omit
  type: command | convention | gotcha | reference | defect | purpose
  when: <one kind of work, only if the fact matters to that kind of work alone; leave the line out otherwise>

A group that finds nothing reports the single line "nothing found".

"place" is where the fact belongs: root when it holds everywhere, a directory path when it holds only under that directory, omit when it is obvious from the code or enforced by a linter, formatter, or type checker. "type": command for something to run, convention for how things are done here, gotcha for what goes wrong and how to avoid it, reference for a document that already covers a need (give its path as the fact), defect for something broken or stale in the repository (a wrong count, a dead link, an orphaned file) that someone should fix — a defect is reported, never written into an AGENTS.md; purpose for the one sentence saying what a directory owns and does not own. "when": the one kind of work the fact matters to (for example "adding or modifying API routes"); most facts have no when line.

When two parts of the repository do the same thing differently, report both with their evidence and place "root"; the user decides. When a documented command fails or a referenced file is missing, report that as a gotcha with the evidence.
```

### Collect

Merge every report into one file, `survey-list.md` in the scratch directory: every entry kept with its evidence, exact duplicates dropped, sorted by place with `root` first. This file is the **survey list**; every later step reads it and nothing else from the survey. `## Ask the user` appends the user's answers to it as entries of type identity and purpose.

Done when every group has reported ("nothing found" counts), every `- fact:` line in `survey-list.md` is followed by its own `  evidence:` line and every `  evidence:` line follows a `- fact:` line — read the file top to bottom and name every line on either side that has no partner — and the entries are sorted by place.

## Ask the user

The survey list holds what the repository shows. Four things it cannot show: who the project serves and how serious it is, what this repository is not, the conventions nobody wrote down, and the reasons behind the odd choices. You get those from the user now, with the fixed questions below. Each question carries a recommended answer drawn from the survey list, so the user confirms or corrects instead of composing.

This is one round: the questions are fixed, there is no follow-up tree, and nothing else is asked here.

### Format

Ask the whole set in one message: number each question and give your recommended answer. Then wait for the user's answers before writing.

Each question should be formatted like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

The recommended answer quotes the survey entry and its evidence. When the survey list has nothing for a question, the recommended answer is "the survey found nothing for this". In the rewrite situation, the lines `destinations.md` sent to `ask` are the old file's identity lines; they are the recommended answers to the four identity questions, each marked "from the current file".

### Project identity, four questions

1. In one sentence: who is this project for, and what problem does it solve for them?
2. What stage is it at? Are there real users, real data, or real money running through it?
3. What lives outside this repository — related repositories, machines it deploys to? What has been split out, and which directories are frozen?
4. Is there anything in the repository an agent is likely to misread — content that looks like rules but is the product, files that look like code but are the user's assets?

### Key Conventions and Gotchas, seven questions

1. Which files are generated and must not be hand-edited? What command regenerates them?
2. Is there anything that must be done in a fixed order?
3. Where do two places record the same thing, and which one wins when they disagree?
4. Which problems have you debugged more than once?
5. Which practices look unconventional here but are deliberate? Why?
6. How do machines or environments differ from each other (local and production, one OS and another)?
7. Which areas are legacy and must be left alone?

### Nested purpose, one question per directory

A directory **earns a pair** when the survey list has at least one entry of type command, convention, or gotcha whose place is that directory; entries of type defect and reference do not count. Ask about every directory that earns a pair in one question: a table with one row per directory, the recommended purpose line in the second column, drawn from that directory's purpose entry in the survey list. The user edits rows or strikes directories out.

### Record

Append every answer to `survey-list.md` as an entry with `evidence: user, <date>`, the place it belongs to, and its type. An answer of "no" or "nothing" is appended too, so the writer does not go looking. Identity answers take the type `identity`; purpose answers the type `purpose`.

Done when every question has an appended answer or the user's explicit "skip".

## Write

You have `survey-list.md`, with the user's answers appended. You now write the files, root first, one at a time, from that list alone. Each line you write comes from one entry; an idea with no entry is not written. Entries of type defect are never written; they go to the report that `## Verify and report` writes at the end.

### Language

Write in the language the repository's existing instruction files use; in the create situation, the language the user answered in. Translate the section headings of the templates; keep the subdirectory sentence in English as shown, because `<scripts>/check.sh` looks for it by its English words.

### Steps

1. **List the nested directories**: the directories that earned a pair in `## Ask the user`.
2. **Write the root `AGENTS.md`** on the root template below, from the entries whose place is `root`.
3. **Write the root `CLAUDE.md`**: the line `@AGENTS.md`, plus any other `@` line listed under `## Imports found in old CLAUDE.md files` in `inputs.md` that came from the root `CLAUDE.md`. Nothing else.
4. **Write each nested pair** on the nested template, from the entries whose place is that directory. The `CLAUDE.md` beside it holds the one line `@AGENTS.md`, replacing whatever was there.

### Root template

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

Hosts that load nested files on their own lose nothing by the last line; hosts that stop at the working directory depend on it.

A root file carries only the sections above: no directory map, no environment variables, no list of installed skills, no commit attribution, no metadata header, no index of nested files. It stays within the limit `check.sh` sets — `bash <scripts>/check.sh --limit` prints it; past that, rules that hold only in one directory move to that directory's file and documents get a row in External References instead of a summary.

### Code and test rules

A repository's code rules (how code is written here) live in its `CODING_STANDARDS.md`, and its test rules (the test layers, which external boundaries may be stubbed, how to run the tests) in its `TESTING.md`. The reviewer's Standards and Tests axes read those two files, and a worker gets the rules it needs through the spec and the ticket. So no `AGENTS.md` carries a code or test rule: the root's External References names each of the two files that exists. An entry that is a code or test rule is written into the matching file, which is created when absent.

### Nested template

```markdown
# <directory path>

<purpose: one sentence — what this directory owns and what it does not own, from the user's nested-purpose answer>

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

Every section after the purpose line appears only when it has rows. An entry whose place is this directory and which carries a `when` line goes in bare under its type: the nested file is already scoped, so it carries no domain sections. A nested file says only what differs from the root: keep narrower files shorter than root files. Nothing in it points back to the root, wraps in `<important if>`, names a skill, or carries a metadata header.

### Domain sections

#### 1. Foundational context stays bare, domain guidance gets wrapped

Domain-specific guidance that only matters for certain tasks — releasing, deploying, editing translations — gets wrapped in `<important if>` blocks with targeted conditions. Such a block is a **domain section**; in the survey list it is every entry that carries a `when` line, and entries with the same `when` value share one block.

#### 2. Conditions must be specific and targeted

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

### Writing rules

Write the smallest useful file. Use only sections that add non-obvious value.

- Use headings, bullets, and tables; avoid paragraphs outside the identity lines.
- Use repository-relative paths; avoid vague references like "see docs". A path that stands for a whole class of files carries a `<name>` placeholder for the varying segment (`packages/<name>/package.json`); `<scripts>/check.sh` skips a backticked token with `<…>` and checks every other slashed token against the disk.
- List exact external files for setup, architecture, API specs, security, release, and policy docs when they exist.
- Prefer file-scoped lint and typecheck commands; include full builds only when no narrower command exists. Write only commands whose meaning `--help` and the manifest's scripts do not give. On a rewrite every command in the old file passes through this rule: one whose meaning is discoverable stays in `inputs.md`, every other one is kept.
- Put commands in tables when there is more than one.
- Keep one rule per bullet.
- Keep rationale out unless it prevents a likely mistake. The one rationale that does is the reason behind a deliberate unconventional choice: it stops the next agent from "fixing" it.
- State each rule as the behaviour to perform. A prohibition stays only where no positive phrasing exists, and then sits next to the positive target.

### Pointers

An External References row and the subdirectory sentence are context pointers: their wording, not the file behind them, decides whether an agent reaches the file. Write the Need column as the situation that should send an agent there, leading with the word that situation is named by, one row per distinct situation.

Done when every pair from step 1 exists, every line in every file traces to one survey-list entry, and the root is within the limit `check.sh` sets.

## Prune

The files are written. Now read each one you wrote or edited line by line: first against the list of what must not be there, then through the self-check.

### What NOT to Add

Each rule, then what it catches.

1. **Obvious code info** — what the code already says. Bad: `The UserService class handles user operations.` The class name already tells us this.
2. **Discoverable from code** — cut any instruction the agent can discover from existing code patterns. LLMs are in-context learners — if your codebase consistently uses a pattern, the agent will follow it after a few searches. Bad: `Use named exports.` Every file in `src/` already does.
3. **Generic best practices** — universal advice, quality slogans, "follow best practices". Bad: `Always write tests for new features.` `Use meaningful variable names.`
4. **One-off fixes** — won't recur; clutters the file. Bad: `We fixed a bug in commit abc123 where the login button didn't work.`
5. **Verbose explanations** — verbose explanations when a one-liner suffices. Bad: `The authentication system uses JWT tokens. JWT (JSON Web Tokens) are an open standard (RFC 7519) that defines a compact and self-contained way for securely transmitting information between parties as a JSON object. In our implementation, we use the HS256 algorithm which...` Good: `Auth: JWT with HS256, tokens in `Authorization: Bearer <token>` header.`
6. **Linter territory** — anything a linter, formatter, typechecker, or pre-commit hook can enforce. When you cut one, suggest in the report wiring it as a pre-commit hook with the `code-checkers` skill. Bad: `Use camelCase for variables, PascalCase for components.`
7. **Code snippets** — cut code snippets. They go stale and bloat the file. Use file path references instead (e.g., "see `src/utils/example.ts` for the pattern"). Bad: a ten-line example handler.
8. **Copies of other documents** — content that `README.md`, `CONTRIBUTING.md`, or a policy doc already holds. Reference it instead. Bad: the setup steps from `CONTRIBUTING.md` pasted in.
9. **Installed skills and plugins** — a list of what is installed. Bad: `Available skills: tdd, research, ...`
10. **Welcome text** — welcome text, intros, conclusions, or pleasantries.
    Bad: `Welcome! This file helps you work effectively in our codebase.`
11. **Prose about why** — long prose explaining why instructions matter.
    Bad: a paragraph on how following these rules keeps the team productive.
12. **Nested repeats** — nested `AGENTS.md` files that repeat root instructions.
    Bad: a nested file that restates the root's commit rule.

### Self-check

Answer each for the file in front of you. A "no" means the file is not finished: fix the lines behind it before going on. A "no" whose cause is that the repository has none of the thing (a project with no commands, no documents to reference) is a pass; write that cause down.

| Criterion | Check |
| --- | --- |
| Commands | Has every command in the table passed the command rule in `## Write`, and is none of that kind missing? |
| Orientation | Do the identity lines and External References let an agent find where things live? |
| Non-obvious patterns | Are gotchas and quirks documented? |
| Currency | Does it reflect current codebase state — no outdated versions? |
| Actionability | Are instructions executable, not vague — no template text left uncustomized, no "TODO"? |
| Single source | Does no line repeat a line of another `AGENTS.md` in this repository? |

Done when every line of every file you wrote or edited has passed the list and the self-check, and every rule is phrased as the behaviour to perform or, where a prohibition had to stay, sits next to its positive target.

## Verify and report

Two things close the work: the mechanical checks pass, and the report says what changed.

### Checks

From the repository root:

```bash
bash <scripts>/check.sh .
```

Fix every line `check.sh` prints and run it again until it prints `ok`. A failure this repository cannot satisfy is a pass; write its cause down. Two reach that: a root file over the limit with nothing left to move into a directory's file, and a backticked path a clean checkout does not hold (a generated or ignored file).

Verify exact paths and commands exist. The script covers paths. Commands you verify yourself: run each one a file names, or read the script it invokes, and fix the line when it fails.

### Report

The report goes into the conversation, never into a file in the repository.

**create** — the files written with their line counts, and the user's answers that became lines. Then **Defects found**: every survey entry of type defect, one line each with its evidence.

**rewrite** — the two lists from the end of `destinations.md`, then **Defects found** as above:

```
What was removed and why:
- <rule or section> — <reason>

What was NOT removed:
- Commands kept (<count>), dropped as discoverable (<count>)
- <rule kept on the user's confirmation>
```

Done when `check.sh` prints `ok`, every command in every file you wrote or edited has been verified, and the report is written.
