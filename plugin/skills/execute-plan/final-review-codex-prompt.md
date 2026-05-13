# Final Review — Codex Second Opinion

Phase B：与 workflow-auditor 并行调度 codex:codex-rescue，用不同模型对最终实现做独立第二意见审查。

## 调度方式

用 Agent tool 调度，`subagent_type: "codex:codex-rescue"`。将下方 prompt 作为 Agent 的 prompt 参数发送。

## 发送给 codex:codex-rescue 的 prompt

Review the implementation changes in this repository since commit [STARTING_COMMIT_SHA].
The design doc is at [DESIGN_FILE_PATH] and the plan is at [PLAN_FILE_PATH].

<task>
Independently verify the full implementation for correctness, regression risks, and potential issues.
You are a second-opinion reviewer — another reviewer is checking in parallel using a different approach.
Focus on what a fresh pair of eyes from a different model would catch.

Your review scope: `git diff [STARTING_COMMIT_SHA]..HEAD`

Check these dimensions:
1. Correctness: Are there logic errors, off-by-one bugs, null/undefined handling gaps, or type mismatches?
2. Regression: Do the changes break any existing functionality? Run the test suite and report results.
3. Security: Are there injection risks, auth bypasses, sensitive data leaks, or insecure defaults?
4. Integration: Do cross-file changes work together correctly? Are there inconsistencies between modules?
5. Design alignment: Does the implementation match the design doc's stated intents?
</task>

<structured_output_contract>
Return:
1. findings ordered by severity (critical, high, medium, low)
2. for each finding: exact file:line + specific issue + supporting evidence (code snippet, test output)
3. test suite results (pass/fail counts)
4. brief next steps or recommendations
</structured_output_contract>

<grounding_rules>
Ground every claim in actual code reads or test outputs.
If a point is an inference (e.g., "this might cause a race condition under load"), label it clearly.
Distinguish between: definite bugs (evidence confirms), likely issues (strong indicators), and observations (worth noting but uncertain).
Do NOT report stylistic issues or pre-existing problems not introduced by this change.
</grounding_rules>

<dig_deeper_nudge>
After finding initial issues, check for:
- Second-order failures (if A fails, does B handle it gracefully?)
- Empty-state and error-path handling
- Retry and rollback paths
- Race conditions or timing dependencies
- Edge cases not covered by tests
- Stale imports or dead code introduced by the changes
</dig_deeper_nudge>

<verification_loop>
Before finalizing, verify that:
1. Each finding is material and actionable (would a developer need to fix this before shipping?)
2. Each finding has concrete file:line evidence
3. You haven't flagged pre-existing issues that weren't introduced by this change
4. The test results you report are from a fresh run, not cached
</verification_loop>
