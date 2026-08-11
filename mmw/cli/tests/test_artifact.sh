#!/usr/bin/env bash
# artifact path 只测 agent 从命令行能观察到的结果：路径、失败回应、标准流和副作用。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$HERE/../mmw"
DATA="$HERE/../artifacts.json"
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

copy_stamp() {
  python3 -c 'import os, sys; state = os.stat(sys.argv[1]); print(f"{state.st_mtime_ns}:{state.st_ino}")' "$1"
}

expect_path() {
  local label="$1" want="$2"
  shift 2
  capture "$label" "$@"
  check "$label 退出码" "0" "$LAST_STATUS"
  check "$label 标准输出" "$want" "$(cat "$LAST_OUT")"
  check "$label 标准错误" "" "$(cat "$LAST_ERR")"
}

expect_error() {
  local label="$1" message="$2"
  shift 2
  capture "$label" "$@"
  if [ "$LAST_STATUS" -ne 0 ]; then
    echo "  过  $label 非零退出"
    pass=$((pass + 1))
  else
    echo "  失败 $label 非零退出" >&2
    fail=$((fail + 1))
  fi
  check "$label 没有路径标准输出" "" "$(cat "$LAST_OUT")"
  contains "$label 标准错误" "$message" "$(cat "$LAST_ERR")"
}

export MMW_HOST=claude-code
git -C "$WORK" init -q repo
cp "$HERE/../mmw.default.json" "$WORK/repo/.mmw.json"
cd "$WORK/repo"
REPO="$(pwd -P)"
git -C "$REPO" config user.name "MMW Artifact"
git -C "$REPO" config user.email "artifact@example.invalid"
printf 'seed\n' > "$REPO/seed.txt"
git -C "$REPO" add seed.txt
git -C "$REPO" commit -q -m "seed"

