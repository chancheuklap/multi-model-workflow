---
name: research
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

Investigate a question against high-trust primary sources and capture the findings as one Markdown file. The session that briefed you reads it and nothing else of yours, and may keep it unchanged where later sessions read it with nothing else of this run: the file stands on its own and names the question it answers.

The brief's question is your whole scope: answer it, and decide nothing it does not ask. Read only. Change no file of the repository but the answer and the files beside it that your brief's closing lines name, and run nothing that changes state except the browser session step 1 names and the report command your brief ends with.

| Your start prompt has you follow | Work by |
| --- | --- |
| this skill's `references/explorer.md` | that file, then the steps below, with its Output in place of step 2's `## Answer` |
| this skill's `references/investigator.md` | that file, then the steps below, with its Output Format in place of step 2's `## Answer` |
| this skill | the steps below |

1. Apply **principle-read-before-you-conclude**, and **principle-guard-the-context-window** when reading large source material. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it. If a page returns only a JavaScript shell, times out, or returns HTTP 403, read its body with `playwright-cli -s=<session name from the brief footer>`. Use that browser session name only; do not start another name.
2. Write the findings to a single Markdown file, citing each claim's source: at the path your brief's closing lines name, with every file you made or saved for it in the directory they name beside it; with no such path, in the operating system's temporary directory. Open it with `## Answer`: at most three sentences a reader can act on.
3. A brief that ends with a report command takes this file as your answer: report it. With no brief, say where the file is.

Done when the report command has printed `reported brief …`, or, with no brief, you have said where the file is.
