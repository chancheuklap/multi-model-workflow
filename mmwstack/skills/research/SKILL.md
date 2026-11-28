---
name: research
description: "Investigate a question via primary sources with parallel reader subagents and save a research report in the repo. Use for topic research, broad surveys, multi-angle investigations, docs/API lookup, or delegated reading legwork."
---

# Research

Act as a lead researcher orchestrating parallel subagents to investigate a topic, then synthesize a grounded report yourself in the main chat. Do not spawn another agent to synthesize. All investigation findings return to the main chat.

If another agent assigned you a single track or question directly, investigate only that scope under step 3 without spawning subagents, and return your verified findings and remaining gaps to the parent agent.

## Workflow

1. Orient first: clarify scope only if genuinely ambiguous. If the topic is unfamiliar, run one quick search to map the landscape. For narrow or single-fact lookups, answer directly or use at most 2 subagents; for broad topics, decompose into 3 to 5 non-overlapping sub-questions (cap at 2 to 3 on slow or high-thinking models).
2. Gather in parallel: spawn concurrent fresh subagents using the `reader` role from the current host's section in `~/.agents/mmwstack-models.md` (or the supplied rule file) following [Subagents](../mmw-mode/SKILL.md#subagents) (use browser access when a sub-question needs full-page reads of live or authenticated pages). If subagent tools are unavailable, execute the search tracks directly. Give each subagent its work issue URL, known sources, a distinct angle, time frame, source scope, and a budget of at most 8 to 12 web searches or tool steps.
3. Keep evidence primary: tell subagents to verify claims against primary sources (official docs, source code, specs, first-party APIs) rather than search snippets or secondary write-ups, follow every claim back to the source that owns it, include exact quotes or raw outputs for key numbers, and return partial verified findings plus remaining gaps to the main chat when they hit their search budget instead of looping.
4. Resolve gaps and avoid straggler stalls: read findings as they arrive. If most subagents finish and one track stalls, cancel the stalled worker under [Subagents](../mmw-mode/SKILL.md#subagents) and move on. Run one targeted follow-up pass with `reader` subagents only if important gaps remain, and spawn a fresh `reader` verification subagent only for high-stakes or data-heavy reports.
5. Synthesize: write the final Markdown report yourself in the main chat and save it per [Save and hand over](#save-and-hand-over) (or reply directly when no repository or report path applies), using [technical-writing](../technical-writing/SKILL.md), inline clickable citations, the full question with a 2-sentence top-line summary, the investigation date, relevant versions and ticket links, and a brief Unresolved section whenever sources conflict or data is missing. When writing a report file, keep chat output to a short pointer and key decisions.

## Save and hand over

Use the invoker's explicit path or the repository's established research convention. Otherwise, save to `docs/research/<topic>/README.md`. Look for an existing report on the same question before choosing a new directory. Continue that report when the question is the same.

For the default structure:

- Name `<topic>` with the subject and question keywords, using lowercase English words joined by hyphens, such as `codex-cloud-usage`. Keep dates, ticket numbers, and branch names in the report rather than the directory name.
- Write the complete report in `README.md`. Put an optional HTML explanation in `overview.html` beside it, and necessary small attachments in `assets/`. Create those only when needed.
- Add the report's link to `docs/research/README.md` under the full question. This index holds titles and links. The report holds the findings.

Keep large logs, media, caches, and temporary downloads in `.scratch/<topic>/` or the OS temporary directory. Retain the safe excerpt or stable controlled-storage link needed to support a conclusion that cannot be reproduced. Keep credentials and raw customer data out of commits.

Link the saved report from its work issue once the files are accessible there. In a separate checkout, return the files or a pushed commit the invoker can integrate.

Done when the invoker can retrieve the cited report, its necessary attachments, and the index link required by the chosen convention.