echo "artifact data"
if [ -f "$DATA" ]; then
  check "数据是 JSON 对象" "true" "$(jq -r 'type == "object"' "$DATA")"
  expected_categories="$(printf '%s\n' \
    spec plan prototype research adr context context-map out-of-scope scratch review \
    task agent-report release-state release-artifact delivery-record graph worktree \
    handoff explanation map decision-ticket conclusion-comment handback-comment spec-issue \
    tracer-ticket agent-brief | sort)"
  check "类别集合完整" "$expected_categories" "$(jq -r 'keys[]' "$DATA" | sort)"

  required_fields='["term","root","root_kind","has_name","allows_scope","sub_naming","sub_fixed","sub_pattern","status","answered_by"]'
  check "每条记录都有十个字段" "true" \
    "$(jq -r --argjson required "$required_fields" 'all(.[]; (keys | sort) == ($required | sort))' "$DATA")"
  check "状态值受限" "true" \
    "$(jq -r 'all(.[]; .status | IN("active", "no-file", "not-shaped", "external", "tracker"))' "$DATA")"
  expected_terms="$(printf '%s\n' \
    $'adr\tADR' \
    $'agent-brief\tagent brief' \
    $'agent-report\t报告' \
    $'conclusion-comment\t结论评论' \
    $'context\tleaf' \
    $'context-map\tContext Map' \
    $'decision-ticket\tdecision ticket' \
    $'delivery-record\t交付记录' \
    $'explanation\t解释 HTML' \
    $'graph\t结构图谱' \
    $'handoff\thandoff' \
    $'handback-comment\t交回评论' \
    $'map\tmap' \
    $'out-of-scope\t否决记录' \
    $'plan\tplan' \
    $'prototype\tprototype 资产' \
    $'release-artifact\t出包阶段产物' \
    $'release-state\t出包状态' \
    $'research\tresearch' \
    $'review\t审查记录' \
    $'scratch\tscratch' \
    $'spec\tspec' \
    $'spec-issue\tspec issue' \
    $'task\ttask' \
    $'tracer-ticket\ttracer bullet ticket' \
    $'worktree\t任务 worktree' | sort)"
  check "全部类别使用规定术语" "$expected_terms" \
    "$(jq -r 'to_entries | sort_by(.key)[] | [.key, .value.term] | @tsv' "$DATA")"
  expected_active_shape="$(printf '%s\n' \
    $'adr\tdocs/adr\tfixed\tfalse\tfalse\tallocated' \
    $'context\tdocs/context\tfixed\tfalse\tfalse\tone-per-concept' \
    $'context-map\t\tfixed\tfalse\tfalse\tfixed-file' \
    $'out-of-scope\t.out-of-scope\tfixed\tfalse\tfalse\tone-per-concept' \
    $'plan\tdocs/plans\tfixed\ttrue\tfalse\tallocated' \
    $'prototype\tdocs/prototypes\tfixed\ttrue\ttrue\tad-hoc' \
    $'research\tdocs/research\tfixed\ttrue\ttrue\tad-hoc' \
    $'review\treviews\tworkdir\ttrue\tfalse\tfixed-file' \
    $'scratch\tscratch\tworkdir\ttrue\ttrue\tfixed-file' \
    $'spec\tdocs/specs\tfixed\ttrue\tfalse\tfixed-file' | sort)"
  check "活动类别的路径形状数据完整" "$expected_active_shape" \
    "$(jq -r 'to_entries | map(select(.value.status == "active")) | sort_by(.key)[] | [.key, .value.root, .value.root_kind, .value.has_name, .value.allows_scope, .value.sub_naming] | @tsv' "$DATA")"
  expected_fixed_subs="$(printf '%s\n' \
    $'adr\t' \
    $'context\t' \
    $'context-map\tCONTEXT-MAP.md' \
    $'out-of-scope\t' \
    $'plan\t' \
    $'prototype\t' \
    $'research\t' \
    $'review\tunderstanding.md,spec.md,plan.md,final.md' \
    $'scratch\tunderstanding.md,evidence,questionnaire,wizard,diagnosis,architecture-review,dispatch' \
    $'spec\tspec.md' | sort)"
  check "活动类别的固定细分取值完整" "$expected_fixed_subs" \
    "$(jq -r 'to_entries | map(select(.value.status == "active")) | sort_by(.key)[] | [.key, (.value.sub_fixed | join(","))] | @tsv' "$DATA")"
  check "context-map 的根是空字符串" "" "$(jq -r '."context-map".root' "$DATA")"
  check "context-map 的固定文件名" "CONTEXT-MAP.md" \
    "$(jq -r '."context-map".sub_fixed[]' "$DATA")"
  check "scratch 使用工作目录根" "scratch" "$(jq -r '.scratch.root' "$DATA")"
  check "review 使用工作目录根" "reviews" "$(jq -r '.review.root' "$DATA")"
  check "计划的类别内细分模式" '^\d{2}-[a-z0-9][a-z0-9._-]*\.md$' \
    "$(jq -r '.plan.sub_pattern' "$DATA")"
  check "ADR 的类别内细分模式" \
    '^\d{4}-[a-z0-9][a-z0-9._-]*\.md$|^draft-\d+-[a-z0-9][a-z0-9._-]*\.md$' \
    "$(jq -r '.adr.sub_pattern' "$DATA")"
  check "审查记录的类别内细分模式" '^integration-\d{4}-\d{2}-\d{2}(-\d+)?\.md$' \
    "$(jq -r '.review.sub_pattern' "$DATA")"
  check "not-shaped 类别完整" \
    "delivery-record graph release-artifact release-state worktree" \
    "$(jq -r 'to_entries[] | select(.value.status == "not-shaped") | .key' "$DATA" | sort | tr '\n' ' ' | sed 's/ $//')"
  check "no-file 类别完整" "agent-report task" \
    "$(jq -r 'to_entries[] | select(.value.status == "no-file") | .key' "$DATA" | sort | tr '\n' ' ' | sed 's/ $//')"
  check "external 类别完整" "explanation handoff" \
    "$(jq -r 'to_entries[] | select(.value.status == "external") | .key' "$DATA" | sort | tr '\n' ' ' | sed 's/ $//')"
  check "tracker 类别完整" \
    "agent-brief conclusion-comment decision-ticket handback-comment map spec-issue tracer-ticket" \
    "$(jq -r 'to_entries[] | select(.value.status == "tracker") | .key' "$DATA" | sort | tr '\n' ' ' | sed 's/ $//')"
else
  check "产物落点数据文件存在" "存在" "缺失"
fi

