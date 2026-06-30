#!/usr/bin/env bash
# Unified route worker dispatch script — replaces validate-route-worker-dispatch.sh + record-route-worker-dispatch.sh.
# Subcommands: validate | record
# Usage:
#   dispatch-route-worker.sh validate --prompt-file PATH [--transport Agent|SendMessage]
#   dispatch-route-worker.sh record  --prompt-file PATH --agent-id AGENT_ID --agent-file PATH
set -euo pipefail

SUBCMD="${1:-}"
shift 2>/dev/null || true

case "$SUBCMD" in
  validate)
    # --- validate subcommand (from validate-route-worker-dispatch.sh) ---
    PROMPT_FILE=""
    TRANSPORT="Agent"

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
        --transport) TRANSPORT="${2:-}"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
      esac
    done

    [[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" ]] || { echo "Usage: dispatch-route-worker.sh validate --prompt-file PATH [--transport Agent|SendMessage]" >&2; exit 2; }
    [[ "$TRANSPORT" == "Agent" || "$TRANSPORT" == "SendMessage" ]] || { echo "Error: --transport must be Agent or SendMessage" >&2; exit 2; }

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    # shellcheck source=../hooks/lib/routes.sh
    source "$SCRIPT_DIR/../hooks/lib/routes.sh"
    ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

    RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
    PHASE=$(echo "$ENVELOPE" | jq -r '.phase // empty')
    AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role // empty')
    AGENT_ID=$(echo "$ENVELOPE" | jq -r '.agent_id // empty')
    PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
    REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round // 0')
    IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key // empty')

    case "$AGENT_ROLE" in
      pack-executor|complex-pack-executor) ;;
      *)
        echo "Error: route worker dispatch agent_role must be pack-executor or complex-pack-executor" >&2
        exit 2
        ;;
    esac

    # Route-worker phases are legal iff routes-v1.json[PHASE].dispatch_shape[PHASE]
    # == "route-worker". For route-worker routes the phase equals the route name
    # (e.g. bug-investigation route → bug-investigation phase).
    # Fail-open: manifest unreadable → fall back to the route-worker route whitelist.
    if routes_manifest_readable; then
      if [[ "$(routes_dispatch_shape "$PHASE" "$PHASE")" != "route-worker" ]]; then
        echo "Error: route worker dispatch phase must be a non-execution route-worker phase (routes-v1.json)" >&2
        exit 2
      fi
    else
      case "$PHASE" in
        bug-investigation|direct-repair|multi-pr-merge) ;;
        *)
          echo "Error: route worker dispatch phase must be a non-execution route phase" >&2
          exit 2
          ;;
      esac
    fi

    if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
      echo "Error: route worker dispatch requires run_id" >&2
      exit 2
    fi

    if [[ -n "$PACK_ID" && "$PACK_ID" != "null" ]]; then
      echo "Error: route worker dispatch must set pack_id to null; execution dispatch is plan-level (validate-plan-dispatch.sh)" >&2
      exit 2
    fi

    if [[ -z "$IDEMPOTENCY_KEY" || "$IDEMPOTENCY_KEY" == "null" ]]; then
      echo "Error: route worker dispatch requires idempotency_key" >&2
      exit 2
    fi

    if [[ "$TRANSPORT" == "SendMessage" ]]; then
      if [[ -z "$AGENT_ID" || "$AGENT_ID" == "null" ]]; then
        echo "Error: route worker repair must include original worker agent_id" >&2
        exit 2
      fi
      if [[ "$REPAIR_ROUND" -lt 1 ]] 2>/dev/null; then
        echo "Error: route worker repair must set repair_round >= 1" >&2
        exit 2
      fi
    else
      if [[ -n "$AGENT_ID" && "$AGENT_ID" != "null" ]]; then
        echo "Error: first route worker dispatch must set agent_id to null" >&2
        exit 2
      fi
    fi

    bash "$SCRIPT_DIR/state.sh" budget check --run-id "$RUN_ID" >/dev/null
    bash "$SCRIPT_DIR/state.sh" idempotency check --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY" >/dev/null

    echo "OK"
    ;;

  record)
    # --- record subcommand (from record-route-worker-dispatch.sh) ---
    PROMPT_FILE=""
    AGENT_ID=""
    AGENT_FILE=""

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
        --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
        --agent-file) AGENT_FILE="${2:-}"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
      esac
    done

    [[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" && -n "$AGENT_ID" && -n "$AGENT_FILE" ]] || {
      echo "Usage: dispatch-route-worker.sh record --prompt-file PATH --agent-id AGENT_ID --agent-file PATH" >&2
      exit 2
    }

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

    RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
    IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key // empty')
    PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')

    if [[ -z "$RUN_ID" || "$RUN_ID" == "null" || -z "$IDEMPOTENCY_KEY" || "$IDEMPOTENCY_KEY" == "null" ]]; then
      echo "Error: run_id and idempotency_key required" >&2
      exit 2
    fi

    if [[ -n "$PACK_ID" && "$PACK_ID" != "null" ]]; then
      echo "Error: route worker record must not receive an execution pack_id" >&2
      exit 2
    fi

    bash "$SCRIPT_DIR/state.sh" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY"
    mkdir -p "$(dirname "$AGENT_FILE")"
    printf '%s\n' "$AGENT_ID" > "$AGENT_FILE"

    echo "OK"
    ;;

  -h|--help|help)
    cat <<'HELP'
dispatch-route-worker.sh — Unified route worker dispatch (validate + record)

Subcommands:
  validate  Validate a route worker dispatch envelope before sending
  record    Record a successful dispatch after receiving agent_id

Usage:
  dispatch-route-worker.sh validate --prompt-file PATH [--transport Agent|SendMessage]
  dispatch-route-worker.sh record  --prompt-file PATH --agent-id AGENT_ID --agent-file PATH
HELP
    ;;

  *)
    echo "Usage: dispatch-route-worker.sh <validate|record> [options]" >&2
    echo "Run 'dispatch-route-worker.sh --help' for details." >&2
    exit 2
    ;;
esac
