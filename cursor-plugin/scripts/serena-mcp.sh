#!/usr/bin/env bash
# Cursor 插件 Serena MCP 启动器（MMW 一体化检索包）。
# 启动前：检测 serena-agent 是否有新版本 → 有才 upgrade → 合同自检（失败回滚）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/uv-tool-maintain.sh
source "$ROOT/scripts/lib/uv-tool-maintain.sh"
MMW_RETRIEVAL_PLUGIN_ROOT="$ROOT"
mmw_maintain_serena

CONTEXT="$ROOT/config/serena/cursor-readonly.yml"
[ -f "$CONTEXT" ] || { echo "ERROR: missing Serena context: $CONTEXT" >&2; exit 2; }

SERENA_BIN="${SERENA_BIN:-$(command -v serena 2>/dev/null || true)}"
[ -n "$SERENA_BIN" ] && [ -x "$SERENA_BIN" ] || {
  echo "ERROR: serena not on PATH after maintain. Install uv and retry, or set SERENA_BIN." >&2
  exit 2
}

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
