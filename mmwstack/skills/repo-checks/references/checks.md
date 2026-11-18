# Repo checks reference

The [engine](../scripts/check.mjs), [schema](../scripts/checks.schema.json), and [tests](../scripts/test/) define the command contract.

## Moment rules

| Moment | Trigger and scope | Required result |
| --- | --- | --- |
| Commit run | The pre-commit hook calls `scripts/check --staged`. With `prek.toml` or `.pre-commit-config.yaml`, it runs `prek run` on staged files. Without either file, it does nothing. | A prek failure exits 1. Missing prek with a config exits 2 and names its installation command. The repository's prek config decides which commit checks run. |
| Push run | The pre-push hook passes stdin to `scripts/check --push`. Each pushed branch contributes its merge-base range against `origin/<integration>`. Deletions and non-branch remote refs contribute nothing. | The union of committed paths selects affected checks. Renames contribute old and new paths. The run reads the committed HEAD Check Config and executes in the current worktree. Dirty files or a pushed tip different from HEAD print `DIRTY` and disable reuse, but do not change selection. |
| Deploy gate | A GitHub workflow runs all clean-runner checks on the exact commit before deployment or publication. | The deploy or publish job depends on the gate through `needs`. A repository without deployment or publication has no deploy gate. CI runs repository commands directly, without the engine. |

A manual `scripts/check` uses the current Check Config and combines committed changes since the merge base with staged, unstaged, and untracked files. `--base <ref>` overrides the base and avoids a fetch. `--all` runs whole checks. `--only <ids>` restricts selection and needs `--all` to force a check.

### CI placement

GitHub retains PR source and title policies, release and operations jobs needing secrets or servers, builds needing Windows or x64, and deploy gates. Other feedback checks run locally.

| Repository | Workflow rule |
| --- | --- |
| Four ERP application repositories | The push gate remains `development-ci`, with deployment dependent on it. PR `verify` runs only for `main`, not `development`. The full `main` PR run remains because the production push deploys without another gate. |
| doudian-automation-worker | The release workflow's `verify` precedes publication. Its commands also run locally. The PR workflow keeps the version-title and `main` source policies. Local tests need PowerShell. |
| agentflow-infrastructure | Existing triggers and job names stay. `infrastructure-ci` remains required. Shared repository scripts replace the workflow's inline commands. |
| qianchuan-rules-kb | The existing `gate.yml` server-side fallback keeps its PR trigger and limits push to `main`. |
| agentflow, multi-model-workflow, and Home Repo | No new PR workflow or deploy gate. Existing operations and release workflows stay. |

Existing branch protection, required statuses, and job names, including `main-source-policy`, stay unchanged. A green run is neither independent live verification nor a shipping verdict.

### Hook results and bypass

Hook runs set `MMW_REPO_CHECKS_HOOK`. The entry runs the engine as a child, and check commands never receive that variable. Hooks block only engine exit codes 1 and 2. Every other code, including 70, a signal, a missing engine, or missing Node, allows the Git operation. A missing engine falls back to prek for a commit when a prek config exists.

`MMW_CHECKS_SKIP` with a reason prints `SKIPPED BY REASON <reason>` and appends one JSON line containing `type`, `time`, `reason`, and `hook`. Use it only as a one-command prefix, such as `MMW_CHECKS_SKIP='repair the wrong input rule' git commit ...`. An exported value also skips `lint`, `ensure`, and `--all`. `report`, `selftest`, and `replay` remain diagnostic.

Ctrl-C stops running checks and never retries an interrupted check. A killed engine can leave a check running until it finishes. A later run waits for its lock or names the holder at its own lock timeout.

The text `SUMMARY` counts blocked checks, including a lock timeout or failed `prepare`, in `skipped`. JSON keeps `blocked` separate. Exit 0 can include gate-covered skips or no selected checks. Exit 1 means a failed check. Exit 2 covers invalid requests or config, failed selectors, blocked execution, or missing needs with no gate coverage. Exit 70 means an unavailable engine or an internal error. Diagnostic modes have the specific exit codes below.

## Check Config

The target repository holds `.agents/checks.json`. Paths and globs are repository-relative with forward slashes. Globs support `*`, `**`, `?`, character classes, and brace alternatives. Unknown fields are invalid.

### Top-level fields

| Field | Meaning |
| --- | --- |
| `integration` | Required branch name, such as `dev`, matching an actual `origin` remote branch and the registry. |
| `ci_workflow` | Required workflow filename or relative path. `null` means no deploy gate and forbids `ci: true`. |
| `test_files` | Required array of patterns that identify tests for the coverage audit. |
| `inert` | Required array of paths that cannot affect checks. |
| `affects_all` | Required array of patterns whose changes select every check and print `WIDEN`. |
| `marker_exempt` | Optional patterns exempt from legacy-marker scanning. Defaults to `[]`. Exemption does not classify a path or claim a test. |
| `prepare` | Optional object with `run` and `stamps` patterns. Runs before selected checks when the stamp hash changes or a selected `path:` need is missing. |
| `checks` | Required array of executable checks. |
| `lanes` | Required array of tests the engine never runs. Each has `id`, `kind` (`ci-only`, `device`, or `owner-only`), `reason`, `run_by` (workflow, skill, or `owner`), and `tests` patterns. `command` is optional. |
| `excluded` | Required array of non-test paths with `paths` patterns and a `reason`. |

