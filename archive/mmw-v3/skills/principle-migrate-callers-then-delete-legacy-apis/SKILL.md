---
name: principle-migrate-callers-then-delete-legacy-apis
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Migrate Callers Then Delete Legacy APIs

When we decide a new API is the right design, migrate callers and remove the old API in the same refactor wave instead of preserving compatibility layers.

**Rule:**
- Do not keep legacy API paths only because internal callers still exist
- Inventory callers, migrate them, and delete the old API immediately
- Before changing a function, helper or API, grep every caller. A defect in shared code is fixed in the shared code, once, for all of them, not at the one caller that met it
- Treat temporary adapters as exceptional and time-boxed, not default architecture
- Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details

**When this applies:**
- No external users depend on backward compatibility
- The project can absorb coordinated breaking changes
- The new API is part of a simplification or refactor initiative
- The grep and the fix in shared code apply to every change of code that other code calls, a bug fix included

Keeping both old and new APIs creates dual-path complexity, slows cleanup, and makes the codebase feel append-only.
