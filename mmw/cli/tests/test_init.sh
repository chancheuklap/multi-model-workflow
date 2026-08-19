#!/usr/bin/env bash
# mmw init。要验的核心是幂等：重跑不覆盖任何已存在的文件，也不追加第二份领域
# 上下文块。它会动用户仓库里的文件，覆盖一次就找不回来。
#
# 装转发脚本和方法论不在这里验：那两件事归 mmw/install.sh，init 只配置目标仓库。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$HERE/../mmw"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
check() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       想要：$want" >&2
    echo "       得到：$got" >&2
    fail=$((fail + 1))
  fi
}
nonzero() { [ "$1" -ne 0 ] && echo 非零 || echo 零; }

# HOME 与 CODEX_HOME 都指到临时目录：init 会往前者装转发脚本、往后者装方法论，
# 不能碰真的。
export HOME="$WORK/home" CODEX_HOME="$WORK/codex" MMW_HOST=claude-code
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$HOME"

mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
  "auth status") ;;
  "label list --limit 200 --json name --jq .[].name") cat "$MMW_TEST_EXISTING" ;;
  "label create "*)
    printf '%s\n' "$3" >> "$MMW_TEST_CREATED"
    printf '%s\n' "$3" >> "$MMW_TEST_EXISTING" ;;
  *) echo "stub gh 没预置：$*" >&2; exit 90 ;;
esac
STUB
chmod +x "$WORK/bin/gh"
export PATH="$WORK/bin:$PATH"
# EXISTING 是 tracker 上现有的标签，建成功就长一条——不这样重跑那一轮验不出
# 「已经建过的不再建」。CREATED 只记本轮建了哪些，每轮开头清空。
export MMW_TEST_CREATED="$WORK/created" MMW_TEST_EXISTING="$WORK/existing"
: > "$MMW_TEST_CREATED"
printf 'bug\nenhancement\n' > "$MMW_TEST_EXISTING"

newrepo() {
  local name="$1"
  git -C "$WORK" init -q -b main "$name"
  cd "$WORK/$name"
  git commit -q --allow-empty -m init
}

echo "首次跑"

newrepo one
printf '# 项目\n' > CLAUDE.md
git add CLAUDE.md && git commit -qm "加 CLAUDE.md"
"$MMW" init > "$WORK/out1" 2>&1

check "生成了 .mmw.json" "yes" "$([ -f .mmw.json ] && echo yes || echo no)"
check "新配置的 paths 只有四个工作目录根" "release,reviews,scratch,worktrees" \
  "$(jq -r '.paths | keys | join(",")' .mmw.json)"
check "新配置没有顶层 wiki" "false" "$(jq 'has("wiki")' .mmw.json)"
check "铺了 TESTING.md 骨架" "yes" "$([ -f TESTING.md ] && echo yes || echo no)"
check "TESTING.md 是骨架不是填好的" "yes" \
  "$(grep -q '例如' TESTING.md && echo yes || echo no)"
# 守:随 worktree 死的过程材料不能进版本库——把任务 worktree、审查记录或出包状态提交
# 上去,别人拉下来就是一堆跟他无关的中间产物。清单从 .mmw.json 读出来比对,不在这里
# 手抄第二份:抄一份的话,加一个路径就得改两处,漏改的那天测试还是绿的。
missing=""
for key in worktrees reviews release scratch; do
  p="$(jq -r ".paths[\"$key\"]" .mmw.json)/"
  grep -qxF "$p" .gitignore || missing="$missing $key"
done
# 图谱几十兆、每次改代码都变。漏掉这一行，第一次建完图它就跟着下一次提交进版本库，
# 而那时没有任何一处会提醒。
grep -qxF 'graphify-out/' .gitignore || missing="$missing graphify-out"
check "配置里声明的过程目录都被 gitignore 挡住" "" "$missing"
check "gitignore 不再忽略退役的派发目录" "0" \
  "$(grep -cxF '.dispatch/' .gitignore || true)"
# 领域上下文块的本体写在 AGENTS.md，CLAUDE.md 只留一行 @AGENTS.md 引用过去。
# 断标记不断标题：标题文案会改，标记是 CLI 认领这一段的凭据（见 lib/context_docs.py）。
check "AGENTS.md 收下领域上下文块" 1 \
  "$(grep -c 'MMW-DOMAIN-CONTEXT-START' AGENTS.md)"
