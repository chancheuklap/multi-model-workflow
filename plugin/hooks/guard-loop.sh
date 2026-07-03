#!/usr/bin/env bash
# SubagentStop 看守:落地/审 loop 没做完不让帮手停下。
# 读 loop-state → exit-check;NOT-DONE → exit 2 顶回去续;DONE/PAUSED → 放停。
# 只在有 loop-state 时生效(普通 subagent 无 state 直接放行)。
# 空转熔断:连续 6 次顶回且账本零进展(done/covered/findings/decisions 计数没变)= 帮手在打转,
# 机器写 pause 交人并放停(留痕,不无限顶回);有进展则计数归 1 继续看守。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/../scripts/loop.sh"

cat >/dev/null 2>&1 || true   # 吞掉 stdin payload(本 hook 不需要它的字段)

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
f="$top/.claude/multi-model-workflow/loop-state.json"
[ -f "$f" ] || exit 0

# exit-check 自身执行失败 = 不放停(fail-closed),别静默放行
res="$(cd "$top" && bash "$LOOP" exit-check 2>/dev/null)" \
  || { echo "看守:exit-check 执行失败,不放停,请人查 loop-state。" >&2; exit 2; }
case "$res" in
  DONE|PAUSED:*) exit 0 ;;                                  # 放它停
  NOT-DONE:*)
    # 进展签名:账本四个计数;与上次顶回时相同 = 零进展
    sig="$(jq -r '[([.steps[]|select(.status=="done")]|length),([.checklist[]|select(.status=="covered")]|length),(.findings|length),(.decisions|length)]|join("/")' "$f" 2>/dev/null || echo "?")"
    prev_sig="$(jq -r '.guard_sig // ""' "$f" 2>/dev/null || echo "")"
    blocks="$(jq -r '.guard_blocks // 0' "$f" 2>/dev/null || echo 0)"
    if [ "$sig" = "$prev_sig" ]; then blocks=$((blocks+1)); else blocks=1; fi
    if [ "$blocks" -ge 6 ]; then
      tmp="$(mktemp)"
      if jq --arg s "$sig" --argjson b "$blocks" \
           --arg q "看守连续顶回 $blocks 次且账本零进展,疑似空转,熔断交人" \
           '.guard_sig=$s | .guard_blocks=$b | .pause={at_step:"", kind:"surface", reason:"needs-context", question:$q}' \
           "$f" > "$tmp" 2>/dev/null && [ -s "$tmp" ]; then mv "$tmp" "$f"; else rm -f "$tmp"; fi
      echo "看守熔断:连续 $blocks 次零进展顶回,已写 pause 交人处置。" >&2
      exit 0
    fi
    tmp="$(mktemp)"
    if jq --arg s "$sig" --argjson b "$blocks" '.guard_sig=$s | .guard_blocks=$b' "$f" > "$tmp" 2>/dev/null && [ -s "$tmp" ]; then
      mv "$tmp" "$f"
    else rm -f "$tmp"; fi
    hint=""
    [ "$(jq -r '.kind // ""' "$f" 2>/dev/null)" = "review" ] && hint="审 loop 整轮跑完记得 loop round next 记轮(轮账熔断靠它)。"
    echo "内层未完成($res),做完再停。$hint" >&2; exit 2 ;;   # 顶回去续
  CORRUPT:*)  echo "看守:loop-state 损坏($res),不放停,请人查。" >&2; exit 2 ;;  # fail-closed
  *) echo "看守:exit-check 输出异常($res),不放停。" >&2; exit 2 ;;          # 默认 fail-closed
esac