### Check fields

| Field | Meaning |
| --- | --- |
| `id` | Required repository-unique identifier, with no whitespace or comma and no leading hyphen. |
| `run` | Required command. For narrowed scope, `{files}` and `{tests}` expand to shell-quoted changed files and selected tests. Interpolation needs a POSIX shell host. |
| `run_all` | Whole-check command, with no `{files}` or `{tests}`. Required when `run` contains either placeholder. Whole scope uses `run_all`, or `run` when absent. |
| `inputs` | Required patterns. A changed match selects the entire check. Includes reads that import selectors cannot infer. |
| `sources`, `select` | Optional pair. `sources` patterns identify changed source files. `select` maps them to a JSON array of repository-relative test paths on stdout. Each returned path must match `tests`. An empty array selects nothing. A failed selector exits 2. |
| `tests` | Required patterns claiming the tests this check runs. Test files also need classification through `inputs`, `sources`, `inert`, or `affects_all`. |
| `needs` | Optional conditions. `cmd:<name>` requires an executable on PATH. `docker` requires a reachable daemon. `os:<darwin, linux, or windows>` requires that OS. `env:<name>` requires a set variable. `path:<relative path>` requires an existing path. Other forms are invalid. |
| `ci`, `ci_run`, `ci_reason` | `ci` is required. When true, `ci_run` is required verbatim text in `ci_workflow`. When false, `ci_reason` is required. Missing needs skip a check with gate coverage, or exit 2 without it. |
| `timeout_s`, `retry`, `lock` | Optional positive timeout in seconds (default 600), retry count 0 or 1 (default 0), and machine-wide shared-resource lock name. Only a failed check retries. |

An unclassified changed path prints `UNCLASSIFIED` and widens selection to every check. `lint` reports unclassified tracked paths and unclaimed tracked tests. It also checks integration, gate command text, protected lane commands, canonical entry bytes, and legacy markers outside exemptions. It does not prove local and gate command equivalence.

## JSON results

`lint --json`, `ensure --check --json`, `report --json`, and `selftest --json` emit one object on stdout. These fields come from the engine's test assertions. Optional finding fields appear only when relevant.

| Shared field | Meaning |
| --- | --- |
| `mode` | `lint`, `ensure`, `report`, or `selftest`. |
| `ok` | Boolean success result. |
| `exit_code` | Numeric command result. |
| `findings` | Array of diagnostics with `rule` and `message`. A finding can also contain `field`, `check`, `path`, or `marker`. |

### Lint

Fields are `mode`, `ok`, `exit_code`, and `findings`. Exit 0 is clean, 1 means findings, 2 means unreadable config or invalid usage, and 70 means an internal error.

The asserted finding keys are `findings[].rule`, `findings[].message`, `findings[].field`, `findings[].check`, `findings[].path`, and `findings[].marker`.

### Ensure

| Field | Meaning |
| --- | --- |
| `check` | True for read-only `--check`. |
| `pending` | Repairs not applied, each with `kind`, `path`, and `message`. |
| `changed` | Applied repairs, each with `kind`, `path`, and `message`. Empty with `--check`. |
| `retained` | Empty array. |

The full field set is `mode`, `ok`, `exit_code`, `check`, `pending`, `changed`, `retained`, and `findings`. Exit 0 means healthy or repaired, 1 means pending repairs under `--check`, and 2 means unable to repair. `ensure` also accepts `--json` without `--check`.

### Report

| Field | Meaning |
| --- | --- |
| `runs` | Retained run counts across worktrees, with `total`, `passed`, `failed`, `blocked`, and `internal_error`. |
| `bypasses` | Last 14 days, with `count`, `latest_reason` (string or null), and `records`. Each record has `type`, `time`, `reason`, and `hook`. |
| `engine_failures` | Last 14 days, with `count` and `records`. Each record has `type`, `time`, `reason`, `hook`, and `exit_code`. |
| `retry_recoveries` | Number of actual executions recovered on retry in 14 days. Reused results do not count. |
| `slow` | Checks above half their effective timeout, each with `id`, `samples`, `p90_s`, and `timeout_s`. Uses nearest-rank p90 of the last 20 actual executions, or fewer when fewer exist. |
| `flaky` | Checks with at least two recoveries in 14 days, each with `id` and `recoveries`. Retry 0 produces no recovery evidence. |
| `passed_push_commits` | Deduplicated commit SHAs from successful, clean, matching-HEAD push records. |

The shared fields also appear. `report` reads retained history without fetching or running checks. A healthy report exits 0, invalid usage exits 2, and an internal error exits 70.

### Selftest

`assertions` contains `{name, ok}` objects with `message` on failure. The names are `fixture`, `engine-run`, `selection`, `check-pass`, and `check-log`. The shared fields also appear. The test uses a temporary repository and the canonical entry, then removes its fixture. Its commits use an author configured inside the temporary repository.

Exit 0 means passed, 1 means a failed self-test, and 2 means invalid usage.

### Run records

Run JSON adds `timing.select_ms` for selection alone, excluding fetch and selector subprocess waits. A run's `summary` has `selected`, `passed`, `failed`, `skipped`, `blocked`, and `internal-error`. Logs and records live under the git common directory's `repo-checks` folder, separated by worktree. The engine retains 50 run records and 20 log sets per worktree.
