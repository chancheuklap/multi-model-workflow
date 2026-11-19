---
name: principle-experience-first
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Experience First

When implementation convenience conflicts with user delight, choose delight.

- Every feature, control, and option must be justified
- Ship less, ship better (polished experience with three features beats rough one with ten)
- Get the details right (transitions, alignment, spacing, feedback, error states)
- Tighten the core loop (every feature should serve the central workflow or get out of the way)

The user is whoever consumes the work. For a UI that is the end user. For a library or an internal API it is the colleague who imports it. The engineer who maintains the code next is a user too. Weigh their experience the same way, and explain impact from their perspective.

**In a diff:**

- A feature, control or option the experience does not justify, or one shipped half-finished: cut it or finish it. A half-finished feature is worse than a missing one.
- A visual change made on purpose is not a defect. One that costs accessibility (focus visibility, keyboard navigation, color contrast) or changes a component's API contract is, however intentional.

Foundations should serve the experience. **principle-sequence-verifiable-units** governs the sequence of work. This principle governs the target.
