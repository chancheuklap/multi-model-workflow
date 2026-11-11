---
name: framework-mode
description: Use when filling or adapting the framework-mode source template. Fill its routes, operating rules and model roles before use.
---

# Framework mode

Bundled skills live at `../<name>/SKILL.md` from this file, so put this file's absolute path in every `framework-agent` prompt.

## Non-negotiables

The Principles section below grounds every trigger. In your reply, name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf SKILL.md you read this session.

Remaining triggers:

- Your first message on a task → tell the user, in your own words, their goal, the problem they are solving, and, if the task ships a change, the smallest change you expect to meet it. Proceed with the work already authorized. If the evidence rules out the change the user asked for, show it and stop. Restate the user's goal in each subagent brief and in the PR's `## Summary`. Open each final report with the outcome against that goal, except after a fully specified one-line edit.
- Nontrivial change, architecture decision, or "are we sure?" about the code → the **how** skill.
- About to ask the user a "which approach", "how should I", or "what should this do" question → classify it before you ask. If the answer is a fact you can look up or observe by running something, get the evidence yourself. Use **prototype** when a throwaway sketch would settle a design question. For a read-only investigation, answer from the evidence. Reserve the question for a genuine product or preference call no experiment can settle. Under an autonomy grant, make the decisions it covers and report them. Gates the operator named and the Always-pause list in Autonomy still need the operator.
- Asked to stress-test a plan or idea → **grilling**. When the unresolved decisions span more than one session and the route is still unclear, use **wayfinder** to map and resolve decision tickets.
- The owner needs to see current and proposed behavior to choose a direction → show both with **big-pics-little-words** before asking for the decision.
- Working from an approved answer, prototype, spec, or ticket → **principle-baseline-is-the-contract**. Carry the settled decisions forward. If the evidence conflicts with one, take that conflict back to its owner.
- Asked to record the agreed solution as a spec → **to-spec**. Synthesize what was decided. Resolve any outstanding owner decision before publishing.
- Recording an agreed problem and solution as implementation tickets → **to-tickets**. For one diagnosed fix, use its issue template with the supporting evidence. For a breakdown, get the owner's approval for the proposed scope before publishing. An agreed conversation, plan, or spec can supply the decisions.
- Calling a skill whose steps extend beyond the request → give it the requested deliverable and stop there. For diagnosis alone, return the finding and evidence. For ticket publication, return the published tickets. When implementation is authorized, the chat running the playbook delegates the agreed ticket under **Subagents**. Carry forward authorization already given for that scope.
- Any code → name the data shape first, and choose its organizing structure per **principle-model-the-domain**.
- Code crossing a function boundary with an open interface → **codebase-design** before implementing. If viable designs have different consequences for callers, explore them in parallel. Work from the chosen sketch.
- Parallel fan-out → identify the blocking first steps and independent workstreams. Where agents would write the same state, apply **principle-separate-before-serializing-shared-state** before delegating.
- Asked for an independent second opinion, or a consequential design dispute remains after checking the evidence → give a fresh subagent the decision and scope and have it use **advisor**. The caller weighs its recommendation.
- Any prose surface, your reply to the user included → the **unslop** skill. Write the reply per **Writing the reply**. Agent-facing prose also follows **writing-for-agents**.
- Docs, RFCs, readmes, PR descriptions, or commit messages → the **technical-writing** skill. For a PR body, use the **pr** template.
- Before review of a code change → the **no-comments** skill on the implementation diff.
- Shipping user-visible behavior → verify the promised outcome on the surface the user actually uses. For bug fixes, reproduce first on the same surface yourself. Use the project's matching `verify-<app>` skill when available.
- Running a benchmark, measuring perf yourself, or reporting a speedup or regression you measured → the **benchmark-checklist** skill before you report or act on the number.
- Review feedback → assess each finding on its merits against the reviewed change and its intent. Rerun a claim about runtime behavior. Dismiss a finding the evidence refutes with a concrete reason, and mark a finding you cannot verify as unverified.
- Broken skill mid-task → report the failure and track its repair separately. Continue work that can proceed. Don't silently work around it.
- Long, autonomous, or multi-phase work, or any task the user steps away from to review later → record each consequential decision and its reason on the map, spec, ticket, or PR the next reader will open, per **principle-write-for-where-it-is-read**.

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
