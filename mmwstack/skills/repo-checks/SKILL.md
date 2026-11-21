---
name: repo-checks
description: "Install repo checks, maintain slow or flaky checks from run records, and fix Doctor selection misses. Use when adding a repo or handling Doctor checks findings."
---

# Repo checks

You are the session agent installing checks or handling a Doctor checks finding. Choose Install, Maintain, or Fix a miss. Return the changed Check Config and proof, or the evidence that no correction is needed.

Use [to-tickets](../to-tickets/SKILL.md) to reuse the work issue and record the result. Keep one PR per repository for the assigned correction.

Run every command from the target repository root. The [check engine](scripts/check.mjs) reads the current directory and takes no repository-path argument. The entry uses the installed engine at `~/.agents/skills/repo-checks/scripts/check.mjs`; `MMW_REPO_CHECKS_ENGINE` can point at another engine file for a proof.

Read the [reference](references/checks.md) for Check Config fields, JSON results, and moment rules. Use `scripts/check --help` for command syntax. Use top-level `slots` and per-check `slot` for cross-worktree counting leases with optional `perRunMax` caps. Checks declare either binary `lock` or counting `slot`, never both.

During execution, check commands receive two per-run environment variables documented in [Selection manifest and deferral](references/checks.md#selection-manifest-and-deferral). `MMW_REPO_CHECKS_SELECTION_MANIFEST` points to a file listing `<check-name> <repo-relative-test-path>` for scheduled and clean `reused` checks, excluding pre-run `skipped` checks. `MMW_REPO_CHECKS_DEFERRED_MARKER` holds a per-check marker path cleared before every attempt so a check that defers work and exits 0 records `reusable: false`.

## Install

Enter with the target repository and the Home Repo registry. Finish with a valid Check Config, three canonical entry files, a registry entry, and saved probes.

1. Read the repository's instructions, package commands, tests, prek configuration, and workflows. Inventory each check's inputs, test files, environment, and existing runner. Put CI-only, device, and owner-only tests in lanes rather than automatic checks.
2. Draft `.agents/checks.json` against the [schema](scripts/checks.schema.json) and the [field reference](references/checks.md#check-config). Use language selectors for import dependencies and `inputs` for disk reads the selector cannot see. Classify every tracked path and claim every test through a check, lane, or exclusion. Put lockfiles, tool configuration, the Check Config, `scripts/check`, `.githooks/pre-commit`, and `.githooks/pre-push` in `affects_all`. Keep `inert` limited to paths that cannot affect a check.
3. Copy the three templates without edits. Set `skill` to this skill's absolute directory and `repo` to the target root.

   ```sh
   mkdir -p "$repo/scripts" "$repo/.githooks"
   cp -p "$skill/templates/check" "$repo/scripts/check"
   cp -p "$skill/templates/pre-commit" "$repo/.githooks/pre-commit"
   cp -p "$skill/templates/pre-push" "$repo/.githooks/pre-push"
   git -C "$repo" add -- .agents/checks.json scripts/check .githooks/pre-commit .githooks/pre-push
   ```

   Preserve other repository-owned hooks. The entry is a small shell wrapper with an inline Node part. The templates carry executable permissions. Staging these files lets `lint` check their classification.
4. Add or update the repository in the Home Repo's `repos/registry.json`. Match the existing entry shape with `name`, `path`, `remote`, and `integration`, plus `release` when applicable. Keep an existing entry rather than adding a duplicate. Make `integration` agree with the Check Config and an actual `origin` branch.
5. Run `scripts/check ensure`, `scripts/check lint`, and `scripts/check ensure --check --json`. Require exit 0 from each. Run `ensure` again and require no changes. `ensure` repairs local state; it does not create or overwrite entry files.
6. Run [Prove a Check Config change](#prove-a-check-config-change). For a repository with a gate, also prove the workflow commands and dependency in the [moment rules](references/checks.md#moment-rules). Save the config, entry-file comparison, registry entry, commands, output, and exit codes on the work issue.

## Maintain

Enter with Doctor findings or run records for one repository. Finish with at most one PR containing a proved correction, or a recorded finding with no speculative config change.

1. Run `scripts/check report --json`. Read the records behind the flagged check in the git common directory's `repo-checks` folders. Use the [report fields](references/checks.md#report) to distinguish actual executions, reused passes, bypasses, and engine failures.
2. For `flaky`, inspect the failed attempts and retry recoveries. Propose `retry: 1` only for a check with at least two proved retry recoveries in 14 days. A check with `retry: 0` cannot appear as flaky because `report` counts recoveries only. Keep that check's retry at 0 without recovery evidence.
3. For `slow`, inspect the log and command behind a nearest-rank p90 above half the effective timeout over the last 20 actual executions. Flag the duration with its sample count and timeout. Prove a correction before proposing it. Slowness alone is not retry evidence.
4. Reproduce each accepted problem and prove the proposed correction. For a Check Config edit, run [Prove a Check Config change](#prove-a-check-config-change). Collect the proved corrections in one PR for this repository, with before-and-after output. If no correction is proved, record the finding and stop without a PR.

## Fix a miss

Enter with one Doctor miss naming the repository, commit, and gate run link. Finish with a Check Config correction and a regression probe that selects the missed check.

1. Read the failing gate job and the passed push record. Identify the local check that corresponds to the failed command. Save the missed commit, gate link, check id, and changed paths.
2. Run `scripts/check replay <pr>` for its merged PR, or `scripts/check replay --range <base>..<head>` for the missed local range. Save the before output. Replay uses the current Check Config and runs selectors, but never preparation or checks. PR replay uses the paginated changed-file list, including previous names of renamed files, for squash, merge, and rebase merges. Range replay needs no network.
3. Trace the missed path through `inputs`, `sources` and its selector, `inert`, and `affects_all`. Add the missing check or input and remove any false inert classification. Use the smallest correction that selects the failed check.
4. Replay the identical PR or range. Require `SELECT <failed check id>` and the intended reason, not an unrelated widen. Save a regression probe for that selection in the target repository's existing test structure. Run [Prove a Check Config change](#prove-a-check-config-change). If the correction changes a local command or `ci_run`, rerun both commands in a clean clone.
5. Link the config diff and before-and-after probe on the work issue. Return the PR with the selected check and the gate failure it addresses.

## Prove a Check Config change

Use disposable repositories or clones with a temporary home, a bare remote, and a copy of the registry. Keep planted failures out of the working repository and run the canonical entry with hooks enabled.

- With a prek configuration, stage a planted lint error and require a real `git commit` to refuse it and name the hook. Remove the error and require the commit to pass. Without a prek configuration, record that the commit run does nothing.
- Commit a failing test inside a selected check's scope. Require a real `git push` to refuse it and name the failing check. Repair the test and require the push to pass.
- On a branch containing only an inert-path change, require `SUMMARY nothing selected`. Change a check's `inputs` path and require `SELECT <check id> inputs <path>`.
- Run `scripts/check lint` after the config change. For a gate, run the local and gate commands in a clean clone and read back the deploy or publish job's `needs`.

Record each probe's command, output, and exit code. A green check run supplies repository-check evidence, not verification on the real product surface or a shipping verdict.
