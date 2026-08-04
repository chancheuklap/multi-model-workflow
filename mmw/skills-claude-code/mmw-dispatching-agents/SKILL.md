---
name: mmw-dispatching-agents
description: >
  把一件活派给隔离上下文的 subagent。要启动 worker、planner、investigator
  或审查者时用。
---

把活派给隔离上下文的 subagent。你编排；它执行。
用 `mmw dispatch` 启动（型号与后台由 CLI 写入，你不填型号）。
按下方「启动」四节依次做完。

## 派不派

**默认派。** 仅下列情形自己做，不启动 subagent：

- 必须和用户来回才能推进
- 结论必须由你对用户负责（不能下放）
- 事先写不出 brief，只能边看边改方向
- 一句话能做完，派发往返更慢

subagent 内部的探路仍派。只有**你**要改判断方向时才留下。

**一个方向一个人。** 多个独立方向就多次启动。并行时：先在同一条消息里发出多个后台 `mmw dispatch`；收齐 `mode: host-tool` 回执后，再在同一条消息里调用各自的宿主工具。

## 角色

下列名字原样作为 `mmw dispatch` 的角色参数（不要改成 `mmw-worker` 这种 agent 文件名）：

`worker` · `worker-high-risk` · `planner` · `investigator` · `reviewer-gpt` · `reviewer-claude`

不带参数执行 `mmw dispatch` 可查看用法。  
角色以当前任务说明为准（含是否改用 `worker-high-risk`、派哪个审查角色）。

## 启动

### 写 brief 文件

brief 是写在磁盘上的一段指令，只含：

1. 要交付什么、边界与验收  
2. **去读哪些路径**（派前确认仓库内路径存在）  
3. 当前任务说明里要求写入的其它项  

brief **只放指令与路径**。文件正文由 subagent 自己读取。

落盘位置：

- 一般派发：目标 worktree 下 `.dispatch/<名>.md`  
- 审查派发：目标 worktree 下 `.reviews/<名>.md`  

需要时先 `mkdir -p` 对应目录。路径使用**绝对路径**传给后面的 `--brief`。

**完成判据：** brief 文件已存在且非空；其中每个声称存在的仓库内路径检查为真，或不存在的已在 brief 里写明「无」。

### 运行 mmw dispatch

用 Bash 工具，`run_in_background: true`：

```bash
mmw dispatch <角色> --brief <brief文件绝对路径> [--cwd <worktree绝对路径>]
```

- `<角色>`：「角色」节列出的名字之一  
- 可写角色（`worker`、`worker-high-risk`、`planner`）：`--cwd` **必填**，值为 worktree 根绝对路径；工作区不干净时命令失败  
- 只读角色：可省略 `--cwd`

**完成判据：** 后台命令已启动，且你已读到该次运行的完整回执文本（含首行 `mode:`）。

### 按回执调用宿主工具

读回执第一行 `mode:`。

**`mode: executed`**  
报告路径在 `report:` 字段。读该文件即 subagent 报告。本节无其它动作。

**`mode: host-tool`**  

1. 读取 `tool:` 字段（`Agent` 或 `Bash`）  
2. 读取 `params:` 后的整包 JSON  
3. 调用对应宿主工具时，**原样传入该 JSON 的每一个键**（不删键、不改名、不手写子集）

| `tool` 值 | 你要做的 |
| --- | --- |
| `Agent` | 将 brief 文件的**完整文件内容**作为提示词；若回执有 `skill-path:`，在提示词中要求 subagent 先读该路径；`params` 整包带上 |
| `Bash` | 使用 `params` 里的 `command` 字段（命令已含后台语义） |

工具会先返回 run id；等该次运行结束后再读报告。

**完成判据：**

- `executed`：已拿到 `report:` 路径  
- `host-tool`：已按 `tool` 启动，且传入的 params 键集合与回执一致  

### 收回

将报告交给 `/mmw-verifying-agent-output` 验证。  
未经验证的句子不当作事实写进交付物或对用户的结论。

**完成判据：** 已打开 `/mmw-verifying-agent-output` 并按其正文处理；或已改好 brief、准备从「写 brief 文件」重新跑一遍（新会话）。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 报告已交回 | **移交**：`/mmw-verifying-agent-output` |
| 验证后要重派 | **自己继续**：修改 brief 文件后，从「运行 mmw dispatch」重做（新会话） |
| 工作区不干净 | **停**：列出未提交改动 |
| brief 路径或其中引用的路径不存在 | **自己继续**：改路径后从「写 brief 文件」重做 |
| 回执表明认不出宿主 | **停**：说明当前环境没有宿主标记 |
| Codex 报 model is not supported（ChatGPT 账号） | **停**：请用户刷新 Codex 型号缓存并核对 `~/.codex/models_cache.json`；未证实缓存缺该型号前不改 `.mmw.json` |
