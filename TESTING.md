# TESTING.md

本仓库不保留自动化测试、测试夹具或测试套件。`archive/` 与 `vendor/` 是冻结内容，不参与活跃仓库检查。

## 提交前静态检查

```bash
shellcheck --severity=warning mmw/cli/mmw mmw/cli/adapters/*.sh mmw/cli/lib/*.sh \
  mmw/mcp/install-mcp.sh mmw/release/release-flow.sh

test "$(MMW_HOST=codex mmw/cli/mmw artifact path prototype effort issue-42)" = \
  "docs/prototypes/effort/issue-42"
test "$(MMW_HOST=codex mmw/cli/mmw artifact path investigation effort issue-42)" = \
  "docs/investigating/effort/issue-42"
test "$(MMW_HOST=codex mmw/cli/mmw artifact path scratch effort)" = ".scratch/effort"
test "$(MMW_HOST=codex mmw/cli/mmw artifact path scratch effort task-feat-a)" = \
  ".scratch/effort/task-feat-a"
test "$(MMW_HOST=codex mmw/cli/mmw artifact root review)" = ".reviews"
! MMW_HOST=codex mmw/cli/mmw artifact path prototype .. >/dev/null 2>&1
! MMW_HOST=codex mmw/cli/mmw artifact path prototype effort ticket-42 >/dev/null 2>&1
test "$(MMW_HOST=codex mmw/cli/mmw artifact path unknown effort >/dev/null 2>&1; echo $?)" = 2

(
  source mmw/cli/lib/artifact.sh
  mmw_path_field() { printf '%s\n' '../outside'; }
  ! mmw_artifact_path scratch effort >/dev/null 2>&1
)

migration_dir="$(mktemp -d "${TMPDIR:-/tmp}/mmw-init-test.XXXXXX")"
jq 'del(.paths.investigations, .paths.evidence, .paths.scratch)' \
  mmw/cli/mmw.default.json > "$migration_dir/.mmw.json"
(
  source mmw/cli/lib/artifact.sh
  source mmw/cli/lib/init.sh
  MMW_ROOT="$PWD/mmw"
  mmw_repo_root() { printf '%s\n' "$migration_dir"; }
  mmw_init_config
)
test "$(jq -r '.paths.investigations' "$migration_dir/.mmw.json")" = "docs/investigating"
test "$(jq -r '.paths.evidence' "$migration_dir/.mmw.json")" = "docs/evidence"
test "$(jq -r '.paths.scratch' "$migration_dir/.mmw.json")" = ".scratch"
unlink "$migration_dir/.mmw.json"
rmdir "$migration_dir"

git diff --check
mmw/cli/mmw skills materialize --host all --check
python3 mmw/codex/runtime.py materialize --check
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool mmw/codex/profiles.json >/dev/null
python3 -m json.tool mmw/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool mmw/.mcp-codex.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool mmw/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool mmw/package.json >/dev/null
```

## 真实宿主验证

Codex App、Claude Code、Pi、Cursor 和 Windows 出包行为只能在对应真实宿主上验证。静态检查不代表这些运行路径已经通过。
