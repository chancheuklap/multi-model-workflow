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
    tracer-ticket agent-brief ui-criteria ui-qa-wiring | sort)"
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
    $'ui-criteria\t界面 QA 判据' \
    $'ui-qa-wiring\t界面 QA 接线' \
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
    $'spec\tdocs/specs\tfixed\ttrue\tfalse\tfixed-file' \
    $'ui-criteria\tdocs/ui-criteria\tfixed\tfalse\tfalse\tone-per-concept' \
    $'ui-qa-wiring\tdocs/ui-qa-wiring\tfixed\tfalse\tfalse\tone-per-concept' | sort)"
  check "活动类别的路径形状数据完整" "$expected_active_shape" \
    "$(jq -r 'to_entries | map(select(.value.status == "active")) | sort_by(.key)[] | [.key, .value.root, .value.root_kind, .value.has_name, .value.allows_scope, .value.sub_naming] | @tsv' "$DATA")"
  expected_fixed_subs="$(printf '%s\n' \
    $'adr\t' \
    $'context\t' \
    $'context-map\tCONTEXT-MAP.md' \
    $'out-of-scope\t' \
    $'plan\t' \
    $'prototype\tREADME.md' \
    $'research\tREADME.md' \
    $'review\tunderstanding.md,spec.md,plan.md,final.md' \
    $'scratch\tunderstanding.md,evidence,questionnaire,wizard,diagnosis,architecture-review,dispatch,outbox' \
    $'spec\tspec.md' \
    $'ui-criteria\t' \
    $'ui-qa-wiring\t' | sort)"
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
  check "界面 QA 判据的类别内细分模式" \
    '^(thresholds\.json|products/[a-z0-9][a-z0-9-]*\.md)$' \
    "$(jq -r '."ui-criteria".sub_pattern' "$DATA")"
  check "界面 QA 接线的类别内细分模式" '^[a-z0-9][a-z0-9-]*\.json$' \
    "$(jq -r '."ui-qa-wiring".sub_pattern' "$DATA")"
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
capture "artifact 顶层用法" "$MMW" artifact
check "artifact 顶层用法退出码" "2" "$LAST_STATUS"
contains "artifact 顶层用法有 path" "mmw artifact path <类别>" "$(cat "$LAST_ERR")"
contains "artifact 顶层用法有 index" "mmw artifact index <类别>" "$(cat "$LAST_ERR")"
contains "artifact 顶层用法有 check" "mmw artifact check" "$(cat "$LAST_ERR")"
contains "artifact 顶层用法有 list" "mmw artifact list" "$(cat "$LAST_ERR")"

capture "artifact path 动作" "$MMW" artifact path
check "artifact path 动作退出码" "2" "$LAST_STATUS"
contains "artifact path 动作回应" "mmw artifact path <类别>" "$(cat "$LAST_ERR")"

capture "artifact index 动作" "$MMW" artifact index
check "artifact index 动作退出码" "2" "$LAST_STATUS"
contains "artifact index 动作回应" "用法是 mmw artifact index <类别>" "$(cat "$LAST_ERR")"

capture "artifact check 动作" "$MMW" artifact check
check "artifact check 动作退出码" "0" "$LAST_STATUS"
check "artifact check 动作标准输出" "" "$(cat "$LAST_OUT")"
check "artifact check 动作标准错误" "" "$(cat "$LAST_ERR")"

capture "artifact list 动作" "$MMW" artifact list --name release
check "artifact list 动作退出码" "0" "$LAST_STATUS"
check "artifact list 动作标准输出" "" "$(cat "$LAST_OUT")"
check "artifact list 动作标准错误" "" "$(cat "$LAST_ERR")"

echo
echo "仓库外拒绝"
OUTSIDE_REPO="$WORK/outside-repo"
mkdir -p "$OUTSIDE_REPO"
outside_tree_before="$(cd "$OUTSIDE_REPO" && find . -print | sort)"
capture "仓库外 ADR 索引拒绝" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact index adr' _ "$OUTSIDE_REPO" "$MMW"
if [ "$LAST_STATUS" -ne 0 ]; then
  echo "  过  仓库外 ADR 索引拒绝非零退出"
  pass=$((pass + 1))
