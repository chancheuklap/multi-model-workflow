---
name: verify-this
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Verify This

Verification is not a recap. It proves or disproves a specific claim with repeatable evidence.

## When To Use

- The user asks "verify this", "prove it works", "did this fix it", or "show me the evidence".
- A bug fix needs a before/after repro.
- A UI, CLI, API, performance, or memory claim needs measurement.
- A test passes but the user-visible behavior still needs confirmation.

Do not use this for vague claims like "the code is cleaner". Ask for a measurable claim first.

## Workflow

1. Restate the claim in falsifiable form: condition, metric, and threshold.
2. Pick the smallest local surface that can disprove it.
3. Capture a baseline from the old state: merge base, parent commit, failing branch, or current broken repro.
4. Capture treatment from the changed state with the same command, data, warmup, and environment.
5. Run the repository's own checks on the changed state before the comparison. Run its checker command and the tests its own instructions name for the files the change touched. Those instructions are its `AGENTS.md` and the files that file points to. A full suite runs only when those instructions name one for this change. Read what each run ran. A run that collected no test, or none that reach the changed files, has checked nothing. When the repository names no tests for the changed files, say so in the output, and the surface evidence decides the verdict.
6. Compare raw artifacts: numbers, screenshots, terminal transcripts, HTTP responses, profiles, heap snapshots, or test output.
7. Return exactly one verdict: `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`.

## Local Surfaces

When the surface is the running product, follow the `ui-acceptance` skill's **Five rules while the product is running**.

- Code behavior: focused unit/integration tests or a minimal repro script.
- CLI/TUI behavior: the `ui-acceptance` skill's `references/control-cli.md`, a terminal transcript, or a demo recording.
- UI behavior: the `ui-acceptance` skill's `references/control-ui.md`, screenshots, accessibility snapshots, or browser traces.
- API behavior: local HTTP/RPC request and response diff.
- Performance: same-machine baseline/treatment timings or CPU profiles.
- Memory: heap snapshots before and after the suspected operation.

## Artifact Layout

When safe to write artifacts:

```text
.scratch/verify/<claim-slug>/
├── claim.md
├── timeline.md
├── baseline/
├── treatment/
├── diff/
└── verdict.md
```

If artifacts may contain sensitive code, prompts, screenshots, HTTP bodies, or heap data, keep only the minimal inline evidence unless the user agrees to disk storage.

## Verdict Rules

- `VERIFIED`: baseline and treatment differ in the predicted direction, by the claimed threshold, with no obvious confound.
- `NOT VERIFIED`: the behavior is unchanged, moves the wrong way, or misses the threshold, or a repository check fails.
- `INCONCLUSIVE`: no valid baseline, noisy signal, failed measurement, an environment difference invalidates the comparison, or a repository check that ran reached none of the changed code.

## Output

Use this shape:

```text
VERIFIED | NOT VERIFIED | INCONCLUSIVE
Claim: <falsifiable claim>

Evidence:
<metric/artifact>: baseline=<...>, treatment=<...>, delta=<...>, threshold=<...>
<check command>: <result, and what it reached>

Reasoning:
<one tight paragraph naming the evidence and any confounds>
```

Do not soften a negative result. A clear `NOT VERIFIED` is useful.
