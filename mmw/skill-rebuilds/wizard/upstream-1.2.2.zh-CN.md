# `wizard` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/SKILL.md:1-4 -->

```yaml
---
name: wizard
description: 生成一个交互式 Bash wizard，逐步引导人类完成只有他们才能执行的操作。配置基础设施、设置凭证或 CI secret、操作不熟悉的第三方 dashboard，或者运行一次性 migration 或 cutover 时使用。不要为 agent 自己能够执行的步骤调用本技能。
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/SKILL.md:6-14 -->

# Wizard

**Wizard** 是一份 Bash 脚本，逐步引导人类完成手动流程；该流程由人手动完成很繁琐，每次向 AI 重新解释也很繁琐。它会打开每个 URL，准确说明点击和复制什么，捕获各项值，把值写入对应位置，例如 `.env` 和 GitHub secret，在每个阶段进行确认，并显示剩余进度。它可以配置第三方 service、运行一次性 migration，或把项目从一种状态迁移到另一种状态。

[template.sh](template.sh) 已经解决令人愉悦的 UX：显示进度和剩余时间、设置确认关卡、跨平台打开 URL，包括 WSL、隐藏 secret 输入、幂等 upsert `.env`、写入 `gh secret` 或 `gh variable`，以及结束总结。**你的职责只有限定流程并编写各个阶段。** `STAGES` 标记上方的 library 在每份 wizard 中完全相同；一致性就是目的，绝不要手工编辑。

Wizard 默认是临时产物：为一次运行而构建，保存在 scratch 或 `scripts/` 路径中，并在工作完成时删除。只有用户想要一条应该长期保存在仓库中的可重复设置路径时，才提交它。

## 流程

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/SKILL.md:16-25 -->

### 1. 限定流程

找出人类必须执行的每一个手动步骤，以及过程中捕获的每一项值。先读取仓库，不要在毫无上下文时提问：

- 对于设置流程：读取 `.env`、`.env.example`、`.env.*`、`README`、`docker-compose*`、框架配置和 `.github/workflows/*`。每个 `secrets.*` 或 `vars.*` 引用都是 wizard 必须产生的一项值。
- 对于 migration 或 transition：读取当前状态、目标状态，以及二者之间的不可逆动作。

随后向用户展示有序的阶段清单和每个阶段产生的值，并请求确认；用户可能会增加、删除或重新排序。

**完成判据：** 每个阶段都按照顺序命名；对于每项捕获值，你都知道：(a) 人类从哪里取得它；(b) 它写入哪里，包括 `.env`、GitHub secret、两者或不写入任何位置，因为某些阶段只有动作；(c) 它是 secret，需要隐藏输入，还是公开值。

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/SKILL.md:27-31 -->

### 2. 描绘每个阶段的操作路径

为每个阶段写出人类遵循的准确路径：打开哪个 URL、在那里做什么、值显示在哪里、填入哪个变量。例如：“Dashboard → Developers → API keys → Reveal test key → copy”。如果你实际上不知道当前 UI 或准确命令，就明确说明，并询问用户或查阅文档；绝不要编造可能不存在的步骤。

**完成判据：** 每个阶段都能够追溯到陌生人也能遵循的具体指令。

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/SKILL.md:33-37 -->

### 3. 编写 wizard

把 `template.sh` 复制到目标路径。按照依赖顺序，用每个步骤一个 `stage` 替换示例阶段。使用 library helper：`stage`、`say` 或 `step`、`open_url`、`ask` 或 `ask_secret`、`write_env`、`set_secret` 或 `set_var`、`pause` 或 `confirm`。把 `TOTAL_STAGES` 和 `TOTAL_MINUTES` 设置为诚实估计；这两个值驱动剩余时间显示。

达到模板设定的标准：索取值前先打开 URL；所有 secret 都使用 `ask_secret`；所有持久化值都使用 `write_env`；只有 CI 实际需要的值才使用 `set_secret`；任何不可逆动作前都使用 `confirm`。每个 `stage` 会清空屏幕，使画面上只显示当前步骤；一个阶段只完成一项聚焦任务，避免人类需要的信息滚出画面。不要改动标记上方的 library。

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/SKILL.md:39-44 -->

### 4. 验证并交给用户

- 运行 `bash -n <script>`；如果可以使用 ShellCheck，就运行 ShellCheck。
- 运行 `chmod +x <script>`。
- 不要自己端到端运行；脚本会打开浏览器并阻塞等待人工输入。改为静态追踪：第 1 步中的每个值都被捕获，并写入第 1 步所说的位置；每个 `set_secret` 名称都与 CI 中的一项 `secrets.*` 引用准确匹配。
- 告诉用户如何运行。如果它是一条可重复的设置路径，就提交脚本，并从 README 链接它，使下一位用户直接运行脚本，不必询问 AI。

## `template.sh`

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/template.sh:1-211 -->

```bash
#!/usr/bin/env bash
#
# Wizard——逐步引导人类完成手动流程。
# 由 /wizard 技能生成。
#
# "STAGES" 标记上方的所有内容都是 wizard library；不要手工编辑。
# 在标记下方编写各个步骤的阶段。

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────
# Wizard library——令人愉悦且一致的 UX。每份 wizard 都完全相同。
# ──────────────────────────────────────────────────────────────────────────

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  BOLD=$(tput bold); DIM=$(tput dim); RESET=$(tput sgr0)
  BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1)
else
  BOLD=""; DIM=""; RESET=""; BLUE=""; GREEN=""; YELLOW=""; RED=""
fi

# 编写者在阶段章节顶部设置这两个值。
TOTAL_STAGES=0
TOTAL_MINUTES=0

_STAGE_INDEX=0
_MINUTES_ELAPSED=0
ENV_FILE="${ENV_FILE:-.env}"
WRITTEN_ENV=()    # 本次运行写入 ENV_FILE 的 KEY
WRITTEN_SECRET=() # 本次运行设置的 secret NAME
SKIPPED=()        # 无法完成的内容，例如缺少 gh

# _clear——清空 terminal，使屏幕上只有当前步骤。输出不是 terminal 时不执行，
# 使管道日志保持可读。
_clear() {
  [[ -t 1 ]] || return 0
  if command -v tput >/dev/null 2>&1; then tput clear; else printf '\033[2J\033[3J\033[H'; fi
}

# banner "Title"——开场画面：本 wizard 的作用和所需时间。
banner() {
  _clear
  printf '\n%s%s  %s%s\n' "$BOLD" "$BLUE" "$1" "$RESET"
  printf '%s  %s 个阶段 · 约 %s 分钟%s\n\n' \
    "$DIM" "$TOTAL_STAGES" "$TOTAL_MINUTES" "$RESET"
  printf '%s  你操作浏览器；本 wizard 会准确告诉你做什么，并\n' "$DIM"
  printf '  捕获你复制回来的值。随时可以按 Ctrl-C 停止，稍后重新运行；\n'
  printf '  它会记住已经保存的值。%s\n' "$RESET"
  pause "准备开始吗？"
}

# stage "Name" <minutes>——清空屏幕，然后宣布一个阶段，并显示
# 进度和剩余时间。清屏使画面上只有当前步骤。
stage() {
  _clear
  _STAGE_INDEX=$((_STAGE_INDEX + 1))
  local remaining=$((TOTAL_MINUTES - _MINUTES_ELAPSED))
  (( remaining < 0 )) && remaining=0
  _MINUTES_ELAPSED=$((_MINUTES_ELAPSED + ${2:-0}))
  printf '\n%s%s▸ 阶段 %s/%s · %s%s  %s(剩余约 %s 分钟)%s\n' \
    "$BOLD" "$BLUE" "$_STAGE_INDEX" "$TOTAL_STAGES" "$1" "$RESET" "$DIM" "$remaining" "$RESET"
}

# say "..."——一行普通指令。
say()  { printf '  %s\n' "$1"; }
# step "..."——人类在浏览器中执行的一项带编号感的动作。
step() { printf '  %s•%s %s\n' "$BLUE" "$RESET" "$1"; }
note() { printf '  %s%s%s\n' "$DIM" "$1" "$RESET"; }
warn() { printf '  %s⚠ %s%s\n' "$YELLOW" "$1" "$RESET"; }

# open_url URL——跨平台在人的浏览器中打开，包括 WSL。
open_url() {
  local url="$1"
  printf '  %s↗ 正在打开%s %s\n' "$GREEN" "$RESET" "$url"
  { if   command -v wslview     >/dev/null 2>&1; then wslview "$url"
    elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url"
    elif command -v xdg-open    >/dev/null 2>&1; then xdg-open "$url"
    elif command -v open        >/dev/null 2>&1; then open "$url"
    else warn "无法打开浏览器；请手动访问：$url"; fi
  } >/dev/null 2>&1 || warn "无法打开浏览器；请手动访问：$url"
}

# pause "msg"——等待人类确认已完成手动部分。
pause() {
  printf '  %s%s%s ' "$DIM" "${1:-按 Enter 继续}" "$RESET"
  read -r _ || true
}

# confirm "question"——y/N 关卡；回答 yes 时返回成功。
confirm() {
  local reply=""
  printf '  %s? %s [y/N] ' "$YELLOW" "$1"
  read -r reply || true
  [[ "$reply" =~ ^[Yy] ]]
}

# _existing KEY——ENV_FILE 中 KEY 的当前值，如果存在。
_existing() {
  [[ -f "$ENV_FILE" ]] || return 1
  local line; line=$(grep -E "^${1}=" "$ENV_FILE" | tail -n1) || return 1
  printf '%s' "${line#*=}"
}

# ask KEY "Prompt"——把一个值读入 $KEY。重新运行时，把现有 .env 值
# 作为默认值；按 Enter 保留。输入可见，不是 secret。
ask() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[按 Enter 保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -r input || true
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

# ask_secret KEY "Prompt"——与 ask 相同，但隐藏输入。
ask_secret() {
  local key="$1" prompt="$2" current input
  current=$(_existing "$key" || true)
  if [[ -n "$current" ]]; then
    printf '  %s%s%s %s[按 Enter 保留当前值]%s ' "$BOLD" "$prompt" "$RESET" "$DIM" "$RESET"
  else
    printf '  %s%s%s ' "$BOLD" "$prompt" "$RESET"
  fi
  read -rs input || true
  printf '\n'
  [[ -z "$input" && -n "$current" ]] && input="$current"
  printf -v "$key" '%s' "$input"
}

# write_env KEY VALUE——在 ENV_FILE 中 upsert KEY=VALUE；创建文件并替换
# 任何现有行。操作幂等。
write_env() {
  local key="$1" value="$2" tmp
  touch "$ENV_FILE"
  tmp=$(mktemp)
  grep -vE "^${key}=" "$ENV_FILE" > "$tmp" || true
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  mv "$tmp" "$ENV_FILE"
  WRITTEN_ENV+=("$key")
  printf '  %s✓ 已写入%s %s → %s\n' "$GREEN" "$RESET" "$key" "$ENV_FILE"
}

# set_secret NAME VALUE——通过 gh 设置 GitHub Actions 仓库 secret。gh 不可用
# 或未认证时降级为 warning，并记录该项。
set_secret() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if printf '%s' "$value" | gh secret set "$name" >/dev/null 2>&1; then
      WRITTEN_SECRET+=("$name")
      printf '  %s✓ 已设置%s GitHub secret %s\n' "$GREEN" "$RESET" "$name"
      return
    fi
  fi
  SKIPPED+=("GitHub secret $name（手动设置：gh secret set $name）")
  warn "已跳过 GitHub secret $name；gh 尚未准备好，请稍后设置"
}

# set_var NAME VALUE——设置 GitHub Actions 仓库 variable，不是 secret。
set_var() {
  local name="$1" value="$2"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    if gh variable set "$name" --body "$value" >/dev/null 2>&1; then
      printf '  %s✓ 已设置%s GitHub variable %s\n' "$GREEN" "$RESET" "$name"
      return
    fi
  fi
  SKIPPED+=("GitHub variable $name")
  warn "已跳过 GitHub variable $name；gh 尚未准备好，请稍后设置"
}

# finish——清空屏幕，然后总结已经完成的全部配置。
finish() {
  _clear
  printf '\n%s%s  ✓ 设置完成%s\n' "$BOLD" "$GREEN" "$RESET"
  (( ${#WRITTEN_ENV[@]} ))    && note "已把 ${#WRITTEN_ENV[@]} 个值写入 $ENV_FILE：${WRITTEN_ENV[*]}"
  (( ${#WRITTEN_SECRET[@]} )) && note "已设置 ${#WRITTEN_SECRET[@]} 个 GitHub secret：${WRITTEN_SECRET[*]}"
  if (( ${#SKIPPED[@]} )); then
    printf '\n'; warn "仍需手动完成："
    for s in "${SKIPPED[@]}"; do note "  - $s"; done
  fi
  printf '\n'
}

# ──────────────────────────────────────────────────────────────────────────
# STAGES——编写本章节。人类执行的每个步骤对应一个 stage()。
# 替换下方示例。把两个总数设置为与你编写的阶段一致。
# ──────────────────────────────────────────────────────────────────────────

TOTAL_STAGES=1
TOTAL_MINUTES=5

banner "Stripe 设置"

# ── 示例阶段：替换为真实步骤 ────────────────────────────────────────────
stage "Stripe — API keys" 5
say "我们将取得 Stripe 测试 key，并存储给本地开发和 CI 使用。"
open_url "https://dashboard.stripe.com/test/apikeys"
step "在 API key 页面复制 Publishable key，以 pk_test_ 开头。"
ask STRIPE_PUBLISHABLE_KEY "粘贴 publishable key："
step "点击 Secret key 行中的 'Reveal test key'，然后复制。"
ask_secret STRIPE_SECRET_KEY "粘贴 secret key："
write_env STRIPE_PUBLISHABLE_KEY "$STRIPE_PUBLISHABLE_KEY"
write_env STRIPE_SECRET_KEY "$STRIPE_SECRET_KEY"
set_secret STRIPE_SECRET_KEY "$STRIPE_SECRET_KEY"   # CI 需要这一项
# ──────────────────────────────────────────────────────────────────────────

finish
```

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/wizard/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Wizard"
  short_description: "生成交互式设置 wizard"
```
