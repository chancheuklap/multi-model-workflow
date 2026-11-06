---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

# Research

When another agent assigns you this question, investigate it and write the notes file. That work is below.

Otherwise, write a prompt asking a **fresh agent** to use **research** for the question and its sources. Save it to a file, run `dispatch.sh spawn researcher --prompt FILE --host HOST`, and send the printed assignment to that fresh agent with a new context that does not inherit your conversation, as [Dispatch](../dispatch/SKILL.md) describes. Continue your own work while the researcher runs.

## Investigate

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source. Use **technical-writing** for the notes.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

Done when the notes file exists and every claim in it cites the source that owns it.
