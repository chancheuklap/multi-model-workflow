---
description: 需求变化,砍或加范围(必要时回流 design/plan)
argument-hint: "<范围变化说明>"
disable-model-invocation: true
---

用户要改本任务范围。变化说明 = `$ARGUMENTS`。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——候选(缓存各版本 + 本地源安装)按版本取最高,不许 `head -1` 抓第一个:

```sh
P=~/.claude/plugins
MMW="$( { find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null
  jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|'
  } | while IFS= read -r f; do
    [ -f "$f" ] || continue
    r="${f%/scripts/mmw.sh}"
    v="$(jq -r '.version' "$r/.claude-plugin/plugin.json" 2>/dev/null || echo 0)"
    printf '%s %s\n' "$v" "$f"
  done | sort -V | tail -1 | cut -d' ' -f2- )"
echo "MMW=$MMW"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。
<!-- END: locate-mmw -->

1. 先跑 `mmw where` 看当前阶段。
2. 判断范围变化影响面:
   - 只调当前阶段内 → 就地改,更新设计/计划对应处。
   - 触及已过门的设计/计划 → 回流对应阶段(`mmw` 阶段掉头),已完成部分保留。
3. 大改先读后写:触碰设计/计划权威文档前先读再改;说明保留了什么、重做什么。
4. 刷新板:`mmw progress render`。
