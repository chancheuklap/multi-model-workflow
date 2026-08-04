#!/usr/bin/env bash
# skills 源占位符物化到 skills-pi / skills-claude-code
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
MMW="$ROOT/cli/mmw"

pass_n=0
fail_n=0
check() {
  local name=$1
  shift
  if "$@"; then
    echo "  过  $name"
    pass_n=$((pass_n + 1))
  else
    echo "  失败  $name"
    fail_n=$((fail_n + 1))
  fi
}

check "materialize all" python3 "$ROOT/cli/lib/materialize_skills.py" --host all
check "check pi" python3 "$ROOT/cli/lib/materialize_skills.py" --host pi --check
check "check claude-code" python3 "$ROOT/cli/lib/materialize_skills.py" --host claude-code --check
check "mmw skills CLI check" "$MMW" skills materialize --host pi --check
check "mmw skills CLI check cc" "$MMW" skills materialize --host claude-code --check

pi_impl="$ROOT/skills-pi/mmw-implement/SKILL.md"
cc_impl="$ROOT/skills-claude-code/mmw-implement/SKILL.md"
check "pi has subagent" grep -q 'subagent({' "$pi_impl"
check "pi no dispatch" bash -c "! grep -q 'mmw dispatch' \"$pi_impl\""
check "cc has dispatch" grep -q 'mmw dispatch worker' "$cc_impl"
check "cc no subagent call" bash -c "! grep -q 'subagent({' \"$cc_impl\""
check "no dispatching skill on pi" test ! -e "$ROOT/skills-pi/mmw-dispatching-agents"
check "no dispatching skill on cc" test ! -e "$ROOT/skills-claude-code/mmw-dispatching-agents"

echo
echo "过 ${pass_n}，失败 ${fail_n}"
exit "${fail_n}"
