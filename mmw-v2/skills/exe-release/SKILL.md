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

The build machine receives `git archive HEAD` and nothing else. Uncommitted work does not ship, so a dirty tree means the user would test a package that differs from the code in front of them: stop and say which files are uncommitted. `<release> init` refuses to start on a dirty tree for the same reason. Whether this repository ships anything is answered by the next step.

## 2. Name the products for this run

List the release manifests:

```bash
git ls-files '*.release-adapter.json'
```

Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from — the repository default branch when you have nothing better). Match them against the paths each release manifest names — its shell directory, its compile entrypoints and packaged data, its `asset_roots`. A hit means ship that product.

The paths are evidence, not the rule. What decides is whether the change reaches what this product's customer installs: a package the product lists in `python_backend.include_packages` that lives outside its own directory, a dependency lock, a hook script, or the release manifest itself all change the package. Leaving out a product the change reached ships it stale; including one it did not costs one build.

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

`<release> close` one product before starting the next.

Done when `<release> close` succeeded for every product on the step 2 list.

## 4. Same-commit check

A set whose packages come from different commits is two versions of the product: whoever installs more than one gets a combination nobody built or tested together.

After every product on the step 2 list has shipped, run:

```bash
<release> same-commit <product> [<product> ...]
```

with exactly the products on that list. It prints `OK <product>` or `MISMATCH <product> <commit>` for each. Reship each `MISMATCH` (back to step 3), then run it again — a reship can itself move HEAD.

Done when it prints `OK` for every product on the step 2 list.

## 5. User install test

Give the user: which products shipped, where each package is, which commit this set is.

**Stop and wait for the user to install and try it.** The machine cannot judge install or use. Pass: stop and report the packages, the commit, and the test result to the user. Fail: report the symptoms to the user and wait for their decision.

Done when the user has reported the install test result and you have acted on it as above.
