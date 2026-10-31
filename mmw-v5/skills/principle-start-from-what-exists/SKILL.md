---
name: principle-start-from-what-exists
description: Use before choosing a new nontrivial implementation approach. Search the repository and existing external solutions, then justify reuse, extension, or a new implementation. Skip trivial changes and settled approaches.
---

# Start From What Exists

Every design and every implementation starts from what already exists.

**Why:** A search the reply records is checkable, and the next agent does not repeat it. Building is allowed only after a real search came back empty.

**Pattern:**
- Before you propose an approach or write non-trivial code, search for it. First this repository and the material the task names: a helper, module or pattern that already does it. Then open-source implementations of the same thing, libraries that cover it, and projects that solve the same problem in another form.
- The outside search goes to GitHub and the package registries before the general web, in that order. Look for what covers 80% of the need, not an exact-name match, and read at least one implementation file of each serious candidate, not only its README.
- Then decide one of three: use it as is, fork or extend it, or build it yourself.
- The reply names what you searched, the URLs of what you read, and the decision with its reason.
- Stated figures such as stars, last commit or downloads are ones you saw, never estimated.

**Does not apply** to trivial changes in existing code, to fixing a bug in place, or when the owner has already named the project to build on. A ticket's settled approach counts as a named project.

**In a diff:**

- A hand-built copy of something the platform already does (native sticky positioning, scroll targeting, hit-testing, focus handling): use the native behavior. A manual reimplementation breeds real bugs, so a finding against one defaults to a fix.

Distinct from **principle-first-principles-thinking**, which says, while reasoning, to use a proven pattern that already fits. This is the search you run before you build, and the record you leave of it.
