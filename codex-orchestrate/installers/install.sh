#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_DIR/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
MARKETPLACE_NAME="multi-model-workflow"
PLUGIN_NAME="codex-orchestrate"
APPLY=false

usage() {
  cat <<USAGE
Usage: install.sh --user [--dry-run|--apply]

Installs $PLUGIN_NAME from the repo-local marketplace and syncs managed custom agents.
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) shift ;;
    --dry-run) APPLY=false; shift ;;
    --apply) APPLY=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "install: missing required command: $1" >&2; exit 2; }
}

run() {
  if [[ "$APPLY" == "true" ]]; then
    "$@"
  else
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  fi
}

validate_source() {
  require jq
  require python3
  require codex
  [[ -f "$PLUGIN_DIR/.codex-plugin/plugin.json" ]] || { echo "install: missing plugin manifest" >&2; exit 2; }
  local validator="$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py"
  if python3 -c 'import yaml' >/dev/null 2>&1; then
    python3 "$validator" "$PLUGIN_DIR"
  elif command -v uv >/dev/null 2>&1; then
    uv run --with pyyaml --no-project python "$validator" "$PLUGIN_DIR"
  else
    echo "install: PyYAML is required for plugin validation; install PyYAML or uv" >&2
    exit 2
  fi
}

check_features() {
  local required=(plugins plugin_hooks hooks multi_agent unified_exec)
  local features
  features="$(codex features list)"
  for feature in "${required[@]}"; do
    if ! awk -v f="$feature" '$1 == f && $3 == "true" { found=1 } END { exit(found ? 0 : 1) }' <<< "$features"; then
      echo "install: required Codex feature not enabled: $feature" >&2
      exit 2
    fi
  done
}

marketplace_registered() {
  codex plugin marketplace list | awk -v n="$MARKETPLACE_NAME" -v r="$REPO_ROOT" '$1 == n && $2 == r { found=1 } END { exit(found ? 0 : 1) }'
}

any_marketplace_registered() {
  codex plugin marketplace list | awk -v n="$MARKETPLACE_NAME" '$1 == n { found=1 } END { exit(found ? 0 : 1) }'
}

sync_agents() {
  run mkdir -p "$CODEX_HOME/agents"
  for file in "$PLUGIN_DIR"/agents/*.toml; do
    [[ -f "$file" ]] || continue
    run cp "$file" "$CODEX_HOME/agents/$(basename "$file")"
  done
}

sync_agent_config() {
  run python3 "$SCRIPT_DIR/sync-agent-config.py" install \
    --config-file "$CODEX_HOME/config.toml" \
    --source-agents-dir "$PLUGIN_DIR/agents" \
    --target-agents-dir "$CODEX_HOME/agents"
}

validate_source
check_features

if marketplace_registered; then
  echo "install: marketplace already registered: $MARKETPLACE_NAME -> $REPO_ROOT"
elif any_marketplace_registered; then
  echo "install: marketplace already registered: $MARKETPLACE_NAME"
elif [[ -f "$REPO_ROOT/.agents/plugins/marketplace.json" ]]; then
  run codex plugin marketplace add "$REPO_ROOT"
else
  [[ "$APPLY" == "false" ]] || { echo "install: repo marketplace not found from $REPO_ROOT" >&2; exit 2; }
  echo "install: repo marketplace not found in dry-run context; skipping marketplace add"
fi

run codex plugin add "${PLUGIN_NAME}@${MARKETPLACE_NAME}"
sync_agents
sync_agent_config

if [[ "$APPLY" == "true" ]]; then
  "$SCRIPT_DIR/verify-runtime-parity.sh" --user
  echo "install: runtime parity passed"
  echo "install: open a new Codex session, review/trust the plugin hook definitions when prompted, then confirm SessionStart reports codex-orchestrate runtime active"
else
  echo "install: dry run complete"
fi
