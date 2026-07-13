---
description: 当前步骤先放下,继续后面(记 blocked/skipped 留痕)
argument-hint: ""
disable-model-invocation: true
---

用户要放下当前卡住的步骤先继续后面。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——候选(缓存各版本 + 本地源安装)按版本取最高,不许 `head -1` 抓第一个:

```sh
P=~/.factory/plugins
MMW="$( { find "$P" -type f \( -path '*multi-model-workflow-droid*/scripts/mmw.sh' -o -path '*/droid-plugin/scripts/mmw.sh' \) 2>/dev/null
  jq -r '.["multi-model-workflow-droid"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/droid-plugin/scripts/mmw.sh|'
  } | while IFS= read -r f; do
    [ -f "$f" ] || continue
    r="${f%/scripts/mmw.sh}"
    v="$(jq -r '.version' "$r/.factory-plugin/plugin.json" 2>/dev/null || echo 0)"
    printf '%s %s\n' "$v" "$f"
  done | sort -V | tail -1 | cut -d' ' -f2- )"
echo "MMW=$MMW"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。
<!-- END: locate-mmw -->

1. 先跑 `mmw where` 看现状。
2. 记下放下的是什么、为什么(一句话),落 `mmw side-finding record` 或 `mmw loop softstop` 留痕,别静默跳过。
3. 推进到下一步(`mmw step next` 或推进游标),说明放下了哪一步、后面从哪续。
4. 刷新板:`mmw progress render`。
