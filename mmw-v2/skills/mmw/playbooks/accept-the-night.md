### Accept the night

**The user owns acceptance and the release decision.**

This playbook takes a night that has run to the user's decision. The user accepts a night from what this session tells them and from the tracker, without reading its code, and nothing the night landed reaches the project branch until they accept it. Whatever the account leaves out, the user accepts unseen, because `finish` merges every ticket the night landed.

**Entry.**
- **Handed the night.** **Run a night** ends by handing the night to the user, and `dispatch.sh where <spec>` points here once the spec carries `spec.retroed`. Start at **Read the night out**.
- **Asked about a night.** The user asks what a night that has run left them: the morning queue, acceptance, `finish`. Start at **Read the night out**.
- **Unattended.** This playbook runs with the user present. An unattended session that reaches it runs none of its steps: acceptance and `finish` wait for the user.

1. **Read the night out.** (judgement) Read `NIGHT SUMMARY` and `NIGHT RETRO`, and give the user what acceptance turns on: each ticket of the batch that did not close and the reason recorded on it, and each problem the retro recorded.
   Tell the user that after they accept the result **Merge the accepted night** runs `finish` to merge it into the project branch.
   Done when the user has heard, for each ticket of the batch that did not close, its number and the reason recorded on it.
2. **Work the needs-triage queue.** List the open issues labelled `needs-triage`, oldest first, and run the `triage` skill on each.
   An issue labelled `mmw:child` or `mmw:ticket`, or a retro proposal (title `Retro #<spec>: …`), came from this repository's own pipeline: read `references/pipeline-issues.md` first; it replaces the reproduction in the `triage` skill's **Verify the claim** and adds destinations to its **Apply the outcome**.
   A child whose default was right, or whose fix is already on the base branch, is closed through `dispatch.sh resolve-child <ticket> <child> fixed` or `stale <invalid|fixed-elsewhere>` so its ticket records the route; `wontfix` means nobody will do it, not that it is done.
   Done when each issue the list returned has an outcome the user agreed to, or the user has said it waits.
3. **Put the retro proposals to the user.** Put each proposal `NIGHT RETRO` records to the user with the problem and the evidence it cites, and take the user's answer.
   An approved proposal that changes a skill, a playbook or other text an agent reads goes to **Authoring or modifying a skill**; any other approved proposal goes to **Write a spec and tickets**.
   Done when each proposal the retro recorded has the user's answer, and the user knows which playbook takes each approved one.
4. **List what only the user can do.** List the open issues labelled `ready-for-human`, and tell the user each one's title and what it asks of them (**principle-human-steps-stay-human**).
   Done when the user has that list, one line per issue, or has heard that none is open.
5. **Merge the accepted night.** Only after the user has accepted the result, run `dispatch.sh finish <spec>`.
   A worktree that has the base branch checked out, usually the one this session runs in, is kept: stderr gives the commands that remove it, for the user to run once this session is done, and `finish` needs no second run.
   Exit 0: the merge is recorded. Exit 1: the merge conflicted or the repository checks failed, and nothing was pushed or deleted. Exit 2: fix what stderr names and run `finish` again. Do not merge the project branch into the repository default branch here; that remains the user's release decision.
   On exit 1, give the user the files or the checks stderr names: the night stays unmerged until they are fixed and `finish` runs again.
   Done when `finish` has exited 0 and the user has every command its stderr gave.

**Reply:** each `needs-triage` issue with the outcome the user agreed to; the `ready-for-human` list; the line `finish` printed, and the commands its stderr left for the user to run.
