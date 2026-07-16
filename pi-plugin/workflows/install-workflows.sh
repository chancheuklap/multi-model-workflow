#!/usr/bin/env bash
# 把 pi-plugin/workflows/*.workflow.js 包装成 pi-dynamic-workflows 的 saved 格式
# (~/.pi/workflows/saved/<name>.json,{name,description,script}),装完可用
# /investigate-internal、/investigate-external 或 workflow('name', args) 调用。
# 幂等:重复跑覆盖同名文件。依赖:jq、node(取 meta 字段)。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SAVED_DIR="${MMW_PI_WORKFLOWS_SAVED:-$HOME/.pi/workflows/saved}"
mkdir -p "$SAVED_DIR"

installed=0
for wf in "$SCRIPT_DIR"/*.workflow.js; do
  [ -f "$wf" ] || continue
  # 从 meta 里取 name/description(以脚本自身声明为准,不从文件名猜)
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
    '{name: $meta.name, description: $meta.description, script: $script}' \
    > "$SAVED_DIR/$name.json"
  echo "installed: $SAVED_DIR/$name.json"
  installed=$((installed + 1))
done

[ "$installed" -gt 0 ] || { echo "ERROR: 没找到任何 *.workflow.js" >&2; exit 2; }
echo "done: $installed workflow(s) → $SAVED_DIR (需已安装 @quintinshaw/pi-dynamic-workflows,重载后用 /workflows 核对)"
