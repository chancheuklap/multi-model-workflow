# Survey

You are collecting the facts the `AGENTS.md` files will be written from. Everything that ends up in a file traces back to an entry in the **survey list** you build here, or to the user's answer later. So the survey covers the whole repository; the shortlist below is only what every surveyor reads first.

On the **incremental** branch the survey covers only `scope.md`: for each listed `AGENTS.md`, its change set and the lines in that file the changes bear on. Dispatch one directory group per listed file and no topic groups, and skip the reading list below; the change set is the whole assignment.

## What every surveyor reads first

Inspect before writing:
- package manager: lock files and manifests
- commands: `package.json`, `Makefile`, task runners, CI workflows
- docs/specs/policies: `README.md`, `CONTRIBUTING.md`, `docs/`, `specs/`, `policies/`, `SECURITY.md`, `.github/`
- conventions: current code patterns, test layout, generated files, legacy areas to avoid

Added for this skill:
- history: the directories with the most commits in the last year (`git log --since='1 year ago' --name-only --format= | cut -d/ -f1-2 | sort | uniq -c | sort -rn`), which tells where nested files earn their place
- the files under `## Other tools' instruction files` in your scratch directory's `inputs.md`, read for facts

## Groups

Two kinds of group. Each gets the prompt template below with its own **assignment**.

Topic groups, always these four, feeding the root file:

| Group | Assignment |
| --- | --- |
| toolchain | manifests, lock files, `Makefile`, task runners, `scripts/`, CI workflows: which package manager and runtime; which commands exist; which of them a reader cannot understand from `--help` or the manifest alone; which are file-scoped |
| documents | `README.md`, `CONTRIBUTING.md`, `docs/`, `specs/`, `SECURITY.md`, `.github/`, and every file listed in `inputs.md`: which documents cover setup, architecture, API, security, release, policy; where they disagree with each other or with the code |
| history | commit history: the busiest directories; directories untouched for a year; committed files that a command generates; areas that look legacy |
| patterns | the code: test layout and how one test file is run; generated files and their generators; ordering dependencies between modules; anything two parts of the code do differently |

Directory groups: one per top-level directory holding code, tests, scripts, or deployment files (dependency, build-output, and VCS directories get none). Directories the user's instruction files or their own READMEs mark as frozen, retired, or archived share one group, and that group samples — top two levels, READMEs, script and test entry points — and says in each evidence field what it sampled. Assignment: everything under that directory, looking for rules that hold only there — what the directory owns and does not own (reported as one entry of type purpose), what must never be hand-edited there, what breaks if done in the wrong order, which commands apply only there. A rule that holds only in a deeper subdirectory is reported with that subdirectory's path.

## Dispatch

When the host can run subagents, dispatch every group at once, one subagent each, on a model one tier below your own. When it cannot, run the groups yourself one after another with the same template, writing each report to the scratch directory before starting the next, so no report depends on your memory of an earlier one.

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

## Collect

Merge every report into one file, `survey-list.md` in the scratch directory: every entry kept with its evidence, exact duplicates dropped, sorted by place with `root` first. This file is the **survey list**; every later step reads it and nothing else from the survey. [ask.md](ask.md) appends the user's answers to it as entries of type identity and purpose.

Done when every group has reported ("nothing found" counts), `grep -c '^- fact:' survey-list.md` equals `grep -c '^  evidence:' survey-list.md`, and the entries are sorted by place.

Next, by branch:

| Branch | Open |
| --- | --- |
| create | [ask.md](ask.md) |
| rewrite | [migrate.md](migrate.md) |
| incremental | [additions.md](additions.md) |
