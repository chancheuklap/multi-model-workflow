# Checks for a description

For a skill's frontmatter `description`. These apply on top of `references/checks.md`.

- A description carries the trigger and nothing else: what the skill is, and the branches on which to load it (`writing-for-agents` `SKILL.md` `## Context pointers`); a user-invoked skill's is a one-line summary for the person (`writing-for-agents` `SKILL-MECHANICS.md` `## Invocation`). Routing (which role's file, which row of a command table, which reference), usage, process and outputs belong to the body; a description carrying them is a finding. A branch naming the role an agent was started as ("when you were started as the advisor") is a trigger.
- Read every description in the set side by side, also in a partial review. Two descriptions that claim the same job are a conflict. A caller and the skill it hands to may share a trigger word when each description names only its own part of the job.
- A description names no host and no runner: every host scans it into its system prompt, so one name ties the skill to that host or runner. A runner that cannot start is refused by its script at run time.
- A skill this repository wrote has no host-side manifest beside it (upstream skills keep their `agents/openai.yaml`), so its name and description have one authority. The `disable-model-invocation` pairing on upstream skills is in `mmw-v2/merge-notes/README.md`.
