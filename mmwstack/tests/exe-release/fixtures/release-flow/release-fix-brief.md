# Release fix brief

The release is stuck on a fixable failure. Fix it from the findings below.

Rules:

- **Commit to the current branch**, then `resume`. The remote build takes `git archive HEAD`; edits left in the working tree never reach the build machine, so not committing means not changing, and the next round fails on the same code.
- If the same root cause survives a second fix, stop and hand it to a human. Do not keep looping.

## Findings

- [P1] missing_module (missing_module:scipy): 缺 scipy
  Suggested fix: 补依赖
