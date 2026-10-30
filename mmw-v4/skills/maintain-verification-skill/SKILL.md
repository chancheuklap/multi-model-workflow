---
name: maintain-verification-skill
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Maintain verification assets

| Work in hand | Read |
| --- | --- |
| Find the existing features affected by a planned change | **Find affected features** below, then return the list to the caller |
| Review and maintain verification assets | [Maintain the product](references/maintain.md) |

## Find affected features

For a product with a `verify-<product>` skill, list its `features/` and read each
feature file's first three lines: `# <feature>`, `Route:`, and `Tests:`. Read only
the affected feature files in full. List the affected existing features by their
feature map names and say whether each behavior stays unchanged or changes.

Return the affected feature names, paths and unchanged/changed behavior decisions. This lookup ends here; it does not start maintenance.
