#!/usr/bin/env bash
# Shared route-manifest reader for hooks (P2).
# Thin jq lookup against state-schema/routes-v1.json — avoids each consuming
# hook re-implementing the same jq query for dispatch_shape / commit_format.
# Sourced (not executed); callers must have set ROUTES_LIB_DIR or rely on the
# default resolution below.

# Resolve the manifest path once, relative to this lib file's location:
# hooks/lib/routes.sh -> ../../state-schema/routes-v1.json
_routes_manifest_path() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  echo "${d}/../../state-schema/routes-v1.json"
}

# routes_manifest_readable — succeed (0) iff the manifest exists and jq can parse it.
routes_manifest_readable() {
  local mf
  mf="$(_routes_manifest_path)"
  [[ -f "$mf" ]] && jq -e . "$mf" >/dev/null 2>&1
}

# routes_dispatch_shape <route> <phase>
# Echo the dispatch_shape value (e.g. "plan-level" / "route-worker") for the
# given route/phase, or empty string if the manifest is unreadable, the route
# is unknown, or the phase has no declared shape. Callers treat empty as
# "fail-open: fall back to the legacy literal".
routes_dispatch_shape() {
  local route="$1" phase="$2" mf
  mf="$(_routes_manifest_path)"
  [[ -f "$mf" ]] || { echo ""; return 0; }
  jq -r --arg r "$route" --arg p "$phase" \
    '.routes[$r].dispatch_shape[$p] // empty' "$mf" 2>/dev/null || echo ""
}

# routes_commit_format <route>
# Echo the route's commit_format value (e.g. "hotfix-unreviewed"), or empty
# string if unreadable / unknown / null. Empty = fail-open to legacy behavior.
routes_commit_format() {
  local route="$1" mf
  mf="$(_routes_manifest_path)"
  [[ -f "$mf" ]] || { echo ""; return 0; }
  jq -r --arg r "$route" \
    '.routes[$r].commit_format // empty' "$mf" 2>/dev/null || echo ""
}

# routes_review_required <route>
# Echo the route's review_required intents one per line (e.g. "baseline"), or
# empty if the manifest is unreadable / route unknown / field absent. This is the
# per-route review-gate intent whitelist (execution-bearing routes declare
# "baseline" → Plan Implementation Review pack-completion gate; route-worker
# routes declare []). Empty output = fail-open: caller falls back to the legacy
# intent literal.
routes_review_required() {
  local route="$1" mf
  mf="$(_routes_manifest_path)"
  [[ -f "$mf" ]] || { echo ""; return 0; }
  jq -r --arg r "$route" \
    '.routes[$r].review_required // [] | .[]' "$mf" 2>/dev/null || echo ""
}
