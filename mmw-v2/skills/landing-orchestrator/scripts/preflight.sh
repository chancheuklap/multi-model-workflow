#!/usr/bin/env bash
# 编排技能的前置检查。任一不过即报错退出 1，不降级硬跑。
#
#   bash preflight.sh [消费仓库根目录]     缺省为当前目录
#
# 通过时 stdout 输出 models.md 解析出的 JSON（供技能后续步骤直接用），退出 0。
# 四项按序：HERDR_ENV=1；gh 已认证且仓库有远端；docs/agents/models.md 存在且可解析；
# herdr 的 agent kinds 覆盖表内每个宿主 kind。
set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="${1:-$PWD}"

die() { printf 'preflight: %s\n' "$1" >&2; exit 1; }

[ "${HERDR_ENV:-}" = 1 ] || die "HERDR_ENV 不是 1：编排者必须在 Herdr 管理的 pane 里运行"

command -v gh >/dev/null 2>&1 || die "找不到 gh"
gh auth status >/dev/null 2>&1 || die "gh 未认证（gh auth status 失败）"
[ -d "$REPO" ] || die "仓库目录不存在 ${REPO}"
git -C "$REPO" remote get-url origin >/dev/null 2>&1 || die "仓库没有远端 origin（${REPO}）"

MODELS="${REPO}/docs/agents/models.md"
[ -f "$MODELS" ] || die "缺 ${MODELS}（模板：$(dirname "$HERE")/reference/models.md）"
TABLE="$(python3 "${HERE}/models.py" "$MODELS")" || die "models.md 解析失败"

command -v herdr >/dev/null 2>&1 || die "找不到 herdr"
KINDS="$(herdr agent start --help 2>&1 | sed -n '/possible values:/{s/.*possible values: *//;s/\]//;p;}' | tr ',' ' ')"
[ -n "$KINDS" ] || die "从 herdr agent start --help 读不到 kind 列表"
for kind in $(printf '%s' "$TABLE" | python3 -c 'import json,sys; print(" ".join(sorted({v["kind"] for v in json.load(sys.stdin).values()})))'); do
  case " $KINDS " in
    *" ${kind} "*) ;;
    *) die "models.md 里的宿主 kind ${kind} 不在 herdr 支持的 kinds 内（${KINDS}）" ;;
  esac
done

printf '%s\n' "$TABLE"
