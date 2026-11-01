---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings. Start every sub-agent with a fresh context window.

Report findings. Do not apply fixes. Read issue sources through the repository's configured tracker or the host's tools, including their full bodies and comments.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If they didn't specify one, ask for it.

Resolve the fixed point and `HEAD` to commit IDs once, and record their merge-base. Capture the diff command as `git diff <merge-base> <reviewed-commit>` and the commit list via `git log <fixed-point-commit>..<reviewed-commit> --oneline`. Both reviewers and every reproduction use this same reviewed commit. State that uncommitted changes are outside this comparison.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside two parallel sub-agents.

### 2. Identify the spec source

Use a spec supplied by the user as text or a path. Otherwise look for the originating spec in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched with the repository's configured tracker or the host's tools.
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Search the repo for every file that documents how code should be written. When `CODING_STANDARDS.md` or `CONTRIBUTING.md` exists, it must be on the list.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn both sub-agents in parallel

Use the host's general-purpose subagents and existing model settings. Issue one Standards call and one Spec call together, in the foreground. Each reviewer works only its own axis and does not read the other reviewer's analysis.

Give the Spec reviewer its own temporary directory for reproduction scripts and output, and include its path in the prompt. Reproductions use the reviewed commit and independent test data without changing the reviewed code.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** should include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Keep the findings summary under 400 words; attach reproduction evidence separately."
- This adversarial task, pasted in full:

  > Break this change. Actively seek conditions under which the implementation violates the spec. Trace the real execution paths behind the requirements, identify assumptions the implementation relies on, and challenge them with counterexamples. Find inputs, states, or sequences of operations that make the implementation fail, rather than stopping because the expected checks appear in the code.
  >
  > Construct and run counterexamples against the real code at the reviewed commit. For each runtime finding, report a title, code location, the exact command, actual output, required output, and the spec text that makes the output wrong. Include the setup and working directory needed to rerun from the same initial state. Keep reproduction scripts and output in your assigned temporary directory, using independent test data without modifying the reviewed code.
  >
  > Missing requirements and unrequested behaviour that can be established directly from the spec and code still belong in the report, with their citations. Claims about actual runtime behaviour require a run. If a suspected failure cannot be run, list it separately as unverified with the reason. No findings is a valid result. Report findings and reproduction materials, not fixes.

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Verify the findings

The main session checks the returned findings against the reviewed commit:

- **Standards and static spec differences:** read the cited rule or requirement and the code. Keep supported findings. Preserve the distinction between documented violations and structural judgement calls; a structural judgement does not need a runtime failure.
- **Runtime claims:** rerun the reproduction from the same initial state. Keep the finding only when the output demonstrates the failure and the failure contradicts the cited requirement or documented rule. Reproducing a phenomenon alone does not establish that it is wrong.

Record why unsupported findings are dropped. If a reproduction cannot be rerun, report it as unverified with the reason, not as a clean result or a disproved defect. Finish when every returned finding has a checked conclusion or an explicit verification limitation. The main session performs this check directly.

### 6. Aggregate

Present the checked reports under `## Standards` and `## Spec` headings, retaining their supporting evidence and judgement-call labels. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

Under each axis, include the dropped-finding count and reasons, and any unverified limitations. When no findings survive, say "no verified findings" alongside those limitations. An unavailable or incomplete reviewer is a review limitation, not a clean result.

End with a one-line summary: total supported findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
