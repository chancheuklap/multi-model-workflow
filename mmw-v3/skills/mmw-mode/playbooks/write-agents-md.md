### Write AGENTS.md

**You own one repository's agent instruction files: a root `AGENTS.md` with a `CLAUDE.md` beside it, and the same pair in every directory that has a rule of its own, written to the `manage-agents-md` skill's format from a survey list every line traces back to; surveyor subagents read the repository, one per group.** An `AGENTS.md` is loaded into every session of every agent that works in this repository, on every host, and each line is obeyed as fact: a wrong or stale line misleads every agent after you, and a line the code already says only thins attention. Distinct from the `setup-mmw` skill, which adds the rows this pipeline needs to an `AGENTS.md` as it stands and writes nothing else into it.

The survey and the questions exist to find what the owner has not told you. When the owner has already said what the file must say, survey only what verifies those facts and ask only what is still missing; the format, `check.sh` and the report stay the same.

1. **Find your situation.** From the repository root, list what exists with the `manage-agents-md` skill's `bash scripts/check.sh --list .`. Nothing listed is the **create** situation. Any file listed, and the owner asked you to rewrite, migrate, redo or change these files, is the **rewrite** situation: when you are done the old files are gone or rewritten, every command they held that `--help` and the manifest do not explain is still there, and what only the owner knows has been confirmed by the owner.
   Done when you know which situation this is.
2. **Set up.** Work from the repository root (`git rev-parse --show-toplevel`). A folder that is not a git repository still gets its files: its root is the folder the owner named, and the history group of step 3 is left out. Make a scratch directory outside the repository (`mktemp -d`) and keep its path; survey reports and the owner's answers go there, never into the repository. In the rewrite situation, read every old file `check.sh --list` names, in full.
   Done when the root is resolved, the scratch directory exists, and in a rewrite every file `check.sh --list` names has been read.
3. **Survey.** You are collecting the facts the `AGENTS.md` files will be written from. Everything that ends up in a file traces back to an entry in the **survey list** you build here, or to the owner's answer later, so the survey covers the whole repository. Split it into the groups of **Survey groups** below, and send out one subagent per group, all at once, the AGENTS.md surveyor, with the prompt in the `mmw-mode` skill's `references/agents-md-survey.md` and the group's assignment. Merge every report into one file, `survey-list.md` in the scratch directory: every entry kept with its evidence, exact duplicates dropped, sorted by place with `root` first. This file is the survey list; every later step reads it and nothing else from the survey.
   Done when every group has reported ("nothing found" counts) and the entries are merged and sorted by place.
4. **Migrate the old files** (rewrite only), as **Migrate** below says. No line of an old file is lost without a reason written down.
   Done when every rule and every command in each old file has a line in `destinations.md`, and every line with a section destination is an entry in `survey-list.md`.
5. **Ask the owner** the questions of **The questions** below, in one message, each numbered with your recommended answer under it, then wait for the answers. Append every answer to `survey-list.md` as an entry with `evidence: user, <date>`, the place it belongs to, and its type. An answer of "no" or "nothing" is appended too, so the writer does not go looking. Identity answers take the type `identity`; purpose answers the type `purpose`.
   Done when every question has an appended answer or the owner's explicit "skip".
6. **Write the files**, root first, one at a time, from `survey-list.md` alone, in the `manage-agents-md` skill's format: read its `SKILL.md` in full first. Each line you write comes from one entry; an idea with no entry is not written. Entries of type defect are never written; they go to the reply.
   1. List the nested directories: the directories that earned a pair in step 5.
   2. Write each code or test rule into the repository's `CODING_STANDARDS.md`, as the skill's `## Code and test rules` says, not into an `AGENTS.md`.
   3. Write the root `AGENTS.md` on the skill's root template, from the entries whose place is `root`.
   4. Write the root `CLAUDE.md`: the line `@AGENTS.md`, plus any other `@` line whose destination in `destinations.md` is `CLAUDE.md`. Nothing else.
   5. Write each nested pair on the skill's nested template, from the entries whose place is that directory. The `CLAUDE.md` beside it holds the one line `@AGENTS.md`, replacing whatever was there.

   Done when every pair from step 6.1 exists, every code or test rule is in `CODING_STANDARDS.md`, every line in every file traces to one survey-list entry, and the root is within the limit `check.sh` sets.
