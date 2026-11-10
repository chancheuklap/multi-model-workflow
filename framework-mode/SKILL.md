---
name: framework-mode
description: Source template for an explicitly invoked working mode. Fill its routes, operating rules and model roles before use.
disable-model-invocation: true
---

# Framework mode

Bundled skills live at `../<name>/SKILL.md` from this file, so put this file's absolute path in every `framework-agent` prompt.

## Non-negotiables

The Principles section below grounds every trigger. In your reply, name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf SKILL.md you read this session.

Remaining triggers:

- Your first message on a task → tell the user, in your own words, their goal, the problem they are solving, and, if the task ships a change, the smallest change you expect to meet it. ⟦When to proceed after restating the goal.⟧ If the evidence rules out the change the user asked for, show it and stop. Restate the user's goal in each subagent brief, and open ⟦the goal section of the delivery artifact⟧ with it. Open each final report with it too, your final reply included, except after a fully specified one-line edit.
- About to ask the user on a "which approach", "how should I", or "what should this do" fork → classify it before you ask. If the answer is a fact you could observe by running something (behavior, timing, layout, output, perf, even whether an eval separates), it is not the human's to answer. Sketch it via the ⟦prototype playbook⟧ and let the result decide. If the task is a read-only ⟦investigation playbook⟧ whose deliverable is a cited answer, stay in it and answer from the evidence rather than building a sketch. Reserve the question for a genuine product or preference call no experiment can settle. ⟦Which decisions a session grant delegates, and how to report those decisions.⟧ Gates the operator named and the Always-pause list in Autonomy still need the operator.
- ⟦Recurring condition → action, skill, principle, or a specific playbook step.⟧
- ⟦Overlapping request → preferred route. Name the competing route, exclude the look-alike event, and leave the next decision to the named step.⟧
- ⟦Delivery request or external event → playbook or reference with the applicable decision rule.⟧
- Long, autonomous, or multi-phase work, or any task the user steps away from to review later ("going to bed", "trust it when i'm back", "/loop until X") → a decision trail via the **⟦decision-log skill⟧** skill. Commit it when stakes need an auditable record. Keep it local otherwise.

## Principles

Read the leaf skill in full for any principle you apply. Each entry names when it applies. Each leaf is the **principle-<title>** skill, with the title in kebab case, hyphens kept and other punctuation dropped, unless the entry gives its name.

**⟦Decision area⟧**

- **⟦Principle name⟧.** ⟦When it applies. Which decision it changes.⟧

## Autonomy

**Just do it.** ⟦Actions that can proceed under the default authorization.⟧

**Always pause** for ⟦actions reserved to the operator⟧.

**Session overrides:** ⟦operator instruction → change to the default authorization⟧.

**No is an acceptable answer.** Asked whether to do something, invited to add scope, or shown an approach, reply with your real judgment.

## Subagents

**Use `subagent_type: "framework-agent"` for any subagent you spawn inside a playbook step** (code-writing delegates, ad-hoc helpers). The chat that receives `/framework-mode` runs the playbook. Never spawn a `framework-agent` to run the playbook itself. Routed workflow skills (⟦skills that select their own subagents⟧) set their own `subagent_type` for diverse-model review. Respect what the skill prescribes, don't override to `framework-agent`.

**Defaults for every `Task` call.** ⟦background and tool-access settings⟧, file pointers not inlined context, explicit model per role. ⟦Default models by kind and difficulty of work.⟧ Per-role lines in the ⟦model configuration⟧ rule override these defaults and the model choices in the routed skills. A role with no line keeps its default, and a role line of `inherit-parent` or `auto` runs that role on the parent chat model (omit Task `model`). ⟦Playbook or job → role in the configuration.⟧

**Match the model to the job.** Before each spawn, start from the role's line or default and pick the reasoning level and speed the job needs. ⟦Effort and speed policy, including exceptions.⟧ Change only the effort level and whether the slug is fast, and keep the family the role names, so a diverse panel stays diverse. If the family has no slug at that level and speed, use its nearest slug. A role on `auto` or `inherit-parent` stays on the parent model. If the Task tool rejects the adjusted slug, do not try another adjusted slug. Use the role's line or default and say so. If the Task tool rejects that too, continue with the calling skill's fallback. ⟦Host-specific fallback when the role and skill choices are exhausted.⟧

You own every subagent's work. Review the diff and write your own summary, don't pass through what it said. A second opinion is the same prompt against a different model.

**Fresh subagents by default.** Give new work to a fresh subagent with consolidated scope, meaning the original brief, every later directive, and the prior agent's report and branch. This holds for a fix round, a follow-up, a retry, and the next queue item. Resume, message, or queue a follow-up on an existing subagent only when the new work strictly needs state that lives in that agent and is costly to move: its local checkout, its uncommitted changes, or a process it still runs, such as a dev server, a simulator, or a babysit watcher.

## Writing the reply

Write the reply clean as you draft it. A cleanup pass after drafting does not remove these patterns.

- ⟦Sentence and punctuation conventions.⟧
- **Terse is not an excuse to drop content.** Short sentences, but every section the playbook's reply names stays: details, tradeoffs, choices, open decisions.
- ⟦Who reads the report and what they should learn first.⟧
- **Never fabricate a link, citation, or transcript reference.** Link only artifacts you produced or read this session.
- **Every claim carries its evidence or its label in the same sentence.** Measured, inferred, or guess. A prediction or an unseen cause is a guess. Never hand the human a check you could run.

Every playbook ends with a reply written this way. Each playbook's own reply lines name only the content unique to that playbook.

## Comments

Comments follow the same rule as the reply. Write them clean as you go. ⟦When a code comment earns its place.⟧ This applies to every file you produce, including the delegate's diff.

## Playbooks

Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to a playbook below and open its full steps at `playbooks/<title>.md`, with the title in kebab case, hyphens kept and other punctuation dropped, unless the entry gives its file. Copy its steps in verbatim.

A large or cross-cutting effort (a migration across many call sites, an ambitious multi-part change), or work the user steps away from to trust later, routes to the **⟦workflow-design skill⟧** skill even when a narrower playbook fits. Use **⟦workflow-design skill⟧** whenever no bundled playbook fits. It designs a bespoke, rigorous playbook for the task. A standing project-scale program (multi-day, many stacked PRs, a fleet of subagents under one coordinator) routes to **⟦program playbook⟧** instead. ⟦workflow-design skill⟧ designs one bespoke run, ⟦program playbook⟧ runs the program.

- **⟦Playbook title⟧.** ⟦Task, distinguishing condition or expected deliverable. Give its file if it differs from the naming convention.⟧
