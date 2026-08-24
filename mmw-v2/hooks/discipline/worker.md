MMW DISCIPLINE ACTIVE — role: worker

每条纪律逐字取自 `docs/specs/landing-closeout/discipline-sources.md`（下称存档），条目后一行「出处」指向存档章节与原件行号。

## 反过度构建

出处：存档第 1 章 ponytail/AGENTS.md（1-32 行）第 5-13 行。

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here, don't re-write it.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

出处：存档第 1 章 ponytail/AGENTS.md 第 15 行。

The ladder runs after you understand the problem, not instead of it: read the task and the code it touches, trace the real flow end to end, then climb.

出处：存档第 1 章 ponytail/AGENTS.md 第 17 行。

Bug fix = root cause, not symptom: a report names a symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the path the ticket names leaves a sibling caller still broken.

出处：存档第 1 章 ponytail/AGENTS.md 第 19-28 行。

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins, but only once you understand the problem. The smallest change in the wrong place isn't lazy, it's a second bug.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- Pick the edge-case-correct option when two stdlib approaches are the same size, lazy means less code, not the flimsier algorithm.
- Mark deliberate simplifications that cut a real corner with a known ceiling (global lock, O(n²) scan, naive heuristic) with a `ponytail:` comment naming the ceiling and upgrade path.

出处：存档第 1 章 ponytail/AGENTS.md 第 30 行（四条安全红线在此句内）。

Not lazy about: understanding the problem (read it fully and trace the real flow before picking a rung, a small diff you don't understand is just laziness dressed up as efficiency), input validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs (the platform is never the spec ideal, a clock drifts, a sensor reads off), anything explicitly requested. Lazy code without its check is unfinished: non-trivial logic leaves ONE runnable check behind, the smallest thing that fails if the logic breaks (an assert-based demo/self-check or one small test file; no frameworks, no fixtures). Trivial one-liners need no test.

## 反偷懒

出处：存档第 2 章 unlazy@origin/v1:SKILL.md（1-68 行）第 34 行「The Depth Tree method」第 6 条。

6. **Stop condition.** A leaf is finished when the budget is spent or a full pass finds nothing to improve. "It works" is never the stop condition.

出处：存档第 2 章 unlazy@origin/v1:SKILL.md 第 54 行「Enforcement rules」。

**Full files, full lists, full sweeps.** If the task says all 80 files, the count of files actually opened must be 80, and you state that count. Sampling is only acceptable when declared.

出处：存档第 2 章 unlazy@origin/v1:SKILL.md 第 56 行「Enforcement rules」。

**Banned outputs.** The following are defects, not style: "TODO", "rest of the code unchanged", "simplified for brevity", "left as an exercise", stub functions, elided list items, and any completion claim without the measurement that backs it.
