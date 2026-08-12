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

contains() {
  local name="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       没找到：$needle" >&2
    echo "       实际：$haystack" >&2
    fail=$((fail + 1))
  fi
}

capture() {
  local label="$1"
  shift
  LAST_OUT="$WORK/${label}.out"
  LAST_ERR="$WORK/${label}.err"
  if "$@" >"$LAST_OUT" 2>"$LAST_ERR"; then
    LAST_STATUS=0
  else
    LAST_STATUS=$?
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

counter_increment() {
  local name="$1" dir="$MMW_TEST_CONCURRENT_DIR" lock="$MMW_TEST_CONCURRENT_DIR/lock"
  while ! mkdir "$lock" 2> /dev/null; do
    /bin/sleep 0.01
  done
  local n=0
  [ ! -f "$dir/$name" ] || n="$(cat "$dir/$name")"
  n=$((n + 1))
  printf '%s\n' "$n" > "$dir/$name"
  rmdir "$lock"
  printf '%s\n' "$n"
}

counter_value() {
  local name="$1"
  if [ -f "$MMW_TEST_CONCURRENT_DIR/$name" ]; then
    cat "$MMW_TEST_CONCURRENT_DIR/$name"
  else
    echo 0
  fi
}

wait_for_counter() {
  local name="$1" wanted="$2" current=0
  while [ "$current" -lt "$wanted" ]; do
    current="$(counter_value "$name")"
    [ "$current" -ge "$wanted" ] || /bin/sleep 0.01
  done
}

issue_body_path() {
  printf '%s/%s.body\n' "$MMW_TEST_ISSUE_DIR" "$1"
}

read_body() {
  local n="$1" path read_count
  path="$(issue_body_path "$n")"
  if [ -n "${MMW_TEST_CONCURRENT_DIR:-}" ]; then
    read_count="$(counter_increment reads)"
    if [ "$read_count" -le 2 ]; then
      wait_for_counter reads 2
    else
      wait_for_counter writes 2
    fi
  else
    read_count=0
    if [ -n "${MMW_TEST_READ_COUNT:-}" ]; then
      read_count="$(cat "$MMW_TEST_READ_COUNT")"
    fi
    read_count=$((read_count + 1))
    printf '%s\n' "$read_count" > "$MMW_TEST_READ_COUNT"
  fi

  case ",${MMW_TEST_MUTATE_READS:-}," in
    *,"$read_count",*) printf '%s' "$MMW_TEST_MUTATE_BODY" > "$path" ;;
  esac
  cat "$path"
}

write_body() {
  local n="$1" source="$2" path body writes
  path="$(issue_body_path "$n")"
  body="$(cat "$source")"
  if [ -n "${MMW_TEST_CONCURRENT_DIR:-}" ]; then
    writes="$(counter_value writes)"
    if [ "$writes" -eq 0 ] && grep -Fqx 'B-append' <<<"$body" && ! grep -Fqx 'A-append' <<<"$body"; then
      wait_for_counter a-written 1
    fi
    if grep -Fqx 'A-append' <<<"$body" && ! grep -Fqx 'B-append' <<<"$body"; then
      printf '1\n' > "$MMW_TEST_CONCURRENT_DIR/a-written"
    fi
    counter_increment writes > /dev/null
  fi
  printf '%s' "$body" > "$path"
}

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
  "issue edit "*"--body-file "*)
    write_body "$3" "$5" ;;
  "api --method POST repos/o/r/issues/"*)
    if [ "${MMW_TEST_FAIL_SET_PARENT:-}" = 1 ]; then
      echo "stub gh: sub_issues endpoint unavailable" >&2
      exit 71
    fi
    echo '{}' ;;
  "api repos/o/r/issues/"*)
    n="${2##*/}"
    if [ "${3:-}" = "--jq" ] && [ "${4:-}" = ".body" ]; then
      read_body "$n"
    else
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
      fi
    fi ;;
  *)
    echo "stub gh: 没预置这条命令：$*" >&2
    exit 90 ;;
esac
STUB
chmod +x "$WORK/bin/gh"
cat > "$WORK/bin/sleep" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
printf 'sleep %s\n' "$*" >> "${MMW_TEST_LOG:-/dev/null}"
STUB
chmod +x "$WORK/bin/sleep"
export PATH="$WORK/bin:$PATH"
export MMW_TEST_BYNUM="$WORK/bynumber.json"
export MMW_TEST_CLAIMED="$WORK/claimed"
export MMW_TEST_ISSUE_DIR="$WORK/issues"
export MMW_TEST_READ_COUNT="$WORK/read-count"
mkdir -p "$MMW_TEST_ISSUE_DIR"
: > "$MMW_TEST_CLAIMED"
export MMW_HOST=claude-code

