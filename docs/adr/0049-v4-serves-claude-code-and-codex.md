---
date: 2026-10-14
amends: [0003, 0006, 0007, 0021]
---

# MMW v4 只服务 Claude Code 与 Codex 两个 host，Grok 与 Cursor 退出

主人 2026-10-14 停用了 Grok 和 Cursor。v4 之前为它们各备了一整套：`hosts.json` 里的启动块与 `models.py` 里的目录解析，`tool-guard.py`、`turn-guard.py` 的注册与「在别家里让位」的判断，`render.py` 生成的 `~/.grok/AGENTS.md`，Grok 的子代理层数，`~/.paseo/config.json` 里的两条 provider，board 的 host 列表，以及把 junior-worker、researcher 默认派给 Grok 的 `hosts.json` 默认值。这些都拿掉了；`models.json` 里写 `grok` 或 `cursor` 的行从此按未知 host 拒绝。

## 拿掉之后还留着什么

- `install.sh` 的 hook 清扫名单保留 `~/.cursor/hooks.json` 与 `~/.grok/hooks/` 两个文件的三行，以及读 Cursor 格式的那段代码：真机重装时由它把 MMW 从前写进去的处理器摘干净，别人的处理器不动，`--check` 在摘之前报残留。Paseo 的 grok、cursor 两条 provider 同理，装的时候摘，`--check` 见到就报。
- 两个守卫收到 `grok` 或 `cursor` 这种旧注册的调用，只打印用法、退出 0，什么都不拦。
- `mmw-mode` 的 `scripts/worktree-audit.sh` 仍读 Grok 与 Cursor 的会话目录：一个刚被它们用过的工作树，不能因为少看了两处就被判成可以删。
- `recall`、`reflect`、`automate-me` 三个技能里写给 Cursor 的部分，以及指南里讲它们的段落，留待主人另行决定。
- `install.sh --back` 不变：退回 v3 时，v3 自己的 `install.sh` 照旧为它认识的 host 装。

## Considered Options

- **代码留着，只把默认值从 Grok 挪走。** 否决。每多一个 host，就多一份要随它版本升级重测的东西：事件的字段拼法、拒绝的格式、回合结束能不能拦、环境变量会不会漏进子进程。没人用的 host 没人重测，这些判断会悄悄过期，而 Claude 那份 hook 前面的 Grok 环境守卫、读 payload 认 Cursor 的分支，都在每一次 Claude 会话里实际执行。
- **把相关代码挪进 `mmw-v4/docs/retired-skills/` 一类目录。** 否决。拿掉的是脚本里的分支和配置块，不是一个技能或 playbook，没有可以整体搬走的单位；git 历史已经保存了它们。
- **连清扫名单也一起删。** 否决。真机上 `~/.cursor/hooks.json`、`~/.grok/hooks/` 里还有 MMW 装过的处理器，名单一删，它们就再也没人认领，指着的脚本一变就各自在那个 host 上报错。

## Consequences

- 新机器的 junior-worker 与 researcher 默认是 codex `gpt 6.1 sol` medium，senior-worker 是 codex `gpt 6.1 sol` high；已有的 `models.json` 只补缺的角色行，不改已有行。
- 发布之后第一次 `install.sh --check` 会报 Claude 那几条 hook 命令「缺」（命令前不再带 Grok 守卫），以及 Cursor、Grok 两处的残留和 Paseo 的两条 provider；跑一次 `install.sh` 即齐。
- 再加回一个 host 是一个新决定：要有启动块、目录解析、hook 的事件形状与拒绝格式、提示词的送达路径，并且逐项在那个 host 的当前版本上实测。
- 0003、0006、0007、0021 里关于 Grok、Cursor 的部分不再成立；它们其余的决定不变。
