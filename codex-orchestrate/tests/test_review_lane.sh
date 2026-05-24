#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

make_prompt() {
  local file="$1" phase="$2"
  cat > "$file" <<JSON
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "review-test",
  "phase": "$phase",
  "agent_role": "reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "review-test/$phase/r0",
  "disposition_refs": null,
  "review_intent": "baseline",
  "exception_code": null,
  "correlation_id": "review-test/$phase"
}
-->

Review fixture.
JSON
}

make_prompt "$TMP/design-review.md" "discovery"
make_prompt "$TMP/code-review.md" "execution"
make_prompt "$TMP/code-re-review.md" "execution"
perl -0pi -e 's/"review_intent": "baseline"/"review_intent": "targeted-re-review"/; s/"exception_code": null/"exception_code": "user_requested"/' "$TMP/code-re-review.md"

DOC_JOB="$(STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" submit --dry-run --prompt-file "$TMP/design-review.md" --result-file "$TMP/design-result.md")"
CODE_JOB="$(STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" submit --dry-run --prompt-file "$TMP/code-review.md" --result-file "$TMP/code-result.md")"
REREVIEW_JOB="$(STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" submit --dry-run --resume --prompt-file "$TMP/code-re-review.md" --result-file "$TMP/code-rereview-result.md")"

grep -q 'kind=document model=gpt-5.5 effort=xhigh' "$TMP/design-result.md"
grep -q 'kind=code model=gpt-5.4 effort=xhigh' "$TMP/code-result.md"
grep -q 'resume=true thread=dry-run-thread-' "$TMP/code-rereview-result.md"

[[ "$(STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" status --job-id "$DOC_JOB")" == "completed" ]]
STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" fetch --job-id "$CODE_JOB" | grep -q 'kind=code model=gpt-5.4'

jq -e '.review_kind == "document" and .model == "gpt-5.5" and .reasoning_effort == "xhigh"' "$TMP/state/review-jobs/${DOC_JOB}.json" >/dev/null
jq -e '.review_kind == "code" and .model == "gpt-5.4" and .reasoning_effort == "xhigh" and .thread_id != "" and .resume == false' "$TMP/state/review-jobs/${CODE_JOB}.json" >/dev/null
jq -e --arg base "$CODE_JOB" '.review_kind == "code" and .model == "gpt-5.4" and .reasoning_effort == "xhigh" and .resume == true and .resumed_from_job_id == $base' "$TMP/state/review-jobs/${REREVIEW_JOB}.json" >/dev/null

if STATE_BASE="$TMP/no-baseline" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" submit --dry-run --resume --prompt-file "$TMP/code-re-review.md" --result-file "$TMP/missing.md" >/dev/null 2>&1; then
  echo "expected --resume without baseline to fail" >&2
  exit 1
fi

if STATE_BASE="$TMP/state" bash "$PLUGIN_DIR/scripts/review/review-lane.sh" submit --dry-run --lane claude --prompt-file "$TMP/code-review.md" --result-file "$TMP/claude.md" >/dev/null 2>&1; then
  echo "expected Claude review lane to be unsupported" >&2
  exit 1
fi
