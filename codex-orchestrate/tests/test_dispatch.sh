#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/state.sh" init --run-id dispatch-test --slug dispatch-test --route formal >/dev/null
STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/state.sh" budget initialize --run-id dispatch-test --plan-count 1

cat > "$TMP/envelope.json" <<'JSON'
{
  "protocol_version": "1",
  "run_id": "dispatch-test",
  "phase": "execution",
  "agent_role": "pack_executor",
  "agent_id": null,
  "pack_id": "1.1",
  "repair_round": 0,
  "idempotency_key": "dispatch-test/1.1/r0",
  "disposition_refs": null,
  "review_intent": null,
  "exception_code": null,
  "correlation_id": "dispatch-test/1.1"
}
JSON

STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/dispatch/dispatch-gateway.sh" --dry-run --envelope-file "$TMP/envelope.json" \
  | jq -e '.status == "validated" and .agent_role == "pack_executor" and .pack_id == "1.1"' >/dev/null

if STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/dispatch/dispatch-gateway.sh" --dry-run --envelope-file "$TMP/envelope.json" >/dev/null 2>&1; then
  echo "duplicate dispatch idempotency was not blocked" >&2
  exit 1
fi

cat > "$TMP/pack-brief.md" <<'MD'
Pack: 1.1 dry-run
Goal behavior: prove worktree-exec injects agent config
Implementation tasks:
  - dry-run only
Owned files:
  - Test: none
Acceptance criteria:
  - [ ] dry-run job records agent runtime fields
Verification commands:
  - true
Risk flags: normal
State directory: /tmp/state
Return contract:
  ### Verdict
  pass
MD

cat > "$TMP/state/execution-state-dispatch-test.json" <<'JSON'
{
  "run_id": "dispatch-test",
  "plans": {
    "001": {
      "packs": {
        "1.1": {
          "status": "pending",
          "agent_id": null,
          "worker_backend": null,
          "worker_thread_id": null,
          "worker_job_file": null,
          "commit_sha": null,
          "worker_verdict": null,
          "repair_round": 0
        }
      }
    }
  }
}
JSON

JOB_FILE="$(STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/dispatch/worktree-exec.sh" \
  --dry-run \
  --worktree-root "$TMP/worktrees" \
  --envelope-file "$TMP/envelope.json" \
  --pack-brief "$TMP/pack-brief.md")"

jq -e '.model == "gpt-5.3-codex" and .reasoning_effort == "xhigh" and .sandbox_mode == "workspace-write" and (.agent_config | endswith("agents/pack_executor.toml"))' "$JOB_FILE" >/dev/null
jq -e '.thread_id | startswith("dry-run-thread-")' "$JOB_FILE" >/dev/null
head -1 "$(jq -r '.prompt_file' "$JOB_FILE")" | grep -q '<!-- DISPATCH_ENVELOPE'
grep -q '# Agent Runtime Contract' "$(jq -r '.prompt_file' "$JOB_FILE")"
jq -e '.plans["001"].packs["1.1"].worker_backend == "codex-exec" and (.plans["001"].packs["1.1"].worker_thread_id | startswith("dry-run-thread-")) and (.plans["001"].packs["1.1"].worker_job_file | length > 0) and (.plans["001"].packs["1.1"].agent_id | startswith("codex-exec:dry-run-thread-"))' "$TMP/state/execution-state-dispatch-test.json" >/dev/null

STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/state.sh" disposition append \
  --run-id dispatch-test \
  --review-round 1 \
  --finding-id F1 \
  --disposition accepted \
  --confidence 9 \
  --severity H \
  --evidence "fixture accepted finding" \
  --path "tests/test_dispatch.sh:1"

cat > "$TMP/repair-prompt.md" <<'MD'
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "dispatch-test",
  "phase": "execution",
  "agent_role": "pack_executor",
  "agent_id": "codex-exec:dry-run",
  "pack_id": "1.1",
  "repair_round": 1,
  "idempotency_key": "dispatch-test/1.1/r1",
  "disposition_refs": ["F1"],
  "review_intent": null,
  "exception_code": null,
  "correlation_id": "dispatch-test/1.1"
}
-->

Repair finding F1.
MD

RESUMED_JOB="$(STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/dispatch/worktree-resume.sh" \
  --dry-run \
  --job-file "$JOB_FILE" \
  --repair-prompt "$TMP/repair-prompt.md")"

[[ "$RESUMED_JOB" == "$JOB_FILE" ]]
jq -e '.resume_jobs | length == 1' "$JOB_FILE" >/dev/null
jq -e '.plans["001"].packs["1.1"].worker_backend == "codex-exec" and (.plans["001"].packs["1.1"].worker_thread_id | startswith("dry-run-thread-"))' "$TMP/state/execution-state-dispatch-test.json" >/dev/null
