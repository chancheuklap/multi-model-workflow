---
name: mmw-release
description: Build official install packages for changes that passed final review. Use when the user asks to ship, or the work touched a product that has a release config.
---

# Release

Ship an install package for every product this change touched, far enough that the user can install it.

The engine is the deterministic layer: the state machine, the three failure grades, path guards, same-cause circuit breakers, and budget breakers all live in `mmw release`. **You are the judgment layer:** name the products for this run, read the state and run the action it names, and diagnose the one class of pause the engine cannot judge. You do not grade failures. You do not bypass guards. You do not build a second executor.

## 1. Preconditions

All four must hold. If one fails, stop and name it.

| Check | How |
| --- | --- |
| Final review ran; accepted findings are fixed and verified | Run `mmw artifact path review --sub final.md`. The file exists. When there were accepted findings, its header has `修复提交` |
| Current HEAD is that final-review commit | Run `mmw artifact path review --sub final.md`. Read the file. `终审提交` equals `git rev-parse HEAD` |
| Working tree is clean | `git status --porcelain` is empty. The engine refuses to mix self-heal commits with uncommitted work |
| This repo has a release config | At least one release config exists (next step) |

**No release config is not a failure.** Report that this task does not ship, the current branch HEAD, and the verification evidence. Hand back to the user to integrate.

## 2. Name the products for this run

The repo registers release configs. One product per file. The filename ends with `.release-adapter.json`. List them:

```bash
grep -rl '"product"' --include='*.release-adapter.json' .
```

Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from — the repo default branch, or the map branch when this task came from `$mmw:mmw-wayfinder`, recorded under `## 分支` in the map body). Match each config's `build_target.desktop_dir` and `asset_roots`. A hit means ship that product.

If you cannot tell, ask the user. Do not omit a product.

Show this list once and continue. Do not wait for a reply:

```
| product | release config | why this run includes it |
```

## 3. One product per loop, driven by driving.md

For each product from step 2, in order:

```bash
mmw release init --manifest <absolute path of that config>
```

Then read [driving.md](driving.md) in full and drive until the package is ready. **That file is the driving contract.** This skill does not retell it.

`mmw release close` one product before starting the next. Do not run two at once — the repo has one state file.

## 4. Same-commit check

Do this after every product has shipped. A stage, a dispatch, or a self-heal can create new commits, so an earlier package may not match the final code.

```bash
git rev-parse HEAD
```

The delivery-record working-directory root is `.mmw.json` `paths.release` in the current repo. Read that value, then the records under `delivered/` there. Records live at the **main checkout root**, not in this task worktree.

That directory holds one record per product. A later run overwrites the earlier one. **Read only the products on the step 2 list.** Their `source_commit` values must all equal current HEAD.

A mismatch: ship that product again (back to step 3, only the mismatches). Then check again — a reship can create new commits.

**Do not give the user a mixed-commit set of packages.**

## 5. User install test

Package paths come from the engine's `DELIVERED` lines. On success it gathers packages at the delivery root, one path per line.

On gather failure the engine prints WARN with the path left in the build directory. Report that path, and say the package did not reach the delivery root. If neither line exists, say you have no path. Do not invent one from a directory convention.

Give the user: which products shipped, where each package is, which commit this set is.

**Stop and wait for the user to install and try it.** The machine cannot judge install or use. Pass: report the packages, the commit, and the test result, then hand back to the user to integrate. Fail: take the symptoms and repro steps to `$mmw:mmw-implement`, then ship again. Do not start another review.
