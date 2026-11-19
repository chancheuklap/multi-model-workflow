# Start a task

Every session reads the **mmw-mode** skill in full before anything else; its description says so. The mode selects a workflow from Playbooks or an independently requested method from Requested results in references/handling-a-request.md, reads its complete instructions, and follows them. A workflow calls other skills at the steps that need them. A good prompt states the goal and how to tell it's done. It doesn't list skills, because a hand-written sequence tends to drop or reorder steps the playbook would keep. Read [`references/prompting.md`](prompting.md) before you help word one. Guide page 2 (`mmw-v4/docs/guide/02-mmw-mode.md`) has examples.

Mid-session, starting a message with "new task" tells the session to match a fresh playbook.
