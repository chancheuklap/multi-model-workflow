#!/usr/bin/env bash
# 合同自检冒烟（跳过网络升级）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

export MMW_RETRIEVAL_SKIP_UPGRADE=1
export MMW_RETRIEVAL_PLUGIN_ROOT="$PLUGIN"
# shellcheck source=../lib/uv-tool-maintain.sh
source "$PLUGIN/scripts/lib/uv-tool-maintain.sh"

if mmw_maintain_graphify; then
  ok "graphify contract with skip-upgrade"
else
  no "graphify contract"
fi

if command -v serena >/dev/null 2>&1; then
  if mmw_maintain_serena; then
    ok "serena contract with skip-upgrade"
  else
    no "serena contract"
  fi
else
  ok "serena binary absent — skip live contract"
fi

# wrapper must live in skill scripts/
grep -q 'pi-local-extensions/extensions/graphify.ts' \
  "$PLUGIN/skills/graphify/scripts/graphify_mcp.py" \
  && ok "plugin ships custom graphify MCP wrapper" || no "wrapper missing"

# launcher must not start official serve; wrapper docstring may warn against it
! grep -nE 'exec graphify-mcp|python -m graphify\.serve' \
  "$PLUGIN/scripts/graphify-mcp.sh" >/dev/null 2>&1 \
  && grep -q 'skills/graphify/scripts/graphify_mcp.py' "$PLUGIN/scripts/graphify-mcp.sh" \
  && ok "launcher uses plugin wrapper only" || no "official serve leaked"

exit "$fail"
