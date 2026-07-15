#!/usr/bin/env bash
# build.sh 自检:--apply 后 --check 干净;改片段能传播;手改锚点区被 --check 抓出 DRIFT。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$HERE/../.." && pwd)"
BUILD="$PLUGIN_DIR/build/build.sh"
SCEN="$PLUGIN_DIR/skills/orchestrate/references/scenario"
FRAG="$PLUGIN_DIR/build/fragments"
SKILL="$PLUGIN_DIR/skills/orchestrate/SKILL.md"

pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }
echo "=== test_build.sh ==="

# 1. 当前已 --apply 过 → --check 应干净
bash "$BUILD" --check >/dev/null 2>&1 && ok "已构建状态 --check 干净" || no "--check 应干净却报 DRIFT"

# 2. 三条路径都注入了 worktree 片段(共用内容真到了每份)
hit=0
for f in develop small-change bug; do
  grep -q "建 worktree(进去之后才开干)" "$SCEN/$f.md" && hit=$((hit+1))
done
[ "$hit" -eq 3 ] && ok "共用片段注入了全部 3 条路径" || no "共用片段没覆盖全(只 $hit/3)"

# 3. merge.md 无锚点 → 不被构建动(特殊路径)
if grep -q '<!-- BEGIN:' "$SCEN/merge.md" 2>/dev/null; then no "merge.md 不应有锚点"; else ok "merge.md 无锚点(特殊路径,build 跳过)"; fi

# 4. 手改某路径锚点区 → --check 必须抓出 DRIFT
cp "$SCEN/develop.md" "$SCEN/develop.md.bak"
# 在注入区插一行(模拟有人直接改了被构建管的内容)
awk '/<!-- END: worktree-setup -->/ && !done {print "篡改行"; done=1} {print}' "$SCEN/develop.md.bak" > "$SCEN/develop.md"
if bash "$BUILD" --check >/dev/null 2>&1; then no "手改锚点区没被 --check 抓到"; else ok "手改锚点区被 --check 抓出 DRIFT"; fi
# 还原
mv "$SCEN/develop.md.bak" "$SCEN/develop.md"
bash "$BUILD" --check >/dev/null 2>&1 && ok "还原后 --check 干净" || no "还原失败"

# 5. 改片段 → --apply 传播到所有路径,--check 再次干净(改完还原)
cp "$FRAG/closing-cleanup.md" "$FRAG/closing-cleanup.md.bak"
printf '\n临时片段改动验证传播\n' >> "$FRAG/closing-cleanup.md"
bash "$BUILD" --apply >/dev/null 2>&1
prop=0
for f in develop small-change bug; do
  grep -q "临时片段改动验证传播" "$SCEN/$f.md" && prop=$((prop+1))
done
[ "$prop" -eq 3 ] && ok "改片段 --apply 传播到全部 3 路径" || no "传播失败($prop/3)"
# 还原片段 + 重建 + 校验
mv "$FRAG/closing-cleanup.md.bak" "$FRAG/closing-cleanup.md"
bash "$BUILD" --apply >/dev/null 2>&1
bash "$BUILD" --check >/dev/null 2>&1 && ok "还原片段重建后 --check 干净" || no "还原重建失败"

# 6. skill 触发面与正文都先排除无需编排的请求
grep -q "不用于问答、解释、只读查看" "$SKILL" && ok "skill metadata 排除无需编排请求" || no "skill metadata 触发面过宽"
grep -q "琐碎单步动作.*不跑.*mmw.*不建 worktree" "$SKILL" && ok "入口正文给出直接处理出口" || no "入口正文缺直接处理出口"
direct_line="$(grep -n '^先判是否需要正式编排' "$SKILL" | cut -d: -f1)"
step0_line="$(grep -n '^## Step 0' "$SKILL" | cut -d: -f1)"
[ -n "$direct_line" ] && [ "$direct_line" -lt "$step0_line" ] && ok "直接处理判断先于 mmw where" || no "直接处理判断顺序过晚"
grep -q '^# Small-change · 需独立任务边界的小改$' "$SCEN/small-change.md" && ok "small-change reference 同步收窄" || no "small-change reference 仍用旧宽口径"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
