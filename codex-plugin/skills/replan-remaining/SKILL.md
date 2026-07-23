---
name: replan-remaining
description: 用户明确要求保留已完成内容并重做后续计划时使用。
---

# 重做剩余计划

本入口只响应用户显式调用。

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 replan-remaining/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

先运行 `bash "$MMW" where` 和 `bash "$MMW" progress render --stdout`，向用户说明保留哪些已完成内容、重做哪些未完成内容。然后执行：

```bash
bash "$MMW" handoff --conclusion needs-redirection --to-phase plan
```

只修订后续 plan，不改已经完成的落地；最后重渲染进度板。
