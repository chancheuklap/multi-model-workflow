---
description: 当前步骤先放下,继续后面(记 blocked/skipped 留痕)
argument-hint: ""
disable-model-invocation: true
---

用户要放下当前卡住的步骤先继续后面。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 先跑 `mmw where` 看现状。
2. 记下放下的是什么、为什么(一句话),落 `mmw side-finding record` 或 `mmw loop softstop` 留痕,别静默跳过。
3. 推进到下一步(`mmw step next` 或推进游标),说明放下了哪一步、后面从哪续。
4. 刷新板:`mmw progress render`。
