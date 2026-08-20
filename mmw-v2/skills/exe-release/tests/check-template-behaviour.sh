#!/usr/bin/env bash
# 把模板送到构建机，验它那几个守卫函数判得对不对（不是语法）。
#
#   bash tests/check-template-behaviour.sh <构建机 SSH Host>
#
# Mac 上没有 PowerShell，所以这一条跟 check-generated-powershell.sh 一样进不了 run.sh。
# 语法过了不代表判得对：源码泄漏扫描误报过两次，每次都挡下了一个本来没问题的发布。

set -euo pipefail

[ $# -ge 1 ] || { echo "用法：check-template-behaviour.sh <host>" >&2; exit 2; }

host="$1"
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
remote="D:/mmw-template-behaviour"

ssh "$host" "powershell -NoProfile -NonInteractive -Command \"New-Item -ItemType Directory -Force -Path '$remote' | Out-Null\"" >/dev/null
scp -q "$HERE/template-behaviour.ps1" "$host:$remote/check.ps1"
scp -q "$HERE/../scripts/release_templates/nuitka_electron.ps1.tmpl" "$host:$remote/template.tmpl"

ssh "$host" "powershell -NoProfile -NonInteractive -File $remote/check.ps1 -Template $remote/template.tmpl" 2>&1 | LC_ALL=C tr -d '\r'