nonzero() { [ "$1" -ne 0 ] && echo 非零 || echo 零; }
posts() { grep -F -- '--method POST' "$1" | tr '\n' ';'; }
body_set() { printf '%s' "$2" > "$MMW_TEST_ISSUE_DIR/$1.body"; }
body_get() { cat "$MMW_TEST_ISSUE_DIR/$1.body"; }
append_events() {
  sed -E '/^repo view /d; s|issue edit ([0-9]+) --body-file .*|issue edit \1 --body-file <文件>|' "$1" | tr '\n' ';'
}

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
echo "issue append"

append_body='## Decisions so far

原有决定

## Destination
仍在这里'
append_written='## Decisions so far

原有决定
新的决定

## Destination
仍在这里'

body_set 100 "$append_body"
export MMW_TEST_LOG="$WORK/log-append-arguments"
: > "$MMW_TEST_LOG"
capture "append-缺编号" "$MMW" issue append --section "Decisions so far" --line "新的决定"
check "append 缺 issue 编号时失败" "非零" "$(nonzero "$LAST_STATUS")"
check "append 缺 issue 编号时不写正文" "" "$(grep -F 'issue edit' "$MMW_TEST_LOG" || true)"

capture "append-缺小节" "$MMW" issue append 100 --line "新的决定"
check "append 缺小节时失败" "非零" "$(nonzero "$LAST_STATUS")"
check "append 缺小节时不写正文" "" "$(grep -F 'issue edit' "$MMW_TEST_LOG" || true)"

capture "append-缺内容" "$MMW" issue append 100 --section "Decisions so far"
check "append 缺内容时失败" "非零" "$(nonzero "$LAST_STATUS")"
check "append 缺内容时不写正文" "" "$(grep -F 'issue edit' "$MMW_TEST_LOG" || true)"
contains "append 缺内容时显示更新后的 issue 用法" "mmw issue set-parent" "$(cat "$LAST_ERR")"

body_set 100 "$append_body"
: > "$MMW_TEST_READ_COUNT"
unset MMW_TEST_MUTATE_READS MMW_TEST_MUTATE_BODY MMW_TEST_CONCURRENT_DIR
export MMW_TEST_LOG="$WORK/log-append-five-steps"
: > "$MMW_TEST_LOG"
capture "append-成功" "$MMW" issue append 100 --section "Decisions so far" --line "新的决定"
check "append 成功退出" "0" "$LAST_STATUS"
check "append 在指定小节末尾插入一行" "$append_written" "$(body_get 100)"
check "append 依次读、写、等两秒、重读" \
  'api repos/o/r/issues/100 --jq .body;issue edit 100 --body-file <文件>;sleep 2;api repos/o/r/issues/100 --jq .body;' \
  "$(append_events "$MMW_TEST_LOG")"

body_set 100 "$append_written"
: > "$MMW_TEST_READ_COUNT"
unset MMW_TEST_MUTATE_READS MMW_TEST_MUTATE_BODY MMW_TEST_CONCURRENT_DIR
export MMW_TEST_LOG="$WORK/log-append-existing-line"
: > "$MMW_TEST_LOG"
capture "append-目标行已存在" "$MMW" issue append 100 --section "Decisions so far" --line "新的决定"
check "目标行已存在时正常收敛" "0" "$LAST_STATUS"
check "目标行已存在时不抛 bash 错误" "" "$(cat "$LAST_ERR")"
check "目标行已存在时正文不变" "$append_written" "$(body_get 100)"

body_set 100 "$append_body"
: > "$MMW_TEST_READ_COUNT"
export MMW_TEST_MUTATE_READS=2
export MMW_TEST_MUTATE_BODY="$append_body"
export MMW_TEST_LOG="$WORK/log-append-own-line"
: > "$MMW_TEST_LOG"
capture "append-自己的行丢失" "$MMW" issue append 100 --section "Decisions so far" --line "新的决定"
check "自己的新增行丢失时重做后成功" "0" "$LAST_STATUS"
check "自己的新增行丢失后仍在" "$append_written" "$(body_get 100)"
check "自己的新增行丢失时写两次" "2" "$(grep -c '^issue edit' "$MMW_TEST_LOG")"

body_set 100 "$append_body"
: > "$MMW_TEST_READ_COUNT"
export MMW_TEST_MUTATE_READS=2
export MMW_TEST_MUTATE_BODY='## Decisions so far

