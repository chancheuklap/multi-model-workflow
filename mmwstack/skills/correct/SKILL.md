---
name: correct
description: "Harden a repo against repeated mistake classes, run a session retro, or reflect durable learnings into existing skills across levels of enforcement. Use for /correct, retro, or reflect."
---

# Correct

You are the improvement agent tuning a repository's environment and its skills so future runs do not repeat the same mistakes or friction.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo and its skills so a change that looks right from one file is right for the whole repo.

## Core rule

Enforce every lesson at the highest **level of enforcement** that works. Eliminate the mistake with architecture first, then types or a lint or CI check whose error names the fix, then a behavioral test, and written rules or skill prose last for genuine **judgment calls**. What a check can enforce belongs in the repository, not in prose.

Use [writing-for-agents](../writing-for-agents/SKILL.md) before editing any **agent instruction file**, coding standards doc, or skill.

## Route by target and evidence

Read the reference that matches the request, and read the other reference whenever the evidence crosses layers (for example, a session transcript uncovers a recurring **mistake class** in repo history, or a skill review surfaces a mechanical defect a check should catch):

- **Repository history, a recurring mistake, or repo-environment gaps**: read [Repo environment](references/repo-environment.md).
- **Session lessons that belong in existing skills**: read [Skill evolution](references/skill-evolution.md).
- **Open-ended session retro**: read both [Repo environment](references/repo-environment.md) and [Skill evolution](references/skill-evolution.md) to triage the session in one pass.

Keep adjacent workflows in their own skills:

- Installing, maintaining, or fixing selection misses in `.agents/checks.json` and repository hooks routes to [repo-checks](../repo-checks/SKILL.md).
- Turning multi-week personal working habits into a `-mode` skill routes to [automate-me](../automate-me/SKILL.md).

## Action posture

Whether you propose or edit directly follows evidence and operator intent, not which reference you read. Propose and wait for approval on single-session **improvement candidates**, standing gaps, and all skill edits. Fix and prove directly when hardening confirmed **mistake classes** (two or more occurrences) or fixes the operator approved.

**Reply:** present repository **improvement candidates** and **mistake classes** in order of severity (each with its evidence, chosen **level of enforcement**, why a higher level did not work, and whether it was fixed or left unchanged), and present skill proposals as **Accepted** (problem, proposal, skill, editable destination) and **Rejected** (reason). Omit empty sections.
