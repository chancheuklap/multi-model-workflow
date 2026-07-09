---
description: 切回有人值守(退出强无人,恢复可向用户提问)
argument-hint: ""
---

用户要切回**有人值守**。

## 现状(动态注入)

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/mmw.sh" unattended exit 2>&1`

## 指令

1. 若输出 `ATTENDANCE=attended`:告诉用户已回到有人值守,后续软停会正常问人(AskUserQuestion)。
2. 若输出 `NO-ACTIVE-RUN` 或报错:说明当前不在在管任务,无 run 可切换。
3. 切回后照 `mmw where` 续跑。
