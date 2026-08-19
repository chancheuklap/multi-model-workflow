---
name: exe-release
description: Build an official install package from the code on the current branch. Use when the user asks to ship, to package, or to build an installer, or when the work touched a product that has a release config.
---

# Release

Ship an install package for every product this change touched, far enough that the user can install it.

**Ship what is on the current branch now.** Whether the code is reviewed, whether it is finished, whether it is a good idea — that is the user's call, already made when they asked. Do not re-judge it here.

## The engine

`scripts/release-flow.sh`, next to this file. Resolve its absolute path once. Every command below is written `<engine> <subcommand>` and means:

```bash
bash /absolute/path/to/scripts/release-flow.sh <subcommand>
```

The engine is the deterministic layer: the state machine, the three failure grades, path guards, same-cause circuit breakers, and budget breakers all live there. **You are the judgment layer:** name the products for this run, read the state and run the action it names, and diagnose the one class of pause the engine cannot judge. Grades, guards, and the executor stay with the engine — [driving.md](driving.md) holds that line at the point where it bites.

## 1. Preconditions

Both must hold. If one fails, stop and name it.

| Check | How |
| --- | --- |
| Working tree is clean | `git status --porcelain` is empty. The engine refuses to mix self-heal commits with uncommitted work |
| This repo ships something | At least one release config exists (next step) |

**A repo with no release config at all does not ship.** Report that, and the current branch HEAD. Hand back to the user. (One product missing a config in a repo that does ship is a different case — step 2.)

## 2. Name the products for this run

The repo registers release configs. One product per file. The filename ends with `.release-adapter.json`. List them:

```bash
grep -rl '"product"' --include='*.release-adapter.json' .
```

Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from — the repo default branch when you have nothing better). Match each config's `build_target.desktop_dir` and `asset_roots`. A hit means ship that product.

If you cannot tell, ask the user. Do not omit a product.

**A product this change touched but no config names does not ship yet — write it a key.** Writing
one key is the whole job of adding a product, and it is JSON: [key.md](key.md) has the three steps,
including what the product repo must already have before a key is worth writing. Do not write
packaging scripts in the product repo to work around a key that cannot say something; add the
field or the capability, where every product gets it.

Show this list once and continue. Do not wait for a reply:

```
| product | release config | why this run includes it |
```

## 3. One product per loop, driven by driving.md

For each product from step 2, in order:

```bash
<engine> init --manifest <absolute path of that config>
```

Then read [driving.md](driving.md) in full and drive until the package is ready. **That file is the driving contract.** This skill does not retell it.

`<engine> close` one product before starting the next. Do not run two at once — the repo has one state file.

## 4. Same-commit check

Do this after every product has shipped. A stage, a dispatch, or a self-heal can create new commits, so an earlier package may not match the final code.

```bash
git rev-parse HEAD
```

Delivery records live under `<release dir>/delivered/`. The release dir is `paths.release` from `.mmw.json` when the repo has that file, otherwise `.release`. Records live at the **main checkout root**, not in this task worktree.

That directory holds one record per product. A later run overwrites the earlier one. **Read only the products on the step 2 list.** Their `source_commit` values must all equal current HEAD.

A mismatch: ship that product again (back to step 3, only the mismatches). Then check again — a reship can create new commits.

**Do not give the user a mixed-commit set of packages.**

## 5. User install test

Package paths come from the engine's `DELIVERED` lines. On success it gathers packages at the delivery root, one path per line.

On gather failure the engine prints WARN with the path left in the build directory. Report that path, and say the package did not reach the delivery root. If neither line exists, say you have no path. Do not invent one from a directory convention.

Give the user: which products shipped, where each package is, which commit this set is.

**Stop and wait for the user to install and try it.** The machine cannot judge install or use. Pass: report the packages, the commit, and the test result, then hand back to the user. Fail: take the symptoms and repro steps to `/implement`, then ship again.
