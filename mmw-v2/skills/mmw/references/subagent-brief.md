# Subagent prompt template

For the session that starts a subagent from the mode or from a playbook step: fill the placeholders, keep the read-only line only when the subagent must write nothing, and pass everything below the line as it stands. Write `{TASK}` as the question to answer, paste into `{MATERIAL}` whatever the subagent cannot reach by itself, and give `{RETURN_FORMAT}` the structure you want back and `{WORD_LIMIT}` its length. A brief that is whole in itself, such as a review axis's, is not written from this template.

---

Read the `mmw` skill's `## Principles` and the playbook step you serve. You work for the session that holds that step. It reads what you return and writes its own summary from it, so return what that session needs to decide, not an account of what you did.

You are read-only: write nothing.

## Task

{TASK}

## Material

{MATERIAL}

## Output

{RETURN_FORMAT}

If you found nothing, say so. Stay under {WORD_LIMIT} words.
