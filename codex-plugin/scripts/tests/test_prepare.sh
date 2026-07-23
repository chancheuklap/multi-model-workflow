#!/usr/bin/env bash
# Codex outer worktree 合同：只采用 App/用户已创建的 linked worktree 与 branch。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
STATE_SUBDIR=".codex/multi-model-workflow"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_prepare.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
DETACHED="$TMP/detached"
APP_WT="$TMP/app-worktree"
SLUG="2026-07-24-app-adoption"
EXPECTED_BRANCH="codex/$SLUG"

mkdir -p "$REPO"
git -C "$REPO" init -q
git -C "$REPO" config user.email t@t
git -C "$REPO" config user.name t
printf 'seed\n' > "$REPO/seed.txt"
git -C "$REPO" add seed.txt
git -C "$REPO" commit -qm seed
BASE="$(git -C "$REPO" rev-parse HEAD)"

# Local checkout 不得被 plugin 改造成它自己的 outer worktree。
BEFORE_STATUS="$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)"
BEFORE_WT_COUNT="$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')"
LOCAL_OUT="$(cd "$REPO" && bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "App 采用" --request "保持 App 可见" 2>&1 || true)"
if printf '%s\n' "$LOCAL_OUT" | grep -q '^NEEDS_APP_WORKTREE$'; then
  ok "local checkout 返回 NEEDS_APP_WORKTREE"
else
  no "local checkout 没给 App worktree 指引"
fi
if [ "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)" = "$BEFORE_STATUS" ] \
  && [ "$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')" = "$BEFORE_WT_COUNT" ] \
  && [ ! -e "$REPO/.codex" ] \
  && [ ! -e "$REPO/docs" ]; then
  ok "local checkout 拒绝路径零写入"
else
  no "local checkout 拒绝路径产生了副作用"
fi

# App 刚创建的 worktree 可能仍是 detached；plugin 只请用户在 App 内建 branch。
git -C "$REPO" worktree add --detach "$DETACHED" HEAD >/dev/null
DETACHED_HEAD="$(git -C "$DETACHED" rev-parse HEAD)"
DETACHED_OUT="$(cd "$DETACHED" && bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "App 采用" --request "保持 App 可见" 2>&1 || true)"
if printf '%s\n' "$DETACHED_OUT" | grep -q '^NEEDS_APP_BRANCH$' \
  && printf '%s\n' "$DETACHED_OUT" | grep -q "expected_branch=$EXPECTED_BRANCH"; then
  ok "detached worktree 返回 App branch 名"
else
  no "detached worktree 没给精确 branch 指引"
fi
if [ "$(git -C "$DETACHED" rev-parse HEAD)" = "$DETACHED_HEAD" ] \
  && [ -z "$(git -C "$DETACHED" status --porcelain=v1 --untracked-files=all)" ] \
  && [ ! -e "$DETACHED/.codex" ] \
  && [ ! -e "$DETACHED/docs" ]; then
  ok "detached 拒绝路径零写入"
else
  no "detached 拒绝路径产生了副作用"
fi
git -C "$REPO" worktree remove "$DETACHED"

# 已进入 linked worktree，但 branch 与任务不一致时仍然只给 App 指引。
git -C "$REPO" worktree add -b wrong-branch "$DETACHED" HEAD >/dev/null
WRONG_OUT="$(cd "$DETACHED" && bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "App 采用" --request "保持 App 可见" 2>&1 || true)"
if printf '%s\n' "$WRONG_OUT" | grep -q '^NEEDS_APP_BRANCH$' \
  && printf '%s\n' "$WRONG_OUT" | grep -q 'current_branch=wrong-branch' \
  && [ -z "$(git -C "$DETACHED" status --porcelain=v1 --untracked-files=all)" ]; then
  ok "错误 branch 只返回更正指引且零写入"
else
  no "错误 branch 处理不符合合同"
fi
git -C "$REPO" worktree remove "$DETACHED"
git -C "$REPO" branch -D wrong-branch >/dev/null

# 模拟 App 的 Create branch here；task new 必须原地采用，不得再建第二个 outer。
git -C "$REPO" worktree add -b "$EXPECTED_BRANCH" "$APP_WT" HEAD >/dev/null
APP_WT="$(cd "$APP_WT" && pwd -P)"
COUNT_BEFORE_ADOPT="$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')"
OUT="$(cd "$APP_WT" && bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "App 采用" --request "保持 App 可见")"
MAN="$APP_WT/$STATE_SUBDIR/task.json"
if printf '%s\n' "$OUT" | grep -q '^PREPARED$'; then
  ok "App branch 原地采用成功"
