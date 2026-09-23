# Create

The repository has no agent instruction file. When you are done it has a root `AGENTS.md` with a `CLAUDE.md` beside it, and the same pair in every directory that has a rule of its own.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel` and work from there; every path you write from now on is relative to it. If this is not a git repository, stop and tell the user: this situation needs git from its first step — the root is resolved with `git rev-parse`, and the survey reads the commit history — and this repository has none.
2. Make a scratch directory outside the repository, for example `mktemp -d`, and keep its path. Survey reports and the user's answers go there, never into the repository.
3. Write `inputs.md` in the scratch directory, in the format `SKILL.md` `## The scratch directory` gives. Under the first heading list other tools' instruction files, if any: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md` — survey input, read for facts, their form is not reused. The other two headings say `none` in this situation.

Done when the root is resolved, the scratch directory exists, and `inputs.md` is in it with its three headings.

Continue at `SKILL.md` `## Survey` and run each section to the end.
