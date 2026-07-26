---
name: rescope
description: 需求变化,砍或加范围(必要时回流 design/plan)
argument-hint: "<范围变化说明>"
disable-model-invocation: true
---

用户要改本任务范围。变化说明 = `$ARGUMENTS`。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时按安装位查找（Marketplace / Team Marketplace 安装后通常落在 Cursor plugins 目录；本地试装在 `~/.cursor/plugins/local`）：

```sh
MMW_ROOT=""
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ] && [ -f "$CURSOR_PLUGIN_ROOT/scripts/mmw.sh" ]; then
  MMW_ROOT="$CURSOR_PLUGIN_ROOT"
fi
if [ -z "$MMW_ROOT" ]; then
  for cand in \
    "$HOME/.cursor/plugins/local/multi-model-workflow-cursor" \
    "$(pwd | sed -n 's|\(.*multi-model-workflow\)/.*|\1/cursor-plugin|p')" \
    "$(pwd)/cursor-plugin"
  do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
# Marketplace 缓存安装位：按 name 扫一层
if [ -z "$MMW_ROOT" ]; then
  for cand in "$HOME"/.cursor/plugins/*/*/multi-model-workflow-cursor \
              "$HOME"/.cursor/plugins/*/multi-model-workflow-cursor; do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先从 Cursor Marketplace / Team Marketplace 安装 multi-model-workflow-cursor，或设 CURSOR_PLUGIN_ROOT"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从 `.pi` / `.claude` / `.factory` 宿主镜像目录取运行时代码。
<!-- END: locate-mmw -->

1. 先跑 `mmw where` 看当前阶段。
2. 刷新任务档案的源意图:`mmw task scope --request '<更新后的完整范围与验收条件>'`(写完整新范围,不是增量说明;审闸拿它当源意图,过期就审错标)。
3. 判断范围变化影响面:
   - 只调当前阶段内 → 就地改,更新设计/计划对应处。
   - 触及已过门的设计/计划 → 回流对应阶段(`mmw` 阶段掉头),已完成部分保留。
4. 大改先读后写:触碰设计/计划权威文档前先读再改;说明保留了什么、重做什么。
5. 刷新板:`mmw progress render`。
