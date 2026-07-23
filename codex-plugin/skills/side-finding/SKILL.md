---
name: side-finding
description: 用户明确指定把当前计划外发现开 issue 留后续或纳入当前修复时使用。
---

# 处置计划外发现

本入口只响应用户显式调用。读取用户给出的 `issue` 或 `fix`、问题标签和一句话摘要。

从本 skill 的绝对路径定位 plugin：

```bash
MMW_SKILL="<本轮 skill source locator 给出的 side-finding/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$MMW_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
```

标签只能是 `bug`、`optimize`、`out-of-scope` 或 `needs-evaluation`。执行：

```bash
bash "$MMW" side-finding record --tag <标签> --disposition <issue|fix> --finding "<摘要>"
```

`fix` 不扩大当前合法修复边界；需要扩大范围时改走调整范围入口。照实回报落盘结果。