7. **Prune.** Read each file you wrote or edited as the agent who loads it at the start of every session, and cut every line that would not change what that agent does.
   Done when no line states an outdated version or count, and no template placeholder or `TODO` is left.
8. **Check.** From the repository root, run the `manage-agents-md` skill's `bash scripts/check.sh .`. Fix every line it prints and run it again until it prints `ok`. A failure this repository cannot satisfy is a pass; write its cause down. Two reach that: a root file over the limit with nothing left to move into a directory's file, and a backticked path a clean checkout does not hold (a generated or ignored file). Verify exact paths and commands exist. The script covers paths. Commands you verify yourself: run a command only when running it changes nothing outside a temporary directory (`--help`, a test, a lint, a local build); a command that deploys, publishes, migrates, sends messages or writes to a shared service is verified by reading the script it invokes, never by running it. Fix the line when it fails (**principle-prove-it-works**).
   Done when `check.sh` prints `ok` and every command in every file you wrote or edited has been verified.

**Survey groups.** Split so every part of the repository is read by someone whose share fits one session: by default, the four topic groups below plus one directory group per top-level directory. In a small repository, merge groups whose assignments would each be a few files into one subagent.

Topic groups, always these four, feeding the root file:

| Group | Assignment |
| --- | --- |
| toolchain | manifests, lock files, `Makefile`, task runners, `scripts/`, CI workflows: which package manager and runtime; which commands exist; which of them a reader cannot understand from `--help` or the manifest alone; which are file-scoped |
| documents | `README.md`, `CONTRIBUTING.md`, `docs/`, `specs/`, `SECURITY.md`, `.github/`, and other tools' instruction files (`.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md`): which documents cover setup, architecture, API, security, release, policy; where they disagree with each other or with the code |
| history | commit history: the busiest directories (command below); directories untouched for a year; committed files that a command generates; areas that look legacy |
| patterns | the code: test layout and how one test file is run; generated files and their generators; ordering dependencies between modules; anything two parts of the code do differently |

The history group finds the busiest directories with `git log --since='1 year ago' --name-only --format= | cut -d/ -f1-2 | sort | uniq -c | sort -rn`.

Directory groups: one per top-level directory holding code, tests, scripts, or deployment files (dependency, build-output, and VCS directories get none). Directories the owner's instruction files or their own READMEs mark as frozen, retired, or archived share one group, and that group samples — top two levels, READMEs, script and test entry points — and says in each evidence field what it sampled. Assignment: everything under that directory, looking for rules that hold only there — what the directory owns and does not own (reported as one entry of type purpose), what must never be hand-edited there, what breaks if done in the wrong order, which commands apply only there. A rule that holds only in a deeper subdirectory is reported with that subdirectory's path.

**Migrate.** You have read every old file in full, and you have `survey-list.md`. Every old rule and command gets a destination: a section of the new format, the owner's questions, or the "what was removed" list.

