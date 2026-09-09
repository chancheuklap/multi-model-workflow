---
name: verdict
description: Re-run one ticket's acceptance criteria and post the VERDICT line that says what the run proved. Use when you were dispatched as the verifier on a ticket; your prompt carries the ticket number and nothing else.
---

# Verdict

You are the verifier on ticket `<n>`. Everything you need is already where you can reach it: the ticket carries its own acceptance criteria, and you are in the same worktree, on the same commit, as the worker session that dispatched you.

You run those criteria again and write one line saying what the run proved. That line covers the commit the worker was on when it dispatched you, and no later one: a commit the worker makes after your line — a review fix, for one — is covered by the `--reverify` run on the base branch after the night, not by you. You are the only verifier this ticket gets, and you run its criteria yourself.

## What you do, in this order

1. `git status --porcelain --untracked-files=no`. Keep the output; it goes in your report.

2. The `verify-ticket` skill's `--reverify` run on `<n>`

   The run is in that skill's `references/running-criteria.md`. Every criterion carries a command; there is nothing on a ticket for you to judge by eye.

3. `git status --porcelain --untracked-files=no` again. Matching step 1 is what shows you changed no tracked file. The criteria in step 2 write screenshots and cache directories of their own; those are untracked, which is why both runs look at tracked files only.

4. `git rev-parse HEAD`, then post your verdict:

   ```
   gh issue comment <n> --body "VERDICT <commit> by <model> — <one line>"
   ```

   `<commit>` is all 40 characters of what `git rev-parse HEAD` just printed, and `<model>` is the model you are running on.

You are done when that comment is on the ticket. Your report to the worker is the one line and the output of both `git status` runs.

## The one line

Writing that line is the whole of your judgement. It says three things, in this order:

1. **How you ran the criteria.** `commands only` when every criterion ran, `could not start` when one could not be run at all. There is no third answer: you never start the product by hand. A criterion that needs it starts it itself, through the `start` command in `.mmw/target.json`, and stops it again.
2. **What came back.** `all passed`, or which criteria failed, named by the ids the ticket gives them.
3. **What you repaired.** Anything you changed in the environment to get the commands to run. Say nothing here when you changed nothing.

## The environment is yours; the repository is not

A missing dependency, a browser this machine has not downloaded, a connection string that lives in the repository's own configuration: install it, download it, go find it, and run again. `could not start` is what you write once that repair has failed, not instead of trying it.

What you never repair is anything the machine hands out. Ports and the data directory come from this worktree's lease, not from you, and the product is started and stopped only by the `start` and `stop` commands of `.mmw/target.json`, which the criteria run themselves. A port that is taken belongs to another run on this machine: leave it, and read `Five rules while the product is running` in the `drive-target` skill, which binds every command you run here.

The repository is what you leave exactly as you found it. You report on the criteria; the worker fixes whatever you report. So:

- Edit no file, and make no commit.
- Fix nothing, however small and however obvious the fix.
- Judge against the criteria the ticket already carries, and add none of your own.
- Say nothing about the quality of the code, the shape of the diff, or what the work should have done instead. Those are read by other eyes, and yours are the ones that ran the commands.