## Destination
仍在这里'
export MMW_TEST_LOG="$WORK/log-append-v1-line"
: > "$MMW_TEST_LOG"
capture "append-V1-行丢失" "$MMW" issue append 100 --section "Decisions so far" --line "新的决定"
check "V1 行丢失时重做后成功" "0" "$LAST_STATUS"
contains "V1 行丢失后恢复原有决定" "原有决定" "$(body_get 100)"
contains "V1 行丢失后保留新增决定" "新的决定" "$(body_get 100)"
check "V1 行丢失时写两次" "2" "$(grep -c '^issue edit' "$MMW_TEST_LOG")"

append_blank_line_lost='## Decisions so far
原有决定
新的决定

## Destination
仍在这里'
append_blank_line_restored='## Decisions so far
原有决定
新的决定


## Destination
仍在这里'
body_set 100 "$append_body"
: > "$MMW_TEST_READ_COUNT"
export MMW_TEST_MUTATE_READS=2
export MMW_TEST_MUTATE_BODY="$append_blank_line_lost"
unset MMW_TEST_CONCURRENT_DIR
export MMW_TEST_LOG="$WORK/log-append-v1-blank-line"
: > "$MMW_TEST_LOG"
capture "append-V1-空行丢失" "$MMW" issue append 100 --section "Decisions so far" --line "新的决定"
check "V1 只丢空行时重做后成功" "0" "$LAST_STATUS"
check "V1 只丢空行时恢复空行数量" "$append_blank_line_restored" "$(body_get 100)"
check "V1 只丢空行的桩触发重做" "2" "$(grep -c '^issue edit' "$MMW_TEST_LOG")"

append_same_line_other_section='## A

相同行

## B

B 原有行

## Destination
仍在这里'
append_same_line_written='## A

相同行

## B

B 原有行
相同行

## Destination
仍在这里'
body_set 100 "$append_same_line_other_section"
: > "$MMW_TEST_READ_COUNT"
unset MMW_TEST_MUTATE_READS MMW_TEST_MUTATE_BODY MMW_TEST_CONCURRENT_DIR
export MMW_TEST_LOG="$WORK/log-append-same-line-other-section"
: > "$MMW_TEST_LOG"
capture "append-别的小节有同一行" "$MMW" issue append 100 --section "B" --line "相同行"
check "别的小节有同一行时仍成功追加" "0" "$LAST_STATUS"
check "别的小节有同一行时目标小节真的新增" "$append_same_line_written" "$(body_get 100)"

append_other_section='## Decisions so far

原有决定

## Destination

别的小节的决定

仍在这里'
append_other_section_lost='## Decisions so far

原有决定
新的决定

## Destination

仍在这里'
body_set 100 "$append_other_section"
: > "$MMW_TEST_READ_COUNT"
export MMW_TEST_MUTATE_READS=2
export MMW_TEST_MUTATE_BODY="$append_other_section_lost"
unset MMW_TEST_CONCURRENT_DIR
export MMW_TEST_LOG="$WORK/log-append-other-section-lost"
: > "$MMW_TEST_LOG"
capture "append-别的小节的行丢失" "$MMW" issue append 100 --section "Decisions so far" --line "新的决定"
check "别的小节的行丢失时要求调用方重跑" "非零" "$(nonzero "$LAST_STATUS")"
check "别的小节的行丢失时不搬进目标小节" "$append_other_section_lost" "$(body_get 100)"
check "别的小节的行丢失时桩触发明确冲突" "1" "$(grep -c '^issue edit' "$MMW_TEST_LOG")"
contains "别的小节的行丢失时报出来源小节" "Destination" "$(cat "$LAST_ERR")"
contains "别的小节的行丢失时报出丢失行" "别的小节的决定" "$(cat "$LAST_ERR")"

body_set 100 "$append_body"
: > "$MMW_TEST_READ_COUNT"
export MMW_TEST_MUTATE_READS='2,4,6,8'
export MMW_TEST_MUTATE_BODY="$append_body"
export MMW_TEST_LOG="$WORK/log-append-limit"
: > "$MMW_TEST_LOG"
capture "append-重做上限" "$MMW" issue append 100 --section "Decisions so far" --line "顽固的新行"
check "append 重做用尽时失败" "非零" "$(nonzero "$LAST_STATUS")"
check "append 初次加三次重做后停止" "4" "$(grep -c '^issue edit' "$MMW_TEST_LOG")"
contains "append 重做用尽时输出缺失行原文" "顽固的新行" "$(cat "$LAST_ERR")"

body_set 100 '## 已有一

内容

## 已有二

