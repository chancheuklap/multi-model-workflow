---
name: mmw-dispatching-agents
description: >
  把一件活派给隔离上下文的 subagent。在要派 worker、planner、investigator、
  审查者，或别的技能写「按 /mmw-dispatching-agents 派」时用。
---

把活派给隔离上下文的 subagent。你编排；它执行。
启动：`mmw dispatch`（型号与后台由它写入）。调用方已写好角色与 brief 要点时，从「步骤」做起。

## 派不派

**默认派。** 仅下面情况自己做：要跟用户来回；结论必须由你对用户负责；事先写不出 brief、只能边看边定方向；一句话就做完、派发往返更慢。

subagent 内部的探路照派。只有**你**要换判断方向时才留下。

**一个方向一个人。** 多方向就多派。并行：一条消息里多个后台 `mmw dispatch`；拿到 `mode: host-tool` 后，再一条消息里调各自的宿主工具。

## 角色

角色名原样传给 `mmw dispatch`：`worker`、`worker-high-risk`、`planner`、`investigator`、`reviewer-gpt`、`reviewer-claude`。
不带参数跑 `mmw dispatch` 可看用法。哪两个审查角色、何时升 `worker-high-risk`，由调用方技能决定。

## 步骤

### 1. 写 brief 文件

内容：要交付什么、去读哪些路径、边界与验收。路径须真实存在。
brief 里只放指令与路径；文件内容由 subagent 自读。

写到 worktree 下 `.dispatch/<名>.md`（审查写 `.reviews/<名>.md`），`mkdir -p` 按需。
调用方技能若列出要点名的材料，照那份清单写。

**完成**：brief 文件在磁盘上；其中每个仓库内路径存在（或已标明「无」）。

### 2. 派发

Bash，`run_in_background: true`：

```bash
mmw dispatch <角色> --brief <brief文件绝对路径> [--cwd <worktree绝对路径>]
```

可写角色 `--cwd` 必填；工作区不干净时命令失败。

**完成**：命令已在后台启动并已读到回执文本。

### 3. 接回执

看第一行 `mode:`。

**`mode: executed`** — 读 `report:` 路径即报告。

**`mode: host-tool`** — 调 `tool:` 指名的工具，**原样**传入 `params:` 整包 JSON（每个键都保留）。

| tool | 做法 |
| --- | --- |
| `Agent` | 将 brief 文件内容作为提示词；有 `skill-path:` 则要求 subagent 先读该路径；`params` 整包带上 |
| `Bash` | 使用 params 里的 `command`（已含后台） |

工具先回 run id；完成后再读报告。

**完成**：宿主工具已按回执启动；未改写 params 键集。

### 4. 收回

报告交 `/mmw-verifying-agent-output`。未经验证的句子不当事实用。

**完成**：已移交验证，或已按验证结果准备重派。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 报告已交回 | **移交**：`/mmw-verifying-agent-output` |
| 验证后要重派 | **自己继续**：改 brief 后重新 `mmw dispatch`（新会话） |
| 工作区不干净 | **停**：列出未提交改动 |
| brief 路径不存在 | **自己继续**：改路径后再派 |
| 认不出宿主 | **停**：说明当前环境没有宿主标记 |
| Codex 报 model is not supported（ChatGPT 账号） | **停**：先让用户刷新 Codex 型号缓存并核对 `~/.codex/models_cache.json`；未证实缓存缺型号前不改 `.mmw.json` |
