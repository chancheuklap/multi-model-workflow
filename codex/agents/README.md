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
- `complex_coding_worker`: high-risk implementation for migrations, billing, auth, permissions, runtime, shared contracts, compatibility, rollback, and manual gates.
- `code_reviewer`: executes parent-supplied Design Review, Plan Review, Pack Review, Final Intent Review, behavior-test review, vertical Task Pack review, and architecture finding classification payloads; does not define Orchestrate phase contracts itself.
- `code_explorer`: narrow read-only file, symbol, call-chain, test-entry, config-source, and small behavior fact lookup.
- `complex_code_explorer`: read-only diagnosis loop, feedback-loop gap reporting, facts vs inference, architecture friction vocabulary, dependency-category seam analysis.
- `release_reviewer`: early / final release-risk gate for data, permissions, billing, migrations, deploy order, rollback, compatibility, and manual verification; not a replacement for baseline design / plan / pack / final review.
- `docs_worker`: low-risk documentation cleanup, self-contained design / issue drafting, stale reference cleanup, and mechanical structure repair.
