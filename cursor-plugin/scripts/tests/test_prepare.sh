#!/usr/bin/env bash
# prepare.sh 端到端自检:new → resume → cleanup,跑在一次性 git 仓库里。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.cursor/multi-model-workflow}"
WT_REL="${WT_REL:-.cursor/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
SCHEMA="$SCRIPT_DIR/../../state-schema/task-manifest.schema.json"

pass=0; fail=0
ok()  { echo "  PASS: $1"; pass=$((pass+1)); }
no()  { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_prepare.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q; git config user.email t@t; git config user.name t
mkdir -p .cursor
cat >.cursor/worktree-init.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
source_wt="$1"
target_wt="$2"
printf '%s\n' "$source_wt" >"$target_wt/.cursor/worktree-initialized"
SH
chmod +x .cursor/worktree-init.sh
cat >.cursor/.gitignore <<'EOF'
*
!.gitignore
!worktree-init.sh
EOF
echo seed > seed.txt; git add -A; git commit -qm seed
BASE="$(git rev-parse HEAD)"
ROOT="$(git rev-parse --show-toplevel)"

SLUG="2026-06-28-test-feature"

# --- 入口治理能力合同 + 失败原子性 ---
ENTRY_SLUG="2026-06-28-entry-contract"
if bash "$PREPARE" new --scenario small-change --slug "$ENTRY_SLUG" --title t --request t \
  --entry-capability gated-assurance --entry-evidence "用户明确要求独立终审" >/dev/null 2>&1; then
  ok "new 接受结构化入口能力与证据"
else
  no "new 未接受结构化入口能力与证据"
fi
ENTRY_WT="$TMP/${WT_REL}/$ENTRY_SLUG"
[ -d "$ENTRY_WT" ] && git worktree remove --force "$ENTRY_WT" >/dev/null 2>&1 || true
git branch -D "$ENTRY_SLUG" >/dev/null 2>&1 || true
git worktree prune >/dev/null 2>&1

BAD_CAP_SLUG="2026-06-28-bad-capability"
if bash "$PREPARE" new --scenario small-change --slug "$BAD_CAP_SLUG" --title t --request t \
  --entry-capability not-a-capability --entry-evidence "无效能力" >/dev/null 2>&1; then
  no "未知入口治理能力应拒绝"
else
  ok "未知入口治理能力被拒绝"
fi
[ ! -e "$TMP/${WT_REL}/$BAD_CAP_SLUG" ] && ! git show-ref --verify --quiet "refs/heads/$BAD_CAP_SLUG" \
  && ok "未知入口能力失败无副作用" || no "未知入口能力残留副作用"

MISSING_ENTRY_SLUG="2026-06-28-missing-entry"
if bash "$PREPARE" new --scenario small-change --slug "$MISSING_ENTRY_SLUG" --title t --request t >/dev/null 2>&1; then
  no "缺入口治理能力与证据应拒绝"
else
  ok "缺入口治理能力与证据被拒绝"
fi
MISSING_ENTRY_WT="$TMP/${WT_REL}/$MISSING_ENTRY_SLUG"
[ ! -d "$MISSING_ENTRY_WT" ] && ! git show-ref --verify --quiet "refs/heads/$MISSING_ENTRY_SLUG" \
  && ok "入口校验失败无 worktree/branch 副作用" || no "入口校验失败残留 worktree 或 branch"
[ -d "$MISSING_ENTRY_WT" ] && git worktree remove --force "$MISSING_ENTRY_WT" >/dev/null 2>&1 || true
git branch -D "$MISSING_ENTRY_SLUG" >/dev/null 2>&1 || true
git worktree prune >/dev/null 2>&1

WAYFIND_SLUG="2026-06-28-invalid-wayfind"
if bash "$PREPARE" new --scenario bug --slug "$WAYFIND_SLUG" --title t --request t --with-wayfind \
  --entry-capability durable-state --entry-evidence "调查需要跨会话持续" >/dev/null 2>&1; then
  no "bug 不应接受 --with-wayfind"
else
  ok "bug 拒绝 --with-wayfind"
fi
WAYFIND_WT="$TMP/${WT_REL}/$WAYFIND_SLUG"
[ ! -d "$WAYFIND_WT" ] && ! git show-ref --verify --quiet "refs/heads/$WAYFIND_SLUG" \
  && ok "场景校验失败无 worktree/branch 副作用" || no "场景校验晚于 worktree 副作用"
[ -d "$WAYFIND_WT" ] && git worktree remove --force "$WAYFIND_WT" >/dev/null 2>&1 || true
git branch -D "$WAYFIND_SLUG" >/dev/null 2>&1 || true
git worktree prune >/dev/null 2>&1

# --- new ---
OUT="$(bash "$PREPARE" new --scenario develop --slug "$SLUG" --title "测试任务" --request "实现完整需求并保留验收条件" --entry-capability design-approval --entry-capability coordinated-delivery --entry-evidence "目标架构需用户审批且分为两个独立交付切片" 2>/dev/null)"
WT="$TMP/${WT_REL}/$SLUG"
echo "$OUT" | grep -q "^PREPARED" && ok "new 返回 PREPARED" || no "new 返回 PREPARED"
[ -d "$WT" ] && ok "worktree 目录建好" || no "worktree 目录建好"
[ "$(cat "$WT/.cursor/worktree-initialized")" = "$ROOT" ] \
  && ok "task worktree 调用项目初始化 hook" || no "task worktree 初始化 hook"
git show-ref --verify --quiet "refs/heads/$SLUG" && ok "分支建好" || no "分支建好"
[ -d "$WT/docs/design" ] && [ -d "$WT/docs/issues" ] && [ -d "$WT/docs/plans" ] && [ -d "$WT/docs/context" ] && [ ! -d "$WT/docs/investigating" ] && ok "docs 布局 scaffold(design/issues/plans/context 全;investigating 不再单设,进设计文件夹)" || no "docs 布局 scaffold"
git -C "$WT" check-ignore -q .cursor/worktree-initialized \
  && ! git -C "$WT" check-ignore -q .cursor/worktree-init.sh \
  && ok "状态平面忽略运行态并保留项目 hook" || no ".pi gitignore"
# 主仓库零残留:建完 worktree 主仓库 git status 干净(.cursor/.gitignore 遮蔽 worktrees/ 与状态平面)
[ -z "$(git status --porcelain)" ] && ok "建 worktree 后主仓库 git status 零残留" || no "主仓库残留 ($(git status --porcelain | head -1))"
git check-ignore -q .cursor/worktrees/example \
  && git check-ignore -q .cursor/multi-model-workflow/example \
  && ! git check-ignore -q .cursor/worktree-init.sh \
  && ok "主仓库 .cursor/.gitignore 遮蔽状态平面并保留 hook" || no "主仓库遮蔽条目"
LC1="$(wc -l < .cursor/.gitignore)"
bash "$PREPARE" new --scenario bug --slug 2026-06-28-idem --title t --request t --entry-capability explicit-request --entry-evidence "测试夹具明确要求 MMW" >/dev/null 2>&1
[ "$(wc -l < .cursor/.gitignore)" = "$LC1" ] && ok "遮蔽写入幂等(重复 new 不追行)" || no "遮蔽幂等"
[ "$(jq -r .attendance "$TMP/${WT_REL}/2026-06-28-idem/${STATE_SUBDIR}/task.json")" = "afk" ] && ok "bug 无讨论期 → attendance 起步 afk" || no "bug attendance afk"
git worktree remove --force "$TMP/${WT_REL}/2026-06-28-idem" >/dev/null 2>&1; git branch -D 2026-06-28-idem >/dev/null 2>&1; git worktree prune >/dev/null 2>&1   # 清掉幂等试探,不影响后续 team 断言
grep -q "reviews/" "$WT/docs/.gitignore" && grep -q -- "-final-review.md" "$WT/docs/.gitignore" && ! grep -q "investigating/" "$WT/docs/.gitignore" && ok "过程产物 docs/.gitignore(reviews/终审报告不存档;investigating 已转为设计文件夹正式成员)" || no "docs gitignore"
# 提交白名单:设计文件夹全部成员(主文档+direction/investigating/prototype/mockup/evidence)/计划/issue/领域进 git;过程产物 + .gitignore 自身进不了
mkdir -p "$WT/docs/reviews" "$WT/docs/design/$SLUG/prototype" "$WT/docs/design/$SLUG/mockup" "$WT/docs/design/$SLUG/evidence"
echo v>"$WT/docs/reviews/v.md"; echo f>"$WT/docs/$SLUG-final-review.md"
echo d>"$WT/docs/design/$SLUG/$SLUG.md"; echo di>"$WT/docs/design/$SLUG/direction.md"; echo iv>"$WT/docs/design/$SLUG/investigating.md"
echo pr>"$WT/docs/design/$SLUG/prototype/p.py"; echo mk>"$WT/docs/design/$SLUG/mockup/m.html"; echo ev>"$WT/docs/design/$SLUG/evidence/e.md"
echo i>"$WT/docs/issues/001.md"; echo p>"$WT/docs/plans/001.md"; echo c>"$WT/docs/context/CONTEXT.md"
git -C "$WT" add -A
STAGED="$(git -C "$WT" diff --cached --name-only)"
WANT="docs/context/CONTEXT.md
docs/design/$SLUG/$SLUG.md
docs/design/$SLUG/direction.md
docs/design/$SLUG/evidence/e.md
docs/design/$SLUG/investigating.md
docs/design/$SLUG/mockup/m.html
docs/design/$SLUG/prototype/p.py
docs/issues/001.md
docs/plans/001.md"
[ "$STAGED" = "$WANT" ] && ok "add -A 只进白名单(设计文件夹全部成员+issue+计划+领域;无过程产物无 .gitignore)" || no "提交白名单 (staged=$(echo $STAGED))"
git -C "$WT" reset -q
[ "$(jq -r .docs.plans "$WT/${STATE_SUBDIR}/task.json")" = "docs/plans/$SLUG" ] && ok "manifest.docs.plans 路径" || no "docs.plans 路径"
[ "$(jq -r .docs.design "$WT/${STATE_SUBDIR}/task.json")" = "docs/design/$SLUG" ] && ok "manifest.docs.design 路径" || no "docs.design 路径"
[ "$(jq -r .docs.investigating "$WT/${STATE_SUBDIR}/task.json")" = "docs/design/$SLUG/investigating.md" ] && ok "manifest.docs.investigating 进设计文件夹" || no "docs.investigating 路径"

MAN="$WT/${STATE_SUBDIR}/task.json"
[ -f "$MAN" ] && ok "manifest 存在" || no "manifest 存在"
jq -e . "$MAN" >/dev/null 2>&1 && ok "manifest 合法 JSON" || no "manifest 合法 JSON"
jq -e '.properties.prototype.type == ["object","null"] and (.required | index("prototype")) == null' "$SCHEMA" >/dev/null \
  && ok "schema 接受旧任务缺字段并定义 nullable prototype" || no "schema prototype 合同"
jq -e '.properties.entry_capabilities.minItems == 1 and .properties.entry_evidence.minLength == 1 and (.required | index("entry_capabilities")) == null and (.required | index("entry_evidence")) == null' "$SCHEMA" >/dev/null \
  && ok "schema 定义入口审计字段且兼容旧任务" || no "schema 入口审计字段合同"
[ "$(jq -r .slug "$MAN")" = "$SLUG" ] && ok "manifest.slug" || no "manifest.slug"
[ "$(jq -r .request "$MAN")" = "实现完整需求并保留验收条件" ] && ok "manifest.request 保留源意图" || no "manifest.request"
[ "$(jq -rc .entry_capabilities "$MAN")" = '["design-approval","coordinated-delivery"]' ] && ok "manifest 固化入口治理能力" || no "manifest.entry_capabilities"
[ "$(jq -r .entry_evidence "$MAN")" = "目标架构需用户审批且分为两个独立交付切片" ] && ok "manifest 固化入口证据" || no "manifest.entry_evidence"
[ "$(jq -r .scenario "$MAN")" = "develop" ] && ok "manifest.scenario" || no "manifest.scenario"
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
[ "$(jq -r .prototype "$MAN")" = "null" ] && ok "prototype 初始 null(design 必须启动内层循环)" || no "prototype 初始 null"

# 分支从 HEAD 分叉(同 base commit)
[ "$(git -C "$WT" rev-parse HEAD)" = "$BASE" ] && ok "worktree HEAD=base" || no "worktree HEAD=base"

# --- 重复 new 应拒绝 ---
if bash "$PREPARE" new --scenario develop --slug "$SLUG" --title x --request x --entry-capability explicit-request --entry-evidence "测试夹具" >/dev/null 2>&1; then
  no "重复 slug 被拒"; else ok "重复 slug 被拒"; fi

# --- 坏 slug 拒绝 ---
if bash "$PREPARE" new --scenario develop --slug "Bad Slug" --title x --request x --entry-capability explicit-request --entry-evidence "测试夹具" >/dev/null 2>&1; then
  no "坏 slug 被拒"; else ok "坏 slug 被拒"; fi

# --- scope(范围变更刷新 request) ---
( cd "$WT" && bash "$PREPARE" scope --request "改后的完整范围与验收" >/dev/null )
[ "$(jq -r .request "$MAN")" = "改后的完整范围与验收" ] && ok "task scope 刷新 manifest.request" || no "scope 刷新 request"
if ( cd "$WT" && bash "$PREPARE" scope >/dev/null 2>&1 ); then
  no "scope 缺 --request 被拒"; else ok "scope 缺 --request 被拒"; fi

# --- 缺原始需求拒绝 ---
if bash "$PREPARE" new --scenario small-change --slug missing-request --title x --entry-capability explicit-request --entry-evidence "测试夹具" >/dev/null 2>&1; then
  no "缺原始 request 被拒"; else ok "缺原始 request 被拒"; fi

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

# --- 任务 worktree 内拆并行子任务 ---
P_SLUG="2026-07-28-parent-task"
C_SLUG="2026-07-28-child-task"
bash "$PREPARE" new --scenario bug --slug "$P_SLUG" --title "父任务" --request 父需求 \
  --entry-capability explicit-request --entry-evidence "测试夹具" >/dev/null 2>&1
P_WT="$TMP/${WT_REL}/$P_SLUG"
( cd "$P_WT" && echo progress > progress.txt && git add -A && git commit -qm "parent progress" )
P_HEAD="$(git -C "$P_WT" rev-parse HEAD)"
[ "$P_HEAD" != "$BASE" ] && ok "父 worktree 已领先主线(子任务应继承进度)" || no "父 worktree 提交"
C_OUT="$(cd "$P_WT" && bash "$PREPARE" new --scenario small-change --slug "$C_SLUG" --title "子任务" --request 子需求 \
  --entry-capability explicit-request --entry-evidence "测试夹具" 2>/dev/null)"
C_WT="$TMP/${WT_REL}/$C_SLUG"
echo "$C_OUT" | grep -q "^parent_slug=$P_SLUG" && ok "子任务回执报 parent_slug" || no "子任务回执 parent_slug"
[ -d "$C_WT" ] && [ ! -e "$P_WT/${WT_REL}/$C_SLUG" ] && ok "子 worktree 挂主仓库下(扁平不嵌套)" || no "子 worktree 落点"
[ "$(git -C "$C_WT" rev-parse HEAD)" = "$P_HEAD" ] && ok "子任务分支从父 worktree HEAD 分叉(继承进度)" || no "子任务分叉点"
C_MAN="$C_WT/${STATE_SUBDIR}/task.json"
P_WT_GIT="$(git -C "$P_WT" rev-parse --show-toplevel)"   # macOS /var→/private/var:git 输出物理路径
[ "$(jq -r .parent.slug "$C_MAN")" = "$P_SLUG" ] && [ "$(jq -r .parent.worktree_path "$C_MAN")" = "$P_WT_GIT" ] \
  && ok "子 manifest.parent 双向可溯源" || no "子 manifest.parent"
P_MAN="$P_WT/${STATE_SUBDIR}/task.json"
jq -e --arg c "$C_SLUG" '[.child_tasks[] | .slug] | index($c) != null' "$P_MAN" >/dev/null \
  && ok "父 manifest.child_tasks 已登记子任务" || no "父 manifest.child_tasks"
# 不在管 worktree(无 task.json)内拆任务 → 拒
BARE="$TMP/bare-wt"; git worktree add -q "$BARE" -b bare-side HEAD 2>/dev/null
if ( cd "$BARE" && bash "$PREPARE" new --scenario bug --slug 2026-07-28-orphan --title x --request x \
  --entry-capability explicit-request --entry-evidence "测试夹具" >/dev/null 2>&1 ); then
  no "无 task.json 的 worktree 内拆任务应拒"; else ok "无 task.json 的 worktree 内拆任务被拒"; fi
git worktree remove --force "$BARE" >/dev/null 2>&1; git branch -D bare-side >/dev/null 2>&1
# 清子父 worktree(不进主线,直接强拆)
git worktree remove --force "$C_WT" >/dev/null 2>&1; git branch -D "$C_SLUG" >/dev/null 2>&1
git worktree remove --force "$P_WT" >/dev/null 2>&1; git branch -D "$P_SLUG" >/dev/null 2>&1
git worktree prune >/dev/null 2>&1


echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
