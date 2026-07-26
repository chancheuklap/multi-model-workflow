#!/usr/bin/env bash
# Cursor 插件 Serena MCP 启动器。
# 由 mcp.json 以 ${CURSOR_PLUGIN_ROOT}/scripts/serena-mcp.sh 调用；勿用相对 ./scripts（会被解析到工作区根）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTEXT="$ROOT/config/serena/cursor-readonly.yml"
[ -f "$CONTEXT" ] || { echo "ERROR: missing Serena context: $CONTEXT" >&2; exit 2; }

SERENA_BIN="${SERENA_BIN:-$(command -v serena 2>/dev/null || true)}"
[ -n "$SERENA_BIN" ] && [ -x "$SERENA_BIN" ] || {
  echo "ERROR: serena not on PATH. Install Serena and ensure \`serena\` is available to Cursor, or set SERENA_BIN." >&2
  exit 2
}

# 插件 MCP 的进程 cwd 往往是插件安装目录，不能靠 --project-from-cwd。
# 优先：mcp.json 注入的 SERENA_PROJECT=${workspaceFolder}，否则 WORKSPACE_FOLDER_PATHS。
PROJECT="${SERENA_PROJECT:-}"
if [ -z "$PROJECT" ] && [ -n "${WORKSPACE_FOLDER_PATHS:-}" ]; then
  PROJECT="${WORKSPACE_FOLDER_PATHS%%,*}"
fi
if [ -z "$PROJECT" ] && [ -n "${PWD:-}" ] && [ -d "$PWD/.git" ]; then
  PROJECT="$PWD"
fi

ARGS=(
  start-mcp-server
  --context "$CONTEXT"
  --enable-web-dashboard false
  --open-web-dashboard false
  --enable-gui-log-window false
)

if [ -n "$PROJECT" ] && [ -d "$PROJECT" ]; then
  ARGS+=(--project "$PROJECT")
else
  echo "WARN: no workspace project path; falling back to --project-from-cwd (cwd=$(pwd))" >&2
  ARGS+=(--project-from-cwd)
fi

exec "$SERENA_BIN" "${ARGS[@]}"
