---
name: exe-release
description: Build an official install package from the code on the current branch. Use when the user asks to ship, to package, or to build an installer.
---

# Release

Ship an install package for every product this change touched, far enough that the user can install it.

**Ship what is on the current branch now.** Whether the code is reviewed, whether it is finished, whether it is a good idea — that is the user's call, already made when they asked.

## Resolve `<release>` and `<scripts>` once

`<release>` in every command below is `bash <absolute path of scripts/release-flow.sh>` — the release engine, next to this file — so `<release> where` runs `bash /…/scripts/release-flow.sh where`. `<scripts>` is the `scripts/` directory the release engine lives in, and [key.md](references/key.md) runs two more executables out of it. Resolve both from this file's own location, once: the path differs by machine and by host.

## 1. Preconditions

A **release manifest** is the JSON file that declares how one product is packaged: one product per file, its filename ending in `.release-adapter.json`.

Both must hold. If one fails, stop and tell the user which, with the current branch HEAD.

| Check | How |
| --- | --- |
| Working tree is clean | `git status --porcelain` is empty. The release engine refuses to mix self-heal commits with uncommitted work |
| This repository ships something | At least one release manifest exists (next step) |

## 2. Name the products for this run

List the release manifests:

```bash
git ls-files '*.release-adapter.json'
```

Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from — the repository default branch when you have nothing better). Match them against the paths each release manifest names — its shell directory, its compile entrypoints and packaged data, its `asset_roots`. A hit means ship that product.

If you cannot tell, include the product and write the reason in the table below, then continue. A product whose release manifest names no path that could ever match is a release manifest to fix, not a product to skip.

**A product this change touched but no release manifest names does not ship yet.** Bringing it in is one
JSON file plus whatever the repository still lacks: [new-product.md](references/new-product.md) starts there and
hands off to [key.md](references/key.md) for the fields.

Show this list once and continue. Do not wait for a reply:

```
| product | release manifest | why this run includes it |
```

## 3. One product per loop, driven by driving.md

For each product from step 2, in order:

```bash
<release> init --manifest <absolute path of that release manifest>
```

Then read [driving.md](references/driving.md) in full and drive until the package is ready.

`<release> close` one product before starting the next. Do not run two at once — the repository has one state file.

Done when `<release> exit-check` printed `DONE` and `<release> close` ran for every product on the step 2 list.

## 4. Same-commit check

Do this after every product has shipped. A stage, a dispatch, or a self-heal can create new commits, so an earlier package may not match the final code.

```bash
git rev-parse HEAD
```

Delivery records live under `.release/delivered/`, at the **main checkout root**, not in this task worktree.

That directory holds one record per product. A later run overwrites the earlier one. **Read only the products on the step 2 list.** Their `source_commit` values must all equal current HEAD.

A mismatch: ship that product again (back to step 3, only the mismatches). Then check again — a reship can create new commits.

Done when every listed product's `source_commit` equals `git rev-parse HEAD`.

## 5. User install test

Give the user: which products shipped, where each package is, which commit this set is.

**Stop and wait for the user to install and try it.** The machine cannot judge install or use. Pass: stop and report the packages, the commit, and the test result to the user. Fail: report the symptoms to the user and wait for their decision.

Done when the user has reported the install test result and you have acted on it as above.
