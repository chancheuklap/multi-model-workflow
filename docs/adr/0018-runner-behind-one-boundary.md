---
date: 2026-09-10
amends: [0009, 0016]
---

# runner 收进一条边界：协议只调三个动词，一个 runner 一个适配器，今晚用哪个是本机一行配置

协议（`dispatch.sh` 与它读写的票）和跑会话的程序（runner：有适配器的是 Paseo、Orca、Herdr）之间只有一条边界。边界上是三个动词——起会话（给目录、host、model、effort 与第一句话，拿回会话号，起不来就拒绝）、送消息（三态回执：送到了 / 在回合中没接 / 没有这个会话；答不出就答不知道）、问死活（活着 / 已停止 / 不知道）——外加结束会话的 `stop`。每个 runner 一个适配器文件 `mmw-v2/skills/dispatch/scripts/runners/<runner>.sh`，是写这个 runner 命令的地方；文件头的 `# MMW_USES:` 由 `install.sh --check` 对着二进制核对。今晚用哪个 runner 由 `models.py runner` 从上往下找：`MMW_RUNNER`、活表的 `| runner | <name> |` 行、本进程所在的 runner（自己切工作树的那类永不被探测选中）、`orca`。`start` 把 `RUNNER <runner> <session> <kind>` 写在票上，之后的 `resume`、`wait`、`retract`、`land`、`suspend` 只问那一行点名的 runner。工作树由协议用 git 切、用 git 删，runner 只拿到绝对路径。起会话被拒就是终点：stderr 上一行拒绝，不重试，不换 host，不换 runner。

## 要修的是什么

runner 的知识散在四个脚本里（`dispatch.sh`、`status.py`、`verify-ticket.py`、`hook.py`），没有一个地方能只换它们，于是「让夜跑在 Herdr 上」只能开一条分支把四个脚本各改一遍。`spec-300-herdr-night` 就是这样分出去的：分支与 main 各自往前走，同一件事写了两遍，最后合不回来，只能收成 tag `archive/spec-300-herdr-night`。那条分支还给 `dispatch/SKILL.md` 的 `description` 加了一句 `Requires HERDR_ENV.`，一句话把整份技能锁在一个 runner 上。

## Considered Options

- **runner 知识留在各脚本里，按 runner 名分支。** 否决。换一个 runner 要改四个文件，每加一个 runner 代价都再涨一次，开分支的理由一直在。
- **起会话仍然打印一个 `create_agent` 对象，由 main agent 自己去调。** 否决。那是 Paseo 的 MCP 工具，没有它的会话不能派发；起没起来取决于模型有没有照做一段散文，协议也拿不回会话号。
- **起会话失败时退避重试五次（1、2、4、8、16 秒），再落到活表第二行的 fallback host。** 否决（用户 2026-09-10）。重试是叠在 runner 自带超时外面的第二层等待，针对的是 Paseo 的一个具名症状；fallback host 让「今晚这个角色跑在哪」有两个答案，而主 host 起不来的那一夜被悄悄顶替，第二天早上才看得见。要更有耐心，就调适配器传给 runner 的那个超时。
- **选定的 runner 起不来时换另一个顶上。** 否决，理由同上：拒绝要响，替换是静默的（`docs/adr/0008-silence-is-never-a-pass.md`）。
- **工作树交给 runner 切（`paseo workspace create`，或 Orca 自己的工作区）。** 否决。工作树是 `land` 要合并、归档的东西，交给 runner，换 runner 时它就要跟着搬。代价是只肯在自己切的工作树里起会话的 runner（Lody）接不进来。
- **适配器运行时读 runner 自带的技能指南，再拼命令。** 否决。每起一个会话多一次调用，又慢又脆，解析自然语言也比写死几条命令更容易错。二进制才是命令的权威，由 `--check` 核对声明。
- **把 runner 前置条件写进技能的 `description`。** 否决。`description` 被扫进各 host 的系统提示；runner 起不来是脚本运行时 stderr 上的一行拒绝。这一条写进了 `AGENTS.md` 约定的第一条。
- **判活时向别的 runner 求证。** 否决。2026-09-10 实测：一个从 Herdr 挪到 Orca 接着跑的 Claude 会话，Herdr 的 `agent list` 仍把它绑在旧 pane 上并报 `idle`。一个自信的错误答案比「不知道」坏。

## Consequences

- 加一个 runner 是写一个适配器文件和它的 `MMW_USES` 声明。三个动词里答不出的那一个就答不知道：Herdr 的 `send` 对正在回合中的会话就是这样答的。
- 0009 的原则不变：脚本只做工具，判断归 main agent。改写的是它 Consequences 里写死 Paseo 的几条：`dispatch.sh` 不再建 Paseo workspace，也不再打印 `create_agent` 参数；归档由协议自己做——给回 slot，经各自 runner 的 `stop` 结束票上 `RUNNER` 行点名的每个会话，再 `git worktree remove`；reviewer 与 verifier 是 worker 经 `dispatch.sh start` 起的会话，只在两边都跑在 Paseo 上时才是它的 Paseo subagent。
- 0016 的原则不变：会话怎么起写在本机活表里。改写的是三处：活表多一行 `| runner | <name> |`，换今晚的 runner 是改这一行，不是换装另一个 checkout；一个 agent 只有一行，第二行在读表时被拒；`hosts.json` 里每个 host 的两块启动参数——它自己的命令行 flag（凡是在终端里跑 host CLI 的 runner 都读它，Herdr 与 Orca 是两个）与它在 Paseo 上的 settings——是 host 与 runner 的交叉，留在 `hosts.json`，不搬进适配器。
- 逐票指定 runner 是选法的第一级：`pick_runner` 为它留了参数，票上还没有写它的地方。
- 边界还没把所有 runner 知识收进去。四处仍直接问 Paseo：`status.py` 用 `paseo ls` 认活 worker，`verify-ticket.py` 用 `paseo send` 发 ticket message，`hook.py` 的 question gate 与 Cursor 上的 pretool gate 读 `PASEO_AGENT_ID` / `PASEO_AGENT_CWD`，`dispatch.sh check` 用 `paseo provider ls` 核 host。在它们搬走之前，别的 runner 上的会话不在 `status` 的表里，收不到 ticket message，也不受 question gate 管。
- 因为收不到 ticket message，Orca 与 Herdr 上的调用方靠反复跑 `wait` 或 `status` 得知会话结束（`mmw-v2/skills/dispatch/SKILL.md` 的「What tells you it is done」）。这与 0010「谁都不许轮询另一个 agent」冲突。本份不改写 0010；把唤醒从 runner 上拿走是 #316 的事。
