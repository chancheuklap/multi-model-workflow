---
name: mmw-help
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# MMW help

Answer the user's question about MMW, hand them a prompt they can send, and link the file the answer came from. For a help question, don't start the work. The user asked how, and a run spends real tokens, so let them send the prompt.

A message that asks for work, such as "fix this bug", is not a help question: do the work.

This file maps questions to the skills and guide pages that hold the answers. Those files own the details. Read the file you route to before you quote it, and trust it when it disagrees with this map. Give the user each file's path in the toolbox checkout, the directory above the one `~/.mmw/installed-root` names.

## Find out what they need

Infer the need from the message and the conversation. A named situation, such as "which skill reviews a diff?", goes straight to its reference. If the need is still unclear, ask one multiple-choice question with these options, then answer only the selected question:

- Get set up
- Start a task
- Pick a skill
- Fix a run that went wrong
- Make MMW my own

Check the state that changes the answer, and mention it only when it does:

- No `~/.mmw/models.json` means install has not run on this machine, so no dispatched role can start.
- No `verify-*` skill or other app harness in the project means agents have no scripted way to drive the app. Mention the **create-verification-skill** skill when the question is about proving a change works.

| Question | Read |
| --- | --- |
| Get set up | [Method](references/get-set-up.md) |
| Start a task | [Method](references/start-a-task.md) |
| Pick a skill | [Method](references/pick-a-skill.md) |
| Playbooks and principles | [Method](references/playbooks-and-principles.md) |
| Fix a run that went wrong | [Method](references/fix-a-run.md) |
| Make MMW my own | [Method](references/make-mmw-my-own.md) |

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
