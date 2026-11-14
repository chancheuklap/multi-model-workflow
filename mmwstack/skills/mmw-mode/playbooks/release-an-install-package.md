### Release an install package

**You own one release: an install package for every product this change touched, built from the code on the current branch, all from one commit, and in the operator's hands far enough that they can install it.** Run it when the operator asks for an installer, an exe or an install package. A bare "ship" with a PR stack in play is [Shipping](shipping.md), which lands PRs and builds no package. **Ship what is on the current branch now.** Whether the code is reviewed, whether it is finished, whether it is a good idea is the operator's call, already made when they asked.

The [exe-release](../../exe-release/SKILL.md) skill holds the release engine, the release manifest format and the scripts. Every `scripts/` path below is in that skill's directory, not the mode's. Call it by its absolute path and keep the product repository as the working directory, because the release engine reads that repository, its commit and its `.release/` state.

1. **Check the preconditions.** A **release manifest** is the JSON file that declares how one product is packaged: one product per file, its filename ending in `.release-adapter.json`. The build machine receives `git archive HEAD` and nothing else. Uncommitted work does not ship, so a dirty tree means the operator would test a package that differs from the code in front of them: stop and say which files are uncommitted. `bash scripts/release-flow.sh init` refuses to start on a dirty tree for the same reason. Whether this repository ships anything is answered by the next step.
   Done when the tree is clean, or the operator has been told which files are uncommitted.
2. **Name the products for this run.** List the release manifests:

   ```bash
   git ls-files '*.release-adapter.json'
   ```

   Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from, the repository default branch when you have nothing better). Match them against the paths each release manifest names: its shell directory, its compile entrypoints and packaged data, its `asset_roots`. A hit means ship that product.

   The paths are evidence, not the rule. What decides is whether the change reaches what this product's customer installs: a package the product lists in `python_backend.include_packages` that lives outside its own directory, a dependency lock, a hook script, or the release manifest itself all change the package. Leaving out a product the change reached ships it stale; including one it did not costs one build.

   If you cannot tell, include the product and write the reason in the table below, then continue. A product whose release manifest names no path that could ever match is a release manifest to fix, not a product to skip.

   **A product this change touched but no release manifest names does not ship yet.** Bringing it in is one JSON file plus whatever the repository still lacks: [new-product.md](../../exe-release/references/new-product.md) starts there and hands off to [key.md](../../exe-release/references/key.md) for the fields. Once its release manifest is committed, the product is on this list.

   Show this list once and continue. Do not wait for a reply:

   ```
   | product | release manifest | why this run includes it |
   ```

   Done when the list is shown.
3. **Ship one product per loop.** For each product from step 2, in order:

   ```bash
   bash scripts/release-flow.sh init --manifest <absolute path of that release manifest>
   ```

   Then read [driving.md](../../exe-release/references/driving.md) in full and drive until the package is ready. `bash scripts/release-flow.sh close` one product before starting the next.
   Done when `bash scripts/release-flow.sh close` succeeded for every product on the step 2 list.
4. **Check the set came from one commit.** A set whose packages were built from different inputs is two versions of the product: whoever installs more than one gets a combination nobody built or tested together. A package whose inputs have not changed since it shipped is already part of this set, and building it again only spends a version number and a round of install testing.

   After every product on the step 2 list has shipped, run:

   ```bash
   bash scripts/release-flow.sh same-commit [--scope <package scope file>] <product> [<product> ...]
   ```

   with exactly the products on that list, and with `--scope` when the repository has a release package scope file, the file that lists which paths each product is built from. It prints `OK <product>` or `MISMATCH <product> <commit>` for each. With `--scope`, a product shipped from an older commit is `OK` when no path changed since that commit belongs to that product or to every product, and the line says so; a changed path the file classifies nowhere is a `MISMATCH`. Reship each `MISMATCH` (back to step 3), then run it again, because a reship can itself move HEAD.
   Done when it prints `OK` for every product on the step 2 list.
5. **Hand the operator the install test.** Give the operator: which products shipped, where each package is, which commit this set is, and each commit this run added to the branch to get a build through. **Stop and wait for the operator to install and try it.** The machine cannot judge install or use. Pass: stop and report the packages, the commit, and the test result to the operator. Fail: report the symptoms to the operator and wait for their decision.
   Done when the operator has reported the install test result and you have acted on it as above.

**Reply:** the step 2 table; for each product, its package path from the `DELIVERED` lines (or that there is none) and any pause the operator must answer, with its receipt as-is; the commit the set came from and the `same-commit` result; each commit this run added to the branch; and, once the operator has tried it, the install test result and what you did on it.
