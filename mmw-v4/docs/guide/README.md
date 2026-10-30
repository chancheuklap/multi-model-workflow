# The MMW v4 guide

MMW v4 works best when you stop managing each step of the agent. You say what you want and how you will know it is done. [`mmw-mode`](../../skills/mmw-mode/SKILL.md) selects the component for the requested result, runs the other skills as the steps need them, and shows you the evidence. This guide teaches that habit with realistic prompts.

The chapters:

1. [Set up MMW v4](./01-setup.md). Install the skills, check the install, go back to v3, and choose a model for each role.
2. [Route work through `mmw-mode`](./02-mmw-mode.md). How every session enters it, how it selects an entry, and how to prompt it.
3. [Understand the code](./03-understand.md). The Investigation playbook, then `how`, `why` and `teach`, before anything changes.
4. [Design the change](./04-design.md). Prototypes and their sketch branch, `arena` and `code-review`, and Develop a change and its discussion, to-spec and to-tickets methods.
5. [Build and clean the change](./05-build-and-clean.md). How every change outside a night becomes one ticket: the session writes the plan, you say go, a worker builds it. Then `tdd`, `unslop` and `no-comments`.
6. [Verify and ship](./06-verify-and-ship.md). Prove the change on the real product with `control-cli`, `control-ui` and a verification skill, vet numbers with `benchmark-checklist`, and deliver one pull request through One ticket or a night, with Opening a PR.
7. [Run work while you sleep](./07-overnight.md). A spec's tickets worked unattended by dispatched workers, delivered as one pull request in the morning.
8. [Shared principles and automatic loading](./08-principles.md). The 33 shared judgments, how tasks load them automatically, and how new tasks reuse them.
9. [Make it yours](./09-make-it-yours.md). Author a skill, test it with Eval, and register problems with `register-problem`, review them through Retrospective, and stop repeated mistakes with `correct`.
10. [Recipes and pitfalls](./10-recipes-and-pitfalls.md). Prompts to copy and mistakes to skip.

Read the chapters in order the first time. After that, each chapter stands alone.

When you are stuck, or cannot tell which skill fits, type [`/mmw-help`](../../skills/mmw-help/SKILL.md) with your question:

```text
/mmw-help which skill should i use to review this branch?
```

It answers, hands you a prompt to send, and links the skill or chapter the answer came from. It does not start the work. You send the prompt when you are ready.

## If you only remember one thing

Give the agent a goal and a check that can pass or fail, in your own words:

```text
the export writes duplicate rows when a retry lands mid-run. repro first, then fix and verify.
```

You do not name a playbook or list skills. The session has already read `mmw-mode`, because every session reads it first. "repro first" and a checkable outcome are all the routing signal it needs. It prepares the change with Develop a change and the bug-fix method. It reproduces the defect and finds the cause. Then it writes one ticket, sends a worker to fix it, checks the fix on the original reproduction, and gives you one pull request to merge.

Next: [Set up MMW v4](./01-setup.md).
