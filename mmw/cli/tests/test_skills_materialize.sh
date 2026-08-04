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
check "materialize codex to out" python3 "$ROOT/cli/lib/materialize_skills.py" --host codex --out "$OUT/codex"
check "check pi out" python3 "$ROOT/cli/lib/materialize_skills.py" --host pi --out "$OUT/pi" --check
check "check cc out" python3 "$ROOT/cli/lib/materialize_skills.py" --host claude-code --out "$OUT/cc" --check
check "check codex out" python3 "$ROOT/cli/lib/materialize_skills.py" --host codex --out "$OUT/codex" --check

# 结构化：生成物无占位符；Pi implement 含 worker agent 名与 task 字段说明；Claude 含 dispatch worker 与 --task
python3 - "$OUT" <<'PY' || exit 1
import pathlib, sys
out = pathlib.Path(sys.argv[1])
pi = (out / "pi" / "mmw-implement" / "SKILL.md").read_text()
cc = (out / "cc" / "mmw-implement" / "SKILL.md").read_text()
codex = (out / "codex" / "mmw-implement" / "SKILL.md").read_text()
assert all("[[mmw-launch:" not in text for text in (pi, cc, codex))
assert "mmw-worker" in pi and "task:" in pi
assert "mmw dispatch" not in pi
assert "mmw dispatch worker" in cc and "--task" in cc
assert "subagent" not in cc or "subagent({" not in cc
assert "`create_thread`" in codex and "`wait_threads`" in codex
assert "gpt-5.6-sol" in codex and "思考档设为 `high`" in codex
assert "mmw dispatch" not in codex and "codex exec" not in codex
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
check "repo codex --check" python3 "$ROOT/cli/lib/materialize_skills.py" --host codex --check
check "mmw skills CLI check pi" "$MMW" skills materialize --host pi --check
check "mmw skills CLI check cc" "$MMW" skills materialize --host claude-code --check
check "mmw skills CLI check codex" "$MMW" skills materialize --host codex --check
check "no dispatching on repo pi" test ! -e "$ROOT/skills-pi/mmw-dispatching-agents"
check "no dispatching on repo cc" test ! -e "$ROOT/skills-claude-code/mmw-dispatching-agents"
check "no dispatching on repo codex" test ! -e "$ROOT/skills-codex/mmw-dispatching-agents"

echo
echo "过 ${pass_n}，失败 ${fail_n}"
exit "${fail_n}"
