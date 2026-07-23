---
name: force-validate
description: 用户要求立刻审查当前 MMW 阶段产物时，启动当前层唯一合法的审查。
---

# 立刻审当前层

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 force-validate/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

先运行 `bash "$MMW" where`。只有输出给出完整 `review_start` 时才照抄执行；它已经包含当前 stage 和必需的 Source。没有 `review_start` 就说明当前不在审闸，不自造跨阶段审查。
