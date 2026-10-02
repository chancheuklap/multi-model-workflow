---
date: 2026-10-02
amends: [0020, 0031]
---

# 唤醒、告警、回合守卫和 `resume` 都是一行，末尾带步骤指针；收件角色只由 watch 的 `kind` 决定；开工提示词是一行，数据在文件里；位置只由 `dispatch.sh where` 给出

一次 watch 里，会话之间传递的文字是一行。唤醒、告警、turn guard 拦住回合时的文字，以及 `dispatch.sh resume` 送出的文字，都以 ` · mmw <playbook>#<step>` 结束。指针按（收件角色，事件）取自 `mmw-v2/skills/mmw/roles.json` 的 `wakes`。`ack` 仍按收件人、票和事件名匹配，不按指针匹配。这修订 ADR 0020 的唤醒文字 `#<n> <event>`。

收件角色由 watch 的 `kind` 决定：`night` 是 `night-orchestrator`，`ticket` 是 `one-ticket-orchestrator`，`adopted-ticket` 是 `adopting-worker`。没有 `kind` 的 watch 不被猜。relay 拒绝投递，并点名重开的命令：`dispatch.sh open-night`、`dispatch.sh open-ticket-watch` 或 `dispatch.sh adopt`。这是 ADR 0032 留给本份记下的那一半。

开工时会话拿到的提示词是一行，带 `unattended:`。worker、reviewer 和 researcher 的形状是 `Use the mmw skill. Role <role>, ticket #<n>, unattended: mmw <playbook>#<step>. Data: <file>.`，reviewer 另带 `base <commit>`。advisor 的形状是 `Use the advisor skill. Role advisor, unattended: the mmw skill's ## Autonomy. Brief: <file>.`。Memory 索引、Rules 指针和简报路径写在数据文件 `state/<owner>__<name>/prompts/<n>-<role>.md` 里。相关经验仍按 ADR 0031 的方法搜索：本票 `## Owns` 的路径和各级标题，不用 spec 或 map 正文。变的是投递：索引进文件，不进那一行提示词。

`dispatch.sh where` 是唯一的位置来源。`ticket_state.py <n> --claim` 只打印 `NOT_READY:`、`READY:` 和 `CARRIED:`。

## Considered Options

- 多行提示词里夹带规则。否决。H4：runner 把换行当作提交，一条消息必须是一行。规则另有家，在 playbook、原则和数据文件里。
- `--claim` 继续打印 `RESUME:`，与 `dispatch.sh where` 并存。否决。两个位置来源会分歧，会话不知道听哪一个。
- 没有 `kind` 时按 playbook 猜收件角色。否决。ADR 0008：猜错就是静默送到错误的人。拒绝并点名重开的命令是唯一出路。

## Consequences

- 唤醒文字不再是 `#<n> <event>` 单独一行。告警、turn guard 和 `resume` 与唤醒用同一种结尾。
- `roles.json` 的 `wakes` 是「哪个事件把哪个角色叫醒到哪一步」的唯一清单。说明机器怎么跑的文档指向它，不再逐角色另抄一份。
- 开工提示词不再把 Memory 索引和 Rules 写进会话的第一行。搜索方法与 ADR 0031 相同。
- `where` 成为位置的唯一来源。认领不再报告该从哪一步接着做。
