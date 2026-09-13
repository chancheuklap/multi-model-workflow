# Ambiguity scan

Reached from the door table of [`SKILL.md`](../SKILL.md) when this run is the scan: the prompt names this skill, a spec, and a file of drafted tickets, and asks you to scan them for ambiguities.

It is very likely that important decisions are missing or ambiguous, even if the spec looks good on the surface. Be skeptical, adversarial, and actively try to find gaps.

Read only the spec and the drafted tickets. Do not read the code. Run one pass. Write nothing on the tracker.

## Scan

Load the spec and the drafted tickets. Perform a structured ambiguity and coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output the raw map).

Functional Scope & Behavior:
- Core user goals & success criteria
- Explicit out-of-scope declarations
- User roles / personas differentiation

Domain & Data Model:
- Entities, attributes, relationships
- Identity & uniqueness rules
- Lifecycle/state transitions
- Data volume / scale assumptions

Interaction & UX Flow:
- Critical user journeys / sequences
- Error/empty/loading states
- Accessibility or localization notes

Non-Functional Quality Attributes:
- Performance (latency, throughput targets)
- Scalability (horizontal/vertical, limits)
- Reliability & availability (uptime, recovery expectations)
- Observability (logging, metrics, tracing signals)
- Security & privacy (authN/Z, data protection, threat assumptions)
- Compliance / regulatory constraints (if any)

Integration & External Dependencies:
- External services/APIs and failure modes
- Data import/export formats
- Protocol/versioning assumptions

Edge Cases & Failure Handling:
- Negative scenarios
- Rate limiting / throttling
- Conflict resolution (e.g., concurrent edits)

Constraints & Tradeoffs:
- Technical constraints (language, storage, hosting)
- Explicit tradeoffs or rejected alternatives

Terminology & Consistency:
- Canonical glossary terms
- Avoided synonyms / deprecated terms

Completion Signals:
- Acceptance criteria testability
- Measurable Definition of Done style indicators

Misc / Placeholders:
- TODO markers / unresolved decisions
- Ambiguous adjectives ("robust", "intuitive") lacking quantification

For each category with Partial or Missing status, add a candidate question opportunity unless:
- Clarification would not change what a ticket delivers or what its criteria check
- Information is better deferred to planning (note internally)

## Questions

Generate a prioritized queue of candidate questions. Maximum of 5 total questions across the whole session. Apply these constraints:

- Only include questions whose answers change what a ticket delivers or what its criteria check.
- Exclude questions already answered, trivial stylistic preferences, or plan-level execution details (unless blocking correctness).
- Favor clarifications that reduce downstream rework risk or prevent misaligned acceptance tests.
- If more than 5 categories remain unresolved, select the top 5 by Impact × Uncertainty.

Each question carries:

- One full interrogative that ends with `?`. The question text before the `?` must make sense on its own. Never use a topic label, section heading, or requirement id as the question itself.
- One plain-language "Why it matters" sentence (the stake for what a ticket delivers or what its criteria check).
- The spec sentence it cites, quoted.
- 2–5 distinct, mutually exclusive options.
- `Recommended: Option X — <1–2 sentences of reasoning>`

Present every question in this pass. This is not a sequential loop.

If no valid questions exist, return exactly:

No critical ambiguities detected worth formal clarification.
