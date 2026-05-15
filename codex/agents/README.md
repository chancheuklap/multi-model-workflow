# Codex Agent Templates

Sync templates:

```bash
bash codex/agents/sync-agents.sh --dry-run
bash codex/agents/sync-agents.sh --apply
```

Roles:

- `coding_worker`
- `complex_coding_worker`
- `code_reviewer`
- `release_reviewer`
- `code_explorer`
- `complex_code_explorer`
- `docs_worker`

Role methods:

- `coding_worker`: public-behavior vertical TDD, no horizontal slicing, external-boundary mocks only, testable interface discipline.
- `complex_coding_worker`: root-cause feedback loop, loop refinement, falsifiable hypotheses, instrumentation cleanup, correct-seam regression.
- `code_reviewer`: Design Review, Plan Review, Pack Review, Final Intent Review, behavior-test review, vertical Task Pack review, architecture finding classification.
- `complex_code_explorer`: read-only diagnosis loop, feedback-loop gap reporting, facts vs inference, architecture friction vocabulary, dependency-category seam analysis.
- `release_reviewer`: production-risk review across design, plan, implementation, and final release for data, permissions, billing, migrations, deploy order, rollback, and manual verification.
