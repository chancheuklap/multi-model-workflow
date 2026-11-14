# Agent definitions

Read this when the host runs a role through a named agent definition, as Droid does with a custom droid: a Markdown file that fixes a model, a reasoning effort and a system prompt for whoever it names. Setup reads it at step 5b, and the main chat and every owner read it to spawn. A host that sets the model and effort in each spawn skips this file.

## Write the droids

Done when the droids folder holds one `pstack-*` droid for each role line that passed the check, each entry of a list role counting as a line, and `pstack-comment-sicko`, and holds no other `pstack-*` file.

1. Take each role line in the rule except `swarm workers`, whose workers are owners that start as sessions of their own and read the line themselves. A line with one model is one droid. A list role (`arena runners`, `arena cross-judge pool`, `architect runners`, `interrogate reviewers`) is one droid for each entry, in list order.
2. Check each model and effort pair before writing (below).
3. Write each droid to `.factory/droids/` in the folder the user starts Droid sessions from (`~/.agents/.factory/droids/` for a user who starts in `~/.agents`), and nowhere else, `~/.factory/droids/` included.
4. Delete each `pstack-*.md` file in that folder that step 3 did not write. Leave every file whose name does not start with `pstack-`.
5. Rewrite files that already exist, so a re-run converges.

**Name.** `pstack-` followed by the role line's name, lowercase, with each run of characters outside `a-z` and `0-9` replaced by one `-`, and no `-` at either end. A list entry appends `-<n>`, counting from 1. `bug-fix` is `pstack-bug-fix`, `feature, refactoring` is `pstack-feature-refactoring`, and the second entry of `arena runners` is `pstack-arena-runners-2`.

**Model and effort.** Copy the role line's, or the entry's. `inherit-parent` and `auto` write `model: inherit` and no `reasoningEffort`.

**Comment Sicko.** Write `pstack-comment-sicko` as well. It takes the model and effort of the `judgment and prose` line, and its role text is [comment-sicko](../../../agents/comment-sicko.md).

**Template.**

```markdown
---
name: pstack-<role>
description: pstack delegate for the <role line name> role
model: <model>
reasoningEffort: <effort>
---

<leaf rule>

<role text, for a role that carries one>
```

- **Description.** One line of about ten words. A list entry reads `pstack delegate for seat <n> of the <role line name> role`.
- **Tools.** Omit `tools`, so the droid keeps every tool its host grants a subagent. Add `tools: read-only` below `reasoningEffort` only when the pstack skill the role's line is named for says in so many words that the role's delegates are read-only. "Read access" or "should not write" does not say so. [arena](../../arena/SKILL.md) calls its cross-judge a read-only judge, so `arena cross-judge pool` qualifies. A line no skill names, such as `judgment and prose`, gets none.
- **Role text.** The code roles and `hardest tasks` are the roles the mode's Delegation assigns to a playbook step's code delegate, so they carry the full text of [poteto-agent](../../../agents/poteto-agent.md) under the leaf rule. Every other role carries the leaf rule only. `judgment and prose` is shared by reviewers and researchers that other skills brief, and poteto-agent tells its holder to read the whole mode first, so a step that wants that style on it names [poteto-agent](../../../agents/poteto-agent.md) in the brief. [poteto-mode](../../poteto-mode/SKILL.md#subagents)
- **Copied files.** Copy `agents/poteto-agent.md` and `agents/comment-sicko.md` without their frontmatter. The droid sits outside the bundle, so replace each link with its text, which is the skill's name, and write no path: the agent loads a skill by name. The `agents/` files stay the single source of truth, and each run refreshes the copies.

**Leaf rule.** Every droid opens with this text:

```markdown
You are a pstack delegate. The brief you are given is your whole task. Do it, then reply with the result the brief asks for.

You cannot start other agents. When the brief needs a skill or step you cannot run yourself, stop and reply `needs: <the skill or step, and the inputs it needs>`. The agent that spawned you runs it and resumes you with what it found.
```

### Check each pair before writing

- **Effort.** Droid accepts an effort the model supports, `xhigh` included. It does not reject one the model lacks. It runs the model on its own default and reports no error, so a droid written for that pair carries an effort it does not run. Check each pair against the model's supported levels from setup step 1, and write no droid for a pair that fails. Apply step 3(b): take the highest supported level at or below the target, and flag the role when none fits.
- **Model.** Droid also reports no error for a model the organization blocks. It runs the droid on the parent's model. Confirm each id is on the session's model list. `droid exec --list-tools -m <id>` prints `Invalid model` and the available ids for an id it does not know. Report each role whose model you cannot confirm as an unfilled role.

## Find a role's droid

Apply the naming rule to the role's line. Comment Sicko's droid is `pstack-comment-sicko`. A droid carries its own model and effort, so a spawn does not read the rule file. A list role's seats are the droids that carry its name followed by `-1`, `-2` and on. Read a droid's `model` when a step needs the model itself, as [arena](../../arena/SKILL.md) does to pick a judge from another family. `model: inherit` marks an inherited seat. A droid that does not exist leaves the role unfilled, so report it.

## Spawn a delegate

Call Task with `subagent_type` set to the droid's name. A list role takes one Task for each seat. Droid finds a droid only from a session started in the folder that holds its `.factory/droids/`. Anywhere else Task reports `Droid configuration not found`, and the role is unfilled.

- A code role's droid and `pstack-comment-sicko` already carry their role text, so the brief leaves it out and states the scope. Any other droid carries the leaf rule only, so a brief that names a role gives its path.
- Pass no `complexity` to a droid whose model is `inherit`, so the delegate runs on the parent model.
- Start a delegate whose result you do not need yet with `run_in_background`.
- A delegate that replies `needs:` has paused. Run the step it names, then call Task with `resume` set to its task id and the findings in the prompt. When Droid cannot resume that task, brief a fresh delegate with the findings.

A Task subagent cannot start agents, which is the delegate rule.

## Start an owner

An owner starts delegates, so it runs as a session of its own. On Droid this is where a playbook says "own remote machine". Start it from the folder that holds the droids, with the absolute path of its project worktree in the brief:

```
cd ~/.agents && droid exec --auto high -m <model> -r <effort> "<brief>"
```

Start it in the background, with the model and effort of the owner's role line in the rule. For `inherit-parent` or `auto`, pass the model and effort of the session that starts it, because `droid exec` otherwise uses its own default model.

- `--auto high` is required. Task, which the owner needs to start its delegates, is blocked at read-only, low and medium, and allowed at high.
- Create the owner's worktree and branch first, and give the owner its absolute path. Leave out `--worktree` and `--cwd`: they move the session into the project repository, where Droid cannot find the droids. An owner started this way still works in the worktree by absolute path and starts its delegates.
- A worktree separates files only, so owners that run the app also need their own ports and build output.
- Continue an owner with `-s <session-id>`, or branch from its built state with `--fork <session-id>`. Read its progress from its pushes, its PR and its trail.
