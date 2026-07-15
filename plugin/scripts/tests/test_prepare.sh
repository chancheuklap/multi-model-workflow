#!/usr/bin/env bash
# prepare.sh 端到端自检:new → resume → cleanup,跑在一次性 git 仓库里。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
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
OUT="$(bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "测试任务" --request "实现完整需求并保留验收条件" 2>/dev/null)"
WT="$TMP/${WT_REL}/$SLUG"
echo "$OUT" | grep -q "^PREPARED" && ok "new 返回 PREPARED" || no "new 返回 PREPARED"
[ -d "$WT" ] && ok "worktree 目录建好" || no "worktree 目录建好"
git show-ref --verify --quiet "refs/heads/$SLUG" && ok "分支建好" || no "分支建好"
[ -d "$WT/docs/investigating" ] && [ -d "$WT/docs/design" ] && [ -d "$WT/docs/issues" ] && [ -d "$WT/docs/plans" ] && [ -d "$WT/docs/context" ] && ok "docs 布局 scaffold(investigating/design/issues/plans/context 全)" || no "docs 布局 scaffold"
[ "$(cat "$WT/.claude/.gitignore" 2>/dev/null)" = "*" ] && ok "状态平面 .claude/ 已 gitignore(git status 不脏)" || no ".claude gitignore"
# 主仓库零残留:建完 worktree 主仓库 git status 干净(.claude/.gitignore 遮蔽 worktrees/ 与状态平面)
[ -z "$(git status --porcelain)" ] && ok "建 worktree 后主仓库 git status 零残留" || no "主仓库残留 ($(git status --porcelain | head -1))"
grep -qxF 'worktrees/' .claude/.gitignore && grep -qxF 'multi-model-workflow/' .claude/.gitignore && ok "主仓库 .claude/.gitignore 遮蔽状态平面" || no "主仓库遮蔽条目"
LC1="$(wc -l < .claude/.gitignore)"
bash "$PREPARE" new --scenario bug --slug 2026-06-28-idem --title t --request t >/dev/null 2>&1
[ "$(wc -l < .claude/.gitignore)" = "$LC1" ] && ok "遮蔽写入幂等(重复 new 不追行)" || no "遮蔽幂等"
[ "$(jq -r .attendance "$TMP/${WT_REL}/2026-06-28-idem/${STATE_SUBDIR}/task.json")" = "afk" ] && ok "bug 无讨论期 → attendance 起步 afk" || no "bug attendance afk"
git worktree remove --force "$TMP/${WT_REL}/2026-06-28-idem" >/dev/null 2>&1; git branch -D 2026-06-28-idem >/dev/null 2>&1; git worktree prune >/dev/null 2>&1   # 清掉幂等试探,不影响后续 team 断言
grep -q "investigating/" "$WT/docs/.gitignore" && grep -q "reviews/" "$WT/docs/.gitignore" && grep -q -- "-final-review.md" "$WT/docs/.gitignore" && ok "过程产物 docs/.gitignore(investigating/reviews/终审报告不存档)" || no "docs gitignore"
# 提交白名单:设计(含 prototype/mockup)/计划/issue/领域进 git;过程产物 + .gitignore 自身进不了
mkdir -p "$WT/docs/investigating" "$WT/docs/reviews" "$WT/docs/design/$SLUG/prototype" "$WT/docs/design/$SLUG/mockup"
echo r>"$WT/docs/investigating/r.md"; echo v>"$WT/docs/reviews/v.md"; echo f>"$WT/docs/$SLUG-final-review.md"
echo d>"$WT/docs/design/$SLUG.md"; echo pr>"$WT/docs/design/$SLUG/prototype/p.py"; echo mk>"$WT/docs/design/$SLUG/mockup/m.html"
echo i>"$WT/docs/issues/001.md"; echo p>"$WT/docs/plans/001.md"; echo c>"$WT/docs/context/CONTEXT.md"
git -C "$WT" add -A
STAGED="$(git -C "$WT" diff --cached --name-only)"
WANT="docs/context/CONTEXT.md
docs/design/$SLUG.md
docs/design/$SLUG/mockup/m.html
docs/design/$SLUG/prototype/p.py
docs/issues/001.md
docs/plans/001.md"
[ "$STAGED" = "$WANT" ] && ok "add -A 只进白名单(设计+prototype+mockup+issue+计划+领域;无过程产物无 .gitignore)" || no "提交白名单 (staged=$(echo $STAGED))"
git -C "$WT" reset -q
[ "$(jq -r .docs.plans "$WT/${STATE_SUBDIR}/task.json")" = "docs/plans/$SLUG" ] && ok "manifest.docs.plans 路径" || no "docs.plans 路径"
[ "$(jq -r .docs.design "$WT/${STATE_SUBDIR}/task.json")" = "docs/design/$SLUG" ] && ok "manifest.docs.design 路径" || no "docs.design 路径"

