### Deliver a change

This playbook hands over a finished change the way the repository takes changes. A change that stops short of that way is not delivered, however finished it looks in this session: in a repository that releases through a playbook of its own, an edit reaches no user until that playbook has run.

1. **Find how this repository takes changes.** In a ticket's worktree, the ticket's closeout delivers the change, and this playbook does not apply. Anywhere else, read the `delivery` key of `.mmw/target.json`. With `commit`, with no `delivery` key, or with no `.mmw/target.json` at all, the way is to commit to the current branch and tell the user. With `playbook:<slug>`, the way is the repository's own playbook in `.mmw/playbooks/<slug>.md`. Any other value, or a `<slug>` with no such file, is a fault in `.mmw/target.json`: tell the user what it holds, and deliver nothing until they say which way to take.
   Done when you know which of the two ways this repository takes the change, or you are in a ticket's worktree and have stopped, or the user has been told what is wrong with `delivery`.
2. **Deliver.** Deliver the change the way **Find how this repository takes changes** found. In the reply, name each step only the user can take as what remains (`principles/principle-human-steps-stay-human.md`). When the change edits a skill's `description`, tell the user to open a new session: a host reads skill descriptions only when a session starts.
   Done when the change is committed, or every step of the repository's own playbook that this session can take has run, and the user has heard each step that remains.

**Reply:** the commit id; how far the delivery went; what remains, and who takes it.
