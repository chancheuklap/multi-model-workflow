#!/usr/bin/env bash
# redline-check.sh — advisory 红线探测器（NOT a hook）。
#
# Entry Gate 的辅助工具：Coordinator 把一段文本（改动路径 / diff 文本 / 关键词，
# 可走 args 或 stdin）喂给它，判断是否触碰北极星核心红线（计费 / 权限 / 数据权威 /
# 用户可见合同）。命中 = 该改动应升 formal（doc03 §3.1 D1 判定线）。
#
# 这是 advisory：它只给信号，不做强制拦截（doc03 §3.1 明令不做 fire-on-every-Bash
# 强 hook，避免误报卡住正常 light 改动）。SKILL.md Entry Gate 散文指示 Coordinator
# 调用它辅助判定；机器侧硬兜底由"升级门存在 + 北极星不变量"承担。
#
# 退出码语义：
#   exit 0 — 命中至少一个红线类别（打印命中类别名，每行一个）
#   exit 1 — 未命中任何红线（纯文案 / 普通改动）
#
# 用法：
#   redline-check.sh "src/billing/charge.py docs/copy.md"
#   echo "<diff 或路径文本>" | redline-check.sh
set -euo pipefail

# 收集输入：优先 args，否则读 stdin。
INPUT=""
if [[ $# -gt 0 ]]; then
  INPUT="$*"
else
  INPUT="$(cat)"
fi

# 红线类别 → 关键词集（大小写不敏感，词内子串匹配）。
# doc03 §3.1 核心红线判定表的 machine-checkable 近似。
# 用并行函数而非 `declare -A`，兼容 bash 3.2（macOS 系统 bash 无关联数组）。
redline_pattern() {
  case "$1" in
    billing)        echo 'billing|pricing|charge|quota|idempotency|metering|subscription' ;;
    auth)           echo 'auth|permission|role|acl|rbac|token|session|credential' ;;
    data-authority) echo 'schema|migration|LINEAGE' ;;
    user-contract)  echo 'public.?api|endpoint|pricing' ;;
  esac
}

hit=0
# 稳定输出顺序：计费 → 权限 → 数据权威 → 用户可见合同。
for category in billing auth data-authority user-contract; do
  pattern="$(redline_pattern "$category")"
  if echo "$INPUT" | grep -qiE "$pattern"; then
    echo "$category"
    hit=1
  fi
done

if [[ "$hit" -eq 1 ]]; then
  exit 0
fi
exit 1
