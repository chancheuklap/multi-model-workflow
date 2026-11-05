---
name: no-comments
description: "Spawn Comment Sicko, fix accepted findings, and offer encodings for claimed constraints."
---

# No comments

Send Comment Sicko. Act on accepted findings.

Defer to Comment Sicko's fresh perspective.

## Scope

Use the caller's files or diff. Otherwise use the committed ticket diff against its integration base, including the working tree.

## Steps

1. Write a prompt directing the subagent to follow [Comment Sicko](references/comment-sicko.md) on this diff. Include the resolved reference path and diff scope, save it to FILE, and run `dispatch.sh spawn researcher --prompt FILE`. Send the printed assignment as [Dispatch](../dispatch/SKILL.md) describes and wait for its report.
2. Inspect its report and diff. Reject application-code edits, scope escapes, exception-protected deletions, misstated `MUST KILL` reasons, and flags that treat kept intentional code as guilty. Reshape flags on our-code surprises stay actionable. Do not restore those comments. A keep survives only with proof it is about something we cannot change. Audit missed scoped lint and TypeScript suppressions. Correctness or safety suppressions stay actionable `MUST KILL`s. Restore deletions only with exact exceptions and scoped proof. Before accepting thin `IMPORTANT` or `do not remove` kills or keeps, use **how** for the symbol, and read the glossary and the ADRs. If a kill is ambiguous, do not restore. If a keep is refuted or still ambiguous, delete it. Revert and rerun one rejected report with the failure named. Reject a second, report it open, and fail this skill.
3. Fix trivial accepted flags directly by deleting a dead path, dropping a parameter, or using the real API. If any fix needs a shape, use **codebase-design** for Phase A, Phase B, and Phase C, once for the accepted set and surrounding code. Stop at the sketch. The sketch shapes. Step 4 implements.
4. Implement the smallest root-cause fix in scope. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open. Use **principle-fix-root-causes** and **principle-redesign-from-first-principles**. They guide intent only. Neither authorizes widening the fence nor fixing instances outside it. Never bolt on symptom guards.
5. Constraint comments say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave keeps about things we cannot change. Offer the cheapest in-scope type, runtime, test, or CI lint in the report. Encode it only when the caller has already approved that encoding. Otherwise delete the comment, report the constraint open, and sketch the out-of-scope work.
6. Report the deletion count, restored comments, reruns, sketch, fixes, encoding offers, encodings, unenforced constraints, and other open work.

Done when the report in step 6 is written and every accepted flag is fixed, deleted, or recorded open.
