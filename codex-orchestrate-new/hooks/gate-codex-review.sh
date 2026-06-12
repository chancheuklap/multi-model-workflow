#!/usr/bin/env bash
# PreToolUse Bash hook for Codex review gates.
#
# Review dispatch in the Codex runtime is explicit:
#   1. Coordinator writes a prompt file with DISPATCH_ENVELOPE.
#   2. Coordinator runs dispatch-review.sh validate.
#   3. Coordinator calls spawn_agent(agent_type="codex_reviewer").
#   4. Coordinator records the returned agent id with dispatch-review.sh record.
#
# Codex hook payloads do not reliably include the full future subagent prompt at
# SubagentStart, so prompt validation belongs in dispatch-review.sh. This hook is
# a safety reminder only and never tries to infer review state from external job
# command text.
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/payload.sh
source "$SCRIPT_DIR/lib/payload.sh"

COMMAND="$(mmw_payload_command "$INPUT")"
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

if echo "$COMMAND" | grep -qE 'dispatch-review\.sh[[:space:]]+validate'; then
  exit 0
fi

exit 0
