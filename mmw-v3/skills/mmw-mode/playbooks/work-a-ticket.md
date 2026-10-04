### Work a ticket

**You own one ticket, as its worker, from its claim to its closing comment; its reviewer is dispatched from here.** A script started you on it and nobody is watching, so the mode's **Unattended** paragraph holds from the first step. Distinct from Review a ticket, which judges this work and writes nothing but its report.

Commands of the `verify-ticket` skill's `verify-ticket.py` and the `dispatch` skill's `dispatch.sh` are named bare below.

1. **Claim the ticket and find your step.** Run `verify-ticket.py <n> --preflight`. On `NOT_READY`, stop: the reason is already on the ticket, as a `ticket.refused` event that wakes the orchestrator. A `RESUME:` line names, by its title, the step below to carry on at; where you are is what the ticket's events say, not what this session remembers. With no `RESUME:` line, go on to the next step.
   Done when `--preflight` claimed the ticket and you are at the step its `RESUME:` line names or the next one, or it printed `NOT_READY` and you stopped.
2. **Read yourself in and write the code.**
   <!-- Shell. Source in MMW v2 at 9df1ab67d: mmw-v2/upstream/skills/engineering/implement/SKILL.md `## Claim, read in, write the code` and `## Shared experience while implementing` (the Memory indexes the start prompt carries), with references/saving-memory.md and references/writing-interface-code.md. A lesson on how a worker works writes it. -->
3. **Integrate and run every criterion.** A run that exits 3 found no product slot free and ran nothing: end your turn, and when `#<n> worker.queued` wakes you, do the `dispatch` skill's `## On waking`, then run the same command again.
   <!-- Shell for the rest of the step. Source: implement's `## Closing steps` step 1 (`dispatch.sh integrate <n>`, `verify-ticket.py <n>`, how many rounds a criterion gets, the `ABANDON` kinds). -->
   Done when `verify-ticket.py <n>` has recorded a run of your own after the integration.
4. **Post the decisions comment.**
   <!-- Shell. Source: implement's `## Closing steps` step 2 (`verify-ticket.py <n> --decisions <file>`). -->
5. **Start the reviewer.** Run `dispatch.sh start <n> reviewer`, then end your turn. One reviewer per round. Exit 2 whose stderr says to start again: run it once more. Any other exit 2, or a second one: the pipeline is at fault, so open a `fault` child as the `verify-ticket` skill's `references/sub-issues.md` says, and stop.
   Done when `start` exited 0 and your turn has ended, or the `fault` child is open.
6. **Read the review.** When `#<n> reviewer.reported` wakes you, do the `dispatch` skill's `## On waking`, then read the report: `dispatch.sh wait <n> reviewer` prints the event with the two commits it read. When `#<n> reviewer.lost` wakes you instead, the reviewer died with no report: do `## On waking`, then go back to **Start the reviewer**.
   <!-- Shell for the rest of the step. Source: implement's `## Closing steps` step 3 after the wake (the in-ticket round of fixes, `refuted:`, a `finding` child for each out-of-ticket finding still true). -->
   Done when the report is read and its wake acked.
7. **Run every criterion one final time.**
   <!-- Shell. Source: implement's `## Closing steps` step 4 (`verify-ticket.py <n> --reverify --actor worker`). -->
8. **Audit.**
   <!-- Shell. Source: implement's `## Closing steps` step 5. -->
9. **Tell the tickets whose files you changed.**
   <!-- Shell. Source: implement's `## Closing steps` step 6 (`verify-ticket.py <n> --touched`). -->
10. **Write the closing-comment draft.**
    <!-- Shell. Source: implement's `## Closing steps` step 7 (`verify-ticket.py <n> --draft`). -->
11. **Close the ticket.** Run `verify-ticket.py <n> --closeout <draft>`. It posts the closing comment and puts `ticket.passed` or `ticket.returned` on the ticket, which wakes the orchestrator to land it. Never close the ticket or swap its labels yourself: a hook blocks the command. Open no pull request, and do not run `land` from this session: it stops every session the ticket's events name, this one included.
    Done when `--closeout` exits 0.

**Reply:** the closing comment `--closeout` posted is this run's reply; this session's own last message is read by nobody.
