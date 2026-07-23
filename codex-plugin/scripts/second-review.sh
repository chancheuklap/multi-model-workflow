#!/usr/bin/env bash
# 中性第二审查模型适配器：stdin 是完整 prompt，stdout 是审查回执。
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 2; }

worktree=""
while [ $# -gt 0 ]; do
  case "$1" in
    --worktree) worktree="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac
done

[ -n "$worktree" ] || die "--worktree 必填"
[ -d "$worktree" ] || die "worktree 不存在:$worktree"
[ -n "${MMW_SECOND_REVIEW_CMD:-}" ] || die "未配置 MMW_SECOND_REVIEW_CMD"
timeout_seconds="${MMW_SECOND_REVIEW_TIMEOUT_SECONDS:-900}"
case "$timeout_seconds" in
  ''|*[!0-9]*) die "MMW_SECOND_REVIEW_TIMEOUT_SECONDS 必须是正整数" ;;
  0) die "MMW_SECOND_REVIEW_TIMEOUT_SECONDS 必须大于 0" ;;
esac

temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/mmw-second-review.XXXXXX")"
trap 'rm -rf "$temp_dir"' EXIT
prompt_file="$temp_dir/prompt"
output_file="$temp_dir/output"
error_file="$temp_dir/error"
cat >"$prompt_file"
[ -s "$prompt_file" ] || die "stdin prompt 为空"

command -v perl >/dev/null 2>&1 || die "缺少超时执行器:perl"
set +e
(
  cd "$worktree"
  perl -e 'alarm shift; exec "/bin/sh", "-c", "exec $ENV{MMW_SECOND_REVIEW_CMD}"' "$timeout_seconds"
) <"$prompt_file" >"$output_file" 2>"$error_file"
provider_status=$?
set -e

if [ "$provider_status" -eq 142 ]; then
  die "第二审查模型超时(${timeout_seconds}s)"
fi
if [ "$provider_status" -ne 0 ]; then
  [ ! -s "$error_file" ] || sed 's/^/provider: /' "$error_file" >&2
  die "第二审查模型退出码:$provider_status"
fi
[ -s "$output_file" ] || die "第二审查模型返回空输出"

cat "$output_file"
