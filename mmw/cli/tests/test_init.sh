#!/usr/bin/env bash
# mmw init。要验的核心是幂等：重跑不覆盖任何已存在的文件，也不追加第二份指针
# 节。另加一条——既没有 CLAUDE.md 也没有 AGENTS.md 时非零退出，不替用户挑一份
# 建，那是这条命令唯一一处要人拿主意的地方。

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
check "铺了 TESTING.md 骨架" "yes" "$([ -f TESTING.md ] && echo yes || echo no)"
check "TESTING.md 是骨架不是填好的" "yes" \
  "$(grep -q '例如' TESTING.md && echo yes || echo no)"
# 守:随 worktree 死的过程材料不能进版本库——把任务 worktree、审查记录或出包状态提交
# 上去,别人拉下来就是一堆跟他无关的中间产物。清单从 .mmw.json 读出来比对,不在这里
# 手抄第二份:抄一份的话,加一个路径就得改两处,漏改的那天测试还是绿的。
missing=""
for key in worktrees reviews release; do
  p="$(jq -r ".paths[\"$key\"]" .mmw.json)/"
  grep -qxF "$p" .gitignore || missing="$missing $key"
done
grep -qxF '.dispatch/' .gitignore || missing="$missing dispatch"
# 图谱几十兆、每次改代码都变。漏掉这一行，第一次建完图它就跟着下一次提交进版本库，
# 而那时没有任何一处会提醒。
grep -qxF 'graphify-out/' .gitignore || missing="$missing graphify-out"
check "配置里声明的过程目录都被 gitignore 挡住" "" "$missing"
check "指针节进了 CLAUDE.md" 1 "$(grep -c '^## 多模型工作流' CLAUDE.md)"
check "装了转发脚本" "yes" \
  "$([ -x "$HOME/.local/bin/mmw" ] && echo yes || echo no)"
check "方法论装进了 CODEX_HOME" "yes" \
  "$([ -e "$CODEX_HOME/skills/mmw-reviewer" ] && echo yes || echo no)"
check "只建缺的标签，已有的两个不重建" 10 \
  "$(grep -c . "$MMW_TEST_CREATED")"
check "建的标签里没有 bug" 0 \
  "$(grep -cx 'bug' "$MMW_TEST_CREATED" || true)"
# 守:配置留在工作区不提交,任务 worktree 检出的分支上就没有它们。.mmw.json 缺席时
# worktree 里每条 mmw 命令都报没配置;.gitignore 缺席时过程材料变成未跟踪文件,
# mmw task cleanup 被它们挡住,git 报的却是「contains untracked files」,看不出真因。
check "配置文件都进了分支，工作区不留" "" "$(git status --porcelain)"
for f in .mmw.json TESTING.md .gitignore CLAUDE.md; do
  check "$f 在分支上" "yes" \
    "$(git cat-file -e "HEAD:$f" 2>/dev/null && echo yes || echo no)"
done

echo
echo "从这个提交建 worktree，过程材料不挡清理"

# 守:上面那几条只证明文件进了分支,不证明它们真管用。这一段跑一遍真实路径——
# 建 worktree、写三种过程材料、非强制清理。gitignore 少一行,这里就会被 git 拦住。
git worktree add -q "$WORK/one-wt" -b task-x
mkdir -p "$WORK/one-wt/.reviews" "$WORK/one-wt/.dispatch" "$WORK/one-wt/.release/delivered"
printf 'x\n' > "$WORK/one-wt/.reviews/r.md"
printf 'x\n' > "$WORK/one-wt/.dispatch/b.md"
printf '{}\n' > "$WORK/one-wt/.release/delivered/p.json"
check "worktree 里这三样都被忽略" "" "$(git -C "$WORK/one-wt" status --porcelain)"
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
check "指针节不追加第二份" 1 "$(grep -c '^## 多模型工作流' CLAUDE.md)"
check "标签一个都不再建" 0 "$(grep -c . "$MMW_TEST_CREATED" || true)"

echo
echo "指针节没处写"