echo
echo "artifact command discovery"
top_commands="$(sed -n '/^case "${1:-}" in$/,/^esac$/p' "$MMW" | sed -nE 's/^  ([a-z-]+)\) shift; .*/\1/p')"
contains "顶层分发解析到 artifact" "artifact" "$top_commands"
artifact_actions="$(sed -n '/^cmd_artifact() {$/,/^}$/p' "$MMW" | sed -nE 's/^    ([a-z-]+)\).*/\1/p')"
contains "artifact 动作解析到 path" "path" "$artifact_actions"
contains "artifact 动作解析到 index" "index" "$artifact_actions"

echo
echo "artifact index"
mkdir -p docs/adr docs/specs/alpha docs/specs/beta
printf '%s\n' \
  '---' \
  'date: 2026-08-11' \
  'amends: []' \
  '---' \
  '# 初始决定' > docs/adr/0001-initial.md
printf '%s\n' \
  '---' \
  'date: 2026-08-12' \
  'amends: [1]' \
  '---' \
  '# 后续决定' > docs/adr/0002-follow-up.md
printf '%s\n' \
  '---' \
  'slug: alpha' \
  'summary: Alpha spec' \
  'date: 2026-08-11' \
  'branch: task-alpha' \
  'spec_issue: 31' \
  'artifact_refs: []' \
  '---' \
  '# Alpha spec' > docs/specs/alpha/spec.md
printf '%s\n' \
  '---' \
  'slug: beta' \
  'summary: Beta spec' \
  'date: 2026-08-12' \
  'branch: task-beta' \
  'spec_issue: 32' \
  'artifact_refs: []' \
  '---' \
  '# Beta spec' > docs/specs/beta/spec.md

expected_adr=$'# ADR 索引\n\n由 `mmw artifact index adr` 生成。\n\n| 编号 | 标题 | 日期 | 改写了哪几份 | 被哪几份改写 |\n| --- | --- | --- | --- | --- |\n| 0001 | 初始决定 | 2026-08-11 | 无 | 0002 |\n| 0002 | 后续决定 | 2026-08-12 | 0001 | 无 |'
expected_spec=$'# spec 索引\n\n由 `mmw artifact index spec` 生成。\n\n| 工作名 | 摘要 | 日期 | 任务分支名 | spec issue 编号 |\n| --- | --- | --- | --- | --- |\n| alpha | Alpha spec | 2026-08-11 | task-alpha | 31 |\n| beta | Beta spec | 2026-08-12 | task-beta | 32 |'

capture "ADR 当场计算" "$MMW" artifact index adr
check "ADR 当场计算退出码" "0" "$LAST_STATUS"
check "ADR 当场计算标准输出" "$expected_adr" "$(cat "$LAST_OUT")"
check "ADR 当场计算标准错误" "" "$(cat "$LAST_ERR")"
check "ADR 副本与输出逐字节相同" "true" "$(cmp -s "$LAST_OUT" docs/adr/README.md && echo true || echo false)"

capture "spec 当场计算" "$MMW" artifact index spec
check "spec 当场计算退出码" "0" "$LAST_STATUS"
check "spec 当场计算标准输出" "$expected_spec" "$(cat "$LAST_OUT")"
check "spec 当场计算标准错误" "" "$(cat "$LAST_ERR")"
check "spec 副本与输出逐字节相同" "true" "$(cmp -s "$LAST_OUT" docs/specs/README.md && echo true || echo false)"

adr_copy_before="$(copy_stamp docs/adr/README.md)"
capture "ADR 一致副本不写" "$MMW" artifact index adr
check "ADR 一致副本不写退出码" "0" "$LAST_STATUS"
check "ADR 一致副本不写" "$adr_copy_before" "$(copy_stamp docs/adr/README.md)"

printf '过期副本\n' > docs/specs/README.md
capture "spec 过期副本更新" "$MMW" artifact index spec
check "spec 过期副本更新退出码" "0" "$LAST_STATUS"
check "spec 过期副本更新" "true" "$(cmp -s "$LAST_OUT" docs/specs/README.md && echo true || echo false)"

printf '旧 ADR 副本\n' > docs/adr/README.md
chmod a-w docs/adr
capture "ADR 不可写降级" "$MMW" artifact index adr
chmod u+w docs/adr
check "ADR 不可写降级退出码" "0" "$LAST_STATUS"
check "ADR 不可写降级仍输出完整清单" "$expected_adr" "$(cat "$LAST_OUT")"
check "ADR 不可写降级保留旧副本" "旧 ADR 副本" "$(cat docs/adr/README.md)"
check "ADR 不可写降级标准错误一行" "1" "$(wc -l < "$LAST_ERR" | tr -d ' ')"
contains "ADR 不可写降级标准错误说明" "跳过" "$(cat "$LAST_ERR")"

