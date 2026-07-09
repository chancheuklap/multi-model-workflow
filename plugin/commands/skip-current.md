---
description: 当前步骤先放下,继续后面(记 blocked/skipped 留痕)
argument-hint: ""
disable-model-invocation: true
---

用户要放下当前卡住的步骤先继续后面。

## 指令

1. 读 `${CLAUDE_PLUGIN_ROOT}/scripts/mmw.sh` 现状:先跑 `mmw where`。
2. 记下放下的是什么、为什么(一句话),落 `mmw side-finding record` 或 `mmw loop softstop` 留痕,别静默跳过。
3. 推进到下一步(`mmw step next` 或推进游标),说明放下了哪一步、后面从哪续。
4. 刷新板:`mmw progress render`。
