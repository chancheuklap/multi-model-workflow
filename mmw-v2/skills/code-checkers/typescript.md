# TypeScript / JavaScript

`oxlint` lints; `oxlint-tsgolint` gives it types, and with them the type check itself. No separate `tsc --noEmit`, and no `typescript-eslint` — TypeScript 7 ships no stable programmatic API, so it cannot run there at all.

```bash
pnpm add -D oxlint oxlint-tsgolint
```

```json
"devDependencies": {
  "oxlint": "^1.80.0",
  "oxlint-tsgolint": "7.0.2001"
}
```

**Pin `oxlint-tsgolint` exactly.** Its version encodes the TypeScript it embeds — `7.0.2001` is patch 1 for TypeScript `7.0.2` — so a range drifts off the compiler the repo builds with. `oxlint` itself only gains diagnostics, so a range is fine.

Requires TypeScript 7 or newer. A `tsconfig.json` still carrying `baseUrl`, or anything removed in TS 7, must migrate first.

## Configuration

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "extends": ["../.oxlintrc.base.json"],
  "options": { "typeAware": true }
}
```

**`options.typeAware` is read only from the root config** — the file oxlint starts from, not a file it extends. In a repo where each package has its own `.oxlintrc.json` extending a shared base, the flag goes in each package's file; put it in the shared base and it is silently ignored.

Type-aware rules worth having on, all undecidable without types: `typescript/no-floating-promises`, `typescript/no-misused-promises`, `typescript/await-thenable`.

## Commands

```bash
pnpm exec oxlint --type-aware               # lint, type-aware rules included
pnpm exec oxlint --type-aware --type-check  # the above plus TypeScript's own diagnostics
pnpm exec oxlint --type-aware --fix
```

## Probe before believing a clean run

Type-aware linting's common failure is silent: tsgolint is not found, or `typeAware` sat in an extended config, and oxlint runs the non-type rules and exits zero. Nothing says the type-aware pass never happened.

```ts
async function work(): Promise<void> { await Promise.resolve() }
export function trigger(): void {
  work()   // no await, no .catch()
}
```

`no-floating-promises` must fire on this. If it does not, the type-aware pass is not running, and every type-aware rule in the config is decoration.

## Two packages sharing one toolchain

Two apps built from one repo — two Electron shells, an app and its admin console — need identical build and checker versions: the same code has to pass the same checks, and a build-tool version that differs between them produces artifacts that differ in ways nobody sees until release day.

Merging them into one workspace does fix it, and costs more than it looks: bootstrap scripts that expect a lockfile per package, release scripts that run `pnpm install` inside each package, and a packaging step that can only be verified by actually building on the target OS.

**Assert it in a test instead.** Compare the two `package.json` files' `dependencies` and `devDependencies` — keys and version ranges, verbatim — and fail with the specific difference. It is a few lines, it runs with the existing suite, and it turns a release-day surprise into a red test the moment the two drift.
