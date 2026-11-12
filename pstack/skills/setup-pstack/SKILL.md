---
name: setup-pstack
description: Configure which models pstack uses per role and at what reasoning budget. Detects your available models and saves the user's choices for future tasks. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

## Model rule

In a new session, read `~/.agents/pstack-models.md` or the pstack model rule the user supplies. For each delegation, use the model and settings assigned to its role. Give a subagent that will delegate in turn a readable path to the same rule or the relevant role lines in its brief. `inherit-parent` and `auto` run a role on the parent model when the user selects them. If an assignment cannot run, report the unfilled role.

## Steps

### 1. Detect available models

List the models, reasoning levels, and speeds this session can assign to subagents. Use the user's available-model list when it gives a more complete inventory. If subagents inherit the parent model and offer no model choice, offer `inherit-parent` as an explicit choice. If selection is possible but you cannot list the options, ask the user which models they can select. Save only confirmed choices.

### 2. Load current state

If the rule exists, read its `# budget` line and each role's current assignment. On first setup, use the roles in step 5. Drop retired role names, such as `how critics`.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Prefer a structured choice when available. Offer these four options with these exact labels, and name the current budget when the rule records one.

- `unlimited — max reasoning`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Ask the user to choose models for unassigned roles from the inventory in step 1. On a rerun, keep their current models, panel lists, aliases, and speeds. `unlimited`, `large`, `medium`, and `small` request `max`, `xhigh`, `high`, and `medium` reasoning respectively, including panel entries. For each chosen model, show the highest supported reasoning level at or below the target. If none fits, flag it for the user. Leave inherited settings unchanged.

**(c) Show the roles and confirm.** Show every role with its model, marking any model or setting unavailable to subagents as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` as the options. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but [arena](../arena/SKILL.md) runs one judge. It tries only values from a family other than the parent's, in list order, so order it by preference. An `inherit-parent` or `auto` value never judges. `swarm workers` assigns the workers. For a model race, each arm names its model from this configuration.

### 4. Validate

Confirm each selected model and setting is available before saving it. For `inherit-parent` or `auto`, confirm the session supports running the role on the parent model. If a choice is unavailable, ask for another.

### 5. Write the rule

Save the confirmed budget label and target effort, then one line per role in `~/.agents/pstack-models.md` or the rule file the user supplied. Overwrite the role table so re-runs stay idempotent. Fill the template with the user's choices. Use the model names and settings their subagents accept.

```
# pstack model configuration. One line per role.
# Use inherit-parent or auto for an explicitly inherited model.
# budget: <chosen budget> (<target effort>)
feature, refactoring: <model and settings>
bug-fix: <model and settings>
perf-issue: <model and settings>
hillclimb: <model and settings>
judgment and prose: <model and settings>
hardest tasks: <model and settings>
how explorer: <model and settings>
how explainer: <model and settings>
why investigators: <model and settings>
why synthesizer: <model and settings>
reflect tooling: <model and settings>
reflect judgment, divergent, synthesizer: <model and settings>
arena runners: <one model and its settings per seat, comma-separated>
arena cross-judge pool: <judge models in preference order>
swarm workers: <model and settings>
architect runners: <one model and its settings per seat, comma-separated>
interrogate reviewers: <one model and its settings per seat, comma-separated>
```

### 6. Confirm

Tell the user where you saved the rule and that it applies to new sessions. Re-running this skill updates it.

When setting up a repository, add this rule once to its persistent project instructions so direct skill calls also start from a work issue:

> For every new repository task, use the bundled `to-tickets` skill to open or reuse a GitHub work issue before starting. Reuse the work issue for follow-ups. Use the same skill to split a checked plan into execution tickets when implementation is requested. Give each subagent its assigned work issue URL. For each code writer, use the execution ticket URL. Open one corresponding PR for each authorized code ticket and link the PR and ticket to each other. Record evidence, decisions, assignments and results on the work issue.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke [create-verification-skill](../create-verification-skill/SKILL.md) (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.

### 8. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /create-formal-verification-skill." On yes, invoke [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md) (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.
