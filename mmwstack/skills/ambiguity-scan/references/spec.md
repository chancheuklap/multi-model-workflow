# Spec stage review

You are reviewing a draft spec produced by [to-spec](../../to-spec/SKILL.md) before publication or handoff. Follow [Reviewer contract](../SKILL.md#reviewer-contract), then check the draft against its upstream sources across the three areas below.

## 1. Upstream inheritance and drift

- **Original problem and evidence.** `Problem Statement` preserves the user's original report and evidence without silently narrowing or reframing the problem.
- **Settled decisions.** Every settled decision from the discussion, Wayfinder `Decisions so far` and decision ticket `Result`s, linked approved plan, and `approved prototype` appears intact without silent alteration.
- **Scope exclusions.** Explicit `Out of Scope` items from the discussion or Wayfinder map stay excluded and do not reappear inside `User Stories` or `Implementation Decisions`.
- **Decision ownership.** Any open product or operator choice left unsettled by the sources stays flagged as open instead of being presented as settled. Engineering choices the author made while drafting carry the marker `"this spec's decision"`.

## 2. Spec process and contract

- **Required sections and perspective.** The draft includes `Problem Statement`, `Solution`, `User Stories`, `Implementation Decisions`, `Testing Decisions`, and `Out of Scope` (plus `Further Notes` when needed). `Problem Statement` and `Solution` describe the problem and solution from the user's perspective.
- **User stories and expected results.** `User Stories` cover every agreed outcome in `As an <actor>, I want <feature>, so that <benefit>` form. Whenever a story states a user-observable outcome, that `expected result` stands as its own standalone sentence that a plan, execution ticket, or verification script can copy unchanged.
- **Decision-level implementation notes.** `Implementation Decisions` name modules, interfaces, schemas, API contracts, and architectural decisions without volatile file paths or raw code snippets. An inline snippet is valid only when trimmed to decision-rich parts (such as a state machine, schema, or type shape) and explicitly noted as coming from a prototype.
- **Observable testing decisions.** `Testing Decisions` specify conditions, expected results, tested modules, prior art, and any `intended change to a promise` on `covered code` rather than generic test placeholders.
- **Verification boundary.** The spec does not claim to create `verify-<app>` or a `formal verification skill` (`formal-verify-<area>` or a differently named project formal verification skill), and does not claim to edit `features/` maps, models, or formal verification harnesses.

## 3. Document clarity

- **Anchored names and glossary.** Each concept uses one consistent name from the project glossary or sources, with no unanchored back-references ("the above option", "this flow").
- **Concrete, unslopped prose.** Observable requirements use concrete terms instead of vague adjectives ("fast", "robust", "properly", "seamlessly"). Sentences stay active, single-thought, and free of em dashes, mid-sentence colons, and AI filler.
