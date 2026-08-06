#!/usr/bin/env bash
# mmw init：把一个仓库配置成能跑这套工作流的样子。
#
# 幂等。每一步已经做过就跳过并报一行，重跑无害。已有配置只执行字段迁移；其他
# 已存在文件不覆盖，要删除的内容由人决定。

set -euo pipefail

# 每一步往这里追加一行，最后统一报。
MMW_INIT_LOG=""
mmw_init_say() {
  MMW_INIT_LOG="${MMW_INIT_LOG}$1
"
}

# 本轮自己动过、要提交进分支的仓库内文件，仓库根的相对路径。
MMW_INIT_TOUCHED=()
mmw_init_touch() {
  MMW_INIT_TOUCHED+=("$1")
}

mmw_init_config() {
  local root config default_config default_research default_evidence default_scratch temp config_mode
  root="$(mmw_repo_root)"
  config="$root/.mmw.json"
  default_config="$MMW_ROOT/cli/mmw.default.json"
  if [ -f "$config" ]; then
    if jq -e '.paths.research != null and .paths.investigations == null and .paths.evidence != null and .paths.scratch != null' "$config" >/dev/null 2>&1; then
      mmw_init_say "配置     : 已有 ${config}，无需迁移"
      return 0
    fi
    default_research="$(jq -er '.paths.research' "$default_config")" || return 1
    default_evidence="$(jq -er '.paths.evidence' "$default_config")" || return 1
    default_scratch="$(jq -er '.paths.scratch' "$default_config")" || return 1
    mmw_path_safe_base "$default_research" || return 1
    mmw_path_safe_base "$default_evidence" || return 1
    mmw_path_safe_base "$default_scratch" || return 1
    if config_mode="$(stat -f '%Lp' "$config" 2>/dev/null)"; then
      :
    elif config_mode="$(stat -c '%a' "$config" 2>/dev/null)"; then
      :
    else
      return 1
    fi
    temp="$(mktemp "$root/.mmw.json.migrate.XXXXXX")" || return 1
    if ! jq --arg research "$default_research" --arg evidence "$default_evidence" --arg scratch "$default_scratch" '
      .paths = (.paths // {}) |
      .paths.research //= $research |
      del(.paths.investigations) |
      .paths.evidence //= $evidence |
      .paths.scratch //= $scratch
    ' "$config" > "$temp"; then
      rm -f "$temp"
      return 1
    fi
    chmod "$config_mode" "$temp"
    mv -f "$temp" "$config"
    mmw_init_touch ".mmw.json"
    mmw_init_say "配置     : 已为 ${config} 补入 paths.research、paths.evidence 与 paths.scratch，并删除旧 research 路径字段"
  else
    cp "$default_config" "$config"
    mmw_init_touch ".mmw.json"
    mmw_init_say "配置     : 已生成 $config"
  fi
}

# 转发脚本先看当前 git 树里有没有 CLI——mmw 是自己开发自己的，任务 worktree
# 里改了 CLI 要能自测；没有再回退主仓库那份。
mmw_init_forward() {
  local bin="$HOME/.local/bin/mmw"
  if [ -x "$bin" ]; then
    mmw_init_say "转发脚本 : 已有 $bin"
    return 0
  fi
  mkdir -p "$(dirname "$bin")"
  cat > "$bin" <<'FORWARD'
#!/usr/bin/env bash
set -euo pipefail
root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -n "$root" ] && [ -x "$root/mmw/cli/mmw" ]; then
  exec "$root/mmw/cli/mmw" "$@"
fi
exec "$HOME/multi-model-workflow/mmw/cli/mmw" "$@"
FORWARD
  chmod +x "$bin"
  mmw_init_say "转发脚本 : 已装 $bin"
}

# Codex 的本机运行面一次装齐：原生 agent、指向已安装 plugin 的 mmw 命令，
# 并清掉旧 Claude bridge 的三个技能链接。
mmw_init_codex_runtime() {
  local out
  if out="$(python3 "$MMW_ROOT/codex/runtime.py" install 2>&1)"; then
    mmw_init_say "Codex运行时: 已装四个原生 subagent 与 mmw 转发脚本；旧 Claude bridge 已检查"
    return 0
  fi
  mmw_init_say "Codex运行时: 装不上，原样报出——$(printf '%s' "$out" | tail -5 | tr '\n' ' ')"
  return 1
}

# TESTING.md 铺的是骨架，不是填好的事实。通用测试方法随插件走，
# 这一份留空位给本仓库的目录分层、外部 seam、权威源和跑法。
mmw_init_testing() {
  local root target
  root="$(mmw_repo_root)"
  target="$root/TESTING.md"
  if [ -f "$target" ]; then
    mmw_init_say "TESTING  : 已有 ${target}，不覆盖"
  else
    cp "$MMW_ROOT/cli/seeds/TESTING.md" "$target"
    mmw_init_touch "TESTING.md"
    mmw_init_say "TESTING  : 已铺骨架 ${target}，空位要人或后续技能填"
  fi
}

