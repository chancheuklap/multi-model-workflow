# Repo checks

Repo checks selects and runs a repository's checks from one Check Config and a shared check engine. Git hooks supply local feedback. A deploy gate checks the exact commit before deployment or publication.

## Language

### Configuration and selection

**Check Config**:
The repository's `.agents/checks.json`. It declares checks, their inputs and environment, paths that affect every check, inert paths, lanes, and exclusions.

**Check**:
A command the engine can select and run. Its repository-unique id connects selection, output, logs, and run records. A check can run at whole scope or on tests returned by its selector.

**Lane**:
Tests the engine never runs. A lane records their test paths, why they need another runner, and who runs them. Its kind is `ci-only`, `device`, or `owner-only`.

**Selection**:
The checks and test scope chosen for changed paths. An `inputs` match selects a whole check. A source selector can narrow tests. Renames contribute both old and new paths.

**Widen**:
A selection of every check because a changed path matches `affects_all` or is unclassified. The engine prints the reason rather than silently dropping the path.
_Avoid_: always-run group. A widen is caused by a change, not by membership in a permanently selected group.

**Inert path**:
A path whose changes cannot affect a check. A change containing only inert paths selects nothing. A path unknown to the config is unclassified, not inert.

Sources include [repo-checks](../../../skills/repo-checks/SKILL.md), the [Check Config fields](../../../skills/repo-checks/references/checks.md#check-config), and the [selection tests](../../../skills/repo-checks/scripts/test/run.test.mjs).

### Runs and results

**Commit run**:
The pre-commit run on staged files through the repository's prek configuration. A repository without a prek configuration has no commit checks.
_Avoid_: tier for a commit or push moment.

**Push run**:
The pre-push run selected from the union of committed branch ranges against the integration branch. It reads the committed HEAD Check Config. It executes checks in the current worktree and disables reuse when that tree is dirty or HEAD differs from a pushed tip.

**Gate**:
The GitHub workflow job that runs clean-runner checks on the exact commit before deployment or publication. The deploy or publish job depends on it. This deploy gate is distinct from the Home Repo's Gate that controls agent commands.

**Bypass**:
A single operation allowed with `MMW_CHECKS_SKIP` set to a reason. The engine prints the reason and appends an audit record for Doctor to report. An exported value also bypasses manual checks and config diagnostics.

Sources include the [moment rules](../../../skills/repo-checks/references/checks.md#moment-rules), the [hook tests](../../../skills/repo-checks/scripts/test/hooks.test.mjs), and the [report tests](../../../skills/repo-checks/scripts/test/modes.test.mjs).

### Shared engine

**Check engine**:
The Node program owned by mmwstack and installed in the Home Repo skill library. Repositories keep the Check Config and three canonical entry files, not engine copies. The engine owns selection, execution, local repairs, run records, reports, replay, and self-test.

Sources include the [engine](../../../skills/repo-checks/scripts/check.mjs) and the [entry templates](../../../skills/repo-checks/templates/).
