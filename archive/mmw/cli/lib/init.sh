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

# 目标仓库配置不保存模型档。模型档由源码安装流程写进各宿主 runtime。
# paths 只保留 CLI 消费的四个键（worktrees、reviews、release、scratch）。
mmw_init_config() {
  local root config default_config default_scratch default_reviews default_release default_worktrees temp config_mode
  root="$(mmw_repo_root)"
  config="$root/.mmw.json"
  default_config="$MMW_ROOT/cli/mmw.default.json"
  if [ -f "$config" ]; then
    if jq -e '
      (.paths.scratch != null and .paths.reviews != null and .paths.release != null and .paths.worktrees != null)
      and ((.paths // {}) | [has("specs"), has("plans"), has("prototypes"),
                             has("research"), has("evidence"), has("investigations")] | all(. == false))
      and (has("wiki") | not)
      and (.models == null)
    ' "$config" >/dev/null 2>&1; then
      mmw_init_say "配置     : 已有 ${config}，无需迁移"
      return 0
    fi
    default_scratch="$(jq -er '.paths.scratch' "$default_config")" || return 1
    default_reviews="$(jq -er '.paths.reviews' "$default_config")" || return 1
    default_release="$(jq -er '.paths.release' "$default_config")" || return 1
    default_worktrees="$(jq -er '.paths.worktrees' "$default_config")" || return 1
    mmw_path_safe_base "$default_scratch" || return 1
    mmw_path_safe_base "$default_reviews" || return 1
    mmw_path_safe_base "$default_release" || return 1
    mmw_path_safe_base "$default_worktrees" || return 1
    if config_mode="$(stat -f '%Lp' "$config" 2>/dev/null)"; then
      :
    elif config_mode="$(stat -c '%a' "$config" 2>/dev/null)"; then
      :
    else
      return 1
    fi
    temp="$(mktemp "$root/.mmw.json.migrate.XXXXXX")" || return 1
    if ! jq --arg scratch "$default_scratch" --arg reviews "$default_reviews" \
            --arg release "$default_release" --arg worktrees "$default_worktrees" '
      .paths = (.paths // {}) |
      .paths.scratch //= $scratch |
      .paths.reviews //= $reviews |
      .paths.release //= $release |
      .paths.worktrees //= $worktrees |
      del(.paths.specs, .paths.plans, .paths.prototypes,
          .paths.research, .paths.evidence, .paths.investigations, .wiki, .models)
    ' "$config" > "$temp"; then
      rm -f "$temp"
      return 1
    fi
    chmod "$config_mode" "$temp"
    mv -f "$temp" "$config"
    mmw_init_touch ".mmw.json"
    mmw_init_say "配置     : 已删除仓库级模型档，并把 paths 收敛到 CLI 消费的四个键"
  else
    temp="$(mktemp "$root/.mmw.json.create.XXXXXX")" || return 1
    if ! jq 'del(.models)' "$default_config" > "$temp"; then
      rm -f "$temp"
      return 1
    fi
    chmod 0600 "$temp"
    mv -f "$temp" "$config"
    mmw_init_touch ".mmw.json"
    mmw_init_say "配置     : 已生成不含模型档的 $config"
  fi
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
  if ! out="$(mmw_domain_sync all 2>&1)"; then
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
  local root file added=0 line
  root="$(mmw_repo_root)"
  file="$root/.gitignore"
  touch "$file"
  local -a lines=(
    "$(mmw_path_field reviews)/"
    "$(mmw_path_field release)/"
    "$(mmw_path_field scratch)/"
    "$(mmw_path_field worktrees)/"
    "graphify-out/"
  )
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

# 结构图谱的排除清单。graphify 自己读这个文件，gitignore 语法。
#
# Markdown 必须排除，否则「文档不进图」这句话是假的。新鲜度指纹排除 .md
# （mmw/mcp/graphify_ensure.py 的 _EXCLUDE_PATHSPEC），两边不一致的后果是静默的：
# 文档进了图，改文档不会让图过期，图里那份正文永远是旧的，而 mmw graph status
# 照报 FRESH。完整流水线有一道校验挡住 Markdown（mmw/graph/rebuild.py），但它只在
# 配了 retrieval.graph 的仓库里走到；没配的仓库走裸 graphify update，没有任何拦截。
#
# 任务 worktree 是一整份代码副本。不排除的话每个符号在图里有两份，查询预算
# 全花在重复节点上。
mmw_init_graphifyignore() {
  local root file added=0 line
  root="$(mmw_repo_root)"
  file="$root/.graphifyignore"
  touch "$file"
  local -a lines=(
    "*.md"
    "/$(mmw_path_field worktrees)/"
  )
  for line in "${lines[@]}"; do
    if grep -qxF "$line" "$file"; then
      continue
    fi
    printf '%s\n' "$line" >> "$file"
    added=$((added + 1))
  done
  if [ "$added" -eq 0 ]; then
    mmw_init_say "graphify : 排除清单都在"
    return 0
  fi
  mmw_init_say "graphify : .graphifyignore 补了 ${added} 行"
  mmw_init_touch ".graphifyignore"
}

# init 写的配置文件要提交进分支才算数。任务 worktree 检出的是分支上的版本：
# .gitignore 那几行留在工作区没提交的话，worktree 里那份 .gitignore 里没有它
# 们，于是 scratch 根与 reviews 根变成未跟踪文件，旧宿主的 mmw task cleanup 被它们挡
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

# 语言工具链配置：oxlint 规则、各工作区的继承文件、持续集成工作流、宿主的语言服务器
# 开关。哪些语言要配由探测决定，内容由 MMW 的模板决定，所以换一个仓库、换一台电脑，
# 这些配置不用靠人想起来。
#
# 写出来的路径登记进本轮提交清单：配置留在工作区没提交，任务 worktree 里就看不到。
mmw_init_toolchain() {
  local root list rel count=0
  root="$(mmw_repo_root)"
  list="$(mktemp)"

  if ! mmw_toolchain_apply --written-to "$list" > /dev/null 2>&1; then
    rm -f "$list"
    mmw_init_say "工具链   : 探测或产出失败，自己跑一次 mmw toolchain apply 看报什么"
    return 1
  fi

  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_init_touch "$rel"
    count=$((count + 1))
  done < "$list"
  rm -f "$list"

  if [ "$count" -eq 0 ]; then
    mmw_init_say "工具链   : 配置都在"
    return 0
  fi
  mmw_init_say "工具链   : 写了 ${count} 份配置"
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
  mmw_init_domain_context || status=1
  mmw_init_testing
  mmw_init_labels
  mmw_init_gitignore
  mmw_init_graphifyignore
  mmw_init_toolchain || status=1
  # 提交排在最后：上面各步骤都登记完了，一个提交装下这一轮的全部配置改动。
  mmw_init_commit || status=1
  mmw_init_legacy

  printf '%s' "$MMW_INIT_LOG"

  if [ "$status" -ne 0 ]; then
    cat >&2 <<'NOTE'

上面有步骤没做完，看那几行说的是什么。
NOTE
  fi

  return "$status"
}
