#!/usr/bin/env bash
# Neutral second-model adapter contract.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ADAPTER="$SCRIPT_DIR/../second-review.sh"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/repo"
git -C "$TMP/repo" init -q
git -C "$TMP/repo" config user.email test@example.com
git -C "$TMP/repo" config user.name Test
printf 'seed\n' >"$TMP/repo/seed.txt"
git -C "$TMP/repo" add seed.txt
git -C "$TMP/repo" commit -qm seed

printf '#!/usr/bin/env bash\ninput="$(cat)"\nprintf "Verdict: pass\\nEvidence: %%s\\n" "$input"\n' >"$TMP/pass"
printf '#!/usr/bin/env bash\ncat >/dev/null\nexit 7\n' >"$TMP/fail"
printf '#!/usr/bin/env bash\ncat >/dev/null\n' >"$TMP/empty"
printf '#!/usr/bin/env bash\ncat >/dev/null\nsleep 5\nprintf late\n' >"$TMP/slow"
chmod +x "$TMP/pass" "$TMP/fail" "$TMP/empty" "$TMP/slow"

if printf 'same rendered prompt' \
  | MMW_SECOND_REVIEW_CMD="$TMP/pass" bash "$ADAPTER" --worktree "$TMP/repo" \
  | grep -q 'Evidence: same rendered prompt'; then
  ok "adapter passes stdin to configured executable and returns stdout"
else
  no "adapter stdin/stdout contract"
fi

if MMW_SECOND_REVIEW_CMD='' bash "$ADAPTER" --worktree "$TMP/repo" </dev/null >/dev/null 2>&1; then
  no "missing second-model command must fail"
else
  ok "missing command fails loud"
fi

if printf prompt | MMW_SECOND_REVIEW_CMD="$TMP/fail" \
  bash "$ADAPTER" --worktree "$TMP/repo" >/dev/null 2>&1; then
  no "nonzero provider exit must fail"
else
  ok "nonzero provider exit fails loud"
fi

if printf prompt | MMW_SECOND_REVIEW_CMD="$TMP/empty" \
  bash "$ADAPTER" --worktree "$TMP/repo" >/dev/null 2>&1; then
  no "empty provider output must fail"
else
  ok "empty provider output fails loud"
fi

if printf prompt | MMW_SECOND_REVIEW_CMD="$TMP/slow" MMW_SECOND_REVIEW_TIMEOUT_SECONDS=1 \
  bash "$ADAPTER" --worktree "$TMP/repo" >/dev/null 2>&1; then
  no "provider timeout must fail"
else
  ok "provider timeout fails loud"
fi

if rg -ni 'claude|gemini|gpt|codex exec|fallback' "$ADAPTER" >/dev/null; then
  no "adapter core must not name a model vendor or fallback"
else
  ok "adapter core is vendor-neutral"
fi

exit "$fail"
