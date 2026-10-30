# Frontend workflow and verification implementation

The owner approved the complete frontend workflow plan after advisor review and requested implementation, commit, push and a pull request without merging. Work continued on `codex/upstream-review-20261030` alongside the already committed upstream refresh. This was direct iteration, not an MMW run. ADR [0066](../adr/0066-ui-design-and-verification-have-distinct-owners.md) records the design and the narrow amendment to ADR 0055.

## Content and ownership

- Design a UI owns scope, owner operation, selection, repeated feedback, visible decisions, design freeze and the design return. The original prototype UI construction rules remain in prototype/references/UI.md. LOGIC, EXP and SKETCH remain methods, with their original source names.
- create-verification-skill separates environment preparation from full generation and proof. Its feature-file format stays authoritative. maintain-verification-skill retains the separate affected-feature lookup and owner-requested whole-product maintenance.
- prepare-ui-acceptance owns new-design, repair, preservation and contract-correction preparation. The original tests-from-prototype text is preserved in mmw-v4/docs/retired-skills/create-verification-skill/references/tests-from-prototype.md. The Notes example and original two-target requirements survive in the active skill.
- Independent tickets, batches, bug fixes and refactoring share Prepare verification in to-tickets/references/ticket-format.md. Existing adequate methods and matching results are reused.
- Formal create and maintain adapt `cursor/plugins` at `4dd1d05818d19792e7cd6e818f1667f95f7e1dbe`, under `pstack/skills/`. Native checker results and real-code replay replace the statechart runtime requirement. Automated statechart reporting was intentionally not adopted. The existing Tests reviewer reads formal artifacts and their code correspondence without a new reviewer or run.
- When implementation does not exist, ticket preparation fixes the rule, tool, paths and CHECK. Work a ticket generates the check only after writing and committing the real code. Models in Owns can change with code; settled UI acceptance remains read-only.
- Eighteen root branch documents across six skills moved to their own references/. Basenames, callers, relative links, checker consumers and upstream-map destination paths moved together. Historical review records, fixed ticket fixtures and upstream source paths retain their original evidence.

## Bounded behavior proof

Two independent agents read only the candidate entry and the pointers reached from it. The jobs were made up, not real product deliveries. Writes and commands were followed on paper without tracker changes or product runs.

The design-only walk followed a new web product through preparation-record opening, standalone environment preparation, two UI candidates, owner selection, same-winner iteration, explicit pause and resumption, feature description and design return. It stopped conditionally on absent product scope and owner answers rather than inventing either. It read 35 candidate files, 26,949 whitespace-separated words, including applicable principles and complete referenced documents.

That walk found two conflicts: UI step 2 still required an existing product mount despite the standalone branch, and opening a preparation record prohibited this session from writing prototype code. The text now gives standalone launch its own completion condition and assigns preparation assets to the calling method while reserving implementation code for the Worker. The same agent reread only those changes and confirmed that both original conflicts were resolved.

The other agent followed a settled duplicate-save repair through Develop a change, actual-product acceptance, one independent ticket and Worker handoff. It selected neither a new prototype nor full product maintenance. Its second job followed an explicitly assigned deferred formal check through committed implementation, generation, integration, original criteria and the existing Tests reviewer. It found no routing failure in those paths. Missing actual tool, CHECK, repository and evidence were retained as hypothetical gaps. A new-design example pointer was made conditional so the repair entry need not read that example.

These walks establish readable routes for the exercised jobs. They do not prove a runnable frontend handoff, a formal property's truth, or model behavior across all tasks. No frontend product, formal toolchain, installation or release was run for this change.

## Mechanical validation

The migration inventory confirms eighteen destinations, no old forwarding files, and no non-entry Markdown files remaining beside SKILL.md in the live skill directories. Existing shared checks and selected test suites supply the source/tooling results, reported separately from behavior proof in the pull request.

`scripts/check` passed all twelve selected default steps against origin/dev, including syntax, shared checks, lib, interfaces, diagram-design, dispatch, setup-mmw, retro, register-problem, writing-for-agents and worktree-audit. The complete default check took 208 seconds. No all-tier product e2e or Windows packaging was selected. `git diff --check` passed. The Artifact passed its existing single-file/accessibility and SVG geometry checks; browser navigation to the local file was blocked by the browser tool, so no rendered-page inspection is claimed.
