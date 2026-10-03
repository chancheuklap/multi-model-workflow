# Checks for what a script prints for an agent

For what a script prints for an agent: a refusal, a status line, a next step. These apply on top of `references/checks.md`.

- A refusal follows `CODING_STANDARDS.md`, and its next step fits the skill that receives it.
- Hosts cut long output before the agent sees it, so the next step sits in the first lines.
- The suggested next step is safe to run as written.
