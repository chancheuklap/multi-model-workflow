# TESTING.md

本仓库不保留自动化测试、测试夹具或测试套件。`archive/` 与 `vendor/` 是冻结内容，不参与活跃仓库检查。

## 提交前静态检查

整段用 `bash -euo pipefail` 运行，不要粘进交互式 shell。交互式 shell 没有开
`errexit`，`test` 断言失败只是静默返回非零，后面的命令照常往下跑，整段看起来
像通过。这段也只在 bash 下成立：zsh 会把 `errexit` 带进命令替换的子 shell，
`test "$(... ; echo $?)" = 2` 这类用例拿不到退出码。

```bash
shellcheck --severity=warning mmw/cli/mmw mmw/cli/adapters/*.sh mmw/cli/lib/*.sh \
  mmw/install.sh mmw/mcp/install-mcp.sh mmw/release/release-flow.sh

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
mmw_source_root="$PWD/mmw"
init_dir="$(mktemp -d "${TMPDIR:-/tmp}/mmw-init-test.XXXXXX")"
git -C "$init_dir" init -q
git -C "$init_dir" config user.name "MMW Test"
git -C "$init_dir" config user.email "mmw-test@example.invalid"
printf 'keep-existing-testing\n' > "$init_dir/TESTING.md"
git -C "$init_dir" add TESTING.md
git -C "$init_dir" commit -q -m "test: seed repository"

# 当前 gh 桩不支持 auth status，使 init 明确跳过真实 GitHub 标签操作。
cat > "$gh_stub_dir/gh" <<'STUB'
#!/bin/sh
exit 1
STUB
chmod +x "$gh_stub_dir/gh"

(cd "$init_dir" && PATH="$gh_stub_dir:$PATH" MMW_HOST=codex "$mmw_source_root/cli/mmw" init)
test "$(cat "$init_dir/TESTING.md")" = "keep-existing-testing"
jq -e '.models == null' "$init_dir/.mmw.json" >/dev/null
test "$(jq -c '.paths | keys' "$init_dir/.mmw.json")" = \
  '["release","reviews","scratch","worktrees"]'
grep -q 'MMW-DOMAIN-CONTEXT-START' "$init_dir/AGENTS.md"
# init 生成的 CLAUDE.md 是一行 @AGENTS.md 引用（mmw/cli/lib/context_docs.py），标记本体在 AGENTS.md。
grep -qxF '@AGENTS.md' "$init_dir/CLAUDE.md"
grep -qxF '.scratch/' "$init_dir/.gitignore"
grep -qxF '.reviews/' "$init_dir/.gitignore"
test -z "$(git -C "$init_dir" status --porcelain)"

init_head="$(git -C "$init_dir" rev-parse HEAD)"
(cd "$init_dir" && PATH="$gh_stub_dir:$PATH" MMW_HOST=codex "$mmw_source_root/cli/mmw" init)
test "$(git -C "$init_dir" rev-parse HEAD)" = "$init_head"
test -z "$(git -C "$init_dir" status --porcelain)"

find "$init_dir" -depth -delete
find "$gh_stub_dir" -depth -delete

git diff --check
mmw/cli/mmw skills materialize --host all --check
mmw/cli/mmw agents materialize --host pi --check
python3 mmw/codex/runtime.py materialize --check
grep -qxF 'argument-hint: "[wayfinder] [需求、bug、issue/PR/map 编号或链接；留空恢复当前任务]"' \
  mmw/prompts-pi/mmw-start.md
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
python3 -m json.tool mmw/codex/profiles.json >/dev/null
python3 -m json.tool mmw/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool mmw/.mcp-codex.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool mmw/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool mmw/package.json >/dev/null

mmw_version="$(jq -r '.version' mmw/package.json)"
test "$(jq -r '.version' mmw/.codex-plugin/plugin.json)" = "$mmw_version"
test "$(jq -r '.version' mmw/.claude-plugin/plugin.json)" = "$mmw_version"
test "$(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)" = "$mmw_version"
test "$(jq -r '.version' .claude-plugin/marketplace.json)" = "$mmw_version"
```

## 真实宿主验证

Codex App、Claude Code、Pi、Cursor 和 Windows 出包行为只能在对应真实宿主上验证。静态检查不代表这些运行路径已经通过。
