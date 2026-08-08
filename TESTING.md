# TESTING.md

本仓库不保留自动化测试、测试夹具或测试套件。`archive/` 与 `vendor/` 是冻结内容，不参与活跃仓库检查。

## 提交前静态检查

整段用 `bash -euo pipefail` 运行，不要粘进交互式 shell。交互式 shell 没有开
`errexit`，`test` 断言失败只是静默返回非零，后面的命令照常往下跑，整段看起来
像通过。这段也只在 bash 下成立：zsh 会把 `errexit` 带进命令替换的子 shell，
`test "$(... ; echo $?)" = 2` 这类用例拿不到退出码。

```bash
shellcheck --severity=warning mmw/cli/mmw mmw/cli/adapters/*.sh mmw/cli/lib/*.sh \
  mmw/mcp/install-mcp.sh mmw/release/release-flow.sh

test "$(MMW_HOST=codex mmw/cli/mmw path prototype effort issue-42)" = \
  "docs/prototypes/effort/issue-42"
test "$(MMW_HOST=codex mmw/cli/mmw path research effort issue-42)" = \
  "docs/research/effort/issue-42"
test "$(MMW_HOST=codex mmw/cli/mmw path scratch effort)" = ".scratch/effort"
test "$(MMW_HOST=codex mmw/cli/mmw path scratch effort task-feat-a)" = \
  ".scratch/effort/task-feat-a"
test "$(MMW_HOST=codex mmw/cli/mmw path spec feat-a)" = \
  "docs/specs/feat-a/feat-a.md"
test "$(MMW_HOST=codex mmw/cli/mmw path review)" = ".reviews"
test "$(MMW_HOST=codex mmw/cli/mmw artifact >/dev/null 2>&1; echo $?)" = 2
! MMW_HOST=codex mmw/cli/mmw path prototype .. >/dev/null 2>&1
! MMW_HOST=codex mmw/cli/mmw path prototype effort ticket-42 >/dev/null 2>&1
! MMW_HOST=codex mmw/cli/mmw path spec ../feat-a >/dev/null 2>&1
test "$(MMW_HOST=codex mmw/cli/mmw path unknown effort >/dev/null 2>&1; echo $?)" = 2

# gh 桩放进 PATH，不用 shell 函数：函数形式依赖 bash 的 export -f，
# 在别的 shell 下会静默失活，让下面三条断言打到真实 gh 上并假通过。
gh_stub_dir="$(mktemp -d "${TMPDIR:-/tmp}/mmw-gh-stub.XXXXXX")"
cat > "$gh_stub_dir/gh" <<'STUB'
#!/bin/sh
if [ "$1" = "api" ] && [ "$2" = "--paginate" ]; then
  printf '%s\n' '[
    {"number":101,"title":"Spec issue","state":"open","assignees":[],"labels":[],"issue_dependencies_summary":{"blocked_by":0}},
    {"number":102,"title":"Prototype decision","state":"open","assignees":[],"labels":[{"name":"wayfinder:prototype"}],"issue_dependencies_summary":{"blocked_by":0}}
  ]'
  exit 0
fi
exit 1
STUB
chmod +x "$gh_stub_dir/gh"
# 先确认桩真的生效：这条失败说明 mmw 没走 PATH 上的 gh，下面三条不能算数。
test "$(PATH="$gh_stub_dir:$PATH" command -v gh)" = "$gh_stub_dir/gh"
test "$(PATH="$gh_stub_dir:$PATH" MMW_GH_REPO=owner/repo MMW_HOST=codex mmw/cli/mmw \
  issue frontier 1 --label-prefix wayfinder:)" = $'102\tPrototype decision'
test "$(PATH="$gh_stub_dir:$PATH" MMW_GH_REPO=owner/repo MMW_HOST=codex mmw/cli/mmw \
  issue frontier 1 --label wayfinder:prototype)" = $'102\tPrototype decision'
test "$(PATH="$gh_stub_dir:$PATH" MMW_GH_REPO=owner/repo MMW_HOST=codex mmw/cli/mmw \
  issue frontier 1 --label ready-for-agent --label-prefix wayfinder: >/dev/null 2>&1; echo $?)" = 2
rm -rf "$gh_stub_dir"

mmw_source_root="$PWD/mmw"
path_test_dir="$(mktemp -d "${TMPDIR:-/tmp}/mmw-path-test.XXXXXX")"
git -C "$path_test_dir" init -q
jq '.paths.scratch = "../outside"' mmw/cli/mmw.default.json > "$path_test_dir/.mmw.json"
! (cd "$path_test_dir" && MMW_HOST=codex "$mmw_source_root/cli/mmw" path scratch effort) \
  >/dev/null 2>&1
jq '.paths.specs = "../outside"' mmw/cli/mmw.default.json > "$path_test_dir/.mmw.json"
! (cd "$path_test_dir" && MMW_HOST=codex "$mmw_source_root/cli/mmw" path spec feat-a) \
  >/dev/null 2>&1
find "$path_test_dir" -depth -delete

migration_dir="$(mktemp -d "${TMPDIR:-/tmp}/mmw-init-test.XXXXXX")"
# 模拟仍使用旧 research 路径字段的配置。
jq '.paths.investigations = "docs/investigating" | del(.paths.research, .paths.evidence, .paths.scratch)' \
  mmw/cli/mmw.default.json > "$migration_dir/.mmw.json"
chmod 0600 "$migration_dir/.mmw.json"
git -C "$migration_dir" init -q
(
  cd "$migration_dir"
  source "$mmw_source_root/cli/lib/config.sh"
  source "$mmw_source_root/cli/lib/path.sh"
  source "$mmw_source_root/cli/lib/init.sh"
  MMW_ROOT="$mmw_source_root"
  mmw_init_config
)
test "$(jq -r '.paths.research' "$migration_dir/.mmw.json")" = "docs/research"
test "$(jq -r '.paths | has("investigations")' "$migration_dir/.mmw.json")" = "false"
test "$(jq -r '.paths.evidence' "$migration_dir/.mmw.json")" = "docs/evidence"
test "$(jq -r '.paths.scratch' "$migration_dir/.mmw.json")" = ".scratch"
if migration_mode="$(stat -f '%Lp' "$migration_dir/.mmw.json" 2>/dev/null)"; then
  :
else
  migration_mode="$(stat -c '%a' "$migration_dir/.mmw.json")"
fi
test "$migration_mode" = "600"
find "$migration_dir" -depth -delete

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
