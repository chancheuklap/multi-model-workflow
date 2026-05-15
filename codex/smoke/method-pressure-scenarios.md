# Method Pressure Scenarios

Run with fresh Codex processes or subagent smoke tests.

## Code Reviewer: Design Alignment

Input shape:

- A design invents a new business object called `activation receipt` but never states owner, writer, reader, verifier, cleanup, or relationship to existing Gateway license terms.
- It says "sync is complete" without naming fields, states, systems, or acknowledgement protocol.
- It has no failure scenario.

Expected `code_reviewer` behavior:

- Raises findings for unresolved domain language and missing responsibility ownership.
- Runs at least one concrete success scenario and one failure/boundary scenario.
- Checks whether the new object requires SPEC/ADR/GUIDE treatment.

## Code Reviewer: Plan / Task Pack Slice

Input shape:

- A plan splits work into "write all backend", "write all frontend", "write all tests".
- Acceptance criteria are vague and no pack is independently verifiable.
- Some packs require user credentials but are not marked HITL.

Expected `code_reviewer` behavior:

- Flags horizontal slicing.
- Requires vertical packs that are demoable or independently verifiable.
- Requires AFK/HITL classification and real dependency order.
- Identifies missing public-behavior verification.

## Code Reviewer: Mockup Alignment

Input shape:

- A UI / UX plan references a webpage mockup but only says "implement the mockup".
- It does not list viewport, visible states, interaction, DOM / screenshot checks, or manual visual acceptance.
- Implementation changes templates and CSS, but no browser screenshot or DOM evidence is provided.

Expected `code_reviewer` behavior:

- Treats the mockup as a design / plan peer artifact, not a loose inspiration.
- Requires mockup path, target viewport, key states, interaction, and allowed deviations.
- Flags horizontal UI slicing if tasks are split into CSS / JS / template layers without independently verifiable page states.
- Blocks final pass until browser screenshot, DOM scan, responsive check, manual checklist, or visual regression evidence exists.

## Coding Worker: TDD Execution

Input shape:

- A worker receives one normal implementation pack with a public behavior and a tempting internal helper.
- The pack can be tested through an API, CLI, UI state, or public module interface.

Expected `coding_worker` behavior:

- Starts from one public behavior check.
- Avoids testing private helper details.
- Uses external-boundary mocks only.
- Reports behavior slices completed with verification evidence.

## Complex Explorer: Unknown Bug

Input shape:

- User reports a runtime bug with symptoms but no reproduction.
- Logs are incomplete and the likely module is uncertain.

Expected `complex_code_explorer` behavior:

- Builds or requests a feedback loop before guessing.
- If no loop is possible, returns attempted loops and needed artifacts.
- Produces 3-5 falsifiable hypotheses only after a loop or evidence source exists.
- Reports facts vs inference and likely fix owner.

## Complex Worker: Root-Cause Repair

Input shape:

- A bug has a reproducible failing command and affects billing/runtime/permissions.

Expected `complex_coding_worker` behavior:

- Re-runs or preserves the original feedback loop.
- States ranked hypotheses and the confirmed hypothesis.
- Instruments only one variable at a time.
- Cleans `[DEBUG-...]` temporary logs.
- Adds regression coverage at the correct behavior seam or reports missing seam.

## Release Reviewer: Production Gate

Input shape:

- A diff changes migration order, billing settlement, permission state, or deployment sequence.
- Local tests pass, but no rollback/manual verification evidence is shown.

Expected `release_reviewer` behavior:

- Separates blockers from manual verification and architecture follow-up.
- Blocks only data loss, permission bypass, billing inconsistency, irreversible migration, deploy-order breakage, broken rollback, or unverified production dependency.
- Does not block on style or ordinary architecture cleanup.
