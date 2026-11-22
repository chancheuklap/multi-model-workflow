# Plan stage review

You are reviewing a complete multi-phase plan produced by [Multi-phase plan](../../mmw-mode/playbooks/multi-phase-plan.md) after `check-plan.mjs` has already passed. Follow [Reviewer contract](../SKILL.md#reviewer-contract), then check the draft against its agreed spec or design across the three areas below.

Skip mechanical format rules `check-plan.mjs` already enforces (intro length, required top-level headings, phase sub-block order, checkbox presence, long dashes, curly quotes, and mid-sentence colons).

## 1. Upstream inheritance and drift

- **Complete outcome coverage.** Every in-scope user story or agreed outcome from the spec maps to the phase that delivers or enables it, or cites concrete evidence that existing behavior already satisfies it.
- **Verbatim expected results.** Whenever a user story states an `expected result` sentence, the delivering phase's `You see` block copies that sentence unchanged.
- **Constraints and prototypes preserved.** `Implementation Decisions`, `Testing Decisions`, `Out of Scope`, `Further Notes`, and any `approved prototype` from the spec hold across every phase without scope creep. If a prototype altered an agreed product decision, flag that the spec must be updated before planning from it rather than diverging silently in the plan.

## 2. Plan process and contract

- **Consistent dependencies.** Each phase's `Depends on` names real prerequisite results that match phase order, with no forward dependency on a later phase and no unstated hidden prerequisite.
- **Closed verification chain.** In each phase, `Build` states changes that implement agreed decisions and names which user story or outcome they enable; `You see` states observable outcomes (exact screen state, log line, or copied `expected result`); `Verify` pairs each outcome with a concrete check (test case, live scenario, formal check, or performance probe with baseline and pass/fail rule). Preparatory phases state what they enable and how to prove the prerequisite is ready.
- **Verification skill coverage.** Live checks in `Verify` name the project's `verify-<app>` skill (or `verify-this` when none matches) and how to drive the surface. When any phase touches `covered code` or guarded state, `Verification skill`, `Boot recipe`, and `Verify` name every matching project `formal verification skill` (`formal-verify-<area>` or a differently named skill covering that area) and its check command. Any surface that cannot be exercised, and any uncheckable `bound` or `assumption` gap, is recorded as a risk in Appendix C.
- **Concrete execution setup and appendices.** `How to read this` names a real execution playbook (`autopilot-full.md` or `autopilot-stack.md`). `Execution setup` and `Boot recipe` hold concrete project parameters with no leftover `<...>` placeholders. Interaction changes name required screenshots or video in `Review gate`. Prototype-answered questions record branch, commit SHA, and artifact links in Appendix A, with unproven questions listed explicitly.

## 3. Document clarity

- **Diátaxis mode discipline.** The main body stays pure how-to (executable checklist steps). Explanations, rejected alternatives, prototype evidence, and risks live in Appendices A through D rather than inside phase steps.
- **Specific, unslopped prose.** Headings state the task or finding, terminology matches the spec and project glossary, and checks avoid vague language ("verify it works", "ensure smooth UX") and AI filler.
