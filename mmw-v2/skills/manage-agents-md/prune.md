# Prune

All branches. The files are written. Now read each one you wrote or edited line by line: first against the list of what must not be there, then with the four tests under Pruning, then through the self-check.

Only add information that will genuinely help future sessions. The context window is precious - every line must earn its place.

On the **incremental** branch the maintainer-owned lines named in [incremental.md](incremental.md) are exempt: read them, leave them, and put a doubt about one into the report.

## What NOT to Add

Each rule, then what it catches.

1. **Obvious code info** — what the code already says.
   Bad: `The UserService class handles user operations.` The class name already tells us this.
2. **Discoverable from code** — cut any instruction the agent can discover from existing code patterns. LLMs are in-context learners — if your codebase consistently uses a pattern, the agent will follow it after a few searches.
   Bad: `Use named exports.` Every file in `src/` already does.
3. **Generic best practices** — universal advice, quality slogans, "follow best practices".
   Bad: `Always write tests for new features.` `Use meaningful variable names.`
4. **One-off fixes** — won't recur; clutters the file.
   Bad: `We fixed a bug in commit abc123 where the login button didn't work.`
5. **Verbose explanations** — verbose explanations when a one-liner suffices.
   Bad: `The authentication system uses JWT tokens. JWT (JSON Web Tokens) are an open standard (RFC 7519) that defines a compact and self-contained way for securely transmitting information between parties as a JSON object. In our implementation, we use the HS256 algorithm which...`
   Good: `Auth: JWT with HS256, tokens in `Authorization: Bearer <token>` header.`
6. **Linter territory** — anything a linter, formatter, typechecker, or pre-commit hook can enforce. When you cut one, suggest a pre-push or pre-commit hook in the report.
   Bad: `Use camelCase for variables, PascalCase for components.`
7. **Code snippets** — cut code snippets. They go stale and bloat the file. Use file path references instead (e.g., "see `src/utils/example.ts` for the pattern").
   Bad: a ten-line example handler.
8. **Copies of other documents** — content that `README.md`, `CONTRIBUTING.md`, or a policy doc already holds. Reference it instead.
   Bad: the setup steps from `CONTRIBUTING.md` pasted in.
9. **Installed skills and plugins** — a list of what is installed.
   Bad: `Available skills: tdd, research, ...`
10. **Welcome text** — welcome text, intros, conclusions, or pleasantries.
    Bad: `Welcome! This file helps you work effectively in our codebase.`
11. **Prose about why** — long prose explaining why instructions matter.
    Bad: a paragraph on how following these rules keeps the team productive.
12. **Nested repeats** — nested `AGENTS.md` files that repeat root instructions.
    Bad: a nested file that restates the root's commit rule.

## Pruning

- Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place edit. **Duplication** (the same meaning in more than one place) costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank. (The accidental inverse of a leading word, which repeats a token on purpose, never the meaning.)
- The **environment** is a source of truth too (`package.json` scripts, config files, the directory layout, `--help` output), and a document that restates it is a **cache**: a copy of a lookup, earning its load only when the lookup is expensive. Cache what the agent cannot find by looking: the unwritten convention, the reason behind a choice, the gotcha no config confesses. Leave the one-file, one-command lookups to the environment, where they cannot go stale.
- Check every line for **relevance**: does it still bear on what the document does? A line loses relevance by never bearing on the task (mere exposition, or a branch that should be disclosed) or by going stale as the behaviour or world it describes changes. Shorter documents are easier to keep relevant. Without a pruning discipline the default fate is **sediment**: stale layers that settle because adding feels safe and removing feels risky, until you must core down through them to find what is still live.
- Hunt **no-ops** sentence by sentence: an instruction the model already obeys by default pays load to say nothing. The test (does it change behaviour versus the default?) is model-relative, not reader-relative: two people disagreeing about a no-op disagree about the default, and settle it by running the document, not by debate. When a sentence fails, delete the whole sentence rather than trim words from it. The test also grades leading words: a word too weak to beat the default (_be thorough_ when the agent is already thorough-ish) is a no-op, and the fix is a stronger word (_relentless_), not a different technique.

## Negation

**Negation** is the failure mode beside this lever: steering by prohibition drags the forbidden behaviour into context and makes it _more_ available, not less. _Don't think of an elephant_, and the elephant is all there is; the negation is a weak modifier the strongly-activated concept overruns, so the ban half-reads as an instruction to do the thing. Prompt the **positive**: state the target behaviour ("write one-line comments") so the banned one is never spoken. A prohibition earns its place only as a hard guardrail you cannot phrase positively; even then, pair it with the positive target so attention lands on what to do.

## Self-check

Answer each for the file in front of you. A "no" sends you back to the section it names. A "no" whose cause is that the repository has none of the thing (a project with no commands, no documents to reference) is a pass; write that cause down.

| Criterion | Check |
| --- | --- |
| Commands | Is every command in the table one that `--help` and the manifest do not explain, and is none of that kind missing? Would each one run as written? |
| Orientation | Do the identity lines and External References let an agent find where things live? |
| Non-obvious patterns | Are gotchas and quirks documented? |
| Conciseness | No verbose explanations or obvious info? |
| Currency | Does it reflect current codebase state — no outdated versions, no deleted files? |
| Actionability | Are instructions executable, not vague — no template text left uncustomized, no "TODO"? |
| Single source | Does no line repeat a line of another `AGENTS.md` in this repository? |

Done when every line of every file you wrote or edited has passed the list, the four tests under Pruning, and the self-check.

Next: [verify.md](verify.md).