check "块有头有尾" 1 "$(grep -c 'MMW-DOMAIN-CONTEXT-END' AGENTS.md)"
# 用户原有的 CLAUDE.md 不被改写成引用行——那会把他自己写的内容顶掉。
check "已有的 CLAUDE.md 原样留着" "yes" \
  "$(grep -q '^# 项目$' CLAUDE.md && echo yes || echo no)"
check "只建缺的标签，已有的两个不重建" 10 \
  "$(grep -c . "$MMW_TEST_CREATED")"
check "建的标签里没有 bug" 0 \
  "$(grep -cx 'bug' "$MMW_TEST_CREATED" || true)"
# 守:配置留在工作区不提交,任务 worktree 检出的分支上就没有它们。.mmw.json 缺席时
# worktree 里每条 mmw 命令都报没配置;.gitignore 缺席时过程材料变成未跟踪文件,
# mmw worktree remove 被它们挡住,git 报的却是「contains untracked files」,看不出真因。
check "配置文件都进了分支，工作区不留" "" "$(git status --porcelain)"
for f in .mmw.json TESTING.md .gitignore CLAUDE.md; do
  check "$f 在分支上" "yes" \
    "$(git cat-file -e "HEAD:$f" 2>/dev/null && echo yes || echo no)"
done

echo
echo "从这个提交建 worktree，过程材料不挡清理"

# 守:上面那几条只证明文件进了分支,不证明它们真管用。这一段跑一遍真实路径——
# 建 worktree、写四个工作目录根的过程材料、非强制清理。gitignore 少一行,这里就会被 git 拦住。
git worktree add -q "$WORK/one-wt" -b task-x
mkdir -p "$WORK/one-wt/.reviews" "$WORK/one-wt/.scratch/session" \
  "$WORK/one-wt/.release/delivered" "$WORK/one-wt/.worktrees/child"
printf 'x\n' > "$WORK/one-wt/.reviews/r.md"
printf 'x\n' > "$WORK/one-wt/.scratch/session/note.md"
printf '{}\n' > "$WORK/one-wt/.release/delivered/p.json"
printf 'x\n' > "$WORK/one-wt/.worktrees/child/state"
check "worktree 里四个工作目录根都被忽略" "" "$(git -C "$WORK/one-wt" status --porcelain)"
set +e
git worktree remove "$WORK/one-wt" > "$WORK/wtrm" 2>&1
rc=$?
set -e
check "非强制清理不被过程材料挡住" "零" "$(nonzero $rc)"
check "目录连同过程材料一起没了" "no" \
  "$([ -d "$WORK/one-wt" ] && echo yes || echo no)"
git branch -q -D task-x

echo
echo "重跑"

printf '本仓库的事实\n' >> TESTING.md
: > "$MMW_TEST_CREATED"
"$MMW" init > "$WORK/out2" 2>&1

check "配置不覆盖" 1 "$(grep -c '已有.*\.mmw\.json' "$WORK/out2")"
check "TESTING.md 不覆盖，人填的内容还在" "yes" \
  "$(grep -q '本仓库的事实' TESTING.md && echo yes || echo no)"
# 守:重跑 init 是常事(换机器、加了新配置),每跑一次就往 .gitignore 里追加一遍同样的行,
# 那个文件会越滚越长。断有没有重复行,不断总行数——总行数会随配置增删而变,那不是合同。
check "gitignore 不重复追加" "" "$(sort .gitignore | uniq -d | tr '\n' ' ' | sed 's/ $//')"
check "领域上下文块不追加第二份" 1 \
  "$(grep -c 'MMW-DOMAIN-CONTEXT-START' AGENTS.md)"
check "标签一个都不再建" 0 "$(grep -c . "$MMW_TEST_CREATED" || true)"

echo
echo "迁移已有配置"

newrepo legacy-config
cp "$HERE/../mmw.default.json" .mmw.json
jq '
  .paths.scratch = ".private-scratch" |
  .paths.reviews = ".private-reviews" |
  .paths.release = ".private-release" |
  .paths.worktrees = ".private-worktrees" |
  .paths.specs = "old-specs" |
  .paths.plans = "old-plans" |
  .paths.prototypes = "old-prototypes" |
  .paths.research = "old-research" |
  .paths.evidence = "old-evidence"
' .mmw.json > .mmw.json.next
mv .mmw.json.next .mmw.json
git add .mmw.json && git commit -qm "加旧配置"
"$MMW" init > "$WORK/out-legacy-config" 2>&1
check "迁移后 paths 只有四个工作目录根" "release,reviews,scratch,worktrees" \
  "$(jq -r '.paths | keys | join(",")' .mmw.json)"
