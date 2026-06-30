#!/usr/bin/env bash
# build.sh —— 极简多文档构建:把共用片段注入各路径 reference 的锚点区。
#
#   每条路径的 reference(references/scenario/*.md)里写锚点:
#     <!-- BEGIN: worktree-setup -->
#     ...(构建时由 build/fragments/worktree-setup.md 填充,手改无效)...
#     <!-- END: worktree-setup -->
#   改共用步骤 → 只改 build/fragments/<name>.md → 跑 --apply 覆盖所有路径。
#   重复内容只此一份源;各 reference 读者看到的是各自一份干净完整文档。
#
#   build.sh --check    干跑:生成 vs 现状有差异就报 DRIFT 并 exit 1
#   build.sh --apply    把片段写进各 reference 锚点区
set -euo pipefail

BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="${PLUGIN_DIR:-$(cd "$BUILD_DIR/.." && pwd)}"
FRAG_DIR="$BUILD_DIR/fragments"

MODE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --apply) MODE="apply"; shift ;;
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    *) echo "用法: build.sh [--check|--apply] [--plugin-dir <dir>]" >&2; exit 1 ;;
  esac
done
[ -n "$MODE" ] || { echo "ERROR: 要 --check 或 --apply" >&2; exit 1; }

SCEN_DIR="$PLUGIN_DIR/skills/orchestrate/references/scenario"
[ -d "$SCEN_DIR" ] || { echo "ERROR: 找不到 $SCEN_DIR" >&2; exit 1; }

# 渲染一个文件:遇到 BEGIN 锚点,打印锚点行 + 对应片段全文,跳过原内容直到 END。
render() {
  awk -v fragdir="$FRAG_DIR" '
    /<!-- BEGIN: / {
      print
      name=$0; sub(/.*<!-- BEGIN: /,"",name); sub(/ -->.*/,"",name)
      file=fragdir"/"name".md"
      n=0
      while ((getline line < file) > 0) { print line; n++ }
      close(file)
      if (n==0) { print "BUILD_ERROR_MISSING_OR_EMPTY_FRAGMENT:" name > "/dev/stderr"; exit 3 }
      skip=1; next
    }
    /<!-- END: / { skip=0; print; next }
    skip!=1 { print }
  ' "$1"
}

fail=0
shopt -s nullglob
for f in "$SCEN_DIR"/*.md; do
  grep -q '<!-- BEGIN: ' "$f" || continue   # 没锚点的(如 merge.md)跳过
  out="$(render "$f")" || { echo "ERROR: 渲染失败 $f" >&2; exit 3; }
  if [ "$MODE" = check ]; then
    if ! diff -q <(printf '%s\n' "$out") "$f" >/dev/null; then
      echo "DRIFT: ${f#$PLUGIN_DIR/}(片段已改但没 --apply)"; fail=1
    else
      echo "OK:    ${f#$PLUGIN_DIR/}"
    fi
  else
    printf '%s\n' "$out" > "$f"
    echo "APPLIED: ${f#$PLUGIN_DIR/}"
  fi
done

[ "$fail" -eq 0 ] || { echo "" >&2; echo "有 DRIFT,跑 build.sh --apply 同步" >&2; exit 1; }
