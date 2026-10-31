# Playbooks and principles

Playbooks are step lists inside the **mmw-mode** skill, not skills. Describing the task picks one; the `## Playbooks` of the mode's `references/handling-a-request.md` is the one list of which task goes to which playbook, so read it there rather than answering from memory. Guide page 5 (`mmw-v4/docs/guide/05-build-and-clean.md`), page 6 (`mmw-v4/docs/guide/06-verify-and-ship.md`) and page 7 (`mmw-v4/docs/guide/07-overnight.md`) show how a change is built, delivered as one pull request, and run unattended overnight.

Planning here is a spec and its tickets, because the owner checks those, not code. Develop a change reuses settled work, calls Grill with docs or wayfinder for missing decisions, to-spec for a spec when needed, and to-tickets for independent or batch tickets. Ready work enters One ticket or Run a night directly. For a design question, the **prototype** skill settles it in code first.

Principles are one-rule skills that the mode indexes in its `## Principles` and applies when their conditions arise. The user rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output." Guide page 8 (`mmw-v4/docs/guide/08-principles.md`) lists them.
