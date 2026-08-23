# Survey

The writer writes only from survey reports. Nothing goes into an `AGENTS.md` that a report does not carry with evidence, except what the maintainer says in [ask.md](ask.md). So the survey reads the whole repository, not a shortlist; the shortlist below is what every surveyor reads first.

## What every surveyor reads first

Inspect before writing:
- package manager: lock files and manifests
- commands: `package.json`, `Makefile`, task runners, CI workflows
- docs/specs/policies: `README.md`, `CONTRIBUTING.md`, `docs/`, `specs/`, `policies/`, `SECURITY.md`, `.github/`
- conventions: current code patterns, test layout, generated files, legacy areas to avoid

Added for this skill:
- history: the directories with the most commits in the last year (`git log --since='1 year ago' --name-only --format= | cut -d/ -f1-2 | sort | uniq -c | sort -rn`), which tells where nested files earn their place
- existing instruction files of any tool: `AGENTS.md`, `CLAUDE.md`, `AGENTS.override.md`, `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md` — read for facts, their form is not reused

Cross-reference with actual codebase:
- Run documented commands (mentally or actually)
- Check if referenced files exist
- Verify architecture descriptions

## Groups

Survey in parallel. Two kinds of group; every group gets the same prompt template below with its own **assignment**.

Topic groups, always four, feeding the root file:

| Group | Assignment |
| --- | --- |
| toolchain | manifests, lock files, `Makefile`, task runners, `scripts/`, CI workflows: which package manager and runtime, which commands exist, which of them a reader cannot understand from `--help` or the manifest alone, which are file-scoped |
| documents | `README.md`, `CONTRIBUTING.md`, `docs/`, `specs/`, `SECURITY.md`, `.github/`, and every existing instruction file: which documents exist for setup, architecture, API, security, release, policy; which of them disagree with each other or with the code |
| history | commit history: the busiest directories, the directories untouched for a year, files that are generated (committed outputs of a command), the areas that look legacy |
| patterns | the code itself: test layout and how tests are run per file, generated files and their generators, ordering dependencies between modules, anything two parts of the code do differently |

Directory groups, one per top-level directory that holds code, tests, scripts, or deployment files (skip dependency, build-output, and VCS directories). Assignment: everything under that directory, looking for rules that hold only there: what the directory owns and does not own, what must never be hand-edited there, what breaks if done in the wrong order, which commands apply only there. Report a rule for a deeper subdirectory when it holds only there, with the subdirectory path.

On the incremental branch the assignment is the change set only: the listed files and the `AGENTS.md` lines they bear on.

## Dispatch

When the host can run subagents, dispatch every group at once, one subagent each, each one tier below your own model. When the host cannot, run the groups yourself one after another with the same template, and write each report to a scratch file before starting the next group, so no report depends on memory of an earlier one.

Prompt template — fill the two placeholders, send the rest verbatim:

```
You are surveying a repository so that another agent can write its AGENTS.md. You report facts with evidence; you do not write the AGENTS.md and you do not judge style.

Repository root: <ROOT>
Assignment: <ASSIGNMENT>

Read everything in your assignment. Then report every fact that an agent working in this repository would need and could not learn by reading the obvious file (a manifest, a config, a README). Leave out what those files already say plainly.

Report format, one entry per fact, nothing else:

- fact: one sentence
  evidence: <file>:<line>, or the command you ran and its output
  place: root | <directory path> | omit
  type: command | convention | pitfall | reference

"place" is where the fact belongs: root when it holds everywhere, a directory path when it holds only under that directory, omit when it is obvious from the code or enforced by a linter, formatter, or type checker. "type": command for something to run, convention for how things are done here, pitfall for what goes wrong and how to avoid it, reference for a document that already covers a need (give its path as the fact).

When two parts of the repository do the same thing differently, report both with their evidence and place "root"; the maintainer decides. When a documented command fails or a referenced file is missing, report that as a pitfall with the evidence.
```

## Collecting

Merge the reports into one list, keep every entry's evidence, and drop exact duplicates only. Sort by place. This list is the input to [ask.md](ask.md) and [write.md](write.md).

Done when every group has reported, every entry has an evidence field that names a file and line or a command and output, and the merged list is sorted by place.
