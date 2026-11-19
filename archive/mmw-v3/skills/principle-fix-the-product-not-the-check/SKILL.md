---
name: principle-fix-the-product-not-the-check
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Fix the Product, Not the Check

A check that fails is answered by fixing the product, or by recording that the criterion was not met. It is never answered by changing the check, its harness, its test, its expected output or the baseline it compares against until it passes.

**Why:** The checks exist so the owner can trust finished work without reading its code. An honest "not met" costs the owner one look; a false pass lands broken behavior under a green mark, and everything built on it inherits it.

**Pattern:**
- A check that is itself wrong (it tests the wrong thing, names the wrong file, expects the wrong value) is reported where its owner sees it, with what it should be; on a ticket that is a `contract` child. The work it judges does not correct it.
- Loosening an expected value, adding a retry, a sleep or a skip, or widening a timeout until red turns green is changing the check.

**Stop:** when no fix is in sight, stop trying and record what each round tried. That record is the whole account of the trying.

Distinct from **principle-a-check-must-be-able-to-fail**, which asks whether a check can fail at all before you trust it.
