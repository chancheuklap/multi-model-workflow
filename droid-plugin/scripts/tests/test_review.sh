#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEW="$SCRIPT_DIR/../review.sh"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git -C "$TMP" init -q
git -C "$TMP" config user.email test@example.com
git -C "$TMP" config user.name Test
echo base > "$TMP/a"
git -C "$TMP" add a
git -C "$TMP" commit -qm base
mkdir -p "$TMP/.factory/multi-model-workflow"

write_task() {
  jq -n --arg s "$1" --arg base "$(git -C "$TMP" rev-parse HEAD)" \
    '{slug:"demo",scenario:$s,status:"active",phase:"build",base_commit:$base}' \
    > "$TMP/.factory/multi-model-workflow/task.json"
}

write_task develop
(cd "$TMP" && bash "$REVIEW" start --stage design --source docs/design/demo.md >/dev/null)
BRIEF="$TMP/.factory/multi-model-workflow/review-brief.md"
grep -q reviewer-design-a "$BRIEF" && grep -q reviewer-design-b "$BRIEF" && ok "design reviewers" || no "design reviewers"
grep -q 'Task' "$BRIEF" && ok "Task dispatch" || no "Task dispatch"

(cd "$TMP" && bash "$REVIEW" start --stage plan --source docs/plans/demo >/dev/null)
grep -q reviewer-plan-a "$BRIEF" && grep -q reviewer-plan-b "$BRIEF" && ok "plan reviewers" || no "plan reviewers"

write_task small-change
(cd "$TMP" && bash "$REVIEW" start --stage final --source HEAD >/dev/null)
grep -q 'tier=1' "$BRIEF" && grep -q reviewer-final-a "$BRIEF" \
  && grep -q '覆盖两条基线' "$BRIEF" && ok "small final tier one" || no "tier one"

write_task develop
mkdir -p "$TMP/docs/plans/demo"
printf '# plan\nComplexity: standard\n' > "$TMP/docs/plans/demo/001.md"
(cd "$TMP" && bash "$REVIEW" start --stage final --source HEAD >/dev/null)
grep -q 'tier=2' "$BRIEF" && grep -q reviewer-final-a "$BRIEF" && grep -q reviewer-final-b "$BRIEF" &&
  ok "develop final cross-model tier" || no "develop final tier"

printf '# plan\nComplexity: capable\n' > "$TMP/docs/plans/demo/001.md"
(cd "$TMP" && bash "$REVIEW" start --stage final --source HEAD >/dev/null)
grep -q 'tier=4' "$BRIEF" \
  && [ "$(grep -c 'reviewer-final-a' "$BRIEF")" -ge 2 ] \
  && [ "$(grep -c 'reviewer-final-b' "$BRIEF")" -ge 2 ] \
  && grep -q '只负责指定基线' "$BRIEF" \
  && ok "capable final tier four dynamic routes" || no "tier four"

(cd "$TMP" && bash "$REVIEW" start --stage merge-impl --source merge-brief.md >/dev/null)
grep -q '七角度' "$BRIEF" && grep -q reviewer-final-a "$BRIEF" \
  && grep -q reviewer-final-b "$BRIEF" && ok "merge integration review" || no "merge review"

DESIGN="$TMP/design.md"
printf '# D\n## Cross-Plan Contract Anchors\n\n无跨计划共享合同\n' > "$DESIGN"
OUT="$(cd "$TMP" && bash "$REVIEW" start --stage plan-impl --source "$DESIGN")"
echo "$OUT" | grep -q '已自动 cover' && ok "empty contract auto covered" || no "contract gate"

exit "$fail"