else
  echo "  失败 仓库外 ADR 索引拒绝非零退出" >&2
  fail=$((fail + 1))
fi
check "仓库外 ADR 索引拒绝没有标准输出" "" "$(cat "$LAST_OUT")"
contains "仓库外 ADR 索引拒绝说明" "当前目录不在 git 仓库里" "$(cat "$LAST_ERR")"
check "仓库外 ADR 索引拒绝不改文件树" "$outside_tree_before" \
  "$(cd "$OUTSIDE_REPO" && find . -print | sort)"

capture "仓库外声明校验拒绝" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact check' _ "$OUTSIDE_REPO" "$MMW"
if [ "$LAST_STATUS" -ne 0 ]; then
  echo "  过  仓库外声明校验拒绝非零退出"
  pass=$((pass + 1))
else
  echo "  失败 仓库外声明校验拒绝非零退出" >&2
  fail=$((fail + 1))
fi
check "仓库外声明校验拒绝没有标准输出" "" "$(cat "$LAST_OUT")"
contains "仓库外声明校验拒绝说明" "当前目录不在 git 仓库里" "$(cat "$LAST_ERR")"
check "仓库外声明校验拒绝不改文件树" "$outside_tree_before" \
  "$(cd "$OUTSIDE_REPO" && find . -print | sort)"

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
expected_spec=$'# spec 索引\n\n由 `mmw artifact index spec` 生成。\n\n| 名字段 | 摘要 | 日期 | 任务分支名 | spec issue 编号 |\n| --- | --- | --- | --- | --- |\n| alpha | Alpha spec | 2026-08-11 | task-alpha | 31 |\n| beta | Beta spec | 2026-08-12 | task-beta | 32 |'

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

echo
echo "artifact check"
mkdir -p \
  docs/specs/check-valid \
  docs/specs/check-empty \
  docs/specs/check-history-no-block \
  docs/specs/check-errors \
  docs/plans/check-valid \
  docs/plans/check-empty \
  docs/plans/check-history-no-block \
  docs/plans/check-history-no-key
printf '%s\n' \
  '---' \
  'slug: check-valid' \
  'summary: Valid reference' \
  'date: 2026-08-12' \
  'branch: task-check-valid' \
  'spec_issue: 41' \
  'artifact_refs:' \
  '  - category: research' \
  '    name: release' \
  '    issue: 99' \
  '    sub: not-on-disk' \
  '---' \
  '# Valid reference' > docs/specs/check-valid/spec.md
printf '%s\n' \
  '---' \
  'slug: check-empty' \
  'summary: Explicitly empty' \
  'date: 2026-08-12' \
  'branch: task-check-empty' \
  'spec_issue: 42' \
  'artifact_refs: []' \
  '---' \
  '# Explicitly empty' > docs/specs/check-empty/spec.md
printf '# Historical spec\n' > docs/specs/check-history-no-block/spec.md
printf '%s\n' \
  '---' \
  'ticket: 44' \
  'artifact_refs:' \
  '  - category: research' \
  '    name: release' \
  '    issue: 99' \
  '    sub: not-on-disk' \
  '---' \
  '# Valid plan reference' > docs/plans/check-valid/01-valid.md
printf '%s\n' \
  '---' \
  'ticket: 45' \
  'artifact_refs: []' \
  '---' \
  '# Explicitly empty plan' > docs/plans/check-empty/02-empty.md
printf '# Historical plan\n' > docs/plans/check-history-no-block/03-no-block.md
artifact_check_tree_before="$(find . -print | sort)"
capture "只有历史文件的声明校验" "$MMW" artifact check
check "只有历史文件的声明校验退出码" "0" "$LAST_STATUS"
contains "没有元数据块的历史文件报告" "docs/specs/check-history-no-block/spec.md: 历史文件，缺少 YAML 元数据块" "$(cat "$LAST_OUT")"
check "只有历史文件的声明校验没有标准错误" "" "$(cat "$LAST_ERR")"
check "只有历史文件的声明校验不改文件树" "$artifact_check_tree_before" "$(find . -print | sort)"

