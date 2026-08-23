#!/usr/bin/env bash
# check.sh: each of the six checks passes on a good repo and fails on exactly the broken one.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECK="$SCRIPT_DIR/../scripts/check.sh"
pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

SENTENCE='Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.'

# good_repo <dir>: a repo that passes every check
good_repo() {
  local d="$1"
  mkdir -p "$d/src/api" "$d/docs"
  cat > "$d/AGENTS.md" <<EOT
# AGENTS.md

An API for a shop. Runs in production.

## Commands

| Command | What it does |
|---|---|
| \`make seed\` | seed a local database |

## References

| Need | File |
|---|---|
| Architecture | \`docs/architecture.md\` |

<important if="you are adding or modifying API routes">
- Routes live in \`src/api/\`.
</important>

$SENTENCE
EOT
  printf '@AGENTS.md\n' > "$d/CLAUDE.md"
  printf '# docs\n' > "$d/docs/architecture.md"
  cat > "$d/src/api/AGENTS.md" <<'EOT'
# src/api

Owns HTTP routes. Does not own persistence.

- Validate input with the shared schema in `../schema.py`.
EOT
  printf '@AGENTS.md\n' > "$d/src/api/CLAUDE.md"
  printf 'x\n' > "$d/src/schema.py"
}

expect_pass() {  # label dir
  local out
  if out="$(bash "$CHECK" "$2" 2>&1)"; then ok "$1"; else no "$1 ($out)"; fi
}
expect_fail() {  # label dir pattern
  local out
  if out="$(bash "$CHECK" "$2" 2>&1)"; then no "$1 (passed, expected failure)"
  elif grep -q "$3" <<<"$out"; then ok "$1"
  else no "$1 (failed for another reason: $out)"; fi
}

echo "=== test_check.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

d="$TMP/good"; good_repo "$d"; expect_pass "good repo passes" "$d"

d="$TMP/long"; good_repo "$d"; for i in $(seq 1 151); do echo "- line $i" >> "$d/AGENTS.md"; done
expect_fail "root over 150 lines" "$d" "limit is 150"

d="$TMP/nobridge"; good_repo "$d"; rm "$d/src/api/CLAUDE.md"
expect_fail "missing CLAUDE.md bridge" "$d" "src/api/CLAUDE.md: missing"

d="$TMP/badbridge"; good_repo "$d"; printf '@AGENTS.md\nextra text\n' > "$d/CLAUDE.md"
expect_fail "bridge with non-import line" "$d" "CLAUDE.md: line 2"

d="$TMP/bridge-noagents"; good_repo "$d"; printf '@PROJECT.md\n' > "$d/CLAUDE.md"
expect_fail "bridge without @AGENTS.md" "$d" "CLAUDE.md: no @AGENTS.md"

d="$TMP/multi-import"; good_repo "$d"; printf '@PROJECT.md\n@AGENTS.md\n' > "$d/CLAUDE.md"; printf '# p\n' > "$d/PROJECT.md"
expect_pass "bridge with several imports passes" "$d"

d="$TMP/deadpath"; good_repo "$d"; rm "$d/docs/architecture.md"
expect_fail "dead path in backticks" "$d" "docs/architecture.md"

d="$TMP/deadrel"; good_repo "$d"; rm "$d/src/schema.py"
expect_fail "dead relative path in nested file" "$d" "schema.py"

d="$TMP/cmdok"; good_repo "$d"; echo '- Run `pnpm vitest run src/api/x.test.ts` per file.' >> "$d/AGENTS.md"
expect_pass "backticked command with spaces is not a path" "$d"

d="$TMP/unclosed"; good_repo "$d"; echo '<important if="you touch tests">' >> "$d/AGENTS.md"
expect_fail "unclosed important tag" "$d" "important"


d="$TMP/nosentence"; good_repo "$d"; grep -v 'subdirectory' "$d/AGENTS.md" > "$d/A" && mv "$d/A" "$d/AGENTS.md"
expect_fail "missing subdirectory sentence" "$d" "subdirectory sentence"

d="$TMP/override"; good_repo "$d"; printf 'x\n' > "$d/src/AGENTS.override.md"
expect_fail "leftover AGENTS.override.md" "$d" "AGENTS.override.md"

d="$TMP/noroot"; mkdir -p "$d"
expect_fail "no root AGENTS.md" "$d" "AGENTS.md: missing"

d="$TMP/ignored"; good_repo "$d"; mkdir -p "$d/node_modules/x" "$d/.worktrees/y"; printf 'x\n' > "$d/node_modules/x/AGENTS.override.md"; printf 'x\n' > "$d/.worktrees/y/AGENTS.override.md"
expect_pass "node_modules and .worktrees are skipped" "$d"

echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]
