#!/usr/bin/env bash
# Cursor 插件 Graphify MCP 启动器（MMW 一体化检索包）。
# 上游只升 graphifyy CLI；MCP 包装器与 ensure 永远用插件内自定义脚本。
# 启动前：检测 graphifyy 是否有新版本 → 有才 upgrade → 合同自检（失败回滚 CLI，不动包装器）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/uv-tool-maintain.sh
source "$ROOT/scripts/lib/uv-tool-maintain.sh"
MMW_RETRIEVAL_PLUGIN_ROOT="$ROOT"
mmw_maintain_graphify

SERVER="${GRAPHIFY_MCP_PY:-$ROOT/skills/graphify/scripts/graphify_mcp.py}"
ENSURE="${GRAPHIFY_ENSURE_BIN:-$ROOT/skills/graphify/scripts/graphify_ensure.py}"
[ -f "$SERVER" ] || {
  echo "ERROR: missing plugin Graphify MCP server: $SERVER" >&2
  exit 2
}
[ -f "$ENSURE" ] || {
  echo "ERROR: missing plugin Graphify ensure: $ENSURE" >&2
  exit 2
}
export GRAPHIFY_ENSURE_BIN="$ENSURE"

PYTHON_BIN="${GRAPHIFY_PYTHON:-$(command -v python3 2>/dev/null || true)}"
[ -n "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ] || {
  echo "ERROR: python3 not on PATH for Graphify MCP" >&2
  exit 2
}

PROJECT="${GRAPHIFY_PROJECT:-${SERENA_PROJECT:-}}"
if [ -z "$PROJECT" ] && [ -n "${WORKSPACE_FOLDER_PATHS:-}" ]; then
  PROJECT="${WORKSPACE_FOLDER_PATHS%%,*}"
fi
if [ -z "$PROJECT" ] && [ -n "${PWD:-}" ] && [ -d "$PWD/.git" ]; then
  PROJECT="$PWD"
fi

if [ -n "$PROJECT" ] && [ -d "$PROJECT" ]; then
  export GRAPHIFY_PROJECT="$PROJECT"
  cd "$PROJECT"
else
  echo "WARN: no workspace project path for Graphify; using cwd=$(pwd)" >&2
fi

exec "$PYTHON_BIN" "$SERVER"
