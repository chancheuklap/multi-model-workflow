# research：把 Cursor 订阅接到 pi CLI

## 这次要回答的问题

付了 Cursor 订阅的人，怎么在 Mario Zechner 的 pi coding agent（终端里的 `pi` 命令）里用那份额度，而不是再买一份 Anthropic / OpenAI 的 API。

查证日期：2026-08-25。优先看官方文档、包源码/README、npm 发布时间；社区帖只用来核对有没有人真跑通过。

## 查证范围

- pi 官方 provider 清单：`earendil-works/pi` 的 `packages/coding-agent/README.md`、`docs/providers.md`（Cursor 不在内置订阅里）。
- Cursor 官方：TypeScript SDK 认证与计费、CLI `agent login` / `CURSOR_API_KEY`、2026-04-29 SDK 发布博文、服务条款 1.5 与可接受使用政策。
- 社区扩展（按 2026-07-26 到 2026-08-24 的 npm 月下载排序）：`pi-cursor-sdk`、`@akepka/pi-cursor-cli-provider`、`@netandreus/pi-cursor-provider`、`@offbynan/pi-cursor-provider`、`pi-cursor-provider`、`pi-cursor-oauth`、`pi-oauth`。
- 实测帖：DeepakNess 2026-05-23 的用量截图、r/PiCodingAgent 上的接入讨论、X 上 2026-08 的使用反馈。

## 结论摘要

1. **pi 本体没有 Cursor 订阅登录。** `/login` 的内置订阅只有 Claude、ChatGPT/Codex、GitHub Copilot、xAI、OpenRouter、Radius。Cursor 一律走扩展。
2. **2026 年 8 月该装的是 `pi-cursor-sdk`。** 它走 Cursor 官方 `@cursor/sdk`，用 Dashboard 上的 User API Key。SDK 文档写：User API Key 记到该用户的计划，与 IDE、Cloud Agents 同一套定价和请求池。npm 最新 `0.3.6`（2026-08-21），过去一周约 1879 次下载，过去一个月约 8576 次，GitHub 295 star。
3. **不要指望复用 Cursor 桌面或 `agent status` 的登录态。** `pi-cursor-sdk` 明确不读那份 OAuth。密钥来源是 Dashboard → API Keys，或环境变量 `CURSOR_API_KEY`。
4. **第二条合法路径是包装官方 Cursor CLI。** `@akepka/pi-cursor-cli-provider` 每个回合起一个 `agent` 子进程，用 `agent login` 或同一把 API Key。月下载约 782，比 SDK 桥少一个数量级，但不用逆向 Cursor 内部协议。
5. **浏览器 OAuth 直连 `api2.cursor.sh` 的扩展是另一条路，条款风险不同。** `pi-oauth`、`pi-cursor-oauth`、`ndraiman`/`offbynan` 的 `pi-cursor-provider` 走 PKCE + AgentService/gRPC。Cursor 条款 1.5(i) 禁止 reverse engineer、获取底层结构。这些包能跑，但不算官方接入。

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

- 没有在本机执行 `pi install npm:pi-cursor-sdk`，也没有用真实 Cursor 密钥跑冒烟命令。安装步骤来自包 README，计费规则来自 Cursor SDK 文档，用量数字来自 DeepakNess 2026-05 的个人截图。
- Cursor Dashboard 的密钥页，官方文档写 `cursor.com/dashboard/api`；DeepakNess 2026-05-24 的截图写 `/dashboard/integrations`。两边都指向 User API Key，页面路径是否已改，未打开登录后的 Dashboard 核对。
- Cursor 有没有在工单或论坛里点名禁止「把 CLI 当 pi 的 provider」，这次没有找到官方点名；Reddit 上有用户转述「Cursor mentioned this is not allowed」，原话出处未核实。
