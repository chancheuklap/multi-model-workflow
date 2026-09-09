---
date: 2026-09-09
amends: [0015]
---

# 会话怎么起写在本机活表里

`start` 读的是本机 `~/.mmw/models.md`：日常名，四列 `agent | host | model | effort`。仓库不再放给人改的 `models.md`。`hosts.json` 按 host 记下 Herdr 怎么起、Paseo 怎么起，以及第一次 `install.sh` 拷进活表的默认行。`start` 问这台机器今晚该 host 有哪些模型，对上恰好一个才起。

## 要修的是什么

`AGENTS.md` 写 `models.md` 是这台机器的一份，实际它跟着技能软链进 git。换 reviewer 的 host 等于改仓库。表上还要求写成各家命令行内部名，Herdr 和 Paseo 对同一台 Cursor 要的名字又不一样。Paseo 再按这张表写 Agent profile，是第二份要靠安装同步的缓存。

## Considered Options

- **活表写 host 命令行原名，Paseo 再翻成自己的 id。** 否决。人要先去查 slug；两边目录已经对不上（Paseo 上 Cursor 的思考档只有开和关，仓里却写 `high`）。
- **JSON 按 agent × host × 夜间进程宿主列出完整启动指令。** 否决。今晚 junior-worker 用谁又写回 git。
- **认名写进 git 的别名表。** 否决。会过期，`fable` 已经让 Paseo 界面显示成别的模型。
- **`editing-models.md` 当作 `start` 读的说明，认不出就指向它。** 否决。那份文件只在用户下令改 host、model，或改夜班跑 Herdr 还是 Paseo 时给 agent 看。拒绝写在那次 `start` 的 stderr 上。

## Consequences

- **活表第一次 `install.sh` 从 `hosts.json` 的 defaults 拷入，之后不覆盖。** 缺活表时 `start` 拒绝并点名 `install.sh`。`--check` 不拿活表和默认行做 diff。
- **Paseo 不再从活表写 Agent profile，也不再打 `mmw.profile`。** 笔记含 `from models.md` 的生成 profile 报残留；手写的不动。不删 `~/paseo-worktrees`。
- **0015 里「这次不删 `permissions` 列」不再成立。** 派出的全是会话，那一列只有一个合法值。
- **轴评审和 main agent 仍然没有自己的行。**
