#!/usr/bin/env bash
# mmw —— pi 原生 multi-model-workflow 统一 CLI
#
#   mmw where | mmw handoff | mmw pin | mmw spinoff
#   mmw note set|show                            # 讨论态书签(现场注记)
#   mmw approve --report <设计文档>...           # 唯一人闸:确认设计,盖承重指纹,过门放权
#   mmw prototype start|checkpoint               # design 内层原型迭代:登记/接管→逐轮验证→接受/废止
#   mmw task new|resume|scope|cleanup|team|escalate
#   mmw loop init|step|attendance|softstop|surface|resume|status|close   # build 执行账本(只记录)
#   mmw review start ...
#   mmw worker dispatch|verify|resume|check-docs ...
#   mmw worker plan-dispatch|plan-resume|plan-check ...
#   mmw release init|where|stage run|stage done|stage fail|round|surface|resume|close|exit-check|receipt|dispatch
#   mmw package resolve|init|where|confirm|record-release|exit-check|close   # 出包阶段运行态(④终审后;where 自带 next 指路)
#   mmw help
#
# 用法(读完 skill 直接用):
#   推进(最常用,主线程每阶段):
#     mmw where                                查我在哪阶段/审闸/上阶段产出(prev_outputs)
#     mmw handoff --conclusion <词> [--produced <产出>]...   交接 + 推进(缺钉产出只警告;审闸收口核审查留痕)
#     mmw pin --produced <路径> [--phase <阶段>]             补钉产出到接力单(只登记,不推进)
#     mmw spinoff --tag <t> --finding <s>      中途挖到的旁路登记成关联子任务
#   讨论态书签 + prototype + 过门:
#     mmw note set --text "<一句话现场注记>" | mmw note show
#     mmw prototype start --kind <logic|ui|mixed> --question <q> --run <cmd> [--adopt --artifact <路径>]...
#     mmw prototype checkpoint --feedback <f> --change <c> --result <r> --verdict <continue|accepted|superseded> ...
#     mmw approve --report <主设计文档> [--report <合同文档>]...   确认设计(用户过门后执行;盖指纹,attendance→afk)
#   任务(入口/收尾,主仓库):
#     mmw task new --scenario <small-change|develop|bug> --slug <s> --title <t> --request '<用户原始需求与验收条件>' [--direction-given]
#     mmw task resume | mmw task cleanup --slug <s> | mmw task team(列全队在管 worktree)
#     mmw task escalate --to develop          bug/小改撞出系统性设计问题→原地升级完整设计路
#   执行账本(build 派发映射,断点恢复用;只记录不当闸):
#     mmw loop init | step add/done | attendance | softstop | surface | resume | status | close
#   审闸一条命令:
#     mmw review start --stage <design|plan|plan-impl|final|merge-impl> --source <...>
#   写码工人派发(准备 worktree/prompt/账本,工人由协调者在会话内 subagent 工具派 agent=pack-executor, async:true):
#     mmw worker dispatch --plan <p> --worktree <wt> | worker resume --worktree <wt> --instructions <f>
#     mmw worker note-run-id --worktree <wt> --id <run id>   # 派发后把 run id 落账,返修 resume 凭据
#     mmw worker verify --worktree <wt>       # 工人回执后跑:核 docs 边界门
#   写计划工人派发(同上,agent=plan-writer;隔离沙箱内、不 commit):
#     mmw worker plan-dispatch --plan <落点> --worktree <wt> [--design <d>] [--issue <i>]
#     mmw worker plan-resume --plan <落点> --worktree <wt> --instructions <f>
#     mmw worker verify --plan <落点> --worktree <wt>       # 核计划边界,过门才原子发布
#   进度板(负责人可读投影):
#     mmw progress render [--stdout]           从 task.json/loop-state 聚合 progress-board.md(--stdout 供 command 注入)
#   控制面(运行级值守 + 计划外分流):
#     mmw attend --mode attended|afk           自由切档
#     mmw unattended enter|status|exit         强无人:enter 过门禁才进,不静默降级
#     mmw side-finding record --tag <t> --disposition issue|fix [--finding <s>]   计划外分流落 open_items
#   发布红线:push / gh pr merge / 部署由 guard-redline(tool_call 拦截)交用户亲批,无令牌可自铸;
#   本地 git merge(含合并进 main)不拦——可逆、不出站,真正红线是它之后的 push。
# 状态平面固定为 .pi/multi-model-workflow/,worktree 根固定为 .pi/worktrees/。
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"

# 打头部注释全文(到 set -euo 前一行为止,不再硬编码行号截断)
usage() { sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; }

cmd="${1:-help}"; shift || true
case "$cmd" in
  where|handoff|pin|spinoff) exec bash "$D/flow.sh" "$cmd" "$@" ;;
  note|approve) exec bash "$D/note.sh" "$cmd" "$@" ;;
  prototype) exec bash "$D/prototype.sh" "$@" ;;
  task)   exec bash "$D/prepare.sh" "$@" ;;
  loop)   exec bash "$D/loop.sh" "$@" ;;
  review) exec bash "$D/review.sh" "$@" ;;
  worker) exec bash "$D/worker.sh" "$@" ;;
  release) exec bash "$D/release-flow.sh" "$@" ;;
  package) exec bash "$D/package-phase.sh" "$@" ;;
  progress) exec bash "$D/progress.sh" "$@" ;;
  attend|unattended|side-finding) exec bash "$D/steer.sh" "$cmd" "$@" ;;
  help|-h|--help) usage ;;
  *) echo "未知命令: $cmd" >&2; echo "跑 mmw help 看全部" >&2; exit 2 ;;
esac
