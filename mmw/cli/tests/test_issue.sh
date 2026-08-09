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
# 逐个补齐时单查返回的那一份。database id 一律是编号加一千，用来验连依赖边取的
# 是 database id 而不是 #编号。
jq 'map({(.number | tostring): (. + {id: (.number + 1000)})}) | add' \
  "$WORK/children.json" > "$WORK/bynumber.json"

mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${MMW_TEST_LOG:-/dev/null}"
case "$*" in
  "repo view --json nameWithOwner -q .nameWithOwner")
    echo "o/r" ;;
  "api --paginate repos/o/r/issues/100/sub_issues")
    cat "$MMW_TEST_LIST" ;;
  "api user --jq .login")
    echo "me" ;;
  "issue create "*)
    echo "https://github.com/o/r/issues/42" ;;
  "issue edit "*"--add-assignee @me")
    printf '%s\n' "$3" >> "$MMW_TEST_CLAIMED" ;;
  "api --method POST repos/o/r/issues/"*)
    echo '{}' ;;
  "api repos/o/r/issues/"*)
    n="${2##*/}"
    obj="$(jq -c --arg n "$n" '
      .[$n] // {number: ($n | tonumber), id: (($n | tonumber) + 1000),
                state: "open", title: "新建的", assignees: [], labels: []}
      ' "$MMW_TEST_BYNUM")"
    if grep -qx "$n" "$MMW_TEST_CLAIMED" 2> /dev/null; then
      obj="$(jq -c '.assignees = [{"login": "me"}]' <<<"$obj")"
    fi
    if [ "${3:-}" = "--jq" ]; then
      jq -r "$4" <<<"$obj"
    else
      printf '%s\n' "$obj"
    fi ;;
  *)
    echo "stub gh: 没预置这条命令：$*" >&2
    exit 90 ;;
esac
STUB
chmod +x "$WORK/bin/gh"
export PATH="$WORK/bin:$PATH"
export MMW_TEST_BYNUM="$WORK/bynumber.json"
export MMW_TEST_CLAIMED="$WORK/claimed"
: > "$MMW_TEST_CLAIMED"
export MMW_HOST=claude-code

nonzero() { [ "$1" -ne 0 ] && echo 非零 || echo 零; }
posts() { grep -F -- '--method POST' "$1" | tr '\n' ';'; }

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

# 下面三条是写命令。它们收进 CLI 的全部理由就是要连着发好几个请求、而且中间
# 要先取 database id——所以断言的是发出去的请求序列，不只是最后那行输出。
echo
echo "issue create"

printf '一段正文\n' > "$WORK/body.md"

export MMW_TEST_LOG="$WORK/log-create"
: > "$MMW_TEST_LOG"
got="$("$MMW" issue create --title "新 ticket" --body-file "$WORK/body.md" \
  --parent 100 --blocked-by 1,2 --label ready-for-agent)"
check "create 输出新 issue 的编号" "42" "$got"
check "create 依次挂父、连两条阻塞边，用的都是 database id" \
  "api --method POST repos/o/r/issues/100/sub_issues -F sub_issue_id=1042;api --method POST repos/o/r/issues/42/dependencies/blocked_by -F issue_id=1001;api --method POST repos/o/r/issues/42/dependencies/blocked_by -F issue_id=1002;" \
  "$(posts "$MMW_TEST_LOG")"
check "create 把标签一次带上，不另发请求" 1 \
  "$(grep -c -- '--label ready-for-agent' "$MMW_TEST_LOG")"

export MMW_TEST_LOG="$WORK/log-create-bare"
: > "$MMW_TEST_LOG"
"$MMW" issue create --title "光杆" --body-file "$WORK/body.md" > /dev/null
check "不给 --parent 与 --blocked-by 时一条 POST 都不发" "" \
  "$(posts "$MMW_TEST_LOG")"

set +e
"$MMW" issue create --body-file "$WORK/body.md" > /dev/null 2>&1
rc=$?
set -e
check "create 缺 --title 时失败" "非零" "$(nonzero $rc)"

export MMW_TEST_LOG="$WORK/log-create-nobody"
: > "$MMW_TEST_LOG"
set +e
"$MMW" issue create --title "x" --body-file "$WORK/没有这个文件.md" > /dev/null 2>&1
rc=$?
set -e
check "正文文件不存在时失败" "非零" "$(nonzero $rc)"
check "而且失败在建 issue 之前，不留孤儿" "" \
  "$(grep -F 'issue create' "$MMW_TEST_LOG" || true)"

echo
echo "issue link"

export MMW_TEST_LOG="$WORK/log-link"
: > "$MMW_TEST_LOG"
got="$("$MMW" issue link 5 --blocked-by 3)"
check "link 报出关系" "#5 被 #3 挡着" "$got"
check "link 取阻塞方的 database id" \
  "api --method POST repos/o/r/issues/5/dependencies/blocked_by -F issue_id=1003;" \
  "$(posts "$MMW_TEST_LOG")"

echo
echo "issue claim"

export MMW_TEST_LOG="$WORK/log-claim-taken"
: > "$MMW_TEST_LOG"
set +e
"$MMW" issue claim 3 > /dev/null 2>&1
rc=$?
set -e
check "已被别人认领时失败" "非零" "$(nonzero $rc)"
check "而且不发指派请求" "" "$(grep -F 'issue edit' "$MMW_TEST_LOG" || true)"

export MMW_TEST_LOG="$WORK/log-claim"
: > "$MMW_TEST_LOG"
got="$("$MMW" issue claim 1)"
check "没人占时认领成功" "#1 已认领" "$got"
check "指派之后再读一次确认落在自己头上" 2 \
  "$(grep -c 'api repos/o/r/issues/1 ' "$MMW_TEST_LOG")"

set +e
"$MMW" issue claim 1 > /dev/null 2>&1
rc=$?
set -e
check "同一张再认领一次就失败" "非零" "$(nonzero $rc)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