MAN="$WT/${STATE_SUBDIR}/task.json"
[ -f "$MAN" ] && ok "manifest 存在" || no "manifest 存在"
jq -e . "$MAN" >/dev/null 2>&1 && ok "manifest 合法 JSON" || no "manifest 合法 JSON"
[ "$(jq -r .slug "$MAN")" = "$SLUG" ] && ok "manifest.slug" || no "manifest.slug"
[ "$(jq -r .scenario "$MAN")" = "develop" ] && ok "manifest.scenario" || no "manifest.scenario"
[ "$(jq -r .request "$MAN")" = "实现完整需求并保留验收条件" ] && ok "manifest.request 保留源意图" || no "manifest.request"
[ "$(jq -r .phase "$MAN")" = "investigate" ] && ok "develop→首阶段 investigate" || no "develop→investigate"
[ "$(jq -rc .phases "$MAN")" = '["investigate","propose","design","to-issue","plan","build","package","closing"]' ] && ok "phases 固化进 manifest" || no "phases 固化"
[ "$(jq -r .base_commit "$MAN")" = "$BASE" ] && ok "base_commit=本地HEAD" || no "base_commit=本地HEAD"
[ "$(jq -r .step_index "$MAN")" = "0" ] && ok "step_index 初始化=0(阶段内步骤游标)" || no "step_index 初始化"
[ "$(jq -r .phase_index "$MAN")" = "0" ] && ok "phase_index=0" || no "phase_index=0"
[ "$(jq -r .gate "$MAN")" = "null" ] && ok "gate 初始 null" || no "gate 初始 null"
[ "$(jq -r '.repair_count,.turnaround_count' "$MAN" | tr '\n' ',')" = "0,0," ] && ok "计数器归零" || no "计数器归零"
[ "$(jq -r '.artifacts,.open_items,.subtasks,.history|length' "$MAN" | paste -sd, -)" = "0,0,0,0" ] && ok "数组初始为空" || no "数组初始为空"
[ "$(jq -rc .phase_outputs "$MAN")" = "{}" ] && ok "phase_outputs 初始为空对象(接力单)" || no "phase_outputs 初始空"
[ "$(jq -r .attendance "$MAN")" = "attended" ] && ok "develop 讨论态生来 attended(过门才切 afk)" || no "develop attendance attended"
[ "$(jq -r .unattended_policy "$MAN")" = "null" ] && ok "unattended_policy 初始 null" || no "unattended_policy 初始 null"
[ -n "$(jq -r '.plugin_version // ""' "$MAN")" ] && ok "manifest 记 plugin_version(时效戳)" || no "plugin_version 缺失"
[ "$(jq -r .updated_at "$MAN")" = "$(jq -r .created_at "$MAN")" ] && ok "updated_at 初始=created_at" || no "updated_at 初始"
[ "$(jq -r .note "$MAN")" = "null" ] && ok "note 书签初始 null" || no "note 初始 null"
[ "$(jq -r .approval "$MAN")" = "null" ] && ok "approval 初始 null(设计未过门)" || no "approval 初始 null"

# 分支从 HEAD 分叉(同 base commit)
[ "$(git -C "$WT" rev-parse HEAD)" = "$BASE" ] && ok "worktree HEAD=base" || no "worktree HEAD=base"

# --- 重复 new 应拒绝 ---
if bash "$PREPARE" new --scenario develop --slug "$SLUG" --title x --request x >/dev/null 2>&1; then
  no "重复 slug 被拒"; else ok "重复 slug 被拒"; fi

# --- scope(范围变更刷新 request) ---
( cd "$WT" && bash "$PREPARE" scope --request "改后的完整范围与验收" >/dev/null )
[ "$(jq -r .request "$MAN")" = "改后的完整范围与验收" ] && ok "task scope 刷新 manifest.request" || no "scope 刷新 request"
if ( cd "$WT" && bash "$PREPARE" scope >/dev/null 2>&1 ); then
  no "scope 缺 --request 被拒"; else ok "scope 缺 --request 被拒"; fi

# --- 缺原始 request 拒绝 ---
if bash "$PREPARE" new --scenario small-change --slug missing-request --title x >/dev/null 2>&1; then
  no "缺原始 request 被拒"; else ok "缺原始 request 被拒"; fi

# --- 坏 slug 拒绝 ---
if bash "$PREPARE" new --scenario develop --slug "Bad Slug" --title x --request x >/dev/null 2>&1; then
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
