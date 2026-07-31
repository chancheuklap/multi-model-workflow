#!/usr/bin/env bash
# 适配层。只有模型专用宿主（Claude Code、Codex CLI）需要它：这类宿主派不了别家模型的
# 子代理，得起无头进程。多模型宿主（Cursor、pi、Droid）在角色文件里直接指定模型，不用这个。
#
# 它只做机器能判死的事：读角色参数、把命令行一次拼对、抓会话号、按角色声明的边界核越界。
# 它不组装提示词、不建工作树、不判该派谁——那些是判断，留给主线程。
#
#   dispatch.sh run    --role <角色> --cwd <目录> --prompt <文件> [--add-dir <目录>] [--schema <文件>]
#   dispatch.sh resume --role <角色> --cwd <目录> --session <会话号> --prompt <文件>
#   dispatch.sh check  --role <角色> --cwd <目录> --since <提交>
#
# run / resume 头两行是机器可读的 SESSION= 与 EXIT=，之后是被派者的最后一条消息。
# 会话号不落盘：主线程后台起、从输出里读，少一套记账。
# 后台起由调用方负责——审一轮、落地一份计划都常超前台超时上限。

set -euo pipefail

ROLES_DIR="${MMW_ROLES_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../roles" && pwd)}"
CODEX_BIN="${CODEX_BIN:-codex}"

die() { echo "ERROR: $*" >&2; exit 2; }

# ---------- 角色文件 ----------
# frontmatter 取标量：sed 掐出两条 --- 之间，取 `key: value`
role_field() {  # $1=角色文件 $2=字段
  sed -n '/^---$/,/^---$/p' "$1" | sed -n "s/^$2:[[:space:]]*//p" | head -1
}
# frontmatter 取列表：`key:` 之后连续的 `  - item`
role_list() {  # $1=角色文件 $2=字段
  sed -n '/^---$/,/^---$/p' "$1" | awk -v k="$2:" '
    $0 == k { grab=1; next }
    grab && /^[[:space:]]+-[[:space:]]/ { sub(/^[[:space:]]+-[[:space:]]*/, ""); print; next }
    grab { exit }'
}

# ---------- 参数 ----------
role="" cwd="" prompt="" add_dir="" schema="" session="" since=""
sub="${1:-}"; [ -n "$sub" ] || die "缺子命令: run | resume | check"
shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --role) role="$2"; shift 2 ;;
    --cwd) cwd="$2"; shift 2 ;;
    --prompt) prompt="$2"; shift 2 ;;
    --add-dir) add_dir="$2"; shift 2 ;;
    --schema) schema="$2"; shift 2 ;;
    --session) session="$2"; shift 2 ;;
    --since) since="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac
done
[ -n "$role" ] || die "--role 必填"
[ -n "$cwd" ] || die "--cwd 必填"
[ -d "$cwd" ] || die "--cwd 不是目录: $cwd"

# 角色文件不走命令替换取路径：那样 die 只杀得掉子 shell，主流程会带着空值往下跑。
rf="$ROLES_DIR/$role.md"
[ -f "$rf" ] || die "角色不存在: ${role}（找的是 ${rf}）"

