#!/usr/bin/env bash
# prototype 共同行为用三份实体 copy；任一镜像漏同步立即失败。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

files=(
  scripts/prototype.sh
  scripts/lib/prototype-state.sh
  scripts/tests/test_prototype.sh
  skills/orchestrate/references/design/prototype-mockup.md
  skills/orchestrate/references/design/evidence-campaign.md
)

for rel in "${files[@]}"; do
  base="$ROOT/plugin/$rel"
  [ -f "$base" ] && [ ! -L "$base" ] || { echo "FAIL: plugin/$rel 必须是实体文件" >&2; exit 1; }
  for mirror in pi-plugin droid-plugin; do
    target="$ROOT/$mirror/$rel"
    [ -f "$target" ] && [ ! -L "$target" ] || { echo "FAIL: $mirror/$rel 必须是实体文件" >&2; exit 1; }
    cmp -s "$base" "$target" || { echo "FAIL: $rel 在 plugin 与 $mirror 之间漂移" >&2; exit 1; }
  done
done

echo "PASS: prototype 共同行为三镜像实体副本一致"
