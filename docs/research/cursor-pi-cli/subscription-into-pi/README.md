# research：把 Cursor 订阅接到 pi CLI

## 这次要回答的问题

付了 Cursor 订阅的人，怎么在 Mario Zechner 的 pi coding agent（终端里的 `pi` 命令）里用那份额度，而不是再买一份 Anthropic / OpenAI 的 API。

查证日期：2026-08-31。优先看官方文档、包源码/README、npm 发布时间；社区帖只用来核对有没有人真跑通过。

## 查证范围

- pi 官方 provider 清单：本机 `@earendil-works/pi-coding-agent` 0.84.4 的 `docs/providers.md`，以及 GitHub `earendil-works/pi` 同一文件。Cursor 不在内置订阅里。
- Cursor 官方：[TypeScript SDK](https://cursor.com/docs/sdk/typescript) 认证与计费、[CLI authentication](https://cursor.com/docs/cli/reference/authentication.md)、Dashboard API Keys 页、服务条款 1.5 与可接受使用政策。
- 社区扩展（按 2026-08-23 到 2026-08-29 的 npm 周下载排序）：`pi-cursor-sdk`、`@rahularya01/pi-cursor`、`@akepka/pi-cursor-cli-provider`、`@pi-stef/cursor`，以及更旧的 `pi-oauth` / `pi-cursor-oauth` / `ndraiman`/`offbynan` `pi-cursor-provider`。
- 官方是否把 Cursor 做成 pi 内置：GitHub `earendil-works/pi` #7793。

## 结论摘要

1. **pi 本体没有 Cursor 订阅登录。** `/login` 的内置订阅只有 Claude、ChatGPT/Codex、GitHub Copilot、xAI、OpenRouter、Radius。把 Cursor 接到 pi 一律走扩展。把 Cursor CLI 会话做成内置桥的工单 [#7793](https://github.com/earendil-works/pi/issues/7793) 已于 2026-08-07 以 `no-action` 关闭。
2. **2026 年 8 月该装的仍是 `pi-cursor-sdk`。** 它走 Cursor 官方 `@cursor/sdk`，用 Dashboard 上的 User API Key。SDK 文档写：User API Key 记到该用户的计划，与 IDE、Cloud Agents 同一套定价和请求池。npm 最新 `0.3.6`（2026-08-21），过去一周约 1649 次下载。
3. **不要指望复用 Cursor 桌面或 `agent status` 的登录态。** `pi-cursor-sdk` 明确不读那份 OAuth。密钥来源是 [Dashboard → API Keys](https://cursor.com/dashboard/api)，或环境变量 `CURSOR_API_KEY`。Team Admin API Key 会被 SDK 拒绝。
4. **第二条合法路径是包装官方 Cursor CLI。** `@akepka/pi-cursor-cli-provider` 每个回合起一个 `agent` 子进程，用 `agent login` 或同一把 API Key。工具执行在 Cursor CLI 里，不在 pi 的 read/edit/bash 里。
5. **能复用桌面登录的包是非官方逆向。** `@rahularya01/pi-cursor` 1.4.29（2026-08-29）会读 Keychain / IDE `state.vscdb`，或走 `/login cursor` 到 `api2.cursor.sh`。README 自称 unofficial、reverse-engineered；npm `engines` 只要 Bun `>=1.4.0`。官方 `pi` 是 Node 入口（`#!/usr/bin/env node`），和这条运行时对不上。

## 本目录的文件

| 文件 | 内容 |
| --- | --- |
| `README.md` | 本文件，research 索引 |
| `report.md` | 完整结论：官方边界、三条路径、逐步操作、对照表、坑 |

## 章节指引

`report.md` 按阅读顺序分成六节：

1. **pi 本体接不了 Cursor 订阅** — 官方 `/login` 名单，以及「扩展才是接入面」。
2. **现在该用哪条路** — 三条路径各扣什么账、各走哪段协议。
3. **推荐路径：官方 SDK + User API Key** — `pi-cursor-sdk` 的安装、密钥、选模型和冒烟命令。
4. **次选：包装官方 Cursor CLI** — `agent login` 接到 pi 里，以及它和 SDK 桥的差别。
5. **不推荐作默认：逆向 AgentService** — 哪些包、它们做什么、条款上踩哪几条。
6. **对照与未核实** — 下载量/新鲜度表，以及这次没在本机跑通的部分。

## 没查清楚的部分

- 没有在本机执行 `pi install npm:pi-cursor-sdk`，也没有用真实 Cursor 密钥跑冒烟命令。安装步骤来自包 README，计费规则来自 Cursor SDK 文档。
- User API Key 的具体前缀（社区示例有 `crsr_` 也有 `cursor_`）没有从登录后的 Dashboard 核对。官方 SDK 文档只写 `your-key`。
- Cursor CLI 认证文档没有写 CLI 与 IDE 是否共用请求池；本次没有找到官方句子，所以第 4 节不把「同一池」写成事实。
- Reddit 上有用户转述「Cursor mentioned this is not allowed」，原话出处未核实。
