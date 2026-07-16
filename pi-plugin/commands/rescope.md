---
description: 需求变化,砍或加范围(必要时回流 design/plan)
argument-hint: "<范围变化说明>"
disable-model-invocation: true
---

用户要改本任务范围。变化说明 = `$ARGUMENTS`。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——**读实际激活的安装位**(installed_plugins.json),不扫缓存挑版本号(缓存里躺着历史版本,版本号最高 ≠ 正在运行的那个):

```sh
P=~/.factory/plugins
MMW="$( jq -r '.plugins | to_entries[] | select(.key | startswith("multi-model-workflow-droid@")) | .value[0].installPath // empty' \
        "$P/installed_plugins.json" 2>/dev/null | head -1 | sed 's|$|/scripts/mmw.sh|' )"
[ -f "$MMW" ] || MMW="$( jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/droid-plugin/scripts/mmw.sh|' )"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败:插件未装?(装了才有 installed_plugins.json 条目)"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。**别用仓库里的相对路径 `droid-plugin/scripts/mmw.sh` 当运行时**——在旧分支 worktree 里那是旧代码。
<!-- END: locate-mmw -->

1. 先跑 `mmw where` 看当前阶段。
2. 刷新任务档案的源意图:`mmw task scope --request '<更新后的完整范围与验收条件>'`(写完整新范围,不是增量说明;审闸拿它当源意图,过期就审错标)。
3. 判断范围变化影响面:
   - 只调当前阶段内 → 就地改,更新设计/计划对应处。
   - 触及已过门的设计/计划 → 回流对应阶段(`mmw` 阶段掉头),已完成部分保留。
4. 大改先读后写:触碰设计/计划权威文档前先读再改;说明保留了什么、重做什么。
5. 刷新板:`mmw progress render`。
