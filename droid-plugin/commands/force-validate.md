---
description: 立刻跑当前层的合法审查
argument-hint: ""
---

用户要立刻对当前阶段产物跑审查。

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

1. 先跑 `mmw where` 看当前阶段与可用的 `review_start`(在审闸内 where 会吐出带 `--stage` 和 `--source` 的完整命令)。
2. 触发当前层合法 review:照抄 where 吐的 `review_start` 整条跑(`--source` 必填,不可省)。不在审闸内则无合法审可起,如实告知用户。
3. 只跑当前层该跑的审,不越层;审完照 review 回执处理 findings。