check "迁移保留四个工作目录根的现有取值" \
  ".private-scratch,.private-reviews,.private-release,.private-worktrees" \
  "$(jq -r '[.paths.scratch, .paths.reviews, .paths.release, .paths.worktrees] | join(",")' .mmw.json)"
check "迁移删除五个旧路径键" "0" \
  "$(jq '[.paths.specs, .paths.plans, .paths.prototypes, .paths.research, .paths.evidence] | map(select(. != null)) | length' .mmw.json)"
check "迁移删除顶层 wiki" "false" "$(jq 'has("wiki")' .mmw.json)"

jq '.wiki = null' .mmw.json > .mmw.json.next
mv .mmw.json.next .mmw.json
git add .mmw.json && git commit -qm "加空的 wiki 键"
"$MMW" init > "$WORK/out-null-wiki" 2>&1
check "迁移删除值为空的顶层 wiki 键" "false" "$(jq 'has("wiki")' .mmw.json)"

jq '
  .paths.specs = null |
  .paths.plans = null |
  .paths.prototypes = null |
  .paths.research = null |
  .paths.evidence = null |
  .paths.investigations = null
' .mmw.json > .mmw.json.next
mv .mmw.json.next .mmw.json
git add .mmw.json && git commit -qm "加值为空的旧路径键"
"$MMW" init > "$WORK/out-null-legacy-paths" 2>&1
check "迁移删除值为空的旧路径键" "" \
  "$(jq -r '.paths | keys - ["release", "reviews", "scratch", "worktrees"] | join(",")' .mmw.json)"
check "迁移值为空的旧路径键时保留四个工作目录根的现有取值" \
  ".private-scratch,.private-reviews,.private-release,.private-worktrees" \
  "$(jq -r '[.paths.scratch, .paths.reviews, .paths.release, .paths.worktrees] | join(",")' .mmw.json)"

echo
echo "两份都没有"
# 空仓库上 init 要能一次配好，不停下来问该往哪写：块的本体固定进 AGENTS.md，
# CLAUDE.md 建成一行引用。这两份都是新建，没有任何用户内容会被顶掉。
newrepo two
set +e
"$MMW" init > "$WORK/out3" 2>&1
rc=$?
set -e
check "照配不报错" "零" "$(nonzero $rc)"
check "建出 AGENTS.md" "yes" "$([ -f AGENTS.md ] && echo yes || echo no)"
check "块进 AGENTS.md" 1 "$(grep -c 'MMW-DOMAIN-CONTEXT-START' AGENTS.md)"
check "CLAUDE.md 是一行引用" "@AGENTS.md" "$(cat CLAUDE.md)"
check "前面几步照做" "yes" "$([ -f .mmw.json ] && echo yes || echo no)"

echo
echo "只有 AGENTS.md"

newrepo three
printf '# 约定\n' > AGENTS.md
git add AGENTS.md && git commit -qm "加 AGENTS.md"
"$MMW" init > /dev/null 2>&1
check "块进 AGENTS.md" 1 "$(grep -c 'MMW-DOMAIN-CONTEXT-START' AGENTS.md)"
check "用户原有内容还在" "yes" \
  "$(grep -q '^# 约定$' AGENTS.md && echo yes || echo no)"

echo
echo "目标文件还没跟踪或者不干净"
# 守:往一个有未提交改动的文件里追加块,再一起提交,会把用户那半截改动也带进去。
# 所以这里拒绝,并且非零退出——它不是"顺手跳过"的一步。
newrepo six
printf '# 约定\n' > AGENTS.md          # 建了但没提交
set +e
"$MMW" init > "$WORK/out6" 2>&1
rc=$?
set -e
check "拒绝写块并非零退出" "非零" "$(nonzero $rc)"
check "说清楚是哪个文件挡住了" 1 "$(grep -c 'dirty-target' "$WORK/out6")"
check "用户那份原样不动" "yes" \
  "$(grep -qx '# 约定' AGENTS.md && [ "$(wc -l < AGENTS.md)" -eq 1 ] && echo yes || echo no)"

echo
echo "两份都有"
# 守:块只进 AGENTS.md。CLAUDE.md 常被写成纯 import 列表,往里追加正文会把那个形态
# 破坏掉;而那样的仓库通常正好从 CLAUDE.md 引用 AGENTS.md,写进后者一样生效。
newrepo five
printf '@AGENTS.md\n' > CLAUDE.md
printf '# 约定\n' > AGENTS.md
git add CLAUDE.md AGENTS.md && git commit -qm "加两份"
"$MMW" init > /dev/null 2>&1
check "块进 AGENTS.md" 1 "$(grep -c 'MMW-DOMAIN-CONTEXT-START' AGENTS.md)"
check "CLAUDE.md 原样不动" "@AGENTS.md" "$(cat CLAUDE.md)"

