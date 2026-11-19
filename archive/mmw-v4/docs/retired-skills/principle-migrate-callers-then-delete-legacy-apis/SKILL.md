---
name: principle-migrate-callers-then-delete-legacy-apis
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Migrate Callers Then Delete Legacy APIs

When we decide a new API is the right design, migrate callers and remove the old API in the same refactor wave instead of preserving compatibility layers.

- Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details
- Before changing a function, find every caller
- When what you add supersedes an existing branch, guard or file, not only an API, delete it in the same commit

**When this applies:**
- No external users depend on backward compatibility
- The project can absorb coordinated breaking changes
- The new API is part of a simplification or refactor initiative

**In a diff:**

- A new path added beside the old one, or compatibility scaffolding kept after the migration is done: migrate the callers and delete the old path in the same change.
