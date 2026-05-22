#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

pass=0
fail=0

echo "=== test_resolvers.sh ==="

for resolver in "$BUILD_DIR"/resolvers/*.sh; do
  name="$(basename "$resolver" .sh)"

  # Check resolver is executable
  if [[ ! -x "$resolver" ]]; then
    echo "  FAIL: $name resolver not executable"
    fail=$((fail + 1))
    continue
  fi

  # Check corresponding template exists
  tmpl="$BUILD_DIR/templates/${name}.md.tmpl"
  if [[ ! -f "$tmpl" ]]; then
    echo "  FAIL: $name template missing ($tmpl)"
    fail=$((fail + 1))
    continue
  fi

  # Run resolver and verify it outputs something
  output=$(bash "$resolver" "$BUILD_DIR/templates" "$name" "" 2>&1) || {
    echo "  FAIL: $name resolver exit non-zero"
    fail=$((fail + 1))
    continue
  }

  if [[ -z "$output" ]]; then
    echo "  FAIL: $name resolver output is empty"
    fail=$((fail + 1))
    continue
  fi

  # Verify resolver outputs template content
  expected=$(cat "$tmpl")
  if [[ "$output" == "$expected" ]]; then
    echo "  PASS: $name (output matches template)"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (output differs from template)"
    fail=$((fail + 1))
  fi
done

# Verify total resolver count
count=$(ls -1 "$BUILD_DIR"/resolvers/*.sh | wc -l | tr -d ' ')
if [[ "$count" -ge 9 ]]; then
  echo "  PASS: $count resolvers found (>= 9)"
  pass=$((pass + 1))
else
  echo "  FAIL: only $count resolvers found (expected >= 9)"
  fail=$((fail + 1))
fi

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
