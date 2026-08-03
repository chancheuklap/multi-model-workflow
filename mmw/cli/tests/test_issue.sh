#!/usr/bin/env bash
# issue 子命令的过滤与排序。gh 换成 stub，不碰真仓库。
#
# 要验的是三件在真仓库里难得凑齐的事：乱序返回照样按编号升序、四条过滤条件
# 各自生效、sub_issues 端点没带依赖摘要时逐个补齐那条退路。

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

# 乱序给：3 号在前、1 号在后。1 号可开工，2 号被挡，3 号有人认领，
# 4 号关掉了，5 号可开工但没有 ready-for-agent 标签。
cat > "$WORK/children.json" <<'JSON'
[
  {"number": 3, "state": "open", "title": "有人在做",
   "assignees": [{"login": "someone"}], "labels": [{"name": "ready-for-agent"}],
   "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 5, "state": "open", "title": "还没准备好",
   "assignees": [], "labels": [],
   "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 1, "state": "open", "title": "可以开工",
   "assignees": [], "labels": [{"name": "ready-for-agent"}],
   "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 4, "state": "closed", "title": "做完了",
   "assignees": [], "labels": [{"name": "ready-for-agent"}],
   "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 2, "state": "open", "title": "被 1 挡着",
   "assignees": [], "labels": [{"name": "ready-for-agent"}],
   "issue_dependencies_summary": {"blocked_by": 1}}
]
JSON

# 同一批，但去掉依赖摘要——试 sub_issues 端点不带这个字段时的退路。
jq 'map(del(.issue_dependencies_summary))' "$WORK/children.json" > "$WORK/children-nodeps.json"
# 逐个补齐时单查返回的那一份。
jq 'map({(.number | tostring): .}) | add' "$WORK/children.json" > "$WORK/bynumber.json"

mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
  "repo view --json nameWithOwner -q .nameWithOwner")
    echo "o/r" ;;
  "api --paginate repos/o/r/issues/100/sub_issues")
    cat "$MMW_TEST_LIST" ;;
  "api repos/o/r/issues/"*)
    n="${1##*/}"
    # 单查某一张：从按编号索引的那份里取
    jq -c --arg n "${*##* }" '.[($n | split("/") | last)]' "$MMW_TEST_BYNUM" 2>/dev/null \
      || jq -c ".[\"$n\"]" "$MMW_TEST_BYNUM" ;;
  *)
    echo "stub gh: 没预置这条命令：$*" >&2
    exit 90 ;;
esac
STUB
chmod +x "$WORK/bin/gh"
export PATH="$WORK/bin:$PATH"
export MMW_TEST_BYNUM="$WORK/bynumber.json"
export MMW_HOST=claude-code

# CLI 要在一个 git 仓库里、且有 .mmw.json 才跑得起来。
git -C "$WORK" init -q repo
cp "$HERE/../mmw.default.json" "$WORK/repo/.mmw.json"
cd "$WORK/repo"

echo "issue frontier / children"

export MMW_TEST_LIST="$WORK/children.json"

got="$("$MMW" issue frontier 100 | tr '\t' ' ' | tr '\n' ';')"
check "frontier 只留可开工的，按编号升序" "1 可以开工;5 还没准备好;" "$got"

got="$("$MMW" issue frontier 100 --label ready-for-agent | tr '\t' ' ' | tr '\n' ';')"
check "frontier 加标签过滤" "1 可以开工;" "$got"

got="$("$MMW" issue children 100 | cut -f1 | tr '\n' ' ')"
check "children 给出全部，按编号升序" "1 2 3 4 5 " "$got"

got="$("$MMW" issue children 100 | awk -F'\t' '$1 == 3 {print $3}')"
check "children 报出认领人" "someone" "$got"

got="$("$MMW" issue children 100 | awk -F'\t' '$1 == 2 {print $4}')"
check "children 报出被几张挡着" "1" "$got"

export MMW_TEST_LIST="$WORK/children-nodeps.json"
got="$("$MMW" issue frontier 100 | tr '\t' ' ' | tr '\n' ';')"
check "列表缺依赖摘要时逐个补齐" "1 可以开工;5 还没准备好;" "$got"

echo
echo "过 ${pass}，失败 $fail"
[ "$fail" -eq 0 ]
