### Retrospective

**You own the retrospective of one run, from its gathered evidence to proposals the owner can decide.** Run after a night or one ticket, or on the owner's request for a named spec or ticket. Every registration and signal must have a disposition. A proposal asks for a decision, not permission to implement it.

`retro.py` below is the `retro` skill's `scripts/retro.py`; `dispatch.sh` is the `dispatch` skill's `scripts/dispatch.sh`. Use the installed skills. In a self-hosted run, the repository's `AGENTS.md` `## Self-hosting boundary` keeps that runtime frozen.

1. **Expire candidates.** Run `retro.py expire <product owner/repo> <MMW owner/repo>`.
   Done when expire succeeds, or its failure goes to **Record the outcome**.
2. **Gather the run.** From the product checkout, run `retro.py gather --spec <spec> <product owner/repo> <MMW owner/repo> --out <material directory>` for a night, or replace `--spec <spec>` with `--ticket <n>` for one ticket. Preserve the generated `context.json`. If every angle has no material, go to **Record the outcome** with zero dispositions.
   Done when the material paths and counts are available, or the failure goes to **Record the outcome**.
3. **Send the analysts.** Write one brief for each angle with material. Its `## Task` opens with the corresponding sentence below, then asks for that angle's sorting. `## Known` names the material file, the generated context path, and the run's circumstances. `## For` says the owner will decide which proposals to implement.

   | Angle | First sentence of `## Task` |
   | --- | --- |
   | 判断 | Follow the retro skill's references/judgement.md. |
   | 环境 | Follow the retro skill's references/environment.md. |
   | 流程 | Follow the retro skill's references/process.md. |

   Send all these briefs in one batch with `dispatch.sh send retro-analyst --follow "the brief" <brief>…`, then end your turn. The dispatch footer tells each analyst how to report its answer.
   Done when the batch is started and your turn has ended, or the failure goes to **Record the outcome**.
4. **Check and apply the answers.** On `brief <batch> done`, follow the dispatch skill's `## On waking` to read the answers and ack the wake. Open every row's evidence and check its conclusion against it. Change a row you disagree with to `candidate` and state why. Reconcile conflicting rows about one cause. Account for each gathered signal, including new registrations in `## Problems`, before running `retro.py apply <answer file>… --context <material directory>/context.json`. If a session was lost without an answer, record the missing angle as a failure rather than treating it as empty material. Close the brief batch with `dispatch.sh brief close <batch>` once its answers are preserved and no longer needed there.
   Done when every registration and signal has a checked disposition and apply succeeds, or the failure goes to **Record the outcome**.
5. **Record the outcome.** Read the `spec.retroed` or `ticket.retroed` receipt apply wrote. For a gather with no material, write an empty answer table in the material directory with the retro skill's `## Analyst instructions` columns and `## Problems` set to `None`, then run apply with that answer and the generated context to record zero dispositions. Keep the receipt's evidence limits and counts in the result.

   If any step failed, record the command and concrete reason. Use the `verify-ticket` skill's `scripts/events.py emit` to build the run's `spec.retroed` or `ticket.retroed` with `result=unrecorded` and `reason`, then post its comment body to the spec or ticket with `gh issue comment --body-file <file>`. If recording also fails, put both failures in the reply or PR. A retrospective failure does not block merging. Return to the calling playbook; a standalone retrospective ends with its reply.
   Done when every registration and signal has a disposition in the receipt, including a zero result, or the failure and its missing coverage are recorded for the owner.

**Reply:** the new proposals with links, their solutions and your recommendations; the number and query link for earlier unanswered lessons; each recurrence after the owner's refusal; counts of new registrations, merges, recurrences after refusal, and previously approved proposals that landed; any failure or unreadable evidence.