printf '%s\n' \
  '---' \
  'ticket: 46' \
  '---' \
  '# 新格式但缺产物引用' > docs/plans/check-history-no-key/04-no-key.md
capture "有元数据块但缺 artifact_refs 拒绝" "$MMW" artifact check
check "有元数据块但缺 artifact_refs 拒绝退出码" "1" "$LAST_STATUS"
contains "有元数据块但缺 artifact_refs 仍报告历史文件" "docs/plans/check-history-no-block/03-no-block.md: 历史文件，缺少 YAML 元数据块" "$(cat "$LAST_OUT")"
contains "有元数据块但缺 artifact_refs 说明" "docs/plans/check-history-no-key/04-no-key.md: 缺少 artifact_refs" "$(cat "$LAST_ERR")"
rm docs/plans/check-history-no-key/04-no-key.md

echo
echo "metadata subset"
METADATA_REPO="$WORK/metadata-subset"
git init -q "$METADATA_REPO"
mkdir -p "$METADATA_REPO/docs/specs/boundary"
printf '%s\n' \
  '---' \
  'slug: boundary' \
  'summary: Boundary spec' \
  'date: 2026-08-12' \
  'branch: task-boundary' \
  'spec_issue: 49' \
  'artifact_refs: # 产物引用' \
  '  - category: research' \
  '    name: release' \
  '    issue: 99' \
  '    sub: not-on-disk' \
  '---' \
  '# Boundary spec' > "$METADATA_REPO/docs/specs/boundary/spec.md"
capture "行尾注释的产物引用通过声明校验" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact check' _ "$METADATA_REPO" "$MMW"
check "行尾注释的产物引用通过声明校验退出码" "0" "$LAST_STATUS"
check "行尾注释的产物引用通过声明校验标准错误" "" "$(cat "$LAST_ERR")"
capture "行尾注释的产物引用通过 spec 索引" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact index spec' _ "$METADATA_REPO" "$MMW"
check "行尾注释的产物引用通过 spec 索引退出码" "0" "$LAST_STATUS"
check "行尾注释的产物引用通过 spec 索引标准错误" "" "$(cat "$LAST_ERR")"

mkdir -p "$METADATA_REPO/docs/plans/quoted-issue"
printf '%s\n' \
  '---' \
  'ticket: 50' \
  'artifact_refs:' \
  '  - category: research' \
  '    name: release' \
  '    issue: "20"' \
  '    sub: not-on-disk' \
  '---' \
  '# Quoted issue' > "$METADATA_REPO/docs/plans/quoted-issue/01-quoted-issue.md"
capture "带引号的 issue 拒绝" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact check' _ "$METADATA_REPO" "$MMW"
check "带引号的 issue 拒绝退出码" "1" "$LAST_STATUS"
contains "带引号的 issue 拒绝说明" "artifact_refs[0]: 缺少或无效的 issue" "$(cat "$LAST_ERR")"
rm "$METADATA_REPO/docs/plans/quoted-issue/01-quoted-issue.md"

mkdir -p "$METADATA_REPO/docs/specs/folded"
printf '%s\n' \
  '---' \
  'slug: folded' \
  'summary: >-' \
  '  不支持折叠字符串' \
  'date: 2026-08-12' \
  'branch: task-folded' \
  'spec_issue: 51' \
  'artifact_refs: []' \
  '---' \
  '# Folded spec' > "$METADATA_REPO/docs/specs/folded/spec.md"
capture "折叠字符串的声明校验拒绝" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact check' _ "$METADATA_REPO" "$MMW"
check "折叠字符串的声明校验拒绝退出码" "1" "$LAST_STATUS"
contains "折叠字符串的声明校验说明" "第 3 行不支持 YAML 折叠字符串" "$(cat "$LAST_ERR")"
capture "折叠字符串的 spec 索引拒绝" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact index spec' _ "$METADATA_REPO" "$MMW"
check "折叠字符串的 spec 索引拒绝退出码" "1" "$LAST_STATUS"
contains "折叠字符串的 spec 索引说明" "第 3 行不支持 YAML 折叠字符串" "$(cat "$LAST_ERR")"
rm "$METADATA_REPO/docs/specs/folded/spec.md"

