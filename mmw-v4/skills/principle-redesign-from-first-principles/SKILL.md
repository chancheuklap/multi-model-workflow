---
name: principle-redesign-from-first-principles
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Redesign From First Principles

When integrating a change, don't bolt it onto the existing design. Redesign as if the requirement had been a foundational assumption from the start.

- Read all affected files and understand the current design
- Ask: "if we were writing this from scratch with this new requirement, what would we build?"
- Propagate the change through every reference: types, docs, examples, rationale sections
- Think about the whole redesign, then deliver it incrementally

This is the method for preserving option value when integrating changes into an existing design.

**In a diff:**

- A change patched onto the design rather than read as if the design always held it: ask whether the code would look like this had the requirement been known from the start, and write that form. One that reaches beyond the ticket's files is a finding outside the ticket.

## When code keeps fighting its sketch

When the code written against a sketch from the **prototype** skill keeps producing friction the sketch can't absorb, throw the sketch out. Don't bolt fixes onto a wrong design, per **principle-fix-root-causes**.

A worker whose ticket holds the sketch under **Read first** does not scrap it: it raises a `contract` child naming the tells below, as Work a ticket says, and the session that coordinates the ticket decides.

The signal is a *pattern*, not single instances. Tells:

- The same shape of workaround appearing repeatedly across unrelated code.
- Multiple unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Two or more independent deviations from the sketch of the same shape across the implementation.

Use judgment. A few edge cases don't condemn an architecture. Some problems are legitimately complex. Complexity in the data is not complexity in the design.

When you scrap:

1. Re-run the **how** skill over what's been built.
2. Redesign as if the new constraints had been day-one assumptions.
3. Subtract before adding, per **principle-subtract-before-you-add**. The new sketch should be smaller than the old one before it grows.
4. Re-run the **prototype** skill's sketch branch.
