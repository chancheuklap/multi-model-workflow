# Prune

All branches. The files are written. Now read each one you wrote or edited line by line: first against the list of what must not be there, then with the four tests under Pruning, then through the self-check.

On the **incremental** branch the user-owned lines named in [incremental.md](incremental.md) are exempt: read them, leave them, and put a doubt about one into the report.

## What NOT to Add

Each rule, then what it catches.

1. **Obvious code info** — what the code already says. Bad: `The UserService class handles user operations.` The class name already tells us this.
2. **Discoverable from code** — cut any instruction the agent can discover from existing code patterns. LLMs are in-context learners — if your codebase consistently uses a pattern, the agent will follow it after a few searches. Bad: `Use named exports.` Every file in `src/` already does.
3. **Generic best practices** — universal advice, quality slogans, "follow best practices". Bad: `Always write tests for new features.` `Use meaningful variable names.`
4. **One-off fixes** — won't recur; clutters the file. Bad: `We fixed a bug in commit abc123 where the login button didn't work.`
5. **Verbose explanations** — verbose explanations when a one-liner suffices. Bad: `The authentication system uses JWT tokens. JWT (JSON Web Tokens) are an open standard (RFC 7519) that defines a compact and self-contained way for securely transmitting information between parties as a JSON object. In our implementation, we use the HS256 algorithm which...` Good: `Auth: JWT with HS256, tokens in `Authorization: Bearer <token>` header.`
6. **Linter territory** — anything a linter, formatter, typechecker, or pre-commit hook can enforce. When you cut one, suggest a pre-push or pre-commit hook in the report. Bad: `Use camelCase for variables, PascalCase for components.`
7. **Code snippets** — cut code snippets. They go stale and bloat the file. Use file path references instead (e.g., "see `src/utils/example.ts` for the pattern"). Bad: a ten-line example handler.
8. **Copies of other documents** — content that `README.md`, `CONTRIBUTING.md`, or a policy doc already holds. Reference it instead. Bad: the setup steps from `CONTRIBUTING.md` pasted in.
9. **Installed skills and plugins** — a list of what is installed. Bad: `Available skills: tdd, research, ...`
10. **Welcome text** — welcome text, intros, conclusions, or pleasantries.
    Bad: `Welcome! This file helps you work effectively in our codebase.`
11. **Prose about why** — long prose explaining why instructions matter.
    Bad: a paragraph on how following these rules keeps the team productive.
12. **Nested repeats** — nested `AGENTS.md` files that repeat root instructions.
    Bad: a nested file that restates the root's commit rule.

## Pruning

The criteria are the `writing-for-agents` skill's Context pointers, Pruning and Negation sections — read them there. Its Pruning section holds the four tests: single source of truth, environment and cache, relevance, no-ops. Its Negation section is why a rule that survives is phrased as the behaviour to perform.

## Self-check

Answer each for the file in front of you. A "no" means the file is not finished: fix the lines behind it before going on. A "no" whose cause is that the repository has none of the thing (a project with no commands, no documents to reference) is a pass; write that cause down.

| Criterion | Check |
| --- | --- |
| Commands | Is every command in the table one that `--help` and the manifest do not explain, and is none of that kind missing? Would each one run as written? |
| Orientation | Do the identity lines and External References let an agent find where things live? |
| Non-obvious patterns | Are gotchas and quirks documented? |
| Conciseness | No verbose explanations or obvious info? |
| Currency | Does it reflect current codebase state — no outdated versions, no deleted files? |
| Actionability | Are instructions executable, not vague — no template text left uncustomized, no "TODO"? |
| Single source | Does no line repeat a line of another `AGENTS.md` in this repository? |

Done when every line of every file you wrote or edited has passed the list, the four tests under Pruning, and the self-check, and every rule is phrased as the behaviour to perform or, where a prohibition had to stay, sits next to its positive target.

Next: [verify.md](verify.md).
