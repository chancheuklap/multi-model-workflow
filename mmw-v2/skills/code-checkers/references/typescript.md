# TypeScript / JavaScript

`oxlint` lints; `oxlint-tsgolint` gives it types, and with them the type check itself. No separate `tsc --noEmit`, and no `typescript-eslint`.

```bash
pnpm add -D oxlint oxlint-tsgolint
```

```json
"devDependencies": {
  "oxlint": "^<current>",
  "oxlint-tsgolint": "<matching>"
}
```

`<current>` is the release `pnpm view oxlint version` prints. `<matching>` is the newest release `pnpm view oxlint-tsgolint versions` lists; pin it exactly (below).

**Pin `oxlint-tsgolint` exactly.** Its version encodes the TypeScript it embeds — `7.0.2001` is patch 1 for TypeScript `7.0.2` — so a range changes the TypeScript engine the check runs under between installs. `oxlint` itself only gains diagnostics, so a range is fine.

`oxlint-tsgolint` checks with the TypeScript 7 engine it embeds, so the repository's `tsconfig.json` must be valid under TS 7 (no `baseUrl`, nothing else TS 7 removed). If it is not, stop and report: that migration is its own task.

## Configuration

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "extends": ["../.oxlintrc.base.json"],
  "options": { "typeAware": true }
}
```

**`options.typeAware` is read only from the root config** — the file oxlint starts from, not a file it extends. In a repository where each package has its own `.oxlintrc.json` extending a shared base, the flag goes in each package's file; put it in the shared base and it is silently ignored.

Type-aware rules worth having on, all undecidable without types: `typescript/no-floating-promises`, `typescript/no-misused-promises`, `typescript/await-thenable`.

## Commands

```bash
pnpm exec oxlint --type-aware               # lint, type-aware rules included
pnpm exec oxlint --type-aware --type-check  # the above plus TypeScript's own diagnostics
pnpm exec oxlint --type-aware --fix
```

## Probe before believing a clean run

```ts
async function work(): Promise<void> { await Promise.resolve() }
export function trigger(): void {
  work()   // no await, no .catch()
}
```

`no-floating-promises` must fire on this. If it does not, the type-aware pass is not running, and every type-aware rule in the config is decoration.
