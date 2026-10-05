#!/usr/bin/env bash
# 把一份装配出来的 release.ps1 送到构建机，让 PowerShell 自己解析一遍。
#
#   bash tests/check-generated-powershell.sh <构建机 SSH Host> <release.ps1> [更多 .ps1 ...]
#
# Mac 上没有 PowerShell 解析器，所以这一条验不进 run.sh。构建机就是脚本真正要跑的地方，
# 拿它来验比装一个本地解析器更实。语法错在这里发现是几秒，在构建机上跑到那一步才发现是几十分钟。

set -euo pipefail

[ $# -ge 2 ] || { echo "用法：check-generated-powershell.sh <host> <release.ps1> [...]" >&2; exit 2; }

host="$1"
shift
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
remote="D:/mmw-ps-syntax-check"

ssh "$host" "powershell -NoProfile -NonInteractive -Command \"New-Item -ItemType Directory -Force -Path '$remote' | Out-Null\"" >/dev/null
scp -q "$HERE/ps-syntax-check.ps1" "$host:$remote/check.ps1"

rc=0
for script in "$@"; do
  name="$(basename "$script")"
  scp -q "$script" "$host:$remote/$name"
  out="$(ssh "$host" "powershell -NoProfile -NonInteractive -File $remote/check.ps1 -Path $remote/$name" 2>&1 | LC_ALL=C tr -d '\r')"
  if [ "$out" = "OK" ]; then
    echo "$name 解析通过"
  else
    echo "$name 解析失败：" >&2
    echo "$out" >&2
    rc=1
  fi
done
exit "$rc"
