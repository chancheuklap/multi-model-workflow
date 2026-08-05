#!/usr/bin/env bash
# 领域文档：落点在哪、下一个 ADR 编号是几。
#
# 只答机械问题。「这次要碰哪几个上下文」是读 CONTEXT-MAP.md 正文之后的判断，
# 归技能，不归这里——CLI 侧写一条匹配规则就等于凭空造了一条配置没持有的判据。
#
# 草稿编号那条分支也不归这里：几条分支同时写 ADR 时要先用 draft- 名，判断
# 「我现在是不是那种分支」CLI 做不可靠，判据在 mmw-domain-modeling/ADR-FORMAT.md。

set -euo pipefail

# 这个仓库的领域文档是哪种形态。输出两列：形态、路径。
#   map      有索引，路径是索引本身，读它再决定取哪几份 leaf
#   single   单上下文，路径是根 CONTEXT.md
#   none     两个都没有，直接往下走，别提它缺失
#
# 第三列是照着做的话，给读它的 agent 看。没有这一列，每个要读领域文档的技能
# 都得自己把三种形态解释一遍——那段话原本在五份技能里逐字重复。
mmw_domain_path() {
  local root map fallback
  root="$(mmw_repo_root)"
  map="$(mmw_config '.domain.map // "CONTEXT-MAP.md"')"
  fallback="$(mmw_config '.domain.fallback // "CONTEXT.md"')"

  if [ -f "$root/$map" ]; then
    printf 'map\t%s\t这是索引：读它，再读取它列出的本次相关全部 leaf\n' "$root/$map"
  elif [ -f "$root/$fallback" ]; then
    printf 'single\t%s\t单上下文，读这一份\n' "$root/$fallback"
  else
    printf 'none\t\t这个仓库没有领域文档：直接往下走，不要停下来建，也不要提它缺失\n'
  fi
}

# 从 MMW 持有的种子同步目标仓库规则。Python 模块负责整轮预检和原子写入；
# shell 只提供当前仓库、配置与宿主，不复制 Markdown 合同。
mmw_domain_sync() {
  local root config host
  root="$(mmw_repo_root)"
  config="$(mmw_require_config)" || return 1
  host="$(mmw_host)" || return 1
  python3 "$MMW_ROOT/cli/lib/context_docs.py" sync \
    --root "$root" \
    --config "$config" \
    --host "$host"
}

# 检查器与同步器消费同一份种子和配置，避免 doctor 另抄一套受管正文。
mmw_domain_check() {
  local root config host
  root="$(mmw_repo_root)"
  config="$(mmw_require_config)" || return 1
  host="$(mmw_host)" || return 1
  python3 "$MMW_ROOT/cli/lib/context_docs.py" check \
    --root "$root" \
    --config "$config" \
    --host "$host"
}

# 写入侧要的两个落点：新上下文的根目录、ADR 目录。读的那一侧用 mmw_domain_path
# 就够，写的那一侧还要知道往哪建。
mmw_domain_dirs() {
  local root
  root="$(mmw_repo_root)"
  printf 'context\t%s\n' "$root/$(mmw_config '.domain.context_dir // "docs/context"')"
  printf 'adr\t%s\n' "$root/$(mmw_config '.domain.adr_dir // "docs/adr"')"
}

# 下一个 ADR 编号，四位、零填充。目录不存在或空的时候是 0001。
# 只数正式编号，draft- 开头的不参与——它们还没占号。
mmw_domain_adr_next() {
  local root dir max next
  root="$(mmw_repo_root)"
  dir="$root/$(mmw_config '.domain.adr_dir // "docs/adr"')"

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