echo
echo "artifact check data roots"
B10_MMW_ROOT="$WORK/b10-mmw"
mkdir -p "$B10_MMW_ROOT"
cp -R "$HERE/.." "$B10_MMW_ROOT/cli"
B10_DATA="$B10_MMW_ROOT/cli/artifacts.json"
jq '.plan.root = "alternate/plans"' "$B10_DATA" > "$WORK/b10-artifacts.json"
mv "$WORK/b10-artifacts.json" "$B10_DATA"
B10_REPO="$WORK/b10-repo"
git init -q "$B10_REPO"
mkdir -p "$B10_REPO/alternate/plans/from-data"
printf '%s\n' \
  '---' \
  'ticket: 52' \
  '---' \
  '# 新格式但缺产物引用' > "$B10_REPO/alternate/plans/from-data/01-from-data.md"
capture "声明校验读取数据里的 plan 根" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact check' \
  _ "$B10_REPO" "$B10_MMW_ROOT/cli/mmw"
check "声明校验读取数据里的 plan 根退出码" "1" "$LAST_STATUS"
contains "声明校验读取数据里的 plan 根说明" \
  "alternate/plans/from-data/01-from-data.md: 缺少 artifact_refs" "$(cat "$LAST_ERR")"

printf '%s\n' \
  '---' \
  'ticket: 47' \
  'artifact_refs:' \
  '  - category: spec' \
  '  - category: absent' \
  '    name: release' \
  '  - category: spec' \
  '    name: release' \
  '    issue: 19' \
  '  - category: research' \
  '    name: release' \
  '    issue: no' \
  '    sub: Topic' \
  '---' \
  '# Invalid declarations' > docs/specs/check-errors/spec.md
capture "错误声明逐条汇总" "$MMW" artifact check
if [ "$LAST_STATUS" -ne 0 ]; then
  echo "  过  错误声明逐条汇总非零退出"
  pass=$((pass + 1))
else
  echo "  失败 错误声明逐条汇总非零退出" >&2
  fail=$((fail + 1))
fi
contains "错误声明逐条汇总仍报告历史文件" "docs/plans/check-history-no-block/03-no-block.md: 历史文件，缺少 YAML 元数据块" "$(cat "$LAST_OUT")"
contains "错误声明逐条汇总缺工作名" "docs/specs/check-errors/spec.md: artifact_refs[0]: 缺少或无效的 name" "$(cat "$LAST_ERR")"
contains "错误声明逐条汇总非法类别" "docs/specs/check-errors/spec.md: artifact_refs[1]: mmw artifact: 认不出的类别 absent" "$(cat "$LAST_ERR")"
contains "错误声明逐条汇总非法范围段" "docs/specs/check-errors/spec.md: artifact_refs[2]: mmw artifact: spec 没有范围段" "$(cat "$LAST_ERR")"
contains "错误声明逐条汇总非法编号" "docs/specs/check-errors/spec.md: artifact_refs[3]: 缺少或无效的 issue" "$(cat "$LAST_ERR")"
rm docs/specs/check-errors/spec.md

echo
echo "artifact reference source forms"
to_spec_source="$(cat "$HERE/../../skills-src/mmw-to-spec/SKILL.md")"
spec_template_source="$(cat "$HERE/../../skills-src/mmw-to-spec/spec-template.md")"
to_tickets_source="$(cat "$HERE/../../skills-src/mmw-to-tickets/SKILL.md")"
to_plan_source="$(cat "$HERE/../../skills-src/mmw-to-plan/SKILL.md")"
planner_source="$(cat "$HERE/../../skills-src/mmw-planner/SKILL.md")"
planner_check_source="$(cat "$HERE/../../skills-src/mmw-planner/references/self-check.md")"
implement_source="$(cat "$HERE/../../skills-src/mmw-implement/SKILL.md")"
worker_brief_source="$(cat "$HERE/../../skills-src/mmw-implement/worker-brief.md")"
contains "spec 生产 YAML 产物引用" "artifact_refs:" "$spec_template_source"
contains "spec 生产空 YAML 产物引用" "artifact_refs: []" "$spec_template_source"
contains "spec 运行声明校验" "mmw artifact check" "$to_spec_source"
# spec issue 正文只剩 `## 输入出处` 一节。`## 工作名` 与 `## 产物引用` 已经去掉：
# 名字段由当前任务分支决定，产物引用由 spec 文件的元数据块权威回答，issue 正文
# 重复它们就是第二份事实来源。#49 的 B13 是这个决定。
contains "spec issue 生产输入出处固定节" "## 输入出处" "$to_spec_source"
contains "spec issue 正文只固定写出一节" "正文固定写出以下一节" "$to_spec_source"
check "spec issue 不再生产产物引用的键值形态" "" \
  "$(grep -F 'category=<类别> name=<工作名>' <<<"$to_spec_source" || true)"
