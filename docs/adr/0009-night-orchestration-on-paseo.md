---
date: 2026-09-06
amends: []
---

# 夜间编排从 Herdr 迁到 Paseo：脚本只做工具，判断归 main agent

夜间编排原来由一份不带模型的守夜脚本（`board.py --watch`）读会话事件、决定 `continue` / `STOPPED` / `TIME LIMIT`、再把 `mmw board:` 行发给 main agent。现在夜间只有 main agent 在线：`dispatch.sh` 与 `status.py` 合并、建 workspace、打印 `create_agent` 参数、给出一张表；每一张 finish notification 之后，是否 `advance`、是否 `resume`、一次失败是不是自己的，都由 main agent 判断。理由是判断本来就是它的，把判断再交给一份无模型脚本，只是把同一张表藏进状态机。

## Considered Options

- **保留不带模型的守夜脚本，改读 Paseo 事件。** 否决。Paseo 的完成通知已经把「某个 agent 停了」送到 main agent 眼前；再养一份脚本去订阅、分类、代写 `continue`，等于在通知和判断之间加一层没有模型的中介。user 2026-09-05 确认「主 agent 整夜在线、按通知逐次工作并不是坏事」，所以这一层不留。

## Consequences

- `dispatch.sh` 的动词是 `check`、`advance`、`start`、`wait`、`resume`、`status`、`reverify`、`summary`、`suspend`。没有 `run`。`wait` 只等一个自己起的 agent 并打印它的结果首行，不写票、不设超时评论；main agent 对 worker 不用它，靠 finish notification 与 `check` 建的 heartbeat 被叫醒。夜的顺序在 `mmw-v2/skills/dispatch/references/night.md`。
- `install.sh` 装什么，就负责把它上一代装过、这一代不再装的东西摘掉——技能软链、hook 登记、Agent profile 三类都一样；`--check` 把它们报为残留。一个 host 配置里指着已删脚本的登记，会在每次事件上让 host 调用失败。
- `status.py` 只读：tracker 与 `paseo ls` / `paseo inspect`。`phase` 从票的评论推出。
- 归档只有一处：`advance` 合并该票分支后归档其 workspace，连带其中的 agent。`--closeout` 不归档。
- reviewer 与 verifier 是 worker 起的 Paseo subagent，结果写回票。
