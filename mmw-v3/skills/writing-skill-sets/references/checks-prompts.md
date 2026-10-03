# Checks for a prompt written for another agent

For a start prompt, a subagent's brief, and the template either is written from. These apply on top of `references/checks.md`.

- A start prompt carries only what is known when the agent is started (the ticket number, a base commit, where the task came from). Rules reach the agent through the skill it loads; a ticket or spec is named and read from the tracker, not retold. A brief a model writes from a template counts as a start prompt, and the template lists everything the receiver needs.
- Everything an agent must apply reaches it by one of two means: a skill or file its prompt tells it to load, or text pasted into the prompt. A rule the prompt says the agent applies, delivered by neither, is a broken hand-off. A rule stated both in a skill and in a prompt a script builds is duplication; the prompt keeps the data.
- A subagent's brief states what it returns and its length (upstream `code-review`: "Under 400 words"), so its report fits the caller's attention.
