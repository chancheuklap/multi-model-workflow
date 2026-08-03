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
"$MMW" init > "$WORK/out1" 2>&1

check "生成了 .mmw.json" "yes" "$([ -f .mmw.json ] && echo yes || echo no)"
check "铺了 TESTING.md 骨架" "yes" "$([ -f TESTING.md ] && echo yes || echo no)"
check "TESTING.md 是骨架不是填好的" "yes" \
  "$(grep -q '例如' TESTING.md && echo yes || echo no)"
check "gitignore 三行" ".worktrees/ .reviews/ .dispatch/" \
  "$(tr '\n' ' ' < .gitignore | sed 's/ $//')"
check "指针节进了 CLAUDE.md" 1 "$(grep -c '^## 多模型工作流' CLAUDE.md)"
check "装了转发脚本" "yes" \
  "$([ -x "$HOME/.local/bin/mmw" ] && echo yes || echo no)"
check "方法论装进了 CODEX_HOME" "yes" \
  "$([ -e "$CODEX_HOME/skills/mmw-reviewer" ] && echo yes || echo no)"
check "只建缺的标签，已有的两个不重建" 10 \
  "$(grep -c . "$MMW_TEST_CREATED")"
check "建的标签里没有 bug" 0 \
  "$(grep -cx 'bug' "$MMW_TEST_CREATED" || true)"

echo
echo "重跑"

printf '本仓库的事实\n' >> TESTING.md
: > "$MMW_TEST_CREATED"
"$MMW" init > "$WORK/out2" 2>&1

check "配置不覆盖" 1 "$(grep -c '已有.*\.mmw\.json' "$WORK/out2")"
check "TESTING.md 不覆盖，人填的内容还在" "yes" \
  "$(grep -q '本仓库的事实' TESTING.md && echo yes || echo no)"
check "gitignore 不重复追加" 3 "$(grep -c . .gitignore)"
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
echo "旧的 docs/agents/ 还在"

newrepo four
printf '# 项目\n' > CLAUDE.md
mkdir -p docs/agents && printf 'x\n' > docs/agents/issue-tracker.md
"$MMW" init > "$WORK/out4" 2>&1
check "报出来" 1 "$(grep -c '旧副本' "$WORK/out4")"
check "但不删" "yes" \
  "$([ -f docs/agents/issue-tracker.md ] && echo yes || echo no)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
