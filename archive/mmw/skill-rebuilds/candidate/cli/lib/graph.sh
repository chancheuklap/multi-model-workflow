#!/usr/bin/env bash
# 结构图谱：建一次、验证建对了。
#
# 构建的实现在 mcp/graphify_ensure.py，这一层只做转发和报告。
#
# 图谱本身是本机派生物：不进版本库，也不跨机器同步。

set -euo pipefail

mmw_graph_ensure_bin() {
  echo "$MMW_ROOT/mcp/graphify_ensure.py"
}

# 显式点名要建，就真的建一次，不因为"看着还新鲜"直接返回：会来敲这条命令的场合
# 是配置刚改完、或者怀疑图跟代码对不上，那时新鲜度判断本身就是被怀疑的那一方。
mmw_graph_build() {
  python3 "$(mmw_graph_ensure_bin)" --repo "$(mmw_repo_root)" --force
}

# 图里各类关系各有多少条。判据不是数量本身，是配置里声明要算的那几类边一条都
# 不能是零——某一类是零，说明配置跟当前代码结构对不上，而不是这个仓库没有那种
# 关系。
mmw_graph_verify() {
  local root graph
  root="$(mmw_repo_root)"
  graph="$root/graphify-out/graph.json"

  if [ ! -f "$graph" ]; then
    echo "图不在：$graph" >&2
    echo "先跑 mmw graph build" >&2
    return 1
  fi

  echo "图        : $graph"
  echo "节点      : $(jq '.nodes | length' "$graph")"
  echo "边        : $(jq '.links | length' "$graph")"
  echo "各类关系  :"
  jq -r '.links | group_by(.relation) | map({relation: .[0].relation, count: length})
         | sort_by(-.count) | .[] | "            \(.count)\t\(.relation)"' "$graph"

  # 跨语言边有没有、是谁建的，是两件事。关系名从合同读，不在这里手抄第二份。
  local relations present configured
  relations="$(jq -r '.graph_relations | del(._why) | .[][]' \
    "$MMW_ROOT/config/retrieval-contract.json")"
  present="$(jq -r --arg rel "$relations" \
    '[.links[].relation] | unique | map(select(. as $r | ($rel | split("\n")) | index($r)))
     | length' "$graph")"
  configured="$(jq -r '.retrieval.graph // {} | keys[]? ' "$(mmw_config_path)" 2>/dev/null || true)"

  echo
  if [ "$present" -gt 0 ] && [ -z "$configured" ]; then
    cat <<'NOTE'
跨语言边  : 图里有，但这个仓库没有在 .mmw.json 里配过它们——说明这份图是别的
            入口建的，不是插件建的。插件重建一次就会把它们全丢掉，而文件名和
            体积看不出区别。在配好之前，不要让插件重建这个仓库的图。
NOTE
  elif [ "$present" -eq 0 ] && [ -z "$configured" ]; then
    cat <<'NOTE'
跨语言边  : 没有。图里只有各语言各自扫出来的关系，前端发出的请求和后端处理它的
            函数之间没有边，装饰器注册的处理函数也连不到调用方。要补上，看
            mmw-retrieval 技能的 building.md。
NOTE
  elif [ "$present" -eq 0 ]; then
    cat <<'NOTE'
跨语言边  : 配了，但图里一条都没有。配置跟当前代码结构对不上，按 building.md
            第 1 节那张表逐项核对。
NOTE
  else
    echo "跨语言边  : ${present} 类都在"
  fi
}
