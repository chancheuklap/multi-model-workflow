# External Claude Reviewer Bridge

Codex has two Claude reviewer lanes plus the normal internal Codex reviewer fallback.

## Automated Subscription Lane

Use `claude-subscription-review.sh` for the normal Codex -> Claude external
review path. It calls ordinary `claude` with stdin and deliberately does not use
`-p/--print` or Agent SDK mode.

This lane always runs `claude-opus-4-7` with `--effort high`.

```bash
bash codex/reviewers/claude-subscription-review.sh \
  --prompt-file .codex/multi-model-workflow/review-prompts/pack-review.md \
  --output .codex/multi-model-workflow/review-results/pack-review-claude.md \
  --review-name pack-review
```

Default tools are `Read,Grep,Glob`; `Edit`, `Write`, and `Bash` are not enabled.
This is the preferred cross-model review lane when Claude CLI is logged in to a
subscription-backed account.

When `.codex/multi-model-workflow/active-run-id` and the matching budget file
exist, the runner records successful review dispatches through
`codex/hooks/track-review-budget.sh`.

Internal Codex reviewer fallback does not pass through this bridge; the
coordinator records that review by invoking `codex/hooks/track-review-budget.sh`
with `MULTI_MODEL_WORKFLOW_REVIEW_LANE=internal-codex`.

## Extra-Usage Lane

`claude-review.sh` uses `claude -p`, so it is non-interactive Agent SDK usage.
It does not draw from the normal interactive subscription pool. It is disabled
by default and requires explicit authorization:

```bash
printf 'Return exactly: CLAUDE_REVIEW_BRIDGE_OK' \
  | bash codex/reviewers/claude-review.sh --allow-extra-usage --tools ""
```

Automated non-interactive review:

```bash
bash codex/reviewers/claude-review.sh \
  --allow-extra-usage \
  --prompt-file .codex/multi-model-workflow/review-prompts/pack-review.md \
  --output .codex/multi-model-workflow/review-results/pack-review-claude.md \
  --review-name pack-review
```

The extra-usage wrapper does not enable `Edit`, `Write`, or `Bash` by default.
It also uses the fixed review model contract: `claude-opus-4-7` with `--effort high`.

## Prompt Requirements

Parent prompts must be self-contained and include:

- review mode and angle;
- source artifacts and read-first list;
- scope and out-of-scope;
- pass condition;
- finding shape;
- return contract.
