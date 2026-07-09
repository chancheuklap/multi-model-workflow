---
description: 保留已完成,重做后续计划
argument-hint: ""
disable-model-invocation: true
---

用户要保留已完成部分、重做后续计划。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 先跑 `mmw where` + 看 progress board,确认哪些 plan/step 已完成(done)。
2. 已完成的不动;回流 plan 阶段,只重写未完成部分的计划。
3. 说明保留了哪些、重做哪些,给新的执行序。
4. 刷新板:`mmw progress render`。
