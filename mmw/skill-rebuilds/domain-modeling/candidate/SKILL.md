---
name: mmw-domain-modeling
description: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology, a ubiquitous language, or a bounded context; record an architectural decision; or when another skill needs to maintain the domain model.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* domain docs for vocabulary is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

- The user wants to grill a whole plan, decision, or unformed idea: invoke `/mmw-grilling`. It applies this skill in the same conversation.
- The user wants to define or correct terms, ubiquitous language, bounded contexts, relationships between bounded contexts, or an ADR: continue here.
- Another skill invoked this one to maintain the domain model: continue here, then return.

## File structure

`mmw domain path` prints the current shape, the path to read, and the read instruction. Follow that output. `mmw domain dirs` prints the write paths for the single-context doc, the Context Map, the leaf directory, and ADRs.

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

If a Context Map exists, the repo has multiple contexts. The map points to where each leaf lives:

```
/
├── CONTEXT-MAP.md
├── docs/adr/                    ← system-wide decisions
├── docs/context/
│   ├── ordering.md
│   └── billing.md
└── src/
```

Create files lazily — only when you have something to write. If the shape from `mmw domain path` is `none`, keep going. Do not announce a missing glossary. Create the first domain doc when the first term that must live in the glossary is resolved. Create the ADR directory when the first ADR is needed.

Before the first write of a domain doc or ADR:

[[mmw-require-task-branch]]

When creating the first domain doc, how many bounded contexts the project has decides the shape:

- One: write the first term into the single-context path from `mmw domain dirs`.
- More than one: `mmw domain map-init`. After it creates the Context Map, add the first leaf under the context directory and register its path, ownership, and any relationship already confirmed. Format: [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).
- Still unclear: ask, then create.

After creating or changing a Context Map or leaf, run `mmw domain check`. The write is done when that command exits 0. If it exits non-zero, fix from its output and run it again.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in the owning domain doc, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update the glossary inline

When a term is resolved, update the owning domain doc right there. Don't batch these up — capture them as they happen. A single-context repo updates `CONTEXT.md`. A multi-context repo updates the leaf that owns the term. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

A shared term is defined in one leaf. Every other leaf points at that definition with an authoritative reference.

The glossary should be totally devoid of implementation details. Do not treat it as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

If another skill invoked this one, return the terms, bounded contexts, relationships, and ADRs you updated. If the user invoked it, report the same.
