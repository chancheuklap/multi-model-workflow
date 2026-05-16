# AgentFlow Issue-Backed Planning Evidence

Read-only evidence captured from `/Users/cheuklapchan/agentflow`.

## Inputs Checked

- `docs/superpowers/specs/2026-05-16-ai-video-review-batch-completion-design-draft.md`
- `docs/issues/2026-05-17-ai-review-batch-completion-progress.md`
- `docs/issues/2026-05-17-ai-review-failed-completion-retry-product-results.md`
- `docs/issues/2026-05-17-ai-review-settlement-topup-charge-gate.md`
- `docs/issues/2026-05-17-compass-video-review-workspace-feedback.md`
- `docs/issues/2026-05-17-xhy-information-presentation-message-center-home.md`

## Observed Shape

The design draft has a `后续 issue 拆分` section that explicitly defines these files as large issues. The sampled issue files each contain:

- `Type`
- `Source`
- `What to build`
- `User-visible behavior`
- `Acceptance criteria`
- `Blocked by`
- `Out of scope`

No corresponding vertical small issue files were present for this issue set in `docs/issues`.

## Expected Workflow Result

`orchestrate-plan-writing` must not generate a final implementation plan from these inputs yet.

Correct result:

```text
### Verdict
NEEDS_ISSUES

### Missing
- vertical small issues under each large issue

### Upstream route
- to-issues

### Suggested prompt
- Split each reviewed large issue into vertical small issues. Each small issue must preserve Source, acceptance criteria, blocked-by, AFK / HITL, out of scope, and independent verification.
```

After `to-issues` produces small issues, the same design and issue set should enter `orchestrate-plan-writing` again. The generated plan should then use each large issue as a top-level section and each small issue as one Task Pack.
