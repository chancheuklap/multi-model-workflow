#!/usr/bin/env bash
# mmw init：把一个仓库配置成能跑这套工作流的样子。
#
# 幂等。每一步已经做过就跳过并报一行，重跑无害。不覆盖任何已存在的文件，也不
# 删任何东西——要删的由人决定。
#
# 这条命令问不了问题。全流程只有一处要人拿主意：仓库既没有 CLAUDE.md 也没有
# AGENTS.md 时，指针节往哪一份写。那时非零退出说清缺什么，由主 agent 去问，
# CLI 不替用户挑一个。

set -euo pipefail

# 每一步往这里追加一行，最后统一报。
MMW_INIT_LOG=""
mmw_init_say() {
  MMW_INIT_LOG="${MMW_INIT_LOG}$1
"
}

mmw_init_config() {
  local root config
  root="$(mmw_repo_root)"
  config="$root/.mmw.json"
  if [ -f "$config" ]; then
    mmw_init_say "配置     : 已有 ${config}，不覆盖"
  else
    cp "$MMW_ROOT/cli/mmw.default.json" "$config"
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

# TESTING.md 铺的是骨架，不是填好的事实。测试怎么写、够不够格进仓库随插件走，
# 这一份只留空位给本仓库的目录分层、外部 seam、权威源和跑法。
mmw_init_testing() {
  local root target
  root="$(mmw_repo_root)"
  target="$root/TESTING.md"
  if [ -f "$target" ]; then
    mmw_init_say "TESTING  : 已有 ${target}，不覆盖"
  else
    cp "$MMW_ROOT/cli/seeds/TESTING.md" "$target"
    mmw_init_say "TESTING  : 已铺骨架 ${target}，空位要人或后续技能填"
  fi
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

# 三个目录都是随 worktree 死的过程材料，不进 git。
mmw_init_gitignore() {
  local root file added=0 line
  root="$(mmw_repo_root)"
  file="$root/.gitignore"
  touch "$file"
  for line in "$(mmw_path_field worktrees)/" "$(mmw_path_field reviews)/" "$(mmw_path_field release)/" ".dispatch/"; do
    if grep -qxF "$line" "$file"; then
      continue
    fi
    printf '%s\n' "$line" >> "$file"
    added=$((added + 1))
  done
  if [ "$added" -eq 0 ]; then
    mmw_init_say "gitignore: 三行都在"
  else
    mmw_init_say "gitignore: 补了 ${added} 行"
  fi
}

# 三个检索工具。Claude Code 读插件自带的 .mcp.json、Codex 派发时注入，两边都不用装；
# 只有 pi 要写用户级配置，脚本自己判断这台机器有没有 pi。同样是每台机器一次。
mmw_init_mcp() {
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

# 装方法论是每台机器一次，不是每个仓库一次。脚本自己幂等。
mmw_init_skills() {
  local script="$MMW_ROOT/skills/mmw-dispatching-agents/install-agent-skills.sh"
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

MMW_INIT_POINTER_HEADING="## 多模型工作流"

mmw_init_pointer_body() {
  cat <<'BODY'
## 多模型工作流

本仓库装了多模型开发编排插件。约定住在三个地方，技能不硬编码它们的值：

- **机械动作**：`mmw` 这个 CLI。不带参数跑一次列出全部命令；**要哪条命令的参数，就跑那条命令本身不带参数**，只拿到那一条的。例外是 `mmw doctor` 与 `mmw init`，它们本来就不收参数，跑一次就是执行。技能正文不复述这些，不确定就跑一次，不要凭记忆拼。
- **参数**：仓库根 `.mmw.json` 存着模型档、标签清单、路径、领域文档落点。技能会用到的两样跑 `mmw` 查：领域文档落在哪跑 `mmw domain path` 与 `mmw domain dirs`，有哪些角色、各配什么模型跑 `mmw dispatch`。标签名一律由点名它的那个技能给出，模型档由角色决定，这两样不用你挑，也不要手抄 `.mmw.json` 里的值。
- **本仓库的测试事实**：根目录的 `TESTING.md`。测试怎么写、够不够格进仓库随插件走，那一份只补本仓库的目录分层、外部 seam、权威源和跑法。

**AFK 不附带把东西发出仓库的授权。** `git push`、推 Wiki、往外部服务写数据这三类动作把东西送到别人看得见、也收不回的地方。要发的内容用户还没看过就停下来，把内容原样给他看，他点头再发。issue tracker 不在这三类里——它是这套流程自己的工作面，建 ticket、贴评论、打标签、关 issue 都照各技能自己的步骤做。
BODY
}

mmw_init_pointer() {
  local root target
  root="$(mmw_repo_root)"
  if [ -f "$root/CLAUDE.md" ]; then
    target="$root/CLAUDE.md"
  elif [ -f "$root/AGENTS.md" ]; then
    target="$root/AGENTS.md"
  else
    mmw_init_say "指针节   : 这个仓库既没有 CLAUDE.md 也没有 AGENTS.md，指针节没处写"
    return 1
  fi

  if grep -qF "$MMW_INIT_POINTER_HEADING" "$target"; then
    # 只认标题在不在，不比内容——那一节用户可能已经改过，覆盖会把他的改动
    # 冲掉。代价是插件升级后老仓库拿不到新文案，所以这里说出来。
    mmw_init_say "指针节   : $target 里已经有，原样留着。插件升级过的话，新文案要自己对照更新"
    return 0
  fi

  printf '\n' >> "$target"
  mmw_init_pointer_body >> "$target"
  mmw_init_say "指针节   : 已追加到 $target"
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
  local status=0
  mmw_init_config
  mmw_init_forward
  mmw_init_testing
  mmw_init_labels
  mmw_init_gitignore
  mmw_init_skills || status=1
  mmw_init_mcp || status=1
  mmw_init_pointer || status=1
  mmw_init_legacy

  printf '%s' "$MMW_INIT_LOG"

  if [ "$status" -ne 0 ]; then
    cat >&2 <<'NOTE'

上面有步骤没做完，看那几行说的是什么。指针节没处写时不要替用户挑一份建，
问他要 CLAUDE.md 还是 AGENTS.md。
NOTE
  fi

  cat <<'NOTE'

还有一件要改宿主的全局配置，不替你动，确认后自己加：
  Claude Code  ~/.claude/settings.json 的 permissions.allow 加 "Bash(mmw:*)"
  pi           无沙箱，不用加
NOTE
  return "$status"
}
