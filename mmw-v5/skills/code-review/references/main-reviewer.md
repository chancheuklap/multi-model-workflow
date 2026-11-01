# Main reviewer

Three-axis review of the diff between `HEAD` and the fixed point supplied in your assignment:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?
- **Tests**: do the tests provide trustworthy, proportionate proof of the assigned change?

The axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings. Start every sub-agent with a fresh context window.

Report findings. Do not apply fixes. Read issue sources through the repository's configured tracker or the host's tools, including their full bodies and comments.

## Process

### 1. Pin the fixed point

Use the fixed point supplied in your assignment (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If it is missing, ask your caller for it.

Resolve the fixed point and `HEAD` to commit IDs once, and record their merge-base. Capture the diff command as `git diff <merge-base> <reviewed-commit>` and the commit list via `git log <fixed-point-commit>..<reviewed-commit> --oneline`. All reviewers and every reproduction use this same reviewed commit. State that uncommitted changes are outside this comparison.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside the parallel sub-agents.

### 2. Identify the spec source

Use the spec supplied in your assignment as text or a path. Otherwise look for the originating spec in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched with the repository's configured tracker or the host's tools.
2. A path supplied in your assignment.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask your caller where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Search the repo for every file that documents how code should be written. When `CODING_STANDARDS.md` or `CONTRIBUTING.md` exists, it must be on the list.

### 4. Spawn the axis sub-agents in parallel

Apply **principle-write-for-where-it-is-read**.

Use the host's general-purpose subagents and existing model settings. Issue one Standards call, one Spec call, and one Tests call together, in the foreground. Each reviewer works only its own axis and does not read the other reviewer's analysis.

Give the Spec and Tests reviewers separate temporary directories for reproduction scripts and output, and include the corresponding path in each prompt. Reproductions use the reviewed commit and independent test data without changing the reviewed code; Tests controls that alter code run in an isolated copy.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3.
- The instruction: "Invoke `code-review` and follow `references/standards-reviewer.md`. Return the Standards report to me."

**Spec sub-agent prompt** should include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The instruction: "Invoke `code-review` and follow `references/spec-reviewer.md`. Return the Spec report and reproduction materials to me."

**Tests sub-agent prompt** should include:

- The reviewed commit ID, full diff command, and commit list.
- The review task, available spec or ticket, and its testing decisions and acceptance criteria.
- The temporary reproduction directory assigned to the Tests reviewer.
- The instruction: "Invoke `code-review` and follow `references/tests-reviewer.md`. Return the Tests report and reproduction materials to me."

If the spec is missing, skip the Spec sub-agent and note this in the final report. The Tests reviewer can still assess the tests and available task evidence, and records the missing requirement source as a limitation. Wait for every axis you started before verifying and aggregating its findings.

### 5. Verify the findings

The main session checks the returned findings against the reviewed commit:

- **Standards and static Spec or Tests findings:** read the cited rule or requirement and the code. Keep supported findings. Preserve the distinction between documented violations and structural judgement calls; a structural judgement does not need a runtime failure.
- **Runtime claims:** rerun the reproduction from the same initial state. Keep the finding only when the output demonstrates the failure and the failure contradicts the cited requirement or documented rule. Reproducing a phenomenon alone does not establish that it is wrong.

Record why unsupported findings are dropped. If a reproduction cannot be rerun, report it as unverified with the reason, not as a clean result or a disproved defect. Finish when every returned finding has a checked conclusion or an explicit verification limitation. The main session performs this check directly.

### 6. Aggregate

Present the checked reports under `## Standards`, `## Spec`, and `## Tests` headings, retaining their supporting evidence and judgement-call labels. Do **not** merge or rerank findings, because the axes are deliberately separate (see _Why separate axes_).

Under each axis, include the dropped-finding count and reasons, and any unverified limitations. When no findings survive, say "no verified findings" alongside those limitations. An unavailable or incomplete reviewer is a review limitation, not a clean result.

End with a one-line summary: total supported findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why separate axes

A change can pass one axis and fail another:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

- Code meets the requirements but a test only repeats its mock's behavior → **Spec pass, Tests fail.**

Reporting them separately stops a passing axis from masking a failing one.


Return the completed review report to your caller.
