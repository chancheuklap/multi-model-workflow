# Ambiguity scan

Read only the spec and the drafted tickets. Run one pass. Write nothing on the tracker.

It is very likely that important decisions are missing or ambiguous, even if the spec looks good on the surface. Be skeptical, adversarial, and actively try to find gaps.

## Scan

Load the spec and the drafted tickets. For each category below, mark status: Clear / Partial / Missing. Keep an internal map for prioritization (do not output it).

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

For each category with Partial or Missing status, add a candidate question opportunity unless the answer would not change what a ticket delivers or what its criteria check.

## Questions

Generate a prioritized queue of candidate questions. Maximum of 5 questions. Apply these constraints:

- Only include questions whose answers change what a ticket delivers or what its criteria check.
- Exclude questions already answered, trivial stylistic preferences, or plan-level execution details (unless blocking correctness).
- Prefer questions that reduce downstream rework risk or prevent misaligned acceptance tests.
- If more than 5 categories remain unresolved, select the top 5 by Impact × Uncertainty.

Each question carries:

- One full interrogative that ends with `?`. The question text before the `?` must make sense on its own. Never use a topic label, section heading, or requirement id as the question itself.
- Use everyday wording; introduce jargon only if defined in the same sentence. A reader who has not read this file must be able to answer from the Question line alone.
- One plain-language "Why it matters" sentence (the stake for what a ticket delivers or what its criteria check).
- The spec sentence it cites, quoted.
- 2–5 distinct, mutually exclusive options.
- `Recommended: Option X, because <1–2 sentences of reasoning>`, chosen from best practices for the project type, common patterns in similar implementations, risk reduction, and alignment with explicit project goals or constraints visible in the spec. Present the recommendation first.

Present every question in this pass. This is not a sequential loop.

If no valid questions exist, return exactly:

No critical ambiguities detected worth formal clarification.
