---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

# Research

When a card assigns this question to you, investigate it and write the notes file. That work is below.

When no card has assigned the question, resolve `../../tools/dispatch/scripts/dispatch.sh` from this file and run `dispatch.sh spawn researcher --host HOST --question FILE` in the consuming repository. HOST is `cursor` or `codex`. Hand the printed card to Task. When it has `run_in_background` set, continue your own work.

## Investigate

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source. Call the Skill tool with "technical-writing" and write that file through it.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

Done when the notes file exists and every claim in it cites the source that owns it.