echo
echo "旧的 docs/agents/ 还在"

newrepo four
printf '# 项目\n' > CLAUDE.md
mkdir -p docs/agents && printf 'x\n' > docs/agents/issue-tracker.md
git add CLAUDE.md docs && git commit -qm "加 CLAUDE.md 与旧 docs/agents"
"$MMW" init > "$WORK/out4" 2>&1
check "报出来" 1 "$(grep -c '旧副本' "$WORK/out4")"
check "但不删" "yes" \
  "$([ -f docs/agents/issue-tracker.md ] && echo yes || echo no)"

echo
echo "doctor 只读报告"

# doctor 会真的运行 MCP 探针。这里替换三个外部服务器进程，保留探针、合同校验和
# doctor 本身。每个替身只返回该服务器公开合同里的工具集合。
export MMW_TEST_PYTHON3="$(command -v python3)"
cat > "$WORK/bin/serena" <<'STUB'
#!/usr/bin/env bash
cat > /dev/null
printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"find_implementations"},{"name":"find_referencing_symbols"},{"name":"find_symbol"},{"name":"get_symbols_overview"}]}}'
STUB
cat > "$WORK/bin/npx" <<'STUB'
#!/usr/bin/env bash
cat > /dev/null
printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"query-docs"},{"name":"resolve-library-id"}]}}'
STUB
cat > "$WORK/bin/python3" <<'STUB'
#!/usr/bin/env bash
case "${1:-}" in
  */mcp/graphify_mcp.py)
    cat > /dev/null
    printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"graphify"}]}}'
    ;;
  *) exec "$MMW_TEST_PYTHON3" "$@" ;;
esac
STUB
cat > "$WORK/bin/git-credential-mmw-test" <<'STUB'
#!/usr/bin/env bash
if [ "${1:-}" = "get" ]; then
  printf 'username=test\npassword=test\n'
fi
STUB
cat > "$WORK/bin/codex" <<'STUB'
#!/usr/bin/env bash
exit 0
STUB
chmod +x "$WORK/bin/serena" "$WORK/bin/npx" "$WORK/bin/python3" \
  "$WORK/bin/git-credential-mmw-test" "$WORK/bin/codex"

export MMW_HOST=claude-code
export GIT_CONFIG_GLOBAL="$WORK/gitconfig-global" GIT_CONFIG_SYSTEM=/dev/null
: > "$GIT_CONFIG_GLOBAL"
mkdir -p "$CODEX_HOME/skills/mmw-reviewer"

# doctor 除了看目标仓库，还看这台机器装没装。沙箱的 HOME 是空的，所以先在沙箱里
# 按真安装器装一遍。手工摆几个文件也能骗过检查，但摆出来的样子会跟安装器的产出
# 各走各的，那时这几条用例就不再验安装。
MMW_SRC="$HERE/../.."
bash "$MMW_SRC/cli/lib/install-skills.sh" --dest "$HOME/.claude/skills" > /dev/null
mkdir -p "$HOME/.claude/agents"
ln -sfn "$MMW_SRC/agents/mmw-reviewer-claude.md" "$HOME/.claude/agents/mmw-reviewer-claude.md"
bash "$MMW_SRC/mcp/install-mcp.sh" > /dev/null

newrepo doctor
"$MMW" init > "$WORK/out-doctor-init" 2>&1
git config credential.helper "$WORK/bin/git-credential-mmw-test"

set +e
"$MMW" doctor > "$WORK/out-doctor-clean" 2>&1
clean_rc=$?
set -e
if [ "$clean_rc" -ne 0 ]; then
  sed 's/^/       /' "$WORK/out-doctor-clean" >&2
fi
check "没有遗留项时 doctor 通过" "零" "$(nonzero "$clean_rc")"
check "推送鉴权成功输出保持不变" 1 \
  "$(grep -cxF '推送鉴权 : github.com 的 https 凭据有人答得上' "$WORK/out-doctor-clean" || true)"

mkdir -p docs/evidence .dispatch docs/specs/legacy-spec \
  docs/plans/legacy-plan docs/research/legacy-research \
  .scratch/old-internal .reviews/old-internal
