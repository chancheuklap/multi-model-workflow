---
date: 2026-10-06
amends: []
---

# 一夜的 Memory 只写进本仓库的 Space：开夜的会话 `NMEM_SPACE` 不对就拒绝开夜；Nowledge Mem 列不全这份 spec 的记录时，夜照样关，不做 Memory 收尾

`dispatch.sh check`、`open` 和 `open-ticket` 先比较本会话的 `NMEM_SPACE` 和本仓库的 Space（`<owner>__<name>`，小写），不一样就退 2，什么都不推、不开。`brief` 开出的会话由 runner 起，不继承调用它的会话的环境，所以和 worker、reviewer 一样，由 `dispatch.sh` 把本仓库的 Space 交给它；Space 核不到时照样开，stderr 说它们会写进 Default。收尾时，`memory-list` 退 2（Nowledge Mem 没回应，或只返回部分记录）之后，`summary <spec> --memory-unavailable` 关夜：`spec.closed` 的 `memory_closing` 是空的决定列表加原因，`NIGHT SUMMARY` 写一行「Memory closing: not done」。Nowledge Mem 能把记录列全时，这个开关被拒绝。

## 要修的是什么

- orchestrator 写 Memory 用的是它自己会话的环境。用户的终端经 `~/.zshrc` 按仓库设好 `NMEM_SPACE`，但那段只在有 TTY 的 shell 里运行；从别处起的会话没有它，nmem 遇到空的或不认识的 Space 不报错，静默写进 Default，第二天注入用户开的每个会话。
- 原来的收尾没有 Nowledge Mem 就关不了夜：`memory-list` 退 2，`summary` 必须有决定文件。一夜的票都已落地，却因为一个记忆服务停着而挂在那里。

## Considered Options

- **会话 Space 不对时只警告。** 否决。会话开起来以后脚本改不了它的环境，警告之后这一夜学到的照样进 Default；拒绝发生在推送和开夜之前，重开会话就能继续。
- **`dispatch.sh` 替 orchestrator 写 Memory。** 否决。orchestrator 在会话里随时自己调 `nmem` 写 Memory，这些调用不经过 `dispatch.sh`。
- **等 Nowledge Mem 恢复再关夜。** 否决（用户决定）。夜的结果在 tracker 上，不在 Memory 里；等待让 `finish` 和下一夜都跟着停。
- **只在没回应时才允许不做收尾。** 否决。只返回部分记录时，`memory-list` 拒绝写决定文件，`--memory-unavailable` 又因为「它回应了」被拒绝，夜会在两步之间来回。

## Consequences

- 从不经过 `~/.zshrc` 的地方起的 orchestrator 会话，开不了夜，直到带着本仓库的 `NMEM_SPACE` 重开。
- 不做收尾关掉的那一夜，它的记录原样留着，仍带 `mmw-experience` 标签，后来的 worker 照样会看到，其中可能有已过时的；没有哪一步回头处理它们。
- 用户层的会话（不开夜、不派 agent）写 Memory 仍只靠 `~/.zshrc`，这份决定不管。