capture "不支持索引类别" "$MMW" artifact index plan
check "不支持索引类别退出码" "2" "$LAST_STATUS"
contains "不支持索引类别说明" "adr 或 spec" "$(cat "$LAST_ERR")"

printf '%s\n' \
  '---' \
  'amends: []' \
  '---' \
  '# 缺少日期' > docs/adr/0003-missing-date.md
capture "ADR 缺字段失败" "$MMW" artifact index adr
if [ "$LAST_STATUS" -ne 0 ]; then
  echo "  过  ADR 缺字段失败非零退出"
  pass=$((pass + 1))
else
  echo "  失败 ADR 缺字段失败非零退出" >&2
  fail=$((fail + 1))
fi
contains "ADR 缺字段失败说明" "date" "$(cat "$LAST_ERR")"
rm docs/adr/0003-missing-date.md

artifact_path_dirs_before="$(find . -type d -print | sort)"

echo
echo "artifact path"
expect_path "spec 的默认固定文件" "docs/specs/release/spec.md" \
  "$MMW" artifact path spec --name release
expect_path "全小写工作名可以作为名字段" "docs/specs/beta/spec.md" \
  "$MMW" artifact path spec --name beta
expect_path "spec 的绝对路径" "$REPO/docs/specs/release/spec.md" \
  "$MMW" artifact path spec --name release --absolute
capture "research 的范围和类别内细分" "$MMW" artifact path research --name release --issue 19 --sub report
check "research 的范围和类别内细分退出码" "0" "$LAST_STATUS"
check "research 的范围和类别内细分标准输出" "docs/research/release/issue-19/report" "$(cat "$LAST_OUT")"
contains "research 的范围和类别内细分标准错误" "写第一个文件之前先列一次父目录" "$(cat "$LAST_ERR")"
expect_path "scratch 的固定首段与第二段" ".scratch/release/issue-19/evidence/screenshot" \
  "$MMW" artifact path scratch --name release --issue 19 --sub evidence/screenshot
expect_path "plan 的类别内细分模式" "docs/plans/release/01-artifact-path.md" \
  "$MMW" artifact path plan --name release --sub 01-artifact-path.md
expect_path "review 的类别内细分模式" ".reviews/release/integration-2026-08-12.md" \
  "$MMW" artifact path review --name release --sub integration-2026-08-12.md
expect_path "ADR 的类别内细分模式" "docs/adr/0001-architecture.md" \
  "$MMW" artifact path adr --sub 0001-architecture.md
expect_path "仓库根的 Context Map" "CONTEXT-MAP.md" \
  "$MMW" artifact path context-map

capture "当场取名提醒" "$MMW" artifact path research --name release --sub topic
check "当场取名提醒退出码" "0" "$LAST_STATUS"
check "当场取名提醒的路径" "docs/research/release/topic" "$(cat "$LAST_OUT")"
contains "当场取名提醒在标准错误" "写第一个文件之前先列一次父目录" "$(cat "$LAST_ERR")"
check "显式工作名查询不建立目录" "$artifact_path_dirs_before" "$(find . -type d -print | sort)"

echo
echo "artifact path 的缺省工作名"
task_worktree="$REPO/.worktrees/artifact-task"
capture "建立带工作名的任务 worktree" \
  "$MMW" task new artifact-task "产物路径测试" --name artifact-work
check "建立带工作名的任务 worktree 退出码" "0" "$LAST_STATUS"
check "建立带工作名的任务 worktree 输出路径" "$task_worktree" "$(cat "$LAST_OUT")"
capture "缺省工作名" bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' \
  _ "$task_worktree" "$MMW"
check "缺省工作名退出码" "0" "$LAST_STATUS"
check "缺省工作名与显式工作名路径相同" "docs/specs/artifact-work/spec.md" "$(cat "$LAST_OUT")"
check "缺省工作名没有标准错误" "" "$(cat "$LAST_ERR")"