newrepo two
set +e
"$MMW" init > "$WORK/out3" 2>&1
rc=$?
set -e
check "两份都没有时非零退出" "非零" "$(nonzero $rc)"
check "不替用户建 CLAUDE.md" "no" "$([ -f CLAUDE.md ] && echo yes || echo no)"
check "也不替用户建 AGENTS.md" "no" "$([ -f AGENTS.md ] && echo yes || echo no)"
check "报清楚是缺什么" 1 "$(grep -c '既没有 CLAUDE.md 也没有 AGENTS.md' "$WORK/out3")"
check "但前面几步照做" "yes" "$([ -f .mmw.json ] && echo yes || echo no)"

echo
echo "只有 AGENTS.md"

newrepo three
printf '# 约定\n' > AGENTS.md
"$MMW" init > /dev/null 2>&1
check "指针节进 AGENTS.md" 1 "$(grep -c '^## 多模型工作流' AGENTS.md)"
check "不另建 CLAUDE.md" "no" "$([ -f CLAUDE.md ] && echo yes || echo no)"

echo
echo "两份都有"
# 守:AGENTS.md 优先。CLAUDE.md 常被写成纯 import 列表,往里追加正文会把那个形态
# 破坏掉;而那样的仓库通常正好从 CLAUDE.md 引用 AGENTS.md,写进后者一样生效。
newrepo five
printf '@AGENTS.md\n' > CLAUDE.md
printf '# 约定\n' > AGENTS.md
"$MMW" init > /dev/null 2>&1
check "指针节进 AGENTS.md" 1 "$(grep -c '^## 多模型工作流' AGENTS.md)"
check "CLAUDE.md 原样不动" 0 "$(grep -c '^## 多模型工作流' CLAUDE.md)"

echo
echo "旧的 docs/agents/ 还在"

newrepo four
printf '# 项目\n' > CLAUDE.md
mkdir -p docs/agents && printf 'x\n' > docs/agents/issue-tracker.md
"$MMW" init > "$WORK/out4" 2>&1
check "报出来" 1 "$(grep -c '旧副本' "$WORK/out4")"
check "但不删" "yes" \
  "$([ -f docs/agents/issue-tracker.md ] && echo yes || echo no)"

echo
echo "Codex 原生运行面"

newrepo six
printf '# 约定\n' > AGENTS.md
git add AGENTS.md && git commit -qm "加 AGENTS.md"
export HOME="$WORK/home-codex" CODEX_HOME="$WORK/codex-native" MMW_HOST=codex
mkdir -p "$CODEX_HOME/skills"
mmw_plugin_root="$(cd "$HERE/../.." && pwd)"
mmw_plugin_version="$(jq -r .version "$mmw_plugin_root/.codex-plugin/plugin.json")"
mmw_plugin_cache="$CODEX_HOME/plugins/cache/mmw-codex/mmw/$mmw_plugin_version"
mkdir -p "$(dirname "$mmw_plugin_cache")"
cp -R "$mmw_plugin_root" "$mmw_plugin_cache"
mmw_main_root="$(git -C "$HERE/../../.." rev-parse --path-format=absolute --git-common-dir)"
mmw_main_root="$(dirname "$mmw_main_root")"
for skill in mmw-planner mmw-reviewer mmw-tdd; do
  ln -s "$mmw_main_root/mmw/skills/$skill" "$CODEX_HOME/skills/$skill"
done
"$MMW" init > "$WORK/out-codex" 2>&1
check "Codex 装两个只读 agent" "2" \
  "$(find "$CODEX_HOME/agents" -type f -name 'mmw-*.toml' | wc -l | tr -d ' ')"
check "Codex 转发脚本由原生运行时管理" "yes" \
  "$(grep -qF '# Managed by MMW Codex runtime.' "$HOME/.local/bin/mmw" && echo yes || echo no)"
check "Codex 清掉旧 Claude bridge" "no" \
  "$([ -e "$CODEX_HOME/skills/mmw-reviewer" ] && echo yes || echo no)"
check "Codex 不装用户级 MCP" 0 "$(grep -c 'install-mcp' "$WORK/out-codex" || true)"
check "Codex 命令指向已安装 plugin" 1 \
  "$(grep -cF "$mmw_plugin_cache/cli/mmw" "$HOME/.local/bin/mmw")"
check "Codex 项目说明使用原生合同" 1 "$(grep -c '^## MMW 开发工作流' AGENTS.md)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
