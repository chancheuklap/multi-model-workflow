---
name: progress
description: 从 MMW 磁盘状态重建并展示当前任务进度板。
---

# 展示进度

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 progress/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

运行：

```bash
bash "$MMW" progress render --stdout
```

`NO-ACTIVE-RUN` 表示当前没有在管任务，不能伪造进度。有进度板时直接展示，只补一句当前阻塞或待用户拍板项；不自动续跑。