# 同步器已经完成整轮 marker 与 Git 状态预检。init 只消费稳定的四列结果，
# 并把确实变化的仓库路径交给现有按路径提交机制。
mmw_init_domain_context() {
  local out line prefix kind rel state
  local agents_state="" map_state="" claude_state=""
  if ! out="$(mmw_domain_sync 2>&1)"; then
    mmw_init_say "领域规则 : 同步失败"
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      mmw_init_say "             $line"
    done <<< "$out"
    return 1
  fi

  while IFS=$'\t' read -r prefix kind rel state; do
    if [ "$prefix" != "sync" ] || [ -z "$rel" ] || [ -z "$state" ]; then
      mmw_init_say "领域规则 : 同步器返回了无法识别的结果：$prefix $kind $rel $state"
      return 1
    fi
    case "$kind" in
      agents) agents_state="$state" ;;
      map) map_state="$state" ;;
      claude) claude_state="$state" ;;
      *)
        mmw_init_say "领域规则 : 同步器返回了无法识别的目标：$kind"
        return 1
        ;;
    esac
    case "$state" in
      created|inserted|updated|appended) mmw_init_touch "$rel" ;;
      current|not-present|not-required) ;;
      *)
        mmw_init_say "领域规则 : 同步器返回了无法识别的状态：$state"
        return 1
        ;;
    esac
  done <<< "$out"

  if [ -z "$agents_state" ] || [ -z "$map_state" ] || [ -z "$claude_state" ]; then
    mmw_init_say "领域规则 : 同步结果缺少 agents、map 或 claude"
    return 1
  fi
  mmw_init_say "领域规则 : agents=${agents_state} map=${map_state} claude=${claude_state}"
}

# 标签清单的唯一事实来源是 .mmw.json 的 tracker.labels。这里只建缺的。
mmw_init_labels() {
  if ! command -v gh > /dev/null; then
    mmw_init_say "标签     : 跳过，gh 没装"
    return 0
  fi
  if ! gh auth status > /dev/null 2>&1; then
    mmw_init_say "标签     : 跳过，gh 没登录"
    return 0
  fi

  local have want desc created=0 existed=0
  have="$(gh label list --limit 200 --json name --jq '.[].name' 2>/dev/null || true)"
  while IFS= read -r want; do
    [ -n "$want" ] || continue
    if printf '%s\n' "$have" | grep -qxF "$want"; then
      existed=$((existed + 1))
      continue
    fi
    desc="$(mmw_config ".tracker.labels[\"$want\"]")"
    if gh label create "$want" --description "$desc" > /dev/null 2>&1; then
      created=$((created + 1))
    else
      mmw_init_say "标签     : 建不出 ${want}，自己去 tracker 上看是什么挡着"
    fi
  done <<< "$(mmw_config '.tracker.labels | keys[]')"

  mmw_init_say "标签     : 新建 ${created} 个，已有 ${existed} 个"
}

# scratch 只随任务存活，不进 Git。graphify-out 是结构图谱：本机派生物，
# 几十兆，每次改代码都变。漏掉它，第一次建完图那几十兆就跟着下一次提交进了版本库。
mmw_init_gitignore() {
  local root file added=0 line host
  root="$(mmw_repo_root)"
  file="$root/.gitignore"
  host="$(mmw_host)" || return 1
  touch "$file"
  local -a lines=("$(mmw_path_field reviews)/" "$(mmw_path_field release)/" "$(mmw_path_field scratch)/" "graphify-out/")
  if [ "$host" != "codex" ]; then
    lines+=("$(mmw_path_field worktrees)/" ".dispatch/")
  fi
  for line in "${lines[@]}"; do
    if grep -qxF "$line" "$file"; then
      continue
    fi
    printf '%s\n' "$line" >> "$file"
    added=$((added + 1))
  done
  if [ "$added" -eq 0 ]; then
    mmw_init_say "gitignore: 所需条目都在"
    return 0
  fi
  mmw_init_say "gitignore: 补了 ${added} 行"
  mmw_init_touch ".gitignore"
}

# 三个检索工具。Codex 与 Claude Code 都由各自 plugin 直接提供；Pi/Cursor 才写用户配置。
mmw_init_mcp() {
  local host
  host="$(mmw_host)" || return 1
  if [ "$host" = "codex" ]; then
    mmw_init_say "检索工具 : Codex plugin 直接提供，不写用户配置"
    return 0
  fi
  local script="$MMW_ROOT/mcp/install-mcp.sh"
  if [ ! -x "$script" ]; then
    mmw_init_say "检索工具 : 找不到安装脚本 $script"
    return 1
  fi
  local out
  if out="$(bash "$script" 2>&1)"; then
    mmw_init_say "检索工具 : $(printf '%s' "$out" | tail -1)"
  else
    mmw_init_say "检索工具 : 装不上，原样报出——$(printf '%s' "$out" | tail -3 | tr '\n' ' ')"
    return 1
  fi
}

