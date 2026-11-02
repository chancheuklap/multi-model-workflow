---
name: principle-type-system-discipline
description: Use when designing or reviewing typed data, functions, or interfaces. Make invalid states and mismatched domain values unrepresentable, derive types from authoritative schemas, and parse external data at boundaries.
---

# Type System Discipline

Make the compiler reject impossible states, mismatched primitives, and unhandled variants. Prefer defining errors and special cases out of existence over proliferating handlers. For TypeScript syntax, see the **`typescript-best-practices`** skill.

- **Brand semantic primitives.** `UserId` and `OrderId` are strings underneath but should not be interchangeable. Give each its own type, such as a branded intersection in TypeScript or a newtype elsewhere. Validate once at creation, trust the type downstream. If two arguments share a primitive type but mean different things, brand them.
- **External data is untyped until parsed.** Apply **principle-boundary-discipline** to establish the typed model before trusting it internally.
- **Derive types from authoritative schemas.** When a protocol buffer, OpenAPI spec, GraphQL schema, database migration, design-token file, or another file owns a shape, derive from it instead of hand-rolling a parallel type. See **principle-encode-lessons-in-structure**.