内容'
: > "$MMW_TEST_READ_COUNT"
unset MMW_TEST_MUTATE_READS MMW_TEST_MUTATE_BODY
export MMW_TEST_LOG="$WORK/log-append-no-section"
: > "$MMW_TEST_LOG"
capture "append-小节不存在" "$MMW" issue append 100 --section "不存在" --line "新的决定"
check "append 小节不存在时失败" "非零" "$(nonzero "$LAST_STATUS")"
contains "append 小节不存在时列出第一个现有小节" "已有一" "$(cat "$LAST_ERR")"
contains "append 小节不存在时列出第二个现有小节" "已有二" "$(cat "$LAST_ERR")"
check "append 小节不存在时不写正文" "" "$(grep -F 'issue edit' "$MMW_TEST_LOG" || true)"

body_set 100 '## Decisions so far

起点

## Destination
仍在这里'
concurrent_dir="$WORK/concurrent"
mkdir -p "$concurrent_dir"
export MMW_TEST_CONCURRENT_DIR="$concurrent_dir"
export MMW_TEST_LOG="$WORK/log-append-concurrent"
: > "$MMW_TEST_LOG"
set +e
"$MMW" issue append 100 --section "Decisions so far" --line "A-append" > "$WORK/append-a.out" 2> "$WORK/append-a.err" &
append_a_pid=$!
"$MMW" issue append 100 --section "Decisions so far" --line "B-append" > "$WORK/append-b.out" 2> "$WORK/append-b.err" &
append_b_pid=$!
wait "$append_a_pid"
append_a_status=$?
wait "$append_b_pid"
append_b_status=$?
set -e
check "并发 append 的 A 成功" "0" "$append_a_status"
check "并发 append 的 B 成功" "0" "$append_b_status"
contains "并发 append 最终保留 A" "A-append" "$(body_get 100)"
contains "并发 append 最终保留 B" "B-append" "$(body_get 100)"
unset MMW_TEST_CONCURRENT_DIR

echo
echo "issue set-parent"

export MMW_TEST_LOG="$WORK/log-set-parent"
: > "$MMW_TEST_LOG"
capture "set-parent-成功" "$MMW" issue set-parent 42 --parent 100
check "set-parent 成功退出" "0" "$LAST_STATUS"
check "set-parent 复用 create 的 sub_issues 端点和 database id" \
  'api --method POST repos/o/r/issues/100/sub_issues -F sub_issue_id=1042;' \
  "$(posts "$MMW_TEST_LOG")"

capture "set-parent-缺父 issue" "$MMW" issue set-parent 42
check "set-parent 缺父 issue 时失败" "非零" "$(nonzero "$LAST_STATUS")"
contains "set-parent 缺父 issue 时显示更新后的 issue 用法" "mmw issue append" "$(cat "$LAST_ERR")"

export MMW_TEST_FAIL_SET_PARENT=1
export MMW_TEST_LOG="$WORK/log-set-parent-failure"
: > "$MMW_TEST_LOG"
capture "set-parent-端点失败" "$MMW" issue set-parent 42 --parent 100
check "set-parent 端点失败时直接失败" "非零" "$(nonzero "$LAST_STATUS")"
check "set-parent 端点失败时不写正文降级" "" \
  "$(grep -E 'issue edit|--method PATCH' "$MMW_TEST_LOG" || true)"
unset MMW_TEST_FAIL_SET_PARENT

echo
echo "issue usage"

capture "issue-无参" "$MMW" issue
check "issue 无参时返回用法错误" "2" "$LAST_STATUS"
usage_text="$(cat "$LAST_ERR")"
contains "issue 用法列出 append" "mmw issue append" "$usage_text"
contains "issue 用法列出 set-parent" "mmw issue set-parent" "$usage_text"
contains "issue 用法说明七条动作" "以上七条" "$usage_text"
check "issue 用法不再说明五条动作" "" "$(grep -F '以上五条' "$LAST_ERR" || true)"
contains "issue 用法把追加一行导向 append" "追加一行" "$usage_text"
contains "issue 用法写出 append 命令" "mmw issue append" "$usage_text"
contains "issue 用法把整份替换限于明确操作" "有意替换整份正文" "$usage_text"
contains "issue 用法给出 Destination 例子" "Destination" "$usage_text"

capture "append-无参" "$MMW" issue append
check "append 无参时返回更新后的 issue 用法" "2" "$LAST_STATUS"
contains "append 无参时显示 append 用法" "mmw issue append" "$(cat "$LAST_ERR")"
capture "set-parent-无参" "$MMW" issue set-parent
check "set-parent 无参时返回更新后的 issue 用法" "2" "$LAST_STATUS"
contains "set-parent 无参时显示 set-parent 用法" "mmw issue set-parent" "$(cat "$LAST_ERR")"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
