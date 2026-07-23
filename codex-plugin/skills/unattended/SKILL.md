---
name: unattended
description: 用户明确要求当前 MMW 任务进入强无人值守时使用；门禁不满足就拒绝。
---

# 进入强无人值守

本入口只响应用户显式调用。

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 unattended/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

运行：

```bash
bash "$MMW" unattended enter
```

`UNATTENDED-ENTERED` 后按盘上的 policy 继续，不向用户提问；软停自行处置留痕，只有设计被打穿、外部环境、预算或没有自动路径时才硬停写板。`ERROR: 拒绝进入` 时原样报告缺失门禁，不能降级或强行进入。
