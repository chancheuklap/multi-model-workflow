#!/usr/bin/env bash
# 承重句校验自证：仓库现状全绿；把一份权威位置里的短语删掉一个字就红。
set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
H="$(dirname "$HERE")"
REPO="$(cd "$H/../.." && pwd -P)"
rc=0
fail() { echo "失败：$1" >&2; rc=1; }

node "$H/check-invariants.js" || fail "仓库现状应全绿"

# 把清单引用的文件复制到临时根，改坏第一条短语的第一个权威位置。
T="$(mktemp -d)"
python3 - "$H/invariants.json" "$REPO" "$T" <<'PY' || fail "准备坏副本"
import json, os, shutil, sys
lst, repo, tmp = sys.argv[1:4]
inv = [e for e in json.load(open(lst))["invariants"] if e.get("phrase") and e.get("files")]
for e in inv:
    for f in e["files"]:
        dst = os.path.join(tmp, f); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(os.path.join(repo, f), dst)
e = inv[0]; f = os.path.join(tmp, e["files"][0])
s = open(f, encoding="utf-8").read(); p = e["phrase"]
assert p in s
# 全部出现都改坏：同一文件里若还有一处完整短语，校验就不会红——那是假绿，不是通过。
open(f, "w", encoding="utf-8").write(s.replace(p, p[:-1]))
print("改坏：", e["files"][0], "短语删掉末字：", p[:-1])
PY
if node "$H/check-invariants.js" --root "$T"; then fail "删一个字后应判红"; else echo "删一个字：红（预期）"; fi

exit "$rc"