# ---------- 派发 ----------
dispatch_codex() {  # $1=resume 的会话号（空=首派）
  local model effort sandbox
  model="$(role_field "$rf" model)"
  effort="$(role_field "$rf" effort)"
  sandbox="$(role_field "$rf" sandbox)"
  # 三个都必须由角色文件给出。缺了当场停——静默默认值等于围栏失效。
  [ -n "$model" ]   || die "角色 $role 缺 model"
  [ -n "$effort" ]  || die "角色 $role 缺 effort"
  [ -n "$sandbox" ] || die "角色 $role 缺 sandbox（read-only 还是 workspace-write）"

  [ -n "$prompt" ] || die "--prompt 必填"
  [ -f "$prompt" ] || die "提示词文件不存在: $prompt"

  # 开工前预检：角色点名要读的技能得先装进无头这一侧的技能根，
  # 缺装备当场报错，不让它开工后才发现。
  local skills_root="${MMW_AGENT_SKILLS_DIR:-$HOME/.codex/skills}"
  local sk
  while IFS= read -r sk; do
    [ -n "$sk" ] || continue
    [ -f "$skills_root/$sk/SKILL.md" ] || die "角色 $role 要读的技能未装: $skills_root/$sk/SKILL.md"
  done < <(role_list "$rf" skills)

  # 可写角色首派前工作树必须干净：否则收工核越界时分不清哪些改动是它的。
  # 恢复会话不查——那时的脏正是它自己干的。
  if [ "$sandbox" = "workspace-write" ] && [ -z "$1" ]; then
    local dirty
    dirty="$(git -C "$cwd" status --porcelain --untracked-files=all 2>/dev/null \
             | sed 's/^...//' | grep -v '^\.mmw/' | head -5 || true)"
    [ -z "$dirty" ] || die "工作树有未提交改动，先提交再派 ${role}：
$(printf '%s\n' "$dirty" | sed 's/^/  /')"
  fi

  local last; last="$(mktemp)"
  local args=(exec -C "$cwd" --sandbox "$sandbox" --color never --json
              -m "$model" -c "model_reasoning_effort=\"$effort\"" -o "$last")
  # 这几个用 if 不用 &&：set -e 下 `[ 假 ] && …` 会让整条语句返回非零，脚本当场退出。
  if [ -n "$add_dir" ]; then args+=(--add-dir "$add_dir"); fi
  if [ -n "$schema" ]; then
    [ -f "$schema" ] || die "返回结构文件不存在: $schema"
    args+=(--output-schema "$schema")
  fi
  # resume 自己没有 --sandbox / -C / --add-dir，那几个是 exec 的选项，
  # 所以 resume 与会话号追加在最后，围栏仍由前面的 exec 选项钉住。
  if [ -n "$1" ]; then args+=(resume "$1"); fi

  # 会话号在第一个事件里：{"type":"thread.started","thread_id":"..."}。
  # 走 --json 拿，不 grep 带色码的文本头。
  local events rc=0
  events="$(mktemp)"
  set +e
  "$CODEX_BIN" "${args[@]}" - < "$prompt" > "$events" 2>&1
  rc=$?
  set -e

  local sid
  sid="$(sed -n 's/.*"thread_id":"\([^"]*\)".*/\1/p' "$events" | head -1)"
  echo "SESSION=${sid:-unknown}"
  echo "EXIT=$rc"
  echo "--- 最后一条消息（事实需主线程亲验）---"
  cat "$last" 2>/dev/null || echo "(无最后消息；排障读 $events)"
  [ "$rc" -eq 0 ] || echo "--- 事件流 $events ---"
  rm -f "$last"
  return "$rc"
}

# ---------- 越界 ----------
# 角色声明 allow-paths 就是白名单（只准碰这些），声明 deny-paths 就是黑名单（禁碰这些）。
# 两者都没有的角色不写盘，没什么可核。
cmd_check() {
  [ -n "$since" ] || die "--since 必填（起点提交）"
  local touched allow deny bad
  # --untracked-files=all：否则 git 把整棵未跟踪目录折成一条，核不到文件级。
  touched="$( { git -C "$cwd" diff --name-only "$since" HEAD 2>/dev/null
                git -C "$cwd" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'; } \
              | sort -u | grep -v '^[[:space:]]*$' | grep -v '^\.mmw/' || true )"
  [ -z "$touched" ] && { echo "CLEAN: 没有改动"; return 0; }

  allow="$(role_list "$rf" allow-paths)"
  deny="$(role_list "$rf" deny-paths)"

  if [ -n "$allow" ]; then
    local pat; pat="$(printf '%s\n' "$allow" | sed 's/[].[^$\\*]/\\&/g' | paste -sd'|' -)"
    bad="$(printf '%s\n' "$touched" | grep -vE "^($pat)" || true)"
  elif [ -n "$deny" ]; then
    local pat; pat="$(printf '%s\n' "$deny" | sed 's/[].[^$\\*]/\\&/g' | paste -sd'|' -)"
    bad="$(printf '%s\n' "$touched" | grep -E "^($pat)" || true)"
  else
    echo "CLEAN: 角色 $role 没声明可写边界"; return 0
  fi

  [ -z "$bad" ] && { echo "CLEAN: 改动都在 $role 的边界内"; return 0; }
  echo "VIOLATION: $role 碰了边界外的文件，打回重来：" >&2
  printf '%s\n' "$bad" | sed 's/^/  /' >&2
  return 3
}

case "$sub" in
  run)    dispatch_codex "" ;;
  resume) [ -n "$session" ] || die "--session 必填"; dispatch_codex "$session" ;;
  check)  cmd_check ;;
  *)      die "未知子命令: $sub" ;;
esac
