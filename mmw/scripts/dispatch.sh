#!/usr/bin/env bash
# 起一个无头 Codex 进程。只有模型专用宿主用得上：那类宿主派不了别家模型的子代理。
# 多模型宿主（pi、Cursor、Droid）在角色文件里直接指定模型，五个角色全走原生，不碰这个脚本。
#
# 走哪条路不在这里判断——装机时读 adapters/<宿主>/fields.json 的模型表就定死了，
# 本宿主派得了的角色装成原生子代理，翻出 null 的才落到这里。
#
#   dispatch.sh run    --role <角色> --cwd <目录> --brief <文件> [--add-dir <目录>]
#   dispatch.sh resume --role <角色> --cwd <目录> --session <会话号> --brief <文件>
#
# 它只做机器能判死的事：读角色参数、把角色文件正文抄进提示词开头、把命令行一次拼对、抓会话号。
# 这次干什么、建不建工作树、该派谁，是判断，留给主线程。
#
# 头两行是机器可读的 SESSION= 与 EXIT=，之后是被派者的最后一条消息。
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
# 角色文件正文：frontmatter 之后的全部，含「线下」那一节——
# 那几段是给读源码的人看的，抄过去多几行，不值得为它写一套切割。
role_body() {  # $1=角色文件
  awk 'n>=2; /^---$/{n++}' "$1"
}

# 送进被派进程的完整提示词，三段。脚本只做拼接，一个字的内容都不在这里——
# 角色说明与边界在角色文件正文，方法论在技能里，这次干什么由调用方写。
#
# 第二段非抄不可：无头那一侧看不见我们的角色文件。它进去之后按第一行的任务名，
# 照正文那张表读到具体哪一份方法——技能由 install.sh 软链在它自己的技能目录下。
build_prompt() {  # $1=角色文件 $2=角色名 $3=这次的活
  printf '你的角色是 %s。\n' "$2"
  { role_body "$1"; printf '\n'; } | cat -s   # 压掉连续空行，正文与前后各隔一行
  printf '\n## 这次的活\n\n'
  cat "$3"
}

# ---------- 参数 ----------
role="" cwd="" brief="" add_dir="" session=""
sub="${1:-}"; [ -n "$sub" ] || die "缺子命令: run | resume"
shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --role) role="$2"; shift 2 ;;
    --cwd) cwd="$2"; shift 2 ;;
    --brief) brief="$2"; shift 2 ;;
    --add-dir) add_dir="$2"; shift 2 ;;
    --session) session="$2"; shift 2 ;;
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

  [ -n "$brief" ] || die "--brief 必填"
  [ -f "$brief" ] || die "这次的活那份文件不存在: $brief"

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
  build_prompt "$rf" "$role" "$brief" > "$full"

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
  run)    dispatch_codex "" ;;
  resume) [ -n "$session" ] || die "--session 必填"
          dispatch_codex "$session" ;;
  *)      die "未知子命令: $sub（run | resume）" ;;
esac