contains "ticket 生产产物引用固定节" "## 产物引用" "$to_tickets_source"
contains "ticket 产物引用写无" "无" "$to_tickets_source"
contains "ticket 拥有产物引用解析" "解析产物引用" "$to_tickets_source"
contains "to-plan 向 planner 传产物引用" "artifact_refs" "$to_plan_source"
contains "to-plan 运行声明校验" "mmw artifact check" "$to_plan_source"
contains "planner 解析产物引用" "mmw artifact path" "$planner_source"
contains "planner 自检工作名必填" "name" "$planner_check_source"
contains "implement 向 worker 传产物引用" "原样写进" "$implement_source"
contains "worker 解析产物引用" "mmw artifact path" "$worker_brief_source"

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
capture "prototype 的固定 README" "$MMW" artifact path prototype --name probe --sub README.md
check "prototype 的固定 README 退出码" "0" "$LAST_STATUS"
check "prototype 的固定 README 标准输出" "docs/prototypes/probe/README.md" "$(cat "$LAST_OUT")"
contains "prototype 的固定 README 标准错误" "写第一个文件之前先列一次父目录" "$(cat "$LAST_ERR")"
capture "research 的末段固定 README" "$MMW" artifact path research --name probe --issue 19 --sub topic/README.md
check "research 的末段固定 README 退出码" "0" "$LAST_STATUS"
check "research 的末段固定 README 标准输出" "docs/research/probe/issue-19/topic/README.md" "$(cat "$LAST_OUT")"
contains "research 的末段固定 README 标准错误" "写第一个文件之前先列一次父目录" "$(cat "$LAST_ERR")"
expect_path "scratch 的固定首段与第二段" ".scratch/release/issue-19/evidence/screenshot" \
  "$MMW" artifact path scratch --name release --issue 19 --sub evidence/screenshot
# outbox 是待发出的 issue 正文与评论正文的载体。它与 evidence 分开：读技能的 agent
# 不该把待发出的 map 正文当成界面验收证据。
expect_path "scratch 的待发出正文带范围段" ".scratch/release/issue-19/outbox/answer.md" \
  "$MMW" artifact path scratch --name release --issue 19 --sub outbox/answer.md
expect_path "scratch 的待发出正文无范围段" ".scratch/release/outbox/spec-issue-body.md" \
  "$MMW" artifact path scratch --name release --sub outbox/spec-issue-body.md
expect_path "plan 的类别内细分模式" "docs/plans/release/01-artifact-path.md" \
  "$MMW" artifact path plan --name release --sub 01-artifact-path.md
expect_path "review 的类别内细分模式" ".reviews/release/integration-2026-08-12.md" \
  "$MMW" artifact path review --name release --sub integration-2026-08-12.md
expect_path "review 的固定终审文件" ".reviews/probe/final.md" \
  "$MMW" artifact path review --name probe --sub final.md
expect_error "固定终审文件不能再接路径" "文件名后面不能接路径段" \
  "$MMW" artifact path review --name probe --sub final.md/extra
expect_path "ADR 的类别内细分模式" "docs/adr/0001-architecture.md" \
  "$MMW" artifact path adr --sub 0001-architecture.md
expect_path "仓库根的 Context Map" "CONTEXT-MAP.md" \
  "$MMW" artifact path context-map
