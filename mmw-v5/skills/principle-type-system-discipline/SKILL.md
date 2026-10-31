---
name: principle-type-system-discipline
description: Use when designing or reviewing typed data, functions, or interfaces. Make invalid states and mismatched domain values unrepresentable, derive types from authoritative schemas, and parse external data at boundaries.
---

# Type System Discipline

Make the compiler reject impossible states, mismatched primitives, and unhandled variants. Prefer defining errors and special cases out of existence over proliferating handlers. For TypeScript syntax, see the **`typescript-best-practices`** skill.

- **Brand semantic primitives.** `UserId` and `OrderId` are strings underneath but should not be interchangeable. Give each its own type, such as a branded intersection in TypeScript or a newtype elsewhere. Validate once at creation, trust the type downstream. If two arguments share a primitive type but mean different things, brand them.
- **External data is untyped until parsed.** Apply **principle-boundary-discipline** to establish the typed model before trusting it internally.
- **Derive types from authoritative schemas.** When a protocol buffer, OpenAPI spec, GraphQL schema, database migration, design-token file, or another file owns a shape, derive from it instead of hand-rolling a parallel type. See **principle-encode-lessons-in-structure**.

**In a diff:**

- An input the type admits and the code does not handle (empty, nil or undefined, a boundary value): narrow the type so it cannot arrive, or handle it.
- Unnecessary optionality, `unknown`, `any`, or cast-heavy code where a clearer type boundary could exist, or a loosely shaped ad-hoc object: write the typed model.
- Primitive Obsession, a primitive or string standing for a domain concept: give the concept its own small type.
- An invariant the change relies on that no type holds and no assertion checks, so a regression would pass unseen: put it in the type, or assert it at the boundary.
- A suppression (`eslint-disable`, `@ts-ignore`, `@ts-expect-error`) of a rule that catches real bugs: remove it and fix what it hid.
