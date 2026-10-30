---
name: sharpen
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

Before starting, ask how a top expert would approach this task (their raw sources, their real methods, an outside check that the result is right), what the user is really after, and whether the task is over- or underspecified. Loosen constraints that don't serve the goal as readily as you add ones that do. Apply **principle-never-block-on-the-human** to distinguish engineering calls from decisions only the owner makes. Fold in only what makes the work better, not bigger, but always keep one outside check that the result is right. Hand these four conclusions back to whoever invoked this skill, each with one sentence explaining why:

- The expert approach and its primary sources.
- What you understand the user is really after.
- The constraints you propose to loosen or add.
- The outside check that will establish whether the result is right.

When a step names this skill, hand the conclusions to that step so it asks the owner about them together with its own questions in one batch. When the owner types `/sharpen`, hand the conclusions directly to the owner. Wait for the owner's reply before starting work that depends on an owner's decision. Then continue with the conclusions the owner agreed to. Don't hand back a rewritten prompt.