printf 'old\n' > docs/evidence/screenshot.png
printf 'old\n' > .dispatch/task.txt
printf 'old\n' > docs/specs/legacy-spec/legacy-spec.md
printf 'normal\n' > docs/plans/legacy-plan/01-plan.md
printf 'normal\n' > docs/research/legacy-research/report.md
printf 'normal\n' > .scratch/old-internal/note.md
printf 'normal\n' > .reviews/old-internal/review.md
jq '
  .paths.specs = "old-specs" |
  .paths.plans = "old-plans" |
  .paths.prototypes = "old-prototypes" |
  .paths.research = "old-research" |
  .paths.evidence = "old-evidence" |
  .wiki = {"kind": "github-wiki"}
' .mmw.json > .mmw.json.next
mv .mmw.json.next .mmw.json
git add .mmw.json && git commit -qm "恢复遗留配置"

snapshot_tree() {
  {
    find . -path './.git' -prune -o -type d -print
    find . -path './.git' -prune -o -type f -print
    find . -path './.git' -prune -o -type f -exec shasum {} \;
  } | LC_ALL=C sort
}
before_doctor="$(snapshot_tree)"
set +e
"$MMW" doctor > "$WORK/out-doctor-legacy" 2>&1
legacy_rc=$?
set -e
after_doctor="$(snapshot_tree)"

check "遗留报告不改变 doctor 的通过退出码" "零" "$(nonzero "$legacy_rc")"
check "报告退役的证据目录" 1 \
  "$(grep -cxF '历史产物 : 已退役路径 docs/evidence/' "$WORK/out-doctor-legacy" || true)"
check "报告退役的派发目录" 1 \
  "$(grep -cxF '历史产物 : 已退役路径 .dispatch/' "$WORK/out-doctor-legacy" || true)"
check "报告旧文件名的 spec" 1 \
  "$(grep -cxF '历史产物 : 已退役路径 docs/specs/legacy-spec/legacy-spec.md' "$WORK/out-doctor-legacy" || true)"
for key in specs plans prototypes research evidence; do
  check "报告退役配置 paths.$key" 1 \
    "$(grep -cxF "遗留配置 : .mmw.json 的 paths.$key 已退役" "$WORK/out-doctor-legacy" || true)"
done
check "报告退役配置 wiki" 1 \
  "$(grep -cxF '遗留配置 : .mmw.json 的 wiki 已退役' "$WORK/out-doctor-legacy" || true)"
check "不报告 plan 名字段" 0 \
  "$(grep -cF 'docs/plans/legacy-plan' "$WORK/out-doctor-legacy" || true)"
check "不报告 research 名字段" 0 \
  "$(grep -cF 'docs/research/legacy-research' "$WORK/out-doctor-legacy" || true)"
check "不报告 scratch 内部细分" 0 \
  "$(grep -cF '.scratch/old-internal' "$WORK/out-doctor-legacy" || true)"
check "不报告 reviews 内部细分" 0 \
  "$(grep -cF '.reviews/old-internal' "$WORK/out-doctor-legacy" || true)"
check "doctor 不修改配置或历史产物" "$before_doctor" "$after_doctor"

set +e
"$MMW" init > "$WORK/out-doctor-migrate" 2>&1
doctor_init_rc=$?
set -e
if [ "$doctor_init_rc" -ne 0 ]; then
  sed 's/^/       /' "$WORK/out-doctor-migrate" >&2
fi
check "doctor 报告后 init 仍通过" "零" "$(nonzero "$doctor_init_rc")"
check "doctor 报告后 init 删除六个退役配置键" "0" \
  "$(jq '[.paths.specs, .paths.plans, .paths.prototypes, .paths.research, .paths.evidence, .wiki] | map(select(. != null)) | length' .mmw.json)"
check "init 不删除已有派发目录" "yes" "$([ -d .dispatch ] && echo yes || echo no)"
check "init 不删除已有证据目录" "yes" "$([ -d docs/evidence ] && echo yes || echo no)"

git config --unset-all credential.helper
set +e
"$MMW" doctor > "$WORK/out-doctor-no-auth" 2>&1
no_auth_rc=$?
set -e
check "缺少推送凭据时 doctor 仍失败" "非零" "$(nonzero "$no_auth_rc")"
check "推送鉴权修复命令保持不变" 1 \
  "$(grep -c '推送鉴权.*gh auth setup-git' "$WORK/out-doctor-no-auth" || true)"
check "推送鉴权提示不再限定 Wiki" 0 \
  "$(grep -c '推 Wiki 要它' "$WORK/out-doctor-no-auth" || true)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
