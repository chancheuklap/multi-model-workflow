#!/usr/bin/env bash
# 适配层。只有模型专用宿主（Claude Code、Codex CLI）需要它：这类宿主派不了别家模型的
# 子代理，得起无头进程。多模型宿主（Cursor、pi、Droid）在角色文件里直接指定模型，不用这个。
#
# 它只做机器能判死的事：读角色参数、把角色文件正文与技能名单抄进提示词开头、
# 把命令行一次拼对、抓会话号。
# 这次干什么、建不建工作树、该派谁，是判断，留给主线程。
#
#   dispatch.sh run    --role <角色> --cwd <目录> --prompt <文件> [--add-dir <目录>]
#   dispatch.sh resume --role <角色> --cwd <目录> --session <会话号> --prompt <文件>
#   dispatch.sh preview --role <角色> --prompt <文件>          # 只打印会送出去的全文，不派
#
# 六份角色都往这里投，不必先自己判断走原生还是无头：碰到本宿主自家模型的角色，
# 脚本回 NATIVE=<角色名> 并退 4，告诉调用方改用宿主的子代理工具、subagent_type 填什么。
#
# run / resume 头两行是机器可读的 SESSION= 与 EXIT=，之后是被派者的最后一条消息。
# 会话号不落盘：主线程后台起、从输出里读，少一套记账。
# 后台起由调用方负责——审一轮、落地一份计划都常超前台超时上限。

set -euo pipefail

PLUGIN_ROOT="${MMW_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ROLES_DIR="$PLUGIN_ROOT/roles"
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
# 角色文件正文：frontmatter 之后的全部
role_body() {  # $1=角色文件
  awk 'n>=2; /^---$/{n++}' "$1"
}

# 送进被派进程的完整提示词。脚本只做拼接，一个字的内容都不在这里——
# 角色说明与边界在角色文件正文，方法论在技能里，这次干什么由调用方写。
# 拼出来的四段长什么样，写在 skills/mmw-dispatch 里。
build_prompt() {  # $1=角色文件 $2=角色名 $3=这次的活
  printf '你的角色是 %s。\n' "$2"
  { role_body "$1"; printf '\n'; } | cat -s   # 压掉连续空行，正文与前后各隔一行
  printf '先读你已装的这几份 skill，照它们走：'
  role_list "$1" skills | paste -sd'、' -
  printf '\n\n## 这次的活\n\n'
  cat "$3"
}

# ---------- 参数 ----------
role="" cwd="" prompt="" add_dir="" session=""
sub="${1:-}"; [ -n "$sub" ] || die "缺子命令: run | resume | preview"
shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --role) role="$2"; shift 2 ;;
    --cwd) cwd="$2"; shift 2 ;;
    --prompt) prompt="$2"; shift 2 ;;
    --add-dir) add_dir="$2"; shift 2 ;;
    --session) session="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac
done
[ -n "$role" ] || die "--role 必填"
if [ "$sub" != preview ]; then
  [ -n "$cwd" ] || die "--cwd 必填"
  [ -d "$cwd" ] || die "--cwd 不是目录: $cwd"
fi

# 角色文件不走命令替换取路径：那样 die 只杀得掉子 shell，主流程会带着空值往下跑。
rf="$ROLES_DIR/$role.md"
[ -f "$rf" ] || die "角色不存在: ${role}（找的是 ${rf}）"

# 本宿主自家模型的角色由宿主原生派，脚本代劳不了，但可以把人指对地方——
# 于是调用方永远只记一条命令，不必自己先翻角色文件判断走哪条路。
NATIVE_MODELS="${MMW_NATIVE_MODELS:-fable opus sonnet haiku}"
is_native() {
  local m; m="$(role_field "$rf" model)"
  local n; for n in $NATIVE_MODELS; do case "$m" in "$n"|"$n"-*|*"/$n") return 0 ;; esac; done
  return 1
}