expect_path "界面 QA 判据的阈值表" "docs/ui-criteria/thresholds.json" \
  "$MMW" artifact path ui-criteria --sub thresholds.json
expect_path "界面 QA 判据的按产品分文件" "docs/ui-criteria/products/xiaohuangya.md" \
  "$MMW" artifact path ui-criteria --sub products/xiaohuangya.md
expect_path "界面 QA 接线的按产品分文件" "docs/ui-qa-wiring/xiaohuangya.json" \
  "$MMW" artifact path ui-qa-wiring --sub xiaohuangya.json
expect_error "界面 QA 判据拒绝模式外的取值" "不匹配允许的模式" \
  "$MMW" artifact path ui-criteria --sub thresholds.yaml
expect_error "界面 QA 接线拒绝模式外的取值" "不匹配允许的模式" \
  "$MMW" artifact path ui-qa-wiring --sub products/xiaohuangya.json
expect_error "界面 QA 判据没有名字段" "没有名字段" \
  "$MMW" artifact path ui-criteria --name ui-qa --sub thresholds.json
expect_error "界面 QA 接线没有范围段" "没有范围段" \
  "$MMW" artifact path ui-qa-wiring --issue 52 --sub xiaohuangya.json

capture "当场取名提醒" "$MMW" artifact path research --name release --sub topic
check "当场取名提醒退出码" "0" "$LAST_STATUS"
check "当场取名提醒的路径" "docs/research/release/topic" "$(cat "$LAST_OUT")"
contains "当场取名提醒在标准错误" "写第一个文件之前先列一次父目录" "$(cat "$LAST_ERR")"
check "显式工作名查询不建立目录" "$artifact_path_dirs_before" "$(find . -type d -print | sort)"

echo
echo "artifact path 的缺省名字段"
orig_branch="$(git -C "$REPO" branch --show-current)"
expect_error "主检出缺省名字段不回退" "请用户用当前宿主开一棵工作树" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$REPO" "$MMW"

git -C "$REPO" switch -q -c feat-login
expect_error "主检出上的任务分支也不算" "请用户用当前宿主开一棵工作树" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$REPO" "$MMW"
git -C "$REPO" switch -q "$orig_branch"
git -C "$REPO" branch -D feat-login >/dev/null

linked_worktree="$REPO/.worktrees/feat-login"
git -C "$REPO" worktree add -q -b feat-login "$linked_worktree"
capture "缺省名字段来自当前分支" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$linked_worktree" "$MMW"
check "缺省名字段来自当前分支退出码" "0" "$LAST_STATUS"
check "缺省名字段来自当前分支" "docs/specs/feat-login/spec.md" "$(cat "$LAST_OUT")"
check "缺省名字段没有标准错误" "" "$(cat "$LAST_ERR")"

git -C "$linked_worktree" switch -q -c cursor/feat-login
capture "缺省名字段去掉宿主前缀" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$linked_worktree" "$MMW"
check "缺省名字段去掉宿主前缀退出码" "0" "$LAST_STATUS"
check "缺省名字段去掉宿主前缀" "docs/specs/feat-login/spec.md" "$(cat "$LAST_OUT")"
check "缺省名字段不含宿主前缀" "0" \
  "$(grep -c cursor <<<"$(cat "$LAST_OUT")" || true)"

expect_path "显式 --name 覆盖当前分支" "docs/specs/other-work/spec.md" \
  "$MMW" artifact path spec --name other-work

detached_worktree="$REPO/.worktrees/artifact-detached"
git -C "$REPO" worktree add -q --detach "$detached_worktree" HEAD
failure_dirs_before="$(find "$REPO" -type d -print | sort)"

expect_error "仓库外缺省名字段不回退" "不在 git 仓库里" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$WORK" "$MMW"
expect_error "detached worktree 缺省名字段不回退" "当前没有任务分支" \
  bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact path spec' _ "$detached_worktree" "$MMW"
check "缺省名字段的拒绝路径不建目录" "$failure_dirs_before" "$(find "$REPO" -type d -print | sort)"

