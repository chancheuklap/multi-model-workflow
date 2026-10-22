### Retrospective

**You own the retrospective of one run, from its gathered evidence to proposals the owner can decide.** Run after a night or one ticket, or on the owner's request for a named spec or ticket. Every registration and signal must have a disposition. A proposal asks for a decision, not permission to implement it.

Unlike Opening a PR, this playbook investigates a run's unresolved problems and proposes solutions; it implements none. Opening a PR presents those proposals with the delivered work for the owner's decision.

On re-entry, read the run's retrospective progress comment for its material directory and batch identifier before starting again. Use `dispatch.sh brief show <batch>` on an existing batch. If analysts are still running, end your turn and wait for its wake; if all have reported or been lost, continue at **Check and apply the answers**. If a send was interrupted before its identifier was recorded, inspect the existing batch records described by the `dispatch` skill's `scripts/briefs.py` header, matching the sender and the run's material path in its briefs, and adopt that batch. Start no second batch for the same unfinished retrospective. A recorded batch that is absent with no preserved answers is a failure, not a fresh run.

`retro.py` below is the `retro` skill's `scripts/retro.py`; `dispatch.sh` is the `dispatch` skill's `scripts/dispatch.sh`. Pass the product and MMW repository slugs once each to expire and gather, removing duplicates. When the product repository is MMW itself, pass its slug only once. Use the installed skills. In a self-hosted run, the repository's `AGENTS.md` `## Self-hosting boundary` keeps that runtime frozen.

1. **Expire candidates.** Run `retro.py expire <distinct owner/repo>…`.
   Done when expire succeeds, or its failure goes to **Record the outcome**.
2. **Gather the run.** From the product checkout, run `retro.py gather --spec <spec> <distinct owner/repo>… --out <material directory>` for a night, or replace `--spec <spec>` with `--ticket <n>` for one ticket. Preserve the generated `context.json` and comment on the run with the material directory before dispatch. If every angle has no material, go to **Record the outcome** with zero dispositions.
   Done when the material paths and counts are available, or the failure goes to **Record the outcome**.
3. **Send the analysts.** Write one brief for each angle with material. Its `## Task` opens with the corresponding sentence below, then asks for that angle's sorting. `## Known` names the material file, the generated context path, and the run's circumstances. `## For` says the owner will decide which proposals to implement.

   | Angle | First sentence of `## Task` |
   | --- | --- |
   | 判断 | Follow the retro skill's references/judgement.md. |
   | 环境 | Follow the retro skill's references/environment.md. |
   | 流程 | Follow the retro skill's references/process.md. |

   Send all these briefs in one batch with `dispatch.sh send retro-analyst --follow "the brief" <brief>…`, record the returned batch identifier in the run's retrospective progress comment, then end your turn. The dispatch footer tells each analyst how to report its answer.
   Done when the batch is started and your turn has ended, or the failure goes to **Record the outcome**.
4. **Check and apply the answers.** On `brief <batch> done`, follow steps 1 through 3 of the dispatch skill's `## On waking` to read the answers and ack the wake. Leave `## Problems` registration to apply, which registers these as `retro-signal`; running the generic waking step's add first would register each occurrence twice and undercount new registrations. Open every row's evidence and check its conclusion against it. Change a row you disagree with to `candidate` and state why. Reconcile conflicting rows about one cause. Account for each gathered signal, including new registrations in `## Problems`, before running `retro.py apply <answer file>… --context <material directory>/context.json`. If a session was lost without an answer, record the missing angle as a failure rather than treating it as empty material. Close the brief batch with `dispatch.sh brief close <batch>` once its answers are preserved and no longer needed there.
   Done when every registration and signal has a checked disposition and apply succeeds, or the failure goes to **Record the outcome**.
5. **Record the outcome.** Read the `spec.retroed` or `ticket.retroed` receipt apply wrote. For a gather with no material, write an empty answer table in the material directory with the retro skill's `## Analyst instructions` columns and `## Problems` set to `None`, then run apply with that answer and the generated context to record zero dispositions. Keep the receipt's evidence limits, counts and problem list in the result.

   If any step failed, record the command and concrete reason. Use the `verify-ticket` skill's `scripts/events.py emit` to build the run's `spec.retroed` or `ticket.retroed` with `result=unrecorded` and `reason`, then post its comment body to the spec or ticket with `gh issue comment --body-file <file>`. If recording also fails, put both failures in the reply or PR. A retrospective failure does not block merging. Return the receipt to the calling playbook for its page, without a reply of this playbook's own; a standalone retrospective ends with its reply below.
   Done when every registration and signal has a disposition in the receipt, including a zero result, or the failure and its missing coverage are recorded for the owner.

**Reply:** the new proposals with links, their solutions and your recommendations; the number and query link for earlier unanswered lessons; each recurrence after the owner's refusal; counts of new registrations, merges, recurrences after refusal, and previously approved proposals that landed; any failure or unreadable evidence.
