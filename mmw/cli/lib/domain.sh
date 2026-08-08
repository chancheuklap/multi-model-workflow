#!/usr/bin/env bash
# 领域文档：初始化 Map、同步与检查消费合同、下一个 ADR 编号是几。
#
# 只答机械问题。「这次要碰哪几个上下文」是读 CONTEXT-MAP.md 正文之后的判断，
# 归技能，不归这里——CLI 侧写一条匹配规则就等于凭空造了一条配置没持有的判据。
#
# 草稿编号那条分支也不归这里：几条分支同时写 ADR 时要先用 draft- 名，判断
# 「我现在是不是那种分支」CLI 做不可靠，判据在 mmw-domain-modeling/ADR-FORMAT.md。

set -euo pipefail

# 从 MMW 持有的种子同步目标仓库规则。Python 模块负责整轮预检和原子写入；
# shell 只提供当前仓库、配置与宿主，不复制 Markdown 合同。
mmw_domain_sync() {
  local root config host
  root="$(mmw_repo_root)"
  config="$(mmw_require_config)" || return 1
  host="${1:-}"
  if [ -z "$host" ]; then
    host="$(mmw_host)" || return 1
  fi
  python3 "$MMW_ROOT/cli/lib/context_docs.py" sync \
    --root "$root" \
    --config "$config" \
    --host "$host"
}

# 多上下文领域建模的首次 Map 骨架。Python 入口独占创建配置目标；shell 不复制
# 规则种子，也不代替领域建模流程填写项目拥有的 Contexts 与 Relationships。
mmw_domain_map_init() {
  local root config
  root="$(mmw_repo_root)"
  config="$(mmw_require_config)" || return 1
  python3 "$MMW_ROOT/cli/lib/context_docs.py" map-init \
    --root "$root" \
    --config "$config"
}

# 检查器与同步器消费同一份种子和配置，避免 doctor 另抄一套受管正文。
mmw_domain_check() {
  local root config host
  root="$(mmw_repo_root)"
  config="$(mmw_require_config)" || return 1
  host="${1:-}"
  if [ -z "$host" ]; then
    host="$(mmw_host)" || return 1
  fi
  python3 "$MMW_ROOT/cli/lib/context_docs.py" check \
    --root "$root" \
    --config "$config" \
    --host "$host"
}

# 路径查询与同步、检查共用 Python 配置边界。该入口只供本文件消费。
mmw_domain_validated_config() {
  local root config
  root="$(mmw_repo_root)"
  config="$(mmw_require_config)" || return 1
  python3 "$MMW_ROOT/cli/lib/context_docs.py" paths \
    --root "$root" \
    --config "$config"
}

# 下一个 ADR 编号，四位、零填充。目录不存在或空的时候是 0001。
# 只数正式编号，draft- 开头的不参与——它们还没占号。
mmw_domain_adr_next() {
  local root domain adr_dir dir max next
  root="$(mmw_repo_root)"
  domain="$(mmw_domain_validated_config)" || return 1
  adr_dir="$(jq -er '.adr_dir' <<< "$domain")" || return 1
  dir="$root/$adr_dir"

  max=0
  if [ -d "$dir" ]; then
    local f base num
    for f in "$dir"/*.md; do
      [ -e "$f" ] || continue
      base="$(basename "$f")"
      case "$base" in
        [0-9][0-9][0-9][0-9]-*) num="${base%%-*}" ;;
        *) continue ;;
      esac
      num=$((10#$num))
      if [ "$num" -gt "$max" ]; then
        max="$num"
      fi
    done
  fi

  next=$((max + 1))
  printf '%04d\n' "$next"
}
