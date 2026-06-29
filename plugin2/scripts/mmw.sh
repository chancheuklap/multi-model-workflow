#!/usr/bin/env bash
# mmw —— multi-model-workflow 统一 CLI。
#
# 整个 plugin 的所有脚本一个入口:主线程 agent 和各阶段 sub-agent 读完 skill,
# 就用 `mmw <命令>` 推进环节 / 登记 / 派发,不用记 5 个脚本路径。薄路由——底层仍是
# 各专责脚本(prepare/flow/loop/review/codex-worker),mmw 只把统一动词转发过去。
#
# 用法(读完 skill 直接用):
#   推进(最常用,主线程每阶段):
#     mmw where                                查我在哪阶段/审闸/上阶段产出(prev_outputs)
#     mmw handoff --conclusion <词> [--produced <产出>]...   交接 + 推进
#     mmw spinoff --tag <t> --finding <s>      中途挖到的旁路登记成关联子任务
#   任务(入口/收尾,主仓库):
#     mmw task new --scenario <small-change|develop|bug> --slug <s> --title <t>
#     mmw task resume | mmw task cleanup --slug <s>
#   内层 loop(落地/审):
#     mmw loop init --kind <execution|review|contract-gate> | attendance | step | checklist | finding | softstop | surface | resume | exit-check
#   审闸一条命令:
#     mmw review start --stage <design|plan|plan-impl|final> --source <...>
#   Codex 落地派发:
#     mmw codex dispatch --plan <p> --worktree <wt> | codex resume --worktree <wt> --instructions <f>
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; }

cmd="${1:-help}"; shift || true
case "$cmd" in
  where|handoff|spinoff) exec bash "$D/flow.sh" "$cmd" "$@" ;;
  task)   exec bash "$D/prepare.sh" "$@" ;;
  loop)   exec bash "$D/loop.sh" "$@" ;;
  review) exec bash "$D/review.sh" "$@" ;;
  codex)  exec bash "$D/codex-worker.sh" "$@" ;;
  help|-h|--help) usage ;;
  *) echo "未知命令: $cmd" >&2; echo "跑 mmw help 看全部" >&2; exit 2 ;;
esac
