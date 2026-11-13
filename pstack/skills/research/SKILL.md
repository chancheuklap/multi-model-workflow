---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
disable-model-invocation: true
---

# Research

When another agent assigns you this question, investigate it and return the report and its attachments. That work is below.

Otherwise, spawn one fresh general-purpose subagent. Give it the question, its work issue URL, known sources, the report location and a readable path to this skill. Use the `judgment and prose` role from the [setup-pstack](../setup-pstack/SKILL.md#model-rule) model rule. Continue your own work while the researcher runs.

## Investigate

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown report, citing each claim's source. Open with the full question and a short, actionable answer. State the investigation date and any relevant versions and ticket links. Name what remains unverified. Use [technical-writing](../technical-writing/SKILL.md) for the report.

## Save and hand over

Use the caller's explicit path or the repository's established research convention. Otherwise, save to `docs/research/<topic>/README.md`. Look for an existing report on the same question before choosing a new directory. Continue that report when the question is the same.

For the default structure:

- Name `<topic>` with the subject and question keywords, using lowercase English words joined by hyphens, such as `codex-cloud-usage`. Keep dates, ticket numbers, and branch names in the report rather than the directory name.
- Write the complete report in `README.md`. Put an optional HTML explanation in `overview.html` beside it, and necessary small attachments in `assets/`. Create those only when needed.
- Add a link to the report in `docs/research/README.md`, using the report's full question as the link title. This index holds titles and links. The report holds the findings.

Keep large logs, media, caches, and temporary downloads in `.scratch/<topic>/` or the OS temporary directory. Retain the safe excerpt or stable controlled-storage link needed to support a conclusion that cannot be reproduced. Keep credentials and raw customer data out of commits.

Return the report path and its attachments for inclusion in the calling task's repository changes. In a separate checkout, return the files or a pushed commit the caller can integrate. The caller links the report from its work issue once the files are accessible there.

Done when the caller can retrieve the cited report, its necessary attachments, and the index link required by the chosen convention.
