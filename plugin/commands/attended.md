---
description: 切回有人值守(退出强无人,恢复可向用户提问)
argument-hint: ""
---

用户要切回**有人值守**。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 跑 `mmw unattended exit`,按输出处置:
2. 若输出 `ATTENDANCE=attended`:告诉用户已回到有人值守,后续软停会正常问人(AskUserQuestion)。
3. 若输出 `NO-ACTIVE-RUN` 或报错:说明当前不在在管任务,无 run 可切换。
4. 切回后照 `mmw where` 续跑。
