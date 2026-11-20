---
name: setup-mmwstack
description: Configure which models mmwstack uses per role and at what reasoning budget. Detects your available models and saves the user's choices for future tasks. Use for /setup-mmwstack or when the user asks to configure mmwstack models or change the reasoning budget.
---

# Setup mmwstack

## Steps

### 1. Detect available models

Identify the current host from the session environment. If it is unclear, ask the user once. List the models, reasoning levels, and speeds this session can assign to subagents. Use the user's available-model list when it gives a more complete inventory. If subagents inherit the parent model and offer no model choice, offer `inherit-parent` as an explicit choice. If selection is possible but you cannot list the options, ask the user which models they can select. Save only confirmed choices. On Factory Droid, list the effective model and reasoning for each tier (`light`, `medium`, and `heavy`). On Antigravity (AGY), run `agy models` to list the exact model IDs for `## agy`. Each ID encodes its reasoning level. If `agy` is unavailable, list the four `invoke_subagent` tiers: `inherit`, `pro`, `flash`, and `flash_lite`.

### 2. Load current state

Read the current host section's budget, `# fallback:` rules, and role assignments in `~/.agents/mmwstack-models.md` or the rule file the user supplies. If the rule has older unsectioned assignments, offer those choices for confirmation against this host's inventory. On first setup, use the roles in step 5. A line named `how explorer` is the earlier name of `reader`, so its model and settings carry over to `reader`. When upgrading this host, carry the model, reasoning and speed from its old `swarm workers` line to `verifier` if no `verifier` value exists. Remove the old line when saving the confirmed section. If the section records `# budget: unlimited`, map it to `large` (`xhigh`) and note the change to the user. Drop retired role names from this host section, including `architect runners`, `how critics`, `how explainer`, `why investigators`, `why synthesizer`, `interrogate reviewers`, `hardest tasks`, `reflect tooling`, and `reflect judgment, divergent, synthesizer`.

### 3. Budget, map, and confirm

For Droid, confirm tiers instead of a budget or per-role reasoning. When copying another host, use the user's current tier-to-model bindings once to translate each source model to a tier; flag any model without a unique match. Save only tier names in `## droid`, one per role or panel entry, preserving order and repetitions. Leave Droid settings and the source host section unchanged. Skip the model-and-budget template below.

**(a) Ask for a budget.** Prefer a structured choice when available. Offer these three options with these exact labels, and name the current budget when the rule records one.

- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Ask the user to choose models for unassigned roles from the inventory in step 1. On a rerun, keep their current models, panel lists, aliases, speeds and explicitly chosen per-role reasoning levels. Apply the budget to settings the user leaves to the budget. `large`, `medium`, and `small` request `xhigh`, `high`, and `medium` reasoning respectively, including panel entries. For each chosen model, show the highest supported reasoning level at or below the target. If none fits, flag it for the user. Leave inherited settings unchanged.

**(c) Show the roles and confirm.** Show every role with its model and any existing `# fallback:` rules, marking any model, fallback target, or setting unavailable to subagents as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` as the options. Require exactly two ordered entries for `arena runners`, including repeats. Confirm a pair before saving a list of any other size. `arena cross-judge pool` is also a list, but [arena](../arena/SKILL.md) runs one judge. It uses the first available entry in preference order, including an explicitly inherited model. For a model race, each arm names its model from this configuration.

### 4. Validate

On Factory Droid, confirm each selected tier is available with the model and reasoning shown in step 1. On other hosts, confirm each selected model, concrete fallback target, and setting is available before saving it. For `inherit-parent` or `auto`, confirm the session supports running the role on the parent model. If a choice is unavailable, ask for another.

### 5. Write the rule

Save the confirmed budget label and target effort, any `# fallback: <pattern> -> <target>[, <target>...]` lines, then one line per role in `~/.agents/mmwstack-models.md` or the rule file the user supplied. Update only the current host section. Preserve existing `# fallback:` lines in the current host section unless the user asks to change or remove them, along with other sections and any unsectioned choices for hosts still to configure. Fill the template with the user's choices. Use the model names and settings their subagents accept.

```
## <host>
# Use inherit-parent or auto for an explicitly inherited model.
# budget: <chosen budget> (<target effort>)
coder: <model and settings>
feature, refactoring: <model and settings>
bug-fix: <model and settings>
perf-issue: <model and settings>
hillclimb: <model and settings>
judgment and prose: <model and settings>
advisor: <model and settings>
reader: <model and settings>
code review: <model and settings>
arena runners: <first seat>, <second seat>
arena cross-judge pool: <judge models in preference order>
verifier: <model and settings>
```

On Factory Droid, sync the project's native registrations in `.factory/droids/` before starting the next session. Bind `mmw-agent-light`, `mmw-agent-medium`, and `mmw-agent-heavy` to their Factory tier models and reasoning settings. Bind `advisor` and `comment-sicko` to the tiers from the `advisor` and `judgment and prose` entries in the rule file for that session. Sync again after a Factory tier binding changes or a model rule, including a supplied rule file, changes the tier of either specialist.

On Antigravity (AGY), sync the native registrations for `mmw-agent`, `advisor`, and `comment-sicko` in `.agents/agents/` before starting the next session. Omit the `model` frontmatter field so `scripts/agy-delegate` can pass exact models and `# fallback:` rules from `## agy` while preserving each role's instructions and `tools:` allowlist.

### 6. Confirm

Tell the user where you saved the rule and that it applies to new sessions. Name the host and each role you left unfilled.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a project-local `verify-<app>` for the target surface, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke [create-verification-skill](../create-verification-skill/SKILL.md) (resolves wherever mmwstack is installed: workspace, user, or plugin). On no, move on without pushing.

### 8. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /create-formal-verification-skill." On yes, invoke [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md) (resolves wherever mmwstack is installed: workspace, user, or plugin). On no, move on without pushing.
