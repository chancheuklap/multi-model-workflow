#!/usr/bin/env bash
# 查界面 QA 的四个能力在不在，按 deps.json 说的找法逐个找。
#
# 这个技能不装任何东西。npm 那几个由这台机器的 Node 全局工具目录供给，技能那一个
# 由 skills CLI 装——两个来源各有自己的装法和升级路径，技能再装一份就是第三份，
# 而三份之间的版本分歧只会在跑到一半时才暴露。
#
#   check-deps.sh   齐了回 0 并逐条报出在哪；缺了回 1 并点名缺哪个能力
#
# 输出每个能力一行，缺的那些写明 missing 级别，好让技能正文按它分流。

set -uo pipefail

HERE="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS_JSON="$HERE/deps.json"

case "${1:-}" in
  "") ;;
  *)
    echo "用法：check-deps.sh" >&2
    exit 2
    ;;
esac

die() {
  echo "ui-qa deps: $1" >&2
  exit "${2:-1}"
}

[ -f "$DEPS_JSON" ] || die "找不到能力声明：$DEPS_JSON"
command -v jq >/dev/null 2>&1 || die "要 jq 才能读能力声明"

missing=0
total=0

report_missing() {
  echo "ui-qa deps: 缺 $1（$2）$3" >&2
  missing=1
}

while IFS=$'\t' read -r cap kind cmd pkg file next_to detect installed_by lvl; do
  [ -n "$cap" ] || continue
  total=$((total + 1))
  case "$kind" in
    command)
      if path="$(command -v "$cmd" 2>/dev/null)"; then
        echo "ui-qa deps: $cap -> $path"
      else
        report_missing "$cap" "$lvl" "：PATH 上没有 $cmd，它来自 npm 包 $pkg"
      fi
      ;;
    sibling-file)
      # 没有命令入口，从同目录装着的那个命令反推。
      if anchor="$(command -v "$next_to" 2>/dev/null)"; then
        candidate="$(dirname "$anchor")/../$pkg/$file"
        if [ -f "$candidate" ]; then
          echo "ui-qa deps: $cap -> $candidate"
        else
          report_missing "$cap" "$lvl" "：$next_to 旁边没有 $pkg/$file，两个包要装在同一个目录下"
        fi
      else
        report_missing "$cap" "$lvl" "：找不到 $next_to，无从反推 $pkg/$file 的位置"
      fi
      ;;
    skill)
      if [ -f "$HOME/$detect" ]; then
        echo "ui-qa deps: $cap -> ~/$detect"
      else
        report_missing "$cap" "$lvl" "：装它 $installed_by"
      fi
      ;;
    *)
      die "能力声明里有不认识的 kind：$kind"
      ;;
  esac
# 缺的字段填 "-" 而不是空串：tab 是空白字符，IFS 设成 tab 时 bash 会把连续的
# tab 折叠成一个分隔符，于是空字段整个消失，后面的值全部左移一位。
done < <(jq -r '.capabilities[] | [
  .capability, .kind,
  (.command // "-"), (.package // "-"), (.file // "-"), (.nextTo // "-"),
  (.detect // "-"), (.installedBy // "-"), .missing
] | @tsv' "$DEPS_JSON")

[ "$missing" -eq 0 ] || exit 1
echo "ui-qa deps: ${total} 个能力齐了"
