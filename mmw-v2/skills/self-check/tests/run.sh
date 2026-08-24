#!/usr/bin/env bash
# 关卡格式自证：一条会诚实失败的关卡，一条断言恒真的坏关卡。
# 判定规则与 to-tickets 的 <gate-rules> 相同：退出码 0 且输出含 EXPECT 标记才算过。
# 两条的判定结果都要与 reference/gate-examples.md 记录的一致，否则本脚本非零退出。
#
#   bash mmw-v2/skills/self-check/tests/run.sh
set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

# 返回 PASS / FAIL；参数：CHECK 命令、EXPECT 标记
judge() {
  local check="$1" expect="$2" out rc marker
  out="$(bash -c "$check" 2>&1)"; rc=$?
  if printf '%s\n' "$out" | grep -qF -- "$expect"; then marker=present; else marker=absent; fi
  if [ "$rc" -eq 0 ] && [ "$marker" = present ]; then verdict=PASS; else verdict=FAIL; fi
  printf 'exit=%s marker=%s -> %s' "$rc" "$marker" "$verdict"
}

rc=0
honest="$(judge 'test -f MISSING-ON-PURPOSE.txt && echo GATE_OK' GATE_OK)"
echo "honest gate: $honest   (expected FAIL)"
case "$honest" in *"-> FAIL") ;; *) rc=1 ;; esac

broken="$(judge 'echo GATE_OK' GATE_OK)"
echo "broken gate: $broken  (expected PASS — and that is the defect the format cannot catch)"
case "$broken" in *"-> PASS") ;; *) rc=1 ;; esac

if [ "$rc" -eq 0 ]; then echo "GATE-SELFTEST OK"; else echo "GATE-SELFTEST FAILED: a verdict differs from reference/gate-examples.md" >&2; fi
exit "$rc"
