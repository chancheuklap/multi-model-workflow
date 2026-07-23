---
name: skip-current
description: 用户明确要求暂时放下当前步骤、留下阻塞记录并继续其他可执行工作时使用。
---

# 放下当前步骤

本入口只响应用户显式调用。

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 skip-current/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

先运行 `bash "$MMW" where`，记录当前放下的步骤和原因。build 内层步骤用 `mmw loop softstop` 留 pause；计划外项用 `mmw side-finding record` 落入 `open_items`。随后只继续不依赖该阻塞项的工作，并运行 `bash "$MMW" progress render`。不能静默标成完成。