# ---------- 派发 ----------
dispatch_codex() {  # $1=resume 的会话号（空=首派）
  local model effort write sandbox
  model="$(role_field "$rf" model)"
  effort="$(role_field "$rf" effort)"
  write="$(role_field "$rf" write)"
  # 三个都必须由角色文件给出。缺了当场停——静默默认值等于围栏失效。
  [ -n "$model" ]  || die "角色 $role 缺 model"
  [ -n "$effort" ] || die "角色 $role 缺 effort"
  # write 是产品层的说法（这个角色能不能写盘），在这里翻成本宿主的沙箱档位。
  case "$write" in
    true)  sandbox="workspace-write" ;;
    false) sandbox="read-only" ;;
    *)     die "角色 $role 的 write 要么 true 要么 false，现在是「${write}」" ;;
  esac

  [ -n "$prompt" ] || die "--prompt 必填"
  [ -f "$prompt" ] || die "提示词文件不存在: $prompt"

  # 开工前预检：被派者那一侧得先装好方法论技能，否则它按名字找不到。
  # 缺了就是没跑 install.sh，当场报错，不让它开工后才发现。
  local skills_root="${MMW_AGENT_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"
  local sk
  while IFS= read -r sk; do
    [ -n "$sk" ] || continue
    [ -f "$skills_root/$sk/SKILL.md" ] || die "角色 ${role} 要读的技能没装到派发后端: ${skills_root}/${sk}（跑 ${PLUGIN_ROOT}/scripts/install.sh）"
  done < <(role_list "$rf" skills)

  # 可写角色首派前工作树必须干净：否则验收读 diff 时分不清哪些改动是它的。
  # 恢复会话不查——那时的脏正是它自己干的。
  if [ "$write" = "true" ] && [ -z "$1" ]; then
    local dirty
    dirty="$(git -C "$cwd" status --porcelain --untracked-files=all 2>/dev/null \
             | sed 's/^...//' | grep -v '^\.mmw/' | head -5 || true)"
    [ -z "$dirty" ] || die "工作树有未提交改动，先提交再派 ${role}：
$(printf '%s\n' "$dirty" | sed 's/^/  /')"
  fi

  local full; full="$(mktemp)"
  build_prompt "$rf" "$role" "$prompt" > "$full"

  local last; last="$(mktemp)"
  local args=(exec -C "$cwd" --sandbox "$sandbox" --color never --json
              -m "$model" -c "model_reasoning_effort=\"$effort\"" -o "$last")
  # 用 if 不用 &&：set -e 下 `[ 假 ] && …` 会让整条语句返回非零，脚本当场退出。
  if [ -n "$add_dir" ]; then args+=(--add-dir "$add_dir"); fi
  # resume 自己没有 --sandbox / -C / --add-dir，那几个是 exec 的选项，
  # 所以 resume 与会话号追加在最后，围栏仍由前面的 exec 选项钉住。
  if [ -n "$1" ]; then args+=(resume "$1"); fi

  # 会话号在第一个事件里：{"type":"thread.started","thread_id":"..."}。
  # 走 --json 拿，不 grep 带色码的文本头。
  local events rc=0
  events="$(mktemp)"
  set +e
  "$CODEX_BIN" "${args[@]}" - < "$full" > "$events" 2>&1
  rc=$?
  set -e
  rm -f "$full"

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

case "$sub" in
  run|resume)
    if is_native; then
      echo "NATIVE=$role"
      echo "这份角色用本宿主自己的子代理工具派，subagent_type 填 ${role}。" \
           "模型、思考档、工具白名单由宿主按角色文件强制执行；开工提示词里让它读：" >&2
      role_list "$rf" skills | paste -sd'、' - >&2
      exit 4
    fi
    if [ "$sub" = resume ]; then
      [ -n "$session" ] || die "--session 必填"
      dispatch_codex "$session"
    else
      dispatch_codex ""
    fi ;;
  preview) [ -n "$prompt" ] || die "--prompt 必填"
           build_prompt "$rf" "$role" "$prompt" ;;
  *)      die "未知子命令: $sub（run | resume | preview）" ;;
esac
