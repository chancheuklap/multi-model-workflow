#!/usr/bin/env bash
# MMW 创建新 worktree 时准备结构图：同提交复用、否则调用项目重建，失败可见但不阻断。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"

fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
TARGET="$TMP/target"
mkdir -p "$REPO/scripts/dev/knowledge_graph"
git -C "$REPO" init -q
git -C "$REPO" config user.email test@example.com
git -C "$REPO" config user.name Test
cat >"$REPO/scripts/dev/knowledge_graph/rebuild.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [ "${MMW_TEST_REBUILD_FAIL:-0}" = 1 ]; then
  exit 9
fi
mkdir -p graphify-out
head_sha="$(git rev-parse HEAD)"
printf '{"graph":{"agentflow_build":{"head_sha":"%s"}},"nodes":[],"links":[]}\n' "$head_sha" >graphify-out/graph.json
: >graphify-out/rebuild-called
SH
chmod +x "$REPO/scripts/dev/knowledge_graph/rebuild.sh"
printf 'graphify-out/\n' >"$REPO/.gitignore"
printf 'seed\n' >"$REPO/seed.txt"
git -C "$REPO" add -A
git -C "$REPO" commit -qm base
HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
git -C "$REPO" worktree add -q "$TARGET" HEAD

mkdir -p "$REPO/graphify-out"
printf '{"graph":{"agentflow_build":{"head_sha":"%s"}},"nodes":[],"links":[]}\n' "$HEAD_SHA" >"$REPO/graphify-out/graph.json"
mmw_prepare_retrieval_graph "$REPO" "$TARGET" >/dev/null 2>"$TMP/reuse.err"
if [ "$(jq -r '.graph.agentflow_build.head_sha' "$TARGET/graphify-out/graph.json")" = "$HEAD_SHA" ] \
  && [ ! -e "$TARGET/graphify-out/rebuild-called" ]; then
  ok "same-HEAD graph is reused without rebuild"
else
  no "same-HEAD graph reuse"
fi

rm -rf "$TARGET/graphify-out"
printf '{"graph":{"agentflow_build":{"head_sha":"stale"}},"nodes":[],"links":[]}\n' >"$REPO/graphify-out/graph.json"
mmw_prepare_retrieval_graph "$REPO" "$TARGET" >/dev/null 2>"$TMP/rebuild.err"
if [ -f "$TARGET/graphify-out/rebuild-called" ] \
  && [ "$(jq -r '.graph.agentflow_build.head_sha' "$TARGET/graphify-out/graph.json")" = "$HEAD_SHA" ]; then
  ok "stale source graph invokes target rebuild"
else
  no "target rebuild for stale source graph"
fi

rm -rf "$TARGET/graphify-out" "$REPO/graphify-out"
if MMW_TEST_REBUILD_FAIL=1 mmw_prepare_retrieval_graph "$REPO" "$TARGET" >/dev/null 2>"$TMP/fail.err" \
  && grep -q 'WARNING' "$TMP/fail.err"; then
  ok "rebuild failure warns without blocking worktree flow"
else
  no "non-blocking visible rebuild failure"
fi

PLAIN="$TMP/plain"
PLAIN_TARGET="$TMP/plain-target"
mkdir -p "$PLAIN"
git -C "$PLAIN" init -q
git -C "$PLAIN" config user.email test@example.com
git -C "$PLAIN" config user.name Test
printf 'plain\n' >"$PLAIN/plain.txt"
git -C "$PLAIN" add plain.txt
git -C "$PLAIN" commit -qm plain
git -C "$PLAIN" worktree add -q "$PLAIN_TARGET" HEAD
if mmw_prepare_retrieval_graph "$PLAIN" "$PLAIN_TARGET" >/dev/null 2>"$TMP/plain.err" \
  && [ ! -e "$PLAIN_TARGET/graphify-out" ] && [ ! -s "$TMP/plain.err" ]; then
  ok "repository without rebuild provider is unchanged"
else
  no "provider-free repository no-op"
fi

exit "$fail"
