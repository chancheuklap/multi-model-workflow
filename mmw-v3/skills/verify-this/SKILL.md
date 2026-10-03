---
name: verify-this
description: "Verify a claim with fresh local evidence: restate it falsifiably, capture baseline and treatment, compare artifacts, and return VERIFIED, NOT VERIFIED, or INCONCLUSIVE."
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
5. Run the repository's own checks on the changed state: its checker command (type checks, lint) and the tests its own instructions (its `AGENTS.md` and the files it points to) name for the files the change touched; a full suite runs only when user rule 15 allows it. Read what each run ran: a run that collected no test, or none that reach the changed files, has checked nothing. When the repository names no tests for the changed files, say so in the output, and the surface evidence decides the verdict.
6. Compare raw artifacts: numbers, screenshots, terminal transcripts, HTTP responses, profiles, heap snapshots, or test output.
7. Return exactly one verdict: `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`.

When this session has already run the claim on its surface before and after the change (a feedback loop on the original scenario), those runs are the baseline and treatment: point to them instead of capturing them again.

## Local Surfaces

- The repository's own verification skill, when it has one (`.agents/skills/verify-<app>/`, made by the `create-verification-skill` skill): its Launch, Doctor, Drive, Evidence and Cleanup sections, and the feature file for what the claim touches, drive every surface it covers. Without one, use the surfaces below, and say in the Reasoning that `/create-verification-skill` would give this repository one.
- Code behavior: focused unit/integration tests or a minimal repro script.
- CLI/TUI behavior: `control-cli`, terminal transcript, or demo recording.
- UI behavior: `control-ui`, screenshots, accessibility snapshots, or browser traces.
- API behavior: local HTTP/RPC request and response diff.
- Performance: same-machine baseline/treatment timings or CPU profiles.
- Memory: heap snapshots before and after the suspected operation.

## Artifact Layout

When safe to write artifacts:

```text
/tmp/verify-this/<claim-slug>/
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
