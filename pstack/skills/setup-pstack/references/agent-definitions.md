# Agent definitions

Read this when the host runs a role through a named agent definition, as Droid does with a custom droid: a Markdown file that fixes one model and one reasoning effort for whoever it names. Setup reads it at step 5b, and the main chat and every owner read it to spawn. A host that sets the model and effort in each spawn skips this file.

## Write the droids

Done when the droids folder holds one `pstack-*` droid for each distinct model and effort in the rule, and no other `pstack-*` file.

1. Collect every distinct model and effort pair across the role lines, panel and pool lists included. Five roles on three pairs write three droids.
2. Check each pair before writing (below).
3. Write each droid to `.factory/droids/` in the folder the user starts Droid sessions from, which is `~/.agents/.factory/droids/` for a user who starts in `~/.agents`. Write them there and nowhere else, `~/.factory/droids/` included.
4. Delete each `pstack-*.md` file in that folder that no pair references. Leave every file whose name does not start with `pstack-`.
5. Rewrite files that already exist, so a re-run converges.

**Name.** `pstack-<model>-<effort>`, lowercase, with every character outside `a-z`, `0-9`, `_` and `-` replaced by `-`. `gpt-6.1-terra` at `xhigh` is `pstack-gpt-6-1-terra-xhigh`.

**Inherited roles.** `inherit-parent` and `auto` both map to `pstack-inherit`, which sets `model: inherit` and no effort. Write it only when a role uses one of the two.

**Template.** Omit `tools`, so the droid keeps every tool its host grants a subagent.

```markdown
---
name: pstack-<model>-<effort>
description: pstack delegate on <model> at <effort> reasoning
model: <model>
reasoningEffort: <effort>
---

You are a pstack delegate. The brief you are given is your whole task. Do it, then reply with the result the brief asks for.

You cannot start other agents. When the brief needs a skill or step you cannot run yourself, stop and reply `needs: <the skill or step, and the inputs it needs>`. The agent that spawned you runs it and resumes you with what it found.
```

`pstack-inherit` takes the description `pstack delegate on the parent model` and omits `reasoningEffort`.

### Check each pair before writing

- **Effort.** Droid accepts an effort the model supports, `xhigh` included. It does not reject one the model lacks. It runs the model on its own default and reports no error, so a droid written for that pair carries an effort it does not run. Check each pair against the model's supported levels from setup step 1, and write no droid for a pair that fails. Apply step 3(b): take the highest supported level at or below the target, and flag the role when none fits.
- **Model.** Droid also reports no error for a model the organization blocks. It runs the droid on the parent's model. Confirm each id is on the session's model list. `droid exec --list-tools -m <id>` prints `Invalid model` and the available ids for an id it does not know. Report each role whose model you cannot confirm as an unfilled role.

## Find a role's droid

Read the role's line in the model rule, take its model and effort, and apply the naming rule. A value of `inherit-parent` or `auto` names `pstack-inherit`. A droid that does not exist leaves the role unfilled, so report it.

## Spawn a delegate

Call Task with `subagent_type` set to the droid's name. A panel or list role takes one Task for each seat or entry.

- Pass no `complexity` to `pstack-inherit`, so the delegate runs on the parent model.
- Start a delegate whose result you do not need yet with `run_in_background`.
- A delegate that replies `needs:` has paused. Run the step it names, then call Task with `resume` set to its task id and the findings in the prompt. When Droid cannot resume that task, brief a fresh delegate with the findings.

A Task subagent cannot start agents, which is the delegate rule.

## Start an owner

An owner starts delegates, so it runs as a session of its own. On Droid this is where a playbook says "own remote machine":

```
droid exec --auto high -m <model> -r <effort> --worktree <name> "<brief>"
```

Start it in the background, with the model and effort from the owner's role line. For `inherit-parent` or `auto`, pass the model and effort of the session that starts it, because `droid exec` otherwise uses its own default model.

- `--auto high` is required. Task, which the owner needs to start its delegates, is blocked at read-only, low and medium, and allowed at high.
- `--worktree` gives the owner its own working tree and branch on this machine. It separates files only, so owners that run the app also need their own ports and build output.
- Continue an owner with `-s <session-id>`, or branch from its built state with `--fork <session-id>`. Read its progress from its pushes, its PR and its trail.