git -C "$REPO" switch -q "$orig_branch"
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
expect_error "任务 worktree 不套路径形状" "git worktree list" \
  "$MMW" artifact path worktree
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
# 取值列表用「逗号加空格」逐项分隔。分隔错了的话，读错误提示的人会把两个取值
# 当成一个，例如把 `evidence questionnaire` 当成一个合法取值。
expect_error "允许的取值逐项分隔" \
  "understanding.md, evidence, questionnaire, wizard, diagnosis, architecture-review, dispatch, outbox" \
  "$MMW" artifact path scratch --name release --sub nosuchsub
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
expect_error "小写 README 前缀不能伪装固定文件" "不能用固定取值的大小写变体" \
  "$MMW" artifact path prototype --name probe --sub readme.md/extra
expect_error "固定 README 后面不能再接路径" "文件名后面不能接路径段" \
  "$MMW" artifact path prototype --name probe --sub README.md/extra
expect_error "sub 拒绝非法首字符" "首字符必须是字母或数字" \
  "$MMW" artifact path research --name release --sub -topic
expect_error "sub 拒绝其他非法字符" "只能包含小写字母、数字、点、下划线和连字符" \
  "$MMW" artifact path research --name release --sub 'topic$'
expect_error "sub 拒绝中间空段" "空路径段" \
  "$MMW" artifact path research --name release --sub topic//detail
expect_error "sub 拒绝换行" "不能包含换行" \
  "$MMW" artifact path research --name probe --sub $'safe\n/../../../../../escape'

echo
echo "artifact list"
mkdir -p \
  docs/research/list-work/issue-42/scoped \
  docs/research/list-work/unscoped \
  docs/research/list-work/issue-99/incomplete \
  docs/research/other-work/ignored \
  docs/prototypes/list-work/issue-7/demo \
  docs/prototypes/list-work/gallery \
  docs/prototypes/list-work/empty
printf '# Scoped research\n' > docs/research/list-work/issue-42/scoped/README.md
printf '# Unscoped research\n' > docs/research/list-work/unscoped/README.md
printf '# Other work\n' > docs/research/other-work/ignored/README.md
printf '# Scoped prototype\n' > docs/prototypes/list-work/issue-7/demo/README.md
printf '# Unscoped prototype\n' > docs/prototypes/list-work/gallery/README.md
mkdir -p docs/research/artifact-work/default
printf '# Default name segment\n' > docs/research/artifact-work/default/README.md

mkdir -p "$WORK/list-bin"
cat > "$WORK/list-bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$MMW_LIST_LOG"

case "$*" in
  "repo view --json nameWithOwner -q .nameWithOwner")
    echo "o/r" ;;
  "api --paginate repos/o/r/issues/88/sub_issues")
    cat "$MMW_LIST_CHILDREN" ;;
  *)
    echo "stub gh: 没预置这条命令：$*" >&2
    exit 90 ;;
esac
STUB
chmod +x "$WORK/list-bin/gh"
export PATH="$WORK/list-bin:$PATH"
export MMW_LIST_LOG="$WORK/list-gh.log"
cat > "$WORK/list-children.json" <<'JSON'
[
  {"number": 70, "state": "open", "title": "还在处理", "labels": [{"name": "wayfinder:research"}], "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 21, "state": "closed", "title": "不是 decision ticket", "labels": [{"name": "ready-for-agent"}], "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 16, "state": "closed", "title": "已关闭原型", "labels": [{"name": "wayfinder:prototype"}], "issue_dependencies_summary": {"blocked_by": 0}},
  {"number": 12, "state": "closed", "title": "已关闭对谈", "labels": [{"name": "wayfinder:grilling"}], "issue_dependencies_summary": {"blocked_by": 0}}
]
JSON
export MMW_LIST_CHILDREN="$WORK/list-children.json"

repository_list=$'- category=prototype name=list-work issue=7 sub=demo\n- category=prototype name=list-work sub=gallery\n- category=research name=list-work issue=42 sub=scoped\n- category=research name=list-work sub=unscoped'
: > "$MMW_LIST_LOG"
capture "显式工作名只列仓库候选" "$MMW" artifact list --name list-work
check "显式工作名只列仓库候选退出码" "0" "$LAST_STATUS"
check "显式工作名只列已保存产物" "$repository_list" "$(cat "$LAST_OUT")"
check "显式工作名只列仓库候选标准错误" "" "$(cat "$LAST_ERR")"
check "不传 map 不调用 GitHub" "" "$(cat "$MMW_LIST_LOG")"