else
  no "App branch 未返回 PREPARED"
fi
if [ "$(git -C "$REPO" worktree list --porcelain | grep -c '^worktree ')" = "$COUNT_BEFORE_ADOPT" ] \
  && [ "$(git -C "$APP_WT" branch --show-current)" = "$EXPECTED_BRANCH" ]; then
  ok "采用过程没有创建第二个 outer worktree/branch"
else
  no "采用过程擅自创建了 outer worktree"
fi
if [ -f "$MAN" ] \
  && [ "$(jq -r .worktree_path "$MAN")" = "$APP_WT" ] \
  && [ "$(jq -r .branch "$MAN")" = "$EXPECTED_BRANCH" ] \
  && [ "$(jq -r .base_commit "$MAN")" = "$BASE" ] \
  && [ "$(jq -r .plugin_version "$MAN")" = "0.1.0" ]; then
  ok "manifest 记录 App 当前 worktree、branch、base 和 plugin 版本"
else
  no "manifest 没有忠实记录 App checkout"
fi
if [ -d "$APP_WT/docs/design" ] \
  && [ -d "$APP_WT/docs/issues" ] \
  && [ -d "$APP_WT/docs/plans" ] \
  && [ -d "$APP_WT/docs/context" ] \
  && [ "$(cat "$APP_WT/.codex/.gitignore")" = "*" ]; then
  ok "任务文档与 Codex 状态 scaffold 完整"
else
  no "任务 scaffold 不完整"
fi
if [ "$(jq -r .attendance "$MAN")" = attended ] \
  && [ "$(jq -r .phase "$MAN")" = investigate ] \
  && [ "$(jq -r .prototype "$MAN")" = null ]; then
  ok "develop 起始流程和值守合同保持不变"
else
  no "采用 App worktree 改坏了业务流程"
fi

if (cd "$APP_WT" && bash "$PREPARE" new --scenario develop --slug "$SLUG" --title x --request x >/dev/null 2>&1); then
  no "重复建档应被拒"
else
  ok "同一 App worktree 重复建档被拒"
fi

# resume/scope/team 继续以磁盘状态为真相源。
RESUME="$(cd "$APP_WT" && bash "$PREPARE" resume)"
if printf '%s\n' "$RESUME" | head -1 | grep -q '^MANAGED$' \
  && printf '%s\n' "$RESUME" | tail -n +2 | jq -e --arg slug "$SLUG" '.slug==$slug' >/dev/null; then
  ok "resume 从 App worktree 恢复任务"
else
  no "resume 无法恢复 App 任务"
fi
(cd "$APP_WT" && bash "$PREPARE" scope --request "更新后的完整范围" >/dev/null)
if [ "$(jq -r .request "$MAN")" = "更新后的完整范围" ]; then
  ok "scope 原地更新任务真相源"
else
  no "scope 未更新 manifest"
fi
TEAM="$(cd "$REPO" && bash "$PREPARE" team)"
if printf '%s\n' "$TEAM" | tail -n +2 | jq -e --arg slug "$SLUG" --arg wt "$APP_WT" '.slug==$slug and .worktree==$wt' >/dev/null 2>&1; then
  ok "target checkout 可从 git worktree 清单看到 App 任务"
else
  no "team 看不到 App 任务"
fi

# cleanup 只能在已合并后清状态；App worktree 和 branch 由 App 继续持有。
printf 'feature\n' > "$APP_WT/feature.txt"
git -C "$APP_WT" add docs feature.txt
git -C "$APP_WT" commit -qm "feature work"
BRANCH_SHA="$(git -C "$APP_WT" rev-parse HEAD)"
if (cd "$REPO" && bash "$PREPARE" cleanup --slug "$SLUG" >/dev/null 2>&1); then
  no "未合并任务 cleanup 应被拒"
else
  ok "未合并任务拒绝清状态"
fi
git -C "$REPO" merge -q --no-ff "$EXPECTED_BRANCH" -m "merge $EXPECTED_BRANCH"
(cd "$REPO" && bash "$PREPARE" cleanup --slug "$SLUG" >/dev/null)
if [ ! -e "$APP_WT/$STATE_SUBDIR" ] \
  && [ -d "$APP_WT" ] \
  && git -C "$REPO" show-ref --verify --quiet "refs/heads/$EXPECTED_BRANCH" \
  && [ "$(git -C "$APP_WT" rev-parse HEAD)" = "$BRANCH_SHA" ]; then
  ok "cleanup 只清 MMW 状态，保留 App worktree/branch"
else
  no "cleanup 越权接管了 App worktree/branch"
fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