1. **Identify the project identity** — extract what the old files say about what this is. It becomes the recommended answer in step 5, where the owner confirms or replaces it.
2. **Extract commands and imports** — every command in the old file passes through the command rule in the `manage-agents-md` skill's `## Writing rules`: one whose meaning is discoverable gets `removed: discoverable` as its destination, every other one is kept. Every `@` line in an old `CLAUDE.md` other than `@AGENTS.md` gets `CLAUDE.md` as its destination when it came from the root `CLAUDE.md`, or is dropped when it came from a nested one (only `@AGENTS.md` survives there).
3. **Assign `when` values** — a line that matters to one kind of work only gets a `when` value, chosen as the skill's `` ## `<important if>` blocks `` says.
4. **Move code and test rules out** — a line that is a code or test rule gets `CODING_STANDARDS.md` as its destination (the skill's `## Code and test rules`); copy it into that file verbatim, a test rule under `## Tests`.
5. **Send the rest to prune** — a line that matches the list in the skill's `## What NOT to Add` gets `removed: <reason>` as its destination now, so the "what was removed" list is complete before writing starts.

Record the outcome as `destinations.md` in the scratch directory: one line per rule or command, as `<old file>:<line> → <destination>`, where the destination is a section name of the skill's templates, `CODING_STANDARDS.md`, `ask` (identity lines only), or `removed: <reason>`.

Then append every line whose destination is a section to `survey-list.md` as an entry: `fact` is the line, `evidence` is `<old file>:<line>`, `place` is root or the directory the old file sat in, `type` is command, convention, gotcha, or reference by the section, and `when` is the value chosen in step 3 for a line that goes into an `<important if>` block. The writer reads only the survey list; a kept line that is not in it is not written. Lines whose destination is `ask` stay in `destinations.md`; step 5 reads them there as recommended answers.

What happens to each old file on disk:

| Old file | Destination |
| --- | --- |
| `AGENTS.override.md` in a directory | Its lines get destinations like any other old file's and reach that directory's `AGENTS.md` through the survey list; the override file is deleted |
| A nested pair whose every rule moved to the root or was removed | Both files deleted; the directory goes on the "what was removed" list |
| `> ` metadata lines at the top of old files (last-checked commit, domain context, review scope) | Removed; git history is the anchor |

Keep two lists at the end of `destinations.md` as you go; the reply prints them:

- **What was removed and why** — one line per removed rule or section with its reason, in the words of the skill's `## What NOT to Add`; a linter-territory line carries the hook suggestion.
- **What was NOT removed** — every kept command, every rule moved to `CODING_STANDARDS.md`, and every rule that will stay only if the owner confirms it.

**The questions.** The survey list holds what the repository shows. Four things it cannot show: who the project serves and how serious it is, what this repository is not, the conventions nobody wrote down, and the reasons behind the odd choices. You get those from the owner now, with the fixed questions below. Each question carries a recommended answer drawn from the survey list, so the owner confirms or corrects instead of composing. The recommended answer quotes the survey entry and its evidence. When the survey list has nothing for a question, the recommended answer is "the survey found nothing for this". In the rewrite situation, the lines `destinations.md` sent to `ask` are the old file's identity lines; they are the recommended answers to the four identity questions, each marked "from the current file".

The questions below are a coverage checklist, not a script: one the survey list already answers with evidence becomes a one-line confirmation, and an answer that surfaces a fact the file still needs earns one follow-up question, never a design discussion.

Project identity, four questions:

1. In one sentence: who is this project for, and what problem does it solve for them?
2. What stage is it at? Are there real users, real data, or real money running through it?
3. What lives outside this repository — related repositories, machines it deploys to? What has been split out, and which directories are frozen?
4. Is there anything in the repository an agent is likely to misread — content that looks like rules but is the product, files that look like code but are the owner's assets?

Key Conventions and Gotchas, seven questions:

1. Which files are generated and must not be hand-edited? What command regenerates them?
2. Is there anything that must be done in a fixed order?
3. Where do two places record the same thing, and which one wins when they disagree?
4. Which problems have you debugged more than once?
5. Which practices look unconventional here but are deliberate? Why?
6. How do machines or environments differ from each other (local and production, one OS and another)?
7. Which areas are legacy and must be left alone?

Nested purpose, one table. A nested file is one more file that drifts as the code under it changes, and nothing reminds anyone to update it. A directory earns one when an agent working there would break something it would not notice; a rule the agent would learn from the first error or the first file it opens stays out, and a rule for one kind of work can be an `<important if>` block in the root instead. Ask about every directory that earns a pair in one question: a table with one row per directory, the recommended purpose line in the second column, drawn from that directory's purpose entry in the survey list. The owner edits rows or strikes directories out.

**Reply:** the report goes into the conversation, never into a file in the repository. In the create situation, the files written with their line counts, and the owner's answers that became lines. In the rewrite situation, the two lists from the end of `destinations.md`:

```
What was removed and why:
- <rule or section> — <reason>

What was NOT removed:
- Commands kept (<count>), dropped as discoverable (<count>)
- <rule kept on the owner's confirmation>
```

Then, in both, **Defects found**: every survey entry of type defect, one line each with its evidence; and each `check.sh` failure accepted as a pass, with its cause.
