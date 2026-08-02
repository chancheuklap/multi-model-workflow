---
name: code-review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along three axes — Standards (does the code follow this repo's documented coding standards?), Spec (does the code match what the originating issue/spec asked for?), and Correctness (does the code actually work?). Each axis runs as its own reviewer, at least one of them from a different model family than whoever wrote the code. Findings are verified one by one before they reach the report. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

Three-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards** — does the code conform to this repo's documented coding standards?
- **Spec** — does the code faithfully implement the originating issue / spec?
- **Correctness** — does the code actually work?

Each axis runs as its own reviewer so they don't pollute each other's context, then this skill verifies every finding and reports the three axes side by side.

The issue tracker should have been provided to you — run `/setup` if `docs/agents/issue-tracker.md` is missing. Who reviews what is decided by `docs/agents/models.md`.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it. On a re-review the fixed point is not what the user said the first time — see step 7.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here — not inside three parallel reviewers.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. `docs/specs/<slug>/` on this branch, where `<slug>` is the branch name — the layout in `docs/agents/worktrees.md`.
2. Issue references in the commit messages (`#123`, `Closes #45`, etc.) — fetch via the workflow in `docs/agents/issue-tracker.md`.
3. A path the user passed as an argument.
4. Any other spec file under `docs/` or `specs/` matching the branch name or feature.
5. If nothing is found, ask the user where the spec is. If they say there isn't one, skip the **Spec** axis entirely and say so in the report.

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries a **smell baseline** — a fixed set of Fowler code smells that applies even when a repo documents nothing. It lives in `standards.md` next to this file, along with the two rules that bind it: a documented repo standard always overrides the baseline, and every smell is a judgement call rather than a hard violation.

### 4. Dispatch the reviewers

Four reviewers, one message. Follow `dispatching-agents` for the mechanics and `docs/agents/models.md` for the model of each.

| Axis | Who reviews |
| --- | --- |
| Standards | one Claude sub-agent |
| Spec | one Claude sub-agent |
| Correctness | one Claude sub-agent **and** one headless Codex reviewer |

The code was written by a Codex worker, so at least one reviewer on every axis comes from the other family — that is the red line in `models.md`, not a preference. Correctness carries the extra same-family reviewer because it is the axis where a miss costs the most and where the two families' blind spots differ most. Both Correctness reviewers get the identical prompt.

Each prompt is assembled from files, not from memory:

1. `reviewer-brief.md` in full — the shared discipline.
2. Exactly one axis file — `standards.md`, `spec.md`, or `correctness.md` — with its `<!-- Main thread: -->` placeholder filled in first.
3. The diff command and the commit list from step 1.

Write each assembled prompt to `.reviews/<slug>-code-review-<n>-<axis>.prompt.md` and dispatch from there (`mkdir -p .reviews` if needed; `<n>` is the review round, starting at 1). Never hand a reviewer a path inside this plugin — the headless one cannot read it and will invent something instead.

If the spec was not found in step 2, drop the Spec reviewer and note it in the report.

### 5. Land the findings, then judge them

Copy every reviewer's findings **verbatim** into `.reviews/<slug>-code-review-<n>.md`, grouped by axis. Do not rewrite or summarise them. Put one header line at the top recording the fixed point SHA.

Then work through them with `judging-agent-output`: re-check each anchor yourself, ask who gets hurt and whether this round should pay for it, and mark one disposition word under each finding — `accepted`, `rejected`, `duplicate`, `needs-evidence`, or `waived`. Close the file with one line of overall conclusion.

Only `accepted` findings drive rework. Shelved findings with a namable victim become GitHub issues tagged `needs-triage`; the rest live and die in the report.

### 6. Report

Present the findings under `## Standards`, `## Spec`, and `## Correctness`, each finding carrying its disposition word — including the rejected ones. Do **not** merge or rerank across axes; the axes are deliberately separate (see _Why three axes_). Verifying findings one by one is not reranking, and it does not licence blending the axes into a single list.

End with, per axis, the number of findings and how many were accepted, plus the worst accepted issue in that axis. Don't pick a single winner across axes — that's the reranking the separation exists to prevent. Add one closing line for anything shelved: what it was and which issue now holds it.

### 7. Re-review after fixes

When the accepted findings have been fixed and the branch comes back:

- The fixed point becomes the previous round's `HEAD`, recorded in that round's trace header. The reviewers only see the fix diff.
- Tell each reviewer this is a re-review, and give it the previous trace path. Its job is two things only: did the accepted findings actually get fixed, and did the fixes break something.
- Findings already marked `rejected`, `duplicate`, or `waived` may not be raised again without new evidence. Reworded repeats don't count as new evidence.
- If the same `accepted` finding survives two rounds of fixes, stop. Ask yourself whether the fix is aimed at the wrong place or whether the finding should never have been accepted, and take it to the user.

## Why three axes

A change can pass one axis and fail the others:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**
- Code that is well-written and does what was asked, and still drops a null on the failure path → **Standards pass, Spec pass, Correctness fail.**

Reporting them separately stops one axis from masking another. The third axis exists because the first two are both comparisons against a document — one against the conventions, one against the spec — and a diff can match both documents perfectly and still not work.
