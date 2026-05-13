# Plan Review — Codex Second Opinion

Phase 0b：与 workflow-auditor 并行调度 codex:codex-rescue，用不同模型对计划文档做独立第二意见审查。

## 调度方式

用 Agent tool 调度，`subagent_type: "codex:codex-rescue"`。将下方 prompt 作为 Agent 的 prompt 参数发送。

## 发送给 codex:codex-rescue 的 prompt

Review the implementation plan at [PLAN_FILE_PATH] for this project.
If a design doc exists, also read [DESIGN_FILE_PATH] for context.

<task>
Independently verify this implementation plan for correctness and executability.
You are a second-opinion reviewer — another reviewer is checking in parallel.
Focus on what a fresh pair of eyes would catch.

Check these dimensions:
1. Do ALL file paths, function names, and class names referenced in the plan actually exist in the codebase? Use grep/find to verify each one.
2. Are the task descriptions clear enough that an implementer could start without asking questions?
3. Are there logical contradictions between tasks? (Task A assumes X, Task B assumes not-X)
4. Are there missing tasks? (The plan says "refactor module X" but doesn't include updating tests for module X)
5. Are there risky assumptions? (Plan assumes an API exists that might not, or assumes a specific data shape)
</task>

<structured_output_contract>
Return:
1. findings ordered by severity (critical, high, medium, low)
2. for each finding: file path or plan section + specific issue + supporting evidence (grep output, code snippet)
3. brief next steps or recommendations
</structured_output_contract>

<grounding_rules>
Ground every claim in actual grep results or file reads.
If a point is an inference (e.g., "this path might not exist", "this function signature appears to have changed"), label it clearly.
Do NOT report stylistic or formatting issues.
</grounding_rules>

<dig_deeper_nudge>
After initial checks, look for:
- Tasks that reference each other in circular dependencies
- Tasks that modify the same file but are in different sections (merge conflict risk)
- Implicit ordering dependencies not marked in the plan
- Project engineering rules violations (read CLAUDE.md if it exists)
</dig_deeper_nudge>

<verification_loop>
Before finalizing, verify that each finding is material — would it actually block or break the implementation?
Remove any low-confidence observations that aren't directly supported by grep/read evidence.
</verification_loop>
