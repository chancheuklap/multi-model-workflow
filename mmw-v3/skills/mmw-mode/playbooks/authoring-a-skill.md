### Authoring or modifying a skill

**You own the change. Write it, check it, deliver it.**

1. **Write it.** Follow the `writing-skill-sets` skill in this session to write the change: it places each passage, writes it, validates it, and has a fresh agent walk the tasks it touches.
   Done when that skill has handed back what was written and where, what was deleted, each check with its command and result, and the walk, or that the walk is not done.
2. **Verify it.** Follow the `verify-this` skill in this session on the claim that the changed text does what the change was for; the walks from **Write it** are its baseline and treatment.
   Done when `verify-this` has returned `VERIFIED` on the final text, or `INCONCLUSIVE` because the walk is not done, which the Reply states.
3. **Deliver.** Run `playbooks/deliver-a-change.md`.
   Done when that playbook is done.

**Reply:** what the `writing-skill-sets` skill handed back; the `verify-this` verdict and its evidence, on a line of their own; and what remains of the delivery.
