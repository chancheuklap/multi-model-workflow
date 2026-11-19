---
name: prepare-ui-acceptance
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Prepare UI acceptance

Prepare this ticket's fixed-step UI tests and feature registration from its agreed baseline. Use the product-local verification method supplied by the caller, and return the tests, complete command and evidence to that caller. Missing reusable launch or drive capability returns its prerequisite to the preparation step.

Use the **test-audit** skill's writing branch. Keep the caller's product, issue, effort checkout, settled behavior and valid proof. Read the complete product SKILL.md and config, then the affected feature files. The product method supplies launch, rules, drive, evidence and cleanup. Reuse matching preparation.

During initial verification generation, the creator supplies its usable draft recipe, config and feature Proof. Prepare its first proving test and return to that same creator for end-to-end proof before handoff. This method does not invoke its creator or run whole-product maintenance.

## Choose the baseline

| Work | Read |
| --- | --- |
| New or changed UI design | [New design](references/new-design.md) |
| Repair with settled expected behavior | [Repair](references/repair.md) |
| Structure changes while behavior stays unchanged | [Preserve behavior](references/preserve-behavior.md) |
| Correct an erroneous frozen test | [Correct acceptance](references/correct-acceptance.md) |

Complete the selected method, then register and return its result below. Established UI acceptance remains read-only to implementation workers.

## Register and return

Read the **create-verification-skill** skill's `references/feature-map.md` for the shared feature-file format and source rules. Update the changed behavior from its settled sources, put Proof before its test, and commit Tests and Driving it with e2e with that test. Each ticket owns a new e2e file; keep unchanged pins in their registered files. Copy the product's complete Launch command, with config, preparation and independent output path, for the writer's CHECK. Preserve backend proof separately from e2e.

Commit and push the prepared test, feature registration and description on the caller's effort branch before execution. Return their paths, the baseline used, the complete command, the observed result and evidence paths, and any unproved scope. Missing access or an unsupported target returns the specific prerequisite to the caller, not a claimed pass. Existing UI assets stay read-only during execution.
