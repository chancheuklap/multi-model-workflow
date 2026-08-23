# Additions

On the incremental branch you decide, from the change sets and the scoped survey, what each `AGENTS.md` has lost and gained. Two kinds of edit: a line the changes made false (fix it or remove it, with the evidence), and a fact the changes introduced that belongs in the file (add it).

Only lines with code evidence are yours. The identity lines, the scope sentence, and any convention without code evidence stay as they are; a doubt about one of them goes to the report's **Pending maintainer decisions**.

## What TO Add

### 1. Commands/Workflows Discovered

```markdown
## Build

`npm run build:prod` - Full production build with optimization
`npm run build:dev` - Fast dev build (no minification)
```

Why: Saves future sessions from discovering these again.

### 2. Gotchas and Non-Obvious Patterns

```markdown
## Gotchas

- Tests must run sequentially (`--runInBand`) due to shared DB state
- `yarn.lock` is authoritative; delete `node_modules` if deps mismatch
```

Why: Prevents repeating debugging sessions.

### 3. Package Relationships

```markdown
## Dependencies

The `auth` module depends on `crypto` being initialized first.
Import order matters in `src/bootstrap.ts`.
```

Why: Architecture knowledge that isn't obvious from code.

### 4. Testing Approaches That Worked

```markdown
## Testing

For API endpoints: Use `supertest` with the test helper in `tests/setup.ts`
Mocking: Factory functions in `tests/factories/` (not inline mocks)
```

Why: Establishes patterns that work.

### 5. Configuration Quirks

```markdown
## Config

- `NEXT_PUBLIC_*` vars must be set at build time, not runtime
- Redis connection requires `?family=0` suffix for IPv6
```

Why: Environment-specific knowledge.

The section headings in these examples are the reference's; in this skill's format an addition lands in the section [write.md](write.md) names for its type (command, convention and pitfall, reference, or a task-scoped block).

## Draft Additions

**Keep it concise** - one line per concept. AGENTS.md is part of the prompt, so brevity matters.

Format: `<command or pattern>` - `<brief description>`

Avoid:
- Verbose explanations
- Obvious information
- One-off fixes unlikely to recur

## Where an addition goes

A fact that holds only under one directory goes into that directory's `AGENTS.md`; create the pair if the directory has none. A fact that holds everywhere goes into the root. A directory whose only rule just disappeared loses its pair: delete both files and say so in the report.

Done when every change set has produced either edits with evidence or an explicit "no change needed", and nothing maintainer-owned was touched.