# 旧方法论链接只服务 Claude Code 启动的外部 Codex 进程。Codex plugin 不装这些链接。
mmw_init_skills() {
  local host
  host="$(mmw_host)" || return 1
  if [ "$host" = "codex" ]; then
    mmw_init_say "方法论   : Codex plugin 直接提供，不装旧 Claude bridge"
    return 0
  fi
  local script="$MMW_ROOT/cli/lib/install-agent-skills.sh"
  if [ ! -x "$script" ]; then
    mmw_init_say "方法论   : 找不到安装脚本 $script"
    return 1
  fi
  local out
  if out="$(bash "$script" 2>&1)"; then
    mmw_init_say "方法论   : $(printf '%s' "$out" | tail -1)"
  else
    mmw_init_say "方法论   : 装不上，原样报出——$(printf '%s' "$out" | tail -3 | tr '\n' ' ')"
    return 1
  fi
}

# init 写的配置文件要提交进分支才算数。任务 worktree 检出的是分支上的版本：
# .gitignore 那几行留在工作区没提交的话，worktree 里那份 .gitignore 里没有它
# 们，于是 .reviews/ 与 .dispatch/ 变成未跟踪文件，旧宿主的 mmw task cleanup 被它们挡
# 住，git 报的却是「contains modified or untracked files」，看不出真因是配置
# 没提交。.mmw.json 同理，它不在分支上时 worktree 里每条 mmw 命令都报没配置。
#
# 只提交本轮自己动过的那几个路径。带路径的提交形式不碰暂存区，用户已经
# git add 的东西留在原地。
mmw_init_commit() {
  local root rel paths_display=""
  local -a paths=()
  root="$(mmw_repo_root)"

  if [ "${#MMW_INIT_TOUCHED[@]}" -eq 0 ]; then
    mmw_init_say "提交     : 这一轮没有要提交的配置改动"
    return 0
  fi

  for rel in "${MMW_INIT_TOUCHED[@]}"; do
    git -C "$root" add -- "$rel" || {
      mmw_init_say "提交     : git add 失败，${rel} 没提交，自己看是什么挡着"
      return 1
    }
    paths+=("$rel")
    paths_display="${paths_display} ${rel}"
  done

  if git -C "$root" commit -q -m "chore(mmw): 配置多模型工作流" -- "${paths[@]}"; then
    mmw_init_say "提交     : 已提交${paths_display}"
  else
    mmw_init_say "提交     : 提交失败，${paths_display} 还在工作区。原样报出来，自己看是 git 身份没配还是 hook 拦了"
    return 1
  fi
}

# 上一轮铺进去的 docs/agents/ 副本。技能不再读它，留着会被人当成有效配置。
# 只报不删——删文件要用户点头。
mmw_init_legacy() {
  local root dir
  root="$(mmw_repo_root)"
  dir="$root/docs/agents"
  if [ -d "$dir" ]; then
    mmw_init_say "旧副本   : $dir 还在。技能已经不读它了，留着会被当成有效配置——要不要删由你定"
  fi
}

mmw_init() {
  local status=0 host
  host="$(mmw_host)" || return 1
  mmw_init_config
  mmw_init_domain_context || status=1
  if [ "$host" = "codex" ]; then
    mmw_init_codex_runtime || status=1
  else
    mmw_init_forward
  fi
  mmw_init_testing
  mmw_init_labels
  mmw_init_gitignore
  if [ "$host" != "codex" ]; then
    if python3 "$MMW_ROOT/cli/lib/materialize_skills.py" --host all; then
      :
    else
      status=1
    fi
  fi
  mmw_init_skills || status=1
  mmw_init_mcp || status=1
  # 提交排在最后：上面各步骤都登记完了，一个提交装下这一轮的全部配置改动。
  mmw_init_commit || status=1
  mmw_init_legacy

  printf '%s' "$MMW_INIT_LOG"

  if [ "$status" -ne 0 ]; then
    cat >&2 <<'NOTE'

上面有步骤没做完，看那几行说的是什么。
NOTE
  fi

  case "$host" in
    claude-code)
      cat <<'NOTE'

还有一件要改宿主的全局配置，不替你动，确认后自己加：
  ~/.claude/settings.json 的 permissions.allow 加 "Bash(mmw:*)"
NOTE
      ;;
    codex)
      cat <<'NOTE'

Codex 运行时由已安装的 MMW plugin 和四个原生 subagent 组成。
四个 subagent、指向已安装 plugin 的 mmw 命令与旧 Claude bridge 清理已经完成。
NOTE
      ;;
  esac
  return "$status"
}
