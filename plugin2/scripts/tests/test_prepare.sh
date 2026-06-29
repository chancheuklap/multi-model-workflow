#!/usr/bin/env bash
# prepare.sh 端到端自检:new → resume → cleanup,跑在一次性 git 仓库里。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"

pass=0; fail=0
ok()  { echo "  PASS: $1"; pass=$((pass+1)); }
no()  { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_prepare.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q; git config user.email t@t; git config user.name t
echo seed > seed.txt; git add -A; git commit -qm seed
BASE="$(git rev-parse HEAD)"

SLUG="2026-06-28-test-feature"

# --- new ---
OUT="$(bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "测试任务" 2>/dev/null)"
WT="$TMP/.claude/worktrees/$SLUG"
echo "$OUT" | grep -q "^PREPARED" && ok "new 返回 PREPARED" || no "new 返回 PREPARED"
[ -d "$WT" ] && ok "worktree 目录建好" || no "worktree 目录建好"
git show-ref --verify --quiet "refs/heads/$SLUG" && ok "分支建好" || no "分支建好"
[ -d "$WT/docs/investigating" ] && [ -d "$WT/docs/design" ] && [ -d "$WT/docs/issues" ] && [ -d "$WT/docs/plans" ] && [ -d "$WT/docs/context" ] && ok "docs 布局 scaffold(investigating/design/issues/plans/context 全)" || no "docs 布局 scaffold"
[ "$(jq -r .docs.plans "$WT/.claude/multi-model-workflow/task.json")" = "docs/plans/$SLUG" ] && ok "manifest.docs.plans 路径" || no "docs.plans 路径"
[ "$(jq -r .docs.design "$WT/.claude/multi-model-workflow/task.json")" = "docs/design/$SLUG" ] && ok "manifest.docs.design 路径" || no "docs.design 路径"

MAN="$WT/.claude/multi-model-workflow/task.json"
[ -f "$MAN" ] && ok "manifest 存在" || no "manifest 存在"
jq -e . "$MAN" >/dev/null 2>&1 && ok "manifest 合法 JSON" || no "manifest 合法 JSON"
[ "$(jq -r .slug "$MAN")" = "$SLUG" ] && ok "manifest.slug" || no "manifest.slug"
[ "$(jq -r .scenario "$MAN")" = "develop" ] && ok "manifest.scenario" || no "manifest.scenario"
[ "$(jq -r .phase "$MAN")" = "investigate" ] && ok "develop→首阶段 investigate" || no "develop→investigate"
[ "$(jq -rc .phases "$MAN")" = '["investigate","propose","design","plan","build","verify","closing"]' ] && ok "phases 固化进 manifest" || no "phases 固化"
[ "$(jq -r .base_commit "$MAN")" = "$BASE" ] && ok "base_commit=本地HEAD" || no "base_commit=本地HEAD"
[ "$(jq -r .phase_index "$MAN")" = "0" ] && ok "phase_index=0" || no "phase_index=0"
[ "$(jq -r .gate "$MAN")" = "null" ] && ok "gate 初始 null" || no "gate 初始 null"
[ "$(jq -r '.repair_count,.turnaround_count' "$MAN" | tr '\n' ',')" = "0,0," ] && ok "计数器归零" || no "计数器归零"
[ "$(jq -r '.artifacts,.open_items,.subtasks,.history|length' "$MAN" | paste -sd, -)" = "0,0,0,0" ] && ok "数组初始为空" || no "数组初始为空"
[ "$(jq -rc .phase_outputs "$MAN")" = "{}" ] && ok "phase_outputs 初始为空对象(接力单)" || no "phase_outputs 初始空"

# 分支从 HEAD 分叉(同 base commit)
[ "$(git -C "$WT" rev-parse HEAD)" = "$BASE" ] && ok "worktree HEAD=base" || no "worktree HEAD=base"

# --- 重复 new 应拒绝 ---
if bash "$PREPARE" new --scenario develop --slug "$SLUG" --title x >/dev/null 2>&1; then
  no "重复 slug 被拒"; else ok "重复 slug 被拒"; fi

# --- 坏 slug 拒绝 ---
if bash "$PREPARE" new --scenario develop --slug "Bad Slug" --title x >/dev/null 2>&1; then
  no "坏 slug 被拒"; else ok "坏 slug 被拒"; fi

# --- resume(worktree 内) ---
ROUT="$(cd "$WT" && bash "$PREPARE" resume 2>/dev/null)"
echo "$ROUT" | head -1 | grep -q "^MANAGED" && ok "resume 返回 MANAGED" || no "resume 返回 MANAGED"
echo "$ROUT" | tail -n +2 | jq -e --arg s "$SLUG" '.slug==$s' >/dev/null 2>&1 && ok "resume 带正确 manifest" || no "resume 带正确 manifest"

# --- resume(主仓库,无 manifest) ---
RMAIN="$(bash "$PREPARE" resume 2>/dev/null)"
[ "$RMAIN" = "UNMANAGED" ] && ok "主仓库 resume=UNMANAGED" || no "主仓库 resume=UNMANAGED"

# --- team(merge 用:列全队 manifest)---
TEAM="$(bash "$PREPARE" team 2>/dev/null)"
echo "$TEAM" | head -1 | grep -q "^TEAM" && ok "team 返回 TEAM" || no "team 返回 TEAM"
echo "$TEAM" | tail -n +2 | jq -e --arg s "$SLUG" '.slug==$s and (.design|type=="string")' >/dev/null 2>&1 \
  && ok "team 列出队员身份 + 设计文档路径(供 merge 查冲突)" || no "team 列队员"

# 在 worktree 里做一次真提交,让分支与主线分叉(否则 base==HEAD,trivially merged)
( cd "$WT" && echo work > feature.txt && git add -A && git commit -qm "feature work" )

# --- cleanup(分支未合并 → 拒删,防丢工作) ---
if bash "$PREPARE" cleanup --slug "$SLUG" >/dev/null 2>&1; then
  no "未合并分支 cleanup 应拒"; else ok "未合并分支 cleanup 被拒(branch -d 安全)"; fi
[ -d "$WT" ] || no "拒删后 worktree 仍在"

# --- 合并后 cleanup 成功 ---
git merge -q --no-ff "$SLUG" -m "merge $SLUG"
bash "$PREPARE" cleanup --slug "$SLUG" >/dev/null 2>&1 && ok "合并后 cleanup 成功" || no "合并后 cleanup 成功"
[ ! -d "$WT" ] && ok "worktree 已删" || no "worktree 已删"
git show-ref --verify --quiet "refs/heads/$SLUG" && no "分支已删" || ok "分支已删"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
