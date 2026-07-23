#!/usr/bin/env bash
# Codex review matrix, prompt parity, prototype handoff and read-only boundary.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEW="$SCRIPT_DIR/../review.sh"
STATE=".codex/multi-model-workflow"
pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
git config user.email test@example.com
git config user.name Test
printf 'seed\n' >seed.txt
git add seed.txt
git commit -qm seed

printf '#!/usr/bin/env bash\ncat\n' >"$TMP/second"
chmod +x "$TMP/second"
export MMW_SECOND_REVIEW_CMD="$TMP/second"

DESIGN_ROOT="docs/design/demo"
mkdir -p "$STATE" "$DESIGN_ROOT/prototype" docs/plans/demo docs/reviews
printf '# design\n' >"$DESIGN_ROOT/demo.md"
printf '# iterations\n' >"$DESIGN_ROOT/prototype/README.md"
printf 'selected\n' >"$DESIGN_ROOT/prototype/selected.py"
printf 'rejected\n' >"$DESIGN_ROOT/prototype/rejected.py"
printf '# plan\n' >docs/plans/demo/001.md
cat >"$STATE/task.json" <<JSON
{"scenario":"develop","slug":"demo","base_commit":"$(git rev-parse HEAD)","docs":{"design":"$DESIGN_ROOT"},"repair_count":0,"prototype":{"status":"accepted","kind":"logic","question":"q","iteration":1,"run_command":"run","artifacts":["$DESIGN_ROOT/prototype/selected.py","$DESIGN_ROOT/prototype/rejected.py"],"selected":["$DESIGN_ROOT/prototype/selected.py"],"log":"$DESIGN_ROOT/prototype/README.md","updated_at":"2026-07-24T00:00:00Z"}}
JSON

start_review() {
  bash "$REVIEW" start --stage "$1" --source "$2"
}

OUT="$(start_review design "$DESIGN_ROOT/demo.md")"
SLOTS="$STATE/review-slots.json"
BRIEF="$STATE/review-brief.md"
if echo "$OUT" | grep -q 'REVIEW_STARTED stage=design host=codex' \
  && jq -e 'length == 2 and all(.provider == "second")' "$SLOTS" >/dev/null; then
  ok "design uses two independent second-model slots"
else
  no "design matrix"
fi
jq -e '.[0].view == "轴A 设计内容" and .[1].view == "轴B 项目对齐"' "$SLOTS" >/dev/null \
  && ok "design keeps both review axes" || no "design axes"
DESIGN_PROMPT="$(jq -r '.[0].prompt_file' "$SLOTS")"
grep -q "$DESIGN_ROOT/prototype/README.md" "$DESIGN_PROMPT" \
  && grep -q "$DESIGN_ROOT/prototype/selected.py" "$DESIGN_PROMPT" \
  && ! grep -q "$DESIGN_ROOT/prototype/rejected.py" "$DESIGN_PROMPT" \
  && ok "design reviewers receive accepted README and selected only" || no "design prototype sources"

rm "$DESIGN_ROOT/prototype/selected.py"
rm -rf "$STATE/review-baseline.json" "$STATE/review-brief.md" "$STATE/review-slots.json" \
  "$STATE/review-prompts" "$STATE/review-results"
if start_review design "$DESIGN_ROOT/demo.md" >/dev/null 2>&1; then
  no "invalid accepted prototype must block design review"
elif [ -e "$STATE/review-baseline.json" ] || [ -e "$STATE/review-slots.json" ] \
  || [ -e "$STATE/review-prompts" ] || [ -e "$STATE/review-results" ]; then
  no "invalid accepted prototype must fail before review state"
else
  ok "invalid accepted prototype fails before review dispatch state"
fi
printf 'selected\n' >"$DESIGN_ROOT/prototype/selected.py"

OUT="$(start_review plan docs/plans/demo/)"
if echo "$OUT" | grep -q 'REVIEW_STARTED stage=plan host=codex' \
  && jq -e 'length == 2 and all(.provider == "second")' "$SLOTS" >/dev/null; then
  ok "plan uses two independent second-model slots"
else
  no "plan matrix"
fi

OUT="$(start_review final HEAD)"
if jq -e '
  length == 2
  and (map(select(.provider == "second")) | length == 1)
  and (map(select(.provider == "native")) | length == 1)
  and .[0].view != .[1].view
' "$SLOTS" >/dev/null; then
  ok "light develop final uses one native and one second-model reviewer"
else
  no "light develop final matrix"
fi

printf 'Complexity: capable\n' >>docs/plans/demo/001.md
OUT="$(start_review final HEAD)"
if jq -e '
  length == 4
  and (map(select(.provider == "second")) | length == 2)
  and (map(select(.provider == "native")) | length == 2)
