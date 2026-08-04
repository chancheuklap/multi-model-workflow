#!/usr/bin/env bash
# skills 源占位符物化；--check 双向比对；不先写回工作树再自检。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
MMW="$ROOT/cli/mmw"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

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

# 隔离 out：不写回仓库 skills-pi
check "materialize pi to out" python3 "$ROOT/cli/lib/materialize_skills.py" --host pi --out "$OUT/pi"
check "materialize cc to out" python3 "$ROOT/cli/lib/materialize_skills.py" --host claude-code --out "$OUT/cc"
check "check pi out" python3 "$ROOT/cli/lib/materialize_skills.py" --host pi --out "$OUT/pi" --check
check "check cc out" python3 "$ROOT/cli/lib/materialize_skills.py" --host claude-code --out "$OUT/cc" --check

# 结构化：生成物无占位符；Pi implement 含 worker agent 名与 task 字段说明；Claude 含 dispatch worker 与 --task
python3 - "$OUT" <<'PY' || exit 1
import pathlib, sys
out = pathlib.Path(sys.argv[1])
pi = (out / "pi" / "mmw-implement" / "SKILL.md").read_text()
cc = (out / "cc" / "mmw-implement" / "SKILL.md").read_text()
assert "[[mmw-launch:" not in pi and "[[mmw-launch:" not in cc
assert "mmw-worker" in pi and "task:" in pi
assert "mmw dispatch" not in pi
assert "mmw dispatch worker" in cc and "--task" in cc
assert "subagent" not in cc or "subagent({" not in cc
print("structural ok")
PY
check "structural launch contract" true

# 多余文件必须让 --check 失败
mkdir -p "$OUT/pi/stale-skill"
echo x > "$OUT/pi/stale-skill/SKILL.md"
if python3 "$ROOT/cli/lib/materialize_skills.py" --host pi --out "$OUT/pi" --check >/dev/null 2>&1; then
  check "stale file fails check" false true
else
  check "stale file fails check" true true
fi

# 仓库内已提交产物与源一致（不先 materialize 写回）
check "repo pi --check" python3 "$ROOT/cli/lib/materialize_skills.py" --host pi --check
check "repo cc --check" python3 "$ROOT/cli/lib/materialize_skills.py" --host claude-code --check
check "mmw skills CLI check pi" "$MMW" skills materialize --host pi --check
check "mmw skills CLI check cc" "$MMW" skills materialize --host claude-code --check
check "no dispatching on repo pi" test ! -e "$ROOT/skills-pi/mmw-dispatching-agents"
check "no dispatching on repo cc" test ! -e "$ROOT/skills-claude-code/mmw-dispatching-agents"

echo
echo "过 ${pass_n}，失败 ${fail_n}"
exit "${fail_n}"
