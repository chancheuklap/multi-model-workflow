#!/usr/bin/env bash
# workflows 单源同步守卫:*.workflow.js(源)与 dist/<name>.json(入库生成物)必须一致。
# 机器侧 ~/.pi/workflows/saved 是指向 dist 的软链,永不快照漂移;唯一能漂的是
# "改了 js 忘跑 install-workflows.sh"——本测试就是那道闸(--check 抓)。
# 另用沙箱验证:--check 能抓出突变,install 建出指向 dist 的可解析软链。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WF_DIR="$SCRIPT_DIR/../../workflows"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_workflows_dist_sync.sh ==="

# 1) 仓库现状:dist 与源一致
if bash "$WF_DIR/install-workflows.sh" --check >/dev/null 2>&1; then
  ok "dist 与 *.workflow.js 一致"
else
  no "dist 落后于源——跑 bash workflows/install-workflows.sh 后重试"
fi

# 2) 沙箱:突变源后 --check 必须报漂移(exit 2)
sandbox="$(mktemp -d)"
trap 'rm -rf "$sandbox"' EXIT
cp -R "$WF_DIR/" "$sandbox/workflows/"
first_js="$(ls "$sandbox/workflows"/*.workflow.js | head -1)"
echo "// drift-probe" >> "$first_js"
if bash "$sandbox/workflows/install-workflows.sh" --check >/dev/null 2>&1; then
  no "--check 没抓出被突变的源(应 exit 2)"
else
  ok "--check 抓出源与 dist 漂移"
fi

# 3) 沙箱:install 重建 dist 并在 SAVED_DIR 建出指向 dist 的软链,内容与源逐字一致
saved="$sandbox/saved"
if MMW_PI_WORKFLOWS_SAVED="$saved" bash "$sandbox/workflows/install-workflows.sh" >/dev/null 2>&1; then
  ok "install 幂等跑通"
else
  no "install 失败"
fi
link_ok=1
for wf in "$sandbox/workflows"/*.workflow.js; do
  name="$(node --input-type=module -e "
    const { readFileSync } = await import('node:fs');
    const lines = readFileSync(process.argv[1], 'utf8').split('\n');
    const s = lines.findIndex((l) => l.startsWith('export const meta'));
    const e = lines.findIndex((l, i) => i > s && l === '}');
    const meta = new Function('return ' + lines.slice(s, e + 1).join('\n').replace(/^export const meta =\s*/, ''))();
    console.log(meta.name);
  " "$wf")"
  l="$saved/$name.json"
  [ -L "$l" ] || { link_ok=0; echo "  (saved/$name.json 不是软链)"; continue; }
  case "$(readlink "$l")" in "$sandbox/workflows/dist/"*) ;; *) link_ok=0; echo "  (saved/$name.json 没指向 dist)";; esac
  diff -q <(jq -j .script "$l") "$wf" >/dev/null 2>&1 || { link_ok=0; echo "  (saved/$name.json script 与源不一致)"; }
done
[ "$link_ok" -eq 1 ] && ok "saved 软链指向 dist 且 script 与源逐字一致" || no "saved 软链校验失败"

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
