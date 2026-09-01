# Create

Branch: **create**. The repository has no agent instruction file. When you are done it has a root `AGENTS.md` with a `CLAUDE.md` beside it, and the same pair in every directory that has a rule of its own.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel` and work from there; every path you write from now on is relative to it. If this is not a git repository, stop and tell the user: the skill's update branch reads git history and this repository has none.
2. Make a scratch directory outside the repository, for example `mktemp -d`, and keep its path. Survey reports and the user's answers go there, never into the repository.
3. Write `inputs.md` in the scratch directory. Under the first heading list other tools' instruction files, if any: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md` — survey input, read for facts, their form is not reused. The other two headings say `none` on this branch.

`inputs.md` has three headings, each followed by one line per item or the word `none`:

```markdown
## Other tools' instruction files
<path>

## Commands found in old files
`<command>` — <file>:<line>

## Imports found in old CLAUDE.md files
<@line> — <file>:<line>
```

Done when the root is resolved, the scratch directory exists, and `inputs.md` is in it with its three headings.

Next: [survey.md](survey.md).