: > "$MMW_LIST_LOG"
capture "空清单" "$MMW" artifact list --name empty-work
check "空清单退出码" "0" "$LAST_STATUS"
check "空清单没有标准输出" "" "$(cat "$LAST_OUT")"
check "空清单没有标准错误" "" "$(cat "$LAST_ERR")"
check "空清单不调用 GitHub" "" "$(cat "$MMW_LIST_LOG")"

: > "$MMW_LIST_LOG"
list_worktree="$REPO/.worktrees/artifact-work"
git -C "$REPO" worktree add -q -b artifact-work "$list_worktree"
mkdir -p "$list_worktree/docs/research/artifact-work/default"
printf '# Default name segment\n' > "$list_worktree/docs/research/artifact-work/default/README.md"
capture "缺省名字段" bash -c 'cd "$1" && MMW_HOST=claude-code "$2" artifact list' \
  _ "$list_worktree" "$MMW"
check "缺省名字段退出码" "0" "$LAST_STATUS"
check "缺省名字段列已保存产物" \
  "- category=research name=artifact-work sub=default" "$(cat "$LAST_OUT")"
check "缺省名字段没有标准错误" "" "$(cat "$LAST_ERR")"
check "缺省名字段不调用 GitHub" "" "$(cat "$MMW_LIST_LOG")"

: > "$MMW_LIST_LOG"
capture "给 map 时加入结论评论候选" "$MMW" artifact list --name list-work --map 88
check "给 map 时加入结论评论候选退出码" "0" "$LAST_STATUS"
check "给 map 时过滤并排序候选" \
  "$repository_list"$'\n- issue=12 结论评论 已关闭对谈\n- issue=16 结论评论 已关闭原型' \
  "$(cat "$LAST_OUT")"
check "给 map 时没有标准错误" "" "$(cat "$LAST_ERR")"
check "给 map 时只查询子 issue" \
  $'repo view --json nameWithOwner -q .nameWithOwner\napi --paginate repos/o/r/issues/88/sub_issues' \
  "$(cat "$MMW_LIST_LOG")"

# 读不到 map 时不能只列仓库那一半然后成功返回。调用方拿这份清单补必读材料声明，
# 缺了结论评论那一半会让它以为 map 上没有已关闭的 decision ticket，于是一条上游
# 结论都不补——那正是必读材料声明本身要修的失效。
: > "$MMW_LIST_LOG"
capture "读不到 map 时失败" "$MMW" artifact list --name list-work --map 77
check "读不到 map 时退出码" "1" "$LAST_STATUS"
check "读不到 map 时没有标准输出" "" "$(cat "$LAST_OUT")"
contains "读不到 map 时点名编号" "读不到 map 77 的子 issue" "$(cat "$LAST_ERR")"

before_dirs="$(find . -type d -print | sort)"

echo
echo "artifact usage"
capture "无参用法" "$MMW" artifact
check "无参用法退出码" "2" "$LAST_STATUS"
check "无参用法没有标准输出" "" "$(cat "$LAST_OUT")"
usage_text="$(cat "$LAST_ERR")"
contains "无参用法有 path 说明" "mmw artifact path" "$usage_text"
contains "无参用法有 index 说明" "mmw artifact index" "$usage_text"
contains "无参用法有 check 说明" "mmw artifact check" "$usage_text"
contains "无参用法有 list 说明" "mmw artifact list" "$usage_text"
contains "无参用法列出 spec 术语" $'spec\tspec' "$usage_text"
contains "无参用法列出解释 HTML 术语" $'explanation\t解释 HTML' "$usage_text"
contains "无参用法列出 agent brief 术语" $'agent-brief\tagent brief' "$usage_text"

after_dirs="$(find . -type d -print | sort)"
check "查询不建立目录" "$before_dirs" "$after_dirs"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
