---
description: 需求变化,砍或加范围(必要时回流 design/plan)
argument-hint: "<范围变化说明>"
disable-model-invocation: true
---

用户要改本任务范围。变化说明 = `$ARGUMENTS`。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 先跑 `mmw where` 看当前阶段。
2. 判断范围变化影响面:
   - 只调当前阶段内 → 就地改,更新设计/计划对应处。
   - 触及已过门的设计/计划 → 回流对应阶段(`mmw` 阶段掉头),已完成部分保留。
3. 大改先读后写:触碰设计/计划权威文档前先读再改;说明保留了什么、重做什么。
4. 刷新板:`mmw progress render`。
