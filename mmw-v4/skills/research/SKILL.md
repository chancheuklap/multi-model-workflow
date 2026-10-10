---
name: research
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

Investigate a question against high-trust primary sources and capture the findings as one Markdown file. The session that briefed you reads it and nothing else of yours. When your brief is a research ticket of a map, that session also saves the file unchanged as the map's research note, which later sessions read with nothing else of this run: the file stands on its own and names the question it answers.

The brief's question is your whole scope: answer it, and decide nothing it does not ask. Read only. Change no file of the repository, and run nothing that changes state but the report command your brief ends with.

| Your brief | Work by |
| --- | --- |
| gives one angle of a question about how the repository's code works | `references/explorer.md`, then the steps below, with its Output in place of step 2's `## Answer` |
| assigns you one evidence source for why the repository's code is the way it is | `references/investigator.md`, then the steps below, with its Output Format in place of step 2's `## Answer` |
| asks anything else | the steps below |

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file in the operating system's temporary directory, citing each claim's source. Open it with `## Answer`: at most three sentences a reader can act on.
3. A brief that ends with a report command takes this file as your answer: report it. With no brief, say where the file is.

Done when the report command has printed `reported brief …`, or, with no brief, you have said where the file is.
