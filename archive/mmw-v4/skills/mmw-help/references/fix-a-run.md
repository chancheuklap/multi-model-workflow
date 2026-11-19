# Fix a run that went wrong

| Symptom | Fix |
|---|---|
| A question got treated as the next step of the last task | Say "new task". |
| A new model choice had no effect | `models.py config set` takes effect at the next start of that role; a session already running keeps its model. |
| A skill's new description had no effect | A host reads descriptions at session start. Start a new session. |
| Runs cost more than expected | Read [Get set up](get-set-up.md) for the cost choices. |
| Parallel agents overwrote each other | Give each agent its own worktree. |
| A night moved but closed no ticket | Each ticket needs criteria a command decides. See guide page 7 (`mmw-v4/docs/guide/07-overnight.md`). |
| The reply claims success from a green build | Ask for the real command, flow, stored value, or profile. That's the prove-it-works principle. |

For a run that drifts, [`references/prompting.md`](prompting.md) has one-line steers. Guide page 10 (`mmw-v4/docs/guide/10-recipes-and-pitfalls.md`) has more pitfalls and the recipes worth copying.
