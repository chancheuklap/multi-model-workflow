#!/usr/bin/env bash
# workflows 单源同步:*.workflow.js(源)→ dist/<name>.json(入库生成物)→
# ~/.pi/workflows/saved/<name>.json(软链指向 dist;pi-dynamic-workflows 只认 saved 下的
# {name,description,script} JSON,不直接吃 js,所以垫 dist 一层,软链保证机器侧永不快照漂移)。
#
# 默认(install):重新生成 dist、清掉无源孤儿、重建软链。幂等,重复跑覆盖。
# --check:只验 dist 与源一致(不碰机器状态);漂移/孤儿 exit 2——改了 *.workflow.js
#          必须重跑本脚本再提交,测试 test_workflows_dist_sync.sh 靠它抓漂移。
# 依赖:jq、node。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
SAVED_DIR="${MMW_PI_WORKFLOWS_SAVED:-$HOME/.pi/workflows/saved}"
MODE=install
[ "${1:-}" = "--check" ] && MODE=check

render() { # $1=workflow.js → stdout 生成 JSON(以脚本自身 meta 声明为准,不从文件名猜)
  local wf="$1" meta_json
  meta_json="$(node --input-type=module -e "
    const { readFileSync } = await import('node:fs');
    const lines = readFileSync(process.argv[1], 'utf8').split('\n');
    const start = lines.findIndex((l) => l.startsWith('export const meta'));
    if (start === -1) { console.error('meta not found: ' + process.argv[1]); process.exit(1); }
    const end = lines.findIndex((l, i) => i > start && l === '}');
    if (end === -1) { console.error('meta block unterminated: ' + process.argv[1]); process.exit(1); }
    const literal = lines.slice(start, end + 1).join('\n').replace(/^export const meta =\s*/, '');
    const meta = new Function('return ' + literal)();
    console.log(JSON.stringify({ name: meta.name, description: meta.description || '' }));
  " "$wf")"
  name="$(printf '%s' "$meta_json" | jq -r .name)"
  [ -n "$name" ] && [ "$name" != null ] || { echo "ERROR: $wf 缺 meta.name" >&2; exit 2; }
  jq -n --rawfile script "$wf" --argjson meta "$meta_json" \
    '{name: $meta.name, description: $meta.description, script: $script}'
}

sources=("$SCRIPT_DIR"/*.workflow.js)
[ -f "${sources[0]}" ] || { echo "ERROR: 没找到任何 *.workflow.js" >&2; exit 2; }

# 先全部渲染到临时目录(check/install 共用;name 由 meta 决定)
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
names=()
for wf in "${sources[@]}"; do
  json="$(render "$wf")"
  name="$(printf '%s' "$json" | jq -r .name)"
  printf '%s\n' "$json" > "$tmp/$name.json"
  names+=("$name")
done

if [ "$MODE" = "check" ]; then
  drift=0
  for name in "${names[@]}"; do
    if [ ! -f "$DIST_DIR/$name.json" ]; then
      echo "DRIFT: dist/$name.json 缺失(有源无生成物)" >&2; drift=1
    elif ! diff -q "$tmp/$name.json" "$DIST_DIR/$name.json" >/dev/null; then
      echo "DRIFT: dist/$name.json 落后于源——重跑 install-workflows.sh" >&2; drift=1
    fi
  done
  for d in "$DIST_DIR"/*.json; do
    [ -f "$d" ] || continue
    base="$(basename "$d" .json)"
    printf '%s\n' "${names[@]}" | grep -qx "$base" \
      || { echo "DRIFT: dist/$base.json 是孤儿(无对应源)——重跑 install-workflows.sh 清理" >&2; drift=1; }
  done
  [ "$drift" -eq 0 ] && echo "OK: dist 与 ${#names[@]} 个 workflow 源一致" || exit 2
  exit 0
fi

# install:dist 全量重建(清孤儿)+ saved 软链重建
mkdir -p "$DIST_DIR" "$SAVED_DIR"
for d in "$DIST_DIR"/*.json; do
  [ -f "$d" ] || continue
  base="$(basename "$d" .json)"
  printf '%s\n' "${names[@]}" | grep -qx "$base" || { rm "$d"; echo "pruned: dist/$base.json(孤儿)"; }
done
for name in "${names[@]}"; do
  cp "$tmp/$name.json" "$DIST_DIR/$name.json"
  ln -sfn "$DIST_DIR/$name.json" "$SAVED_DIR/$name.json"
  echo "installed: $SAVED_DIR/$name.json -> dist/$name.json"
done
# 清 saved 里指进本 dist 但目标已不存在的悬空软链
for l in "$SAVED_DIR"/*.json; do
  [ -L "$l" ] || continue
  target="$(readlink "$l")"
  case "$target" in "$DIST_DIR"/*) [ -e "$l" ] || { rm "$l"; echo "pruned: $l(悬空软链)"; } ;; esac
done
echo "done: ${#names[@]} workflow(s) → dist 入库 + $SAVED_DIR 软链(重载后用 /workflows 核对)"