' "$SLOTS" >/dev/null; then
  ok "full develop final uses two providers on both baselines"
else
  no "full develop final matrix"
fi
BASE1_NATIVE="$(jq -r '.[] | select(.provider=="native" and .view=="基线1 回归+意图+跨plan") | .prompt_file' "$SLOTS")"
BASE1_SECOND="$(jq -r '.[] | select(.provider=="second" and .view=="基线1 回归+意图+跨plan") | .prompt_file' "$SLOTS")"
cmp -s "$BASE1_NATIVE" "$BASE1_SECOND" \
  && ok "native and second provider receive the same rendered method" || no "provider prompt parity"

jq '.scenario="small-change"' "$STATE/task.json" >"$STATE/task.tmp"
mv "$STATE/task.tmp" "$STATE/task.json"
start_review final HEAD >/dev/null
jq -e 'length == 1 and .[0].provider == "second" and (.[] | .view | contains("基线1") and contains("基线2"))' "$SLOTS" >/dev/null \
  && ok "small-change final uses one second-model reviewer for both baselines" || no "small-change final matrix"
jq '.scenario="bug"' "$STATE/task.json" >"$STATE/task.tmp"
mv "$STATE/task.tmp" "$STATE/task.json"
start_review final HEAD >/dev/null
jq -e 'length == 1 and .[0].provider == "second"' "$SLOTS" >/dev/null \
  && ok "bug final uses one second-model reviewer" || no "bug final matrix"

start_review merge-impl HEAD >/dev/null
jq -e '
  length == 2
  and (map(select(.provider == "second")) | length == 1)
  and (map(select(.provider == "native")) | length == 1)
' "$SLOTS" >/dev/null \
  && ok "merge review uses one native and one second-model reviewer" || no "merge matrix"

if grep -q 'spawn_agent' "$BRIEF" \
  && grep -q 'second-review.sh' "$BRIEF" \
  && grep -q 'fork_turns="none"' "$BRIEF" \
  && ! grep -qE 'Claude|Gemini|codex exec|pi-subagents|agents-roster/reviewer' "$BRIEF"; then
  ok "brief only names native spawn and neutral adapter"
else
  no "Codex dispatch brief"
fi
if jq -e 'all(.task_name | test("^[a-z0-9_]+$"))' "$SLOTS" >/dev/null; then
  ok "all native task names satisfy Codex schema"
else
  no "native task names"
fi

printf '# d\n## Cross-Plan Contract Anchors\n<!-- empty -->\n' >docs/design/contracts.md
OUT="$(start_review plan-impl docs/design/contracts.md)"
echo "$OUT" | grep -q CONTRACT_GATE_EMPTY \
  && ok "empty contract gate remains mechanical" || no "empty contract gate"
printf '# d\n## Cross-Plan Contract Anchors\n| owner | consumer |\n| 001 | 002 |\n' >docs/design/contracts.md
OUT="$(start_review plan-impl docs/design/contracts.md)"
echo "$OUT" | grep -q 'REVIEW_STARTED stage=plan-impl host=codex' \
  && echo "$OUT" | grep -q '不派审者' \
  && ok "non-empty contract gate stays with coordinator" || no "contract gate"

jq '.scenario="develop" | .slug="demo" | .repair_count=1' "$STATE/task.json" >"$STATE/task.tmp"
mv "$STATE/task.tmp" "$STATE/task.json"
printf '# prior\n## verdict\nneeds-repair\n' >docs/reviews/demo-plan.md
start_review plan docs/plans/demo >/dev/null
grep -q '本轮是 re-review' "$BRIEF" && grep -q prior_trace "$BRIEF" \
  && ok "re-review carries prior trace and narrowed scope" || no "re-review brief"

BASELINE="$(jq -r .fingerprint "$STATE/review-baseline.json")"
bash "$REVIEW" clean-check --worktree "$TMP" --baseline "$BASELINE" >/dev/null \
  && ok "read-only review boundary passes unchanged worktree" || no "clean check"
printf 'changed\n' >>seed.txt
if bash "$REVIEW" clean-check --worktree "$TMP" --baseline "$BASELINE" >/dev/null 2>&1; then
  no "review worktree mutation must fail"
else
  ok "review worktree mutation fails closed"
fi

if MMW_SECOND_REVIEW_CMD='' bash "$REVIEW" start --stage plan --source docs/plans/demo >/dev/null 2>&1; then
  no "missing required second model must block review start"
else
  ok "missing required second model fails loud"
fi

if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then
  no "invalid stage must fail"
else
  ok "invalid stage fails loud"
fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
