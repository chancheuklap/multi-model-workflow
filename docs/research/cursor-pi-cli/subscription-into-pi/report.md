# 把 Cursor 订阅接到 pi CLI

查证日期：2026-08-31。下面说的 pi，是 Mario Zechner 那套终端 coding agent（命令是 `pi`），不是树莓派，也不是 Pi Network。Cursor 订阅指 Anysphere 的个人或团队付费计划，额度记在 Cursor 自己的 usage dashboard 上。

## 1. pi 本体接不了 Cursor 订阅

pi 的 `/login` 只接内置订阅。本机 `@earendil-works/pi-coding-agent` 0.84.4 的 `docs/providers.md`，以及 GitHub [`earendil-works/pi` 的同一文件](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/providers.md)，列出的订阅是：ChatGPT Plus/Pro（Codex）、Claude Pro/Max、GitHub Copilot、xAI、OpenRouter、Radius。两处都没有 Cursor。

官方给自定义 API / OAuth 的出口是扩展：`docs/custom-provider.md`。所以「把 Cursor 订阅接到 pi」不是改一份 `models.json`，而是装一个 pi 扩展，让它注册名为 `cursor` 的 provider。

有人在 2026-08-07 开过工单，想把已登录的 Cursor CLI 做成 pi 内置桥（不写 `CURSOR_API_KEY`、不写 `auth.json`）。工单 [earendil-works/pi#7793](https://github.com/earendil-works/pi/issues/7793) 当天以 `no-action` 关闭，状态 `NOT_PLANNED`。截止本次，pi 没有这条内置路径。

## 2. 现在该用哪条路

社区走出三条路。认证方式和底层协议互不相同；装哪一个，pi 里就会出现一套 Cursor 模型。它们可以同时装在同一台机器上，但同一时刻通常只选一条来跑。

| 路径 | 认证 | 计费落在哪 | 协议 | 2026-08-31 是否还在更新 |
| --- | --- | --- | --- | --- |
| A. 官方 SDK 桥 | Cursor User API Key（或团队 service account key） | User API Key 记到该用户的计划；service account key 记到该团队。SDK 文档写：与 IDE、Cloud Agents 同一套定价、请求池和 Privacy Mode；花费出现在 usage dashboard 的 SDK 标签下 | `@cursor/sdk` 本地 agent loop（模型仍在 Cursor 云端） | 是。主包 `pi-cursor-sdk` 0.3.6（2026-08-21）；依赖钉在 `@cursor/sdk@1.0.27`。npm 上的 `@cursor/sdk` 已到 1.0.30（2026-08-27） |
| B. 官方 CLI 包装 | `agent login`，或同一把 `CURSOR_API_KEY` | 走官方 Cursor CLI。[CLI 认证文档](https://cursor.com/docs/cli/reference/authentication.md) 没有写 CLI 与 IDE 是否共用请求池 | 每个回合起 `agent` 子进程 | 主包 `@akepka/pi-cursor-cli-provider` 停在 2026-06-18 的 0.10.1；仓库 `Strus/pi-cursor-cli-provider` 最后 push 2026-08-08 |
| C. 逆向 AgentService | 浏览器 PKCE OAuth、`CURSOR_ACCESS_TOKEN`，或从 Cursor 桌面 / CLI 抽出的会话 | 包 README 写的是订阅登录态本身；官方计费文档不覆盖这条路径 | 直连 `api2.cursor.sh` 的 Connect / protobuf / HTTP2 | 当前还在发版的是 `@rahularya01/pi-cursor` 1.4.29（2026-08-29）。更旧的 `pi-oauth`、`pi-cursor-oauth`、`ndraiman`/`offbynan` 的 `pi-cursor-provider` 停在 2026-03 到 2026-07 |

路径 A 是 Cursor 自己在 2026-04-29 开放的 SDK 用法：[博文](https://cursor.com/blog/typescript-sdk) 写 available to all users。[SDK 文档 Authentication / Usage and billing](https://cursor.com/docs/sdk/typescript) 的原句是：SDK 调用跟 IDE、Cloud Agents 走同一套定价、请求池和 Privacy Mode；User API Key 记到该用户的计划上（可能含计划内用量，也可能触发按量加购，以你账号当时的计费设置为准）。入口从编辑器换成一把 key，账还是记在同一份计划上。

路径 B 用的是 Cursor 官方 CLI。CLI 文档把浏览器登录标成推荐方式，API Key 留给脚本和 CI。扩展只是把 `agent` 当成子进程。

路径 C 自己实现 Cursor 内部协议。`@rahularya01/pi-cursor` 的 README 第一段就写：Unofficial integration，not affiliated with or endorsed by Cursor / Anysphere，uses reverse-engineered wire protocol。Cursor 服务条款 1.5(i) 禁止 reverse engineer、获取底层结构；可接受使用政策禁止 reverse engineer，也禁止绕过系统或保护措施。这些扩展能跑，但不在官方接入面里。可接受使用政策里还有一条禁止用 bot 访问服务——官方 SDK 和官方 CLI 本身就是脚本入口，所以那一条不能单独拿来给路径 C 定罪。路径 C 真正踩到的是 reverse engineer / 底层结构这一层。

## 3. 推荐路径：官方 SDK + User API Key

包名 `pi-cursor-sdk`，作者 Mitch Fultz，仓库 [github.com/fitchmultz/pi-cursor-sdk](https://github.com/fitchmultz/pi-cursor-sdk)。npm 最新 **0.3.6**，发布时间 **2026-08-21**。过去一周（2026-08-23 到 2026-08-29）约 1649 次下载，过去一个月（2026-07-31 到 2026-08-29）约 7187 次。GitHub 308 star，最后一次 push 2026-08-18。

它把 Cursor 的 agent loop 留在 `@cursor/sdk` 里，pi 负责选模型、会话、确认和显示。默认跑本地 runtime：文件在你的磁盘上读，推理仍走 Cursor 托管模型。

同走 `@cursor/sdk` 的还有 [`@pi-stef/cursor`](https://www.npmjs.com/package/@pi-stef/cursor) 1.3.3（2026-08-04）。它用 `/cursor-login` 存 key，过去一周约 14 次下载。本次推荐装 `pi-cursor-sdk`，不并装两个都会注册 `cursor` provider 的包。

### 前置

- Node.js 22.19 或更高（`pi-cursor-sdk` 的 `engines.node`）。官方 `pi` 入口是 Node（安装后的 `pi` 文件第一行是 `#!/usr/bin/env node`）。
- pi 0.84.0 或更高（README Requirements）。
- 一把 Cursor **User API Key** 或团队 **service account key**。Team Admin API Key 被 Cursor SDK 拒绝。

### 拿密钥

官方文档写：打开 [Cursor Dashboard → API Keys](https://cursor.com/dashboard/api)，建一把 user key。CLI 认证文档指向同一页。Team Admin API Key 会被 SDK 拒掉；论坛 [Can't generate User API Key, only Admin scope](https://forum.cursor.com/t/cant-generate-user-api-key-only-admin-scope/166423) 有人因此拿到 Invalid User API Key。

不要用 Cursor 桌面登录，也不要用 `agent status` 里那份会话。[`pi-cursor-sdk` README](https://github.com/fitchmultz/pi-cursor-sdk/blob/main/README.md) 写明：它**不**复用 Agent CLI 登录、Desktop 登录、或 `agent status` 显示的订阅/OAuth 状态。

SDK 另有一条 `Cursor.auth.login()`：浏览器登录后铸造一把默认 90 天的 User API Key，存在 `~/.cursor/sdk/auth.json`。那是 SDK 自己的登录，不是 Cursor 桌面的登录。`pi-cursor-sdk` 的推荐路径仍是把 key 交给 pi 的 `/login` 或 `CURSOR_API_KEY`。

### 安装和登录

```bash
pi install npm:pi-cursor-sdk
pi --model cursor/grok-4.6
```

进入 pi 之后：

1. `/login`
2. 选 **Use an API key**
3. 选 **Cursor**
4. 把 User API Key 贴进去

密钥写进 pi 自己的 `~/.pi/agent/auth.json`。也可以不进交互登录：

```bash
export CURSOR_API_KEY="your-key"
pi --model cursor/grok-4.6
```

如果启动时还没有 key，扩展会先注册一份兜底模型列表，让 `/login` 仍然能打开。登录后再跑 `/cursor-refresh-models`，从 Cursor SDK 拉完整模型目录。

README 提示：若 `/login` 显示 `Cursor ✓ key in models.json`，但你并没有存过 Cursor key、也没有 `CURSOR_API_KEY`，那是 pi 认证状态的限制，不是真的已经有一把 SDK key。

### 冒烟（来自包 README，本次未在本机执行）

```bash
pi --list-models cursor

pi --model cursor/grok-4.6 --cursor-no-fast --no-session --mode json \
  -p "Reply exactly PI_CURSOR_MODEL_OK and nothing else."
```

期望：助手正文正好是 `PI_CURSOR_MODEL_OK`。缺 key 时，pi 会提示走 `/login`、`CURSOR_API_KEY` 或 `--api-key`。

### 选模型

`/model` 里挑，或命令行写 `cursor/<id>`。README 把 `cursor/grok-4.6` 标成当前推荐默认。Composer 2 / 2.5 可能默认开 fast；要关 fast，用 `--cursor-no-fast` 或模型别名 `:slow`。思考力度用 pi 的 `--thinking` 或模型后缀 `:medium` / `:high` / `:xhigh` / `:max`，扩展再映射到 Cursor SDK 的参数。

### 计费怎么读

官方说法只有：[SDK Usage and billing](https://cursor.com/docs/sdk/typescript) —— SDK 与 IDE、Cloud Agents 共用请求池，花费出现在 usage dashboard 的 SDK 标签下；User API Key 记到该用户的计划。本次没有用真实账号核对 dashboard 上的数字。

## 4. 次选：包装官方 Cursor CLI

如果你已经在用 Cursor 官方 CLI（命令名 `agent`），不想再管第二把 SDK key，可以走这条。本机若已能运行 `agent login` 或 `agent status`，这条的登录步骤更短，但工具执行会离开 pi。

当前更完整的包装是 [`@akepka/pi-cursor-cli-provider`](https://www.npmjs.com/package/@akepka/pi-cursor-cli-provider)（fork 自 `@netandreus/pi-cursor-provider`）。npm 最新 **0.10.1**，发布时间 **2026-06-18**；GitHub 仓库 `Strus/pi-cursor-cli-provider` 默认分支 `master`，最后 push **2026-08-08**。过去一周约 253 次下载，过去一个月约 867 次。原包 `@netandreus/pi-cursor-provider` 停在 2026-02-21 的 0.1.4。

作者 Kepka 写选择 CLI 包装的理由：逆向 Cursor 内部 API「太 hacky」；他自己试过 ACP（Agent Client Protocol），认为 ACP 只暴露部分模型，且每种模型只有一种思考档。CLI 是 Cursor 自己提供的订阅入口。

### 步骤

1. 安装 Cursor CLI：`curl https://cursor.com/install -fsS | bash`（官方 [CLI overview](https://cursor.com/docs/cli/overview)）
2. 登录：`agent login`（浏览器），或 `export CURSOR_API_KEY=...`。CLI 认证文档把浏览器登录标成推荐，API key 留给脚本和 CI；key 同样从 [Dashboard → API Keys](https://cursor.com/dashboard/api) 生成。
3. 装扩展：

```bash
pi install npm:@akepka/pi-cursor-cli-provider
```

4. 在 pi 里用 `/model` 选 Cursor 模型。`@akepka` 的 README 只写启动时自动发现模型；上游 `@netandreus` 写明发现命令是 `agent models`。本次没有打开 `@akepka` 源码核对它现在是否仍调用同一条命令。

每个 pi 回合会起一个 `agent --print --yolo --output-format stream-json` 子进程。第一回合送完整 transcript；之后用 `--resume <session-id>` 只送最新一句。工具执行发生在 Cursor CLI 里，不是 pi 的 read/edit/bash。token 计数是估计值，因为 CLI 不在回合结束时报精确用量。

第三条相关包装是 [`@0xkobold/pi-cursor`](https://www.npmjs.com/package/@0xkobold/pi-cursor)：用 `agent acp`（JSON-RPC over stdio）把任务委托给 Cursor Agent，而不是把 Cursor 注册成 pi 的模型 provider。停在 2026-03-24 的 0.1.0。ACP 模型覆盖不够用，是 `@akepka` 作者 Kepka 在自己 README 里的判断，不是这个包的作者声明。

## 5. 不推荐作默认：逆向 AgentService

这些扩展让你在 pi 里 `/login cursor`，或直接抽 Cursor 桌面 / CLI 的会话，然后本地把请求译成 Cursor 的 protobuf/HTTP2。

当前还在发版的是 [`@rahularya01/pi-cursor`](https://github.com/Rahularya01/pi-cursor) **1.4.29**（npm 发布时间 **2026-08-29**）。过去一周约 1140 次下载，过去一个月约 2274 次。GitHub 16 star。它自称：若本机 Cursor 桌面或 CLI 已登录，会自动检测凭据；否则 `/login cursor` 打开 `cursor.com/loginDeepControl`，轮询 `api2.cursor.sh/auth/poll`。凭据级联是：`CURSOR_ACCESS_TOKEN` → pi 的 `auth.json` → macOS Keychain → IDE `state.vscdb`。协议代码注明改编自 `ephraimduncan/opencode-cursor` 和 `@pi-stef/cursor`。

这条路看起来「不用再拿 key」，但有三道硬边界：

1. README 自己写 unofficial / reverse-engineered。
2. npm `engines` 只要 **Bun >= 1.4.0**。官方 `pi` 是 Node 进程。本机核对过：`pi` 文件第一行是 `#!/usr/bin/env node`。把这个包装进 Node 版 `pi`，和它声明的运行时不一致。
3. Cursor 条款 1.5(i) 禁止 reverse engineer、获取 underlying structure。

`wweir/pi-cursor` 是 `Rahularya01/pi-cursor` 的 fork，最后 push 2026-08-15，没有独立 npm 包。

更旧、基本停更的同类包：

| 包 | 最新 | 发布 | 做法 |
| --- | --- | --- | --- |
| `pi-oauth` | 0.0.1 | 2026-05-26 | `/login` → Use a subscription → Cursor；直连 AgentService |
| `@offbynan/pi-cursor-provider` | 0.6.0 | 2026-07-08 | fork `ndraiman/pi-cursor-provider`，本地 OpenAI 兼容代理 → `api2.cursor.sh` |
| `pi-cursor-provider`（ndraiman） | 0.1.11 | 2026-04-09 | 上游：PKCE + gRPC 代理 |
| `pi-cursor-oauth` | 0.2.0 | 2026-03-24 | `/login cursor`，`CURSOR_ACCESS_TOKEN` 兜底 |

条款上的对应关系（不是法律意见，是原文对照）：

- [Terms of Service 1.5](https://cursor.com/terms-of-service) Use Restrictions (i)：禁止 reverse engineer、disassemble、decompile、decode，或 otherwise attempt to derive or gain access to the source code, object code or underlying structure of the Service。
- [Acceptable Use Policy](https://cursor.com/acceptable-use-policy)：禁止 reverse engineer；禁止 bypassing our systems or protective measures。

官方 SDK 和官方 CLI 是 Cursor 自己提供的自动化入口。路径 C 是社区对内部协议的再实现。r/PiCodingAgent 在 2026-05 有人转述「Cursor mentioned this is not allowed」——转述，不是官方帖，原文未找到。

## 6. 对照与未核实

过去一周（2026-08-23 到 2026-08-29）和过去一个月（2026-07-31 到 2026-08-29）的 npm 下载：

| 包 | 周下载 | 月下载 | 最新发布 |
| --- | --- | --- | --- |
| `pi-cursor-sdk` | 1649 | 7187 | 2026-08-21 |
| `@rahularya01/pi-cursor` | 1140 | 2274 | 2026-08-29 |
| `@akepka/pi-cursor-cli-provider` | 253 | 867 | 2026-06-18 |
| `@pi-stef/cursor` | 14 | 951 | 2026-08-04 |
| `@netandreus/pi-cursor-provider` | 82 | 314 | 2026-02-21 |
| `@offbynan/pi-cursor-provider` | 40 | 273 | 2026-07-08 |
| `pi-cursor-provider` | 35 | 146 | 2026-04-09 |
| `pi-cursor-oauth` | 26 | 113 | 2026-03-24 |
| `pi-oauth` | 28 | 92 | 2026-05-26 |
| `@0xkobold/pi-cursor` | 4 | 35 | 2026-03-24 |

下载量不是质量证明。它只说明：在上面列出的这些 npm 扩展里，2026 年 8 月最后一周的下载仍以 `pi-cursor-sdk` 为主；`@rahularya01/pi-cursor` 的周下载已经接近它，但协议和运行时都不是官方 `pi` + `@cursor/sdk` 这条线。没装进 npm、或走别的安装方式的用法，这张表看不到。

**未在本机核实：**

- 没有执行 `pi install`，也没有用真实 Cursor 密钥跑第 3 节的冒烟命令。
- 没有打开登录后的 Cursor Dashboard，所以没有核对自己账号的密钥页菜单，也没有核对本账号 User API Key 的前缀。
- 没有核对这些扩展是否违反你账号适用的 Cursor 合同；第 5 节只对照公开条款文本。
- 没有在 Bun 宿主（例如 oh-my-pi）上试 `@rahularya01/pi-cursor`。