detached_worktree="$REPO/.worktrees/artifact-detached"
git -C "$REPO" worktree add -q --detach "$detached_worktree" HEAD
broken_worktree="$REPO/.worktrees/artifact-broken"
capture "建立损坏绑定的任务 worktree" \
  "$MMW" task new artifact-broken "损坏绑定" --name broken-work
check "建立损坏绑定的任务 worktree 退出码" "0" "$LAST_STATUS"
git -C "$broken_worktree" config --worktree --unset mmw.task.work-name
failure_dirs_before="$(find "$REPO" -type d -print | sort)"

expect_error "主检出缺省工作名不回退" "工作名" \
  "$MMW" artifact path spec
expect_error "仓库外缺省工作名不回退" "工作名" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$WORK" "$MMW"
expect_error "detached worktree 缺省工作名不回退" "工作名" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$detached_worktree" "$MMW"
expect_error "损坏绑定缺省工作名不回退" "mmw task bind artifact-broken" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$broken_worktree" "$MMW"
check "缺省工作名的拒绝路径不建目录" "$failure_dirs_before" "$(find "$REPO" -type d -print | sort)"
expect_path "显式工作名不读取损坏绑定" "docs/specs/other-work/spec.md" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec --name other-work' \
  _ "$broken_worktree" "$MMW"
before_dirs="$(find . -type d -print | sort)"

echo
echo "artifact failures"
expect_error "认不出的类别" "全部合法类别名" \
  "$MMW" artifact path absent --name release
expect_error "四栏 task 不写文件" "不写文件" \
  "$MMW" artifact path task
expect_error "结构图谱不套路径形状" "mmw graph" \
  "$MMW" artifact path graph
expect_error "handoff 在仓库外" "操作系统临时目录" \
  "$MMW" artifact path handoff
expect_error "map 在 issue tracker" "gh issue view <编号>" \
  "$MMW" artifact path map
expect_error "带名字段必须显式给 name" "要 --name" \
  "$MMW" artifact path spec
expect_error "name 拒绝大写字母" "只能用小写字母" \
  "$MMW" artifact path spec --name Release
expect_error "不允许范围段的类别拒绝 issue" "没有范围段" \
  "$MMW" artifact path spec --name release --issue 19
expect_error "issue 只接收纯编号" "--issue 只接收纯编号" \
  "$MMW" artifact path research --name release --issue x --sub report
expect_error "缺少必填类别内细分" "要 --sub" \
  "$MMW" artifact path research --name release
expect_error "固定类别内细分不匹配" "允许的取值" \
  "$MMW" artifact path spec --name release --sub other.md
expect_error "模式类别内细分不匹配" "允许的模式" \
  "$MMW" artifact path plan --name release --sub plan.md
expect_error "sub 拒绝空段" "空路径段" \
  "$MMW" artifact path research --name release --sub ''
expect_error "sub 拒绝当前目录" "不能是 . 或 .." \
  "$MMW" artifact path research --name release --sub .
expect_error "sub 拒绝上级目录" "不能是 . 或 .." \
  "$MMW" artifact path research --name release --sub ..
expect_error "sub 拒绝大写字母" "只能用小写字母" \
  "$MMW" artifact path research --name release --sub Topic
expect_error "sub 拒绝非法首字符" "首字符必须是字母或数字" \
  "$MMW" artifact path research --name release --sub -topic
expect_error "sub 拒绝其他非法字符" "只能包含小写字母、数字、点、下划线和连字符" \
  "$MMW" artifact path research --name release --sub 'topic$'
expect_error "sub 拒绝中间空段" "空路径段" \
  "$MMW" artifact path research --name release --sub topic//detail

echo
echo "artifact usage"
capture "无参用法" "$MMW" artifact
check "无参用法退出码" "2" "$LAST_STATUS"
check "无参用法没有标准输出" "" "$(cat "$LAST_OUT")"
usage_text="$(cat "$LAST_ERR")"
contains "无参用法有 path 说明" "mmw artifact path" "$usage_text"
contains "无参用法有 index 说明" "mmw artifact index" "$usage_text"
contains "无参用法列出 spec 术语" $'spec\tspec' "$usage_text"
contains "无参用法列出解释 HTML 术语" $'explanation\t解释 HTML' "$usage_text"
contains "无参用法列出 agent brief 术语" $'agent-brief\tagent brief' "$usage_text"

after_dirs="$(find . -type d -print | sort)"
check "查询不建立目录" "$before_dirs" "$after_dirs"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
