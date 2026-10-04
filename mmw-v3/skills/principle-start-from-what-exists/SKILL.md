---
name: principle-start-from-what-exists
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Start from What Exists

Every design and every implementation starts from what already exists. Before you propose an approach or write non-trivial code, search for it.

**Why:** Building what already exists costs the build and then the upkeep, and usually ends worse than the thing that was already used and fixed by others.

**Pattern:**
- Search for open-source implementations of the same thing, libraries that cover it, and projects that solve the same problem in another form. Search GitHub and the package registries before the general web, in that order.
- Look for what covers 80% of the need, not an exact-name match. Read at least one implementation file of each serious candidate, not only its README.
- Decide one of three: use it as is, fork or extend it, or build it yourself. Building is allowed only after a real search came back empty.
- The reply names what you searched, the URLs of what you read, and the decision with its reason, so the search is checkable and the next agent does not repeat it. Figures such as stars, last commit, or downloads are ones you saw, never estimated.

**Stop:** the rule does not apply to a trivial change in existing code, to fixing a bug in place, or when the owner has already named the project to build on.
