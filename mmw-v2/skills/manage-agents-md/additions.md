# Additions

Branch: **incremental**. You have `scope.md` and `survey-list.md` built from the change sets. For each `AGENTS.md` in scope you now decide what the code changes made false and what they added, and edit the file. Every edit has code evidence in the survey list; the maintainer-owned lines named in [incremental.md](incremental.md) stay as they are, and a doubt about one of them goes to the report.

## Steps

For each file in `scope.md`:

1. Read the file. For each line, look for a survey entry that contradicts it. A contradicted line is fixed when the entry gives the new fact, removed when it gives none. Write the old line, the new line, and the evidence into `changes.md` in the scratch directory.
2. For each survey entry with no line covering it, decide whether it belongs in the file by the categories below, and add it where its type goes: command to `## Commands`, reference to `## References`, convention or pitfall to `## Conventions and pitfalls` when it has no `when` line and to the `<important if>` block whose condition is its `when` value otherwise (open the block if none exists).
3. When no entry contradicts or extends the file, record "no change needed" for it in `changes.md`.

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

The headings in these examples are the reference's own; in this skill's files an addition lands in the section step 2 names for its type.

## Draft Additions

**Keep it concise** - one line per concept. AGENTS.md is part of the prompt, so brevity matters.

Format: `<command or pattern>` - `<brief description>`

Avoid:
- Verbose explanations
- Obvious information
- One-off fixes unlikely to recur

## Update Principles

When updating any AGENTS.md:

1. **Be specific**: Use actual file paths, real commands from this project
2. **Be current**: Verify info against the actual codebase
3. **Be brief**: One line per concept when possible
4. **Be useful**: Would this help a new session understand the project?

## Validation Checklist

Before finalizing an update, verify:

- [ ] Each addition is project-specific
- [ ] No generic advice or obvious info
- [ ] Commands are tested and work
- [ ] File paths are accurate
- [ ] Would a new session find this helpful?
- [ ] Is this the most concise way to express the info?

## Where an addition goes

A fact whose place is a directory goes into that directory's `AGENTS.md`; when the directory has no pair yet, create both files on the nested template in [write.md](write.md), with the scope sentence left as the directory group's scope finding and listed under **Pending maintainer decisions** for confirmation. A fact whose place is `root` goes into the root file. A directory whose last rule just disappeared is an **empty pair**: it keeps both files on this branch; the report lists it under **Pending maintainer decisions** and the maintainer removes it.

Done when every file in `scope.md` has an entry in `changes.md` — edits with evidence, or "no change needed".

Next: [prune.md](prune.md).
