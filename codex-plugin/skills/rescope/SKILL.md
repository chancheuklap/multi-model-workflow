---
name: rescope
description: 用户明确改变当前 MMW 任务范围时，更新完整需求并回流受影响阶段。
---

# 调整范围

本入口只响应用户显式调用。用户随调用给出的文字是范围变化；结合原任务整理成更新后的完整范围与验收条件，不能只写增量。

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 rescope/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

先运行 `bash "$MMW" where`，再执行 `bash "$MMW" task scope --request '<更新后的完整范围与验收条件>'`。只影响当前阶段就地更新；触及已过门设计或计划时，执行 `mmw handoff --conclusion needs-redirection --to-phase <design|plan>`。设计有改动后必须由用户重新显式调用确认设计入口。最后重渲染进度板。
