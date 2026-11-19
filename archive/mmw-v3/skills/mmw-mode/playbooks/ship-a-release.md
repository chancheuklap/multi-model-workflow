### Ship a release

**You own one release: an install package for every product this change touched, built from the code on the current branch, all from one commit, and in the owner's hands far enough that they can install it.** The `exe-release` skill's `scripts/release-flow.sh` is the **release engine**: it owns each product's loop, and every `bash scripts/release-flow.sh` below is that script. What a release manifest is and how one is written is the `exe-release` skill. **Ship what is on the current branch now.** Whether the code is reviewed, whether it is finished, whether it is a good idea — that is the owner's call, already made when they asked. Distinct from Run a night and Run one ticket, which land code on the base branch and ship nothing.

1. **Check the preconditions.** The build machine receives `git archive HEAD` and nothing else. Uncommitted work does not ship, so a dirty tree means the owner would test a package that differs from the code in front of them: stop and say which files are uncommitted. `bash scripts/release-flow.sh init` refuses to start on a dirty tree for the same reason. Whether this repository ships anything is answered by the next step.
   Done when the tree is clean, or the owner has been told which files are uncommitted.
2. **Name the products for this run.** List the release manifests:

   ```bash
   git ls-files '*.release-adapter.json'
   ```

   Decide which to ship: take the paths this change touched (`git diff --name-only $(git merge-base HEAD <parent>)..HEAD`; `<parent>` is the branch this task branch was created from — the repository default branch when you have nothing better). Match them against the paths each release manifest names — its shell directory, its compile entrypoints and packaged data, its `asset_roots`. A hit means ship that product.

   The paths are evidence, not the rule. What decides is whether the change reaches what this product's customer installs: a package the product lists in `python_backend.include_packages` that lives outside its own directory, a dependency lock, a hook script, or the release manifest itself all change the package. Leaving out a product the change reached ships it stale; including one it did not costs one build.

   If you cannot tell, include the product and write the reason in the table below, then continue. A product whose release manifest names no path that could ever match is a release manifest to fix, not a product to skip.

   **A product this change touched but no release manifest names does not ship yet.** Bringing it in is one JSON file plus whatever the repository still lacks: the `exe-release` skill's `references/new-product.md` starts there and hands off to its `references/key.md` for the fields.

   Show this list once and continue. Do not wait for a reply (**principle-never-block-on-the-human**):

   ```
   | product | release manifest | why this run includes it |
   ```

   Done when the list is shown.
3. **Ship one product per loop.** For each product from step 2, in order:

   ```bash
   bash scripts/release-flow.sh init --manifest <absolute path of that release manifest>
   ```

   Then drive it as **Drive one product** below says, until the package is ready. `bash scripts/release-flow.sh close` one product before starting the next.
   Done when `bash scripts/release-flow.sh close` succeeded for every product on the step 2 list.
4. **Check the set came from one commit.** A set whose packages come from different commits is two versions of the product: whoever installs more than one gets a combination nobody built or tested together. After every product on the step 2 list has shipped, run:

   ```bash
   bash scripts/release-flow.sh same-commit <product> [<product> ...]
   ```

   with exactly the products on that list. It prints `OK <product>` or `MISMATCH <product> <commit>` for each. Reship each `MISMATCH` (back to step 3), then run it again — a reship can itself move HEAD.
   Done when it prints `OK` for every product on the step 2 list.
5. **Hand the owner the install test.** Give the owner: which products shipped, where each package is, which commit this set is. **Stop and wait for the owner to install and try it.** The machine cannot judge install or use (**principle-prove-it-works**). Pass: stop and report the packages, the commit, and the test result. Fail: report the symptoms and wait for their decision.
   Done when the owner has reported the install test result and you have acted on it as above.

**Drive one product.** By the time step 3 gets here, this product's loop is started, or a previous loop is still there to resume. **The release engine owns the loop.** Progress, next action, repair count, and success come from release engine state. Do not resume from session memory. Do not pick the next stage yourself. Do not keep a second log of what you already tried. You do not assign the tier (P0, P1 or P2) (**principle-progress-is-what-the-record-says**).

Each time, first run:

```bash
bash scripts/release-flow.sh where
```

Every state `where` prints, `PAUSED` and `CORRUPT:` included, exits 0: read the state from stdout, never from the exit code. Exit 1 is one `ERROR:` line on stderr naming the fact the release engine cannot get past.

| Output | Do | Stop and report to the owner? |
| --- | --- | --- |
| `STAGE:<name>` | `bash scripts/release-flow.sh stage run --stage <name>` — when the stage fails, it dispatches a fix and counts the round itself before returning | No |
| `PAUSED:needs-context` | See **Pause: missing context** below. This is not the end | Only after two failed attempts |
| `SUCCESS:all stages done` | `bash scripts/release-flow.sh close` | No |
| `PAUSED:needs-redirection` | Read `bash scripts/release-flow.sh receipt`. Give it to the owner as-is | Yes. Circuit breakers and spent budget must not continue on their own |
| `CORRUPT:` | Read `bash scripts/release-flow.sh receipt`. Do not run a stage. Do not `resume` | Yes |
| Any other output, or the command itself errors | Do not guess the state. Do not `init` again | Yes, with the raw output |

After a stage, ask `where` again until the table names a terminal state. **Do not stop to report to the owner after every `where`.**

**Pause: missing context.** `PAUSED:needs-context` means the release engine lacks information it cannot judge. **Resolve it yourself when you can.**

Goal: the release loop resumes with the cause gone, or the owner holds the one question only they can answer. The release receipt and the logs it names are the evidence; do not guess past them. Environment causes you act on; code or config causes you fix and commit (the build ships `git archive HEAD`); then `resume`.

**Same root cause twice, or the cause is billing, a contract, or a product decision the owner must make — stop and report to the owner.** Do not loop.

The paragraph above says commit because the remote build ships `git archive HEAD`. A change left in the worktree never reaches the build machine, so the next build rebuilds the same code and fails the same way. `resume` sees the new HEAD and re-verifies every stage — that is what you want after a code change.

**Close.**

- Package paths come from the build stage's `DELIVERED` lines. If copying the package into the delivery directory failed, read the WARN path left in the build directory. If neither exists, say you have no path. Do not invent one.
- `close` leaves a delivery record (product name plus the ship commit). Step 4 uses it for the same-commit check. **Do not delete it by hand.**
- `close` refuses a release loop that has not shipped; `abort` drops it and writes no record.

**An interrupted build.** An interrupted build keeps running on the build machine. Run the stage `where` names again: `stage run` asks the build machine whether this build (same commit, same product) is still running and attaches to it. Do not `abort` or `init` to restart it: a fresh release loop wipes the source tree that build is reading.

**Reply:** the step 2 table; for each product, its package path from the `DELIVERED` lines (or that there is none) and any pause the owner must answer, with its receipt as-is; the commit the set came from and the `same-commit` result; and, once the owner has tried it, the install test result and what you did on it.
